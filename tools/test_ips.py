#!/usr/bin/env python3
"""Stdlib-only regression tests for tools/ips.py, make_ips.py, and tools/release.py."""
import io, json, os, subprocess, sys, tempfile, urllib.error, urllib.request, zipfile
from pathlib import Path

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
sys.path.insert(0, ROOT)
import ips, logo, make_ips, make_puyopuy2e_md, release


class BlockPIL:
    def find_spec(self, name, *args):
        if name == 'PIL' or name.startswith('PIL.'):
            raise ImportError('PIL blocked: IPS tools must stay stdlib-only')


def test_ips_edge_cases():
    # Identical buffers
    src = bytes(range(256))
    p = ips.encode(src, src)
    assert p == b'PATCHEOF' and ips.apply(src, p) == src

    # RLE compression inside, at edge, and short (<14) non-RLE run inside changed region
    dst = bytearray(src)
    dst[10:60] = b'\xaa' * 50
    dst[100:105] = b'HELLO'
    dst[105:118] = b'\x33' * 13
    dst[118:143] = b'\x55' * 25
    dst[143:148] = b'WORLD'
    p = ips.encode(src, bytes(dst))
    assert ips.apply(src, p) == bytes(dst)
    assert len(p) < 75, f'expected RLE savings, got {len(p)} bytes'

    # 0x454f46 ('EOF') offset edge case (both normal and RLE starting right at 0x454f46)
    big_src = bytearray(0x455000)
    big_dst = bytearray(big_src)
    big_dst[0x454f46:0x454f4a] = b'TEST'
    p = ips.encode(big_src, big_dst)
    assert ips.apply(big_src, p) == bytes(big_dst)

    big_dst2 = bytearray(big_src)
    big_dst2[0x454f46:0x454f66] = b'\x77' * 32
    p2 = ips.encode(big_src, big_dst2)
    assert ips.apply(big_src, p2) == bytes(big_dst2)

    # Chunk larger than 0xffff (65535 bytes)
    s70 = bytes(70000)
    d70 = bytes((i * 37 + 1) & 0xff for i in range(70000))
    p70 = ips.encode(s70, d70)
    assert ips.apply(s70, p70) == d70

    # Expansion + truncation
    p_grow = ips.encode(b'abc', b'abcdef')
    assert ips.apply(b'abc', p_grow) == b'abcdef'
    p_cut = ips.encode(b'abcdef', b'abc')
    assert ips.apply(b'abcdef', p_cut) == b'abc'
    print('PASS ips unit edge cases')


def test_git_changelog():
    def git(cwd, *args):
        subprocess.run(['git', '-C', cwd, *args], check=True, capture_output=True, text=True)

    with tempfile.TemporaryDirectory() as td:
        git(td, 'init')
        git(td, 'config', 'user.email', 'test@example.com')
        git(td, 'config', 'user.name', 'Tester')
        (Path(td) / 'a.txt').write_text('1')
        git(td, 'add', 'a.txt')
        git(td, 'commit', '-m', 'Initial commit')
        head, prev, commits = release.git_changelog(td)
        assert head == 'Initial commit' and prev == '' and len(commits) == 1

        git(td, 'tag', 'r20261124-0000001')
        (Path(td) / 'a.txt').write_text('2')
        git(td, 'commit', '-am', 'Fix Nomi icon arrow')
        (Path(td) / 'a.txt').write_text('3')
        git(td, 'commit', '-am', 'Add Mega Drive IPS patches')
        head, prev, commits = release.git_changelog(td)
        assert head == 'Add Mega Drive IPS patches'
        assert prev == 'r20261124-0000001'
        assert commits == ['Add Mega Drive IPS patches', 'Fix Nomi icon arrow']

        notes = release.release_notes(
            repo='me/repo', tag='r20261124-0000002', prev_tag=prev, commits=commits,
        )
        assert '### Changes\n- Add Mega Drive IPS patches\n- Fix Nomi icon arrow' in notes
        assert '### Base ROMs required\n\n| Platform |' in notes
        assert '### Auto-patcher' in notes and '#### Windows (PowerShell)' in notes and '#### Linux / macOS' in notes
        assert '### GUI patcher' in notes and 'RomPatcher.js' in notes and 'Lunar IPS' not in notes
        assert 'https://github.com/me/repo/compare/r20261124-0000001...r20261124-0000002' in notes
    print('PASS git_changelog + release notes')


