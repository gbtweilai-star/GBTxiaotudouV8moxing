# GBT 社交交易系统 — 设计文档

## 功能概述

GBT 社交交易平台允许用户：
1. **发布交易策略** — 分享交易思路和分析
2. **跟单交易** — 自动复制成功交易者持仓
3. **排行榜** — 基于收益率、胜率、风险调整后收益排名
4. **社区互动** — 评论、点赞、关注交易者

---

## 核心模块

### 1. 策略发布模块
```python
class TradingStrategy:
    id: str
    author_id: str
    title: str
    description: str
    symbols: List[str]
    indicators: Dict[str, Any]
    backtest_results: BacktestResult
    created_at: datetime
    tags: List[str]
    
    def publish(self) -> StrategyID: ...
    def update(self, data: Dict) -> None: ...
    def delete(self) -> None: ...
```

### 2. 跟单引擎
```python
class CopyTradingEngine:
    def __init__(self, config: CopyTradeConfig):
        self.config = config
        self.position_manager = PositionManager()
        self.risk_controller = RiskController()
        
    def follow(self, follower_id: str, strategy_id: str, allocation: float) -> FollowID:
        """用户跟单"""
        
    def copy_position(self, original_trade: Trade) -> Trade:
        """复制交易"""
        
    def update_allocation(self, follow_id: str, new_allocation: float) -> None:
        """调整仓位"""
        
    def unfollow(self, follow_id: str) -> None:
        """取消跟单"""
```

### 3. 排行榜系统
```python
class LeaderboardService:
    def get_rankings(
        self,
        timeframe: str = "7d",
        min_trades: int = 10,
        sort_by: str = "roi"
    ) -> List[TraderRanking]:
        """获取排行榜"""
        
    def calculate_metrics(self, trader_id: str) -> TraderMetrics:
        """计算交易指标"""
```

### 4. 社交互动模块
```python
class SocialInteraction:
    def like_strategy(self, user_id: str, strategy_id: str) -> None:
        """点赞策略"""
        
    def comment(self, user_id: str, strategy_id: str, content: str) -> CommentID:
        """发表评论"""
        
    def follow_trader(self, follower_id: str, trader_id: str) -> None:
        """关注交易者"""
```

---

## 数据模型

### 交易策略表
| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 策略ID |
| author_id | UUID | 作者ID |
| title | VARCHAR(100) | 策略标题 |
| description | TEXT | 策略描述 |
| symbols | JSON | 交易对列表 |
| indicators | JSON | 技术指标配置 |
| backtest_results | JSON | 回测结果 |
| created_at | TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | 更新时间 |
| status | ENUM | published/draft/archived |
| likes_count | INT | 点赞数 |
| comments_count | INT | 评论数 |
| followers_count | INT | 关注数 |
| copies_count | INT | 跟单数 |

### 跟单记录表
| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 跟单ID |
| follower_id | UUID | 跟单者ID |
| strategy_id | UUID | 策略ID |
| allocation_percentage | DECIMAL | 仓位比例 |
| initial_balance | DECIMAL | 初始资金 |
| current_pnl | DECIMAL | 当前盈亏 |
| status | ENUM | active/paused/closed |
| created_at | TIMESTAMP | 创建时间 |
| last_copy_at | TIMESTAMP | 最后复制时间 |

### 交易者排行榜表
| 字段 | 类型 | 说明 |
|------|------|------|
| trader_id | UUID | 交易者ID |
| period_start | DATE | 统计周期开始 |
| total_trades | INT | 总交易次数 |
| win_rate | DECIMAL | 胜率 |
| total_return | DECIMAL | 总收益率 |
| sharpe_ratio | DECIMAL | 夏普比率 |
| max_drawdown | DECIMAL | 最大回撤 |
| rank | INT | 排名 |
| calculated_at | TIMESTAMP | 计算时间 |

---

## API 端点

### 策略管理
```http
GET /api/strategies — 获取策略列表
POST /api/strategies — 创建策略
GET /api/strategies/{id} — 获取策略详情
PUT /api/strategies/{id} — 更新策略
DELETE /api/strategies/{id} — 删除策略
POST /api/strategies/{id}/like — 点赞
POST /api/strategies/{id}/comment — 评论
GET /api/strategies/{id}/comments — 获取评论
```

