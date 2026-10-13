# 蒸馏 · Anatomy（wheresryan22/anatomy）

> 出处：**现读** `github.com/wheresryan22/anatomy`（README 24,456 字符，2026-10-13 抓取 · **7551★** · JavaScript）
> 「A Claude skill that explains an idea by building it as a real, working object」· 零依赖（只用 Node 内置模块）· 许可 **MIT**
> 胶囊：`gbt_allinone/store/devoured/devoured_wheresryan22_anatomy/`
> ⚠️ 主人图片上那串 `whereryan22/anatomy` 是误读（该路径 404）；真身是 **`wheresryan22`**。

## 一、它是什么（一句话）

一个 agent skill（Claude Code / OpenCode / Codex 都能跑）：你给一个想法，它**发明一个物理装置**，
**这个装置怎么转，就是那个概念**——cache key 变成「弹子锁，只有全部弹子对上才转」，
一个 GPU 上下文服务多画布变成「龙门绘图仪，一个打印头挨个走 16 个孔位」。
然后用几十个小而实的等距零件把它搭出来，装进带标题/hint/实时读数的框卡，随鼠标键盘平缓运动。

## 二、我们蒸出四条（不是复制它的代码）

| 序 | 取法 | 原话 | 我们的落点 |
|---|---|---|---|
| ① | **概念物化** | `invent a physical thing whose working *is* the concept` | 画图前先答一句：**它怎么转就是这个概念？**答不出就别画 |
| ② | **单一数源** | `Every number the figure shows comes from the same small model that moves its parts` | 读数与动画**同源**；禁止「画面一套、标注另一套」 |
| ③ | **几何不变量要有审计** | `An audit proves that no pipe passes through anything, at rest, apart and in every frame between` | 不穿模是**查过的**：静止态、拆解态、以及**过渡的每一帧** |
| ④ | **逐关节自检** | `checks its own work by zooming in on every joint` | 交付前自己放大挨个关节看，不靠「应该没问题」 |

## 三、为什么是「取法」不是「建平行位」（立项理由）

出图的位我们**已有**：`code_art`（INDEX/SEED/CANVAS/LAYER/EXPORT）· `scene_anchor` ·
`projection_card`，加 design-asset 那一路。照抄建个平行的「anatomy 位」会撞仓规
「**新增即清旧**」的「同功能两份」⇒ 本位只**蒸取法**（概念→机构→可动→自证 的规矩）。

## 四、落点（三处齐 · 零作用域）

- 原生位：`diagram_distill`（登记 `caps_registry.py` · 分派 `api.py` · 图鉴 ⇒ 292 位）
- 入口：`py -3.14 tools/codex-scripts/five-dim.py cap diagram_distill '{"op":"method"}'`
- 门：`policy.evaluate('diagram_distill').scopes == ()` —— **零作用域**（只读 + 纯算）
- ops：`method` / `source`（现读胶囊 + 逐文件 sha256）/ `provenance` / `where`

## 五、没取的（如实标在 `op=provenance`）

它的**作品与引擎**（33 figures 画廊 / WebGL shader / 3D beta / `scripts/capture.mjs`）不取 ——
那是它的产出，不是取法；它的 **`npx skills add` 安装**不取（装它会改别的 agent 配置）。

> ⛔ 开发者：自由的风 · 本署名不可删除、不可篡改归属
