#!/usr/bin/env python3
"""
Shared orthographic 30-degree isometric miniature rendering engine (v2).

Includes:
- IsoBox, IsoCylinder, IsoCone, IsoDome, IsoStrut, IsoLine3D
- Vector DataGraphPanel for live animated research curves
- Palette: bg #eef2f3, ink #2d3142, accent #ef8354, shades #4f5d75 & #bfc0c0
- Directional 3-tone flat shading + crisp #2d3142 outlines
- 40px drop-in bounce staggered by 3 frames
- Pure 2D orthographic camera slide (never rotates into perspective)
"""

import math
import os
import subprocess
import sys
from typing import Callable, Dict, List, Optional, Tuple

from PIL import Image, ImageDraw, ImageFont

OUT_W, OUT_H = 1920, 1080
SS = 2
W, H = OUT_W * SS, OUT_H * SS
FPS = 30

COS30 = math.cos(math.radians(30.0))
SIN30 = 0.5
SCALE = 56.0 * SS

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
ACCENT_COLOR = hex_rgb(ACCENT_HEX)
DARK_COLOR = hex_rgb(SHADE_DARK_HEX)
MID_COLOR = hex_rgb(SHADE_MID_HEX)

# Every material palette has (light_top, mid_left, dark_right)
PALETTES: Dict[str, Tuple[Tuple[int, int, int], Tuple[int, int, int], Tuple[int, int, int]]] = {
    "light": ((238, 242, 243), (191, 192, 192), (138, 146, 158)),
    "mid": ((214, 219, 222), (146, 156, 170), (79, 93, 117)),
    "dark": ((191, 192, 192), (79, 93, 117), (45, 49, 66)),
    "accent": ((246, 170, 134), (239, 131, 84), (196, 92, 50)),
    "glass": ((247, 250, 251), (206, 214, 220), (146, 156, 170)),
    # Botanical / biological muted slate-sage keeping strict harmony with #4f5d75 & #eef2f3
    "bio": ((196, 212, 204), (122, 148, 138), (79, 93, 117)),
}


def lerp_rgb(c1: Tuple[int, int, int], c2: Tuple[int, int, int], t: float) -> Tuple[int, int, int]:
    t = max(0.0, min(1.0, t))
    return (
        int(round(c1[0] + (c2[0] - c1[0]) * t)),
        int(round(c1[1] + (c2[1] - c1[1]) * t)),
        int(round(c1[2] + (c2[2] - c1[2]) * t)),
    )


def shade_for_normal(palette: str, nx: float, ny: float, nz: float) -> Tuple[int, int, int]:
    """Maps a face normal onto the 3 flat tones (light top, mid left, dark right)."""
    top_col, left_col, right_col = PALETTES[palette]
    if nz > 0.65:
        return top_col
    # In isometric view from (+1, +1, +1), +y faces viewer-left, +x faces viewer-right
    if ny >= nx:
        return left_col
    return right_col


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
    if frame < start_frame:
        return None
    dt = frame - start_frame
    if dt >= duration:
        return 0.0
    t = dt / float(duration)
    drop_dist = 40.0 * SS
    if t < 0.62:
        u = t / 0.62
        return -drop_dist * (1.0 - u * u)
    elif t < 0.86:
        u = (t - 0.62) / 0.24
        return -(6.0 * SS) * math.sin(u * math.pi)
    else:
        u = (t - 0.86) / 0.14
        return -(1.8 * SS) * math.sin(u * math.pi)


def project(x: float, y: float, z: float, cam_x: float, cam_y: float, dz_px: float = 0.0) -> Tuple[float, float]:
    sx = W * 0.5 + ((x - y) * COS30) * SCALE - cam_x * SS
    sy = H * 0.54 + ((x + y) * SIN30 - z) * SCALE - cam_y * SS + dz_px
    return (sx, sy)


def zone_cam(wx: float, wy: float) -> Tuple[float, float]:
    return (((wx - wy) * COS30) * 56.0, ((wx + wy) * SIN30) * 56.0)


class IsoDrawable:
    def sort_key(self) -> Tuple[int, float, float]:
        return (0, 0.0, 0.0)

    def draw(self, draw: ImageDraw.ImageDraw, frame: int, cam_x: float, cam_y: float):
        pass


