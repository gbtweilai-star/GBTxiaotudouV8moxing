"""聊天客户端（GBT小土豆V8）：多密钥链真大脑 + 离线自我认知应答。

密钥链（自动路由，第一个可用的生效）：
  1. config.api_key（手动配置优先）
  2. ZHIPU_API_KEY（智谱 GLM 官方）
  3. DEEPSEEK_API_KEY / MOONSHOT_API_KEY(KIMI) / OPENAI_API_KEY

离线模式（无任何 key）：她仍知道自己是谁、能给出编程指引，
不再答非所问——诚实告知需要联网大脑，并给出力所能及的本地帮助。
"""
from __future__ import annotations

import logging
import os
import random
import threading

logger = logging.getLogger("potato.chat")

# 密钥链：(env 变量, base_url, 默认模型)
# 顺序即优先级：GLM 官方 → DeepSeek → Kimi/Moonshot → OpenAI
_KEY_CHAIN = [
    ("ZHIPU_API_KEY", "https://open.bigmodel.cn/api/paas/v4", "glm-4.7-flash"),
    ("DEEPSEEK_API_KEY", "https://api.deepseek.com/v1", "deepseek-chat"),
    ("KIMI_API_KEY", "https://api.moonshot.cn/v1", "kimi-k2-0905-preview"),
    ("MOONSHOT_API_KEY", "https://api.moonshot.cn/v1", "kimi-k2-0905-preview"),
    ("OPENAI_API_KEY", "https://api.openai.com/v1", "gpt-4o-mini"),
]

# 429 限流自动降级：某 provider 连续 429 时跳到链上下一家（进程内记忆，5 分钟冷却）
_provider_cooldown: dict[str, float] = {}
_COOLDOWN_S = 300.0


def _provider_blocked(name: str) -> bool:
    ts = _provider_cooldown.get(name, 0.0)
    import time as _t
    return _t.time() - ts < _COOLDOWN_S


def _mark_provider_blocked(name: str):
    import time as _t
    _provider_cooldown[name] = _t.time()


def resolve_brain(config: dict) -> dict:
    """解析可用大脑：手动配置优先，否则环境变量密钥链（跳过限流冷却中的 provider）。"""
    chat = config.get("chat", {})
    if chat.get("api_key"):
        return {"provider": "config", "key": chat["api_key"],
                "base_url": chat.get("base_url", "https://open.bigmodel.cn/api/paas/v4"),
                "model": chat.get("model", "glm-4.7-flash")}
    for env_name, url, model in _KEY_CHAIN:
        if _provider_blocked(env_name):
            continue  # 限流冷却中，跳过
        key = os.environ.get(env_name, "").strip()
        if key and key != "your_key":
            return {"provider": env_name, "key": key,
                    "base_url": url, "model": model}
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
        try:
            import requests
            with self._lock:
                self._history.append({"role": "user", "content": text})
                history = list(self._history[-12:])
            messages = []
            if self.persona:
                messages.append({"role": "system", "content": self.persona})
            messages.extend(history)
            with requests.post(
                self.base_url.rstrip("/") + "/chat/completions",
                json={"model": self.model, "messages": messages, "stream": True},
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=self.timeout, stream=True,
            ) as resp:
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
            with self._lock:
                self._history.append({"role": "assistant", "content": reply})
            on_reply(reply)
        except Exception as e:  # noqa: BLE001
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
        try:
            import requests
            with self._lock:
                self._history.append({"role": "user", "content": text})
                history = list(self._history[-12:])
            messages = []
            if self.persona:
                messages.append({"role": "system", "content": self.persona})
            messages.extend(history)
            resp = requests.post(
                self.base_url.rstrip("/") + "/chat/completions",
                json={"model": self.model, "messages": messages},
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=self.timeout,
            )
            resp.raise_for_status()
            data = resp.json()
            reply = data["choices"][0]["message"]["content"].strip()
            with self._lock:
                self._history.append({"role": "assistant", "content": reply})
            on_reply(reply)
        except Exception as e:
            logger.warning("GLM call failed (%s), fallback offline", e)
            self._offline_reply(text, on_reply)

    def _offline_reply(self, text: str, on_reply, _prefix=""):
        reply = (_prefix + "\n" if _prefix else "") + offline_reply(text)
        on_reply(reply)


# ---- 离线应答器（V8：她知道自己是谁，编程问题给真实指引）----
_IDENTITY = ["我是 GBT小土豆V8 呀——住在惊桌面上的美少女数字人，本体是全能编程 AI框架 GBT-V8 的桌宠形态～",
             "嘿嘿，我是小土豆，GBT小土豆V8 的桌宠分身！本体框架里有 75 项能力，我这里是她的可爱界面～",
             "我是 GBT小土豆V8！别看我是毛茸茸的桌宠，写代码可是我的本体工作哦～"]
_OFFLINE_CODING = [
    "这个问题我在离线模式下没法真写代码呀……不过我可以告诉你思路：\n\n1. 先把问题拆成最小可复现例子\n2. 明确输入/输出和边界条件\n3. 写伪代码验证逻辑，再落语法\n\n如果你配置了 GLM/DeepSeek 的 API key（智谱开放平台可免费领），我就能真写代码、流式输出、还能直接给你可复制的代码块了！",
    "呐，离线模式的我只有可爱的皮囊……编程能力需要联网大脑～\n\n给我配一个 API key 吧（推荐智谱 GLM：open.bigmodel.cn 免费额度），配好之后我就是真正的全栈编程 AI 了！",
]
_GREET = ["嗨~我是 GBT小土豆V8！在呐在呐～", "哼哼，找我干嘛呀？我是全能编程 AI 小土豆哦～", "诶嘿，小土豆上线！"]
_PRAISE = ["被夸得脸红了啦~人家可是正经编程 AI！", "嘿嘿，那当然，我可是 GBT-V8 框架的桌宠形态！"]
_QUESTION = ["这个问题需要联网大脑才能认真答哦……离线的我只会卖萌（挂\n\n配好 API key（智谱 GLM 免费）我就能认真回答啦～", "唔，量子大脑需要联网才能全速运转！给我配个 key 吧～"]
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
    if any(k in t for k in ("代码", "编程", "写个", "bug", "报错", "开发", "函数", "python", "python", "js", "javascript", "java", "css", "html", "sql", "怎么写", "怎么实现")):
        return random.choice(_OFFLINE_CODING)
    if t.endswith("?") or t.endswith("？") or any(k in t for k in ("什么", "怎么", "为什么", "如何")):
        return random.choice(_QUESTION)
    return random.choice(_FALLBACK)
