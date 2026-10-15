"""Persistent SQLite development host for the same production router."""

import os
import tempfile
from functools import lru_cache
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from dashboard.plugin_api import api
from dev.preview_api import scenario_middleware
from dev.seed_sqlite import mock_runtime, Principal, Store

ROOT = Path(__file__).resolve().parents[1]
default = Path(os.environ.get('LOCALAPPDATA', str(Path.home() / '.local/share'))) / 'hermes-usage-manager-dev' / 'm2-mock.sqlite3'
runtime = mock_runtime(os.environ.get('HUM_MOCK_DB_PATH', str(default)))
app = FastAPI(title='Hermes Usage Manager M2 SQLite Mock Host')
app.state.hum_runtime = runtime
app.state.preview = {}
app.middleware('http')(scenario_middleware)
empty_directory = tempfile.TemporaryDirectory(prefix='hum-empty-')
empty_runtime = api.Runtime(Store(Path(empty_directory.name) / 'empty.sqlite3', 'mock'), '2026-10-15')


@lru_cache(maxsize=64)
def test_runtime(identifier):
    import hashlib
    return mock_runtime(Path(empty_directory.name) / (hashlib.sha256(identifier.encode()).hexdigest() + '.sqlite3'))


def selected_runtime(request: Request):
    if request.headers.get('x-hum-mock-scenario') == 'empty':
        return empty_runtime
    if os.environ.get('HUM_MOCK_TESTING') == '1' and request.headers.get('x-hum-test-case'):
        return test_runtime(request.headers['x-hum-test-case'])
    return runtime


app.dependency_overrides[api.get_runtime] = selected_runtime
app.dependency_overrides[api.data_source] = lambda: 'mock'


def principal(request: Request):
    role = request.headers.get('x-hum-mock-role', 'admin')
    return Principal('mock-' + role, role, department_id='d1' if role == 'department' else None)


app.dependency_overrides[api.get_principal] = principal
app.include_router(api.router, prefix='/api/plugins/hermes-usage-manager')
app.mount('/dashboard-plugins/hermes-usage-manager', StaticFiles(directory=ROOT / 'dashboard'))
app.mount('/mock-assets', StaticFiles(directory=ROOT / 'frontend/.mock-dist', check_dir=False))


@app.get('/')
def index():
    return FileResponse(ROOT / 'frontend/mock/index.html')
