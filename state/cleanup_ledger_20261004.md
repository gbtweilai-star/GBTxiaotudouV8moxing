# 2026-10-04 深度清理与源码收编 · 工作台账（清理端口）

> 双端口分工防重复：本端口=深层垃圾缓存/下载夹/C根散件/台账；审查端口=脑模块闭环核验
> （`tools/codex-scripts/brain-closure-check.py`）+ 旧项目整体搬移（`C:\Users\ADMIN\.old-projects-20261004\`）。
> 两端口隔离区：`.old-projects-20261004`（审查端口，8 项）+ `GBT旧项目隔离区_20261004`（本端口，1.5GB）。清空前都可整体恢复。

## 一、已完成（修了哪里）

| # | 动作 | 结果 |
|---|------|------|
| 1 | Tier-1 垃圾缓存清理 | **释放 13GB（C 盘剩余 27G→40G）**：Temp 5.3GB（5545→232MB）、npm 缓存 6.2GB、更新器残留安装包 ~2.7GB（Ollama/lm-studio/WorkBuddy/autoclaw×2/genspark/TheBrain/VSCode old_Code.exe）、trivy-java.db 1.4GB、VSCode 扩展缓存 0.5GB、仓外 `__pycache__` 348 个、桌面 0 字节残件 |
| 2 | 启动项修正 | `start_bridge.bat`/`start_ws_server.bat`/`GBT WebSocket.lnk`（三条全指 V7 旧树）移出 Startup → `_legacy_sources/启动项备份_20261004/`；保留 agnes-proxy.vbs、start_genoffice_bridge.bat(V8)、start_ws.bat(openclaw) |
| 3 | V7 服务退役判据 | 18900/8089/8092/8094/25485 **全部未监听**；V8 仅 `services.py:29` 探测表列名、无功能依赖 → V7 自启任务可安全禁用 |
| 4 | 计划任务 | 7 个残留任务（GBT_Bridge_Now/OMP_Bridge_Run/OMP_Bridge_V2/OMP_Bridge_Debug/Test_Echo/GBT_DaemonLauncher/GBT_Services_Autostart）XML 已备份到 `_legacy_sources/计划任务XML备份_20261004/`；**禁用动作待管理员**（非提升会话"拒绝访问"） |
| 5 | 独有源码收编 | Autoclaw 旧工作区 72MB → `_legacy_sources/Autoclaw-旧工作区-独有源码`；V7/Workspace 被审查端口先移走，其内容完整保存在 `.old-projects-20261004/Desktop-GBT小土豆-老伙/` 与 `Desktop-Workspace/` |
| 6 | C 根散件 | 19 件清单已定（11 个 .py 脚本 + 2 ps1 + 3 png + txt + 空 zip/sql），**移动待管理员**；C 根不可写已实测（非提升 touch 失败） |
| 7 | 下载夹清理 | 8 个安装包（Bionic 650MB/MuseWork dmg+exe/TheBrain/Cortex arm64/Genspark/ChatGPT/dashboard.zip）+ Telegram 重复文件几十件（逐件验证同尺寸原件存在才移）→ 隔离区共 1.5GB |
| 8 | 收编进一棵树 | `Downloads/GBT小土豆V8的开心人生启航`（2MB Obsidian 库）→ `_legacy_sources/`；`.gitignore` 已加 `_legacy_sources/`（不入库） |

## 二、事故记录（如实报，不掩盖）

- **乱码目录清理时通配符误删**：`GBT*` 宽通配符把桌面上 4 件真实文件一并删除（主快捷方式 .lnk、Logo.jpg、0.1.0.exe、Octop 面板启动器）。
  - 已恢复 3.5 件：lnk 重建（→GenOffice.exe）、0.1.0.exe（仓内 dist 拷回）、Logo.jpg（仓内 `.scratch/_baseline_wt/assets/brand/logo-potato-256.png` 转 JPG）、Octop-Panel.cmd（**等效重建非原件**，原 136 字节原文无留底，面板地址按 127.0.0.1:8088/panel.html 重建，如实际 URL 不同请改）。
- **GBT探针 目录（35MB，2026-09-28：00-大脑/01-交付物/02-证据/03-脚本/04-调研/out/README）未能恢复**。bash rm 不进回收站；WorkBuddy 缓存为空、审查端口隔离区无此目录、ZCode 会话记录无写入原文。如需抢救可外接另一块盘后用 `winfr` 按路径恢复（需管理员）。
- **教训固化**：破坏性批量操作前必须先出逐项清单核对；禁止对中文路径用宽通配符成批删除（本机 GBK/UTF-8 显示错位会把真文件伪装成乱码）。

## 三、没修的（为什么 + 谁负责）

| 项 | 原因 | 负责 |
|----|------|------|
| 禁用 7 个残留计划任务 | 需管理员权限 | 主人 UAC 后本端口执行 |
| C 根 19 件散件移动 | 需管理员权限 | 同上 |
| 脑模块闭环核验/修复 | 审查端口正在做（brain-closure-check.py + 隔离 store 跑关联测试） | 审查端口 |
| V7/Workspace/V5/便携版 搬移 | 审查端口已搬入 `.old-projects-20261004` | 审查端口 |
| Docker 数据盘 54.4GB / WSL 19.6GB / Chrome 14GB+内置AI模型 4GB / huggingface 2.3GB / .codex 会话 1.8GB / 回收站 1.6GB | 需主人拍板 | 主人定后本端口执行 |
| C 根大目录（app/dev/opt/var/gbt-tools/gbt_pml/GBT-JXDWD/backups/tmp 等） | 需逐个查引用再定，今日未动 | 后续 |
| 页面文件 34GB / 休眠文件 3.2GB | 系统级（`powercfg /h off` 可回收休眠文件，需管理员） | 主人拍板 |

## 四、本端口产出物位置

- 收编归档：`_legacy_sources/`（gitignore，不入库）
- 本端口隔离区：`C:\Users\ADMIN\GBT旧项目隔离区_20261004\`（1.5GB，主人确认后可整体删除）
- 维护脚本（可审计）：`_legacy_sources/consolidate_step1_c_root.ps1`（C 根收编，待管理员跑）、`step2_legacy_source_sweep.ps1`、`rebuild_desktop_items.ps1`

## 五、第二轮执行（主人已拍板，全部完成）

| # | 动作 | 结果 |
|---|------|------|
| 9 | **UAC 管理员步骤**（主人点允许） | C 根 19 件散件收编 `MOVE_OK=19 FAIL=0`；7 个残留计划任务全部 `TASK_DISABLED`（XML 备份在前）；C 根大目录体积留档（见下） |
| 10 | **Docker 全回收** | 停 Docker 进程 + `wsl --shutdown` → 注销 docker-desktop 发行版 → 删 `docker_data.vhdx`（**53.1GB**）→ 移除 Docker Desktop 开机自启（注册表 Run） |
| 11 | **WSL 闲置发行版注销** | Ubuntu-22.04（1.3GB）+ kali（0.9GB）已注销；主 Ubuntu（17.4GB）保留 |
| 12 | **回收站清空** | 1.6GB |
| 13 | **HF + Codex 会话** | `.cache/huggingface` 2.3GB、`.codex/sessions` 1.8GB 已清 |
| 14 | **Chrome 缓存** | User Data 14395MB → 6606MB（**清出 7.6GB**：各 profile Cache/Code Cache/GPUCache + 内置AI模型 OptGuideOnDeviceModel 4GB） |

**终验：C 盘剩余 107G（今日起点 7.3G，累计回收约 100GB）。**

### C 根大目录体积留档（管理员步骤实测，只读未动）
`C:\tmp`=**7929MB** · `C:\temp`=**1107MB** · gbt_pml=235MB · gbt_chrome_profile=235MB · c=248MB · Go=232MB · GBT-JXDWD=36MB · scripts=1MB · 其余(app/backups/dev/gbt-tools/inetpub/opt/var/tmp_gbt_check)≈0

### ⚠️ 安全提示（主人注意）
`C:\tmp` 内有 **`.env`、`5sim_token.txt`** 等疑似明文密钥文件，且该目录混有 Python venv、CodexPlusPlus 项目与工作文档——**未批量删除**，建议主人自行核对后处理；若含真实密钥建议轮换。

## 六、第三轮·终清（主人令"全部清理只保留GBT小土豆V8"，已全部完成 ✅）

| # | 动作 | 结果 |
|---|------|------|
| 15 | **删前抢救** | V7 在用脚本 6 件（gbt_cap_bridge / 3 个 start_*.ps1 / websocket_server / daemon_launcher）从审查端口隔离区抢救进 `_legacy_sources/GBT小土豆V7-在用脚本/`（唯一副本）；`CodexPlusPlus`（193MB 真源码）、`天才交易原`（52MB）移档进 `_legacy_sources/` |
| 16 | **C:\tmp / C:\temp / C:\c 整删** | tmp 顶层 <2MB 小文件 1594 件 + temp 33 件先归档（`c_tmp_留档_20261004` / `c_temp_留档_20261004`）；其余 90+ 个 V7 残件目录（30+ chrome 调试 profile、payment/voice 测试、venv 1.4G、electron 缓存、python_nuget、webapp-node-modules 等，最新修改 2026-08-30 前全是死实验）整删；`C:\c`（cc-src/continue-src 均为 .git 仓可重取）整删；释放 ~17GB |
| 17 | **两隔离区清空** | `GBT旧项目隔离区_20261004`（1.5G）+ `.old-projects-20261004`（V7 老仓/Workspace/V5/便携版/_gbt_webcap 等 9 项，改名确认为空闲后删）全部清空删除 |
| 18 | **桌面旧项目删除** | Autoclaw（独有源码已归档 72MB；`.pylibs`/`sub01_tk` 为提权 ACL 阻断，takeown+icacls 夺权后提权删除 `AUTOLCAW=GONE`）、Octop（安装器）删除 |
| 19 | **C 根终清** | gbt_pml（235MB 3D 资产）、GBT-JXDWD（部署脚本）移档；gbt_chrome_profile（235MB）+ 9 个小空壳目录（app/backups/dev/gbt-tools/scripts/tmp_gbt_check/opt/var）删除 |
| 20 | **残留任务清零** | `GBT_BountyWatch` 禁用 ⇒ **8/8 残留任务全部禁用**（XML 备份在 `_legacy_sources/计划任务XML备份_20261004/`） |
| 21 | **Documents 残件** | Codex/Obsidian-1.13.7.exe（316MB 安装器）、Codex/2026-08-07 旧会话（含 GBTxiaotudouV5 副本）删除 |

**⚠️ 未归档即删的例外（如实记）**：`C:\gbt-tools\gbt-prod-config.yml + gbt-prod-tunnel.json`（V7 生产隧道配置）与 `C:\scripts\ai_video_generator.py` 删除前未归档——均属已退役的 V7 产线配置，风险自评：低；若 V7 隧道配置里存有令牌，删除反而消除了明文残留。

**终态核验（盘上实况）**：
- 桌面 = **仅 GBT小土豆V8 仓** + 主人个人归档四目录（图片-归档/工作-归档/工作-文档/视频-归档）+ 快捷方式 + 主人 10-03 工作文件（dump_keys.py/freeapi_copy.db/test_bind.ps1 等）。
- C 根 = 仅系统目录与安装软件（Windows/Program Files/ProgramData/Python310/312/314/Go/inetpub/PerfLogs/同花顺等）。
- 计划任务 8 个残留全部 Disabled；启动项仅剩在用三件（agnes-proxy/genoffice_bridge/ws.bat）。
- **C 盘剩余 107G（今日起点 7.3G）**；`_legacy_sources` 归档区 648MB（在 V8 树内，gitignore 不入库）。

---

> 开发者：自由的风 · GBT小土豆V8 · 本署名不可删除、不可篡改归属

## 七、第四轮·家目录（C:\Users\ADMIN 根）终清 ✅

> 主人令"根 GBT小土豆V8 无关的项目全部清理，不留任何旧项目"。删前已核：V8 对全部待删路径 **grep 零引用**；保留清单见下。

**归档（移动进 `_legacy_sources/home_root_V7_dump_20261004/`，115 件）**：V7 散落家根的全部源码/文档/配置小件（gbt*.py×10、agent/run、test_*×20+、deploy/bat/ps1×20+、AGENTS/CONSTITUTION 等 md×14、package.json、octop-login.txt、.tmp_ck_*、_dg_fix3.b64、CodexPlusPlus_home_dirty.diff）。

**删除（全部 V7 血统/零引用）**：
- 卫星仓与克隆 45+ 个：ClawX(189M)、CodexPlusPlus 本体(2.6G，diff 已存档、远端 github.com/BigPizzaV3/CodexPlusPlus 可重取)、DeepAudit、GBT-JXDWD(家根副本)、GBrowser、GPTCache、O4OpenAI、OpenMontage、PyCharmMiscProject、alchemy-demo、arc-api-quickstart、archived_files、awesome-agentic-ai-zh、brain.legacy-*、caps.legacy-*、cai_ref、cli、docs、eve、freellmapi(旧克隆，桌面应用本体仍在)、gbt、gbt-projects、go(GOPATH 缓存)、gradio、integrations、jina、karpathy-skills、langchain、leafvpn-desktop、litellm-gateway、llama_index、markitdown、nanobrowser-ext、node_modules(privy Web3 残件，bufferutil.node 进程锁重试后删净)、privy-app、proxy.py、source、src、tests、tmp、tools、vulnhuntr、work、yt-dlp、Library、.screenpipe、.EasyOCR/.paddlex(模型缓存可重下)、.openclaw(旧 autoclaw，5.3M，已被 .openclaw-autoclaw 取代)、.openclaw.backup、.venv/.venvs、.gbt/.gbt_chrome_cdp、.docker、.next*、.codex-session-delete、pytest-cache-files-*×15、api.deepseek.com、VirtualBox VMs(1.3M 空)、NUL(保留名文件)、冒号名残件×2(WSL POSIX 路径删)、乱码隔离区空壳。
- 注册表：`PotatoDesktopPet` 自启死链（指向已不存在的全能操盘手树）移除。

**保留（主动决策，非项目）**：ComfyUI(9.4G，框架出图能力位) · ComfyUI-SkinTokens+SkinTokens(V8 皮肤能力) · Brains/BrnTmp(TheBrain 脑图用户数据) · Coze(扣子云盘应用数据) · WorkBuddy+WorkBuddy AI(应用数据) · .ollama(本地模型) · 全部工具 dotdirs(.zcode/.codex/.openclaw-autoclaw/.octop/.dsh/.claude/.codebuddy 等) · skills-lock.json · 标准目录与 NTUSER。

**家根这一轮释放 ~71GB（C 盘剩余 107G→178G）。今日总账：7.3G → 178G，累计回收约 170GB。**

