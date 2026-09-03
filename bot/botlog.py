"""
botlog.py - เขียน log พร้อมเวลา และตัดไฟล์ไม่ให้โตไม่จำกัด

ทุก print ของบอทจะได้เวลานำหน้า เช่น
    [10:09:33] [เปิด] กด E ที่เสา GARAGE (ครั้งที่ 1)...

ไฟล์โตเกิน MAX_MB จะถูกย้ายไปเป็น bot_log.old.txt แล้วเริ่มไฟล์ใหม่
(เก็บไฟล์เก่าไว้ 1 รุ่น ไม่ให้กินดิสก์ไปเรื่อย ๆ)
"""

import os
import time

MAX_MB = 20


class TimestampedLog:
    """ไฟล์ log ที่ใส่เวลานำหน้าทุกบรรทัด ใช้แทน sys.stdout ได้เลย"""

    def __init__(self, path, max_mb=MAX_MB):
        self.path = path
        self.max_bytes = int(max_mb * 1024 * 1024)
        self._at_line_start = True
        os.makedirs(os.path.dirname(path), exist_ok=True)
        self._rotate_if_big()
        self._f = open(path, "a", encoding="utf-8", buffering=1)
        self._f.write(f"\n{'=' * 60}\n"
                      f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] เริ่มโปรแกรม\n"
                      f"{'=' * 60}\n")

    def _rotate_if_big(self):
        try:
            if os.path.getsize(self.path) < self.max_bytes:
                return
        except OSError:
            return
        old = self.path.replace(".txt", ".old.txt")
        try:
            if os.path.exists(old):
                os.remove(old)
            os.replace(self.path, old)
        except OSError:
            pass

    def write(self, text):
        if not text:
            return
        stamp = time.strftime("[%H:%M:%S] ")
        out = []
        for ch in text:
            if self._at_line_start and ch != "\n":
                out.append(stamp)
                self._at_line_start = False
            out.append(ch)
            if ch == "\n":
                self._at_line_start = True
        self._f.write("".join(out))

    def flush(self):
        try:
            self._f.flush()
        except ValueError:
            pass

    def isatty(self):
        return False
