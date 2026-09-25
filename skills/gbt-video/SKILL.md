---
name: gbt-video
displayName: GBT 视频职业域 · 用法规程（4 个能力位）
version: 1.0.0
description: GBT小土豆V8 的 `video` 职业域用法规程 —— 图鉴里这个域只有 4 个能力位（`media_pipeline` / `libtv_skill` / `libtv_workflow` / `h3_video_gen`），四位**当前全是只读契约面**：能读编排骨架、能读官方契约与红线、能读四条带牙判据，但**真出片/出图的那条生成端一条都没接线**。本规程逐位写清「用途 / 要不要授权 / 怎么调（真命令）/ 要什么参数 / 依赖什么（外部服务·密钥·本地工具）/ 返回哪些字段 / 失败长什么样」，并附**真跑出来的诚实账**：`policy.py` 里这 4 个 kind **零命中**（所以「门」是命名、不是挂载）· 骨架判否时外层仍打 `status:"ok"` 且退出码 0（`status:"ok"` ≠ 本体 `ok:true`）· `libtv_skill` 在 `omni` 里被 🔒 的唯一理由是名字里的 "skill" 撞上了 "kill" 正则（**假阳性，不是安全判断**）· 技能包未装 / 密钥未配 / 显存读数拿不到。当用户要「出条视频 / 用 LibTV / 用 H3mini / 跑短视频电影音乐流水线 / 分镜到成片」，或怀疑"怎么没出片"、读数对不上、拿不准该走本域还是走 Ark 云端时使用。
triggers:
  - "出视频"
  - "生视频"
  - "短视频"
  - "成片"
  - "分镜"
  - "LibTV"
  - "liblib"
  - "节点式工作流"
  - "H3mini"
  - "T2VA"
  - "I2VA"
  - "视频流水线"
  - "media_pipeline"
  - "h3_video_gen"
  - "video 域"
---

# GBT 视频职业域 · 用法规程（`video`）

> 开发者：自由的风 · GBT小土豆V8 · 本署名不可删除、不可篡改归属
>
> **这份规程解决什么**：`video` 域只有 4 个能力位，但它们**名字像"能出片"、实物是"只读契约"** ——
> 四位的能力位描述里都写着一个「门」字（`只读骨架·门` / `只读骨架·门` / `只读骨架·门` / type=external），
> 而 `gbt_allinone/security/policy.py` 里**这四个 kind 一个分支都没有**（grep 零命中）。
> ⇒ 最容易被念反的两句话就是：
> ① **「没挂作用域」不等于「能出片」** —— 只说明门没拦它，不说明生成端接上了；
> ② **「内层 `denied:true`」不等于「授权被拒」** —— 前者是能力自己的判据，后者是 policy 门。
> 本文件把「哪个位、什么时候用、要不要授权、失败长什么样、读数该看哪一层」逐个钉死，
> **没验过的一律写「未验」并写明卡在哪、为什么不做**。

**唯一现读入口（别信任何二手描述，包括本文件）**：

```powershell
py -3.14 tools/codex-scripts/five-dim.py cap <能力位> ['<JSON载荷>']
```

`cap` 一律走 `gbt_allinone.run_task`（**唯一门**）；被门拒绝就**如实报缺什么作用域**，不绕路。
本域**四位当前都不需要授权**（§4 静态查证），所以本文件里不会出现 `missing_scopes` 的实例 —— **那不是漏抄**。

**口径以 `cap` 的实时输出为准**，本文件只是导读。图鉴里这个域**只有这 4 个位**
（以 `state/skill_atlas.json` 中 `domain == "video"` 的 `kind` 为准），**一个不多一个不少**。

---

## 0. 一句话总表（4 个位）

| 能力位 | 用途（一句话） | 门（静态查） | `omni` 会自动跑吗 | 本规程真跑过 |
|---|---|---|---|---|
| `media_pipeline` | 短视频/电影/音乐的**编排+自审+发布门**（不是生成器） | **无作用域** | ✅ AUTO | `status` · `plan` · `knowledge` · `publish`（不带授权） |
| `libtv_skill` | LibTV（liblib.tv）**技能入口骨架**：会话/切项目/批量下载的契约与红线 | **无作用域** | 🔒 **不自动跑**（唯一理由见 §3.2） | `status` · `install` · `session_contract` |
| `libtv_workflow` | LibTV **节点式工作流骨架**：五动作 / 五节点 / 参数契约 / 两条避坑 | **无作用域** | ✅ AUTO | `status` · `params` · `gate_group` · `gate_schema` |
| `h3_video_gen` | H3mini 视频生成**骨架**：四原语 + 三条带牙用例 + 五条红线 | **无作用域** | ✅ AUTO | `status` · `skills` · `test_cases` · `hardware` · `gate_hw` · `gate_prompt` · `gate_localize` |

四位的图鉴读数**完全一致**：`enabled=true` · `safe=true` · `disabled=false` ·
`needs_confirmation=false` · `requires_params=[]` · `params_hint=""` · `channel="omnipulg"`。
**`type=external` 只出现在 `h3_video_gen` 的能力位描述里**（`media_pipeline` 在
`gbt_allinone/tools/caps_called_audit.py:55` 另被登记为 `external` = **入口型**，那是"给人/API 用的门、不被别的模块 import 也不算孤儿"的意思，**不是"要出网"**）。
`libtv_skill` / `libtv_workflow` / `h3_video_gen` 三个模块里的 `CAP_TYPE = "external"` 是同一层含义（`libtv_skill.py:21` · `libtv_workflow.py:23` · `h3_video_gen.py:40`）。

**三位共用同一套"只读骨架"形状**（能力位描述里的 `只读骨架·门`），这是本域最重要的共同特征：

| 骨架里有什么 | 说了什么 |
|---|---|
| `readonly: true` | 它自己声明这一发只读 |
| `ok` / `denied` / `rule` / `why` | 带牙判据的**判**（不是执行） |
| `source` / `evidence` / `evidenced` | 这些契约**从哪来、有没有独立取证** |

### 🔴 先记住这一句：**本域现在一条生成端都没接**

四位真跑出来的自报读数（§3 逐个有原文）：

- `media_pipeline` → `external_generators_connected: false`；
  模块 docstring 原话：*「这是编排和审查层，**不是假装拥有某个外部生成服务**」*；
