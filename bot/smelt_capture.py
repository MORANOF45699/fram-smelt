"""
smelt_capture.py - ชั้นจับภาพ เลือกได้ 2 แบบผ่าน config.CAPTURE_MODE

  "screen" (เดิม)  - จับจากหน้าจอด้วย mss
                     เกมต้องอยู่บนจอ ไม่โดนหน้าต่างอื่นทับ

  "window"        - จับจากหน้าต่างเกมตรง ๆ ด้วย Windows Graphics Capture
                     เอาหน้าต่างอื่นทับได้ / จอดเกมไว้นอกจอได้
                     แต่ "ย่อ (minimize) ไม่ได้" — Windows หยุด render หน้าต่างที่ย่อ

ทั้งสองแบบคืนภาพเป็น BGRA แบบเดียวกับ mss → ตัว detector ใช้ต่อได้เลย
"""

import threading
import time

import numpy as np

import config

_warned = {"no_frame": False}


class ScreenCapture:
    """จับจากหน้าจอ (mss) — พฤติกรรมเดิมทุกอย่าง"""

    mode = "screen"

    def __init__(self):
        import mss
        self._sct = mss.mss()
        self.monitors = self._sct.monitors

    def grab(self, region):
        return np.array(self._sct.grab(region))

    def ready(self):
        return True

    def close(self):
        try:
            self._sct.close()
        except Exception:
            pass

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()


class WindowCapture:
    """
    จับจากหน้าต่างเกมด้วย Windows Graphics Capture
    เปิด session ค้างไว้ เก็บเฟรมล่าสุดไว้ในหน่วยความจำ แล้ว crop ตาม region ที่ขอ
    """

    mode = "window"

    def __init__(self, hwnd):
        from windows_capture import WindowsCapture, Frame, InternalCaptureControl

        self.hwnd = hwnd
        self._frame = None
        self._lock = threading.Lock()
        self.monitors = [
            {"left": config.SCREEN_LEFT, "top": config.SCREEN_TOP,
             "width": config.SCREEN_W, "height": config.SCREEN_H},
            {"left": config.SCREEN_LEFT, "top": config.SCREEN_TOP,
             "width": config.SCREEN_W, "height": config.SCREEN_H},
        ]

        cap = WindowsCapture(cursor_capture=False, draw_border=False,
                             window_hwnd=hwnd)

        @cap.event
        def on_frame_arrived(frame: Frame, control: InternalCaptureControl):
            with self._lock:
                self._frame = frame.frame_buffer.copy()   # BGRA

        @cap.event
        def on_closed():
            with self._lock:
                self._frame = None

        self._ctrl = cap.start_free_threaded()
        self._wait_first_frame()

    def _wait_first_frame(self, timeout=5.0):
        t0 = time.time()
        while time.time() - t0 < timeout:
            with self._lock:
                if self._frame is not None:
                    return True
            time.sleep(0.05)
        return False

    def ready(self):
        with self._lock:
            return self._frame is not None

    def grab(self, region):
        with self._lock:
            frame = None if self._frame is None else self._frame

            if frame is None:
                if not _warned["no_frame"]:
                    print("[capture] ⚠ ยังไม่ได้เฟรมจากหน้าต่างเกม "
                          "(เกมถูกย่อ? WGC จับหน้าต่างที่ย่อไม่ได้)")
                    _warned["no_frame"] = True
                return np.zeros((region["height"], region["width"], 4), np.uint8)
            _warned["no_frame"] = False

            fh, fw = frame.shape[:2]
            # region เป็นพิกัดจอ → แปลงเป็นพิกัดในเฟรมของหน้าต่าง
            sx = fw / config.SCREEN_W
            sy = fh / config.SCREEN_H
            x = int(round((region["left"] - config.SCREEN_LEFT) * sx))
            y = int(round((region["top"] - config.SCREEN_TOP) * sy))
            w = max(1, int(round(region["width"] * sx)))
            h = max(1, int(round(region["height"] * sy)))

            x = max(0, min(x, fw - 1))
            y = max(0, min(y, fh - 1))
            w = min(w, fw - x)
            h = min(h, fh - y)
            return frame[y:y + h, x:x + w].copy()

    def close(self):
        try:
            self._ctrl.stop()
        except Exception:
            pass

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()


def open_capture():
    """เปิดตัวจับภาพตาม config.CAPTURE_MODE (ล้มเหลว → ถอยกลับไปใช้ mss)"""
    if getattr(config, "CAPTURE_MODE", "screen") != "window":
        return ScreenCapture()

    import smelt_input as inp
    hwnd = inp._find_game_hwnd()
    if not hwnd:
        print("[capture] ⚠ หาหน้าต่างเกมไม่เจอ — ใช้โหมดจับหน้าจอแทน")
        return ScreenCapture()
    try:
        cap = WindowCapture(hwnd)
    except Exception as e:
        print(f"[capture] ⚠ เปิด Windows Graphics Capture ไม่ได้ ({e}) — ใช้โหมดจับหน้าจอแทน")
        return ScreenCapture()
    if not cap.ready():
        cap.close()
        print("[capture] ⚠ ไม่ได้เฟรมจากหน้าต่างเกม (เกมถูกย่ออยู่?) — ใช้โหมดจับหน้าจอแทน")
        return ScreenCapture()
    print(f"[capture] ✓ โหมดจับหน้าต่างเกม (hwnd={hwnd}) — เอาหน้าต่างอื่นทับได้")
    return cap
