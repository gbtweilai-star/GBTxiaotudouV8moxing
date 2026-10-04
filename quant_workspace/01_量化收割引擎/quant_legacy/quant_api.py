"""
GBT Quantitative Trading API - FastAPI
策略管理 + 回测执行 + 实时信号
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict
import asyncio
import json
import random
from datetime import datetime
import numpy as np

app = FastAPI(title="GBT Quant Trading API", version="3.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== Models ====================
class StrategyCreate(BaseModel):
    name: str
    type: str
    symbol: str
    params: Dict[str, float]
    description: str = ""

class BacktestRequest(BaseModel):
    strategy_id: str
    symbol: str
    days: int = 90
    initial_capital: float = 100000.0

class TradeSignal(BaseModel):
    timestamp: str
    symbol: str
    side: str
    price: float
    quantity: float
    strategy: str
    confidence: float

# ==================== In-memory Storage ====================
strategies = {}
trades = []
signals = []

# ==================== Price Generator ====================
def generate_prices(symbol: str, days: int, base_price: float = None) -> List[float]:
    """生成模拟价格数据"""
    base_prices = {
        "BTC/USDT": 65000,
        "ETH/USDT": 3500,
        "SOL/USDT": 140,
        "BNB/USDT": 600,
        "XRP/USDT": 0.62
    }
    base = base_price or base_prices.get(symbol, 100)
    
    prices = [base]
    trend = random.choice([-0.0001, 0, 0.0001])
    volatility = 0.02
    
    for _ in range(days * 24):  # Hourly data
        drift = trend
        diffusion = volatility * np.random.randn()
        change = np.exp(drift + diffusion)
        prices.append(prices[-1] * change)
    
    return prices

# ==================== Strategy Engine ====================
class MACDStrategy:
    def __init__(self, params: Dict):
        self.name = "MACD"
        self.fast = params.get("fast", 12)
        self.slow = params.get("slow", 26)
        self.signal = params.get("signal", 9)
    
    def generate_signal(self, prices: List[float]) -> Optional[str]:
        if len(prices) < self.slow + self.signal:
            return None
        
        ema_fast = np.mean(prices[-self.fast:])
        ema_slow = np.mean(prices[-self.slow:])
        macd = ema_fast - ema_slow
        
        prev_ema_fast = np.mean(prices[-self.fast-1:-1])
        prev_ema_slow = np.mean(prices[-self.slow-1:-1])
        prev_macd = prev_ema_fast - prev_ema_slow
        
        if prev_macd <= 0 and macd > 0:
            return "buy"
        elif prev_macd >= 0 and macd < 0:
            return "sell"
        return None

class RSIStrategy:
    def __init__(self, params: Dict):
        self.name = "RSI"
        self.period = params.get("period", 14)
        self.oversold = params.get("oversold", 30)
        self.overbought = params.get("overbought", 70)
    
    def generate_signal(self, prices: List[float]) -> Optional[str]:
        if len(prices) < self.period:
            return None
        
        rsi = self._calculate_rsi(prices)
        if rsi < self.oversold:
            return "buy"
        elif rsi > self.overbought:
            return "sell"
        return None
    
    def _calculate_rsi(self, prices: List[float]) -> float:
        period = self.period
        changes = [prices[i] - prices[i-1] for i in range(1, len(prices))]
        gains = [c for c in changes[-period:] if c > 0]
        losses = [-c for c in changes[-period:] if c < 0]
        avg_gain = np.mean(gains) if gains else 0
        avg_loss = np.mean(losses) if losses else 0.001
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))

class BollingerStrategy:
    def __init__(self, params: Dict):
        self.name = "Bollinger"
        self.period = params.get("period", 20)
        self.std_dev = params.get("std_dev", 2)
    
    def generate_signal(self, prices: List[float]) -> Optional[str]:
        if len(prices) < self.period:
            return None
        
        sma = np.mean(prices[-self.period:])
        std = np.std(prices[-self.period:])
        upper = sma + self.std_dev * std
        lower = sma - self.std_dev * std
        current = prices[-1]
        
        if current <= lower:
            return "buy"
        elif current >= upper:
            return "sell"
        return None

# ==================== Backtest Engine ====================
def run_backtest(strategy_name: str, strategy_params: Dict, symbol: str, days: int, initial_capital: float) -> Dict:
    """运行回测"""
    # Select strategy
    if "MACD" in strategy_name.upper():
        strategy = MACDStrategy(strategy_params)
    elif "RSI" in strategy_name.upper():
        strategy = RSIStrategy(strategy_params)
    elif "BOLL" in strategy_name.upper():
        strategy = BollingerStrategy(strategy_params)
    else:
        strategy = MACDStrategy(strategy_params)
    
    # Generate prices
    prices = generate_prices(symbol, days)
    
    # Run backtest
    cash = initial_capital
    position = None
    trades_list = []
    equity_curve = [initial_capital]
    
    for i in range(len(prices)):
        current_price = prices[i]
        timestamp = f"2024-01-{min(i % 28 + 1, 28):02d}T{(i % 24):02d}:00:00"
        
        signal = strategy.generate_signal(prices[:i+1])
        
        if signal == "buy" and position is None:
            # Open position
            quantity = min(cash * 0.1 / current_price, 1.0)
            cash -= quantity * current_price
            position = {
                "entry_price": current_price,
                "quantity": quantity,
                "timestamp": timestamp
            }
            trades_list.append({
                "timestamp": timestamp,
                "side": "buy",
                "price": current_price,
                "quantity": quantity
            })
        
        elif signal == "sell" and position is not None:
            # Close position
            pnl = (current_price - position["entry_price"]) * position["quantity"]
            cash += position["quantity"] * current_price
            trades_list.append({
                "timestamp": timestamp,
                "side": "sell",
                "price": current_price,
                "quantity": position["quantity"],
                "pnl": pnl
            })
            position = None
        
        # Record equity
        equity = cash
        if position:
            equity += position["quantity"] * current_price
        equity_curve.append(equity)
    
    # Close remaining position
    if position:
        final_price = prices[-1]
        pnl = (final_price - position["entry_price"]) * position["quantity"]
        cash += position["quantity"] * final_price
        trades_list.append({
            "timestamp": f"2024-{len(prices)}T23:00:00",
            "side": "sell",
            "price": final_price,
            "quantity": position["quantity"],
            "pnl": pnl
        })
    
    # Calculate metrics
    final_equity = equity_curve[-1]
    total_return = ((final_equity - initial_capital) / initial_capital) * 100
    
    # Max drawdown
    peak = initial_capital
    max_dd = 0
    for equity in equity_curve:
        if equity > peak:
            peak = equity
        dd = (peak - equity) / peak
        if dd > max_dd:
            max_dd = dd
    
    # Win rate
    wins = sum(1 for t in trades_list if t.get("pnl", 0) > 0)
    losses = sum(1 for t in trades_list if t.get("pnl", 0) < 0)
    total_trades = wins + losses
    win_rate = (wins / total_trades * 100) if total_trades > 0 else 0
    
    # Sharpe ratio (simplified)
    daily_returns = []
    for i in range(1, len(equity_curve)):
        daily_returns.append((equity_curve[i] - equity_curve[i-1]) / equity_curve[i-1])
    
    sharpe = 0
    if len(daily_returns) > 1:
        mean_ret = np.mean(daily_returns)
        std_ret = np.std(daily_returns)
        if std_ret > 0:
            sharpe = (mean_ret / std_ret) * np.sqrt(252)
    
    return {
        "strategy": strategy_name,
        "symbol": symbol,
        "days": days,
        "initial_capital": initial_capital,
        "final_equity": round(final_equity, 2),
        "total_return": round(total_return, 2),
        "max_drawdown": round(max_dd * 100, 2),
        "win_rate": round(win_rate, 1),
        "sharpe_ratio": round(sharpe, 2),
        "total_trades": total_trades,
        "buy_trades": len([t for t in trades_list if t["side"] == "buy"]),
        "sell_trades": len([t for t in trades_list if t["side"] == "sell"]),
        "trades": trades_list[:10]  # Return first 10 trades
    }

# ==================== API Endpoints ====================
@app.get("/")
async def root():
    return {
        "service": "GBT Quant Trading API",
        "version": "3.0.0",
        "status": "running"
    }

@app.get("/api/strategies")
async def list_strategies():
    """列出所有策略"""
    return {
        "strategies": list(strategies.values()),
        "total": len(strategies)
    }

@app.post("/api/strategies")
async def create_strategy(strategy: StrategyCreate):
    """创建策略"""
    strategy_id = f"strat_{len(strategies) + 1:03d}"
    strategies[strategy_id] = {
        "id": strategy_id,
        "name": strategy.name,
        "type": strategy.type,
        "symbol": strategy.symbol,
        "params": strategy.params,
        "description": strategy.description,
        "created_at": datetime.now().isoformat()
    }
    return {"id": strategy_id, "message": "Strategy created"}

@app.delete("/api/strategies/{strategy_id}")
async def delete_strategy(strategy_id: str):
    """删除策略"""
    if strategy_id not in strategies:
        raise HTTPException(status_code=404, detail="Strategy not found")
    del strategies[strategy_id]
    return {"message": "Strategy deleted"}

@app.post("/api/backtest")
async def run_backtest_test(request: BacktestRequest):
    """运行回测"""
    result = run_backtest(
        strategy_name=request.strategy_id,
        strategy_params={},
        symbol=request.symbol,
        days=request.days,
        initial_capital=request.initial_capital
    )
    return result

@app.get("/api/strategies/predefined")
async def get_predefined_strategies():
    """获取预设策略"""
    return {
        "strategies": [
            {
                "id": "MACD",
                "name": "MACD均线策略",
                "type": "trend",
                "symbol": "BTC/USDT",
                "params": {"fast": 12, "slow": 26, "signal": 9},
                "description": "双EMA交叉策略"
            },
            {
                "id": "RSI",
                "name": "RSI均值回归",
                "type": "mean_reversion",
                "symbol": "ETH/USDT",
                "params": {"period": 14, "oversold": 30, "overbought": 70},
                "description": "超卖超买策略"
            },
            {
                "id": "BOLL",
                "name": "布林带突破",
                "type": "breakout",
                "symbol": "SOL/USDT",
                "params": {"period": 20, "std_dev": 2},
                "description": "布林带上下轨策略"
            }
        ]
    }

@app.get("/api/signals")
async def get_signals():
    """获取交易信号"""
    return {"signals": signals[-10:], "total": len(signals)}

@app.get("/api/performance")
async def get_performance(strategy_id: Optional[str] = None):
    """获取绩效数据"""
    if strategy_id and strategy_id in strategies:
        return {
            "strategy": strategy_id,
            "metrics": {
                "total_trades": random.randint(50, 200),
                "win_rate": round(random.uniform(40, 65), 1),
                "total_return": round(random.uniform(-5, 20), 2),
                "max_drawdown": round(random.uniform(2, 15), 2),
                "sharpe_ratio": round(random.uniform(0.5, 2.0), 2)
            }
        }
    return {"error": "Strategy not found"}

# ==================== Main ====================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8091)
