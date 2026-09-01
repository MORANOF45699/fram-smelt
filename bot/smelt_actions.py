"""
smelt_actions.py - ลำดับการทำงานของบอทแปรรูป

ลูป 1 รอบ:
  1. อยู่ที่เสา GARAGE -> กด E เปิดเมนู -> กด L เปิดท้ายรถ
  2. เอาแท่งที่โพเสร็จ (ถ้ามีในกระเป๋า) ใส่ท้ายรถ
  3. ดึงแร่ดิบจากท้ายรถออกมา (Max)
  4. ESC ปิด -> เดินไปจุดแปรรูป
  5. กด E เริ่มแปรรูป -> รอจนแถบ Processing หาย
  6. เดินกลับเสา -> วนข้อ 1

ความปลอดภัย: คลิกเมาส์ตอนไม่มีหน้าต่างเปิด = ต่อยคนที่ยืนแถวนั้น
บอทจะคลิกเฉพาะตอนยืนยันได้ว่าหน้าต่างท้ายรถเปิดจริงเท่านั้น
"""

import time

import config
import smelt_input as inp
from smelt_detector import (find_item, is_garage_menu_open, is_trunk_open,
                            is_processing, template_available,
                            save_debug_screenshot)

_abort = [False]


def request_abort():
    """สั่งให้ขั้นตอนที่กำลังทำอยู่หยุดทันที (กด F10 พัก)"""
    _abort[0] = True


def clear_abort():
    _abort[0] = False


def _aborted(tag):
    if not _abort[0]:
        return False
    print(f"[{tag}] ถูกสั่งพัก - ปิดหน้าต่างแล้วหยุด")
    inp.press_esc()
    return True


def _can_click(sct, tag):
    """
    ปลอดภัยพอที่จะคลิกไหม - ต้องยืนยันได้ว่าหน้าต่างท้ายรถเปิดอยู่
    ไม่งั้นคลิกไปโดนโลก = ต่อยคนที่ยืนแถวนั้น
    """
    if not config.REQUIRE_WINDOW_BEFORE_CLICK:
        return True
    if not template_available(config.TRUNK_TEMPLATE):
        print(f"[{tag}] ไม่มี trunk_open.png ให้ยืนยันหน้าต่าง - "
              f"งดคลิกทั้งหมด (กันต่อยคน) รัน calibrate ก่อน")
        return False
    if not is_trunk_open(sct):
        print(f"[{tag}] หน้าท้ายรถไม่ได้เปิด - งดคลิก (กันต่อยคน)")
        return False
    return True


def open_trunk(sct):
    """
    กด E ที่เสา เปิดเมนู GARAGE แล้วกด L เปิดท้ายรถ
    แท็บรูปดาวกรองเหลือรถคันที่ใช้อยู่แล้ว จึงไม่ต้องคลิกเลือกรถ
    """
    if not inp.focus_game():
        save_debug_screenshot(sct, "no_focus")
        print("[เปิด] เกมไม่ได้อยู่หน้าจอ - ข้ามรอบนี้")
        return False

    check_menu = template_available(config.GARAGE_MENU_TEMPLATE)
    if not check_menu:
        print("[เปิด] (ข้ามการยืนยันเมนู GARAGE - ยังไม่มี garage_menu.png)")

    opened_menu = False
    for attempt in range(1, config.GARAGE_MENU_RETRIES + 1):
        if _aborted("เปิด"):
            return False
        print(f"[เปิด] กด E ที่เสา GARAGE (ครั้งที่ {attempt})...")
        inp.press_e()
        time.sleep(config.E_MENU_DELAY)
        if not check_menu or is_garage_menu_open(sct):
            opened_menu = True
            break
        print("[เปิด] เมนู GARAGE ยังไม่ขึ้น - ลองกด E ใหม่")

    if not opened_menu:
        save_debug_screenshot(sct, "garage_menu_not_open")
        print("[เปิด] เปิดเมนู GARAGE ไม่ได้ - ยกเลิกรอบนี้")
        inp.press_esc()
        return False

    check_trunk = template_available(config.TRUNK_TEMPLATE)
    if not check_trunk:
        print("[เปิด] (ข้ามการยืนยันหน้าท้ายรถ - ยังไม่มี trunk_open.png)")

    for attempt in range(1, config.TRUNK_KEY_RETRIES + 1):
        if _aborted("เปิด"):
            return False
        print(f"[เปิด] กด L เปิดท้ายรถ (ครั้งที่ {attempt})...")
        inp.press_l()
        time.sleep(config.TRUNK_OPEN_DELAY)
        if not check_trunk:
            return True
        if is_trunk_open(sct):
            print("[เปิด] หน้าท้ายรถเปิดแล้ว")
            return True
        print("[เปิด] หน้าท้ายรถยังไม่เปิด - ลองกด L ใหม่")

    save_debug_screenshot(sct, "trunk_not_open")
    print("[เปิด] เปิดท้ายรถไม่ได้ - ยกเลิกรอบนี้")
    inp.press_esc()
    return False


