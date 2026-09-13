"""
Генератор абстрактных SVG-заглушек для афиши.

14 сюжетов, каждый в изумрудной палитре сайта:
  • волны, орбиты, диагонали, градиентные пятна;
  • столбцы, треугольники, спирали, шум;
  • полуокружности, кривые, круги, штриховка, квадраты.

Запуск:
    python generate_placeholders.py
"""
import os
import random
import math

OUTPUT_DIR = os.path.join('static', 'images', 'placeholders')

# Палитра сайта
BG_DARK = '#04201c'
BG_MED = '#064e46'
BG_LIGHT = '#0b5e57'
ACCENT = '#5eead4'
ACCENT_LIGHT = '#a7f3d0'
ACCENT_SOFT = '#99f6e4'
WHITE = '#ffffff'


# ======================================================================
#  Утилиты
# ======================================================================

def svg_open():
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 500" '
        'preserveAspectRatio="xMidYMid slice">'
    )


def defs(idx, with_radial=True):
    """Градиенты и фильтры. Один набор на файл, уникальный id."""
    parts = [
        f'<linearGradient id="bg-{idx}" x1="0" y1="0" x2="0.6" y2="1">',
        f'<stop offset="0%" stop-color="{BG_DARK}"/>',
        f'<stop offset="55%" stop-color="{BG_MED}"/>',
        f'<stop offset="100%" stop-color="{BG_LIGHT}"/>',
        '</linearGradient>',
    ]
    if with_radial:
        parts += [
            f'<radialGradient id="glow-{idx}" cx="30%" cy="80%" r="70%">',
            f'<stop offset="0%" stop-color="{ACCENT}" stop-opacity="0.35"/>',
            f'<stop offset="100%" stop-color="{ACCENT}" stop-opacity="0"/>',
            '</radialGradient>',
        ]
    return '<defs>' + ''.join(parts) + '</defs>'


def bg(idx, with_radial=True):
    layers = [f'<rect width="800" height="500" fill="url(#bg-{idx})"/>']
    if with_radial:
        layers.append(f'<rect width="800" height="500" fill="url(#glow-{idx})"/>')
    return ''.join(layers)


# ======================================================================
#  Сюжеты
# ======================================================================

def scene_waves(rnd):
    """Наслаивающиеся волны."""
    parts = []
    for i in range(8):
        y_base = 380 - i * 25
        amp = 20 + rnd.randint(0, 25)
        freq = 0.008 + rnd.random() * 0.008
        phase = rnd.random() * 6
        opacity = max(0.05, 0.55 - i * 0.06)

        d = f'M-20 {y_base} '
        for x in range(-20, 821, 20):
            y = y_base + math.sin(x * freq + phase) * amp
            d += f'L{x} {y:.1f} '
        d += f'L820 520 L-20 520 Z'

        color = ACCENT if i % 2 == 0 else ACCENT_LIGHT
        parts.append(f'<path d="{d}" fill="{color}" opacity="{opacity:.2f}"/>')
    return ''.join(parts)


def scene_dot_grid(rnd):
    """Сетка точек с радиальной прозрачностью."""
    parts = []
    cx, cy = 400, 250
    for y in range(20, 481, 24):
        for x in range(20, 781, 24):
            dist = math.hypot(x - cx, y - cy) / 400
            opacity = max(0.05, 0.9 - dist)
            r = 1.2 + rnd.random() * 0.8
            parts.append(
                f'<circle cx="{x}" cy="{y}" r="{r:.1f}" '
                f'fill="{ACCENT_LIGHT}" opacity="{opacity:.2f}"/>'
            )
    return ''.join(parts)


def scene_orbits(rnd):
    """Концентрические окружности + орбитальные дуги."""
    parts = []
    cx = 400 + rnd.randint(-80, 80)
    cy = 250 + rnd.randint(-60, 60)

    for i in range(9):
        r = 40 + i * 40
        op = max(0.06, 0.7 - i * 0.06)
        parts.append(
            f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" '
            f'stroke="{ACCENT}" stroke-width="1" opacity="{op:.2f}"/>'
        )

    for _ in range(5):
        angle = rnd.random() * math.tau
        r = 100 + rnd.randint(0, 200)
        parts.append(
            f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" '
            f'stroke="{ACCENT_LIGHT}" stroke-width="2" opacity="0.5" '
            f'stroke-dasharray="{rnd.randint(10, 40)} {rnd.randint(20, 80)}" '
            f'transform="rotate({math.degrees(angle):.0f} {cx} {cy})"/>'
        )

    parts.append(f'<circle cx="{cx}" cy="{cy}" r="18" fill="{ACCENT}" opacity="0.9"/>')
    parts.append(f'<circle cx="{cx}" cy="{cy}" r="40" fill="{ACCENT}" opacity="0.15"/>')
    return ''.join(parts)


