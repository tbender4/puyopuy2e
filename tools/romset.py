"""Puyo Puyo 2 (Sega C2, MAME set puyopuy2): the program is two 512 KB EPROMs,
epr-17241.ic32 the even bytes and epr-17240.ic31 the odd ones, 1 MB at 0x000000."""
import zipfile, zlib

PROGRAM = (('epr-17241.ic32', 0x1cad1149), ('epr-17240.ic31', 0xbeecf96d))
SOUND = ('epr-17239.ic4', 0x020ff6ef)


def read_chip(z, name, crc):
    """a chip of the zip, found by CRC (the names inside the zip do not matter)"""
    for info in z.infolist():
        if info.CRC == crc:
            data = z.read(info)
            if zlib.crc32(data) & 0xffffffff == crc:
                return data
    raise SystemExit('%s (CRC %08x) not found in the zip: not the MAME puyopuy2 dump' % (name, crc))


def read_program(zip_path):
    """the 1 MB program of puyopuy2.zip, interleaved, checked by CRC"""
    z = zipfile.ZipFile(zip_path)
    halves = [read_chip(z, name, crc) for name, crc in PROGRAM]
    prog = bytearray(len(halves[0]) * 2)
    prog[0::2], prog[1::2] = halves
    return prog


def split_program(prog):
    """(even, odd) EPROM images of a 1 MB program"""
    return bytes(prog[0::2]), bytes(prog[1::2])


def read_sound(zip_path):
    """the UPD7759 sample ROM, unchanged"""
    return read_chip(zipfile.ZipFile(zip_path), *SOUND)
