#!/usr/bin/env python3
"""tools/release.py - Publish a directory of built IPS/BPS artifacts to GitHub Releases.

Each platform's patches carry a release candidate number (puyopuy2e-<platform>-rcN...) that goes
up by one only when that platform's patches differ from the previous release's.
Only the Python 3 standard library is used. Reads GITHUB_TOKEN from the environment."""
import argparse, hashlib, io, json, os, re, subprocess, sys, urllib.error, urllib.parse, urllib.request, zipfile
from pathlib import Path

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, ROOT)
import make_ips, make_puyopuy2e_md, make_puyopuy2e_saturn, romset

API_BASE = 'https://api.github.com'
UPLOAD_BASE = 'https://uploads.github.com'
HTTP_TIMEOUT = 60
PLATFORMS = {'arcade': 'Arcade', 'md': 'Mega Drive', 'saturn': 'Saturn'}
PATCH_NAME = re.compile(r'puyopuy2e-(arcade|md|saturn)(?:-rc(\d+))?([-.].+)')
SUMS = 'SHA256SUMS.txt'


def patch_key(name, data):
    """what makes a patch count as changed: its bytes, or for the arcade zip only its .ips files
    (its README.txt and patcher scripts don't move the arcade RC)"""
    if not name.endswith('.zip'):
        return hashlib.sha256(data).hexdigest()
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        return ' '.join(n + ':' + hashlib.sha256(z.read(n)).hexdigest()
                        for n in sorted(z.namelist()) if n.endswith('.ips'))


def number_rcs(dist, prev=None):
    """Rename dist's patches to puyopuy2e-<platform>-rcN<rest> and rewrite SHA256SUMS.txt.
    prev is the previous release's {asset name: bytes}; returns {platform: (N, changed)}."""
    prev_rc, prev_key = {}, {}
    for name, data in (prev or {}).items():
        m = PATCH_NAME.fullmatch(name)
        if m and m[2]:          # releases before RC numbering count as no release
            prev_rc[m[1]] = max(prev_rc.get(m[1], 0), int(m[2]))
            prev_key[m[1], m[3]] = patch_key(name, data)
    dist = Path(dist)
    patches = {}
    for f in sorted(dist.iterdir()):
        m = PATCH_NAME.fullmatch(f.name)
        if m:
            patches.setdefault(m[1], []).append((f, m[3]))
    rcs = {}
    for plat, items in patches.items():
        changed = any(prev_key.get((plat, rest)) != patch_key(f.name, f.read_bytes()) for f, rest in items)
        rc = prev_rc.get(plat, 0) + changed
        for f, rest in items:
            f.rename(dist / f'puyopuy2e-{plat}-rc{rc}{rest}')
        rcs[plat] = (rc, changed)
    make_ips.write_checksums(dist, sorted(str(f) for f in dist.iterdir() if f.name != SUMS))
    return rcs


def new_files(dist, prev):
    """names of dist's files that the previous release ({name: bytes}) lacks or has with other bytes;
    a patcher script fix is published even when no RC moves"""
    return [f.name for f in sorted(Path(dist).iterdir()) if f.name != SUMS and prev.get(f.name) != f.read_bytes()]


def previous_assets(repo, tag, token):
    """{name: bytes} of the files (all but SHA256SUMS.txt) of the newest published release older
    than tag that is complete (has SHA256SUMS.txt, which is uploaded last); {} if none"""
    releases = [r for r in _gh_request('GET', f'{API_BASE}/repos/{repo}/releases?per_page=30', token)
                if not r.get('draft')]      # newest first; a re-run of an older tag skips the newer ones
    start = next((i + 1 for i, r in enumerate(releases) if r.get('tag_name') == tag), 0)
    rel = next((r for r in releases[start:] if any(a['name'] == SUMS for a in r.get('assets', ()))), None)
    out = {}
    for a in (rel or {}).get('assets', ()):
        if a['name'] != SUMS:
            with urllib.request.urlopen(a['browser_download_url'], timeout=HTTP_TIMEOUT) as resp:
                out[a['name']] = resp.read()
    return out


def _git(cwd, *args):
    try:
        r = subprocess.run(['git', '-C', cwd, *args], capture_output=True, text=True, encoding='utf-8', errors='replace')
    except FileNotFoundError:
        return ''
    return r.stdout.strip() if r.returncode == 0 else ''


