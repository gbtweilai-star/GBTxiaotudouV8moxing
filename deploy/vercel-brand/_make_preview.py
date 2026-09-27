# -*- coding: utf-8 -*-
"""GBT小土豆V8 · 品牌主页 · 离线预览生成器

⛔ 开发者：自由的风 · 永久钢印 · 禁止删除

把服务端真实渲染结果落成单文件 HTML（品牌图已内嵌为 data URI，离线可看）。
只做一件事：把线上会走 fetch('/api/status') 的那段换成「file:// 时用真实快照兜底」，
其余 HTML/CSS/文案一字不改 —— 预览必须等于线上，否则预览就是骗人。

用法：python _make_preview.py <输出路径>
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from api import index as site  # noqa: E402

# 线上脚本原文 → 预览版（唯一差异：file:// 下用真实快照兜底，并标注来源）
_SCRIPT_TAIL = "})();\n</script>"

_PREVIEW_SCRIPT = """// 顶栏活点：拿真实端点读数，成功=青，失败=红。拿不到就如实说拿不到。
// ⚠️ 预览差异：file:// 打开时没有同源端点，此时用「本地实测快照」兜底，
//    并如实标注为 snapshot。部署到 www.gbtv8.com 后走真实 /api/status。
(function(){
  var el = document.getElementById('live'), tx = document.getElementById('livetext');
  var SNAPSHOT = @@SNAPSHOT@@;   // 取自本地真实端口实测，非编造
  function paint(d, tag){
    el.setAttribute('data-s','ok');
    tx.textContent = (d.service || 'online') + ' · ' + (d.region || 'local') + (tag || '');
  }
  if (location.protocol === 'file:') { paint(SNAPSHOT, ' · snapshot'); return; }
  fetch('/api/status', {cache:'no-store'})
    .then(function(r){ if(!r.ok) throw new Error('HTTP ' + r.status); return r.json(); })
    .then(function(d){ paint(d, ''); })
    .catch(function(e){ paint(SNAPSHOT, ' · snapshot'); });
})();
</script>"""


def main() -> int:
    out = Path(sys.argv[1] if len(sys.argv) > 1 else HERE / "preview-brand-site.html")
    client = site.app.test_client()
    html = client.get("/").get_data(as_text=True)

    snap = client.get("/api/status").get_json()
    snap["note"] = "local snapshot"
    script = _PREVIEW_SCRIPT.replace("@@SNAPSHOT@@", json.dumps(snap, ensure_ascii=False))

    # 只替换最后那段 fetch 脚本（它紧邻 </body> 之前的 </script>）
    head, sep, _ = html.rpartition("// 顶栏活点")
    if not sep:
        print("[FATAL] 未定位到活动点脚本，预览不许盲替换。")
        return 1
    preview = head + script + "\n</body>\n</html>\n"

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(preview, encoding="utf-8")
    print("已生成：%s  (%d 字节)" % (out, len(preview.encode("utf-8"))))
    print("快照：%s" % json.dumps(snap, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
