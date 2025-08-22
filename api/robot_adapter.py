from __future__ import annotations

from contextlib import asynccontextmanager
from threading import Thread
from typing import Optional, Any, Dict

import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient

from fastapi import FastAPI, Path
from pydantic import BaseModel, Field
import uvicorn

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
        self.create_subscription(Int32, "/stack_light", self.light_callback, 10)
        self.estop_pressed: Optional[bool] = False
        self.create_subscription(Bool, "/estop_pressed", self.estop_callback, 10)
        self.door_closed: Optional[bool] = True
        self.create_subscription(Bool, "/door_closed", self.door_callback, 10)

        self.pick_action = ActionClient(self, FakeBinPick, "/fake_bin_pick")
        while not self.pick_action.wait_for_server(timeout_sec=1.0):
            self.get_logger().info("Waiting for /fake_bin_pick action server...")

    def light_callback(self, msg: Int32):
        self.stack_light_state = int(msg.data)

    def estop_callback(self, msg: Bool):
        self.estop_pressed = bool(msg.data)

    def door_callback(self, msg: Bool):
        self.door_closed = bool(msg.data)

    def call_estop(self, pressed: bool):
        req = SetEStopState.Request()
        req.pressed = bool(pressed)
        fut = self.cli_estop.call_async(req)
        rclpy.spin_until_future_complete(self, fut)
        return fut.result()

    def call_door(self, closed: bool):
        req = SetDoorState.Request()
        req.closed = bool(closed)
        fut = self.cli_door.call_async(req)
        rclpy.spin_until_future_complete(self, fut)
        return fut.result()

    def run_pick_sync(self, pick_id: int) -> PickSyncResponse:
        """
        Sends a FakeBinPick goal (task_id) and BLOCKS until the result returns.
        Maps the action result to the required response JSON.
        """
        goal = FakeBinPick.Goal()
        goal.task_id = int(pick_id)

        # Send goal
        send_future = self.pick_action.send_goal_async(goal)
        rclpy.spin_until_future_complete(self, send_future)
        goal_handle = send_future.result()

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
        rclpy.spin_until_future_complete(self, result_future)
        result_obj = result_future.result()
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


def _spin(node: Node):
    rclpy.spin(node)


@asynccontextmanager
async def lifespan(app: FastAPI):
    rclpy.init()
    node = ApiNode()
    spin_thread = Thread(target=_spin, args=(node,), daemon=True)
    spin_thread.start()

    app.state.ros_node = node
    try:
        yield
    finally:
        node.get_logger().info("Shutting down ROS2...")
        node.destroy_node()
        rclpy.shutdown()


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
    res = app.state.ros_node.call_estop(pressed)
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
    res = app.state.ros_node.call_door(closed)
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
    return app.state.ros_node.run_pick_sync(req.pickId)


if __name__ == "__main__":
    uvicorn.run("robot_adapter:app", host="0.0.0.0", port=8081, reload=True)