def scene_diagonals(rnd):
    """Наклонные полосы разной толщины."""
    parts = []
    for _ in range(30):
        x = rnd.randint(-200, 900)
        w = rnd.choice([1, 2, 4, 6, 10])
        op = rnd.uniform(0.1, 0.7)
        color = rnd.choice([ACCENT, ACCENT_LIGHT, WHITE])
        parts.append(
            f'<line x1="{x}" y1="-50" x2="{x - 150}" y2="550" '
            f'stroke="{color}" stroke-width="{w}" opacity="{op:.2f}"/>'
        )
    return ''.join(parts)


def scene_blobs(rnd):
    """Крупные размытые пятна."""
    parts = []
    for _ in range(8):
        cx = rnd.randint(0, 800)
        cy = rnd.randint(0, 500)
        r = rnd.randint(80, 220)
        op = rnd.uniform(0.06, 0.22)
        color = rnd.choice([ACCENT, ACCENT_LIGHT, ACCENT_SOFT, WHITE])
        parts.append(
            f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{color}" opacity="{op:.2f}"/>'
        )
    return ''.join(parts)


def scene_columns(rnd):
    """Вертикальные столбцы разной высоты."""
    parts = []
    x = 0
    while x < 800:
        w = rnd.randint(15, 60)
        h = rnd.randint(80, 400)
        y = 500 - h
        op = rnd.uniform(0.1, 0.35)
        color = rnd.choice([ACCENT, ACCENT_LIGHT])
        parts.append(
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" '
            f'fill="{color}" opacity="{op:.2f}"/>'
        )
        x += w + rnd.randint(4, 20)
    return ''.join(parts)


def scene_triangles(rnd):
    """Геометрические треугольники low-poly."""
    parts = []
    for _ in range(20):
        x = rnd.randint(0, 800)
        y = rnd.randint(0, 500)
        size = rnd.randint(50, 200)
        op = rnd.uniform(0.08, 0.3)
        color = rnd.choice([ACCENT, ACCENT_LIGHT, WHITE])
        rot = rnd.randint(0, 360)
        parts.append(
            f'<polygon points="{x},{y} {x + size},{y + rnd.randint(-30, 30)} '
            f'{x + rnd.randint(-30, 30)},{y + size}" '
            f'fill="{color}" opacity="{op:.2f}" '
            f'transform="rotate({rot} {x} {y})"/>'
        )
    return ''.join(parts)


def scene_spiral(rnd):
    """Спиральные линии."""
    parts = []
    cx = 400 + rnd.randint(-100, 100)
    cy = 250 + rnd.randint(-50, 50)

    for spiral_i in range(3):
        d = f'M{cx} {cy} '
        turns = 4 + rnd.randint(0, 3)
        points = 200
        for i in range(points):
            t = i / points * turns * math.tau
            r = t * (18 + rnd.randint(0, 8))
            x = cx + math.cos(t) * r
            y = cy + math.sin(t) * r
            d += f'L{x:.1f} {y:.1f} '
        op = 0.5 - spiral_i * 0.12
        color = [ACCENT, ACCENT_LIGHT, WHITE][spiral_i]
        parts.append(
            f'<path d="{d}" fill="none" stroke="{color}" '
            f'stroke-width="1.5" opacity="{op:.2f}"/>'
        )
    return ''.join(parts)


def scene_noise(rnd):
    """Мелкая случайная сетка точек."""
    parts = []
    for _ in range(400):
        x = rnd.randint(0, 800)
        y = rnd.randint(0, 500)
        r = rnd.choice([0.5, 1, 1.5, 2])
        op = rnd.uniform(0.1, 0.8)
        color = rnd.choice([ACCENT, ACCENT_LIGHT, WHITE])
        parts.append(
            f'<circle cx="{x}" cy="{y}" r="{r}" fill="{color}" opacity="{op:.2f}"/>'
        )
    return ''.join(parts)


def scene_arcs(rnd):
    """Полуокружности и дуги."""
    parts = []
    for _ in range(14):
        cx = rnd.randint(0, 800)
        cy = rnd.randint(0, 500)
        r = rnd.randint(60, 220)
        start = rnd.randint(0, 360)
        end = start + rnd.randint(60, 240)
        op = rnd.uniform(0.15, 0.5)
        color = rnd.choice([ACCENT, ACCENT_LIGHT])
        parts.append(
            f'<path d="M{cx - r} {cy} A{r} {r} 0 0 1 {cx + r} {cy}" '
            f'fill="none" stroke="{color}" stroke-width="2" '
            f'opacity="{op:.2f}" '
            f'transform="rotate({start} {cx} {cy})"/>'
        )
        _ = end  # заглушка, используем start
    return ''.join(parts)


