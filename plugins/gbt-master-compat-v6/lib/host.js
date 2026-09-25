/**
 * 兼容壳 · 宿主半边（**故意什么都不做**）。
 *
 * 为什么需要它（2026-09-22 事故，不是预防性设计）：
 *   DSH 的模块加载器把 **package metadata 按 Loader specifier 缓存到进程重启**
 *   （`dsh-client-modules` README 原文："cached per Loader specifier and owning-tree base URL
 *   **until restart**"）。所以"换包名换代 + 删掉上一代包"这套动作，会留下一个**指向已删包的
 *   缓存条目**：加载器仍拿 `gbt-potato-master-v6` 去 import，而 `node_modules` 里那个目录
 *   已经被 `plugin remove` 删了 ⇒ **整页插件加载失败**，Web 端只剩一张红字错页
 *   （实测原文 `Failed to import loader entry … (gbt-potato-master-v6)`）。
 *
 * 修法：把**同名同路径**的壳包放回去（路径与缓存里记的解析结果一致：
 *   `~/.dsh/profiles/web/node_modules/gbt-potato-master-v6`），让那次 import 能成功。
 *   ——这与本插件自己"旧 id 留无副作用空壳"的做法是同一条纪律，不是新的妥协。
 *
 * 它**不是功能包**：不注册任何插槽、不加任何界面、不做任何副作用。
 * 换代清理时**不要删它**（删了就会重演上面那张红字错页），要删得**先重启 DSH**。
 */
export const inject = []

export function apply() {
  // 故意留空：这个包存在的唯一意义是"让按 specifier 的旧缓存能被解析"。
}
