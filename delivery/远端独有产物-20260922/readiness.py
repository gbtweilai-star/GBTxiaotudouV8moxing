"""GBT小土豆V8 · 依赖就绪自检（readiness）。

立场（Owner 定调）：这是纯 AI 框架 + 全 AI 能力体系。
本模块【绝不删除、绝不禁用】任何能力——只做一件事：
在进生产前诚实探测「外部后端/密钥」是否就位，
让依赖外部资源的能力（vision/voice/browser/sec_llm/llm_chat）
在缺依赖时能显式降级为 needs_dependency，而不是在生产静默失败。

能力永远在注册表里、永远可调用；缺依赖只是如实报缺，不是被限制。

用法：
    import gbt_allinone as g
    g.run_task("readiness")            # 若在 api 里接了路由
    # 或直接：
    from gbt_allinone.readiness import check
    check()
"""
import importlib
import os


# 能力 -> 所需外部后端/密钥（探测项）。缺失 = needs_dependency（不是病、不是禁用）。
_DEP_MATRIX = {
    "vision": {
        "kind": "external_backend",
        "probe_modules": ["vision_cap"],
        "env_any": ["AUTOGLM_API_KEY", "OPENAI_API_KEY", "GBT_VISION_BACKEND"],
        "note": "视觉识别需 AutoGLM/OpenAI 视觉后端；缺则该能力如实报 needs_dependency。",
    },
    "voice": {
        "kind": "external_backend",
        "probe_modules": ["voice_cap"],
        "env_any": ["GBT_TTS_BACKEND", "GBT_ASR_BACKEND"],
        "note": "语音合成/识别需 TTS/ASR 后端；缺则如实报 needs_dependency。",
    },
    "browser": {
        "kind": "external_backend",
        "probe_modules": ["browser_cap"],
        "import_any": ["playwright", "selenium"],
        "note": "浏览器自动化需 Playwright/Selenium；缺则如实报 needs_dependency。",
    },
    "sec_llm": {
        "kind": "api_key",
        "probe_modules": ["security.abl_gateway"],
        "env_any": ["ABLITERATION_API_KEY"],
        "note": "黑客大脑推理引擎需独立密钥 ABLITERATION_API_KEY；缺则如实报 needs_dependency。",
    },
    "llm_chat": {
        "kind": "api_key",
        "probe_modules": ["llm.bridge"],
        "env_any": ["DEEPSEEK_API_KEY", "KIMI_API_KEY", "OPENAI_API_KEY", "MOONSHOT_API_KEY"],
        "note": "LLM 网关需密钥链任一；缺则如实报 needs_dependency。",
    },
}


def _module_ok(name: str) -> bool:
    full = name if name.startswith("gbt_allinone") else "gbt_allinone." + name
    try:
        importlib.import_module(full)
        return True
    except Exception:
        return False


def _third_party_ok(name: str) -> bool:
    try:
        importlib.import_module(name)
        return True
    except Exception:
        return False


def _env_any(keys) -> bool:
    return any((os.environ.get(k) or "").strip() for k in (keys or []))


def probe(cap: str) -> dict:
    """探测单个能力的依赖就绪度。返回 ready/needs_dependency + 缺什么。"""
    spec = _DEP_MATRIX.get(cap)
    if not spec:
        # 不在依赖矩阵里的能力 = 框架自带真执行，天然 ready。
        return {"capability": cap, "ready": True, "kind": "native",
                "note": "框架原生能力，无外部依赖。"}

    missing = []
    # 模块可导入性
    for m in spec.get("probe_modules", []):
        if not _module_ok(m):
            missing.append(f"module:{m}")
    # 第三方库（任一满足即可）
    imp_any = spec.get("import_any")
    if imp_any and not any(_third_party_ok(x) for x in imp_any):
        missing.append("import_any:" + "|".join(imp_any))
    # 环境变量/密钥（任一满足即可）
    env_any = spec.get("env_any")
    if env_any and not _env_any(env_any):
        missing.append("env_any:" + "|".join(env_any))

    ready = not missing
    return {
        "capability": cap,
        "ready": ready,
        "kind": spec.get("kind"),
        "status": "ready" if ready else "needs_dependency",
        "missing": missing,
        "note": spec.get("note", ""),
    }


def is_ready(cap: str) -> bool:
    """给 api 层用的轻量判断：该能力的外部依赖是否就位。"""
    return probe(cap).get("ready", True)


def check() -> dict:
    """全量就绪自检：逐个探测依赖矩阵中的能力。"""
    results = [probe(c) for c in _DEP_MATRIX]
    not_ready = [r for r in results if not r["ready"]]
    return {
        "ok": not not_ready,
        "total_probed": len(results),
        "ready": [r["capability"] for r in results if r["ready"]],
        "needs_dependency": [
            {"capability": r["capability"], "missing": r["missing"], "note": r["note"]}
            for r in not_ready
        ],
        "note": ("全部外部依赖就位。" if not not_ready else
                 "以下能力缺外部后端/密钥——能力仍在、仍可调用，只是缺依赖时如实报 needs_dependency（非删除/非禁用）。"),
    }


if __name__ == "__main__":
    import json
    print(json.dumps(check(), ensure_ascii=False, indent=2))
