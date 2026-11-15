#!/usr/bin/env python3
"""
v2 Complete Remake of Episodes 2, 3, and 4:
Recognizable 3D isometric miniature objects + live animated research graphs
from analysis/output/esm_4arch_comparison.csv and paper hydrodynamics/ESM models.
"""

import csv
import math
import os
import shutil
import subprocess
import sys
from typing import List, Tuple

from PIL import Image, ImageDraw

from iso_engine import (
    ACCENT_COLOR,
    BG_COLOR,
    DARK_COLOR,
    H,
    INK_COLOR,
    IsoBox,
    IsoCylinder,
    IsoDome,
    IsoDrawable,
    IsoStrut,
    MID_COLOR,
    SS,
    W,
    clamp,
    draw_graph_panel,
    draw_hud,
    draw_leader_label,
    ease_in_out_cubic,
    encode_episode,
    load_fonts,
    zone_cam,
)


def load_esm_csv(repo_root: str) -> List[dict]:
    path = os.path.join(repo_root, "analysis", "output", "esm_4arch_comparison.csv")
    rows = []
    with open(path, newline="") as f:
        for r in csv.DictReader(f):
            rows.append({k: float(v) for k, v in r.items()})
    return rows


# ===========================================================================
# EPISODE 2 (v2): Pore Physics, Gravity Scaling & Live Fig. 3 Graph (18s = 540f)
# ===========================================================================
def render_ep2(frame: int, fonts: Tuple) -> Image.Image:
    _, _, f_lbl, f_sub = fonts
    img = Image.new("RGB", (W, H), BG_COLOR)
    draw = ImageDraw.Draw(img)

    # Shift camera slightly right of world objects so the live Fig. 3 graph sits cleanly on the right
    c1 = (zone_cam(0.0, 0.0)[0] + 240, zone_cam(0.0, 0.0)[1])
    c2 = (zone_cam(7.5, -2.5)[0] + 240, zone_cam(7.5, -2.5)[1])
    c3 = (zone_cam(14.5, -5.0)[0] + 240, zone_cam(14.5, -5.0)[1])

    if frame < 180:
        cam_x, cam_y = c1
    elif frame < 215:
        u = ease_in_out_cubic((frame - 180) / 35.0)
        cam_x = c1[0] + (c2[0] - c1[0]) * u
        cam_y = c1[1] + (c2[1] - c1[1]) * u
    elif frame < 360:
        cam_x, cam_y = c2
    elif frame < 395:
        u = ease_in_out_cubic((frame - 360) / 35.0)
        cam_x = c2[0] + (c3[0] - c2[0]) * u
        cam_y = c2[1] + (c3[1] - c2[1]) * u
    else:
        cam_x, cam_y = c3

    objs: List[IsoDrawable] = []

    # --- SCENE 1: Cylindrical Soil Column Cutaways ---
    # Left: Raw Regolith Cylinder (waterlogged accent bottom + hypoxic dust top)
    objs.append(IsoCylinder(-1.7, 0.0, -0.20, 0.95, 0.95, 0.20, "dark", segments=12, start_frame=0, layer=0))
    objs.append(IsoCylinder(-1.7, 0.0, 0.0, 0.78, 0.78, 0.85, "accent", segments=12, start_frame=9, layer=1))
    objs.append(IsoCylinder(-1.7, 0.0, 0.85, 0.78, 0.78, 0.65, "mid", segments=12, start_frame=12, layer=1))
    lift1 = -95.0 * SS * ease_in_out_cubic(clamp((frame - 50) / 30.0)) if frame >= 50 else 0.0
    objs.append(IsoCylinder(-1.7, 0.0, 1.50, 0.86, 0.86, 0.18, "dark", segments=12, start_frame=18, dz_px_extra=lift1, layer=5))

    # Right: Sintered Ceramic Cylinder (layered monodisperse rings + bio plant sprout on top)
    objs.append(IsoCylinder(1.2, 0.0, -0.20, 0.95, 0.95, 0.20, "dark", segments=12, start_frame=6, layer=0))
    for ti in range(4):
        objs.append(IsoCylinder(1.2, 0.0, ti * 0.36, 0.78, 0.78, 0.32, "light" if ti % 2 == 0 else "mid", segments=12, start_frame=21 + ti * 3, layer=1))
    objs.append(IsoCylinder(1.2, 0.0, 1.44, 0.32, 0.22, 0.32, "bio", segments=8, start_frame=33, layer=2))
    objs.append(IsoDome(1.2, 0.0, 1.48, 0.86, 0.55, "glass", rings=2, segments=12, start_frame=36, dz_px_extra=lift1, layer=5))

    # --- SCENE 2: Gravity Capillary Rise Columns (Earth 1g vs Mars 0.38g vs Moon 0.165g) ---
    kx, ky = 7.5, -2.5
    s2 = 200
    for gi, (dx, pal, h_cap) in enumerate([(-1.8, "dark", 0.50), (0.0, "mid", 1.20), (1.8, "accent", 2.30)]):
        objs.append(IsoCylinder(kx + dx, ky, -0.20, 0.62, 0.62, 0.20, "light", segments=10, start_frame=s2 + gi * 3, layer=0))
        objs.append(IsoCylinder(kx + dx, ky, 0.0, 0.42, 0.42, h_cap, pal, segments=12, start_frame=s2 + 12 + gi * 3, layer=1))

    # --- SCENE 3: PWM Passive Capillary Tapered Manifold (PSI-187) ---
    px0, py0 = 14.5, -5.0
    s3 = 375
    objs.append(IsoBox(px0 - 1.4, py0 - 0.9, -0.20, 2.8, 1.8, 0.20, "dark", start_frame=s3, layer=0))
    objs.append(IsoBox(px0 - 1.2, py0 - 0.7, 0.0, 2.4, 1.4, 0.22, "mid", start_frame=s3 + 6, layer=1))
    # Tapered wedge capillary channels + fluid reservoir cylinder
    objs.append(IsoBox(px0 - 1.0, py0 - 0.45, 0.22, 1.9, 0.32, 0.38, "accent", start_frame=s3 + 12, layer=2))
    objs.append(IsoBox(px0 - 1.0, py0 + 0.08, 0.22, 1.9, 0.32, 0.38, "bio", start_frame=s3 + 15, layer=2))
    objs.append(IsoCylinder(px0 + 0.95, py0, 0.22, 0.34, 0.34, 0.65, "light", segments=10, start_frame=s3 + 18, layer=2))
    lift3 = -95.0 * SS * ease_in_out_cubic(clamp((frame - 425) / 30.0)) if frame >= 425 else 0.0
    objs.append(IsoBox(px0 - 1.25, py0 - 0.75, 0.65, 2.5, 1.5, 0.16, "glass", start_frame=s3 + 24, dz_px_extra=lift3, layer=5))

    objs.sort(key=lambda o: o.sort_key())
    for o in objs:
        o.draw(draw, frame, cam_x, cam_y)

    # Live Fig. 3 Hydrodynamics Graph on right side of frame
    air_curve = [(0.0, 0.08), (0.15, 0.14), (0.28, 0.42), (0.45, 0.56), (0.65, 0.72), (0.85, 0.86), (1.0, 0.92)]
    suction_curve = [(0.0, 0.95), (0.18, 0.72), (0.30, 0.46), (0.48, 0.34), (0.70, 0.18), (1.0, 0.08)]
    g_rev = clamp((frame - 45) / 140.0)
    draw_graph_panel(
        draw,
        (1140, 180, 700, 480),
        "FIG. 3 · PORE THROAT AERATION & SUCTION (1/6 g)",
        "Pore Throat Diameter (um)",
        "Air Porosity (%) / Suction",
        [(0.0, "5"), (0.25, "30"), (0.45, "60"), (0.75, "100"), (1.0, "150")],
        [(0.0, "0%"), (0.35, "25%"), (0.70, "50%"), (1.0, "75%")],
        [
            (air_curve, ACCENT_COLOR, "Air-Filled Porosity (>25-30%)", 3.2),
            (suction_curve, DARK_COLOR, "Matric Suction (-kPa)", 2.8),
        ],
        g_rev,
        fonts,
        highlight_band=(0.25, 0.45, "OPTIMAL: 30-60 um"),
    )

    if 75 <= frame < 185:
        p = clamp((frame - 75) / 20.0)
        draw_leader_label(draw, (-1.7, 0.0, 0.45), (-70, -145), "RAW REGOLITH (<12% AIR)", "WATERLOGGED HYPOXIA", cam_x, cam_y, p, f_lbl, f_sub, align_right=True)
        draw_leader_label(draw, (1.2, 0.0, 1.55), (100, -120), "SINTERED CERAMIC", "AERATED 30-60 um PORES", cam_x, cam_y, p, f_lbl, f_sub, align_right=False)
    if 240 <= frame < 365:
        p = clamp((frame - 240) / 20.0)
        draw_leader_label(draw, (kx + 1.8, ky, 2.30), (-110, -110), "LUNAR 0.165 g RISE", "6x EXPANSION (NS-29 Lc=4.2-5.2mm)", cam_x, cam_y, p, f_lbl, f_sub, align_right=True)
    if 445 <= frame:
        p = clamp((frame - 445) / 20.0)
        draw_leader_label(draw, (px0, py0, 0.55), (-95, -145), "PWM MANIFOLD (PSI-187)", "PASSIVE CAPILLARY AERATION", cam_x, cam_y, p, f_lbl, f_sub, align_right=True)

    sub = "01 / PORE-SCALE CUTAWAY & FIG. 3" if frame < 195 else ("02 / GRAVITY SCALING (1g -> 0.38g -> 0.165g)" if frame < 375 else "03 / PWM PASSIVE CAPILLARY FLUIDICS")
    draw_hud(draw, "EPISODE 2 · VADOSE PHYSICS & GRAVITY SCALING", sub, frame, 540, fonts)
    return img.resize((1920, 1080), Image.Resampling.LANCZOS)


