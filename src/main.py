import base64
import cv2
import numpy as np
from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse
import mediapipe as mp
import math
import json

app = FastAPI()
mp_drawing = mp.solutions.drawing_utils
mp_face_mesh = mp.solutions.face_mesh
mp_pose = mp.solutions.pose

html = """
<!DOCTYPE html>
<html>
    <head>
        <title>WebSocket Image Stream</title>
    </head>
    <body>
        <h1>WebSocket Image Stream with MediaPipe</h1>
        <video id="video" width="320" height="240" autoplay></video>
        <canvas id="canvas" width="320" height="240"></canvas>
        <script>
            const video = document.getElementById('video');
            const canvas = document.getElementById('canvas');
            const ctx = canvas.getContext('2d');
            let ws;
            let lastImg = null;

            // Get webcam
            navigator.mediaDevices.getUserMedia({ video: true })
                .then(stream => {
                    video.srcObject = stream;
                    ws = new WebSocket("ws://localhost:8000/ws");
                    ws.onmessage = (event) => {
                        let data = JSON.parse(event.data);
                        if (data.has_angle) {
                            lastImg = new Image();
                            lastImg.onload = function() {
                                ctx.clearRect(0, 0, 320, 240); // 캔버스 초기화
                                ctx.drawImage(lastImg, 0, 0, 320, 240);
                            };
                            lastImg.src = 'data:image/jpeg;base64,' + data.img;
                        }
                    };
                    setInterval(() => {
                        ctx.drawImage(video, 0, 0, 320, 240); // 웹캠 프레임만 그림
                        let dataURL = canvas.toDataURL('image/jpeg');
                        let base64 = dataURL.split(',')[1];
                        ws.send(base64);
                    }, 100); // 10fps
                });
        </script>
    </body>
</html>
"""

def calculate_angle(a, b, c):
    # a, b, c: (x, y)
    ba = np.array(a) - np.array(b)
    bc = np.array(c) - np.array(b)
    cosine_angle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc))
    angle = np.arccos(np.clip(cosine_angle, -1.0, 1.0))
    return np.degrees(angle)

@app.get("/")
async def get():
    return HTMLResponse(html)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    with mp_face_mesh.FaceMesh(static_image_mode=False, max_num_faces=1) as face_mesh, \
         mp_pose.Pose(static_image_mode=False) as pose:
        while True:
            data = await websocket.receive_text()
            img_bytes = base64.b64decode(data)
            np_arr = np.frombuffer(img_bytes, np.uint8)
            img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
            if img is None:
                continue
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            face_results = face_mesh.process(img_rgb)
            pose_results = pose.process(img_rgb)

            # 어깨와 코 위치 추출
            nose = None
            left_shoulder = None
            right_shoulder = None
            h, w, _ = img.shape
            # 코: face mesh 1번
            if face_results.multi_face_landmarks:
                face_landmarks = face_results.multi_face_landmarks[0]
                nose_landmark = face_landmarks.landmark[1]
                nose = (int(nose_landmark.x * w), int(nose_landmark.y * h))
            # 어깨: pose 11(왼), 12(오)
            if pose_results.pose_landmarks:
                left = pose_results.pose_landmarks.landmark[11]
                right = pose_results.pose_landmarks.landmark[12]
                left_shoulder = (int(left.x * w), int(left.y * h))
                right_shoulder = (int(right.x * w), int(right.y * h))
            # 각도 계산 및 시각화
            angle = None
            if nose and left_shoulder and right_shoulder:
                angle = calculate_angle(left_shoulder, nose, right_shoulder)
                # 시각화
                cv2.circle(img, nose, 5, (0,255,0), -1)
                cv2.circle(img, left_shoulder, 5, (255,0,0), -1)
                cv2.circle(img, right_shoulder, 5, (0,0,255), -1)
                cv2.line(img, left_shoulder, nose, (255,255,0), 2)
                cv2.line(img, right_shoulder, nose, (255,255,0), 2)
                cv2.putText(img, f"Angle: {angle:.1f}", (nose[0]+10, nose[1]), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,255), 2)
            _, buffer = cv2.imencode('.jpg', img)
            img_b64 = base64.b64encode(buffer).decode('utf-8')
            # 각도 검출 여부와 이미지 함께 전송
            await websocket.send_text(json.dumps({
                'has_angle': angle is not None,
                'img': img_b64
            }))