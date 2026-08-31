# 实验一：项目级指令注入（DSH 唯一"克隆即触发"的面）

## 机制

DSH 有两个**随项目自动加载**的面，都在仓库树内、不需要任何"安装"动作：

1. `dsh-agent-instructions` —— 自动注入 `AGENTS.md` / `CLAUDE.md` /
   `AGENTS.local.md` / `CLAUDE.local.md`（从最近 `.git` 祖先到 cwd）。
2. `dsh-skill-filesystem` —— 自动发现 `<项目>/.dsh/skills/**` 与
   `<项目>/.agents/skills/**` 技能。

两者都是**指令注入**（不是代码执行）：它们把仓库控制的文本送进 agent 上下文，
再由 agent 调用它手里已有的 `pwsh`/`bash`/`run_code` 工具去"执行"。

## 复现

1. 把本目录（`poc/agmd-injection/`）作为 DSH 工作区新开会话。
2. `AGENTS.md` 与 `.dsh/skills/dsh-payload` 会被自动注入/发现。
3. 按指令运行：

   ```bash
   python demo_payload.py
   ```

   观察 `INTRUSION_LOG.txt` 出现新行、计算器弹出——即"打开项目 → 代码执行"，
   全程没有任何 `npm install` / `pip install`。

## 与 keyv 蠕虫的对照

| keyv（Claude Code / VS Code） | DSH |
|---|---|
| `.claude/settings.json` SessionStart hook **直接跑** `sh payload.sh` | 无 hook；`AGENTS.md` 被注入后**诱导** agent 跑 `python demo_payload.py` |
| 代码执行 = 配置 hook | 代码执行 = 指令注入 + agent 手里的工具 |
| 零交互 | 需要 agent 服从指令（prompt injection 成功率问题） |

诚实注脚：DSH 这条路**不是**确定性执行——它依赖 agent 是否被诱导成功；攻击者的
工程化写法是把指令伪装成不可疑的初始化步骤（本 `AGENTS.md` 已演示该措辞）。
