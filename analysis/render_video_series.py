#!/usr/bin/env python3
"""
Render Episodes 2, 3, and 4 of the orthographic isometric miniature video series,
plus concatenate Episodes 1-4 into lunar_blss_full_series.mp4.
"""

import os
import shutil
import subprocess
import sys
from typing import List, Tuple

from PIL import Image, ImageDraw

from iso_engine import (
    BG_COLOR,
    H,
    IsoBox,
    SS,
    W,
    clamp,
    draw_hud,
    draw_leader_label,
    ease_in_out_cubic,
    encode_episode,
    load_fonts,
    zone_cam,
)

# ===========================================================================
# EPISODE 2: Vadose Zone & Gravity Scaling (16.0 s = 480 frames)
# ===========================================================================
def render_ep2(frame: int, fonts: Tuple) -> Image.Image:
    _, _, f_lbl, f_sub = fonts
    img = Image.new("RGB", (W, H), BG_COLOR)
    draw = ImageDraw.Draw(img)

    c1 = zone_cam(0.0, 0.0)
    c2 = zone_cam(7.5, -2.5)
    c3 = zone_cam(14.5, -5.0)
    if frame < 155:
        cam_x, cam_y = c1
    elif frame < 190:
        u = ease_in_out_cubic((frame - 155) / 35.0)
        cam_x = c1[0] + (c2[0] - c1[0]) * u
        cam_y = c1[1] + (c2[1] - c1[1]) * u
    elif frame < 320:
        cam_x, cam_y = c2
    elif frame < 355:
        u = ease_in_out_cubic((frame - 320) / 35.0)
        cam_x = c2[0] + (c3[0] - c2[0]) * u
        cam_y = c2[1] + (c3[1] - c2[1]) * u
    else:
        cam_x, cam_y = c3

    boxes: List[IsoBox] = []

    # --- SCENE 1: Side-by-side Soil Column Cutaways (x=-1.6 & x=+1.6) ---
    # Base plinths
    for idx, (bx, by) in enumerate([(-2.2, -0.6), (-1.1, -0.6), (0.8, -0.6), (1.9, -0.6)]):
        boxes.append(IsoBox(bx, by, -0.25, 1.05, 1.2, 0.25, "dark", start_frame=idx * 3, layer=0))

    # Left column: Raw Regolith (<1-1000 um) -> waterlogged accent lower half + hypoxic seal
    boxes.append(IsoBox(-2.0, -0.4, 0.0, 1.5, 0.9, 0.85, "accent", start_frame=12, layer=1))
    boxes.append(IsoBox(-2.0, -0.4, 0.85, 1.5, 0.9, 0.75, "mid", start_frame=15, layer=1))
    # Roof cap lifts at frame 50..80
    lift1 = -100.0 * SS * ease_in_out_cubic(clamp((frame - 50) / 30.0)) if frame >= 50 else 0.0
    boxes.append(IsoBox(-2.1, -0.5, 1.60, 1.7, 1.1, 0.22, "dark", start_frame=21, dz_px_extra=lift1, layer=5))

    # Right column: Sintered Ceramic (30-60 um monodisperse pores)
    for ti in range(4):
        pal = "light" if ti % 2 == 0 else "mid"
        boxes.append(IsoBox(1.0, -0.4, ti * 0.40, 1.5, 0.9, 0.36, pal, start_frame=24 + ti * 3, layer=1))
    boxes.append(IsoBox(1.0, -0.4, 1.60, 1.5, 0.9, 0.12, "accent", start_frame=36, layer=1))
    boxes.append(IsoBox(0.9, -0.5, 1.72, 1.7, 1.1, 0.22, "glass", start_frame=39, dz_px_extra=lift1, layer=5))

    # --- SCENE 2: Gravity Capillary Rise Towers (1.0g vs 0.38g vs 0.165g) ---
    kx, ky = 7.5, -2.5
    s2 = 175
    for gi, (dx, pal, h_cap, lbl_h) in enumerate([
        (-2.0, "dark", 0.55, 0.55),   # Earth 1.0 g (2.71 mm)
        (0.0, "mid", 1.25, 1.25),     # Mars 0.38 g
        (2.0, "accent", 2.35, 2.35),  # Moon 0.165 g (6x rise / 4.2-5.2 mm NS-29)
    ]):
        boxes.append(IsoBox(kx + dx - 0.55, ky - 0.55, -0.25, 1.1, 1.1, 0.25, "light", start_frame=s2 + gi * 3, layer=0))
        boxes.append(IsoBox(kx + dx - 0.38, ky - 0.38, 0.0, 0.76, 0.76, h_cap, pal, start_frame=s2 + 12 + gi * 3, layer=1))

    # --- SCENE 3: PWM Passive Capillary Manifold (PSI-187) ---
    px0, py0 = 14.5, -5.0
    s3 = 335
    for pi in range(3):
        boxes.append(IsoBox(px0 - 1.5 + pi * 1.05, py0 - 0.9, -0.25, 1.0, 1.8, 0.25, "mid" if pi % 2 else "light", start_frame=s3 + pi * 3, layer=0))
    # Tapered wedge channels
    boxes.append(IsoBox(px0 - 1.2, py0 - 0.6, 0.0, 2.4, 1.2, 0.25, "dark", start_frame=s3 + 12, layer=1))
    boxes.append(IsoBox(px0 - 1.0, py0 - 0.4, 0.25, 2.0, 0.35, 0.45, "accent", start_frame=s3 + 15, layer=2))
    boxes.append(IsoBox(px0 - 1.0, py0 + 0.1, 0.25, 2.0, 0.35, 0.45, "light", start_frame=s3 + 18, layer=2))
    lift3 = -105.0 * SS * ease_in_out_cubic(clamp((frame - 385) / 30.0)) if frame >= 385 else 0.0
    boxes.append(IsoBox(px0 - 1.25, py0 - 0.65, 0.75, 2.5, 1.3, 0.20, "glass", start_frame=s3 + 24, dz_px_extra=lift3, layer=5))

    boxes.sort(key=lambda b: b.sort_key())
    for b in boxes:
        b.draw(draw, frame, cam_x, cam_y)

    # Labels
    if 70 <= frame < 165:
        p = clamp((frame - 70) / 20.0)
        draw_leader_label(draw, (-1.2, 0.0, 0.6), (-110, -130), "RAW REGOLITH (<1-1000 um)", "CAPILLARY HYPOXIA (<12% AIR)", cam_x, cam_y, p, f_lbl, f_sub, align_right=True)
        draw_leader_label(draw, (1.8, 0.0, 1.0), (120, -110), "SINTERED CERAMIC (30-60 um)", ">25-30% AIR · -2.5 TO -5.0 kPa", cam_x, cam_y, p, f_lbl, f_sub, align_right=False)
    if 215 <= frame < 330:
        p = clamp((frame - 215) / 20.0)
        draw_leader_label(draw, (kx + 2.0, ky, 2.35), (140, -135), "LUNAR 0.165 g CAPILLARY RISE", "6x HEAD EXPANSION · Lc = 4.2-5.2 mm", cam_x, cam_y, p, f_lbl, f_sub, align_right=False)
        draw_leader_label(draw, (kx, ky, 1.25), (140, 45), "MARS 0.38 g vs EARTH 1.0 g", "REDUCED GRAVITY SHIFTS AERATION", cam_x, cam_y, p, f_lbl, f_sub, align_right=False)
    if 405 <= frame:
        p = clamp((frame - 405) / 20.0)
        draw_leader_label(draw, (px0, py0, 0.65), (145, -165), "PWM PASSIVE CAPILLARY MANIFOLD", "PSI-187 · ZERO-PUMP BUBBLE CONTROL", cam_x, cam_y, p, f_lbl, f_sub, align_right=False)
        draw_leader_label(draw, (px0 + 0.8, py0 + 0.2, 0.35), (145, 30), "SLM CERAMIC WICK CHANNELS", "MOLDRUP WLR GAS DIFFUSION", cam_x, cam_y, p, f_lbl, f_sub, align_right=False)

    sub = "01 / PORE-SCALE CUTAWAY" if frame < 165 else ("02 / GRAVITY SCALING (1g -> 0.38g -> 0.165g)" if frame < 330 else "03 / PWM PASSIVE CAPILLARY FLUIDICS")
    draw_hud(draw, "EPISODE 2 · VADOSE PHYSICS & GRAVITY SCALING", sub, frame, 480, fonts)
    return img.resize((1920, 1080), Image.Resampling.LANCZOS)


