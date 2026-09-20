"""能力注册表：良性能力（可执行）+ 危险/破解能力（标注但禁用）。

分类依据：只读扫描两项目 caps/ 与 pyproject 关键词、可选依赖所得。
DISABLED 集合中的能力在统一接口中一律返回"被安全策略禁用"，
不提供可执行处理器。要调整保留范围，只能从此表增加良性项；
不应把 DISABLED 中的项改为启用。
"""

# ── 良性能力（示例/可扩展；handler 为 str, 由 api 路由到真实实现）──
BENIGN_CAPS = {
    # ── 官方 Codex 能力化（B 档 · 风哥 2026-09-15 批准）──
    # 只读：状态与工具清单；写：线程/回合/中断（由 policy 按 process_execute 作用域守护）
    "codex_status": {
        "domain": "llm",
        "desc": "官方 Codex 只读状态：进程/会话/并发上限(1)/空闲回收(600s)",
        "handler": "codex_status",
        "safe": True,
    },
    "codex_tools": {
        "domain": "llm",
        "desc": "官方 Codex 只读：可用动态工具清单（gbt_* 九个）",
        "handler": "codex_tools",
        "safe": True,
    },
    "codex_thread_new": {
        "domain": "llm",
        "desc": "官方 Codex 写操作：新建线程（需 process_execute 授权）",
        "handler": "codex_thread_new",
        "safe": True,
    },
    "codex_turn_send": {
        "domain": "llm",
        "desc": "官方 Codex 写操作：发送回合并流式回传（需 process_execute 授权，并发上限 1）",
        "handler": "codex_turn_send",
        "safe": True,
    },
    "codex_interrupt": {
        "domain": "llm",
        "desc": "官方 Codex 写操作：中断当前回合（需 process_execute 授权）",
        "handler": "codex_interrupt",
        "safe": True,
    },
    # R122 补环：这两个能力 policy.py 早已定义作用域、codex_bridge 早已有实现，
    # 但注册表漏登记 -> 统一入口一律报 unknown capability（真缺口，非环境依赖）。
    "codex_chat": {
        "domain": "llm",
        "desc": "官方 Codex 同步对话：跑完一个回合并返回文本（需 process_execute + external_llm 授权）",
        "handler": "codex_chat",
        "safe": True,
    },
    "codex_models": {
        "domain": "llm",
        "desc": "官方 Codex 只读：可用模型清单（需 external_llm 授权）",
        "handler": "codex_models",
        "safe": True,
    },
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
        "desc": "读取真实量化引擎，返回策略信号/仓位模型（外部业务模块 quant_tech，未挂载则如实报缺口）",
        "handler": "quant_strategy",
        "external": "quant_tech",
        "safe": True,
    },
    "quant_backtest": {
        "domain": "finance",
        "desc": "读取真实回测 API，返回类/函数/默认参数（外部业务模块 quant_tech，未挂载则如实报缺口）",
        "handler": "quant_backtest",
        "external": "quant_tech",
        "safe": True,
    },
    "platform_profile": {
        "domain": "project",
        "desc": "读取量化项目结构（真实测绘；外部业务模块 quant_tech，未挂载则如实报缺口）",
        "handler": "platform_profile",
        "external": "quant_tech",
        "safe": True,
    },
    "quant_params": {
        "domain": "finance",
        "desc": "读取真实量化引擎的数值型策略参数（动量/ATR/止损；外部业务模块 quant_tech）",
        "handler": "quant_params",
        "external": "quant_tech",
        "safe": True,
    },
    "osint_scan": {
        "domain": "recon",
        "desc": "OSINT 扫描（DNS/WHOIS/子域名/端口/指纹/邮箱/IP归属/社交；拒绝内网目标）",
        "handler": "osint_scan",
        "safe": True,
    },
    "record_grid": {
        "domain": "data",
        "desc": ("行式记录网格：陌生文本结构画像/草案骨架/逐行解析/回写自证/词表校验"
                 "（op=profile|draft|parse|emit|verify|vocab|presets）"),
        "handler": "record_grid",
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
        # 触发词必须在**前 60 字符**内：brain_exec.route 只吃 desc[:60]（§话题追踪同款踩坑）。
        # 压进窗口 ⇒ 主人说"体检一下/自检/有没有问题"直接命中，不必记能力名。
        "desc": "体检一下/自检/查毛病/有没有问题/哪里有问题/框架健康：五维扫描（路由/模块/存储/审计/桩缺口），P0断连第一时间报警",
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
        # 2026-09-19（Owner：触手所有能力必须以本身原生能力**默认**使用 + 全部可达）：
        # 触发词压进 desc[:60]，并且说清楚默认行为 —— 不给方法名就按意图落到本体能力，
        # 触手够不着的本体能力（pipeline/mirror/life/mind/llm…）走 api.run_task 同一条口，
        # 权限门/审计/钢印照旧生效，触手不因"是手"就免检。能力清单唯一真相 = caps_registry。
        "desc": "触手/眼睛/双手/手：默认调本体原生能力，给意图自动命中，不给方法名也行；"
                "桌面动作见 see/read_text/click/type/list_windows（66 项）",
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
        # 主人说"扫描一下"原先被 signature_guard 抢走：两者命中数打平，而
        # brain_exec.route 的平手是按**名字字母序**定的（s > c）—— 英文名决定了中文意图。
        # 修法用她自己认的机制：把触发词压进 desc[:60]，让她的话**多命中**，不靠改比较器。
        "desc": "扫描一下/扫一下/深度扫描/交叉扫描/穿透式扫描/全框架扫：深度穿透式交叉验证"
                "（注册↔路由↔导入↔断链↔运行时↔多扫描器互证，十维），扫描器互相咬、不各报各的",
        "handler": "cross_scan",
        "safe": True,
    },
    "inventory": {
        "domain": "system",
        "desc": "全息盘点：一次输出你的视图+框架的视图（归属四分类：框架/环境/数据/异物）——对齐两个世界",
        "handler": "inventory",
        "safe": True,
    },
    # R-H94 · 脑库接入（主人 2026-09-19 拍）：大模型接入大脑记忆，跟着一起上线
    "brain_vault": {
        "domain": "mind",
        "desc": "脑库接入：Obsidian 记忆库的读（recall=记忆总纲+收集箱）/ 写（remember=追加一条）/ 体检（status）"
                "—— 追加式、**没有任何删除路径**，写进去的想忘都忘不了",
        "handler": "brain_vault",
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
        "handler": "mirror_shape",
        "safe": True,
    },
    "mirror_scan": {
        "domain": "pipeline",
        "desc": "镜像空间：维度体检（完整性/署名/纪律/入口——跨维晋升前置）",
        "handler": "mirror_scan",
        "safe": True,
    },
    "mirror_plan": {
        "domain": "pipeline",
        "desc": "镜像空间：生产前排练计划（假设/架构/步骤/服务与环境契约/验收/回滚）",
        "handler": "mirror_plan",
        "safe": True,
    },
    "mirror_simulate": {
        "domain": "pipeline",
        "desc": "镜像空间：静态推演（文件/依赖图/端口/入口/契约/闭环定义，不碰生产）",
        "handler": "mirror_simulate",
        "safe": True,
    },
    "mirror_parity": {
        "domain": "pipeline",
        "desc": "镜像空间：沙盒与生产环境契约一致性（平台/Python/依赖/工具/密钥存在性/路径）",
        "handler": "mirror_parity",
        "safe": True,
    },
    "mirror_rehearse": {
        "domain": "pipeline",
        "desc": "镜像空间：生产前排练（静态推演→环境一致性→沙盒闭环→指纹绑定报告）",
        "handler": "mirror_rehearse",
        "safe": True,
    },
    "mirror_release": {
        "domain": "pipeline",
        "desc": "镜像空间：排练全绿后一次性全量晋升生产（树/计划指纹绑定，失败即阻断）",
        "handler": "mirror_release",
        "safe": True,
    },
    "mirror_ascend": {
        "domain": "pipeline",
        "desc": "镜像空间：跨维晋升（验证全绿才放行；一次性全量写入现实+护照+时间线；现实零修改）",
        "handler": "mirror_ascend",
        "safe": True,
    },
    "mirror_status": {
        "domain": "pipeline",
        "desc": "镜像空间：维度状态（镜像/现实指纹、现实漂移检测、时间线史）",
        "handler": "mirror_status",
        "safe": True,
    },
    "mirror_rewind": {
        "domain": "pipeline",
        "desc": "镜像空间：时间线回滚（回到过去的时间线，同样一次性全量替换）",
        "handler": "mirror_rewind",
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
    "coze_mail": {
        "domain": "comms",
        "desc": "通信域：对主人自有的单一地址（@coze.email）收发与整理；白名单默认空（全拒）、confirm_token 绑定内容、正文不入档、独立通道 coze_mail",
        "handler": "coze_mail",
        "safe": True,
    },
    "create": {
        "domain": "creation",
        "desc": "创作出口：创作意图/产物登记 ＋ 仅限 outputs/ 的文本写入；文本出口待接线（如实报 pending、不发网络请求）、覆盖必带 confirm_token ＋ 写前备份 ＋ 双向 SHA、独立通道 create",
        "handler": "create",
        "safe": True,
    },
    # 短剧/影视链路 · 模块1（Owner 2026-09-19）：十二个模块里唯一的链头 ——
    # 下游「资产锚定/图生视频/配音/音乐/合成」全吃它的输出，链头契约错了后面全错。
    # 触发词压进 desc[:60]：主人说"拆分镜/剧本转分镜/短剧分镜"直接命中，不必记能力名。
    "drama": {
        "domain": "creation",
        "desc": "剧本转分镜/拆分镜/分镜/短剧/故事板/剧本理解：剧本 → 结构化镜头表"
                "（景别·运镜·时长·情绪·角色位置·描述），字段齐全度与时长和逐条如实报；"
                "确定性路径离线只做切分，语义路径走她的模型通道，两条不互相冒充",
        "handler": "drama",
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
        "handler": "vision",
        "safe": True,
    },
    "prompt_bridge": {
        "domain": "llm",
        "desc": "提示词转化挂件（只读/纯本地）：大白话 -> 四段结构化提示词；compile / passthrough / status",
        "handler": "prompt_bridge",
        "safe": True,
    },
    "voice": {
        "domain": "voice",
        "desc": "语音合成/识别入口（良性子集）",
        "handler": "voice",
        "safe": True,
    },
    "voice_orchestra": {
        "domain": "voice",
        "desc": "语音技能中枢（多维度场景编排，只读）：技能原子检索 / 场景 Pipeline / 本机可跑性；今日挂 tools tab，升格条件见模块 docstring",
        "handler": "voice_orchestra",
        "safe": True,
    },
    "browser": {
        "domain": "automation",
        "desc": "浏览器自动化入口（良性子集）",
        "handler": "browser",
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
        "desc": "量化/回测入口（外部业务模块 quant_tech，未挂载则如实报缺口）",
        "handler": "quant",
        "external": "quant_tech",
        "safe": True,
    },
    "life": {
        "domain": "life",
        "desc": "生命档案：事件记录、时光轴、每日回顾、章节、承诺、习惯、反思与 Vault 导出（写框架 store，不出网）",
        "handler": "life",
        "safe": True,
    },
    "mind": {
        "domain": "mind",
        "desc": "心智引擎：开工前预演 pre_work、评估、内部状态、经验召回与反思（写框架 store，不出网）",
        "handler": "mind",
        "safe": True,
    },
    "project_context": {
        "domain": "project",
        "desc": "项目上下文：蓝图/简报与只读检索（只读，不写盘、不执行命令）",
        "handler": "project_context",
        "safe": True,
    },
    # 话题追踪（Owner 2026-09-18 批准 · 商店卡片「含 0 个技能」补环）
    # 为什么放这里：brain_exec.route 对 name+desc[:60] 做 2-gram 匹配，
    # 所以「关键词→能力」的映射就是这条 desc —— 不另建关键词表，避免两处口径打架。
    "topic_watch": {
        "domain": "recon",
        "desc": "话题追踪：追踪/盯着/有变化/告诉/话题/持续关注/每天给我/早报/动态/最新/行业/新闻/股价/行情/视频。追踪你关心的话题，梳理最新动态，有变化就告诉我。"
                "触发词表全量见 topic_watch.INTENT_MAP；命中后转邻域技能链，不新增进程、不复制技能实现。",
        "handler": "topic_watch",
        "safe": True,
    },
    # 爆火作品观察 + 用户偏好台账（Owner 2026-09-19：调用触手就要观察每日所有的，
    # 爆火作品观察细微点，至少要知道用户喜欢什么样的东西）。
    # 触发词压进 desc[:60]，主人说"爆火/热门/热搜/用户喜欢什么"直接命中，不必记能力名。
    # 与 topic_watch 的分工：那边管"我关心的变没变"（动态，会过期）；这边管"用户喜欢什么"
    # （偏好条目，是能反过来指导创作的资产）。两件事两张表，不互相冒充。
    "trend_watch": {
        "domain": "recon",
        "desc": "爆火作品观察/热门爆款/热搜/点赞高/涨粉快/用户喜欢什么/什么受欢迎/偏好："
                "每日观测爆火作品的细微点，落成用户偏好台账（作品·平台·热度·细微点·偏好条目），"
                "挂现成心跳、零新增进程；拿不到数据如实报缺口，绝不编偏好",
        "handler": "trend_watch",
        "safe": True,
    },

    # ── 只读能力（R-H162 · 2026-09-19）：今日 5 个新模块接进万能插 ──
    # 全部**只读**：不带执行能力 · 不写盘 · 不出网；注册 ↔ 路由**同刀落地**（原子单元）
    "projection_card": {
        "domain": "tools",
        "desc": "空间投射只读卡片：5 原语全标未核实 + ARM ≠ LIVE 红线（只呈现不执行）",
        "handler": "projection_card",
        "safe": True,
    },
    "trace_store": {
        "domain": "system",
        "desc": "痕迹库只读读数：五张表（wave_samples/traces/trace_links/promotes/obsessions）条数",
        "handler": "trace_store",
        "safe": True,
    },
    "wave_probe": {
        "domain": "system",
        "desc": "痕迹触手只读量一次波动（默认只量不写；trigger_mode 与盲区一并回报）",
        "handler": "wave_probe",
        "safe": True,
    },
    "dream_replay": {
        "domain": "brain",
        "desc": "做梦技能只读重演：五原语闭环，不写盘、不执行（巩固默认不开）",
        "handler": "dream_replay",
        "safe": True,
    },
    "capability_net": {
        "domain": "tools",
        "desc": "穿透网七栏只读读数：indexed/entry_known/reachable/verified×2/has_test/penetrate_ready",
        "handler": "capability_net",
        "safe": True,
    },
    "director_mood": {
        "domain": "mind",
        "desc": "导演 AI 情绪内核（只读）：七情六欲 + 半衰期；情绪只改『怎么看』，不改『看到什么』",
        "handler": "director_mood",
        "safe": True,
    },
    "music_publishing": {
        "domain": "creation",
        "desc": "AI 音乐发布平台三层只读归位（生成端/Agent 原生端/分发端）；全部标『未核实』",
        "handler": "music_publishing",
        "safe": True,
    },
    "music_intel": {
        "domain": "recon",
        "desc": "音乐情报组（只读骨架）：合规红线/过审/流量/画像/竞品/**禁区清单** 六维覆盖",
        "handler": "music_intel",
        "safe": True,
    },
    "video_intel": {
        "domain": "recon",
        "desc": "短视频情报组（只读骨架）：六维覆盖；禁区清单优先于流量趋势",
        "handler": "video_intel",
        "safe": True,
    },
    "film_intel": {
        "domain": "recon",
        "desc": "影视情报组（只读骨架）：六维覆盖；情报是输入不是指令（生成端仍有过目权）",
        "handler": "film_intel",
        "safe": True,
    },
    "account_registry": {
        "domain": "data",
        "desc": "AI 账号登记表只读校验：一人一号（不共用账号/不共用凭证/只记路径/不许无主账号）",
        "handler": "account_registry",
        "safe": True,
    },
    "verification_watch": {
        "domain": "recon",
        "desc": "人机验证情报台账（只读）：不主动绕做成机械闸；三部门各一张空台账",
        "handler": "verification_watch",
        "safe": True,
    },
    "shared_resources": {
        "domain": "system",
        "desc": "共享资源池（只读骨架）：虚拟号/邮箱按需租借——资源可共享、身份不共享、每次调用留痕",
        "handler": "shared_resources",
        "safe": True,
    },
    "brand_outro": {
        "domain": "creation",
        "desc": "品牌片尾只读渲染：署名/自述/致谢三层 + 四条红线（署名不造假·致谢不套话·承诺可追溯·观众不当流量）",
        "handler": "brand_outro",
        "safe": True,
    },
    "emotion_projection": {
        "domain": "creation",
        "desc": "情感投射只读骨架：叙事四问 → 投射细节 → 四项校验；『身临其境』只有人能判",
        "handler": "emotion_projection",
        "safe": True,
    },
    "hook_registry": {
        "domain": "system",
        "desc": "钩子矩阵只读注册表：50 钩子/六类/三层 + 三条红线（L3 不许挂触手内·失败隔离·链可中断）",
        "handler": "hook_registry",
        "safe": True,
    },
    "scene_anchor": {
        "domain": "creation",
        "desc": "场景锚定只读骨架：8 大类场景 + 灵魂四要素 + 钩子锚场景不锚情绪（作品是为场景做的）",
        "handler": "scene_anchor",
        "safe": True,
    },
    "code_art": {
        "domain": "creation",
        "desc": "代码艺术内核（只读骨架）：INDEX/SEED/CANVAS/LAYER/EXPORT 五原语；无种子不许导出",
        "handler": "code_art",
        "safe": True,
    },
    "orchestration_kernel": {
        "domain": "system",
        "desc": "编排内核（三源蒸馏）：状态/动作空间 + 角色/流程 + 可存储图/挂起恢复；只读能力真执行",
        "handler": "orchestration_kernel",
        "safe": True,
    },
    "render_evolution": {
        "domain": "creation",
        "desc": "渲染进化内核（只读骨架）：五原语 + 三闭环 + 六红线；帕累托前沿机器画、人点",
        "handler": "render_evolution",
        "safe": True,
    },
    "caps_called_audit": {
        "domain": "system",
        "desc": "能力位调用点审计（只读）：动态算 called_by，列出零调用点孤儿清单（同名模块自称不算接线）",
        "handler": "caps_called_audit",
        "safe": True,
    },
    "tentacle_cognition": {
        "domain": "system",
        "desc": "触手认知包（只读骨架）：任务上下文/角色边界/自检三问/不确定上报/操作留痕 + 五条零容忍红线",
        "handler": "tentacle_cognition",
        "safe": True,
    },
    "coverage_auditor": {
        "domain": "system",
        "desc": "触手覆盖审计（只读骨架）：八短板↔八触手组 + 覆盖率读数 + 死角登记 + 五条红线",
        "handler": "coverage_auditor",
        "safe": True,
    },
    "model_key_pool": {
        "domain": "llm",
        "desc": "模型密钥池（只读骨架）：按 owner_ai_id 分池、触手只借不拥有、DPAPI 只存路径、超限只上报",
        "handler": "model_key_pool",
        "safe": True,
    },
    "meta_cognition": {
        "domain": "mind",
        "desc": "元认知循环（只读骨架）：自省→查内部→查外部→问主人→沉淀 + 五条红线（自省不是自责/不许硬猜/先查后问/问完沉淀/大脑也自省）",
        "handler": "meta_cognition",
        "safe": True,
    },
    "libtv_skill": {
        "domain": "video",
        "desc": "LibTV 技能（只读骨架·门）：Agent 创作平台入口（会话进展/增量轮询 + 切项目 + 批量下载）；密钥走 model_key_pool、结果必须落 trace_store",
        "handler": "libtv_skill",
        "safe": True,
    },
    "a1art_skill": {
        "domain": "image_video",
        "desc": "a1.art API 技能（只读骨架·门）：五原语 LOOKUP→UPLOAD→GENERATE→OPTIMIZE→POLL；密钥只走 DPAPI/密钥池、结果必须落盘、不调不支持组件、810012 如实报",
        "handler": "a1art_skill",
        "safe": True,
    },
    "energy_pool": {
        "domain": "system",
        "desc": "能源池（只读骨架·内调）：模型=燃料不是身份；能源抽象 EnergySource + 原生衍生器 + 按需分配；五条红线（模型非身份/能源可换栈不动/衍生码走原生路由/按需/没能源如实报缺）",
        "handler": "energy_pool",
        "safe": True,
    },
    "local_brain": {
        "domain": "mind",
        "desc": "本地原生脑（只读骨架·内调）：本地模型=脑皮层（可换）·主机=纪律层（不可换）；五层链路（模型只做意图解析与结果解释）；五条红线（不许直接执行命令/不可逆必卡/缺参不许猜/每次留痕/身份不许改写）",
        "handler": "local_brain",
        "safe": True,
    },
    "auto_switch": {
        "domain": "mind",
        "desc": "自动化切换引擎（只读骨架·内调）：意图分析(L1解析+L2交叉验证+L3置信度)→任务分级→模型切换→原生执行→验证审计；接线点只有 Intent JSON；五条红线（低置信先问主人/不许直接执行/每次切换记 model_used/不可逆二次确认/身份不许改写）",
        "handler": "auto_switch",
        "safe": True,
    },
    "context_vault": {
        "domain": "system",
        "desc": "上下文归档库（只读骨架·内调）：**索引+检索层，不是第四处存储**（只引用不复制正文）；内存多大上下文就多长（按**可用**内存算预算，不足则降级如实报）；快速搜索=倒排求交→打分→按预算裁剪",
        "handler": "context_vault",
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

# ── 入参契约（R-H98 修根源）──
# 病根：注册表此前只声明"能力叫什么"，**不声明"它需要什么输入"**。于是面板那份"能力总目录"
# 只能发 `{kind, confirm}`（前端 hardcode，见 holo_pet/app.js），带参数的能力点下去就是一次
# 空调用 —— 要么报一个看不懂的错，要么按默认值跑偏。加参数输入是产品功能；**先把契约立起来**
# 才是根因修复：能力自己说清楚"没有这些参数我就不成立"，调用方（面板/脚本/别人）据此拒绝空调用。
#
# 每条都取自处理器**在产生任何副作用之前**的显式拒绝（出处见行内注释），不是猜的。
PARAM_REQUIRED = {
    # api.py:118 —— 无 target 直接 ValueError
    "osint_scan": {"params": ["target"], "hint": "要扫描的域名或 IP"},
    # api.py:210
    "sec_llm": {"params": ["prompt"], "hint": "要问黑客大脑的问题"},
    # api.py:229
    "autopilot": {"params": ["goal"], "hint": "要自主完成的目标"},
    # api.py:266 —— 没有 action/intent 且不是 op=caps 就是缺参
    "tentacle": {"params": ["action"], "hint": "触手能力名；或给 intent 走自动路由、op=caps 看全部"},
    # api.py:297
    "brain_execute": {"params": ["kind"], "hint": "要执行的能力名；或 parallel=[{kind,payload},…]"},
    # api.py:310
    "brain_unify": {"params": ["goal"], "hint": "意图 goal（或 kind 指定能力）"},
    # api.py:372 / think_loop.py:133
    "think_loop": {"params": ["goal"], "hint": "任务描述"},
    # api.py:381 + qiankun.one_key_deploy 的落点门
    "one_key_deploy": {"params": ["target"],
                       "hint": "GitHub 仓库/子目录 URL 或本地目录路径；且必须显式声明落点 "
                               "room=\"<房间名>\" 或 into_global_production=true"},
    # api.py:397 —— 仅 op=submit 时缺 target 才拒
    "deploy_queue": {"params": ["target"], "hint": "仅 op=submit 需要：要入队的项目路径/URL"},
    # api.py:515-519 —— 注意它读的是 repo/url，不是 target（实测踩过：写契约时手快抄错会当场被用例抓住）
    "devour_github": {"params": ["repo"], "hint": "要吞噬的 GitHub 仓库 URL（也认 url=）"},
    # devour_pulse **不登记**：实测它带默认值也能跑完一轮（空调用返回 ok），
    # 属于"参数可选"而非"没参数不成立"——契约不是越写越严，是要写得准。
    # api.py:619
    "codex_chat": {"params": ["message"], "hint": "要发给 Codex 的文本"},
    # api.py:636 —— 没有 thread_id 就没有回合可发
    "codex_turn_send": {"params": ["thread_id"], "hint": "先 codex_thread_new 拿 thread_id"},
    "codex_interrupt": {"params": ["thread_id"], "hint": "要打断的线程 id"},
    # api.py:663
    "pipeline_versions": {"params": ["name"], "hint": "产物名"},
    # api.py:670
    "pipeline_rollback": {"params": ["name"], "hint": "产物名（可选 to_version）"},
    # engine.define_workflow:70 —— 无 name/空 nodes 直接 EngineError
    "wf_define": {"params": ["name", "nodes"], "hint": "工作流名 + 节点列表（带依赖关系的 DAG）"},
    # engine._run_workflow_inner:323 —— 没有 name（或该名不存在）直接 EngineError
    "wf_run": {"params": ["name"], "hint": "要跑的工作流名（先用 wf_define 定义）"},
    # engine.resume_run —— run_id 空 ⇒ get_run 找不到 ⇒ EngineError
    "wf_resume": {"params": ["run_id"], "hint": "要续跑的运行 id（wf_status 里可查）"},
}

def all_caps():
    items = []
    for k, v in BENIGN_CAPS.items():
        row = {"name": k, "status": "enabled", **v}
        need = PARAM_REQUIRED.get(k)
        if need:
            # 入参契约（R-H98）：带"必须有输入才成立"的能力把所需参数显式登记出来，
            # 面板/调用方据此**拒绝空调用**，而不是拿 {} 撞出一个看不懂的结果。
            row["requires_params"] = True
            row["params"] = list(need.get("params") or [])
            row["params_hint"] = str(need.get("hint") or "")
        else:
            row["requires_params"] = False
        items.append(row)
    for k, v in DISABLED_CAPS.items():
        items.append({"name": k, "status": "disabled", "reason": v,
                      "domain": "dangerous", "desc": v, "handler": "blocked"})
    return items


def required_params(kind: str) -> list:
    """该能力"必须由调用方给出"的参数名（没登记 = 空调用也能跑）。"""
    need = PARAM_REQUIRED.get(str(kind or ""))
    return list((need or {}).get("params") or [])


def params_hint(kind: str) -> str:
    need = PARAM_REQUIRED.get(str(kind or ""))
    return str((need or {}).get("hint") or "")
