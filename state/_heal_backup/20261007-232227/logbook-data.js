/* GBT小土豆V8 · 记录本数据件 —— **生成产物**，由 logbook.py render 覆盖，不许手改。
 * 重生成：py -3.14 tools/codex-scripts/logbook.py render
 * 口径：只追加 + 自链哈希；数字全部现算自 state/logbook.jsonl。 */
window.GBT_LOGBOOK = {
 "generated_at": "2026-10-08T00:14:34+08:00",
 "regen": "py -3.14 tools/codex-scripts/logbook.py render",
 "source": "state/logbook.jsonl（只追加 · 自链哈希）",
 "chain": {
  "ok": true,
  "detail": "链自洽：13 条记录，末条 hash=sha256:809086c3ede9d33",
  "records": 13
 },
 "totals": {
  "records": 13,
  "scans": 3,
  "changes": 8,
  "decisions": 0,
  "delivers": 2
 },
 "scans": [
  {
   "n": 2,
   "ts": "2026-10-07T22:16:15+08:00",
   "label": "首扫 · 建基线",
   "scanned": 148692,
   "unchanged": 0,
   "added": 148692,
   "modified": 0,
   "deleted": 0,
   "baseline": true,
   "truncated": false,
   "samples": {
    "added": [
     ".agents/skills/better-auth-best-practices/SKILL.md",
     ".agents/skills/chrome-extensions/SKILL.md",
     ".agents/skills/chrome-extensions/references/extensions/api-calling.md",
     ".agents/skills/chrome-extensions/references/extensions/auth-identity.md",
     ".agents/skills/chrome-extensions/references/extensions/content-scripts.md",
     ".agents/skills/chrome-extensions/references/extensions/context-menus.md",
     ".agents/skills/chrome-extensions/references/extensions/csp-sandbox.md",
     ".agents/skills/chrome-extensions/references/extensions/declarative-net-request.md",
     ".agents/skills/chrome-extensions/references/extensions/devtools.md",
     ".agents/skills/chrome-extensions/references/extensions/icons.md",
     ".agents/skills/chrome-extensions/references/extensions/media-capture.md",
     ".agents/skills/chrome-extensions/references/extensions/message-passing.md",
     ".agents/skills/chrome-extensions/references/extensions/omnibox.md",
     ".agents/skills/chrome-extensions/references/extensions/permissions.md",
     ".agents/skills/chrome-extensions/references/extensions/popup-ui.md",
     ".agents/skills/chrome-extensions/references/extensions/prompt-api.md",
     ".agents/skills/chrome-extensions/references/extensions/service-worker.md",
     ".agents/skills/chrome-extensions/references/extensions/side-panel.md",
     ".agents/skills/chrome-extensions/references/extensions/storage.md",
     ".agents/skills/chrome-extensions/references/extensions/tab-management.md",
     ".agents/skills/chrome-extensions/references/extensions/user-scripts.md",
     ".agents/skills/chrome-extensions/references/webstore/chromewebstore-template.md",
     ".agents/skills/chrome-extensions/references/webstore/privacy-policy.md",
     ".agents/skills/chrome-extensions/references/webstore/review-checklist.md",
     ".agents/skills/chrome-extensions/references/webstore/store-listing.md",
     ".agents/skills/create-auth/SKILL.md",
     ".agents/skills/fc-nginx-website/.bundled-hash",
     ".agents/skills/fc-nginx-website/SKILL.md",
     ".agents/skills/modern-web-guidance/SKILL.md",
     ".agents/skills/modern-web-guidance/guides/accessibility/accessibility.md",
     ".agents/skills/modern-web-guidance/guides/accessibility/accessible-error-announcement.md",
     ".agents/skills/modern-web-guidance/guides/built-in-ai/language-detection.md",
     ".agents/skills/modern-web-guidance/guides/built-in-ai/language-model.md",
     ".agents/skills/modern-web-guidance/guides/built-in-ai/prompt-api.md",
     ".agents/skills/modern-web-guidance/guides/built-in-ai/summarizer.md",
     ".agents/skills/modern-web-guidance/guides/built-in-ai/translator.md",
     ".agents/skills/modern-web-guidance/guides/css/animate-to-intrinsic-sizes.md",
     ".agents/skills/modern-web-guidance/guides/css/calculate-with-intrinsic-sizes.md",
     ".agents/skills/modern-web-guidance/guides/css/child-state-based-styling.md",
     ".agents/skills/modern-web-guidance/guides/css/content-based-styling.md"
    ],
    "modified": [],
    "deleted": []
   }
  },
  {
   "n": 5,
   "ts": "2026-10-07T22:22:17+08:00",
   "label": "本轮改动扫描",
   "scanned": 148699,
   "unchanged": 148686,
   "added": 7,
   "modified": 6,
   "deleted": 0,
   "baseline": false,
   "truncated": false,
   "samples": {
    "added": [
     "holo_pet_w3/blueprint/blueprint-data.js",
     "holo_pet_w3/blueprint/index.html",
     "holo_pet_w3/logbook/index.html",
     "holo_pet_w3/logbook/logbook-data.js",
     "state/logbook-digest.md",
     "state/logbook-snapshot.json",
     "tools/codex-scripts/blueprint-feed.py"
    ],
    "modified": [
     "PROJECT_BLUEPRINT.md",
     "holo_pet_w3/package.json",
     "holo_pet_w3/panel/index.html",
     "holo_pet_w3/shell/windows.json",
     "state/logbook.jsonl",
     "tools/codex-scripts/logbook.py"
    ],
    "deleted": []
   }
  },
  {
   "n": 8,
   "ts": "2026-10-07T22:43:26+08:00",
   "label": "交付后扫描",
   "scanned": 148790,
   "unchanged": 148679,
   "added": 91,
   "modified": 20,
   "deleted": 0,
   "baseline": false,
   "truncated": false,
   "samples": {
    "added": [
     "dist/win-unpacked/resources/app/blueprint/blueprint-data.js",
     "dist/win-unpacked/resources/app/blueprint/index.html",
     "dist/win-unpacked/resources/app/brain/caps/action_gate.html",
     "dist/win-unpacked/resources/app/brain/caps/actioncam.html",
     "dist/win-unpacked/resources/app/brain/caps/agent_console.html",
     "dist/win-unpacked/resources/app/brain/caps/agent_control.html",
     "dist/win-unpacked/resources/app/brain/caps/agent_council.html",
     "dist/win-unpacked/resources/app/brain/caps/agent_rig.html",
     "dist/win-unpacked/resources/app/brain/caps/answer_shaper.html",
     "dist/win-unpacked/resources/app/brain/caps/asset_index.html",
     "dist/win-unpacked/resources/app/brain/caps/audio_extract.html",
     "dist/win-unpacked/resources/app/brain/caps/audio_mix.html",
     "dist/win-unpacked/resources/app/brain/caps/automation_keys.html",
     "dist/win-unpacked/resources/app/brain/caps/belief_forge.html",
     "dist/win-unpacked/resources/app/brain/caps/blender.html",
     "dist/win-unpacked/resources/app/brain/caps/brain_council.html",
     "dist/win-unpacked/resources/app/brain/caps/cap_tags.html",
     "dist/win-unpacked/resources/app/brain/caps/case_mine.html",
     "dist/win-unpacked/resources/app/brain/caps/claude_code.html",
     "dist/win-unpacked/resources/app/brain/caps/cli_chat.html",
     "dist/win-unpacked/resources/app/brain/caps/code_audit.html",
     "dist/win-unpacked/resources/app/brain/caps/codebuddy.html",
     "dist/win-unpacked/resources/app/brain/caps/collab_gateway.html",
     "dist/win-unpacked/resources/app/brain/caps/comfyui.html",
     "dist/win-unpacked/resources/app/brain/caps/command_chain.html",
     "dist/win-unpacked/resources/app/brain/caps/console_hub.html",
     "dist/win-unpacked/resources/app/brain/caps/console_pages.html",
     "dist/win-unpacked/resources/app/brain/caps/control_loop.html",
     "dist/win-unpacked/resources/app/brain/caps/creation_camp.html",
     "dist/win-unpacked/resources/app/brain/caps/datakit.html",
     "dist/win-unpacked/resources/app/brain/caps/db_probe.html",
     "dist/win-unpacked/resources/app/brain/caps/devour_fusion.html",
     "dist/win-unpacked/resources/app/brain/caps/edit_pipeline.html",
     "dist/win-unpacked/resources/app/brain/caps/energy_scheduler.html",
     "dist/win-unpacked/resources/app/brain/caps/event_ledger.html",
     "dist/win-unpacked/resources/app/brain/caps/filmkit.html",
     "dist/win-unpacked/resources/app/brain/caps/flow_canvas.html",
     "dist/win-unpacked/resources/app/brain/caps/freebuff_term.html",
     "dist/win-unpacked/resources/app/brain/caps/freellmapi.html",
     "dist/win-unpacked/resources/app/brain/caps/genoffice.html"
    ],
    "modified": [
     "dist/GBT小土豆V8 0.1.0.exe",
     "dist/builder-debug.yml",
     "dist/win-unpacked/GBT小土豆V8.exe",
     "dist/win-unpacked/resources/app/brain/brain-data.js",
     "dist/win-unpacked/resources/app/package.json",
     "dist/win-unpacked/resources/app/panel/index.html",
     "dist/win-unpacked/resources/app/plugins-mesh/index.html",
     "dist/win-unpacked/resources/app/shell/main.cjs",
     "dist/win-unpacked/resources/app/shell/windows.json",
     "dist/win-unpacked/resources/tools/codex-scripts/desktop-shell-guard.py",
     "holo_pet_w3/blueprint/blueprint-data.js",
     "holo_pet_w3/blueprint/index.html",
     "holo_pet_w3/logbook/logbook-data.js",
     "holo_pet_w3/shell/dsh-launch.cjs",
     "holo_pet_w3/shell/windows.json",
     "holo_pet_w3/tests/test_dsh_launch.cjs",
     "state/desktop-install-receipt.json",
     "state/logbook-digest.md",
     "state/logbook-snapshot.json",
     "state/logbook.jsonl"
    ],
    "deleted": []
   }
  }
 ],
 "records": [
  {
   "n": 1,
   "ts": "2026-10-07T22:15:50+08:00",
   "kind": "change",
   "actor": "ZCode/DeepSeek Harness",
   "what": "DeepSeek Harness 自接入接进桌面壳：壳自己拉起 dsh web --no-open，读就绪行把带 token 的 URL 交给同一个 w3ConnectDsh（过回环白名单 · URL 只在内存 · 只回 host）",
   "where": [
    "holo_pet_w3/shell/dsh-launch.cjs",
    "holo_pet_w3/shell/main.cjs",
    "holo_pet_w3/shell/windows.json",
    "holo_pet_w3/tests/test_dsh_launch.cjs"
   ],
   "hash": "sha256:3a9923dc9bc5277",
   "prev": "genesis"
  },
  {
   "n": 2,
   "ts": "2026-10-07T22:16:15+08:00",
   "kind": "scan",
   "actor": "logbook.py scan",
   "what": "首扫 · 建基线：**建基线**（第一次扫描，没有旧快照可比）—— 现盘 148692 个文件已记成基线",
   "where": [
    "."
   ],
   "hash": "sha256:9f59d64dce9aabb",
   "prev": "sha256:3a9923dc9bc5277"
  },
  {
   "n": 3,
   "ts": "2026-10-07T22:21:52+08:00",
   "kind": "change",
   "actor": "ZCode/DeepSeek Harness",
   "what": "记录本上线：只追加 JSONL + 自链哈希（prev_hash→hash）+ 每日扫描（文件指纹现算：扫到/未变/新增/改动/删除）—— 重启后大模型读 state/logbook-digest.md 就知道上一轮做过什么",
   "where": [
    "tools/codex-scripts/logbook.py",
    "holo_pet_w3/logbook/index.html",
    "holo_pet_w3/logbook/logbook-data.js",
    "state/logbook.jsonl"
   ],
   "hash": "sha256:cd897f739df232e",
   "prev": "sha256:9f59d64dce9aabb"
  },
  {
   "n": 4,
   "ts": "2026-10-07T22:21:53+08:00",
   "kind": "change",
   "actor": "ZCode/子代理",
   "what": "项目蓝图可视化面板上线：边界环/DAG/树登记表/窗口登记表/Phase 0-5/风险 R/故障 F-Q/装机回执，全部现算自真源",
   "where": [
    "tools/codex-scripts/blueprint-feed.py",
    "holo_pet_w3/blueprint/index.html",
    "holo_pet_w3/blueprint/blueprint-data.js"
   ],
   "hash": "sha256:a2e119d9ddcf8e9",
   "prev": "sha256:cd897f739df232e"
  },
  {
   "n": 5,
   "ts": "2026-10-07T22:22:17+08:00",
   "kind": "scan",
   "actor": "logbook.py scan",
   "what": "本轮改动扫描：扫 148699 个文件 · 未变 148686 · 改动 6 · 新增 7 · 删除 0",
   "where": [
    "."
   ],
   "hash": "sha256:596fe909b306fba",
   "prev": "sha256:a2e119d9ddcf8e9"
  },
  {
   "n": 6,
   "ts": "2026-10-07T22:33:00+08:00",
   "kind": "deliver",
   "actor": "ZCode/DeepSeek Harness",
   "what": "DSH 自接入**端到端实测通过**：真起 dsh web → 18.3s 拿到就绪行 → 请求得 303 → 跟到 200 · 28330 字节 · 标题 DeepSeek Harness。实测同时逼出并修掉两个真缺陷：① 3080 被孤儿占用时改走 --port 0 另起（否则永远接不上）② shell:true 下 kill() 只杀 cmd 外壳、dsh 变孤儿 ⇒ 改 taskkill /T 收整棵进程树",
   "where": [
    "holo_pet_w3/shell/dsh-launch.cjs",
    "holo_pet_w3/tests/test_dsh_launch.cjs"
   ],
   "hash": "sha256:0323802dffe3fd7",
   "prev": "sha256:596fe909b306fba"
  },
  {
   "n": 7,
   "ts": "2026-10-07T22:42:48+08:00",
   "kind": "deliver",
   "actor": "ZCode",
   "what": "桌面成品交付：新版 portable 已拷到桌面，旧的 20261004 版改名保留未删；装机回执 9/9 绿，包内 12 扇窗含新增的记录本与蓝图",
   "where": [
    "C:/Users/ADMIN/Desktop/GBT小土豆V8 0.1.0.exe"
   ],
   "hash": "sha256:c81a32fec33365e",
   "prev": "sha256:0323802dffe3fd7"
  },
  {
   "n": 8,
   "ts": "2026-10-07T22:43:26+08:00",
   "kind": "scan",
   "actor": "logbook.py scan",
   "what": "交付后扫描：扫 148790 个文件 · 未变 148679 · 改动 20 · 新增 91 · 删除 0",
   "where": [
    "."
   ],
   "hash": "sha256:f22029aabc4853d",
   "prev": "sha256:c81a32fec33365e"
  },
  {
   "n": 9,
   "ts": "2026-10-07T23:01:50+08:00",
   "kind": "change",
   "actor": "ZCode/子代理",
   "what": "云插件独立页 + 可视化连接状态面板上线：现役真源 mesh.json 的 10 位插件逐位成卡（端点/op/互绑/三态）+ 拓扑与 10x10 矩阵按三态着色 + 90 条连接明细带原始 status；真探测 10/10 通；发请求前校 host（回环/私网/元数据地址一律不发）",
   "where": [
    "holo_pet_w3/cloud-plugins/index.html",
    "holo_pet_w3/cloud-status/index.html",
    "state/cloud-status.json"
   ],
   "hash": "sha256:8f218599c6fefdb",
   "prev": "sha256:f22029aabc4853d"
  },
  {
   "n": 10,
   "ts": "2026-10-07T23:39:54+08:00",
   "kind": "change",
   "actor": "子代理+ZCode",
   "what": "云插件独立页与连接状态面板上线并登记成窗；真探测 10/10 通，发请求前校 host（回环私网元数据地址一律不发）",
   "where": [
    "holo_pet_w3/cloud-plugins/index.html",
    "holo_pet_w3/cloud-status/index.html"
   ],
   "hash": "sha256:de209e682f9b118",
   "prev": "sha256:8f218599c6fefdb"
  },
  {
   "n": 11,
   "ts": "2026-10-07T23:53:57+08:00",
   "kind": "change",
   "actor": "ZCode",
   "what": "Logo 修正：托盘图标从代码现画的方块改成品牌真图（assets/brand/logo-potato-32.png 的逐字节复制，随包分发），并加单测钉住同字节；托盘提示改为「点一下显示/隐藏全部窗」",
   "where": [
    "holo_pet_w3/build/tray-logo-32.png",
    "holo_pet_w3/tests/test_tray_logo.cjs"
   ],
   "hash": "sha256:0133340d1f0b292",
   "prev": "sha256:de209e682f9b118"
  },
  {
   "n": 12,
   "ts": "2026-10-07T23:54:19+08:00",
   "kind": "change",
   "actor": "ZCode",
   "what": "面板两处真缺陷修掉：① 左栏 5 个页面（总控台/工作空间首页/页面卡库/Bento工作台/触手3D全景）相对路径写错（../assets 实为 ../../holo_pet/assets），点进去是空白 ⇒ 已改对并加 extraResources 随包分发 ② 面板桥 8765 掉线（APP 里显示「离线」）⇒ 重新拉起 holo_pet/launch_panel.py，运行中的 APP 已重新连上",
   "where": [
    "holo_pet_w3/panel/index.html",
    "holo_pet_w3/package.json"
   ],
   "hash": "sha256:52752d8dbb905f3",
   "prev": "sha256:0133340d1f0b292"
  },
  {
   "n": 13,
   "ts": "2026-10-08T00:12:56+08:00",
   "kind": "change",
   "actor": "ZCode",
   "what": "免费数据库编队上线（7 库）：Neon/TiDB/Turso 当主（不因闲置暂停 + 有回滚面），D1/Upstash/Supabase/R2 当备；含指向表（哪类数据走哪库·单一写主）与每库存什么；额度与稳定性逐条带官方出处（取证 2026-10-07）；status 全为未开通",
   "where": [
    "deploy/cloud-10/db-fleet.json",
    "holo_pet_w3/db-fleet/index.html",
    "docs/免费数据库编队-设计.md"
   ],
   "hash": "sha256:809086c3ede9d33",
   "prev": "sha256:52752d8dbb905f3"
  }
 ]
};
