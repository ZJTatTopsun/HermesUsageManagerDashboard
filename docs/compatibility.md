# Hermes Usage Manager 兼容性记录

## 当前 M2（0.3.0）

本机仍没有安装/运行 Hermes。M2 在 Windows 上用同一生产 router 的 SQLite Mock Host 验证；没有连接用户服务器。M0 v0.21.0 的截图确认不外推为 M2 的运行时兼容证明。当前 health=0.3.0/M2；storage 由实际数据库检查决定，collection=unavailable、hermes_runtime=unverified。

### 官方源码核对与版本风险

沿用只读官方源码基线 `525dbcad8d744710a43d01eb7366500e46eacbf4`，本阶段再次检查：

- `plugins/plugin_storage.py:27` 的 `plugin_data_dir(name)` 作为默认外部数据目录 helper；缺失时允许显式 USAGE_MANAGER_DB_PATH，不写源码目录。
- `hermes_cli/web_server.py:330` 的同步 `_require_token(request)` 为当前认证适配点。该名字带下划线，是版本相关内部接口，不视作稳定 SDK；用户 v0.21.0 是否相同尚未验证。
- Dashboard API 仍通过 manifest 的 api 文件导出 APIRouter；路径作用域 package loader 已通过解压后独立加载测试，无需修改 Hermes sys.path 或核心源码。
- 不使用 Hermes Desktop Plugin SDK。前端继续复用 Web Dashboard 的 React/fetchJSON/register，构建 AST+模块图检查无 React/ReactDOM。

默认不信任角色 header、查询参数或仅前端隐藏按钮。真实业务请求403 IDENTITY_UNAVAILABLE；测试管理员显式 opt-in 后仍必须经过宿主 token 校验。身份适配缺失返回503。真实部门/个人身份 Provider、隔离 Plugin Host、跨 Profile 共享数据库与会话读取 Adapter 均留待目标环境/M3验证。

### M2 本地验证

后端40项（包含迁移、重启持久化、价格修订冻结、缓存公式、缺失值、三次重播、角色越权、MCP分类、午夜/DST、CSV安全、独立发行包加载）、浏览器21项、IIFE3项通过；类型检查和 lint 通过。Windows 无法证明 Linux 文件权限或目标宿主兼容；没有宣称通过规模压测。完整命令/结果见 m2-report.md。

### 仅供独立测试 Hermes 的命令

不要在生产账号执行；不要直接覆盖用户已成功的 M0。以下用于**没有现有此插件的独立测试账号**。先由用户将 M2 zip 放到该账号当前目录，并为 HERMES_PYTHON 填入实际 Hermes 使用的解释器；缺依赖应停下确认安装到正确环境。

```bash
hermes --version
hermes plugins doctor --help
command -v hermes
"$HERMES_PYTHON" -c 'import fastapi, sqlite3; from zoneinfo import ZoneInfo; print(fastapi.__version__, sqlite3.sqlite_version, ZoneInfo("Asia/Shanghai"))'

(
set -eu
test -f ./hermes-usage-manager-0.3.0-m2.zip
test ! -e "$HOME/.hermes/plugins/hermes-usage-manager"
test ! -L "$HOME/.hermes/plugins/hermes-usage-manager"
mkdir -p "$HOME/.hermes/plugins"
"$HERMES_PYTHON" -m zipfile -e ./hermes-usage-manager-0.3.0-m2.zip "$HOME/.hermes/plugins"
hermes plugins doctor --ci "$HOME/.hermes/plugins/hermes-usage-manager"
hermes plugins enable hermes-usage-manager
hermes plugins list
hermes plugins doctor --ci hermes-usage-manager
mkdir -p "$HOME/.hermes/usage-manager-test-data"
chmod 700 "$HOME/.hermes/usage-manager-test-data"
export USAGE_MANAGER_DB_PATH="$HOME/.hermes/usage-manager-test-data/usage.sqlite3"
export USAGE_MANAGER_TRUST_DASHBOARD_ADMIN=1
hermes dashboard --no-open
)
```

不要用 `hermes plugins validate`：用户 v0.21.0 已确认没有该子命令。安装目录没有 `.git` 时，`rev-parse` 失败是源码来源未知，不表示插件失败；保留 `hermes --version` 输出即可，不擅自初始化 git 或升级 Hermes。

在认证 Dashboard 内检查：health 的版本与 storage=ready；正式页面空数据而非 fixture；管理员新建部门/价格后重启仍存在；关闭显式 opt-in 后业务请求403；篡改 role 参数不能越权；Network/Console 无重复 React。M2真实对话**不会**采集记录，不能据此判采集失败或声称 Hooks 已接入。若宿主返回 HOST_AUTH_UNAVAILABLE，保存脱敏输出并停下定位，不能改为跳过认证。

