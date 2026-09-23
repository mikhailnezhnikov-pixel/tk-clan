"""Build fixed-foot sprite animations from the existing Battle V4 pose art.

Run once when the art changes. The browser only decodes the resulting WebP
atlases; pixel warping and green-screen cleanup never run in its render loop.
"""
from pathlib import Path
import math
import numpy as np
from PIL import Image
from scipy.ndimage import map_coordinates

ROOT = Path(__file__).resolve().parents[1] / "units"
SHEET = np.asarray(Image.open(ROOT / "combat-atlas-v4.webp").convert("RGB"), dtype=np.float32)
CELL_W, CELL_H, COLS = 480, 320, 6
FOOT_X, FOOT_Y, BODY_HEIGHT = 185, 300, 260

# Crops and measurements belong to the existing atlas. Body heights exclude
# headwear, weapon and cape; every pose lands on the same foot line.
POSES = {
    "topking": [(0, 0, 420, 430, 290, 185, 391),
                (0, 450, 449, 360, 267, 150, 318),
                (0, 840, 420, 414, 274, 202, 333)],
    "raider": [(420, 0, 418, 430, 290, 190, 391),
               (449, 450, 389, 360, 267, 112, 318),
               (420, 840, 418, 414, 274, 195, 333)],
    "bot": [(838, 0, 416, 430, 290, 186, 391),
            (838, 450, 416, 360, 272, 164, 318),
            (838, 840, 416, 414, 283, 237, 333)],
}


def keyed(crop):
    rgb = crop.copy()
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    excess = g - np.maximum(r, b)
    alpha = 255 * (1 - np.clip((excess - 35) / 65, 0, 1))
    rgb[..., 1] = np.minimum(g, np.maximum(r, b) + 25)
    return Image.fromarray(np.uint8(np.dstack((rgb, alpha))), "RGBA")


def align(spec):
    x, y, width, height, body, footx, footy = spec
    art = keyed(SHEET[y:y + height, x:x + width])
    scale = BODY_HEIGHT / body
    art = art.resize((round(width * scale), round(height * scale)), Image.Resampling.LANCZOS)
    frame = Image.new("RGBA", (CELL_W, CELL_H))
    frame.alpha_composite(art, (round(FOOT_X - footx * scale), round(FOOT_Y - footy * scale)))
    return np.asarray(frame, dtype=np.uint8)


Y, X = np.mgrid[:CELL_H, :CELL_W].astype(np.float32)


def deform(src, breath=0, lean=0, drive=0, recoil=0):
    # Displacement is concentrated in the head, chest, arm and cape. The feet
    # are pinned: there is no translation below the ankle line.
    upper = np.clip((FOOT_Y - Y) / 230, 0, 1) ** 1.5
    head = np.exp(-((Y - 95) / 53) ** 2)
    chest = np.exp(-((Y - 175) / 65) ** 2)
    cape = np.exp(-((X - 80) / 80) ** 2) * np.clip((Y - 140) / 160, 0, 1)
    arm = np.exp(-((X - 235) / 76) ** 2 - ((Y - 150) / 85) ** 2)
    dx = lean * (3 * head + 1.5 * chest) + drive * (10 * upper + 6 * arm) + breath * 4 * cape - recoil * 9 * upper
    dy = -breath * (2.7 * head + 1.6 * chest) + drive * (2 * head - 4 * arm) + recoil * (3 * head + 2 * chest)
    coords = [Y - dy, X - dx]
    # Warp premultiplied colour so transparent green cannot bleed into edges.
    rgba = src.astype(np.float32)
    a = rgba[..., 3:4] / 255
    rgba[..., :3] *= a
    out = np.stack([map_coordinates(rgba[..., c], coords, order=1, mode="constant", cval=0) for c in range(4)], axis=-1)
    visible = out[..., 3] > 0.5
    out[..., :3][visible] *= 255 / out[..., 3][visible, None]
    return Image.fromarray(np.uint8(np.clip(out, 0, 255)), "RGBA")


def build(name, specs):
    idle, attack, hit = [align(spec) for spec in specs]
    frames = []
    for i in range(16):
        phase = 2 * math.pi * i / 16
        frames.append(deform(idle, breath=math.sin(phase), lean=math.sin(phase + .6)))

    # Distinct attack poses, arm/weapon drive and cape follow-through. The
    # transition is deliberately fast, like a drawn action, and the returned
    # frames settle at the same origin as idle.
    for i in range(12):
        if i < 3:
            frame = deform(idle, breath=-.4, lean=-i * .22, drive=-.22 * i)
        elif i < 10:
            drive = [0, .45, 1, 1.4, 1.25, .8, .35][i - 3]
            frame = deform(attack, drive=drive, lean=drive * .5)
        else:
            frame = deform(idle, breath=-.25 + .25 * (i - 10), lean=.2)
        frames.append(frame)

    for i in range(8):
        if i == 0 or i >= 7:
            frame = deform(idle, recoil=0)
        else:
            recoil = [.5, 1.2, 1.5, 1.15, .7, .3][i - 1]
            frame = deform(hit, recoil=recoil, lean=-recoil * .35)
        frames.append(frame)

    atlas = Image.new("RGBA", (COLS * CELL_W, 6 * CELL_H))
    for i, frame in enumerate(frames):
        atlas.paste(frame, ((i % COLS) * CELL_W, (i // COLS) * CELL_H))
    path = ROOT / f"{name}-motion-v5.webp"
    atlas.save(path, "WEBP", quality=83, method=6)
    print(path.name, path.stat().st_size, "bytes", len(frames), "frames")


for fighter, poses in POSES.items():
    build(fighter, poses)
