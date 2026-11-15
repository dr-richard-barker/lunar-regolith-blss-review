#!/usr/bin/env python3
"""
v2 Remake of Episode 1: Recognizable Isometric Miniature Objects
- Cratered lunar terrain + octagonal sintered landing pad + blast berms
- CLPS cargo lander with splayed landing struts, footpads, tanks, parabolic dish, solar wings, conical thruster plume
- Microwave sintering kiln with conical regolith hopper, cylindrical 2.45 GHz cavity, roller conveyor
- Geodesic BLSS greenhouse dome (lifts vertically) revealing botanical crop canopies & PWM manifolds
"""

import math
import os
import shutil
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
    SS,
    W,
    clamp,
    draw_hud,
    draw_leader_label,
    ease_in_out_cubic,
    ease_out_cubic,
    encode_episode,
    load_fonts,
    zone_cam,
)

TOTAL_FRAMES = 540


def build_ep1_world(frame: int) -> List[IsoDrawable]:
    objs: List[IsoDrawable] = []

    # --- ZONE 1: CRATERED TERRAIN & OCTAGONAL LANDING PAD (0, 0) ---
    idx = 0
    for gx in range(-2, 3):
        for gy in range(-2, 3):
            pal = "mid" if (gx + gy) % 2 == 0 else "light"
            objs.append(IsoBox(gx * 1.15 - 0.55, gy * 1.15 - 0.55, -0.35, 1.12, 1.12, 0.35, pal, start_frame=idx * 2, layer=0))
            idx += 1

    # Miniature stepped lunar craters on terrain corners
    for ci, (cx, cy, cr) in enumerate([(-2.3, 1.9, 0.45), (2.1, -2.0, 0.52), (2.2, 2.0, 0.38)]):
        objs.append(IsoCylinder(cx, cy, 0.0, cr, cr * 0.72, 0.16, "light", segments=10, start_frame=44 + ci * 3, layer=1))

    # Octagonal Sintered Landing Pad (layered octagonal disks)
    objs.append(IsoCylinder(0.0, 0.0, 0.0, 1.65, 1.55, 0.14, "dark", segments=8, start_frame=52, layer=1))
    objs.append(IsoCylinder(0.0, 0.0, 0.14, 1.25, 1.25, 0.06, "mid", segments=8, start_frame=55, layer=1))
    objs.append(IsoCylinder(0.0, 0.0, 0.20, 0.55, 0.55, 0.03, "accent", segments=8, start_frame=58, layer=1))

    # Sloped Dust-Shield Blast Berm walls around perimeter
    berms = [(-2.4, -2.2), (-1.2, -2.4), (0.1, -2.4), (1.3, -2.2), (-2.4, -0.9), (-2.4, 0.4), (-1.2, 2.0), (0.2, 2.0)]
    for bi, (bx, by) in enumerate(berms):
        objs.append(IsoCylinder(bx, by, 0.0, 0.48, 0.30, 0.38, "mid", segments=6, start_frame=64 + bi * 3, layer=2))

    # Corner Beacons
    for ci, (bx, by) in enumerate([(-1.45, -1.45), (1.45, -1.45), (-1.45, 1.45), (1.45, 1.45)]):
        objs.append(IsoCylinder(bx, by, 0.0, 0.10, 0.08, 0.42, "accent", segments=8, start_frame=92 + ci * 3, layer=2))

    # --- ZONE 2: MICROWAVE SINTERING KILN (x=7.2, y=-2.8) ---
    kx, ky = 7.2, -2.8
    ks = 240
    for dx in range(-2, 3):
        for dy in range(-2, 3):
            objs.append(IsoBox(kx + dx * 1.1 - 0.55, ky + dy * 1.1 - 0.55, -0.35, 1.08, 1.08, 0.35, "light" if (dx + dy) % 2 else "mid", start_frame=ks + (dx + 2) * 3, layer=0))

    # Kiln base & cutaway housing walls
    objs.append(IsoBox(kx - 1.35, ky - 1.35, 0.0, 2.7, 2.7, 0.20, "dark", start_frame=ks + 12, layer=1))
    objs.append(IsoBox(kx - 1.35, ky - 1.35, 0.20, 0.22, 2.7, 1.45, "mid", start_frame=ks + 15, layer=2))
    objs.append(IsoBox(kx - 1.13, ky - 1.35, 0.20, 2.48, 0.22, 1.45, "mid", start_frame=ks + 18, layer=2))

    # Conical Regolith Feed Hopper + Cylindrical 2.45 GHz Microwave Cavity
    objs.append(IsoCylinder(kx - 0.55, ky - 0.55, 0.20, 0.22, 0.58, 0.95, "light", segments=10, start_frame=ks + 21, layer=3))
    objs.append(IsoCylinder(kx + 0.30, ky - 0.35, 0.20, 0.58, 0.58, 0.85, "accent", segments=12, start_frame=ks + 24, layer=3))
    objs.append(IsoCylinder(kx + 0.30, ky - 0.35, 1.05, 0.24, 0.24, 0.32, "dark", segments=10, start_frame=ks + 27, layer=3))

    # Roller conveyor + exiting sintered ceramic trays
    objs.append(IsoBox(kx + 0.2, ky + 0.45, 0.20, 1.85, 0.65, 0.14, "dark", start_frame=ks + 30, layer=3))
    for ti in range(3):
        objs.append(IsoBox(kx + 0.35 + ti * 0.52, ky + 0.52, 0.34, 0.38, 0.48, 0.18, "light", start_frame=ks + 33 + ti * 3, layer=3))

    # Kiln Roof lifts vertically at frame 305..335
    lift_k = -115.0 * SS * ease_in_out_cubic(clamp((frame - 305) / 30.0)) if frame >= 305 else 0.0
    objs.append(IsoBox(kx - 1.45, ky - 1.45, 1.65, 2.9, 2.9, 0.22, "dark", start_frame=ks + 42, dz_px_extra=lift_k, layer=6))
    objs.append(IsoCylinder(kx, ky, 1.87, 0.95, 0.65, 0.25, "accent", segments=8, start_frame=ks + 45, dz_px_extra=lift_k, layer=6))

    # --- ZONE 3: GEODESIC BLSS GREENHOUSE (x=14.4, y=-5.6) ---
    gx0, gy0 = 14.4, -5.6
    gs = 375
    for dx in range(-2, 3):
        for dy in range(-2, 3):
            objs.append(IsoBox(gx0 + dx * 1.1 - 0.55, gy0 + dy * 1.1 - 0.55, -0.35, 1.08, 1.08, 0.35, "light" if (dx + dy) % 2 else "mid", start_frame=gs + (dx + 2) * 3, layer=0))

    # Cylindrical foundation ring + cutaway back walls
    objs.append(IsoCylinder(gx0, gy0, 0.0, 1.55, 1.55, 0.22, "dark", segments=12, start_frame=gs + 12, layer=1))
    objs.append(IsoBox(gx0 - 1.25, gy0 - 1.25, 0.22, 0.20, 2.3, 1.30, "mid", start_frame=gs + 15, layer=2))
    objs.append(IsoBox(gx0 - 1.05, gy0 - 1.25, 0.22, 2.1, 0.20, 1.30, "mid", start_frame=gs + 18, layer=2))

    # 3-Tier Vertical Ceramic Racks + Botanical Canopies (bio) + PAR LED Strips (accent)
    for tier in range(3):
        tz = 0.26 + tier * 0.40
        objs.append(IsoBox(gx0 - 0.85, gy0 - 0.75, tz, 1.5, 0.55, 0.10, "light", start_frame=gs + 21 + tier * 3, layer=3))
        # Botanical leafy crop clusters
        for ci in range(3):
            objs.append(IsoCylinder(gx0 - 0.55 + ci * 0.45, gy0 - 0.48, tz + 0.10, 0.18, 0.14, 0.18, "bio", segments=8, start_frame=gs + 24 + tier * 3, layer=3))
        # PAR LED grow bar
        objs.append(IsoBox(gx0 - 0.80, gy0 - 0.65, tz + 0.30, 1.4, 0.14, 0.05, "accent", start_frame=gs + 27 + tier * 3, layer=3))

    # PWM Cylindrical Nutrient Reservoir + Capillary Feed Manifold
    objs.append(IsoCylinder(gx0 - 0.55, gy0 + 0.48, 0.22, 0.34, 0.34, 0.95, "mid", segments=10, start_frame=gs + 36, layer=3))
    objs.append(IsoBox(gx0 - 0.10, gy0 + 0.35, 0.22, 0.85, 0.38, 0.32, "accent", start_frame=gs + 39, layer=3))

    # Faceted Geodesic Greenhouse Dome lifts straight up at frame 435..465
    lift_g = -125.0 * SS * ease_in_out_cubic(clamp((frame - 435) / 30.0)) if frame >= 435 else 0.0
    objs.append(IsoDome(gx0, gy0, 1.52, 1.55, 1.05, "glass", rings=3, segments=12, start_frame=gs + 45, dz_px_extra=lift_g, layer=6))

    return objs


