"""
smelt_detector.py - อ่านหน้าจอให้บอทแปรรูป

  - หาช่องไอเทม (แร่ดิบ / แท่งที่โพเสร็จ) ในกระเป๋าหรือท้ายรถ
  - เช็คว่าเมนู SYSTEM GARAGE / หน้าท้ายรถ เปิดอยู่ไหม
  - เช็คว่ากำลังแปรรูปอยู่ไหม (แถบ Processing ล่างจอ)
"""

import os
import time

import cv2
import numpy as np

import config

DEBUG_DIR = config.DEBUG_DIR


def _imread(path):
    """อ่านภาพได้แม้ path มีอักษรไทย (cv2.imread ใช้ path แบบ ANSI อ่านไม่ออก)"""
    try:
        data = np.fromfile(path, dtype=np.uint8)
    except OSError:
        return None
    if data.size == 0:
        return None
    return cv2.imdecode(data, cv2.IMREAD_COLOR)


def _imwrite(path, img):
    """เขียนภาพได้แม้ path มีอักษรไทย"""
    ok, buf = cv2.imencode(".png", img)
    if ok:
        buf.tofile(path)
    return ok


def _grab(sct, region):
    return cv2.cvtColor(np.array(sct.grab(region)), cv2.COLOR_BGRA2BGR)


def _scale_template(img):
    """ย่อ/ขยาย template (จับที่ 1080p) ให้ตรงสเกลจอปัจจุบัน"""
    if abs(config.SCALE - 1.0) < 0.01:
        return img
    h, w = img.shape[:2]
    nw, nh = max(1, int(w * config.SCALE)), max(1, int(h * config.SCALE))
    interp = cv2.INTER_AREA if config.SCALE < 1 else cv2.INTER_CUBIC
    return cv2.resize(img, (nw, nh), interpolation=interp)


_cache = {}


def _colour_sig(bgr):
    """
    ลายเซ็นสีของไอคอน: (hue เฉลี่ยแบบวงกลม, ความอิ่มสีเฉลี่ย)
    ดูเฉพาะพิกเซลสว่าง = ตัวไอคอน ไม่เอาพื้นหลังดำของช่อง
    """
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    mask = hsv[:, :, 2] > 60
    if int(mask.sum()) < 20:
        return None
    hue_deg = hsv[:, :, 0][mask].astype(float) * 2.0
    sat = hsv[:, :, 1][mask].astype(float)
    ang = np.deg2rad(hue_deg)
    hue = np.rad2deg(np.arctan2(np.sin(ang).mean(), np.cos(ang).mean())) % 360.0
    return hue, float(sat.mean())


def _colour_gap(a, b):
    """ต่างกันแค่ไหน คืน (องศา hue, ความอิ่มสี)"""
    if a is None or b is None:
        return 0.0, 0.0
    dh = abs(a[0] - b[0])
    dh = min(dh, 360.0 - dh)
    return dh, abs(a[1] - b[1])


def _template(path):
    if path not in _cache:
        img = _imread(path)
        _cache[path] = _scale_template(img) if img is not None else None
    return _cache[path]


def template_available(path):
    return _template(path) is not None


def _match(sct, path, region, threshold):
    """บริเวณ region ตรงกับ template ไหม — ไม่มีไฟล์ template → False"""
    tmpl = _template(path)
    if tmpl is None:
        return False
    scene = _grab(sct, region)
    if tmpl.shape[0] > scene.shape[0] or tmpl.shape[1] > scene.shape[1]:
        return False
    return cv2.minMaxLoc(cv2.matchTemplate(scene, tmpl,
                                           cv2.TM_CCOEFF_NORMED))[1] >= threshold


def is_garage_menu_open(sct):
    """หน้า SYSTEM GARAGE เปิดอยู่ไหม (หลังกด E ที่เสา)"""
    return _match(sct, config.GARAGE_MENU_TEMPLATE, config.GARAGE_MENU_REGION,
                  config.GARAGE_MENU_THRESHOLD)


def is_trunk_open(sct):
    """หน้าท้ายรถ (INVENTORY | SECONDARY) เปิดอยู่ไหม"""
    return _match(sct, config.TRUNK_TEMPLATE, config.TRUNK_CHECK_REGION,
                  config.TRUNK_MATCH_THRESHOLD)


def is_processing(sct):
    """
    กำลังแปรรูปอยู่ไหม — ดูแถบ Processing ล่างจอ
    แถบหายไป = แปรรูปเสร็จแล้ว
    """
    return _match(sct, config.PROCESS_BAR_TEMPLATE, config.PROCESS_BAR_REGION,
                  config.PROCESS_BAR_THRESHOLD)


