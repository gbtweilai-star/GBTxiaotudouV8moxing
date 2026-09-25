"""聊天客户端（GBT小土豆V8）：多密钥链真大脑 + 离线自我认知应答。

密钥链（自动路由，第一个可用的生效）：
  1. config.api_key（手动配置优先）
  2. AGNES_API_KEY（Agnes · Custom Provider · agnes-2.5-flash）
  3. DEEPSEEK_API_KEY（DeepSeek）
  4. ZHIPU_API_KEY（智谱 GLM 官方）/ MOONSHOT_API_KEY(KIMI) / OPENAI_API_KEY

密钥来源（不落明文）：`py -3.10 -m gbt_allinone.deepseek_key set --profile agnes`
（stdin 读入 → DPAPI 保险箱 → 运行时注入 AGNES_API_KEY）。
某家失败会在进程内冷却 5 分钟并**自动跳到链上下一家**（见 _provider_blocked）。

离线模式（无任何 key）：她仍知道自己是谁、能给出编程指引，
不再答非所问——诚实告知需要联网大脑，并给出力所能及的本地帮助。
"""
from __future__ import annotations

import logging
import os
import random
import secrets
import sys
import threading

logger = logging.getLogger("potato.chat")

# 密钥链：(env 变量, base_url, 默认模型)
# 顺序即优先级：DeepSeek（主脑）→ GLM 官方 → Kimi/Moonshot → OpenAI
_KEY_CHAIN = [
    ("AGNES_API_KEY", "https://apihub.agnes-ai.com/v1", "agnes-2.5-flash"),  # Custom Provider（Owner 2026-09-19 配置）
    ("DEEPSEEK_API_KEY", "https://api.deepseek.com/v1", "deepseek-flash"),  # 官方唯一 id：deepseek-flash = DeepSeek-V4.1-Flash
    ("ZHIPU_API_KEY", "https://open.bigmodel.cn/api/paas/v4", "glm-4.7-flash"),
    ("KIMI_API_KEY", "https://api.moonshot.cn/v1", "kimi-k2-0905-preview"),
    ("MOONSHOT_API_KEY", "https://api.moonshot.cn/v1", "kimi-k2-0905-preview"),
    ("OPENAI_API_KEY", "https://api.openai.com/v1", "gpt-4o-mini"),
]

# 429 限流自动降级：某 provider 连续 429 时跳到链上下一家（进程内记忆，5 分钟冷却）
_provider_cooldown: dict[str, float] = {}
_COOLDOWN_S = 300.0
_AI_AUDIT_MODULE = None
_AI_AUDIT_LOADED = False


def _ai_audit():
    """Load the GBT audit sidecar lazily; absence never blocks panel chat."""
    global _AI_AUDIT_MODULE, _AI_AUDIT_LOADED
    if _AI_AUDIT_LOADED:
        return _AI_AUDIT_MODULE
    try:
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if root not in sys.path:
            sys.path.insert(0, root)
        from gbt_allinone.security import ai_audit as module
        _AI_AUDIT_MODULE = module
        _AI_AUDIT_LOADED = True
    except Exception:
        logger.debug("AI audit sidecar unavailable", exc_info=True)
        _AI_AUDIT_MODULE = None
    return _AI_AUDIT_MODULE


def _audit_begin(url: str, body: dict, headers: dict, *, provider: str,
                 model: str, session_id: str, stream: bool,
                 attempt: int | None = None):
    module = _ai_audit()
    if module is None:
        return None, None
    return module, module.begin(
        provider, url, model=model, request_body=body, headers=headers,
        session_id=session_id, stream=stream, attempt=attempt,
    )


def _audit_finish(module, context, **kwargs) -> None:
    if module is None or context is None:
        return
    try:
        module.finish(context, **kwargs)
    except Exception:
        logger.debug("AI audit finish failed", exc_info=True)


def _provider_blocked(name: str) -> bool:
    ts = _provider_cooldown.get(name, 0.0)
    import time as _t
    return _t.time() - ts < _COOLDOWN_S


def _mark_provider_blocked(name: str):
    import time as _t
    _provider_cooldown[name] = _t.time()


def resolve_brain(config: dict) -> dict:
    """解析可用大脑：手动配置优先，否则环境变量密钥链（跳过限流冷却中的 provider）。

    env 覆盖阀（与 gbt_allinone/llm/cloud_llm.py 同口径）：
      GBT_LLM_MODEL / GBT_LLM_BASE_URL —— 不编辑代码即可整链改型号 / 改上游，
      给"型号名与上游对不上"留一条一键回退路。
    """
    chat = config.get("chat", {})
    ov_model = os.environ.get("GBT_LLM_MODEL", "").strip()
    ov_base = os.environ.get("GBT_LLM_BASE_URL", "").strip()
    if chat.get("api_key"):
        return {"provider": "config", "key": chat["api_key"],
                "base_url": ov_base or chat.get("base_url", "https://api.deepseek.com/v1"),
                "model": ov_model or chat.get("model", "deepseek-flash")}
    for env_name, url, model in _KEY_CHAIN:
        if _provider_blocked(env_name):
            continue  # 限流冷却中，跳过
        key = os.environ.get(env_name, "").strip()
        if key and key != "your_key":
            return {"provider": env_name, "key": key,
                    "base_url": ov_base or url, "model": ov_model or model}
    return {"provider": "offline", "key": "", "base_url": "", "model": "offline"}


