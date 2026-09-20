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
  non_readonly_capability: "summon（只起一个本机窗口：不写文件、不发网络、不 kill 进程）",
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
  eigenflux: () => invoke("w3:eigenflux"),
  onEvent: (handler) => ipcRenderer.on("w3:event", (_e, msg) => handler(msg)),
  onStreamState: (handler) => ipcRenderer.on("w3:stream", (_e, st) => handler(st)),
});