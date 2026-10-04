"""
GBT 社交交易系统 — PostgreSQL 版本
"""
from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import uuid
import json
import os

# 尝试导入 psycopg2，如果失败则使用内存存储
try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False

app = FastAPI(
    title="GBT Social Trading API",
    description="GBT 社交交易系统后端 API (PostgreSQL 版)",
    version="1.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== 配置 ====================

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:pass@localhost:5432/gbt_social")

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

class CommentCreate(BaseModel):
    user_id: str
    content: str

class UserRegister(BaseModel):
    username: str
    email: str
    password: str

class UserLogin(BaseModel):
    email: str
    password: str

# ==================== 数据库初始化 ====================

def init_database():
    """初始化数据库表结构"""
    if not DB_AVAILABLE:
        print("[INFO] PostgreSQL not available, using memory storage")
        return
    
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        # 策略表
        cur.execute("""
            CREATE TABLE IF NOT EXISTS strategies (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                author_id UUID NOT NULL,
                title VARCHAR(200) NOT NULL,
                description TEXT,
                symbols JSONB,
                indicators JSONB,
                backtest_results JSONB,
                tags JSONB,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW(),
                status VARCHAR(20) DEFAULT 'draft',
                likes_count INT DEFAULT 0,
                comments_count INT DEFAULT 0,
                followers_count INT DEFAULT 0,
                copies_count INT DEFAULT 0
            )
        """)
        
        # 跟单记录表
        cur.execute("""
            CREATE TABLE IF NOT EXISTS copy_trades (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                follower_id UUID NOT NULL,
                strategy_id UUID NOT NULL,
                allocation_percentage DECIMAL(5,2) NOT NULL,
                initial_balance DECIMAL(15,2) NOT NULL,
                current_balance DECIMAL(15,2) DEFAULT 0,
                current_pnl DECIMAL(15,2) DEFAULT 0,
                status VARCHAR(20) DEFAULT 'active',
                created_at TIMESTAMP DEFAULT NOW(),
                last_copy_at TIMESTAMP,
                positions JSONB,
                trade_history JSONB
            )
        """)
        
        # 交易者排行榜表
        cur.execute("""
            CREATE TABLE IF NOT EXISTS leaderboards (
                trader_id UUID PRIMARY KEY,
                period_start DATE NOT NULL,
                total_trades INT DEFAULT 0,
                win_rate DECIMAL(5,2) DEFAULT 0,
                total_return DECIMAL(10,2) DEFAULT 0,
                sharpe_ratio DECIMAL(5,2) DEFAULT 0,
                max_drawdown DECIMAL(5,2) DEFAULT 0,
                rank INT DEFAULT 0,
                calculated_at TIMESTAMP DEFAULT NOW()
            )
        """)
        
        # 用户表
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                username VARCHAR(50) UNIQUE NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                avatar_url VARCHAR(500),
                bio TEXT,
                created_at TIMESTAMP DEFAULT NOW(),
                is_verified BOOLEAN DEFAULT FALSE,
                total_earned DECIMAL(15,2) DEFAULT 0,
                total_trades INT DEFAULT 0,
                win_rate DECIMAL(5,2) DEFAULT 0
            )
        """)
        
        conn.commit()
        cur.close()
        conn.close()
        print("[INFO] Database tables initialized")
        
    except Exception as e:
        print(f"[WARN] DB init failed: {e}")
        print("使用内存存储模式")

init_database()

# ==================== 内存存储 (备用) ====================

strategies = {}
copy_trades = {}
comments = {}
leaderboards = {}
users = {}
follows = {}

# 初始化测试数据
def init_test_data():
    test_strategies = [
        {
            "id": str(uuid.uuid4()),
            "author_id": "author_001",
            "title": "BTC 突破回踩买入策略",
            "description": "基于布林带收口突破 + EMA 多头排列，在关键支撑位买入，目标 5-8% 收益。",
            "symbols": ["BTC/USDT"],
            "indicators": {"bollinger_bands": {"period": 20, "std_dev": 2}, "ema": {"fast": 12, "slow": 26}, "rsi": {"period": 14}},
            "backtest_results": {"win_rate": 78.5, "total_return": 23.5, "sharpe_ratio": 1.85, "max_drawdown": -8.2, "total_trades": 45},
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
            "indicators": {"elliott_wave": True, "rsi": {"period": 14}, "macd": {"fast": 12, "slow": 26, "signal": 9}},
            "backtest_results": {"win_rate": 82.1, "total_return": 31.2, "sharpe_ratio": 2.10, "max_drawdown": -6.5, "total_trades": 38},
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
            "indicators": {"atr": {"period": 14}, "grid_layers": 10, "grid_spacing_percent": 2.5},
            "backtest_results": {"win_rate": 85.3, "total_return": 18.7, "sharpe_ratio": 1.95, "max_drawdown": -4.2, "total_trades": 256},
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
    
    leaderboards["author_001"] = {"trader_id": "author_001", "rank": 1, "total_return": 23.5, "win_rate": 78.5, "sharpe_ratio": 1.85, "total_trades": 45, "max_drawdown": -8.2}
    leaderboards["author_002"] = {"trader_id": "author_002", "rank": 2, "total_return": 31.2, "win_rate": 82.1, "sharpe_ratio": 2.10, "total_trades": 38, "max_drawdown": -6.5}
    leaderboards["author_003"] = {"trader_id": "author_003", "rank": 3, "total_return": 18.7, "win_rate": 85.3, "sharpe_ratio": 1.95, "total_trades": 256, "max_drawdown": -4.2}

init_test_data()

# ==================== API 端点 ====================

@app.get("/api/health")
async def health_check():
    return {
        "status": "ok",
        "service": "GBT Social Trading",
        "version": "1.1.0",
        "database": "postgresql" if DB_AVAILABLE else "memory",
        "strategies_count": len(strategies),
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/strategies")
async def list_strategies(
    status: Optional[str] = Query(None),
    symbol: Optional[str] = Query(None),
    sort_by: str = Query("created_at"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    filtered = list(strategies.values())
    if status:
        filtered = [s for s in filtered if s["status"] == status]
    if symbol:
        filtered = [s for s in filtered if symbol.upper() in [x.upper() for x in s.get("symbols", [])]]
    sorted_strategies = sorted(filtered, key=lambda x: x.get(sort_by, ""), reverse=True)
    return {"data": sorted_strategies[offset:offset+limit], "total": len(sorted_strategies), "limit": limit, "offset": offset}

@app.get("/api/strategies/{strategy_id}")
async def get_strategy(strategy_id: str):
    strategy = strategies.get(strategy_id)
    if not strategy:
        raise HTTPException(status_code=404, detail="策略不存在")
    return strategy

@app.post("/api/strategies", status_code=201)
async def create_strategy(strategy: StrategyCreate):
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
    if strategy_id not in strategies:
        raise HTTPException(status_code=404, detail="策略不存在")
    strategies[strategy_id]["updated_at"] = datetime.now()
    for key, value in update.dict().items():
        if value is not None:
            strategies[strategy_id][key] = value
    return strategies[strategy_id]

@app.delete("/api/strategies/{strategy_id}")
async def delete_strategy(strategy_id: str):
    if strategy_id not in strategies:
        raise HTTPException(status_code=404, detail="策略不存在")
    del strategies[strategy_id]
    return {"message": "策略已删除"}

@app.post("/api/strategies/{strategy_id}/like")
async def like_strategy(strategy_id: str):
    if strategy_id not in strategies:
        raise HTTPException(status_code=404, detail="策略不存在")
    strategies[strategy_id]["likes_count"] += 1
    return {"likes_count": strategies[strategy_id]["likes_count"]}

@app.post("/api/strategies/{strategy_id}/publish")
async def publish_strategy(strategy_id: str):
    if strategy_id not in strategies:
        raise HTTPException(status_code=404, detail="策略不存在")
    strategies[strategy_id]["status"] = "published"
    strategies[strategy_id]["updated_at"] = datetime.now()
    return strategies[strategy_id]

@app.post("/api/strategies/{strategy_id}/comments")
async def add_comment(strategy_id: str, comment: CommentCreate):
    if strategy_id not in strategies:
        raise HTTPException(status_code=404, detail="策略不存在")
    comment_id = str(uuid.uuid4())
    new_comment = {"id": comment_id, "strategy_id": strategy_id, "user_id": comment.user_id, "content": comment.content, "created_at": datetime.now()}
    if strategy_id not in comments:
        comments[strategy_id] = []
    comments[strategy_id].append(new_comment)
    strategies[strategy_id]["comments_count"] += 1
    return new_comment

@app.get("/api/strategies/{strategy_id}/comments")
async def get_comments(strategy_id: str, limit: int = 20):
    return comments.get(strategy_id, [])[-limit:]

@app.post("/api/copy-trade/follow", status_code=201)
async def follow_strategy(follow: CopyTradeFollow):
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
    return [t for t in copy_trades.values() if t["follower_id"] == follower_id and t["status"] == "active"]

@app.get("/api/copy-trade/{follow_id}")
async def get_follow_status(follow_id: str):
    if follow_id not in copy_trades:
        raise HTTPException(status_code=404, detail="跟单记录不存在")
    return copy_trades[follow_id]

@app.put("/api/copy-trade/{follow_id}")
async def update_follow(follow_id: str, update: dict):
    if follow_id not in copy_trades:
        raise HTTPException(status_code=404, detail="跟单记录不存在")
    copy_trades[follow_id]["allocation_percentage"] = update.get("allocation_percentage", copy_trades[follow_id]["allocation_percentage"])
    return copy_trades[follow_id]

@app.post("/api/copy-trade/{follow_id}/pause")
async def pause_follow(follow_id: str):
    if follow_id not in copy_trades:
        raise HTTPException(status_code=404, detail="跟单记录不存在")
    copy_trades[follow_id]["status"] = "paused"
    return copy_trades[follow_id]

@app.post("/api/copy-trade/{follow_id}/resume")
async def resume_follow(follow_id: str):
    if follow_id not in copy_trades:
        raise HTTPException(status_code=404, detail="跟单记录不存在")
    copy_trades[follow_id]["status"] = "active"
    return copy_trades[follow_id]

@app.post("/api/copy-trade/{follow_id}/unfollow")
async def unfollow(follow_id: str):
    if follow_id not in copy_trades:
        raise HTTPException(status_code=404, detail="跟单记录不存在")
    strategy_id = copy_trades[follow_id]["strategy_id"]
    strategies[strategy_id]["followers_count"] = max(0, strategies[strategy_id]["followers_count"] - 1)
    strategies[strategy_id]["copies_count"] = max(0, strategies[strategy_id]["copies_count"] - 1)
    del copy_trades[follow_id]
    return {"message": "已取消跟单"}

@app.get("/api/copy-trade/{follow_id}/positions")
async def get_positions(follow_id: str):
    if follow_id not in copy_trades:
        raise HTTPException(status_code=404, detail="跟单记录不存在")
    return copy_trades[follow_id].get("positions", [])

@app.get("/api/copy-trade/{follow_id}/history")
async def get_trade_history(follow_id: str, limit: int = 20):
    if follow_id not in copy_trades:
        raise HTTPException(status_code=404, detail="跟单记录不存在")
    return copy_trades[follow_id].get("trade_history", [])[-limit:]

@app.get("/api/leaderboard")
async def get_leaderboard(
    timeframe: str = Query("7d"),
    min_trades: int = Query(0),
    sort_by: str = Query("total_return")
):
    leaderboard_list = list(leaderboards.values())
    if min_trades > 0:
        leaderboard_list = [l for l in leaderboard_list if l["total_trades"] >= min_trades]
    if sort_by == "total_return":
        leaderboard_list.sort(key=lambda x: x.get("total_return", 0), reverse=True)
    elif sort_by == "win_rate":
        leaderboard_list.sort(key=lambda x: x.get("win_rate", 0), reverse=True)
    elif sort_by == "sharpe_ratio":
        leaderboard_list.sort(key=lambda x: x.get("sharpe_ratio", 0), reverse=True)
    for i, entry in enumerate(leaderboard_list, 1):
        entry["rank"] = i
    return {"data": leaderboard_list, "total": len(leaderboard_list), "timeframe": timeframe}

@app.get("/api/leaderboard/{trader_id}")
async def get_trader_ranking(trader_id: str):
    ranking = leaderboards.get(trader_id)
    if not ranking:
        raise HTTPException(status_code=404, detail="交易者不存在")
    return ranking

@app.get("/api/social/feed")
async def get_social_feed(user_id: str, limit: int = 20):
    following_strategies = [t["strategy_id"] for t in copy_trades.values() if t["follower_id"] == user_id]
    feed_items = []
    for sid in following_strategies:
        if sid in strategies:
            feed_items.append({"type": "strategy_update", "strategy": strategies[sid], "timestamp": strategies[sid].get("updated_at", datetime.now())})
    feed_items.sort(key=lambda x: x["timestamp"], reverse=True)
    return feed_items[:limit]

@app.get("/api/social/notifications")
async def get_notifications(user_id: str):
    notifications = [
        {"id": str(uuid.uuid4()), "type": "trade_filled", "message": "你的跟单交易已完成", "strategy_id": "strategy_001", "timestamp": datetime.now() - timedelta(minutes=5), "read": False},
        {"id": str(uuid.uuid4()), "type": "new_comment", "message": "有人评论了你的策略", "strategy_id": "strategy_002", "timestamp": datetime.now() - timedelta(hours=1), "read": False},
        {"id": str(uuid.uuid4()), "type": "follower", "message": "新粉丝关注了你", "strategy_id": None, "timestamp": datetime.now() - timedelta(hours=2), "read": True}
    ]
    return notifications

@app.post("/api/auth/register", status_code=201)
async def register_user(user: UserRegister):
    user_id = str(uuid.uuid4())
    new_user = {
        "id": user_id,
        "username": user.username,
        "email": user.email,
        "password_hash": "hashed_" + user.password,  # 生产环境使用 bcrypt
        "avatar_url": None,
        "bio": None,
        "created_at": datetime.now(),
        "is_verified": False,
        "total_earned": 0,
        "total_trades": 0,
        "win_rate": 0
    }
    users[user_id] = new_user
    return {"user_id": user_id, "username": user.username, "message": "注册成功"}

@app.post("/api/auth/login")
async def login_user(login: UserLogin):
    user = next((u for u in users.values() if u["email"] == login.email), None)
    if not user or user["password_hash"] != "hashed_" + login.password:
        raise HTTPException(status_code=401, detail="邮箱或密码错误")
    return {"user_id": user["id"], "username": user["username"], "message": "登录成功"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8084)
