from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Normalize transparent researcher portraits to a consistent canvas."
    )
    parser.add_argument(
        "inputs",
        nargs="+",
        help="Input image paths (PNG/WebP with transparent background recommended).",
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Directory for processed images. Defaults to the source image folder.",
    )
    parser.add_argument(
        "--canvas-width",
        type=int,
        default=1080,
        help="Output canvas width in pixels.",
    )
    parser.add_argument(
        "--canvas-height",
        type=int,
        default=1400,
        help="Output canvas height in pixels.",
    )
    parser.add_argument(
        "--side-margin",
        type=float,
        default=0.07,
        help="Relative left/right margin (0.0-0.4).",
    )
    parser.add_argument(
        "--top-margin",
        type=float,
        default=0.04,
        help="Relative top margin (0.0-0.4).",
    )
    parser.add_argument(
        "--bottom-margin",
        type=float,
        default=0.02,
        help="Relative bottom margin (0.0-0.4).",
    )
    parser.add_argument(
        "--suffix",
        default="-styled",
        help="Suffix appended to processed file names.",
    )
    return parser.parse_args()


def find_alpha_bbox(image: Image.Image) -> tuple[int, int, int, int]:
    alpha = image.getchannel("A")
    bbox = alpha.getbbox()
    if bbox is None:
        return (0, 0, image.width, image.height)
    return bbox


def normalize_image(
    src_path: Path,
    dst_path: Path,
    canvas_width: int,
    canvas_height: int,
    side_margin: float,
    top_margin: float,
    bottom_margin: float,
) -> None:
    with Image.open(src_path) as source:
        image = source.convert("RGBA")
        crop_box = find_alpha_bbox(image)
        crop = image.crop(crop_box)

    max_w = int(canvas_width * max(0.1, 1.0 - (2 * side_margin)))
    max_h = int(canvas_height * max(0.1, 1.0 - top_margin - bottom_margin))
    scale = min(max_w / crop.width, max_h / crop.height)
    resized_w = max(1, int(crop.width * scale))
    resized_h = max(1, int(crop.height * scale))
    resized = crop.resize((resized_w, resized_h), Image.Resampling.LANCZOS)

    canvas = Image.new("RGBA", (canvas_width, canvas_height), (0, 0, 0, 0))
    x = (canvas_width - resized_w) // 2
    bottom_px = int(canvas_height * max(0.0, bottom_margin))
    y = canvas_height - resized_h - bottom_px
    y = max(0, y)
    canvas.alpha_composite(resized, dest=(x, y))

    dst_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(dst_path, format="PNG", optimize=True)


def main() -> None:
    args = parse_args()
    for raw_path in args.inputs:
        src_path = Path(raw_path).expanduser().resolve()
        if not src_path.exists():
            print(f"[SKIP] Not found: {src_path}")
            continue

        output_dir = (
            Path(args.output_dir).expanduser().resolve()
            if args.output_dir
            else src_path.parent
        )
        dst_name = f"{src_path.stem}{args.suffix}.png"
        dst_path = output_dir / dst_name

        normalize_image(
            src_path=src_path,
            dst_path=dst_path,
            canvas_width=args.canvas_width,
            canvas_height=args.canvas_height,
            side_margin=args.side_margin,
            top_margin=args.top_margin,
            bottom_margin=args.bottom_margin,
        )
        print(f"[OK] {src_path.name} -> {dst_path}")


if __name__ == "__main__":
    main()
