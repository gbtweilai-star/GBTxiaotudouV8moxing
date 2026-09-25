# GBT小土豆V8 · 设置·密钥（DSH 客户端插件）

> 开发者：自由的风 · GBT小土豆V8 · 本署名不可删除、不可篡改归属

Owner 2026-09-22 看图定：「把设置口对齐，另外一个端口在安装上帝视角和其他可视化面板**你别动**，
你就把设置密钥的安装好」

---

## 一、装在哪：`settings.section`

**读 DSH 源码得到**（`dsh-client-ui-settings/lib/types/client/contract/slots.d.ts`）：

> 「A feature owns its own settings pages —— **adding a setting never means
> editing the shell**」

settings 域一共 8 个 seat：

| seat | kind | 用途 |
|---|---|---|
| `settings.trigger` | single | 侧栏底部「设置」按钮的内容 |
| `settings.header` | single | 面板标题 |
| `settings.action` | list | 标题栏动作 |
| `settings.close` | single | 关闭 |
| **`settings.section`** | **list** | **← 本插件落点：自己的一节设置** |
| `settings.plugins.tab` | list | 插件页签 |
| `settings.onboarding` | list | 引导 |
| `settings.general.item` | list | 常规项 |

⇒ 加一节设置的正路 = 往 `settings.section` 注册。**不改 DSH 一行源码。**

---

## 二、**明确不碰**的东西（Owner 明令）

顶部那排标签是 **`conversation.view`** 的位。凭证
（`dsh-client-ui-conversation/lib/types/client/contract/views.d.ts`）：

> 「One conversation view tab, projected from a **'conversation.view'** slot
> entry's registration options」

**那些空位是留给上帝视角和其他可视化面板的。本插件一个都不注册。**
它只占 `settings.section` 一个 seat。

---

## 三、注册 API：抄已验实的写法

抄自 `plugins/gbt-master/lib/client.js:210-218`（那份**已无「未验」标记**，是验过的）：

```js
ctx.slots.inject('<slot>', function () {
  return ctx.slots.register({ name: '<slot>', id: '<id>', order: N }, Component)
})
```

本插件：
```js
export const inject = ['@deepseek-ai/dsh-client-ui-slots']
export function apply(ctx) {
  ctx.slots.inject('settings.section', function () {
    return ctx.slots.register(
      { name: 'settings.section', id: 'gbt-settings-keys', order: 40 },
      KeysSettingsSection)
  })
}
```

---

## 四、数据从哪来：接我们自己的后端（**不硬编码任何密钥**）

后端就是本会话刚建好并端到端实测过的那两个出口
（`holo_pet/panel_server.py`，见 `delivery/20260922-设置面与密钥配置-交付报告.md`）：

| 出口 | 用途 |
|---|---|
| `GET  /api/settings` | 读数：4 组；密钥组含探活 + 34 家供应商已配/未配 |
| `POST /api/settings/action` | `probe / login / logout / providers / add_key / health` |

面板基址默认 `http://127.0.0.1:8765`，可用 `globalThis.__GBT_PANEL_BASE__` 覆盖。

---

## 五、三条自律（写进代码，防止后来人放宽）

1. **绝不回显明文密钥**：后端已打码，前端**也不做"显示原文"按钮**。
2. **密码不落盘**：登录框只把 email/password 发一次换会话；
   前端**不 localStorage、不 cookie、不写任何地方**；登录成功即清内存里的密码。
3. **拿不到就说拿不到**：后端没起 ⇒ 显示「源未接」并写明怎么接
   （起 `holo_pet\start-holo-panel.bat`），**绝不用空壳界面冒充"密钥已就绪"**。

---

## 六、✅ 已验 / ⚠️ 未验（必须分清，不许混）

### 已验
- `node --check plugins/gbt-settings-keys/lib/client.js` → **退出码 0**（语法过）
- slot 名 **`settings.section`** —— 从 `dsh-client-ui-settings` 的 `.d.ts` 契约文件读出
- 注册写法 `ctx.slots.inject(name, () => ctx.slots.register({name, id, order}, C))`
  —— 抄自仓里**已验实的** `gbt-master/lib/client.js:210-218`
- 后端两个出口 —— 端到端实测过（含未登录拒绝、密码不泄露、未知 op 拒绝）

### ⚠️ 未验（**不许当成"已经装好了"**）
1. **`SettingsSectionOwnerProps` 的确切形状**：我只读到它是从 `./contract/slots.ts`
   再导出的，**没读到定义本体**。因此**组件到底从哪拿 React**（props 注入 / 全局 / 转出）
   我**没确认**。代码里写的是 `props.React || globalThis.React` 兜底 —— **这是兜底，不是验证**。
2. **组件注册形态**：`register(opts, Component)` 里 Component 是函数组件还是别的形态，
   未逐字确认。
3. **`order: 40`** 只是我挑的一个数，**没验过**它和别的 section 的先后关系。
4. **未做加载验证**：没有跑过 DSH web 的重载，**不确定它是否真能挂上**。

⇒ **在这些未验项被源码确认之前，本插件不许被当成"能加载的插件"。**
这正是「资料核实律」与「严禁假执行」要防的东西。
