"""Game Arts formats on the Saturn disc (EFFECT.DAT, PUYOSHOW.FLD).

- LZSS (SH-2 0x06051024): BE u32 compressed length, then Okumura LZSS: 4096-byte ring starting
  at 0xFEE, flag byte LSB first (1 = literal), reference b0 | (b1 & 0xF0) << 4, length (b1 & 15) + 3.
- Scene block: u16 colours, u16 ?, BE u32 offsets up to the first part: [0] RGB555 palette, [1] LZSS 4bpp tiles,
  [2..] VDP2 maps (some blocks also hold small tables there). Map: u16 w, u16 h (cells), BE u32 words: cell = W & 0xF07F7FFF repeated
  count + 1 times, count = (W >> 23 & 31) | (W >> 10 & 32) (blitter 0x06050B2C).
- Container (PUYOSHOW 149/151/153/155): u16 0, u16 header size, BE u32 block offsets
  (0 = right after the header). Blocks are scenes or sprite sets (palette offset 0x10).
- FLD: BE (offset, size) pairs; entries start on 2048-byte boundaries."""
import struct

SECTOR = 2048


def lzss_decompress(buf, off=0):
    """(data, end) of the LZSS stream at off"""
    n = struct.unpack_from('>I', buf, off)[0]
    p, end = off + 4, off + 4 + n
    ring, r, flags, out = bytearray(4096), 0xFEE, 0, bytearray()
    while p < end:
        flags >>= 1
        if not flags & 0x100:
            flags = buf[p] | 0xFF00
            p += 1
            if p >= end:
                break
        if flags & 1:
            c = buf[p]
            p += 1
            out.append(c)
            ring[r] = c
            r = (r + 1) & 0xFFF
        else:
            s = buf[p] | (buf[p + 1] & 0xF0) << 4
            for k in range((buf[p + 1] & 15) + 3):
                c = ring[(s + k) & 0xFFF]
                out.append(c)
                ring[r] = c
                r = (r + 1) & 0xFFF
            p += 2
    return bytes(out), end


def lzss_compress(data):
    """LZSS stream (with its length word) decoding to data; greedy longest match in a 4 KB window"""
    out, flags, items = bytearray(), 0, bytearray()
    pos, nbit = 0, 0
    heads = {}                                  # 3-byte prefix -> recent positions
    n = len(data)

    def flush():
        nonlocal flags, items, nbit
        out.append(flags)
        out.extend(items)
        flags, items, nbit = 0, bytearray(), 0

    while pos < n:
        best, bpos = 0, 0
        if pos + 3 <= n:
            for cand in reversed(heads.get(data[pos:pos + 3], ())):
                if pos - cand > 4078:           # ring slots still holding cand's bytes
                    break
                ln = 3
                while ln < 18 and pos + ln < n and data[cand + ln] == data[pos + ln]:
                    ln += 1
                if ln > best:
                    best, bpos = ln, cand
                    if ln == 18:
                        break
        if best >= 3:
            ring = (0xFEE + bpos) & 0xFFF
            items += bytes((ring & 0xFF, (ring >> 4) & 0xF0 | (best - 3)))
            step = best
        else:
            flags |= 1 << nbit
            items.append(data[pos])
            step = 1
        for k in range(pos, min(pos + step, n - 2)):
            heads.setdefault(data[k:k + 3], []).append(k)
        pos += step
        nbit += 1
        if nbit == 8:
            flush()
    if nbit:
        flush()
    return struct.pack('>I', len(out)) + bytes(out)


