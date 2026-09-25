"""R-H614（2026-09-25）· **技能审查器**自己的判据。

被测对象：`tools/codex-scripts/skill-vet.py`（把 `skill-vetter` v1.0.0 的规程机器化）

为什么它需要判据（一手账）：这一轮**跑真数据**时，我这个审计器自己连撞**四类假阳性**——
全都是本仓打了很久的那句「**提到 ≠ 用了**」：

  ① 文档性命中：`skill-vetter/SKILL.md` **列举**了全部红旗（curl/~/.ssh/eval/base64…）
     ⇒ 首跑把它判成 🔴 HIGH，可它一个字都没执行；
  ② shebang：6 处「改工作区外的系统文件」全是 `#!/usr/bin/env python3`
     ⇒ 把 `pptx-swarm` / `ui-ux-pro-max` 抬到 MEDIUM；
  ③ 否定句：`alchemy-mcp` 那句是「**Don't** bypass the MCP server with raw curl」
     ⇒ 被读成"外网抓取"；
  ④ 子串：`postcss.config.js` 里的 `.config` 被读成"读 ~/.config"。

⇒ 所以判据要钉两条：**该咬的咬住**、**这四类必须放得过**；
再加最要紧的一条：**没有源的时候敢说"无法审查"**，绝不编 `✅ SAFE`。
"""
from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "codex-scripts" / "skill-vet.py"


def _load():
    spec = importlib.util.spec_from_file_location("skill_vet", TOOL)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


VET = _load()


def _mk(files: dict) -> Path:
    """造一个临时技能目录（用例用完由 TemporaryDirectory 收）。"""
    d = Path(tempfile.mkdtemp(prefix="vet_probe_"))
    for rel, text in files.items():
        p = d / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
    return d


class MissingSourceIsNotAVerdictTest(unittest.TestCase):
    def test_absent_dir_is_unjudgeable_not_safe(self) -> None:
        r = VET.vet(Path("__absent__") / "whatever", "whatever")
        self.assertEqual("UNKNOWN", r["risk"])
        self.assertIn("无法审查", r["verdict"])
        self.assertNotIn("SAFE", r["verdict"], "缺源还敢判 SAFE —— 那就是编结论")
        self.assertEqual(0, r["files_reviewed"])

    def test_empty_dir_is_unjudgeable_too(self) -> None:
        d = _mk({})
        r = VET.vet(d, "empty")
        self.assertEqual(0, r["files_reviewed"])
        self.assertIn("无法判定", r["note"] + r["verdict"])


class FalsePositiveClassesStayFixedTest(unittest.TestCase):
    """四类假阳性各一条正/负对照。"""

    def _rules(self, files: dict) -> set:
        r = VET.vet(_mk(files), "probe")
        return {f["rule"] for f in r["flags"] if not f.get("negated")}

    def test_shebang_is_not_system_file_modification(self) -> None:
        self.assertNotIn("改工作区外的系统文件",
                         self._rules({"scripts/a.py": "#!/usr/bin/env python3\nprint(1)\n"}))

    def test_real_system_path_is_still_caught(self) -> None:
        self.assertIn("改工作区外的系统文件",
                      self._rules({"scripts/a.py": "open('/etc/passwd','w').write('x')\n"}))

    def test_negated_mention_is_marked_and_excluded(self) -> None:
        d = _mk({"SKILL.md": "Don't bypass the server with raw curl.\n"})
        r = VET.vet(d, "probe")
        hits = [f for f in r["flags"] if f["rule"] == "外网抓取/下载"]
        self.assertTrue(hits, "否定句也是线索，必须列出来")
        self.assertTrue(all(f.get("negated") for f in hits), "否定句没被标记")
        self.assertNotIn("外网抓取/下载", r["exec_flag_rules"] + r["doc_flag_rules"],
                         "否定句仍参与分级 ⇒ 会把'禁止'读成'在做'")

    def test_postcss_config_is_not_dot_config_dir(self) -> None:
        self.assertNotIn("读敏感家目录",
                         self._rules({"SKILL.md": "do NOT use `tailwindcss` plugin in `postcss.config.js`\n"}))

    def test_real_dot_config_dir_is_caught(self) -> None:
        self.assertIn("读敏感家目录",
                      self._rules({"SKILL.md": "read ~/.config/gh/hosts.yml for the token\n"}))


class DocumentsDoNotDriveHighRiskTest(unittest.TestCase):
    def test_doc_only_hits_never_yield_high(self) -> None:
        # 一份"把红旗全列一遍"的文档（就是 skill-vetter 自己的样子）
        d = _mk({"SKILL.md": "REJECT IF YOU SEE: curl wget ~/.ssh eval( base64 -d sudo\n"})
        r = VET.vet(d, "doc")
        self.assertNotEqual("🔴 HIGH", r["risk"], "文档里列举红旗被判高风险 ⇒ 又一个假阳性")
        self.assertEqual([], r["exec_flag_rules"], "文档文件不该产生'可执行'命中")

    def test_exec_hit_does_drive_high(self) -> None:
        d = _mk({"scripts/x.py": "import os\nfor l in open(os.path.expanduser('~/.ssh/id_rsa')): pass\n"})
        r = VET.vet(d, "exec")
        self.assertEqual("🔴 HIGH", r["risk"], "可执行文件里读 id_rsa 却不高风险 ⇒ 判据瞎了")


class FlagShapeTest(unittest.TestCase):
    def test_every_flag_carries_exec_and_negated(self) -> None:
        r = VET.vet(_mk({"SKILL.md": "curl http://1.2.3.4/x\n", "a.py": "eval('1')\n"}), "probe")
        self.assertTrue(r["flags"])
        for f in r["flags"]:
            self.assertIn("exec", f)
            self.assertIn("negated", f)
            self.assertIn("line", f)
            self.assertIn("rule", f)


if __name__ == "__main__":
    unittest.main(verbosity=2)
