/* 兼容壳 · 浏览器半边（**故意什么都不做**）。
 *
 * 与 lib/host.js 同一件事的另一半：加载器缓存里那条 `gbt-potato-master-v6` 的**浏览器模块 id**
 * 也要能被解析，否则客户端名册里那一条照样报"找不到模块"，整页插件加载一起失败。
 *
 * 只做一件事：把这个 id 注册成一个**无副作用空壳**（apply 空、inject 空）。
 * 正文 UI 由现役的 `gbt-potato-master-v8` 提供，本壳不碰任何插槽、不装任何样式。
 */
;(function () {
  try {
    if (!window.__ModuleLoader__ || typeof window.__ModuleLoader__.load !== "function") return
    window.__ModuleLoader__.load({
      id: "gbt-potato-master-v6",
      factory: function () {
        var stub = { exports: {} }
        stub.exports.apply = function () {}
        stub.exports.inject = []
        return stub.exports
      },
    })
  } catch (e) {
    /* 兼容壳自己坏了也绝不能连累页面 */
  }
})()
