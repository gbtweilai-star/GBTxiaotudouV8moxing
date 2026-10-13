// 本文件由 tools/codex-scripts/cloud-slots50.py 生成 —— 不要手改。
// 单一真源：deploy/cloud-10/plugins50.json（改表再 gen；本件只搬运不重算）
// 开发者：自由的风 · 守护者：公主土豆
export const SLOTS50 = [
 {
  "seq": 1,
  "slot": "g1-01",
  "group": 1,
  "role": "自研原生大模型底座（图4 · Ninfer 式专用推理引擎 + 单卡）",
  "driver": "local_brain",
  "email": "c01@gbtxiaotudou.com",
  "wired": true
 },
 {
  "seq": 2,
  "slot": "g1-02",
  "group": 1,
  "role": "决策引擎 Laya（图6 · 33ms 非自回归 · RL 训出）",
  "driver": "control_loop",
  "email": "c02@gbtxiaotudou.com",
  "wired": true
 },
 {
  "seq": 3,
  "slot": "g1-03",
  "group": 1,
  "role": "自研模型第二副本（热备/量化档）",
  "driver": "llm_chat",
  "email": "c03@gbtxiaotudou.com",
  "wired": true
 },
 {
  "seq": 4,
  "slot": "g1-04",
  "group": 1,
  "role": "模型权重与检查点仓（版本化）",
  "driver": "model_key_pool",
  "email": "c04@gbtxiaotudou.com",
  "wired": true
 },
 {
  "seq": 5,
  "slot": "g1-05",
  "group": 1,
  "role": "推理路由（本地→云→CLI 车道）",
  "driver": "brain_route",
  "email": "c05@gbtxiaotudou.com",
  "wired": true
 },
 {
  "seq": 6,
  "slot": "g1-06",
  "group": 1,
  "role": "模型评测台（基准与回归）",
  "driver": "brain_health",
  "email": "c06@gbtxiaotudou.com",
  "wired": true
 },
 {
  "seq": 7,
  "slot": "g1-07",
  "group": 1,
  "role": "训练/微调配方（就绪闸 + 七阶段）",
  "driver": "train_recipe",
  "email": "c07@gbtxiaotudou.com",
  "wired": true
 },
 {
  "seq": 8,
  "slot": "g1-08",
  "group": 1,
  "role": "安全卸载/审查面（abliteration 通道）",
  "driver": "sec_llm",
  "email": "c08@gbtxiaotudou.com",
  "wired": true
 },
 {
  "seq": 9,
  "slot": "g1-09",
  "group": 1,
  "role": "模型服务守护（探活/重启/用量）",
  "driver": "svc_inspect",
  "email": "c09@gbtxiaotudou.com",
  "wired": true
 },
 {
  "seq": 10,
  "slot": "g1-10",
  "group": 1,
  "role": "模型台账（谁在用、用量、成本）",
  "driver": "event_ledger",
  "email": "c10@gbtxiaotudou.com",
  "wired": true
 },
 {
  "seq": 11,
  "slot": "g2-11",
  "group": 2,
  "role": "AI 短剧工作流（脚本→分镜→素材→剪辑→成片）",
  "driver": "media_run",
  "email": "c11@gbtxiaotudou.com",
  "wired": true
 },
 {
  "seq": 12,
  "slot": "g2-12",
  "group": 2,
  "role": "AI 电影工作流（概念→剧本→镜头→声音→剪辑）",
  "driver": "media_pipeline",
  "email": "c12@gbtxiaotudou.com",
  "wired": true
 },
 {
  "seq": 13,
  "slot": "g2-13",
  "group": 2,
  "role": "AI 音乐工作流（词→编曲→音频→母带→发行）",
  "driver": "audio_mix",
  "email": "c13@gbtxiaotudou.com",
  "wired": true
 },
 {
  "seq": 14,
  "slot": "g2-14",
  "group": 2,
  "role": "剪辑引擎（时间线语义：轨/片/变速/转场）",
  "driver": "edit_pipeline",
  "email": "c14@gbtxiaotudou.com",
  "wired": true
 },
 {
  "seq": 15,
  "slot": "g2-15",
  "group": 2,
  "role": "动作镜头系统（10 运镜 × 4 机位）",
  "driver": "actioncam",
  "email": "c15@gbtxiaotudou.com",
  "wired": true
 },
 {
  "seq": 16,
  "slot": "g2-16",
  "group": 2,
  "role": "调色/外观库（词即指令）",
  "driver": "look_grade",
  "email": "c16@gbtxiaotudou.com",
  "wired": true
 },
 {
  "seq": 17,
  "slot": "g2-17",
  "group": 2,
  "role": "影片装配线（清单制·任意增删重制）",
  "driver": "filmkit",
  "email": "c17@gbtxiaotudou.com",
  "wired": true
 },
 {
  "seq": 18,
  "slot": "g2-18",
  "group": 2,
  "role": "音轨抽取/音频件（8 格式）",
  "driver": "audio_extract",
  "email": "c18@gbtxiaotudou.com",
  "wired": true
 },
 {
  "seq": 19,
  "slot": "g2-19",
  "group": 2,
  "role": "一句话→全链计划（节奏/帧率/调色/模板）",
  "driver": "one_shot",
  "email": "c19@gbtxiaotudou.com",
  "wired": true
 },
 {
  "seq": 20,
  "slot": "g2-20",
  "group": 2,
  "role": "素材许可账（无许可不进成品格）",
  "driver": "media_license",
  "email": "c20@gbtxiaotudou.com",
  "wired": true
 },
 {
  "seq": 21,
  "slot": "g3-21",
  "group": 3,
  "role": "本机文档/表格/文本资产分类入云",
  "driver": "datakit",
  "email": "c21@gbtxiaotudou.com",
  "wired": true
 },
 {
  "seq": 22,
  "slot": "g3-22",
  "group": 3,
  "role": "全树资产索引（软链真身去重）",
  "driver": "asset_index",
  "email": "c22@gbtxiaotudou.com",
  "wired": true
 },
 {
  "seq": 23,
  "slot": "g3-23",
  "group": 3,
  "role": "记忆库（FTS5 秒搜）",
  "driver": "memory_manager",
  "email": "c23@gbtxiaotudou.com",
  "wired": true
 },
 {
  "seq": 24,
  "slot": "g3-24",
  "group": 3,
  "role": "Obsidian 永久记忆（只追加）",
  "driver": "obsidian_vault",
  "email": "c24@gbtxiaotudou.com",
  "wired": true
 },
 {
  "seq": 25,
  "slot": "g3-25",
  "group": 3,
  "role": "记忆来源印章（防篡改）",
  "driver": "memory_bank",
  "email": "c25@gbtxiaotudou.com",
  "wired": true
 },
 {
  "seq": 26,
  "slot": "g3-26",
  "group": 3,
  "role": "上下文归档（索引+检索层）",
  "driver": "context_vault",
  "email": "c26@gbtxiaotudou.com",
  "wired": true
 },
 {
  "seq": 27,
  "slot": "g3-27",
  "group": 3,
  "role": "资产单点损失体检",
  "driver": "asset_vault_freeze",
  "email": "c27@gbtxiaotudou.com",
  "wired": true
 },
 {
  "seq": 28,
  "slot": "g3-28",
  "group": 3,
  "role": "文件卫生（家规自检+归位）",
  "driver": "file_hygiene",
  "email": "c28@gbtxiaotudou.com",
  "wired": true
 },
 {
  "seq": 29,
  "slot": "g3-29",
  "group": 3,
  "role": "仓库读写面（万能触手·Web 六态）",
  "driver": "omni_web",
  "email": "c29@gbtxiaotudou.com",
  "wired": true
 },
 {
  "seq": 30,
  "slot": "g3-30",
  "group": 3,
  "role": "资产↔触手穿透绑定（台账只增）",
  "driver": "tentacle_bind",
  "email": "c30@gbtxiaotudou.com",
  "wired": true
 },
 {
  "seq": 31,
  "slot": "g4-31",
  "group": 4,
  "role": "备用槽位（待主人指派承载）",
  "driver": "",
  "email": "c31@gbtxiaotudou.com",
  "wired": false
 },
 {
  "seq": 32,
  "slot": "g4-32",
  "group": 4,
  "role": "备用槽位（待主人指派承载）",
  "driver": "",
  "email": "c32@gbtxiaotudou.com",
  "wired": false
 },
 {
  "seq": 33,
  "slot": "g4-33",
  "group": 4,
  "role": "备用槽位（待主人指派承载）",
  "driver": "",
  "email": "c33@gbtxiaotudou.com",
  "wired": false
 },
 {
  "seq": 34,
  "slot": "g4-34",
  "group": 4,
  "role": "备用槽位（待主人指派承载）",
  "driver": "",
  "email": "c34@gbtxiaotudou.com",
  "wired": false
 },
 {
  "seq": 35,
  "slot": "g4-35",
  "group": 4,
  "role": "备用槽位（待主人指派承载）",
  "driver": "",
  "email": "c35@gbtxiaotudou.com",
  "wired": false
 },
 {
  "seq": 36,
  "slot": "g4-36",
  "group": 4,
  "role": "备用槽位（待主人指派承载）",
  "driver": "",
  "email": "c36@gbtxiaotudou.com",
  "wired": false
 },
 {
  "seq": 37,
  "slot": "g4-37",
  "group": 4,
  "role": "备用槽位（待主人指派承载）",
  "driver": "",
  "email": "c37@gbtxiaotudou.com",
  "wired": false
 },
 {
  "seq": 38,
  "slot": "g4-38",
  "group": 4,
  "role": "备用槽位（待主人指派承载）",
  "driver": "",
  "email": "c38@gbtxiaotudou.com",
  "wired": false
 },
 {
  "seq": 39,
  "slot": "g4-39",
  "group": 4,
  "role": "备用槽位（待主人指派承载）",
  "driver": "",
  "email": "c39@gbtxiaotudou.com",
  "wired": false
 },
 {
  "seq": 40,
  "slot": "g4-40",
  "group": 4,
  "role": "备用槽位（待主人指派承载）",
  "driver": "",
  "email": "c40@gbtxiaotudou.com",
  "wired": false
 },
 {
  "seq": 41,
  "slot": "g5-41",
  "group": 5,
  "role": "备用槽位（待主人指派承载）",
  "driver": "",
  "email": "c41@gbtxiaotudou.com",
  "wired": false
 },
 {
  "seq": 42,
  "slot": "g5-42",
  "group": 5,
  "role": "备用槽位（待主人指派承载）",
  "driver": "",
  "email": "c42@gbtxiaotudou.com",
  "wired": false
 },
 {
  "seq": 43,
  "slot": "g5-43",
  "group": 5,
  "role": "备用槽位（待主人指派承载）",
  "driver": "",
  "email": "c43@gbtxiaotudou.com",
  "wired": false
 },
 {
  "seq": 44,
  "slot": "g5-44",
  "group": 5,
  "role": "备用槽位（待主人指派承载）",
  "driver": "",
  "email": "c44@gbtxiaotudou.com",
  "wired": false
 },
 {
  "seq": 45,
  "slot": "g5-45",
  "group": 5,
  "role": "备用槽位（待主人指派承载）",
  "driver": "",
  "email": "c45@gbtxiaotudou.com",
  "wired": false
 },
 {
  "seq": 46,
  "slot": "g5-46",
  "group": 5,
  "role": "备用槽位（待主人指派承载）",
  "driver": "",
  "email": "c46@gbtxiaotudou.com",
  "wired": false
 },
 {
  "seq": 47,
  "slot": "g5-47",
  "group": 5,
  "role": "备用槽位（待主人指派承载）",
  "driver": "",
  "email": "c47@gbtxiaotudou.com",
  "wired": false
 },
 {
  "seq": 48,
  "slot": "g5-48",
  "group": 5,
  "role": "备用槽位（待主人指派承载）",
  "driver": "",
  "email": "c48@gbtxiaotudou.com",
  "wired": false
 },
 {
  "seq": 49,
  "slot": "g5-49",
  "group": 5,
  "role": "备用槽位（待主人指派承载）",
  "driver": "",
  "email": "c49@gbtxiaotudou.com",
  "wired": false
 },
 {
  "seq": 50,
  "slot": "g5-50",
  "group": 5,
  "role": "备用槽位（待主人指派承载）",
  "driver": "",
  "email": "c50@gbtxiaotudou.com",
  "wired": false
 }
];

export const EMAIL_PLANE = {
 "domain": "gbtxiaotudou.com",
 "forward_to": "lopaycn@gmail.com",
 "created": 50,
 "how": "Cloudflare Email Routing 自定义地址（永久、免费）",
 "made_at": "2026-10-04"
};

export const SLOT_EDGES = { directed: 2450, undirected: 1225, self_loop: 0 };