- `libtv_skill` → `forensics.key_configured: false` · `libtv_hits_on_disk: 0` · `INSTALL.status: "未安装"`；
- `libtv_workflow` → `source: "主人提供 · 盘上无命中 · 未独立取证（出网受限 + 画布需登录）"`；
- `h3_video_gen` → `mode: "api"` · `requires_external_key: true` · 官方技能包 `evidenced: false`。

⇒ **说"我出了一条视频"是假话**；本域现在能说的最硬一句是：
**"我把出片该走的编排、契约、红线、判据读全了，等的钥匙和技能包还没到。"**

---

## 1. 什么时候用（意图 → 落点）

| 人想干什么 | 落到哪个位 | 只读还是要授权 |
|---|---|---|
| "短视频/电影/音乐从策划到成片怎么排"、"要哪些门" | `media_pipeline`（`op=plan` / `op=knowledge`） | 只读，零作用域 |
| "这条片子过没过审、能不能发" | `media_pipeline`（`op=review` / `op=publish`） | `publish` 只读且**必被阻断**；`review` 会写审计（§7） |
| "LibTV 怎么登录 / 怎么查进展 / 怎么切项目 / 怎么批量下载" | `libtv_skill`（`op=cli` / `op=contract` / `op=session_contract`） | 只读，零作用域 |
| "LibTV 的密钥该怎么放" | `libtv_skill`（`op=key_policy` / `op=gate_key_injection`） | 只读，零作用域 |
| "LibTV 节点式工作流怎么搭（建节点/连线/跑）" | `libtv_workflow`（`op=actions` / `op=node_types` / `op=howto`） | 只读，零作用域 |
| "生成器参数 `-s` 该写哪些键" | `libtv_workflow`（`op=params` / `op=gate_schema`） | 只读，零作用域 |
| "H3mini 有哪几种入口（文生/图生/首尾帧/参考）" | `h3_video_gen`（`op=primitives`） | 只读，零作用域 |
| "H3mini 的提示词该怎么写" | `h3_video_gen`（`op=gate_prompt`） | 只读，零作用域 |
| "H3mini 本地能不能跑" | `h3_video_gen`（`op=hardware` / `op=gate_hw`） | 只读，零作用域（**门槛读数当下是空的**） |
| **"帮我出条视频/出张图"** | ⚠ **本域没有能真出片的位**（见 §0 那一句） | —— |

### 🔴 与 `gbt-arkcli` 的分工（**一句话，两边都不许冒充**）

> **Ark 云端那条走 `gbt-arkcli` 规程**（`arkcli +gen` / Seedream / Seedance，要带调用前缀、过登录闸+账号验证闸、按计费纪律报价确认）；
> **本域管的是本机这 4 个能力位**（LibTV / H3mini / 流水线骨架的**契约与判据**）。
> 谁都不许拿对方的读数替自己说话：本域**不替 Ark 报价、不替 Ark 出片**；`gbt-arkcli` **也不代表本域这几位已经接线**。

---

## 2. 怎么调（万能插唯一门）

```powershell
# ── media_pipeline · 流水线编排面（纯读）──
py -3.14 tools/codex-scripts/five-dim.py cap media_pipeline                                  # status：有哪三类
py -3.14 tools/codex-scripts/five-dim.py cap media_pipeline '{"op":"plan","kind":"short_video","title":"<片名>","brief":"<一句话>"}'
py -3.14 tools/codex-scripts/five-dim.py cap media_pipeline '{"op":"knowledge","kind":"short_video"}'
py -3.14 tools/codex-scripts/five-dim.py cap media_pipeline '{"op":"publish","room_id":"media-draft-short_video"}'   # 不带授权 → 必 blocked

# ── libtv_skill · LibTV 技能入口骨架 ──
py -3.14 tools/codex-scripts/five-dim.py cap libtv_skill
py -3.14 tools/codex-scripts/five-dim.py cap libtv_skill '{"op":"install"}'                  # 官方两种装法 + 未安装读数
py -3.14 tools/codex-scripts/five-dim.py cap libtv_skill '{"op":"session_contract"}'         # projectUuid/sessionId 契约
py -3.14 tools/codex-scripts/five-dim.py cap libtv_skill '{"op":"access_redlines"}'          # 官方五条 + 追加四条
py -3.14 tools/codex-scripts/five-dim.py cap libtv_skill '{"op":"gate_key_injection","source":"model_key_pool","inject_to_child_env":true}'

# ── libtv_workflow · 节点式工作流骨架 ──
py -3.14 tools/codex-scripts/five-dim.py cap libtv_workflow
py -3.14 tools/codex-scripts/five-dim.py cap libtv_workflow '{"op":"params"}'
py -3.14 tools/codex-scripts/five-dim.py cap libtv_workflow '{"op":"gate_group","bound_keys":[]}'
py -3.14 tools/codex-scripts/five-dim.py cap libtv_workflow '{"op":"gate_schema","keys":["aspect"]}'

# ── h3_video_gen · H3mini 骨架 ──
py -3.14 tools/codex-scripts/five-dim.py cap h3_video_gen                                    # status 很大 → 默认收窄成键清单
py -3.14 tools/codex-scripts/five-dim.py cap h3_video_gen '{"op":"skills"}'
py -3.14 tools/codex-scripts/five-dim.py cap h3_video_gen '{"op":"test_cases"}'
py -3.14 tools/codex-scripts/five-dim.py cap h3_video_gen '{"op":"hardware"}'
py -3.14 tools/codex-scripts/five-dim.py cap h3_video_gen '{"op":"gate_hw","mode":"local"}'
py -3.14 tools/codex-scripts/five-dim.py cap h3_video_gen '{"op":"gate_prompt","prompt":"<一整段散文>"}'
py -3.14 tools/codex-scripts/five-dim.py cap h3_video_gen '{"op":"gate_localize","targets":["https://oss.example.com/a.mp4"]}'
```

🔴 **PowerShell 里传 JSON 载荷：用单引号原样包住 JSON**（`'{"op":"params"}'`）。
写成 `'{\"op\":\"params\"}'` 会让 `five-dim.py:130` 的 `json.loads` 直接抛
`JSONDecodeError: Expecting property name enclosed in double quotes` —— **还没碰到门就死了**，
而且看起来像"命令写错了"。**这是本机在 `llm` 域实测踩到的同一个坑**，本域照同一条规矩。

