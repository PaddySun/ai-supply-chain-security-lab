# 源码逐行阅读：DSH 的两条"自动执行"路径

阅读对象：`@deepseek-ai/dsh@0.1.1-rc.2`（已编译产物 `lib/*.js`）。
安装源：`~/.npm/_npx/*/node_modules/@deepseek-ai/`。

---

## 一、`dsh-mcp-client` 的进程派生（配置 → spawn）

文件：`node_modules/@deepseek-ai/dsh-mcp-client/lib/index.js`（共 785 行）。

### 1. 依赖

```js
// L5
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";
// L7
import { scrubbedParentEnv } from "@deepseek-ai/dsh-subprocess";
```

- `StdioClientTransport` 是 MCP 官方 SDK 的 stdio 传输，**内部用
  `child_process.spawn(command, args, { env, cwd, stdio: 'pipe' })`** 起子进程。
- `scrubbedParentEnv` 是 DSH 的统一"环境擦洗"函数（见下）。

### 2. 环境组装（L27–32）

```js
function buildChildEnv(extra) {
    return { ...scrubbedParentEnv(), ...extra };
}
```

先铺擦洗后的父环境，再叠加 MCP 配置里**显式**写的 `env`。含义：擦洗只防"隐式
泄漏"，**显式 `env` 在擦洗之后合并**——攻击者可故意把任意秘密转发进子进程。

### 3. 传输工厂（L39–49）—— 核心

```js
function createTransport(config) {
    switch (config.transport) {
        case "stdio": return new StdioClientTransport({
            command: config.command,   // ← 任意可执行文件，无白名单
            args: config.args,         // ← 任意参数
            env: buildChildEnv(config.env),
            cwd: config.cwd            // ← 任意工作目录
        });
        case "streamable-http": return new StreamableHTTPClientTransport(...);
    }
}
```

`command` / `args` / `cwd` **原样透传**给 SDK 去 `spawn`。没有任何"只允许
`npx`/`node`/白名单命令"的校验。写 `command: cmd, args: ['/c','demo_payload.cmd']`
即等价于 keyv 蠕虫 `.vscode/tasks.json` 里的 `command: cmd /c .\demo_payload.cmd`。

### 4. 配置 schema（L738–756）

```js
const Config = z.union([z.object({
    transport: z.const("stdio"),
    serverName: z.string().required().pattern(SERVER_NAME_PATTERN),
    command: z.string().required(),      // 只要求是字符串，不校验它是什么
    args: z.array(String).default([]),
    env: z.dict(String).default({}),
    cwd: z.string().default(""),
    ...
}), ...]);
```

确认：`command` 仅 `z.string().required()`，无枚举、无 allowlist、无 deny 逻辑。

### 5. 激活即连接（L765–783）

```js
async function apply(ctx, config) {
    ...
    const connection = startConnection(ctx, config, reconnect);
    ...
    const outcome = await connection.ready;   // 激活 = spawn + 握手 + 工具发现
    if (outcome.error !== void 0 && config.failOnStartupError) throw ...
}
```

Cordis 插件 `apply` 在装配时执行 → **DSH 启动（或 HMR 加载该插件）时即 spawn**。
`failOnStartupError` 默认 `false`：spawn/握手失败**不报错**，静默带 0 工具激活。

### 6. 环境擦洗的边界（`dsh-subprocess/lib/index.js`）

```js
// L31
const SENSITIVE_ENV_PATTERN = /KEY|PASSWORD|SECRET|TOKEN/i;
// L12
const DSH_ENV_PREFIX = "DSH_";

// L46–50
function scrubbedParentEnv() {
    const env = {};
    for (const [key, value] of Object.entries(process.env))
        if (value !== void 0
            && !SENSITIVE_ENV_PATTERN.test(key)         // 名字含 KEY/PASSWORD/SECRET/TOKEN 的剔除
            && !key.toUpperCase().startsWith("DSH_"))   // DSH_* 全部剔除
            env[key] = value;
    return env;
}
```

结论：这是**名字启发式**擦洗，不是安全边界。`PATH`/`HOME`/代理保留（子进程能正常
起 CLI）；攻击者通过 MCP 的显式 `env` 仍可注入任意变量。

**小结（实验二的依据）**：MCP 服务器 = 一条"配置即派生任意进程"的通道，进程以
DSH 宿主用户权限运行，无沙箱、无命令白名单。唯一门槛是它位于 **profile 级**
（`cordis.yml` / `~/.dsh/cordis.patch.yml`），不是项目级。

---

## 二、`dsh-cordis-host-runner` 的 vm 沙箱（进程内 eval）

文件：`node_modules/@deepseek-ai/dsh-cordis-host-runner/lib/index.js`（共 2596 行）。
该包是 `dsh-tool-cordis`（`cordis_define`/`cordis_run`/`cordis_stop`/`cordis_undefine`/
`cordis_inspect` 五个**模型可见工具**）的运行时底座。

### 1. 依赖与自述（L8, L1069–1080）

```js
// L8
import { Script, createContext, runInContext } from "node:vm";
```

模块注释原文（L1069–1080，重点）：

> The `node:vm` sandbox a dynamic package's HOST half evaluates in: a fresh realm
> ... callable traps over the Node APIs the sandbox deliberately withholds.
> ... **is not containment: host-realm helper functions remain an escape route.**

官方已明说：这是给"诚实代码"的隔离，**不是安全边界**，宿主 realm 的 helper 函数
仍是逃逸通道。

### 2. Node API 陷阱（L1195–1211）

