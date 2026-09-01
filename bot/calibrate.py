"""
calibrate.py - จับพิกัดและ template ให้บอทแปรรูป

วิธีใช้: รัน calibrate.bat แล้วสลับไปหน้าเกม กดปุ่มตามนี้

  ที่เสา GARAGE (กด E ให้เมนู SYSTEM GARAGE ขึ้นก่อน):
     [1] กด 1  -> garage_menu.png   (ยืนยันว่าเมนู GARAGE เปิด)

  เปิดท้ายรถแล้ว (กด L ให้หน้า INVENTORY | SECONDARY ขึ้น):
     [2] กด 2  -> trunk_open.png    (จำเป็น! ไม่มีอันนี้บอทจะไม่คลิกเลย)
     [3] ชี้ไอคอนแร่ดิบในท้ายรถ กด 3   -> ore_template.png
     [4] ชี้ไอคอนแท่งที่โพเสร็จ กด 4    -> bar_template.png
     [5] ชี้ช่องว่างฝั่งกระเป๋า กด 5     -> DROP_TO_INVENTORY
     [6] ชี้ช่องว่างฝั่งท้ายรถ กด 6      -> DROP_TO_TRUNK

  ลากของจนขึ้น dialog ใส่จำนวน:
     [7] ชี้ปุ่ม Max กด 7   -> BTN_MAX
     [8] ชี้ปุ่ม O ยืนยัน กด 8 -> BTN_CONFIRM

  ตอนกำลังแปรรูป (แถบ Processing ขึ้นอยู่):
     [9] กด 9  -> process_bar.png

     [0] บันทึกแล้วออก
"""

import ctypes
import json
import os
import sys

import cv2
import keyboard
import mss
import numpy as np

sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
TEMPLATE_DIR = os.path.join(ROOT, "templates")
os.makedirs(TEMPLATE_DIR, exist_ok=True)

ICON_SIZE = 70      # ขนาด crop รอบ cursor ตอนถ่ายไอคอนไอเทม


class POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]


def get_cursor():
    p = POINT()
    ctypes.windll.user32.GetCursorPos(ctypes.byref(p))
    return p.x, p.y


def main():
    data = {}
    print(__doc__)

    with mss.mss() as sct:
        import config

        def rec(key, name):
            pos = get_cursor()
            data[name] = pos
            print(f"[{key}] {name} = {pos}")

        def save_icon(key, filename, label):
            x, y = get_cursor()
            half = ICON_SIZE // 2
            region = {"left": x - half, "top": y - half,
                      "width": ICON_SIZE, "height": ICON_SIZE}
            bgr = cv2.cvtColor(np.array(sct.grab(region)), cv2.COLOR_BGRA2BGR)
            path = os.path.join(TEMPLATE_DIR, filename)
            cv2.imwrite(path, bgr)
            print(f"[{key}] บันทึก {label} ที่ ({x},{y}) -> {filename}")

        def crop_to_text(bgr, margin=4):
            """ตัดเหลือเฉพาะตัวอักษรสว่าง - พื้นหลังเกมมองทะลุแผงเมนูได้
            ถ้าเก็บทั้ง region ไว้ พอไปยืนที่อื่นพื้นหลังเปลี่ยน จะ match ไม่ติด"""
            gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
            mask = cv2.threshold(gray, 170, 255, cv2.THRESH_BINARY)[1]
            pts = cv2.findNonZero(mask)
            if pts is None:
                return bgr
            x, y, w, h = cv2.boundingRect(pts)
            H, W = bgr.shape[:2]
            return bgr[max(0, y - margin):min(H, y + h + margin),
                       max(0, x - margin):min(W, x + w + margin)]

        def save_region(key, region_name, filename, label, tight=True):
            bgr = cv2.cvtColor(np.array(sct.grab(getattr(config, region_name))),
                               cv2.COLOR_BGRA2BGR)
            if tight:
                bgr = crop_to_text(bgr)
            path = os.path.join(TEMPLATE_DIR, filename)
            cv2.imwrite(path, bgr)
            print(f"[{key}] บันทึก {label} {bgr.shape[1]}x{bgr.shape[0]} -> {filename}")

        keyboard.add_hotkey("1", lambda: save_region(
            "1", "GARAGE_MENU_REGION", "garage_menu.png", "เมนู SYSTEM GARAGE"))
        keyboard.add_hotkey("2", lambda: save_region(
            "2", "TRUNK_CHECK_REGION", "trunk_open.png", "หน้าท้ายรถ"))
        keyboard.add_hotkey("3", lambda: save_icon(
            "3", "ore_template.png", "ไอคอนแร่ดิบ"))
        keyboard.add_hotkey("4", lambda: save_icon(
            "4", "bar_template.png", "ไอคอนแท่งที่โพเสร็จ"))
        keyboard.add_hotkey("5", lambda: rec("5", "DROP_TO_INVENTORY"))
        keyboard.add_hotkey("6", lambda: rec("6", "DROP_TO_TRUNK"))
        keyboard.add_hotkey("7", lambda: rec("7", "BTN_MAX"))
        keyboard.add_hotkey("8", lambda: rec("8", "BTN_CONFIRM"))
        keyboard.add_hotkey("9", lambda: save_region(
            "9", "PROCESS_BAR_REGION", "process_bar.png", "แถบ Processing",
            tight=False))

        print("รอการกดปุ่ม... (กด 0 เพื่อบันทึกและออก)")
        keyboard.wait("0")

    path = os.path.join(TEMPLATE_DIR, "calibration.json")
    existing = {}
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            existing = json.load(f)
    existing.update(data)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(existing, f, indent=2)
    print(f"บันทึก {path} แล้ว: {existing}")


if __name__ == "__main__":
    main()
