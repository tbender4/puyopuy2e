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


def main():
    os.makedirs(OUT, exist_ok=True)
    for name, (text, w, h, size, track, dy, fill, edge, outline) in BIG.items():
        img = bigtext.indexed(bigtext.mask(text, w, h, size, track, dy=dy), fill, edge, outline)
        png.write(os.path.join(OUT, name + '.png'), img, GREY)
        print(name)


if __name__ == '__main__':
    main()
