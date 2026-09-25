/**
 * GBT小土豆V8 · 能力栏 —— DSH 客户端插件（浏览器半边）· **草案 v0.1**
 *
 * Owner 2026-09-22：
 *   「对话面板就使用我们对话这个，把能力栏设计上去，以及我们的品牌 GBT小土豆V8，
 *     最好是 3D 立体感强、视觉感强，展示出那种运行轨迹一眼就看懂的意思」
 *   「不破坏环境，我们加装其他的而已」「只要能力全部不丢失就行」
 *
 * ═══════════════════════════════════════════════════════════════════
 * 🔴 本文件是**草案**，不是可加载版本。以下三条我**没有验证**，列在此处防误用：
 *
 *   ⚠️ 未验 1：`ctx.sidebarRightTabs.register({...})` 的确切签名
 *      —— 我是从 `dsh-client-ui-sidebar-documentpreview` 的 **doc 注释**里读到的
 *      「definition into ctx.sidebarRightTabs / body into sidebar.right.pane.tab」，
 *      **没读它的实现**。真实签名可能不同。
 *
 *   ⚠️ 未验 2：`ctx.slots.register(slot, id, factory)` 的参数顺序与返回
 *      —— 同上，只从注释推的。
 *
 *   ⚠️ 未验 3：组件形态
 *      —— **已确认 DSH 客户端是 React**（`dsh-client-ui-trajectory/README.zh.md` 原文：
 *      「选择、时间线导航、折叠与搜索只覆盖 **React** 可见窗口」）。
 *      本文件上一版我误写了 Vue（`import { ref } from 'vue'`）—— **那是猜的，已删**。
 *      下面按 React 写，但**React 的具体版本与 hooks 来源（是全局 React 还是 DSH 转出）
 *      仍未验证**。
 *
 *   ⇒ **在这些未验项被读源码确认之前，本文件不许被当成"能加载的插件"。**
 *      这正是今晚立的「资料核实律」与「严禁假执行」要防的东西。
 * ═══════════════════════════════════════════════════════════════════
 *
 * ═══ 本插件的三条自律（这部分是定的）═══
 *  ① **不改 DSH 一行源码**：只走公开注册路径，够不到 Sidebar 的 store / panes / sequence。
 *  ② **能力一个都不丢**：数据从**活源**读，**不在此文件硬编码任何能力名**
 *     —— 硬编码必然过期（今晚「自我认知失真」那个坑的同型）。
 *  ③ **拿不到数据就说拿不到**：显示「源未接」并给出怎么接，
 *     **绝不用一个空的漂亮界面冒充"能力栏已就绪"**。
 */

/** 本插件登记的右侧栏页签 id —— **登记后不许改**（改了等于换一个页签） */
export const TAB_ID = 'gbt-capability'

/** 插件需要的客户端服务（照官方范本用字符串数组声明） */
export const inject = [
  '@deepseek-ai/dsh-client-ui-slots',
  '@deepseek-ai/dsh-client-ui-sidebar-right',
  '@deepseek-ai/dsh-client-locale',
]

/**
 * 能力数据源（按序试；**全拿不到就如实报"源未接"**）。
 *
 * 为什么不写进本文件：能力的真值只有一处 —— `gbt_allinone/caps_registry`。
 * 这里只负责**把它取过来显示**，不复制、不落第二份。
 */
const SOURCES = [
  {
    name: 'window.__GBT_CAPS__',
    hint: '宿主注入：由 GBT 侧在启动时把能力目录挂到 window',
    get: () => (typeof window !== 'undefined' ? window.__GBT_CAPS__ : null),
  },
  {
    name: 'GET /api/gbt/capabilities',
    hint: '本机能力目录端点（面板或轻量 sidecar 提供）',
    get: async () => {
      const r = await fetch('/api/gbt/capabilities', { cache: 'no-store' })
      if (!r.ok) throw new Error(`HTTP ${r.status}`)
      return await r.json()
    },
  },
]

/** 读能力目录。**只读，不写盘、不改 DSH 任何状态。** */
export async function loadCapabilities() {
  for (const s of SOURCES) {
    try {
      const v = await s.get()
      const list = Array.isArray(v) ? v : (v && Array.isArray(v.caps) ? v.caps : null)
      if (list && list.length) return { ok: true, from: s.name, caps: list }
    } catch (_e) {
      /* 静默试下一个，最后统一如实报 */
    }
  }
  return {
    ok: false,
    caps: [],
    why: '能力目录未接',
    how: SOURCES.map(s => `· ${s.name} —— ${s.hint}`),
  }
}

/**
 * 插件本体。**这是草案骨架，不是可加载实现。**
 *
 * 真实实现前必须先做的一件事：读 `dsh-client-ui-sidebar-documentpreview/lib/client.js`
 * （24,970 B 那种量级的**实现**，不是注释），把 register 的真实签名抄下来。
 */
export function apply(ctx) {
  // —— 待验证区（下面每一行都依赖未验项）——
  // const def = ctx.sidebarRightTabs.register({ id: TAB_ID, title: () => '能力栏', order: 15 })
  // const body = ctx.slots.register('sidebar.right.pane.tab', TAB_ID, CapabilityPane)
  // const chip = ctx.slots.register('sidebar.right.pane.tab.title', TAB_ID, () => '能力栏')
  // ctx.on('dispose', () => { chip?.(); body?.(); def?.() })

  // 未验证前：**只注册一个"说真话"的占位**，不假装能力栏已经好了
  try {
    ctx.slots?.register?.('sidebar.right.pane.tab', TAB_ID, () =>
      '能力栏草案 v0.1 —— 注册 API 尚未验证，故不渲染假界面')
  } catch (_e) {
    /* 注册不上就什么也不做 —— 不许抛错打扰宿主 */
  }
}

export default { inject, apply, TAB_ID, loadCapabilities }
