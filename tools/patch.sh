#!/bin/sh
# Apply Puyo Puyo 2 English patches (Mega Drive .ips, Arcade -ips.zip or Saturn .bps).
# Pure POSIX sh + coreutils (od/awk/dd/tr; unzip/zip for arcade; perl or python3 for Saturn CRC32 checks).
# Usage:
#   ./patch.sh "Puyo Puyo 2 (Japan) (v1.1).md" puyopuy2e-md-rcN.ips [out.md]
#   ./patch.sh puyopuy2.zip puyopuy2e-arcade-rcN-ips.zip [out.zip] [--mame]
#   ./patch.sh "PUYO_PUYO_TSU____ (Track 1).bin" puyopuy2e-saturn-rcN.bps [out.bin]
set -eu

MAME=0
ROM=""
PATCH=""
OUT=""
for arg in "$@"; do
    case "$arg" in
        --mame) MAME=1 ;;
        *)
            if [ -z "$ROM" ]; then ROM="$arg"
            elif [ -z "$PATCH" ]; then PATCH="$arg"
            elif [ -z "$OUT" ]; then OUT="$arg"
            else echo "Unexpected argument: $arg" >&2; exit 2
            fi ;;
    esac
done

if [ -z "$ROM" ] || [ -z "$PATCH" ]; then
    echo "Usage: $0 <rom> <patch.ips|arcade-ips.zip|patch.bps> [out] [--mame]" >&2
    exit 2
fi
if [ ! -f "$ROM" ]; then echo "ROM not found: $ROM" >&2; exit 1; fi
if [ ! -f "$PATCH" ]; then echo "Patch not found: $PATCH" >&2; exit 1; fi

abs_path() {
    dir=$(dirname -- "$1")
    base=$(basename -- "$1")
    d=$(cd -- "$dir" && pwd -P) || exit 1
    printf '%s/%s\n' "$d" "$base"
}

# Stop unless $1 is the exact base ROM the patches were made from (POSIX cksum: "crc size").
check_base() {
    got=$(cksum < "$1" | awk '{print $1" "$2}')
    if [ "$got" != "$2" ]; then
        echo "$3 is not the expected base ROM (cksum $got, need $2)" >&2
        exit 1
    fi
}

apply_ips() {
    src="$1"
    ips="$2"
    dst="$3"
    # Parse and validate IPS binary before touching dst: D off src_pos size | R off cnt oct | T len
    ops=$(od -An -tu1 -v "$ips" | awk '
        { for (i = 1; i <= NF; i++) b[n++] = $i + 0 }
        END {
            if (n < 8 || b[0]!=80 || b[1]!=65 || b[2]!=84 || b[3]!=67 || b[4]!=72) {
                print "Invalid IPS header" > "/dev/stderr"; exit 1
            }
            p = 5
            while (p + 3 <= n) {
                if (b[p]==69 && b[p+1]==79 && b[p+2]==70) {
                    p += 3
                    if (p == n) exit 0
                    if (p + 3 == n) {
                        printf "T %d\n", b[p]*65536 + b[p+1]*256 + b[p+2]
                        exit 0
                    }
                    print "Unexpected trailing bytes after IPS EOF" > "/dev/stderr"; exit 1
                }
                if (p + 5 > n) { print "Truncated IPS record header" > "/dev/stderr"; exit 1 }
                off = b[p]*65536 + b[p+1]*256 + b[p+2]
                sz  = b[p+3]*256 + b[p+4]
                p += 5
                if (sz == 0) {
                    if (p + 3 > n) { print "Truncated IPS RLE record" > "/dev/stderr"; exit 1 }
                    cnt = b[p]*256 + b[p+1]
                    val = b[p+2]
                    p += 3
                    printf "R %d %d %03o\n", off, cnt, val
                } else {
                    if (p + sz > n) { print "Truncated IPS data record" > "/dev/stderr"; exit 1 }
                    printf "D %d %d %d\n", off, p, sz
                    p += sz
                }
            }
            print "Missing IPS EOF marker" > "/dev/stderr"; exit 1
        }
    ')
    cp -- "$src" "$dst"
    printf '%s\n' "$ops" | while read -r op a b c; do
        case "$op" in
            D)
                dd if="$ips" of="$dst" bs=1 skip="$b" seek="$a" count="$c" conv=notrunc 2>/dev/null
                ;;
            R)
                if [ "$c" = "000" ]; then
                    dd if=/dev/zero of="$dst" bs=1 seek="$a" count="$b" conv=notrunc 2>/dev/null
                else
                    dd if=/dev/zero bs=1 count="$b" 2>/dev/null | LC_ALL=C tr '\000' "\\$c" \
                        | dd of="$dst" bs=1 seek="$a" conv=notrunc 2>/dev/null
                fi
                ;;
            T)
                # IPS truncation only shrinks (dd would also grow the file)
                if [ "$a" -lt "$(wc -c < "$dst")" ]; then
                    dd if=/dev/null of="$dst" bs=1 seek="$a" 2>/dev/null
                fi
                ;;
        esac
    done
}

