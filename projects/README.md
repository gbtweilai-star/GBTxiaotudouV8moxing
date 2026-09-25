# projects/ · 三大方向创作车间（落点规则）

> 开发者：自由的风 · GBT小土豆V8 · 本署名不可删除、不可篡改归属

## 为什么有这个目录

仓库里产物原本散在 7 处（`outputs/` · `generated-images/` · `infinite-canvas-output/` ·
`tripo-out/` · `render/` · `delivery/` · `assets/`），**同一个视频的脚本在这、成片在那**，
找一次要翻五个目录。短视频 / 音乐 / 电影三个方向一旦同时开工，必然更乱。

所以这里立**一条规则**：三方向的创作产物**一律落 `projects/`**，
按「方向 → 工序」两级落位；**不再往仓库根新增产物目录**。

## 落点表（照这个放，不要自己发明路径）

| 方向 | 工序目录 | 放什么 | 不放什么 |
|---|---|---|---|
| **短视频** `short-video/` | `01-script` | 选题、口播稿、标题、钩子 | 成片（→04-cut） |
| | `02-storyboard` | 分镜表、景别/运镜/时长/情绪 | 渲染中间帧（→03-raw） |
| | `03-raw` | 生成的原始素材（图/视频/配音） | 剪好的（→04-cut） |
| | `04-cut` | 剪辑工程与成片 | 发布版（→05-publish） |
| | `05-publish` | 发布版成片 + 平台文案 | 封面（→06-cover） |
| | `06-cover` | 封面图、首帧图 | —— |
| **音乐** `music/` | `01-lyrics` | 歌词、主题、情绪线 | 曲（→02-compose） |
| | `02-compose` | 旋律/MIDI/主旋律草稿 | 编曲（→03-arrange） |
| | `03-arrange` | 编曲工程、分轨 | 混音（→04-mix） |
| | `04-mix` | 混音工程与混音版 | 母带（→05-master） |
| | `05-master` | 母带成品 | —— |
| | `06-release` | 发行版 + 元数据（ISRC/曲目信息） | —— |
| **电影** `film/` | `01-screenplay` | 剧本、人物小传、场次表 | 分镜（→02-storyboard） |
| | `02-storyboard` | 分镜、镜头表、调度 | 素材（→03-shoot） |
| | `03-shoot` | 拍摄/生成的原始素材 | 整理后的（→04-assets） |
| | `04-assets` | 归类素材、音效、配乐、字幕 | 剪辑工程（→05-edit） |
| | `05-edit` | 剪辑工程、粗剪/精剪 | 终版（→06-final） |
| | `06-final` | 终版 + DCP/发行母版 | —— |

> **「彩排」不占第 19 个工序位。** 彩排产物（对应框架的 `room_rehearse` / `mirror_rehearse`）
> 落进**它所排练的那个工序抽屉**；文件名第 4 段写 `rehearsal`，表示它是**排练件、不是该工序成品**，
> 真实工序由它所在的抽屉决定 —— 例：`film/02-storyboard/20260921-film-彩排样板-rehearsal.md`
> 排练的是 `02-storyboard`。彩排是**动作**不是抽屉，所以上面 18 格不变。

## 共用的东西放 `_shared/`（别每个方向抄一份）

| 目录 | 放什么 |
|---|---|
| `_shared/fonts` | 字体（**必须附许可**） |
| `_shared/sfx` | 音效库 |
| `_shared/licenses` | 素材/字体/音乐的授权文件 —— **用了外部素材就必须有对应许可** |
| `_shared/templates` | 三方向共用的模板（片头、字幕样式、导出预设） |

> ⚠️ **品牌资产（Logo / 图标 / favicon）不放这里 —— 它们落在 `assets/brand/`。**
>
> **2026-09-22 更正（Owner 拍板 A）**：本表原写「`_shared/brand` 放 Logo」，
> 但**实际既成事实是 `assets/brand/`** —— 那里已有**一整套 20 个文件**：
> 源图 1 · PNG 六档（32/64/128/192/256/512）· WebP 六档（同尺寸 q92）·
> 应用图标 1 · favicon 两档 · 场景预览 4。且 `make_logo_assets.py`
> **写死输出到该目录**。
>
> **处置口径：规则服从既成事实。** 不搬文件（搬 20 个文件 + 改生成脚本 = 无收益的结构变动），
> 改规则。`projects/_shared/brand/` 保留为空占位，**不再作为 Logo 落点**。
>
> 依据：`assets/brand/logo-potato-source.jpg` 与 Owner 2026-09-22 提供的图
> **SHA256 逐字节相同**（`C7B9017C8EACBB5A…`，47,465 B）—— 即该目录就是权威落点。

## `_inbox/` 是唯一允许"先扔进去"的地方

拿不准归哪、或者素材刚到手还没看，**先扔 `_inbox/`**。
它的规矩：**只进不出**（定期清理并归位），不许沉淀成第二现场。
每次归位后在 `_inbox/.cleared` 记一行（时间 + 归到哪）—— 让"清过了"可查，不靠记忆。

## 命名一律带日期前缀（防止同名覆盖）