**`--full`**：`cap h3_video_gen` 的 status 是 **102 个键 / 19051 字符**，默认被收窄成键清单
（`_truncated.原始字符数: 19051` · `默认上限: 1500`）。要看全量加 `--full`，
或**收窄 payload**（推荐：`{"op":"modalities"}` / `{"op":"hardware"}` 这类）。
收窄后**输出始终是合法 JSON**（不是硬切字符）—— 这是 `five-dim.py:31-49` 那条实测缺陷修完后的样子。

---

## 3. 四个位逐个点（实测读数 + 失败典型）

> 下表 `门` 列 = `policy.evaluate()` 静态查出来的作用域（§4）；`omni` 列 = `omni.py auto_run_verdict()` 会不会自动替你跑。

### 3.1 `media_pipeline` —— 流水线编排 + 自审 + 发布门

| 项 | 值 |
|---|---|
| 用途 | AI 短视频/电影/音乐流水线：**镜像房间编排、产物自审、版权/安全/品牌/质量检查、主人授权后发布** |
| 门 | **无作用域**（`risk='low'` · `restricted=False`），`omni` 判 **AUTO** |
| 参数 | 不要（`requires_params=[]`）；但**不同 op 要不同字段**，见下 |
| 真身 | `gbt_allinone/tools/media_pipeline.py`（`run:228`）· 分发 `api.py:730` |

**纯读 op**（本规程真跑过）：`status` · `plan` · `knowledge` · `collaborate` · `publish`
**有副作用的 op**（本规程**没跑**，见 §7）：`compose`（往镜像房间落盘）· `launch_cycle`（建长程任务）
· `review`（**会写一条审计** `media_self_review`）

**真跑返回（原文摘录）**：

```json
// cap media_pipeline
{ "ok": true, "kinds": ["short_video", "film", "music"],
  "policy": "mirror-first, self-review, owner-gated publish" }

// cap media_pipeline '{"op":"plan","kind":"short_video","title":"测试片","brief":"验证骨架"}'
{ "ok": true, "schema": "gbt-media-pipeline/v1", "kind": "short_video", "label": "短视频",
  "stages": ["script","storyboard","assets","edit","export"],
  "gates": ["asset_integrity","copyright","safety","brand","quality","owner_review","publish_auth"],
  "publish_policy": "draft_or_blocked_until_owner_authorization" }

// cap media_pipeline '{"op":"publish","room_id":"media-draft-short_video"}'  ← 不带授权
{ "ok": false, "blocked": true, "room_id": "media-draft-short_video",
  "reason": "发布属于不可逆外部动作，需要主人一次性授权",
  "next": "先在镜像房间完成自审和排练，再由主人发放 deploy_publish" }
```

**`op=knowledge` 的关键字段（真跑，`kind=short_video`）**：
`knowledge.roles` **8 个**（商业机会研究员 / 短视频策划 / 分镜导演 / AI视觉制片 / 配音与混音 / 短片剪辑 / 独立质审 / 发布归因）·
`knowledge.craft` **4 条**（首 3 秒建立冲突或收益承诺 · 每个镜头只承载一个信息 · 画面/旁白/字幕语义一致 · 节奏服务信息而不是堆转场）·
`knowledge.quality` **5 条** · `knowledge.metrics` **5 条** ·
`common_gates` **10 条**（需求与受众证据 / 成本上限 / 脚本事实核验 / 角色与品牌一致性 / 素材授权清单 / 技术读数 / 独立 checker / 镜像排练 / 主人发布授权 / 发布后收益归因）·
🔴 **`external_generators_connected: false`**。

**怎么念这几个字段（最容易读错的地方）**：

- `gates` / `common_gates` 是**清单**（该过哪些门），不是**读数**（过了几道门）。**没有任何一格告诉你"已经过审"**。
- `publish` **不带授权必 `blocked:true`**；**带上授权也一样 `blocked:true`** ——
  源码 `media_pipeline.py:222-225` 的第二个分支明写：
  *「授权令牌只允许通过统一 run_task 发布门消费；**模块不接受自带令牌绕门**」*。
  ⇒ **别指望从这条 op 拿到"发布成功"**；它是**阻断面**，不是发布面。
- `plan` 全程**不碰盘、不出网**，纯拼一个清单；`title` / `brief` 只是回显。

**失败典型长什么样**：

- 未知 kind（比如 `{"op":"plan","kind":"mv"}`）→ `{"ok": false, "error": "unknown media kind: mv"}`；
  `film` / `music` / `short_video` 才是三个合法值。
- 未知 op → `{"ok": false, "error": "unknown op: <op>"}`。
- ⚠️ **这两种失败都是"本体 `ok:false`"，而外层 `status` 仍是 `ok`、退出码仍是 0** —— 见 §5。

---

### 3.2 `libtv_skill` —— LibTV 技能入口骨架（**`omni` 里唯一被 🔒 的那个位**）

| 项 | 值 |
|---|---|
| 用途 | LibTV 技能（只读骨架·门）：Agent 创作平台入口（会话进展/增量轮询 + 切项目 + 批量下载）；**密钥走 `model_key_pool`、结果必须落 `trace_store`** |
| 门 | **无作用域**（`risk='low'` · `restricted=False`） |
| `omni` | 🔒 **不自动跑** —— 理由只有一条：`名字带写动作字样（deploy/release/publish/…）` |
| 参数 | 不要（`requires_params=[]`）；op 见下 |
| 真身 | `gbt_allinone/tools/libtv_skill.py`（`run:739`）· 分发 `api.py:424` |

🔴 **这条 🔒 是假阳性，必须点名**：`omni.py:137-140` 的
`DANGEROUS_NAME_RE = deploy|release|publish|submit|rollback|rewind|ascend|purge|delete|drop|shape|rehearse|simulate|install|uninstall|write|patch|**kill**|stop|restart`，
而 **`skill` 这个词里就含 `kill`** ⇒ `libtv_skill` 被名字误伤。
实测原文：`🔒 不自动跑：名字带写动作字样（deploy/release/publish/…）`。
⇒ **不许把它念成"这个能力位有安全风险"** —— 它零作用域、只读骨架；
真正拦住它的是**一条子串正则的误伤**。（同族坑：`omni.py` 的自动执行判据宁可保守，
假阳性可解释、假阴性会出事故 —— 所以这条**不必修**，但要**知道**。）

**真跑返回（原文摘录）**：

