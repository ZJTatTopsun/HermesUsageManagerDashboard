import importlib.util
import json
import sys
from pathlib import Path

import yaml
from fastapi import FastAPI
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]


def load_file(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def test_router_loads_without_package_context_like_hermes():
    module = load_file("hermes_dashboard_plugin_hermes-usage-manager", ROOT / "dashboard/plugin_api.py")
    app = FastAPI()
    app.include_router(module.router, prefix="/api/plugins/hermes-usage-manager")
    client = TestClient(app)
    response = client.get("/api/plugins/hermes-usage-manager/health")
    assert response.status_code == 200
    assert response.json() == {
        "status": "ok", "plugin": "hermes-usage-manager", "version": "0.6.0",
        "milestone": "M4", "data_source": "live",
        "capabilities": {"storage": "unavailable", "collection": "unavailable", "hermes_runtime": "unverified", "business_api": True},
    }
    assert client.get("/health").status_code == 404


def test_mock_overrides_only_its_own_router_dependency():
    from dev.mock_api import app

    client = TestClient(app)
    assert client.get("/api/plugins/hermes-usage-manager/health").json()["data_source"] == "mock"
    assert client.get("/").status_code == 200


def test_register_subscribes_only_to_observer_and_ignores_sensitive_payload():
    module = load_file("usage_manager_poc", ROOT / "__init__.py")
    registered = []

    class Context:
        def register_hook(self, name, callback):
            registered.append((name, callback))

    module.register(Context())
    assert [name for name, _ in registered] == ['pre_llm_call', 'post_api_request', 'api_request_error', 'post_tool_call', 'on_session_end']
    assert registered[0][1](session_id="fixture", user_message="not retained", future_field=True) is None


def test_manifest_identity_and_prebuilt_assets():
    manifest = json.loads((ROOT / "dashboard/manifest.json").read_text(encoding="utf-8"))
    plugin = yaml.safe_load((ROOT / "plugin.yaml").read_text(encoding="utf-8"))
    assert manifest["name"] == plugin["name"] == "hermes-usage-manager"
    assert manifest["version"] == plugin["version"] == "0.6.0"
    assert plugin["provides_hooks"] == ['pre_llm_call', 'post_api_request', 'api_request_error', 'post_tool_call', 'on_session_end']
    assert manifest["tab"]["path"] == "/usage-manager"
    for key in ("entry", "css", "api"):
        assert (ROOT / "dashboard" / manifest[key]).is_file()
