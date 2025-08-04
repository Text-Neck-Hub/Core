

from typing import List
from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:

            try:
                await connection.send_text(message)
            except RuntimeError as e:
                print(f"메시지 전송 중 오류 발생: {e}, 연결 끊음")
                self.disconnect(connection)
            except Exception as e:
                print(f"알 수 없는 오류 발생: {e}, 연결 끊음")
                self.disconnect(connection)


manager = ConnectionManager()