```json
// cap libtv_skill
{ "ok": true, "readonly": true, "kind": "libtv_skill", "domain": "video", "type": "external",
  "skill_source": "libtv-labs/libtv-skills", "actions": 3,
  "key_envs": ["LIBTV_ACCESS_KEY","LIBTV_API_KEY","LIBTV_TOKEN"],
  "forensics": { "as_of": "2026-09-20T12:5x", "libtv_hits_on_disk": 0,
                 "skill_dirs": {"~/.openclaw/skills": true, "~/.openclaw-autoclaw/skills": true,
                                "~/.agents/skills": true},
                 "key_configured": false },
  "note": "技能包与密钥均**未接**（取证：libtv 命中 0 · 密钥未配）" }
```

**依赖什么（真跑 `op=install` 的原文）**：

```json
{ "method_npx": "npx skills add libtv-labs/libtv-skills --skill libtv-skill",
  "method_clone": "git clone https://github.com/libtv-labs/libtv-skills.git → 解压到 ~/.openclaw/skills/",
  "landing": "~/.openclaw/skills/（OpenClaw 技能规范）",
  "deps": "**无需额外依赖：仅用 Python 标准库**",
  "requires_network": true, "needs_owner_authorization": true,
  "status": "未安装（R-H208 取证：三个技能目录里都没有 libtv）" }
```

⇒ **依赖三件**：① 官方技能包（**未装**，且装它要**出网 + 主人点头**，本规程不装）；
② `LIBTV_ACCESS_KEY`（**未配**，且只许从 `model_key_pool` 借、只在该次子进程 env 里注入）；
③ **人的浏览器登录**（`POLICIES.human_login` 原话：*「登录这一步要人在浏览器里点 ⇒ **Agent 不代签**」*）。

**会话契约（真跑 `op=session_contract`）**：

```json
{ "scripts_dir": "scripts/",
  "invocation": "python3 scripts/<脚本> …（脚本在技能包的 scripts/ 目录下）",
  "returns": ["projectUuid","sessionId"],
  "why": "**这两个是后续一切操作的钥匙**：查进展、下载结果都要带它们；丢了就只能重建会话（= 白花钱）",
  "poll_cursor": "--after-seq <N>（**增量轮询的游标**：只拿第 N 条之后的新增，不拿全量）",
  "creation_style": "**所有创作通过发送自然语言消息完成**，Agent 自己编排工作流 —— 不许绕过这条去自己拼参数/拼请求" }
```

**这个位怎么用（正确姿势）**：**把它当"查规章的地方"** —— 密钥口径、脚本白名单、失败归类、交付七件、画布分区，
全部通过 `op=` 读出来（`key_policy` / `scripts` / `contract` / `canvas` / `delivery` / `policies`）。
**它自己不发一个请求**：模块 docstring 原话 *「本骨架只读：**不装技能包、不复制脚本、不调 API、不落盘、不出网**」*。

**失败典型长什么样**：
`op` 不在白名单 → `raise ValueError("未知 op %r（可用：status/redlines/actions/…）")`。
**注意这不是"信封式的失败"**：它是 Python 异常。经 `run_task(safe=False)` 时**异常会向上传播**，
`five-dim.py` 不会把它包装成 `status:error` —— 你会看到**一条 traceback 而不是一段 JSON**。
⇒ 见到 traceback **先看 `可用：…` 那半句**（它把合法 op 全列了），别急着当"能力坏了"。

---

### 3.3 `libtv_workflow` —— LibTV 节点式工作流骨架

| 项 | 值 |
|---|---|
| 用途 | 节点式工作流（只读骨架·门）：五动作 `create_node`/`connect`/`set_params`/`run`/`batch_run` + 五大基础节点 + 参数契约（`-s` 走 schema / `-u` 顶层）+ 两条避坑（资源组绑定 / 终点抑制 stdout） |
| 门 | **无作用域**（`risk='low'` · `restricted=False`），`omni` 判 **AUTO** |
| 参数 | 不要（`requires_params=[]`）；gate 类 op 要各自字段 |
| 真身 | `gbt_allinone/tools/libtv_workflow.py`（`run:139`）· 分发 `api.py:459` |

**真跑返回（原文摘录）**：

```json
// cap libtv_workflow
{ "ok": true, "readonly": true, "kind": "libtv_workflow", "domain": "video", "type": "external",
  "actions": 5,
  "node_types": ["文本节点","图片节点","视频节点","音频节点","脚本节点"],
  "core": "不是「写提示词」，是「搭工作流」",
  "evidence": "五动作与已落两套（3 actions / 5 原语）全不相同 ⇒ 真新增量",
  "source": "主人提供 · 盘上无命中 · 未独立取证（出网受限 + 画布需登录）" }

// cap libtv_workflow '{"op":"params"}'
{ "generator":    { "flag": "-s", "rule": "走模型 schema 校验，**schema 外的键会被拒绝**" },
  "node_top_level": { "flag": "-u", "rule": "节点顶层属性" },
  "history_defaults": { "model": "StarVideo 2.0", "aspect": "16:9",
                        "resolutions": ["720p（预览）","1080p（定稿）"] } }
```

**两条避坑（骨架原文，`PITFALLS`）**：
① **资源组绑定** —— 建组后**必须** `libtv group use -r` 从**标准输入**读 key 绑定资源，
否则节点可能**找不到依赖的素材**；
② **管道输出** —— **终点节点**建议 `>/dev/null` 抑制 stdout，避免输出误流到外层管道，
导致下游程序**收不到预期的 key**。

**两个 gate 的真跑读数（本域最重要的读数陷阱现场，见 §5）**：

```json
// cap libtv_workflow '{"op":"gate_group","bound_keys":[]}'
{ "ok": false, "denied": true, "rule": "group_not_bound", "stage": "run",
  "why": "建组后必须 `libtv group use -r` 从标准输入读 key 绑定资源；未绑定就 run / batch_run ⇒ 节点找不到依赖素材" }

// cap libtv_workflow '{"op":"gate_schema","keys":["aspect"]}'
{ "ok": false, "denied": true, "rule": "schema_unknown",
  "why": "拿不到模型 schema ⇒ 不许凭记忆写键（schema 外的会被平台拒）" }
```

