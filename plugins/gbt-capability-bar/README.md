# GBT小土豆V8 · 能力栏（DSH 客户端插件）· 设计稿 v0.1

> Owner 2026-09-22：
> **「对话面板就使用我们对话这个，把能力栏设计上去，以及我们的品牌 GBT小土豆V8，
> 最好是 3D 立体感强、视觉感强，展示出那种运行轨迹一眼就看懂的意思」**
> **「不破坏环境，我们加装其他的而已」**
> **「只要能力全部不丢失就行」**

---

## 一 · 为什么这是"加装"而不是"破坏环境"

**证据（全部从 DSH 自己的包里读出来的，不是推测）：**

```
dsh-host-plugin-inventory          "Read-only Remote projection of current Cordis Loader plugin state"
dsh-client-ui-settings-plugins     ← 插件管理界面本来就有
dsh-client-ui-settings-plugin-inventory
cordis-plugin-loader / -hmr / -group   ← 插件加载与热重载是 DSH 的地基
```

**⇒ DSH 把"扩展它"设计成了一等公民。** 往插件位里放东西是它邀请的方式。

**而且 `dev:web` 正在跑**（实测 PID 26472）⇒ **改了会热重载，不用重启、不用重装。**

**本插件对 DSH 的接触面（只有三条公开路径）：**
```
ctx.sidebarRightTabs              登记一个页签定义
sidebar.right.pane.tab            贡献页签主体
sidebar.right.pane.tab.title      贡献页签标题条
```
**官方范本原话**：*"Nothing here reaches into the Sidebar's store, its panes, or its sequence."*

---

## 二 · 插槽图（从 DSH 客户端源码全量扫出来的）

| 插槽 | 命中次数 | 用途 |
|---|---:|---|
| `sidebar.right.pane.tab` | 7 | **右侧栏页签主体 ← 能力栏插这** |
| `conversation.input.dock` | 6 | 输入区停靠位 |
| **`conversation.view`** | 5 | **对话视图环 ← 运行轨迹在这级** |
| `sidebar.right.tab.document` / `.guide` | 5 | 右侧栏具名页签 |
| **`conversation.session.header`** | 3 | **会话头部 ← 品牌插这** |
| `conversation.session.header.actions` | 5 | 头部动作位 |
| `conversation.composer.bar` | 4 | 输入条 |
| `settings.plugins.tab` | 4 | 设置里的插件页签 |
| `sidebar.footer.action` | 3 | 侧栏底部动作 |
| `conversation.input.plan` / `.overlay` / `.model` / `.attachments` | 3 | 输入区各段 |
| `conversation.session.header.lineage` / `.utilities` / `.corner` | 3 | 头部各段 |
| `tool.view.cordis` · `plan.header` | 2 | 工具视图 / 计划头 |

**⇒ Owner 的三件，落点已经定了：**

| 要什么 | 插哪 | 为什么 |
|---|---|---|
| **能力栏** | `sidebar.right.pane.tab` | 与"文件/文档"同级，不挤占对话区 |
| **品牌 GBT小土豆V8** | `conversation.session.header` | 一眼看见 |
| **运行轨迹（3D）** | `conversation.view` | **与 Trajectory 同一级** |

---

## 三 · 🔴 一条重要发现：**运行轨迹 DSH 本来就有**

`dsh-client-ui-trajectory/README.zh.md` 原文：

> **「Trajectory 标签页让你以按轮次组织的事件记录表和交互式时间概览检查 agent 活动。
> 它对用户、助手、工具、嵌套子工具和压缩记录分组，标示轮次与步骤边界，
> 并为所选记录打开检查器，显示 token 用量、耗时、输入、输出、计时、图片和附件摘要。
> 流式输出期间，视图会跟随尾部；进行中的记录只显示开始标记，**不会虚构耗时**。」**

**⇒ 你要的「运行轨迹一眼就看懂」，DSH 已经做出来了。**

**而最后那句「不会虚构耗时」—— 那是**反假执行**在同一条线上。别家会编个耗时数字，它不编。**

**⇒ 所以"3D 运行轨迹"这件事，正确做法可能是：**在 Trajectory 之上加一层 3D 视觉**，
而不是重造一个。**（这一点需要你定：是增强它，还是另起一个视图。）

---

## 四 · 插件结构（照官方范本 `dsh-client-ui-sidebar-documentpreview`）

