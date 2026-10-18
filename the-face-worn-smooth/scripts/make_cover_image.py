"""Cut the brass plaque out of the museum photograph and set it on the cover color.

Input:  images/fumi-e-christ-on-the-cross.jpg  (Tokyo National Museum, CC BY 4.0)
Output: build/cover-plate.jpg
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from scipy import ndimage
from scipy.spatial import ConvexHull

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "images" / "fumi-e-christ-on-the-cross.jpg"
OUT = ROOT / "build" / "cover-plate.jpg"
BG = (21, 17, 12)  # must match --cover-bg in book.css

def main():
    im = Image.open(SRC).convert("RGB")
    a = np.asarray(im).astype(float)
    # The plaque is warm brass; the museum backdrop is a cool sage green.
    # Red minus blue separates them better than distance from a single color,
    # because the backdrop darkens toward the bottom of the photograph.
    mask = (a[:, :, 0] - a[:, :, 2]) > 36
    mask = ndimage.binary_opening(mask, iterations=3)
    mask = ndimage.binary_closing(mask, iterations=12)
    mask = ndimage.binary_fill_holes(mask)
    labels, n = ndimage.label(mask)
    sizes = ndimage.sum(mask, labels, range(1, n + 1))
    mask = labels == (int(np.argmax(sizes)) + 1)
    # The dark, worn rim is not as warm as the face of the plaque, so take the
    # convex hull of what was found; the plaque itself is convex.
    ys, xs = np.where(mask)
    pts = np.column_stack([xs, ys])[::50]
    hull = ConvexHull(pts)
    poly = Image.new("L", im.size, 0)
    ImageDraw.Draw(poly).polygon([tuple(map(float, pts[i])) for i in hull.vertices], fill=255)
    mask = ndimage.binary_dilation(np.asarray(poly) > 0, iterations=30)
    # Then trim back to brass: the backdrop is greener than it is red, brass never is.
    mask &= a[:, :, 0] > a[:, :, 1] + 1
    mask = ndimage.binary_opening(mask, iterations=2)
    mask = ndimage.binary_fill_holes(mask)
    # Smooth the outline so the edge reads as cast metal, not pixel noise.
    mask = ndimage.gaussian_filter(mask.astype(float), 6) > 0.5

    ys, xs = np.where(mask)
    pad = 160
    box = (max(xs.min() - pad, 0), max(ys.min() - pad, 0),
           min(xs.max() + pad, im.width), min(ys.max() + pad, im.height))

    alpha = Image.fromarray((mask * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.5))
    # soft shadow, offset down
    shadow = Image.fromarray((mask * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(40))
    canvas = Image.new("RGB", im.size, BG)
    dark = Image.new("RGB", im.size, (0, 0, 0))
    shadow_off = Image.new("L", im.size, 0)
    shadow_off.paste(shadow.point(lambda v: int(v * 0.85)), (0, 34))
    canvas = Image.composite(dark, canvas, shadow_off)
    canvas = Image.composite(im, canvas, alpha)
    canvas = canvas.crop(box)
    canvas.thumbnail((1500, 2000), Image.LANCZOS)
    OUT.parent.mkdir(exist_ok=True)
    canvas.save(OUT, quality=90)
    print(OUT, canvas.size)

if __name__ == "__main__":
    sys.exit(main())
