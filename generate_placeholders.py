"""Генерация фирменных изображений-плейсхолдеров для направлений и туров.

Создаёт сдержанные градиентные изображения в цветах бренда с названием
направления. Владелец сайта заменит их реальными фотографиями (те же имена
файлов в static/img/).
"""
import os
from PIL import Image, ImageDraw, ImageFont

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "img")
W, H = 1200, 800

NAVY = (16, 35, 63)
GOLD = (199, 166, 106)

# Оттенки для каждого направления (верх, низ) — сдержанные морские/тёплые тона
PALETTES = {
    "turkey": ((26, 68, 108), (64, 132, 160)),
    "egypt": ((120, 88, 50), (199, 166, 106)),
    "uae": ((36, 52, 88), (110, 130, 160)),
    "thailand": ((20, 84, 92), (66, 150, 138)),
    "maldives": ((18, 74, 110), (80, 170, 190)),
    "vietnam": ((24, 80, 66), (84, 150, 112)),
    "italy": ((70, 54, 84), (150, 110, 130)),
    "russia": ((22, 50, 82), (78, 118, 152)),
}

NAMES = {
    "turkey": "Турция", "egypt": "Египет", "uae": "ОАЭ", "thailand": "Таиланд",
    "maldives": "Мальдивы", "vietnam": "Вьетнам", "italy": "Италия", "russia": "Россия",
}


def find_font(size):
    for path in (
        r"C:\Windows\Fonts\georgia.ttf",
        r"C:\Windows\Fonts\arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ):
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def make_image(slug, name, top, bottom):
    img = Image.new("RGB", (W, H))
    px = img.load()
    for y in range(H):
        t = y / H
        row = tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3))
        for x in range(W):
            px[x, y] = row

    # Тонкая золотая линия-горизонт
    draw = ImageDraw.Draw(img)
    draw.line([(0, int(H * 0.68)), (W, int(H * 0.68))], fill=GOLD + (255,) if len(GOLD) == 3 else GOLD, width=3)

    # Круг-солнце/лунный акцент
    cx, cy, r = int(W * 0.72), int(H * 0.34), 90
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=GOLD, width=4)

    # Название
    font = find_font(84)
    small = find_font(30)
    bbox = draw.textbbox((0, 0), name, font=font)
    tw = bbox[2] - bbox[0]
    draw.text(((W - tw) / 2, H * 0.72), name, font=font, fill=(255, 255, 255))
    sub = "Business Travel"
    bbox2 = draw.textbbox((0, 0), sub, font=small)
    draw.text(((W - (bbox2[2] - bbox2[0])) / 2, H * 0.72 + 110), sub, font=small, fill=(230, 215, 185))

    img.save(os.path.join(OUT, f"dest_{slug}.jpg"), quality=88)
    print("saved", slug)


def main():
    os.makedirs(OUT, exist_ok=True)
    for slug, (top, bottom) in PALETTES.items():
        make_image(slug, NAMES[slug], top, bottom)


if __name__ == "__main__":
    main()
