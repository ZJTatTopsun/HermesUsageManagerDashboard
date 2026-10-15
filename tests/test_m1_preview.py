import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from dashboard.plugin_api import router
from dev.fixtures import make_state
from dev.mock_api import app

PREFIX = "/api/plugins/hermes-usage-manager"
RANGE = {"start": "2026-10-09", "end": "2026-10-16"}


@pytest.fixture
def client():
    app.state.preview = make_state()
    with TestClient(app) as test_client:
        yield test_client


def test_preview_contract_and_filter_linkage(client):
    filters = client.get(f"{PREFIX}/filters").json()
    assert filters["meta"]["data_source"] == "mock"
    assert len(filters["data"]["users"]) == 12
    full = client.get(f"{PREFIX}/preview/analytics", params=RANGE).json()["data"]
    filtered = client.get(f"{PREFIX}/preview/analytics", params={**RANGE, "department_id": "d1"}).json()["data"]
    assert len(full["trend"]) == 7
    assert 0 < filtered["count"] < full["count"]
    assert {item["id"] for item in filtered["distributions"]["department"]} == {"d1"}
    assert full["kpis"]["unknown_cost"] > 0
    assert full["kpis"]["unknown_cache"] > 0


def test_server_filter_limits_mcp_rankings(client):
    payload = client.get(f"{PREFIX}/preview/analytics", params={**RANGE, "server_id": "catalog"}).json()["data"]
    assert payload["tools"]
    assert {tool["server_id"] for tool in payload["tools"]} == {"catalog"}


def test_pagination_sort_search_and_unknowns(client):
    first = client.get(f"{PREFIX}/requests", params={**RANGE, "page_size": 20}).json()
    second = client.get(f"{PREFIX}/requests", params={**RANGE, "page_size": 20, "page": 2}).json()
    assert len(first["data"]) == 20
    assert {row["id"] for row in first["data"]}.isdisjoint({row["id"] for row in second["data"]})
    assert first["meta"]["total"] == 252
    filtered = client.get(f"{PREFIX}/requests", params={**RANGE, "search": "gpt-5", "sort": "input", "order": "asc"}).json()["data"]
    assert filtered and all(item["model"] == "gpt-5" for item in filtered)
    all_rows = app.state.preview["requests"]
    assert any(item["status"] == "failed" and item["input"] is None for item in all_rows)
    assert client.get(f"{PREFIX}/requests", params={**RANGE, "page_size": 101}).status_code == 422
    assert client.get(f"{PREFIX}/preview/analytics", params={"start": "2026-10-16", "end": "2026-10-09"}).status_code == 422


def test_roles_are_enforced_by_mock_api_and_do_not_exist_in_live_router(client):
    headers = {"x-hum-mock-role": "department"}
    assert client.get(f"{PREFIX}/sessions", params=RANGE, headers=headers).status_code == 403
    assert client.post(f"{PREFIX}/people/departments", json={"name": "越权部门"}, headers=headers).status_code == 403
    rows = client.get(f"{PREFIX}/requests", params=RANGE, headers=headers).json()["data"]
    assert rows and all(item["department_id"] == "d1" for item in rows)
    live = FastAPI()
    live.include_router(router, prefix=PREFIX)
    assert TestClient(live).get(f"{PREFIX}/preview/analytics", params=RANGE).status_code == 404


def test_department_crud_move_preserves_history(client):
    assert client.delete(f"{PREFIX}/people/departments/d1").status_code == 409
    new = client.post(f"{PREFIX}/people/departments", json={"name": "模拟测试部"}).json()["data"]
    assert client.patch(f"{PREFIX}/people/departments/{new['id']}", json={"name": "模拟新部门"}).status_code == 200
    original = [item["department_id"] for item in app.state.preview["requests"] if item["user_id"] == "u1"]
    assert client.post(f"{PREFIX}/people/assignments/move", json={"user_ids": ["u1"], "department_id": new["id"]}).status_code == 200
    assert [item["department_id"] for item in app.state.preview["requests"] if item["user_id"] == "u1"] == original
    assert client.delete(f"{PREFIX}/people/departments/{new['id']}").status_code == 409
    assert client.post(f"{PREFIX}/people/assignments/move", json={"user_ids": ["u1"], "department_id": "d1"}).status_code == 200
    assert client.delete(f"{PREFIX}/people/departments/{new['id']}").status_code == 200