def _move_item(sct, template, from_region, to_base, label, tag):
    """
    ลากไอเทมข้ามฝั่ง แล้วกด Max -> O
    ลองหลายจุดปล่อย เผื่อช่องแรกมีของอยู่แล้ว
    Returns: True ถ้าย้ายได้
    """
    if not _can_click(sct, tag):
        return False

    candidates = config.drop_candidates(to_base)
    for attempt in range(1, config.DRAG_RETRIES + 1):
        if _aborted(tag):
            return False

        slot = find_item(sct, template, from_region, label)
        if slot is None:
            return False

        drop = candidates[(attempt - 1) % len(candidates)]
        print(f"[{tag}] ลาก{label} {slot} -> {drop} "
              f"(ครั้งที่ {attempt}/{config.DRAG_RETRIES})")
        inp.drag(*slot, *drop, duration=config.DRAG_DURATION)
        time.sleep(config.DIALOG_OPEN_DELAY)

        print(f"[{tag}] คลิก Max แล้วยืนยัน O")
        inp.click(*config.BTN_MAX)
        time.sleep(config.CLICK_DELAY)
        inp.click(*config.BTN_CONFIRM)
        time.sleep(config.AFTER_MOVE_DELAY)

        # หายไปจากฝั่งเดิม = ย้ายสำเร็จ
        if find_item(sct, template, from_region, label) is None:
            print(f"[{tag}] ย้าย{label}สำเร็จ")
            return True
        print(f"[{tag}] {label}ยังอยู่ที่เดิม - ลองจุดปล่อยถัดไป")

    save_debug_screenshot(sct, f"move_failed_{tag}")
    return False


def store_bars(sct):
    """เอาแท่งที่โพเสร็จในกระเป๋า ใส่กลับท้ายรถ (ไม่มีก็ข้าม)"""
    if find_item(sct, config.BAR_TEMPLATE, config.INVENTORY_REGION,
                 "แท่งที่โพเสร็จ") is None:
        print("[เก็บ] ไม่มีแท่งที่โพเสร็จในกระเป๋า - ข้าม")
        return True
    return _move_item(sct, config.BAR_TEMPLATE, config.INVENTORY_REGION,
                      config.DROP_TO_TRUNK, "แท่งที่โพเสร็จ", "เก็บ")


def take_ore(sct):
    """ดึงแร่ดิบจากท้ายรถออกมาใส่กระเป๋า (Max)"""
    return _move_item(sct, config.ORE_TEMPLATE, config.TRUNK_REGION,
                      config.DROP_TO_INVENTORY, "แร่ดิบ", "ดึง")


