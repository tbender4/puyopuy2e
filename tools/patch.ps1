<#
.SYNOPSIS
  Apply Puyo Puyo 2 English patches (Mega Drive .ips, Arcade -ips.zip or Saturn .bps).
.EXAMPLE
  powershell -ExecutionPolicy Bypass -File .\patch.ps1 "Puyo Puyo 2 (Japan) (v1.1).md" puyopuy2e-md-no-red-puyos.ips
.EXAMPLE
  powershell -ExecutionPolicy Bypass -File .\patch.ps1 puyopuy2.zip puyopuy2e-arcade-no-red-puyos-ips.zip
.EXAMPLE
  powershell -ExecutionPolicy Bypass -File .\patch.ps1 puyopuy2.zip puyopuy2e-arcade-no-red-puyos-ips.zip -Mame
.EXAMPLE
  powershell -ExecutionPolicy Bypass -File .\patch.ps1 "PUYO_PUYO_TSU____ (Track 1).bin" puyopuy2e-saturn-no-red-puyos.bps
#>
param(
    [Parameter(Mandatory = $true, Position = 0)][string]$Rom,
    [Parameter(Mandatory = $true, Position = 1)][string]$Patch,
    [Parameter(Position = 2)][string]$Out = '',
    [switch]$Mame
)
$ErrorActionPreference = 'Stop'

function Apply-Ips([byte[]]$Src, [byte[]]$Ips) {
    if ($Ips.Length -lt 8 -or [Text.Encoding]::ASCII.GetString($Ips, 0, 5) -ne 'PATCH') {
        throw 'Invalid IPS header'
    }
    [byte[]]$buf = New-Object byte[] $Src.Length
    [Array]::Copy($Src, $buf, $Src.Length)
    $p = 5
    while ($p + 3 -le $Ips.Length) {
        if ($Ips[$p] -eq 0x45 -and $Ips[$p + 1] -eq 0x4F -and $Ips[$p + 2] -eq 0x46) {
            $p += 3
            if ($p -eq $Ips.Length) { return ,$buf }
            if ($p + 3 -eq $Ips.Length) {
                $trunc = ([int]$Ips[$p] -shl 16) -bor ([int]$Ips[$p + 1] -shl 8) -bor [int]$Ips[$p + 2]
                if ($trunc -lt $buf.Length) { [Array]::Resize([ref]$buf, $trunc) }
                return ,$buf
            }
            throw 'Unexpected trailing bytes after IPS EOF'
        }
        if ($p + 5 -gt $Ips.Length) { throw 'Truncated IPS record header' }
        $off  = ([int]$Ips[$p] -shl 16) -bor ([int]$Ips[$p + 1] -shl 8) -bor [int]$Ips[$p + 2]
        $size = ([int]$Ips[$p + 3] -shl 8) -bor [int]$Ips[$p + 4]
        $p += 5
        if ($size -eq 0) {
            if ($p + 3 -gt $Ips.Length) { throw 'Truncated IPS RLE record' }
            $cnt = ([int]$Ips[$p] -shl 8) -bor [int]$Ips[$p + 1]
            $val = $Ips[$p + 2]
            $p += 3
            if ($off + $cnt -gt $buf.Length) { [Array]::Resize([ref]$buf, $off + $cnt) }
            for ($i = 0; $i -lt $cnt; $i++) { $buf[$off + $i] = $val }
        } else {
            if ($p + $size -gt $Ips.Length) { throw 'Truncated IPS data record' }
            if ($off + $size -gt $buf.Length) { [Array]::Resize([ref]$buf, $off + $size) }
            [Array]::Copy($Ips, $p, $buf, $off, $size)
            $p += $size
        }
    }
    throw 'Missing IPS EOF marker'
}

# Stop unless $Data is the exact base ROM the patches were made from
function Assert-Base([byte[]]$Data, [string]$Sha1, [string]$Label) {
    $sha = [Security.Cryptography.SHA1]::Create()
    try { $h = -join ($sha.ComputeHash($Data) | ForEach-Object { $_.ToString('X2') }) } finally { $sha.Dispose() }
    if ($h -ne $Sha1) { throw "$Label is not the expected base ROM (SHA-1 $h, need $Sha1)" }
}

