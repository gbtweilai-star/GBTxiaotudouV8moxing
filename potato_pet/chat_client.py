"""聊天客户端：GLM API（OpenAI 兼容）+ 离线俏皮应答降级。"""
from __future__ import annotations

import logging
import random
import threading

logger = logging.getLogger("potato.chat")


class ChatClient:
    """异步聊天客户端：有 key 走 GLM，失败/无 key 降级离线俏皮应答。"""

    def __init__(self, config: dict):
        chat = config.get("chat", {})
        self.api_key = chat.get("api_key", "")
        self.base_url = chat.get("base_url", "https://open.bigmodel.cn/api/paas/v4")
        self.model = chat.get("model", "glm-4.7-flash")
        self.timeout = chat.get("timeout", 30)
        self.persona = chat.get("persona", "")
        self._history = []
        self._lock = threading.Lock()

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
            logger.warning("GLM stream failed: %s — fallback offline", e)
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


# ---- 离线俏皮应答器（纯本地） ----
_GREET = ["嗨~我在呐！", "哼哼，找我干嘛呀？", "诶嘿，小土豆上线！"]
_PRAISE = ["被夸得脸红了啦~", "嘿嘿，那当然，我可是未来科技美少女！"]
_QUESTION = ["这个问题……让本土豆想想哦~", "唔，量子大脑飞速运转中！"]
_CODING = ["写代码？我最拿手啦！", "哼哼，代码这种小事，交给本土豆！"]
_FALLBACK = ["呐，你继续说，我在认真听~", "收到收到！", "嘿嘿，有我在呢。",
             "唔……这个话题有点量子力学哦。", "我在的我在的~"]


def offline_reply(text: str) -> str:
    t = text.strip()
    if not t:
        return random.choice(_GREET)
    if any(k in t for k in ("你好", "嗨", "哈喽", "hello", "hi", "在吗")):
        return random.choice(_GREET)
    if any(k in t for k in ("厉害", "棒", "真棒", "强", "赞")):
        return random.choice(_PRAISE)
    if any(k in t for k in ("代码", "编程", "写个", "bug", "报错", "开发")):
        return random.choice(_CODING)
    if t.endswith("?") or t.endswith("？") or any(k in t for k in ("什么", "怎么", "为什么", "如何")):
        return random.choice(_QUESTION)
    return random.choice(_FALLBACK)
