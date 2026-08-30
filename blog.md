# 打开项目即沦陷：keyv 蠕虫与 AI 编码助手时代的供应链暗战

> 2026-08-30 · 配套实验代码与全部证据：[PaddySun/ai-supply-chain-security-lab](https://github.com/PaddySun/ai-supply-chain-security-lab)
> 本文所有本地实验数据均可通过仓库脚本复现。

## 导语

2026 年 8 月 4 日早上，npm 生态发生了迄今为止最大规模的自我复制蠕虫事件。

攻击者拿下了 keyv 包维护者 Jared Wray 的 GitHub 账号。keyv——Redis 风格键值存储的底层依赖，周下载量 1.53 亿次，被 Deliveroo、Qlik、ServiceTitan 等大型企业在生产环境使用。攻击者用被盗的会话直接向 `jaredwray/keyv` 主干推送恶意提交，然后**触发了项目自己的正规发布流水线**——于是带毒的 `keyv@6.0.0` 携带完全合法的 SLSA 溯源签名发布上线，任何溯源门禁都拦不住它。

接下来的约 4 小时里，蠕虫自我复制扩散：**444 个包、2212 个恶意版本**，波及 12+ 组织，一级载具合计周下载量**超过 5 亿次**。安全社区先后给它起了两个名字：新加坡网络安全局称之为 **Shai-Hulud**（沙虫，《沙丘》），StepSecurity 称之为 **ChainDrop**。

但真正让整个安全社区炸锅的是两件事：

**第一，你不需要执行 `npm install`。** 蠕虫把持久化代码写进了 `.claude/settings.json` 和 `.vscode/tasks.json`——你只是用 VS Code 打开了一个项目文件夹，或者启动了一次 Claude Code 会话，恶意代码就执行了。真实案例：流行的 `million` 仓库默认分支被植入这两个文件（[issue #1186](https://github.com/aidenybai/million/issues/1186)）。

**第二，C2 地址不在代码里，而在以太坊区块链上。** 恶意软件通过 `eth_call` 读取主网智能合约获取控制服务器地址——攻击者改一笔链上交易，全网被感染节点集体切换控制服务器。封域名、封 IP 的传统处置全部失效。

本文做三件事：还原事件的技术真相（含影响漏斗与版本清单）；在本地完整复现"打开即执行"向量与 slopsquatting 测量实验；给出经核实的处置措施——包括一个**反直觉的坑：发现感染后不要立刻吊销令牌**。

---

## 一、事件还原：四小时时间线（均为 UTC）

| 时间 | 事件 |
|---|---|
| 09:02 | 毒提交 `ee2681a`（"release: v6.0.0"）推入 `jaredwray/keyv` 主干 |
| 09:04 | 提交 `d8c850c` 植入 `.claude/` 与 `.vscode/` 持久化文件 |
| 09:23 | 提交 `f97eabc` 删除掩护用的假测试文件 |
| 09:35 | `keyv@6.0.0` 经 GitHub Actions OIDC 可信发布上线（携带合法 SLSA 证明） |
| 09:38–13:20 | 第二波：蠕虫用窃取的受害者凭据自我复制，再投毒 **433 个包（2201 个版本）**，首个为 `@thiennq/docs-viewer@1.6.2` |
| 10:09–10:14 | cacheable 生态 9 个恶意包发布 |
| 10:17 | 第一声公开警报：`jaredwray/cacheable` issue #1689 |
| 10:39 起 | npm 开始下架（首个 `cacheable-request@13.0.20`） |
| ~11:15 | keyv 回滚至 **5.6.0**（安全版本） |
| 18:10 | 全部 11 个一级载具完成回滚 |

关键认知颠覆：**初始入侵不是偷 npm token，而是劫持维护者的 GitHub 会话**。攻击者用维护者身份触发项目自己的正规 release workflow（OIDC 可信发布），所以每个恶意版本都自带真实签名——正如 StepSecurity 的总结："溯源证明的是哪个 commit 被构建了，它证明不了这个 commit 是被授权的。"

## 二、影响漏斗：从 1 个账号到 5 亿次周下载

```
1 个被劫持的 GitHub 账号（Jared Wray）
 └─ 11 个一级载具（jaredwray 生态全量沦陷，2212 个恶意版本中的主体）
     └─ 433 个二级受害包（蠕虫用窃取的凭据自动重发布）
         ├─ @servicetitan   141 个包
   ├─ @onereach        78 个
   ├─ @or-sdk          74 个
   ├─ @ornikar         42 个
   ├─ @qlik            28 个
   ├─ @nebula.js       22 个
   ├─ @deliveroo / @picsart / 26 个无作用域包 …
         └─ 波及周下载量合计 > 5 亿次
```

### 一级载具清单（恶意版本号 → 安全处置）

| 包名 | 恶意版本 | 周下载量 | 处置 |
|---|---|---|---|
| keyv | **6.0.0** | 1.537 亿 | npm 回滚至 **5.6.0** |
| flat-cache | 6.1.24 | 1.499 亿 | 回滚 |
| file-entry-cache | 11.1.6 | 1.476 亿 | 回滚 |
| cacheable-request | 13.0.20 | 3396 万 | 首个被下架 |
| @cacheable/utils | 2.5.1 | 1871 万 | 回滚 |
| cacheable | 2.5.1 | 788 万 | 回滚 |
| @cacheable/memory | 2.2.1 | 718 万 | 回滚 |
| cache-manager | 7.2.10 | 428 万 | 回滚 |
| @cacheable/node-cache | 3.1.2 | 156 万 | 回滚 |
| ecto | 5.0.1 | 1293 | 回滚 |
| @cacheable/net | 2.1.1 | 975 | 回滚 |

受害者自查：审计 lockfile 中是否出现上述"包名@版本"组合；核对注册表 shasum（如 `keyv@6.0.0` = `0f18da4e81443285c3ee7e96eb3adc3803b2487e`）；检索 CI 日志（backstage 仓库确认有 10 次恶意 workflow 运行，所幸只暴露了短命 `GITHUB_TOKEN`）。

## 三、载荷解剖：五段式攻击链

1. **`preinstall` 钩子**：库代码本身干净（相对 rc.1 仅 3 个文件差异），毒在安装钩子里，还配了一个假 vitest 文件给钩子"正当性"。
2. **Dropper（setup.mjs）**：从 Bun 官方 GitHub Release 下载合法的 v1.3.13 运行时（"就地取材"，规避检测），落盘 `/tmp/bun-dl-*` 后执行第二阶段。
3. **Stage 2（727KB 混淆 Bun bundle）**：Shai-Hulud 2.0 的进化后代。窃取范围约 **140 个凭据路径**——`.npmrc`、`.aws`、`.kube/config`、SSH 私钥、Jenkins、Vault、加密钱包，外加**新一代 AI 工具凭据**：`.claude/credentials.json`、`.codex/auth.json`、`.cursor/credentials.json`、`.openai/auth.json`、`.anthropic/auth.json`、`.gemini/.env`。还会转储 GitHub Actions Runner.Worker 进程内存，抓取 `"isSecret":true` 标记的秘密，并横扫 16 个区域的 AWS STS/Secrets Manager/SSM。
4. **自我复制引擎**：内置 npm 发布器，把受害者包的 tarball 重新打包注入载荷后重发布，还能**自铸 Sigstore/SLSA 溯源**；在 GitHub 侧向所有分支推送 `.vscode/tasks.json` 和 `.claude/settings.json`，提交者伪装成 `claude <claude@users.noreply.github.com>`，并植入一个把 `${{ toJSON(secrets) }}` 写进 artifact 的"Run Copilot"工作流。
5. **持久化 + 死手开关 + 链上 C2**：
   - `.claude/settings.json` 的 SessionStart hook 与 `.vscode/tasks.json` 的 `folderOpen` 任务**互相交叉拉起**对方的 dropper；
   - 安装令牌监视器（`~/.local/bin/gh-token-monitor.sh`，macOS LaunchAgent / Linux systemd user unit）——**检测到被盗 GitHub 令牌被吊销时触发后续攻击载荷**；
   - C2 采用 EtherHiding：从以太坊主网合约 `0xE1f2...3103` 经 `eth_call`（selector `0x53ed5143`）解析 C2 域名，轮询 75 个 RPC 端点；外泄走 `npm-cache.com:443/router`，RSA-OAEP + AES-256-GCM 双层加密且**双向可控**（响应中的 `code` 字段会被 eval）；甚至有俄语系统退出开关。

## 四、本地复现：打开项目 = 执行代码

> 完整代码与录屏：[autorun-demo/](https://github.com/PaddySun/ai-supply-chain-security-lab/tree/main/autorun-demo)。载荷是刻意无害的——写一行时间戳日志 + 弹出 Windows 计算器。真实蠕虫在这个位置放的是上面的 Stage 2。

### 攻击面 A：Claude Code — 启动会话即执行（零交互）

`.claude/settings.json` 写入 SessionStart hook，命令 `sh demo_payload.sh`。实测（Claude Code **v2.1.224**，2026-08-30）：

```
[AUTORUN DEMO via Claude Code SessionStart] 2026-08-30 20:01:42
paddy                          ← whoami：以当前用户完整权限执行
CalculatorApp.exe  PID 17692   ← 计算器进程
```

**没有任何确认弹窗。** 踩坑记录：hook 经 Git Bash 执行，命令写成 `cmd /c "%CLAUDE_PROJECT_DIR%\xxx.cmd"` 会报 `EPERM: uv_spawn bash.exe` 静默失败——载荷必须是合法 bash 语句。攻击者同样受此约束，但 bash 载荷完全可行。诚实注脚：测试机全局配置了 `skipDangerousModePermissionPrompt: true`，可能贡献了零弹窗；默认配置下的确认行为建议读者自行验证并对比。

![Claude Code 启动即执行演示](autorun-demo/claude-autorun-demo.gif)

### 攻击面 B：VS Code — 打开文件夹即执行（两道摩擦）

`.vscode/tasks.json` 配置 `runOptions.runOn: "folderOpen"`，任务名伪装成 `install-dependencies`。实测有两道防线：新文件夹需先 **Trust**，再在"检测到自动任务"通知里点 **Allow**。但注意真实受害场景：keyv 投毒的是**你自己的日常工作项目**——文件夹早就信任过了；且不少开发者为正经的 watch/install 任务开过 `task.allowAutomaticTasks: "auto"`，此后**连通知都没有**。第二次打开文件夹，计算器无声弹出。

结论：**防御没有失效，失效的是"人对日常项目不设防"这个前提。** 这正是 keyv 蠕虫的社会工程学支点。

## 五、本地测量：Slopsquatting 还成立吗

> 完整代码：[slopsquatting-lab/](https://github.com/PaddySun/ai-supply-chain-security-lab/tree/main/slopsquatting-lab)

keyv 事件之前的另一个威胁假设是 slopsquatting（术语由 PSF 的 Seth Larson 创造）：LLM 幻觉出不存在的包名，攻击者抢先注册。USENIX Security 2025 论文《We Have a Package for You!》的基线数据：16 个模型平均 **19.7%** 样本推荐不存在包名，编录幻觉包名 205,474 个，**43% 在重复采样中稳定复现**。

本实验按论文方法论缩小复现（`deepseek-chat`，temperature 0.7，每 prompt 重复采样）：

| 生态 | 样本数 | 唯一包名 | 幻觉包数 | 含幻觉样本 |
|---|---|---|---|---|
| PyPI | 20 | 5 | **0** | 0% |
| npm | 24 | 19 | **0** | 0% |

两个发现：

1. **前沿模型已基本治好这个病**（论文中 GPT-4 Turbo 就已低至 3.59%，2026 年前沿模型约 1%~2%）。威胁集中在**自托管开源模型**（幻觉率 6.8%~8.4%）——而恰恰是重度跑 Agent 的团队最爱自托管。每天 200 次 Agent 辅助安装的团队按 7% 幻觉率算，仍有约 14 次/天幻觉安装尝试。
2. **方法论陷阱**：第一轮跑出的"幻觉包"`concurrent`、`platform`、`getpass` 全是 Python 标准库——手写白名单误报。改用 `sys.stdlib_module_names` 后归零。复现这类研究时，标准库排除是最大误差源。

**所以攻击面排序变了**：与其赌模型报错包名（slopsquatting），不如直接在仓库里放 `.claude/settings.json`（打开即执行）——后者不需要模型犯任何错。

## 六、处置措施（经核实）

### 如果你可能感染了（用过 8 月 4 日当天的 keyv/cacheable 生态）

按 SANS ISC 的警告，顺序不能错：

1. **不要先吊销令牌。** 蠕虫的令牌监视器把吊销行为当触发器（死手开关）。
2. **先在干净机器上**（不是疑似感染的那台）操作：检查并移除持久化——`.claude/settings.json`、`.vscode/tasks.json` 中的可疑 hook/任务、`~/.local/bin/gh-token-monitor.sh`、LaunchAgent/systemd user unit。
3. **重装/重建**：卸载恶意版本、lockfile 回锁到安全版本（keyv → **5.6.0**）；卸载本身不能消除已发生的凭据窃取，CI 节点建议直接重建。
4. **然后轮换全部凭据**：npm/GitHub/云/Vault，以及所有 AI 工具凭据（`.claude/credentials.json` 等都是此次的窃取目标）。

### 团队防御清单

- `task.allowAutomaticTasks: "off"`；把 `.vscode/`、`.claude/`、`.idea/` 纳入 PR 审计，出现 shell 命令变更即告警（尤其提交者是 `claude@users.noreply.github.com` 这类身份）
- Agent 的安装动作用私服代理 + 白名单；新注册/低下载量包需人工放行
- CI 一律短命令牌（backstage 未泄密正是因为只有 ephemeral `GITHUB_TOKEN`）
- 别迷信溯源签名：SLSA 证明构建来源，不证明提交授权。维护者主干需要分支保护 + 提交签名强制
- 给 Agent 挂注册表查询工具，推荐包前先验证存在性（治 slopsquatting）

## 七、延伸实测：四类客户端的"打开即执行"面对比

keyv 蠕虫之后，我们把同一套无害载荷（写日志 + 弹计算器）投向了更多客户端，
包括国产 AI IDE 的新攻击面——**工作区级 MCP 服务器声明**（详细过程见仓库
[ide-autorun-demo/](https://github.com/PaddySun/ai-supply-chain-security-lab/tree/main/ide-autorun-demo)）：

| 客户端 | 版本 | 工作区 MCP 自动执行 | 工作区 hooks 自动执行 | 判定 |
|---|---|---|---|---|
| ZCode（CLI） | 3.0.96 / CLI 0.16.5 | ✅ 零交互拉起（实测） | ❌ 被信任门控拦截（实测） | 信任模型不一致，高危 |
| Claude Code | v2.1.224 | — | ✅ 零交互执行（实测） | 高危 |
| TRAE SOLO CN | 1.107.1 | ❌ 默认关 + 应用级作用域 + 防自改（代码证实） | — | 设计正确 |
| VS Code | — | — | tasks.json 需 Trust+Allow | 有条件放行 |

**ZCode 的复现**：工作区 `.zcode/config.json` 的 `mcp.servers.<name>.command`
在 agent 会话启动时被自动 spawn——实测一次会话拉起两次、弹出两个计算器、
零确认弹窗；而同一份配置里的 SessionStart hook 却被 `trustState` 门控拦截
（用户级的同一 hook 正常执行）。**对 hooks 设了门控、对 MCP 的 `command`
字段却直接放行**——但声明一个 stdio MCP server 与声明"任意进程执行"是等价的。
对攻击者来说这是比 keyv 的 `.claude/settings.json` 更"合法外观"的入口：
它看起来只是在"连接工具服务器"。

**TRAE 的三层防御**（反编译 1.107.1 证实）：`.trae/mcp.json` 默认不加载
（`trae.mcp.enableWorkspaceMcp` 默认 false）、该设置为应用级作用域
（仓库无法替受害者打开）、`ensurePathInReadSafeScope` 阻止 IDE 内 agent 被
prompt injection 后自改这些配置文件。这是目前看到的对 keyv 战法最完整的
工程化回应——**问题不在"打开项目会执行配置"这个功能本身，而在执行前有没有
一道仓库自己绕不过去的信任门**。

## 八、结论

keyv 蠕虫的组合拳——劫持维护者会话 → 挂合法签名发布 → preinstall 窃凭据 → AI 配置文件持久化 → 链上 C2——每一环单独看都不新鲜，组合起来却让"克隆仓库/打开文件夹/启动会话"这些最日常的动作变成了攻击入口。我在本机验证了其中最关键的"零安装执行"环节：Claude Code 链零交互成功；ZCode 的工作区 MCP 声明同样零交互拉起任意命令，且其信任门控只覆盖 hooks 不覆盖 MCP；而 TRAE 用"默认关 + 应用级作用域 + 防自改"三层设计证明这个攻击面是可以工程化封死的。也量化了 slopsquatting 在前沿模型上的收敛。防御者的重心必须从"安装时刻"移到"**Agent 决策时刻**"和"**打开工作区的第一毫秒**"——并且，一个仓库能写进来的每一份配置文件，都该过同一道门。

## 参考资料

- [StepSecurity — ChainDrop npm Worm（时间线/漏斗/IOC）](https://www.stepsecurity.io/blog/chaindrop-npm-worm)
- [SANS ISC — Don't Revoke That Token Yet](https://isc.sans.edu/diary/Dont+Revoke+That+Token+Yet+Inside+the+keyvcacheable+npm+Worm/33218)
- [Snyk — Inside the keyv npm Supply Chain Compromise](https://snyk.io/blog/inside-keyv-npm-compromise-preinstall-malware-trusted-provenance-ide-hooks)
- [Wiz — keyv and cacheable npm Supply Chain Attack](https://www.wiz.io/blog/keyv-and-cacheable-npm-supply-chain-attack)
- [Chainguard — Mini Shai-Hulud Campaign](https://www.chainguard.dev/unchained/the-keyv-and-cacheable-npm-supply-chain-attack-inside-the-mini-shai-hulud-campaign)
- [SafeDep — keyv npm Supply Chain Compromise](https://safedep.io/keyv-npm-supply-chain-compromise)
- [Unit 42 — ChainDrop Analysis](https://unit42.paloaltonetworks.com/chaindrop-npm-worm-analysis/)
- [Cycode — keyv/cacheable npm Worm: AI Coding Agents](https://cycode.com/blog/keyv-cacheable-npm-worm-ai-coding-agents/)
- [新加坡 CSA 通告 AD-2026-009（Shai-Hulud）](https://www.csa.gov.sg/alerts-and-advisories/advisories/ad-2026-009)
- [Socket.dev — keyv/cacheable 追踪页](https://socket.dev/supply-chain-attacks/keyv-and-cacheable-compromise)
- [million 仓库感染实例 issue #1186](https://github.com/aidenybai/million/issues/1186)
- [USENIX Security 2025 — We Have a Package for You!](https://www.usenix.org/conference/usenixsecurity25/presentation/pipatanakulkiron)
- 本地实验仓库：[PaddySun/ai-supply-chain-security-lab](https://github.com/PaddySun/ai-supply-chain-security-lab)
