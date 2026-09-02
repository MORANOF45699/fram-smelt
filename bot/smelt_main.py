"""
smelt_main.py - บอทแปรรูป (Smelt Bot) ไม่มีหน้าคอนโซล + HUD เล็กบนจอ

รันผ่าน run.bat
  - กด F10 เริ่ม/พัก
  - กด F11 ซ่อน/แสดง HUD
  - ดับเบิลคลิกขวาที่ HUD = ปิดโปรแกรม
  - log ทั้งหมดเขียนลง logs/bot_log.txt

ก่อนใช้ครั้งแรกต้องรัน calibrate.bat ให้ครบก่อน
ไม่งั้นบอทจะไม่ยอมคลิกเลย (กันคลิกโดนโลกแล้วต่อยคน)
"""

import os
import sys
import threading
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
os.chdir(ROOT)

_LOG_DIR = os.path.join(ROOT, "logs")
os.makedirs(_LOG_DIR, exist_ok=True)
_log = open(os.path.join(_LOG_DIR, "bot_log.txt"), "a", encoding="utf-8",
            buffering=1)
sys.stdout = _log
sys.stderr = _log

import tkinter as tk

import keyboard

import config
import smelt_capture
import smelt_input as inp
from smelt_actions import one_cycle, request_abort, clear_abort

# กันรันซ้ำ: สองตัวพร้อมกันจะกดปุ่มตีกัน
_MUTEX_NAME = "SmeltBot_SingleInstance"
_mutex_handle = None


def acquire_single_instance():
    global _mutex_handle
    import ctypes
    k32 = ctypes.windll.kernel32
    _mutex_handle = k32.CreateMutexW(None, False, _MUTEX_NAME)
    return k32.GetLastError() != 183      # ERROR_ALREADY_EXISTS


status = {"text": "พร้อม - กด F10 เริ่ม (F11 ซ่อน HUD)", "color": "#cccccc"}
stop_flag = [False]


def set_status(text, color="#2ecc71"):
    status["text"] = text
    status["color"] = color
    print(f"[smelt] {text}")


def check_calibration():
    """เตือนว่ายังขาด template อะไรบ้าง"""
    from smelt_detector import template_available
    need = [
        (config.TRUNK_TEMPLATE, "trunk_open.png", "หน้าท้ายรถ (จำเป็น - ไม่มีจะไม่คลิกเลย)"),
        (config.ORE_TEMPLATE, "ore_template.png", "ไอคอนแร่ดิบ (จำเป็น)"),
        (config.BAR_TEMPLATE, "bar_template.png", "ไอคอนแท่งที่โพเสร็จ"),
        (config.PROCESS_BAR_TEMPLATE, "process_bar.png", "แถบ Processing"),
        (config.GARAGE_MENU_TEMPLATE, "garage_menu.png", "เมนู SYSTEM GARAGE"),
    ]
    missing = [(f, why) for path, f, why in need if not template_available(path)]
    if missing:
        print("=" * 55)
        print("ยังขาด template - รัน calibrate.bat ก่อน:")
        for f, why in missing:
            print(f"   - {f:22s} {why}")
        print("=" * 55)
    return missing