# ===========================================================================
# EPISODE 3: ESM Equation & Lunar Habitat Scaling Factors (18.0 s = 540 frames)
# ===========================================================================
def render_ep3(frame: int, fonts: Tuple) -> Image.Image:
    _, _, f_lbl, f_sub = fonts
    img = Image.new("RGB", (W, H), BG_COLOR)
    draw = ImageDraw.Draw(img)

    c1 = zone_cam(0.0, 0.0)
    c2 = zone_cam(7.5, -2.5)
    c3 = zone_cam(15.0, -5.0)
    if frame < 165:
        cam_x, cam_y = c1
    elif frame < 205:
        u = ease_in_out_cubic((frame - 165) / 40.0)
        cam_x = c1[0] + (c2[0] - c1[0]) * u
        cam_y = c1[1] + (c2[1] - c1[1]) * u
    elif frame < 350:
        cam_x, cam_y = c2
    elif frame < 390:
        u = ease_in_out_cubic((frame - 350) / 40.0)
        cam_x = c2[0] + (c3[0] - c2[0]) * u
        cam_y = c2[1] + (c3[1] - c2[1]) * u
    else:
        cam_x, cam_y = c3

    boxes: List[IsoBox] = []

    # --- SCENE 1: 5 Terms of the ESM Equation Stacked (Raw vs Sintered at 60 mo) ---
    # Left stack: Raw Regolith ESM (11,910 kg @ 60 mo)
    # Right stack: Sintered Ceramic ESM (3,848 kg @ 60 mo)
    for idx, (bx, pal, h) in enumerate([
        (-1.4, "dark", 0.35),    # M initial
        (-1.4, "mid", 0.45),     # V*Cv
        (-1.4, "light", 0.30),   # P*Cp + C*Cc
        (-1.4, "accent", 1.85),  # Recurring H2O + Buffers + T*Ct
    ]):
        z_acc = [0.0, 0.35, 0.80, 1.10][idx]
        boxes.append(IsoBox(bx, -0.45, z_acc, 1.1, 1.1, h, pal, start_frame=10 + idx * 6, layer=1))

    for idx, (bx, pal, h) in enumerate([
        (1.0, "dark", 0.72),     # M sintering plant (1850 kg)
        (1.0, "mid", 0.18),      # V*Cv (66% smaller volume)
        (1.0, "light", 0.25),    # P*Cp + C*Cc
        (1.0, "accent", 0.22),   # Minimal recurring consumables
    ]):
        z_acc = [0.0, 0.72, 0.90, 1.15][idx]
        boxes.append(IsoBox(bx, -0.45, z_acc, 1.1, 1.1, h, pal, start_frame=36 + idx * 6, layer=1))

    # --- SCENE 2: Crew & Power Scaling (3 / 6 / 12 Crew + Nuclear vs Solar) ---
    cx0, cy0 = 7.5, -2.5
    s2 = 190
    for ci, (dx, h_raw, h_sin) in enumerate([
        (-2.1, 1.1, 0.65),   # 3 Crew -> 15.4 mo breakeven
        (0.0, 2.0, 0.95),    # 6 Crew -> 9.4 mo breakeven
        (2.1, 3.2, 1.35),    # 12 Crew -> 6.5 mo breakeven
    ]):
        boxes.append(IsoBox(cx0 + dx - 0.65, cy0 - 0.4, 0.0, 0.60, 0.80, h_raw, "mid", start_frame=s2 + ci * 6, layer=1))
        boxes.append(IsoBox(cx0 + dx + 0.05, cy0 - 0.4, 0.0, 0.60, 0.80, h_sin, "accent", start_frame=s2 + 3 + ci * 6, layer=1))

    # --- SCENE 3: 4-Architecture Mission Horizon Scaling ---
    mx0, my0 = 15.0, -5.0
    s3 = 375
    # 4 columns: Raw (11.9t), Hydroponics (5.6t), Hybrid (4.6t), Sintered (3.8t) at 60 mo
    for ai, (dx, h, pal) in enumerate([
        (-2.2, 2.8, "dark"),     # Raw Regolith
        (-0.7, 1.35, "mid"),     # Hydroponics (best <6 mo)
        (0.8, 1.10, "light"),    # Hybrid (6-24 mo bridge)
        (2.3, 0.92, "accent"),   # Sintered ISRU (best >24 mo)
    ]):
        boxes.append(IsoBox(mx0 + dx - 0.45, my0 - 0.5, -0.25, 0.95, 1.0, 0.25, "mid", start_frame=s3 + ai * 3, layer=0))
        boxes.append(IsoBox(mx0 + dx - 0.40, my0 - 0.45, 0.0, 0.85, 0.9, h, pal, start_frame=s3 + 12 + ai * 3, layer=1))

    boxes.sort(key=lambda b: b.sort_key())
    for b in boxes:
        b.draw(draw, frame, cam_x, cam_y)

    if 65 <= frame < 170:
        p = clamp((frame - 65) / 20.0)
        draw_leader_label(draw, (-0.85, 0.1, 2.5), (-110, -90), "RAW ESM = M + V·Cv + P·Cp + C·Cc + T·Ct", "11,910 kg @ 60 MO (80% H2O + 145 kg/yr BUFFER)", cam_x, cam_y, p, f_lbl, f_sub, align_right=True)
        draw_leader_label(draw, (1.55, 0.1, 1.15), (125, -135), "SINTERED CERAMIC ESM", "3,848 kg @ 60 MO · 8,062 kg SAVED", cam_x, cam_y, p, f_lbl, f_sub, align_right=False)
    if 230 <= frame < 355:
        p = clamp((frame - 230) / 20.0)
        draw_leader_label(draw, (cx0 + 2.1, cy0, 1.35), (140, -175), "CREW SCALING (3 / 6 / 12 CREW)", "BREAKEVEN SHRINKS: 15.4 -> 9.4 -> 6.5 MO", cam_x, cam_y, p, f_lbl, f_sub, align_right=False)
        draw_leader_label(draw, (cx0, cy0, 0.95), (140, 40), "POWER SCALING: NUCLEAR vs SOLAR", "Cp = 54 kg/kWe (FISSION) vs 237 kg/kWe (PV+RFC)", cam_x, cam_y, p, f_lbl, f_sub, align_right=False)
    if 420 <= frame:
        p = clamp((frame - 420) / 20.0)
        draw_leader_label(draw, (mx0 + 2.3, my0, 0.92), (135, -175), "PHASED ARCHITECTURE CROSSOVER", "<6 MO HYDROPONICS · 6-24 MO HYBRID · >24 MO SINTERED", cam_x, cam_y, p, f_lbl, f_sub, align_right=False)
        draw_leader_label(draw, (mx0 + 0.8, my0, 0.55), (135, 35), "MARS 0.38 g SENSITIVITY", "7,198 kg NET SAVINGS @ 60 MO (6 CREW)", cam_x, cam_y, p, f_lbl, f_sub, align_right=False)

    sub = "01 / BVAD ESM EQUATION ANATOMY" if frame < 170 else ("02 / CREW & POWER INFRASTRUCTURE SCALING" if frame < 355 else "03 / 4-ARCHITECTURE MISSION HORIZON SCALING")
    draw_hud(draw, "EPISODE 3 · ESM MODEL & HABITAT SCALING FACTORS", sub, frame, 540, fonts)
    return img.resize((1920, 1080), Image.Resampling.LANCZOS)


