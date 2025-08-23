import os
import json
import time
from collections import deque
from datetime import datetime, timezone
from typing import Optional, Dict, Any

import requests
from fastapi import FastAPI, Response, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, StrictInt

ROBOT_BASE_URL = os.getenv("ROBOT_BASE_URL")
CONFIRM_PICK_URL = f"{ROBOT_BASE_URL}/confirmPick" if ROBOT_BASE_URL else None
# ALLOW_ORIGINS = os.getenv("ALLOW_ORIGINS", "http://localhost:80").split(",")

app = FastAPI(
    title="WMS API",
    version="1.1.0",
    description=(
        "Warehouse Management System (WMS)\n\n"
        "- POST /pick → forwards body to robot /confirmPick\n"
        "- GET  /status → aggregates estop/door/stack_light from robot\n"
        "- GET  /traffic → recent /pick traffic (monitoring)\n"
        "- GET  /traffic/stream → live Server‑Sent Events (monitoring)\n"
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


class PickRequest(BaseModel):
    model_config = {
        "extra": "forbid",
        "json_schema_extra": {"example": {"pickId": 123, "quantity": 4}},
    }
    pickId: StrictInt = Field(..., example=123)
    quantity: StrictInt = Field(..., ge=1, example=4)


class TrafficEntry(BaseModel):
    ts: str  # ISO8601 UTC
    path: str  # "/pick"
    latency_ms: int
    request_json: Optional[Dict[str, Any]] = None
    response_status: int
    response_json: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


TRAFFIC = deque(maxlen=int(os.getenv("TRAFFIC_MAX", "500")))


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_get_json(url: str, timeout: float = 3.0) -> Dict[str, Any]:
    try:
        r = requests.get(url, timeout=timeout)
        ct = r.headers.get("content-type", "")
        if "application/json" in ct:
            return r.json()
        return {"raw": r.text}
    except requests.RequestException as e:
        return {"error": str(e)}


def _require_robot_base():
    if not ROBOT_BASE_URL:
        raise HTTPException(status_code=500, detail="ROBOT_BASE_URL not configured.")


@app.get("/health", summary="Health check")
def healthz():
    return {"ok": True, "robot_base": bool(ROBOT_BASE_URL)}


@app.get("/status", summary="Robot status: estop, door, stack_light")
def status_endpoint():
    _require_robot_base()

    estop = _safe_get_json(f"{ROBOT_BASE_URL}/estop")
    door = _safe_get_json(f"{ROBOT_BASE_URL}/door")
    light = _safe_get_json(f"{ROBOT_BASE_URL}/stack_light")

    state_map = {0: "Operational", 1: "Paused", -1: "Estop"}
    label = None
    if isinstance(light, dict) and light.get("state") is not None:
        label = state_map.get(light.get("state"), "Unknown")

    light_out = dict(light) if isinstance(light, dict) else {}
    light_out["label"] = label

    return {"estop": estop, "door": door, "stack_light": light_out}


@app.post("/pick", summary="Forward a pick to the robot /confirmPick")
def pick_endpoint(payload: PickRequest, request: Request):
    _require_robot_base()
    if not CONFIRM_PICK_URL:
        raise HTTPException(status_code=500, detail="CONFIRM_PICK_URL not resolved.")

    started = time.perf_counter()
    req_dict = payload.model_dump()
    status_code = 500
    body_json: Optional[Dict[str, Any]] = None
    err: Optional[str] = None

    try:
        upstream_resp = requests.post(
            CONFIRM_PICK_URL,
            json=req_dict,
            timeout=10.0,
        )
        ct = upstream_resp.headers.get("content-type", "")
        # Try to parse JSON body (even on non-2xx)
        if "application/json" in ct:
            try:
                body_json = upstream_resp.json()
            except Exception:
                body_json = {"raw": upstream_resp.text[:8000]}
        else:
            body_json = {"raw": upstream_resp.text[:8000]}

        status_code = upstream_resp.status_code
        return Response(
            content=upstream_resp.content,
            status_code=status_code,
            media_type=ct or "application/json",
        )
    except requests.RequestException as e:
        err = str(e)
        raise HTTPException(status_code=502, detail=f"Upstream connection error: {e}")
    finally:
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        TRAFFIC.append(
            TrafficEntry(
                ts=_utcnow_iso(),
                path="/pick",
                latency_ms=elapsed_ms,
                request_json=req_dict,
                response_status=status_code,
                response_json=body_json,
                error=err,
            )
        )


@app.get("/traffic", summary="Recent /pick traffic (most recent first)")
def get_traffic(limit: int = 100):
    """Return recent pick traffic as JSON (for dashboards / debugging)."""
    limit = max(1, min(limit, len(TRAFFIC)))
    items = list(TRAFFIC)[-limit:]
    return list(reversed([e.model_dump() for e in items]))


@app.get("/traffic/stream", summary="Live traffic stream (SSE)")
def stream_traffic():
    """
    Server-Sent Events stream of /pick traffic entries as they arrive.
    Sends a replay of the last ~50 entries on connect, then tails live.
    """
    replay = list(reversed(list(TRAFFIC)[-50:]))

    def gen():
        # initial replay
        for e in replay:
            yield f"data: {json.dumps(e.model_dump())}\n\n"

        idx = len(TRAFFIC)
        try:
            while True:
                if len(TRAFFIC) > idx:
                    new_items = list(TRAFFIC)[idx:]
                    idx = len(TRAFFIC)
                    for e in new_items:
                        yield f"data: {json.dumps(e.model_dump())}\n\n"
                time.sleep(0.5)
        except GeneratorExit:
            return

    headers = {
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no",
    }
    return StreamingResponse(gen(), media_type="text/event-stream", headers=headers)
