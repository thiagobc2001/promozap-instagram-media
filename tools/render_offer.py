"""Render distinct, factual PromoZap Feed and Story artwork from a real product photo."""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
BACKGROUND = HERE / "background-promo-v1.jpg"
if not BACKGROUND.is_file():
    BACKGROUND = ROOT / "assets" / "instagram-background-promo-v1.jpg"
LOGO = ROOT / "assets" / "promozap-logo.jpg"
FONT_BOLD = next((str(path) for path in [Path("C:/Windows/Fonts/arialbd.ttf"), Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")] if path.is_file()), "DejaVuSans-Bold.ttf")
FONT_REGULAR = next((str(path) for path in [Path("C:/Windows/Fonts/arial.ttf"), Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")] if path.is_file()), "DejaVuSans.ttf")
BLUE = "#061943"
ORANGE = "#ff9714"
YELLOW = "#ffcf28"


def font(size: int, bold: bool = True) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(FONT_BOLD if bold else FONT_REGULAR, size)


def background(size: tuple[int, int]) -> Image.Image:
    plate = Image.open(BACKGROUND).convert("RGB")
    return ImageOps.fit(plate, size, Image.Resampling.LANCZOS, centering=(0.5, 0.5))


def rounded_photo(canvas: Image.Image, photo_path: Path, box: tuple[int, int, int, int]) -> None:
    left, top, right, bottom = box
    width, height = right - left, bottom - top
    shadow = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    shade = ImageDraw.Draw(shadow)
    shade.rounded_rectangle((left + 10, top + 16, right + 10, bottom + 16), radius=43, fill=(0, 7, 42, 95))
    canvas.paste(Image.alpha_composite(canvas.convert("RGBA"), shadow).convert("RGB"))
    photo = Image.open(photo_path).convert("RGB")
    photo = ImageOps.contain(photo, (width - 20, height - 20), Image.Resampling.LANCZOS)
    panel = Image.new("RGB", (width, height), "#eaf3ff")
    panel.paste(photo, ((width - photo.width) // 2, (height - photo.height) // 2))
    mask = Image.new("L", (width, height), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, width - 1, height - 1), radius=34, fill=255)
    canvas.paste(panel, (left, top), mask)
    ImageDraw.Draw(canvas).rounded_rectangle(box, radius=34, outline="#ffffff", width=8)


def brand(canvas: Image.Image, top: int, logo_size: int, name_size: int, tagline_size: int) -> None:
    draw = ImageDraw.Draw(canvas)
    left = 54
    logo = ImageOps.fit(Image.open(LOGO).convert("RGB"), (logo_size, logo_size))
    mask = Image.new("L", (logo_size, logo_size), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, logo_size - 1, logo_size - 1), radius=logo_size // 5, fill=255)
    canvas.paste(logo, (left, top), mask)
    x = left + logo_size + 23
    draw.text((x + 3, top + 9), "PromoZap", font=font(name_size), fill="#00113a")
    draw.text((x, top + 6), "PromoZap", font=font(name_size), fill="white")
    draw.text((x + 2, top + logo_size - tagline_size - 10), "OFERTAS TODOS OS DIAS", font=font(tagline_size), fill=YELLOW)


def headline(draw: ImageDraw.ImageDraw, title: str, left: int, top: int, max_width: int, max_lines: int, start_size: int) -> int:
    for size in range(start_size, 37, -2):
        face = font(size)
        words = title.split()
        lines: list[str] = []
        current = ""
        for word in words:
            trial = f"{current} {word}".strip()
            if current and draw.textbbox((0, 0), trial, font=face)[2] > max_width:
                lines.append(current)
                current = word
            else:
                current = trial
        if current:
            lines.append(current)
        if len(lines) <= max_lines:
            break
    line_height = int(size * 1.13)
    for index, line in enumerate(lines):
        y = top + index * line_height
        draw.text((left + 3, y + 4), line, font=face, fill="#00113a")
        draw.text((left, y), line, font=face, fill="white")
    return top + len(lines) * line_height


def price_panel(draw: ImageDraw.ImageDraw, price: str, box: tuple[int, int, int, int], price_size: int, before: str = "", coupon: str = "") -> None:
    left, top, right, bottom = box
    draw.rounded_rectangle(box, radius=37, fill=BLUE, outline=YELLOW, width=6)
    label = "PREÇO DA OFERTA" if price else "CONFIRA AS CONDIÇÕES"
    draw.text((left + 33, top + 18), label, font=font(30), fill="#bfe8ff")
    if not price:
        return
    if before:
        old_font = font(40)
        old_width = draw.textbbox((0, 0), before, font=old_font)[2]
        old_x = right - 38 - old_width
        draw.text((old_x, top + 18), before, font=old_font, fill="#ffffff")
        draw.line((old_x - 4, top + 45, right - 35, top + 45), fill="#ff5722", width=6)
    face = font(price_size)
    width = draw.textbbox((0, 0), price, font=face)[2]
    max_price_width = right - left - (470 if coupon else 68)
    while width > max_price_width and price_size > 72:
        price_size -= 4
        face = font(price_size)
        width = draw.textbbox((0, 0), price, font=face)[2]
    draw.text((left + 31 + 5, top + 50 + 6), price, font=face, fill="#a73500")
    draw.text((left + 31, top + 50), price, font=face, fill=YELLOW)
    if coupon:
        pill = (right - 420, top + 93, right - 25, bottom - 22)
        draw.rounded_rectangle(pill, radius=24, fill=YELLOW)
        draw.text((pill[0] + 19, pill[1] + 13), "CUPOM", font=font(25), fill=BLUE)
        coupon_size = 41
        coupon_font = font(coupon_size)
        while draw.textbbox((0, 0), coupon, font=coupon_font)[2] > pill[2] - pill[0] - 30 and coupon_size > 24:
            coupon_size -= 2
            coupon_font = font(coupon_size)
        draw.text((pill[0] + 17, pill[1] + 43), coupon, font=coupon_font, fill=BLUE)


def render_feed(photo: Path, title: str, price: str, out: Path, before: str = "", coupon: str = "") -> None:
    canvas = background((1080, 1350))
    brand(canvas, top=46, logo_size=132, name_size=68, tagline_size=25)
    draw = ImageDraw.Draw(canvas)
    draw.rounded_rectangle((54, 199, 440, 251), radius=26, fill=ORANGE)
    draw.text((82, 208), "OFERTA PROMOZAP", font=font(30), fill=BLUE)
    rounded_photo(canvas, photo, (128, 267, 952, 969))
    draw = ImageDraw.Draw(canvas)
    headline(draw, title, 65, 989, 950, 2, 52)
    price_panel(draw, price, (62, 1123, 1018, 1321), 142, before, coupon)
    canvas.save(out, "JPEG", quality=95, subsampling=0, optimize=True)


def render_story(photo: Path, title: str, price: str, out: Path, before: str = "", coupon: str = "") -> None:
    canvas = background((1080, 1920))
    brand(canvas, top=92, logo_size=154, name_size=74, tagline_size=29)
    draw = ImageDraw.Draw(canvas)
    draw.rounded_rectangle((54, 298, 445, 357), radius=28, fill=ORANGE)
    draw.text((85, 309), "OFERTA PROMOZAP", font=font(31), fill=BLUE)
    headline(draw, title, 62, 381, 950, 3, 66)
    rounded_photo(canvas, photo, (61, 585, 1019, 1495))
    draw = ImageDraw.Draw(canvas)
    price_panel(draw, price, (61, 1530, 1019, 1750), 154, before, coupon)
    footer = "Mais ofertas no grupo PromoZap"
    f = font(39, bold=False)
    width = draw.textbbox((0, 0), footer, font=f)[2]
    draw.text(((1080 - width) // 2, 1810), footer, font=f, fill="white")
    canvas.save(out, "JPEG", quality=95, subsampling=0, optimize=True)


def main() -> None:
    global BACKGROUND, LOGO
    parser = argparse.ArgumentParser()
    parser.add_argument("--photo", type=Path, required=True)
    parser.add_argument("--title", required=True)
    parser.add_argument("--price", required=True)
    parser.add_argument("--before", default="")
    parser.add_argument("--coupon", default="")
    parser.add_argument("--background", type=Path, default=BACKGROUND)
    parser.add_argument("--logo", type=Path, default=LOGO)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    BACKGROUND, LOGO = args.background, args.logo
    if not args.photo.is_file():
        raise SystemExit("Foto original não encontrada")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    render_feed(args.photo, args.title, args.price, args.output_dir / "feed.jpg", args.before, args.coupon)
    render_story(args.photo, args.title, args.price, args.output_dir / "story.jpg", args.before, args.coupon)
    print(args.output_dir / "feed.jpg")
    print(args.output_dir / "story.jpg")


if __name__ == "__main__":
    main()