def build_ep1_lander(frame: int) -> List[IsoDrawable]:
    """Detailed CLPS Cargo Lander: octagonal bus, 4 splayed legs + footpads, tanks, dish, solar wings, conical plume."""
    if frame < 130:
        return []

    if frame < 205:
        u = clamp((frame - 130) / 75.0)
        zb = 0.22 + 6.2 * (1.0 - ease_out_cubic(u))
    elif frame < 220:
        u = (frame - 205) / 15.0
        zb = 0.22 - 0.09 * math.sin(u * math.pi)
    else:
        zb = 0.22

    objs: List[IsoDrawable] = []

    # 4 Splayed Landing Struts + Circular Footpads
    for sx, sy in [(-1.0, -1.0), (1.0, -1.0), (-1.0, 1.0), (1.0, 1.0)]:
        fx, fy = sx * 0.95, sy * 0.95
        hx, hy = sx * 0.52, sy * 0.52
        objs.append(IsoCylinder(fx, fy, zb, 0.18, 0.15, 0.08, "dark", segments=8, start_frame=130, layer=4))
        objs.append(IsoStrut((fx, fy, zb + 0.06), (hx, hy, zb + 0.62), width=3.5, color=DARK_COLOR, start_frame=130, layer=4))

    # Conical Thruster Plume while descending
    if 130 <= frame < 205:
        flicker = 0.16 * math.sin(frame * 1.4)
        ph = 0.72 + flicker
        objs.append(IsoCylinder(0.0, 0.0, zb + 0.42 - ph, 0.34, 0.12, ph, "accent", segments=10, start_frame=130, layer=4, draw_top=False))

    # Main Engine Bell + Octagonal Descent Bus
    objs.append(IsoCylinder(0.0, 0.0, zb + 0.32, 0.22, 0.12, 0.22, "dark", segments=10, start_frame=130, layer=4))
    objs.append(IsoCylinder(0.0, 0.0, zb + 0.52, 0.68, 0.68, 0.58, "mid", segments=8, start_frame=130, layer=4))

    # 2 Visible Spherical/Cylindrical Propellant Tanks on flanks
    objs.append(IsoCylinder(-0.56, 0.18, zb + 0.60, 0.20, 0.20, 0.42, "accent", segments=10, start_frame=130, layer=4))
    objs.append(IsoCylinder(0.18, -0.56, zb + 0.60, 0.20, 0.20, 0.42, "accent", segments=10, start_frame=130, layer=4))

    # Upper ISRU Payload Cylinder + Parabolic Comms Dish + Twin Solar Wings
    objs.append(IsoCylinder(0.0, 0.0, zb + 1.10, 0.48, 0.44, 0.55, "light", segments=8, start_frame=130, layer=4))
    objs.append(IsoCylinder(0.22, 0.22, zb + 1.65, 0.06, 0.28, 0.18, "accent", segments=10, start_frame=130, layer=4))
    objs.append(IsoStrut((0.22, 0.22, zb + 1.75), (0.22, 0.22, zb + 1.98), width=2.5, color=INK_COLOR, start_frame=130, layer=4))

    # Solar array wings
    objs.append(IsoBox(-1.65, -0.25, zb + 0.85, 0.92, 0.50, 0.06, "dark", start_frame=130, layer=4))
    objs.append(IsoBox(0.73, -0.25, zb + 0.85, 0.92, 0.50, 0.06, "dark", start_frame=130, layer=4))

    return objs


