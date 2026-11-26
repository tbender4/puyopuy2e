<#
.SYNOPSIS
  Apply Puyo Puyo 2 English IPS patches (Mega Drive .ips or Arcade -ips.zip).
.EXAMPLE
  powershell -ExecutionPolicy Bypass -File .\patch.ps1 "Puyo Puyo 2 (Japan) (v1.1).md" puyopuy2e-md-no-red-puyos.ips
.EXAMPLE
  powershell -ExecutionPolicy Bypass -File .\patch.ps1 puyopuy2.zip puyopuy2e-arcade-no-red-puyos-ips.zip
.EXAMPLE
  powershell -ExecutionPolicy Bypass -File .\patch.ps1 puyopuy2.zip puyopuy2e-arcade-no-red-puyos-ips.zip -Mame
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

if ($patchPath.ToLower().EndsWith('.zip')) {
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