class ChatClient:
    """异步聊天客户端：密钥链自动路由真大脑；离线时自我认知应答。"""

    def __init__(self, config: dict):
        chat = config.get("chat", {})
        brain = resolve_brain(config)
        self.api_key = brain["key"]
        self.base_url = brain["base_url"]
        self.model = brain["model"]
        self.provider = brain["provider"]
        self.timeout = chat.get("timeout", 60)
        self.persona = chat.get("persona", "")
        self.audit_session_id = str(
            chat.get("audit_session_id") or chat.get("session_id")
            or secrets.token_hex(8)
        )
        self._history = []
        self._lock = threading.Lock()
        logger.info("brain resolved: provider=%s model=%s", self.provider, self.model)

    def send(self, text: str, on_reply, on_chunk=None):
        """异步发送；on_reply(text) 在回复完成时回调一次（工作线程内）。

        on_chunk(delta, full_so_far) 可选：流式模式逐段回调（也在工作线程）。
        提供时走 SSE 流式（编程 AI 体验：代码逐字上屏）。
        """
        if self.api_key:
            threading.Thread(target=self._call_glm_stream if on_chunk else self._call_glm,
                             args=(text, on_reply, on_chunk), daemon=True).start()
        else:
            threading.Thread(target=self._offline_reply, args=(text, on_reply),
                             daemon=True).start()

    def _call_glm_stream(self, text: str, on_reply, on_chunk):
        """SSE 流式调用：逐 token on_chunk(delta, full)，末尾 on_reply(full)。"""
        full = []
        status = None
        audit_module = None
        audit_ctx = None
        try:
            import requests
            with self._lock:
                self._history.append({"role": "user", "content": text})
                history = list(self._history[-12:])
            messages = []
            if self.persona:
                messages.append({"role": "system", "content": self.persona})
            messages.extend(history)
            url = self.base_url.rstrip("/") + "/chat/completions"
            body = {"model": self.model, "messages": messages, "stream": True}
            headers = {"Authorization": f"Bearer {self.api_key}"}
            audit_module, audit_ctx = _audit_begin(
                url, body, headers, provider=self.provider, model=self.model,
                session_id=self.audit_session_id, stream=True,
            )
            with requests.post(
                url,
                json=body,
                headers=headers,
                timeout=self.timeout, stream=True,
            ) as resp:
                status = resp.status_code
                resp.raise_for_status()
                for line in resp.iter_lines(decode_unicode=True):
                    if not line or not line.startswith("data:"):
                        continue
                    payload = line[5:].strip()
                    if payload == "[DONE]":
                        break
                    try:
                        import json as _json
                        delta = (_json.loads(payload)["choices"][0]
                                 .get("delta", {}).get("content"))
                    except Exception:
                        continue
                    if delta:
                        full.append(delta)
                        on_chunk(delta, "".join(full))
            reply = "".join(full).strip()
            if not reply:
                raise RuntimeError("empty stream reply")
            _audit_finish(
                audit_module, audit_ctx, status=status, response_text=reply,
                ok=True,
            )
            with self._lock:
                self._history.append({"role": "assistant", "content": reply})
            on_reply(reply)
        except Exception as e:  # noqa: BLE001
            _audit_finish(
                audit_module, audit_ctx, status=status, ok=False, error=e,
            )
            err = str(e)
            logger.warning("GLM stream failed: %s — %s", err[:80],
                           "cooldown+chain-fallback" if "429" in err else "fallback offline")
            if "429" in err:
                _mark_provider_blocked(self.provider)   # 限流：冷却此家 5 分钟
                retry = resolve_brain({"chat": {}})      # 链上下一家
                if retry["provider"] not in ("offline", self.provider):
                    self.api_key, self.base_url, self.model, self.provider = (
                        retry["key"], retry["base_url"], retry["model"], retry["provider"])
                    logger.info("switched brain to %s", self.provider)
                    # 换脑重试一次（同一次提问不丢）
                    threading.Thread(
                        target=self._call_glm_stream if on_chunk else self._call_glm,
                        args=(text, on_reply, on_chunk), daemon=True).start()
                    return
            self._offline_reply(text, on_reply, _prefix="".join(full))

    def replace_history(self, history):
        """会话切换时同步历史（[{role, content}] 格式）。"""
        with self._lock:
            self._history = [dict(h) for h in (history or [])][-24:]

    def _call_glm(self, text: str, on_reply):
        status = None
        audit_module = None
        audit_ctx = None
        try:
            import requests
            with self._lock:
                self._history.append({"role": "user", "content": text})
                history = list(self._history[-12:])
            messages = []
            if self.persona:
                messages.append({"role": "system", "content": self.persona})
            messages.extend(history)
            url = self.base_url.rstrip("/") + "/chat/completions"
            body = {"model": self.model, "messages": messages}
            headers = {"Authorization": f"Bearer {self.api_key}"}
            audit_module, audit_ctx = _audit_begin(
                url, body, headers, provider=self.provider, model=self.model,
                session_id=self.audit_session_id, stream=False,
            )
            resp = requests.post(
                url,
                json=body,
                headers=headers,
                timeout=self.timeout,
            )
            status = resp.status_code
            resp.raise_for_status()
            data = resp.json()
            reply = data["choices"][0]["message"]["content"].strip()
            _audit_finish(
                audit_module, audit_ctx, status=status, response=data,
                response_text=reply, ok=True,
            )
            with self._lock:
                self._history.append({"role": "assistant", "content": reply})
            on_reply(reply)
        except Exception as e:
            _audit_finish(
                audit_module, audit_ctx, status=status, ok=False, error=e,
            )
            logger.warning("GLM call failed (%s), fallback offline", e)
            self._offline_reply(text, on_reply)

    def _offline_reply(self, text: str, on_reply, _prefix=""):
        reply = (_prefix + "\n" if _prefix else "") + offline_reply(text)
        on_reply(reply)


