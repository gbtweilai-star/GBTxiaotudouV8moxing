# GBT 社交交易系统 — 下一步行动计划

## 当前状态

### ✅ 已完成
- 社交交易系统完整设计文档
- 前端 UI 原型 (React 风格 HTML)
- 核心功能模块定义
- 数据模型设计
- API 端点规划

### ⏳ 待完成
- 后端 API 实现
- 数据库 schema 创建
- 智能合约开发 (可选)
- 移动端适配
- 实时 WebSocket 推送

---

## 下一步开发计划

### Phase 1: 后端基础 (本周)
- [ ] FastAPI 服务框架搭建
- [ ] PostgreSQL 数据库 schema
- [ ] Redis 缓存层
- [ ] 用户认证系统 (JWT)
- [ ] 策略 CRUD API
- [ ] 跟单引擎核心逻辑

### Phase 2: 前端集成 (下周)
- [ ] React + TypeScript 重构
- [ ] Zustand 状态管理
- [ ] 实时 WebSocket 连接
- [ ] 移动端响应式设计
- [ ] 性能优化

### Phase 3: 高级功能 (下月)
- [ ] AI 策略推荐引擎
- [ ] 跨链跟单支持
- [ ] 策略市场 (NFT)
- [ ] 收益分成机制
- [ ] 移动端 App

---

## 立即行动项

### 1️⃣ 配置数据库 (需用户操作)
```sql
-- 创建数据库
CREATE DATABASE gbt_social;

-- 策略表
CREATE TABLE strategies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    author_id UUID NOT NULL,
    title VARCHAR(100) NOT NULL,
    description TEXT,
    symbols JSONB,
    indicators JSONB,
    backtest_results JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    status VARCHAR(20) DEFAULT 'draft',
    likes_count INT DEFAULT 0,
    comments_count INT DEFAULT 0,
    followers_count INT DEFAULT 0,
    copies_count INT DEFAULT 0
);

-- 跟单记录表
CREATE TABLE copy_trades (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    follower_id UUID NOT NULL,
    strategy_id UUID NOT NULL,
    allocation_percentage DECIMAL(5,2) NOT NULL,
    initial_balance DECIMAL(15,2) NOT NULL,
    current_pnl DECIMAL(15,2) DEFAULT 0,
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT NOW(),
    last_copy_at TIMESTAMP
);
```

### 2️⃣ 启动后端服务
```bash
# 安装依赖
pip install fastapi uvicorn psycopg2-binary redis

# 启动服务
python social_trading_backend.py
```

### 3️⃣ 部署到 Cloudflare
```bash
npx wrangler pages deploy dist --project-name gbtxiaotudou-social --branch main
```

---

## 技术栈选型

### 后端
- **框架**: FastAPI + Python 3.10+
- **数据库**: PostgreSQL 15
- **缓存**: Redis 7
- **ORM**: SQLAlchemy 2.0
- **认证**: JWT + bcrypt

### 前端
- **框架**: React 18 + TypeScript
- **状态管理**: Zustand
- **样式**: Tailwind CSS
- **图表**: Chart.js / Recharts
- **实时通信**: WebSocket (原生)

### 智能合约 (可选)
- **语言**: Solidity 0.8+
- **链**: Arbitrum L2
- **标准**: ERC-20 (GBTToken)
- **框架**: Hardhat

---

## 核心算法

### 跟单复制算法
```python
def copy_position(original_trade: Trade, follower_config: CopyConfig) -> Trade:
    """
    复制交易算法
    根据跟单者的资金比例和风险管理参数，
    计算并执行对应的交易操作
    """
    # 计算仓位比例
    allocation_ratio = follower_config.allocation_percentage / 100
    
    # 计算跟单者可用资金
    available_balance = follower_config.current_balance * allocation_ratio
    
    # 计算交易数量
    trade_quantity = available_balance / original_trade.price
    
    # 应用风控限制
    trade_quantity = apply_risk_limits(trade_quantity, follower_config)
    
    # 构建跟单交易
    return Trade(
        symbol=original_trade.symbol,
        side=original_trade.side,
        quantity=trade_quantity,
        price=original_trade.price,
        stop_loss=original_trade.stop_loss,
        take_profit=original_trade.take_profit,
        source="copy_trade",
        original_trade_id=original_trade.id
    )
```

### 排行榜评分算法
```python
def calculate_ranking_score(trader_metrics: TraderMetrics) -> float:
    """
    排行榜综合评分
    考虑收益率、胜率、夏普比率、最大回撤等多个维度
    """
    # 收益率得分 (权重 40%)
    return_score = min(trader_metrics.total_return / 100, 1.0) * 0.4
    
    # 胜率得分 (权重 25%)
    winrate_score = trader_metrics.win_rate / 100 * 0.25
    
    # 夏普比率得分 (权重 20%)
    sharpe_score = min(trader_metrics.sharpe_ratio / 3.0, 1.0) * 0.20
    
    # 回撤控制得分 (权重 15%)
    drawdown_score = max(0, 1 - trader_metrics.max_drawdown / 50) * 0.15
    
    # 交易活跃度得分 (权重 10%)
    activity_score = min(trader_metrics.total_trades / 100, 1.0) * 0.10
    
    return return_score + winrate_score + sharpe_score + drawdown_score + activity_score
```

---

## 下一步立即执行

1. **用户确认**: 是否继续开发社交交易系统？
2. **数据库准备**: 创建 PostgreSQL 数据库和表结构
3. **后端开发**: 实现 FastAPI 服务
4. **前端集成**: 将设计稿转为 React 组件
5. **测试部署**: 本地测试 + Cloudflare 部署