# ===========================================================================
# EPISODE 4: Closed-Loop Multitrophic Scaling (16.0 s = 480 frames)
# ===========================================================================
def render_ep4(frame: int, fonts: Tuple) -> Image.Image:
    _, _, f_lbl, f_sub = fonts
    img = Image.new("RGB", (W, H), BG_COLOR)
    draw = ImageDraw.Draw(img)

    c1 = zone_cam(0.0, 0.0)
    c2 = zone_cam(7.0, -2.5)
    c3 = zone_cam(14.0, -5.0)
    if frame < 155:
        cam_x, cam_y = c1
    elif frame < 190:
        u = ease_in_out_cubic((frame - 155) / 35.0)
        cam_x = c1[0] + (c2[0] - c1[0]) * u
        cam_y = c1[1] + (c2[1] - c1[1]) * u
    elif frame < 320:
        cam_x, cam_y = c2
    elif frame < 355:
        u = ease_in_out_cubic((frame - 320) / 35.0)
        cam_x = c2[0] + (c3[0] - c2[0]) * u
        cam_y = c2[1] + (c3[1] - c2[1]) * u
    else:
        cam_x, cam_y = c3

    boxes: List[IsoBox] = []

    # --- BAY A: 500 C Pyrolytic Regeneration Chamber ---
    for i in range(4):
        boxes.append(IsoBox(-1.3 + (i % 2) * 1.3, -1.3 + (i // 2) * 1.3, -0.25, 1.25, 1.25, 0.25, "light" if i % 2 else "mid", start_frame=i * 3, layer=0))
    boxes.append(IsoBox(-1.1, -1.1, 0.0, 2.2, 2.2, 0.20, "dark", start_frame=12, layer=1))
    boxes.append(IsoBox(-1.1, -1.1, 0.20, 0.22, 2.2, 1.35, "mid", start_frame=15, layer=2))
    boxes.append(IsoBox(-0.88, -1.1, 0.20, 1.98, 0.22, 1.35, "mid", start_frame=18, layer=2))
    # Pyrolytic heater + ceramic tray stack inside
    boxes.append(IsoBox(-0.55, -0.55, 0.20, 1.1, 1.1, 0.55, "accent", start_frame=21, layer=3))
    boxes.append(IsoBox(-0.40, -0.40, 0.75, 0.8, 0.8, 0.25, "light", start_frame=24, layer=3))
    lift1 = -110.0 * SS * ease_in_out_cubic(clamp((frame - 55) / 30.0)) if frame >= 55 else 0.0
    boxes.append(IsoBox(-1.2, -1.2, 1.55, 2.4, 2.4, 0.22, "dark", start_frame=30, dz_px_extra=lift1, layer=6))

    # --- BAY B: Mycoponics Bay (Pleurotus straw upcycling) ---
    bx0, by0 = 7.0, -2.5
    s2 = 180
    boxes.append(IsoBox(bx0 - 1.2, by0 - 1.2, -0.25, 2.4, 2.4, 0.25, "dark", start_frame=s2, layer=0))
    boxes.append(IsoBox(bx0 - 1.1, by0 - 1.1, 0.0, 0.22, 2.2, 1.35, "mid", start_frame=s2 + 3, layer=2))
    boxes.append(IsoBox(bx0 - 0.88, by0 - 1.1, 0.0, 1.98, 0.22, 1.35, "mid", start_frame=s2 + 6, layer=2))
    for ti in range(3):
        boxes.append(IsoBox(bx0 - 0.65, by0 - 0.65, 0.1 + ti * 0.42, 1.3, 1.3, 0.18, "light", start_frame=s2 + 12 + ti * 3, layer=3))
        boxes.append(IsoBox(bx0 - 0.35, by0 - 0.35, 0.28 + ti * 0.42, 0.45, 0.45, 0.14, "accent", start_frame=s2 + 15 + ti * 3, layer=3))
    lift2 = -110.0 * SS * ease_in_out_cubic(clamp((frame - 225) / 30.0)) if frame >= 225 else 0.0
    boxes.append(IsoBox(bx0 - 1.2, by0 - 1.2, 1.35, 2.4, 2.4, 0.22, "mid", start_frame=s2 + 24, dz_px_extra=lift2, layer=6))

    # --- BAY C: External BioRock Chemostat & LECA Tailings Yard ---
    cx0, cy0 = 14.0, -5.0
    s3 = 340
    for i in range(4):
        boxes.append(IsoBox(cx0 - 1.3 + (i % 2) * 1.3, cy0 - 1.3 + (i // 2) * 1.3, -0.25, 1.25, 1.25, 0.25, "light" if i % 2 else "mid", start_frame=s3 + i * 3, layer=0))
    # Bioreactor cylinder-like tower + LECA tailings pavers
    boxes.append(IsoBox(cx0 - 0.8, cy0 - 0.8, 0.0, 1.1, 1.1, 1.35, "dark", start_frame=s3 + 12, layer=2))
    boxes.append(IsoBox(cx0 - 0.6, cy0 - 0.6, 1.35, 0.7, 0.7, 0.35, "accent", start_frame=s3 + 15, layer=3))
    for ti in range(3):
        boxes.append(IsoBox(cx0 + 0.55, cy0 - 0.9 + ti * 0.65, 0.0, 0.55, 0.55, 0.28, "light", start_frame=s3 + 18 + ti * 3, layer=2))

    boxes.sort(key=lambda b: b.sort_key())
    for b in boxes:
        b.draw(draw, frame, cam_x, cam_y)

    if 75 <= frame < 165:
        p = clamp((frame - 75) / 20.0)
        draw_leader_label(draw, (0.0, 0.0, 0.85), (145, -175), "500 °C PYROLYTIC BAKE-OUT", "OXIDIZES BIOFILMS · RECOVERS CO2, H2O & ASH", cam_x, cam_y, p, f_lbl, f_sub, align_right=False)
    if 240 <= frame < 330:
        p = clamp((frame - 240) / 20.0)
        draw_leader_label(draw, (bx0, by0, 0.95), (145, -175), "SAPROTROPHIC MYCOPONICS", "UPCYCLES 40-60% INEDIBLE STRAW + POLYOLS", cam_x, cam_y, p, f_lbl, f_sub, align_right=False)
    if 395 <= frame:
        p = clamp((frame - 395) / 20.0)
        draw_leader_label(draw, (cx0 - 0.2, cy0 - 0.2, 1.35), (145, -175), "DECOUPLED BIOWEATHERING REACTOR", "MINERAL REPLENISHMENT · ZERO DUST IN HABITAT", cam_x, cam_y, p, f_lbl, f_sub, align_right=False)
        draw_leader_label(draw, (cx0 + 0.8, cy0 + 0.4, 0.25), (145, 35), "LECA & SINTERED TAILINGS", "DRAINAGE BEDS + ROADWAY PAVERS", cam_x, cam_y, p, f_lbl, f_sub, align_right=False)

    sub = "01 / PYROLYTIC SUBSTRATE REGENERATION" if frame < 165 else ("02 / MYCOPONIC BIOMASS UPCYCLING" if frame < 330 else "03 / BIO-ISRU & TAILINGS VALORIZATION")
    draw_hud(draw, "EPISODE 4 · CLOSED-LOOP MULTITROPHIC SCALING", sub, frame, 480, fonts)
    return img.resize((1920, 1080), Image.Resampling.LANCZOS)


def main():
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    docs_assets = os.path.join(repo_root, "docs", "assets")
    inter_assets = os.path.join(repo_root, "interactive", "assets")
    os.makedirs(docs_assets, exist_ok=True)
    os.makedirs(inter_assets, exist_ok=True)
    fonts = load_fonts()

    specs = [
        ("Ep2", 480, 110, render_ep2, "ep2_vadose_capillary_physics.mp4", "ep2_poster.png"),
        ("Ep3", 540, 120, render_ep3, "ep3_esm_habitat_scaling.mp4", "ep3_poster.png"),
        ("Ep4", 480, 110, render_ep4, "ep4_closed_loop_scaling.mp4", "ep4_poster.png"),
    ]
    for label, total_f, p_frame, fn, mp4_name, p_name in specs:
        mp4_out = os.path.join(docs_assets, mp4_name)
        p_out = os.path.join(docs_assets, p_name)
        encode_episode(mp4_out, p_out, total_f, p_frame, fn, fonts, label)
        shutil.copy2(mp4_out, os.path.join(inter_assets, mp4_name))
        shutil.copy2(p_out, os.path.join(inter_assets, p_name))

    # Concatenate Episodes 1-4 into lunar_blss_full_series.mp4
    concat_txt = os.path.join(docs_assets, "_concat_list.txt")
    with open(concat_txt, "w") as f:
        for name in [
            "lunar_blss_intro.mp4",
            "ep2_vadose_capillary_physics.mp4",
            "ep3_esm_habitat_scaling.mp4",
            "ep4_closed_loop_scaling.mp4",
        ]:
            f.write(f"file '{os.path.join(docs_assets, name)}'\n")

    full_mp4 = os.path.join(docs_assets, "lunar_blss_full_series.mp4")
    res = subprocess.run(
        ["/opt/homebrew/bin/ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat_txt, "-c", "copy", "-movflags", "+faststart", full_mp4],
        capture_output=True,
        text=True,
    )
    os.remove(concat_txt)
    if res.returncode != 0:
        print("Concat failed:", res.stderr, file=sys.stderr)
        sys.exit(res.returncode)
    shutil.copy2(full_mp4, os.path.join(inter_assets, "lunar_blss_full_series.mp4"))
    print(f"[OK] Full 4-episode reel -> {full_mp4}")


if __name__ == "__main__":
    main()
