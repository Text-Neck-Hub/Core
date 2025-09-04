
import json
import uuid
import asyncio
import threading
import subprocess
from typing import Dict, List, Optional


class PopenWorker:
    def __init__(self, cmd: List[str], env: Optional[dict] = None):
        self.proc = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, bufsize=1, close_fds=True, start_new_session=True, env=env
        )
        self.lock = threading.Lock()
        self.pending: Dict[str, asyncio.Future] = {}
        self._stop = threading.Event()
        self.t_out = threading.Thread(target=self._read_stdout, daemon=True)
        self.t_err = threading.Thread(target=self._drain_stderr, daemon=True)
        self.t_out.start()
        self.t_err.start()

    def _read_stdout(self):
        while not self._stop.is_set():
            line = self.proc.stdout.readline()
            if not line:
                if self.proc.poll() is not None:
                    for fid, fut in list(self.pending.items()):
                        if not fut.done():
                            fut.set_result(
                                {"id": fid, "ok": False, "error": "worker_exited"})
                    self.pending.clear()
                    break
                continue
            try:
                msg = json.loads(line.strip())
                fid = msg.get("id")
                if fid and fid in self.pending:
                    fut = self.pending.pop(fid)
                    if not fut.done():
                        fut.set_result(msg)
            except Exception:
                pass

    def _drain_stderr(self):
        for _ in self.proc.stderr:
            pass
        # TODO: 로깅 시스템에 연결

    async def ask(self, image_b64: str, expect_gray: bool, timeout: float = 0.5) -> dict:
        fid = uuid.uuid4().hex
        loop = asyncio.get_running_loop()
        fut = loop.create_future()
        self.pending[fid] = fut

        req = {"id": fid, "image_b64": image_b64, "gray": expect_gray}
        payload = json.dumps(req) + "\n"
        try:
            with self.lock:
                self.proc.stdin.write(payload)
                self.proc.stdin.flush()
        except Exception:
            if fid in self.pending and not self.pending[fid].done():
                self.pending[fid].set_result(
                    {"id": fid, "ok": False, "error": "write_failed"})
            return await fut

        try:
            return await asyncio.wait_for(fut, timeout=timeout)
        except asyncio.TimeoutError:
            if fid in self.pending and not self.pending[fid].done():
                self.pending[fid].set_result(
                    {"id": fid, "ok": False, "error": "timeout"})
                self.pending.pop(fid, None)
            return {"id": fid, "ok": False, "error": "timeout"}

    def is_alive(self) -> bool:
        return self.proc.poll() is None

    def stop(self):
        self._stop.set()
        try:
            if self.is_alive():
                self.proc.terminate()
        except Exception:
            pass
