# state/ · 机器写，人只读

本目录是**实测层**，唯一有权回答"本机现在到底行不行"的地方。

| 路径 | 谁写 | 含义 |
|---|---|---|
| `probe/<id>.json` | 能力探针 | 最近一次只读探测的结果（`reachable` / `authorized` / `checked_at` / `http` / `reason`） |
| `tokens/<id>.json` | 授权流程 | 凭据本体。**只允许存在性被读取**，内容不进日志、不进响应、不进对话 |
| `ledger.jsonl` | 判断账本 | append-only：每条判断必带 `falsifier`（可证伪条件）与 `due`（到期日） |
| `last_seen.json` | 采集器 | 防漏检水位：每个信源最后一次成功采集的时刻 |
| `runs/<id>.json` | 采集器 | 最近一次采集的**结局**（`outcome` / `http` / `reason` / `finished_at`）。失败写这里，**不写水位** |
| `signals.jsonl` | 采集器（入库闸） | 信号记录，append-only。**缺 url 的记录一律拒收**（判据 F）：控制台报错，不写盘 |

三条硬规矩：

1. **人改这里 = 造假。** `sources.json` 里写的是"我声明要用"，本目录里写的是"我实测通了"。
   门禁读后者。手改前者不会让门禁变绿，手改后者会让结论失效。
2. **没有时间戳 = 过期。** 探针结果一律带 `checked_at`；缺它按 `stale` 处理。
   一次通过不是永久证明。
3. **凭据只报存在，不报内容。** `credential_present` 只回答文件在不在。

> 本文件由 GBT小土豆V8 落盘 · 归属不可篡改

## 探针四态（面板原样显示这一列）

| probe_state | 显示 | 含义 |
|---|---|---|
| `ok` | 已探测 · 通过 | 唯一允许为绿的态 |
| `stale` | 已登记 · 探测过期 | 探过，但超过 TTL，降级为未核验（不是失败） |
| `failed` | 已探测 · 未通过 | 探过且被拒（如 401） |
| `unprobed` | **已登记 · 未探测** | 登记表里有它，本机还没探过。**不许写成「未登记」** |
| `spec_unknown` | 已登记 · 无探针定义 | 登记表里有它，但平台规格表里没有，不知道该探什么 |
| `unsupported` | 无官方发布接口 | 官方没有接口，不是待办 |

「已登记」来自 `sources.json` 的 `channels`（登记表）；「探测」结果只认本目录的
`probe/<id>.json`。两者分家，就是为了让"没探过"永远显示成"没探过"。

## 落点优先级（写死一处，别处不许再判）

1. `state/probe/<id>.json` 存在且可解析 -> **以它为准**（唯一实测落点）
2. 否则回落到 `social.json` 里内嵌的 `capability_probe`（旧形状，兼容保留）
3. 都没有 -> `unprobed`

> 面板与 API 的字段：`probe_state`（机器读）· `status_label`（人读）· `probe_source`（这结论从哪来）。

## 采集六态（调研信源；面板原样显示这一列）

| run_state | 显示 | 含义 |
|---|---|---|
| `ok` | 最近采集 · 正常 | 最后一次成功在采集周期内。唯一允许为绿的态 |
| `stale` | 已登记 · 采集过期 | 有水位但超两个周期（漏一次不算、漏两次算）。**是漏采，不是失败** |
| `failed` | 最近采集 · 失败 | 最近一次采集失败（带 `http` / `reason`）。**失败不清水位** |
| `never_run` | **已登记 · 未采集** | 登记表里有它，本机还没采过。不许写成「失败」，也不许写成绿 |
| `unreadable` | 状态文件不可信 | `runs/<id>.json` 读不出来。这一轮"不知道"，不许退回「未采集」 |
| `disabled` | 未启用 | 登记表显式写 `enabled: false`。是意愿声明，不计入采集失败 |

### 采集四层（写死一处，别处不许再判）

1. **声明层** `sources.json` 的 `research`：人写"我要用这个源"。
2. **实测层** `runs/<id>.json`：采集器写最近一次结局。
3. **水位层** `last_seen.json`：**只记最后一次成功**的时刻。
4. **判定层** `holo_pet/research_status.py`：六态互斥，优先级 `unreadable > disabled > failed > never_run / stale / ok`。
   （读不出来 > 意愿声明：本机事实优先于人的声明。）

### 采集侧硬规矩（接上面三条）

4. **失败不抹水位、不连坐。** 一次失败只写 `runs/<id>.json`，不走 `last_seen.json`：
   防漏检水位仍是上一次成功；其余信源的结论一个字节都不许变。
5. **本次值不沿用旧值。** 报告里分两个袋子，**不许混**：

   | 袋子 | 只来自 | 没有数据时 |
   |---|---|---|
   | `this_run`（本次值） | `runs/<id>.json` | `present=false`、`items=null`——写「未知」，不许回落 0，更不许拿历史顶 |
   | `history`（历史水位） | `last_seen.json` | `items=null`、`watermark_age_label=""` |

   水位条目若写成 `{"at": ..., "items": 42}`，那个 `42` 是**上一次成功**的条数，
   只进 `history.items`；它永远不许流进 `this_run`。同理，`run_report` 里的
   `this_run_items_total` 只累加**本次 `outcome == "ok"`** 的源：
   没采到的源是"未知"、失败源写 `items: 0` 也只是"没采到"，两者都不进总数。

### 入库侧硬规矩（判据 F / G，判定只写在 `holo_pet/signal_ingest.py`）

6. **缺 url 不入库。** 任何 SignalRecord 缺 `url`（键不在 / 不是字符串 / 全空白）一律**拒收**：
   控制台报一行错，`signals.jsonl` 一个字节都不写。单条被拒**不连坐**同批其它记录。
   **不许**用 `or ""` 之类把「缺」填成「有」—— 缺 url 不是空链接，是这条信号没有出处。
7. **有 value 无 baseline 不出增长率。** 算不出增长率时，输出里 `growth` 这个键**根本不出现**，
   **不许**印 `+0%`。只有量出来的 0（`value == baseline`）才允许印 `+0.0%`。
   顺带一条：策略字符串（`rolling_7d`）**不是** baseline，只有数字才算。

### severity（机器可读的「标红」，面板与 run_report 都读它）

| severity | 来自 state | 含义 |
|---|---|---|
| `red` | `failed` / `unreadable` | 标红：本次失败，或状态文件读不出来 |
| `warn` | `stale` | 漏采（漏两次才算），不是故障 |
| `neutral` | `never_run` / `disabled` | 没采过 / 未启用，都不是错 |
| `ok` | `ok` | 在采集周期内 |

`run_report` 是从上面三层**派生**的视图（`derived=true`），不落盘、不缓存 ——
缓存正是「沿用旧值」的温床。