# ===========================================================================
# EPISODE 3 (v2): Habitat Scaling Clusters + Live Fig. 4 ESM Graph (20s = 600f)
# ===========================================================================
def render_ep3(frame: int, fonts: Tuple, esm_rows: List[dict]) -> Image.Image:
    _, _, f_lbl, f_sub = fonts
    img = Image.new("RGB", (W, H), BG_COLOR)
    draw = ImageDraw.Draw(img)

    c1 = (zone_cam(0.0, 0.0)[0] + 240, zone_cam(0.0, 0.0)[1])
    c2 = (zone_cam(7.5, -2.5)[0] + 240, zone_cam(7.5, -2.5)[1])
    if frame < 260:
        cam_x, cam_y = c1
    elif frame < 305:
        u = ease_in_out_cubic((frame - 260) / 45.0)
        cam_x = c1[0] + (c2[0] - c1[0]) * u
        cam_y = c1[1] + (c2[1] - c1[1]) * u
    else:
        cam_x, cam_y = c2

    objs: List[IsoDrawable] = []

    # --- SCENE 1: Power & Hardware Scaling (Fission Kilopower vs Solar + RFC) ---
    # Left: 40 kWe Kilopower Reactor (cylinder core + vertical radiator fins)
    objs.append(IsoCylinder(-1.6, 0.2, -0.20, 0.85, 0.85, 0.20, "dark", segments=10, start_frame=0, layer=0))
    objs.append(IsoCylinder(-1.6, 0.2, 0.0, 0.36, 0.30, 1.35, "accent", segments=10, start_frame=9, layer=2))
    objs.append(IsoBox(-2.45, 0.12, 0.95, 1.70, 0.16, 0.55, "light", start_frame=15, layer=2))
    # Right: Solar PV + RFC Battery Arrays (tall recurring mass)
    objs.append(IsoBox(0.6, -0.5, -0.20, 1.8, 1.6, 0.20, "dark", start_frame=6, layer=0))
    objs.append(IsoBox(0.8, -0.3, 0.0, 1.4, 0.55, 0.65, "mid", start_frame=18, layer=2))
    objs.append(IsoBox(0.7, 0.45, 0.0, 1.6, 0.45, 0.12, "dark", start_frame=21, layer=2))

    # --- SCENE 2: Crew Scaling Habitat Clusters (3 / 6 / 12 Crew Linked Domes) ---
    hx, hy = 7.5, -2.5
    s2 = 275
    # 3-Crew (1 dome) -> 15.4 mo
    objs.append(IsoCylinder(hx - 2.3, hy + 0.5, 0.0, 0.68, 0.68, 0.25, "dark", segments=10, start_frame=s2, layer=1))
    objs.append(IsoDome(hx - 2.3, hy + 0.5, 0.25, 0.68, 0.45, "light", rings=2, segments=10, start_frame=s2 + 3, layer=2))
    # 6-Crew (2 linked domes) -> 9.4 mo
    for di, dy in enumerate([-0.5, 0.6]):
        objs.append(IsoCylinder(hx - 0.3, hy + dy, 0.0, 0.65, 0.65, 0.25, "dark", segments=10, start_frame=s2 + 9 + di * 3, layer=1))
        objs.append(IsoDome(hx - 0.3, hy + dy, 0.25, 0.65, 0.45, "mid", rings=2, segments=10, start_frame=s2 + 12 + di * 3, layer=2))
    # 12-Crew (4 linked domes with accent hub) -> 6.5 mo
    for ci, (dx, dy) in enumerate([(1.5, -0.6), (2.6, -0.6), (1.5, 0.5), (2.6, 0.5)]):
        objs.append(IsoCylinder(hx + dx, hy + dy, 0.0, 0.55, 0.55, 0.28, "dark", segments=10, start_frame=s2 + 18 + ci * 3, layer=1))
        objs.append(IsoDome(hx + dx, hy + dy, 0.28, 0.55, 0.40, "accent", rings=2, segments=10, start_frame=s2 + 21 + ci * 3, layer=2))

    objs.sort(key=lambda o: o.sort_key())
    for o in objs:
        o.draw(draw, frame, cam_x, cam_y)

    # Live Fig. 4 Cumulative ESM Crossover Graph driven directly by analysis/output/esm_4arch_comparison.csv
    max_esm = 12500.0
    raw_pts = [(r["month"] / 60.0, r["raw_esm"] / max_esm) for r in esm_rows]
    hydro_pts = [(r["month"] / 60.0, r["hydro_esm"] / max_esm) for r in esm_rows]
    hybrid_pts = [(r["month"] / 60.0, r["hybrid_esm"] / max_esm) for r in esm_rows]
    sin_pts = [(r["month"] / 60.0, r["sintered_esm"] / max_esm) for r in esm_rows]

    g_rev = clamp((frame - 35) / 240.0)
    draw_graph_panel(
        draw,
        (1110, 175, 740, 500),
        "FIG. 4 · 4-ARCHITECTURE ESM TRAJECTORY (6 CREW, NUCLEAR)",
        "Mission Duration (Months)",
        "Cumulative ESM (kg)",
        [(0.0, "0"), (9.4 / 60.0, "9.4"), (20.5 / 60.0, "20.5"), (0.6, "36"), (1.0, "60 mo")],
        [(0.0, "0"), (3848 / max_esm, "3.8t"), (5665 / max_esm, "5.7t"), (11910 / max_esm, "11.9t")],
        [
            (raw_pts, DARK_COLOR, "Raw Regolith (11,910 kg)", 2.8),
            (hydro_pts, MID_COLOR, "Hydroponics (5,665 kg)", 2.6),
            (hybrid_pts, INK_COLOR, "Hybrid (4,625 kg)", 2.4),
            (sin_pts, ACCENT_COLOR, "Sintered ISRU (3,848 kg)", 3.5),
        ],
        g_rev,
        fonts,
        highlight_band=(20.5 / 60.0, 1.0, "SINTERED OPTIMAL >20.5 MO (8,062 kg SAVED vs RAW)"),
    )

    if 55 <= frame < 265:
        p = clamp((frame - 55) / 20.0)
        draw_leader_label(draw, (-1.6, 0.2, 1.35), (-70, -140), "FISSION POWER (Cp=54)", "BREAKEVEN: 9.4 MO", cam_x, cam_y, p, f_lbl, f_sub, align_right=True)
        draw_leader_label(draw, (1.5, 0.0, 0.65), (90, -100), "SOLAR PV+RFC (Cp=237)", "14-DAY NIGHT: 18-22 MO", cam_x, cam_y, p, f_lbl, f_sub, align_right=False)
    if 325 <= frame:
        p = clamp((frame - 325) / 20.0)
        draw_leader_label(draw, (hx - 2.3, hy + 0.5, 0.70), (-85, -165), "3 CREW (15.4 MO)", "1 HABITAT MODULE", cam_x, cam_y, p, f_lbl, f_sub, align_right=True)
        draw_leader_label(draw, (hx + 2.0, hy, 0.68), (-30, -210), "12 CREW (6.5 MO)", "ECONOMIES OF SCALE · 4 MODULES", cam_x, cam_y, p, f_lbl, f_sub, align_right=True)

    sub = "01 / POWER SCALING & FIG. 4 ESM CROSSOVER" if frame < 275 else "02 / CREW HABITAT SCALING (3 / 6 / 12 CREW)"
    draw_hud(draw, "EPISODE 3 · ESM MODEL & HABITAT SCALING FACTORS", sub, frame, 600, fonts)
    return img.resize((1920, 1080), Image.Resampling.LANCZOS)


