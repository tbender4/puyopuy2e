"""tools/saturn_arch.py - Bits Lab 10/6 LZSS, .BIN archive codec, and VDP1 sprite converters.

Stdlib-only helpers for Sega Saturn Puyo Puyo 2 (T-6601G) H_PUYODT.BIN and the 13 Bits Lab
.BIN graphics banks (DEMO_G00..06, GFILE08..09, FACE_G00..03)."""
import struct

LOW_WRAM_SLOT = 0x10000  # 64 KB fixed Low Work RAM slot per .BIN file
_RING_MASK = 0x3FF
_RING_INIT = 0x3BE
_MAX_MATCH = 66


def bits_decompress(buf, off=0):
    """Decompress one Bits Laboratory 10/6 LZSS stream at buf[off:]. Returns (bytes, end_off)."""
    if off + 4 > len(buf):
        raise ValueError(f'truncated LZSS header at {off}')
    usize = struct.unpack_from('<I', buf, off)[0]
    p = off + 4
    if usize == 0:
        return b'', p
    ring = bytearray(1024)
    r = _RING_INIT
    out = bytearray()
    n = len(buf)
    while len(out) < usize:
        if p >= n:
            raise ValueError(f'truncated LZSS stream at {p} (got {len(out)}/{usize} bytes)')
        flags = buf[p]
        p += 1
        for bit in range(8):
            if len(out) >= usize:
                break
            if flags & (1 << bit):
                if p >= n:
                    raise ValueError(f'truncated LZSS literal at {p}')
                c = buf[p]
                p += 1
                out.append(c)
                ring[r] = c
                r = (r + 1) & _RING_MASK
            else:
                if p + 1 >= n:
                    raise ValueError(f'truncated LZSS match at {p}')
                b1, b2 = buf[p], buf[p + 1]
                p += 2
                src = b1 | ((b2 & 0xC0) << 2)
                ln = (b2 & 0x3F) + 3
                for _ in range(ln):
                    if len(out) >= usize:
                        break
                    c = ring[src]
                    src = (src + 1) & _RING_MASK
                    out.append(c)
                    ring[r] = c
                    r = (r + 1) & _RING_MASK
    return bytes(out), p


def bits_compress(data):
    """Compress bytes-like input into Bits Laboratory 10/6 LZSS (4-byte LE uncompressed size + stream)."""
    data = bytes(data)
    n = len(data)
    out = bytearray(struct.pack('<I', n))
    if n == 0:
        return bytes(out)
    head = {}
    prev = [-1] * n
    i = 0
    while i < n:
        flag_pos = len(out)
        out.append(0)
        flags = 0
        for bit in range(8):
            if i >= n:
                break
            best_len = 0
            best_j = 0
            max_len = min(_MAX_MATCH, n - i)
            if max_len >= 3:
                lo = max(0, i - 1023)  # strictly < 1024 so ring src != r
                j = head.get(data[i:i + 3], -1)
                steps = 0
                while j >= lo and steps < 64:
                    l = 3
                    while l < max_len and data[j + l] == data[i + l]:
                        l += 1
                    if l > best_len:
                        best_len = l
                        best_j = j
                        if best_len == max_len:
                            break
                    j = prev[j]
                    steps += 1
            step = best_len if best_len >= 3 else 1
            # Insert consumed positions after searching so current position never self-matches
            for k in range(i, min(i + step, n - 2)):
                k3 = data[k:k + 3]
                prev[k] = head.get(k3, -1)
                head[k3] = k
            if best_len >= 3:
                src = (_RING_INIT + best_j) & _RING_MASK
                out.append(src & 0xFF)
                out.append(((src >> 2) & 0xC0) | (best_len - 3))
            else:
                flags |= 1 << bit
                out.append(data[i])
            i += step
        out[flag_pos] = flags
    return bytes(out)


def unpack_hpuyodt(data):
    """Unpack H_PUYODT.BIN (32-bit BE offset table of 4-byte-aligned Bits Lab LZSS chunks)."""
    if len(data) < 4:
        raise ValueError('H_PUYODT.BIN too short')
    first_off = struct.unpack_from('>I', data, 0)[0]
    if first_off == 0 or first_off % 4 != 0 or first_off > len(data):
        raise ValueError(f'invalid H_PUYODT.BIN header offset: {first_off:#x}')
    n = first_off // 4
    offs = struct.unpack_from(f'>{n}I', data, 0)
    chunks, orig_u, orig_c = [], [], []
    for o in offs:
        u, end = bits_decompress(data, o)
        chunks.append(bytearray(u))
        orig_u.append(u)
        orig_c.append(data[o:end])
    return {'chunks': chunks, '_orig_uncomp': orig_u, '_orig_comp': orig_c}