def git_changelog(cwd=ROOT):
    """Return (prev_tag, [subject, ...]) since the previous git tag."""
    prev_tag = _git(cwd, 'describe', '--tags', '--abbrev=0', 'HEAD^')
    rev_range = f'{prev_tag}..HEAD' if prev_tag else 'HEAD'
    log_args = ['log', '--no-merges', '--format=%s']
    if not prev_tag:
        log_args += ['-n', '1']
    raw = _git(cwd, *log_args, rev_range)
    if not raw:
        raw = _git(cwd, 'log', '-n', '1', '--format=%s', 'HEAD')
    commits = [line for line in raw.splitlines() if line]
    return prev_tag, commits


def release_notes(repo=None, tag=None, prev_tag='', commits=(), updated=()):
    """Format GitHub Release markdown from git commits and base ROM requirements."""
    lines = [f'**Updated:** {", ".join(updated)}', ''] if updated else []
    if commits:
        lines.append('### Changes')
        for subj in commits:
            lines.append(f'- {subj}')
        if repo and prev_tag and tag:
            lines += ['', f'**Full Changelog:** https://github.com/{repo}/compare/{prev_tag}...{tag}']
        lines.append('')
    lines += [
        '### Base ROMs required',
        '',
        '| Platform | File | Size | CRC32 |',
        '|---|---|---|---|',
        f'| Mega Drive | `{make_puyopuy2e_md.ORIG_NAME}` | {make_puyopuy2e_md.ORIG_SIZE:,} | `{make_puyopuy2e_md.ORIG_CRC:08x}` |',
    ]
    for name, crc in romset.PROGRAM:
        lines.append(f'| Arcade (`puyopuy2.zip`) | `{name}` | 524,288 | `{crc:08x}` |')
    snd_name, snd_crc = romset.SOUND
    lines += [
        f'| Arcade (`puyopuy2.zip`) | `{snd_name}` (unchanged) | 524,288 | `{snd_crc:08x}` |',
        f'| Saturn | `{make_puyopuy2e_saturn.ORIG_NAME}` (Track 2 unchanged) | {make_puyopuy2e_saturn.ORIG_SIZE:,} '
        f'| `{make_puyopuy2e_saturn.ORIG_CRC:08x}` |',
        '',
        '### Auto-patcher',
        '',
        '#### Windows (PowerShell)',
        '```powershell',
        r'powershell -ExecutionPolicy Bypass -File .\patch.ps1 <base_rom> <patch.ips, arcade-ips.zip or saturn .bps>',
        '```',
        'Add `-Mame` for upstream MAME (`epr-*` filenames).',
        '',
        '#### Linux / macOS',
        '```sh',
        './patch.sh <base_rom> <patch.ips, arcade-ips.zip or saturn .bps>',
        '```',
        'Add `--mame` for upstream MAME (`epr-*` filenames).',
        '',
        'Saturn: pass Track 1; the patcher writes the English Track 1 and a `.cue` that uses the original Track 2 (keep it in the same folder).',
        '',
        '### GUI patcher',
        'Patch in the browser with [RomPatcher.js](https://www.marcrobledo.com/RomPatcher.js/) (see `README.txt` inside the arcade zip for manual steps).',
    ]
    return '\n'.join(lines)


def _gh_request(method, url, token, body=None, content_type='application/json'):
    headers = {
        'Authorization': f'Bearer {token}',
        'Accept': 'application/vnd.github+json',
        'X-GitHub-Api-Version': '2022-11-28',
        'User-Agent': 'puyopuy2e-release',
    }
    if body is not None:
        headers['Content-Type'] = content_type
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as resp:
        raw = resp.read()
        return json.loads(raw.decode('utf-8')) if raw else None


def _find_release(repo, tag, token):
    tag_q = urllib.parse.quote(tag, safe='')
    try:
        return _gh_request('GET', f'{API_BASE}/repos/{repo}/releases/tags/{tag_q}', token)
    except urllib.error.HTTPError as e:
        if e.code != 404:
            raise
        e.close()
    # Draft releases are hidden from /releases/tags/{tag}; check recent releases for a matching draft
    releases = _gh_request('GET', f'{API_BASE}/repos/{repo}/releases?per_page=30', token)
    return next((r for r in releases if r.get('tag_name') == tag), None)


