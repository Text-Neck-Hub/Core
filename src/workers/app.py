import os
import json
import base64
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from worker_pool import WorkerPool

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")

app = FastAPI()
POOL: WorkerPool | None = None


class Session:
    def __init__(self, ws: WebSocket):
        self.ws = ws
        self.q = asyncio.Queue(maxsize=1)
        self.expect_gray = False
        self.running = True
        self.inflight = False

    async def recv_loop(self):
        while self.running:
            msg = await self.ws.receive()
            if (b := msg.get("bytes")) is not None:
                if self.q.full():
                    try:
                        _ = self.q.get_nowait()
                        self.q.task_done()
                    except asyncio.QueueEmpty:
                        pass
                await self.q.put(b)
            elif (t := msg.get("text")) is not None:
                try:
                    obj = json.loads(t)
                    if obj.get("type") == "config":
                        self.expect_gray = bool(obj.get("gray", False))
                    elif obj.get("type") == "ping":
                        await self.ws.send_text('{"type":"pong"}')
                except Exception:
                    pass

    async def infer_loop(self):
        while self.running:
            frame = await self.q.get()
            if self.inflight:

                self.q.task_done()
                continue
            self.inflight = True
            try:
                worker = POOL.pick()
                b64 = base64.b64encode(frame).decode("ascii")
                res = await worker.ask(b64, self.expect_gray, timeout=0.5)
                await self.ws.send_text(json.dumps({"type": "landmarks", **res}))
            except Exception as e:
                await self.ws.send_text(json.dumps({"type": "landmarks", "ok": False, "error": str(e)[:200]}))
            finally:
                self.inflight = False
                self.q.task_done()


@app.websocket("/ws/face")
async def ws_face(ws: WebSocket):
    await ws.accept()
    sess = Session(ws)
    t1 = asyncio.create_task(sess.recv_loop())
    t2 = asyncio.create_task(sess.infer_loop())
    try:
        await asyncio.gather(t1, t2)
    except WebSocketDisconnect:
        pass
    finally:
        sess.running = False
        try:
            await ws.close()
        except Exception:
            pass
