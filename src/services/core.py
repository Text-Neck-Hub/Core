import cv2
import json
import base64
import numpy as np
import mediapipe as mp
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from typing import Dict, Any

mp_drawing = mp.solutions.drawing_utils
mp_face_mesh = mp.solutions.face_mesh
mp_pose = mp.solutions.pose


def calculate_angle(a, b, c):
    ba = np.array(a) - np.array(b)
    bc = np.array(c) - np.array(b)
    cosine_angle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg(bc))
    angle = np.arccos(np.clip(cosine_angle, -1.0, 1.0))
    return np.degrees(angle)


def process_image_frame(img_bytes_b64: str) -> Dict[str, Any]:
    with mp_face_mesh.FaceMesh(static_image_mode=False, max_num_faces=1) as face_mesh, \
            mp_pose.Pose(static_image_mode=False, model_complexity=1) as pose:

        img_bytes = base64.b64decode(img_bytes_b64)
        np_arr = np.frombuffer(img_bytes, np.uint8)
        img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

        if img is None:
            return {
                'has_angle': False,
                'img': img_bytes_b64
            }

        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        face_results = face_mesh.process(img_rgb)
        pose_results = pose.process(img_rgb)

        nose = None
        left_shoulder = None
        right_shoulder = None
        h, w, _ = img.shape

        if face_results.multi_face_landmarks:
            face_landmarks = face_results.multi_face_landmarks[0]
            nose_landmark = face_landmarks.landmark[1]
            nose = (int(nose_landmark.x * w), int(nose_landmark.y * h))

        if pose_results.pose_landmarks:
            left_shoulder_lm = pose_results.pose_landmarks.landmark[
                mp.solutions.pose.PoseLandmark.LEFT_SHOULDER]
            right_shoulder_lm = pose_results.pose_landmarks.landmark[
                mp.solutions.pose.PoseLandmark.RIGHT_SHOULDER]

            left_shoulder = (int(left_shoulder_lm.x * w),
                             int(left_shoulder_lm.y * h))
            right_shoulder = (int(right_shoulder_lm.x * w),
                              int(right_shoulder_lm.y * h))

        angle = None
        if nose and left_shoulder and right_shoulder:
            if nose != (0, 0) and left_shoulder != (0, 0) and right_shoulder != (0, 0):
                angle = calculate_angle(left_shoulder, nose, right_shoulder)

                cv2.circle(img, nose, 5, (0, 255, 255), -1)
                cv2.circle(img, left_shoulder, 5, (255, 0, 0), -1)
                cv2.circle(img, right_shoulder, 5, (0, 0, 255), -1)

                cv2.line(img, left_shoulder, nose, (0, 255, 0), 2)
                cv2.line(img, right_shoulder, nose, (0, 255, 0), 2)

                cv2.putText(img, f"Angle: {angle:.1f}", (nose[0] + 10, nose[1] + 20),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2, cv2.LINE_AA)

        _, buffer = cv2.imencode('.jpg', img)
        img_b64_output = base64.b64encode(buffer).decode('utf-8')

        return {
            'has_angle': angle is not None,
            'angle_value': angle,
            'img': img_b64_output
        }