def test_publish_mock():
    class FakeResp(io.BytesIO):
        def __enter__(self): return self
        def __exit__(self, *a): pass

    def run_case(existing_releases, **kwargs):
        calls = []
        payloads = []
        created = {
            'id': 42, 'tag_name': kwargs.get('tag', 'r20261124-1234567'),
            'draft': kwargs.get('draft', False), 'html_url': 'https://example/rel',
            'assets': existing_releases[0]['assets'] if existing_releases else [],
        }

        def fake_urlopen(req, timeout=None):
            assert timeout == release.HTTP_TIMEOUT
            calls.append((req.get_method(), req.full_url, req.get_header('Content-type')))
            if req.get_method() == 'GET' and '/releases/tags/' in req.full_url:
                pub = next((r for r in existing_releases if not r.get('draft')), None)
                if pub is not None:
                    return FakeResp(json.dumps(pub).encode())
                raise urllib.error.HTTPError(req.full_url, 404, 'Not Found', {}, io.BytesIO(b''))
            if req.get_method() == 'GET':
                return FakeResp(json.dumps(existing_releases).encode())
            if req.get_method() in ('POST', 'PATCH') and '/assets' not in req.full_url:
                payloads.append(json.loads(req.data.decode('utf-8')))
                return FakeResp(json.dumps(created).encode())
            return FakeResp(b'{}')

        orig_open = urllib.request.urlopen
        urllib.request.urlopen = fake_urlopen
        try:
            with tempfile.TemporaryDirectory() as td:
                f1 = Path(td) / 'a.ips'
                f2 = Path(td) / 'b.zip'
                f1.write_bytes(b'PATCHEOF')
                f2.write_bytes(b'PK')
                url = release.publish_github_release('me/repo', kwargs.pop('tag'), [str(f1), str(f2)], 'tok', **kwargs)
                assert url == 'https://example/rel'
        finally:
            urllib.request.urlopen = orig_open
        return calls, payloads

    # 1. Brand-new release per revision (404 on tag lookup -> check drafts -> POST /releases)
    c_new, p_new = run_case([], tag='r20261124-abc1234', target='a' * 40)
    assert c_new == [
        ('GET', 'https://api.github.com/repos/me/repo/releases/tags/r20261124-abc1234', None),
        ('GET', 'https://api.github.com/repos/me/repo/releases?per_page=30', None),
        ('POST', 'https://api.github.com/repos/me/repo/releases', 'application/json'),
        ('POST', 'https://uploads.github.com/repos/me/repo/releases/42/assets?name=a.ips', 'application/octet-stream'),
        ('POST', 'https://uploads.github.com/repos/me/repo/releases/42/assets?name=b.zip', 'application/zip'),
    ], c_new
    assert len(p_new) == 1 and p_new[0].get('make_latest') == 'true', p_new

    # 2. Idempotent re-run on already-published revision (O(1) tag lookup -> PATCH + replace asset)
    pub_rel = [{'id': 42, 'tag_name': 'r20261124-abc1234', 'draft': False, 'html_url': 'https://example/rel',
                'assets': [{'id': 99, 'name': 'a.ips'}]}]
    c_upd, p_upd = run_case(pub_rel, tag='r20261124-abc1234', target='a' * 40)
    assert c_upd == [
        ('GET', 'https://api.github.com/repos/me/repo/releases/tags/r20261124-abc1234', None),
        ('PATCH', 'https://api.github.com/repos/me/repo/releases/42', 'application/json'),
        ('DELETE', 'https://api.github.com/repos/me/repo/releases/assets/99', None),
        ('POST', 'https://uploads.github.com/repos/me/repo/releases/42/assets?name=a.ips', 'application/octet-stream'),
        ('POST', 'https://uploads.github.com/repos/me/repo/releases/42/assets?name=b.zip', 'application/zip'),
    ], c_upd
    assert len(p_upd) == 1 and p_upd[0].get('make_latest') == 'true', p_upd

    # 3. Updating an existing draft (404 on tag lookup -> found in drafts -> PATCH)
    draft_rel = [{'id': 42, 'tag_name': 'r20261124-abc1234', 'draft': True, 'html_url': 'https://example/rel',
                  'assets': []}]
    c_draft, p_draft = run_case(draft_rel, tag='r20261124-abc1234', target='a' * 40, draft=True)
    assert c_draft[:3] == [
        ('GET', 'https://api.github.com/repos/me/repo/releases/tags/r20261124-abc1234', None),
        ('GET', 'https://api.github.com/repos/me/repo/releases?per_page=30', None),
        ('PATCH', 'https://api.github.com/repos/me/repo/releases/42', 'application/json'),
    ], c_draft
    assert len(p_draft) == 1 and 'make_latest' not in p_draft[0], p_draft
    print('PASS GitHub release publisher mock (new + published re-run + draft)')


def test_rom_ips():
    md_rom = os.path.join(ROOT, make_puyopuy2e_md.ORIG_NAME)
    arc_rom = os.path.join(ROOT, 'puyopuy2.zip')
    with tempfile.TemporaryDirectory(prefix='pp2e_ips_') as td:
        if os.path.exists(md_rom):
            arts = make_ips.build_md_ips(md_rom, td, list(logo.MODES))
            assert len(arts) == 3
            print('PASS Mega Drive IPS round-trip (3/3 logo modes)')
        if os.path.exists(arc_rom):
            arts = make_ips.build_arcade_ips(arc_rom, td, list(logo.MODES))
            assert len(arts) == 3
            for zpath in arts:
                with zipfile.ZipFile(zpath) as z:
                    assert sorted(z.namelist()) == [
                        'README.txt', 'epr-17240.ic31.ips', 'epr-17241.ic32.ips', 'patch.ps1', 'patch.sh'
                    ]
                    assert b'\r\n' not in z.read('patch.sh'), 'patch.sh must use LF line endings'
            print('PASS Arcade per-chip IPS bundles (3/3 logo modes)')


def main():
    sys.meta_path.insert(0, BlockPIL())
    test_ips_edge_cases()
    test_git_changelog()
    test_publish_mock()
    test_rom_ips()
    print('All IPS tests passed (stdlib-only).')


if __name__ == '__main__':
    main()
