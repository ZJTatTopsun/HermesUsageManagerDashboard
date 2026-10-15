# M2 本地开发（0.3.0）

当前实现 SQLite/正式 API/统计与持久化 Mock UI。真实 Hooks 与会话正文留在 M3；尚未更新远端 Hermes。产品契约见 `m2-design.md`，结果见 `m2-report.md`。

## 启动与验证

Python >=3.11、Node >=20、pnpm。以下只运行本机 loopback Mock Host，不连接 Hermes 或生产服务器。

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
$env:HUM_PYTHON=(Resolve-Path .venv/Scripts/python.exe).Path
cd frontend
pnpm install --frozen-lockfile
pnpm run typecheck
pnpm run lint
pnpm run build:plugin
pnpm test
pnpm exec playwright install chromium
pnpm run test:e2e
pnpm run dev
```

浏览器访问 `http://127.0.0.1:8765/`。源码变更需要重启，启动时重新构建。Windows 的 python 若是 Store 别名，用 HUM_PYTHON 指向真实解释器。已有服务器占用8765时先停止自己的旧开发进程再运行 Playwright；测试不会复用现有服务器。

在另一个已激活 venv 的终端、仓库根目录：

```powershell
python -m pytest -q
python scripts/replay_fixture.py --repetitions 3
python scripts/package_m2.py
```

当前环境没有全局 npm；可用 `C:\Users\it\.cache\codex-runtimes\codex-primary-runtime\dependencies\bin\fallback\pnpm.cmd`，也可直接调用 `frontend/node_modules/.bin/tsc.cmd` 等已安装工具。

## Mock 数据持久化

- 默认 Windows 数据路径：`%LOCALAPPDATA%/hermes-usage-manager-dev/m2-mock.sqlite3`；其他平台是 `~/.local/share/hermes-usage-manager-dev/m2-mock.sqlite3`。
- `HUM_MOCK_DB_PATH` 可设置另一条外部绝对路径。首次装入虚构 fixture（3 Profile、12用户、1080请求）；后续重启不重灌，不丢弃配置修改。
- 测试使用系统临时目录内的独立 DB，浏览器各测试注入 test-case header，在仅测试进程的 HUM_MOCK_TESTING=1 模式隔离。它不是生产身份机制，生产包不包含 dev 和 fixtures。
- 顶栏可切换 normal/empty/slow/error/forbidden 与模拟角色。empty 使用另一只空 Mock DB，不删除持久库。
- 如需全新演示，停止服务，设置新的 HUM_MOCK_DB_PATH；不要为了升级删除原数据库。
- M1 截图仍生成在 `build/m1/`（回归用），M2 新截图在 `build/m2/`；不要将标记 Live 的契约模拟截图视为真实 Hermes 验证。

## 原生运行

发行包 `build/hermes-usage-manager-0.3.0-m2.zip` 包含原生声明、Dashboard router、backend 与 SQL 迁移、IIFE/CSS/字体/许可，无 Mock 或 React/ReactDOM 运行时。运行不需要 Node。安装测试须按 `compatibility.md`，不自动上传、覆盖旧插件或连接生产。

真实 DB 使用 `USAGE_MANAGER_DB_PATH`，否则尝试 Hermes 官方源码 helper。它与开发专用 HUM_MOCK_DB_PATH 不同。默认业务认证拒绝访问；受控测试才设置 `USAGE_MANAGER_TRUST_DASHBOARD_ADMIN=1`。缺少宿主内部认证函数时503，不降级。Hermes 进程环境须具备 FastAPI 与 tzdata；本仓库 `.venv` 不等于远端 Hermes 解释器。

M2 storage ready 仅证明 SQLite 可用；collection 仍 unavailable。原生 pre_llm_call Hook 仍是无副作用回调，不会创建真实请求记录。真实正文返回不可用并审计，不读取未经验证的 Hermes 私有表。