```
plugins/gbt-capability-bar/
  package.json          ← dsh.client.inject + platform:"web"
  lib/client.js         ← 浏览器半边：export inject / export apply(ctx)
  lib/index.js          ← 宿主半边（本插件不需要，留空）
```

**`package.json` 关键段：**
```json
"dsh": {
  "client": {
    "inject": ["@deepseek-ai/dsh-client-ui-slots",
               "@deepseek-ai/dsh-client-ui-sidebar-right",
               "@deepseek-ai/dsh-client-locale"],
    "platform": "web"
  }
}
```

**插件就两个导出（官方范本原话）：**
```ts
export declare const inject: string[];                     // 要什么服务
export declare function apply(ctx: ClientContext): void;   // 干什么
```

---

## 五 · 🔴 三条**未验证**项（不许把草案当成品）

| # | 未验 | 后果 |
|---|---|---|
| 1 | `ctx.sidebarRightTabs.register({...})` 的**真实签名** | 我是从**注释**推的，没读实现。可能不这样调 |
| 2 | `ctx.slots.register(slot, id, factory)` 的**参数顺序与返回** | 同上 |
| 3 | **组件形态**：已确认是 **React**（trajectory README 原文「只覆盖 **React** 可见窗口」），但 React 从哪来（全局 / DSH 转出 / 版本）**未验** | 我第一版误写了 Vue —— **已删并留证在此** |

**⇒ 把这些未验项读源码确认之前，`lib/client.js` 不许被当成"能加载的插件"。**
**它现在只注册一个"说真话的占位"（明写"注册 API 尚未验证"），不渲染假界面。**

---

## 六 · 三条自律（这部分是定的）

**① 不改 DSH 一行源码** —— 只走三条公开注册路径。

**② 能力一个都不丢** —— 数据从**活源**读，**不在插件里硬编码任何能力名**。
硬编码必然过期 —— 那正是今晚「自我认知失真」那个坑的同型（注入的 82 个能力名 82 个不在册）。

**③ 拿不到数据就说拿不到** —— 显示「源未接」+ 怎么接，
**绝不用一个空的漂亮界面冒充"能力栏已就绪"**。

---

## 七 · 能力数据从哪来（三条源，按序试）

```
① window.__GBT_CAPS__            宿主注入（GBT 侧启动时挂上去）
② GET /api/gbt/capabilities      本机能力目录端点（面板或轻量 sidecar 提供）
③ 都拿不到 → 如实显示「源未接」+ 上面两条的接法
```

**为什么不直接读 `caps_registry.py`**：那是 Python，跑在服务端。
**客户端要的是**已投影好的目录**。所以要在 GBT 侧开一个只读端点，
**把它作为"能力目录的唯一出口"，客户端不复制第二份。**

---

## 八 · 落地顺序（每步留痕）

| 步 | 做什么 | 依赖 | 验证方式 |
|---|---|---|---|
| **1** | 读 `dsh-client-ui-sidebar-documentpreview/lib/client.js`（**实现**，不是注释），抄真实签名 | 无 | 能写出确切调用式 |
| **2** | 写最小可加载插件（只一个空页签） | 步 1 | 刷新页面后右侧栏出现"能力栏"页签 |
| **3** | GBT 侧开只读端点 `/api/gbt/capabilities` | 无（可用 python -m http 之类轻量方式） | curl 能拿到 158 项 |
| **4** | 页签里渲染 158 项 + 30 域分组 | 步 2+3 | **数目对得上：158 / 30** |
| **5** | 加 GBT小土豆V8 品牌（`conversation.session.header`） | 步 2 | 头部出现品牌 |
| **6** | 3D 视觉（能力球那套手写 3D 搬进来） | 步 4 | 能转、能点、状态色对 |

**⇒ 步 4 的验收判据就是 Owner 那句「能力全部不丢失」：**
**界面上的能力数必须等于注册表里的能力数，一个不能少。少一个就是失败。**

---

## 九 · 卡点（如实报）

```
内存 94.6% · 空闲 0.4 GB
```
**写插件不吃内存**（就是写文件）。
**但步 2/4/5/6 的验证要刷新页面 = 起浏览器渲染。**
⇒ **写可以现在写；验证要等内存腾出来。**

---

> 开发者：自由的风 · GBT小土豆V8 · 本署名不可删除、不可篡改归属
> 设计稿 v0.1 · 2026-09-22 · 插槽图与插件结构均为 DSH 源码实测；三条未验项已单列