def lzss_compress_small(data):
    """lzss_compress, a few percent smaller and much slower: the longest match at every position, then the
    cheapest mix of literals (9 bits) and matches (17 bits); for data that must fit a slot"""
    n = len(data)
    heads = {}                                  # 3-byte prefix -> positions
    longest = [(0, 0)] * n                      # (length, position) of the longest match at each position
    for pos in range(n - 2):
        key = data[pos:pos + 3]
        best, bpos = 0, 0
        for cand in reversed(heads.get(key, ())[-512:]):    # the 512 latest: seconds, not minutes, per sprite set
            if pos - cand > 4078:               # ring slots still holding cand's bytes
                break
            ln = 3
            while ln < 18 and pos + ln < n and data[cand + ln] == data[pos + ln]:
                ln += 1
            if ln > best:
                best, bpos = ln, cand
                if ln == 18:
                    break
        longest[pos] = (best, bpos)
        heads.setdefault(key, []).append(pos)
    cost, step = [0] * (n + 1), [1] * n         # bits from each position to the end, and the step taken
    for pos in range(n - 1, -1, -1):
        cost[pos] = 9 + cost[pos + 1]
        for ln in range(3, longest[pos][0] + 1):    # a shorter match at the same place is valid too
            if 17 + cost[pos + ln] < cost[pos]:
                cost[pos], step[pos] = 17 + cost[pos + ln], ln
    out, flags, items, nbit, pos = bytearray(), 0, bytearray(), 0, 0
    while pos < n:
        if step[pos] > 1:
            ring = (0xFEE + longest[pos][1]) & 0xFFF
            items += bytes((ring & 0xFF, (ring >> 4) & 0xF0 | (step[pos] - 3)))
        else:
            flags |= 1 << nbit
            items.append(data[pos])
        pos += step[pos]
        nbit += 1
        if nbit == 8 or pos >= n:
            out.append(flags)
            out.extend(items)
            flags, items, nbit = 0, bytearray(), 0
    return struct.pack('>I', len(out)) + bytes(out)


def map_decode(buf, off):
    """(w, h, cells, end)"""
    w, h = struct.unpack_from('>2H', buf, off)
    p, cells = off + 4, []
    while len(cells) < w * h:
        word = struct.unpack_from('>I', buf, p)[0]
        p += 4
        cells += [word & 0xF07F7FFF] * (((word >> 23 & 31) | (word >> 10 & 32)) + 1)
    assert len(cells) == w * h
    return w, h, cells, p


def map_encode(w, h, cells):
    assert len(cells) == w * h and all(c & ~0xF07F7FFF == 0 for c in cells)
    out = bytearray(struct.pack('>2H', w, h))
    k = 0
    while k < len(cells):
        run = 1
        while run < 64 and k + run < len(cells) and cells[k + run] == cells[k]:
            run += 1
        out += struct.pack('>I', cells[k] | ((run - 1) & 31) << 23 | ((run - 1) >> 5) << 15)
        k += run
    return bytes(out)


def scene_parse(b):
    """{'head': first 4 bytes, 'parts': [raw bytes per header offset], 'order'}. Part 0 is the
    RGB555 palette (it follows the offset table, which sets the part count), part 1 the LZSS
    tiles, the rest maps or small tables (kept raw unless edited)."""
    n = (struct.unpack_from('>I', b, 4)[0] - 4) // 4
    offs = struct.unpack_from('>%dI' % n, b, 4)
    ends = sorted(offs) + [len(b)]
    return {'head': bytes(b[:4]), 'parts': [bytes(b[o:ends[ends.index(o) + 1]]) for o in offs],
            'order': sorted(range(n), key=offs.__getitem__)}     # parts keep their disc order


def scene_pack(s):
    parts = s['parts']
    out = bytearray(s['head'] + bytes(4 * len(parts)))
    for k in s['order']:
        out += bytes(-len(out) % 4)
        struct.pack_into('>I', out, 4 + 4 * k, len(out))
        out += parts[k]
    return bytes(out)


