"""tools/saturn_iso.py - Sega Saturn Mode 1/2352 sector codec and ISO-9660 file patcher.

Stdlib-only ECMA-130 Mode 1/2352 (Sync, BCD MSF, EDC, Reed-Solomon P/Q ECC) encoder and
in-place flat-root ISO-9660 reader/patcher for Sega Saturn Track 1 .bin/.cue images."""
import os, re, shutil, struct

SECTOR_RAW = 2352
SECTOR_USER = 2048
PREGAP = 150
SYNC = b'\x00' + b'\xff' * 10 + b'\x00'
_CUE_FILE_RE = re.compile(r'(?im)^(\s*FILE\s+)(?:"([^"]+)"|(\S+))')

# Precompute ECMA-130 EDC (reflected CRC-32 poly 0xD8018001) and GF(2^8) ECC lookup tables
_EDC_LUT = []
for _i in range(256):
    _v = _i
    for _ in range(8):
        _v = (_v >> 1) ^ (0xD8018001 if (_v & 1) else 0)
    _EDC_LUT.append(_v)

_ECC_F = [0] * 256
_ECC_B = [0] * 256
for _i in range(256):
    _j = (_i << 1) ^ (0x11D if (_i & 0x80) else 0)
    _ECC_F[_i] = _j
    _ECC_B[_i ^ _j] = _i


