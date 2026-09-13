"""
Генератор favicon PNG и ICO из SVG.

Требует: pip install svglib reportlab pillow
Запуск:  python make_favicons.py

На входе:  static/images/favicon/favicon.svg
На выходе: static/images/favicon/favicon-16.png
           static/images/favicon/favicon-32.png
           static/images/favicon/apple-touch-icon.png
           static/images/favicon/icon-192.png
           static/images/favicon/icon-512.png
           static/images/favicon/favicon.ico
"""
import os

from reportlab.graphics import renderPM
from svglib.svglib import svg2rlg
from PIL import Image


SRC = 'static/images/favicon/favicon.svg'
OUT_DIR = 'static/images/favicon'

PNG_SIZES = [
    ('favicon-16.png', 16),
    ('favicon-32.png', 32),
    ('apple-touch-icon.png', 180),
    ('icon-192.png', 192),
    ('icon-512.png', 512),
]

ICO_SIZES = [16, 32, 48]


def render_png(svg_path, out_path, size):
    """
    Рендерит SVG в PNG заданного размера.
    svglib не умеет масштабировать напрямую — сначала читаем,
    потом масштабируем drawing, потом рендерим.
    """
    drawing = svg2rlg(svg_path)
    if drawing is None:
        raise RuntimeError(f'Не удалось прочитать SVG: {svg_path}')

    # Вычисляем коэффициент
    orig_w = drawing.width
    orig_h = drawing.height
    scale = size / max(orig_w, orig_h)

    drawing.width = orig_w * scale
    drawing.height = orig_h * scale
    drawing.scale(scale, scale)

    renderPM.drawToFile(drawing, out_path, fmt='PNG', bg=0xFFFFFF)


def main():
    if not os.path.exists(SRC):
        print(f'Не найден {SRC}')
        return

    print(f'Конвертирую {SRC}...\n')

    # PNG
    for filename, size in PNG_SIZES:
        out = os.path.join(OUT_DIR, filename)
        render_png(SRC, out, size)
        print(f'  ✓ {filename} ({size}x{size})')

    # ICO — собираем из PNG через PIL
    tmp_files = []
    for size in ICO_SIZES:
        tmp = os.path.join(OUT_DIR, f'_tmp_{size}.png')
        render_png(SRC, tmp, size)
        tmp_files.append(tmp)

    imgs = [Image.open(path) for path in tmp_files]
    ico_path = os.path.join(OUT_DIR, 'favicon.ico')
    imgs[0].save(
        ico_path,
        format='ICO',
        sizes=[(s, s) for s in ICO_SIZES],
    )
    print(f'  ✓ favicon.ico ({ICO_SIZES})')

    # Чистим
    for path in tmp_files:
        try:
            os.remove(path)
        except OSError:
            pass

    print('\nГотово.')


if __name__ == '__main__':
    main()