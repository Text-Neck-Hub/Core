from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from ..connection.manager import manager
from ..services.core import process_image_frame

import logging
logger = logging.getLogger('prod')
textneck_router = APIRouter(prefix="/ws")


@textneck_router.websocket("/textneck/")
async def predict_textneck(websocket: WebSocket):
    await manager.connect(websocket)
    paused = False
    try:
        while True:
            data_str = await websocket.receive_text()
            cmd = data_str.strip().lower()

            if cmd == "init":
                logger.info(f"Init by client: {websocket.client}")
                paused = True
                await websocket.send_json({"status": "initialized", "paused": True})
                continue

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

            processed_data = process_image_frame(data_str)
            await websocket.send_json(processed_data)
    except WebSocketDisconnect:
        logger.info(f"Client disconnected: {websocket.client}")
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}", exc_info=True)
        manager.disconnect(websocket)