# CRC32 (zlib, as BPS uses) of stdin; prints nothing if neither perl nor python3 is installed
crc32_of() {
    if perl -MCompress::Zlib -e 1 2>/dev/null; then
        perl -MCompress::Zlib -e 'binmode STDIN; $c = 0; $c = crc32($b, $c) while read(STDIN, $b, 1048576); print "$c\n"'
    elif command -v python3 >/dev/null 2>&1; then
        python3 -c 'import sys, zlib
c = 0
for b in iter(lambda: sys.stdin.buffer.read(1 << 20), b""): c = zlib.crc32(b, c)
print(c)'
    else
        cat > /dev/null
    fi
}

# Saturn Track 1 BPS (only SourceRead/TargetRead, what make_ips.py writes): copy the source,
# write the new bytes in place (the target may be longer: Track 1 grows), check the three CRC32s
# with perl or python3.
apply_bps() {
    src="$1"
    bps="$2"
    dst="$3"
    label="$4"
    ops=$(od -An -tu1 -v "$bps" | awk '
        function varint(   d, s, x) {
            d = 0; s = 1
            while (1) {
                x = b[p++]; d += (x % 128) * s
                if (x >= 128) return d
                s *= 128; d += s
            }
        }
        { for (i = 1; i <= NF; i++) b[n++] = $i + 0 }
        END {
            if (n < 19 || b[0]!=66 || b[1]!=80 || b[2]!=83 || b[3]!=49) {
                print "Invalid BPS header" > "/dev/stderr"; exit 1
            }
            p = 4
            nsrc = varint(); ndst = varint(); m = varint(); p += m
            if (ndst < nsrc) { print "BPS shrinks the file (not a puyopuy2e patch)" > "/dev/stderr"; exit 1 }
            pos = 0
            while (p < n - 12) {
                c = varint(); k = c % 4; len = int(c / 4) + 1
                if (k == 1) { printf "D %d %d %d\n", pos, p, len; p += len }
                else if (k != 0) { print "Unsupported BPS action (not a puyopuy2e patch)" > "/dev/stderr"; exit 1 }
                pos += len
            }
            if (pos != ndst) { print "BPS actions do not cover the target" > "/dev/stderr"; exit 1 }
            for (k = 0; k < 3; k++) {   # CRC32s of source, target, patch (little-endian)
                q = n - 12 + 4 * k
                printf "%s%.0f", (k ? " " : "C "),  # %.0f: mawk caps %d at 2^31-1
                    b[q] + b[q+1]*256 + b[q+2]*65536 + b[q+3]*16777216
            }
            print ""
        }
    ')
    crcs=$(printf '%s\n' "$ops" | tail -n 1)
    crc_src=$(echo "$crcs" | awk '{print $2}')
    crc_dst=$(echo "$crcs" | awk '{print $3}')
    crc_bps=$(echo "$crcs" | awk '{print $4}')
    if [ -z "$(echo | crc32_of)" ]; then
        echo "perl and python3 not found: checking the base disc with cksum only" >&2
        check_base "$src" "744555374 606498480" "$label"
        crc_dst=""
    elif [ "$(head -c $(($(wc -c < "$bps") - 4)) "$bps" | crc32_of)" != "$crc_bps" ]; then
        echo "$bps is corrupt (patch CRC32 mismatch)" >&2; exit 1
    elif [ "$(crc32_of < "$src")" != "$crc_src" ]; then
        echo "$label is not the expected base disc (need CRC32 $(printf %08x "$crc_src"))" >&2; exit 1
    fi
    cp -- "$src" "$dst"
    printf '%s\n' "$ops" | grep '^D' | while read -r op a b c; do
        dd if="$bps" of="$dst" bs=1 skip="$b" seek="$a" count="$c" conv=notrunc 2>/dev/null
    done
    if [ -n "$crc_dst" ] && [ "$(crc32_of < "$dst")" != "$crc_dst" ]; then
        rm -f -- "$dst"
        echo "Patched disc does not match the BPS target CRC32" >&2; exit 1
    fi
}

ROM_ABS=$(abs_path "$ROM")
PATCH_ABS=$(abs_path "$PATCH")
ROM_DIR=$(dirname -- "$ROM_ABS")

case "$PATCH_ABS" in
    *.[Bb][Pp][Ss])
        if [ -z "$OUT" ]; then
            OUT="$ROM_DIR/Puyo Puyo 2 (English) (Track 1).bin"
        fi
        OUT_ABS=$(abs_path "$OUT")
        if [ "$OUT_ABS" = "$ROM_ABS" ]; then
            echo "Refusing to overwrite input ROM: $ROM_ABS" >&2
            exit 1
        fi
        apply_bps "$ROM_ABS" "$PATCH_ABS" "$OUT_ABS" "$ROM (need PUYO_PUYO_TSU____ (Track 1).bin)"
        # .cue beside the new Track 1; Track 2 (audio) is unchanged and must sit in the same folder
        OUT_DIR=$(dirname -- "$OUT_ABS")
        T2=$(basename -- "$ROM_ABS" | sed 's/(Track 1)/(Track 2)/')
        [ "$T2" != "$(basename -- "$ROM_ABS")" ] || T2='PUYO_PUYO_TSU____ (Track 2).bin'
        printf 'FILE "%s" BINARY\n  TRACK 01 MODE1/2352\n    INDEX 01 00:00:00\nFILE "%s" BINARY\n  TRACK 02 AUDIO\n    INDEX 00 00:00:00\n    INDEX 01 00:02:00\n' \
            "$(basename -- "$OUT_ABS")" "$T2" > "$OUT_DIR/Puyo Puyo 2 (English).cue"
        [ -f "$OUT_DIR/$T2" ] || echo "Copy $T2 next to $OUT_DIR/Puyo Puyo 2 (English).cue" >&2
        echo "Patched Saturn Track 1 written to $OUT_ABS (open $OUT_DIR/Puyo Puyo 2 (English).cue)"
        ;;
    *.[Zz][Ii][Pp])
        for cmd in unzip zip; do
            if ! command -v "$cmd" >/dev/null 2>&1; then
                echo "$cmd is required to patch arcade .zip sets" >&2
                exit 1
            fi
        done
        if [ -z "$OUT" ]; then
            if [ "$MAME" -eq 1 ]; then OUT="$ROM_DIR/puyopuy2-en.zip"
            else OUT="$ROM_DIR/puyopuy2e.zip"
            fi
        fi
        OUT_ABS=$(abs_path "$OUT")
        if [ "$OUT_ABS" = "$ROM_ABS" ]; then
            echo "Refusing to overwrite input ROM: $ROM_ABS" >&2
            exit 1
        fi
        TMP=$(mktemp -d)
        trap 'rm -rf "$TMP"' EXIT
        unzip -oqjL "$ROM_ABS" -d "$TMP/rom"
        unzip -oqjL "$PATCH_ABS" -d "$TMP/ips"
        for f in epr-17241.ic32 epr-17240.ic31 epr-17239.ic4; do
            if [ ! -f "$TMP/rom/$f" ]; then echo "Missing $f inside $ROM" >&2; exit 1; fi
        done
        check_base "$TMP/rom/epr-17241.ic32" "1172277925 524288" "epr-17241.ic32 in $ROM"
        check_base "$TMP/rom/epr-17240.ic31" "3325161525 524288" "epr-17240.ic31 in $ROM"
        if [ "$MAME" -eq 1 ]; then
            EV_OUT="epr-17241.ic32"; OD_OUT="epr-17240.ic31"
        else
            EV_OUT="pp2e-17241.ic32"; OD_OUT="pp2e-17240.ic31"
        fi
        mkdir -p "$TMP/out"
        apply_ips "$TMP/rom/epr-17241.ic32" "$TMP/ips/epr-17241.ic32.ips" "$TMP/out/$EV_OUT"
        apply_ips "$TMP/rom/epr-17240.ic31" "$TMP/ips/epr-17240.ic31.ips" "$TMP/out/$OD_OUT"
        cp "$TMP/rom/epr-17239.ic4" "$TMP/out/epr-17239.ic4"
        rm -f "$OUT_ABS"
        zip -qj "$OUT_ABS" "$TMP/out/$EV_OUT" "$TMP/out/$OD_OUT" "$TMP/out/epr-17239.ic4"
        echo "Patched arcade set written to $OUT_ABS"
        ;;
    *)
        if [ -z "$OUT" ]; then
            OUT="$ROM_DIR/Puyo Puyo 2 (English) (v1.1).md"
        fi
        OUT_ABS=$(abs_path "$OUT")
        if [ "$OUT_ABS" = "$ROM_ABS" ]; then
            echo "Refusing to overwrite input ROM: $ROM_ABS" >&2
            exit 1
        fi
        check_base "$ROM_ABS" "453739695 2097152" "$ROM (need Puyo Puyo 2 (Japan) (v1.1))"
        apply_ips "$ROM_ABS" "$PATCH_ABS" "$OUT_ABS"
        echo "Patched Mega Drive ROM written to $OUT_ABS"
        ;;
esac