🔴 **这两发的外层都是 `status: "ok"` · `denied: false` · `退出码 0`** —— 而本体的 `ok` 是 `false`、`denied` 是 `true`。
**（同一族坑在 `h3_video_gen` 的四个 gate 上逐个复现，共 6 发实测，见 §5。）**

**`source` 那一格要照念**：这个位的依据**不是官方文档**，是**主人提供**（画布项目分析）+ 盘上无命中 + 未独立取证。
⇒ 用它的时候要说清楚「这是主人给的画布口径，未经独立取证」，
**不许把它说成"官方文档说"**。（同族的自报诚实：`gbt_allinone/positions.py:92-95` 把
`make_short`（短视频创作）的 `min_level` 从 `full` 如实标成 `read`，`gap` 写的是
*「libtv_workflow 仍是只读骨架，生成端未接；分镜/剧本段已可跑」* —— **这正是本域现状的官方口径**。）

**失败典型长什么样**：`op` 不在白名单 → 同 §3.2，`raise ValueError("未知 op %r（可用：status/actions/node_types/params/pitfalls/howto/redlines/gate_group/gate_schema/gate_stdout/gate_key）")` —— **异常，不是信封**。

---

### 3.4 `h3_video_gen` —— H3mini 视频生成骨架（**图鉴里标了 `type=external` 的那一个**）

| 项 | 值 |
|---|---|
| 用途 | H3mini 视频生成（只读骨架·门）：四原语 **T2VA / I2VA / FL2VA / Ref2VA** + 三条带牙用例 + 五条红线；**引用官方仓库技能，不复制 SKILL.md** |
| 门 | **无作用域**（`risk='low'` · `restricted=False`），`omni` 判 **AUTO** |
| 参数 | 不要（`requires_params=[]`）；gate 类 op 要各自字段 |
| 真身 | `gbt_allinone/tools/h3_video_gen.py`（`run:1128`）· 分发 `api.py:469` |

**四原语（骨架原文）**：`T2VA` 文生视频（文本）· `I2VA` 图生视频（一张参考图 + 提示词）·
`FL2VA` 首尾帧（首帧 + 尾帧，两端锚定、中间由模型补）· `Ref2VA` 参考生视频（保对象一致性）。

**官方技能包（真跑 `op=skills`，原文）**：

```json
{ "repo": "https://github.com/MiniMax-AI/MiniMax-H3", "count": 9, "core": "h3-prompt-writing",
  "core_note": "纯 Markdown · 零外部依赖 ⇒ 引用它，不抄它",
  "install_hint": "npx skills add https://github.com/MiniMax-AI/MiniMax-H3 --skill h3-prompt-writing",
  "evidenced": false, "evidence_note": "主人提供 · 盘上 0 命中 · 未独立取证（出网受限）",
  "ref_not_copy": "引用官方仓库技能，**不复制 SKILL.md 内容**" }
```

**硬件门槛（真跑 `op=hardware` 与 `op=gate_hw`，原文）**：

```json
// op=hardware
{ "hardware": { "local_min_vram_gb": 32.0, "local_peak_vram_gb": 31.7,
                "local_slim_checkpoint": "精简 INT8 检查点（官方给的低配路径）",
                "this_machine_vram_gb": null,
                "this_machine_note": "读数拿不到（nvidia-smi 不在 PATH · 沙箱身份下 WMI 被拒）",
                "mode": "api",
                "mode_reason": "本机 RAM 7.4GB / 负载 93% ⇒ 带不动 31.7GB 峰值；走 API 不占本地显存" },
  "gate": { "ok": true, "mode": "api", "requires_external_key": true, "local_vram_needed": false,
            "why": "API 模式不占本地显存；**需要 MINIMAX_API_KEY**（当前盘上没有）" } }

// op=gate_hw  mode=local
{ "ok": false, "denied": true, "rule": "hardware_unverified", "need_gb": 32.0,
  "why": "本地模式读数拿不到（显存没测出来）⇒ **不许说能跑**；要本地跑先拿读数，否则走 API 模式" }
```

**带牙用例（真跑 `op=test_cases`）**：

```json
{ "file": "gbt_allinone/tests/test_h3_video_gen.py", "count": 99,
  "teeth_cases": ["密钥不走明文 → plaintext_key",
                  "结果必须落盘（视频 + 音轨）→ result_not_localized / audio_not_localized",
                  "提示词必须官方六段式（不接受散文式）→ prose_prompt_rejected"],
  "note": "读出来的条数；**样本数为 0 就不算测到**（坑册 §45）" }
```

> `count: 99` 是**从盘上真数** `def test_` 的条数（`h3_video_gen.py:432` 的 `test_case_reading`），**不是手写数字**。

**两条判据的真跑读数（带牙用例真的会咬人）**：

```json
// op=gate_prompt（给一整段散文）
{ "ok": false, "denied": true, "rule": "prose_prompt_rejected",
  "why": "散文式提示词被拒：必须按官方六段式分段给（段名以官方技能包为准）；散文会省略**结构显式化**的关系（来源：主人提供 · 2026-09-20）⇒ 所以「散文式提示词」必须拒，而不是「风格偏好」",
  "sections_note": "主人说「必须走官方六段式」；但六段**分别叫什么**要按官方技能包为准 —— 出网受限 ⇒ 本骨架只判「有没有按段给」，**不编段名**" }

// op=gate_localize（只给远程链接）
{ "ok": false, "denied": true, "rule": "result_not_localized",
  "remote_only": ["https://oss.example.com/a.mp4"],
  "why": "只给了远程链接 = 没落盘；必须下载到本地（工作区 / 本地 CDN）" }
```

**五条红线（`h3_video_gen.py:549` 原文）**：
① 密钥只存 DPAPI：`MINIMAX_API_KEY` 走密钥池，不许明文落盘、不许进返回值；
② 结果必须落盘：**视频 + 音轨**都要落到本地，不许只留远程链接；
③ 不绕官方入口：走官方技能 / 官方 API，不许自己拼请求；
④ 硬件门槛先验：本地要 32GB+（峰值 31.7GB）；**验不到就不许说「能本地跑」**；
⑤ 每次操作留痕：写 `trace_store`，`source_kind=h3mini`。

⚠️ **两处"并排记、未定论"的口径（骨架自己留的，不许替它拍板）**：
- 追踪取值：主人给的是 `source_kind="h3"`，盘上钉的是 **`h3mini`** ⇒ 骨架把两条**并排登记**（`TRACE_KIND_GAP`），
  `resolution: None`（**待主人一句话定**）。**本规程不替它改常量。**
