#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""DeepSeek 上游密钥的 DPAPI 保险箱（规格对齐 cloudflare / notion / 星云）。

为什么要有这个文件：
  Codex 的 config.toml 里写的是 env_key = "DEEPSEEK_API_KEY"，
  但本机 HKCU\\Environment 里并没有这个变量 —— 现在能跑，是因为密钥还有一份
  明文副本躺在 ~/.codex/auth.json 与 ~/.codex/.deepseek_key 里。
  "能在跑"不等于"落对了地方"：明文密钥放在用户目录，任何进程都能读。

本模块把密钥收进 DPAPI 保险箱，运行时再解密注入环境变量：
  * 落盘：store/secrets/deepseek_api.dpapi（DPAPI/CurrentUser + 独立熵值，0600）
  * 熵值：GBTxiaotudouV8:deepseek:v1 —— 与飞书/Notion/星云/Cloudflare 互不可解
  * 明文：只进内存（os.environ），不进 argv、不进命令行历史、不进日志

用法：
  "sk-xxx" | py -3.10 -m gbt_allinone.deepseek_key set     # 存（stdin，不回显）
  py -3.10 -m gbt_allinone.deepseek_key status             # 体检（只输出掩码）
  py -3.10 -m gbt_allinone.deepseek_key inject -- <cmd...> # 解密后带环境变量启动子进程

多 profile（2026-09-19 加）：`set|status|inject` 都支持 `--profile <名>`，
默认仍是 deepseek。每个 profile 用**各自的熵值** ⇒ 一个库解不开另一个库。
可用 profile：deepseek · agnes（agnes = apihub.agnes-ai.com 那个 Custom Provider）

