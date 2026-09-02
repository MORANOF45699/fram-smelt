"""
config.py - ค่าพิกัด/ปุ่ม/เวลา ของ Smelt Bot (บอทแปรรูป)

พิกัดทั้งหมดเก็บเป็นสัดส่วนจอ (0.0-1.0) แล้วคูณขนาดจอจริงตอนรัน
→ ใช้ได้ทุกจอ 16:9 โดยไม่ต้องแก้

ค่าที่ปรับบ่อยอยู่ใน user_config.json (แก้ระหว่างบอทรันได้ มีผลทันที)
พิกัด/template ที่ต้อง calibrate อยู่ใน templates/calibration.json
"""

import json
import os
import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning,
                        message=".*mss.mss is deprecated.*")

import mss

# ===== ที่อยู่ไฟล์ =====
BOT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(BOT_DIR)
TEMPLATE_DIR = os.path.join(ROOT, "templates")
LOG_DIR = os.path.join(ROOT, "logs")
DEBUG_DIR = os.path.join(ROOT, "debug_images")
USER_CONFIG_PATH = os.path.join(ROOT, "user_config.json")
CALIBRATION_PATH = os.path.join(TEMPLATE_DIR, "calibration.json")

# ===== ขนาดจอ =====
with mss.mss() as _sct:
    _mon = _sct.monitors[1]
SCREEN_W = _mon["width"]
SCREEN_H = _mon["height"]
SCREEN_LEFT = _mon["left"]
SCREEN_TOP = _mon["top"]
SCALE = SCREEN_H / 1080.0


def _pt(fx, fy):
    return (int(SCREEN_LEFT + fx * SCREEN_W), int(SCREEN_TOP + fy * SCREEN_H))


def _region(fl, ft, fw, fh):
    return {
        "left": int(SCREEN_LEFT + fl * SCREEN_W),
        "top": int(SCREEN_TOP + ft * SCREEN_H),
        "width": int(fw * SCREEN_W),
        "height": int(fh * SCREEN_H),
    }


# ===== เดินระหว่างเสา GARAGE กับจุดแปรรูป =====
# [(ปุ่ม, วินาที), ...] — เดินจากเสาไปจุดแปรรูป
# ขากลับบอทกลับด้านปุ่มให้เอง (w↔s, a↔d) แล้วเดินถอยลำดับ
# *** ต้องจับเวลาเองหน้างานแล้วใส่ตรงนี้ ***
WALK_TO_PROCESS = [["w", 2.3]]

# ขากลับ: เว้นว่าง [] = กลับด้านปุ่มจากขาไปให้อัตโนมัติ (w->s)
# แต่ในเกมเดินถอยหลังช้ากว่าเดินหน้ามาก กด S เท่าเดิมจะถอยไม่ถึง
# ตั้งเองได้ เช่น [["s", 4.0]]  หรือหันกลับแล้วเดินหน้า [["w", 2.3]]
WALK_BACK = [["s", 4.0]]

# ก่อนเดินทุกครั้ง: กด S 1 ที -> รอ WALK_PREP_DELAY -> กด C 1 ที -> รอ WALK_PREP_AFTER
# ไม่ทำแบบนี้ตัวละครเดินไม่ตรง
WALK_PREP = True
WALK_PREP_DELAY = 2.0
WALK_PREP_AFTER = 0.3

# ===== หน้า SYSTEM GARAGE (กด E ที่เสา) =====
# region ครอบคำว่า "SYSTEM GARAGE" ด้านบนซ้าย
GARAGE_MENU_REGION = _region(455 / 1920, 255 / 1080, 300 / 1920, 45 / 1080)
GARAGE_MENU_TEMPLATE = os.path.join(TEMPLATE_DIR, "garage_menu.png")
GARAGE_MENU_THRESHOLD = 0.70
GARAGE_MENU_RETRIES = 3        # กด E ซ้ำได้กี่ครั้งถ้าเมนูไม่ขึ้น

# แท็บรูปดาวกรองเหลือรถคันที่ใช้อยู่แล้ว → ไม่ต้องคลิกเลือกรถ
# กด E ที่เสา แล้วกด L ต่อได้เลย ท้ายรถเปิด — ไม่ต้องใช้เมาส์ในหน้านี้
TRUNK_KEY_RETRIES = 3        # กด L ซ้ำได้กี่ครั้งถ้าท้ายรถไม่เปิด