- 官方六段式的**段名未取证** ⇒ 骨架只判"有没有按段给"，**不编段名**。**用的时候别自己发明六个段名。**

**这个位怎么用（正确姿势）**：**把它当"写提示词前的检查器 + 硬件门槛的先验器"** ——
`op=gate_prompt`（六段式）· `op=gate_localize`（必须落盘）· `op=gate_hw`（先验显存）· `op=gate_official`（不绕官方入口）。
**它不发请求、不装技能、不落盘、不发密钥。**

**失败典型长什么样**：`op` 不在白名单 → `raise ValueError("未知 op %r（可用：status/primitives/skills/hardware/redlines/modalities/gate_key/gate_localize/gate_prompt/gate_hw/gate_official/gate_blank/gate_merge/gate_hw_threshold/gate_source_kind/gate_hw_rows/gate_duration/gate_verbatim/test_cases）")` —— **异常，不是信封**。

---

## 4. 要过哪道门：**静态查，不靠跑它才知道**

```python
from gbt_allinone.security import policy
d = policy.evaluate(kind, {})          # 只读求值，不执行、不消耗授权
list(d.scopes)                          # → 这个位要过哪几个作用域
```

**本域静态查出来的全量（2026-09-22 实测，四个位逐个数过）**：

| 作用域 | 覆盖哪些位 | 说明 |
|---|---|---|
| （**零作用域**） | `media_pipeline` · `libtv_skill` · `libtv_workflow` · `h3_video_gen` | **四个全不要授权** |

四位实测读数**完全一样**：`scopes=()` · `risk='low'` · `restricted=False`。

🔴 **但有一句必须说清（这是读对地方的关键）**：`policy.py` 里
**这四个 kind 一个分支都没有**（`Select-String -Path gbt_allinone/security/policy.py -Pattern 'media_pipeline|libtv|h3_video'` → **零命中**）。
所以它们是**落到默认放行分支**（`policy.py:120-141`：没命中任何 `elif` ⇒ `scopes` 为空 ⇒ `risk='low'`），
**不是因为有一条"这几个是只读"的白纸黑字规则**。
「免授权」在这四位上是**规则缺席**的结果，不是**显式声明**的结果 ——
将来谁给 `video` 域（或这四个 kind）加了分支，这里的结论就要**重查**，**不许把本文件当永久凭证**。
（对照：同族的 `prompt_bridge` / `voice_orchestra` / `ledger_note` 都有**显式分支**做 fail-closed —— 这四个没有。）

### 4.1 `missing_scopes` / `reason` / `how_to_grant` 为什么本规程里一个实例都没有

这三位字段**只在 `denied` 为真时才写进 `five-dim.py` 的输出**（`five-dim.py:148-153`）：

```python
if denied:
    out["missing_scopes"] = gr.get("missing") or gr.get("missing_scopes") or []
    out["reason"] = str(gr.get("reason") or gr.get("message") or "")[:200]
    out["how_to_grant"] = gr.get("how_to_grant") or []
```

而四位零作用域 ⇒ **`denied` 走不到那一段**。**不是我漏抄，是本域不触发。** **编三个字段出来才是造假。**

**万一将来真出现 `denied: true`（规矩，不是读数）**：
照 `cap` 打印的原文把缺的作用域抄进报告，**命令只打印不绕门**；
授权只能主人在终端发（`python -m gbt_allinone auth grant --scope <scope> --ttl 600`），
**AI 永远无权给自己发授权**；而**发出片/出图这类要外部服务、要 `external_llm`/`data_export` 的动作之前，
先要主人配钥匙 + 发授权 + 装技能包 —— 三件缺一不可**。

### 4.2 `omni` 会不会替你自动跑（实测，`auto_run_verdict()` 现算）

| 位 | AUTO | 理由 |
|---|---|---|
| `media_pipeline` | ✅ | —— |
| `libtv_skill` | 🔒 | `名字带写动作字样（deploy/release/publish/…）`（假阳性，§3.2） |
| `libtv_workflow` | ✅ | —— |
| `h3_video_gen` | ✅ | —— |

实测同一份判据下的旁证：`omni list --domain video` 打的就是这三个 ✅ 一个 🔒；
`PROBE_SKIP_KINDS`（2026-09-24 深修后 = 探测专项 ∪ `preflight.state_changing_kinds()`，
共 22 个）里，**这四个位一个都不在**。

🔴 **但"在 AUTO 名单里"从来不等于"跑了就有结果"**：
`omni run` 真跑时执行的是 `five-dim.py cap <kind>`（**不带 payload**，`omni.py:505`），
也就是**只会跑各家的 `status`** —— 所以自动跑本身是只读的、安全的，
**拿回来的仍然只是"骨架形状"，不是一条视频**。
（`video` 也**不在** `DANGER_DOMAINS`（那是 `pipeline`/`dangerous`/`infra`/`integration`）——
但**"不是危险域"不等于"本域能出片"**，逐位仍按上表与 §3 判。）

---

## 5. 🔴 报告层红线（**这四条是本域真跑出来的，不是想象**）

> 出口前先问一句：**「这是事实，还是我读错了层？」**

### 5.1 三层信封：真数据在 `result.result` 里，不在 `status` 上

实测 `gbt_allinone.run_task('libtv_workflow', {'op':'gate_group','bound_keys':[]})` 的**顶层键**只有 7 个：

```
['error', 'gbt_result', 'gbt_stamp', 'kind', 'ok', 'result', 'status']
顶层： status='ok'  ok=True  denied=None
```

而真正的判据在**第三层**：`result.result.ok == False` · `result.result.denied == True` · `rule='group_not_bound'`。
（`gbt_result` 里也有一份同样的三层结构。）

⇒ **读本域任何一位，都要下钻到 `result.result`**；
只看顶层会得到「`status: ok` · `ok: true`」这种**看着全绿、实际被拒**的假象。

### 5.2 `status:"ok"` ≠ 本体 `ok:true`（**本域 6 发实测复现**）

