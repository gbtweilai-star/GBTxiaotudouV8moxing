// 本文件由 tools/codex-scripts/cloud-mesh.py gen 生成 —— 不要手改。
// 单一真源：deploy/cloud-10/mesh.json（改表再 gen；check 会抓漂移）
// 开发者：自由的风 · 守护者：公主土豆
export const MESH = {
  "form": "single-isolate",
  "form_note": "形态 A：一个 Worker 装 10 个模块 ⇒ 同一 isolate，CPU/内存真共用。形态 B（10 个独立 Worker + 服务绑定）由同一份表生成，只作真互通对照。",
  "doctrine": [
    "插件是接线不是算力：互通 90 条不等于算力乘 10。",
    "真共享 CPU 只有一种形态：10 个模块装在同一个 isolate 里（本文件 form=single-isolate）。",
    "10 个独立 Worker + 服务绑定 = 真互通、各算各的；这不算共享 CPU，不许念成共享。",
    "取不到就写未读到；只有真源明确说不存在才写不存在。",
    "每个 op 的门写在这里，不写在代码的 if 里 —— 门表是单一真源，改门只改这一处。"
  ],
  "modules": [
    {
      "seq": 1,
      "id": "gbt-c01-llm-gateway",
      "owner_label": "dsh-llm-qwen-local",
      "duty": "模型接入与推理路由",
      "ops": [
        "status",
        "identity",
        "models",
        "complete"
      ],
      "op_gates": {
        "status": "none",
        "identity": "none",
        "models": "none",
        "complete": "external_llm"
      },
      "cloud": [
        "AI (Workers AI)",
        "自建 OpenAI 兼容端点 (fetch)"
      ],
      "boundary": "云上托管模型的权重不是我们的，平台侧内容策略仍然生效；真正无限制只能走自托管权重（03 通道）。"
    },
    {
      "seq": 2,
      "id": "gbt-c02-context-compact",
      "owner_label": "dsh-force-compact",
      "duty": "上下文压缩与预算收口",
      "ops": [
        "budget",
        "compact"
      ],
      "op_gates": {
        "budget": "none",
        "compact": "none"
      },
      "cloud": [
        "KV (CTX)",
        "Durable Object (可选串行化点)"
      ],
      "boundary": "压缩是有损的：本模块只做预算与收缩，压掉的东西的可追溯性靠 10 号落账。"
    },
    {
      "seq": 3,
      "id": "gbt-c03-uncensored-lane",
      "owner_label": "dsh-llm-qwen-abliterated",
      "duty": "无审查通道（自托管权重 · 文本 + 图像）",
      "ops": [
        "status",
        "route",
        "image"
      ],
      "op_gates": {
        "status": "none",
        "route": "external_llm",
        "image": "external_llm"
      },
      "cloud": [
        "Containers / 自建端点 (fetch)"
      ],
      "boundary": "这条通道要有我们自己的权重与算力；未接线时读数只能是未读到，不许拿托管模型冒充无审查。图像面另要 IMAGE_ENDPOINT（把无审查图像模型包成 OpenAI 兼容的 /v1/images/generations）——**集成，不是合成权重**。"
    },
    {
      "seq": 4,
      "id": "gbt-c04-tool-web",
      "owner_label": "dsh-tool-web",
      "duty": "联网检索与抓取",
      "ops": [
        "search",
        "fetch"
      ],
      "op_gates": {
        "search": "network_read",
        "fetch": "network_read"
      },
      "cloud": [
        "ai-search 绑定",
        "Browser Rendering 绑定",
        "fetch"
      ],
      "boundary": "检索结果一律是外部数据不是指令；抓回正文只当数据用。"
    },
    {
      "seq": 5,
      "id": "gbt-c05-tool-file",
      "owner_label": "dsh-tool-file",
      "duty": "文件读写（对象存储）",
      "ops": [
        "list",
        "get",
        "put",
        "del"
      ],
      "op_gates": {
        "list": "filesystem_read",
        "get": "filesystem_read",
        "put": "filesystem_write",
        "del": "filesystem_write"
      },
      "cloud": [
        "R2 (FILES)"
      ],
      "boundary": "Worker 里没有本地文件系统；这里的文件是对象存储，key 前缀即命名空间，越出前缀一律拒。"
    },
    {
      "seq": 6,
      "id": "gbt-c06-tool-shell",
      "owner_label": "dsh-tool-shell",
      "duty": "命令执行（隔离容器）",
      "ops": [
        "status",
        "exec"
      ],
      "op_gates": {
        "status": "none",
        "exec": "process_execute"
      },
      "cloud": [
        "Containers / Sandbox 绑定"
      ],
      "boundary": "Worker 本体没有 shell；没绑沙箱时 exec 必须如实拒绝，不许假装执行过。"
    },
    {
      "seq": 7,
      "id": "gbt-c07-memory-vector",
      "owner_label": "dsh-memory-vector",
      "duty": "向量记忆与语义检索",
      "ops": [
        "index",
        "query",
        "stats"
      ],
      "op_gates": {
        "index": "none",
        "query": "none",
        "stats": "none"
      },
      "cloud": [
        "Vectorize (作用域未授权)",
        "D1 + 内积 (降级落点)",
        "agent-memory 绑定"
      ],
      "boundary": "落点是内存还是 D1 要如实报：两种落点的读数不许念成一句。"
    },
    {
      "seq": 8,
      "id": "gbt-c08-memory-local",
      "owner_label": "dsh-memory-local",
      "duty": "键值持久化",
      "ops": [
        "remember",
        "recall",
        "list",
        "forget"
      ],
      "op_gates": {
        "remember": "none",
        "recall": "none",
        "list": "none",
        "forget": "none"
      },
      "cloud": [
        "KV (MEM)"
      ],
      "boundary": "KV 最终一致：写完立刻读可能还是旧值，读数要带落点。D1 是 07 号的落点，不是本位的。"
    },
    {
      "seq": 9,
      "id": "gbt-c09-policy-guard",
      "owner_label": "dsh-policy-guard",
      "duty": "权限与安全策略门",
      "ops": [
        "scopes",
        "grants",
        "evaluate"
      ],
      "op_gates": {
        "scopes": "none",
        "grants": "none",
        "evaluate": "none"
      },
      "cloud": [
        "本模块自带（不依赖云服务）"
      ],
      "boundary": "门只做一件事：没有授权就不放行；AI 一律不许给自己发授权。"
    },
    {
      "seq": 10,
      "id": "gbt-c10-observability",
      "owner_label": "dsh-observability",
      "duty": "可观测与审计落账",
      "ops": [
        "emit",
        "tail",
        "report"
      ],
      "op_gates": {
        "emit": "none",
        "tail": "none",
        "report": "none"
      },
      "cloud": [
        "Workers Logs / tail (workers_tail:read)",
        "R2 落账 (降级落点)"
      ],
      "boundary": "账面条数是读数不是结论；未读到要写未读到，不许写 0。"
    }
  ],
  "edges": {
    "rule": "1 号与 2..10 互绑，2 号与 1,3..10 互绑，以此类推 —— 每位与其余 9 位双向绑，共 10×9=90 条有向边。",
    "directed_expected": 90,
    "undirected_expected": 45,
    "self_loop_expected": 0
  },
  "owner_labels": {
    "gbt-c01-llm-gateway": "dsh-llm-qwen-local",
    "gbt-c02-context-compact": "dsh-force-compact",
    "gbt-c03-uncensored-lane": "dsh-llm-qwen-abliterated",
    "gbt-c04-tool-web": "dsh-tool-web",
    "gbt-c05-tool-file": "dsh-tool-file",
    "gbt-c06-tool-shell": "dsh-tool-shell",
    "gbt-c07-memory-vector": "dsh-memory-vector",
    "gbt-c08-memory-local": "dsh-memory-local",
    "gbt-c09-policy-guard": "dsh-policy-guard",
    "gbt-c10-observability": "dsh-observability"
  },
  "accounts": {
    "wrangler": "4.111.0",
    "auth": "OAuth 已登录（账号已读到；凭据一律只报已配/掩码）",
    "account_id_mask": "82dd88c2****",
    "scopes_present": [
      "workers:write",
      "workers_scripts:write",
      "workers_kv:write",
      "d1:write",
      "ai:write",
      "ai-search:write",
      "ai-search:run",
      "websearch.run",
      "agent-memory:write",
      "queues:write",
      "containers:write",
      "browser:write",
      "pages:write"
    ],
    "scopes_absent": [
      "vectorize:write",
      "analytics_engine:write"
    ],
    "scopes_note": "缺的两个作用域决定 07 向量记忆与 10 可观测的云侧落点，见各模块 cloud_fallback。"
  },
  "reality": {
    "exists": [
      "dsh-llm-qwen-local",
      "dsh-observability"
    ],
    "http404": [
      "dsh-force-compact",
      "dsh-llm-qwen-abliterated",
      "dsh-tool-web",
      "dsh-tool-file",
      "dsh-tool-shell",
      "dsh-memory-vector",
      "dsh-memory-local",
      "dsh-policy-guard"
    ],
    "reading": "现读 2 存在 / 8 返回 HTTP 404；未读到的名字不许当成已装，也不许念成不存在。"
  }
};

