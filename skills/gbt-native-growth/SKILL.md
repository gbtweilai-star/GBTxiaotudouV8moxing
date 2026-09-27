# gbt-native-growth · 原生能力成长栈

> 主人令（2026-09-27）一句话版：**吞天要和契合自己的原生能力融合、每根触手一本永久记忆 Obsidian 并与本体互通、
> 要有短板钩子和自主进化钩子、做事先看再动脑不许无脑和盲猜、原生能力要有 GBT 专属标签且只有主人允许才能调、
> 新增就触发双向绑定并连通每一页触手。**

这套栈有六个件，**彼此有依赖顺序**（记忆是底、钩子是鞭、闸是刹车、标签是钥匙）：

```
obsidian_vault（永久记忆·227 本触手库 ↔ 本体库双向）
      ↑ 记
devour_fusion（吞天×原生：三件齐才算融合）
      ↑ 查
tools/binding_hook.py（硬性规则钩子：新增六条腿，缺了就红）
      ↑ 逼
growth_hooks（短板钩子 + 自主进化钩子）
      ↑ 拦
action_gate（先看 → 动脑 → 执行）
      ↑ 管
cap_tags（GBT 专属标签 + 主人许可门）
```

## 一、永久记忆（`obsidian_vault` · 触手 `obsidian_vault`）

- **触手库**：每一根触手（= 能力位 kind ∪ `domain:<域>`，实测 **232** 个标签）**各一本独立库**，
  落在本仓 `vaults/<触手>/`：`README.md`（MOC）· `记忆.md`（追加式）· `.obsidian/app.json`（Obsidian 直接开）。
  为什么在仓内：**永久记忆要和源码一样受保护**（仓外的东西没人扫、不进版本），且它是框架**自己的**记忆。
- **本体库**：`brain_vault` 认的那本（`Documents\Codex\ObsidianVault`）—— 不动它的既有笔记。
- **双向绑定**：触手页链回 `[[GBT本体记忆]]`，本体 `[[触手总索引]]` 链到每一本；`verify` 两条都查。
  **不是复制**（复制只会分叉，本仓吃过技能双真身的亏）：各自的内容留在各自的库，互相**指得到**。
- 共享页 `sync_page`：同一篇在触手库与本体库各一份，**两侧同 sha**。
- 写「主人的 Documents」走 `root=documents`，**过 `filesystem_write` 门**；仓内默认不过门（同 `state/`）。

## 二、吞天 × 原生融合（`devour_fusion` · 触手 `devour_fusion`）

**三件齐才算融合**：①原生位三处齐（注册/分派/图鉴）②有效触手标签 ③触手库永久记忆页。
`status=已融合` 而三件不齐 **当场拒**（假账在门口拦下）；`fuse` 只补第三件，前两件缺着不假装。
台账 `state/devour_fusion.jsonl`；`list` 的输出里 `已融合` 是**盘上算出来的**，不看台账里写的。

## 三、短板钩子 + 自主进化钩子（`growth_hooks` · 触手 `growth_hooks`）

- `shortboard`：短板**从读数算**（六面 + 未清故障 + 未实现 + 触手库覆盖 + 许可缺口），**每条带 `src`**。
- `evolve`：拿最短板 → 生成步骤（标 `safe`/`needs_owner`）→ **只自动做不带门的**，其余列给主人。
- 两条纪律写死在代码里：**不自批授权**；**撞 `state/holdout.json` 封存验收集的步骤一律拦下**
  （判据不许既当训练又当验收）。

## 四、先看 → 动脑 → 执行（`action_gate` · 触手 `action_gate`）

| 规矩 | 判据 |
|---|---|
| 先看 | `evidence` 非空且**真在盘上**（`observe` 记 sha + 龄） |
| 看的是新的 | 证据龄 ≤ `fresh_s`（默认 600s）；旧了要么重看，要么显式 `stale_ok=true` 说理由 |
| 动脑 | `hypothesis` ≥8 字（写出"我预期发生什么"）—— **不许盲猜** |
| 有票 | 写/执行类要给 `scope`，或能力位是 `owner` 类 |

过了发 `gate_id` → 动手 → `close(gate_id, result, saw)`：**`saw` 不许空**（做完必须看到结果，exit 0 不算）。

## 五、GBT 专属标签 + 主人许可（`cap_tags` · 触手 `cap_tags`）

- 标签 `GBT-<域>-<能力位>`（例：`GBT-CREATION-LOBEHUB`），**从注册表现算**，新增自动就有。
- 权限类**不是手写名单**：`policy.evaluate(kind, {op})` 逐 op 问作用域 + 图鉴 `safe`/`needs_confirmation`；
  **读不出来一律按 `owner`**（默认严）。`open`=读类随便调，`owner`=**只有主人允许了才能调**。
- 许可：`gbt_allinone/store/owner_permits.jsonl`（一行一条），或主人终端
  `python -m gbt_allinone.tools.cap_tags permit --tag <TAG> --ttl 600`
  —— **要求 TTY + 手打 YES**，非交互会话直接拒 ⇒ **AI 发不出许可**（本模块里也**没有**第二条写许可的路径，
  `verify` 会结构性地查这一点：写的那一行必须在 `isatty` 闸之后）。
- `audit` 输出的是**待批清单**（哪些 owner 类还没许可）。

## 六、硬性规则钩子（`tools/binding_hook.py`）

新增一件东西，**当场**走完六条腿，缺哪条补哪条，补不了记红：

| 腿 | 查什么 | 缺了怎么补 |
|---|---|---|
| ① 登记 | `caps_registry.py` 有 kind | 加注册条目（钩子**不替你造**能力位） |
| ② 分派 | `api.py` 有 `kind == "<kind>"` | 加分支 |
| ③ 图鉴 | `state/skill_atlas.json` 收录 | `omni.py build` |
| ④ 触手 | kind 是有效触手标签 | 注册即成立 |
| ⑤ 绑定 | 绑定账里查得到（资产或清单） | `surface_bind op=probe` / `tentacle_bind autobind` |
| ⑥ 记忆 | 触手库里有一页 | `obsidian_vault op=provision/remember` |

```
python tools/binding_hook.py after-add --kind <kind> [--tool <工具区名>]
python tools/binding_hook.py sweep      # 自愈：给所有能力位补齐触手页
python tools/binding_hook.py verify     # 复核（漏走钩子的新增在这里露出来）
```

**血账**：`surface_bind` 的委托分支（comfyui/blender/lobehub）曾**提前 return** ⇒ 清单写了**却从没绑上触手**。
"接上了没绑上"就是这个钩子要防的事。

## 这轮抓出来的四个真问题（都属"判据/闸自己先坏"）

1. **判据往真库里写**：`sync_page` 的自检一度往本体库写了张 `自检页.md` —— 判据必须全程在临时目录里做。
2. **自审太钝**：`cap_tags.verify` 只查"代码里有没有写许可"，把主人终端那条合法路径也判红 ⇒ 改成**结构性**检查
   （唯一一处 + 必须在 `isatty` 之后）。
3. **反盲区判据立功**：新加 `vaults/` 后顶层树 60→63，`test_coverage_readings_fresh` 当场红 ⇒ 重扫矩阵，
   新面被登记（不是被忽略）。
4. **假账拦截要真试**：`intake(status='已融合')` 用**真有那三件**的能力位去试，当然会过 —— 要拿"缺件"的去试。
