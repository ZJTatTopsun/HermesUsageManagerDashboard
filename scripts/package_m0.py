"""Package only the M0 Hermes runtime files, including prebuilt browser assets."""

import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path(__file__).resolve().parents[1]
FILES = (
    "plugin.yaml", "__init__.py", "pyproject.toml", "dashboard/manifest.json",
    "dashboard/plugin_api.py", "dashboard/dist/index.js", "dashboard/dist/style.css",
    "docs/compatibility.md", "docs/development.md", "docs/m0-report.md", "CHANGELOG.md",
)


def main():
    manifest = json.loads((ROOT / "dashboard/manifest.json").read_text(encoding="utf-8"))
    if manifest["version"] != "0.1.0":
        raise SystemExit("Historical M0 packer: current M1 code must use scripts/package_m1.py")
    for filename in FILES:
        if not (ROOT / filename).is_file():
            raise FileNotFoundError(filename)
    output = ROOT / "build" / f"{manifest['name']}-{manifest['version']}-m0.zip"
    output.parent.mkdir(exist_ok=True)
    with ZipFile(output, "w", ZIP_DEFLATED) as archive:
        for filename in FILES:
            archive.write(ROOT / filename, f"{manifest['name']}/{filename}")
    print(f"M0 POC package: {output}")


if __name__ == "__main__":
    main()