def get_camera(frame: int) -> Tuple[float, float]:
    c1 = zone_cam(0.0, 0.0)
    c2 = zone_cam(7.2, -2.8)
    c3 = zone_cam(14.4, -5.6)
    if frame < 235:
        return c1
    elif frame < 275:
        u = ease_in_out_cubic((frame - 235) / 40.0)
        return (c1[0] + (c2[0] - c1[0]) * u, c1[1] + (c2[1] - c1[1]) * u)
    elif frame < 370:
        return c2
    elif frame < 410:
        u = ease_in_out_cubic((frame - 370) / 40.0)
        return (c2[0] + (c3[0] - c2[0]) * u, c2[1] + (c3[1] - c2[1]) * u)
    return c3


def render_frame(frame: int, fonts: Tuple) -> Image.Image:
    _, _, f_lbl, f_sub = fonts
    img = Image.new("RGB", (W, H), BG_COLOR)
    draw = ImageDraw.Draw(img)
    cam_x, cam_y = get_camera(frame)

    objs = build_ep1_world(frame) + build_ep1_lander(frame)
    objs.sort(key=lambda o: o.sort_key())
    for o in objs:
        o.draw(draw, frame, cam_x, cam_y)

    if 75 <= frame < 190:
        p = clamp((frame - 75) / 20.0)
        draw_leader_label(draw, (0.0, 0.0, 0.22), (-95, -145), "OCTAGONAL SINTERED PAD", "ISRU CERAMIC SURFACE", cam_x, cam_y, p, f_lbl, f_sub, align_right=True)
        draw_leader_label(draw, (1.3, -2.2, 0.38), (110, -110), "SLOPED BLAST BERMS", "REGOLITH EJECTA SHIELDING", cam_x, cam_y, p, f_lbl, f_sub, align_right=False)
    if 195 <= frame < 260:
        p = clamp((frame - 195) / 18.0)
        draw_leader_label(draw, (0.0, 0.0, 1.65), (125, -155), "CLPS CARGO LANDER", "1850 kg ISRU PLANT + SOLAR WINGS", cam_x, cam_y, p, f_lbl, f_sub, align_right=False)
    if 315 <= frame < 395:
        p = clamp((frame - 315) / 20.0)
        draw_leader_label(draw, (7.5, -3.1, 1.05), (150, -185), "2.45 GHz MICROWAVE KILN", "CONICAL HOPPER + DIELECTRIC CAVITY", cam_x, cam_y, p, f_lbl, f_sub, align_right=False)
        draw_leader_label(draw, (8.6, -2.1, 0.45), (140, 25), "ROLLER CONVEYOR TRAYS", "30-60 um PASSIVATED CERAMICS", cam_x, cam_y, p, f_lbl, f_sub, align_right=False)
    if 445 <= frame:
        p = clamp((frame - 445) / 20.0)
        draw_leader_label(draw, (14.4, -5.6, 1.15), (150, -195), "GEODESIC BLSS GREENHOUSE", "MULTI-TIER BOTANICAL CANOPIES + PWM", cam_x, cam_y, p, f_lbl, f_sub, align_right=False)
        draw_leader_label(draw, (14.7, -5.1, 0.45), (195, 25), ">98.5% WATER RECOVERY", "ESM BREAKEVEN: 9.4-18.5 MO", cam_x, cam_y, p, f_lbl, f_sub, align_right=False)

    step_txt = (
        "01 / CRATERED TERRAIN & OCTAGONAL PAD" if frame < 135
        else "02 / CLPS CARGO LANDER TOUCHDOWN" if frame < 255
        else "03 / MICROWAVE KILN & CONVEYOR CUTAWAY" if frame < 390
        else "04 / GEODESIC BLSS GREENHOUSE CUTAWAY"
    )
    draw_hud(draw, "EPISODE 1 · LUNAR BLSS ISRU BIO-INFRASTRUCTURE", step_txt, frame, TOTAL_FRAMES, fonts)
    return img.resize((1920, 1080), Image.Resampling.LANCZOS)


def main():
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    docs_assets = os.path.join(repo_root, "docs", "assets")
    inter_assets = os.path.join(repo_root, "interactive", "assets")
    os.makedirs(docs_assets, exist_ok=True)
    os.makedirs(inter_assets, exist_ok=True)
    mp4_path = os.path.join(docs_assets, "lunar_blss_intro.mp4")
    poster_path = os.path.join(docs_assets, "lunar_blss_intro_poster.png")
    encode_episode(mp4_path, poster_path, TOTAL_FRAMES, 205, render_frame, load_fonts(), "Ep1-v2")
    shutil.copy2(mp4_path, os.path.join(inter_assets, "lunar_blss_intro.mp4"))
    shutil.copy2(poster_path, os.path.join(inter_assets, "lunar_blss_intro_poster.png"))


if __name__ == "__main__":
    main()
