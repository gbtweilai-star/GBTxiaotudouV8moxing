# OpenPose + LoRA 组合技 · 配方与上云（第 59 轮 · 主人令 2026-09-23）

> 主人原话：「抓取 Stable Diffusion 超强插件组合技 OpenPose+Lora，把这两个的专业化能力
> 学会并且跑通闭环，这样我们就可以做自己的逼真数字人」
> 追加两句：「把云插件部署这三个组合连接大脑执行层不是也能操作」
> 「5.5G要分两个云来部署运行」·「必须要跑通之后才能部署进去」
> 本文件是**配方 + 实测读数 + 上云边界**的唯一载体。凡是没跑过的，一律标「未验」。

---

## 一、这套手艺到底是什么（三件套，缺一不可）

| 件 | 它管什么 | 为什么非有不可 |
|---|---|---|
| **逼真底模** | 决定"像不像真人" | 原版 `v1-5-pruned-emaonly` 出的是**插画脸**；加了 OpenPose+LoRA 也还是插画脸 |
| **ControlNet OpenPose** | 管**姿势**（骨架锁死） | 只靠提示词写"站着、手放腰上"，十张十个样；骨架是**硬约束** |
| **LoRA** | 管**身份/风格**（轻量外挂） | 20-200 MB 就能把"某张脸/某种风格"挂上去，不用重训底模 |

**专业分工一句话**：底模给"真实感"、ControlNet 给"姿势"、LoRA 给"是谁"。三者**缺一不可**，
而且**必须在同一个去噪过程里同时生效**（见第五节）。

---

## 二、真身账（已下载并 sha256 逐字节验真）

| 用途 | 仓库 · 文件 | 体积 | 落点 |
|---|---|---|---|
| 逼真底模 | `SG161222/Realistic_Vision_V5.1_noVAE` · `Realistic_Vision_V5.1_fp16-no-ema.safetensors` | 2,132,625,894 B | `models\checkpoints` |
| OpenPose | `webui/ControlNet-modules-safetensors` · `control_openpose-fp16.safetensors` | 722,596,338 B | `models\controlnet` |
| LoRA | `latent-consistency/lcm-lora-sdv1-5` · `pytorch_lora_weights.safetensors` → 存为 `lcm-lora-sdv1-5.safetensors` | 134,621,556 B | `models\loras` |

- 取件件：`tools/codex-scripts/comfy-fetch-models.ps1`（**带 sha256 验真 + 断点续传**，
  不可用"文件名对了"当验过）
- ⚠️ `lllyasviel/ControlNet` 原版的 `control_sd15_openpose.pth` 是 **5.32 GiB**（fp32），
  ComfyUI 该用的是 fp16 那份 **689 MiB** —— 别下错。

## 三、骨架格式（ControlNet 认的**不是照片**）

- **COCO-18 点序**：0鼻 1颈 2右肩 3右肘 4右腕 5左肩 6左肘 7左腕
  8右髋 9右膝 10右踝 11左髋 12左膝 13左踝 14右眼 15左眼 16右耳 17左耳
- **17 根骨**：(1,2)(1,5)(2,3)(3,4)(5,6)(6,7)(1,8)(8,9)(9,10)(1,11)(11,12)(12,13)
  (1,0)(0,14)(14,16)(0,15)(15,17)
- **官配 18 色**（按**子**关节取色）· 黑底 · 线宽与点半径 512 时 ≈4px
- 生成件：`tools/codex-scripts/openpose-skeleton.py`（预设 stand/tpose/walk/sit，
  也可 `--keypoints-json` 自定义；**零新依赖**，只用 cv2+numpy）

## 四、本机实测读数（真数字；不许念成绿的）

| 项 | 读数 | 出处 |
|---|---|---|
| 纯 txt2img 512×512 · 20 步 | **586 s/张**（≈29 s/步） | 第 25 轮 |
| **加 ControlNet 后** | **≈140 s/步**（每步多跑一遍 UNet） | 第 59 轮服务端 tqdm |
| **8 步 LCM 全三件套（真跑完整一单）** | **1366.3 s ≈ 22.8 分钟/张** | 客户端 `elapsed_s`（含约 3 分钟模型加载） |
| 模型常驻内存 | 底模 3278 MB + ControlNet 1378 MB + CLIP 236×2 + VAE 319 ≈ **5.5 GB** | 服务端 loaded 行 |
| 机器 | 总 7.4 GB · 跑图时可用 **0.29 GB** | `Win32_OperatingSystem` |
| 采样器 | 服务报 45 个，**含 `lcm`**；调度器 9 个 | `/object_info/KSampler` |

⇒ **结论**：本机**能跑通**（5.5 GB 真装进去了、真在采样），但**慢到不能叫"无限"**：
8 步 19 分钟 / 20 步约 47 分钟。**上云的动机是速度与吞吐，不是"装不下"。**

