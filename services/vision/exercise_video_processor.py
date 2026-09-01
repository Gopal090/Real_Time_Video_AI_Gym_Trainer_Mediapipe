import os
import time
import threading
import cv2
import numpy as np
import mediapipe as mp
import av
from streamlit_webrtc import VideoProcessorBase
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

from detectors.squats import SquatDetector
from detectors.pushup import PushUpDetector
from detectors.biceps_curl import BicepCurlDetector
from detectors.lunges import LungesDetector
from detectors.shoulder_press import ShoulderPressDetector
from services.config.workout_config import POSE_CONNECTIONS


_GLOBAL_LANDMARKER = None
_LANDMARKER_LOCK = threading.Lock()


def get_shared_landmarker():
    global _GLOBAL_LANDMARKER
    if _GLOBAL_LANDMARKER is None:
        with _LANDMARKER_LOCK:
            if _GLOBAL_LANDMARKER is None:
                current_file_dir = os.path.dirname(os.path.abspath(__file__))
                project_root = os.path.abspath(os.path.join(current_file_dir, "..", ".."))
                model_path = os.path.join(project_root, "ml_models", "pose_landmarker_full.task")

                if not os.path.exists(model_path):
                    model_path = os.path.join(os.getcwd(), "ml_models", "pose_landmarker_full.task")

                base_options = python.BaseOptions(model_asset_path=model_path)

                options = vision.PoseLandmarkerOptions(
                    base_options=base_options,
                    running_mode=vision.RunningMode.IMAGE,
                    min_pose_detection_confidence=0.5,
                    min_tracking_confidence=0.5,
                    min_pose_presence_confidence=0.5,
                    output_segmentation_masks=False
                )

                _GLOBAL_LANDMARKER = vision.PoseLandmarker.create_from_options(options)
    return _GLOBAL_LANDMARKER