# ===== หน้าท้ายรถ (INVENTORY | SECONDARY) =====
TRUNK_CHECK_REGION = _region(370 / 1920, 180 / 1080, 250 / 1920, 90 / 1080)
TRUNK_TEMPLATE = os.path.join(TEMPLATE_DIR, "trunk_open.png")
TRUNK_MATCH_THRESHOLD = 0.70

# ฝั่งซ้าย = กระเป๋าตัวละคร, ฝั่งขวา = ท้ายรถ
INVENTORY_REGION = _region(140 / 1920, 270 / 1080, 730 / 1920, 520 / 1080)
TRUNK_REGION = _region(1070 / 1920, 270 / 1080, 730 / 1920, 520 / 1080)

# ไอเทม
ORE_TEMPLATE = os.path.join(TEMPLATE_DIR, "ore_template.png")    # แร่ดิบ (Steel)
BAR_TEMPLATE = os.path.join(TEMPLATE_DIR, "bar_template.png")    # แท่งที่โพเสร็จ (Steel Bar)
TEMPLATE_MATCH_THRESHOLD = 0.70
INV_SCROLL_RETRIES = 4

# จุดปล่อยของ (ลากข้ามฝั่ง)
DROP_TO_INVENTORY = _pt(500 / 1920, 520 / 1080)   # ลากจากท้ายรถ → กระเป๋า
DROP_TO_TRUNK = _pt(1440 / 1920, 520 / 1080)      # ลากจากกระเป๋า → ท้ายรถ
SLOT_W = 117 / 1920
SLOT_H = 117 / 1080
DRAG_RETRIES = 3


def drop_candidates(base):
    """จุดปล่อยสำรอง เผื่อช่องแรกมีของอยู่แล้ว"""
    dx = int(SLOT_W * SCREEN_W)
    dy = int(SLOT_H * SCREEN_H)
    x, y = base
    return [(x, y), (x + dx, y), (x + 2 * dx, y),
            (x, y + dy), (x + dx, y + dy), (x + 2 * dx, y + dy)]


# ปุ่มใน dialog ใส่จำนวน
BTN_MAX = _pt(1102 / 1920, 559 / 1080)
BTN_CONFIRM = _pt(920 / 1920, 618 / 1080)

# ===== แถบแปรรูป (Processing) ล่างกลางจอ =====
# แถบหายไป = แปรรูปเสร็จ
PROCESS_BAR_REGION = _region(700 / 1920, 800 / 1080, 520 / 1920, 90 / 1080)
PROCESS_BAR_TEMPLATE = os.path.join(TEMPLATE_DIR, "process_bar.png")
PROCESS_BAR_THRESHOLD = 0.60
# ไม่มี process_bar.png ก็ใช้ได้ - เทียบว่าบริเวณแถบเปลี่ยนไปกี่ %
# วัดจริงตอนไม่ได้โพ ฉากเกมขยับเองแค่ ~1.4% ส่วนแผงแถบโพขึ้นมาเปลี่ยนเยอะกว่ามาก
PROCESS_CHANGE_MIN_PCT = 8.0
PROCESS_POLL = 3.0           # เช็คแถบทุกกี่วินาที
PROCESS_TIMEOUT = 600        # รอโพนานสุดกี่วินาที ก่อนยอมแพ้แล้วเริ่มรอบใหม่
PROCESS_START_RETRIES = 3    # กด E เริ่มโพซ้ำได้กี่ครั้ง

# ===== เวลา (วินาที) =====
CHECK_INTERVAL = 2.0
E_MENU_DELAY = 2.5           # รอเมนู GARAGE เปิดหลังกด E
TRUNK_OPEN_DELAY = 3.0       # รอหน้าท้ายรถเปิดหลังคลิก Open Trunk
DIALOG_OPEN_DELAY = 1.5      # รอ dialog ใส่จำนวนเด้งหลังลาก
CLICK_DELAY = 0.8
DRAG_DURATION = 0.8
AFTER_MOVE_DELAY = 2.0       # รอหลังยืนยันย้ายของ
AFTER_CLOSE_DELAY = 1.5      # รอหลังกด ESC
WALK_SETTLE_DELAY = 1.0      # รอหลังเดินถึงที่