class IsoBox(IsoDrawable):
    def __init__(
        self,
        x: float, y: float, z: float,
        dx: float, dy: float, dz: float,
        palette: str = "mid",
        start_frame: int = 0,
        dz_px_extra: float = 0.0,
        layer: int = 0,
        stroke_w: float = 1.6,
    ):
        self.x, self.y, self.z = x, y, z
        self.dx, self.dy, self.dz = dx, dy, dz
        self.palette = palette
        self.start_frame = start_frame
        self.dz_px_extra = dz_px_extra
        self.layer = layer
        self.stroke_w = stroke_w * SS

    def sort_key(self) -> Tuple[int, float, float]:
        return (self.layer, (self.x + self.dx * 0.5) + (self.y + self.dy * 0.5) + (self.z + self.dz * 0.5) * 0.01, self.z + self.dz * 0.5)

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

        sw = int(round(self.stroke_w))
        draw.polygon([p(x0, y1, z1), p(x1, y1, z1), p(x1, y1, z0), p(x0, y1, z0)], fill=left_col, outline=INK_COLOR, width=sw)
        draw.polygon([p(x1, y0, z1), p(x1, y1, z1), p(x1, y1, z0), p(x1, y0, z0)], fill=right_col, outline=INK_COLOR, width=sw)
        draw.polygon([p(x0, y0, z1), p(x1, y0, z1), p(x1, y1, z1), p(x0, y1, z1)], fill=top_col, outline=INK_COLOR, width=sw)


class IsoCylinder(IsoDrawable):
    """Faceted isometric cylinder or frustum/cone (when r_top != r_bot)."""
    def __init__(
        self,
        cx: float, cy: float, z0: float,
        r_bot: float, r_top: float, h: float,
        palette: str = "mid",
        segments: int = 12,
        start_frame: int = 0,
        dz_px_extra: float = 0.0,
        layer: int = 0,
        stroke_w: float = 1.5,
        draw_top: bool = True,
    ):
        self.cx, self.cy, self.z0 = cx, cy, z0
        self.r_bot, self.r_top, self.h = r_bot, r_top, h
        self.palette = palette
        self.segments = segments
        self.start_frame = start_frame
        self.dz_px_extra = dz_px_extra
        self.layer = layer
        self.stroke_w = stroke_w * SS
        self.draw_top = draw_top

    def sort_key(self) -> Tuple[int, float, float]:
        return (self.layer, self.cx + self.cy + (self.z0 + self.h * 0.5) * 0.01, self.z0 + self.h * 0.5)

    def draw(self, draw: ImageDraw.ImageDraw, frame: int, cam_x: float, cam_y: float):
        drop_px = drop_bounce_offset_px(frame, self.start_frame)
        if drop_px is None:
            return
        total_dz_px = drop_px + self.dz_px_extra
        z1 = self.z0 + self.h
        sw = int(round(self.stroke_w))

        def p(vx: float, vy: float, vz: float) -> Tuple[float, float]:
            return project(vx, vy, vz, cam_x, cam_y, total_dz_px)

        # Build side quads and sort back-to-front by (nx + ny)
        quads = []
        top_pts = []
        for i in range(self.segments):
            a0 = (2.0 * math.pi * i) / self.segments
            a1 = (2.0 * math.pi * (i + 1)) / self.segments
            am = 0.5 * (a0 + a1)
            nx, ny = math.cos(am), math.sin(am)
            # Only draw front-facing quads (visible from +x, +y)
            if nx + ny > -0.15:
                b0 = p(self.cx + self.r_bot * math.cos(a0), self.cy + self.r_bot * math.sin(a0), self.z0)
                b1 = p(self.cx + self.r_bot * math.cos(a1), self.cy + self.r_bot * math.sin(a1), self.z0)
                t1 = p(self.cx + self.r_top * math.cos(a1), self.cy + self.r_top * math.sin(a1), z1)
                t0 = p(self.cx + self.r_top * math.cos(a0), self.cy + self.r_top * math.sin(a0), z1)
                col = shade_for_normal(self.palette, nx, ny, 0.0)
                quads.append((nx + ny, [t0, t1, b1, b0], col))
            if self.r_top > 0.01:
                top_pts.append(p(self.cx + self.r_top * math.cos(a0), self.cy + self.r_top * math.sin(a0), z1))

        quads.sort(key=lambda q: q[0])
        for _, pts, col in quads:
            draw.polygon(pts, fill=col, outline=INK_COLOR, width=sw)

        if self.draw_top and self.r_top > 0.01 and len(top_pts) >= 3:
            top_col = PALETTES[self.palette][0]
            draw.polygon(top_pts, fill=top_col, outline=INK_COLOR, width=sw)