def pack_hpuyodt(arc):
    """Repack H_PUYODT.BIN dict (reuses original compressed bytes for untouched chunks)."""
    chunks = arc['chunks']
    orig_u = arc['_orig_uncomp']
    orig_c = arc['_orig_comp']
    if len(chunks) != len(orig_u):
        raise ValueError('cannot change H_PUYODT.BIN chunk count')
    out = bytearray(len(chunks) * 4)
    offs = []
    for i, ch in enumerate(chunks):
        raw = bytes(ch)
        comp = orig_c[i] if raw == orig_u[i] else bits_compress(raw)
        offs.append(len(out))
        out.extend(comp)
        pad = (-len(out)) & 3
        if pad:
            out.extend(b'\x00' * pad)
    struct.pack_into(f'>{len(offs)}I', out, 0, *offs)
    if len(out) > LOW_WRAM_SLOT:
        raise ValueError(f'H_PUYODT.BIN ({len(out)} B) exceeds 64 KB Low Work RAM slot')
    return bytes(out)


def unpack_bank(data):
    """Unpack a Bits Lab .BIN graphics bank (DEMO_G00..06, GFILE08..09, FACE_G00..03)."""
    n = len(data)
    if n < 2:
        raise ValueError('bank too short')
    # Walk 16-bit BE table until reaching the minimum non-zero pointer (handles leading zero slots)
    raw_tbl = []
    min_target = n
    i = 0
    while i * 2 < min_target:
        v = struct.unpack_from('>H', data, i * 2)[0]
        if v != 0 and v < min_target:
            min_target = v
        raw_tbl.append(v)
        i += 1

    desc_raw = {}
    raw_by_off = {}
    raw_table = []
    lz_offs = set()

    for t in raw_tbl:
        if t == 0:
            raw_table.append(None)
            continue
        w0 = struct.unpack_from('>H', data, t)[0]
        if w0 in (0xC000, 0xFFFF):
            if t not in desc_raw:
                p = t
                items = []
                while p + 2 <= n:
                    tag = struct.unpack_from('>H', data, p)[0]
                    if tag == 0xFFFF:
                        p += 2
                        break
                    if tag != 0xC000:
                        raise ValueError(f'unexpected descriptor tag {tag:#06x} at {p:#x}')
                    dst, doff = struct.unpack_from('>HH', data, p + 2)
                    items.append((dst, doff))
                    lz_offs.add(doff)
                    p += 6
                desc_raw[t] = items
            raw_table.append(('desc', t))
        else:
            if t not in raw_by_off:
                raw_by_off[t] = len(raw_by_off)
            raw_table.append(('raw', raw_by_off[t]))

    # Keep descriptor lists in original offset order so untouched repack is bit-for-bit identical
    desc_offs_sorted = sorted(desc_raw)
    desc_id_by_off = {o: idx for idx, o in enumerate(desc_offs_sorted)}
    desc_lists = [desc_raw[o] for o in desc_offs_sorted]
    table = [('desc', desc_id_by_off[ref[1]]) if (ref and ref[0] == 'desc') else ref for ref in raw_table]

    # Sort all payloads (LZSS chunks + raw entries like GFILE09[7] font) by original offset
    payloads = sorted([(o, 'lz') for o in lz_offs] + [(o, 'raw') for o in raw_by_off])
    lz_id_by_off = {}
    chunks, orig_u, orig_c = [], [], []
    raw_entries = [None] * len(raw_by_off)
    order = []

    for idx, (off, kind) in enumerate(payloads):
        nxt = payloads[idx + 1][0] if idx + 1 < len(payloads) else n
        if kind == 'lz':
            u, end = bits_decompress(data, off)
            if end > nxt:
                raise ValueError(f'LZSS chunk at {off:#x} overruns next payload at {nxt:#x}')
            cid = len(chunks)
            lz_id_by_off[off] = cid
            chunks.append(bytearray(u))
            orig_u.append(u)
            orig_c.append(data[off:end])
            order.append(('lz', cid))
        else:
            rid = raw_by_off[off]
            raw_entries[rid] = bytearray(data[off:nxt])
            order.append(('raw', rid))

    norm_descs = [[(dst, lz_id_by_off[doff]) for dst, doff in dlist] for dlist in desc_lists]

    return {
        'table': table,
        'descs': norm_descs,
        'chunks': chunks,
        'raw': raw_entries,
        '_order': order,
        '_orig_uncomp': orig_u,
        '_orig_comp': orig_c,
    }


