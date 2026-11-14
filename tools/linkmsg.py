"""The join-in and link messages (乱入されたよ, もう一台に乱入するの？, はい / いいえ, 回線が
切れました ...): byte strings drawn by the routine at 0x15be, one 16x16 glyph per byte
(tile 4 x glyph, column by column: top left, bottom left, top right, bottom right).

A string is a VRAM offset word (from the plane at 0xc000), then glyph bytes ("80 hh" sets
the high byte of the tile words, 0x80 at the start of each line), then 0xfe (another line
follows, word aligned) or 0xff (the end); an offset word 0xffff is followed by a long
pointer to where the string goes on.

The glyphs (stream 0x8cb5e, 32 glyphs, tiles 0x400 on with high byte 0x84) are redrawn as
pairs of 8x16 letters, white (f) outlined in 1, and each original string is pointed at an
English one written in free space."""
import struct
import font

GLYPHS = 0x8cb5e
HIGH = 0x84

NEW = "NEW CHALLENGER!"
CANT = "CAN'T JOIN THE OTHER ONE"
# original string: [(VRAM offset, text, half a glyph of space first)]
STRINGS = {
    0x19dc8: [(0x208, NEW, 0)],
    0x19dd4: [(0x208, NEW, 0), (0x508, CANT, 0)],
    0x19de0: [(0x508, CANT, 0)],
    0x19df6: [(0x308, "JOINING IN!", 0)],
    0x19e00: [(0x508, "JOIN THE OTHER ONE?", 0)],
    0x19e14: [(0x508, "JOIN THE OTHER ONE TOO?", 0), (0x208, NEW, 0)],
    0x19e30: [(0x728, "NO", 0), (0x928, "YES", 0)],      # (0x19e38, the second offset, is read
    0x1b274: [(0x308, "LINK DOWN!", 1), (0x508, "CALL THE STAFF", 0)],   # by the game: kept)
}


def pairs(text, shift):
    t = ' ' * shift + text
    if len(t) % 2:
        t += ' '
    return [t[i:i + 2] for i in range(0, len(t), 2)]


def glyph_pixels(pair, glyphs):
    """16 x 16: the two letters in f, outlined in 1"""
    img = [[0] * 16 for _ in range(16)]
    for k, ch in enumerate(pair):
        for y, row in enumerate(glyphs[ord(ch)]):
            for x in range(8):
                if row >> (7 - x) & 1:
                    img[y][8 * k + x] = 0xf
    out = [r[:] for r in img]
    for y in range(16):
        for x in range(16):
            if img[y][x] == 0 and any(0 <= y + dy < 16 and 0 <= x + dx < 16 and img[y + dy][x + dx]
                                      for dy in (-1, 0, 1) for dx in (-1, 0, 1)):
                out[y][x] = 1
    return out


def apply(prog, streams, at, end):
    """redraws the glyphs, writes the strings from at (below end); returns where they end"""
    glyphs = font.font()
    index = {}
    for lines in STRINGS.values():
        for _, text, shift in lines:
            for p in pairs(text, shift):
                index.setdefault(p, len(index))
    if len(index) > 32:
        raise SystemExit('linkmsg: %d glyphs, there are 32' % len(index))
    tiles = streams.get(GLYPHS)
    for p, g in index.items():
        img = glyph_pixels(p, glyphs)
        for q, (dx, dy) in enumerate(((0, 0), (0, 8), (8, 0), (8, 8))):
            data = bytearray(32)
            for y in range(8):
                for x in range(8):
                    v = img[dy + y][dx + x]
                    data[y * 4 + x // 2] |= v << (4 if x % 2 == 0 else 0)
            tiles[(4 * g + q) * 32:(4 * g + q + 1) * 32] = data
    for orig, lines in STRINGS.items():
        data = bytearray()
        for k, (offset, text, shift) in enumerate(lines):
            if len(data) % 2:
                data.append(0)
            data += struct.pack('>H', offset) + bytes([0x80, HIGH])
            data += bytes(index[p] for p in pairs(text, shift))
            data.append(0xff if k == len(lines) - 1 else 0xfe)
        if len(data) % 2:
            data.append(0)
        if at + len(data) > end:
            raise SystemExit('linkmsg: no room')
        prog[at:at + len(data)] = data
        prog[orig:orig + 6] = struct.pack('>HI', 0xffff, at)
        at += len(data)
    return at