def bot_loop():
    # at_process = ตอนนี้ยืนอยู่จุดแปรรูปแล้วหรือยัง
    state = {"active": False, "at_process": False}

    def toggle():
        state["active"] = not state["active"]
        if state["active"]:
            clear_abort()
            state["at_process"] = False   # เริ่มใหม่ = ไม่รู้ว่ายืนตรงไหน เดินไปจุดโพก่อน
            state["reset_fails"] = True
            set_status("เริ่มทำงาน", "#2ecc71")
        else:
            request_abort()
            inp.unpark_game()
            set_status("พัก - กด F10 เริ่มต่อ", "#f39c12")

    keyboard.add_hotkey(config.KEY_TOGGLE, toggle)

    fails = 0
    covered = [False]
    hud_x = config.SCREEN_LEFT + config.SCREEN_W // 2
    hud_y = config.SCREEN_TOP + int(config.SCREEN_H * 0.8)

    with smelt_capture.open_capture() as sct:
        while not stop_flag[0]:
            if not state["active"]:
                time.sleep(0.2)
                continue

            config.reload_user_config()

            if state.pop("reset_fails", False):
                fails = 0

            # โหมดจับหน้าจอ: เกมต้องไม่โดนหน้าต่างอื่นบัง/ถูกย่อ
            # โหมดจับหน้าต่าง: ทับได้ ข้ามการเช็คนี้
            if sct.mode == "screen" and not inp.game_covers_point(hud_x, hud_y):
                if not covered[0]:
                    set_status("เกมโดนบัง - รอจนเห็นจอเกม", "#f39c12")
                    covered[0] = True
                time.sleep(config.CHECK_INTERVAL)
                continue
            covered[0] = False

            ok = one_cycle(sct, state, lambda m: set_status(m, "#3498db"))
            if ok:
                fails = 0
                set_status("จบรอบ - เริ่มรอบใหม่", "#2ecc71")
            else:
                fails += 1
                limit = config.MAX_FAILS
                if limit and fails >= limit:
                    # พลาดติดกันหลายรอบ = มีอะไรผิดจริง หยุดดีกว่าปล่อยวนมั่ว
                    state["active"] = False
                    request_abort()
                    inp.unpark_game()
                    set_status(f"พลาดติดกัน {fails} รอบ - หยุดบอท (กด F10 เริ่มใหม่)",
                               "#e74c3c")
                    fails = 0
                else:
                    suffix = f"/{limit}" if limit else ""
                    set_status(f"รอบนี้ไม่สำเร็จ ({fails}{suffix}) - ลองใหม่",
                               "#e74c3c")
            time.sleep(config.CHECK_INTERVAL)


def main():
    import atexit
    inp.rescue_offscreen_game()       # เกมค้างนอกจอจากรอบก่อน -> ลากกลับ
    atexit.register(inp.unpark_game)  # ปิดโปรแกรมยังไง เกมต้องกลับเข้าจอ

    if not acquire_single_instance():
        print("[smelt] มีบอทตัวอื่นรันอยู่แล้ว - ปิดตัวนี้ทิ้ง")
        return

    check_calibration()

    root = tk.Tk()
    root.overrideredirect(True)
    root.attributes("-topmost", True)
    root.attributes("-alpha", 0.85)
    root.configure(bg="#111111")
    root.geometry("+8+8")

    label = tk.Label(root, text=status["text"], fg=status["color"],
                     bg="#111111", font=("Segoe UI", 10, "bold"),
                     padx=10, pady=4)
    label.pack()

    drag = {"x": 0, "y": 0}

    def press(e):
        drag["x"], drag["y"] = e.x, e.y

    def move(e):
        root.geometry(f"+{e.x_root - drag['x']}+{e.y_root - drag['y']}")

    label.bind("<Button-1>", press)
    label.bind("<B1-Motion>", move)

    def quit_app(_e=None):
        stop_flag[0] = True
        root.destroy()

    label.bind("<Double-Button-3>", quit_app)

    def refresh():
        label.config(text=status["text"], fg=status["color"])
        root.after(300, refresh)

    def keep_top():
        root.attributes("-topmost", True)
        root.lift()
        root.after(2000, keep_top)

    hud_visible = [True]

    def toggle_hud():
        def run():
            if hud_visible[0]:
                root.withdraw()
                hud_visible[0] = False
            else:
                root.deiconify()
                hud_visible[0] = True
        root.after(0, run)

    keyboard.add_hotkey(config.KEY_TOGGLE_HUD, toggle_hud)

    threading.Thread(target=bot_loop, daemon=True).start()
    refresh()
    keep_top()
    root.mainloop()


if __name__ == "__main__":
    main()