### 四·b 闭环已验（第 59 轮 · 真跑一单，不是推演）

| 项 | 读数 |
|---|---|
| prompt_id | `dd26c038-a873-4f78-8466-8b0163007d42` |
| 结果 | `status_str: success` · `completed: true` |
| 耗时 | **1366.3 s**（8 步 · 512×512 · LCM · cfg 2.0 · 含模型加载） |
| 出图 | `render/comfy-pose/1790183271-lora-RAW_photo_full_body.png` · **281,703 B** · `sha256 bcec416cc411fb96…` |
| 姿势自证件 | `render/comfy-pose/1790183271-pose-overlay.png`（骨架叠回成图）· 306,942 B |
| 服务端回填的图结构 | `CheckpointLoaderSimple + LoraLoader + ControlNetLoader + LoadImage + ControlNetApplyAdvanced + KSampler + VAEDecode + SaveImage` ⇒ **三条腿确实都在图里** |

**眼看读数（姿势）**：骨架叠上去后，**肩/肘/腕/髋/膝/踝/脊柱全部落在身体对应位置**，
右手"叉腰"那个腕点与实际手位一致，左臂下垂也对上 ⇒ **肢干级咬合成立**。
**诚实偏差**：头部那组点（鼻/双眼/双耳）**偏高了**，落在发际线/头顶而不是眼睛。

🔴 **一个坏判据当场被抓住**：本来自证的"前景外接框 IoU"在逼真底模上**失效** ——
真实背景有纹理/渐变，四角取背景色的切法切不开（实测前景占比 **0.846**），
外接框退化成整幅画面 ⇒ 算出来的 `0.26` **是个废数，却长得像个合理读数**。
⇒ 已在 `.scratch/_pose_check.py` 里加硬闸：**前景占比 > 0.55 就拒发 IoU**，只报"判据失效"。
**这正是本仓那条纪律的活样本：坏判据比坏对象更危险。**

## 五、上云：能拆的是「段」，不是「模型」（物理限制，必须先说清）

🔴 **一个去噪过程不能跨两个云**。底模、ControlNet、LoRA 在**每一步**里互相作用：
每一步都要"底模出噪声预测 → ControlNet 按骨架纠偏 → LoRA 调权重"。把 ControlNet 放云 A、
底模放云 B，那就不是"分工"，是**每一步都要跨网同步 3 GB 张量** ⇒ 根本算不动。
⇒ **「5.5 GB 分两个云」按模型拆是行不通的。**

✅ **能拆的是流水线的段**：

| 段 | 干什么 | 算力需求 | 放哪 |
|---|---|---|---|
| ① 姿势 | 照片/预设 → OpenPose 骨架 PNG | 极轻（秒级 CPU） | **本机**（已具备：仓 python 有 cv2+onnxruntime） |
| ② 扩散 | 底模 + ControlNet + LoRA → 512 图 | **重（必须一张卡）** | **一个** GPU 云（或本机慢跑） |
| ③ 后处理 | 放大 / 修脸 / 逐帧成片 | 中 | 可**另一个**云（与本仓 `make-video.py` 那条链对接） |

### 哪些云**真能**跑第②段（判据：能不能跑**同一张 ComfyUI 图**）

- ✅ **租 GPU 的 ComfyUI**（RunPod / Vast / 官方 Comfy Cloud 等）：跑的就是本地这张图，
  一行 URL 就能切过去 —— **这是唯一不改图的云路**。
- ❌ **ComfyUI 自带的 44 个官方云插件**：实测全目录扫过，`comfy_cloud.py` 有 `lora`/`style_lora`
  参数，**但 44 个文件里 `controlnet` 一处都没有** ⇒ **接不住 OpenPose 那半边**。
  别把这三件套部署到这些插件上，会缺一条腿。
- ⚠️ 其余家（fal / HF / Cloudflare 等）：多数只做文生图；要 control+lora 得**逐个查它的模型目录**，
  **不许凭印象说"支持"**。

### 五·b Cloudflare Workers AI 逐条查证结果（**双处官方文档**，2026-09-23 现取）

| 能力 | 现读结论 | 出处 |
|---|---|---|
| **图像 LoRA** | ❌ **没有**。LoRA 是**大语言模型**的：示例全为 `@cf/mistralai/mistral-7b-instruct-v0.2-lora` / `llama-2-7b-chat-hf-lora` / gemma；`adapter_config.json` 必须带 `model_type: mistral\|gemma\|llama` + `task_type: CAUSAL_LM` | Workers AI · Using LoRA adapters |
| **公开 LoRA 清单** | ❌ 三条**全是 LLM**：`cf-public-magicoder` / `cf-public-jigsaw-classification` / `cf-public-cnn-summarization`，兼容模型 `@cf/mistral/mistral-7b-instruct-v0.1` | Workers AI · Public LoRA adapters |
| ControlNet | ❌ 没有 | 同前（ComfyUI 官方云插件 44 个文件里亦无） |
| 文生图 | ✅ 有（`flux-1-schnell` 等），但**无 ControlNet、无图像 LoRA** | Workers AI · Models |

