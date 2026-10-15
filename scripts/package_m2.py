"""Build a self-contained native M2 runtime archive, excluding dev fixtures."""

import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path(__file__).resolve().parents[1]


def main():
    manifest = json.loads((ROOT / 'dashboard/manifest.json').read_text(encoding='utf-8'))
    if manifest['version'] != '0.3.0':
        raise RuntimeError('M2 packaging requires version 0.3.0')
    files = [ROOT / item for item in ('plugin.yaml', '__init__.py', 'pyproject.toml', 'README.md', 'CHANGELOG.md')]
    for directory in ('dashboard', 'backend', 'docs'):
        files.extend(sorted(path for path in (ROOT / directory).rglob('*') if path.is_file() and '__pycache__' not in path.parts))
    for key in ('entry', 'css', 'api'):
        if not (ROOT / 'dashboard' / manifest[key]).is_file():
            raise FileNotFoundError(manifest[key])
    if any(path.suffix in ('.sqlite3', '.db', '.pyc') for path in files):
        raise RuntimeError('Runtime package must not contain local state or bytecode')
    output = ROOT / 'build/hermes-usage-manager-0.3.0-m2.zip'
    output.parent.mkdir(exist_ok=True)
    with ZipFile(output, 'w', ZIP_DEFLATED) as archive:
        for path in files:
            archive.write(path, f'hermes-usage-manager/{path.relative_to(ROOT).as_posix()}')
    print(f'M2 test package: {output}')


if __name__ == '__main__':
    main()
