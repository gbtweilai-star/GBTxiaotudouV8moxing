"""
GBT 社交交易系统 — FastAPI 后端
"""
from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import uuid
import json

app = FastAPI(
    title="GBT Social Trading API",
    description="GBT 社交交易系统后端 API",
    version="1.0.0"
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== 数据模型 ====================

class StrategyCreate(BaseModel):
    author_id: str
    title: str
    description: Optional[str] = None
    symbols: List[str]
    indicators: Dict[str, Any]
    tags: Optional[List[str]] = None

class StrategyUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    indicators: Optional[Dict[str, Any]] = None
    status: Optional[str] = None

class CopyTradeFollow(BaseModel):
    follower_id: str
    strategy_id: str
    allocation_percentage: float = Field(..., ge=1, le=100)
    initial_balance: float

class CopyTradeUpdate(BaseModel):
    allocation_percentage: float

class CommentCreate(BaseModel):
    user_id: str
    content: str

class TraderRanking(BaseModel):
    trader_id: str
    rank: int
    total_return: float
    win_rate: float
    sharpe_ratio: float
    total_trades: int
    max_drawdown: float

# ==================== 内存存储 (演示用，生产需替换为数据库) ====================

strategies = {}
copy_trades = {}
comments = {}
leaderboards = {}
users = {}

# 初始化测试数据
def init_test_data():
    test_strategies = [
        {
            "id": str(uuid.uuid4()),
            "author_id": "author_001",
            "title": "BTC 突破回踩买入策略",
            "description": "基于布林带收口突破 + EMA 多头排列，在关键支撑位买入，目标 5-8% 收益。",
            "symbols": ["BTC/USDT"],
            "indicators": {
                "bollinger_bands": {"period": 20, "std_dev": 2},
                "ema": {"fast": 12, "slow": 26},
                "rsi": {"period": 14}
            },
            "backtest_results": {
                "win_rate": 78.5,
                "total_return": 23.5,
                "sharpe_ratio": 1.85,
                "max_drawdown": -8.2,
                "total_trades": 45
            },
            "tags": ["BTC", "趋势跟踪", "SWING"],
            "created_at": datetime.now() - timedelta(days=1),
            "status": "published",
            "likes_count": 128,
            "comments_count": 23,
            "followers_count": 342,
            "copies_count": 89
        },
        {
            "id": str(uuid.uuid4()),
            "author_id": "author_002",
            "title": "ETH 艾略特波浪第五浪买入",
            "description": "识别 Elliott Wave 第 5 浪终点，配合 RSI 顶背离，精准捕捉趋势反转。",
            "symbols": ["ETH/USDT"],
            "indicators": {
                "elliott_wave": True,
                "rsi": {"period": 14},
                "macd": {"fast": 12, "slow": 26, "signal": 9}
            },
            "backtest_results": {
                "win_rate": 82.1,
                "total_return": 31.2,
                "sharpe_ratio": 2.10,
                "max_drawdown": -6.5,
                "total_trades": 38
            },
            "tags": ["ETH", "波浪理论", "SCALP"],
            "created_at": datetime.now() - timedelta(hours=3),
            "status": "published",
            "likes_count": 256,
            "comments_count": 45,
            "followers_count": 567,
            "copies_count": 156
        },
        {
            "id": str(uuid.uuid4()),
            "author_id": "author_003",
            "title": "SOL 网格交易策略",
            "description": "基于 ATR 动态网格，震荡市专用。每个网格层 2-3% 收益，积少成多。",
            "symbols": ["SOL/USDT"],
            "indicators": {
                "atr": {"period": 14},
                "grid_layers": 10,
                "grid_spacing_percent": 2.5
            },
            "backtest_results": {
                "win_rate": 85.3,
                "total_return": 18.7,
                "sharpe_ratio": 1.95,
                "max_drawdown": -4.2,
                "total_trades": 256
            },
            "tags": ["SOL", "网格交易", "日内"],
            "created_at": datetime.now() - timedelta(hours=6),
            "status": "published",
            "likes_count": 89,
            "comments_count": 12,
            "followers_count": 234,
            "copies_count": 67
        }
    ]
    
    for s in test_strategies:
        strategies[s["id"]] = s
    
    # 初始化排行榜数据
    leaderboards["author_001"] = {
        "trader_id": "author_001",
        "rank": 1,
        "total_return": 23.5,
        "win_rate": 78.5,
        "sharpe_ratio": 1.85,
        "total_trades": 45,
        "max_drawdown": -8.2
    }
    leaderboards["author_002"] = {
        "trader_id": "author_002",
        "rank": 2,
        "total_return": 31.2,
        "win_rate": 82.1,
        "sharpe_ratio": 2.10,
        "total_trades": 38,
        "max_drawdown": -6.5
    }
    leaderboards["author_003"] = {
        "trader_id": "author_003",
        "rank": 3,
        "total_return": 18.7,
        "win_rate": 85.3,
        "sharpe_ratio": 1.95,
        "total_trades": 256,
        "max_drawdown": -4.2
    }

init_test_data()

# ==================== API 端点 ====================

@app.get("/api/health")
async def health_check():
    return {
        "status": "ok",
        "service": "GBT Social Trading",
        "version": "1.0.0",
        "strategies_count": len(strategies),
        "timestamp": datetime.now().isoformat()
    }

# --- 策略管理 ---

@app.get("/api/strategies")
async def list_strategies(
    status: Optional[str] = Query(None, description="筛选状态: published/draft/archived"),
    symbol: Optional[str] = Query(None, description="按交易对筛选"),
    sort_by: str = Query("created_at", description="排序字段"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """获取策略列表"""
    filtered = strategies.values()
    
    if status:
        filtered = [s for s in filtered if s["status"] == status]
    if symbol:
        filtered = [s for s in filtered if symbol.upper() in s["symbols"]]
    
    sorted_strategies = sorted(filtered, key=lambda x: x.get(sort_by, ""), reverse=True)
    
    return {
        "data": sorted_strategies[offset:offset+limit],
        "total": len(sorted_strategies),
        "limit": limit,
        "offset": offset
    }

@app.get("/api/strategies/{strategy_id}")
async def get_strategy(strategy_id: str):
    """获取策略详情"""
    strategy = strategies.get(strategy_id)
    if not strategy:
        raise HTTPException(status_code=404, detail="策略不存在")
    return strategy

@app.post("/api/strategies", status_code=201)
async def create_strategy(strategy: StrategyCreate):
    """创建新策略"""
    strategy_id = str(uuid.uuid4())
    new_strategy = {
        "id": strategy_id,
        **strategy.dict(),
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
        "status": "draft",
        "likes_count": 0,
        "comments_count": 0,
        "followers_count": 0,
        "copies_count": 0,
        "backtest_results": None
    }
    strategies[strategy_id] = new_strategy
    return new_strategy

@app.put("/api/strategies/{strategy_id}")
async def update_strategy(strategy_id: str, update: StrategyUpdate):
    """更新策略"""
    if strategy_id not in strategies:
        raise HTTPException(status_code=404, detail="策略不存在")
    
    strategies[strategy_id]["updated_at"] = datetime.now()
    for key, value in update.dict().items():
        if value is not None:
            strategies[strategy_id][key] = value
    return strategies[strategy_id]

@app.delete("/api/strategies/{strategy_id}")
async def delete_strategy(strategy_id: str):
    """删除策略"""
    if strategy_id not in strategies:
        raise HTTPException(status_code=404, detail="策略不存在")
    del strategies[strategy_id]
    return {"message": "策略已删除"}

@app.post("/api/strategies/{strategy_id}/like")
async def like_strategy(strategy_id: str):
    """点赞策略"""
    if strategy_id not in strategies:
        raise HTTPException(status_code=404, detail="策略不存在")
    strategies[strategy_id]["likes_count"] += 1
    return {"likes_count": strategies[strategy_id]["likes_count"]}

@app.post("/api/strategies/{strategy_id}/publish")
async def publish_strategy(strategy_id: str):
    """发布策略"""
    if strategy_id not in strategies:
        raise HTTPException(status_code=404, detail="策略不存在")
    strategies[strategy_id]["status"] = "published"
    strategies[strategy_id]["updated_at"] = datetime.now()
    return strategies[strategy_id]

# --- 评论管理 ---

@app.post("/api/strategies/{strategy_id}/comments")
async def add_comment(strategy_id: str, comment: CommentCreate):
    """添加评论"""
    if strategy_id not in strategies:
        raise HTTPException(status_code=404, detail="策略不存在")
    
    comment_id = str(uuid.uuid4())
    new_comment = {
        "id": comment_id,
        "strategy_id": strategy_id,
        "user_id": comment.user_id,
        "content": comment.content,
        "created_at": datetime.now()
    }
    
    if strategy_id not in comments:
        comments[strategy_id] = []
    comments[strategy_id].append(new_comment)
    strategies[strategy_id]["comments_count"] += 1
    
    return new_comment

@app.get("/api/strategies/{strategy_id}/comments")
async def get_comments(strategy_id: str, limit: int = 20):
    """获取策略评论"""
    if strategy_id not in comments:
        return []
    return comments[strategy_id][-limit:]

# --- 跟单管理 ---

@app.post("/api/copy-trade/follow", status_code=201)
async def follow_strategy(follow: CopyTradeFollow):
    """开始跟单"""
    if follow.strategy_id not in strategies:
        raise HTTPException(status_code=404, detail="策略不存在")
    
    follow_id = str(uuid.uuid4())
    new_follow = {
        "id": follow_id,
        "follower_id": follow.follower_id,
        "strategy_id": follow.strategy_id,
        "allocation_percentage": follow.allocation_percentage,
        "initial_balance": follow.initial_balance,
        "current_balance": follow.initial_balance,
        "current_pnl": 0,
        "status": "active",
        "created_at": datetime.now(),
        "last_copy_at": None,
        "positions": [],
        "trade_history": []
    }
    
    copy_trades[follow_id] = new_follow
    strategies[follow.strategy_id]["followers_count"] += 1
    strategies[follow.strategy_id]["copies_count"] += 1
    
    return new_follow

@app.get("/api/copy-trade/following")
async def list_following(follower_id: str):
    """获取用户跟单列表"""
    following = [t for t in copy_trades.values() if t["follower_id"] == follower_id and t["status"] == "active"]
    return following

@app.get("/api/copy-trade/{follow_id}")
async def get_follow_status(follow_id: str):
    """获取跟单状态"""
    if follow_id not in copy_trades:
        raise HTTPException(status_code=404, detail="跟单记录不存在")
    return copy_trades[follow_id]

@app.put("/api/copy-trade/{follow_id}")
async def update_follow(follow_id: str, update: CopyTradeUpdate):
    """更新跟单设置"""
    if follow_id not in copy_trades:
        raise HTTPException(status_code=404, detail="跟单记录不存在")
    
    copy_trades[follow_id]["allocation_percentage"] = update.allocation_percentage
    copy_trades[follow_id]["updated_at"] = datetime.now()
    
    return copy_trades[follow_id]

@app.post("/api/copy-trade/{follow_id}/pause")
async def pause_follow(follow_id: str):
    """暂停跟单"""
    if follow_id not in copy_trades:
        raise HTTPException(status_code=404, detail="跟单记录不存在")
    copy_trades[follow_id]["status"] = "paused"
    return copy_trades[follow_id]

@app.post("/api/copy-trade/{follow_id}/resume")
async def resume_follow(follow_id: str):
    """恢复跟单"""
    if follow_id not in copy_trades:
        raise HTTPException(status_code=404, detail="跟单记录不存在")
    copy_trades[follow_id]["status"] = "active"
    return copy_trades[follow_id]

@app.post("/api/copy-trade/{follow_id}/unfollow")
async def unfollow(follow_id: str):
    """取消跟单"""
    if follow_id not in copy_trades:
        raise HTTPException(status_code=404, detail="跟单记录不存在")
    
    strategy_id = copy_trades[follow_id]["strategy_id"]
    strategies[strategy_id]["followers_count"] = max(0, strategies[strategy_id]["followers_count"] - 1)
    strategies[strategy_id]["copies_count"] = max(0, strategies[strategy_id]["copies_count"] - 1)
    
    del copy_trades[follow_id]
    return {"message": "已取消跟单"}

@app.get("/api/copy-trade/{follow_id}/positions")
async def get_positions(follow_id: str):
    """获取跟单持仓"""
    if follow_id not in copy_trades:
        raise HTTPException(status_code=404, detail="跟单记录不存在")
    return copy_trades[follow_id].get("positions", [])

@app.get("/api/copy-trade/{follow_id}/history")
async def get_trade_history(follow_id: str, limit: int = 20):
    """获取跟单交易历史"""
    if follow_id not in copy_trades:
        raise HTTPException(status_code=404, detail="跟单记录不存在")
    history = copy_trades[follow_id].get("trade_history", [])
    return history[-limit:]

# --- 排行榜 ---

@app.get("/api/leaderboard")
async def get_leaderboard(
    timeframe: str = Query("7d", description="时间范围: 24h/7d/30d/all"),
    min_trades: int = Query(0, description="最小交易次数"),
    sort_by: str = Query("total_return", description="排序字段")
):
    """获取排行榜"""
    leaderboard_list = list(leaderboards.values())
    
    if min_trades > 0:
        leaderboard_list = [l for l in leaderboard_list if l["total_trades"] >= min_trades]
    
    # 按指定字段排序
    if sort_by == "total_return":
        leaderboard_list.sort(key=lambda x: x.get("total_return", 0), reverse=True)
    elif sort_by == "win_rate":
        leaderboard_list.sort(key=lambda x: x.get("win_rate", 0), reverse=True)
    elif sort_by == "sharpe_ratio":
        leaderboard_list.sort(key=lambda x: x.get("sharpe_ratio", 0), reverse=True)
    
    # 重新计算排名
    for i, entry in enumerate(leaderboard_list, 1):
        entry["rank"] = i
    
    return {
        "data": leaderboard_list,
        "total": len(leaderboard_list),
        "timeframe": timeframe
    }

@app.get("/api/leaderboard/{trader_id}")
async def get_trader_ranking(trader_id: str):
    """获取单个交易者排名"""
    ranking = leaderboards.get(trader_id)
    if not ranking:
        raise HTTPException(status_code=404, detail="交易者不存在")
    return ranking

@app.get("/api/social/feed")
async def get_social_feed(
    user_id: str,
    limit: int = 20
):
    """获取用户动态"""
    # 返回用户关注的策略更新和交易活动
    following_strategies = [
        t["strategy_id"] for t in copy_trades.values()
        if t["follower_id"] == user_id
    ]
    
    feed_items = []
    for sid in following_strategies:
        if sid in strategies:
            feed_items.append({
                "type": "strategy_update",
                "strategy": strategies[sid],
                "timestamp": strategies[sid].get("updated_at", datetime.now())
            })
    
    feed_items.sort(key=lambda x: x["timestamp"], reverse=True)
    return feed_items[:limit]

@app.get("/api/social/notifications")
async def get_notifications(user_id: str):
    """获取用户通知"""
    # 模拟通知数据
    notifications = [
        {
            "id": str(uuid.uuid4()),
            "type": "trade_filled",
            "message": "你的跟单交易已完成",
            "strategy_id": "strategy_001",
            "timestamp": datetime.now() - timedelta(minutes=5),
            "read": False
        },
        {
            "id": str(uuid.uuid4()),
            "type": "new_comment",
            "message": "有人评论了你的策略",
            "strategy_id": "strategy_002",
            "timestamp": datetime.now() - timedelta(hours=1),
            "read": False
        },
        {
            "id": str(uuid.uuid4()),
            "type": "follower",
            "message": "新粉丝关注了你",
            "strategy_id": None,
            "timestamp": datetime.now() - timedelta(hours=2),
            "read": True
        }
    ]
    return notifications

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8083)
