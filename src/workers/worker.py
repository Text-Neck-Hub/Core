
import os
import sys
import json
import base64
import traceback
import numpy as np
import cv2
import mediapipe as mp


os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
try:
    cv2.setNumThreads(1)
except Exception:
    pass


mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(
    static_image_mode=False,
    max_num_faces=1,
    refine_landmarks=False,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5,
)


def process_one(req: dict) -> dict:
    fid = req.get("id")
    try:
        buf = np.frombuffer(base64.b64decode(req["image_b64"]), np.uint8)
        bgr = cv2.imdecode(buf, cv2.IMREAD_COLOR)
        if bgr is None:
            return {"id": fid, "ok": False, "error": "decode_failed"}

        if req.get("gray"):
            g = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
            bgr = cv2.cvtColor(g, cv2.COLOR_GRAY2BGR)

        rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
        res = face_mesh.process(rgb)

        pts = []
        if res.multi_face_landmarks:
            lm = res.multi_face_landmarks[0]
            for p in lm.landmark:
                pts.append([round(p.x, 4), round(p.y, 4), round(p.z, 4)])

        return {"id": fid, "ok": True, "n": len(pts), "points": pts}
    except Exception:
        return {"id": fid, "ok": False, "error": "exception", "trace": traceback.format_exc()[:800]}


def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
            if req.get("type") == "ping":
                print(json.dumps({"type": "pong"}), flush=True)
                continue
            resp = process_one(req)
        except Exception:
            resp = {"ok": False, "error": "bad_request"}
        print(json.dumps(resp), flush=True)


if __name__ == "__main__":
    main()
