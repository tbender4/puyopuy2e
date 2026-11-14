#!/usr/bin/env python3
"""Draws the English graphics of assets/gfx (maintainers only: needs Pillow and the
Poppins Bold font, OFL; the PNGs are in the repository, building the ROM does not run
this). Each PNG is 8-bit palette: the indices are the game's colour numbers."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bigtext, png

OUT = os.path.join(HERE, '..', 'assets', 'gfx')
GREY = [(i * 17, i * 17, i * 17) for i in range(16)]

# name: (text, width, height, font size, tracking, vertical offset, fill, edge, outline)
# (sizes and offsets chosen so the text takes few enough 8x8 cells for the tiles there are)
BIG = {
    'players_wanted': ("PLAYERS WANTED!", 288, 48, 28, -1, 4, 9, None, 1),
}


# the title logo's palette (palette 0 of the title screen): colour number -> RGB
LOGO_PALETTE = {2: (99, 0, 0), 3: (132, 0, 0), 4: (165, 0, 0), 5: (198, 0, 0), 6: (231, 0, 0),
                8: (231, 0, 66), 9: (231, 33, 99), 10: (231, 66, 99), 11: (231, 99, 132),
                12: (231, 132, 198), 13: (231, 198, 198), 15: (231, 231, 231)}


def logo():
    """"Puyo" from assets/puyopuyo_logo.jpg (its first word), 112 x 48, in the logo's
    colours; the near-white background transparent"""
    from PIL import Image
    src = Image.open(os.path.join(HERE, '..', 'assets', 'puyopuyo_logo.jpg')).convert('RGB')
    word = src.crop((0, 0, 286, src.height))
    bbox = word.point(lambda v: 255 if v < 200 else 0).convert('L').getbbox()
    word = word.crop(bbox)
    h = 46
    w = round(word.width * h / word.height)
    word = word.resize((w, h), Image.LANCZOS)
    img = [[0] * 112 for _ in range(48)]
    x0, y0 = (112 - w) // 2, 1
    for y in range(h):
        for x in range(w):
            r, g, b = word.getpixel((x, y))
            if r > 215 and g > 200 and b > 200:
                continue
            best = min(LOGO_PALETTE, key=lambda k: sum((a - c) ** 2 for a, c in zip(LOGO_PALETTE[k], (r, g, b))))
            img[y0 + y][x0 + x] = best
    pal = [(0, 0, 0)] * 16
    for k, c in LOGO_PALETTE.items():
        pal[k] = c
    png.write(os.path.join(OUT, 'logo_puyo.png'), img, pal)
    print('logo_puyo')


def main():
    os.makedirs(OUT, exist_ok=True)
    for name, (text, w, h, size, track, dy, fill, edge, outline) in BIG.items():
        img = bigtext.indexed(bigtext.mask(text, w, h, size, track, dy=dy), fill, edge, outline)
        png.write(os.path.join(OUT, name + '.png'), img, GREY)
        print(name)
    logo()


if __name__ == '__main__':
    main()
