# 视频剪辑任务报告 · `/video-edit`

- **时间**：2026-09-28
- **工作目录**：`C:\Users\ADMIN\Desktop\GBT小土豆V8`（任务说明为空 ⇒ 按技能条款以当前工作目录为素材目录）
- **产出**：`out/preview.mp4`（1920×1080 @30fps · 12.00s · 91KB · sha8 `7471a030`）

## 一、素材发现（先看再动）

无 `materials_manifest.json`。按技能给的 `find` 口径盘点当前工作目录（maxdepth 2，排除 `out/`、`.video_agent/`、`.claude/`、`.git/`、隐藏文件）后，**视频类素材只有两个**：

| 素材 | 规格 | 实测性质 |
|---|---|---|
| `video-out/cut-demo.mp4` | 6.35s · 640×360@30 · h264 + aac | **纯深蓝**整块纯色（YAVG 抽点 0/1.5/3/4.5/6s 全 = 29）+ 低频单音（过零率 0.031 · RMS −21.4dB ⇒ 不是语音） |
| `video-out/motion.mp4` | 10.00s · 1920×1080@30 · h264（**无音轨**） | 黑底 + 左上小号白字「Title」的**静态字卡**（6fps 局部复看 12 格一模一样、YAVG 恒 24.32） |

图片/音频类素材：盘点范围内没有（`find` 命中的其余文件均为 `.png/.jpg` 的截图与验收图，位于 `output/`、`delivery/` 等目录，**不属于本次剪辑源**）。

**假设（任务说明为空 ⇒ 保守选择，逐条记在这里）**：
1. 两份源都是**合成测试片**，没有故事、没有语音 ⇒ 这必然是一条**流水线验证片**，不是内容片；不硬编故事、不加未给素材。
2. 不做风格化处理（调色/转场/特效），只做**结构剪辑**（两段拼接 + 时长裁切）。
3. 面板里那张深蓝 + 黑块的画面是 tile 空格子造成的错觉：确定性 YAVG 抽点证明 cut-demo **全程纯色**。

## 二、剪辑决策（理由写在 `out/timeline.json` 的 `clips[].reason` 与 `out/preview.edit_decisions.json`）

| # | 片段 | 时间线位置 | 为什么 |
|---|---|---|---|
| 1 | `cut-demo.mp4` 0.0→3.0s | 0.0s | **冷开场**：两份里唯一带声轨的素材，给片子一个有声头部；同时验证「非画布分辨率 → 上采样到 1920×1080」这条渲染路径 |
| 2 | `motion.mp4` 0.0→9.0s | 3.0s | **字卡主体**：1080p 原生分辨率与画布一致（不缩放）；源 10s 裁到 9s，去掉尾部 1s |

**被否掉的选项**（也记进决策旁车）：只用 `motion.mp4` 单源裁切（丢掉唯一有声素材、全程同一张静态画面，更像转封装）；把 cut-demo 上采样后拉长到整片（纯色拉长只制造静止段并放大上采样模糊）。

## 三、工件清单（技能文件合同）

| 文件 | 状态 |
|---|---|
| `out/media.json` + `out/media/<源>.json` | ✅ 两个源的完整 ffprobe 元数据 |
| `out/media_analysis.json` | ✅ 场景变化 0 / 黑场区间 / 静音区间 / **YAVG 抽点**（含"blackdetect 会把深蓝当黑"的口径警告） |
| `out/video_ingest.json` + `out/ingest/<源>.json` | ✅ contact sheet + 高帧率局部复看图（**主 agent 已逐张亲自读过**），每包记录"我看到了什么" |
| `out/transcript.json` | ⚠️ `provider="unavailable"`、`segments=[]`：**ASR 不可用**（见第五节），按技能条款走无转录流程；**没有伪造任何转录内容**（且实测两份素材本无语音：单音 + 无音轨） |
| `out/timeline.json` | ✅ project/assets/sequence/tracks（main + audio）+ 片段理由 |
| `out/timeline_validation.json` | ✅ `ok=true` · 9 项检查 · 0 问题（有限数/时长不越源/主轨不重叠/理由非空/画布齐） |
| `out/preview.mp4` | ✅ 1920×1080@30 · 12.00s · 音轨连续覆盖整片 |
| `out/preview.render_report.json` / `render_plan.json` / `edit_decisions.json` | ✅ 绑定当前 timeline（sha8 一致）+ 滤镜图 + 决策与否决理由 |
| `out/preview_qc_report.json` | ✅ **errors = 0**；3 条 warning（下方逐条解释） |
| `out/preview_ingest.jpg` + `out/preview_ingest.json` | ✅ 预览自检抽帧（4×3 @1fps）与观察包（我自己读图后写的"看到了什么"），**不覆盖**源素材的 ingest 包 |