### 跟单管理
```http
POST /api/copy-trade/follow — 开始跟单
GET /api/copy-trade/following — 我的跟单
PUT /api/copy-trade/{follow_id}/allocation — 调整仓位
POST /api/copy-trade/{follow_id}/pause — 暂停跟单
POST /api/copy-trade/{follow_id}/resume — 恢复跟单
POST /api/copy-trade/{follow_id}/unfollow — 取消跟单
GET /api/copy-trade/{follow_id}/positions — 持仓列表
GET /api/copy-trade/{follow_id}/history — 交易历史
```

### 排行榜
```http
GET /api/leaderboard — 获取排行榜
GET /api/leaderboard/{trader_id} — 交易者详情
GET /api/leaderboard/me — 我的排名
```

### 社交互动
```http
POST /api/social/follow — 关注交易者
DELETE /api/social/follow/{trader_id} — 取消关注
GET /api/social/feed — 获取动态
GET /api/social/notifications — 获取通知
```

---

## 前端组件

### 策略卡片
```jsx
const StrategyCard = ({ strategy }) => (
  <div className="strategy-card">
    <div className="strategy-header">
      <Avatar src={strategy.author.avatar} />
      <div className="strategy-info">
        <h3>{strategy.title}</h3>
        <p>{strategy.description}</p>
      </div>
    </div>
    <div className="strategy-metrics">
      <span className="metric">胜率: {strategy.win_rate}%</span>
      <span className="metric">收益: {strategy.total_return}%</span>
      <span className="metric">夏普: {strategy.sharpe_ratio}</span>
    </div>
    <div className="strategy-actions">
      <button onClick={() => likeStrategy(strategy.id)}>❤️ {strategy.likes_count}</button>
      <button onClick={() => openComments(strategy.id)}>💬 {strategy.comments_count}</button>
      <button onClick={() => copyTrade(strategy.id)}>📋 跟单</button>
    </div>
  </div>
);
```

### 跟单面板
```jsx
const CopyTradePanel = ({ strategy }) => (
  <div className="copy-trade-panel">
    <h3>跟单设置</h3>
    <div className="allocation-input">
      <label>分配仓位: {allocation}%</label>
      <input 
        type="range" 
        min="1" 
        max="100" 
        value={allocation}
        onChange={(e) => setAllocation(e.target.value)}
      />
    </div>
    <div className="risk-display">
      <span>预估风险: ${calculateRisk(allocation)}</span>
      <span>预期收益: ${calculateExpectedReturn(allocation)}</span>
    </div>
    <button className="follow-btn" onClick={handleFollow}>
      开始跟单
    </button>
  </div>
);
```

---

## 风险管理

### 跟单风险控制
1. **单笔止损**: 跟随策略设定的止损
2. **总仓位限制**: 单策略最大占用资金比例
3. **日亏损限制**: 每日最大亏损阈值
4. **回撤保护**: 总账户回撤达到阈值自动平仓
5. **仓位重平衡**: 定期调整各策略仓位比例

### 风控参数
```python
RISK_LIMITS = {
    "max_single_allocation": 20.0,  # 单策略最大仓位
    "max_total_allocation": 80.0,   # 总跟单仓位上限
    "daily_loss_limit": 5.0,       # 日亏损限制
    "max_drawdown": 15.0,          # 最大回撤限制
    "min_win_rate": 40.0,          # 最低胜率要求
    "min_trades": 10,              # 最小交易次数
    "min_sharpe_ratio": 0.5,       # 最低夏普比率
}
```

---

## 部署架构

### 前端
- React + TypeScript
- 状态管理: Zustand
- 样式: Tailwind CSS
- 图表: Chart.js

### 后端
- FastAPI + Python
- 数据库: PostgreSQL
- 缓存: Redis
- WebSocket: 实时更新

### 智能合约 (可选)
- Solidity
- Arbitrum L2
- GBTToken ERC-20

---

## 开发计划

### Phase 1 — MVP (本周)
- [ ] 策略发布功能
- [ ] 基础跟单引擎
- [ ] 排行榜系统
- [ ] 前端页面

### Phase 2 — 增强 (下周)
- [ ] 社交互动 (点赞/评论)
- [ ] 实时通知
- [ ] 移动端适配
- [ ] 风险控制优化

### Phase 3 — 高级 (下月)
- [ ] AI 策略推荐
- [ ] 跨链跟单
- [ ] 策略市场
- [ ] 收益分成机制
