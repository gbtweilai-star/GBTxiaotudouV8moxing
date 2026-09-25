# -*- coding: utf-8 -*-
"""vision 密钥路径 · 带牙用例（R-H201）。

① `plaintext_key_in_return`：返回值里出现明文 key ⇒ 拒（backend/status 都不许带）；
② `second_key_path`：不许再有第二条取 key 的路（不读 GBT_VISION_API_KEY、不回落 cloud_llm.API_KEY），
   且必须走保险箱 `load_from_vault`（**不许用 env 优先的 `load_key`**）；
③ `key_leaked_to_log`：审计只收脱敏头（Authorization 变掩码）。
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for p in (ROOT, ROOT / "gbt_allinone"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from gbt_allinone import vision_cap as vc  # noqa: E402


class PlaintextTests(unittest.TestCase):
    def test_backend_has_no_plaintext_key(self):
        b = vc.resolve_vision_backend()
        self.assertNotIn("key", b, "backend 里不许有 key 字段（只许 key_id / key_masked）")
        for k in ("key_id", "key_present", "key_masked"):
            self.assertIn(k, b)
        self.assertTrue(vc.assert_no_plaintext(b, where="backend")["ok"])
        self.assertNotIn("sk-", str(b))

    def test_guard_rejects_plaintext_key(self):
        bad = vc.assert_no_plaintext({"key": "sk-abcdefghijklmnopqrstuvwx"}, where="poisoned")
        self.assertFalse(bad["ok"])
        self.assertEqual(bad["rule"], "plaintext_key_in_return")
        self.assertIn("不许带明文", bad["why"])

    def test_status_op_is_clean_too(self):
        st = vc.run("status")
        self.assertTrue(vc.assert_no_plaintext(st, where="status")["ok"])
        self.assertNotIn("key", st)
        self.assertIn("key_masked", st)


class SinglePathTests(unittest.TestCase):
    def test_no_second_key_path_in_source(self):
        src = Path(vc.__file__).read_text(encoding="utf-8")
        self.assertNotIn('get("GBT_VISION_API_KEY"', src, "不许再从 vision 专用环境变量取 key")
        self.assertNotIn("_cl.API_KEY", src, "不许再回落到模块常量的明文 key")
        self.assertIn("load_from_vault", src, "必须走 DPAPI 保险箱")
        self.assertNotIn("_dk.load_key(", src, "不许用 load_key：它 env 优先 ⇒ 等于偷偷走环境变量")

    def test_missing_vault_key_reports_needs_dependency(self):
        key = vc._vision_key()
        if not key:
            out = vc.cloud_recognize(image=None)
            self.assertFalse(out["ok"])
            self.assertEqual(out.get("status"), "needs_dependency",
                             "保险箱没密钥 ⇒ 如实报缺，不许拿环境变量顶上")


class AuditMaskTests(unittest.TestCase):
    def test_authorization_header_is_masked_for_audit(self):
        masked = vc._safe_headers({"Content-Type": "application/json",
                                   "Authorization": "Bearer sk-abcdefghijklmnopqrstuvwx"})
        self.assertNotIn("sk-abcdefghijklmnopqrstuvwx", masked["Authorization"])
        self.assertTrue(masked["Authorization"].startswith("Bearer "))
        self.assertIn("*", masked["Authorization"])
        self.assertEqual(masked["Content-Type"], "application/json")

    def test_audit_call_uses_masked_headers(self):
        src = Path(vc.__file__).read_text(encoding="utf-8")
        i = src.find("_audit.begin(")
        self.assertGreater(i, -1, "找不到 _audit.begin 调用")
        # **只看审计那一次调用**（判据不许扩大化：真实 HTTP 请求里的 headers=headers 是合法的）
        j = src.find("headers=_safe_headers(headers))", i)
        self.assertGreater(j, i, "审计没走脱敏头")
        block = src[i:j + len("headers=_safe_headers(headers))")]
        self.assertIn("_safe_headers(headers)", block,
                      "审计必须收脱敏头：不许把 Authorization 原文交给审计")
        self.assertNotIn("headers=headers", block, "审计那一段不许直接收原文头")


if __name__ == "__main__":
    unittest.main()
