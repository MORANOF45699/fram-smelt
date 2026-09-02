"""
smelt_input.py - DirectInput สำหรับ Smelt Bot (บอทแปรรูป)
คีย์บอร์ดใช้ SendInput scancode (เกม FiveM รับได้)
เมาส์ใน UI (NUI) ใช้ SetCursorPos + SendInput click
"""

import ctypes
import time

SendInput = ctypes.windll.user32.SendInput
SetCursorPos = ctypes.windll.user32.SetCursorPos

# ===== Scan Codes =====
KEY_L = 0x26
KEY_G = 0x22
KEY_E = 0x12
KEY_T = 0x14
KEY_1 = 0x02
KEY_X = 0x2D
KEY_W = 0x11
KEY_S = 0x1F
KEY_A = 0x1E
KEY_D = 0x20
KEY_C = 0x2E
KEY_2 = 0x03
KEY_ESC = 0x01

PUL = ctypes.POINTER(ctypes.c_ulong)


class KeyBdInput(ctypes.Structure):
    _fields_ = [
        ("wVk", ctypes.c_ushort),
        ("wScan", ctypes.c_ushort),
        ("dwFlags", ctypes.c_ulong),
        ("time", ctypes.c_ulong),
        ("dwExtraInfo", PUL)
    ]


class HardwareInput(ctypes.Structure):
    _fields_ = [
        ("uMsg", ctypes.c_ulong),
        ("wParamL", ctypes.c_short),
        ("wParamH", ctypes.c_ushort)
    ]


class MouseInput(ctypes.Structure):
    _fields_ = [
        ("dx", ctypes.c_long),
        ("dy", ctypes.c_long),
        ("mouseData", ctypes.c_ulong),
        ("dwFlags", ctypes.c_ulong),
        ("time", ctypes.c_ulong),
        ("dwExtraInfo", PUL)
    ]


class Input_I(ctypes.Union):
    _fields_ = [
        ("ki", KeyBdInput),
        ("mi", MouseInput),
        ("hi", HardwareInput)
    ]


class Input(ctypes.Structure):
    _fields_ = [
        ("type", ctypes.c_ulong),
        ("ii", Input_I)
    ]


KEYEVENTF_SCANCODE = 0x0008
KEYEVENTF_KEYUP = 0x0002

MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_RIGHTDOWN = 0x0008
MOUSEEVENTF_RIGHTUP = 0x0010
MOUSEEVENTF_WHEEL = 0x0800
WHEEL_DELTA = 120

INPUT_MOUSE = 0
INPUT_KEYBOARD = 1


def _key_event(scan_code, flags):
    extra = ctypes.c_ulong(0)
    ii_ = Input_I()
    ii_.ki = KeyBdInput(0, scan_code, flags, 0, ctypes.pointer(extra))
    x = Input(ctypes.c_ulong(INPUT_KEYBOARD), ii_)
    SendInput(1, ctypes.pointer(x), ctypes.sizeof(x))


def _mouse_event(flags, data=0):
    extra = ctypes.c_ulong(0)
    ii_ = Input_I()
    ii_.mi = MouseInput(0, 0, data, flags, 0, ctypes.pointer(extra))
    x = Input(ctypes.c_ulong(INPUT_MOUSE), ii_)
    SendInput(1, ctypes.pointer(x), ctypes.sizeof(x))


def scroll_up(notches=3, x=None, y=None, delay=0.08):
    """เลื่อนล้อเมาส์ขึ้น (ไปบนสุดของ inventory) notches = จำนวนคลิกล้อ"""
    if x is not None and y is not None:
        move_to(x, y)
        time.sleep(0.05)
    for _ in range(notches):
        _mouse_event(MOUSEEVENTF_WHEEL, WHEEL_DELTA)
        time.sleep(delay)


def scroll_down(notches=3, x=None, y=None, delay=0.08):
    """เลื่อนล้อเมาส์ลง"""
    if x is not None and y is not None:
        move_to(x, y)
        time.sleep(0.05)
    neg = ctypes.c_long(-WHEEL_DELTA).value & 0xFFFFFFFF
    for _ in range(notches):
        _mouse_event(MOUSEEVENTF_WHEEL, neg)
        time.sleep(delay)


