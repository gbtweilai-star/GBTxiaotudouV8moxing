# GBT小土豆V8 · 独立私人框架

> 本目录是 GBT小土豆V8 的独立家，与任何其他项目物理隔离。
> 独立私人框架，与任何企业公司无关。

## 目录

- `gbt_allinone/` — 框架本体（统一接口 run_task + 77 项能力 + 审计 + 镜像管线）
- `requirements.txt` — 依赖清单（本地依赖在 `gbt_allinone/.pylibs`，已随迁）

## 快速验证

```powershell
cd C:\Users\ADMIN\Desktop\GBT小土豆V8
python gbt_allinone\tests\test_framework.py
```

## 边界声明

- 框架源码 100% 自包含：OSINT 侦察核心在 `gbt_allinone/recon/`（自有）
- 旧收款钱包（gbt_wallet）是独立项目，未随迁；`receive_*` 能力如实降级提示
- 审计/产物/领悟集都在 `gbt_allinone/store/`（框架自己的数据家）

## 历史故居

`C:\Users\ADMIN\Desktop\Autoclaw\archived_logs\` 保留了 2026-09-11 之前的全部归档。

---

> 开发者：自由的风 · GBT小土豆V8 · 本署名不可删除、不可篡改归属