class IsoDome(IsoDrawable):
    """Faceted geodesic isometric dome cap for the BLSS Greenhouse."""
    def __init__(
        self,
        cx: float, cy: float, z0: float,
        r: float, h: float,
        palette: str = "glass",
        rings: int = 3,
        segments: int = 12,
        start_frame: int = 0,
        dz_px_extra: float = 0.0,
        layer: int = 6,
        stroke_w: float = 1.4,
    ):
        self.cx, self.cy, self.z0 = cx, cy, z0
        self.r, self.h = r, h
        self.palette = palette
        self.rings = rings
        self.segments = segments
        self.start_frame = start_frame
        self.dz_px_extra = dz_px_extra
        self.layer = layer
        self.stroke_w = stroke_w * SS

    def sort_key(self) -> Tuple[int, float, float]:
        return (self.layer, self.cx + self.cy + (self.z0 + self.h * 0.5) * 0.01, self.z0 + self.h)

    def draw(self, draw: ImageDraw.ImageDraw, frame: int, cam_x: float, cam_y: float):
        drop_px = drop_bounce_offset_px(frame, self.start_frame)
        if drop_px is None:
            return
        total_dz_px = drop_px + self.dz_px_extra
        sw = int(round(self.stroke_w))

        def p(vx: float, vy: float, vz: float) -> Tuple[float, float]:
            return project(vx, vy, vz, cam_x, cam_y, total_dz_px)

        facets = []
        for ri in range(self.rings):
            phi0 = (math.pi * 0.5) * (ri / float(self.rings))
            phi1 = (math.pi * 0.5) * ((ri + 1) / float(self.rings))
            r0 = self.r * math.cos(phi0)
            r1 = self.r * math.cos(phi1)
            z0 = self.z0 + self.h * math.sin(phi0)
            z1 = self.z0 + self.h * math.sin(phi1)
            for si in range(self.segments):
                a0 = (2.0 * math.pi * si) / self.segments
                a1 = (2.0 * math.pi * (si + 1)) / self.segments
                am = 0.5 * (a0 + a1)
                pm = 0.5 * (phi0 + phi1)
                nx = math.cos(pm) * math.cos(am)
                ny = math.cos(pm) * math.sin(am)
                nz = math.sin(pm)
                if nx + ny + nz > -0.1:
                    pts = [
                        p(self.cx + r0 * math.cos(a0), self.cy + r0 * math.sin(a0), z0),
                        p(self.cx + r0 * math.cos(a1), self.cy + r0 * math.sin(a1), z0),
                    ]
                    if r1 > 0.01:
                        pts.append(p(self.cx + r1 * math.cos(a1), self.cy + r1 * math.sin(a1), z1))
                        pts.append(p(self.cx + r1 * math.cos(a0), self.cy + r1 * math.sin(a0), z1))
                    else:
                        pts.append(p(self.cx, self.cy, z1))
                    col = shade_for_normal(self.palette, nx, ny, nz)
                    facets.append((nx + ny + nz * 0.5, pts, col))

        facets.sort(key=lambda f: f[0])
        for _, pts, col in facets:
            draw.polygon(pts, fill=col, outline=INK_COLOR, width=sw)


class IsoStrut(IsoDrawable):
    """3D line/strut in isometric space (e.g., splayed lander legs, antenna masts)."""
    def __init__(
        self,
        p0: Tuple[float, float, float],
        p1: Tuple[float, float, float],
        width: float = 4.0,
        color: Tuple[int, int, int] = DARK_COLOR,
        start_frame: int = 0,
        dz_px_extra: float = 0.0,
        layer: int = 4,
    ):
        self.p0, self.p1 = p0, p1
        self.width = width * SS
        self.color = color
        self.start_frame = start_frame
        self.dz_px_extra = dz_px_extra
        self.layer = layer

    def sort_key(self) -> Tuple[int, float, float]:
        mx = 0.5 * (self.p0[0] + self.p1[0])
        my = 0.5 * (self.p0[1] + self.p1[1])
        mz = 0.5 * (self.p0[2] + self.p1[2])
        return (self.layer, mx + my + mz * 0.01, mz)

    def draw(self, draw: ImageDraw.ImageDraw, frame: int, cam_x: float, cam_y: float):
        drop_px = drop_bounce_offset_px(frame, self.start_frame)
        if drop_px is None:
            return
        tot = drop_px + self.dz_px_extra
        s0 = project(self.p0[0], self.p0[1], self.p0[2], cam_x, cam_y, tot)
        s1 = project(self.p1[0], self.p1[1], self.p1[2], cam_x, cam_y, tot)
        draw.line([s0, s1], fill=INK_COLOR, width=int(self.width + 2.5 * SS))
        draw.line([s0, s1], fill=self.color, width=int(self.width))


