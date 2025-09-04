
import os
import sys
import threading
from typing import List
from worker_manager import PopenWorker


class WorkerPool:
    def __init__(self, n: int):
        cmd = [sys.executable, "worker.py"]
        env = dict(os.environ)
        env.setdefault("OMP_NUM_THREADS", "1")
        env.setdefault("MKL_NUM_THREADS", "1")
        self.workers: List[PopenWorker] = [
            PopenWorker(cmd, env=env) for _ in range(n)]
        self._idx = 0
        self._lock = threading.Lock()

    def pick(self) -> PopenWorker:
        with self._lock:
            for _ in range(len(self.workers)):
                w = self.workers[self._idx % len(self.workers)]
                self._idx += 1
                if w.is_alive():
                    return w
            return self.workers[0]

    def shutdown(self):
        for w in self.workers:
            w.stop()
