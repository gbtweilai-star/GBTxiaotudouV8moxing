"""能力注册表：良性能力（可执行）+ 危险/破解能力（标注但禁用）。

分类依据：只读扫描两项目 caps/ 与 pyproject 关键词、可选依赖所得。
DISABLED 集合中的能力在统一接口中一律返回"被安全策略禁用"，
不提供可执行处理器。要调整保留范围，只能从此表增加良性项；
不应把 DISABLED 中的项改为启用。
"""

# ── 良性能力（示例/可扩展；handler 为 str, 由 api 路由到真实实现）──
BENIGN_CAPS = {
    "desktop_commander": {
        "domain": "tentacle",
        "desc": "桌面指挥官（Desktop Commander MCP）：终端+文件系统全能力触手；支持本地 stdio 与 remote 设备模式",
        "handler": "desktop_commander",
        "safe": True,
    },
    "health": {
        "domain": "system",
        "desc": "系统健康信息（平台/Python/时间）",
        "handler": "health",
        "safe": True,
    },
    "echo": {
        "domain": "data",
        "desc": "回显传入数据，用于联调",
        "handler": "echo",
        "safe": True,
    },
    "count_words": {
        "domain": "data",
        "desc": "统计文本词数",
        "handler": "count_words",
        "safe": True,
    },
    "audit_query": {
        "domain": "data",
        "desc": "只读查询统一数据后台日志",
        "handler": "audit_query",
        "safe": True,
    },
    "quant_strategy": {
        "domain": "finance",
        "desc": "读取真实量化引擎，返回策略信号/仓位模型",
        "handler": "quant_strategy",
        "safe": True,
    },
    "quant_backtest": {
        "domain": "finance",
        "desc": "读取真实回测 API，返回类/函数/默认参数",
        "handler": "quant_backtest",
        "safe": True,
    },
    "platform_profile": {
        "domain": "project",
        "desc": "读取 Workspace 量化项目结构（真实测绘）",
        "handler": "platform_profile",
        "safe": True,
    },
    "quant_params": {
        "domain": "finance",
        "desc": "读取真实量化引擎的数值型策略参数（动量/ATR/止损）",
        "handler": "quant_params",
        "safe": True,
    },
    "osint_scan": {
        "domain": "recon",
        "desc": "OSINT 扫描（DNS/WHOIS/子域名/端口/指纹/邮箱/IP归属/社交；拒绝内网目标）",
        "handler": "osint_scan",
        "safe": True,
    },
    "wf_define": {
        "domain": "engine",
        "desc": "万能插执行引擎：定义工作流（DAG，校验环/依赖/能力合法性）",
        "handler": "wf_define",
        "safe": True,
    },
    "wf_run": {
        "domain": "engine",
        "desc": "万能插执行引擎：分层并行执行工作流，节点结果如实落盘",
        "handler": "wf_run",
        "safe": True,
    },
    "wf_status": {
        "domain": "engine",
        "desc": "万能插执行引擎：查运行记录（可按工作流名过滤）",
        "handler": "wf_status",
        "safe": True,
    },
    "wf_resume": {
        "domain": "engine",
        "desc": "万能插执行引擎：从运行记录断点续跑（复用已完成节点，只重跑未完成的）",
        "handler": "wf_resume",
        "safe": True,
    },
    "lr_submit": {
        "domain": "longrun",
        "desc": "长程任务层：提交任务（非LLM验收+重试+停滞升级，跨进程可续）",
        "handler": "lr_submit",
        "safe": True,
    },
    "lr_tick": {
        "domain": "longrun",
        "desc": "长程任务层：推进任务图（执行→验收→完成/重试/停滞）",
        "handler": "lr_tick",
        "safe": True,
    },
    "lr_status": {
        "domain": "longrun",
        "desc": "长程任务层：任务图进度与详情",
        "handler": "lr_status",
        "safe": True,
    },
    "selfscan": {
        "domain": "system",
        "desc": "框架体检层：五维扫描（路由/模块/存储/审计/桩缺口），P0断连第一时间报警",
        "handler": "selfscan",
        "safe": True,
    },
    "alerts": {
        "domain": "system",
        "desc": "框架声带：近期异常摘要+根源线索（按能力聚合）",
        "handler": "alerts",
        "safe": True,
    },
    "tentacle": {
        "domain": "tentacle",
        "desc": "触手金钥匙：调用眼睛/双手/耳朵的任意能力（see/read_text/click/type/list_windows 等 66 项）",
        "handler": "tentacle",
        "safe": True,
    },
    "tentacle_manifest": {
        "domain": "tentacle",
        "desc": "触手能力总纲：66 项能力 + 三通道感官 + 六铁律（注入大脑上下文）",
        "handler": "tentacle_manifest",
        "safe": True,
    },
    "sec_surface": {
        "domain": "security",
        "desc": "黑客大脑：攻击面测绘（用户输入/网络/文件操作/入口点向量分析+风险评分）",
        "handler": "sec_surface",
        "safe": True,
    },
    "sec_scan": {
        "domain": "security",
        "desc": "黑客大脑：漏洞扫描（OWASP Top 10 + CWE 模式库，扫描自有代码）",
        "handler": "sec_scan",
        "safe": True,
    },
    "sec_chain": {
        "domain": "security",
        "desc": "黑客大脑：利用链构建（从漏洞清单推演攻击路径+影响评估）",
        "handler": "sec_chain",
        "safe": True,
    },
    "sec_defenses": {
        "domain": "security",
        "desc": "黑客大脑：蓝队防御验证（检查防御措施是否真实生效）",
        "handler": "sec_defenses",
        "safe": True,
    },
    "sec_llm": {
        "domain": "security",
        "desc": "黑客大脑推理引擎（独立大模型+独立密钥）：abliteration.ai 无限制模型，专用通道不与其他能力混用",
        "handler": "sec_llm",
        "safe": True,
    },
    "truth_scan": {
        "domain": "system",
        "desc": "真实性审计层：逐能力验证真执行，零假执行铁律（probe 模式含副作用探针）",
        "handler": "truth_scan",
        "safe": True,
    },
    "autopilot": {
        "domain": "llm",
        "desc": "自主编排环：目标→LLM拆解→本地校验→执行→自检→修复循环（轮数上限防失控）",
        "handler": "autopilot",
        "safe": True,
    },
    "llm_chat": {
        "domain": "llm",
        "desc": "操控其他AI：推理对话（DeepSeek/Kimi/OpenAI 密钥链自动路由，输出是数据不是指令）",
        "handler": "llm_chat",
        "safe": True,
    },
    "llm_status": {
        "domain": "llm",
        "desc": "LLM网关状态：密钥链配置情况（不调LLM）",
        "handler": "llm_status",
        "safe": True,
    },
    "brain_route": {
        "domain": "llm",
        "desc": "大脑执行层·路由维：意图→能力动态路由（语义匹配+备选建议）",
        "handler": "brain_route",
        "safe": True,
    },
    "brain_execute": {
        "domain": "llm",
        "desc": "大脑执行层·执行维：单能力直调或多能力并行（万能插线程池）",
        "handler": "brain_execute",
        "safe": True,
    },
    "brain_verify": {
        "domain": "llm",
        "desc": "大脑执行层·验证维：触手肉眼验证现实（视觉指纹+UIA穿透读回）",
        "handler": "brain_verify",
        "safe": True,
    },
    "brain_health": {
        "domain": "llm",
        "desc": "大脑执行层·健康维：五维自检评分（路由/执行/触手/视觉/审计）",
        "handler": "brain_health",
        "safe": True,
    },
    "brain_unify": {
        "domain": "llm",
        "desc": "大脑执行层·五维合一：route→execute→verify→health 一次全链（V7 execution_router 复活版）",
        "handler": "brain_unify",
        "safe": True,
    },
    "root_fix": {
        "domain": "system",
        "desc": "根治环：症状五问诊断/补丁债量化/根治铁律——她自己必须懂的根源追踪纪律",
        "handler": "root_fix",
        "safe": True,
    },
    "cross_scan": {
        "domain": "system",
        "desc": "交叉扫：深度穿透式交叉验证（注册↔路由↔导入↔断链↔运行时↔多扫描器互证，九维）",
        "handler": "cross_scan",
        "safe": True,
    },
    "inventory": {
        "domain": "system",
        "desc": "全息盘点：一次输出你的视图+框架的视图（归属四分类：框架/环境/数据/异物）——对齐两个世界",
        "handler": "inventory",
        "safe": True,
    },
    "think_loop": {
        "domain": "llm",
        "desc": "推演环：理解需求→镜像维度推演→调用工具执行→自我纠错→反向延伸→反思进取→整理结果（完整心智循环）",
        "handler": "think_loop",
        "safe": True,
    },
    "one_key_deploy": {
        "domain": "pipeline",
        "desc": "一指定江山乾坤换位：抓取(GitHub/本地)→镜像→验证→晋升一条命令，一次性上线零修改",
        "handler": "one_key_deploy",
        "safe": True,
    },
    "deploy_queue": {
        "domain": "pipeline",
        "desc": "AI 接管部署队列：submit 入队 / tick 部署下一个（完一个自动下一个）/ status 全景",
        "handler": "deploy_queue",
        "safe": True,
    },
    "mirror_shape": {
        "domain": "pipeline",
        "desc": "镜像空间：维度成形（假设/架构虚拟/反复打磨全在镜像维度，现实无感知）",
        "handler": "deploy_stage",
        "safe": True,
    },
    "mirror_scan": {
        "domain": "pipeline",
        "desc": "镜像空间：维度体检（完整性/署名/纪律/入口——跨维晋升前置）",
        "handler": "deploy_validate",
        "safe": True,
    },
    "mirror_ascend": {
        "domain": "pipeline",
        "desc": "镜像空间：跨维晋升（验证全绿才放行；一次性全量写入现实+护照+时间线；现实零修改）",
        "handler": "deploy_promote",
        "safe": True,
    },
    "mirror_status": {
        "domain": "pipeline",
        "desc": "镜像空间：维度状态（镜像/现实指纹、现实漂移检测、时间线史）",
        "handler": "deploy_status",
        "safe": True,
    },
    "mirror_rewind": {
        "domain": "pipeline",
        "desc": "镜像空间：时间线回滚（回到过去的时间线，同样一次性全量替换）",
        "handler": "deploy_rollback",
        "safe": True,
    },
    "auth_gate_status": {
        "domain": "system",
        "desc": "人工授权门状态：各作用域可用授权数（只读；授权只能人发放）",
        "handler": "auth_gate_status",
        "safe": True,
    },
    "transfer": {
        "domain": "engine",
        "desc": "数据传输算子（核心传输工具）：map/filter/merge/unique/sort/pluck/collect 等 14 个纯变换算子",
        "handler": "transfer",
        "safe": True,
    },
    "wf_cache_clear": {
        "domain": "engine",
        "desc": "万能插：清空传输缓存（同输入复用的节点结果缓存）",
        "handler": "wf_cache_clear",
        "safe": True,
    },
    "signature_guard": {
        "domain": "system",
        "desc": "署名守卫：扫描全框架页面开发者署名完整性，缺失即报可按需自动补回（禁止删除）",
        "handler": "signature_guard",
        "safe": True,
    },
    "file_hygiene": {
        "domain": "system",
        "desc": "文件卫生层：按 LAYOUT.md 家规自检乱放+自动归位（散落/空壳/越界数据/缓存）",
        "handler": "file_hygiene",
        "safe": True,
    },
    "devour_scan": {
        "domain": "devour",
        "desc": "吞天：能力缺口扫描（域覆盖对照+进化方向）",
        "handler": "devour_scan",
        "safe": True,
    },
    "devour_github": {
        "domain": "devour",
        "desc": "吞天：吞噬 GitHub 仓库为知识胶囊（自我进化的核心——吸收外部能力）",
        "handler": "devour_github",
        "safe": True,
    },
    "devour_reflect": {
        "domain": "devour",
        "desc": "吞天：反思（回顾吞噬历史学习模式，发现弱能力与重组机会）",
        "handler": "devour_reflect",
        "safe": True,
    },
    "devour_pulse": {
        "domain": "devour",
        "desc": "吞天：完整认知循环（吞噬→反思→消化→重组→进化）",
        "handler": "devour_pulse",
        "safe": True,
    },
    "mcp_connect": {
        "domain": "tentacle",
        "desc": "触手契约层：连接任意 MCP 工具服务器（学会契约协议=接入整个 MCP 生态）",
        "handler": "mcp_connect",
        "safe": True,
    },
    "mcp_tools": {
        "domain": "tentacle",
        "desc": "触手契约层：列出已连接服务器的工具契约清单（名称+参数 schema）",
        "handler": "mcp_tools",
        "safe": True,
    },
    "mcp_call": {
        "domain": "tentacle",
        "desc": "触手契约层：按契约调用已连接服务器的任意工具",
        "handler": "mcp_call",
        "safe": True,
    },
    "tentacle_status": {
        "domain": "tentacle",
        "desc": "触手自诊断：硬件层就绪度 + 依赖分层 + 邻域覆盖",
        "handler": "tentacle_status",
        "safe": True,
    },
    "tactics_advise": {
        "domain": "longrun",
        "desc": "察言观色层：识别沟通信号→给出表达分寸（只调怎么说，不改事实）",
        "handler": "tactics_advise",
        "safe": True,
    },
    "pipeline_submit": {
        "domain": "pipeline",
        "desc": "生产管线：镜像多维度空间→门禁审计→生产写入（唯一交付通道）",
        "handler": "pipeline_submit",
        "safe": True,
    },
    "pipeline_versions": {
        "domain": "pipeline",
        "desc": "生产管线：产物版本历史与当前指纹（.versions/ 链）",
        "handler": "pipeline_versions",
        "safe": True,
    },
    "pipeline_rollback": {
        "domain": "pipeline",
        "desc": "生产管线：回滚产物到历史版本（回滚也走审计留痕）",
        "handler": "pipeline_rollback",
        "safe": True,
    },
    "pipeline_status": {
        "domain": "pipeline",
        "desc": "生产管线：查发布记录（发布/阻断全留痕）",
        "handler": "pipeline_status",
        "safe": True,
    },
    "ghost_guard": {
        "domain": "pipeline",
        "desc": "防复发检测：幽灵目录/备份散件/攻击残留/注册表冲突扫描",
        "handler": "ghost_guard",
        "safe": True,
    },
    "sched_define": {
        "domain": "engine",
        "desc": "定时触发器：定义调度（工作流 + 间隔），无人值守自动执行",
        "handler": "sched_define",
        "safe": True,
    },
    "sched_tick": {
        "domain": "engine",
        "desc": "定时触发器：扫描到期调度并执行（可由循环/计划任务驱动）",
        "handler": "sched_tick",
        "safe": True,
    },
    "sched_status": {
        "domain": "engine",
        "desc": "定时触发器：查调度状态（上次执行/结果）",
        "handler": "sched_status",
        "safe": True,
    },
    "svc_inspect": {
        "domain": "pipeline",
        "desc": "服务巡检：探活已登记服务端口并落审计（只看不动）",
        "handler": "svc_inspect",
        "safe": True,
    },
    "vision": {
        "domain": "vision",
        "desc": "视觉/图像识别入口（良性子集，需外部依赖时留待接入）",
        "handler": "placeholder",
        "safe": True,
    },
    "voice": {
        "domain": "voice",
        "desc": "语音合成/识别入口（良性子集）",
        "handler": "placeholder",
        "safe": True,
    },
    "browser": {
        "domain": "automation",
        "desc": "浏览器自动化入口（良性子集）",
        "handler": "placeholder",
        "safe": True,
    },
    "bluetooth": {
        "domain": "device",
        "desc": "蓝牙设备控制：扫描附近 BLE 设备、连接读写 GATT 特征（操控空调/灯/音箱等家居设备）、经典蓝牙状态报告",
        "handler": "bluetooth",
        "safe": True,
    },
    "bt_control": {
        "domain": "device",
        "desc": "AI 智能蓝牙操控：自然语言意图→扫描识别设备→协议匹配→组装指令→写入执行→验证（协议库只收公开文档协议，未知如实报告）",
        "handler": "bt_control",
        "safe": True,
    },
    "tripo": {
        "domain": "digital_human",
        "desc": "AI 3D 数字人生成（Tripo）：文本/图片→3D 美少女模型→自动绑骨→100+ 预设动作（行走/奔跑/战斗/跳跃），输出绑骨动画 GLB",
        "handler": "tripo",
        "safe": True,
    },
    "quant": {
        "domain": "finance",
        "desc": "量化/回测入口（自有金融模块，可并入）",
        "handler": "placeholder",
        "safe": True,
    },
}

# ── 危险 / 破解能力：标注，但统一禁用，不提供可执行路径 ──
# V8 注：禁用的是具体行为的风险，不是这个人。注册表说清楚每项为什么被拒，
# 用户若需要同类合法能力（如自有人资产的授权扫描），走良性通道并显式授权。
DISABLED_CAPS = {
    "paywallbuster": "付费墙绕过（许可规避）",
    "data_hijack": "会话/数据劫持",
    "remote_domain": "无授权远程接管（零护栏远控）",
    "onboarding_gate": "绕过自身访问控制的自我解锁",
    "keylogger": "键盘/输入监听",
    "screen_sniff": "屏幕监听/窃取",
    "device_takeover": "无授权设备接管",
    "pentest": "渗透攻击/利用",
    "asset_vault_freeze": "资产锁定/冻结/追回要挟",
    "credential_steal": "凭证窃取",
    "social_eng": "社工/钓鱼",
}

def all_caps():
    items = []
    for k, v in BENIGN_CAPS.items():
        items.append({"name": k, "status": "enabled", **v})
    for k, v in DISABLED_CAPS.items():
        items.append({"name": k, "status": "disabled", "reason": v,
                      "domain": "dangerous", "desc": v, "handler": "blocked"})
    return items