def container_parse(e):
    """(head: header plus any bytes before the first block, [block bytes] in header order,
    header indices in disc order); offset 0 means right after the header"""
    hsz = struct.unpack_from('>H', e, 2)[0]
    starts = [o or hsz for o in struct.unpack_from('>%dI' % ((hsz - 4) // 4), e, 4)]
    ends = sorted(starts) + [len(e)]
    blocks = [e[s:ends[ends.index(s) + 1]] for s in starts]
    return e[:min(starts)], blocks, sorted(range(len(starts)), key=starts.__getitem__)


def container_pack(head, blocks, order):
    hsz = struct.unpack_from('>H', head, 2)[0]
    out = bytearray(head)
    for k in order:
        out += bytes(-len(out) % 4)
        struct.pack_into('>I', out, 4 + 4 * k, 0 if len(out) == hsz else len(out))
        out += blocks[k]
    return bytes(out)


def fld_parse(d):
    ents = []
    for i in range(len(d) // 8):
        off, sz = struct.unpack_from('>II', d, i * 8)
        if sz == 0 or off + sz > len(d):
            break
        ents.append(d[off:off + sz])
    return ents


def fld_pack(ents, index_size):
    pad = lambda n: bytes([0xff]) * n
    out = bytearray(pad(index_size))
    for k, e in enumerate(ents):
        out += pad(-len(out) % SECTOR)
        struct.pack_into('>II', out, 8 * k, len(out), len(e))
        out += e
    return bytes(out + pad(-len(out) % SECTOR))


def sprites_parse(b):
    """VDP1 sprite set (u16 colours, u16 n, u32 palette/table/LZSS offsets; table = n x
    (u16 index, u32 colour bank, u16 w, u16 h, u16 address in 8-byte units), 4bpp linear):
    (table [(bank, w, h, addr)], pixels bytearray)"""
    n = struct.unpack_from('>H', b, 2)[0]
    _, table, data = struct.unpack_from('>3I', b, 4)
    ents = [struct.unpack_from('>HIHHH', b, table + 12 * k)[1:] for k in range(n)]
    return ents, bytearray(lzss_decompress(b, data)[0])


def sprites_pack(b, pixels, small=False):
    """b with its LZSS sprite pixels replaced (small: lzss_compress_small)"""
    data = struct.unpack_from('>I', b, 12)[0]
    end = lzss_decompress(b, data)[1]
    return bytes(b[:data]) + (lzss_compress_small if small else lzss_compress)(bytes(pixels)) + bytes(b[end:])


def sprites_palette(b):
    """the sprite set's colours as (r, g, b), 0..31 each"""
    ncol = struct.unpack_from('>H', b, 0)[0]
    pal = struct.unpack_from('>I', b, 4)[0]
    return [(v & 31, v >> 5 & 31, v >> 10 & 31) for v in struct.unpack_from('>%dH' % ncol, b, pal)]


def sprites_add(b, pixels, bank, w, h, new_pixels):
    """(b with a new last sprite of colour bank `bank`, its frame index); pixels as for sprites_resize"""
    ncol, n, pal, table, data = struct.unpack_from('>HHIII', b, 0)
    assert pal < table < data == table + 12 * n, 'header, palette, table, pixels expected in that order'
    b = bytearray(b)
    b[data:data] = struct.pack('>HIHHH', n, bank, w, h, 0)
    struct.pack_into('>H', b, 2, n + 1)
    struct.pack_into('>I', b, 12, data + 12)
    return sprites_resize(bytes(b), pixels, n, w, h, new_pixels), n


def sprites_resize(b, pixels, k, w, h, new_pixels):
    """give sprite k a new size, its 4bpp pixels appended at the end of the set's pixel data"""
    table = struct.unpack_from('>I', b, 8)[0]
    b = bytearray(b)
    pixels += bytes(-len(pixels) % 8)           # addresses count 8-byte units
    addr = len(pixels) // 8
    assert addr < 0x10000, 'sprite pixel data past the 16-bit address range'
    pixels += new_pixels + bytes(-len(new_pixels) % 8)
    struct.pack_into('>HHH', b, table + 12 * k + 6, w, h, addr)
    return bytes(b)
