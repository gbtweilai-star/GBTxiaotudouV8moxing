---
name: code-security-review
description: 自有资产的代码安全审查契约：三阶段（污点追踪 → 沙箱验证 → 修复指引）、置信度评分公式、置信度阈值、沙箱隔离策略、抑制文件与 14 项已知局限。蒸馏自 backspace-shmackspace/deep-code-security，只保留判据。
triggers:
  - "安全审查"
  - "SAST"
  - "污点追踪"
  - "漏洞扫描"
  - "代码审计"
od:
  mode: utility
  category: security
  distilled_from: "https://github.com/backspace-shmackspace/deep-code-security"
  upstream_license: "见上游仓库（README 未声明许可 —— 使用前请主人确认）"
  scope: "仅自有资产"
---

# 代码安全审查契约（自有资产）

> 蒸馏自 `backspace-shmackspace/deep-code-security`。**范围限定自有资产** —— 与「未授权目标不碰」同级。
> ⚠️ **上游 README 未声明许可**，使用其代码前需主人确认；本技能只蒸馏判据，不含其代码。

## 0. 三阶段流水线

```
HUNTER    扫描后端（Semgrep / tree-sitter）→ 源/汇匹配 → 污点追踪
         产出：RawFinding[]（JSON，分页）
   ↓
AUDITOR   生成 PoC → **在沙箱里真的跑** → 置信度打分
         产出：VerifiedFinding[]（JSON）  ［利用成功只加 10% 分］
   ↓
ARCHITECT 收集上下文 → 生成修复指引 → 依赖分析
         产出：RemediationGuidance[]（JSON）
```

## 1. 置信度评分（0–100，加权）

| 因子 | 权重 | 说明 |
|---|---|---|
| 污点路径完整度 | **45%** | 全路径 = 100 · 部分 = 50 · 启发式 = 20 |
| 净化器缺失 | **25%** | 无净化 = 100 · 有完整净化 = 0 |
| CWE 严重度基线 | **20%** | Critical = 100 · High = 75 · Medium = 50 · Low = 25 |
| 利用验证 | **10%** | **只是加分** —— PoC 失败**不扣分** |

**阈值**：`>=75` 确认 · `>=45` 很可能 · `>=20` 未确认 · `<20` 误报。

> 「PoC 失败不扣分」是这套评分里最诚实的设计：模板化 PoC 多数会因为缺执行上下文而失败，
> **失败不等于漏洞不存在**。

## 2. 沙箱隔离策略（强制项，逐条）

```
--network=none                      无网络
--read-only                         根文件系统只读
--tmpfs /tmp:rw,noexec,nosuid,size=64m   可写临时区，禁止执行
--cap-drop=ALL                      无 Linux capabilities
--security-opt=no-new-privileges    不许提权
--security-opt seccomp=<profile>    自定义 seccomp
--pids-limit=64                     防 fork 炸弹
--memory=512m                       内存上限
--user=65534:65534                  以 nobody 运行
```

**MCP 服务本身跑在宿主机的原生 stdio 进程里，不在容器内** —— 规避 Docker socket 挂载攻击面。

**文件访问**一律走 `DCS_ALLOWED_PATHS` 白名单，且**解析符号链接**。

**发现物的来源**由服务端会话存储校验 —— 外部调用方**不能注入任意 finding**。

## 3. 抑制文件

项目根放 `.dcs-suppress.yaml` 登记误报/已接受风险/延期项：

```yaml
version: 1
suppressions:
  - rule: CWE-22
    file: "src/config/*.py"
    reason: "配置路径由管理员控制"
  - rule: CWE-89
    file: "src/legacy/db.py"
    line: 145
    reason: "遗留代码，Q2 重构"
```

**抑制文件只影响 SAST 发现，不影响 fuzzer 崩溃。** 所有输出格式（text/JSON/SARIF/HTML）
都要显示**抑制统计** —— 不许悄悄吞掉。

## 4. 🔴 十四项已知局限（上游自述，逐条照抄 —— 这是最值钱的部分）

1. **只做过程内污点追踪**：源与汇必须在**同一函数体**内。
   预期检出率 **真实世界注入类漏洞的 10–25%**。**多数 Web 应用漏洞跨函数边界，v1 查不到。**
2. **tree-sitter 后端查询脆**：别名导入 `req = request` · 全限定名 `flask.request.form` ·
   类属性 `self.request.form` · 链式调用 —— 用 tree-sitter 时**不匹配**（用 Semgrep 后端则正常）。
3. **PoC 验证只是加分**：模板化 PoC 多数因缺执行上下文而失败。**失败的 PoC 不代表漏洞是假的。**
4. **无跨语言污点**：Python 经 FFI 调 C 不被分析，各语言独立。
5. **无过程间分析**：跨函数/跨文件调用图不追踪（v1.1 计划）。
6. **fuzzer 需可选依赖**：要装 `anthropic` SDK 等。
7. **MCP 的 fuzz 工具需 Podman**。
8. **C：无预处理器解析**：`#ifdef` 与宏展开对扫描器不可见。
9. **C：无结构体成员污点追踪**：只追标量与直接指针解引用。
10. **C：指针别名只在同函数内追踪**。
11. **C：输出参数型源未支持**：`recv` / `fread` / `read` / `scanf` / `getline` / `getdelim`
    **不是有效污点源**；只有返回值为污点数据的（`argv` / `getenv` / `gets` / `fgets`）才对。
12. **C：CWE-416（释放后使用）检测延后**：需要时序分析，与源→汇模型本质不同。
13. **C：`mktemp()` / `tmpnam()` 检测缺口**：登记为 CWE-676 汇，但污点流水线需要源→汇路径，
    而多数真实用法传的是硬编码模板 ⇒ **不会被报出**。
14. **C fuzzer 的 harness 校验是白名单式，不是防逃逸的**：AI 生成的 C 代码在 Podman 容器内编译执行，
    双层 AST 校验禁危险系统调用与非标准头，但这是**纵深防御，不是完整安全边界**。
    绕过 AST 白名单的提示注入**仍可在容器内执行任意代码**（但不能逃逸到宿主机）。

## 5. 使用纪律

- **范围**：只用**自有资产**。对非自有目标一律不碰（与 `sec_scan`「扫描自有代码」同口径）。
- **与现有能力的关系**：本技能是**判据层**；真跑扫描属于会起进程的动作 ⇒ 走 `run_task`，
  由 `security/policy.py` 判作用域（`process_execute` 等），**授权只能主人在终端发**。
- **检出率预期管理**：按局限 1，**不要把 10–25% 的检出率当成"系统很安全"** ——
  查不到 ≠ 没有。