🔴 **一次自己的错，记在这里**：我曾根据"Workers AI 支持 LoRA"就**暗示它能顶图像那条腿** ——
**错**。LoRA 这个词在两家指的是**两件不同的东西**：Workers AI 的 LoRA = LLM 适配器；
ControlNet+LoRA 组合技的 LoRA = 扩散模型的 UNet 适配器（`lora_name` + `strength_model`）。
**同名 ≠ 同物**，这正是本仓踩过多次的那个坑。
⇒ **Cloudflare 在本流水线（第②段扩散）里能干的活是 0。** 它的位置在别处：
托管（Workers/KV/R2/Pages）与 **LLM/TTS/ASR**。GPU 那一段，Cloudflare 给不了。

### 上云要改的**唯一一处**代码

`tools/codex-scripts/genrouter.py:484` 现读是：
```python
base = (b.get("base") or "http://127.0.0.1:8188").rstrip("/")
```
⇒ **地址本来就是可配的**（注册一个后端换 `base` 即可，不用改代码）。
缺的是 `gen_comfy` 只会拼**纯文生图**那张图，不认 `pose`/`lora`/`controlnet` 参数。
⇒ 要做的就是把 `comfy-pose-lora.py` 里的拼图逻辑接进 `gen_comfy`（一件小事），
之后"大脑执行层 → 云 ComfyUI"这条路就通了。

## 六、连「大脑执行层」的缝在哪

1. 大脑执行层要出图，走的是**唯一门** `gbt_allinone.api.run_task`（经 `genrouter`）。
2. `genrouter` 的 `comfy_local` 腿**换 `base` 就能指向云**；云 ComfyUI 与本地 ComfyUI
   **对客户端完全同构**（同一套 `POST /prompt` → `GET /history` → `GET /view`）。
3. 所以"连上大脑执行层"的实质 = **给 `gen_comfy` 加上 pose/lora 的拼图能力**，
   再在 `POOL` 里注册一条云后端。**不需要动授权门，也不需要新增能力位。**

## 七、未验 / 存疑（**一条都不许念成绿的**）

- ✅ **姿势检测器（照片 → 骨架）已做**（第 70 轮）：`tools/codex-scripts/openpose-extract.py`
  （隔离 venv `.scratch/pose-venv` + `controlnet-aux 0.0.10`；权重 `body_pose_model.pth` **209,267,595 B** 落在 `.scratch/hf`）。
  验收器：`python .scratch\_verify_pose_chain.py`（六条判据：真跑通 · 关节级中位 **6.2 px** ·
  **头部四个**最差 3.2 px · 正名 L/R 不动几何 **IoU 0.9997** · 配色修复有效 · 18 色块齐全）。
  真跑：18/18 关键点解出 · 缓存后 13.8 s。**闭环回检**（把检测器跑在成图上）：与输入骨架
  **Chamfer 中位 0.00 px · 均值 1.24 px** ⇒ 姿势被完整找回。
  ⚠️ 只跑过一张图；仅 body（手/脸权重未下）；`include_hand/face` 默认关。
- 🔴 **同一轮修了 3 个真缺陷**（都在骨架这条链上）：① 渲染器把 **RGB 当 BGR** 喂 cv2 ⇒ 配色红蓝反了
  （改前/改后偏差 **152.2 px → 25.6 px**）；② **L/R 标反**（官方 R 在观众左，我放在右）⇒ 已正名，
  **几何机检未动**（掩膜 IoU 0.9997）；③ 比对器的掩膜用**灰度**判 ⇒ 蓝色抗锯齿边被吃掉、造成假 IoU 0.92 ⇒ 改成任一分量非黑。
  详见 `memory/在办清单.md` §二十三。
- 🔴 **关节级对齐未量**：现只有弱判据（外接框 IoU + 叠加图眼看）。
  要关节级必须上真检测器对成图反检。
- 🔴 **LCM-LoRA 是速度/一致性 LoRA，不是身份 LoRA**。"你自己那张脸"必须有**身份 LoRA**，
  而训练在本机**不可行**（CPU / 7.4 GB / 无 CUDA）⇒ 只有云上训或换机器。
- ⚠️ `Realistic_Vision_V5.1` 是 **CreativeML OpenRAIL-M** 许可，商用前要自己过一遍条款。

> 开发者：自由的风 · GBT小土豆V8 · 本署名不可删除、不可篡改归属
