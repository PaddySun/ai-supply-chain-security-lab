# AI 编码助手供应链安全研究（Slopsquatting + 零安装执行）

📖 **[完整博客文章：《打开项目即沦陷：keyv 蠕虫与 AI 编码助手时代的供应链暗战》](blog.md)** —— 事件还原、影响漏斗、版本清单、本地复现与处置措施。

📖 **[独立实测报告：《打开文件夹即执行：ZCode / TRAE / Claude Code / VS Code 工作区自动执行攻击面实测》](ide-attack-surface.md)** —— 四款客户端分 CLI/UI 触发路径、反编译代码讲解、实验日志与录屏、防御对比。

2026 年 keyv 蠕虫事件（435 个 npm 包投毒）的防御性研究复现，包含两个独立实验。

> ⚠️ **警告：`autorun-demo/` 包含可自动执行的无害演示载荷。**
> 用 VS Code / Claude Code 打开该文件夹会自动弹出计算器并写入日志。
> 载荷仅用于演示攻击向量（打开项目 = 执行代码），不含任何恶意功能。
> 体验请使用一次性环境，勿在日常开发环境打开。

## 实验一：Slopsquatting（模型幻觉包名测量）

`slopsquatting-lab/` — 复现 USENIX Security 2025《We Have a Package for You!》方法论：
LLM 生成代码 → 提取包名 → npm/PyPI 注册表比对 → 幻觉率与复现率统计。

实测（deepseek-chat，2026-08-30）：PyPI 20 样本 + npm 24 样本，**零幻觉**，
与论文 2025 年 19.7% 平均值对照，量化了前沿模型的改进幅度。

详见 `slopsquatting-lab/article_draft.md`。

## 实验二：零安装执行（打开项目 = 运行代码）

`autorun-demo/` — 复现 keyv 蠕虫的核心战法：不执行 `npm install`，
仅打开项目文件夹 / 启动 AI 会话即触发代码执行。

| 攻击面 | 触发条件 | 本机实测 |
|---|---|---|
| `.vscode/tasks.json` (`runOn: folderOpen`) | VS Code 打开 + Trust + Allow | ✅ 计算器弹出 |
| `.claude/settings.json` (SessionStart hook) | `claude` 启动，**零交互** | ✅ v2.1.224 下自动执行 |

详见 `autorun-demo/README.md`（含完整复现步骤、踩坑记录与录屏演示）。

## 实验三：AI IDE 的 MCP/配置自动执行面对比

`ide-autorun-demo/` — 把 keyv 的"零安装执行"向量延伸到工作区级 MCP 声明：
实测 ZCode 3.0.96（工作区 `mcp.servers` 命令零交互拉起、hooks 反而被门控——
信任模型不一致）、TRAE SOLO CN 1.107.1（默认关 + 应用级作用域 + 防自改，
三层防御），并与 Claude Code / VS Code 对照。

## 声明

仅用于防御研究与安全教学。不包含、不接受任何武器化代码
（真实持久化、窃密、C2 通信等）。复现均在本地隔离环境完成。