class VideoProcessor(VideoProcessorBase):
    def __init__(self):
        self._lock = threading.Lock()
        self._latest_metrics = None
        self._exercise_type = "squats"

        current_file_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.abspath(os.path.join(current_file_dir, "..", ".."))
        model_path = os.path.join(project_root, "ml_models", "pose_landmarker_full.task")

        if not os.path.exists(model_path):
            model_path = os.path.join(os.getcwd(), "ml_models", "pose_landmarker_full.task")

        base_options = python.BaseOptions(model_asset_path=model_path)

        options = vision.PoseLandmarkerOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.IMAGE,
            min_pose_detection_confidence=0.5,
            min_tracking_confidence=0.5,
            min_pose_presence_confidence=0.5,
            output_segmentation_masks=False
        )

        try:
            self._landmarker = vision.PoseLandmarker.create_from_options(options)
        except Exception as e:
            print(f"Error creating per-instance PoseLandmarker: {e}")
            self._landmarker = None

        self._detectors = {
            "squats": SquatDetector(),
            "pushups": PushUpDetector(),
            "bicep_curls": BicepCurlDetector(),
            "lunges": LungesDetector(),
            "shoulder_press": ShoulderPressDetector(),
        }

        self._frame_timestamp_ms = 0

    def set_latest_metrics(self, metrics):
        with self._lock:
            self._latest_metrics = metrics.copy() if metrics else None

    def get_latest_metrics(self):
        with self._lock:
            return None if self._latest_metrics is None else self._latest_metrics.copy()

    def set_exercise(self, exercise_type):
        with self._lock:
            self._exercise_type = exercise_type

    def get_exercise(self):
        with self._lock:
            return self._exercise_type

    def _draw_skeleton(self, img, landmarks):
        h, w = img.shape[:2]
        for start_idx, end_idx in POSE_CONNECTIONS:
            if start_idx < len(landmarks) and end_idx < len(landmarks):
                p1 = landmarks[start_idx]
                p2 = landmarks[end_idx]

                if p1.visibility > 0.2 and p2.visibility > 0.2:
                    cv2.line(
                        img,
                        (int(p1.x * w), int(p1.y * h)),
                        (int(p2.x * w), int(p2.y * h)),
                        (0, 255, 0),
                        4
                    )

        for lm in landmarks:
            if lm.visibility > 0.2:
                cv2.circle(
                    img,
                    (int(lm.x * w), int(lm.y * h)),
                    6,
                    (255, 0, 0),
                    -1
                )
        return img

    def _draw_no_pose_warnings(self, img):
        cv2.putText(
            img,
            "NO POSE DETECTED",
            (30, 50),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 0, 255),
            2,
            cv2.LINE_AA,
        )

        cv2.putText(
            img,
            "PLEASE FACE THE CAMERA",
            (30, 100),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 0, 255),
            2,
            cv2.LINE_AA,
        )

    def _draw_overlays(self, img, metrics, ex_type):
        if not metrics:
            return

        if ex_type == "squats":
            self._draw_squats_overlays(img, metrics)
        elif ex_type == "pushups":
            self._draw_pushup_overlays(img, metrics)
        elif ex_type == "lunges":
            self._draw_lunge_overlays(img, metrics)
        elif ex_type == "bicep_curls":
            self._draw_curl_overlays(img, metrics)
        elif ex_type == "shoulder_press":
            self._draw_press_overlays(img, metrics)

    def _draw_squats_overlays(self, img, metrics):
        h, _ = img.shape[:2]
        status = metrics.get("depth_status", "N/A")
        cv2.putText(
            img,
            f"DEPTH : {status}",
            (20, h - 20),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0),
            2,
        )

    def _draw_pushup_overlays(self, img, metrics):
        h, _ = img.shape[:2]
        body = metrics.get("body_alignment", "N/A")
        hip = metrics.get("hip_status", "N/A")
        cv2.putText(
            img,
            f"BODY : {body} | {hip}",
            (20, h - 20),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0),
            2,
        )

    def _draw_curl_overlays(self, img, metrics):
        h, _ = img.shape[:2]
        swing = metrics.get("swing_status", "N/A")
        cv2.putText(
            img,
            f"SWING : {swing}",
            (20, h - 20),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0),
            2,
        )

    def _draw_press_overlays(self, img, metrics):
        h, _ = img.shape[:2]
        ext = metrics.get("extension_status", "N/A")
        back = metrics.get("back_arc_status", "N/A")
        cv2.putText(
            img,
            f"EXT : {ext} | BACK:{back}",
            (20, h - 20),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0),
            2,
        )

    def _draw_lunge_overlays(self, img, metrics):
        h, _ = img.shape[:2]
        balance = metrics.get("balance_status", "N/A")
        cv2.putText(
            img,
            f"BALANCE : {balance}",
            (20, h - 20),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0),
            2,
        )

    def recv(self, frame):
        try:
            image = frame.to_ndarray(format="bgr24")
            image = cv2.flip(image, 1)
            image = np.ascontiguousarray(image)

            mp_image = mp.Image(
                image_format=mp.ImageFormat.SRGB,
                data=cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            )

            result = None
            if self._landmarker is not None:
                try:
                    result = self._landmarker.detect(mp_image)
                except Exception:
                    result = None

            if result and result.pose_landmarks and len(result.pose_landmarks) > 0:
                landmarks = result.pose_landmarks[0]
                self._draw_skeleton(image, landmarks)

                ex_type = self.get_exercise()
                detector = self._detectors.get(ex_type)
                if detector:
                    metrics = detector.process(landmarks)
                    metrics["pose_detected"] = True
                    self._draw_overlays(image, metrics, ex_type)
                    self.set_latest_metrics(metrics)
            else:
                self._draw_no_pose_warnings(image)
                with self._lock:
                    if self._latest_metrics is not None:
                        self._latest_metrics["pose_detected"] = False
                    else:
                        self._latest_metrics = {"pose_detected": False}

            return av.VideoFrame.from_ndarray(image, format="bgr24")
        except Exception:
            return frame


