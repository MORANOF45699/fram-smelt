# -*- coding: utf-8 -*-
"""
set_config.py - เมนูตั้งค่าบอทแปรรูป

เขียนลง user_config.json ซึ่งบอทอ่านใหม่เองระหว่างรัน
(แก้ตอนบอทเปิดอยู่ก็ได้ ค่าใหม่มีผลในไม่กี่วินาที ไม่ต้องปิดเปิด)
"""

import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
sys.stdin.reconfigure(encoding="utf-8")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_FILE = os.path.join(ROOT, "user_config.json")

defaults = {
    "WALK_TO_PROCESS": [["w", 2.3]],
    "WALK_BACK": [["w", 2.3]],
    "WALK_PREP": True,
    "WALK_PREP_C1_DELAY": 1.0,
    "WALK_PREP_S_DELAY": 2.0,
    "WALK_PREP_AFTER": 0.3,
    "PROCESS_POLL": 3.0,
    "PROCESS_TIMEOUT": 1200,
    "MAX_FAILS": 5,
    "CHECK_INTERVAL": 2.0,
    "E_MENU_DELAY": 2.5,
    "TRUNK_OPEN_DELAY": 3.0,
    "WALK_SETTLE_DELAY": 1.0,
    "CAPTURE_MODE": "screen",
    "PARK_GAME_OFFSCREEN": False,
    "RESTORE_FOCUS_AFTER": True,
    "KEY_TOGGLE": "f10",
    "KEY_TOGGLE_HUD": "f11",
}


def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


def load_config():
    cfg = defaults.copy()
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                cfg.update(json.load(f))
        except Exception as e:
            print(f"โหลดไฟล์ตั้งค่าเดิมไม่ได้: {e}")
    return cfg


def save_config(cfg):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=4, ensure_ascii=False)
        print(f"\n[/] บันทึกลง {os.path.basename(CONFIG_FILE)} เรียบร้อย")
        return True
    except Exception as e:
        print(f"\n[X] บันทึกไม่ได้: {e}")
        return False


def walk_text(steps):
    """[['w', 2.3]] -> 'W 2.3 วิ'"""
    if not steps:
        return "(กลับด้านอัตโนมัติ)"
    return " + ".join(f"{str(k).upper()} {float(s):.1f} วิ" for k, s in steps)


def ask_number(prompt, current, cast=float):
    val = input(f"{prompt} [เดิม {current}]: ").strip()
    if not val:
        return current
    try:
        return cast(val)
    except ValueError:
        input("ค่าไม่ถูกต้อง ใส่ตัวเลขเท่านั้น (กด Enter เพื่อกลับ)")
        return current


def ask_walk(prompt, current):
    """
    รับเป็นวินาทีเดียว เช่น 2.3  -> [["w", 2.3]]
    หรือหลายช่วง เช่น  w 1.5, d 0.4, w 0.8
    """
    print(f"\n  ตอนนี้: {walk_text(current)}")
    print("  ใส่เป็นวินาทีเดียว เช่น  2.3        (เดินหน้าอย่างเดียว)")
    print("  หรือหลายช่วง เช่น       w 1.5, d 0.4, w 0.8")
    val = input(f"{prompt}: ").strip()
    if not val:
        return current
    try:
        if "," not in val and " " not in val:
            return [["w", float(val)]]
        steps = []
        for part in val.split(","):
            key, secs = part.split()
            if key.lower() not in ("w", "a", "s", "d"):
                raise ValueError(f"ปุ่ม {key} ใช้ไม่ได้")
            steps.append([key.lower(), float(secs)])
        return steps
    except Exception as e:
        input(f"รูปแบบไม่ถูกต้อง ({e}) (กด Enter เพื่อกลับ)")
        return current


