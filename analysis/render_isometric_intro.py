#!/usr/bin/env python3
"""
Render an orthographic isometric miniature introductory video for lunar-regolith-blss-review.

Strict visual & motion specification:
- Orthographic camera at true 30-degree isometric angles; slides smoothly, never rotates into perspective.
- Palette:
    Background : #eef2f3
    Ink        : #2d3142
    Accent     : #ef8354
    Shades     : #4f5d75, #bfc0c0
- Every block has three flat tones: light top, mid left, dark right, with crisp #2d3142 outlines.
- Pieces drop in from 40px above (at 1080p output scale) with a small damped bounce, staggered by 3 frames.
- Roofs lift straight upward (+Z) off buildings to reveal internal processes.
- Labels use thin #2d3142 leader lines with anchor dots.
"""

import math
import os
import subprocess
import sys
from typing import Dict, List, Optional, Tuple

import numpy as np
from PIL import Image, ImageDraw, ImageFont

# ---------------------------------------------------------------------------
# Output & Supersampling Configuration
# ---------------------------------------------------------------------------
OUT_W, OUT_H = 1920, 1080
SS = 2  # 2x supersampling -> 3840x2160 internal canvas, LANCZOS downsampled
W, H = OUT_W * SS, OUT_H * SS
FPS = 30
TOTAL_FRAMES = 540  # 18.0 seconds

COS30 = math.cos(math.radians(30.0))  # 0.8660254
SIN30 = 0.5
SCALE = 56.0 * SS  # World unit -> supersampled pixels

# ---------------------------------------------------------------------------
# Strict Color Palette
# ---------------------------------------------------------------------------
BG_HEX = "#eef2f3"
INK_HEX = "#2d3142"
ACCENT_HEX = "#ef8354"
SHADE_DARK_HEX = "#4f5d75"
SHADE_MID_HEX = "#bfc0c0"


def hex_rgb(h: str) -> Tuple[int, int, int]:
    h = h.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


BG_COLOR = hex_rgb(BG_HEX)
INK_COLOR = hex_rgb(INK_HEX)

# Every block uses 3 flat tones: (light_top, mid_left, dark_right)
PALETTES: Dict[str, Tuple[Tuple[int, int, int], Tuple[int, int, int], Tuple[int, int, int]]] = {
    # Regolith / Ceramic light blocks (#eef2f3 / #bfc0c0 / #8f96a0)
    "light": ((238, 242, 243), (191, 192, 192), (138, 146, 158)),
    # Mid structural / Sintered blocks (#d6dbde / #9aa3b0 / #4f5d75)
    "mid": ((214, 219, 222), (146, 156, 170), (79, 93, 117)),
    # Slate / Heavy hull / Base (#bfc0c0 / #4f5d75 / #2d3142)
    "dark": ((191, 192, 192), (79, 93, 117), (45, 49, 66)),
    # Accent blocks (#f6aa86 / #ef8354 / #c45c32)
    "accent": ((246, 170, 134), (239, 131, 84), (196, 92, 50)),
    # Glass / Solar / Skylight tint (bright #eef2f3 top, #bfc0c0 mid, #4f5d75 dark)
    "glass": ((247, 250, 251), (191, 192, 192), (79, 93, 117)),
}


# ---------------------------------------------------------------------------
# Easing & Motion Helpers
# ---------------------------------------------------------------------------
def clamp(v: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, v))


def ease_in_out_cubic(t: float) -> float:
    t = clamp(t)
    if t < 0.5:
        return 4.0 * t * t * t
    return 1.0 - pow(-2.0 * t + 2.0, 3) / 2.0


def ease_out_cubic(t: float) -> float:
    t = clamp(t)
    return 1.0 - pow(1.0 - t, 3)


