#!/usr/bin/env python3
"""Generates the app's seagull logo as a tapered-stroke silhouette (two
cubic Bezier arcs meeting at a center dip - the classic minimalist
"gull in flight" glyph) and exports it as logo.png (for the in-app header
and window icon) and icon.ico (multi-resolution, for the Windows .exe).

Re-run this after editing the control points below:
    python3 -m pip install numpy pillow
    python3 assets/generate_logo.py

(numpy/Pillow are only needed to regenerate these assets - not runtime
dependencies of the app itself, so they're deliberately not in
requirements.txt.)
"""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

OUT_DIR = Path(__file__).parent

# Brand color for the bird itself.
COLOR = (31, 111, 235, 255)  # #1f6feb
# Round black badge behind the bird.
BADGE_COLOR = (0, 0, 0, 255)
BADGE_MARGIN_FRAC = 0.04  # badge radius = 0.5 - this, i.e. ~92% of the canvas

# Two symmetric cubic Bezier arcs (left wing, right wing) sharing a center
# "body dip" point. Coordinates are in an abstract unit square-ish space,
# y-up (mathematical convention - flipped to image (y-down) space at the
# end). Tune these to reshape the bird.
P0 = (-100, 12)  # left wingtip, tilted slightly up for a soaring look
C1 = (-72, 85)  # pulls the curve up out of the wingtip
C2 = (-20, 32)  # pulls it back down toward the body
PM = (0, -32)  # body dip (center, lowest point - the "head/body" notch)
C3 = (20, 32)  # mirror of C2
C4 = (72, 85)  # mirror of C1
P2 = (100, 12)  # right wingtip

N_SAMPLES = 400  # per half-wing, before combining


def cubic_bezier(p0, c1, c2, p3, n):
    t = np.linspace(0, 1, n)[:, None]
    p0, c1, c2, p3 = (np.array(p) for p in (p0, c1, c2, p3))
    return (
        (1 - t) ** 3 * p0
        + 3 * (1 - t) ** 2 * t * c1
        + 3 * (1 - t) * t**2 * c2
        + t**3 * p3
    )


def build_centerline():
    left = cubic_bezier(P0, C1, C2, PM, N_SAMPLES)
    right = cubic_bezier(PM, C3, C4, P2, N_SAMPLES)
    return np.concatenate([left, right[1:]], axis=0)


def tapered_outline(centerline, width_at_start, width_at_end):
    """Offsets a single smooth arc perpendicular to its direction, with
    width tapering linearly from one end to the other, producing a closed
    polygon for a solid fill.

    Each wing is offset independently (rather than offsetting the full
    two-arc path as one polygon) because the two arcs meet at a cusp (the
    body dip has a sharp direction change, by design) - offsetting straight
    through a cusp makes the polygon self-intersect there, which shows up
    as a small stray notch/triangle artifact in the fill.
    """
    n = len(centerline)
    tangents = np.gradient(centerline, axis=0)
    norms = np.linalg.norm(tangents, axis=1, keepdims=True)
    tangents = tangents / np.clip(norms, 1e-9, None)
    normals = np.stack([-tangents[:, 1], tangents[:, 0]], axis=1)

    t = np.linspace(0, 1, n)
    width = width_at_start + (width_at_end - width_at_start) * t
    width = width[:, None]

    upper = centerline + normals * width
    lower = centerline - normals * width
    return np.concatenate([upper, lower[::-1]], axis=0)


JOIN_WIDTH = 15  # must match the width at PM in both tapered_outline() calls below


def render(scale, margin_frac=0.2):
    left = cubic_bezier(P0, C1, C2, PM, N_SAMPLES)
    right = cubic_bezier(PM, C3, C4, P2, N_SAMPLES)
    left_outline = tapered_outline(left, width_at_start=3, width_at_end=JOIN_WIDTH)
    right_outline = tapered_outline(right, width_at_start=JOIN_WIDTH, width_at_end=3)

    # Normalize together, scaled by the larger dimension (preserves aspect
    # ratio) and centered on the smaller one (a wide/short glyph like this
    # would otherwise hug one edge of a square canvas instead of sitting in
    # the middle).
    all_pts = np.concatenate([left_outline, right_outline], axis=0)
    min_xy = all_pts.min(axis=0)
    max_xy = all_pts.max(axis=0)
    extent = max_xy - min_xy
    span = extent.max()
    canvas = scale
    draw_size = canvas * (1 - 2 * margin_frac)
    center_offset = (span - extent) / 2  # extra space on the shorter axis

    def to_image_space(pts):
        norm = (pts - min_xy + center_offset) / span  # 0..1, y-up, centered
        px = norm[:, 0] * draw_size + canvas * margin_frac
        py = (1 - norm[:, 1]) * draw_size + canvas * margin_frac  # flip y
        return np.stack([px, py], axis=1)

    img = Image.new("RGBA", (canvas, canvas), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    badge_pad = canvas * BADGE_MARGIN_FRAC
    draw.ellipse([badge_pad, badge_pad, canvas - badge_pad, canvas - badge_pad], fill=BADGE_COLOR)

    for outline in (left_outline, right_outline):
        img_pts = to_image_space(outline)
        draw.polygon([tuple(p) for p in img_pts], fill=COLOR)

    # Round cap over the wing joint at PM: offsetting two strokes through a
    # sharp cusp leaves a "miter spike" poking out past the joint (a classic
    # vector-stroke artifact). A filled circle there covers it with a clean
    # rounded join instead.
    pm_img = to_image_space(np.array([PM]))[0]
    r = (JOIN_WIDTH / span) * draw_size
    draw.ellipse([pm_img[0] - r, pm_img[1] - r, pm_img[0] + r, pm_img[1] + r], fill=COLOR)

    return img


def main():
    # Supersample at 4x then downsample for anti-aliasing.
    supersample = 4
    full_res = None
    for size in (256, 64):
        big = render(size * supersample)
        logo = big.resize((size, size), Image.LANCZOS)
        name = "logo.png" if size == 256 else f"logo_{size}.png"
        logo.save(OUT_DIR / name)
        print(f"wrote {OUT_DIR / name} ({size}x{size})")
        if size == 256:
            full_res = logo

    # Multi-resolution .ico for the Windows executable.
    icon_path = OUT_DIR / "icon.ico"
    full_res.save(icon_path, sizes=[(16, 16), (32, 32), (48, 48), (128, 128), (256, 256)])
    print(f"wrote {icon_path}")


if __name__ == "__main__":
    main()