def _bcd(n):
    return ((n // 10) << 4) | (n % 10)


def _edc(data):
    crc = 0
    lut = _EDC_LUT
    for b in data:
        crc = (crc >> 8) ^ lut[(crc ^ b) & 0xFF]
    return crc


def _ecc_pq(buf, major_count, minor_count, major_mult, minor_inc, dest_off):
    size = major_count * minor_count
    f_lut, b_lut = _ECC_F, _ECC_B
    for major in range(major_count):
        index = (major >> 1) * major_mult + (major & 1)
        a = b = 0
        for _ in range(minor_count):
            t = buf[12 + index]
            index += minor_inc
            if index >= size:
                index -= size
            a ^= t
            b ^= t
            a = f_lut[a]
        a = b_lut[f_lut[a] ^ b]
        buf[dest_off + major] = a
        buf[dest_off + major + major_count] = a ^ b


def encode_mode1_sector(lba, user_data):
    """Build one unscrambled 2352-byte Mode 1 sector for `lba` from 2048 bytes of user data."""
    if len(user_data) != SECTOR_USER:
        raise ValueError(f'expected {SECTOR_USER} bytes of user data, got {len(user_data)}')
    if lba < 0:
        raise ValueError(f'invalid negative LBA: {lba}')
    t = lba + PREGAP
    buf = bytearray(SECTOR_RAW)
    buf[0:12] = SYNC
    buf[12] = _bcd(t // 4500)
    buf[13] = _bcd((t // 75) % 60)
    buf[14] = _bcd(t % 75)
    buf[15] = 0x01
    buf[16:2064] = user_data
    struct.pack_into('<I', buf, 2064, _edc(memoryview(buf)[:2064]))
    # bytes 2068..2075 remain zero; compute Reed-Solomon P (172 B) then Q (104 B)
    _ecc_pq(buf, 86, 24, 2, 86, 2076)
    _ecc_pq(buf, 52, 43, 86, 88, 2248)
    return bytes(buf)


def verify_mode1_sector(lba, raw_sector):
    """Return True iff `raw_sector` is a bit-for-bit valid Mode 1/2352 sector for `lba`."""
    return len(raw_sector) == SECTOR_RAW and encode_mode1_sector(lba, raw_sector[16:2064]) == raw_sector


def _norm_name(name):
    return name.strip('/').split(';')[0].upper()


def _same_path(a, b):
    na, nb = os.path.normcase(os.path.abspath(a)), os.path.normcase(os.path.abspath(b))
    if na == nb:
        return True
    return os.path.exists(a) and os.path.exists(b) and os.path.samefile(a, b)


def _read_sector_user(f, lba):
    f.seek(lba * SECTOR_RAW + 16)
    data = f.read(SECTOR_USER)
    if len(data) != SECTOR_USER:
        raise ValueError(f'unexpected EOF reading LBA {lba}')
    return data


def parse_iso(f):
    """Parse flat ISO-9660 root directory from an open Mode 1/2352 file object.

    Returns dict mapping normalized uppercase filename (without ';1') to
    {'lba', 'size', 'sectors', 'dir_sec', 'dir_off'}."""
    pvd = _read_sector_user(f, 16)
    if pvd[0:6] != b'\x01CD001':
        raise ValueError('sector 16 is not an ISO-9660 Primary Volume Descriptor')
    root_lba = struct.unpack_from('<I', pvd, 156 + 2)[0]
    root_size = struct.unpack_from('<I', pvd, 156 + 10)[0]
    n_sec = (root_size + SECTOR_USER - 1) // SECTOR_USER
    entries = {}
    for i in range(n_sec):
        sec_lba = root_lba + i
        sec = _read_sector_user(f, sec_lba)
        pos = 0
        while pos < SECTOR_USER:
            rec_len = sec[pos]
            if rec_len == 0:
                break
            flags = sec[pos + 25]
            nlen = sec[pos + 32]
            raw_name = sec[pos + 33:pos + 33 + nlen].decode('ascii', 'replace')
            if not (flags & 2):
                lba = struct.unpack_from('<I', sec, pos + 2)[0]
                size = struct.unpack_from('<I', sec, pos + 10)[0]
                entries[_norm_name(raw_name)] = {
                    'lba': lba,
                    'size': size,
                    'sectors': (size + SECTOR_USER - 1) // SECTOR_USER,
                    'dir_sec': sec_lba,
                    'dir_off': pos,
                }
            pos += rec_len
    return entries


def read_iso_file(f, name, entries=None):
    """Read exact bytes of one ISO-9660 root file by name."""
    if entries is None:
        entries = parse_iso(f)
    key = _norm_name(name)
    if key not in entries:
        raise KeyError(f'file not found in ISO root: {name}')
    entry = entries[key]
    out = bytearray()
    rem, lba = entry['size'], entry['lba']
    while rem > 0:
        take = min(SECTOR_USER, rem)
        out.extend(_read_sector_user(f, lba)[:take])
        rem -= take
        lba += 1
    return bytes(out)


def _prepare_cue(src_bin, out_bin, out_cue):
    """Locate and validate source .cue and companion tracks before any disk writes."""
    if not _same_path(os.path.dirname(out_bin), os.path.dirname(out_cue)):
        raise ValueError('out_bin and out_cue must be in the same directory')
    src_dir = os.path.dirname(src_bin)
    src_base = os.path.basename(src_bin).lower()
    src_cue = cue_text = cue_files = None
    for name in sorted(os.listdir(src_dir)):
        if not name.lower().endswith('.cue'):
            continue
        path = os.path.join(src_dir, name)
        with open(path, 'r', encoding='utf-8', errors='replace') as f:
            text = f.read()
        files = [m.group(2) or m.group(3) for m in _CUE_FILE_RE.finditer(text)]
        if files and os.path.basename(files[0]).lower() == src_base:
            src_cue, cue_text, cue_files = path, text, files
            break
    if src_cue is None:
        raise FileNotFoundError(f'no source .cue referencing {os.path.basename(src_bin)} in {src_dir}')
    if _same_path(out_cue, src_cue):
        raise ValueError(f'refusing to overwrite source .cue: {src_cue}')
    extras = []
    for extra in cue_files[1:]:
        src_extra = os.path.abspath(os.path.join(src_dir, extra))
        if not os.path.isfile(src_extra):
            raise FileNotFoundError(f'missing companion track referenced by .cue: {src_extra}')
        extras.append((src_extra, os.path.basename(extra)))
    return cue_text, extras


def _write_out_cue(out_bin, out_cue, cue_text, extras):
    out_dir = os.path.dirname(out_cue)
    for src_extra, base in extras:
        dst_extra = os.path.abspath(os.path.join(out_dir, base))
        if not _same_path(src_extra, dst_extra):
            if not os.path.isfile(dst_extra) or os.path.getsize(dst_extra) != os.path.getsize(src_extra):
                shutil.copyfile(src_extra, dst_extra)
    idx = [0]
    def _sub(m):
        i = idx[0]
        idx[0] += 1
        target = os.path.basename(out_bin) if i == 0 else os.path.basename(m.group(2) or m.group(3))
        return f'{m.group(1)}"{target}"'
    out_text = _CUE_FILE_RE.sub(_sub, cue_text)
    with open(out_cue, 'w', encoding='utf-8', newline='\n') as f:
        f.write(out_text)


def patch_iso(src_bin, out_bin, replacements, out_cue=None, fresh=True):
    """Patch files in-place into a Mode 1/2352 Saturn Track 1 image.

    shortcut: in-place sector replacement only; add free-LBA relocation only if a translated
    file actually exceeds its original ISO sector allocation.

    Defaults to fresh=True (copies src_bin -> out_bin for deterministic builds). Pass
    fresh=False only to overlay onto an existing out_bin of the same size (<1s dev loop)."""
    src_bin = os.path.abspath(src_bin)
    out_bin = os.path.abspath(out_bin)
    if _same_path(src_bin, out_bin):
        raise ValueError(f'refusing to overwrite source image: {src_bin}')
    cue_plan = None
    if out_cue is not None:
        out_cue = os.path.abspath(out_cue)
        cue_plan = _prepare_cue(src_bin, out_bin, out_cue)

    with open(src_bin, 'rb') as sf:
        entries = parse_iso(sf)

    # Validate all replacements before touching disk
    staged = []
    for raw_name, new_data in replacements.items():
        key = _norm_name(raw_name)
        if key not in entries:
            raise KeyError(f'file not found in ISO root: {raw_name}')
        ent = entries[key]
        cap = ent['sectors'] * SECTOR_USER
        if len(new_data) > cap:
            raise ValueError(
                f'{key}: {len(new_data)} bytes exceeds allocated {ent["sectors"]} sectors ({cap} bytes)'
            )
        staged.append((key, ent, new_data))

    out_dir = os.path.dirname(out_bin)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    need_copy = fresh or not os.path.isfile(out_bin) or os.path.getsize(out_bin) != os.path.getsize(src_bin)
    if need_copy:
        shutil.copyfile(src_bin, out_bin)

    dir_cache = {}
    summary = {}
    with open(out_bin, 'r+b') as of:
        for key, ent, new_data in staged:
            lba = ent['lba']
            orig_sectors = ent['sectors']
            for i in range(orig_sectors):
                chunk = bytes(new_data[i * SECTOR_USER:(i + 1) * SECTOR_USER]).ljust(SECTOR_USER, b'\x00')
                of.seek((lba + i) * SECTOR_RAW)
                of.write(encode_mode1_sector(lba + i, chunk))

            # Update LE + BE file size in root directory sector (read from out_bin to preserve sibling overlays)
            dsec = ent['dir_sec']
            if dsec not in dir_cache:
                dir_cache[dsec] = bytearray(_read_sector_user(of, dsec))
            doff = ent['dir_off']
            struct.pack_into('<I', dir_cache[dsec], doff + 10, len(new_data))
            struct.pack_into('>I', dir_cache[dsec], doff + 14, len(new_data))
            summary[key] = {'lba': lba, 'old_size': ent['size'], 'new_size': len(new_data), 'sectors': orig_sectors}

        for dsec, sec_buf in dir_cache.items():
            of.seek(dsec * SECTOR_RAW)
            of.write(encode_mode1_sector(dsec, bytes(sec_buf)))

    if cue_plan is not None:
        _write_out_cue(out_bin, out_cue, *cue_plan)
    return summary