def find_item(sct, template_path, region, label="ไอเทม"):
    """
    หาช่องไอเทมในบริเวณที่กำหนด

    แร่คนละชนิดรูปทรงเหมือนกันแต่คนละสี (เหล็กสีเทา ทองแดงสีส้ม)
    template matching ดูรูปทรงเป็นหลัก จึงสับสนได้ ต้องเทียบสีซ้ำอีกชั้น
    ตัวที่รูปเข้าแต่สีไม่ตรงจะถูกข้ามไปดูตัวถัดไป

    Returns: (x, y) กลางช่อง หรือ None
    """
    tmpl = _template(template_path)
    if tmpl is None:
        print(f"[detector] ไม่พบ {os.path.basename(template_path)} - รัน calibrate ก่อน")
        return None

    scene = _grab(sct, region)
    if tmpl.shape[0] > scene.shape[0] or tmpl.shape[1] > scene.shape[1]:
        return None

    res = cv2.matchTemplate(scene, tmpl, cv2.TM_CCOEFF_NORMED)
    th, tw = tmpl.shape[:2]
    want = _colour_sig(tmpl) if config.CHECK_ITEM_COLOUR else None
    best_score = None

    for _ in range(config.MATCH_CANDIDATES):
        _, score, _, loc = cv2.minMaxLoc(res)
        if best_score is None:
            best_score = score
        if score < config.TEMPLATE_MATCH_THRESHOLD:
            break

        if want is not None:
            patch = scene[loc[1]:loc[1] + th, loc[0]:loc[0] + tw]
            dh, ds = _colour_gap(want, _colour_sig(patch))
            if ds > config.COLOUR_SAT_TOLERANCE or dh > config.COLOUR_HUE_TOLERANCE:
                print(f"[detector] เจอรูปคล้าย{label} (score={score:.2f}) "
                      f"แต่สีไม่ตรง (hue ต่าง {dh:.0f}° sat ต่าง {ds:.0f}) - ข้าม")
                # ลบยอดนี้ทิ้งแล้วดูตัวถัดไป
                x0 = max(0, loc[0] - tw // 2)
                y0 = max(0, loc[1] - th // 2)
                res[y0:loc[1] + th // 2, x0:loc[0] + tw // 2] = -1.0
                continue

        x = region["left"] + loc[0] + tw // 2
        y = region["top"] + loc[1] + th // 2
        print(f"[detector] เจอ{label}ที่ ({x}, {y}) score={score:.2f}")
        return (x, y)

    print(f"[detector] หา{label}ไม่เจอ (score สูงสุด={best_score:.2f})")
    return None


def region_snapshot(sct, region):
    """ภาพย่อของบริเวณหนึ่ง ไว้เทียบว่ามีอะไรเปลี่ยนไปไหม"""
    return _grab(sct, region).copy()


def region_changed(sct, region, before, min_px=200):
    """
    บริเวณนี้เปลี่ยนไปจากภาพ before ไหม
    ใช้ยืนยันว่า "มีของถูกย้ายออกไปจริง" แม้จะยังเหลือของชนิดเดิมอยู่
    """
    after = _grab(sct, region)
    if before is None or before.shape != after.shape:
        return True
    diff = cv2.absdiff(cv2.cvtColor(before, cv2.COLOR_BGR2GRAY),
                       cv2.cvtColor(after, cv2.COLOR_BGR2GRAY))
    changed = cv2.countNonZero(cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)[1])
    return changed >= min_px


def region_diff_pct(sct, region, ref, thr=25):
    """บริเวณนี้ต่างจากภาพอ้างอิงกี่ % ของพื้นที่"""
    if ref is None:
        return 100.0
    now = _grab(sct, region)
    if ref.shape != now.shape:
        return 100.0
    d = cv2.absdiff(cv2.cvtColor(ref, cv2.COLOR_BGR2GRAY),
                    cv2.cvtColor(now, cv2.COLOR_BGR2GRAY))
    changed = cv2.countNonZero(cv2.threshold(d, thr, 255, cv2.THRESH_BINARY)[1])
    return changed / float(now.shape[0] * now.shape[1]) * 100.0


def _prune_debug(name, keep):
    try:
        old = sorted(f for f in os.listdir(DEBUG_DIR)
                     if f.startswith(name + "_") and f.endswith(".png"))
        for f in old[:max(0, len(old) - keep)]:
            os.remove(os.path.join(DEBUG_DIR, f))
    except OSError:
        pass


def save_debug_screenshot(sct, name):
    """เซฟภาพเต็มจอตอนบอทพลาด (เก็บแค่ไม่กี่ไฟล์ล่าสุดต่อชนิดปัญหา)"""
    keep = config.DEBUG_KEEP_PER_NAME
    if keep <= 0:
        return
    os.makedirs(DEBUG_DIR, exist_ok=True)
    bgr = _grab(sct, sct.monitors[1])
    path = os.path.join(DEBUG_DIR, f"{name}_{int(time.time())}.png")
    _imwrite(path, bgr)
    _prune_debug(name, keep)
    print(f"[detector] บันทึก debug: {path}")