# ===========================================================================
# EPISODE 4 (v2): Multitrophic Bays + Recovery Metrics Panel (18s = 540f)
# ===========================================================================
def render_ep4(frame: int, fonts: Tuple) -> Image.Image:
    _, _, f_lbl, f_sub = fonts
    img = Image.new("RGB", (W, H), BG_COLOR)
    draw = ImageDraw.Draw(img)

    c1 = (zone_cam(0.0, 0.0)[0] + 240, zone_cam(0.0, 0.0)[1])
    c2 = (zone_cam(7.0, -2.5)[0] + 240, zone_cam(7.0, -2.5)[1])
    c3 = (zone_cam(14.0, -5.0)[0] + 240, zone_cam(14.0, -5.0)[1])
    if frame < 180:
        cam_x, cam_y = c1
    elif frame < 215:
        u = ease_in_out_cubic((frame - 180) / 35.0)
        cam_x = c1[0] + (c2[0] - c1[0]) * u
        cam_y = c1[1] + (c2[1] - c1[1]) * u
    elif frame < 360:
        cam_x, cam_y = c2
    elif frame < 395:
        u = ease_in_out_cubic((frame - 360) / 35.0)
        cam_x = c2[0] + (c3[0] - c2[0]) * u
        cam_y = c2[1] + (c3[1] - c2[1]) * u
    else:
        cam_x, cam_y = c3

    objs: List[IsoDrawable] = []

    # --- BAY A: 500 C Cylindrical Pyrolytic Furnace ---
    objs.append(IsoCylinder(0.0, 0.0, -0.20, 1.45, 1.45, 0.20, "dark", segments=12, start_frame=0, layer=0))
    objs.append(IsoCylinder(0.0, 0.0, 0.0, 0.95, 0.95, 0.72, "accent", segments=12, start_frame=9, layer=2))
    objs.append(IsoBox(-0.45, -0.45, 0.72, 0.90, 0.90, 0.25, "light", start_frame=15, layer=3))
    lift1 = -105.0 * SS * ease_in_out_cubic(clamp((frame - 50) / 30.0)) if frame >= 50 else 0.0
    objs.append(IsoDome(0.0, 0.0, 1.15, 1.15, 0.65, "dark", rings=2, segments=12, start_frame=21, dz_px_extra=lift1, layer=6))

    # --- BAY B: Mycoponics Bay (Ceramic trays + Pleurotus mushroom clusters) ---
    bx0, by0 = 7.0, -2.5
    s2 = 200
    objs.append(IsoBox(bx0 - 1.2, by0 - 1.2, -0.20, 2.4, 2.4, 0.20, "dark", start_frame=s2, layer=0))
    objs.append(IsoBox(bx0 - 1.1, by0 - 1.1, 0.0, 0.20, 2.2, 1.30, "mid", start_frame=s2 + 3, layer=2))
    objs.append(IsoBox(bx0 - 0.9, by0 - 1.1, 0.0, 2.0, 0.20, 1.30, "mid", start_frame=s2 + 6, layer=2))
    for ti in range(3):
        tz = 0.10 + ti * 0.40
        objs.append(IsoBox(bx0 - 0.7, by0 - 0.7, tz, 1.4, 1.4, 0.14, "light", start_frame=s2 + 12 + ti * 3, layer=3))
        # Stylized mushroom stems + caps
        for mx, my in [(-0.25, -0.2), (0.25, 0.2)]:
            objs.append(IsoCylinder(bx0 + mx, by0 + my, tz + 0.14, 0.08, 0.06, 0.12, "light", segments=8, start_frame=s2 + 15 + ti * 3, layer=3))
            objs.append(IsoCylinder(bx0 + mx, by0 + my, tz + 0.26, 0.22, 0.10, 0.08, "accent", segments=8, start_frame=s2 + 18 + ti * 3, layer=3))
    lift2 = -105.0 * SS * ease_in_out_cubic(clamp((frame - 250) / 30.0)) if frame >= 250 else 0.0
    objs.append(IsoBox(bx0 - 1.2, by0 - 1.2, 1.30, 2.4, 2.4, 0.20, "mid", start_frame=s2 + 24, dz_px_extra=lift2, layer=6))

    # --- BAY C: BioRock Chemostat & LECA Tailings Yard ---
    cx0, cy0 = 14.0, -5.0
    s3 = 375
    objs.append(IsoCylinder(cx0 - 0.3, cy0 - 0.2, -0.20, 1.45, 1.45, 0.20, "dark", segments=12, start_frame=s3, layer=0))
    objs.append(IsoCylinder(cx0 - 0.4, cy0 - 0.3, 0.0, 0.65, 0.65, 1.25, "glass", segments=12, start_frame=s3 + 9, layer=2))
    objs.append(IsoCylinder(cx0 - 0.4, cy0 - 0.3, 0.15, 0.52, 0.52, 0.65, "bio", segments=12, start_frame=s3 + 12, layer=2))
    objs.append(IsoCylinder(cx0 - 0.4, cy0 - 0.3, 1.25, 0.35, 0.35, 0.25, "accent", segments=10, start_frame=s3 + 15, layer=3))
    for ti in range(3):
        objs.append(IsoCylinder(cx0 + 0.65, cy0 - 0.8 + ti * 0.65, 0.0, 0.26, 0.24, 0.24, "light", segments=6, start_frame=s3 + 18 + ti * 3, layer=2))

    objs.sort(key=lambda o: o.sort_key())
    for o in objs:
        o.draw(draw, frame, cam_x, cam_y)

    # Live Recovery & Closure Curves
    h2o_sin = [(0.0, 0.985), (0.33, 0.986), (0.66, 0.987), (1.0, 0.988)]
    h2o_raw = [(0.0, 0.82), (0.33, 0.80), (0.66, 0.79), (1.0, 0.78)]
    g_rev = clamp((frame - 35) / 180.0)
    draw_graph_panel(
        draw,
        (1140, 185, 700, 460),
        "CLOSED-LOOP RECOVERY & BIOMASS CLOSURE",
        "Cultivation Cycles (500°C Pyrolytic Reset)",
        "Water Recovery Efficiency (%)",
        [(0.0, "Cycle 1"), (0.33, "Cycle 5"), (0.66, "Cycle 10"), (1.0, "Cycle 20")],
        [(0.70, "70%"), (0.80, "80%"), (0.90, "90%"), (1.0, "100%")],
        [
            (h2o_sin, ACCENT_COLOR, "Sintered Ceramic (>98.5%)", 3.4),
            (h2o_raw, DARK_COLOR, "Raw Regolith (78-82%)", 2.8),
        ],
        g_rev,
        fonts,
        highlight_band=(0.0, 1.0, None),
    )

    if 75 <= frame < 185:
        p = clamp((frame - 75) / 20.0)
        draw_leader_label(draw, (0.0, 0.0, 0.85), (-85, -145), "500 °C PYROLYTIC FURNACE", "CO2 + H2O + ASH RECOVERY", cam_x, cam_y, p, f_lbl, f_sub, align_right=True)
    if 270 <= frame < 365:
        p = clamp((frame - 270) / 20.0)
        draw_leader_label(draw, (bx0, by0, 0.95), (-85, -145), "MYCOPONICS (PLEUROTUS)", "UPCYCLES 40-60% STRAW + POLYOLS", cam_x, cam_y, p, f_lbl, f_sub, align_right=True)
    if 415 <= frame:
        p = clamp((frame - 415) / 20.0)
        draw_leader_label(draw, (cx0 - 0.4, cy0 - 0.3, 1.25), (-85, -145), "BIOROCK CHEMOSTAT & LECA", "MINERAL EXTRACTION + PAVERS", cam_x, cam_y, p, f_lbl, f_sub, align_right=True)

    sub = "01 / PYROLYTIC REGENERATION" if frame < 195 else ("02 / MYCOPONIC BIOMASS UPCYCLING" if frame < 375 else "03 / BIO-ISRU & TAILINGS VALORIZATION")
    draw_hud(draw, "EPISODE 4 · CLOSED-LOOP MULTITROPHIC SCALING", sub, frame, 540, fonts)
    return img.resize((1920, 1080), Image.Resampling.LANCZOS)