def press_key(scan_code, duration=0.08):
    """กดปุ่มแล้วปล่อย"""
    _key_event(scan_code, KEYEVENTF_SCANCODE)
    time.sleep(duration)
    _key_event(scan_code, KEYEVENTF_SCANCODE | KEYEVENTF_KEYUP)


def press_l():
    press_key(KEY_L)


def press_g():
    press_key(KEY_G)


def press_t():
    press_key(KEY_T)


def press_1():
    press_key(KEY_1)


def press_2():
    press_key(KEY_2)


def press_x():
    press_key(KEY_X)


def press_e():
    press_key(KEY_E)


def hold_key(scan_code, seconds):
    """กดปุ่มค้างไว้กี่วินาที (ใช้เดิน)"""
    _key_event(scan_code, KEYEVENTF_SCANCODE)
    time.sleep(seconds)
    _key_event(scan_code, KEYEVENTF_SCANCODE | KEYEVENTF_KEYUP)


WALK_KEYS = {"w": KEY_W, "s": KEY_S, "a": KEY_A, "d": KEY_D}


def prepare_walk(delay=0.5, after=0.3):
    """
    ท่าตั้งต้นก่อนเดิน: กด S 1 ที -> รอ -> กด C 1 ที -> รอ
    ไม่ทำแบบนี้ตัวละครจะเดินไม่ตรง (กล้อง/ทิศไม่ถูกจัดก่อน)
    """
    print("[input] จัดท่าก่อนเดิน: S แล้ว C")
    press_key(KEY_S)
    time.sleep(delay)
    press_key(KEY_C)
    time.sleep(after)


def walk(steps, prep=True, prep_delay=0.5, prep_after=0.3):
    """
    เดินตามลำดับที่กำหนด
    steps = [("w", 2.0), ("d", 0.5)]  → กด W ค้าง 2 วิ แล้ว D ค้าง 0.5 วิ
    prep=True → จัดท่าก่อน (S แล้ว C) ให้เดินตรง
    """
    if prep:
        prepare_walk(prep_delay, prep_after)
    for key, secs in steps:
        k = WALK_KEYS.get(str(key).lower())
        if k is None:
            print(f"[input] ⚠ ไม่รู้จักปุ่มเดิน {key!r} — ข้าม")
            continue
        print(f"[input] เดิน {key.upper()} {secs} วิ")
        hold_key(k, float(secs))
        time.sleep(0.2)


def walk_back(steps, prep=True, prep_delay=0.5, prep_after=0.3):
    """เดินย้อนกลับ — กลับด้านปุ่มแล้วเดินถอยลำดับ"""
    opposite = {"w": "s", "s": "w", "a": "d", "d": "a"}
    walk([(opposite.get(str(k).lower(), k), s) for k, s in reversed(steps)],
         prep=prep, prep_delay=prep_delay, prep_after=prep_after)


def press_esc():
    press_key(KEY_ESC)


GAME_WINDOW_TITLE = "FiveM"
KEY_ALT = 0x38

user32 = ctypes.windll.user32


class POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]


# ประกาศชนิดค่าคืน/พารามิเตอร์ให้ถูก — ไม่งั้น HWND 64-bit โดนตัดเหลือ 32-bit
user32.GetForegroundWindow.restype = ctypes.c_void_p
user32.WindowFromPoint.restype = ctypes.c_void_p
user32.WindowFromPoint.argtypes = [POINT]
user32.GetAncestor.restype = ctypes.c_void_p
user32.GetAncestor.argtypes = [ctypes.c_void_p, ctypes.c_uint]
user32.IsWindow.argtypes = [ctypes.c_void_p]
user32.IsIconic.argtypes = [ctypes.c_void_p]
user32.ShowWindow.argtypes = [ctypes.c_void_p, ctypes.c_int]
user32.SwitchToThisWindow.argtypes = [ctypes.c_void_p, ctypes.c_bool]


def _find_game_hwnd():
    """หา hwnd หน้าต่างเกม (ชื่อมีคำว่า FiveM)"""
    found = []

    @ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
    def cb(hwnd, _):
        n = user32.GetWindowTextLengthW(hwnd)
        if n:
            buf = ctypes.create_unicode_buffer(n + 1)
            user32.GetWindowTextW(hwnd, buf, n + 1)
            if GAME_WINDOW_TITLE in buf.value:
                found.append(hwnd)
                return False
        return True

    user32.EnumWindows(cb, None)
    return found[0] if found else None