| 命令 | 外层打印 | 本体（`result.result`） |
|---|---|---|
| `cap libtv_workflow '{"op":"gate_group","bound_keys":[]}'` | `status ok` · `denied false` · exit **0** | `ok:false` · `denied:true` · `rule group_not_bound` |
| `cap libtv_workflow '{"op":"gate_schema","keys":["aspect"]}'` | `status ok` · `denied false` · exit **0** | `ok:false` · `denied:true` · `rule schema_unknown` |
| `cap h3_video_gen '{"op":"gate_prompt","prompt":"<散文>"}'` | `status ok` · `denied false` · exit **0** | `ok:false` · `denied:true` · `rule prose_prompt_rejected` |
| `cap h3_video_gen '{"op":"gate_localize","targets":[<远程>]}'` | `status ok` · `denied false` · exit **0** | `ok:false` · `denied:true` · `rule result_not_localized` |
| `cap h3_video_gen '{"op":"gate_hw","mode":"local"}'` | `status ok` · `denied false` · exit **0** | `ok:false` · `denied:true` · `rule hardware_unverified` |
| `cap media_pipeline '{"op":"publish","room_id":"…"}'` | `status ok` · `denied false` · exit **0** | `ok:false` · `blocked:true`（发布被阻断是**设计**，不是故障） |

**原因（源码级）**：`run_task` 的 `status` 说的是**"这一发调用跑没跑通"**，
本体 `ok` 说的是**"这件事能不能做/做对没有"**。两件事。

### 5.3 退出码不可信（本域尤其）

`five-dim.py:163` 的返回值是 `0 if out["status"] in ("ok","success") else 1` ——
而 `out["status"]` 取的是**外层** `status`。⇒ 本域 6 发"本体判否"**全是 exit 0**。
**别把 exit 0 读成"判据通过了"**；也**别把 exit 1 一律读成"命令敲错了"**（在别的域，`denied`/`user_error` 也是 1）。

### 5.4 两种 `denied` **完全不同类**，不许混着念

| 你看到的 `denied:true` 在哪一层 | 它是什么 | 该怎么办 |
|---|---|---|
| **外层**（顶层或 `gbt_result` 顶层）+ 带 `missing_scopes`/`how_to_grant` | **授权门拒了**（policy/auth_gate） | 如实报缺哪个作用域，把 `how_to_grant` 交给主人；**不绕门** |
| **内层**（`result.result.denied`）+ 带 `rule`/`why` | **能力位自己的判据判否**（如"资源组没绑定"、"散文式提示词"） | 照 `rule`/`why` 改输入或如实报缺口；**这不是"欠授权"** |

🔴 **本域四位零作用域 ⇒ 本域现在只会遇到第二种。**
**别把 `rule:"prose_prompt_rejected"` 念成"被授权门拒了"** —— 那会让人白等一张根本不存在的授权。
（顺带一条给别域用的读法：`five-dim.py` 的扁平拒绝信封里，`missing_scopes` / `reason` / `how_to_grant` 在**顶层**
（`five-dim.py:132-153` 的 R-H299 注释就是拿一次事故换的）—— 本域**触发不到**，但知道它在那儿。）

### 5.5 `stamp` 是"回归印章的有无"，不是成功与否

四位真跑全是 `stamp: true`（因为都跑通了）。**别把 `stamp` 当"这件事做对了"** ——
`denied` 与 `user_error` 在别的域一律 `stamp: false`，而**本域的本体判否照样 `stamp: true`**（§5.2 那 6 发）。

---

## 6. 与 `gbt-arkcli` 的分工（再钉一遍）

- **走本域（`gbt-video`）**：本机 **LibTV / H3mini / 流水线骨架**的**契约、判据、红线、编排清单** ——
  也就是「**该怎么做才不犯低级错**」这一层。
- **走 `gbt-arkcli`**：**Ark 云端**那一条（`arkcli +gen` / Seedream / Seedance）—— 它有自己的
  **调用前缀 + 登录闸 + 账号验证闸 + 计费报价确认**纪律，**本域不复制、不代跑、不代报价**。
- **两边都不许冒充对方**：本域**不能**拿"我读到了 H3mini 的四原语"去说"我能在 Ark 上出片"；
  Ark 那条**也**不能拿"arkcli 能生视频"去说"本机 `h3_video_gen` / `libtv_workflow` 已经接线"——
  **实测它们都还是 `readonly` 骨架，生成端未接。**

---

## 7. 未验清单（**如实列，不许拿它当通过**）

| 项 | 卡在哪 / 为什么不做 |
|---|---|
| **LibTV 真出片**（`libtv login` → `libtv node --run`，或技能包 5 个脚本） | **未验**。卡在四处：① **技能包未装**（实测 `INSTALL.status: "未安装"`），装它要**出网 + 主人点头**；② 登录要**人在浏览器里点**（骨架原话：Agent 不代签）；③ 消耗**所登录账户的积分**（= 花钱）；④ 结果进 OSS 要下载落本地。**四条任一条都不该由我擅自动手** |
| **H3mini 真发一次生成**（API 模式） | ① 要 `MINIMAX_API_KEY`（真跑原文：*当前盘上没有*）；② 官方技能包 `evidenced:false` + 盘上 0 命中；③ 出网 + 计费 + 结果落盘。**未验** |
| **H3mini 本地模式** | **未验**。实测 `gate_hw mode=local` → `hardware_unverified`；`this_machine_vram_gb: null`（骨架自报：nvidia-smi 不在 PATH · 沙箱身份下 WMI 被拒）。**门槛读数都没有 ⇒ 不许说能跑** |
| **`media_pipeline` 的 `compose` / `launch_cycle`** | **未验（未跑）**。前者**往镜像房间落盘**（建房间 + `shape` 两个文件），后者**建长程监督任务**（`long_run_supervisor.create`）—— 都是**写面**，不是只读面（本规程只真跑纯读的四个 op） |
| **`media_pipeline` 的 `review`** | **未验（未跑）**。`self_review()` 会 `_audit("media_self_review", …)`，**写一条审计**。虽然只是审计、不是生成，**仍属落盘** ⇒ 如实记 |
| **本域是否该挂作用域** | **未验（且不许由我改）**。`policy.py` 现在零分支（§4）。**这是"当前实测状态"，不是"设计如此"** ——
将来接上 LibTV CLI / H3 API（要出网、要花钱、要 `process_execute`/`data_export`/`filesystem_write`）时，
**必须先给它们加作用域分支，再谈能跑** |
| **Ark 云端那条** | **本域不验**（分工见 §6，走 `gbt-arkcli`） |
| **四位之外这个域还有没有隐藏能力** | **未验（口径性未验）**。按图鉴口径只有 4 个；**图鉴是现扫产物**（`python tools/codex-scripts/omni.py build`），重建后需重查 |