开发者：自由的风 · GBT小土豆V8
"""
from __future__ import annotations

import argparse
import ctypes
import json
import os
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from gbt_allinone._paths import STORE_DIR  # noqa: E402
from gbt_allinone.safe_io import atomic_write_bytes  # noqa: E402

# 一个 profile 一套（熵值 · 落盘文件名 · 主环境变量 · 代理环境变量 · 覆盖落盘路径的环境变量
#                · 可选的密钥形状正则）。
# 熵值互不相同 ⇒ 甲库密文在乙库里解不开，这是"互不可解"的**机制**，不是约定。
#
# `pattern` 为什么做成**每个 profile 各带一条**（2026-09-25 主人令「密钥全部部署跟双向插件一样、
# 可以自动读取」时加）：原来全库共用一条 `^(?:sk|ak)[-_]…`，而不同上游的密钥形状本来就不同 ——
# ADP（来也）的 key 是纯十六进制长串，**不以 sk-/ak- 开头** ⇒ 共用一条就会把合法密钥判成格式错。
# 给 profile 各带一条（不写就落回下面那条默认的），既收得住"贴错东西/多行粘贴"，又不误杀。
_PROFILES: dict[str, dict] = {
    "deepseek": {
        "entropy": b"GBTxiaotudouV8:deepseek:v1",
        "file": "deepseek_api.dpapi",
        "env": "DEEPSEEK_API_KEY",
        "proxy": "GBT_DEEPSEEK_KEY",
        "file_env": "GBT_DEEPSEEK_SECRET_FILE",
    },
    "agnes": {
        "entropy": b"GBTxiaotudouV8:agnes:v1",
        "file": "agnes_api.dpapi",
        "env": "AGNES_API_KEY",
        "proxy": "",
        "file_env": "GBT_AGNES_SECRET_FILE",
    },
    "adp": {
        "entropy": b"GBTxiaotudouV8:adp:v1",
        "file": "adp_api.dpapi",
        "env": "ADP_API_KEY",
        "proxy": "",
        "file_env": "GBT_ADP_SECRET_FILE",
        # 来也 ADP 的 key 是纯十六进制长串，不带 sk-/ak- 前缀 ⇒ 这条只保证"是单行长串"
        "pattern": r"^[A-Za-z0-9_\-]{20,}$",
    },
}
_DEFAULT_PROFILE = "deepseek"
# 默认形状：sk-/ak- 开头的单行长串（deepseek / agnes 用它，**行为与加多 profile 之前一字不差**）
_KEY_PATTERN = re.compile(r"^(?:sk|ak)[-_][A-Za-z0-9_\-]{16,}$")


class DeepseekKeyError(RuntimeError):
    """密钥处理错误。"""


def _profile(name: str | None = None) -> tuple[str, dict]:
    """取 profile 规格；名字不认识 -> **显式报错**（不静默退回默认，免得写错库还不知道）。"""
    key = str(name or _DEFAULT_PROFILE).strip().lower() or _DEFAULT_PROFILE
    spec = _PROFILES.get(key)
    if not spec:
        raise DeepseekKeyError("未知保险箱 profile：%s（可选：%s）"
                               % (key, " / ".join(sorted(_PROFILES))))
    return key, spec


def _secret_file(profile: str | None = None) -> Path:
    _name, spec = _profile(profile)
    raw = os.environ.get(spec["file_env"], "").strip()
    return (Path(raw).expanduser().resolve() if raw
            else Path(STORE_DIR) / "secrets" / spec["file"])


class _DataBlob(ctypes.Structure):
    _fields_ = [
        ("cbData", ctypes.c_ulong),
        ("pbData", ctypes.POINTER(ctypes.c_byte)),
    ]


def _blob(raw: bytes):
    buf = ctypes.create_string_buffer(raw, len(raw))
    return (_DataBlob(len(raw), ctypes.cast(buf, ctypes.POINTER(ctypes.c_byte))), buf)


def _protect_dpapi(data: bytes, profile: str | None = None) -> bytes:
    if os.name != "nt":
        raise DeepseekKeyError("当前系统不支持 Windows DPAPI")
    _name, spec = _profile(profile)
    try:
        crypt32 = ctypes.windll.crypt32
        kernel32 = ctypes.windll.kernel32
        crypt32.CryptProtectData.argtypes = [
            ctypes.POINTER(_DataBlob), ctypes.c_wchar_p,
            ctypes.POINTER(_DataBlob), ctypes.c_void_p, ctypes.c_void_p,
            ctypes.c_ulong, ctypes.POINTER(_DataBlob),
        ]
        crypt32.CryptProtectData.restype = ctypes.c_int
        kernel32.LocalFree.argtypes = [ctypes.c_void_p]
        kernel32.LocalFree.restype = ctypes.c_void_p

        input_blob, input_buf = _blob(data)
        entropy_blob, entropy_buf = _blob(spec["entropy"])
        output = _DataBlob()
        ok = crypt32.CryptProtectData(
            ctypes.byref(input_blob),
            "GBT小土豆V8 %s credential" % _name,
            ctypes.byref(entropy_blob),
            None,
            None,
            0x1,
            ctypes.byref(output),
        )
        _keepalive = (input_buf, entropy_buf)
        if not ok:
            raise DeepseekKeyError("DPAPI 加密失败")
        try:
            return ctypes.string_at(output.pbData, output.cbData)
        finally:
            kernel32.LocalFree(output.pbData)
    except DeepseekKeyError:
        raise
    except Exception as exc:  # noqa: BLE001
        raise DeepseekKeyError(f"DPAPI 不可用：{str(exc)[:160]}") from exc


def _unprotect_dpapi(data: bytes, profile: str | None = None) -> bytes:
    if os.name != "nt":
        raise DeepseekKeyError("当前系统不支持 Windows DPAPI")
    _name, spec = _profile(profile)
    try:
        crypt32 = ctypes.windll.crypt32
        kernel32 = ctypes.windll.kernel32
        crypt32.CryptUnprotectData.argtypes = [
            ctypes.POINTER(_DataBlob), ctypes.POINTER(ctypes.c_wchar_p),
            ctypes.POINTER(_DataBlob), ctypes.c_void_p, ctypes.c_void_p,
            ctypes.c_ulong, ctypes.POINTER(_DataBlob),
        ]
        crypt32.CryptUnprotectData.restype = ctypes.c_int
        kernel32.LocalFree.argtypes = [ctypes.c_void_p]
        kernel32.LocalFree.restype = ctypes.c_void_p

        input_blob, input_buf = _blob(data)
        entropy_blob, entropy_buf = _blob(spec["entropy"])
        output = _DataBlob()
        ok = crypt32.CryptUnprotectData(
            ctypes.byref(input_blob),
            None,
            ctypes.byref(entropy_blob),
            None,
            None,
            0x1,
            ctypes.byref(output),
        )
        _keepalive = (input_buf, entropy_buf)
        if not ok:
            raise DeepseekKeyError("DPAPI 解密失败")
        try:
            return ctypes.string_at(output.pbData, output.cbData)
        finally:
            kernel32.LocalFree(output.pbData)
    except DeepseekKeyError:
        raise
    except Exception as exc:  # noqa: BLE001
        raise DeepseekKeyError(f"DPAPI 不可用：{str(exc)[:160]}") from exc


def mask(value: str) -> str:
    text = str(value or "")
    return f"{text[:5]}****" if len(text) >= 5 else ""


def _validate(key: str, profile: str | None = None) -> str:
    text = str(key or "").strip().strip('"').strip("'")
    name, spec = _profile(profile)
    pattern = spec.get("pattern") or _KEY_PATTERN.pattern
    if not re.match(pattern, text):
        raise DeepseekKeyError("密钥格式不符（profile=%s 的形状是 %s）" % (name, pattern))
    return text


def store_key(key: str, profile: str | None = None) -> dict:
    """把密钥加密落到 DPAPI 文件，返回报告；任何路径都不返回明文。"""
    name, spec = _profile(profile)
    try:
        safe = _validate(key, name)
    except DeepseekKeyError as exc:
        return {"ok": False, "error": str(exc)}
    try:
        target = _secret_file(name)
        atomic_write_bytes(target, _protect_dpapi(safe.encode("utf-8"), name), mode=0o600)
        return {
            "ok": True,
            "configured": True,
            "credential": "dpapi",
            "profile": name,
            "entropy": spec["entropy"].decode("ascii"),
            "masked": mask(safe),
            "path": str(target),
            "bytes": target.stat().st_size,
        }
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": str(exc)[:200]}


def load_key(profile: str | None = None) -> tuple[str, str]:
    """返回 (key, source)。source ∈ env:… / dpapi / missing / unreadable。"""
    name, spec = _profile(profile)
    env = os.environ.get(spec["env"], "").strip()
    if not env and spec["proxy"]:
        env = os.environ.get(spec["proxy"], "").strip()
    if env:
        return env, "env:" + (spec["env"] if os.environ.get(spec["env"]) else spec["proxy"])
    target = _secret_file(name)
    if not target.is_file():
        return "", "missing"
    try:
        key = _unprotect_dpapi(target.read_bytes(), name).decode("utf-8").strip()
    except Exception:  # noqa: BLE001
        return "", "unreadable"
    if not key:
        return "", "missing"
    return key, "dpapi"


def load_from_vault(profile: str | None = None) -> tuple[str, str]:
    """只从 DPAPI 保险箱取密钥，忽略环境变量。

    给"必须以保险箱为准"的调用方用（例如看门狗拉起中继时）：
    环境里来路不明的一份 key 不应该悄悄顶掉保险箱里的那一份。
    """
    name, _spec = _profile(profile)
    target = _secret_file(name)
    if not target.is_file():
        return "", "missing"
    try:
        key = _unprotect_dpapi(target.read_bytes(), name).decode("utf-8").strip()
    except Exception:  # noqa: BLE001
        return "", "unreadable"
    return (key, "dpapi") if key else ("", "missing")


def export_env(profile: str | None = None, *, override: bool = False) -> str:
    """把密钥从保险箱解出来注入当前进程环境。返回 source（不打印密钥）。

    override=False 时不覆盖已有的环境变量（谁先注入谁优先，避免把外部明确
    指定的值悄悄换掉 —— 静默改写也是静默失效的一种）。
    """
    name, spec = _profile(profile)
    if not override and os.environ.get(spec["env"], "").strip():
        return "env:" + spec["env"]
    key, source = load_key(name)
    if not key:
        return source
    os.environ[spec["env"]] = key
    # 中继代理读的是 GBT_DEEPSEEK_KEY（优先级高于它的 .deepseek_key 文件）
    if spec["proxy"] and (override or not os.environ.get(spec["proxy"], "").strip()):
        os.environ[spec["proxy"]] = key
    return source


def status(profile: str | None = None) -> dict:
    name, _spec = _profile(profile)
    key, source = load_key(name)
    target = _secret_file(name)
    return {
        "ok": bool(key),
        "configured": bool(key),
        "profile": name,
        "source": source,
        "masked": mask(key),
        "vault_exists": target.is_file(),
        "vault_path": str(target),
        "vault_bytes": target.stat().st_size if target.is_file() else 0,
    }


def _read_stdin_secret() -> str:
    raw = sys.stdin.buffer.read()
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = raw.decode("latin-1")
    # 密钥本身不含空白；顺带吃掉 PowerShell 管道带的 BOM/CRLF/引号
    return "".join(text.split()).strip('"').strip("'")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="LLM 上游密钥 DPAPI 保险箱（多 profile）")
    sub = parser.add_subparsers(dest="action")
    setter = sub.add_parser("set", help="从 stdin 读密钥并加密保存")
    setter.add_argument("--profile", default=_DEFAULT_PROFILE,
                        choices=sorted(_PROFILES), help="保险箱名（默认 deepseek）")
    checker = sub.add_parser("status", help="输出掩码体检结果")
    checker.add_argument("--profile", default=_DEFAULT_PROFILE,
                         choices=sorted(_PROFILES), help="保险箱名（默认 deepseek）")
    inject = sub.add_parser("inject", help="解密注入环境变量后启动子进程")
    inject.add_argument("--profile", default=_DEFAULT_PROFILE,
                        choices=sorted(_PROFILES), help="保险箱名（默认 deepseek）")
    inject.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args(argv)

    action = args.action or "status"
    profile = getattr(args, "profile", _DEFAULT_PROFILE)

    if action == "set":
        report = store_key(_read_stdin_secret(), profile)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0 if report.get("ok") else 1

    if action == "status":
        print(json.dumps(status(profile), ensure_ascii=False, indent=2))
        return 0 if status(profile).get("ok") else 1

    if action == "inject":
        command = [c for c in args.command if c != "--"]
        if not command:
            print("inject 需要子进程命令，例如：inject -- codex exec \"echo OK\"",
                  file=sys.stderr)
            return 2
        source = export_env(profile)
        if source in ("missing", "unreadable") or source.startswith("missing"):
            print("密钥不可用（source=%s），拒绝在没有密钥的情况下启动子进程" % source,
                  file=sys.stderr)
            return 3
        try:
            return subprocess.call(command)
        except FileNotFoundError:
            print("找不到命令：%s" % command[0], file=sys.stderr)
            return 4

    parser.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