数据升级前须停相关进程或使用 sqlite backup API 做一致性备份，不直接拷贝正在写入的单个 WAL 数据库文件。降级旧代码时保留原 DB 备份；新版 schema 拒绝旧版解释。Windows ACL、Linux权限、后台启动环境变量传递、base path、host隔离等均是待真实验证项。

## M1 历史记录（0.2.0）

M1 的原型页面、Mock API 与交互在本地验证；远端仍只确认过 M0（0.1.0）。正式构建继续仅使用 Web Dashboard 的 SDK.React / SDK.fetchJSON / register，不使用 Desktop SDK、不修改 Hermes 核心。当前 Python health 版本为 0.2.0 / M1，采集与存储仍为 unavailable。

M1 引入 ECharts 6 / Zod 4，模块图允许 ECharts、zrender、tslib、Zod，拒绝 React/ReactDOM 运行时导入。构建单 IIFE，并附完整第三方许可。浏览器测试证明普通 script 加载、一次注册、切换时清理图表实例的 ResizeObserver、Live 状态不请求模拟业务数据。

本地 Mock UI 的角色 header 仅用于演示，不能作为真实身份断言。真实 Hermes 没有挂载 Mock 查询或写入接口，未实现生产 RBAC，也不会展示虚构统计。M2/M3 尚未开始。

完整结果见 `docs/m1-report.md`，本地启动见 `docs/development.md`。M1 安装包仅提供原生运行骨架与预构建页面；若安装至 Hermes，将显示业务数据尚未接入。无需更新远端即可从本仓库本地验收完整 Mock 页面。

## M0 历史核验记录

核验日期：2026-10-15（Asia/Shanghai）。状态：**本地 Mock 测试通过；用户截图确认真实 Hermes 的 Tab、页面和 health 主链路成功，剩余运行时检查待补证**。

## 环境

| 项目 | 结果 |
|---|---|
| 本机 | Windows / PowerShell，工作区 `F:\projects\Hermes_Usage_Manager` |
| Hermes CLI | `Get-Command hermes` 无结果；`where.exe hermes` 未找到，无法执行 `hermes --version` |
| 已安装 Hermes 版本 | unavailable；用户已明确本机未安装 |
| 官方源码核对基线 | `NousResearch/hermes-agent`，commit `525dbcad8d744710a43d01eb7366500e46eacbf4` |
| 源码身份 | 临时目录只读核对，未安装或启动 Hermes；不是本机已安装版本，也不是用户已选目标发布版 |
| 源码提交时间 | 2026-10-15T00:07:50-04:00 |
| Web SDK contract | 源码声明 `1.1.0`；本插件仅依赖 React、fetchJSON 和 register |
| Node | v24.19.0 |
| 包管理器 | pnpm 11.25.0；本机 PATH 无 npm，使用内置 pnpm 执行同名 package scripts |
| Python | 3.12.14（独立 `.venv`） |
| 真实服务连接 | 无；只访问官方公开文档、GitHub、依赖注册表与本地 loopback Mock |

### 用户提供的远端 CLI 实测

2026-10-15 用户粘贴的 `ubuntu@VM-0-10-ubuntu` 输出（本代理未连接该机器）：

- Hermes Agent `v0.21.0 (2026.8.31)`，目录 `/home/ubuntu/.hermes/hermes-agent`，安装方式 unknown。
- Python `3.11.15`，OpenAI SDK `2.24.0`。
- `hermes plugins --help` 不包含 `validate`；实际运行 `validate --help` 返回 invalid choice。
- `hermes plugins doctor --help` 支持 `--ci` 和可选的插件路径/已安装 ID。
- 该版本应使用 `hermes plugins doctor --ci PATH_OR_ID`，不执行 `validate`。此前固定源码比此安装版本更新，不能由源码核对推断此版本已兼容 Dashboard。
- 用户执行 `git -C /home/ubuntu/.hermes/hermes-agent rev-parse HEAD` 返回 not a git repository，远端源码 commit 记为 unavailable。
- 是否隔离测试机尚未确认；以下安装命令仅适用于隔离测试环境。

### 用户提供的真实 Dashboard 截图

用户报告“成功了”，并提供真实 Hermes Dashboard 截图，确认：

- 宿主侧栏已出现并打开“用量管理”插件入口。
- 插件组件渲染“用量管理 · Hello Hermes”，浅紫 CSS 已加载。
- 页面显示“Live 路由”和“API 连接正常”，插件版本 0.1.0；依据当前组件响应校验逻辑，可确认真实 health 请求返回了兼容响应。
- 采集和存储仍显示 unavailable，符合 M0 范围。

