# -*- coding: utf-8 -*-
"""
pm_live.config — Polymarket 真金执行层配置
==========================================
读取 .env(与本包同目录), 提供链上/CLOB 常量与准入判断。
所有私钥/凭证只从环境变量或 .env 读取, 绝不硬编码、绝不打印。
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

PKG_DIR = Path(__file__).resolve().parent
ENV_FILE = PKG_DIR / ".env"

# ---- 链上常量 (Polygon) ----
POLYGON_CHAIN_ID = 137
USDC_E = "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174"          # Polygon 官方桥接 USDC.e
CTF_EXCHANGE = "0x4bFb41d5B3570DeFd03C39a9A4D8dE6Bd8B8982E"    # Polymarket CTF Exchange(标准市场抵押品)
RPC_DEFAULT = "https://polygon-rpc.com"
RPC_FALLBACKS = [
    "https://polygon-rpc.com",
    "https://polygon-bor-rpc.publicnode.com",
    "https://polygon.drpc.org",
    "https://rpc.ankr.com/polygon",
]
GAMMA = "https://gamma-api.polymarket.com"                     # 行情/市场元数据(已验证可达)
CLOB = "https://clob.polymarket.com"                           # 交易主机(订单/撤单/余额)

ENV_KEYS = [
    "PM_API_KEY",          # Polymarket API Key (CLOB)
    "PM_API_SECRET",       # Polymarket API Secret
    "PM_API_PASSPHRASE",   # Polymarket API Passphrase
    "PM_L2_PRIVATE_KEY",   # L2/EOA 私钥(0x...) — 与 API Key 绑定的地址, 也是链上充值钱包
    "PM_RPC_URL",          # 可选, 自定义 Polygon RPC
    "PM_DRY_RUN",          # 可选, 默认 1 = 强制干跑; 0 = 允许真实广播(仍需每条命令 --yes)
]


def _load_env() -> None:
    if not ENV_FILE.exists():
        return
    for line in ENV_FILE.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        k = k.strip()
        v = v.strip().strip('"').strip("'")
        if k and k not in os.environ:
            os.environ[k] = v


_load_env()


def _env(name: str, default: str = "") -> str:
    return os.environ.get(name, default).strip()


@dataclass
class Config:
    api_key: str = field(default_factory=lambda: _env("PM_API_KEY"))
    api_secret: str = field(default_factory=lambda: _env("PM_API_SECRET"))
    api_passphrase: str = field(default_factory=lambda: _env("PM_API_PASSPHRASE"))
    l2_private_key: str = field(default_factory=lambda: _env("PM_L2_PRIVATE_KEY"))
    rpc_url: str = field(default_factory=lambda: _env("PM_RPC_URL") or RPC_DEFAULT)
    dry_run: bool = field(default_factory=lambda: _env("PM_DRY_RUN", "1").lower() not in ("0", "false", "no"))

    @property
    def has_clob_creds(self) -> bool:
        return bool(self.api_key and self.api_secret and self.api_passphrase)

    @property
    def has_l2_key(self) -> bool:
        return bool(self.l2_private_key and self.l2_private_key.lower().startswith("0x"))

    @property
    def configured(self) -> bool:
        return self.has_clob_creds and self.has_l2_key

    def describe(self) -> dict:
        addr = ""
        if self.has_l2_key:
            try:
                from eth_account import Account
                addr = Account.from_key(self.l2_private_key).address
            except Exception:
                addr = "(解析失败)"
        return {
            "clob_creds": self.has_clob_creds,
            "l2_key": self.has_l2_key,
            "l2_address": addr,
            "dry_run": self.dry_run,
            "rpc": self.rpc_url,
        }
