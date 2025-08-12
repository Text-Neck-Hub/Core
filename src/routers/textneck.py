from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from typing import Annotated
from datetime import datetime, timezone
import json
import logging

from ..connection.manager import manager
from ..services.core import CoreService
from ..repositories.log_repository import LogRepository
from ..auth.authentication import get_ws_token_payload
from ..schemas.jwt import TokenData
from ..schemas.logs import Angle

logger = logging.getLogger('prod')
textneck_router = APIRouter(prefix="/ws")
COMMANDS = {"init", "pause", "resume", "stop"}


@textneck_router.websocket("/textneck/")
async def predict_textneck(
    websocket: WebSocket,
    current_user_data: Annotated[TokenData, Depends(get_ws_token_payload)]
):
    await manager.connect(websocket)
    stack: list[Angle] = []
    paused = False
    angle_threshold: float | None = None
    shoulder_y_diff_threshold: float | None = None
    shoulder_y_avg_threshold: float | None = None

    try:
        while True:
            raw = await websocket.receive_text()
            msg = raw.strip()

            init_handled = False
            try:
                obj = json.loads(msg)
                if isinstance(obj, dict) and str(obj.get("action", "")).lower() == "init":
                    if "angle_threshold" in obj:
                        angle_threshold = float(obj["angle_threshold"])
                    if "shoulder_y_diff_threshold" in obj:
                        shoulder_y_diff_threshold = float(
                            obj["shoulder_y_diff_threshold"])
                    if "shoulder_y_avg_threshold" in obj:
                        shoulder_y_avg_threshold = float(
                            obj["shoulder_y_avg_threshold"])
                    paused = True
                    await websocket.send_json({
                        "status": "initialized",
                        "paused": True,
                        "thresholds": {
                            "angle_threshold": angle_threshold,
                            "shoulder_y_diff_threshold": shoulder_y_diff_threshold,
                            "shoulder_y_avg_threshold": shoulder_y_avg_threshold
                        }
                    })
                    init_handled = True
            except json.JSONDecodeError:
                pass

            if init_handled:
                continue

            cmd = msg.lower()
            if len(msg) <= 64 and cmd in COMMANDS:
                if cmd == "init":
                    parts = msg.split(":")
                    if len(parts) == 4:
                        try:
                            angle_threshold = float(parts[1])
                            shoulder_y_diff_threshold = float(parts[2])
                            shoulder_y_avg_threshold = float(parts[3])
                        except ValueError:
                            pass
                    paused = True
                    await websocket.send_json({
                        "status": "initialized",
                        "paused": True,
                        "thresholds": {
                            "angle_threshold": angle_threshold,
                            "shoulder_y_diff_threshold": shoulder_y_diff_threshold,
                            "shoulder_y_avg_threshold": shoulder_y_avg_threshold
                        }
                    })

                if cmd == "pause":
                    if not paused:
                        paused = True
                        await websocket.send_json({"status": "paused"})
                    else:
                        await websocket.send_json({"status": "already_paused"})
                    continue

                if cmd == "resume":
                    if paused:
                        paused = False
                        await websocket.send_json({"status": "resumed"})
                    else:
                        await websocket.send_json({"status": "already_running"})
                    continue

                if cmd == "stop":
                    await websocket.send_json({"status": "stopping"})
                    await websocket.close()
                    break

            if paused:
                continue

            processed = CoreService.process_image_frame(msg)

            if processed.get("has_angle"):
                val = processed.get("neck_angle_deg")
                if val is None:
                    val = processed.get("angle_value")
                if val is not None:
                    log = Angle(
                        angle=float(val),
                        shoulder_y_diff=processed.get("shoulder_y_diff_px"),
                        shoulder_y_avg=processed.get("shoulder_y_avg_px"),
                        logged_at=datetime.now(timezone.utc)
                    )
                    stack.append(log)
                    if len(stack) >= 5:
                        await LogRepository.push_logs(
                            user_id=current_user_data.user_id,
                            items=stack
                        )
                        stack.clear()

            await websocket.send_json(processed)

    except WebSocketDisconnect:
        if stack:
            try:
                await LogRepository.push_logs(
                    user_id=current_user_data.user_id,
                    items=stack
                )
            finally:
                stack.clear()
        logger.info(f"Client disconnected: {websocket.client}")
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}", exc_info=True)
        if stack:
            try:
                await LogRepository.push_logs(
                    user_id=current_user_data.user_id,
                    items=stack
                )
            finally:
                stack.clear()
        manager.disconnect(websocket)
