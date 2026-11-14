"""The attract tutorial's page titles (…のひみつ) in English.

The titles are 22 x 2 tiles of map at 0x8c0 in the tutorial screen's map stream
(MAP_STREAM, loaded to RAM 0xffc000), drawing kana tiles of the tutorial's tile stream
(TILE_STREAM, tiles from VRAM tile 0x100; the map holds tile - 0x100). The kana tiles
(0x38-0xb5 of the stream) are used by the titles only: they become the English capitals
(font/title_font.py), one tile above the other per letter, in colour 2."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'font'))
import title_font, gfx

TILE_STREAM = 0x91545
MAP_STREAM = 0x44ec8
MAP_AT = 0x8c0
FIRST_TILE, LAST_TILE = 0x38, 0xb5
BLANK = 0x1c
COLOUR = 2
WIDTH = 22

TITLES = ["BASIC CONTROLS", "GAME OVER", "CHAIN ATTACKS", "NUISANCE PUYO",
          "OFFSETTING", "ALL CLEAR", "JOINING IN", "QUICK TURN"]


def apply(streams):
    tiles = streams.get(TILE_STREAM)
    tmap = streams.get(MAP_STREAM)
    letters = sorted(set(''.join(TITLES)) - {' '})
    if FIRST_TILE + 2 * len(letters) > LAST_TILE + 1:
        raise SystemExit('too many title letters')
    slot = {}
    for k, ch in enumerate(letters):
        g = title_font.glyph(ch)
        top, bottom = FIRST_TILE + 2 * k, FIRST_TILE + 2 * k + 1
        gfx.tile_put(tiles, top, [[COLOUR * v for v in row] for row in g[:8]])
        gfx.tile_put(tiles, bottom, [[COLOUR * v for v in row] for row in g[8:]])
        slot[ch] = (top, bottom)
    for t in range(FIRST_TILE + 2 * len(letters), LAST_TILE + 1):
        gfx.tile_put(tiles, t, [[0] * 8 for _ in range(8)])
    for k, title in enumerate(TITLES):
        text = title.center(WIDTH)
        for row in range(2):
            for col, ch in enumerate(text):
                v = BLANK if ch == ' ' else slot[ch][row]
                i = MAP_AT + 2 * ((2 * k + row) * WIDTH + col)
                tmap[i:i + 2] = v.to_bytes(2, 'big')