def scene_curves(rnd):
    """Плавные кривые Безье."""
    parts = []
    for _ in range(12):
        x1 = rnd.randint(0, 800)
        y1 = rnd.randint(0, 500)
        x2 = rnd.randint(0, 800)
        y2 = rnd.randint(0, 500)
        cx1 = rnd.randint(0, 800)
        cy1 = rnd.randint(0, 500)
        cx2 = rnd.randint(0, 800)
        cy2 = rnd.randint(0, 500)
        op = rnd.uniform(0.15, 0.6)
        color = rnd.choice([ACCENT, ACCENT_LIGHT, WHITE])
        w = rnd.choice([0.8, 1, 1.5, 2])
        parts.append(
            f'<path d="M{x1} {y1} C{cx1} {cy1} {cx2} {cy2} {x2} {y2}" '
            f'fill="none" stroke="{color}" stroke-width="{w}" '
            f'opacity="{op:.2f}"/>'
        )
    return ''.join(parts)


def scene_big_circles(rnd):
    """Крупные пересекающиеся окружности."""
    parts = []
    for _ in range(6):
        cx = rnd.randint(100, 700)
        cy = rnd.randint(100, 400)
        r = rnd.randint(100, 250)
        op = rnd.uniform(0.1, 0.25)
        color = rnd.choice([ACCENT, ACCENT_LIGHT])
        parts.append(
            f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{color}" opacity="{op:.2f}"/>'
        )
    for _ in range(6):
        cx = rnd.randint(100, 700)
        cy = rnd.randint(100, 400)
        r = rnd.randint(100, 250)
        op = rnd.uniform(0.2, 0.5)
        color = rnd.choice([ACCENT, ACCENT_LIGHT, WHITE])
        parts.append(
            f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" '
            f'stroke="{color}" stroke-width="1" opacity="{op:.2f}"/>'
        )
    return ''.join(parts)


def scene_hatching(rnd):
    """Параллельные короткие штрихи."""
    parts = []
    angle = rnd.randint(0, 180)
    for _ in range(300):
        x = rnd.randint(-50, 850)
        y = rnd.randint(-50, 550)
        length = rnd.randint(6, 30)
        op = rnd.uniform(0.1, 0.7)
        color = rnd.choice([ACCENT, ACCENT_LIGHT, WHITE])
        w = rnd.choice([0.5, 1, 1.5])
        parts.append(
            f'<line x1="{x}" y1="{y}" x2="{x + length}" y2="{y + length}" '
            f'stroke="{color}" stroke-width="{w}" opacity="{op:.2f}"/>'
        )
    return f'<g transform="rotate({angle} 400 250)">' + ''.join(parts) + '</g>'


def scene_rotated_squares(rnd):
    """Повёрнутые квадраты."""
    parts = []
    for _ in range(30):
        x = rnd.randint(-100, 900)
        y = rnd.randint(-100, 600)
        size = rnd.randint(20, 120)
        rot = rnd.randint(0, 360)
        op = rnd.uniform(0.05, 0.25)
        color = rnd.choice([ACCENT, ACCENT_LIGHT, WHITE])
        parts.append(
            f'<rect x="{x}" y="{y}" width="{size}" height="{size}" '
            f'fill="{color}" opacity="{op:.2f}" '
            f'transform="rotate({rot} {x + size/2} {y + size/2})"/>'
        )
    return ''.join(parts)


# ======================================================================
#  Сборка
# ======================================================================

SCENES = [
    scene_waves,           # 1
    scene_dot_grid,        # 2
    scene_orbits,          # 3
    scene_diagonals,       # 4
    scene_blobs,           # 5
    scene_columns,         # 6
    scene_triangles,       # 7
    scene_spiral,          # 8
    scene_noise,           # 9
    scene_arcs,            # 10
    scene_curves,          # 11
    scene_big_circles,     # 12
    scene_hatching,        # 13
    scene_rotated_squares, # 14
]


def make_svg(idx):
    rnd = random.Random(idx * 7919)
    scene_fn = SCENES[(idx - 1) % len(SCENES)]
    scene = scene_fn(rnd)

    return (
        svg_open()
        + defs(idx)
        + bg(idx)
        + scene
        + '</svg>'
    )


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    for i in range(1, 51):
        svg = make_svg(i)
        path = os.path.join(OUTPUT_DIR, f'placeholder-{i:02d}.svg')
        with open(path, 'w', encoding='utf-8') as f:
            f.write(svg)

    print(f'Создано 50 SVG в {OUTPUT_DIR}')


if __name__ == '__main__':
    main()