class RECT(ctypes.Structure):
    _fields_ = [("left", ctypes.c_long), ("top", ctypes.c_long),
                ("right", ctypes.c_long), ("bottom", ctypes.c_long)]


user32.GetWindowRect.argtypes = [ctypes.c_void_p, ctypes.POINTER(RECT)]
user32.SetWindowPos.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_int,
                                ctypes.c_int, ctypes.c_int, ctypes.c_int,
                                ctypes.c_uint]

SWP_NOSIZE = 0x0001
SWP_NOZORDER = 0x0004
SWP_NOACTIVATE = 0x0010
PARK_POS = (-32000, -32000)

_parked_at = [None]      # ตำแหน่งเดิมของหน้าต่างเกมตอนยังไม่ถูกจอด


def is_parked():
    return _parked_at[0] is not None


def window_is_offscreen(hwnd=None):
    """หน้าต่างเกมอยู่นอกขอบเดสก์ท็อปไหม (ใช้กู้เคสบอทตายตอนจอดอยู่)"""
    hwnd = hwnd or _find_game_hwnd()
    if not hwnd:
        return False
    r = RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(r))
    return r.left <= PARK_POS[0] + 1000


def rescue_offscreen_game():
    """
    ตอนเปิดโปรแกรม: ถ้าเจอเกมค้างอยู่นอกจอ (บอทรอบก่อนตายตอนจอดอยู่)
    ลากกลับมาที่ 0,0 ให้ ไม่งั้นผู้ใช้จะหาหน้าต่างไม่เจอเลย
    """
    hwnd = _find_game_hwnd()
    if not hwnd or not window_is_offscreen(hwnd):
        return False
    print("[หน้าต่าง] เจอเกมค้างอยู่นอกจอ — ลากกลับเข้าจอให้")
    user32.SetWindowPos(hwnd, None, 0, 0, 0, 0,
                        SWP_NOSIZE | SWP_NOZORDER | SWP_NOACTIVATE)
    _parked_at[0] = None
    time.sleep(0.5)
    return True


def park_game():
    """
    ย้ายหน้าต่างเกมออกไปนอกจอ (ไม่ใช่ย่อ — ย่อแล้ว Windows หยุด render จับภาพไม่ได้)
    เกมหายจากจอ แต่ยังวาดภาพอยู่ → Windows Graphics Capture ยังอ่าน HUD ได้
    """
    hwnd = _find_game_hwnd()
    if not hwnd or is_parked():
        return False
    r = RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(r))
    if r.left <= PARK_POS[0] + 1000:      # จอดอยู่แล้ว
        return False
    _parked_at[0] = (r.left, r.top)
    user32.SetWindowPos(hwnd, None, PARK_POS[0], PARK_POS[1], 0, 0,
                        SWP_NOSIZE | SWP_NOZORDER | SWP_NOACTIVATE)
    print(f"[หน้าต่าง] จอดเกมไว้นอกจอ (ตำแหน่งเดิม {r.left},{r.top})")
    return True


def unpark_game():
    """ดึงหน้าต่างเกมกลับเข้าจอที่ตำแหน่งเดิม (ต้องทำก่อนใช้เมาส์ลากของ)"""
    hwnd = _find_game_hwnd()
    if not hwnd or not is_parked():
        return False
    x, y = _parked_at[0]
    user32.SetWindowPos(hwnd, None, x, y, 0, 0,
                        SWP_NOSIZE | SWP_NOZORDER | SWP_NOACTIVATE)
    _parked_at[0] = None
    print(f"[หน้าต่าง] ดึงเกมกลับเข้าจอที่ {x},{y}")
    time.sleep(0.6)
    return True


def get_foreground():
    """hwnd ของหน้าต่างที่กำลังโฟกัสอยู่ (ไว้จำไว้คืนทีหลัง)"""
    return user32.GetForegroundWindow()


def restore_foreground(hwnd):
    """คืนโฟกัสให้หน้าต่างเดิมที่ผู้ใช้ทำงานอยู่ก่อนบอทแย่งไป"""
    if not hwnd or hwnd == user32.GetForegroundWindow():
        return
    if not user32.IsWindow(hwnd):
        return
    user32.SwitchToThisWindow(hwnd, True)