```js
const NODE_API_REDIRECTS = {
    require: "Node modules are unavailable...",
    setTimeout: TIMER_REDIRECT,
    setInterval: TIMER_REDIRECT,
    setImmediate: TIMER_REDIRECT,
    clearTimeout: TIMER_REDIRECT,
    clearInterval: TIMER_REDIRECT,
    fetch: "Network access goes through the cordis web service...",
};
function nodeApiTraps() {
    const traps = {};
    for (const [name, redirect] of Object.entries(NODE_API_REDIRECTS))
        traps[name] = () => { throw new Error(`${name} is not available... — ${redirect}`); };
    return traps;
}
```

注意：**`process` 不在陷阱表里**（L1190–1193 注释：数据型全局保持 `undefined`，
避免 `typeof process` 探测触发抛错）。`require`/`fetch`/定时器被换成"抛错陷阱"。

### 3. 沙箱构造（L1220–1237）—— 逃逸线索集中地

```js
function createSandbox(id, harnessExtras = {}) {
    const sandbox = {
        ...nodeApiTraps(),
        console: taggedConsole(id),          // 宿主 console 的包装（写宿主 stdout）
        harness: {
            defineTool: sandboxDefineTool,    // ← 宿主闭包
            registerTool: sandboxRegisterTool,// ← 宿主闭包
            ...harnessExtras                  // ← handle() 也是宿主闭包
        },
        btoa: (s) => Buffer.from(s, "utf-8").toString("base64"), // ← 宿主 Buffer
        atob: (s) => Buffer.from(s, "base64").toString("utf-8"), // ← 宿主 Buffer
        TextEncoder,                          // ← 宿主构造器直接传入
        TextDecoder                           // ← 宿主构造器直接传入
    };
    createContext(sandbox);
    patchDualRealmInstanceof(sandbox);
    return sandbox;
}
```

沙箱里被塞进了多个**宿主 realm 的引用**（`Buffer`、`TextEncoder`/`TextDecoder`、
`harness.*` 闭包）——这正是"host-realm helper functions remain an escape route"
的落点：经典的 `vm` 逃逸只需要拿到一个宿主 realm 的函数引用即可桥接回宿主全局。

### 4. 双 realm `instanceof` 补丁（L1155–1186）

```js
const DUAL_REALM_INSTANCEOF_PRELUDE = `
(hostIntrinsics) => {
  ...
  for (const name of Object.keys(hostIntrinsics)) {
    const VmCtor = globalThis[name]
    const HostCtor = hostIntrinsics[name]   // ← 宿主构造器被当参数传进沙箱
    ...
  }
}`;
function patchDualRealmInstanceof(sandbox) {
    runInContext(DUAL_REALM_INSTANCEOF_PRELUDE, sandbox)({
        Object, Array, Function, Error, TypeError, RangeError,
        SyntaxError, Promise, RegExp, Date, Map, Set   // ← 宿主 intrinsics 全传进去
    });
}
```

又把宿主 `Object/Function/Error/.../Map/Set` 整组传进沙箱——第二个宿主引用桥。

### 5. 求值（L1317–1337）

```js
async function evaluateHostCode(sandbox, code, id, vmTimeoutMs) {
    try {
        return await runInContext(`(async () => {\n${code}\n})()`, sandbox, {
            filename: `cordis-dyn-${id}.js`,
            timeout: vmTimeoutMs
        });
    } catch (error) { ... }
}
```

模型提交的 host half 被包成 `(async () => { <code> })()` 在 vm 里跑。注释（L1317–1319）
明说：`vmTimeoutMs` **只约束同步部分，async body 逃逸超时**。

### 6. 启动（L2273–2294）

```js
async startHost(plugin, hostCode, run) {
    const handle = (method, fn) => { ... };   // 宿主闭包
    try {
        const evaluated = await evaluateHostCode(
            createSandbox(plugin.pluginId, { handle }), hostCode, plugin.pluginId, this.resolved.vmTimeoutMs);
        if (!isPlugin(evaluated)) throw new Error(...); // 必须 return 一个 plugin
        run.fiber = await startHostHalf(this.requireGroup(), evaluated, ...);
        return;
    } catch (error) { ... }
}
```

求值结果必须是"插件形状"（函数或 `{ apply(ctx) }`），随后包成 guarded plugin、
挂成子 fiber 启动；其 `apply(ctx)` 拿到的 `ctx` 是白名单 façade
（`sandboxContext`，L629–660：只暴露 `ctx.tools.register`/`ctx.on`/`ctx.provide`/
定时器 + 声明注入的服务，并拒绝返回 `Context`）。

### 7. 官方定性（`dsh-tool-cordis/README.md`）

> The sandbox isolates globals but is **not a security boundary**. ... host-realm
> helpers make escape possible. ... **Treat this toolset like bash access.**

---

## 三、两条路径的差异总结

| | MCP 派生（实验二） | cordis eval（实验三） |
|---|---|---|
| 触发物 | `cordis.yml` 里一条插件配置 | 模型调用 `cordis_define`+`cordis_run` |
| 执行域 | **新子进程**（宿主用户权限，无沙箱） | **DSH 进程内 vm**（可逃逸） |
| 命令约束 | `command` 任意字符串，无白名单 | 任意 JS，仅"必须 return 插件" |
| 超时 | 无（SDK 默认 60s 握手） | `vmTimeoutMs` 只约束同步部分 |
| 入口层级 | profile 级 | 工具级（默认 gated） |
| 门槛 | 需改 `~/.dsh/cordis.patch.yml` 或装插件 | 需 `cordis_*` 工具被挂进 agent 视图 |
