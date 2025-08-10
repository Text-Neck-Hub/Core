import cv2
import base64
import numpy as np
import mediapipe as mp
from typing import Dict, Any
import logging

logger = logging.getLogger('prod')


class CoreService:
    mp_drawing = mp.solutions.drawing_utils
    mp_face_mesh = mp.solutions.face_mesh
    mp_pose = mp.solutions.pose

    @staticmethod
    def _calculate_angle(a, b, c) -> float:
        ba = np.array(a, dtype=np.float32) - np.array(b, dtype=np.float32)
        bc = np.array(c, dtype=np.float32) - np.array(b, dtype=np.float32)
        denom = float(np.linalg.norm(ba) * np.linalg.norm(bc))
        if denom == 0.0:
            return 0.0
        cosine_angle = float(np.dot(ba, bc) / denom)
        angle = np.degrees(np.arccos(np.clip(cosine_angle, -1.0, 1.0)))
        return float(angle)

    @staticmethod
    def process_image_frame(img_bytes_b64: str) -> Dict[str, Any]:
        try:
            img_bytes = base64.b64decode(img_bytes_b64)
            np_arr = np.frombuffer(img_bytes, np.uint8)
            img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

            if img is None:
                return {
                    "has_angle": False,
                    "angle_value": None,
                    "neck_angle_deg": None,
                    "shoulder_y_diff_px": None,
                    "shoulder_y_avg_px": None,
                    "img": img_bytes_b64
                }

            img = cv2.flip(img, 1)
            h, w, _ = img.shape
            black_bg_img = np.zeros((h, w, 3), dtype=np.uint8)
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

            angle = None
            nose = None
            left_shoulder = None
            right_shoulder = None
            shoulder_y_diff = None
            shoulder_y_avg = None

            with CoreService.mp_face_mesh.FaceMesh(static_image_mode=False, max_num_faces=1) as face_mesh, \
                    CoreService.mp_pose.Pose(static_image_mode=False, model_complexity=1) as pose:

                face_results = face_mesh.process(img_rgb)
                pose_results = pose.process(img_rgb)

                mp_drawing = CoreService.mp_drawing
                mp_face_mesh = CoreService.mp_face_mesh

                if face_results.multi_face_landmarks:
                    spec = mp_drawing.DrawingSpec(
                        color=(0, 255, 128), thickness=1, circle_radius=1)
                    for face_landmarks in face_results.multi_face_landmarks:
                        mp_drawing.draw_landmarks(
                            image=black_bg_img,
                            landmark_list=face_landmarks,
                            connections=mp_face_mesh.FACEMESH_CONTOURS,
                            landmark_drawing_spec=spec,
                            connection_drawing_spec=spec
                        )
                    face_landmarks = face_results.multi_face_landmarks[0]
                    nose_lm = face_landmarks.landmark[1]
                    nose = (int(nose_lm.x * w), int(nose_lm.y * h))

                if pose_results.pose_landmarks:
                    left_shoulder_lm = pose_results.pose_landmarks.landmark[
                        CoreService.mp_pose.PoseLandmark.LEFT_SHOULDER
                    ]
                    right_shoulder_lm = pose_results.pose_landmarks.landmark[
                        CoreService.mp_pose.PoseLandmark.RIGHT_SHOULDER
                    ]
                    left_shoulder = (int(left_shoulder_lm.x * w),
                                     int(left_shoulder_lm.y * h))
                    right_shoulder = (int(right_shoulder_lm.x * w),
                                      int(right_shoulder_lm.y * h))
                    shoulder_y_diff = abs(left_shoulder[1] - right_shoulder[1])
                    shoulder_y_avg = (
                        left_shoulder[1] + right_shoulder[1]) / 2.0

                if nose and left_shoulder and right_shoulder:
                    if nose != (0, 0) and left_shoulder != (0, 0) and right_shoulder != (0, 0):
                        angle = CoreService._calculate_angle(
                            left_shoulder, nose, right_shoulder)
                        cv2.circle(black_bg_img, nose, 5, (0, 255, 0), -1)
                        cv2.circle(black_bg_img, left_shoulder,
                                   5, (0, 255, 0), -1)
                        cv2.circle(black_bg_img, right_shoulder,
                                   5, (0, 255, 0), -1)
                        cv2.line(black_bg_img, left_shoulder,
                                 nose, (0, 255, 0), 2)
                        cv2.line(black_bg_img, right_shoulder,
                                 nose, (0, 255, 0), 2)
                        cv2.putText(
                            black_bg_img, f"Angle: {angle:.1f}", (
                                nose[0] + 10, nose[1] + 20),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (
                                255, 255, 255), 2, cv2.LINE_AA
                        )

                if shoulder_y_diff is not None and shoulder_y_avg is not None:
                    cv2.putText(
                        black_bg_img, f"Y Diff: {shoulder_y_diff:.1f}", (
                            20, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,
                                                        255, 255), 2, cv2.LINE_AA
                    )
                    cv2.putText(
                        black_bg_img, f"Y Avg: {shoulder_y_avg:.1f}", (20, 60),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,
                                                        255, 255), 2, cv2.LINE_AA
                    )

            _, buffer = cv2.imencode(".jpg", black_bg_img)
            img_b64_output = base64.b64encode(buffer).decode("utf-8")

            return {
                "has_angle": angle is not None,
                "angle_value": float(angle) if angle is not None else None,
                "neck_angle_deg": float(angle) if angle is not None else None,
                "shoulder_y_diff_px": float(shoulder_y_diff) if shoulder_y_diff is not None else None,
                "shoulder_y_avg_px": float(shoulder_y_avg) if shoulder_y_avg is not None else None,
                "img": img_b64_output
            }
        except Exception as e:
            logger.error(f"process_image_frame error: {e}", exc_info=True)
            return {
                "has_angle": False,
                "angle_value": None,
                "neck_angle_deg": None,
                "shoulder_y_diff_px": None,
                "shoulder_y_avg_px": None,
                "img": img_bytes_b64
            }
