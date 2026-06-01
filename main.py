import argparse
import re
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


BASE_DIR = Path(__file__).resolve().parent
FONTS_DIR = BASE_DIR / "fonts"
DIST_DIR = BASE_DIR / "dist"

COLOR_MAP = {
    "orange": (255, 127, 0, 255),
    "red": (220, 20, 60, 255),
    "blue": (30, 90, 220, 255),
    "green": (34, 139, 34, 255),
    "black": (0, 0, 0, 255),
    "white": (255, 255, 255, 255),
    "yellow": (255, 215, 0, 255),
    "purple": (128, 0, 128, 255),
    "pink": (255, 105, 180, 255),
}


def parse_args():
    parser = argparse.ArgumentParser(
        description="두 줄 문구를 꽉 채운 투명 PNG 이모티콘으로 생성합니다."
    )
    parser.add_argument("--chars01", default="고맙", help="첫 번째 줄 문구")
    parser.add_argument(
        "--chars02",
        default="습니다",
        help="두 번째 줄 문구 (chars01만 지정하면 단일 줄로 렌더링)",
    )
    parser.add_argument(
        "--color",
        default="orange",
        help="텍스트 색상 이름 (기본: orange, --color-list로 확인)",
    )
    parser.add_argument(
        "--color-list",
        action="store_true",
        help="사용 가능한 색상 목록 출력 후 종료",
    )
    parser.add_argument(
        "--size",
        type=int,
        default=64,
        help="정사각형 크기 (예: 64 -> 64x64, 128 -> 128x128)",
    )
    parser.add_argument(
        "--font",
        default="IropkeBatangM.ttf",
        help="fonts 디렉토리의 폰트 파일명 (확장자 생략 가능)",
    )
    return parser.parse_args()


def sanitize_filename_component(text):
    cleaned = re.sub(r"\s+", "_", text.strip())
    cleaned = re.sub(r"[\\/:*?\"<>|]", "", cleaned)
    cleaned = cleaned.strip("._")
    return cleaned or "text"


def resolve_font_path(font_name):
    name = font_name.strip()
    if not name:
        raise ValueError("폰트 이름이 비어 있습니다.")
    if "." not in name:
        name = f"{name}.ttf"
    font_path = FONTS_DIR / name
    if not font_path.is_file():
        raise FileNotFoundError(
            f"폰트를 찾을 수 없습니다: {font_path} (fonts 디렉토리를 확인하세요)"
        )
    return font_path


def resolve_color(color_name):
    key = color_name.lower().strip()
    if key not in COLOR_MAP:
        available = ", ".join(sorted(COLOR_MAP.keys()))
        raise ValueError(
            f"지원하지 않는 색상입니다: {color_name}. 사용 가능 색상: {available}"
        )
    return COLOR_MAP[key]


def build_output_path(chars01, chars02):
    DIST_DIR.mkdir(parents=True, exist_ok=True)
    c1 = sanitize_filename_component(chars01)
    if chars02 is None:
        return DIST_DIR / f"{c1}.png"
    c2 = sanitize_filename_component(chars02)
    return DIST_DIR / f"{c1}_{c2}.png"


def option_was_provided(argv, option_name):
    return any(arg == option_name or arg.startswith(f"{option_name}=") for arg in argv)


def resolve_render_lines(args, argv):
    chars01_was_provided = option_was_provided(argv, "--chars01")
    chars02_was_provided = option_was_provided(argv, "--chars02")

    if chars01_was_provided and not chars02_was_provided:
        return args.chars01, None

    return args.chars01, args.chars02


def render_text_filled(image, text, box, font_path, color):
    """Render text so it fills the given box as much as possible.
    box: (x0, y0, x1, y1)
    """
    x0, y0, x1, y1 = box
    box_w = x1 - x0
    box_h = y1 - y0

    # Find a large readable base font, then distort to fill the target box.
    best_size = 12
    lo, hi = 8, 256
    while lo <= hi:
        mid = (lo + hi) // 2
        try:
            font = ImageFont.truetype(str(font_path), mid)
        except Exception:
            break

        tmp = Image.new("L", (box_w * 4, box_h * 4), 0)
        d = ImageDraw.Draw(tmp)
        d.text((tmp.width // 2, tmp.height // 2), text, fill=255, font=font, anchor="mm")
        bbox = tmp.getbbox()
        if not bbox:
            hi = mid - 1
            continue

        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        if tw <= box_w * 3 and th <= box_h * 3:
            best_size = mid
            lo = mid + 1
        else:
            hi = mid - 1

    try:
        font = ImageFont.truetype(str(font_path), best_size)
    except Exception:
        font = ImageFont.load_default()

    # Render text mask and crop tight bounds.
    text_mask = Image.new("L", (box_w * 4, box_h * 4), 0)
    d = ImageDraw.Draw(text_mask)
    d.text((text_mask.width // 2, text_mask.height // 2), text, fill=255, font=font, anchor="mm")
    bbox = text_mask.getbbox()
    if not bbox:
        return

    glyph = text_mask.crop(bbox)

    # Fill the box aggressively; slight inset avoids clipping antialias edges.
    target_w = max(1, int(box_w * 0.98))
    target_h = max(1, int(box_h * 0.98))
    glyph = glyph.resize((target_w, target_h), Image.Resampling.LANCZOS)

    # Compose a colored layer with glyph alpha and paste into the image.
    layer = Image.new("RGBA", (target_w, target_h), color)
    layer.putalpha(glyph)
    px = x0 + (box_w - target_w) // 2
    py = y0 + (box_h - target_h) // 2
    image.alpha_composite(layer, (px, py))


def create_emoji(chars01, chars02, size_px, color_rgba, font_path):
    image = Image.new("RGBA", (size_px, size_px), (0, 0, 0, 0))
    if chars02 is None:
        render_text_filled(image, chars01, (0, 0, size_px, size_px), font_path, color_rgba)
        return image

    half = size_px // 2
    top_box = (0, 0, size_px, half)
    bottom_box = (0, half, size_px, size_px)

    render_text_filled(image, chars01, top_box, font_path, color_rgba)
    render_text_filled(image, chars02, bottom_box, font_path, color_rgba)
    return image


def main():
    args = parse_args()
    chars01, chars02 = resolve_render_lines(args, sys.argv[1:])

    if args.color_list:
        print("사용 가능한 색상:")
        for name in sorted(COLOR_MAP.keys()):
            print(f"- {name}")
        return

    if args.size < 16:
        raise ValueError("--size 는 16 이상의 정수를 사용하세요.")

    color_rgba = resolve_color(args.color)
    font_path = resolve_font_path(args.font)
    output_path = build_output_path(chars01, chars02)

    image = create_emoji(chars01, chars02, args.size, color_rgba, font_path)
    image.save(output_path, "PNG", optimize=True)
    print(f"성공: {output_path} 파일이 생성되었습니다.")

if __name__ == "__main__":
    main()