def drop_bounce_offset_px(frame: int, start_frame: int, duration: int = 14) -> Optional[float]:
    """
    Returns vertical screen-space offset in supersampled pixels.
    Piece starts 40px (at 1080p = 40 * SS internal px) above target,
    drops down, and performs a small damped bounce before settling at 0.
    Returns None before start_frame so the piece is hidden until its stagger turn.
    """
    if frame < start_frame:
        return None
    dt = frame - start_frame
    if dt >= duration:
        return 0.0
    t = dt / float(duration)
    drop_dist = 40.0 * SS
    # Main fall (0 -> 0.62), small bounce up (0.62 -> 0.84), settle (0.84 -> 1.0)
    if t < 0.62:
        u = t / 0.62
        # Accelerate like gravity
        return -drop_dist * (1.0 - u * u)
    elif t < 0.86:
        u = (t - 0.62) / 0.24
        # Small bounce peak ~ 6px (at 1080p)
        return -(6.0 * SS) * math.sin(u * math.pi)
    else:
        u = (t - 0.86) / 0.14
        return -(1.8 * SS) * math.sin(u * math.pi)


# ---------------------------------------------------------------------------
# Orthographic Isometric Projection & Primitives
# ---------------------------------------------------------------------------
def project(x: float, y: float, z: float, cam_x: float, cam_y: float, dz_px: float = 0.0) -> Tuple[float, float]:
    """True orthographic isometric projection (30 deg). Camera only slides in (cam_x, cam_y)."""
    sx = W * 0.5 + ((x - y) * COS30) * SCALE - cam_x * SS
    sy = H * 0.54 + ((x + y) * SIN30 - z) * SCALE - cam_y * SS + dz_px
    return (sx, sy)


class IsoBox:
    def __init__(
        self,
        x: float,
        y: float,
        z: float,
        dx: float,
        dy: float,
        dz: float,
        palette: str = "mid",
        start_frame: int = 0,
        dz_px_extra: float = 0.0,
        layer: int = 0,
        stroke_w: float = 1.6,
        alpha_outline: bool = True,
    ):
        self.x = x
        self.y = y
        self.z = z
        self.dx = dx
        self.dy = dy
        self.dz = dz
        self.palette = palette
        self.start_frame = start_frame
        self.dz_px_extra = dz_px_extra
        self.layer = layer
        self.stroke_w = stroke_w * SS
        self.alpha_outline = alpha_outline

    def sort_key(self) -> Tuple[int, float, float]:
        # Painter's sort: layer first, then back-to-front in isometric (x+y), then z
        cx = self.x + self.dx * 0.5
        cy = self.y + self.dy * 0.5
        cz = self.z + self.dz * 0.5
        return (self.layer, cx + cy + cz * 0.01, cz)

    def draw(self, draw: ImageDraw.ImageDraw, frame: int, cam_x: float, cam_y: float):
        drop_px = drop_bounce_offset_px(frame, self.start_frame)
        if drop_px is None:
            return
        total_dz_px = drop_px + self.dz_px_extra
        top_col, left_col, right_col = PALETTES[self.palette]

        x0, x1 = self.x, self.x + self.dx
        y0, y1 = self.y, self.y + self.dy
        z0, z1 = self.z, self.z + self.dz

        def p(vx: float, vy: float, vz: float) -> Tuple[float, float]:
            return project(vx, vy, vz, cam_x, cam_y, total_dz_px)

        # 7 visible vertices of an isometric box viewed from (+x, +y, +z)
        p_top = [p(x0, y0, z1), p(x1, y0, z1), p(x1, y1, z1), p(x0, y1, z1)]
        # Left visible face (x0..x1 at y = y1, facing +y -> viewer's left-down)
        p_left = [p(x0, y1, z1), p(x1, y1, z1), p(x1, y1, z0), p(x0, y1, z0)]
        # Right visible face (y0..y1 at x = x1, facing +x -> viewer's right-down)
        p_right = [p(x1, y0, z1), p(x1, y1, z1), p(x1, y1, z0), p(x1, y0, z0)]

        outline = INK_COLOR if self.alpha_outline else None
        sw = int(round(self.stroke_w))

        draw.polygon(p_left, fill=left_col, outline=outline, width=sw)
        draw.polygon(p_right, fill=right_col, outline=outline, width=sw)
        draw.polygon(p_top, fill=top_col, outline=outline, width=sw)


