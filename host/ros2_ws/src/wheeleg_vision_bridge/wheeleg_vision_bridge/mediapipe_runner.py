import math

import cv2 as cv
import mediapipe as mp


def _dist(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


class MediaPipeRunner:
    def __init__(self, confidence: float):
        self.confidence = float(confidence)
        self._hands = None
        self._pose = None
        self._face = None

    def process(self, frame, mode: str):
        if mode == "gesture":
            return self._process_gesture(frame)
        if mode == "stunt":
            return self._process_stunt(frame)
        if mode == "face":
            return self._process_face(frame)
        return None

    def _ensure_hands(self):
        if self._hands is None:
            self._hands = mp.solutions.hands.Hands(
                static_image_mode=False,
                max_num_hands=1,
                min_detection_confidence=self.confidence,
                min_tracking_confidence=self.confidence,
            )

    def _ensure_pose(self):
        if self._pose is None:
            self._pose = mp.solutions.pose.Pose(
                static_image_mode=False,
                smooth_landmarks=True,
                min_detection_confidence=self.confidence,
                min_tracking_confidence=self.confidence,
            )

    def _ensure_face(self):
        if self._face is None:
            self._face = mp.solutions.face_detection.FaceDetection(
                min_detection_confidence=self.confidence
            )

    def _process_gesture(self, frame):
        self._ensure_hands()
        rgb = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
        results = self._hands.process(rgb)
        if not results.multi_hand_landmarks:
            return None

        points = [(lm.x, lm.y) for lm in results.multi_hand_landmarks[0].landmark]
        fingers = self._fingers_up(points)
        count = sum(fingers)

        if count == 0:
            return {"label": "Zero"}
        if count == 5:
            return {"label": "Five"}

        thumb_tip = points[4]
        index_tip = points[8]
        wrist = points[0]
        if count == 1 and fingers[1]:
            if index_tip[0] < wrist[0] - 0.12:
                return {"label": "PointLeft"}
            if index_tip[0] > wrist[0] + 0.12:
                return {"label": "PointRight"}
            return {"label": "One"}

        if thumb_tip[1] < min(points[8][1], points[12][1], points[16][1], points[20][1]):
            return {"label": "Thumb_up"}

        return {"label": None}

    def _fingers_up(self, points):
        tip_ids = [4, 8, 12, 16, 20]
        fingers = [0]
        for idx in range(1, 5):
            tip = points[tip_ids[idx]]
            pip = points[tip_ids[idx] - 2]
            fingers.append(1 if tip[1] < pip[1] else 0)

        thumb_tip = points[4]
        thumb_ip = points[3]
        index_mcp = points[5]
        fingers[0] = 1 if _dist(thumb_tip, index_mcp) > _dist(thumb_ip, index_mcp) else 0
        return fingers

    def _process_stunt(self, frame):
        self._ensure_pose()
        rgb = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
        results = self._pose.process(rgb)
        if not results.pose_landmarks:
            return None

        lm = results.pose_landmarks.landmark
        left_shoulder, right_shoulder = lm[11], lm[12]
        left_wrist, right_wrist = lm[15], lm[16]
        left_hip, right_hip = lm[23], lm[24]
        left_knee, right_knee = lm[25], lm[26]

        shoulder_y = (left_shoulder.y + right_shoulder.y) * 0.5
        wrist_y = (left_wrist.y + right_wrist.y) * 0.5
        hip_y = (left_hip.y + right_hip.y) * 0.5
        knee_y = (left_knee.y + right_knee.y) * 0.5

        tpose = (
            abs(left_wrist.y - shoulder_y) < 0.12
            and abs(right_wrist.y - shoulder_y) < 0.12
            and left_wrist.x > left_shoulder.x
            and right_wrist.x < right_shoulder.x
        )
        if tpose:
            return {"kind": "tpose"}

        crouch = hip_y > knee_y - 0.05
        if crouch:
            return {"kind": "crouch", "active": True}

        arms_up = wrist_y < shoulder_y - 0.12
        if arms_up:
            return {"kind": "arms_up", "active": True}

        return {"kind": "crouch", "active": False} if not crouch else None

    def _process_face(self, frame):
        self._ensure_face()
        rgb = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
        results = self._face.process(rgb)
        if not results.detections:
            return None

        h, w = frame.shape[:2]
        best = max(
            results.detections,
            key=lambda d: d.location_data.relative_bounding_box.width
            * d.location_data.relative_bounding_box.height,
        )
        bbox = best.location_data.relative_bounding_box
        cx = (bbox.xmin + bbox.width * 0.5) * w
        dx = (cx - w * 0.5) / (w * 0.5)
        return {"dx": dx}
