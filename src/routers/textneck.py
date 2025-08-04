
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from ..services.websocket_manager import manager
import logging
logger = logging.getLogger('prod')
textneck_router = APIRouter(prefix="/ws")


@textneck_router.websocket("/textneck/")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    logger.info(f'웹소켓 등장{websocket}🤖🤖🤖')
    try:
        while True:
            data = await websocket.receive_text()
            await manager.broadcast(f"나의 메시지: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await manager.broadcast("누군가 채팅방을 나갔어요. 🥲")
