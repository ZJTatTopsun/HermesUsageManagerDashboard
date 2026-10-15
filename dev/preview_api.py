"""M1 memory-only Mock API. Hermes never imports or mounts this module."""

import asyncio
from collections import defaultdict
from datetime import date, timedelta
from typing import Literal
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/plugins/hermes-usage-manager")


def state(request):
    return request.scope.get("hum_empty_state", request.app.state.preview)


def authorize(request, write=False, audit=False):
    current = request.headers.get("x-hum-mock-role", "admin")
    if (write and current != "admin") or (audit and current not in ("admin", "auditor")):
        raise HTTPException(403, "模拟角色无权访问")


def envelope(data, **extra):
    return {"data": data, "meta": {"data_source": "mock", "tz": "Asia/Shanghai", **extra}}


@router.get("/filters")
def filters(request: Request):
    data = state(request)
    departments = [item for item in data["departments"] if request.headers.get("x-hum-mock-role") != "department" or item["id"] == "d1"]
    return envelope({"departments": departments, "users": [item for item in data["users"] if item["department_id"] in {entry["id"] for entry in departments}],
                     "servers": [{"id": "catalog", "name": "商品服务"}, {"id": "insights", "name": "数据洞察"}], "anchor": "2026-10-15"})


def selected(request, records, start, end, department_id, user_id):
    return [item for item in records if str(start) <= item["time"][:10] < str(end)
            and (not department_id or item["department_id"] == department_id) and (not user_id or item["user_id"] == user_id)
            and (request.headers.get("x-hum-mock-role") != "department" or item["department_id"] == "d1")]


@router.get("/preview/analytics")
def analytics(request: Request, start: date, end: date, department_id: str = "", user_id: str = "", server_id: str = ""):
    if not 0 < (end - start).days <= 366:
        raise HTTPException(422, "日期范围须为 1–366 天")
    data = state(request)
    rows = selected(request, data["requests"], start, end, department_id, user_id)
    calls = [item for item in selected(request, data["tools"], start, end, department_id, user_id) if not server_id or item["server_id"] == server_id]
    groups = {key: defaultdict(lambda: [0, 0.0, 0, 0, 0]) for key in ("department", "model", "provider", "user")}
    names = {item["id"]: item["name"] for item in data["departments"] + data["users"]}
    trend = []
    for offset in range((end - start).days):
        day = str(start + timedelta(days=offset))
        daily = [item for item in rows if item["time"][:10] == day]
        trend.append({"day": day, **{key: sum(item[key] or 0 for item in daily) for key in ("input", "cached", "output")},
                      "active": len({item["user_id"] for item in daily}), "calls": sum(item["time"][:10] == day for item in calls)})
    for item in rows:
        for dimension, key in [("department", item["department_id"]), ("user", item["user_id"]), ("model", item["model"]), ("provider", item["provider"])]:
            values = groups[dimension][key]
            values[0] += sum(item[field] or 0 for field in ("input", "cached", "output"))
            values[1] += item["cost"] or 0
            for position, field in enumerate(("input", "cached", "output"), 2):
                values[position] += item[field] or 0
    distributions = {dimension: [{"id": key, "name": names.get(key, key), "tokens": values[0], "cost": round(values[1], 6),
                                  "input": values[2], "cached": values[3], "output": values[4]} for key, values in grouped.items()] for dimension, grouped in groups.items()}
    tools = []
    for tool_id in sorted({item["tool_id"] for item in calls}):
        grouped = [item for item in calls if item["tool_id"] == tool_id]
        tools.append({"id": tool_id, "name": grouped[0]["name"], "server_id": grouped[0]["server_id"], "calls": len(grouped),
                      "failed": sum(item["failed"] for item in grouped), "duration_ms": round(sum(item["duration_ms"] for item in grouped) / len(grouped))})
    return envelope({"kpis": {**{key: sum(item[key] or 0 for item in rows) for key in ("input", "cached", "output")},
                              **{key: round(sum(item[key] or 0 for item in rows), 8) for key in ("input_cost", "cached_cost", "output_cost")},
                              "cost": round(sum(item["cost"] or 0 for item in rows), 6), "active": len({item["user_id"] for item in rows}),
                              "unknown_cost": sum(item["cost"] is None for item in rows), "unknown_cache": sum(item["cached"] is None for item in rows),
                              "primary_model": max(distributions["model"], key=lambda item: item["tokens"])["name"] if rows else None},
                     "trend": trend, "distributions": distributions, "tools": sorted(tools, key=lambda item: -item["calls"]), "count": len(rows)})


