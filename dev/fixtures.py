"""Deterministic fictional M1 fixtures, never imported by production."""

from datetime import datetime, timedelta, timezone


def make_state():
    departments = [{"id": f"d{index}", "name": name} for index, name in enumerate(["研发部", "产品部", "运营部"], 1)]
    users = [{"id": f"u{index}", "name": name, "external_id": f"mock_open_{index:04}",
              "department_id": f"d{(index - 1) % 3 + 1}", "profile": f"profile-{(index - 1) % 3 + 1}"}
             for index, name in enumerate(["林一", "沈二", "顾三", "陆四", "许五", "苏六", "叶七", "方八", "程九", "唐十", "周十一", "匿名用户"], 1)]
    models = [("gpt-5", "OpenAI"), ("claude-sonnet-4", "Anthropic"), ("gemini-2.5-pro", "Google"), ("deepseek-chat", "DeepSeek"), ("qwen3-235b", "阿里云"), ("unpriced-demo", "MockProvider")]
    tool_names = ["商品详情", "销售趋势", "评价查询", "关键词检索", "类目排行", "库存查询", "价格历史", "竞品对比", "品牌分析", "流量统计", "转化分析", "市场概况", "活动查询", "订单摘要", "数据导出"]
    anchor = datetime(2026, 10, 15, tzinfo=timezone(timedelta(hours=8)))
    requests, tools, sessions = [], [], []
    for day in range(30):
        for index in range(36):
            serial = day * 36 + index
            user = users[(index + day) % (6 + day % 7)]
            model, provider = models[(index + day) % len(models)]
            failed = serial % 17 == 0
            cost = None if failed or model in ("qwen3-235b", "unpriced-demo") else round((1000 + serial * 17 % 9000) / 1_000_000, 6)
            occurred = anchor - timedelta(days=day) + timedelta(hours=8, minutes=index * 13)
            session_id = f"session-{day:02}-{index:02}"
            requests.append({"id": f"request-{serial:04}", "time": occurred.isoformat(), "department_id": user["department_id"],
                             "user_id": user["id"], "model": model, "provider": provider, "session_id": session_id,
                             "status": "failed" if failed else "success", "profile": user["profile"],
                             "input": None if failed else 4000 + serial * 37 % 12000,
                             "cached": None if failed or serial % 11 == 0 else 1000 + serial * 19 % 5000,
                             "output": None if failed else 800 + serial * 13 % 4000, "duration_ms": 650 + serial * 71 % 9000,
                             "cost": cost, "input_cost": None if cost is None else cost * 0.6,
                             "cached_cost": None if cost is None else cost * 0.1, "output_cost": None if cost is None else cost * 0.3})
            for tool_index in range(8 if serial == 35 else 1 + serial % 3):
                tool = (serial + tool_index) % 15
                tools.append({"id": f"tool-call-{serial}-{tool_index}", "session_id": session_id, "time": occurred.isoformat(),
                              "tool_id": f"tool-{tool}", "name": tool_names[tool], "server_id": ["catalog", "insights"][tool % 2],
                              "department_id": user["department_id"], "user_id": user["id"], "failed": tool_index == 6 if serial == 35 else serial % 13 == 0, "duration_ms": 100 + serial % 850})
            sessions.append({"id": session_id, "time": occurred.isoformat(), "department_id": user["department_id"], "user_id": user["id"], "profile": user["profile"], "platform": "飞书"})
    prices = [{"id": f"price-{index}", "provider": provider, "model": model, "input": 0.5 + index, "cached": 0.1 + index / 10,
               "output": 2.0 + index, "valid_from": "2026-10-01", "valid_to": "2026-10-15", "enabled": True} for index, (model, provider) in enumerate(models[:5])]
    return {"departments": departments, "users": users, "requests": requests, "tools": tools, "sessions": sessions, "prices": prices}
