import time


class CommandEncoder:
    def __init__(self, face_gain_mrad: int, face_deadband: float):
        self.face_gain_mrad = int(face_gain_mrad)
        self.face_deadband = float(face_deadband)
        self._crouching = False
        self._arms_up = False
        self._last_tpose_time = 0.0

    # gesture → command
    # DRIVE,<mm/s>,<mrad/s> is a direct-teleop command that bypasses the queue
    # and needs to be re-sent at ≥2 Hz to feed the 500 ms DRIVE watchdog.
    # JUMP is an impulse queue command; the caller must rate-limit it via the
    # debouncer's edge-triggered output.
    GESTURE_DRIVE_LABELS = {"Zero", "Five", "PointLeft", "PointRight"}

    def encode_gesture(self, label):
        mapping = {
            "Zero":       "DRIVE,0,0",
            "Five":       "DRIVE,250,0",
            "PointLeft":  "DRIVE,0,600",
            "PointRight": "DRIVE,0,-600",
            "Thumb_up":   "JUMP",
        }
        return mapping.get(label)

    def encode_stunt(self, event):
        if not event:
            # pose lost — treat as arms dropped, so a subsequent arms_up → drop
            # cycle can fire JUMP again (runner never emits arms_up active=False).
            if self._arms_up:
                self._arms_up = False
                return "JUMP"
            return None

        kind = event.get("kind")
        now = time.monotonic()

        if kind == "crouch":
            active = bool(event.get("active"))
            # falling edge of arms_up when pose now says "crouch" (or recovery):
            # runner never emits arms_up=False, so detect the drop here.
            if self._arms_up and kind != "arms_up":
                self._arms_up = False
                # prefer firing JUMP over the crouch transition on the same frame
                return "JUMP"
            if active and not self._crouching:
                self._crouching = True
                return "DECREASELEGLENGTH,3"
            if not active and self._crouching:
                self._crouching = False
                return "INCREASELEGLENGTH,3"
            return None

        if kind == "arms_up":
            active = bool(event.get("active"))
            if self._arms_up and not active:
                self._arms_up = False
                return "JUMP"
            self._arms_up = active
            return None

        if kind == "tpose":
            if self._arms_up:
                # T-pose reached with hands up: treat it as a drop edge too
                self._arms_up = False
                return "JUMP"
            if now - self._last_tpose_time > 6.0:
                self._last_tpose_time = now
                return "CROSSLEG,0,5"

        return None

    def encode_face(self, event):
        if not event:
            return "YAWRATE,0"

        dx = float(event.get("dx", 0.0))
        if abs(dx) < self.face_deadband:
            return "YAWRATE,0"

        mrad = int(-self.face_gain_mrad * dx)
        mrad = max(-4500, min(4500, mrad))
        return f"YAWRATE,{mrad}"
