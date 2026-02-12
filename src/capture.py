import mss
import numpy as np
import cv2

class ScreenCapture:
    def __init__(self):
        # Initial ROI (default to a small area or monitor 1)
        self.roi = {"top": 0, "left": 0, "width": 800, "height": 600}

    def set_roi(self, left, top, width, height):
        self.roi = {"top": int(top), "left": int(left), "width": int(width), "height": int(height)}

    def capture(self):
        # mss is not thread-safe, so we create a new instance (or use context manager) 
        # each time if we are running in threads, or just use with block.
        # Although instantiating mss every frame has overhead, it's safer for this simple threading model.
        # A better approach for high performance might be one sct per thread.
        try:
            with mss.mss() as sct:
                img = np.array(sct.grab(self.roi))
                # BGRA to BGR
                return cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
        except Exception as e:
            print(f"Capture error: {e}")
            return None
