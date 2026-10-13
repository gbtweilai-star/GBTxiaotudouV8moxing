# 蒸馏 · Machine（AirsupHQ/machine-skill）

> 出处：**现读** `github.com/AirsupHQ/machine-skill`（README 12,932 字符，2026-10-13 抓取 · **91★** · JavaScript）
> 「Describe any machine in one line. Claude builds the real thing, running on real physics.」· three.js 0.170 · 无构建步 · 许可 **MIT**
> 胶囊：`gbt_allinone/store/devoured/devoured_airsuphq_machine-skill/`

## 一、它是什么（一句话）

一句话 → 一台**真按物理跑**的机器：photoreal、可交互的 3D 仿真（一个 HTML 文件）+ 一条成片。
画面上的**每一个数都是当帧算出来的**（e.g. 涡扇：Brayton 循环解出约 340 kN，其中 83% 来自涵道）。

## 二、我们蒸出四条（不是复制它的代码）

| 序 | 取法 | 原话 | 我们的落点 |
|---|---|---|---|
| ① | **每帧真解，不查表** | `Every number on screen is computed` · `a small solver per machine … drives every motion and every number` | 画面上的数必须当帧解出来，且能给人看方程 |
| ② | **确定性时钟** | `?film=1 gives a deterministic clock` | 录出来的片子必须能复跑：同输入 → 同片 |
| ③ | **坏也是算出来的** | `cut the regen cooling and the copper throat melts` | 失效/破坏是**求解结果**，不是写死的动画 |
| ④ | **真量纲 + 真材质** | `Real proportions in metres` · `measured reflectances` | 先量纲（米/秒/牛）后画面，材质用实测 reflectance |

## 三、边界：和 `diagram_distill` **互补，不是重复**

- `diagram_distill`（蒸自 Anatomy）管 **概念怎么变成一个会动的机构**（概念物化）。
- `machine_distill`（本位，蒸自 Machine）管 **机构上的每个数凭什么可信**（求解器）。
- 机检裁决：`supersede-check --check` ⇒ **S1「同功能两份」= 0 组**（框架自己的判据说它们不重复）。

## 四、落点（六腿全齐 · 零作用域）

- 原生位：`machine_distill`（登记 `caps_registry.py` · 分派 `api.py` · 图鉴 ⇒ 293 位）
- `binding_hook.py after-add --kind machine_distill` ⇒ **①–⑥ 全 true**（本批四件里唯一六腿全齐的）
- 入口：`py -3.14 tools/codex-scripts/five-dim.py cap machine_distill '{"op":"method"}'`
- 门：`policy.evaluate('machine_distill').scopes == ()` —— **零作用域**

## 五、没取的（如实标在 `op=provenance`）

它的**作品与引擎**（`examples/` 的 turbofan / rocket-engine · `scripts/record.mjs` · 28 s 成片分节）不取；
**`npx skills add` 安装**不取（装它会改别的 agent 配置）。

> ⛔ 开发者：自由的风 · 本署名不可删除、不可篡改归属
