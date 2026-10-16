# M3 本地开发（0.4.1）

当前包面向用户v0.21.0，声明/注册五个基础Hook；辅助调用Hook缺失，质量面板明确标记覆盖不完整。会话方法兼容用户提供的旧签名；旧六Hook实现说明见历史记录，实机doctor/真实事件仍待验证。

当前在M2基础上实现原生Hook采集与会话读取适配，真实Hermes验收尚未完成；未更新远端。产品契约见 `m2-design.md`、`m3-design.md`，结果见 `m3-report.md`。六个观察Hook的callback通过本地源码形状重播，不等于已运行真实Hermes。

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
python scripts/replay_hooks.py
python scripts/package_m3.py
```

当前环境没有全局 npm；可用 `C:\Users\it\.cache\codex-runtimes\codex-primary-runtime\dependencies\bin\fallback\pnpm.cmd`，也可直接调用 `frontend/node_modules/.bin/tsc.cmd` 等已安装工具。

## Mock 数据持久化

- 默认 Windows 数据路径：`%LOCALAPPDATA%/hermes-usage-manager-dev/m2-mock.sqlite3`；其他平台是 `~/.local/share/hermes-usage-manager-dev/m2-mock.sqlite3`。
- `HUM_MOCK_DB_PATH` 可设置另一条外部绝对路径。首次装入虚构 fixture（3 Profile、12用户、1080请求）；后续重启不重灌，不丢弃配置修改。
- 测试使用系统临时目录内的独立 DB，浏览器各测试注入 test-case header，在仅测试进程的 HUM_MOCK_TESTING=1 模式隔离。它不是生产身份机制，生产包不包含 dev 和 fixtures。
- 顶栏可切换 normal/empty/slow/error/forbidden 与模拟角色。empty 使用另一只空 Mock DB，不删除持久库。
- 如需全新演示，停止服务，设置新的 HUM_MOCK_DB_PATH；不要为了升级删除原数据库。
- M1/M2 截图仍生成在 `build/m1/`、`build/m2/`（回归用），M3新截图在 `build/m3/`；不要将标记Live的契约模拟截图视为真实Hermes验证。

## 原生运行

测试发行包 `build/hermes-usage-manager-0.4.1-m3.zip` 包含原生声明、Dashboard router、backend与5步SQL迁移、IIFE/CSS/字体/许可，无Mock或React/ReactDOM运行时。运行不需要Node。安装测试须按 `m3-testing.md`，不自动上传、覆盖旧插件或连接生产。

真实 DB 使用 `USAGE_MANAGER_DB_PATH`，否则尝试 Hermes 官方源码 helper。它与开发专用 HUM_MOCK_DB_PATH 不同。默认业务认证拒绝访问；受控测试才设置 `USAGE_MANAGER_TRUST_DASHBOARD_ADMIN=1`。缺少宿主内部认证函数时503，不降级。Hermes 进程环境须具备 FastAPI 与 tzdata；本仓库 `.venv` 不等于远端 Hermes 解释器。

storage ready仅证明SQLite可用。`USAGE_MANAGER_COLLECTION=1`才启动元数据采集；不启用则六个回调均无副作用。共享本机DB可设置相同的外部USAGE_MANAGER_DB_PATH和稳定USAGE_MANAGER_INSTANCE_ID，Profile身份仍独立，不能把多个Profile强制设成同一个USAGE_MANAGER_PROFILE_ID。`USAGE_MANAGER_EXPECTED_PROFILES`可显式列出需要监测的Profile，否则只知道库内已见Profile，不能声称完整覆盖。

`USAGE_MANAGER_SESSION_CONTENT=1`另行启用只读正文，必须设置明确的 `USAGE_MANAGER_SESSION_HOMES` 来源白名单；默认拒绝。工具结果再由 `USAGE_MANAGER_TOOL_CONTENT=1`单独控制，参数不读取。管理员正文权限独立于审计员元数据权限。所有选项、隐私限制与真实验收步骤见 `m3-design.md`、`m3-testing.md`。