# ===== ความปลอดภัย =====
# คลิกเมาส์ตอนไม่มีหน้าต่างเกมเปิด = ต่อยคนที่ยืนอยู่แถวนั้น
# บอทจะคลิกเฉพาะตอนยืนยันได้ว่าหน้าต่างเปิดจริงเท่านั้น
# ไม่มี template ให้ยืนยัน → ไม่คลิกเลย (ยกเลิกรอบแทน)
REQUIRE_WINDOW_BEFORE_CLICK = True

# ===== ภาพ debug =====
DEBUG_KEEP_PER_NAME = 5

# ===== ทำงานตอนเกมไม่ได้โฟกัส =====
CAPTURE_MODE = "screen"      # "screen" | "window"
PARK_GAME_OFFSCREEN = False
RESTORE_FOCUS_AFTER = True

# ===== ปุ่ม =====
KEY_TOGGLE = "f10"
KEY_TOGGLE_HUD = "f11"


def _load_calibration():
    if not os.path.exists(CALIBRATION_PATH):
        return
    with open(CALIBRATION_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    g = globals()
    for key in ("BTN_MAX", "BTN_CONFIRM",
                "DROP_TO_INVENTORY", "DROP_TO_TRUNK"):
        if key in data:
            g[key] = tuple(data[key])
    for key in ("INVENTORY_REGION", "TRUNK_REGION", "PROCESS_BAR_REGION"):
        if key in data:
            g[key] = data[key]


_load_calibration()


def _load_user_config():
    if not os.path.exists(USER_CONFIG_PATH):
        return
    try:
        with open(USER_CONFIG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        g = globals()
        if "WALK_TO_PROCESS" in data:
            g["WALK_TO_PROCESS"] = list(data["WALK_TO_PROCESS"])
        if "WALK_BACK" in data:
            g["WALK_BACK"] = list(data["WALK_BACK"])
        for key in ("CHECK_INTERVAL", "PROCESS_POLL", "PROCESS_TIMEOUT",
                    "E_MENU_DELAY", "TRUNK_OPEN_DELAY", "WALK_SETTLE_DELAY",
                    "WALK_PREP_DELAY", "WALK_PREP_AFTER"):
            if key in data:
                g[key] = float(data[key])
        for key in ("CAPTURE_MODE",):
            if key in data:
                g[key] = str(data[key])
        for key in ("PARK_GAME_OFFSCREEN", "RESTORE_FOCUS_AFTER", "WALK_PREP"):
            if key in data:
                g[key] = bool(data[key])
    except Exception as e:
        print(f"[config] ⚠ โหลด user_config.json ไม่ได้: {e}")


_user_config_seen = [None]


def reload_user_config(verbose=True):
    """โหลด user_config.json ใหม่ถ้าเนื้อไฟล์เปลี่ยน — แก้ระหว่างบอทรันได้"""
    try:
        with open(USER_CONFIG_PATH, "r", encoding="utf-8") as f:
            text = f.read()
    except OSError:
        return False
    if text == _user_config_seen[0]:
        return False
    first = _user_config_seen[0] is None
    _user_config_seen[0] = text
    _load_user_config()
    if verbose and not first:
        print(f"[config] โหลด user_config.json ใหม่ — "
              f"เดิน {WALK_TO_PROCESS}, รอโพสูงสุด {PROCESS_TIMEOUT:.0f} วิ")
    return True


reload_user_config(verbose=False)


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    print(f"จอ: {SCREEN_W}x{SCREEN_H}  SCALE={SCALE:.3f}")
    print(f"เดินไปจุดโพ      = {WALK_TO_PROCESS}")
    print(f"เดินกลับเสา      = {WALK_BACK or '(กลับด้านอัตโนมัติ)'}")
    print(f"BTN_MAX          = {BTN_MAX}")
    print(f"BTN_CONFIRM      = {BTN_CONFIRM}")
    print(f"INVENTORY_REGION = {INVENTORY_REGION}")
    print(f"TRUNK_REGION     = {TRUNK_REGION}")
    print(f"PROCESS_BAR_REGION = {PROCESS_BAR_REGION}")
