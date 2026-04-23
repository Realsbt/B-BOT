from collections import deque


class Debouncer:
    def __init__(self, frames: int):
        self.frames = max(1, int(frames))
        self._items = deque(maxlen=self.frames)
        self._last_emitted = None

    def update(self, label):
        self._items.append(label)
        if label is None:
            self._last_emitted = None
            return None
        if len(self._items) < self.frames:
            return None
        if all(item == label for item in self._items) and label != self._last_emitted:
            self._last_emitted = label
            return label
        return None

    def reset(self):
        self._items.clear()
        self._last_emitted = None