def draw_leader_label(
    draw: ImageDraw.ImageDraw,
    anchor_world: Tuple[float, float, float],
    elbow_offset_px: Tuple[float, float],
    label_text: str,
    sub_text: str,
    cam_x: float,
    cam_y: float,
    progress: float,
    font_title: ImageFont.FreeTypeFont,
    font_sub: ImageFont.FreeTypeFont,
    align_right: bool = False,
):
    """Draws a thin #2d3142 elbow leader line with anchor dot and crisp typography."""
    if progress <= 0.02:
        return
    p = ease_out_cubic(progress)
    ax, ay = project(anchor_world[0], anchor_world[1], anchor_world[2], cam_x, cam_y)
    ex = ax + elbow_offset_px[0] * SS
    ey = ay + elbow_offset_px[1] * SS
    hx = ex + (-130 * SS if align_right else 130 * SS)
    hy = ey

    # Animate line length smoothly
    if p < 0.5:
        u = p / 0.5
        cx = ax + (ex - ax) * u
        cy = ay + (ey - ay) * u
        draw.line([(ax, ay), (cx, cy)], fill=INK_COLOR, width=int(1.6 * SS))
    else:
        u = (p - 0.5) / 0.5
        cx = ex + (hx - ex) * u
        draw.line([(ax, ay), (ex, ey), (cx, hy)], fill=INK_COLOR, width=int(1.6 * SS))

    # Anchor dot
    r = 4.0 * SS
    draw.ellipse([ax - r, ay - r, ax + r, ay + r], fill=hex_rgb(ACCENT_HEX), outline=INK_COLOR, width=int(1.5 * SS))

    if p > 0.55:
        tx = hx + (-8 * SS if align_right else 10 * SS)
        anchor = "rm" if align_right else "lm"
        draw.text((tx, hy - 10 * SS), label_text, fill=INK_COLOR, font=font_title, anchor=anchor)
        if sub_text:
            draw.text((tx, hy + 13 * SS), sub_text, fill=hex_rgb(SHADE_DARK_HEX), font=font_sub, anchor=anchor)


# ---------------------------------------------------------------------------
# Font Loader
# ---------------------------------------------------------------------------
def load_fonts() -> Tuple[ImageFont.FreeTypeFont, ImageFont.FreeTypeFont, ImageFont.FreeTypeFont, ImageFont.FreeTypeFont]:
    font_path = "/System/Library/Fonts/HelveticaNeue.ttc"
    if not os.path.exists(font_path):
        font_path = "/System/Library/Fonts/Helvetica.ttc"
    f_hdr = ImageFont.truetype(font_path, int(15 * SS), index=1 if "HelveticaNeue" in font_path else 0)
    f_step = ImageFont.truetype(font_path, int(12 * SS), index=0)
    f_lbl = ImageFont.truetype(font_path, int(13 * SS), index=1 if "HelveticaNeue" in font_path else 0)
    f_sub = ImageFont.truetype(font_path, int(11 * SS), index=0)
    return f_hdr, f_step, f_lbl, f_sub


