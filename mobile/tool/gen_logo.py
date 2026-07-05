"""Generate the PROGNOS app logo assets — an exact match of the web favicon
(frontend/app/icon.tsx): indigo (#6366F1) rounded square + white lucide
`trending-up` arrow. Outputs the launcher master, the adaptive foreground, and
a splash logo into assets/icon/.
"""
from PIL import Image, ImageDraw

INDIGO = (0x63, 0x66, 0xF1, 255)
WHITE = (255, 255, 255, 255)

# lucide trending-up, viewBox 24x24
MAIN = [(22, 7), (13.5, 15.5), (8.5, 10.5), (2, 17)]
ARROW = [(16, 7), (22, 7), (22, 13)]
VB_MINX, VB_MINY, VB_W, VB_H = 2, 7, 20, 10  # arrow bounding box in viewBox units


def draw_arrow(draw, size, frac, color):
    """Draw the trending-up arrow centered, occupying `frac` of `size` wide."""
    scale = (frac * size) / VB_W
    off_x = (size - VB_W * scale) / 2
    off_y = (size - VB_H * scale) / 2
    w = max(1, round(2.5 * scale))

    def tp(pts):
        return [(off_x + (x - VB_MINX) * scale, off_y + (y - VB_MINY) * scale)
                for x, y in pts]

    for poly in (MAIN, ARROW):
        pts = tp(poly)
        draw.line(pts, fill=color, width=w, joint="curve")
        # round caps at every vertex (PIL has no native round caps)
        r = w / 2
        for (x, y) in pts:
            draw.ellipse([x - r, y - r, x + r, y + r], fill=color)


def rounded_square(size, radius, color):
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, size - 1, size - 1], radius=radius, fill=color)
    return img


def main():
    import os
    out = os.path.join(os.path.dirname(__file__), "..", "assets", "icon")
    os.makedirs(out, exist_ok=True)
    S = 1024

    # 1) Launcher / iOS master: indigo rounded square + white arrow (~52% wide)
    master = rounded_square(S, radius=round(S * 0.22), color=INDIGO)
    draw_arrow(ImageDraw.Draw(master), S, 0.52, WHITE)
    master.save(os.path.join(out, "app_icon.png"))

    # 2) Adaptive foreground: white arrow only, smaller for the safe zone (~40%)
    fg = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    draw_arrow(ImageDraw.Draw(fg), S, 0.40, WHITE)
    fg.save(os.path.join(out, "app_icon_foreground.png"))

    # 3) Splash logo: the full square logo (matches the web login mark)
    master.save(os.path.join(out, "splash_logo.png"))
    print("wrote app_icon.png, app_icon_foreground.png, splash_logo.png ->", out)


if __name__ == "__main__":
    main()
