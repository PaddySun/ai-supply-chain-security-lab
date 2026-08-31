# 实验三：cordis_run 的进程内 vm 求值（工具级，gated）

## 机制（源码见 `../../../docs/dsh-code-reading.md` 第二节）

`dsh-tool-cordis` 暴露五个**模型可见工具**：`cordis_inspect` / `cordis_define` /
`cordis_run` / `cordis_stop` / `cordis_undefine`。其中：

- `cordis_define` 记录一段 host half（Node.js 代码），先只做语法检查。
- `cordis_run` 用 `node:vm` 在 **DSH 进程内** `runInContext` 求值这段代码。

求值在 `createSandbox()` 构造的 vm context 里进行：`require`/`fetch`/定时器被换成
"抛错陷阱"，`process` 为 `undefined`。但沙箱里塞进了多个**宿主 realm 引用**
（`Buffer`、`TextEncoder`/`TextDecoder`、`harness.*` 闭包、`patchDualRealmInstanceof`
传入的宿主 `Object/Function/Error/...`），官方明说：

> The sandbox isolates globals but is **not a security boundary**. ... host-realm
> helpers make escape possible. ... **Treat this toolset like bash access.**

`vmTimeoutMs` 只约束同步部分，`async` body 可逃逸超时。

## 复现（需要 cordis_* 工具被挂进 agent 视图，默认关闭）

1. `cordis_define(name:"demo", purpose:"dsht", code: 见 host-half-example.js)`
2. `cordis_run(name:"demo")`
3. 模型即可调用新注册的工具 `dsh_noinstall_demo_ping`。

## 结论

这是 DSH 里**能力最强**的"不安装执行"通道：模型能在 DSH 进程内动态生成并执行
任意 JS（且可逃逸 vm）。好消息是它**默认被 gated**（本会话工具清单里没有
`cordis_*`）；一旦被挂进某个 agent 预设的工具视图，它等同于把 `eval` + 进程内
任意能力交到模型手上，风险等级官方已自认"当 bash 对待"。