---

## 8. 不许做什么（红线）

1. **不许把"没挂作用域"念成"能出片"**：零作用域只说明门没拦它。本域**生成端一条都没接**（§0）。
2. **不许说"我出了一条视频 / 一张图"** —— 除非真跑通了官方入口并有 `local_path` + `trace_ref` 两样证据；
   本规程**一次都没跑过生成**。
3. **不许绕门**：不为了"绕过授权"直接调 `gbt_allinone` 里的模块函数替掉 `run_task` 唯一门
   （AGENTS.md 明令：那是**未经授权的写入**，纪律上就是违规）。
4. **不许给自己发授权**：不跑 `auth grant`、不手写 `store/auth_grants.jsonl`、**不改 `security/policy.py`**。
5. **不许擅自装技能包**：`npx skills add libtv-labs/libtv-skills` / `npx skills add …/MiniMax-H3`
   都要**出网 + 主人点头**，而且**不许往 `~/.agents/skills/` 装**（工作区 AGENTS.md 明令）。
6. **不许把明文密钥放进任何地方**：LibTV 的 `LIBTV_ACCESS_KEY`、H3 的 `MINIMAX_API_KEY` 只许走
   `model_key_pool`/DPAPI；**只在该次子进程 env 里注入，进程结束即弃**；**不许贴进对话/日志/trace**。
7. **不许把内层 `denied:true` 说成"授权被拒"**（§5.4 两种 denied 不同类），
   **也不许把 `status:"ok"` 说成"判据通过了"**（§5.2）。
8. **不许把 `libtv_skill` 的 🔒 说成"它有安全风险"** —— 那是 `kill` 子串正则的**假阳性**（§3.2）。
9. **不许改 `tools/codex-scripts/omni.py`**（本域的深蒸登记由交付报告给出，不擅自动手）；
   **不许动别的域**、**不许改 `policy.py`**。
10. **不许把本规程当官方文档**：LibTV（`liblib.tv`）/ H3mini（MiniMax）的命令级细节**以官方为准**；
    本文件管的是**我们这儿的纪律、读法、诚实账**。凡标 `source: 主人提供 · 未独立取证` 的，
    **不许转述成"官方说"**。

---

## 9. 验收（做完怎么证明真做了）

**机检入口**：

```powershell
py -3.14 tools/codex-scripts/verify-distill.py --domain video --skill gbt-video
```

它检查五件**可判定**的事：
A 两份产物在、**逐字节相同**（工作区源稿 vs `~/.openclaw-autoclaw/skills/` 安装件）·
B frontmatter 有 `name` / `description` · C 这个域已登记为已深蒸 ·
D 规程里每个 `five-dim.py cap <能力位>` **在图鉴里真存在**（抓编出来的命令）·
E 这个域的**每个**能力位都被点到（抓遗漏）。
**不可判定的部分（叙述质量、坑准不准）它不假装能判** —— 那些靠本文件的诚实账自己扛。

**人复核点（自己做完再过一遍）**：

1. **四位逐个真跑** —— 不许只跑一个然后"其余类似"（四位读的东西完全不同）；
2. **报字段前先下钻到 `result.result`**（§5.1），并区分「外层 status」与「本体 ok」；
3. **凡 `denied:true` 先问是哪一层**（§5.4）；
4. **跑不了的写「未验」并写清卡在哪**（§7 是本域的账，不是免责条款）；
5. **`policy.evaluate()` 现查一遍**：四个位必须仍是 `scopes=()`；
   哪天变了，**回来改 §4 与 §7**，别让规程比代码旧。

---

## 10. 固化与出处（**重启后要在**）

| 什么 | 在哪 |
|---|---|
| 本规程（源） | `<仓>/skills/gbt-video/SKILL.md` |
| 本规程（装机·托管目录） | `~/.openclaw-autoclaw/skills/gbt-video/SKILL.md` |
| ⛔ **不许装到** | `~/.agents/skills/`（本仓 AGENTS.md 明令禁止） |
| 能力位名单（4 个） | `<仓>/state/skill_atlas.json`（`domain == "video"`）· 现扫可重建：`python tools/codex-scripts/omni.py build` |
| 能力位注册 | `gbt_allinone/caps_registry.py`（`media_pipeline:441` · `libtv_skill:850` · `libtv_workflow:892` · `h3_video_gen:904`） |
| 真身实现 | `gbt_allinone/tools/media_pipeline.py`（`run:228`）· `libtv_skill.py`（`run:739`）· `libtv_workflow.py`（`run:139`）· `h3_video_gen.py`（`run:1128`） |
| 分发路由 | `gbt_allinone/api.py`（`libtv_skill:424` · `libtv_workflow:459` · `h3_video_gen:469` · `media_pipeline:730`） |
| 授权判据（**单一真相**） | `gbt_allinone/security/policy.py` 的 `evaluate()`（**本域四位无分支 ⇒ 走默认放行**，见 §4） |
| 门与信封 | `gbt_allinone/api.py` 的 `run_task:1026`（三层信封）· `tools/codex-scripts/five-dim.py:122-163`（`cap` 的读法与退出码） |
| 自动执行判据 | `tools/codex-scripts/omni.py` 的 `required_scopes():143` / `auto_run_verdict():182` / `DANGEROUS_NAME_RE:137` |
| 域的定位现状 | `gbt_allinone/positions.py:90-96`（`make_short` 的 `min_level` 已如实降为 `read` + `gap` 写"生成端未接"） |
| 人话落点 | `python tools/codex-scripts/omni.py ask "用LibTV生一段短视频"` → 落到 `libtv_skill` / `libtv_workflow` / `media_pipeline`（三次实测都命中，见 §9 第 1 条） |

**深蒸登记（应加、本次未擅自动手）**：`omni.py` 的 `DISTILLED_DOMAINS` 加一行

```python
    "video": "gbt-video",
```

加完后 `python tools/codex-scripts/omni.py gaps` 里 `video 4 个能力位` 会从
`⏳ 在队里` 变成 `✅ 已深蒸 → gbt-video`。
（本次**没改** `omni.py` —— 交付命令里用 `--skill gbt-video` 让验收器按"已登记"口径硬判，
**没交付就会 FAIL，不会静默变绿**。）
