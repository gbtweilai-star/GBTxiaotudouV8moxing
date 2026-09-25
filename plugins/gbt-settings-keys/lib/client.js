/**
 * GBT小土豆V8 · 设置·密钥 —— DSH 客户端插件（设置页里的「密钥」一节）
 *
 * Owner 2026-09-22（看着 GUI 截图定）：
 *   「把设置口对齐，另外一个端口在安装上帝视角和其他可视化面板你别动，
 *     你就把设置密钥的安装好」
 *
 * ═══════════════════════════════════════════════════════════════════
 * 落点：**`settings.section`**（`dsh-client-ui-settings` 的 list·root seat）
 *
 *   凭证（读 DSH 源码得到，不是猜）：
 *     `dsh-client-ui-settings/lib/types/client/contract/slots.d.ts` 原文：
 *       「A feature owns its own settings pages —— **adding a setting never
 *         means editing the shell**」
 *     该文件里 settings 域的 seat 一共 8 个：
 *       settings.trigger / settings.header / settings.action / settings.close
 *       settings.section(list) / settings.plugins.tab(list)
 *       settings.onboarding(list) / settings.general.item(list)
 *     ⇒ 加一节设置，正路就是往 `settings.section` 注册。
 *
 * 🔴 **明确不碰的东西**（Owner 明令）：
 *    顶部那排标签是 `conversation.view` 的位 ——
 *    `dsh-client-ui-conversation/lib/types/client/contract/views.d.ts` 原文：
 *      「One conversation view tab, projected from a 'conversation.view' slot
 *        entry's registration options」
 *    那些空位是留给**上帝视角和其他可视化面板**的。本插件**一个都不注册**。
 *
 * ═══ 注册 API：按仓里**已验实**的写法（不是我推的）═══
 *   抄自 `plugins/gbt-master/lib/client.js:210-218`（那份已无"未验"标记）：
 *       ctx.slots.inject("<slot>", function () {
 *         return ctx.slots.register({ name: "<slot>", id: "<id>", order: N }, Component)
 *       })
 *
 * ═══ 三条自律 ═══
 *  ① **绝不回显明文密钥**：后端已经打码，前端也不做"显示原文"按钮。
 *  ② **密码不落盘**：登录框只把 email/password 发一次给本机后端换会话，
 *     前端**不 localStorage、不 cookie、不写任何地方**。
 *  ③ **拿不到就说拿不到**：后端没起 / 面板没跑 ⇒ 显示「源未接」并写明怎么接，
 *     **绝不用一个空壳界面冒充"密钥已就绪"**。
 */

/** 本插件在 settings.section 里的登记 id —— 登记后不改（改了等于换一节） */
export const SECTION_ID = 'gbt-settings-keys'

/** 后端出口：面板（holo_pet/panel_server.py）里我们新加的那两个 */
const API_READ = '/api/settings'
const API_ACT = '/api/settings/action'

/** 面板基址：DSH 与面板不同源，允许用环境注入的地址覆盖 */
const PANEL_BASE = (typeof globalThis !== 'undefined'
  && globalThis.__GBT_PANEL_BASE__) || 'http://127.0.0.1:8765'

async function callPanel(path, body) {
  const opt = body
    ? { method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body), cache: 'no-store' }
    : { cache: 'no-store' }
  const r = await fetch(PANEL_BASE + path, opt)
  if (!r.ok) {
    let detail = ''
    try { detail = (await r.json()).error || '' } catch { /* 非 JSON 就留空 */ }
    throw new Error(`HTTP ${r.status}${detail ? ' · ' + detail : ''}`)
  }
  return r.json()
}

/**
 * 渲染一节设置。`props` 由 DSH 的 settings 域注入（owner props）。
 * **React 组件**（DSH 客户端是 React —— 由 `dsh-client-ui-trajectory/README.zh.md`
 * 原文「只覆盖 React 可见窗口」确认）。这里只用最基础的元素，不引任何 UI 库，
 * 免得绑死某个版本的组件库。
 */