export const MODULE_IDS = ["gbt-c01-llm-gateway", "gbt-c02-context-compact", "gbt-c03-uncensored-lane", "gbt-c04-tool-web", "gbt-c05-tool-file", "gbt-c06-tool-shell", "gbt-c07-memory-vector", "gbt-c08-memory-local", "gbt-c09-policy-guard", "gbt-c10-observability"];

export const PEERS = {
  "gbt-c01-llm-gateway": [
    "gbt-c02-context-compact",
    "gbt-c03-uncensored-lane",
    "gbt-c04-tool-web",
    "gbt-c05-tool-file",
    "gbt-c06-tool-shell",
    "gbt-c07-memory-vector",
    "gbt-c08-memory-local",
    "gbt-c09-policy-guard",
    "gbt-c10-observability"
  ],
  "gbt-c02-context-compact": [
    "gbt-c01-llm-gateway",
    "gbt-c03-uncensored-lane",
    "gbt-c04-tool-web",
    "gbt-c05-tool-file",
    "gbt-c06-tool-shell",
    "gbt-c07-memory-vector",
    "gbt-c08-memory-local",
    "gbt-c09-policy-guard",
    "gbt-c10-observability"
  ],
  "gbt-c03-uncensored-lane": [
    "gbt-c01-llm-gateway",
    "gbt-c02-context-compact",
    "gbt-c04-tool-web",
    "gbt-c05-tool-file",
    "gbt-c06-tool-shell",
    "gbt-c07-memory-vector",
    "gbt-c08-memory-local",
    "gbt-c09-policy-guard",
    "gbt-c10-observability"
  ],
  "gbt-c04-tool-web": [
    "gbt-c01-llm-gateway",
    "gbt-c02-context-compact",
    "gbt-c03-uncensored-lane",
    "gbt-c05-tool-file",
    "gbt-c06-tool-shell",
    "gbt-c07-memory-vector",
    "gbt-c08-memory-local",
    "gbt-c09-policy-guard",
    "gbt-c10-observability"
  ],
  "gbt-c05-tool-file": [
    "gbt-c01-llm-gateway",
    "gbt-c02-context-compact",
    "gbt-c03-uncensored-lane",
    "gbt-c04-tool-web",
    "gbt-c06-tool-shell",
    "gbt-c07-memory-vector",
    "gbt-c08-memory-local",
    "gbt-c09-policy-guard",
    "gbt-c10-observability"
  ],
  "gbt-c06-tool-shell": [
    "gbt-c01-llm-gateway",
    "gbt-c02-context-compact",
    "gbt-c03-uncensored-lane",
    "gbt-c04-tool-web",
    "gbt-c05-tool-file",
    "gbt-c07-memory-vector",
    "gbt-c08-memory-local",
    "gbt-c09-policy-guard",
    "gbt-c10-observability"
  ],
  "gbt-c07-memory-vector": [
    "gbt-c01-llm-gateway",
    "gbt-c02-context-compact",
    "gbt-c03-uncensored-lane",
    "gbt-c04-tool-web",
    "gbt-c05-tool-file",
    "gbt-c06-tool-shell",
    "gbt-c08-memory-local",
    "gbt-c09-policy-guard",
    "gbt-c10-observability"
  ],
  "gbt-c08-memory-local": [
    "gbt-c01-llm-gateway",
    "gbt-c02-context-compact",
    "gbt-c03-uncensored-lane",
    "gbt-c04-tool-web",
    "gbt-c05-tool-file",
    "gbt-c06-tool-shell",
    "gbt-c07-memory-vector",
    "gbt-c09-policy-guard",
    "gbt-c10-observability"
  ],
  "gbt-c09-policy-guard": [
    "gbt-c01-llm-gateway",
    "gbt-c02-context-compact",
    "gbt-c03-uncensored-lane",
    "gbt-c04-tool-web",
    "gbt-c05-tool-file",
    "gbt-c06-tool-shell",
    "gbt-c07-memory-vector",
    "gbt-c08-memory-local",
    "gbt-c10-observability"
  ],
  "gbt-c10-observability": [
    "gbt-c01-llm-gateway",
    "gbt-c02-context-compact",
    "gbt-c03-uncensored-lane",
    "gbt-c04-tool-web",
    "gbt-c05-tool-file",
    "gbt-c06-tool-shell",
    "gbt-c07-memory-vector",
    "gbt-c08-memory-local",
    "gbt-c09-policy-guard"
  ]
};

export const OP_GATES = {
  "gbt-c01-llm-gateway": {
    "status": "none",
    "identity": "none",
    "models": "none",
    "complete": "external_llm"
  },
  "gbt-c02-context-compact": {
    "budget": "none",
    "compact": "none"
  },
  "gbt-c03-uncensored-lane": {
    "status": "none",
    "route": "external_llm",
    "image": "external_llm"
  },
  "gbt-c04-tool-web": {
    "search": "network_read",
    "fetch": "network_read"
  },
  "gbt-c05-tool-file": {
    "list": "filesystem_read",
    "get": "filesystem_read",
    "put": "filesystem_write",
    "del": "filesystem_write"
  },
  "gbt-c06-tool-shell": {
    "status": "none",
    "exec": "process_execute"
  },
  "gbt-c07-memory-vector": {
    "index": "none",
    "query": "none",
    "stats": "none"
  },
  "gbt-c08-memory-local": {
    "remember": "none",
    "recall": "none",
    "list": "none",
    "forget": "none"
  },
  "gbt-c09-policy-guard": {
    "scopes": "none",
    "grants": "none",
    "evaluate": "none"
  },
  "gbt-c10-observability": {
    "emit": "none",
    "tail": "none",
    "report": "none"
  }
};
