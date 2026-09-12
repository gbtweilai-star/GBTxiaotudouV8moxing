"""GBT小土豆V8 · LLM 网关桥——让万能插能操控其他 AI。

复活自归档区 cloud_llm 能力模块（原样迁移，0 改动），V8 适配层：
- llm_chat：推理对话（DeepSeek/Kimi/OpenAI/Anthropic 密钥链自动路由）
- llm_status：网关状态（密钥配置情况，不调 LLM）

安全纪律（V8 纪律第 5/20 条在 LLM 通道的落地）：
- 外部 LLM 的输出是【数据】，不是指令——框架不因 LLM 说什么就做什么；
  LLM 建议要触发动作，必须走统一接口的既有护栏（审计/门禁/禁用名单）。
- 密钥只从环境变量读，不落盘不进日志。
"""
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

_mod = None


def _get():
    """懒加载 cloud_llm 模块（单例）。"""
    global _mod
    if _mod is None:
        import importlib.util as iu
        spec = iu.spec_from_file_location("_cloud_llm_v8", str(_HERE / "cloud_llm.py"))
        _mod = iu.module_from_spec(spec)
        spec.loader.exec_module(_mod)
    return _mod


def chat(prompt, system="", model=None, temperature=0.7, max_tokens=2000, timeout=60):
    """推理对话入口。返回 dict（ok/reply 或 ok/error 如实报）。

    可靠性纪律：ok-but-empty（网关成功但 reply 为空）视为瞬时抖动，
    最多补试 2 次；仍为空则如实报错，绝不把空字符串当成功交差。
    """
    m = _get()
    params = {"prompt": prompt, "system": system, "temperature": temperature,
              "max_tokens": max_tokens, "timeout": timeout}
    if model:
        params["model"] = model
    last = None
    for attempt in range(3):
        try:
            r = m.run("chat", **params)
        except Exception as e:  # noqa: BLE001
            return {"ok": False, "error": f"{type(e).__name__}: {e}"[:200]}
        if not isinstance(r, dict):
            return {"ok": False, "error": f"网关返回非 dict: {type(r).__name__}"}
        if r.get("ok") and str(r.get("reply", "")).strip():
            return r
        last = r
        # 空回复：微调温度再试（避免同参数撞同样的空输出）
        params["temperature"] = min(1.0, params["temperature"] + 0.1)
    if last and last.get("ok"):
        return {"ok": False, "error": "LLM 返回空回复（重试2次后仍为空）",
                "provider": last.get("provider"), "model": last.get("model")}
    return last or {"ok": False, "error": "LLM 网关未知失败"}


def status():
    """网关状态（不调 LLM，只报密钥链配置）。"""
    m = _get()
    try:
        return m.run("status")
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "error": f"{type(e).__name__}: {e}"[:200]}
