"""
smelt_actions.py - ลำดับการทำงานของบอทแปรรูป

ลูป:
  ยืนที่จุดแปรรูป กด E
    - แถบ Processing ขึ้น = ยังมีแร่ในตัว -> รอจนเสร็จ -> กด E ต่อเลย
    - แถบไม่ขึ้น = แร่หมด -> เดินกลับเสา GARAGE
                    -> E เปิดเมนู -> L เปิดท้ายรถ
                    -> เก็บแท่งที่โพเสร็จเข้าท้ายรถ
                    -> ดึงแร่ดิบออกมา (Max) -> ESC
                    -> เดินกลับจุดแปรรูป -> กด E ต่อ

แร่ 1 กระเป๋าโพได้หลายรอบ จึงไม่ต้องวิ่งไปท้ายรถทุกรอบ

ความปลอดภัย: คลิกเมาส์ตอนไม่มีหน้าต่างเปิด = ต่อยคนที่ยืนแถวนั้น
บอทจะคลิกเฉพาะตอนยืนยันได้ว่าหน้าต่างท้ายรถเปิดจริงเท่านั้น
"""

import time

import config
import smelt_input as inp
from smelt_detector import (find_item, is_garage_menu_open, is_trunk_open,
                            is_processing, template_available,
                            region_snapshot, region_changed, region_diff_pct,
                            save_debug_screenshot)

_abort = [False]
_idle_ref = [None]     # ภาพบริเวณแถบตอนยังไม่ได้โพ (ไว้เทียบว่าแถบหายยัง)


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


