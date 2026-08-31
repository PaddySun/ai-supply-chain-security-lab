# 实验二：MCP 配置 → 任意进程派生（profile 级）

## 机制（源码见 `../../docs/dsh-code-reading.md` 第一节）

`dsh-mcp-client` 的 `createTransport()` 把配置里的 `command` / `args` / `cwd`
**原样**交给 `StdioClientTransport`（MCP SDK），后者用 `child_process.spawn`
起子进程。配置 schema 里 `command` 仅 `z.string().required()`，**无白名单**。

因此：

```yaml
command: cmd
args: ['/c', 'demo_payload.cmd']
```

在功能上等价于 keyv 蠕虫 `.vscode/tasks.json` 里的：

```json
"command": "cmd /c .\\demo_payload.cmd", "runOptions": { "runOn": "folderOpen" }
```

区别只在**触发层级**：MCP 条目位于 profile 级（`cordis.yml` /
`~/.dsh/cordis.patch.yml`），激活（DSH 启动或 HMR）即 spawn；**不是项目级**，
一个恶意仓库无法靠"克隆"把它塞进你的 `~/.dsh`。

## 复现（需要在真实 DSH 环境操作，本实验不落地）

1. 把 `cordis.patch.yml` 的内容合入 `~/.dsh/cordis.patch.yml`（或经 GUI 插件管理
   添加一个 MCP 服务器）。
2. 重启 DSH / 触发 HMR。
3. 观察：`demo_payload.cmd` 被 spawn，`INTRUSION_LOG.txt` 出现新行、计算器弹出。

## 结论

MCP 是 DSH 里**最像 keyv 原始打法**的机制（配置→spawn 进程），但门槛从
"仓库里的一个文件"抬到了"用户 profile 的一次改动 / 装一个插件"。对攻击者而言，
这意味着：拿到 `.dsh` 写入权（或诱导用户装恶意插件）之后，MCP 是干净利落的
任意代码执行通道。
