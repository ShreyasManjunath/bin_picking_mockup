from __future__ import annotations

from contextlib import asynccontextmanager
from threading import Event, Thread
from typing import Optional, Any, Dict

import rclpy
from fastapi import FastAPI, HTTPException, Path
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from rclpy.node import Node
from rclpy.action import ActionClient
from rclpy.executors import MultiThreadedExecutor
from rclpy.task import Future

from std_msgs.msg import Int32, Bool
from bin_picking_mockup.srv import SetEStopState, SetDoorState
from bin_picking_mockup.action import (
    FakeBinPick,
)


app = FastAPI(
    title="ROS2 Bin Picking API Adapter",
    description="REST API for E-Stop, Door, Stack Light, and Fake Bin Pick action.",
    version="1.0.0",
    swagger_ui_parameters={"defaultModelsExpandDepth": 0, "tryItOutEnabled": True},
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


class BoolResult(BaseModel):
    success: bool
    message: Optional[str] = None


class LightStateResponse(BaseModel):
    state: Optional[int]
    message: Optional[str] = None


class PickRequest(BaseModel):
    pickId: int = Field(..., description="Mapped to FakeBinPick.Goal.task_id")
    quantity: int = Field(..., ge=1, description="Ignored by the action.")


class PickSyncResponse(BaseModel):
    pickId: int
    pickSuccessful: bool
    errorMessage: Optional[str] = None
    itemBarcode: Optional[int] = None


class EstopStateResponse(BaseModel):
    pressed: Optional[bool]
    message: Optional[str] = None


class DoorStateResponse(BaseModel):
    closed: Optional[bool]
    message: Optional[str] = None


class ApiNode(Node):
    def __init__(self):
        super().__init__("api_service_client")

        self.cli_estop = self.create_client(SetEStopState, "/set_estop_state")
        self.cli_door = self.create_client(SetDoorState, "/set_door_state")
        for name, cli in [
            ("/set_estop_state", self.cli_estop),
            ("/set_door_state", self.cli_door),
        ]:
            while not cli.wait_for_service(timeout_sec=1.0):
                self.get_logger().info(f"Waiting for {name} service...")

        self.stack_light_state: Optional[int] = None
        self.stack_light_sub = self.create_subscription(
            Int32, "/stack_light", self.light_callback, 10
        )
        self.estop_pressed: Optional[bool] = False
        self.estop_sub = self.create_subscription(
            Bool, "/estop_pressed", self.estop_callback, 10
        )
        self.door_closed: Optional[bool] = True
        self.door_sub = self.create_subscription(
            Bool, "/door_closed", self.door_callback, 10
        )

        self.pick_action = ActionClient(self, FakeBinPick, "/fake_bin_pick")
        while not self.pick_action.wait_for_server(timeout_sec=1.0):
            self.get_logger().info("Waiting for /fake_bin_pick action server...")

    def light_callback(self, msg: Int32):
        self.stack_light_state = int(msg.data)

    def estop_callback(self, msg: Bool):
        self.estop_pressed = bool(msg.data)

    def door_callback(self, msg: Bool):
        self.door_closed = bool(msg.data)

    def _wait_for_future(
        self,
        future: Future,
        *,
        timeout_sec: float,
        description: str,
    ) -> Any:
        done = Event()
        result: Dict[str, Any] = {"value": None, "error": None}

        def on_complete(completed_future: Future) -> None:
            try:
                result["value"] = completed_future.result()
            except Exception as exc:  # pragma: no cover - defensive bridge
                result["error"] = exc
            finally:
                done.set()

        future.add_done_callback(on_complete)
        if not done.wait(timeout=timeout_sec):
            raise TimeoutError(f"Timed out waiting for {description}.")
        if result["error"] is not None:
            raise RuntimeError(f"{description} failed.") from result["error"]
        return result["value"]

    def call_estop(self, pressed: bool):
        req = SetEStopState.Request()
        req.pressed = bool(pressed)
        fut = self.cli_estop.call_async(req)
        return self._wait_for_future(
            fut,
            timeout_sec=5.0,
            description="/set_estop_state service call",
        )

    def call_door(self, closed: bool):
        req = SetDoorState.Request()
        req.closed = bool(closed)
        fut = self.cli_door.call_async(req)
        return self._wait_for_future(
            fut,
            timeout_sec=5.0,
            description="/set_door_state service call",
        )

    def run_pick_sync(self, pick_id: int) -> PickSyncResponse:
        """
        Sends a FakeBinPick goal (task_id) and BLOCKS until the result returns.
        Maps the action result to the required response JSON.
        """
        goal = FakeBinPick.Goal()
        goal.task_id = int(pick_id)

        send_future = self.pick_action.send_goal_async(goal)
        goal_handle = self._wait_for_future(
            send_future,
            timeout_sec=10.0,
            description="/fake_bin_pick goal submission",
        )

        if goal_handle is None or not goal_handle.accepted:
            error_msg = "Goal rejected by action server."
            if self.estop_pressed:
                error_msg += " Reason: ESTOP pressed."
            elif not self.door_closed:
                error_msg += " Reason: Safety door open."
            return PickSyncResponse(
                pickId=pick_id,
                pickSuccessful=False,
                errorMessage=error_msg,
                itemBarcode=None,
            )

        result_future = goal_handle.get_result_async()
        result_obj = self._wait_for_future(
            result_future,
            timeout_sec=15.0,
            description="/fake_bin_pick result",
        )
        result_msg = getattr(result_obj, "result", None)

        if result_msg is None:
            return PickSyncResponse(
                pickId=pick_id,
                pickSuccessful=False,
                errorMessage="No result returned by action",
                itemBarcode=None,
            )

        success = bool(getattr(result_msg, "success", False))
        message = str(getattr(result_msg, "message", "")) if not success else None
        barcode = getattr(result_msg, "barcode", None)
        barcode = int(barcode) if barcode is not None else None

        return PickSyncResponse(
            pickId=pick_id,
            pickSuccessful=success,
            errorMessage=message,
            itemBarcode=barcode,
        )


def _spin(executor: MultiThreadedExecutor) -> None:
    executor.spin()


def _raise_api_error(exc: Exception) -> None:
    if isinstance(exc, TimeoutError):
        raise HTTPException(status_code=504, detail=str(exc)) from exc
    raise HTTPException(status_code=502, detail=str(exc)) from exc


@asynccontextmanager
async def lifespan(app: FastAPI):
    rclpy.init()
    node = ApiNode()
    executor = MultiThreadedExecutor(num_threads=2)
    executor.add_node(node)
    spin_thread = Thread(target=_spin, args=(executor,), daemon=True)
    spin_thread.start()

    app.state.ros_node = node
    app.state.ros_executor = executor
    app.state.spin_thread = spin_thread
    try:
        yield
    finally:
        node.get_logger().info("Shutting down ROS2...")
        executor.remove_node(node)
        executor.shutdown(timeout_sec=1.0)
        node.destroy_node()
        rclpy.shutdown()
        spin_thread.join(timeout=2.0)


app.router.lifespan_context = lifespan


@app.post(
    "/estop/{pressed}",
    response_model=BoolResult,
    tags=["E-Stop"],
    summary="Set E-Stop state",
    description="Trigger `/set_estop_state` (bin_picking_mockup/srv/SetEStopState) with `pressed=true|false`.",
)
def trigger_estop(
    pressed: bool = Path(..., description="`true` to press E-Stop, `false` to release.")
):
    try:
        res = app.state.ros_node.call_estop(pressed)
    except Exception as exc:
        _raise_api_error(exc)
    return {
        "success": bool(getattr(res, "success", True)),
        "message": getattr(res, "message", ""),
    }


@app.post(
    "/door/{closed}",
    response_model=BoolResult,
    tags=["Door"],
    summary="Set door state",
    description="Trigger `/set_door_state` (bin_picking_mockup/srv/SetDoorState) with `closed=true|false`.",
)
def trigger_door(
    closed: bool = Path(..., description="`true` to close door, `false` to open.")
):
    try:
        res = app.state.ros_node.call_door(closed)
    except Exception as exc:
        _raise_api_error(exc)
    return {
        "success": bool(getattr(res, "success", True)),
        "message": getattr(res, "message", ""),
    }


@app.get(
    "/stack_light",
    response_model=LightStateResponse,
    tags=["Stack Light"],
    summary="Get current stack light state.",
    description="""
Returns the latest `/stack_light` topic value (`std_msgs/Int32`).

**State mapping (for reference):**
- `0` → Operational
- `1` → Paused
- `-1` → Estop
- any other → Unknown
""",
)
def get_stack_light():
    state = app.state.ros_node.stack_light_state
    if state is None:
        return {"state": None, "message": "No data received yet from /stack_light"}
    return {"state": int(state)}


@app.get(
    "/estop",
    response_model=EstopStateResponse,
    tags=["E-Stop"],
    summary="Get current E-Stop state.",
    description="Returns the latest `/estop_pressed` topic value (`std_msgs/Bool`).",
)
def get_estop_state():
    pressed = app.state.ros_node.estop_pressed
    if pressed is None:
        return {"pressed": None, "message": "No data received yet from /estop_pressed"}
    return {"pressed": bool(pressed)}


@app.get(
    "/door",
    response_model=DoorStateResponse,
    tags=["Door"],
    summary="Get current door state.",
    description="Returns the latest `/door_closed` topic value (`std_msgs/Bool`).",
)
def get_door_state():
    closed = app.state.ros_node.door_closed
    if closed is None:
        return {"closed": None, "message": "No data received yet from /door_closed"}
    return {"closed": bool(closed)}


@app.post(
    "/confirmPick",
    response_model=PickSyncResponse,
    tags=["Bin Picking"],
    summary="Perform a fake bin-pick",
    description=(
        "Receives the request, performs the fake pick via `/fake_bin_pick`, and returns the result.\n\n"
        "**Response format:**\n"
        "```json\n"
        "{\n"
        '  "pickId": 123,\n'
        '  "pickSuccessful": true,\n'
        '  "errorMessage": null,\n'
        '  "itemBarcode": 123\n'
        "}\n"
        "```\n"
        "Note: the action goal only supports `task_id`. The `quantity` field is accepted in the request but ignored."
    ),
)
def start_fake_pick(req: PickRequest):
    try:
        return app.state.ros_node.run_pick_sync(req.pickId)
    except Exception as exc:
        _raise_api_error(exc)