# ---------------------------------------------------------------------------
# Scene Builders
# ---------------------------------------------------------------------------
def build_static_world_boxes(frame: int) -> List[IsoBox]:
    boxes: List[IsoBox] = []

    # --- ZONE 1: LUNAR LANDING PAD (centered at x=0, y=0) ---
    # 5x5 regolith base tiles dropping in staggered by 3 frames from frame 0
    idx = 0
    for gx in range(-2, 3):
        for gy in range(-2, 3):
            dist = abs(gx) + abs(gy)
            pal = "mid" if (gx + gy) % 2 == 0 else "light"
            boxes.append(IsoBox(gx * 1.15 - 0.55, gy * 1.15 - 0.55, -0.35, 1.12, 1.12, 0.35, pal, start_frame=idx * 2, layer=0))
            idx += 1

    # Sintered Landing Pad (3x3 raised central slab, staggered by 3 frames starting frame 48)
    pad_idx = 0
    for px in range(-1, 2):
        for py in range(-1, 2):
            pal = "accent" if (px == 0 and py == 0) else "dark"
            boxes.append(IsoBox(px * 0.95 - 0.45, py * 0.95 - 0.45, 0.0, 0.92, 0.92, 0.18, pal, start_frame=48 + pad_idx * 3, layer=1))
            pad_idx += 1

    # Blast Berm Blocks around perimeter (staggered by 3 frames starting frame 76)
    berm_coords = [
        (-2.6, -2.5), (-1.4, -2.5), (0.0, -2.5), (1.3, -2.5),
        (-2.6, 1.8), (-1.4, 1.8), (0.0, 1.8), (1.3, 1.8),
        (-2.6, -1.2), (-2.6, 0.3),
    ]
    for bi, (bx, by) in enumerate(berm_coords):
        boxes.append(IsoBox(bx, by, 0.0, 0.85, 0.55, 0.45, "mid", start_frame=76 + bi * 3, layer=2))

    # Corner Landing Beacons (#ef8354 accent posts)
    for ci, (cx, cy) in enumerate([(-1.55, -1.55), (1.40, -1.55), (-1.55, 1.40), (1.40, 1.40)]):
        boxes.append(IsoBox(cx, cy, 0.18, 0.22, 0.22, 0.42, "accent", start_frame=105 + ci * 3, layer=2))

    # --- ZONE 2: MICROWAVE SINTERING KILN (centered at x=6.8, y=-2.6) ---
    kx, ky = 6.8, -2.6
    k_start = 240
    # Base platform tiles
    ki = 0
    for dx in range(-2, 3):
        for dy in range(-2, 3):
            boxes.append(IsoBox(kx + dx * 1.1 - 0.55, ky + dy * 1.1 - 0.55, -0.35, 1.08, 1.08, 0.35, "light" if (dx + dy) % 2 else "mid", start_frame=k_start + ki * 2, layer=0))
            ki += 1

    # Kiln foundation & side walls (cutaway front-facing walls lower so interior is visible when roof lifts)
    boxes.append(IsoBox(kx - 1.3, ky - 1.3, 0.0, 2.6, 2.6, 0.22, "dark", start_frame=k_start + 15, layer=1))
    # Back-left wall (x0) and back-right wall (y0) full height
    boxes.append(IsoBox(kx - 1.3, ky - 1.3, 0.22, 0.25, 2.6, 1.45, "mid", start_frame=k_start + 18, layer=2))
    boxes.append(IsoBox(kx - 1.05, ky - 1.3, 0.22, 2.35, 0.25, 1.45, "mid", start_frame=k_start + 21, layer=2))

    # Interior machinery (visible once roof lifts!)
    # Regolith feed hopper
    boxes.append(IsoBox(kx - 0.9, ky - 0.85, 0.22, 0.75, 0.75, 1.05, "light", start_frame=k_start + 24, layer=3))
    # 2.45 GHz Microwave heating cavity (#ef8354 accent core)
    boxes.append(IsoBox(kx - 0.1, ky - 0.75, 0.22, 0.95, 0.95, 0.85, "accent", start_frame=k_start + 27, layer=3))
    # Waveguide top collar
    boxes.append(IsoBox(kx + 0.15, ky - 0.5, 1.07, 0.45, 0.45, 0.35, "dark", start_frame=k_start + 30, layer=3))
    # Sintered ceramic output trays exiting on conveyor
    for ti in range(3):
        boxes.append(IsoBox(kx + 0.35 + ti * 0.55, ky + 0.55, 0.22, 0.42, 0.55, 0.25, "light", start_frame=k_start + 33 + ti * 3, layer=3))

    # Kiln Roof (lifts vertically at frame 305 -> 335)
    roof_lift_k = 0.0
    if frame >= 305:
        u = clamp((frame - 305) / 30.0)
        roof_lift_k = -115.0 * SS * ease_in_out_cubic(u)
    boxes.append(IsoBox(kx - 1.4, ky - 1.4, 1.67, 2.8, 2.8, 0.24, "dark", start_frame=k_start + 42, dz_px_extra=roof_lift_k, layer=6))
    boxes.append(IsoBox(kx - 0.85, ky - 0.85, 1.91, 1.7, 1.7, 0.22, "accent", start_frame=k_start + 45, dz_px_extra=roof_lift_k, layer=6))

    # --- ZONE 3: BLSS GREENHOUSE MODULE (centered at x=13.6, y=-5.2) ---
    gx0, gy0 = 13.6, -5.2
    g_start = 375
    gi = 0
    for dx in range(-2, 3):
        for dy in range(-2, 3):
            boxes.append(IsoBox(gx0 + dx * 1.1 - 0.55, gy0 + dy * 1.1 - 0.55, -0.35, 1.08, 1.08, 0.35, "light" if (dx + dy) % 2 else "mid", start_frame=g_start + gi * 2, layer=0))
            gi += 1

    # Greenhouse base slab & back frame walls
    boxes.append(IsoBox(gx0 - 1.4, gy0 - 1.4, 0.0, 2.8, 2.8, 0.22, "dark", start_frame=g_start + 15, layer=1))
    boxes.append(IsoBox(gx0 - 1.4, gy0 - 1.4, 0.22, 0.22, 2.8, 1.55, "mid", start_frame=g_start + 18, layer=2))
    boxes.append(IsoBox(gx0 - 1.18, gy0 - 1.4, 0.22, 2.58, 0.22, 1.55, "mid", start_frame=g_start + 21, layer=2))

    # Interior 3-tier vertical hydroponic ceramic racks + #ef8354 PAR LED bars + PWM manifold
    for tier in range(3):
        tz = 0.26 + tier * 0.44
        # Ceramic porous tray
        boxes.append(IsoBox(gx0 - 0.9, gy0 - 0.85, tz, 1.7, 0.65, 0.14, "light", start_frame=g_start + 24 + tier * 3, layer=3))
        # PAR LED / PWM capillary bar
        boxes.append(IsoBox(gx0 - 0.85, gy0 - 0.78, tz + 0.14, 1.6, 0.5, 0.08, "accent", start_frame=g_start + 27 + tier * 3, layer=3))
    # Front-right PWM capillary reservoir tank
    boxes.append(IsoBox(gx0 - 0.85, gy0 + 0.3, 0.22, 0.75, 0.75, 1.1, "mid", start_frame=g_start + 36, layer=3))
    boxes.append(IsoBox(gx0 + 0.1, gy0 + 0.4, 0.22, 0.85, 0.55, 0.55, "accent", start_frame=g_start + 39, layer=3))

    # Greenhouse Roof Cap (lifts vertically at frame 435 -> 465)
    roof_lift_g = 0.0
    if frame >= 435:
        u = clamp((frame - 435) / 30.0)
        roof_lift_g = -125.0 * SS * ease_in_out_cubic(u)
    boxes.append(IsoBox(gx0 - 1.5, gy0 - 1.5, 1.77, 3.0, 3.0, 0.22, "glass", start_frame=g_start + 45, dz_px_extra=roof_lift_g, layer=6))
    boxes.append(IsoBox(gx0 - 1.0, gy0 - 1.0, 1.99, 2.0, 2.0, 0.22, "light", start_frame=g_start + 48, dz_px_extra=roof_lift_g, layer=6))

    return boxes


