# 出图源升级决策 · 本地 SD 不可行与三条替代路线

> 开发者：自由的风 · GBT小土豆V8 · 本署名不可删除、不可篡改归属
>
> 背景（Owner 2026-09-27 给料）：①《Stable Diffusion 秋叶整合包 v4.11.1 安装指南》（秋葉aaaki · 免费开源）
> ② 一份本机硬件体检（结论：无独显 / C 盘 2.6G / 8G 内存）。本文把两条料接到**我们的实物**上，给决策。

---

## 一、结论先行

**本机装 SD 不可行（三不足）**；当前**唯一能用的出图源仍是 pollinations**（免费，但硬顶 1024×576 + 水印）；
想要更高图质，三条替代路线里**必须先解一道锁**（积分 / 登录 / 云 GPU），解锁前**没有任何本地办法能突破生成源的天花板**——
我们已做的超采样 + 电影调色（`tools/filmgrade.py`）是**在源图给定前提下的最优解**，不是源图问题的解。

---

## 二、六条出图路线·现读实测（2026-09-27）

| 路线 | 现状读数（实测/现读） | 能不能用 |
|---|---|---|
| **pollinations**（现用） | 免费、无需 key；**忽略 width/height 参数，固定返回 1024×576**；带 `pollinations.ai` 水印 | ✅ **在用**（质量天花板就在这） |
| **genoffice / Genspark** | `image` 子命令支持 **16:9 / 1k–4k / --ref 参考图**；实测生成返回：`app_unavailable · The Genspark CLI requires a paid plan or a credit balance of at least 500` | ⛔ **额度挡住**（需付费计划或 ≥500 积分） |
| **arkcli（即梦/Seedream）** | 技能簇在册（`gbt-arkcli` 25 条）；**STS 令牌过期**，需 `arkcli auth login` | ⛔ 待主人登录 |
| **a1art** | `key_envs_set: 0` · 接口文档不在盘 | ⛔ 无密钥 |
| **fal.ai** | `gbt-fal` 12 条**全是目录桩**（只有 SKILL.md、无脚本、上游未装） | ⛔ 未接 |
| **本地 SD（秋叶整合包）** | 硬件体检：**无独立 GPU**（Radeon 集显 Vega 7，CUDA 不可用）· **C 盘可用 2.6G**（整合包解压 20–30G + 模型 100–200G）· 内存 ~8G（临界，本仓另有 7.39GB 硬顶记录） | ⛔ **三不足，不可行** |
| **云 GPU（Colab）** | 剧组宪法第三律已立（内存压强派单制：渲染→Colab）；Colab 侧环境**未搭** | ⚠️ **可行但要搭一次环境** |

---

## 三、三条替代路线（按代价从低到高）

### 路线 A：给 pollinations 加"二次加工"（**零成本，已做**）

已落地并实测：**3x 超采样（lanczos + `cas`）→ 1080p 渲染 → 外观库调色**（7 味）。
**收益**：软源图 → 可用的 1080p；**代价**：0；**天花板**：源图细节就那么多，放不出不存在的信息。

### 路线 B：解一把锁（**一次动作，立刻换源**）

| 选哪把锁 | 解锁动作（谁做） | 解锁后能拿到 |
|---|---|---|
| **Genspark 积分/付费**（最省事） | 主人充值或升级（≥500 积分）；命令现成：`genoffice image "<prompt>" --aspect 16:9 --size 2k --out <file>` | **2k/4k 无水印出图 + `--ref` 参考图**（顺带打通洗图的参考图环） |
| **arkcli 登录** | 主人在终端跑 `arkcli auth login` | 即梦/Seedream 云出图（有独立计费口径，按 `gbt-arkcli` 规程报价确认） |
| **fal 接上** | 主人给 key（上游未装，得先 vendored） | fal 系模型（含专用放大/抠图/换脸） |

### 路线 C：云 GPU（**能力上限最高，代价最高**）

Colab 搭一次（SD1.5/SDXL/Flux + ControlNet canny/depth/openpose + LoRA）：
**能干什么**：真 img2img 洗图（降噪 0.15→0.85 四档）、**ControlNet 姿态/边缘/深度精准控制**、
LoRA 锁角色一致性——这三样正是我们短片线当前最缺的（角色一致 / 姿势可控 / 洗图）。
**代价**：搭环境 + 每次出图要走派单回传（本机只做调度验收，符合第三律）。

---

## 四、给主人的建议（一句话版）

**先解路线 B 里最便宜的那把锁**（Genspark 充值 或 `arkcli auth login`，二选一即可立刻换源）；
**要"角色一致 + 姿势可控 + 洗图"这四样专业能力，就得走路线 C（Colab）**——本地 SD 这条路在我们这台机器上**物理上走不通**，
不是配置问题（盘/显存/内存三不足，`C:` 仅剩 2.6G）。

---

## 五、秋叶整合包资料（存档 · 供将来有 GPU 的机器用）

> 来源：秋葉aaaki（B站 space.bilibili.com/12566101）· v4.11.1（CUDA 12.8）· 免费开源
> 网盘：`pan.quark.cn/s/85a21818e79e` · 解压密码（旧版）：`bilibili@秋葉aaaki`

- **主包**：`sd-webui-aki-v4.11.1-cu128.zip`（NVIDIA）· AMD 用 `v4.9.1.zip` + HIP SDK
- **必装**：`windowsdesktop-runtime-6.0.36-win-x64.exe`（.NET 6 启动器依赖）
- **解压路径**：非系统盘、**不能有中文和空格**；解压后**先放模型再启动**
- **模型落点**：`models\Stable-diffusion`（大模型）· `models\ControlNet` · `models\LoRA` · `models\VAE`
- **启动**：`A启动器.exe` → 一键启动 → `http://127.0.0.1:7860`
- **推荐模型**：chilloutmix_NiPruned（写实）/ anything-v5（二次元）/ SDXL Base 1.0 / Realistic Vision v6.0
- **推荐 ControlNet**：canny（边缘）/ depth（深度）/ openpose（姿态）/ lineart（线稿）
- **常见坑**：CUDA OOM ⇒ 降分辨率 + `--medvram/--lowvram` + batch=1；无 GPU ⇒ CPU 模式 5–15 分钟/张（不可用）
- **结论**：**这份资料留给"将来有独显 + 大盘的机器"**；本机不用它。
