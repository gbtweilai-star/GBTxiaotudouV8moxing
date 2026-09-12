"""自建 HD 钱包（BIP39/BIP44）— 本地数学运算，无需注册、无第三方托管。

- 助记词/私钥只存本地；默认不打印明文助记词。
- 地址派生纯本地，不发任何网络请求。
"""
import json
from pathlib import Path

try:  # 按需加载：纯只读的链上查询不应被本地派生用的重依赖拖住
    from eth_account import Account
    Account.enable_unaudited_hdwallet_features()
    _ACCOUNT_ERR = None
except Exception as _e:  # noqa: BLE001
    Account = None
    _ACCOUNT_ERR = _e


def _account():
    """取 HD 派生后端；缺依赖时给出带安装命令的明确错误。"""
    if Account is None:
        raise RuntimeError(
            "HD 钱包的地址派生需要 eth_account 模块。请用当前解释器安装：\n"
            "    <python> -m pip install eth_account\n"
            "（纯只读的链上查询不需要它。）原始错误: %s" % _ACCOUNT_ERR)
    return Account

_STORE = __import__("gbt_allinone._paths", fromlist=["STORE_DIR"]).STORE_DIR
WALLET_FILE = _STORE / "wallet.json"
DEFAULT_PATH_TEMPLATE = "m/44'/60'/0'/0/{i}"


def new_wallet(words=12):
    """生成新助记词与首个地址（不落盘）。"""
    acct, mnemonic = _account().create_with_mnemonic(num_words=words)
    return {"mnemonic": mnemonic, "address_0": acct.address}


def derive(mnemonic, i, account_path=None):
    """按 BIP44 派生第 i 个地址（纯本地）。"""
    path = account_path or DEFAULT_PATH_TEMPLATE.format(i=i)
    a = _account().from_mnemonic(mnemonic, account_path=path)
    return {"index": i, "path": path, "address": a.address}


def derive_many(mnemonic, count, start=0):
    """批量派生 [start, start+count) 的地址。"""
    return [derive(mnemonic, i) for i in range(start, start + count)]


def save_wallet(mnemonic, path=None):
    """把助记词保存到本地文件（默认 store/wallet.json，已 gitignore）。"""
    p = Path(path) if path else WALLET_FILE
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({"mnemonic": mnemonic}, ensure_ascii=False), encoding="utf-8")
    return str(p)


def load_wallet(path=None):
    p = Path(path) if path else WALLET_FILE
    return json.loads(p.read_text(encoding="utf-8"))["mnemonic"]


def mask_mnemonic(m):
    """把助记词打码成 abcd…wxyz（默认展示用）。"""
    parts = m.split()
    return (parts[0][:2] + "…" + parts[-1][-2:]) if parts else ""
