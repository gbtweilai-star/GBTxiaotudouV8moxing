# -*- coding: utf-8 -*-
"""统一路径解析 — 全框架 store 基址单一来源，支持 GBT_STORE_DIR 隔离（测试用）。"""
import os
from pathlib import Path

_BASE = Path(__file__).resolve().parent  # gbt_allinone/


def _resolve_store() -> Path:
    env = os.getenv("GBT_STORE_DIR")
    return Path(env).resolve() if env else (_BASE / "store")


STORE_DIR = _resolve_store()
