#!/usr/bin/env python3
"""text_sheet.py puyopuy2e.zip OUT.png

Draws every English page from the built ROM set, the way the game lays it out: the 58
pages of the 33 character profiles (32 x 3 box) and the 15 tutorial pages (18 x 7 box),
with the font of the ROM. It follows the pointer each original page now starts with, so
it shows what the game will draw (for the README; standard library only)."""
import os, struct, sys, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, '..', 'text'))
import png, text, script_en

PALETTE = [(0, 0, 0), (40, 40, 72), (231, 231, 231), (120, 120, 160)] + [(0, 0, 0)] * 12


def program(zip_path):
    z = zipfile.ZipFile(zip_path)
    even, odd = z.read('pp2e-17241.ic32'), z.read('pp2e-17240.ic31')
    prog = bytearray(len(even) * 2)
    prog[0::2], prog[1::2] = even, odd
    return bytes(prog)


def page_cells(prog, orig, columns, first, step):
    """{(row, column): code} of the page that the original page at orig points to"""
    w = lambda a: prog[a] << 8 | prog[a + 1]
    assert w(orig) == 0xfffe
    a = struct.unpack('>I', prog[orig + 2:orig + 6])[0]
    cells, row, col = {}, 0, 0
    while True:
        v = w(a)
        if v == 0xffff:
            return cells
        if v == 0xff08:
            row, col = (w(a + 2) - first) // step, 0
            a += 4
        elif v == 0xff1c:
            a += 6                          # TURN DIRECTION: the default text goes on
        elif v >= 0xff00:
            a += 4
        else:
            if v:
                if col >= columns:
                    raise SystemExit('page at %x: line too long' % orig)
                cells[(row, col)] = v
            col += 1
            a += 2


def draw(prog, img, x0, y0, cells, columns, rows):
    for y in range(rows * 16 + 8):
        for x in range(columns * 8 + 8):
            edge = y in (0, rows * 16 + 7) or x in (0, columns * 8 + 7)
            img[y0 + y][x0 + x] = 3 if edge else 1
    for (r, c), code in cells.items():
        if r >= rows:
            raise SystemExit('page: too many lines')
        glyph = prog[text.FONT + 16 * code:text.FONT + 16 * code + 16]
        for y in range(16):
            for x in range(8):
                if glyph[y] >> (7 - x) & 1:
                    img[y0 + 4 + 16 * r + y][x0 + 4 + 8 * c + x] = 2


def main():
    prog = program(sys.argv[1])
    profiles = [(a, k) for a, k, _ in script_en.TEXT if k != 'tut']
    tutorials = [a for a, k, _ in script_en.TEXT if k == 'tut']
    pw, ph = 32 * 8 + 8 + 8, 3 * 16 + 8 + 8
    tw, th = 18 * 8 + 8 + 8, 7 * 16 + 8 + 8
    cols = 4
    prow = (len(profiles) + cols - 1) // cols
    trow = (len(tutorials) + 5) // 6
    width = max(cols * pw, 6 * tw)
    img = [[0] * width for _ in range(prow * ph + 8 + trow * th)]
    for k, (a, kind) in enumerate(profiles):
        cells = page_cells(prog, a, 32, 0, text.PROFILE_ROWS[0])
        draw(prog, img, (k % cols) * pw, (k // cols) * ph, cells, 32, 3)
    top = prow * ph + 8
    for k, a in enumerate(tutorials):
        cells = page_cells(prog, a, 18, text.TUT_FIRST, text.TUT_STEP)
        draw(prog, img, (k % 6) * tw, top + (k // 6) * th, cells, 18, 7)
    png.write(sys.argv[2], img, PALETTE)
    print('%d profile pages, %d tutorial pages' % (len(profiles), len(tutorials)))


if __name__ == '__main__':
    main()
