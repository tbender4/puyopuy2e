"""The title logo: ぷよぷよ通 becomes "Puyo Puyo" (the big gold 2 behind it stays).

The logo's letters are sprites, in groups described by two tables (TABLES; one with the
priority bit, one without, for the title's two phases): a group is a count, then per
sprite (y, size << 8 | 8 or 4, tile attributes, x). The groups: ぷ, よ (drawn twice, for
both ぷよ), the three handakuten circles, 通 (8 sprites) and its three sparkles. Their
tiles are stream TILES (VRAM tile 0x4e0 on).

ぷ becomes "Pu" and よ "yo" (assets/gfx/logo_puyo.png, 112 x 48: the logo of
assets/puyopuyo_logo.jpg in the title's palette): each a 56 x 48 block of four sprites,
84 tiles from 0x4e0. The three handakuten circles (one 3x3 sprite each, frames of a
bouncing puyo the game swaps as it animates them) keep their original tiles, copied after
the letters, and now bounce over the u of each "Pu"; 通 and its sparkles point to empty
tiles.""" 
import os, struct
import gfx, png

TABLES = (0x2a802, 0x2aa3e)
TILES = 0xb7511
FIRST = 0x4e0
GROUPS = 9                      # ぷ, よ, 3 circles, 通, 3 sparkles
CIRCLES = (2, 3, 4)             # their groups
CIRCLE_TILES = 0x45             # their 3 x 9 tiles in the original stream
CIRCLE_AT = 0x60                # and in the new one
CIRCLE_SHIFT = 30               # x added to the circles: over the u
EMPTY = 0xc0                    # 16 empty tiles from here (stream tile numbers; the stream has 0xd9)
# a 56 x 48 half: 4x3 + 3x3 tiles on top, the same below
LAYOUT = ((0, 0, 4, 3), (0, 32, 3, 3), (24, 0, 4, 3), (24, 32, 3, 3))
# the two "Puyo" are drawn at x 16 and 128 (the original ぷよ's places): moved right by
# SHIFT, the pair is centred on the screen (48-272)
SHIFT = 32
HERE = os.path.dirname(os.path.abspath(__file__))


def read_groups(prog, at):
    groups = []
    for _ in range(GROUPS):
        n = prog[at] << 8 | prog[at + 1]
        groups.append((at, n))
        at += 2 + 8 * n
    return groups


def apply(prog, streams):
    img = png.read(os.path.join(HERE, '..', 'assets', 'gfx', 'logo_puyo.png'))
    original = streams.original(TILES)
    tiles = streams.get(TILES)
    n_tiles = len(tiles) // gfx.TILE
    for t in range(n_tiles):
        gfx.tile_put(tiles, t, [[0] * 8 for _ in range(8)])
    # the tiles: per half, per sprite, column by column
    next_tile = 0
    starts = []
    for half in range(2):
        starts.append([])
        for (y, x, w, h) in LAYOUT:
            starts[half].append(next_tile)
            for c in range(w):
                for r in range(h):
                    x0, y0 = half * 56 + x + 8 * c, y + 8 * r
                    gfx.tile_put(tiles, next_tile, [row[x0:x0 + 8] for row in img[y0:y0 + 8]])
                    next_tile += 1
    assert next_tile <= CIRCLE_AT and CIRCLE_AT + 27 <= EMPTY
    tiles[CIRCLE_AT * gfx.TILE:(CIRCLE_AT + 27) * gfx.TILE] = \
        original[CIRCLE_TILES * gfx.TILE:(CIRCLE_TILES + 27) * gfx.TILE]
    for table in TABLES:
        groups = read_groups(prog, table)
        for g, (at, n) in enumerate(groups):
            if g < 2:
                assert n == 4
                for k, (y, x, w, h) in enumerate(LAYOUT):
                    e = at + 2 + 8 * k
                    attr = prog[e + 4] << 8 | prog[e + 5]
                    low = prog[e + 3]
                    size = (w - 1) << 2 | (h - 1)
                    prog[e:e + 8] = struct.pack('>HBBHH', y, size, low,
                                                (attr & 0xf800) | (FIRST + starts[g][k]), x + SHIFT)
            elif g in CIRCLES:
                e = at + 2 + 4
                attr = prog[e] << 8 | prog[e + 1]
                assert n == 1 and (attr & 0x7ff) - FIRST == CIRCLE_TILES + 9 * (g - CIRCLES[0])
                prog[e:e + 2] = struct.pack('>H', (attr & 0xf800) | (FIRST + CIRCLE_AT + 9 * (g - CIRCLES[0])))
                x = prog[e + 2] << 8 | prog[e + 3]
                prog[e + 2:e + 4] = struct.pack('>H', (x + CIRCLE_SHIFT) & 0xffff)
            else:
                for k in range(n):
                    e = at + 2 + 8 * k + 4
                    attr = prog[e] << 8 | prog[e + 1]
                    prog[e:e + 2] = struct.pack('>H', (attr & 0xf800) | (FIRST + EMPTY))
