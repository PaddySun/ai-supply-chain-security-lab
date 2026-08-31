# 打开文件夹即执行：ZCode / TRAE / Claude Code / VS Code 工作区自动执行攻击面实测

> 2026-08-31 · 配套代码、日志与录屏：[PaddySun/ai-supply-chain-security-lab](https://github.com/PaddySun/ai-supply-chain-security-lab)（`ide-autorun-demo/`）
> 本文是 keyv 蠕虫分析（见 [blog.md](blog.md)）的延伸实验，全部在本机完成，载荷为无害演示（写时间戳日志 + 弹出 Windows 计算器）。

## 摘要

2026 年 8 月的 keyv 蠕虫把 `.claude/settings.json` 和 `.vscode/tasks.json` 变成了"打开项目即执行"的入口。本文把同一套无害载荷投向四款主流 AI 编码客户端，并延伸到一类新的攻击面——**工作区级 MCP 服务器声明**（仓库里的一个 JSON 文件，声明"连接一个 stdio 工具服务器"，语义上等于"以当前用户权限 spawn 任意进程"）。

核心实测结论：

- **ZCode 3.0.96（桌面版）**：用 `Ctrl+K Ctrl+O` 选中工作区文件夹、**还没发任何消息**，计算器即弹出——工作区 `.zcode/config.json` 声明的 MCP 命令在打开工作区瞬间自动执行，零交互、无任何确认（有录屏）。桌面版对工作区 **hooks** 却有完整的审核 UI——信任模型不一致。
- **ZCode CLI 0.16.5**：无头模式同样自动拉起，作为桌面版结论的旁证。
- **Claude Code v2.1.224**：工作区 SessionStart hook 零交互执行（此前实验已证）。
- **TRAE SOLO CN 1.107.1**：三层防御（默认关 + 应用级作用域 + 防 agent 自改配置），实测打开投毒工作区零触发——同类问题可以被工程化封死。
- **VS Code（基线）**：`tasks.json` 自动任务有两道确认，但对已信任文件夹失效。

一句话：**问题不在"打开项目会执行配置"这个功能本身，而在执行前有没有一道仓库自己绕不过去的信任门。**

## 一、环境与版本

| 项目 | 版本 |
|---|---|
| 操作系统 | Windows 10 22H2 (19045)，用户 `paddy` |
| ZCode 桌面版 | 3.0.96（内置 CLI `glm/zcode.cjs` 0.16.5） |
| TRAE SOLO CN | 1.107.1（VS Code fork） |
| Claude Code | v2.1.224 |
| VS Code | 最新稳定版 |
| Git Bash | Git for Windows 2.55.0（`C:\Program Files\Git\bin\bash.exe`） |

判定方法：载荷统一写一行 `[标记] 时间 user= pid=` 到工作区 `TRIGGER_LOG.txt` 并 `start calc.exe`；日志行 + 计算器进程创建时间双重取证。

## 二、原理：配置文件如何变成执行入口

现代 AI 编码客户端为了"开箱即用"，会自动读取工作区里的多种声明式配置。其中两类直接绑定进程执行：

**1. Hooks（生命周期钩子）**——配置声明"在 X 事件时执行命令 Y"：

```json
{ "hooks": { "SessionStart": [ { "hooks": [ { "type": "command", "command": "<任意命令>" } ] } ] } }
```

**2. 工作区级 MCP 服务器**——配置声明"本项目使用工具服务器 S"：

```json
{ "mcp": { "servers": { "S": { "type": "stdio", "command": "<任意可执行文件>", "args": [...] } } } }
```

stdio 传输的 MCP server 就是一个被客户端 spawn 的本地子进程。**声明它的 `command` 字段与声明"执行任意命令"完全等价**——但它披着"连接工具"的合法外衣，且往往享受比 hooks 更宽松的信任策略。这就是本文要量化的不对称。

## 三、ZCode：工作区 MCP 零交互执行（已实测，含录屏）

### 3.1 攻击面与代码讲解

ZCode 的工作区配置文件是 `<repo>/.zcode/config.json`（兼容回退 `<repo>/.agents/mcp.json`）。对其桌面版 `app.asar` 与 CLI bundle `zcode.cjs` 做字符串级分析，两段关键代码：

**MCP 五层合并（`zcode.cjs`，函数 `GEo`）**——工作区（project）层与用户层、系统层平等参与合并，无单独门槛：

```js
// 简化还原：把 system/project/user/env/cli 五个来源的 mcp.servers 合并
for ([s,u] of Object.entries(i?.mcp?.servers ?? {})) { t[s]=u; r[s]=o; }  // o ∈ 五个来源
apply("system", ...); apply("project", e.projectConfig); apply("user", ...); ...
```

官方配置指南也明说：工作区级 MCP 服务器 **"trusted and auto-connected by default"**，并提醒 "only open workspaces you trust"。

**Hooks 信任门控（同 bundle）**——hook 的可运行性校验带 `trustState`：

```js
// zod refine 片段：不可信状态不可运行
message: `${e.trustState} cannot be runnable`
message: "a configured-disabled hook cannot be runnable"
```

即：**hooks 有信任状态机，MCP 没有**——这就是全部差异的来源。

### 3.2 触发方式与结果

**触发方式 A：桌面版 UI（最终实测，2026-08-31 13:17）**

1. `Ctrl+K Ctrl+O` → 选中 `zcode-ws` 文件夹
2. **不需要发消息、不需要任何确认**——选择文件夹的瞬间计算器弹出

结果（`TRIGGER_LOG.txt` 节选，13:17:04–13:18:33 共 **11 次**拉起）：

```
[ZCODE-MCP] 2026-08-31 13:17:04 user=paddy pid=179    ← 打开工作区瞬间
[ZCODE-MCP] 2026-08-31 13:17:05 user=paddy pid=1362
[ZCODE-MCP] 2026-08-31 13:17:05 user=paddy pid=2021
[ZCODE-MCP] 2026-08-31 13:17:05 user=paddy pid=1858
[ZCODE-MCP] 2026-08-31 13:17:15 user=paddy pid=1956
...（后续会话启动与重试共 11 次）
```

录屏证据：[docs/media/zcode-mcp-demo.mp4](media/zcode-mcp-demo.mp4)（10.9MB，完整记录"选文件夹 → 计算器弹出"）。

**触发方式 B：CLI 无头模式（2026-08-30 21:38 初次实测）**

桌面版捆绑的 CLI（`resources/glm/zcode.cjs`）支持 `zcode -p "..." --cwd <工作区>`。需先在 `~/.zcode/cli/config.json` 配置模型（格式见附录），随后：

```
[ZCODE-MCP] 2026-08-30 21:38:00 user=paddy pid=1657   ← 会话启动即拉起
[ZCODE-MCP] 2026-08-30 21:38:01 user=paddy pid=1664   ← 客户端重试再拉起
```

零确认弹窗。

**Hooks 对照实验（同一份工作区配置）**：

- 工作区级 SessionStart hook：桌面版弹出 **"1 个工作区 Hook 待审核，本会话暂未启用"**，用户选择信任后按工作区记忆；移除工作区即注销。CLI 下工作区 hook 同样不执行。
- 同一 hook 移到**用户级** `~/.zcode/cli/config.json`：立即执行（21:38:39 `[ZCODE-HOOK]`）。

### 3.3 踩坑记录（复现者必读，也是攻击者视角的注脚）

第一轮桌面测试中 hook 显示 **"53ms 失败"**、MCP 静默不执行——原因：GUI 启动的进程 PATH 只有 `Git\cmd`（`git.exe`），没有 `Git\bin`（`bash.exe`），载荷写的 `bash` 找不到。改用绝对路径 `C:/Program Files/Git/bin/bash.exe` 后，在模拟 GUI 的最小 PATH 环境下 CLI 全部成功（12:05:40/42），桌面版成功（13:17）。

**结论：PATH 差异对真实攻击者不构成障碍**——keyv 级别的蠕虫会直接用绝对路径或 `cmd /c`，首次投放前必然做过环境适配。

### 3.4 分析

ZCode 桌面版是本次四款中触发最早、最无感的：**攻击面从"会话启动"提前到了"打开工作区"，交互从"零确认"到"用户可能根本没注意窗口还没完全渲染"**。而它对 hooks 的审核 UI（待审核提示 → 信任 → 绑定工作区 → 移除即注销）设计得相当好——这反衬出 MCP 缺失同样门控是纯粹的不一致，而非能力缺失。

**修复建议（厂商）**：工作区级 MCP 服务器声明应与工作区 hooks 走同一 `trustState` 门控——首次出现时"待审核"，用户信任后记忆，移除工作区注销。SSE/HTTP 型 MCP 同样需要门控（服务端可换返回内容）。

## 四、Claude Code：SessionStart hook 零交互执行

**版本 v2.1.224**，此前实验（见 `autorun-demo/`，含 GIF 录屏）已完整复现：

- 触发方式：工作区 `.claude/settings.json` → `hooks.SessionStart` → `command: "sh demo_payload.sh"`
- UI：启动会话（含非交互 `claude -p`）即执行，**无任何确认**（注：测试机全局开了 `skipDangerousModePermissionPrompt`，默认配置行为建议读者自测）
- 踩坑：hook 经 Git Bash 执行，`cmd /c "%CLAUDE_PROJECT_DIR%\x.cmd"` 写法会 `EPERM: uv_spawn bash.exe` 静默失败，载荷必须是合法 bash 语句
- 结果：`[AUTORUN DEMO via Claude Code SessionStart]` + 计算器进程（PID 17692）

keyv 蠕虫的 GitHub 侧传播正是这一机制：向所有分支推送 `.claude/settings.json`/`.vscode/tasks.json`，提交者伪装为 `claude <claude@users.noreply.github.com>`。

## 五、TRAE SOLO CN：三层防御（代码证实 + 实测未触发）

### 5.1 代码讲解（反编译 `resources/app/out` 1.107.1）

**第一层——项目级 MCP 默认不加载**。设置 `trae.mcp.enableWorkspaceMcp`（UI 文案"允许自动从项目根目录下的 .trae/mcp.json 中加载 MCP 配置"）注册处：

```js
// workbench.desktop.main.solo-lite.js（反混淆节选）
registerConfiguration({ id: "trae.mcp", properties: {
  [enableWorkspaceMcp]: { scope: 1 /* APPLICATION */, type: "boolean", default: false, ...
```

**第二层——作用域锁死**。`scope: 1`（APPLICATION）意味着它是全局用户设置，**恶意仓库无法通过自己的 `.vscode/settings.json` 替受害者打开**。

**第三层——防 agent 自改**。工具文件服务把 `.trae/mcp.json` 与 `.vscode` 列入读写安全域：

```js
static { this.G = [".trae"] }  static { this.H = ".trae/mcp.json" }  static { this.I = [".vscode"] }
// ensurePathInReadSafeScope(...)：agent 的文件读写工具不得触碰这些路径
```

这直接封死了 keyv 战法里"提交者伪装成 claude / prompt injection 让 agent 自己写配置"的传播路径。

### 5.2 实测结果

- Code 模式下打开含 `.trae/mcp.json` + `.vscode/tasks.json`（folderOpen）的投毒工作区：**零提示、零执行、设置面板无 MCP 被添加**（2026-08-30/31 两次，含 `--new-window` 自动化与手动打开）
- 待验证项（不影响结论）：用户手动开启 `enableWorkspaceMcp` 后，`.trae/mcp.json` 是否变为自动加载（此时"一次全局开启 = 所有后续工作区文件变执行入口"）；以及 `.vscode/tasks.json` 在 TRAE 的信任/允许交互（应与 VS Code 基线一致）

### 5.3 分析

TRAE 是四款中唯一把"工作区声明的执行原语"当作**默认不可信**的：默认关、开了也只认用户显式同意的作用域、还防住了 agent 自改。这证明该攻击面完全可以工程化封死，成本并不高。

## 六、VS Code（基线）：两道确认，败给"已信任的日常项目"

`.vscode/tasks.json` 的 `runOptions.runOn: "folderOpen"`（任务名伪装成 `install-dependencies`）：

- 首次打开陌生文件夹：Workspace Trust 确认 + "检测到自动任务"确认，两道防线有效
- 已信任文件夹 / 用户曾设 `task.allowAutomaticTasks: "auto"`（不少人为了 watch 任务开过）：**第二次打开完全静默执行**
- 真实受害场景（keyv）投毒的是受害者自己的日常工作项目——文件夹早已信任

详见 `autorun-demo/README.md`。

## 七、汇总对比

| 客户端 | 版本 | 工作区 MCP 自动执行 | 工作区 hooks 自动执行 | 触发点 | 判定 |
|---|---|---|---|---|---|
| **ZCode 桌面版** | 3.0.96 | ✅ **零交互**（实测+录屏，11 次） | ❌ 待审核门控（实测，UI 良好） | **打开工作区瞬间** | **不一致，高危** |
| ZCode CLI | 0.16.5 | ✅ 零交互（实测） | ❌ 门控（用户级放行） | 会话启动 | 同上 |
| Claude Code | v2.1.224 | —（未测） | ✅ **零交互**（实测+GIF） | 会话启动 | 高危 |
| TRAE SOLO CN | 1.107.1 | ❌ 默认关+作用域锁+防自改（代码+实测） | — | — | **设计正确** |
| VS Code | 最新 | — | tasks：Trust+Allow 后静默 | 打开文件夹 | 有条件放行 |

## 八、防御建议

**用户/企业**：
1. 把 `.zcode/`、`.agents/`、`.trae/`、`.cursor/`、`.mcp.json`、`.claude/`、`.vscode/` 全部纳入 PR 审计清单——出现 `command`/`args`/`hooks` 字段即告警
2. 打开不熟悉的工作区前先 `cat` 这些文件；CI 里加一个扫描 job
3. Agent 沙箱内不要放长期凭据（keyv 蠕虫的第一目标是 `~/.claude/credentials.json` 等 AI 工具凭据）

**厂商**：
1. 工作区声明的执行原语（hooks、stdio MCP、folderOpen task）应共享同一套信任状态机：首次审核、按工作区记忆、移除即注销
2. "连接工具服务器"的 UI 语义与"spawn 进程"的安全语义必须对齐——对用户展示后者
3. 参考 TRAE：默认不可信 + 应用级作用域 + 禁止 agent 自改信任配置

## 附录：复现指南

```
ide-autorun-demo/
├── zcode-ws/                  ZCode 演示工作区
│   ├── .zcode/config.json     mcp.servers 声明 + SessionStart hook（绝对路径 bash）
│   ├── payload_mcp.sh         [ZCODE-MCP] 日志 + 计算器
│   ├── payload_hook.sh        [ZCODE-HOOK] 日志
│   └── TRIGGER_LOG.txt        全部触发证据
├── trae-ws/                   TRAE 演示工作区（.trae/mcp.json + .vscode/tasks.json）
├── (zcode-mcp-demo.mp4        桌面版"选文件夹即弹计算器"录屏 → 已归档 ../docs/media/)
└── README.md                  简版步骤
```

- **桌面版**：直接用 ZCode 打开 `zcode-ws` 即可（无需任何配置）
- **CLI**：桌面版捆绑 `resources/glm/zcode.cjs`；`~/.zcode/cli/config.json` 需要 `provider`（含 `options.apiKey/baseURL`）+ `model: "<provider>/<model>"` 字符串（注意：不是对象），hook 放 `hooks.events.SessionStart`。测完删除该文件避免残留触发
- **载荷注意**：命令/参数用**绝对路径**（GUI 进程 PATH 无 `Git\bin`）

## 声明

仅用于防御研究与安全教学。载荷仅写日志与弹出系统计算器，不含窃密、持久化、C2 等任何武器化功能。所有实验在本机隔离环境完成，发现的问题建议通过厂商官方渠道披露。

## 参考

- [StepSecurity — ChainDrop npm Worm](https://www.stepsecurity.io/blog/chaindrop-npm-worm)（keyv 蠕虫载荷与持久化细节）
- [SANS ISC — Don't Revoke That Token Yet](https://isc.sans.edu/diary/Dont+Revoke+That+Token+Yet+Inside+the+keyvcacheable+npm+Worm/33218)
- [本仓库 keyv 蠕虫全文分析](blog.md) · [autorun-demo（Claude Code/VS Code 实验）](autorun-demo/README.md) · [ide-autorun-demo（本文实验）](ide-autorun-demo/README.md)
- ZCode 配置指南（内置技能 `zcode-configuration-guide`："workspace-scoped servers are trusted and auto-connected by default"）
