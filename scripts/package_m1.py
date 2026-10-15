"""Build an M1 runtime review archive without development Mock code."""

import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path(__file__).resolve().parents[1]


def main():
    manifest = json.loads((ROOT / "dashboard/manifest.json").read_text(encoding="utf-8"))
    if manifest['version'] != '0.2.0':
        raise RuntimeError('M1 packaging requires version 0.2.0; use package_m2.py for M2')
    files = [ROOT / item for item in ("plugin.yaml", "__init__.py", "pyproject.toml", "CHANGELOG.md", "README.md")]
    files += sorted(path for path in (ROOT / "dashboard").rglob("*") if path.is_file() and "__pycache__" not in path.parts)
    files += sorted((ROOT / "docs").glob("*.md"))
    output = ROOT / "build" / f"hermes-usage-manager-{manifest['version']}-m1.zip"
    output.parent.mkdir(exist_ok=True)
    for path in files:
        if not path.is_file():
            raise FileNotFoundError(path)
    for key in ("entry", "css", "api"):
        if not (ROOT / "dashboard" / manifest[key]).is_file():
            raise FileNotFoundError(manifest[key])
    with ZipFile(output, "w", ZIP_DEFLATED) as archive:
        for path in files:
            archive.write(path, f"hermes-usage-manager/{path.relative_to(ROOT).as_posix()}")
    print(f"M1 review package: {output}")


if __name__ == "__main__":
    main()
