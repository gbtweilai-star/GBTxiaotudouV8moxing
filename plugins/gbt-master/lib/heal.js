/* GBT小土豆V8 · 首页自愈器 —— 🔴 这一份**在磁盘上**，由宿主路由 `/gbt-master/heal.js` 现读现发。
 *
 * 为什么要把逻辑放在磁盘、而不写进注入的 HTML 里（这是根因修法，不是补丁）：
 *   注入的脚本是**跟着首页一起发下去的**，页面一旦加载，它带的就是**当时那一代**的常量。
 *   于是出现一个死结：**页面永远判不出"我自己这一代旧了"** —— v6 的页面里 GEN='…-v6'，
 *   `dataset.gbtGen` 也是 '…-v6'，自比永远相等 ⇒ 自愈永远不触发。
 *   实测：v6 → v7 换代后，Owner 那张页面就卡在旧包上（左栏还是官方品牌行），
 *   而"自愈注入"报的是"已注入" —— 报告层又是绿的，事实是没救到。
 *   根因还有第二层：注入文本本身也在包里，**改注入逻辑 = 又要换一代**（specifier 变了才重新
 *   import），于是"自愈"每次修都得人手刷一次 —— 这本身就违背自愈的目的。
 *
 * 修法（两层一起断根）：
 *   ① 注入到 HTML 的只剩**一行永不改变的标签**：`<script src="/gbt-master/heal.js" defer></script>`；
 *   ② 判据从"页面自带常量 vs 自己的戳"改成 **"页面自带的戳 vs 宿主现报的世代"** ——
 *      宿主那头的 `plugin` 字段是**当时现读**的，所以任何旧页面都能认出自己旧了。
 *   ⇒ 以后改自愈逻辑**只改这个文件**，不换代、不重装、不用再求人按 F5。
 *
 * 纪律（写死，别放松）：
 *   · 只有 `/gbt-master` 答 200 才动 —— 插件撤掉则整段失效，不惹事；
 *   · 最多自愈 3 次，两次至少隔 60 秒 —— 不可能变成刷新循环；
 *   · 装上了且世代一致就把计数清零；
 *   · `?gbt_noheal=1` 一律不介入；
 *   · 全程 try/catch，不定义全局、不碰别人的东西。
 */
;(function () {
  try {
    var K = 'gbtSelfHeal'
    var S = {}
    try { S = JSON.parse(localStorage.getItem(K) || '{}') || {} } catch (e) { S = {} }
    if (location.search.indexOf('gbt_noheal=1') >= 0) return
    if ((S.tries || 0) >= 3) return
    var N = Date.now()
    if (S.at && N - S.at < 60000) return

    function stamp() {
      try { return String(document.documentElement.dataset.gbtGen || '') } catch (e) { return '' }
    }
    function mounted() { return !!document.querySelector('.gbtm-gv') }
    function clear() {
      S.tries = 0; S.at = Date.now()
      try { localStorage.setItem(K, JSON.stringify(S)) } catch (e) { /* 存不了就下次再说 */ }
    }
    function bump() {
      S.tries = (S.tries || 0) + 1; S.at = Date.now()
      try { localStorage.setItem(K, JSON.stringify(S)) } catch (e) { /* 同上 */ }
    }

    function check() {
      fetch('/gbt-master', { cache: 'no-store' }).then(function (r) {
        if (!r || !r.ok) return null          // 宿主没答 ⇒ 与本插件无关，绝不刷
        return r.json()
      }).then(function (j) {
        if (!j) return
        var gen = j.plugin ? String(j.plugin) : ''
        if (!gen) return
        // 本代判据：世代戳 == 宿主现报的世代。戳只由**当前这一代 bundle 的 apply** 打上，
        // 所以它相等 ⇒ 这个页面跑的就是宿主现在这一代（入口在不在是另一回事，不拿它当判据）。
        if (stamp() === gen && mounted()) { clear(); return }
        setTimeout(function () {
          if (stamp() === gen && mounted()) { clear(); return }
          bump()
          location.reload()
        }, 8000)
      }).catch(function () { /* 网络抖动不自作主张 */ })
    }

    function go() { setTimeout(check, 4000) }
    // 🔴 2026-09-22b 补（**只改这个文件、不换代** —— 这正是把自愈器放磁盘的好处）：
    // 旧版只在**页面加载那一刻**判一次，于是"页面先加载、服务端随后换代"这种情况**永远发现不了**：
    // 实测 v8→v9 换代后，那张页面一直停在 v8，只能等人按 F5。
    // 现在：加载后先判一次，之后**每 60 秒再判一次**；仍受"最多 3 次 / 两次间隔 ≥60s"约束，
    // 不可能变成刷新循环；世代对齐后计数清零。
    if (document.readyState === 'complete') {
      go()
      setInterval(check, 60000)
    } else {
      window.addEventListener('load', function () { go(); setInterval(check, 60000) })
    }
  } catch (e) { /* 自愈器自己坏了也绝不能连累页面 */ }
})();