def publish_github_release(repo, tag, files, token, title=None, body='', draft=False, target=None):
    """Create or update a GitHub Release for `tag` and idempotently upload `files`."""
    rel = _find_release(repo, tag, token)
    spec = {'tag_name': tag, 'name': title or tag, 'body': body, 'draft': draft}
    if not draft:
        spec['make_latest'] = 'true'
    if target:
        spec['target_commitish'] = target
    if rel is None:
        rel = _gh_request('POST', f'{API_BASE}/repos/{repo}/releases', token, json.dumps(spec).encode('utf-8'))
        print(f'created GitHub release {tag} (id={rel["id"]}, draft={draft})')
    else:
        rel = _gh_request('PATCH', f'{API_BASE}/repos/{repo}/releases/{rel["id"]}', token,
                          json.dumps(spec).encode('utf-8'))
        print(f'updated GitHub release {tag} (id={rel["id"]}, draft={rel.get("draft")})')

    existing = {a['name']: a['id'] for a in rel.get('assets', ())}
    # SHA256SUMS.txt goes first and comes back last: only a complete release has it (see previous_assets)
    if SUMS in existing:
        _gh_request('DELETE', f'{API_BASE}/repos/{repo}/releases/assets/{existing.pop(SUMS)}', token)
    for path in sorted(files, key=lambda f: os.path.basename(f) == SUMS):
        name = os.path.basename(path)
        if name in existing:
            _gh_request('DELETE', f'{API_BASE}/repos/{repo}/releases/assets/{existing[name]}', token)
        data = Path(path).read_bytes()
        ctype = 'application/zip' if name.endswith('.zip') else (
            'text/plain' if name.endswith(('.txt', '.ps1', '.sh')) else 'application/octet-stream'
        )
        url = f'{UPLOAD_BASE}/repos/{repo}/releases/{rel["id"]}/assets?name={urllib.parse.quote(name)}'
        _gh_request('POST', url, token, body=data, content_type=ctype)
        print(f'uploaded {name} ({len(data)} bytes)')
    return rel.get('html_url', '')


def main():
    p = argparse.ArgumentParser(description='Publish built release artifacts to GitHub Releases.')
    p.add_argument('--dir', default=os.path.join(ROOT, 'dist'), help='directory of files to upload (default: dist)')
    p.add_argument('--tag', required=True, help='GitHub Release tag name')
    p.add_argument('--repo', required=True, help='GitHub repository OWNER/REPO')
    p.add_argument('--target', help='branch or commit SHA for GitHub release tag (default: repo default branch)')
    p.add_argument('--draft', action='store_true', help='create GitHub release as draft')
    args = p.parse_args()

    token = os.environ.get('GITHUB_TOKEN')
    if not token:
        raise SystemExit('GITHUB_TOKEN environment variable is required')
    dist = Path(args.dir)
    if not dist.is_dir():
        raise SystemExit(f'artifact directory not found: {dist}')
    if not any(f.is_file() for f in dist.iterdir()):
        raise SystemExit(f'no files to upload in {dist}')

    prev_tag, commits = git_changelog(ROOT)
    try:
        prev = previous_assets(args.repo, args.tag, token)
        rcs = number_rcs(dist, prev)
        if not new_files(dist, prev):
            print('nothing differs from the previous release: nothing to publish')
            return
        files = sorted(str(f) for f in dist.iterdir() if f.is_file())
        labels = {p: f'{PLATFORMS[p]} RC{rcs[p][0]}' for p in PLATFORMS if p in rcs}
        body = release_notes(repo=args.repo, tag=args.tag, prev_tag=prev_tag, commits=commits,
                             updated=[labels[p] for p in labels if rcs[p][1]])
        title = ' | '.join(labels.values())
        url = publish_github_release(
            args.repo, args.tag, files, token,
            title=title, body=body, draft=args.draft, target=args.target,
        )
    except urllib.error.HTTPError as e:
        raise SystemExit(f'GitHub API error {e.code}: {e.read().decode("utf-8", "replace")}')
    except (urllib.error.URLError, TimeoutError) as e:
        raise SystemExit(f'GitHub request failed: {e}')
    print('release URL:', url)


if __name__ == '__main__':
    main()