def build_lander_boxes(frame: int) -> List[IsoBox]:
    """
    Model Cargo Ship (CLPS-style lander) descending onto the pad at (0, 0) during frames 135..205,
    with a landing strut compression bounce at frame 205..220.
    """
    if frame < 130:
        return []

    # Descent altitude in world Z
    if frame < 205:
        u = clamp((frame - 130) / 75.0)
        # Smooth deceleration as it approaches pad (z_base = 0.18)
        z_base = 0.18 + 6.2 * (1.0 - ease_out_cubic(u))
        strut_bounce = 0.0
    elif frame < 220:
        u = (frame - 205) / 15.0
        z_base = 0.18
        strut_bounce = -0.10 * math.sin(u * math.pi)  # subtle compression bounce
    else:
        z_base = 0.18
        strut_bounce = 0.0

    zb = z_base + strut_bounce
    boxes: List[IsoBox] = []

    # 4 Landing Struts / Footpads
    for sx, sy in [(-0.75, -0.75), (0.55, -0.75), (-0.75, 0.55), (0.55, 0.55)]:
        boxes.append(IsoBox(sx, sy, zb, 0.22, 0.22, 0.42, "dark", start_frame=130, layer=4))

    # Main Descent Bus
    boxes.append(IsoBox(-0.55, -0.55, zb + 0.35, 1.1, 1.1, 0.65, "mid", start_frame=130, layer=4))
    # Payload Fairing (ISRU Sintering Module)
    boxes.append(IsoBox(-0.42, -0.42, zb + 1.00, 0.84, 0.84, 0.58, "light", start_frame=130, layer=4))
    # Top Antenna / Beacon
    boxes.append(IsoBox(-0.15, -0.15, zb + 1.58, 0.30, 0.30, 0.25, "accent", start_frame=130, layer=4))
    # Twin Solar Wings
    boxes.append(IsoBox(-1.35, -0.25, zb + 0.72, 0.78, 0.50, 0.08, "dark", start_frame=130, layer=4))
    boxes.append(IsoBox(0.57, -0.25, zb + 0.72, 0.78, 0.50, 0.08, "dark", start_frame=130, layer=4))

    # Active #ef8354 Thruster Plume while descending (frames 130..204)
    if 130 <= frame < 205:
        flicker = 0.15 * math.sin(frame * 1.3)
        plume_h = 0.55 + flicker
        boxes.append(IsoBox(-0.22, -0.22, zb - plume_h + 0.25, 0.44, 0.44, plume_h, "accent", start_frame=130, layer=4))

    return boxes


