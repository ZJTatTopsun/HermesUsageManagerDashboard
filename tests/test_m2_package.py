import importlib.util
import subprocess
import sys
from pathlib import Path
from zipfile import ZipFile

from fastapi import FastAPI
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]


def test_archive_is_native_self_contained_and_loads_without_checkout(tmp_path, monkeypatch):
    subprocess.run([sys.executable, str(ROOT / 'scripts/package_release.py')], cwd=ROOT, check=True, capture_output=True, text=True)
    archive_path = ROOT / 'build/hermes-usage-manager-0.6.0.zip'
    with ZipFile(archive_path) as archive:
        names = archive.namelist()
        assert 'hermes-usage-manager/backend/migrations/0004_membership_intervals.sql' in names
        assert 'hermes-usage-manager/backend/migrations/0005_collection.sql' in names
        assert 'hermes-usage-manager/backend/collector.py' in names
        assert 'hermes-usage-manager/backend/adapters/session_content.py' in names
        assert 'hermes-usage-manager/dashboard/dist/index.js' in names
        assert 'hermes-usage-manager/dashboard/dist/THIRD_PARTY_NOTICES.txt' in names
        assert 'hermes-usage-manager/standalone.py' in names
        assert 'hermes-usage-manager/standalone/dist/index.html' in names
        assert 'hermes-usage-manager/standalone/dist/THIRD_PARTY_NOTICES.txt' in names
        assert not any('/dev/' in name or 'node_modules' in name or name.endswith(('.db', '.sqlite3', '.pyc')) for name in names)
        archive.extractall(tmp_path / 'install')
    entry = tmp_path / 'install/hermes-usage-manager/dashboard/plugin_api.py'
    spec = importlib.util.spec_from_file_location('m2_packaged_native_entry', entry)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setenv('USAGE_MANAGER_DB_PATH', str(tmp_path / 'data/usage.sqlite3'))
    monkeypatch.delenv('USAGE_MANAGER_TRUST_DASHBOARD_ADMIN', raising=False)
    application = FastAPI()
    application.include_router(module.router, prefix='/api/plugins/hermes-usage-manager')
    session = TestClient(application)
    health = session.get('/api/plugins/hermes-usage-manager/health').json()
    assert health['data_source'] == 'live'
    assert health['capabilities']['storage'] == 'ready'
    assert health['capabilities']['collection'] == 'unavailable'
    assert session.get('/api/plugins/hermes-usage-manager/people/users').status_code == 403
    assert session.get('/api/plugins/hermes-usage-manager/preview/analytics').status_code == 404
    standalone = __import__('importlib').import_module(module.api.__package__ + '.standalone')
    credentials = tmp_path / 'private/auth.json'
    standalone.initialize_auth(credentials, 'packaged-test-password-2026')
    with TestClient(standalone.create_app(credentials, tmp_path / 'data/usage.sqlite3', 'http://testserver', True)) as independent:
        assert independent.get('/').status_code == 200
        assert independent.get('/api/plugins/hermes-usage-manager/health').status_code == 401
        result = independent.post('/api/auth/login', headers={'Origin': 'http://testserver'}, json={'password': 'packaged-test-password-2026'})
        assert result.status_code == 200
        assert independent.get('/api/plugins/hermes-usage-manager/health').json()['version'] == '0.6.0'
