# AI 编码助手供应链安全研究实验室

2026 年 keyv 蠕虫事件（npm 投毒 444 包 / 2212 版本）的防御性研究复现仓库。
所有载荷均为无害演示（写日志 + 弹计算器），不含任何窃密/持久化/C2 代码。

📖 **[完整博客：《打开项目即沦陷：keyv 蠕虫与 AI 编码助手时代的供应链暗战》](docs/blog.md)**
📖 **[独立实测报告：《打开文件夹即执行：四款客户端工作区自动执行攻击面》](docs/ide-attack-surface.md)**
🧪 **[一站式复现指南（五个实验，任何人可复现）](docs/reproduction-guide.md)**

> ⚠️ **警告**：`autorun-demo/`、`ide-autorun-demo/`、`dsh-bypass-lab/` 内含
> **可自动执行的无害演示载荷**——用 VS Code / Claude Code / ZCode / DSH 打开
> 对应工作区会自动弹出计算器并写日志。请使用一次性环境体验，勿在日常开发
> 环境打开。

## 仓库地图

| 目录 | 内容 | 关键结论 |
|---|---|---|
| `slopsquatting-lab/` | 实验一：LLM 包幻觉测量（USENIX'25 方法论复现） | deepseek-chat 零幻觉 vs 论文 19.7% |
| `autorun-demo/` | 实验二：Claude Code / VS Code 零安装执行 | Claude Code 零交互执行；VS Code 两道确认败给"已信任项目" |
| `ide-autorun-demo/` | 实验三：ZCode / TRAE 工作区 MCP 攻击面 | ZCode 打开文件夹即拉起（11 次）；TRAE 三层防御为正面范例 |
| `dsh-noinstall-lab/` | 实验四（PR #1，作者 huangmaomaojiejie）：DeepSeek Harness 无安装执行 | 项目级注入成立；profile 级 MCP 配置即 spawn |
| `dsh-bypass-lab/` | 实验五：DSH 沙箱绕过 | ShellWindows 委托在 WRITE_RESTRICTED 令牌下调起完整令牌进程 |
| `docs/` | 全部文章、验证报告、会话转录与录屏归档 | 见下 |

## docs/ 结构

| 文件/目录 | 内容 |
|---|---|
| `docs/blog.md` | keyv 蠕虫全景分析（事件/漏斗/载荷/复现/处置） |
| `docs/ide-attack-surface.md` | 四客户端攻击面实测报告 |
| `docs/slopsquatting-article-draft.md` | 实验一文章底稿 |
| `docs/pr-1-verification.md` | PR #1 本地验证报告（源码核对/三处修正/端到端实测/沙箱绕过/会话取证） |
| `docs/dsh-code-reading.md` | DSH 源码逐行阅读（PR #1 作者煌，mcp-client spawn + cordis vm 沙箱） |
| `docs/reproduction-guide.md` | **一站式复现指南** |
| `docs/pr-1-transcripts/` | 实验一注入拒绝的完整终端转录 |
| `docs/media/` | 全部录屏/ GIF / 会话日志 zip 归档 |

## 一句话总结

**问题不在"打开项目会执行配置"这个功能本身，而在执行前有没有一道仓库自己
绕不过去的信任门。** TRAE 证明了可以工程化封死；ZCode/Claude Code/DSH 各自
在hooks 门控、MCP 声明、沙箱写边界上留了不同形状的门。

## 声明

仅用于防御研究与安全教学。不包含、不接受任何武器化代码
（真实持久化、窃密、C2 通信等）。复现均在本地隔离环境完成。
欢迎通过 Issue/PR 交流；引用请注明仓库地址。