def game_covers_point(x, y):
    """
    จุด (x, y) บนจอเป็นของหน้าต่างเกมไหม
    ใช้เช็คว่ามีหน้าต่างอื่นบังเกมอยู่หรือเปล่า — จับภาพหน้าจอจะได้ไม่อ่านของผิดหน้าต่าง
    """
    hwnd = _find_game_hwnd()
    if not hwnd:
        return False
    if user32.IsIconic(hwnd):        # เกมถูกย่อ → จับภาพไม่ได้เลย
        return False

    top = user32.WindowFromPoint(POINT(int(x), int(y)))
    if not top:
        return False
    # WindowFromPoint คืน child window ได้ → ไล่ขึ้นไปหา top-level แล้วเทียบ
    root = user32.GetAncestor(top, 2)     # GA_ROOT
    return root == hwnd or top == hwnd


def is_game_focused():
    """เกมเป็นหน้าต่างที่รับ input อยู่ไหม"""
    hwnd = _find_game_hwnd()
    return bool(hwnd) and user32.GetForegroundWindow() == hwnd


def focus_game(retries=3):
    """
    ดึงหน้าต่างเกมกลับ foreground (กันเมาส์/โฟกัสหลุดไปหน้าต่างอื่น)
    เจอ Start menu / เมนู Windows แย่งโฟกัส → กด ESC ปิดก่อน
    คืน False ถ้าดึงกลับไม่ได้ — ผู้เรียกต้องไม่กดปุ่มต่อ ไม่งั้นปุ่มจะรั่วไปโดนเดสก์ท็อป
    """
    hwnd = _find_game_hwnd()
    if not hwnd:
        return False

    for _ in range(retries):
        if user32.GetForegroundWindow() == hwnd:
            return True
        print("[input] โฟกัสหลุดจากเกม → ดึงหน้าต่างเกมกลับมา")
        # ปิด Start menu / เมนูคลิกขวาของ Windows ที่ค้างทับเกมอยู่
        press_key(KEY_ESC)
        time.sleep(0.25)
        if user32.IsIconic(hwnd):
            user32.ShowWindow(hwnd, 9)      # SW_RESTORE
        user32.SwitchToThisWindow(hwnd, True)
        time.sleep(0.4)

    ok = user32.GetForegroundWindow() == hwnd
    if not ok:
        print("[input] ⚠ ดึงโฟกัสเกมกลับไม่ได้ — งดกดปุ่มรอบนี้")
    return ok


def move_to(x, y):
    """เลื่อน cursor ไปพิกัดหน้าจอ (สำหรับ UI ที่มี cursor)"""
    SetCursorPos(int(x), int(y))


def click(x, y, delay=0.1):
    """คลิกซ้ายที่พิกัด"""
    move_to(x, y)
    time.sleep(0.15)  # รอให้เกมรับตำแหน่ง cursor ก่อนคลิก
    _mouse_event(MOUSEEVENTF_LEFTDOWN)
    time.sleep(delay)
    _mouse_event(MOUSEEVENTF_LEFTUP)


def right_click(x, y, delay=0.15):
    """คลิกขวาที่พิกัด (เปิดเมนู Use/Give/Delete)"""
    move_to(x, y)
    time.sleep(0.25)  # รอให้เกมรับตำแหน่ง cursor ก่อนคลิกขวา (สำคัญมาก)
    _mouse_event(MOUSEEVENTF_RIGHTDOWN)
    time.sleep(delay)
    _mouse_event(MOUSEEVENTF_RIGHTUP)


def drag(x1, y1, x2, y2, duration=0.6, steps=25):
    """ลากไอเทมจาก (x1,y1) ไป (x2,y2) แบบ smooth"""
    move_to(x1, y1)
    time.sleep(0.15)
    _mouse_event(MOUSEEVENTF_LEFTDOWN)
    time.sleep(0.15)
    for i in range(1, steps + 1):
        t = i / steps
        move_to(x1 + (x2 - x1) * t, y1 + (y2 - y1) * t)
        time.sleep(duration / steps)
    time.sleep(0.15)
    _mouse_event(MOUSEEVENTF_LEFTUP)


if __name__ == '__main__':
    print("=== ทดสอบ Smelt Input ===")
    print("สลับไปหน้าเกมภายใน 3 วินาที... จะกด L")
    time.sleep(3)
    press_l()
    print("กด L แล้ว")
