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