function KeysSettingsSection(props) {
  const React = props.React || globalThis.React
  if (!React) return null
  const h = React.createElement
  const { useState, useEffect, useCallback } = React

  const [state, setState] = useState({ phase: 'loading', groups: [], error: '' })
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [busy, setBusy] = useState(false)
  const [toast, setToast] = useState('')

  const load = useCallback(async () => {
    setState((s) => ({ ...s, phase: 'loading', error: '' }))
    try {
      const j = await callPanel(API_READ)
      setState({ phase: 'ready', groups: j.groups || [], error: '' })
    } catch (e) {
      // 拿不到就如实说，并给怎么接 —— 不假装
      setState({ phase: 'unwired', groups: [], error: String(e.message || e) })
    }
  }, [])

  useEffect(() => { load() }, [load])

  const act = useCallback(async (op, extra) => {
    setBusy(true); setToast('')
    try {
      const j = await callPanel(API_ACT, { op, ...(extra || {}) })
      setToast(j.ok ? `✔ ${op}` : `✘ ${op}：${j.error || '失败'}`)
      if (op === 'login' && j.ok) setPassword('')   // 成功即清内存里的密码
      await load()
    } catch (e) {
      setToast(`✘ ${op}：${String(e.message || e)}`)
    } finally { setBusy(false) }
  }, [load])

  const keys = (state.groups || []).find((g) => g.id === 'keys') || {}
  const others = (state.groups || []).filter((g) => g.id !== 'keys')
  const providers = keys.providers || []
  const unconfigured = keys.unconfigured || []

  const box = { padding: '10px 12px', border: '1px solid var(--dsh-border, #3336)',
                borderRadius: 8, marginBottom: 10 }
  const muted = { opacity: 0.7, fontSize: 12, lineHeight: 1.6 }
  const btn = { padding: '4px 10px', borderRadius: 6, cursor: busy ? 'wait' : 'pointer',
                border: '1px solid var(--dsh-border, #3336)', background: 'transparent',
                color: 'inherit' }
  const input = { padding: '5px 8px', borderRadius: 6, width: '100%',
                  border: '1px solid var(--dsh-border, #3336)',
                  background: 'transparent', color: 'inherit', marginBottom: 6 }

  const title = h('div', { style: { fontWeight: 600, marginBottom: 6 } }, '密钥')

  // ── 后端没接上：写明怎么接，不给空壳 ──
  if (state.phase === 'unwired') {
    return h('div', { style: box },
      title,
      h('div', { style: muted },
        '源未接：读不到本地面板。', h('br'),
        '原因：', h('code', null, state.error || '未知'), h('br'),
        '怎么接：先起面板 —— 双击 ',
        h('code', null, 'holo_pet\\start-holo-panel.bat'),
        '（默认 127.0.0.1:8765）；若面板在别的地址，注入 ',
        h('code', null, 'globalThis.__GBT_PANEL_BASE__'), ' 覆盖。'),
      h('div', { style: { marginTop: 8 } },
        h('button', { style: btn, onClick: load, disabled: busy }, '重试')))
  }

  return h('div', { style: box },
    title,

    // ── 第一组：密钥现状 ──
    keys.status === 'server_down'
      ? h('div', { style: muted },
          '免费大模型池**服务没起**。先起 FreeLLMAPI 桌面版 —— ',
          '端口由它自己的 config.json 决定（我这边的后端会自动发现）。')
      : keys.status === 'need_login'
        ? h('div', null,
            h('div', { style: muted },
              '服务在（', h('code', null, (keys.server || {}).base_url || '?'), '）。',
              '要读 34 家供应商、要配密钥，需要 dashboard 会话。'),
            h('div', { style: { marginTop: 6 } },
              h('input', { style: input, placeholder: 'FreeLLMAPI dashboard 邮箱',
                           value: email, onChange: (e) => setEmail(e.target.value) }),
              h('input', { style: input, type: 'password',
                           placeholder: '密码（只发一次换会话，前端不留存）',
                           value: password, onChange: (e) => setPassword(e.target.value) }),
              h('button', { style: btn, disabled: busy || !email || !password,
                            onClick: () => act('login', { email, password }) },
                '登录并读取供应商'),
              h('span', { style: { ...muted, marginLeft: 8 } },
                '密码不落盘：不回显、不 localStorage、不进日志。')))
        : h('div', null,
            h('div', { style: muted },
              '已登录 · 供应商 ', String((keys.summary || {}).configured ?? '?'),
              ' / ', String((keys.summary || {}).total ?? '?'), ' 家已配',
              unconfigured.length ? ` · 未配 ${unconfigured.length} 家` : ' · 全部已配'),
            h('div', { style: { marginTop: 6 } },
              h('button', { style: btn, disabled: busy, onClick: () => act('providers') },
                '刷新供应商'),
              h('button', { style: { ...btn, marginLeft: 6 }, disabled: busy,
                            onClick: () => act('logout') }, '退出登录')),

            // 已配的逐条（后端已打码，前端不做"显示原文"）
            providers.filter((p) => p.configured).length
              ? h('div', { style: { ...muted, marginTop: 8 } },
                  '已配：',
                  providers.filter((p) => p.configured)
                    .map((p) => `${p.name}(${p.keyCount})`).join(' · '))
              : null,

            // 未配的一键入口
            unconfigured.length
              ? h('div', { style: { marginTop: 8 } },
                  h('div', { style: muted }, '未配的（粘贴一把 key 即可）：'),
                  h('div', { style: { display: 'flex', flexWrap: 'wrap', gap: 6,
                                      marginTop: 4 } },
                    unconfigured.slice(0, 40).map((platform) =>
                      h('button', {
                        key: platform, style: { ...btn, fontSize: 12 },
                        disabled: busy,
                        onClick: () => {
                          const k = globalThis.prompt?.(`粘贴 ${platform} 的 API key：`)
                          if (k) act('add_key', { platform, key: k })
                        },
                      }, platform))))
              : null),

    // ── 其余三组：如实标未建 ──
    others.length
      ? h('div', { style: { ...muted, marginTop: 10 } },
          others.map((g) => h('div', { key: g.id },
            `· ${g.title}：${g.status === 'pending' ? '未建（如实标，不做假入口）' : g.status}`)))
      : null,

    toast ? h('div', { style: { ...muted, marginTop: 8 } }, toast) : null)
}

export const inject = ['@deepseek-ai/dsh-client-ui-slots']

export function apply(ctx) {
  // 只占 settings.section 一个 seat。
  // **不注册任何 conversation.view** —— 那些位是上帝视角与可视化面板的（Owner 明令不动）。
  ctx.slots.inject('settings.section', function () {
    return ctx.slots.register(
      { name: 'settings.section', id: SECTION_ID, order: 40 },
      KeysSettingsSection,
    )
  })
}
