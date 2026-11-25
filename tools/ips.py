"""Pure-stdlib IPS (International Patching System) encoder and applier.

Format: b'PATCH' + records + b'EOF' + optional 3-byte big-endian truncation length.
Each record is 3-byte offset + 2-byte size (+ data), or size=0 + 2-byte RLE count + 1-byte value.
Handles the 0x454f46 ('EOF') offset edge case and chunks larger than 0xffff bytes."""
import struct

HEADER = b'PATCH'
TRAILER = b'EOF'
EOF_OFFSET = 0x454f46
MAX_OFFSET = 0xffffff
MAX_CHUNK = 0xffff
MERGE_GAP = 5       # a new IPS record header costs 5 bytes
RLE_MIN_EDGE = 9    # RLE record is 8 bytes; saves space starting at 9 identical bytes
RLE_MIN_MID = 14    # splitting an active normal chunk costs an extra 5-byte header


def _rle_run(data, pos, end):
    val = data[pos]
    p = pos + 1
    limit = min(end, pos + MAX_CHUNK)
    while p < limit and data[p] == val:
        p += 1
    return p - pos


def encode(src, dst):
    """Return an IPS patch (bytes) that transforms src into dst."""
    src, dst = memoryview(src), memoryview(dst)
    n_src, n_dst = len(src), len(dst)
    out = bytearray(HEADER)

    # Collect differing spans, merging gaps <= MERGE_GAP bytes
    spans = []
    i = 0
    while i < n_dst:
        if i < n_src and src[i] == dst[i]:
            i += 1
            continue
        start = i
        i += 1
        while i < n_dst:
            if i < n_src and src[i] == dst[i]:
                gap = i
                while gap < n_dst and gap < n_src and src[gap] == dst[gap] and gap - i <= MERGE_GAP:
                    gap += 1
                if gap - i > MERGE_GAP or gap == n_dst:
                    break
                i = gap
            else:
                i += 1
        spans.append((start, i))

    for start, end in spans:
        pos = start
        while pos < end:
            if pos > MAX_OFFSET:
                raise ValueError('IPS offset 0x%x exceeds 16 MB limit' % pos)
            # Never emit 0x454f46 ('EOF') as a record offset: back up 1 byte and emit a normal pair
            if pos == EOF_OFFSET:
                chunk_end = min(end, pos + 1)
                data = bytes(dst[pos - 1:chunk_end])
                out += struct.pack('>I', pos - 1)[1:] + struct.pack('>H', len(data)) + data
                pos = chunk_end
                continue
            # Prefer RLE when starting on a run >= RLE_MIN_EDGE
            run = _rle_run(dst, pos, end)
            if run >= RLE_MIN_EDGE:
                out += struct.pack('>I', pos)[1:] + struct.pack('>HHB', 0, run, dst[pos])
                pos += run
                continue
            # Emit a normal chunk up to MAX_CHUNK or until an interior RLE run worth splitting
            limit = min(end, pos + MAX_CHUNK)
            scan = pos + 1
            while scan < limit:
                r = _rle_run(dst, scan, limit)
                if r >= RLE_MIN_MID:
                    break
                scan += r
            data = bytes(dst[pos:scan])
            out += struct.pack('>I', pos)[1:] + struct.pack('>H', len(data)) + data
            pos = scan

    out += TRAILER
    if n_dst < n_src:
        if n_dst > MAX_OFFSET:
            raise ValueError('IPS truncation length 0x%x exceeds 16 MB limit' % n_dst)
        out += struct.pack('>I', n_dst)[1:]
    return bytes(out)


def apply(src, patch):
    """Apply an IPS patch to src and return the patched bytes."""
    if len(patch) < 8 or patch[:5] != HEADER:
        raise ValueError('invalid IPS header')
    out = bytearray(src)
    p, n = 5, len(patch)
    while p + 3 <= n:
        if patch[p:p + 3] == TRAILER:
            p += 3
            if p == n:
                return bytes(out)
            if p + 3 == n:
                trunc = (patch[p] << 16) | (patch[p + 1] << 8) | patch[p + 2]
                return bytes(out[:trunc])
            raise ValueError('unexpected trailing bytes after IPS EOF')
        if p + 5 > n:
            raise ValueError('truncated IPS record header')
        off = (patch[p] << 16) | (patch[p + 1] << 8) | patch[p + 2]
        size = (patch[p + 3] << 8) | patch[p + 4]
        p += 5
        if size == 0:
            if p + 3 > n:
                raise ValueError('truncated IPS RLE record')
            count = (patch[p] << 8) | patch[p + 1]
            val = patch[p + 2]
            p += 3
            if off + count > len(out):
                out.extend(b'\x00' * (off + count - len(out)))
            out[off:off + count] = bytes([val]) * count
        else:
            if p + size > n:
                raise ValueError('truncated IPS data record')
            if off + size > len(out):
                out.extend(b'\x00' * (off + size - len(out)))
            out[off:off + size] = patch[p:p + size]
            p += size
    raise ValueError('missing IPS EOF marker')