Add-Type -TypeDefinition @'
public static class Crc32File {
    public static uint Of(string path) {
        uint[] t = new uint[256];
        for (uint n = 0; n < 256; n++) { uint c = n; for (int k = 0; k < 8; k++) c = (c & 1) != 0 ? 0xEDB88320u ^ (c >> 1) : c >> 1; t[n] = c; }
        uint crc = 0xFFFFFFFFu; byte[] buf = new byte[1 << 20]; int r;
        using (var f = System.IO.File.OpenRead(path)) {
            while ((r = f.Read(buf, 0, buf.Length)) > 0) for (int i = 0; i < r; i++) crc = t[(crc ^ buf[i]) & 0xFF] ^ (crc >> 8);
        }
        return ~crc;
    }
}
'@

function Read-Varint([byte[]]$P, [ref]$I) {
    [long]$data = 0; [long]$shift = 1
    while ($true) {
        $x = $P[$I.Value]; $I.Value++
        $data += ($x -band 0x7f) * $shift
        if ($x -band 0x80) { return $data }
        $shift = $shift -shl 7
        $data += $shift
    }
}

# Saturn Track 1 BPS (only SourceRead/TargetRead, what make_ips.py writes): copy the source, write the new bytes in place
function Apply-Bps([string]$Src, [string]$PatchFile, [string]$Dst) {
    [byte[]]$p = [IO.File]::ReadAllBytes($PatchFile)
    if ($p.Length -lt 19 -or [Text.Encoding]::ASCII.GetString($p, 0, 4) -ne 'BPS1') { throw 'Invalid BPS header' }
    $i = 4
    $nSrc = Read-Varint $p ([ref]$i); $nDst = Read-Varint $p ([ref]$i); $meta = Read-Varint $p ([ref]$i); $i += $meta
    $crcSrc = [BitConverter]::ToUInt32($p, $p.Length - 12); $crcDst = [BitConverter]::ToUInt32($p, $p.Length - 8)
    if ((Get-Item -LiteralPath $Src).Length -ne $nSrc -or [Crc32File]::Of($Src) -ne $crcSrc) {
        throw ("$Src is not the expected base disc (need {0} bytes, CRC32 {1:x8})" -f $nSrc, $crcSrc)
    }
    Copy-Item -LiteralPath $Src -Destination $Dst -Force
    $f = [IO.File]::Open($Dst, 'Open', 'ReadWrite')
    try {
        $f.SetLength($nDst)
        [long]$pos = 0
        while ($i -lt $p.Length - 12) {
            $cmd = Read-Varint $p ([ref]$i)
            $n = ($cmd -shr 2) + 1
            switch ($cmd -band 3) {
                0 { }
                1 { $f.Position = $pos; $f.Write($p, $i, $n); $i += $n }
                default { throw 'Unsupported BPS action (use Flips for third-party patches)' }
            }
            $pos += $n
        }
    } finally { $f.Dispose() }
    if ([Crc32File]::Of($Dst) -ne $crcDst) { Remove-Item -LiteralPath $Dst; throw 'Patched disc does not match the BPS target CRC32' }
}

function Read-ZipEntry([System.IO.Compression.ZipArchive]$Zip, [string]$Name) {
    $e = $Zip.Entries | Where-Object { $_.Name -ieq $Name } | Select-Object -First 1
    if (-not $e) { throw "Missing $Name inside archive" }
    $ms = New-Object System.IO.MemoryStream
    $s = $e.Open()
    try {
        $s.CopyTo($ms)
        return ,($ms.ToArray())
    } finally {
        $s.Dispose()
        $ms.Dispose()
    }
}

$romPath = (Resolve-Path -LiteralPath $Rom).Path
$patchPath = (Resolve-Path -LiteralPath $Patch).Path
$resolveOut = {
    param([string]$PathArg, [string]$DefaultName)
    $raw = if ($PathArg) { $PathArg } else { Join-Path (Split-Path -Parent $romPath) $DefaultName }
    $full = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($raw)
    if ($full -ieq $romPath) { throw "Refusing to overwrite input ROM: $romPath" }
    return $full
}

