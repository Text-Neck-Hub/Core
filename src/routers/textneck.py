from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from ..connection.manager import manager
from ..services.core import process_image_frame

import logging
logger = logging.getLogger('prod')
textneck_router = APIRouter(prefix="/ws")


@textneck_router.websocket("/textneck/")
async def predict_textneck(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data_str = await websocket.receive_text()
            processed_data = process_image_frame(data_str)
            await websocket.send_json(processed_data)

    except WebSocketDisconnect:
        logger.info(f"Client disconnected: {websocket.client}")
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}", exc_info=True)
        manager.disconnect(websocket)
