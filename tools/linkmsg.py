"""The join-in and link messages (乱入されたよ, もう一台に乱入するの？, はい / いいえ, 回線が
切れました ...): byte strings drawn by the routine at 0x15be, one 16x16 glyph per byte
(tile 4 x glyph, column by column: top left, bottom left, top right, bottom right).

A string is a VRAM offset word (from the plane at 0xc000), then glyph bytes ("80 hh" sets
the high byte of the tile words, 0x80 at the start of each line), then 0xfe (another line
follows, word aligned) or 0xff (the end); an offset word 0xffff is followed by a long
pointer to where the string goes on. A glyph byte g < 0x80 is drawn as the tiles from
high << 8 | (4g & 0xff) (64 glyphs per high byte); 0x81-0xfd draw a blank cell.

The glyphs (stream 0x8cb5e, 32 glyphs at tile 0x400, high byte 0x84) are redrawn from the
English lines (line_glyphs), as many as the 64 of high byte 0x84 (tiles 0x480-0x4ff hold only
play tiles left over on that screen, as 0x400-0x47f did), and each original string is
pointed at an English one written in free space."""
import struct
import font, labels

GLYPHS = 0x8cb5e
HIGH = 0x84

NEW = "NEW CHALLENGER!"
CANT = "CAN'T JOIN THE OTHER ONE"
# original string: [(row, text)]; each line starts at column 4 as the originals do, but
# NO / YES, which stay at column 20 beside the two cabinets
COLUMN = {"NO": 20, "YES": 20}
STRINGS = {
    0x19dc8: [(4, NEW)],
    0x19dd4: [(4, NEW), (10, CANT)],
    0x19de0: [(10, CANT)],
    0x19df6: [(6, "JOINING IN!")],
    0x19e00: [(10, "JOIN THE OTHER ONE?")],
    0x19e14: [(10, "JOIN THE OTHER ONE TOO?"), (4, NEW)],
    0x19e30: [(14, "NO"), (18, "YES")],       # written in place: see apply
    0x1b274: [(6, "LINK DOWN!"), (10, "CALL THE STAFF")],
}
# The choice under the cursor is drawn again in red (0x19cf8) from the original records,
# 0x19e30 for NO and 0x19e38 for YES: offset word, 80 84 skipped, glyphs to fe/ff. NO / YES
# are written there in place, each 8 bytes (NO padded with 80 84 before fe or a 0 after it,
# as the records are word aligned), so that NO's record ends where YES's starts
IN_PLACE = {0x19e30: 0x19e38}


def offset(row, text):
    """VRAM offset of a line (plane 64 cells wide)"""
    return row * 0x80 + COLUMN.get(text, 4) * 2


def line_glyphs(text, glyphs):
    """16x16 glyphs covering text in f outlined in 1, each letter 1 px into its cell so its
    left outline is in its own cell and its right one in the next (a line ending on a letter
    gets one more cell); two outlined letters do not fit one glyph on their own"""
    cells = len(text) + (text[-1:] != ' ')
    w = 8 * (cells + cells % 2)
    img = [[0] * w for _ in range(16)]
    for k, ch in enumerate(text):
        for y, row in enumerate(glyphs[ord(ch)]):
            for x in range(8):
                if row >> (7 - x) & 1:
                    img[y][8 * k + 1 + x] = 0xf
    img = labels.ring(img, 1, {0xf})
    return [[r[i:i + 16] for r in img] for i in range(0, w, 16)]


def key(img):
    """a glyph as a dict key; None when it is empty (drawn as the blank byte 0x81)"""
    return tuple(map(tuple, img)) if any(map(any, img)) else None


def encode(text, index, glyphs, high):
    """glyph bytes of text after a line's 80 high; index: key -> (high byte, glyph), with
    80 hh where the high byte changes"""
    out = bytearray()
    for img in line_glyphs(text, glyphs):
        k = key(img)
        if k is None:
            out.append(0x81)
            continue
        h, g = index[k]
        if h != high:
            out += bytes([0x80, h])
            high = h
        out.append(g)
    return bytes(out)


def apply(prog, streams, at, end):
    """redraws the glyphs, writes the strings from at (below end); returns where they end"""
    glyphs = font.font()
    imgs = {}
    for lines in STRINGS.values():
        for _, text in lines:
            for img in line_glyphs(text, glyphs):
                if k := key(img):
                    imgs.setdefault(k, img)
    if len(imgs) > 64:
        raise SystemExit('linkmsg: %d glyphs, there are 64' % len(imgs))
    index = {k: (HIGH, g) for g, k in enumerate(imgs)}
    tiles = streams.get(GLYPHS)
    tiles += bytes(max(0, 4 * len(imgs) * 32 - len(tiles)))
    for g, img in enumerate(imgs.values()):
        labels.put_tiles(tiles, img, labels.sprite_order(4 * g, 2, 2, 1))
    enc = lambda text: encode(text, index, glyphs, HIGH)
    for orig, lines in STRINGS.items():
        data = bytearray()
        for k, (row, text) in enumerate(lines):
            if len(data) % 2:
                data.append(0)
            data += struct.pack('>H', offset(row, text)) + bytes([0x80, HIGH])
            data += enc(text)
            data.append(0xff if k == len(lines) - 1 else 0xfe)
        if orig in IN_PLACE:
            (row0, text0), (row1, text1) = lines
            first = struct.pack('>H', offset(row0, text0)) + bytes([0x80, HIGH]) + enc(text0)
            first += bytes([0x80, HIGH]) * ((IN_PLACE[orig] - orig - len(first) - 1) // 2) + b'\xfe'
            first += b'\0' * (len(first) % 2)       # the next record is word aligned
            second = struct.pack('>H', offset(row1, text1)) + bytes([0x80, HIGH])
            second += enc(text1) + b'\xff'
            second += b'\0' * (len(second) % 2)
            if len(first) != IN_PLACE[orig] - orig or len(second) > 8:
                raise SystemExit('linkmsg: NO / YES do not fit their records')
            prog[orig:orig + 16] = (first + second).ljust(16, b'\0')
            continue
        if len(data) % 2:
            data.append(0)
        if at + len(data) > end:
            raise SystemExit('linkmsg: no room')
        prog[at:at + len(data)] = data
        prog[orig:orig + 6] = struct.pack('>HI', 0xffff, at)
        at += len(data)
    return at