def test_user_and_price_validation_and_versioning(client):
    assert client.post(f"{PREFIX}/people/users", json={"name": "新映射", "external_id": "mock-new", "department_id": "d1"}).status_code == 200
    assert client.post(f"{PREFIX}/people/users", json={"name": "冲突", "external_id": "mock-new", "department_id": "d1"}).status_code == 409
    body = {"provider": "OpenAI", "model": "gpt-5", "input": 1, "cached": 0.1, "output": 2, "valid_from": "2026-10-16"}
    assert client.post(f"{PREFIX}/models/prices", json=body).status_code == 200
    prices = client.get(f"{PREFIX}/models/prices").json()["data"]
    assert len([item for item in prices if item["model"] == "gpt-5"]) == 2
    assert client.post(f"{PREFIX}/models/prices", json=body).status_code == 409
    assert client.post(f"{PREFIX}/models/prices", json={**body, "input": -1}).status_code == 422


def test_empty_error_and_timeline_contract(client):
    response = client.get(f"{PREFIX}/requests", params=RANGE, headers={"x-hum-mock-scenario": "empty"})
    assert response.json()["data"] == []
    assert client.get(f"{PREFIX}/filters", headers={"x-hum-mock-scenario": "error"}).status_code == 503
    response = client.get(f"{PREFIX}/sessions/session-00-35/timeline").json()
    group = next(item for item in response["data"]["messages"] if item["kind"] == "tools")
    assert len(group["tools"]) == 8
    assert sum(not item["success"] for item in group["tools"]) == 1


def test_price_ranges_detect_gaps_and_edit_inclusive_boundaries(client):
    source = app.state.preview["requests"][0]
    app.state.preview["requests"] = [{**source, "id": f"range-{day}", "provider": "RangeProvider", "model": "range-model", "time": f"2026-10-{day:02}T12:00:00+08:00"} for day in range(1, 7)]
    body = {"provider": "RangeProvider", "model": "range-model", "input": 1, "cached": 0.1, "output": 2, "valid_from": "2026-10-02", "valid_to": "2026-10-03"}
    saved = client.post(f"{PREFIX}/models/prices", json=body).json()["data"]
    missing = client.get(f"{PREFIX}/models/unpriced").json()["data"]
    assert [(item["valid_from"], item["valid_to"], item["request_count"]) for item in missing] == [("2026-10-01", "2026-10-01", 1), ("2026-10-04", "2026-10-06", 3)]
    assert all(item["reason"] == "日期未覆盖" for item in missing)
    edited = client.patch(f"{PREFIX}/models/prices/{saved['id']}", json={**body, "input": 3, "valid_to": "2026-10-04"})
    assert edited.status_code == 200
    assert edited.json()["data"]["id"] == saved["id"]
    assert edited.json()["data"]["input"] == 3
    missing = client.get(f"{PREFIX}/models/unpriced").json()["data"]
    assert missing[-1]["valid_from"] == "2026-10-05"
    assert client.post(f"{PREFIX}/models/prices", json={**body, "valid_from": "2026-10-04", "valid_to": "2026-10-05"}).status_code == 409
    assert client.post(f"{PREFIX}/models/prices", json={**body, "valid_from": "2026-10-05", "valid_to": None}).status_code == 200
    assert client.post(f"{PREFIX}/models/prices", json={**body, "valid_from": "2026-10-01", "valid_to": "2026-10-01"}).status_code == 200
    assert client.get(f"{PREFIX}/models/unpriced").json()["data"] == []
    assert client.patch(f"{PREFIX}/models/prices/{saved['id']}", json={**body, "valid_from": "2026-10-03", "valid_to": "2026-10-02"}).status_code == 422
    assert client.patch(f"{PREFIX}/models/prices/missing", json=body).status_code == 404


def test_unpriced_models_disabled_prices_and_provider_identity(client):
    source = app.state.preview["requests"][0]
    app.state.preview["requests"] = [{**source, "provider": "OtherProvider", "model": "gpt-5", "time": "2026-10-10T12:00:00+08:00"}]
    missing = client.get(f"{PREFIX}/models/unpriced").json()["data"]
    assert missing[0]["reason"] == "未设置价格"
    body = {"provider": "OtherProvider", "model": "gpt-5", "input": 0, "cached": 0, "output": 0, "valid_from": "2026-10-10", "valid_to": "2026-10-10", "enabled": False}
    saved = client.post(f"{PREFIX}/models/prices", json=body).json()["data"]
    assert client.get(f"{PREFIX}/models/unpriced").json()["data"][0]["reason"] == "价格已停用"
    assert client.patch(f"{PREFIX}/models/prices/{saved['id']}", json={**body, "enabled": True}).status_code == 200
    assert client.get(f"{PREFIX}/models/unpriced").json()["data"] == []
    assert client.get(f"{PREFIX}/models/unpriced", headers={"x-hum-mock-role": "department"}).status_code == 403
