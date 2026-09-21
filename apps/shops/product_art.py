"""
Studio-style demo product images (pure Pillow, no network).

Generates gradient-canvas illustrations for the seeded demo catalog and
attaches them to matching Product rows. Used by:

- ``python manage.py seed_demo_data`` (automatic, skipped if Pillow missing)
- ``python scripts/generate_product_images.py --attach`` (standalone CLI)

Regeneration is cheap (~1 s) and idempotent: attach() only saves rows whose
image is not already pointing at the generated file.
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
MEDIA_PRODUCTS = BASE_DIR / "media" / "products"


# ---------------------------------------------------------------------------
# Drawing helpers (supersampled for anti-aliasing)
# ---------------------------------------------------------------------------

def rounded_rect(draw, box, radius, fill):
    draw.rounded_rectangle(box, radius=radius, fill=fill)


def soft_shadow(base_size, box, radius, blur_radius=30, alpha=70, offset=(0, 18)):
    """Return an RGBA shadow layer for a rounded box."""
    from PIL import Image, ImageDraw, ImageFilter
    scale = 2
    w, h = base_size
    layer = Image.new("RGBA", (w * scale, h * scale), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    ox, oy = offset
    shifted = (box[0] + ox * scale, box[1] + oy * scale,
               box[2] + ox * scale, box[3] + oy * scale)
    d.rounded_rectangle(shifted, radius=radius * scale, fill=(10, 10, 30, alpha))
    layer = layer.filter(ImageFilter.GaussianBlur(blur_radius * scale))
    return layer.resize((w, h), Image.LANCZOS)


def new_canvas(size, top_color, bottom_color):
    from PIL import Image, ImageDraw
    scale = 2
    w, h = size
    img = Image.new("RGB", (w * scale, h * scale), top_color)
    top, bottom = top_color, bottom_color
    d = ImageDraw.Draw(img)
    for y in range(h * scale):
        t = y / (h * scale)
        r = int(top[0] + (bottom[0] - top[0]) * t)
        g = int(top[1] + (bottom[1] - top[1]) * t)
        b = int(top[2] + (bottom[2] - top[2]) * t)
        d.rectangle([0, y, w * scale, y], fill=(r, g, b))
    return img


def finish(img, size):
    from PIL import Image
    w, h = size
    return img.resize((w, h), Image.LANCZOS)


def paste_shadow(img, box, radius):
    from PIL import Image
    shadow = soft_shadow(img.size, box, radius)
    return Image.alpha_composite(img.convert("RGBA"), shadow)


_font_cache = {}


def _font(size):
    from PIL import ImageFont
    if size in _font_cache:
        return _font_cache[size]
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    f = None
    for path in candidates:
        if os.path.exists(path):
            f = ImageFont.truetype(path, size)
            break
    if f is None:
        f = ImageFont.load_default()
    _font_cache[size] = f
    return f


# ---------------------------------------------------------------------------
# Product illustrations
# ---------------------------------------------------------------------------

def draw_headphones(img):
    """Wireless over-ear headphones."""
    from PIL import ImageDraw
    d = ImageDraw.Draw(img)
    W, H = img.size
    cx, cy = W // 2, int(H * 0.46)
    band_r = int(W * 0.30)
    lw = int(W * 0.055)

    # Headband (arc)
    d.arc([cx - band_r, cy - band_r + int(H * 0.06), cx + band_r, cy + band_r + int(H * 0.06)],
          start=180, end=360, fill=(240, 240, 255), width=lw)
    # Ear cups
    cup_w, cup_h = int(W * 0.11), int(W * 0.17)
    for sx in (-1, 1):
        ex = cx + sx * (band_r - lw // 2)
        ey = cy + int(H * 0.06)
        rounded_rect(d, [ex - cup_w // 2, ey - cup_h // 2, ex + cup_w // 2, ey + cup_h // 2],
                     radius=cup_w // 2, fill=(235, 235, 245))
        rounded_rect(d, [ex - int(cup_w * 0.30), ey - int(cup_h * 0.38),
                         ex + int(cup_w * 0.30), ey + int(cup_h * 0.38)],
                     radius=int(cup_w * 0.3), fill=(120, 120, 150))
    # Accent dot (power)
    d.ellipse([cx - lw // 2, cy - band_r + int(H * 0.06) - lw // 2,
               cx + lw // 2, cy - band_r + int(H * 0.06) + lw // 2], fill=(255, 196, 71))
    return img


def draw_watch(img):
    """Smart watch with round face and strap."""
    from PIL import ImageDraw
    d = ImageDraw.Draw(img)
    W, H = img.size
    cx, cy = W // 2, H // 2
    # Strap
    strap_w = int(W * 0.17)
    d.rounded_rectangle([cx - strap_w // 2, int(H * 0.14), cx + strap_w // 2, int(H * 0.86)],
                        radius=strap_w // 2, fill=(60, 60, 80))
    # Watch body
    body_r = int(W * 0.24)
    d.ellipse([cx - body_r, cy - body_r, cx + body_r, cy + body_r], fill=(28, 28, 40))
    # Screen
    screen_r = int(W * 0.195)
    d.ellipse([cx - screen_r, cy - screen_r, cx + screen_r, cy + screen_r], fill=(12, 16, 28))
    # Time text
    d.text((cx, cy - int(W * 0.03)), "09:41", fill=(126, 214, 255),
           font=_font(int(W * 0.085)), anchor="mm")
    # Heart-rate line
    pts = []
    base_y = cy + int(W * 0.09)
    for i, x in enumerate(range(cx - int(W * 0.10), cx + int(W * 0.10), int(W * 0.012))):
        y = base_y + (i % 4 == 2) * -int(W * 0.05)
        pts.append((x, y))
    d.line(pts, fill=(255, 99, 132), width=int(W * 0.008))
    return img


def draw_tshirt(img):
    """Designer t-shirt silhouette."""
    from PIL import ImageDraw
    d = ImageDraw.Draw(img)
    W, H = img.size
    cx = W // 2
    top = int(H * 0.26)
    neck_w = int(W * 0.16)
    sleeve = int(W * 0.16)
    body_w = int(W * 0.34)
    bottom = int(H * 0.80)
    shirt = (238, 240, 246)
    pts = [
        (cx - neck_w, top),
        (cx - body_w - sleeve, top + int(H * 0.07)),
        (cx - body_w - int(sleeve * 0.4), top + int(H * 0.17)),
        (cx - body_w, top + int(H * 0.12)),
        (cx - body_w, bottom),
        (cx + body_w, bottom),
        (cx + body_w, top + int(H * 0.12)),
        (cx + body_w + int(sleeve * 0.4), top + int(H * 0.17)),
        (cx + body_w + sleeve, top + int(H * 0.07)),
        (cx + neck_w, top),
    ]
    d.polygon(pts, fill=shirt)
    # Neckline
    d.arc([cx - neck_w, top - int(H * 0.045), cx + neck_w, top + int(H * 0.045)],
          start=0, end=180, fill=(180, 185, 200), width=int(W * 0.012))
    # Print on chest
    d.ellipse([cx - int(W * 0.10), top + int(H * 0.16),
               cx + int(W * 0.10), top + int(H * 0.16) + int(W * 0.20)],
              fill=(255, 122, 89))
    d.text((cx, top + int(H * 0.16) + int(W * 0.10)), "π", fill=(255, 255, 255),
           font=_font(int(W * 0.10)), anchor="mm")
    return img


def draw_jacket(img):
    """Leather jacket silhouette (open front)."""
    from PIL import ImageDraw
    d = ImageDraw.Draw(img)
    W, H = img.size
    cx = W // 2
    top = int(H * 0.24)
    bottom = int(H * 0.82)
    body_w = int(W * 0.30)
    sleeve = int(W * 0.17)
    leather = (86, 58, 42)
    dark = (64, 42, 30)
    # Left panel
    d.polygon([(cx - int(W * 0.05), top), (cx - body_w - sleeve, top + int(H * 0.06)),
               (cx - body_w - int(sleeve * 0.35), top + int(H * 0.18)),
               (cx - body_w + int(W * 0.02), top + int(H * 0.13)),
               (cx - int(W * 0.035), bottom)], fill=leather)
    # Right panel
    d.polygon([(cx + int(W * 0.05), top), (cx + body_w + sleeve, top + int(H * 0.06)),
               (cx + body_w + int(sleeve * 0.35), top + int(H * 0.18)),
               (cx + body_w - int(W * 0.02), top + int(H * 0.13)),
               (cx + int(W * 0.035), bottom)], fill=leather)
    # Collar
    d.polygon([(cx - int(W * 0.10), top), (cx, top + int(H * 0.05)),
               (cx + int(W * 0.10), top)], fill=dark)
    # Zipper
    d.line([(cx, top + int(H * 0.055)), (cx, bottom)], fill=(230, 200, 120),
           width=int(W * 0.010))
    # Stitch lines
    d.line([(cx - int(W * 0.30), top + int(H * 0.16)), (cx - int(W * 0.24), bottom)],
           fill=dark, width=int(W * 0.008))
    d.line([(cx + int(W * 0.30), top + int(H * 0.16)), (cx + int(W * 0.24), bottom)],
           fill=dark, width=int(W * 0.008))
    return img


def draw_code_card(img, accent=(88, 166, 255), secondary=(255, 196, 71)):
    """Programming course / e-book cover with code editor look."""
    from PIL import ImageDraw
    d = ImageDraw.Draw(img)
    W, H = img.size
    card_w, card_h = int(W * 0.56), int(H * 0.62)
    x0, y0 = (W - card_w) // 2, (H - card_h) // 2
    # Card
    rounded_rect(d, [x0, y0, x0 + card_w, y0 + card_h], radius=int(W * 0.03), fill=(24, 26, 36))
    # Title bar
    bar_h = int(card_h * 0.14)
    rounded_rect(d, [x0, y0, x0 + card_w, y0 + bar_h], radius=int(W * 0.03), fill=(36, 39, 54))
    d.rectangle([x0, y0 + bar_h // 2, x0 + card_w, y0 + bar_h], fill=(36, 39, 54))
    # Traffic lights
    for i, c in enumerate([(255, 95, 86), (255, 189, 46), (39, 201, 63)]):
        r = int(W * 0.012)
        cx = x0 + int(card_w * 0.06) + i * int(card_w * 0.07)
        cy = y0 + bar_h // 2
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=c)
    # Code lines
    line_h = int(card_h * 0.085)
    x_code = x0 + int(card_w * 0.08)
    y = y0 + bar_h + int(card_h * 0.09)
    indents = [0, 1, 2, 1, 0, 1]
    colors = [accent, secondary, accent, accent, secondary, accent]
    for i, (ind, col) in enumerate(zip(indents, colors)):
        width = int(card_w * (0.34 - 0.035 * (i % 3)))
        xx = x_code + ind * int(card_w * 0.07)
        d.rounded_rectangle([xx, y, xx + width, y + int(line_h * 0.42)],
                            radius=int(line_h * 0.2), fill=col)
        y += line_h
    # Cursor
    d.rectangle([x_code + int(card_w * 0.07) * 2, y - line_h,
                 x_code + int(card_w * 0.07) * 2 + int(W * 0.008),
                 y - line_h + int(line_h * 0.42)], fill=(240, 240, 240))
    return img


def draw_book(img, accent=(38, 166, 154)):
    """E-book cover with pages."""
    from PIL import ImageDraw
    d = ImageDraw.Draw(img)
    W, H = img.size
    cx, cy = W // 2, H // 2
    bw, bh = int(W * 0.40), int(H * 0.56)
    x0, y0 = cx - bw // 2, cy - bh // 2
    # Back pages
    for i in range(3):
        off = int(W * 0.016) * (3 - i)
        d.rounded_rectangle([x0 + off, y0 - off // 2, x0 + bw + off, y0 + bh - off // 2],
                            radius=int(W * 0.015), fill=(235, 232, 225))
    # Cover
    d.rounded_rectangle([x0, y0, x0 + bw, y0 + bh], radius=int(W * 0.015), fill=accent)
    # Spine
    d.rectangle([x0, y0, x0 + int(W * 0.022), y0 + bh], fill=tuple(max(0, c - 40) for c in accent))
    # Emblem
    r = int(W * 0.075)
    ecx, ecy = x0 + bw // 2 + int(W * 0.01), y0 + int(bh * 0.34)
    d.ellipse([ecx - r, ecy - r, ecx + r, ecy + r], outline=(255, 255, 255), width=int(W * 0.010))
    d.text((ecx, ecy), "</>", fill=(255, 255, 255), font=_font(int(W * 0.055)), anchor="mm")
    # Title lines
    for i, wl in enumerate((0.62, 0.44)):
        ly = y0 + int(bh * 0.62) + i * int(bh * 0.10)
        d.rounded_rectangle([x0 + int(bw * 0.16), ly, x0 + int(bw * 0.16) + int(bw * wl),
                             ly + int(W * 0.014)],
                            radius=int(W * 0.007), fill=(255, 255, 255))
    return img


# ---------------------------------------------------------------------------
# Catalog
# ---------------------------------------------------------------------------

IMAGES = {
    "wireless-headphones": {
        "match": ("Wireless Headphones",),
        "grad": ((26, 32, 56), (66, 78, 122)),
        "draw": draw_headphones,
    },
    "smart-watch": {
        "match": ("Smart Watch",),
        "grad": ((52, 28, 84), (126, 74, 180)),
        "draw": draw_watch,
    },
    "designer-tshirt": {
        "match": ("Designer T-Shirt",),
        "grad": ((255, 122, 89), (255, 179, 71)),
        "draw": draw_tshirt,
    },
    "leather-jacket": {
        "match": ("Leather Jacket",),
        "grad": ((52, 38, 30), (110, 80, 58)),
        "draw": draw_jacket,
    },
    "python-course": {
        "match": ("Python Programming Course",),
        "grad": ((20, 40, 80), (46, 96, 168)),
        "draw": lambda img: draw_code_card(img, accent=(255, 205, 66), secondary=(120, 200, 255)),
    },
    "webdev-ebook": {
        "match": ("Web Development E-Book",),
        "grad": ((10, 60, 76), (38, 166, 154)),
        "draw": lambda img: draw_book(img, accent=(24, 100, 128)),
    },
}


def generate_all(size=(900, 900)):
    MEDIA_PRODUCTS.mkdir(parents=True, exist_ok=True)
    paths = {}
    for slug, spec in IMAGES.items():
        img = new_canvas(size, *spec["grad"])
        scale = 2
        box = (int(size[0] * scale * 0.24), int(size[1] * scale * 0.24),
               int(size[0] * scale * 0.76), int(size[1] * scale * 0.76))
        img = paste_shadow(img, box, radius=int(size[0] * scale * 0.06))
        dimg = spec["draw"](img.convert("RGBA"))
        out = finish(dimg.convert("RGB"), size)
        path = MEDIA_PRODUCTS / f"{slug}.png"
        out.save(path, "PNG", optimize=True)
        paths[slug] = path
    return paths


def attach(paths):
    """Attach generated images to matching Product rows (idempotent).

    Requires Django to be set up (app registry ready).
    """
    from apps.shops.models import Product

    for slug, spec in IMAGES.items():
        for title in spec["match"]:
            p = Product.objects.filter(title__iexact=title).first()
            if p is None:
                continue
            rel = Path("products") / f"{slug}.png"
            if p.image and str(p.image).endswith(str(rel)):
                continue  # already attached
            p.image.name = str(rel)
            p.save(update_fields=["image"])


def ensure_product_images():
    """Generate demo images and attach them. Returns False if Pillow missing."""
    try:
        from PIL import Image  # noqa: F401
    except ImportError:
        return False
    attach(generate_all())
    return True
