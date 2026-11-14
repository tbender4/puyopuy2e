"""Graphics: editing the LZ streams (tools/lz.py) that hold tiles and tile maps.

A stream is loaded through a list of 6-byte entries in the stream's own 64 KB bank:
flags, count, destination word, then the stream's 16-bit offset inside the bank
(the loader at 0x1b70). A rebuilt stream that no longer fits where it was goes to free
space (0xff) in the same bank, and the list entries that load it are pointed there."""
import lz

TILE = 32


def tile_get(data, n):
    """8x8 pixel values of tile n of a 4 bpp tile stream"""
    t = data[n * TILE:(n + 1) * TILE]
    return [[(t[y * 4 + x // 2] >> (4 if x % 2 == 0 else 0)) & 15 for x in range(8)] for y in range(8)]


def tile_put(data, n, pix):
    for y in range(8):
        for x in range(0, 8, 2):
            data[n * TILE + y * 4 + x // 2] = (pix[y][x] << 4) | pix[y][x + 1]


def entries_pointing(prog, addr):
    """offsets of the list entries loading the stream at addr"""
    bank, off = addr & ~0xffff, addr & 0xffff
    out = []
    for i in range(bank, bank + 0x10000 - 6, 2):
        if prog[i + 4] << 8 | prog[i + 5] == off and prog[i] in (0x00, 0x40, 0x80, 0xc0, 0x01, 0x41, 0x81, 0xc1, 0x02, 0x03, 0x42, 0x82, 0xc2):
            out.append(i)
    return out


def free_space(prog, bank, size, used):
    """an address in bank with size free (0xff) bytes, not in used ranges"""
    run = 0
    for i in range(bank, bank + 0x10000):
        busy = prog[i] != 0xff or any(a <= i < b for a, b in used)
        run = 0 if busy else run + 1
        if run == size + 2:
            return i - size        # leave one 0xff byte before
    return None


class Streams:
    """the streams rebuilt so far; write() puts them back"""

    def __init__(self, prog):
        self.prog = prog
        self.new = {}           # original address -> new uncompressed data

    def original(self, addr):
        """the stream as it is in the original program"""
        return lz.decompress(self.prog, addr)[0]

    def get(self, addr):
        if addr not in self.new:
            self.new[addr] = bytearray(lz.decompress(self.prog, addr)[0])
        return self.new[addr]

    def write(self):
        used, grown = [], []
        for addr, data in self.new.items():         # first the ones that fit: what they
            old_end = lz.decompress(self.prog, addr)[1]     # leave over becomes free space
            packed = lz.compress(bytes(data))
            if len(packed) <= old_end - addr:
                self.prog[addr:old_end] = packed + b'\xff' * (old_end - addr - len(packed))
                print('stream %06x: %d -> %d bytes' % (addr, old_end - addr, len(packed)))
            else:
                grown.append((addr, packed, old_end))
        for addr, packed, old_end in grown:
            self.prog[addr:old_end] = b'\xff' * (old_end - addr)    # its old place is free too
            print('stream %06x: %d -> %d bytes, moved' % (addr, old_end - addr, len(packed)))
            at = free_space(self.prog, addr & ~0xffff, len(packed), used)
            if at is None:
                raise SystemExit('stream %06x: no room for %d bytes in its bank' % (addr, len(packed)))
            refs = entries_pointing(self.prog, addr)
            if len(refs) != 1:
                raise SystemExit('stream %06x: %d list entries' % (addr, len(refs)))
            self.prog[at:at + len(packed)] = packed
            used.append((at, at + len(packed)))
            for r in refs:
                self.prog[r + 4:r + 6] = (at & 0xffff).to_bytes(2, 'big')


def map_words(mapdata, off, count):
    return [mapdata[off + 2 * i] << 8 | mapdata[off + 2 * i + 1] for i in range(count)]


def replace_block(tiles, mapdata, off, width, height, img, row_stride=None, tile_bias=0,
                  background=0, blank=None):
    """draws img (width*8 x height*8 pixel values) over the map block at off (rows of
    width words, row_stride words apart): the block's own tiles (those no other word of
    the map uses) are redrawn, identical 8x8 cells share a tile, empty cells use an empty
    tile of the stream; the words keep their palette/priority bits"""
    stride = row_stride or width
    cells = [(r, c, off + 2 * (r * stride + c)) for r in range(height) for c in range(width)]
    inside = {i for _, _, i in cells}
    words = map_words(mapdata, 0, len(mapdata) // 2)
    used_elsewhere = {w & 0x7ff for k, w in enumerate(words) if 2 * k not in inside}
    pool = sorted({(mapdata[i] << 8 | mapdata[i + 1]) & 0x7ff for _, _, i in cells} - used_elsewhere)
    pool = [t - tile_bias for t in pool]
    n = len(tiles) // TILE
    if blank is None:
        blank = next(t for t in range(n) if not any(tiles[t * TILE:(t + 1) * TILE]))
    empty = blank
    made = {}
    for r, c, i in cells:
        block = [row[c * 8:c * 8 + 8] for row in img[r * 8:r * 8 + 8]]
        key = tuple(tuple(x) for x in block)
        if all(v == background for x in block for v in x):
            t = empty
        elif key in made:
            t = made[key]
        else:
            if not pool:
                raise SystemExit('replace_block: not enough tiles')
            t = pool.pop(0)
            tile_put(tiles, t, block)
            made[key] = t
        word = (mapdata[i] << 8 | mapdata[i + 1]) & 0xe000
        mapdata[i:i + 2] = (word | (t + tile_bias)).to_bytes(2, 'big')
    for t in pool:
        tile_put(tiles, t, [[background] * 8 for _ in range(8)])