def pack_bank(bank):
    """Repack a Bits Lab .BIN bank dict (reuses untouched LZSS bytes, 4-byte aligns raw entries)."""
    table = bank['table']
    descs = bank['descs']
    chunks = bank['chunks']
    raw_entries = bank['raw']
    orig_u = bank['_orig_uncomp']
    orig_c = bank['_orig_comp']

    out = bytearray(len(table) * 2)
    desc_offs = []
    for dlist in descs:
        desc_offs.append(len(out))
        out.extend(b'\x00' * (len(dlist) * 6 + 2))

    chunk_offs = [0] * len(chunks)
    raw_offs = [0] * len(raw_entries)
    for kind, idx in bank['_order']:
        if kind == 'lz':
            raw = bytes(chunks[idx])
            comp = orig_c[idx] if raw == orig_u[idx] else bits_compress(raw)
            chunk_offs[idx] = len(out)
            out.extend(comp)
        else:
            # Pad raw uncompressed entries (e.g. GFILE09[7] 1bpp font) to 4 bytes for SH-2 reads
            pad = (-len(out)) & 3
            if pad:
                out.extend(b'\x00' * pad)
            raw_offs[idx] = len(out)
            out.extend(raw_entries[idx])

    if len(out) > LOW_WRAM_SLOT:
        raise ValueError(f'bank ({len(out)} B) exceeds 64 KB Low Work RAM slot')

    # Back-fill 16-bit BE table pointers and descriptor lists (all offsets < len(out) <= 0x10000)
    for i, ref in enumerate(table):
        ptr = 0 if ref is None else (desc_offs[ref[1]] if ref[0] == 'desc' else raw_offs[ref[1]])
        if ptr >= 0x10000:
            raise ValueError(f'table pointer {ptr:#x} overflows 16-bit offset')
        struct.pack_into('>H', out, i * 2, ptr)

    for d_idx, dlist in enumerate(descs):
        p = desc_offs[d_idx]
        for dst, cid in dlist:
            struct.pack_into('>HHH', out, p, 0xC000, dst, chunk_offs[cid])
            p += 6
        struct.pack_into('>H', out, p, 0xFFFF)

    return bytes(out)


def _swizzle_vdp1(data, w_tiles, h_tiles, to_vdp1):
    need = w_tiles * h_tiles * 32
    if len(data) != need:
        raise ValueError(f'expected {need} bytes for {w_tiles}x{h_tiles} sprite, got {len(data)}')
    stride = w_tiles * 4
    out = bytearray(need)
    for tx in range(w_tiles):
        for ty in range(h_tiles):
            t_off = (tx * h_tiles + ty) * 32
            for py in range(8):
                l_off = (ty * 8 + py) * stride + tx * 4
                if to_vdp1:
                    out[l_off:l_off + 4] = data[t_off + py * 4:t_off + py * 4 + 4]
                else:
                    out[t_off + py * 4:t_off + py * 4 + 4] = data[l_off:l_off + 4]
    return out


def vdp1_to_tiles(linear, w_tiles, h_tiles):
    """Convert one Saturn VDP1 linear 4bpp sprite (w_tiles*8 x h_tiles*8 px) to MD column-major tiles."""
    return _swizzle_vdp1(linear, w_tiles, h_tiles, to_vdp1=False)


def tiles_to_vdp1(tiles, w_tiles, h_tiles):
    """Convert MD column-major 8x8 4bpp tiles to one Saturn VDP1 linear 4bpp sprite."""
    return bytes(_swizzle_vdp1(tiles, w_tiles, h_tiles, to_vdp1=True))


def _map_sprites(data, specs, fn):
    need = sum(w * h * 32 for w, h in specs)
    if len(data) != need:
        raise ValueError(f'expected {need} bytes for specs, got {len(data)}')
    out = bytearray()
    pos = 0
    for w, h in specs:
        sz = w * h * 32
        out.extend(fn(data[pos:pos + sz], w, h))
        pos += sz
    return out


def sprites_to_tiles(linear, specs):
    """Convert a sequence of VDP1 linear sprites described by [(w_tiles, h_tiles), ...] to MD tiles."""
    return _map_sprites(linear, specs, vdp1_to_tiles)


def tiles_to_sprites(tiles, specs):
    """Convert MD column-major tiles to a sequence of VDP1 linear sprites given [(w_tiles, h_tiles), ...]."""
    return bytes(_map_sprites(tiles, specs, tiles_to_vdp1))