@router.get("/requests")
@router.get("/sessions")
def records(request: Request, start: date, end: date, department_id: str = "", user_id: str = "", page: int = Query(1, ge=1),
            page_size: int = Query(20, ge=1, le=100), sort: Literal["time", "input", "output"] = "time", order: Literal["asc", "desc"] = "desc", search: str = ""):
    if not 0 < (end - start).days <= 366:
        raise HTTPException(422, "日期范围须为 1–366 天")
    data = state(request)
    is_sessions = request.url.path.endswith("sessions")
    if is_sessions:
        authorize(request, audit=True)
    rows = [dict(item) for item in selected(request, data["sessions" if is_sessions else "requests"], start, end, department_id, user_id)
            if search.casefold() in f"{item['id']} {item.get('model', '')} {item.get('provider', '')}".casefold()]
    if is_sessions:
        by_session = {item["session_id"]: item for item in data["requests"]}
        counts = defaultdict(int)
        for call in data["tools"]:
            counts[call["session_id"]] += 1
        for item in rows:
            item.update({field: by_session[item["id"]][field] for field in ("input", "cached", "output")})
            item["mcp_calls"] = counts[item["id"]]
    rows.sort(key=lambda item: (item.get(sort) is not None, item.get(sort) or 0), reverse=order == "desc")
    return envelope(rows[(page - 1) * page_size:page * page_size], total=len(rows), page=page, page_size=page_size)


@router.get("/sessions/{session_id}/timeline")
def timeline(session_id: str, request: Request):
    authorize(request, audit=True)
    session = next((item for item in state(request)["sessions"] if item["id"] == session_id), None)
    if not session:
        raise HTTPException(404, "会话不存在")
    calls = [item for item in state(request)["tools"] if item["session_id"] == session_id]
    return envelope({"session": session, "messages": [
        {"id": "message-1", "kind": "user", "text": "请分析示例商品近期趋势。", "tools": []},
        {"id": "message-2", "kind": "assistant", "text": "我会先检索商品和市场数据。", "tools": []},
        {"id": "message-3", "kind": "tools", "text": "连续工具调用", "tools": [
            {"id": call["id"], "name": call["name"], "success": not call["failed"],
             "args": '{"product_id":"MOCK-001"}', "result": "模拟结果：虚构商品趋势摘要。"} for call in calls]},
        {"id": "message-4", "kind": "assistant", "text": "示例数据呈现平稳增长。以上为模拟会话。", "tools": []}]})


@router.get("/people/users")
@router.get("/people/departments")
@router.get("/models/prices")
def settings(request: Request):
    authorize(request, write=True)
    return envelope(state(request)[request.url.path.split("/")[-1]])


class DepartmentBody(BaseModel):
    name: str = Field(min_length=1, max_length=50)


@router.post("/people/departments")
@router.patch("/people/departments/{department_id}")
def save_department(body: DepartmentBody, request: Request, department_id: str = ""):
    authorize(request, write=True)
    data = state(request)
    name = body.name.strip()
    if not name or any(item["name"] == name and item["id"] != department_id for item in data["departments"]):
        raise HTTPException(422, "部门名称为空或已存在")
    if department_id:
        item = next((item for item in data["departments"] if item["id"] == department_id), None)
        if not item:
            raise HTTPException(404, "部门不存在")
        item["name"] = name
    else:
        item = {"id": f"d-{uuid4().hex[:8]}", "name": name}
        data["departments"].append(item)
    return envelope(item)


@router.delete("/people/departments/{department_id}")
def delete_department(department_id: str, request: Request):
    authorize(request, write=True)
    data = state(request)
    if any(item["department_id"] == department_id for item in data["users"]):
        raise HTTPException(409, "部门内仍有成员，请先迁移成员")
    data["departments"] = [item for item in data["departments"] if item["id"] != department_id]
    return envelope({"ok": True})


class MoveBody(BaseModel):
    user_ids: list[str] = Field(min_length=1, max_length=100)
    department_id: str


@router.post("/people/assignments/move")
def move(body: MoveBody, request: Request):
    authorize(request, write=True)
    data = state(request)
    if body.department_id not in {item["id"] for item in data["departments"]} or not set(body.user_ids) <= {item["id"] for item in data["users"]}:
        raise HTTPException(422, "用户或目标部门不存在")
    for item in data["users"]:
        if item["id"] in body.user_ids:
            item["department_id"] = body.department_id
    return envelope({"ok": True})