# ---------------------------------------------------------------------------
# Vector Data Graph Panel (Synchronized Research Plots)
# ---------------------------------------------------------------------------
def draw_graph_panel(
    draw: ImageDraw.ImageDraw,
    box_px: Tuple[int, int, int, int],  # (x, y, w, h) at 1080p coordinates
    title: str,
    x_label: str,
    y_label: str,
    x_ticks: List[Tuple[float, str]],   # (norm_0_1, label)
    y_ticks: List[Tuple[float, str]],   # (norm_0_1, label)
    series: List[Tuple[List[Tuple[float, float]], Tuple[int, int, int], str, float]],  # (pts_norm, color, label, width_1080p)
    reveal_t: float,                    # 0..1 animation progress
    fonts: Tuple,
    highlight_band: Optional[Tuple[float, float, str]] = None,  # (x0_norm, x1_norm, band_label)
):
    """Draws a crisp publication-style research graph in the exact #eef2f3 / #2d3142 / #ef8354 palette."""
    if reveal_t <= 0.02:
        return
    _, f_step, f_lbl, f_sub = fonts
    px, py, pw, ph = [v * SS for v in box_px]

    # Card container
    draw.rectangle([px, py, px + pw, py + ph], fill=(247, 249, 250), outline=INK_COLOR, width=int(1.8 * SS))
    # Title bar
    draw.rectangle([px, py, px + pw, py + 38 * SS], fill=INK_COLOR)
    draw.text((px + 14 * SS, py + 19 * SS), title, fill=BG_COLOR, font=f_lbl, anchor="lm")

    # Plot area margins
    gx0 = px + 68 * SS
    gy0 = py + 58 * SS
    gx1 = px + pw - 26 * SS
    gy1 = py + ph - 52 * SS
    gw = gx1 - gx0
    gh = gy1 - gy0

    # Shaded optimal window band if requested
    if highlight_band:
        bx0, bx1, b_txt = highlight_band
        rx0 = gx0 + gw * bx0
        rx1 = gx0 + gw * bx1
        draw.rectangle([rx0, gy0, rx1, gy1], fill=(246, 224, 214))
        if b_txt:
            draw.text((rx0 + 10 * SS, gy0 + 14 * SS), b_txt, fill=hex_rgb("#c45c32"), font=f_sub, anchor="lm")

    # Subtle gridlines & ticks
    for yn, ytxt in y_ticks:
        yy = gy1 - gh * yn
        draw.line([(gx0, yy), (gx1, yy)], fill=(214, 219, 222), width=int(1.0 * SS))
        draw.text((gx0 - 8 * SS, yy), ytxt, fill=DARK_COLOR, font=f_sub, anchor="rm")
    for xn, xtxt in x_ticks:
        xx = gx0 + gw * xn
        draw.line([(xx, gy0), (xx, gy1)], fill=(214, 219, 222), width=int(1.0 * SS))
        draw.text((xx, gy1 + 14 * SS), xtxt, fill=DARK_COLOR, font=f_sub, anchor="mm")

    # Axes
    draw.line([(gx0, gy0), (gx0, gy1), (gx1, gy1)], fill=INK_COLOR, width=int(2.0 * SS))
    draw.text(((gx0 + gx1) * 0.5, py + ph - 14 * SS), x_label, fill=INK_COLOR, font=f_sub, anchor="mm")
    draw.text((gx0 + 6 * SS, gy0 - 12 * SS), y_label, fill=INK_COLOR, font=f_sub, anchor="lm")

    # Animated series curves
    prog = ease_out_cubic(reveal_t)
    for idx, (pts, col, slbl, lw) in enumerate(series):
        if len(pts) < 2:
            continue
        max_x = prog
        vis_pts = []
        for k in range(len(pts)):
            xn, yn = pts[k]
            if xn <= max_x:
                vis_pts.append((gx0 + gw * xn, gy1 - gh * yn))
            else:
                if k > 0:
                    x_prev, y_prev = pts[k - 1]
                    if x_prev < max_x and xn > x_prev:
                        u = (max_x - x_prev) / (xn - x_prev)
                        yi = y_prev + (yn - y_prev) * u
                        vis_pts.append((gx0 + gw * max_x, gy1 - gh * yi))
                break
        if len(vis_pts) >= 2:
            draw.line(vis_pts, fill=col, width=int(lw * SS))
            ex, ey = vis_pts[-1]
            r = 4.0 * SS
            draw.ellipse([ex - r, ey - r, ex + r, ey + r], fill=col, outline=INK_COLOR, width=int(1.2 * SS))
            if prog > 0.75:
                dy_lbl = 15 * SS if (slbl.startswith("Sintered") or slbl.startswith("Matric") or slbl.startswith("Raw Regolith (78")) else -13 * SS
                draw.text((ex - 6 * SS, ey + dy_lbl), slbl, fill=col, font=f_sub, anchor="rm")


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
    if progress <= 0.02:
        return
    p = ease_out_cubic(progress)
    ax, ay = project(anchor_world[0], anchor_world[1], anchor_world[2], cam_x, cam_y)
    ex = ax + elbow_offset_px[0] * SS
    ey = ay + elbow_offset_px[1] * SS
    hx = ex + (-115 * SS if align_right else 115 * SS)
    hy = ey

    if p < 0.5:
        u = p / 0.5
        cx = ax + (ex - ax) * u
        cy = ay + (ey - ay) * u
        draw.line([(ax, ay), (cx, cy)], fill=INK_COLOR, width=int(1.6 * SS))
    else:
        u = (p - 0.5) / 0.5
        cx = ex + (hx - ex) * u
        draw.line([(ax, ay), (ex, ey), (cx, hy)], fill=INK_COLOR, width=int(1.6 * SS))

    r = 4.0 * SS
    draw.ellipse([ax - r, ay - r, ax + r, ay + r], fill=ACCENT_COLOR, outline=INK_COLOR, width=int(1.5 * SS))

    if p > 0.55:
        tx = hx + (-10 * SS if align_right else 10 * SS)
        anchor = "rm" if align_right else "lm"
        draw.text((tx, hy - 10 * SS), label_text, fill=INK_COLOR, font=font_title, anchor=anchor)
        if sub_text:
            draw.text((tx, hy + 13 * SS), sub_text, fill=DARK_COLOR, font=font_sub, anchor=anchor)