截图文件：`C:/Users/it/AppData/Local/Temp/codex-clipboard-b4a411b5-f97d-4615-9f25-fb4955226213.png`（用户本地临时附件，非发行包文件）。本代理没有远程登录或独立检查服务器。UI 中“尚未验证 Hermes 集成”是 POC 的固定保守文案，不是本次请求失败；本轮仅更新验收记录。

源码构建检查已证明产物未携带第二份 React；截图补充证明组件能够在真实宿主渲染。doctor 原始输出、浏览器 Console/Network、切换/重挂载、真实 Hook 触发、隔离模式和自定义 base path 仍无直接证据。截图顶部还包含宿主 agent 意外重启提示，发生时间及原因未核对，不能从截图判断与插件有关。

## 官方证据

文档：[Dashboard 扩展](https://hermes-agent.nousresearch.com/docs/user-guide/features/extending-the-dashboard)、[Python 插件](https://hermes-agent.nousresearch.com/docs/developer-guide/plugins)、[Hooks](https://hermes-agent.nousresearch.com/docs/user-guide/features/hooks)。文档会变化，下面以固定 commit 的源码为核对依据。

| 协议 | 固定源码证据 | M0 使用方式 |
|---|---|---|
| React 与注册 | [web/src/plugins/registry.ts](https://github.com/NousResearch/hermes-agent/blob/525dbcad8d744710a43d01eb7366500e46eacbf4/web/src/plugins/registry.ts)，`exposePluginSDK`、`registerPlugin` | 从 `window.__HERMES_PLUGIN_SDK__.React` 取实例，同步 `register(name, Component)` |
| SDK 类型 | [sdk.d.ts](https://github.com/NousResearch/hermes-agent/blob/525dbcad8d744710a43d01eb7366500e46eacbf4/web/src/plugins/sdk.d.ts) | 只定义使用到的接口子集，无虚构 SDK 方法 |
| API 认证与前缀 | [web/src/lib/api.ts](https://github.com/NousResearch/hermes-agent/blob/525dbcad8d744710a43d01eb7366500e46eacbf4/web/src/lib/api.ts)，`fetchJSON`、`BASE` | 使用 SDK.fetchJSON，不手取 token，不用裸 fetch 绕过宿主 |
| Dashboard 发现与 API 挂载 | [web_server_dashboard.py](https://github.com/NousResearch/hermes-agent/blob/525dbcad8d744710a43d01eb7366500e46eacbf4/hermes_cli/web_server_dashboard.py)，`_get_dashboard_plugins`、`_mount_one_plugin_api` | dashboard manifest + `router`，挂载 `/api/plugins/hermes-usage-manager` |
| Python 加载 | 同上，`spec_from_file_location`、`sys.modules`、`exec_module` | router 文件自包含，不假定相对包导入；pytest 按相同文件导入形态测试 |
| Hook | [hermes_cli/plugins.py](https://github.com/NousResearch/hermes-agent/blob/525dbcad8d744710a43d01eb7366500e46eacbf4/hermes_cli/plugins.py)，`VALID_HOOKS`、`PluginContext.register_hook` | 仅注册 `pre_llm_call`，`**kwargs`，返回 None；本阶段不采集 |
| Manifest | [plugins_manifest.py](https://github.com/NousResearch/hermes-agent/blob/525dbcad8d744710a43d01eb7366500e46eacbf4/hermes_cli/plugins_manifest.py) | `manifest_version: 2` 与 `api_version: 1` 分离 |
| CLI | [subcommands/plugins.py](https://github.com/NousResearch/hermes-agent/blob/525dbcad8d744710a43d01eb7366500e46eacbf4/hermes_cli/subcommands/plugins.py)、[plugin_validate.py](https://github.com/NousResearch/hermes-agent/blob/525dbcad8d744710a43d01eb7366500e46eacbf4/hermes_cli/plugin_validate.py) | 真实测试使用 validate / enable / doctor；本机未执行 |

### 与 README 示例的差异

1. README 称 API 需重启。当前源码 `_try_hot_mount_plugin_api` 支持未挂载插件首次请求热挂载；已挂载路由的代码替换仍需重启。本项目继续使用重启流程，避免依赖新版特性。
2. 当前源码限制项目级 `./.hermes/plugins/` Python API 自动导入；需安装到测试 Hermes 的用户级插件目录并显式 enable。仅在工作区放 manifest 不证明后端能加载。
3. 源码存在隔离 plugin host 分支，不能以本地 FastAPI 直接导入测试代替真实隔离模式验证。
4. health 采用 README 10.3 的直接健康响应，扩展 version / milestone / data_source / capabilities；业务查询 envelope 留待 M2。`status=ok` 仅表示健康路由可响应，存储/采集均为 `unavailable`。
5. 不声明 `license: MIT`：仓库尚无用户选定许可证，不凭示例替用户确定授权。
6. 补充 `description` 和 `provides_hooks: [pre_llm_call]`；官方 validate 会比对实际注册能力与声明，不能仅复制 README 的最简 YAML。

## 原型阅读记录（9/9）

| 文件 | 已核对内容 |
|---|---|
| 概览.png | 三组 KPI、双轴趋势、部门柱图、三分布饼图、用户排行 |
| 使用分析.png | 部门/日期筛选、堆叠柱与活跃人数、两饼图、用户排行 |
| MCP分析.png | 服务筛选、面积趋势、可滚动工具排行及 Tooltip |
| 用量明细.png | 请求状态、模型与用量表、筛选及分页 |
| 对话审计.png | 会话表、部门/人员/日期筛选 |
| 对话审计-对话详情.png | 与列表近似，未提供独立详情设计，详情留待补充设计 |
| 人员设置-用户列表.png | 用户/部门列、搜索与分页、内嵌 Tab |
| 人员设置-部门分配.png | 实际为部门列表，含新建/编辑/删除 |
| 人员设置-部门分配-1.png | 双列表、选择、搜索、部门迁移 |

M0 仅借用浅薰衣草容器、紫色胶囊按钮与圆角，不提前实现上述 M1 页面。

## M0 真实 Hermes 测试命令（历史流程，非当前 M1 更新命令）

以下仅在独立测试机器或明确隔离的测试账号上执行。使用已有 Hermes 测试安装，不连接生产；先记录实际版本/commit。官方源码基线不等于兼容任意旧版。

```bash
hermes --version
hermes plugins --help
hermes plugins doctor --help
git -C /home/ubuntu/.hermes/hermes-agent rev-parse HEAD

# 将 M0 zip 上传至当前目录；子 shell 中任一步失败即停止
(
set -eu
test -f ./hermes-usage-manager-0.1.0-m0.zip
if [ -e "$HOME/.hermes/plugins/hermes-usage-manager" ] || [ -L "$HOME/.hermes/plugins/hermes-usage-manager" ]; then
  echo "插件目录已存在，停止；请先检查现有安装。" >&2
  exit 1
fi
mkdir -p "$HOME/.hermes/plugins"
python3 -m zipfile -e ./hermes-usage-manager-0.1.0-m0.zip "$HOME/.hermes/plugins"
hermes plugins doctor --ci "$HOME/.hermes/plugins/hermes-usage-manager"
hermes plugins list
hermes plugins enable hermes-usage-manager
hermes plugins doctor --ci hermes-usage-manager
hermes dashboard --no-open
)
```

子 shell 的 `set -e` 确保检查失败时不继续后面的安装/启用命令；单独在交互终端执行 `test` 本身不能保证后续命令停止。doctor 失败时保留输出并停止，不跳过检查或直接升级 Hermes。打包目录内的 FastAPI 依赖由测试 Hermes 环境满足；如缺失，在该测试环境按插件依赖声明安装后重启。以后发布 Git 仓库时可使用官方 `hermes plugins install OWNER/REPO --no-enable`，当前工作区不是 Git 仓库，不伪造仓库地址或创建提交。

打开测试机 loopback Dashboard（默认 `http://127.0.0.1:9119`），点击“用量管理”：

1. `GET /api/dashboard/plugins` 包含 manifest，静态 IIFE/CSS 返回 200。
2. 页面出现“用量管理 · Hello Hermes”，health 返回 `data_source=live` 且采集/存储 unavailable。通过页面的 SDK 请求验证认证；不要以无认证 curl 代替认证测试。
3. 无 invalid hook call、无第二份 React；切走/返回 Tab，Network 与 Console 无异常。
4. doctor 确认 `pre_llm_call` 注册；执行一条测试对话观察 Hermes 无异常。本阶段 callback 不存事件，不能以健康接口声称真实 Hook 已触发。
5. 重启测试 Dashboard 再次验证 API；记录宿主 Python/React 版本、隔离模式、源码 commit、doctor 原始输出与脱敏 health 样例。仅在 CLI 明确支持 validate 的其他版本补充该项。

## 未验证项与退出条件

真实 Hermes v0.21.0 的 Tab、组件渲染和 health 主链路已获用户截图确认；本地构建无重复 React。doctor 原始结果、真实 Hook 调用、浏览器错误检查、重挂载、隔离模式及自定义 base path 尚未补证，不能将全部运行时检查标绿，也不代表生产就绪。

可执行测试和本次输出见 `docs/m0-report.md`。M0 到此停止，等待下一阶段指令。