class UserBody(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    external_id: str = Field(min_length=1, max_length=100)
    department_id: str
    profile: str = Field(default="profile-1", max_length=50)


@router.post("/people/users")
@router.patch("/people/users/{user_id}")
def save_user(body: UserBody, request: Request, user_id: str = ""):
    authorize(request, write=True)
    data = state(request)
    if body.department_id not in {item["id"] for item in data["departments"]} or not body.name.strip() or not body.external_id.strip():
        raise HTTPException(422, "用户信息不完整")
    if any(item["external_id"] == body.external_id and item["id"] != user_id for item in data["users"]):
        raise HTTPException(409, "外部身份已存在")
    existing = next((item for item in data["users"] if item["id"] == user_id), None)
    if user_id and not existing:
        raise HTTPException(404, "用户不存在")
    item = {"id": user_id or f"u-{uuid4().hex[:8]}", **body.model_dump()}
    if existing:
        existing.update(item)
    else:
        data["users"].append(item)
    return envelope(item)


class PriceBody(BaseModel):
    provider: str = Field(min_length=1, max_length=100)
    model: str = Field(min_length=1, max_length=100)
    input: float = Field(ge=0, allow_inf_nan=False)
    cached: float = Field(ge=0, allow_inf_nan=False)
    output: float = Field(ge=0, allow_inf_nan=False)
    valid_from: date
    valid_to: date | None = None
    enabled: bool = True


@router.post("/models/prices")
@router.patch("/models/prices/{price_id}")
def price(body: PriceBody, request: Request, price_id: str = ""):
    authorize(request, write=True)
    data = state(request)
    if body.valid_to is not None and body.valid_to < body.valid_from:
        raise HTTPException(422, "生效结束日期不能早于开始日期")
    if not body.model.strip() or not body.provider.strip():
        raise HTTPException(422, "提供商和模型不能为空")
    existing = next((item for item in data["prices"] if item["id"] == price_id), None)
    if price_id and existing is None:
        raise HTTPException(404, "价格配置不存在")
    for item in data["prices"]:
        if item["id"] == price_id or not item["enabled"] or not body.enabled or item["model"] != body.model or item["provider"] != body.provider:
            continue
        if str(body.valid_from) <= (item.get("valid_to") or "9999-12-31") and item["valid_from"] <= str(body.valid_to or date.max):
            raise HTTPException(409, "同一提供商和模型的启用价格区间不能重叠（起止日期均包含）")
    item = {"id": price_id or f"price-{uuid4().hex[:8]}", **body.model_dump(mode="json")}
    if existing is not None:
        existing.update(item)
    else:
        data["prices"].append(item)
    return envelope(item)


@router.get("/models/unpriced")
def unpriced(request: Request):
    authorize(request, write=True)
    data = state(request)
    missing = defaultdict(lambda: defaultdict(int))
    for item in data["requests"]:
        day = item["time"][:10]
        covered = any(price["enabled"] and price["provider"] == item["provider"] and price["model"] == item["model"]
                      and price["valid_from"] <= day <= (price.get("valid_to") or "9999-12-31") for price in data["prices"])
        if not covered:
            missing[(item["provider"], item["model"])][day] += 1
    pending = []
    for (provider, model), days in sorted(missing.items()):
        prices = [price for price in data["prices"] if price["provider"] == provider and price["model"] == model]
        reason = "未设置价格" if not prices else "日期未覆盖" if any(price["enabled"] for price in prices) else "价格已停用"
        for day, count in sorted(days.items()):
            if pending and pending[-1]["provider"] == provider and pending[-1]["model"] == model and date.fromisoformat(day) == date.fromisoformat(pending[-1]["valid_to"]) + timedelta(days=1):
                pending[-1]["valid_to"] = day
                pending[-1]["request_count"] += count
            else:
                pending.append({"id": f"{len(provider)}:{provider}{len(model)}:{model}:{day}", "provider": provider, "model": model,
                                "valid_from": day, "valid_to": day, "request_count": count, "reason": reason})
    return envelope(pending)


async def scenario_middleware(request: Request, call_next):
    if request.url.path.startswith("/api/plugins/") and not request.url.path.endswith("/health"):
        scenario = request.headers.get("x-hum-mock-scenario", "normal")
        if scenario in ("error", "forbidden"):
            from fastapi.responses import JSONResponse
            return JSONResponse({"detail": "模拟服务暂时不可用" if scenario == "error" else "模拟访问被拒绝"}, status_code=503 if scenario == "error" else 403)
        if scenario == "slow":
            await asyncio.sleep(1.5)
        if scenario == "empty" and request.method == "GET":
            request.scope["hum_empty_state"] = {**request.app.state.preview, "requests": [], "sessions": [], "tools": []}
    return await call_next(request)