# ---------------------------------------------------------------------------
# Camera Slide Schedule (Pure 2D Orthographic Pan, Never Rotates)
# ---------------------------------------------------------------------------
def get_camera(frame: int) -> Tuple[float, float]:
    # Zone 1 center: (0, 0) -> (0, 0)
    # Zone 2 center: (6.8, -2.6) -> screen x offset = (6.8 - (-2.6)) * COS30 * 56 = ~455px
    # Zone 3 center: (13.6, -5.2) -> screen x offset = (13.6 - (-5.2)) * COS30 * 56 = ~911px
    def zone_cam(wx: float, wy: float) -> Tuple[float, float]:
        # Output-pixel space offset (multiplied by SS inside project())
        return (((wx - wy) * COS30) * 56.0, ((wx + wy) * SIN30) * 56.0)

    c1 = zone_cam(0.0, 0.0)
    c2 = zone_cam(6.8, -2.6)
    c3 = zone_cam(13.6, -5.2)

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
    else:
        return c3


# ---------------------------------------------------------------------------
# Frame Renderer & FFmpeg Pipeline
# ---------------------------------------------------------------------------
def render_frame(frame: int, fonts: Tuple) -> Image.Image:
    f_hdr, f_step, f_lbl, f_sub = fonts
    img = Image.new("RGB", (W, H), BG_COLOR)
    draw = ImageDraw.Draw(img)
    cam_x, cam_y = get_camera(frame)

    # Combine & depth-sort all isometric blocks
    boxes = build_static_world_boxes(frame) + build_lander_boxes(frame)
    boxes.sort(key=lambda b: b.sort_key())
    for b in boxes:
        b.draw(draw, frame, cam_x, cam_y)

    # Leader-line annotations per scene
    if 75 <= frame < 190:
        p1 = clamp((frame - 75) / 20.0)
        draw_leader_label(
            draw, (0.0, 0.0, 0.18), (-90, -140),
            "SINTERED REGOLITH LANDING PAD", "3-TONE ISRU CERAMIC SURFACE",
            cam_x, cam_y, p1, f_lbl, f_sub, align_right=True
        )
    if 100 <= frame < 190:
        p2 = clamp((frame - 100) / 20.0)
        draw_leader_label(
            draw, (1.5, -2.3, 0.45), (105, -110),
            "DUST-SHIELD BLAST BERM", "STAGGERED MODULAR BLOCKS",
            cam_x, cam_y, p2, f_lbl, f_sub, align_right=False
        )
    if 195 <= frame < 260:
        p3 = clamp((frame - 195) / 18.0)
        draw_leader_label(
            draw, (0.0, 0.0, 1.55), (120, -155),
            "CLPS CARGO LANDER", "1850 kg ISRU PLANT PAYLOAD",
            cam_x, cam_y, p3, f_lbl, f_sub, align_right=False
        )

    if 315 <= frame < 395:
        p4 = clamp((frame - 315) / 20.0)
        draw_leader_label(
            draw, (6.8, -2.1, 0.85), (150, -185),
            "2.45 GHz MICROWAVE KILN", "ROOF CUTAWAY · VOLUMETRIC SINTERING",
            cam_x, cam_y, p4, f_lbl, f_sub, align_right=False
        )
        p5 = clamp((frame - 328) / 20.0)
        draw_leader_label(
            draw, (8.3, -2.0, 0.47), (140, 25),
            "PASSIVATED CERAMIC TRAYS", "30-60 um PORE THROATS",
            cam_x, cam_y, p5, f_lbl, f_sub, align_right=False
        )

    if 445 <= frame:
        p6 = clamp((frame - 445) / 20.0)
        draw_leader_label(
            draw, (13.6, -5.2, 1.15), (150, -195),
            "PWM CAPILLARY HYDROPONICS", "MULTI-TIER CERAMIC RACKS (PSI-187)",
            cam_x, cam_y, p6, f_lbl, f_sub, align_right=False
        )
        p7 = clamp((frame - 462) / 20.0)
        draw_leader_label(
            draw, (14.1, -4.6, 0.77), (140, 25),
            ">98.5% WATER RECOVERY", "ESM BREAKEVEN: 18.5 MONTHS",
            cam_x, cam_y, p7, f_lbl, f_sub, align_right=False
        )

    # Minimal HUD header & progress bar
    draw.text((64 * SS, 46 * SS), "LUNAR BLSS · ISRU BIO-INFRASTRUCTURE", fill=INK_COLOR, font=f_hdr)
    if frame < 135:
        step_txt = "01 / LANDING PAD & BLAST BERM ASSEMBLY"
    elif frame < 255:
        step_txt = "02 / CLPS CARGO LANDER TOUCHDOWN"
    elif frame < 390:
        step_txt = "03 / 2.45 GHz MICROWAVE SINTERING CUTAWAY"
    else:
        step_txt = "04 / BLSS GREENHOUSE & PWM CAPILLARY CUTAWAY"
    draw.text((64 * SS, 70 * SS), step_txt, fill=hex_rgb(SHADE_DARK_HEX), font=f_step)

    # Bottom progress bar
    prog = (frame + 1) / float(TOTAL_FRAMES)
    bar_y = H - 6 * SS
    draw.rectangle([0, bar_y, W, H], fill=hex_rgb(SHADE_MID_HEX))
    draw.rectangle([0, bar_y, int(W * prog), H], fill=hex_rgb(ACCENT_HEX))

    return img.resize((OUT_W, OUT_H), Image.Resampling.LANCZOS)


