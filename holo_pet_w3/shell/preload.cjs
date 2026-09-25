/* GBT小土豆V8 · 上帝视角 · preload（W3 / W9）
 * 只暴露只读 IPC：渲染进程**没有任何数据写口**（V6）—— 不写文件、不发网络、不碰 store。
 *
 * W9 补记：新增一个**动作口** `summon`（数字人召唤）。它不写任何数据，
 * 只让主进程起一个本机窗口；不 kill 任何进程。除它以外全部仍是只读口，
 * 所以 `readonly: true` 的语义限定为"数据面只读"，动作面另立一行如实登记：
 * `non_readonly_capability`。谁要再加动作口，必须同步改这一行，不许悄悄放宽。
 *
 * 开发者：自由的风 · GBT小土豆V8 · 本署名不可删除、不可篡改归属
 */
"use strict";

const { contextBridge, ipcRenderer } = require("electron");

const invoke = (channel, payload) => ipcRenderer.invoke(channel, payload);

contextBridge.exposeInMainWorld("gbtW3", {
  readonly: true,
  non_readonly_capability: "summon（只起一个本机窗口：不写文件、不发网络、不 kill 进程）"
    + " · connectDsh（把主人**运行时**给的对话面 URL 交给窗口加载：只放行本机回环；"
    + "URL 只在内存，**不落盘、不回显**，返回值只给 host）"
    + " · showWindow（一体式 App 铬的跨窗跳转：**只认注册表里已有的窗 id**；"
    + "只改窗口可见性/焦点，不写文件、不出网、不 kill 进程）"
    + " · intercom（**开麦克风采集 + 让本机出声**。第 58 轮加。"
    + "口径：监听随页面生灭、不设开关；真跑的是 intercom.py，它走唯一门 run_task；"
    + "主进程不直接碰 voice_cap、不读凭据、不写文件；关页面即 kill 该子进程）",
  config: () => invoke("w3:config"),
  state: () => invoke("w3:state"),
  tasks: () => invoke("w3:tasks"),
  env: () => invoke("w3:env"),
  ledger: () => invoke("w3:ledger"),
  health: () => invoke("w3:health"),
  matrix: () => invoke("w3:matrix"),
  mindmap: () => invoke("w3:mindmap"),
  selfcheck: () => invoke("w3:selfcheck"),
  introspect: () => invoke("w3:introspect"),
  tools: () => invoke("w3:tools"),
  h1: () => invoke("w3:h1"),
  pets: (payload) => invoke("w3:pets", payload),
  summon: (payload) => invoke("w3:summon", payload),
  connectDsh: (payload) => invoke("w3:connect-dsh", payload),
  showWindow: (payload) => invoke("w3:show-window", payload),
  eigenflux: () => invoke("w3:eigenflux"),
  /* R-H295 新接的两只**只读**审计器（欠账：「覆盖审计接进上帝视角」「零调用点清单接进上帝视角」）。
     两者都是**实时现跑** —— 主进程侧走 /api/capability 真调框架审计器再等 cap_result，
     不是读快照、不是硬编码数字。仍然全部只读，`readonly: true` 语义不变。 */
  coverage: () => invoke("w3:coverage"),
  orphans: () => invoke("w3:orphans"),
  gene: () => invoke("w3:gene"),
  onEvent: (handler) => ipcRenderer.on("w3:event", (_e, msg) => handler(msg)),
  onStreamState: (handler) => ipcRenderer.on("w3:stream", (_e, st) => handler(st)),
  /* 实时流的**现状**（只读拉取 · 2026-09-23 第 45 轮加）。
     上面那个 `onStreamState` 是**推**：只在状态变化时来一次。而窗口可能**在连接之后**才建
     （`startSse` 跑在建窗之前 —— 数据面先立那条规矩），推的那一次就没人听得到。
     ⇒ 补一个拉取口，谁建的窗都能问现状。**只读**，所以不进 `non_readonly_capability`。 */
  streamState: () => invoke("w3:stream-state"),
  /* W3 · **语音对讲**（2026-09-23 第 58 轮加）。这是**动作口**，不是数据面只读：
     它会①开麦克风采集、②让本机出声（TTS）。两件都不是"读"，所以**必须**
     同步登记进上面 `non_readonly_capability` 那一行，不许悄悄放宽。
     口径（主人令）：「打开页面就自动监听，关闭她也跟着关闭」⇒ **不设开关**；
     监听随**页面**生灭，不随进程常驻（大脑后台另算）。
     真跑的是 `tools/codex-scripts/intercom.py`，它内部走唯一门（`five-dim.py cap voice`
     = `api.run_task`）；**主进程不直接碰 voice_cap、不读凭据、不写数据**。 */
  intercom: (op, args) => invoke("w3:intercom", { op: op, args: args || {} }),
  onIntercom: (handler) => ipcRenderer.on("w3:intercom-event", (_e, msg) => handler(msg)),
});