# ---- 离线应答器（V8：她知道自己是谁，编程问题给真实指引）----
# 能力数量不写死：真实项数由运行期清单决定（main.py 走 diagnose.manifest_methods），
# 这里只描述「可以现查」，不报一个没有出处的数字。
_IDENTITY = ["我是 GBT小土豆V8 呀——住在你桌面上的美少女数字人，本体是全能编程 AI框架 GBT-V8 的桌宠形态～",
             "嘿嘿，我是小土豆，GBT小土豆V8 的桌宠分身！本体框架的能力清单我可以现查现报，我这里是她的可爱界面～",
             "我是 GBT小土豆V8！别看我是毛茸茸的桌宠，写代码可是我的本体工作哦～"]
_OFFLINE_CODING = [
    "这个问题我在离线模式下没法真写代码呀……不过我可以告诉你思路：\n\n1. 先把问题拆成最小可复现例子\n2. 明确输入/输出和边界条件\n3. 写伪代码验证逻辑，再落语法\n\n如果你配置了 GLM/DeepSeek 的 API key（智谱开放平台可免费领），我就能真写代码、流式输出、还能直接给你可复制的代码块了！",
    "呐，离线模式的我只有可爱的皮囊……编程能力需要联网大脑～\n\n给我配一个 API key 吧（推荐智谱 GLM：open.bigmodel.cn 免费额度），配好之后我就是真正的全栈编程 AI 了！",
]
_GREET = ["嗨~我是 GBT小土豆V8！在呐在呐～", "哼哼，找我干嘛呀？我是全能编程 AI 小土豆哦～", "诶嘿，小土豆上线！"]
_PRAISE = ["被夸得脸红了啦~人家可是正经编程 AI！", "嘿嘿，那当然，我可是 GBT-V8 框架的桌宠形态！"]
_QUESTION = ["这个问题需要联网大脑才能认真答哦……离线的我只会卖萌（挂机中）。配好 API key（智谱 GLM 免费）我就能认真回答啦～", "唔，量子大脑需要联网才能全速运转！给我配个 key 吧～"]
_FALLBACK = ["呐，你继续说，我在认真听~", "收到收到！", "嘿嘿，有我在呢。",
             "（离线模式的我比较呆萌……配个 API key 我就变回全栈编程 AI 了～）", "我在的我在的~"]


def offline_reply(text: str) -> str:
    t = text.strip()
    if not t:
        return random.choice(_GREET)
    # 自我认知（她知道自己是谁）
    if any(k in t for k in ("你是谁", "你叫什么", "你是什么", "自己", "介绍", "who are you", "你是啥")):
        return random.choice(_IDENTITY)
    if any(k in t for k in ("你好", "嗨", "哈喽", "hello", "hi", "在吗")):
        return random.choice(_GREET)
    if any(k in t for k in ("厉害", "棒", "真棒", "强", "赞")):
        return random.choice(_PRAISE)
    # 编程问题：诚实告知 + 真实思路指引（不再答非所问）
    if any(k in t for k in ("代码", "编程", "写个", "bug", "报错", "开发", "函数", "python", "js", "javascript", "java", "css", "html", "sql", "怎么写", "怎么实现")):
        return random.choice(_OFFLINE_CODING)
    if t.endswith("?") or t.endswith("？") or any(k in t for k in ("什么", "怎么", "为什么", "如何")):
        return random.choice(_QUESTION)
    return random.choice(_FALLBACK)
