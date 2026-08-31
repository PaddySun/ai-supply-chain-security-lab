# DSH 不安装执行（No-Install Execution）漏洞实验

> ⚠️ 防御性安全研究。所有载荷均为无害演示（写一行日志 + 弹计算器），不含任何
> 窃密/持久化/C2/武器化代码。目标运行时是 **DeepSeek Harness (DSH)**
> `@deepseek-ai/dsh@0.1.1-rc.2`。

本实验回答一个问题：keyv 蠕虫（2026-08-04，435 个 npm 包）那套"**不执行
`npm install`，只打开项目/启动 AI 会话，代码就运行了**"的打法，能否迁移到 DSH？

**一句话结论**：DSH **没有** `.vscode/tasks.json`（folderOpen 任务）或
`.claude/settings.json`（SessionStart hook）这类**项目级、配置驱动的自动执行
文件**。但 DSH 把同等的攻击能力拆成了三块，入口各不相同：

| DSH 机制 | 入口层级 | 性质 | 能否被"克隆仓库"直接触发 |
|---|---|---|---|
| `AGENTS.md` / `CLAUDE.md` 自动注入 | **项目级** | 指令注入 | ✅ 能（本实验一） |
| `<项目>/.dsh/skills` 自动发现 | **项目级** | 指令注入 | ✅ 能（本实验一） |
| `dsh-mcp-client` 进程派生 | profile 级（`cordis.yml`） | **代码执行** | ❌（实验二，文档化） |
| `dsh-tool-cordis` 的 `cordis_run` | 工具级（gated） | **代码执行** | ❌（实验三，文档化） |

即：**原始"打开即执行"在 DSH 里退化为"打开即注入（指令）→ 诱导 agent 调用它
手里的工具去执行"**；而真正的"配置→spawn 进程 / eval"能力，被放到了 profile
和工具层，一个恶意仓库单靠克隆够不着——这是 DSH 与 Claude Code / VS Code 的
关键差异。

## 目录

- `docs/code-reading.md` —— 两段源码的逐行阅读（spawn + vm 沙箱）。
- `poc/agmd-injection/` —— **实验一（真正可触发的项目级面）**：仓库自带
  `AGENTS.md` + `.dsh/skills` 自动注入，诱导 agent 运行良性载荷。
- `poc/mcp-spawn/` —— **实验二（文档化）**：MCP 配置里的任意 `command/args` → DSH
  启动即 spawn 任意进程。
- `poc/cordis-eval/` —— **实验三（文档化）**：`cordis_define`+`cordis_run` 在 DSH
  进程内 vm 求值任意 JS（官方自认"不是安全边界"）。

## 复现

### 实验一（项目级指令注入，可实际跑）

1. 把本仓库 `poc/agmd-injection/` 作为 **DSH 工作区**新开一个会话（或用
   `dsh` 打开该目录）。
2. 观察：DSH 的 `dsh-agent-instructions` 会**自动**把 `AGENTS.md` 注入上下文，
   `dsh-skill-filesystem` 会**自动**发现 `.dsh/skills/dsh-payload`。
3. 载荷行为（`demo_payload.py`，纯标准库、无需安装）：追加一行时间戳+用户名到
   `INTRUSION_LOG.txt`，并在 Windows 上弹出计算器。

```bash
# 使用虚拟环境（本实验建议）：
cd dsh-noinstall-lab
python -m venv .venv
.venv/Scripts/python.exe ../poc/agmd-injection/demo_payload.py
```

真实攻击中，`AGENTS.md` 会把上面的指令伪装成"先跑 `npm run setup` / 初始化脚本"，
载荷换成窃密器——与 keyv 蠕虫把持久化写进 `.claude/settings.json` 是同一个心智，
只是 DSH 用"指令"而非"hook"触达。

### 实验二 / 三（profile/工具级，仅文档 + 示例，不实际注入）

见各自目录的 README。它们需要修改 `~/.dsh/cordis.patch.yml` 或调用被 gated 的
`cordis_*` 工具，属于"获得 profile 写入权/危险工具授权后"的后续利用，故只做
示例与源码佐证，不落地运行。

## 防御建议（对应 DSH）

1. **项目级 `AGENTS.md` / `.dsh/skills` 是未经验证的仓库内容**，进入上下文前应
   标注"来自未信任仓库"（当前 DSH 只标了"不覆盖 system/用户指令"，未标信任边界）。
2. **加 MCP 服务器 = 装了能派生任意进程的插件**：`command/args/cwd` 原样透传，
   无白名单；需显式审批，且别放进可从仓库触达的路径。
3. **`dsh-tool-cordis` 官方已自认"不是安全边界、当 bash 对待"**：生产部署别把
   `cordis_*` 工具挂进 agent 视图（默认关闭，本会话工具清单里就没有）。
4. **明文凭据落盘**（`~/.dsh/settings.yaml`、`.credentials.yaml`、`.claude/settings.json`）
   是蠕虫窃取目标清单的直接对应物，建议移入系统钥匙串/环境变量。