def main():
    cfg = load_config()

    while True:
        clear_screen()
        cap = ("จับหน้าต่างเกม (window) - เอาหน้าต่างอื่นทับได้"
               if cfg.get("CAPTURE_MODE") == "window"
               else "จับหน้าจอ (screen) - เกมต้องอยู่บนจอ")
        park = ("เปิด - เกมหายจากจอระหว่างรอโพ"
                if cfg.get("PARK_GAME_OFFSCREEN") else "ปิด")
        prep = "เปิด" if cfg.get("WALK_PREP") else "ปิด"
        stop = (f"หยุดเมื่อพลาดติดกัน {cfg['MAX_FAILS']} รอบ"
                if cfg.get("MAX_FAILS") else "ไม่หยุดเอง")

        print("=" * 62)
        print("            ตั้งค่าบอทแปรรูป (Smelt)")
        print("=" * 62)
        print("  -- การเดิน --")
        print(f"  [1] เดินไปจุดแปรรูป          : {walk_text(cfg['WALK_TO_PROCESS'])}")
        print(f"  [2] เดินกลับเสา GARAGE       : {walk_text(cfg['WALK_BACK'])}")
        print(f"  [3] ท่าจัดกล้องก่อนเดิน       : {prep}")
        print(f"      C -> รอ {cfg['WALK_PREP_C1_DELAY']:.1f} วิ -> S -> "
              f"รอ {cfg['WALK_PREP_S_DELAY']:.1f} วิ -> รอ {cfg['WALK_PREP_AFTER']:.1f} วิ")
        print(f"  [4] เวลาช่วง C -> S           : {cfg['WALK_PREP_C1_DELAY']:.1f} วิ")
        print(f"  [5] เวลาช่วง S -> C           : {cfg['WALK_PREP_S_DELAY']:.1f} วิ")
        print(f"  [6] รอก่อนออกเดิน             : {cfg['WALK_PREP_AFTER']:.1f} วิ")
        print("  -- การแปรรูป --")
        print(f"  [7] รอโพนานสุด               : {cfg['PROCESS_TIMEOUT']:.0f} วิ "
              f"({cfg['PROCESS_TIMEOUT']/60:.0f} นาที)")
        print(f"  [8] เช็คแถบทุก               : {cfg['PROCESS_POLL']:.1f} วิ")
        print("  -- ทั่วไป --")
        print(f"  [9] พลาดติดกันแล้วหยุด        : {stop}")
        print(f"  [c] วิธีจับภาพ               : {cap}")
        print(f"  [p] จอดเกมไว้นอกจอ           : {park}")
        print(f"  [i] ความถี่สแกน              : {cfg['CHECK_INTERVAL']:.1f} วิ")
        print(f"  [k] ปุ่มเริ่ม/พัก             : {cfg['KEY_TOGGLE'].upper()} "
              f"(ซ่อน HUD = {cfg['KEY_TOGGLE_HUD'].upper()})")
        print("      * บอทหลายตัวต้องใช้คนละปุ่ม ไม่งั้นกดทีเดียวโดนหมด")
        print("-" * 62)
        print("  [s] บันทึกและออก        [x] ออกโดยไม่บันทึก")
        print("=" * 62)

        choice = input("เลือกเมนู: ").strip().lower()

        if choice == "1":
            cfg["WALK_TO_PROCESS"] = ask_walk("เดินไปจุดแปรรูป", cfg["WALK_TO_PROCESS"])
        elif choice == "2":
            cfg["WALK_BACK"] = ask_walk("เดินกลับเสา", cfg["WALK_BACK"])
        elif choice == "3":
            cfg["WALK_PREP"] = not cfg.get("WALK_PREP", True)
        elif choice == "4":
            cfg["WALK_PREP_C1_DELAY"] = ask_number(
                "เวลาช่วง C -> S (วิ)", cfg["WALK_PREP_C1_DELAY"])
        elif choice == "5":
            cfg["WALK_PREP_S_DELAY"] = ask_number(
                "เวลาช่วง S -> C (วิ)", cfg["WALK_PREP_S_DELAY"])
        elif choice == "6":
            cfg["WALK_PREP_AFTER"] = ask_number(
                "รอก่อนออกเดิน (วิ)", cfg["WALK_PREP_AFTER"])
        elif choice == "7":
            cfg["PROCESS_TIMEOUT"] = ask_number(
                "รอโพนานสุด (วิ)", cfg["PROCESS_TIMEOUT"])
        elif choice == "8":
            cfg["PROCESS_POLL"] = ask_number("เช็คแถบทุกกี่วิ", cfg["PROCESS_POLL"])
        elif choice == "9":
            cfg["MAX_FAILS"] = ask_number(
                "พลาดติดกันกี่รอบถึงหยุด (0 = ไม่หยุดเอง)",
                cfg["MAX_FAILS"], int)
        elif choice == "c":
            if cfg.get("CAPTURE_MODE") == "window":
                cfg["CAPTURE_MODE"] = "screen"
            else:
                cfg["CAPTURE_MODE"] = "window"
                print("\n  หมายเหตุ: โหมดนี้ต้องลง  pip install windows-capture")
                print("  ย่อ (minimize) เกมยังไม่ได้ - Windows หยุดวาดหน้าต่างที่ย่อ")
                input("  กด Enter เพื่อไปต่อ...")
        elif choice == "p":
            cfg["PARK_GAME_OFFSCREEN"] = not cfg.get("PARK_GAME_OFFSCREEN", False)
            if cfg["PARK_GAME_OFFSCREEN"] and cfg.get("CAPTURE_MODE") != "window":
                print("\n  ต้องตั้ง [c] เป็น window ก่อน ไม่งั้นจอดแล้วอ่านจอไม่ได้")
                input("  กด Enter เพื่อไปต่อ...")
        elif choice == "i":
            cfg["CHECK_INTERVAL"] = ask_number("สแกนทุกกี่วิ", cfg["CHECK_INTERVAL"])
        elif choice == "k":
            val = input(f"ปุ่มเริ่ม/พัก [เดิม {cfg['KEY_TOGGLE']}]: ").strip().lower()
            if val:
                cfg["KEY_TOGGLE"] = val
            val = input(f"ปุ่มซ่อน HUD [เดิม {cfg['KEY_TOGGLE_HUD']}]: ").strip().lower()
            if val:
                cfg["KEY_TOGGLE_HUD"] = val
        elif choice == "s":
            if save_config(cfg):
                input("กด Enter เพื่อปิดหน้าต่าง...")
                break
        elif choice == "x":
            print("\nยกเลิก ไม่บันทึก")
            break
        else:
            input("เลือกเมนูไม่ถูกต้อง (กด Enter เพื่อลองใหม่)")


if __name__ == "__main__":
    main()