def start_processing(sct):
    """เดินไปจุดแปรรูป กด E เริ่ม แล้วยืนยันว่าแถบ Processing ขึ้นจริง"""
    print(f"[โพ] เดินไปจุดแปรรูป {config.WALK_TO_PROCESS}")
    inp.walk(config.WALK_TO_PROCESS)
    time.sleep(config.WALK_SETTLE_DELAY)

    check_bar = template_available(config.PROCESS_BAR_TEMPLATE)
    if not check_bar:
        print("[โพ] (ข้ามการยืนยันแถบ Processing - ยังไม่มี process_bar.png)")

    for attempt in range(1, config.PROCESS_START_RETRIES + 1):
        if _aborted("โพ"):
            return False
        print(f"[โพ] กด E เริ่มแปรรูป (ครั้งที่ {attempt})...")
        inp.press_e()
        time.sleep(config.WALK_SETTLE_DELAY)
        if not check_bar:
            return True
        if is_processing(sct):
            print("[โพ] แถบ Processing ขึ้นแล้ว")
            return True
        print("[โพ] แถบ Processing ไม่ขึ้น - ลองกด E ใหม่")

    save_debug_screenshot(sct, "process_not_started")
    print("[โพ] เริ่มแปรรูปไม่ได้")
    return False


def wait_processing(sct, on_status=None):
    """
    รอจนแถบ Processing หายไป = แปรรูปเสร็จ
    Returns: True ถ้าเสร็จ, False ถ้าเกินเวลาหรือถูกสั่งพัก
    """
    if not template_available(config.PROCESS_BAR_TEMPLATE):
        print(f"[โพ] ไม่มี process_bar.png - รอแบบจับเวลา "
              f"{config.PROCESS_TIMEOUT:.0f} วิ")
        waited = 0.0
        while waited < config.PROCESS_TIMEOUT:
            if _abort[0]:
                return False
            time.sleep(config.PROCESS_POLL)
            waited += config.PROCESS_POLL
        return True

    t0 = time.time()
    while time.time() - t0 < config.PROCESS_TIMEOUT:
        if _abort[0]:
            print("[โพ] ถูกสั่งพักระหว่างรอ")
            return False
        if not is_processing(sct):
            print(f"[โพ] แถบหายแล้ว - แปรรูปเสร็จ ({time.time() - t0:.0f} วิ)")
            return True
        if on_status:
            left = config.PROCESS_TIMEOUT - (time.time() - t0)
            on_status(f"กำลังแปรรูป... (เหลือเวลารอ {left:.0f} วิ)")
        time.sleep(config.PROCESS_POLL)

    save_debug_screenshot(sct, "process_timeout")
    print(f"[โพ] รอเกิน {config.PROCESS_TIMEOUT:.0f} วิ แถบยังไม่หาย - เริ่มรอบใหม่")
    return False


def walk_back_to_pole():
    """เดินกลับไปที่เสา GARAGE (กลับด้านปุ่มจากขาไป)"""
    print("[กลับ] เดินกลับเสา GARAGE")
    inp.walk_back(config.WALK_TO_PROCESS)
    time.sleep(config.WALK_SETTLE_DELAY)


def one_cycle(sct, on_status=None):
    """
    ทำครบ 1 รอบ: เก็บแท่ง -> ดึงแร่ -> เดินไปโพ -> รอเสร็จ -> เดินกลับ
    Returns: True ถ้าครบรอบ
    """
    def status(msg):
        print(f"[รอบ] {msg}")
        if on_status:
            on_status(msg)

    status("เปิดท้ายรถ")
    if not open_trunk(sct):
        return False

    status("เก็บแท่งที่โพเสร็จเข้าท้ายรถ")
    store_bars(sct)          # ไม่มีก็ข้าม ไม่ถือว่าพลาด

    status("ดึงแร่ดิบออกจากท้ายรถ")
    got_ore = take_ore(sct)

    print("[รอบ] กด ESC ปิดหน้าต่าง")
    inp.press_esc()
    time.sleep(config.AFTER_CLOSE_DELAY)

    if not got_ore:
        print("[รอบ] ไม่มีแร่ดิบในท้ายรถแล้ว - หยุดรอบนี้")
        return False

    if _aborted("รอบ"):
        return False

    status("เดินไปแปรรูป")
    if not start_processing(sct):
        walk_back_to_pole()
        return False

    status("รอแปรรูปเสร็จ")
    done = wait_processing(sct, on_status)

    status("เดินกลับเสา")
    walk_back_to_pole()
    return done
