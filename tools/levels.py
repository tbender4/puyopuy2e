"""The heat of the curry by the level select's numbers (激甘, 甘口, 中辛, 辛口, 激辛): each label
is a list of sprites (stream 0x86339 at VRAM tile 0x380: 5 glyphs of 2x2 tiles, then the
plates); the lists' pointers are at 0x1e96c (levels 1 to 5).

In English the 20 glyph tiles become 10 pieces of 16x8 (3 letters of a 4x7 font, colour 7
with a dark (1) shadow, like the kana) and each level gets a new list of 2x1 sprites
spelling one or two lines: a list is a count word, then per sprite y, size and link
(0x0408: 2x1), attribute (palette 3, priority, tile) and x, relative to the label's
centre."""
import struct

STREAM = 0x86339
TABLE = 0x1e96c
ATTR = 0xe380

LABELS = (["EXTRA", "MILD"], ["MILD"], ["MEDIUM"], ["HOT"], ["EXTRA", "HOT"])

FONT = {   # 4x7
    'A': [".##.", "#..#", "#..#", "####", "#..#", "#..#", "#..#"],
    'D': ["###.", "#..#", "#..#", "#..#", "#..#", "#..#", "###."],
    'E': ["####", "#...", "#...", "###.", "#...", "#...", "####"],
    'H': ["#..#", "#..#", "#..#", "####", "#..#", "#..#", "#..#"],
    'I': [".###", "..#.", "..#.", "..#.", "..#.", "..#.", ".###"],
    'L': ["#...", "#...", "#...", "#...", "#...", "#...", "####"],
    'M': ["#..#", "####", "####", "#..#", "#..#", "#..#", "#..#"],
    'O': [".##.", "#..#", "#..#", "#..#", "#..#", "#..#", ".##."],
    'R': ["###.", "#..#", "#..#", "###.", "#.#.", "#..#", "#..#"],
    'T': ["####", ".#..", ".#..", ".#..", ".#..", ".#..", ".#.."],
    'U': ["#..#", "#..#", "#..#", "#..#", "#..#", "#..#", ".##."],
    'X': ["#..#", "#..#", ".##.", ".#..", ".##.", "#..#", "#..#"],
}
PITCH = 5          # 4 + the shadow
PER_PIECE = 3      # letters in 16 pixels


def piece_pixels(text, width=16):
    img = [[0] * width for _ in range(8)]
    for k, ch in enumerate(text):
        for y, row in enumerate(FONT[ch]):
            for x, c in enumerate(row):
                if c == '#':
                    xx = PITCH * k + x
                    img[y][xx] = 7
                    for dy, dx in ((1, 0), (0, 1), (1, 1)):
                        if y + dy < 8 and xx + dx < width and img[y + dy][xx + dx] == 0:
                            img[y + dy][xx + dx] = 1
    return img


def apply(prog, streams, at, end, table=TABLE):
    """redraws the glyph tiles, writes the lists from at (below end); returns where they end"""
    pieces = {}
    lists = []
    for lines in LABELS:
        sprites = []
        y0 = -4 * len(lines)
        for row, word in enumerate(lines):
            width = PITCH * len(word) - 1
            x0 = -(width // 2)
            for i in range(0, len(word), PER_PIECE):
                part = word[i:i + PER_PIECE]
                k = pieces.setdefault(part, len(pieces))
                sprites.append((y0 + 8 * row, 0x0408, ATTR + 2 * k, x0 + PITCH * i))
        lists.append(sprites)
    if len(pieces) > 10:
        raise SystemExit('levels: %d pieces, there are 10' % len(pieces))
    tiles = streams.get(STREAM)
    for part, k in pieces.items():
        img = piece_pixels(part)
        for half in (0, 1):
            data = bytearray(32)
            for y in range(8):
                for x in range(8):
                    data[y * 4 + x // 2] |= img[y][8 * half + x] << (4 if x % 2 == 0 else 0)
            t = 2 * k + half
            tiles[t * 32:(t + 1) * 32] = data
    for t in range(2 * len(pieces), 20):            # the glyphs left over: empty
        tiles[t * 32:(t + 1) * 32] = bytes(32)
    for level, sprites in enumerate(lists):
        data = struct.pack('>H', len(sprites))
        for y, size, attr, x in sprites:
            data += struct.pack('>hHHh', y, size, attr, x)
        if at + len(data) > end:
            raise SystemExit('levels: no room')
        prog[at:at + len(data)] = data
        prog[table + 4 * level:table + 4 * level + 4] = struct.pack('>I', at)
        at += len(data)
    return at
