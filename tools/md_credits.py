"""Mega Drive staff roll: the Japanese names romanized as MobyGames credits them.

The roll is 17 sprite groups (one per line, frame f of object type 0x42 -> group at the
long CREDITS[f]), spawned by 0x20380 with the (x, delay) pair X_PAIRS[16 - f]. Each line's
tiles are 8x16 columns, column-major, in one of three LZ streams loaded at fixed VRAM tiles.
Names are redrawn in Spleen 8x16 (proportional, white); the original Latin parts such as
(LMS music), (24) and Kengo Morita's face are kept, all lines are regrouped and re-centred."""
import struct
import font, gfx

CREDITS = 0x028e5c      # 17 longs: frame -> sprite group
X_PAIRS = 0x02033c      # 17 (x, delay) words, pair k is used by frame 16 - k
# (stream, first VRAM tile, first VRAM tile not free during the roll)
STREAMS = ((0x1069fe, 0x008, 0x0c0), (0x106efd, 0x100, 0x1ab), (0x107476, 0x540, 0x62c))
NAME_COLOUR = 15
# Group index (in ROM order) -> (English, original columns kept after it)
NAMES = {
    1: ('MOO Niitani', None),            # MOO仁井谷
    3: ('Jemini Hirono', None),          # じぇみに広野
    4: ('Yasutoshi S. Akiyama', None),   # 秋山泰俊S
    8: ('Tsuyoshi Matsushima', 9),       # 松島剛史 (LMS music): columns 9.. equal BA.M's 7..
    11: ('Fukusaburo Kido', None),       # 木戸福三郎
    12: ('Shimeharidzuru', None),        # 〆張鶴
    14: ('Kazuhiko Kitade', None),       # 北出和彦
    15: ('Kengo Morita', 8),             # 森田健吾 (24) + face
}
SHARED = {8: (9, 7)}    # group 8's columns 9.. reuse group 9's tiles from its column 7
MACRONS = {'ā': 'a', 'ō': 'o', 'ū': 'u'}   # Spleen has ASCII only


def _text(s):
    """16-row bitmap of s in Spleen 8x16, each glyph trimmed to its ink + 1 px, spaces 4 px"""
    f = font.font()
    cols = []
    for ch in s:
        if ch == ' ':
            cols += [[0] * 16] * 4
            continue
        base = MACRONS.get(ch, ch)
        rows = bytearray(f[ord(base)])
        if base != ch:                          # a macron 2 rows above the x-height
            rows[3] |= rows[7] | rows[8] | rows[9]
        ink = [c for c in range(8) if any(r >> (7 - c) & 1 for r in rows)]
        for c in range(ink[0], ink[-1] + 1):
            cols.append([NAME_COLOUR if rows[y] >> (7 - c) & 1 else 0 for y in range(16)])
        cols.append([0] * 16)
    return cols[:-1]


def _columns(tiles, first, n):
    return [bytes(tiles[(first + 2 * c) * 32:(first + 2 * c + 2) * 32]) for c in range(n)]


def _pack(pixel_cols):
    """pixel columns -> 8x16 tile columns (top tile then bottom tile, 64 bytes each)"""
    pixel_cols = pixel_cols + [[0] * 16] * (-len(pixel_cols) % 8)
    out = []
    for c in range(0, len(pixel_cols), 8):
        col = bytearray(64)
        for r in range(2):
            gfx.tile_put(col, r, [[pixel_cols[c + x][r * 8 + y] for x in range(8)] for y in range(8)])
        out.append(bytes(col))
    return out


def apply(prog, streams, at, end):
    frames = [struct.unpack_from('>I', prog, CREDITS + 4 * f)[0] for f in range(17)]
    groups = sorted(set(frames))
    assert len(groups) == 17
    stream_of, lines = [], []
    for g in groups:
        n = struct.unpack_from('>H', prog, g)[0]
        ents = [struct.unpack_from('>hBBHh', prog, g + 2 + 8 * k) for k in range(n)]
        first = ents[0][3] & 0x7ff
        ncols = sum((e[1] >> 2 & 3) + 1 for e in ents)
        s = max(k for k, (_, base, _) in enumerate(STREAMS) if base <= first)
        stream_of.append(s)
        lines.append((first - STREAMS[s][1], ncols, ents[0][2], ents[0][3] & 0xf800, ents[0][0]))
    orig = [bytes(streams.original(a)) for a, _, _ in STREAMS]

    # new columns per line: (own tile columns, shared columns as (group, from column, count))
    new_cols, widths = [], []
    for k, (first, ncols, _, _, _) in enumerate(lines):
        cols = _columns(orig[stream_of[k]], first, ncols)
        if k in NAMES:
            name, keep = NAMES[k]
            text = _pack(_text(name) + [[0] * 16] * 2)   # the kept columns bring their own gap
            if k in SHARED:
                new_cols.append((text, (SHARED[k][0], SHARED[k][1], ncols - keep)))
            else:
                new_cols.append((text + (cols[keep:] if keep else []), None))
        else:
            new_cols.append((cols, None))

    # lay the columns out stream by stream, tiles column-major from each stream's VRAM base
    start = {}
    for s, (addr, base, limit) in enumerate(STREAMS):
        data = bytearray()
        for k in range(17):
            if stream_of[k] == s:
                start[k] = base + len(data) // 32
                data += b''.join(new_cols[k][0])
        assert base + len(data) // 32 <= limit, 'staff roll stream %06x: %d tiles, no room' % (addr, len(data) // 32)
        tiles = streams.get(addr)
        tiles[:] = data

    # regroup every line (4-column sprites) and re-centre it on its original centre
    for k, g in enumerate(groups):
        _, ncols, link, attr, y = lines[k]
        own, shared = new_cols[k]
        pieces = [(start[k] + 2 * c, 1) for c in range(len(own))]
        if shared:
            sg, sc, n = shared
            pieces += [(start[sg] + 2 * (sc + c), 1) for c in range(n)]
        sprites, x = [], 0
        while pieces:
            run = 1
            while run < min(4, len(pieces)) and pieces[run][0] == pieces[0][0] + 2 * run:
                run += 1
            sprites.append((y, (run - 1) << 2 | 1, link, attr | pieces[0][0], x))
            pieces, x = pieces[run:], x + 8 * run
        data = struct.pack('>H', len(sprites)) + b''.join(struct.pack('>hBBHh', *sp) for sp in sprites)
        if at + len(data) > end:
            raise SystemExit('staff roll: no room')
        prog[at:at + len(data)] = data
        for f in range(17):
            if frames[f] == g:
                struct.pack_into('>I', prog, CREDITS + 4 * f, at)
                pair = X_PAIRS + 4 * (16 - f)
                old_x = struct.unpack_from('>h', prog, pair)[0]
                struct.pack_into('>h', prog, pair, old_x + (8 * ncols - x) // 2)
        at += len(data)
    return at
