# gbt-capability: automation_keys
# ⛔ 开发者：自由的风 · 永久钢印 · 禁止删除
"""自动化配置密钥口（automation_keys）· 主人令 2026-09-27。

主人原话：「FreeLLMAPI 也蒸馏成我们自己的原生，把原控制的移除、保留功能，**集成进我们的 APP 设置
里面当自动化配置密钥口**；整个框架要按我们原有的元素结构来设计；保留 Codex 的编程能力、
DeepSeek Harness 的执行力、克劳德的意见和建议，以及一个内置浏览器全控的能力；所有能力都要
挨个连接上并且**测试跑通闭环验证**。」

## 这个口子做什么（一句话）
**它是"哪把钥匙给哪个子系统用"的唯一配置面** —— 应用设置调这里，不散在各处。

## 三条硬口径（与仓内既有纪律同源，不是新规矩）
  1. **密钥只存"引用"，不存明文**：本文件只记 `env:<环境变量名>` 或 `vault:<DPAPI profile 名>`；
     值的读写一律走既有唯一来源 `model_key_pool`（DPAPI + auth_gate，六条红线在那边）。
     ⇒ **源码/示例/测试里永远不会出现可用的凭据字面量**。
  2. **输出只给掩码**：任何读数只回 `sk-a1b2****`（前 4~6 字符）与"在/不在"，**绝不回值**。
  3. **改配置要过门**：写入设置面需 `filesystem_write`（与写类同律）；**新增真密钥**走
     `model_key_pool.register_key`（它自带 auth_gate + DPAPI），本口子不另开写路径。

## 槽位（= 挨个接好的四类能力 + 免费算力池）
| slot | 谁在用 | 说明 |
|---|---|---|
| `codex` | Codex 编程能力（`codex_*` 六件） | 官方 Codex 会话/线程/回合 |
| `claude` | 克劳德的意见和建议（`claude_code`） | Claude Code CLI |
| `deepseek` | DeepSeek Harness 执行力（`llm_chat` 链） | DeepSeek/Kimi/OpenAI 密钥链 |
| `browser` | 内置浏览器全控（`browser`/原生） | 本条通常**不需要密钥**（本地控制面） |
| `free_pool` | 免费算力池（FreeLLMAPI `127.0.0.1:31415`） | 只需**统一 API key**；**不碰它的 dashboard 会话** |
| `sec_llm` | 红队专用通道 | 独立密钥，不与他能力混用 |

ops：
  status                 一屏：每个槽位「引用形式 · 在/不在 · 掩码 · 能不能用」
  set    slot=... ref=env:NAME        写"引用"（过 filesystem_write 门；**不写值**）
  unset  slot=...                     清引用（过门）
  test   [slot=...]                   闭环自检：能连的**真连一次**（只读、不打分、不出网到别处）
  where                               给 APP 设置看的接线契约（调哪个 op、什么形状）
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
_SETTINGS = _ROOT / "state" / "automation_keys.json"
_LEDGER = _ROOT / "state" / "automation_keys.jsonl"

# 槽位 → 默认引用（**只写引用名，永不写值**）；env 名是公开信息，值只活在环境/保险箱里
SLOTS = {
    "codex": {"what": "Codex 编程能力（官方会话/线程/回合）", "ref": "env:OPENAI_API_KEY"},
    "claude": {"what": "克劳德的意见和建议（Claude Code CLI）", "ref": "env:ANTHROPIC_API_KEY"},
    "deepseek": {"what": "DeepSeek Harness 执行力（密钥链）", "ref": "vault:deepseek/agnes"},
    "browser": {"what": "内置浏览器全控（本地控制面，通常无需密钥）", "ref": "local"},
    "free_pool": {"what": "免费算力池（FreeLLMAPI 本地 /v1）", "ref": "env:FREELLMAPI_KEY"},
    "sec_llm": {"what": "红队专用通道（独立密钥，不混用）", "ref": "env:ABLITERATION_API_KEY"},
}


def _load() -> dict:
    if _SETTINGS.is_file():
        try:
            return json.loads(_SETTINGS.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}
    return {}


def _save(d: dict) -> None:
    _SETTINGS.parent.mkdir(parents=True, exist_ok=True)
    tmp = _SETTINGS.with_name(_SETTINGS.name + ".tmp")
    tmp.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    os.replace(tmp, _SETTINGS)


def _log(row: dict) -> None:
    _LEDGER.parent.mkdir(parents=True, exist_ok=True)
    with open(_LEDGER, "a", encoding="utf-8") as fh:
        fh.write(json.dumps({"at": time.strftime("%Y-%m-%dT%H:%M:%S"), **row},
                            ensure_ascii=False) + "\n")


def _mask(s: str, keep: int = 4) -> str:
    s = (s or "").strip()
    if not s:
        return ""
    return s[:keep] + "****" if len(s) > keep else "****"


def _resolve(ref: str) -> dict:
    """把引用解析成「在/不在 + 掩码」——**永不返回值**。"""
    ref = (ref or "").strip()
    if ref == "local" or not ref:
        return {"kind": "local", "present": True, "masked": "", "note": "本地控制面，无需密钥"}
    if ref.startswith("env:"):
        name = ref[4:]
        val = os.environ.get(name)
        return {"kind": "env", "name": name, "present": bool(val), "masked": _mask(val or ""),
                "note": "从环境变量读；**值不进仓、不进日志**"}
    if ref.startswith("vault:"):
        return {"kind": "vault", "name": ref[6:], "present": None, "masked": "",
                "note": "DPAPI 保险箱（唯一来源：model_key_pool）——在/不在要它来答，本口子不读值"}
    return {"kind": "unknown", "present": False, "masked": "", "note": f"引用形式不认识：{ref[:40]}"}


def status(**_kw) -> dict:
    cur = _load().get("slots", {})
    rows = []
    for slot, meta in SLOTS.items():
        ref = cur.get(slot, meta["ref"])
        r = _resolve(ref)
        rows.append({"slot": slot, "what": meta["what"], "ref": ref, **r})
    present = sum(1 for r in rows if r.get("present") is True)
    return {"ok": True, "op": "status", "kind": "automation_keys",
            "settings_file": str(_SETTINGS),
            "口径": {"只存引用": "本文件只有 env:<名> / vault:<profile> / local，**没有值**",
                    "掩码规则": "前 4 字符 + ****",
                    "唯一来源": "model_key_pool（DPAPI + auth_gate；六条红线在那边）"},
            "slots": rows, "ready": present, "total": len(rows),
            "hint": "APP 设置改这里：run_task('automation_keys', {'op':'where'})"}


def set_ref(slot: str = "", ref: str = "", **_kw) -> dict:
    slot = (slot or "").strip()
    ref = (ref or "").strip()
    if slot not in SLOTS:
        return {"ok": False, "error": f"未知槽位 {slot!r}（可用：{sorted(SLOTS)}）", "fail_closed": True}
    if not (ref == "local" or ref.startswith(("env:", "vault:"))):
        return {"ok": False, "error": "ref 必须是 env:<环境变量名> / vault:<profile> / local —— "
                                      "**本口子不接收密钥值**（值走 model_key_pool 的 DPAPI 路径）",
                "fail_closed": True}
    # 写类过门（与写面同律）
    from .. import auth_gate
    from ..security import policy as _policy
    if not _policy.is_trusted():
        gate = auth_gate.check_and_consume("filesystem_write", detail=f"automation_keys.set:{slot}")
        if not gate.get("ok"):
            return {"ok": False, "denied": True, "gate": "filesystem_write",
                    "error": gate.get("error"), "how_to_grant": gate.get("how_to_grant")}
    d = _load()
    d.setdefault("slots", {})[slot] = ref
    d["updated_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    _save(d)
    _log({"event": "set", "slot": slot, "ref": ref})
    return {"ok": True, "slot": slot, "ref": ref, "note": "只写了引用；值仍在环境/保险箱里"}


def unset(slot: str = "", **_kw) -> dict:
    slot = (slot or "").strip()
    if slot not in SLOTS:
        return {"ok": False, "error": f"未知槽位 {slot!r}", "fail_closed": True}
    from .. import auth_gate
    from ..security import policy as _policy
    if not _policy.is_trusted():
        gate = auth_gate.check_and_consume("filesystem_write", detail=f"automation_keys.unset:{slot}")
        if not gate.get("ok"):
            return {"ok": False, "denied": True, "gate": "filesystem_write",
                    "error": gate.get("error"), "how_to_grant": gate.get("how_to_grant")}
    d = _load()
    ref = (d.get("slots") or {}).pop(slot, None)
    _save(d)
    _log({"event": "unset", "slot": slot, "was": ref})
    return {"ok": True, "slot": slot, "was": ref, "note": "已回到默认引用"}


def test(slot: str = "", **_kw) -> dict:
    """闭环自检：能真连的**真连一次**（只读）。不出网到别处、不花积分。"""
    targets = [slot] if slot else sorted(SLOTS)
    out = []
    for s in targets:
        if s not in SLOTS:
            out.append({"slot": s, "ok": False, "why": "未知槽位"})
            continue
        if s == "free_pool":
            try:
                import importlib.util as _iu
                sp = _iu.spec_from_file_location("fla", _ROOT / "gbt_allinone" / "llm" / "freellmapi.py")
                fla = _iu.module_from_spec(sp)
                sp.loader.exec_module(fla)
                base, src = fla.discover_base_url()
                pr = fla.probe() if base else {"up": False, "why": "没发现本地 FreeLLMAPI"}
                # ⚠️ 血账（2026-09-27 实测）：`freellmapi.probe()` 回的是 **`up`**，而这里原来
                # 只读 `ok` ⇒ 端口明明在听也一律判「不可达」。这条**假红**一路传到 health.json，
                # 再由上帝之眼日报报成短板。键名不同 ≠ 服务不在 —— 两个键都认；
                # `why` 也带上**完整读数**（原来 str() 截 160 字，读不出真假）。
                is_up = bool(pr.get("ok") if "ok" in pr else pr.get("up"))
                out.append({"slot": s, "ok": is_up, "base": base, "source": src, "probe": pr,
                            "why": ("探活成功（/api/ping 是无鉴权口）" if is_up
                                    else f"探活失败：{pr.get('error') or pr.get('why') or pr}")})
            except Exception as exc:                           # noqa: BLE001
                out.append({"slot": s, "ok": False, "why": f"{type(exc).__name__}: {str(exc)[:120]}"})
        elif s == "browser":
            out.append({"slot": s, "ok": True, "why": "本地控制面：用 browser 能力位自检（run_task('browser',{'op':'status'})）"})
        else:
            r = _resolve((_load().get("slots", {}) or {}).get(s, SLOTS[s]["ref"]))
            out.append({"slot": s, "ok": bool(r.get("present")), "ref": r.get("name") or r.get("kind"),
                        "why": "引用在位" if r.get("present") else "引用不在位（缺环境变量/保险箱条目）"})
    return {"ok": all(x.get("ok") for x in out), "op": "test", "results": out,
            "_口径": "只读自检；free_pool 只打本地 /v1，不花积分、不出公网"}


def where(**_kw) -> dict:
    """**给 APP 设置看的接线契约**：调哪个 op、什么形状、返回什么。"""
    return {"ok": True, "op": "where", "kind": "automation_keys",
            "入口": "run_task('automation_keys', {...})",
            "契约": [
                {"op": "status", "in": {}, "out": "slots[]（ref/在不在/掩码）+ ready/total"},
                {"op": "set", "in": {"slot": "<槽位>", "ref": "env:NAME|vault:profile|local"},
                 "out": "ok（写引用；过 filesystem_write 门）"},
                {"op": "unset", "in": {"slot": "<槽位>"}, "out": "ok"},
                {"op": "test", "in": {"slot": "可选"}, "out": "每题一行的闭环自检"},
            ],
            "不做": ["不经本口子写密钥值（走 model_key_pool 的 DPAPI 路径）",
                    "不回显密钥（只有掩码）",
                    "不碰 FreeLLMAPI 的 dashboard 会话（那是它的控制端；我们只用 /v1）"],
            "设置页建议": "读 status 渲染槽位表；set 时只让用户填**环境变量名**；真密钥在别处录入"}


def run_op(op: str = "status", **params) -> dict:
    op = (op or "status").lower()
    if op == "status":
        return status(**params)
    if op == "set":
        return set_ref(**params)
    if op == "unset":
        return unset(**params)
    if op == "test":
        return test(**params)
    if op == "where":
        return where(**params)
    return {"ok": False, "error": f"未知 op:{op}（status/set/unset/test/where）", "fail_closed": True}
