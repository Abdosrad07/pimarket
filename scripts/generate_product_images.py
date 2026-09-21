"""
Standalone CLI wrapper around apps.shops.product_art.

Usage:
    python3 scripts/generate_product_images.py            # generate PNGs only
    python3 scripts/generate_product_images.py --attach   # + attach to products
"""
import argparse
import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pimarket.settings")

from apps.shops.product_art import generate_all, IMAGES, MEDIA_PRODUCTS  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--attach", action="store_true",
                        help="also attach generated images to matching Product rows")
    args = parser.parse_args()

    paths = generate_all()
    for slug, p in paths.items():
        print(f"generated {p.relative_to(BASE_DIR)}")

    if args.attach:
        import django
        django.setup()
        from apps.shops.product_art import attach
        attach(paths)
        print(f"attached {len(IMAGES)} images from {MEDIA_PRODUCTS}")


if __name__ == "__main__":
    main()