def _move_item(sct, template, from_region, to_region, to_base, label, tag,
               debug_name="move_failed"):
    """
    ลากไอเทมข้ามฝั่ง แล้วกด Max -> O

    เกณฑ์ว่าสำเร็จ: ไอเทมไปโผล่ฝั่งปลายทาง
    (ห้ามใช้ "หายไปจากฝั่งต้นทาง" — ท้ายรถมีของมากกว่าที่กระเป๋ารับไหว
     ดึง Max แล้วยังเหลือของเดิมอยู่ ทั้งที่ย้ายสำเร็จ)
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
            print(f"[{tag}] ไม่มี{label}ให้ย้ายแล้ว")
            return False

        before = region_snapshot(sct, from_region)
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

        if find_item(sct, template, to_region, label) is not None:
            print(f"[{tag}] ย้าย{label}สำเร็จ (เจอที่ปลายทางแล้ว)")
            return True
        if region_changed(sct, from_region, before):
            print(f"[{tag}] ฝั่งต้นทางเปลี่ยนไป — ถือว่าย้ายสำเร็จ")
            return True
        print(f"[{tag}] ไม่มีอะไรขยับ - ลองจุดปล่อยถัดไป")

    save_debug_screenshot(sct, debug_name)
    return False


def store_bars(sct):
    """เอาแท่งที่โพเสร็จในกระเป๋า ใส่กลับท้ายรถ (ไม่มีก็ข้าม)"""
    if find_item(sct, config.BAR_TEMPLATE, config.INVENTORY_REGION,
                 "แท่งที่โพเสร็จ") is None:
        print("[เก็บ] ไม่มีแท่งที่โพเสร็จในกระเป๋า - ข้าม")
        return True
    return _move_item(sct, config.BAR_TEMPLATE, config.INVENTORY_REGION,
                      config.TRUNK_REGION, config.DROP_TO_TRUNK,
                      "แท่งที่โพเสร็จ", "เก็บ", "store_bars_failed")


def take_ore(sct):
    """ดึงแร่ดิบจากท้ายรถออกมาใส่กระเป๋า (Max)"""
    return _move_item(sct, config.ORE_TEMPLATE, config.TRUNK_REGION,
                      config.INVENTORY_REGION, config.DROP_TO_INVENTORY,
                      "แร่ดิบ", "ดึง", "take_ore_failed")


def press_start_process(sct):
    """
    กด E เริ่มแปรรูป (ไม่เดิน - ต้องยืนอยู่จุดโพแล้ว)
    Returns: True ถ้าแถบ Processing ขึ้น = มีแร่ในตัว โพได้
             False = ไม่มีแร่ในตัวแล้ว ต้องไปเอาจากท้ายรถ
    """
    check_bar = template_available(config.PROCESS_BAR_TEMPLATE)
    # เก็บภาพบริเวณแถบตอนยังไม่เริ่ม ไว้เทียบทีหลังว่าแถบหายไปหรือยัง
    _idle_ref[0] = region_snapshot(sct, config.PROCESS_BAR_REGION)
    if not check_bar:
        print("[โพ] (ไม่มี process_bar.png - ใช้วิธีเทียบภาพแทน)")

    for attempt in range(1, config.PROCESS_START_RETRIES + 1):
        if _aborted("โพ"):
            return False
        print(f"[โพ] กด E เริ่มแปรรูป (ครั้งที่ {attempt})...")
        inp.press_e()
        time.sleep(config.WALK_SETTLE_DELAY)
        if not check_bar:
            pct = region_diff_pct(sct, config.PROCESS_BAR_REGION, _idle_ref[0])
            if pct >= config.PROCESS_CHANGE_MIN_PCT:
                print(f"[โพ] แถบขึ้นแล้ว (ภาพต่างไป {pct:.1f}%) - ยังมีแร่ในตัว")
                return True
            print(f"[โพ] ภาพไม่เปลี่ยน ({pct:.1f}%) - แถบยังไม่ขึ้น")
            continue
        if is_processing(sct):
            print("[โพ] แถบ Processing ขึ้นแล้ว - ยังมีแร่ในตัว")
            return True
        print("[โพ] แถบ Processing ไม่ขึ้น - ลองกด E ใหม่")

    print("[โพ] กด E แล้วไม่ติด - แร่ในตัวน่าจะหมดแล้ว")
    return False


def walk_to_process():
    """เดินจากเสา GARAGE ไปจุดแปรรูป"""
    print(f"[เดิน] ไปจุดแปรรูป {config.WALK_TO_PROCESS}")
    inp.walk(config.WALK_TO_PROCESS, prep=config.WALK_PREP,
             prep_delay=config.WALK_PREP_DELAY,
             prep_after=config.WALK_PREP_AFTER)
    time.sleep(config.WALK_SETTLE_DELAY)


def wait_processing(sct, on_status=None):
    """
    รอจนแถบ Processing หายไป = แปรรูปเสร็จ
    Returns: True ถ้าเสร็จ, False ถ้าเกินเวลาหรือถูกสั่งพัก
    """
    if not template_available(config.PROCESS_BAR_TEMPLATE):
        # ไม่มี template ก็ยังรู้ได้ - เทียบว่าบริเวณแถบเปลี่ยนไปกี่ %
        # แผงแถบโพหายไป = ภาพกลับไปเหมือนตอนก่อนเริ่ม
        idle = _idle_ref[0]
        if idle is None:
            print(f"[โพ] ไม่มีทั้ง template และภาพอ้างอิง - "
                  f"รอแบบจับเวลา {config.PROCESS_TIMEOUT:.0f} วิ")
            waited = 0.0
            while waited < config.PROCESS_TIMEOUT:
                if _abort[0]:
                    return False
                time.sleep(config.PROCESS_POLL)
                waited += config.PROCESS_POLL
            return True

        print("[โพ] ไม่มี process_bar.png - ใช้วิธีเทียบภาพแทน")
        t0 = time.time()
        while time.time() - t0 < config.PROCESS_TIMEOUT:
            if _abort[0]:
                return False
            pct = region_diff_pct(sct, config.PROCESS_BAR_REGION, idle)
            if pct < config.PROCESS_CHANGE_MIN_PCT:
                print(f"[โพ] ภาพกลับเหมือนเดิม ({pct:.1f}%) - แปรรูปเสร็จ "
                      f"({time.time() - t0:.0f} วิ)")
                return True
            if on_status:
                on_status(f"กำลังแปรรูป... (ต่างจากตอนว่าง {pct:.0f}%)")
            time.sleep(config.PROCESS_POLL)
        save_debug_screenshot(sct, "process_timeout")
        return False

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
    inp.walk_back(config.WALK_TO_PROCESS, prep=config.WALK_PREP,
                  prep_delay=config.WALK_PREP_DELAY,
                  prep_after=config.WALK_PREP_AFTER)
    time.sleep(config.WALK_SETTLE_DELAY)


def refill_from_trunk(sct, on_status=None):
    """
    ไปเอาแร่จากท้ายรถ: เปิดท้ายรถ -> เก็บแท่งที่โพเสร็จ -> ดึงแร่ใหม่
    (ต้องยืนอยู่ที่เสา GARAGE แล้ว)

    ขั้นตอนนี้ใช้เมาส์ลาก -> ถ้าจอดเกมไว้นอกจอ ต้องดึงกลับเข้าจอก่อน
    (cursor ของ Windows ไปพิกัดนอกจอไม่ได้) เสร็จแล้วส่งกลับไปจอดเหมือนเดิม
    Returns: True ถ้าได้แร่มา
    """
    was_parked = inp.is_parked()
    if was_parked:
        inp.unpark_game()
    try:
        return _refill_from_trunk_inner(sct, on_status)
    finally:
        if was_parked:
            inp.park_game()


def _refill_from_trunk_inner(sct, on_status=None):
    def status(msg):
        print(f"[เติม] {msg}")
        if on_status:
            on_status(msg)

    status("เปิดท้ายรถ")
    if not open_trunk(sct):
        return False

    status("เก็บแท่งที่โพเสร็จเข้าท้ายรถ")
    store_bars(sct)          # ไม่มีก็ข้าม ไม่ถือว่าพลาด

    status("ดึงแร่ดิบออกจากท้ายรถ")
    got_ore = take_ore(sct)

    print("[เติม] กด ESC ปิดหน้าต่าง")
    inp.press_esc()
    time.sleep(config.AFTER_CLOSE_DELAY)

    if not got_ore:
        print("[เติม] ไม่มีแร่ดิบในท้ายรถแล้ว")
    return got_ore


def _wait_and_release(sct, on_status=None):
    """
    รอโพให้เสร็จ - ช่วงนี้บอทไม่ต้องใช้เกมเลย (แค่ดูภาพ)
    เลยคืนโฟกัสให้หน้าต่างที่ผู้ใช้ใช้อยู่ และจอดเกมนอกจอได้ถ้าตั้งไว้
    พอเสร็จค่อยดึงเกมกลับมา
    """
    prev = inp.get_foreground() if config.RESTORE_FOCUS_AFTER else None
    if prev and prev == inp._find_game_hwnd():
        prev = None

    parked = False
    if config.PARK_GAME_OFFSCREEN and config.CAPTURE_MODE == "window":
        parked = inp.park_game()
    if prev:
        print("[โพ] คืนโฟกัสให้ผู้ใช้ระหว่างรอ")
        inp.restore_foreground(prev)

    try:
        return wait_processing(sct, on_status)
    finally:
        if parked:
            inp.unpark_game()
        inp.focus_game()


def one_cycle(sct, state, on_status=None):
    """
    ทำ 1 รอบ โดยจำว่าตอนนี้ยืนอยู่ตรงไหน (state["at_process"])

    มีแร่ในตัว -> โพเลย ไม่ต้องไปท้ายรถ
    แร่หมด    -> เดินกลับเสา เอาแท่งเก็บ ดึงแร่ใหม่ เดินกลับมาโพ

    Returns: True ถ้ารอบนี้ได้โพจริง
    """
    def status(msg):
        if on_status:
            on_status(msg)

    if _aborted("รอบ"):
        return False

    # ยังไม่ได้อยู่จุดโพ -> เดินไปก่อน
    if not state.get("at_process"):
        status("เดินไปจุดแปรรูป")
        walk_to_process()
        state["at_process"] = True

    # ลองโพก่อนเลย - ติดแปลว่ายังมีแร่ในตัว
    status("กด E เริ่มแปรรูป")
    if press_start_process(sct):
        status("รอแปรรูปเสร็จ")
        _wait_and_release(sct, on_status)
        return True

    # โพไม่ติด = แร่หมด -> ไปเอาจากท้ายรถ
    status("แร่หมด - เดินกลับไปเอาที่ท้ายรถ")
    walk_back_to_pole()
    state["at_process"] = False

    if not refill_from_trunk(sct, on_status):
        return False

    status("เดินกลับไปจุดแปรรูป")
    walk_to_process()
    state["at_process"] = True

    status("กด E เริ่มแปรรูป")
    if not press_start_process(sct):
        save_debug_screenshot(sct, "process_not_started")
        return False

    status("รอแปรรูปเสร็จ")
    _wait_and_release(sct, on_status)
    return True