def main():
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    docs_assets = os.path.join(repo_root, "docs", "assets")
    inter_assets = os.path.join(repo_root, "interactive", "assets")
    os.makedirs(docs_assets, exist_ok=True)
    os.makedirs(inter_assets, exist_ok=True)
    fonts = load_fonts()
    esm_rows = load_esm_csv(repo_root)

    specs = [
        ("Ep2-v2", 540, 120, lambda f, fn: render_ep2(f, fn), "ep2_vadose_capillary_physics.mp4", "ep2_poster.png"),
        ("Ep3-v2", 600, 150, lambda f, fn: render_ep3(f, fn, esm_rows), "ep3_esm_habitat_scaling.mp4", "ep3_poster.png"),
        ("Ep4-v2", 540, 120, lambda f, fn: render_ep4(f, fn), "ep4_closed_loop_scaling.mp4", "ep4_poster.png"),
    ]
    for label, total_f, p_frame, fn, mp4_name, p_name in specs:
        mp4_out = os.path.join(docs_assets, mp4_name)
        p_out = os.path.join(docs_assets, p_name)
        encode_episode(mp4_out, p_out, total_f, p_frame, fn, fonts, label)
        shutil.copy2(mp4_out, os.path.join(inter_assets, mp4_name))
        shutil.copy2(p_out, os.path.join(inter_assets, p_name))

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
    print(f"[OK] Full 4-episode v2 reel -> {full_mp4}")


if __name__ == "__main__":
    main()
