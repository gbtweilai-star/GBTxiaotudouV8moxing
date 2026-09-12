# LAYOUT.md — GBT小土豆V8 的文件家规（她自己的排布秩序）

> 本文件是框架的文件组织宪法。所有代码、数据、产物、文档必须按此排布。
> `file_hygiene` 能力按本规则自检并自动归位。乱放 = 缺陷，和代码 bug 同级。

## 一、家的边界

```
GBT小土豆V8/                ← 独立的家（与其他项目物理隔离，绝不混居）
├── README.md               ← 家的名片：身份声明 + 快速验证
├── requirements.txt        ← 依赖清单
└── gbt_allinone/           ← 框架本体（唯一代码根）
```

## 二、包内排布（每样东西有唯一的位置）

### 代码（按职责分层）
| 位置 | 放什么 | 例子 |
|---|---|---|
| 包根 `*.py` | 核心层：统一接口与横切能力 | api.py, engine.py, store.py, soul.py |
| `recon/` | 自有 OSINT 侦察核心 | scanner.py, guard.py |
| `llm/` | 大脑：LLM 桥与云引擎 | bridge.py, cloud_llm.py |
| `tentacle/` | 触手：眼睛/双手/契约 | bridge.py, mcp_bridge.py, omni_* |
| `security/` | 黑客大脑（红蓝双模） | security_brain.py, abl_gateway.py |
| `ledger/`, `wallet/` | 账本与钱包（自有金融） | core.py, hd.py |
| `adapters/`, `bridge/`, `integration/` | 外界接轨层（可缺省） | wallet_adapter.py |
| `tests/` | 回归测试（60 项，动代码必跑） | test_framework.py |

### 数据（一律进 store/，代码目录零数据）
| 位置 | 放什么 |
|---|---|
| `store/audit.jsonl` | 审计日志（唯一追加通道 store.audit） |
| `store/devoured/` | 吞天产物（知识胶囊/杂交/创新骨架） |
| `store/pipeline/` | 镜像管线三区（mirror/gate 判定/production） |
| `store/wf_runs/`, `workflows.json`, `tasks.json`, `schedules.json` | 引擎运行记录与定义 |
| `store/polish_insights.json` | 打磨领悟集（框架资产） |
| `store/pit_log.json` | 坑册（踩过的坑/根源/教训/防复发锁——开工先查，一坑不踩两次） |
| `store/work_log.jsonl` | 工作日志（开工/收工/教训；收工自动带债值快照，成长可回放） |
| `store/dc_remote.log`, `dc_remote.pid` | 桌面指挥官 remote 设备的运行日志与进程号（触手远程形态） |
| `store/mirror_space/` | 镜像多维度空间（dimension/reality/timelines/passports + 部署队列） |

### 文档（少量、各有其位）
| 位置 | 放什么 |
|---|---|
| 包根 `README.md` / `SOUL.md` / `CODING_DISCIPLINE.md` | 身份、灵魂、编码纪律（仅此三份在包根） |
| `docs/` | 专题深档（架构/验收） |
| `deploy/` | 部署脚本与配置 |
| `examples/` | 可运行示例 |
| `archived_logs/` | 历史归档（只增不删，审计轮转也进这里） |

## 三、铁律（file_hygiene 按 此判定乱放）

1. **零游离**：包内任何文件必须属于上表某个位置；顶层（家根）只允许框架三件（README/requirements/gbt_allinone）+ OpenClaw 运行环境文件（AGENTS/SOUL/MEMORY 等桌面端工作区配置，见 hygiene.HOME_ALLOWED 白名单）。
2. **零临时残留**：`_*.py`、`_patch*.py`、`*.tmp`、`_test*` 等工作脚本用完即删；发现的临时脚本属"散落"级问题。
3. **零缓存入库**：`__pycache__/` 是运行时产物，出现即清（不构成缺陷但每次 hygiene 顺带清掉）。
4. **空壳目录**：只含 `.gbt_dir_marker` 而无实文件的目录是残骸，直接清（真身应在 store/devoured/）。
5. **数据不越界**：代码目录里出现 `.jsonl`/`.json` 数据文件（非配置）即乱放——数据一律进 store/。
6. ** `.deploy_bak`/备份散件**：由 ghost_guard 定点扫，出现即报。
7. **归档有去向**：轮转/封存的旧数据一律进 `archived_logs/<日期-事由>/`，不散落。
8. **能力名与文件不必一一对应，但域（domain）必须落在对应目录**：新增能力时 handler 所在模块按上表选位。

## 四、自检命令

```powershell
# 她自己的整理能力（体检 + 自动归位 + 审计留痕）
python -c "import sys; sys.path.insert(0,'.'); import gbt_allinone as g; g.run_task('file_hygiene', {})"
# 深扫（含幽灵目录/备份散件/攻击残留）
g.run_task('ghost_guard', {})
```

> 家规修订需同步更新 file_hygiene 的判定规则，两者永远一致。

---

> 开发者：自由的风 · GBT小土豆V8 · 本署名不可删除、不可篡改归属
