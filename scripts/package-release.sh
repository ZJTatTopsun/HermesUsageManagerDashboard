#!/usr/bin/env bash
set -euo pipefail
root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$root/frontend"
pnpm install --frozen-lockfile
pnpm run typecheck
pnpm run lint
pnpm run build:plugin
pnpm run build:standalone
pnpm test
cd "$root"
"${PYTHON:-python3}" scripts/package_release.py "$@"
"${PYTHON:-python3}" -m pytest -q
cd "$root/frontend"
pnpm run test:e2e
pnpm run test:standalone
