"""Pure-stdlib BPS patch encoder and applier (no size limit, unlike IPS).

Format: b'BPS1', varint source size, target size, metadata size (+ metadata), actions,
then CRC32 of source, target and of the patch itself. Each action is varint
(length - 1) << 2 | kind: 0 SourceRead, 1 TargetRead (+ bytes), 2 SourceCopy and
3 TargetCopy (+ signed relative offset). Only SourceRead/TargetRead are written or read:
enough for in-place disc edits (Flips applies the rest).

Buffers can be bytes or mmap objects, so the 606 MB Saturn track is never copied in memory."""
import struct, zlib

MAGIC = b'BPS1'
CHUNK = 1 << 20
MERGE_GAP = 4   # a SourceRead action costs 1-3 bytes; shorter equal gaps go into the TargetRead


def _varint(n):
    out = bytearray()
    while True:
        x = n & 0x7f
        n >>= 7
        if n == 0:
            out.append(0x80 | x)
            return bytes(out)
        out.append(x)
        n -= 1


def _read_varint(p, i):
    data, shift = 0, 1
    while True:
        if i >= len(p):
            raise ValueError('truncated BPS varint')
        x = p[i]
        i += 1
        data += (x & 0x7f) * shift
        if x & 0x80:
            return data, i
        shift <<= 7
        data += shift


def _crc(buf):
    c = 0
    for i in range(0, len(buf), CHUNK):
        c = zlib.crc32(buf[i:i + CHUNK], c)
    return c & 0xffffffff


def _spans(src, dst):
    """(start, end) runs where dst differs from src (or extends past it), small gaps merged."""
    n_src, n_dst = len(src), len(dst)
    spans = []
    for base in range(0, n_dst, CHUNK):
        d = dst[base:base + CHUNK]
        s = src[base:base + CHUNK] if base < n_src else b''
        if d == s:
            continue
        for i in range(len(d)):
            if i < len(s) and d[i] == s[i]:
                continue
            at = base + i
            if spans and at - spans[-1][1] <= MERGE_GAP:
                spans[-1][1] = at + 1
            else:
                spans.append([at, at + 1])
    return spans


def encode(src, dst):
    """Return a BPS patch (bytes) turning src into dst."""
    out = bytearray(MAGIC + _varint(len(src)) + _varint(len(dst)) + _varint(0))
    pos = 0
    for start, end in _spans(src, dst) + [[len(dst), len(dst)]]:
        if start > pos:             # SourceRead: unchanged bytes (always inside src, see _spans)
            out += _varint((start - pos - 1) << 2)
            pos = start
        if end > start:
            out += _varint((end - start - 1) << 2 | 1) + bytes(dst[start:end])
            pos = end
    out += struct.pack('<II', _crc(src), _crc(dst))
    out += struct.pack('<I', zlib.crc32(out) & 0xffffffff)
    return bytes(out)


def header(patch):
    """(source size, target size, CRC32 source, CRC32 target) after checking the patch's own CRC."""
    if len(patch) < 19 or patch[:4] != MAGIC:
        raise ValueError('invalid BPS header')
    if zlib.crc32(patch[:-4]) & 0xffffffff != struct.unpack_from('<I', patch, len(patch) - 4)[0]:
        raise ValueError('BPS patch is corrupt (patch CRC32 mismatch)')
    n_src, i = _read_varint(patch, 4)
    n_dst, i = _read_varint(patch, i)
    crc_src, crc_dst = struct.unpack_from('<II', patch, len(patch) - 12)
    return n_src, n_dst, crc_src, crc_dst


def apply(src, patch, out):
    """Apply patch to src, writing the target to out (a file opened 'w+b'). Checks all three CRCs."""
    n_src, n_dst, crc_src, crc_dst = header(patch)
    if len(src) != n_src or _crc(src) != crc_src:
        raise ValueError(f'wrong source file (need {n_src} bytes, CRC32 {crc_src:08x})')
    _, i = _read_varint(patch, 4)
    _, i = _read_varint(patch, i)
    meta, i = _read_varint(patch, i)
    i += meta
    end = len(patch) - 12
    pos = 0
    crc = 0
    out.seek(0)
    out.truncate()

    def emit(data):
        nonlocal pos, crc
        out.write(data)
        crc = zlib.crc32(data, crc)
        pos += len(data)

    while i < end:
        cmd, i = _read_varint(patch, i)
        kind, n = cmd & 3, (cmd >> 2) + 1
        if pos + n > n_dst:
            raise ValueError('BPS action writes past the target size')
        if kind == 0:
            stop = pos + n
            if stop > n_src:
                raise ValueError('BPS SourceRead past the source size')
            while pos < stop:
                emit(src[pos:min(stop, pos + CHUNK)])
        elif kind == 1:
            if i + n > end:
                raise ValueError('truncated BPS TargetRead')
            emit(patch[i:i + n])
            i += n
        else:  # only SourceRead/TargetRead: what encode() writes
            raise ValueError('unsupported BPS action (SourceCopy/TargetCopy): use Flips for third-party patches')
    if pos != n_dst or (crc & 0xffffffff) != crc_dst:
        raise ValueError('BPS result does not match the target CRC32')
