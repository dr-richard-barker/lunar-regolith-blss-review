#!/usr/bin/env python3
"""
Shared orthographic 30-degree isometric miniature rendering engine.

Enforces:
- Palette: bg #eef2f3, ink #2d3142, accent #ef8354, shades #4f5d75 & #bfc0c0
- Three flat tones per block (light top, mid left, dark right)
- 40px drop-in bounce staggered by 3 frames
- Pure 2D orthographic camera slide (never rotates into perspective)
- Thin #2d3142 elbow leader-line annotations
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

PALETTES: Dict[str, Tuple[Tuple[int, int, int], Tuple[int, int, int], Tuple[int, int, int]]] = {
    "light": ((238, 242, 243), (191, 192, 192), (138, 146, 158)),
    "mid": ((214, 219, 222), (146, 156, 170), (79, 93, 117)),
    "dark": ((191, 192, 192), (79, 93, 117), (45, 49, 66)),
    "accent": ((246, 170, 134), (239, 131, 84), (196, 92, 50)),
    "glass": ((247, 250, 251), (191, 192, 192), (79, 93, 117)),
}


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
    """40px (at 1080p) vertical drop-in with small damped bounce, staggered by 3 frames."""
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

    def sort_key(self) -> Tuple[int, float, float]:
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

        p_top = [p(x0, y0, z1), p(x1, y0, z1), p(x1, y1, z1), p(x0, y1, z1)]
        p_left = [p(x0, y1, z1), p(x1, y1, z1), p(x1, y1, z0), p(x0, y1, z0)]
        p_right = [p(x1, y0, z1), p(x1, y1, z1), p(x1, y1, z0), p(x1, y0, z0)]

        sw = int(round(self.stroke_w))
        draw.polygon(p_left, fill=left_col, outline=INK_COLOR, width=sw)
        draw.polygon(p_right, fill=right_col, outline=INK_COLOR, width=sw)
        draw.polygon(p_top, fill=top_col, outline=INK_COLOR, width=sw)


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
    hx = ex + (-120 * SS if align_right else 120 * SS)
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
    draw.ellipse([ax - r, ay - r, ax + r, ay + r], fill=hex_rgb(ACCENT_HEX), outline=INK_COLOR, width=int(1.5 * SS))

    if p > 0.55:
        tx = hx + (-10 * SS if align_right else 10 * SS)
        anchor = "rm" if align_right else "lm"
        draw.text((tx, hy - 10 * SS), label_text, fill=INK_COLOR, font=font_title, anchor=anchor)
        if sub_text:
            draw.text((tx, hy + 13 * SS), sub_text, fill=hex_rgb(SHADE_DARK_HEX), font=font_sub, anchor=anchor)


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
    draw.text((64 * SS, 70 * SS), subtitle, fill=hex_rgb(SHADE_DARK_HEX), font=f_step)
    prog = (frame + 1) / float(total_frames)
    bar_y = H - 6 * SS
    draw.rectangle([0, bar_y, W, H], fill=hex_rgb(SHADE_MID_HEX))
    draw.rectangle([0, bar_y, int(W * prog), H], fill=hex_rgb(ACCENT_HEX))


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
