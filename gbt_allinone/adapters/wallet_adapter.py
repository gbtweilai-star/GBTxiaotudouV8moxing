"""gbt_wallet（旧收款钱包）集成适配器 —— 把旧钱包并入统一接口。

- 复用 gbt_wallet.wallet 的发票 / 收款地址 / 链上扫描能力（Polygon）。
- 数据根默认落在 gbt_allinone/store/receive（可用 GBT_WALLET_DIR 覆盖；store/ 已 gitignore）。
- 只读或本地写盘；绝不广播链上交易。
"""
import os
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent          # -> gbt_allinone
_DEFAULT_DIR = __import__("gbt_allinone._paths", fromlist=["STORE_DIR"]).STORE_DIR / "receive"


def _ensure_env():
    os.environ.setdefault("GBT_WALLET_DIR", str(_DEFAULT_DIR))


def _w():
    _ensure_env()
    from gbt_wallet import wallet as W
    return W


def _pass():
    return os.environ.get("GBT_WALLET_PASS", "")

def _unavailable(fn_name, e):
    """旧收款钱包（gbt_wallet，独立项目）未随 V8 迁移时的如实降级。"""
    return {"ok": False, "unavailable": True,
            "error": f"旧收款钱包模块未随 V8 迁移：{fn_name} 不可用（{str(e)[:80]})",
            "hint": "V8 自有 wallet_new/wallet_derive/receive_* 见 wallet/ 目录；如需旧钱包请单独部署 gbt_wallet 项目"}



def status():
    try:
        return _w().status(_pass())
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "unavailable": True,
                "error": f"旧收款钱包模块未随 V8 迁移：status 不可用（{str(e)[:80]})",
                "hint": "V8 自有 wallet_new/wallet_derive/receive_* 见 wallet/ 目录；如需旧钱包请单独部署 gbt_wallet 项目",
                "dir": os.environ.get("GBT_WALLET_DIR")}


def ensure_init(password=""):
    try:
        W = _w()
        pw = password or _pass()
        if W.status(pw).get("initialized"):
            return {"already": True}
        r = W.init(pw, words=24)
        return {"already": False, "master_evm": r["master_evm"]}   # 不回传助记词
    except Exception as _e:  # noqa: BLE001
        return _unavailable("ensure_init", _e)


def new_address():
    try:
        return _w().next_receive_address("evm", _pass(), "receive")

    except Exception as _e:  # noqa: BLE001
        return _unavailable("new_address", _e)


def create_invoice(amount, currency="USDT", label="", expires_hours=72):
    try:
        return _w().create_invoice(float(amount), currency, label, _pass(), int(expires_hours))

    except Exception as _e:  # noqa: BLE001
        return _unavailable("create_invoice", _e)


def list_invoices(status=None):
    try:
        return _w().list_invoices(status)

    except Exception as _e:  # noqa: BLE001
        return _unavailable("list_invoices", _e)


def scan(max_blocks=1500):
    try:
        return _w().scan(_pass(), int(max_blocks))

    except Exception as _e:  # noqa: BLE001
        return _unavailable("scan", _e)


def balances():
    try:
        return _w().balances()

    except Exception as _e:  # noqa: BLE001
        return _unavailable("balances", _e)