if ($patchPath.ToLower().EndsWith('.bps')) {
    $outFull = & $resolveOut $Out 'Puyo Puyo 2 (English) (Track 1).bin'
    Apply-Bps $romPath $patchPath $outFull
    # .cue beside the new Track 1; Track 2 (audio) is unchanged and must sit in the same folder
    $t2 = (Split-Path -Leaf $romPath) -replace '\(Track 1\)', '(Track 2)'
    $cue = "FILE `"$(Split-Path -Leaf $outFull)`" BINARY`n  TRACK 01 MODE1/2352`n    INDEX 01 00:00:00`n" +
           "FILE `"$t2`" BINARY`n  TRACK 02 AUDIO`n    INDEX 00 00:00:00`n    INDEX 01 00:02:00`n"
    $cuePath = Join-Path (Split-Path -Parent $outFull) 'Puyo Puyo 2 (English).cue'
    [IO.File]::WriteAllText($cuePath, $cue)
    if (-not (Test-Path -LiteralPath (Join-Path (Split-Path -Parent $outFull) $t2))) { Write-Warning "Copy $t2 next to $cuePath" }
    Write-Host "Patched Saturn Track 1 written to $outFull (open $cuePath)"
} elseif ($patchPath.ToLower().EndsWith('.zip')) {
    Add-Type -AssemblyName System.IO.Compression, System.IO.Compression.FileSystem
    $outFull = & $resolveOut $Out ($(if ($Mame) { 'puyopuy2-en.zip' } else { 'puyopuy2e.zip' }))

    $rz = [IO.Compression.ZipFile]::OpenRead($romPath)
    $pz = [IO.Compression.ZipFile]::OpenRead($patchPath)
    try {
        $evSrc = Read-ZipEntry $rz 'epr-17241.ic32'
        $odSrc = Read-ZipEntry $rz 'epr-17240.ic31'
        Assert-Base $evSrc '77FB0482FA35E615C0BED65F4D7F4DD89B241F23' "epr-17241.ic32 in $Rom"
        Assert-Base $odSrc 'C2BDAD4B6184C11F81F2A5DB409CB4EA186205A7' "epr-17240.ic31 in $Rom"
        $ev = Apply-Ips $evSrc (Read-ZipEntry $pz 'epr-17241.ic32.ips')
        $od = Apply-Ips $odSrc (Read-ZipEntry $pz 'epr-17240.ic31.ips')
        $sn = Read-ZipEntry $rz 'epr-17239.ic4'
    } finally { $rz.Dispose(); $pz.Dispose() }

    $evName = if ($Mame) { 'epr-17241.ic32' } else { 'pp2e-17241.ic32' }
    $odName = if ($Mame) { 'epr-17240.ic31' } else { 'pp2e-17240.ic31' }
    if (Test-Path -LiteralPath $outFull) { Remove-Item -LiteralPath $outFull -Force }
    $oz = [IO.Compression.ZipFile]::Open($outFull, [IO.Compression.ZipArchiveMode]::Create)
    try {
        foreach ($item in @(@($evName, $ev), @($odName, $od), @('epr-17239.ic4', $sn))) {
            $e = $oz.CreateEntry($item[0], [IO.Compression.CompressionLevel]::Optimal)
            $s = $e.Open()
            try { $s.Write($item[1], 0, $item[1].Length) } finally { $s.Dispose() }
        }
    } finally { $oz.Dispose() }
    Write-Host "Patched arcade set written to $outFull"
} else {
    $outFull = & $resolveOut $Out 'Puyo Puyo 2 (English) (v1.1).md'
    $src = [IO.File]::ReadAllBytes($romPath)
    Assert-Base $src 'D9C0EDAADF66F215565A9DD4178313581FEC811C' "$Rom (need Puyo Puyo 2 (Japan) (v1.1))"
    $patched = Apply-Ips $src ([IO.File]::ReadAllBytes($patchPath))
    [IO.File]::WriteAllBytes($outFull, $patched)
    Write-Host "Patched Mega Drive ROM written to $outFull ($($patched.Length) bytes)"
}
