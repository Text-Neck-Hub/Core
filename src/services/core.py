import cv2
import json
import base64
import numpy as np
import mediapipe as mp


mp_drawing = mp.solutions.drawing_utils
mp_face_mesh = mp.solutions.face_mesh
mp_pose = mp.solutions.pose


def calculate_angle(a, b, c):

    ba = np.array(a) - np.array(b)
    bc = np.array(c) - np.array(b)
    cosine_angle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc))
    angle = np.arccos(np.clip(cosine_angle, -1.0, 1.0))
    return np.degrees(angle)


async def predict_angle(data):

    with mp_face_mesh.FaceMesh(static_image_mode=False, max_num_faces=1) as face_mesh, \
            mp_pose.Pose(static_image_mode=False) as pose:

        img_bytes = base64.b64decode(data)
        np_arr = np.frombuffer(img_bytes, np.uint8)
        img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        if img is None:
            return json.dumps({
                'has_angle': angle is not None,
                'img': data
            })
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
            left = pose_results.pose_landmarks.landmark[11]
            right = pose_results.pose_landmarks.landmark[12]
            left_shoulder = (int(left.x * w), int(left.y * h))
            right_shoulder = (int(right.x * w), int(right.y * h))

        angle = None
        if nose and left_shoulder and right_shoulder:
            angle = calculate_angle(left_shoulder, nose, right_shoulder)

            cv2.circle(img, nose, 5, (0, 255, 0), -1)
            cv2.circle(img, left_shoulder, 5, (255, 0, 0), -1)
            cv2.circle(img, right_shoulder, 5, (0, 0, 255), -1)
            cv2.line(img, left_shoulder, nose, (255, 255, 0), 2)
            cv2.line(img, right_shoulder, nose, (255, 255, 0), 2)
            cv2.putText(img, f"Angle: {angle:.1f}", (
                nose[0]+10, nose[1]), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        _, buffer = cv2.imencode('.jpg', img)
        img_b64 = base64.b64encode(buffer).decode('utf-8')

        return json.dumps({
            'has_angle': angle is not None,
            'img': img_b64
        })