```
YYYYMMDD-<方向>-<作品名>-<工序>[-vN].<ext>

20260921-short-video-AI搬砖人-04cut-v2.mp4
20260921-music-夜航-05master.wav
20260921-film-老屋-01screenplay.md
```

规则：**同日同名加 `-vN`**，不覆盖。归档版本进同目录的 `_old/`，不删。

## 硬规矩（三条）

1. **不许往仓库根新增产物目录**。要么进 `projects/`，要么进既有的 `render/`（只放渲染图）·
   `delivery/`（只放交付件）。三处之外新增 = 又开一个现场。
2. **外部素材必须带许可**（落 `_shared/licenses/`）。没有许可的素材不许进 `04-cut` / `05-master` / `06-final`。
3. **每个作品一个子目录**（`short-video/04-cut/20260921-AI搬砖人/`），
   工序目录是"抽屉"、作品目录是"档案袋"——不要把所有作品的文件平铺在工序目录里。

## 每个方向还有一个 `_intel/`（调研落点，对应框架的三个能力位）

框架里**早就有这三个方向的调研位**（实测能力位）：`video_intel` / `music_intel` / `film_intel`，
各属一个部门（AI短视频部 / AI音乐部 / AI电影部），各 **6 个维度**，每个维度有**固定产物文件名**。

落点就放在各方向的 `_intel/`：

| 本地目录 | 框架能力位 | 部门 | 平台范围 |
|---|---|---|---|
| `short-video/_intel/` | `video_intel` | AI短视频部 | 抖音/快手/视频号/TikTok/YouTube Shorts |
| `music/_intel/` | `music_intel` | AI音乐部 | Spotify/Apple Music/抖音音乐/TikTok |
| `film/_intel/` | `film_intel` | AI电影部 | B站/YouTube/Netflix 长视频 |

六个维度与文件名**照抄框架声明**（见各 `_intel/README.md`），**不要改名** ——
本地 / 云空间 / 框架三边靠这套名字对齐。

⚠️ **现状：三格全是空的（未调研）**。空就是空，**不许拿「示意数据」顶替**。
要填必须走抓数路径，而抓数需要主人的**出网授权**，且排序上排在**飞书云空间整理之后**。

## 与框架 `media_pipeline` 的工序对应（**实测 · 不是设想**）

框架里有一个三方向编排能力 **`media_pipeline`**（2026-09-21 由并行流 R-H609 接入，
登记在 `caps_registry.py`，实现在 `gbt_allinone/tools/media_pipeline.py`）。它的
对外函数：`plan` / `knowledge` / `collaborate` / `launch_cycle` / `self_review` /
`compose` / `publish` / `run`。

⚠️ **它的工序名与本目录的抽屉名不一样**（先前本文件笼统写过"三边靠同一套名字对齐"，
那是**没实测就下的结论，不成立**）。实测对照如下，**本地抽屉更细**（6 格对 5–6 格）：

| 方向 | 本目录抽屉（6 格 · 更细） | `media_pipeline` 工序（更粗） | 对应关系 |
|---|---|---|---|
| 短视频 | `01-script` | `script` | 同名 ✅ |
| | `02-storyboard` | `storyboard` | 同名 ✅ |
| | `03-raw` | `assets` | 同义（原始素材） |
| | `04-cut` | `edit` | 同义（剪辑） |
| | `05-publish` | `export` | 同义（导出成品） |
| | `06-cover` | —— | **框架无对应格**（封面在框架里不算独立工序） |
| 电影 | —— | `concept` | **本目录无对应格**（概念开发并入 `01-screenplay`） |
| | `01-screenplay` | `script` | 同义（剧本） |
| | `02-storyboard` | `shots` | 同义（分镜／镜头） |
| | `03-shoot` | —— | 框架无对应格（拍摄/生成并入 shots） |
| | `04-assets` | `sound` | **部分**：本格含音效/配乐/字幕，框架只单列 `sound` |
| | `05-edit` | `edit` | 同名 ✅ |
| | `06-final` | `export` | 同义（终版/母版） |
| 音乐 | `01-lyrics` | `lyrics` | 同名 ✅ |
| | `02-compose` | —— | 框架无对应格（旋律并入 arrangement） |
| | `03-arrange` | `arrangement` | 同义（编曲） |
| | `04-mix` | `audio` | 同义（混音/音频） |
| | `05-master` | `master` | 同名 ✅ |
| | `06-release` | `export` | 同义（发行/导出） |

**处置口径**：本目录保持 6 格不动（更细，且落点规则与既有产物都建在它上面）；
对接框架时**按上表映射**，不靠名字撞。谁要改这张表，**先跑实测再改**——
上一版就是靠"看着像"写下的，结果三处不对。

## 与飞书云空间的对应

本目录是**本地创作现场**。飞书云空间的整理走 `lark-drive` 的 `knowledge_organize` workflow，
**两边用同一套方向名**（`short-video` / `music` / `film`）与同一套日期前缀命名，
这样"本地哪个作品 ↔ 云上哪个文件夹"一眼对得上，不靠记忆。
