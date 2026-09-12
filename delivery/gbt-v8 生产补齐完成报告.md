# GBT-V8 生产补齐完成报告

> 审计执行：2026-09-13 · 依据 GitHub Copilot 生产能力审计指引
> 结论：**99 项注册能力全部真实路由，零 stub，89/89 测试通过，truth_scan 零假执行**

---

## 一、本轮补齐内容

### 1. 真实 Bug 修复（3 处崩溃 → 优雅降级）

| 位置 | 问题 | 修复 |
|------|------|------|
| `adapters/wallet_adapter.py` | `receive_init` 在 gbt_wallet 缺失时直接崩溃 | 加 try/except 降级保护，返回结构化 `unavailable` 信息 |
| `bridge/deposit_bridge.py` | `bind_invoice` 对降级字典取 `invoice_id` 抛 KeyError | 先判定降级字典，返回明确"收款发票不可用" |
| `bridge/deposit_bridge.py` | `credit_from_invoices` 对降级字典当 list 迭代抛 TypeError | 先判定类型，无发票可记时如实返回 count=0 |

### 2. 三大预留能力真实现（stub → 真后端）

**vision**（`vision_cap.py` 新增，5320 字节）
- `op=analyze`：本地 PIL 像素级分析（尺寸/主色/亮度/对比度/边缘密度/网格分布）+ dxcam 截屏——**已验证 1920×1080 真实出结果**
- `op=cloud`：OpenAI 兼容视觉端点（未配置时如实返回 needs_dependency）
- 依赖兜底：自动挂框架自带 .pylibs（与 tentacle/bridge 同机制）

**voice**（`voice_cap.py` 新增，4317 字节）
- `op=tts`：Windows SAPI 真实合成（桌面宠物同款栈）——**已验证 WAV 落盘**
- `op=asr`：OpenAI 兼容转写端点（未配置时如实返回 needs_dependency）

**browser**（`browser_cap.py` 新增，5659 字节）
- `op=open/search`：系统默认浏览器（标准库零依赖）——真实执行
- `op=fetch`：无头静态抓取——**已验证 example.com 抓取 142 字符**
- `op=automate`：Playwright 自动化（未装时如实返回 needs_dependency + 安装指引）

### 3. 账本闭环补齐

- `wallet_new` 新增 `save=true` 参数：显式要求才落盘助记词（安全设计保留）
- `pool_assign_address` 无钱包时给出闭环指引（`wallet_new {save:true}`）而非裸异常
- 误建的顶层 `ledger.py`（会遮蔽真实现 `ledger/` 包）已归档为 `store/ledger_standalone_draft.py.bak`

### 4. 环境修复（npx 缓存损坏）

- 根因：DC remote 进程（PID 14552）持有已清空的 npx 缓存目录 → 重装 EBUSY
- 处理：终止残留进程 → 清除损坏缓存 → 重装 desktop-commander
- 结果：`_remote_cmd()` 恢复 node 直跑 + `--require dc_brand_preload.js` 品牌注入完整链

### 5. 测试同步升级

- `test_stub_capabilities_honest` 从"期望 needs_dependency"升级为"验证真实后端行为 + 诚实参数校验"

---

## 二、验证结果

### 全能力探针（99 项注册良性能力）

| 分类 | 数量 | 说明 |
|------|------|------|
| 直接 ok | **76** | 真实执行成功（含 vision/voice/browser） |
| 参数校验 error | **23** | 能力真实存在、要求必填参数（正确行为） |
| stub | **0** | 全部消除 |
| 崩溃 | **0** | 降级保护全部生效 |

### 测试套件

- **89/89 通过**（45 秒）
- 覆盖：能力路由 / 工作流断点续跑 / 账本守恒 / 镜像晋升 / 署名守卫 / 品牌注入 / 触手视觉全帧

### 框架体检

- `selfscan`：路由 99/99 无断链、模块 47/47 导入正常、存储 895 个 JSON 零损坏
- `truth_scan`：**FAKE=0，verdict=clean**（零假执行——框架铁律达成）
- `cross_scan` / `signature_guard` / `file_hygiene`：全绿

---

## 三、生产就绪度对比

| 维度 | 审计前 | 审计后 |
|------|--------|--------|
| stub 能力 | 3 项（vision/voice/browser） | **0 项** |
| 崩溃路径 | 3 处（receive_* 系列） | **0 处**（全部优雅降级） |
| 能力真实路由 | 96/99 | **99/99** |
| 测试通过率 | 88/89 | **89/89** |
| 假执行 | 0 | **0**（保持） |
| 品牌注入链 | 断裂（缓存损坏） | **完整恢复** |

### 剩余外部依赖（如实报告，非框架缺口）

| 依赖 | 用途 | 状态 |
|------|------|------|
| GBT_VISION_* 环境变量 | 云端图像识别 | 未配置（本地 analyze 已可用） |
| GBT_ASR_* 环境变量 | 云端语音转写 | 未配置（本地 TTS 已可用） |
| playwright | 浏览器自动化 | 未安装（open/search/fetch 已可用） |
| gbt_wallet 项目 | 链上收款（Polygon） | 独立项目未迁移（receive_* 优雅降级） |

---

## 四、遵守声明

- ✅ 未删除、未限制任何已注册框架能力（只增不删）
- ✅ 未推送任何内容到远端仓库（全部本地修改）
- ✅ DISABLED_CAPS（11 项危险能力）保持原样禁用——这是框架自身安全设计
- ✅ 所有新增代码带开发者钢印署名

---

> 开发者：自由的风 · GBT 小土豆 V8 · 本署名不可删除、不可篡改归属
