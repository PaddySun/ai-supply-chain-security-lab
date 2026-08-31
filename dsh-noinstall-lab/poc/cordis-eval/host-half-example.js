// 实验三：cordis_run 的进程内 vm 求值（工具级，gated）
//
// ⚠️ 防御性研究示例。这是一个【无害】的 host half：它注册一个名为
// `dsh_noinstall_demo_ping` 的只读工具，返回固定字符串，并写一行宿主 stdout。
// 真实攻击者会在这里：桥接宿主 realm 逃逸 vm（见 docs/code-reading.md 第二节），
// 或直接注入一个提供危险能力的插件。
//
// 用法（需要 cordis_* 工具被挂进 agent 视图，默认关闭）：
//   cordis_define(name:"demo", purpose:"dsht", code: 本文件内容)
//   cordis_run(name:"demo")
// 之后模型即可调用工具 mcp… dsh_noinstall_demo_ping。

return {
  name: 'demo',
  inject: ['tools'],
  apply(ctx) {
    ctx.tools.register({
      name: 'dsh_noinstall_demo_ping',
      description: 'Benign demo tool for the DSH no-install-execution lab. Returns "pong".',
      parameters: { type: 'object', properties: {}, required: [] },
      async execute() {
        console.log('[DSH NO-INSTALL CORDIS DEMO] host half ran in-process');
        return 'pong';
      },
    });
  },
};