def main():
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    docs_assets = os.path.join(repo_root, "docs", "assets")
    inter_assets = os.path.join(repo_root, "interactive", "assets")
    os.makedirs(docs_assets, exist_ok=True)
    os.makedirs(inter_assets, exist_ok=True)

    mp4_path = os.path.join(docs_assets, "lunar_blss_intro.mp4")
    poster_path = os.path.join(docs_assets, "lunar_blss_intro_poster.png")

    fonts = load_fonts()

    cmd = [
        "/opt/homebrew/bin/ffmpeg",
        "-y",
        "-f", "rawvideo",
        "-vcodec", "rawvideo",
        "-s", f"{OUT_W}x{OUT_H}",
        "-pix_fmt", "rgb24",
        "-r", str(FPS),
        "-i", "-",
        "-an",
        "-vcodec", "libx264",
        "-pix_fmt", "yuv420p",
        "-crf", "18",
        "-movflags", "+faststart",
        mp4_path,
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    for f in range(TOTAL_FRAMES):
        im = render_frame(f, fonts)
        if f == 205:
            im.save(poster_path)
        proc.stdin.write(im.tobytes())
        if (f + 1) % 90 == 0:
            print(f"Rendered {f + 1}/{TOTAL_FRAMES} frames...")

    proc.stdin.close()
    stderr_out = proc.stderr.read().decode("utf-8", errors="ignore")
    ret = proc.wait()
    if ret != 0:
        print("FFmpeg failed:", stderr_out, file=sys.stderr)
        sys.exit(ret)

    # Sync assets to interactive/assets
    import shutil
    shutil.copy2(mp4_path, os.path.join(inter_assets, "lunar_blss_intro.mp4"))
    shutil.copy2(poster_path, os.path.join(inter_assets, "lunar_blss_intro_poster.png"))
    print(f"[OK] Video rendered to {mp4_path}")
    print(f"[OK] Poster saved to {poster_path}")


if __name__ == "__main__":
    main()