## 四、QC 结论

**硬错误 0 条。** 3 条 warning 全部是"源素材性质"，且都有第二处读数交叉验证：

1. **全程报黑场** —— 两份源本身就是纯色/黑底（cut-demo 暗蓝 YAVG=29、motion 黑底 YAVG≈24.3），
   `blackdetect` 的像素阈值把暗蓝也算黑。预览 YAVG 抽点（0.5–2.5s = 29.0；5.0–11.5s ≈ 23.32）与源一致 ⇒ **不是渲染故障**。
   *读数差异说明*：字卡段预览 YAVG 23.32 vs 源 24.32，差 1.0（≈4%），来自 x264 对"近黑底 + 极小面积白字"的有损量化，不是画面变化。
2. **3s 之后静音** —— 源 B **没有音轨**（`out/media.json` 里 `audio: null` 是硬证据）；渲染器按计划补了连续静音轨，
   以保证音轨覆盖整片（QC 要求音轨覆盖）。属预期行为，不是丢音。
3. **检测到静止段** —— 源 B 是静态字卡（同一帧持续 10s，复看图 12 格一模一样），静止来自素材本身。

## 五、工具限制（必须如实记，不许假装跑过）

技能指定的 **video-edit MCP 工具集在这台机器上不可达**：`mcporter` CLI 不存在（`command not found`），
运行时工具列表里也没有 `inspect_media` / `video_ingest` / `validate_timeline` / `render_preview` / `qc_preview`。

⇒ 按技能的降级条款，用 **ffmpeg/ffprobe 本地实现同等合同**（同名同义的 out/ 工件、同样的"先看→判断→校验→渲染→QC"次序），
并在每个工件里写明 `tooling: "本地等价…"`。**这不是"跑过了 MCP"**，是一套等价的本地实现：

- `inspect_media` → `ffprobe` 元数据；
- `video_ingest` → ffmpeg 出 contact sheet / 高帧率复看图，**由主 agent 亲自读图**后写"我看到了什么"；
- `analyze_media` → `blackdetect` / `silencedetect` / 场景变化 / `signalstats` YAVG 抽点；
- `speech_transcribe` → **不可用**（无云端 ASR、无本地转写后端）⇒ 如实记 `unavailable`，不伪造；
- `validate_timeline` / `render_preview` / `qc_preview` → 本地确定性校验 + ffmpeg 渲染 + 检测器 QC；
- 辅助脚本留在 `out/_local_pipeline.py` 与 `out/_local_render_qc.py`（可复核每一步）。

**无 ASR 的影响**：本片两份源都没有语音（单音 + 无音轨），所以"无转录"对剪辑判断没有实际损失。

## 六、未解风险 / 遗留

1. **工具缺口**：要把这套视频能力真正接通，需要让 video-edit MCP 服务在 `config/mcporter.json` 里可用
   （并装上 `mcporter` CLI）——属于**配置项，需主人决定**，我没有自行改动配置。
2. **素材性质**：本片是流水线验证片。若要做真实内容片，请提供真实素材（有故事/有语音的视频）。
3. **仓内副作用**：按命令要求，项目目录就是当前工作目录 ⇒ `out/` 落在**仓根**（新顶层树）。
   已做两件收尾：把它加进 `.gitignore`（生成物不入版本），并重跑 `tools/coverage_matrix.py sweep`
   把新顶层树登记进覆盖矩阵（免得成为"没人扫过的面"）。

## 七、与 closeout 钩子的字段口径对齐（补记）

本仓的 `video-agent-kit` closeout 钩子对合同工件有一组**更严的字段约定**，我第一版用的是自定的 `ok` 字段，
钩子因此判"未闭合"。已按它的口径重出全套工件（不是手改文件，是把字段加进流水线脚本后重跑）：

- `out/timeline_validation.json`：`status="pass"`（不是 `ok`）+ `project_contract.ok`（项目式时间线自检）
  + `timeline_sha256` = **文件字节** sha256；
- `out/preview.render_report.json`：`timeline_sha256` + `output_sha256`（都按文件字节算）；
- `out/preview.render_plan.json` / `out/preview.edit_decisions.json`：`timeline_sha256`；
- `out/preview_qc_report.json`：`status="pass"` + `timeline_sha256` + `video_sha256`。

核对：上述 10 项全部对上（timeline `7084f3c8…`、preview `7471a030…`），再跑钩子 ⇒ **放行，合同闭合**。

> 口径提醒：钩子算的是**文件 sha256**，我先前用的 `timeline_sha8` 是"规范化 JSON 的短哈希"（给人看的），
> 两者不是一回事 —— 这类"同一概念两套口径"正是本仓反复踩的坑，这次一并写在这里免得下次再踩。