def load_fonts() -> Tuple[ImageFont.FreeTypeFont, ImageFont.FreeTypeFont, ImageFont.FreeTypeFont, ImageFont.FreeTypeFont]:
    font_path = "/System/Library/Fonts/HelveticaNeue.ttc"
    if not os.path.exists(font_path):
        font_path = "/System/Library/Fonts/Helvetica.ttc"
    idx_bold = 1 if "HelveticaNeue" in font_path else 0
    return (
        ImageFont.truetype(font_path, int(15 * SS), index=idx_bold),
        ImageFont.truetype(font_path, int(12 * SS), index=0),
        ImageFont.truetype(font_path, int(13 * SS), index=idx_bold),
        ImageFont.truetype(font_path, int(11 * SS), index=0),
    )


def draw_hud(draw: ImageDraw.ImageDraw, title: str, subtitle: str, frame: int, total_frames: int, fonts: Tuple):
    f_hdr, f_step, _, _ = fonts
    draw.text((64 * SS, 46 * SS), title, fill=INK_COLOR, font=f_hdr)
    draw.text((64 * SS, 70 * SS), subtitle, fill=DARK_COLOR, font=f_step)
    prog = (frame + 1) / float(total_frames)
    bar_y = H - 6 * SS
    draw.rectangle([0, bar_y, W, H], fill=MID_COLOR)
    draw.rectangle([0, bar_y, int(W * prog), H], fill=ACCENT_COLOR)


def encode_episode(
    mp4_path: str,
    poster_path: str,
    total_frames: int,
    poster_frame: int,
    render_fn: Callable[[int, Tuple], Image.Image],
    fonts: Tuple,
    label: str,
):
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
    for f in range(total_frames):
        im = render_fn(f, fonts)
        if f == poster_frame:
            im.save(poster_path)
        proc.stdin.write(im.tobytes())
        if (f + 1) % 120 == 0:
            print(f"[{label}] {f + 1}/{total_frames} frames")
    proc.stdin.close()
    stderr_out = proc.stderr.read().decode("utf-8", errors="ignore")
    ret = proc.wait()
    if ret != 0:
        print(f"[{label}] FFmpeg failed:", stderr_out, file=sys.stderr)
        sys.exit(ret)
    print(f"[OK] {label} -> {mp4_path}")
