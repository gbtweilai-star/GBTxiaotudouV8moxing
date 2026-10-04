"""
GBT 策略回测引擎
支持历史数据回测、绩效分析、参数优化
"""
import json
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
import math

@dataclass
class Trade:
    timestamp: str
    symbol: str
    side: str  # buy/sell
    price: float
    quantity: float
    pnl: float = 0.0
    fees: float = 0.0

@dataclass
class BacktestResult:
    strategy_id: str
    symbol: str
    start_date: str
    end_date: str
    initial_capital: float
    final_capital: float
    total_return: float
    win_rate: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    max_drawdown: float
    sharpe_ratio: float
    profit_factor: float
    trades: List[Dict]
    equity_curve: List[float]
    
    def to_dict(self):
        return asdict(self)

class BacktestEngine:
    """回测引擎"""
    
    def __init__(self, initial_capital: float = 10000.0, commission: float = 0.001):
        self.initial_capital = initial_capital
        self.commission = commission
        self.trades = []
        self.equity_curve = []
        self.cash = initial_capital
        self.positions = {}
        
    def generate_mock_data(self, symbol: str, days: int = 30, volatility: float = 0.02) -> List[Dict]:
        """生成模拟历史数据"""
        data = []
        price = 50000.0  # 初始价格
        base_date = datetime.now() - timedelta(days=days)
        
        for i in range(days * 24 * 60):  # 每分钟数据
            # 随机游走 + 趋势
            trend = 0.0001 * math.sin(i / 100)
            noise = random.gauss(0, volatility / 100)
            price *= (1 + trend + noise)
            
            data.append({
                "timestamp": (base_date + timedelta(minutes=i)).isoformat(),
                "open": price * (1 - random.uniform(0, 0.001)),
                "high": price * (1 + random.uniform(0, 0.002)),
                "low": price * (1 - random.uniform(0, 0.002)),
                "close": price,
                "volume": random.uniform(100, 1000)
            })
            
        return data
    
    def calculate_indicators(self, data: List[Dict], symbol: str) -> Dict[str, Any]:
        """计算技术指标"""
        closes = [d["close"] for d in data]
        
        # EMA
        def ema(prices, period):
            multiplier = 2 / (period + 1)
            result = [prices[0]]
            for price in prices[1:]:
                result.append(price * multiplier + result[-1] * (1 - multiplier))
            return result
        
        # RSI
        def rsi(prices, period=14):
            gains, losses = [], []
            for i in range(1, len(prices)):
                diff = prices[i] - prices[i-1]
                gains.append(max(diff, 0))
                losses.append(max(-diff, 0))
            
            avg_gain = sum(gains[:period]) / period
            avg_loss = sum(losses[:period]) / period
            
            result = [None] * period
            for i in range(period, len(gains)):
                avg_gain = (avg_gain * (period - 1) + gains[i]) / period
                avg_loss = (avg_loss * (period - 1) + losses[i]) / period
                if avg_loss == 0:
                    result.append(100)
                else:
                    rs = avg_gain / avg_loss
                    result.append(100 - 100 / (1 + rs))
            return result
        
        # MACD
        def macd(prices, fast=12, slow=26, signal=9):
            ema_fast = ema(prices, fast)
            ema_slow = ema(prices, slow)
            dif = [f - s for f, s in zip(ema_fast, ema_slow)]
            dea = ema(dif, signal)
            histogram = [d - e for d, e in zip(dif, dea)]
            return dif, dea, histogram
        
        # Bollinger Bands
        def bollinger(prices, period=20, std_dev=2):
            result = []
            for i in range(len(prices)):
                if i < period - 1:
                    result.append(None)
                    continue
                slice_prices = prices[i-period+1:i+1]
                mean = sum(slice_prices) / period
                variance = sum((p - mean) ** 2 for p in slice_prices) / period
                std = math.sqrt(variance)
                result.append({
                    "upper": mean + std_dev * std,
                    "middle": mean,
                    "lower": mean - std_dev * std
                })
            return result
        
        # ATR
        def atr(data, period=14):
            trs = []
            for i in range(1, len(data)):
                high = data[i]["high"]
                low = data[i]["low"]
                prev_close = data[i-1]["close"]
                tr = max(high - low, abs(high - prev_close), abs(low - prev_close))
                trs.append(tr)
            
            result = []
            for i in range(len(trs)):
                if i < period - 1:
                    result.append(None)
                else:
                    avg = sum(trs[i-period+1:i+1]) / period
                    result.append(avg)
            return result
        
        return {
            "symbol": symbol,
            "ema_12": ema(closes, 12)[-1] if len(closes) >= 12 else None,
            "ema_26": ema(closes, 26)[-1] if len(closes) >= 26 else None,
            "rsi_14": rsi(closes, 14)[-1] if len(rsi(closes, 14)) > 14 else None,
            "macd": macd(closes)[-1] if len(macd(closes)) > 0 else (None, None, None),
            "bollinger": bollinger(closes)[-1] if len(bollinger(closes)) > 0 else None,
            "atr": atr(data)[-1] if len(atr(data)) > 0 else None,
            "current_price": closes[-1]
        }
    
    def generate_signals(self, indicators: Dict, strategy_type: str = "trend") -> List[Dict]:
        """生成交易信号"""
        signals = []
        price = indicators["current_price"]
        rsi = indicators.get("rsi_14", 50)
        ema_12 = indicators.get("ema_12", price)
        ema_26 = indicators.get("ema_26", price)
        boll = indicators.get("bollinger")
        atr_val = indicators.get("atr", price * 0.02)
        
        if strategy_type == "trend":
            # 趋势跟踪策略
            if ema_12 and ema_26:
                if ema_12 > ema_26 and rsi < 70:
                    signals.append({"type": "buy", "reason": "EMA金叉 + RSI正常", "strength": 0.8})
                elif ema_12 < ema_26 and rsi > 30:
                    signals.append({"type": "sell", "reason": "EMA死叉 + RSI正常", "strength": 0.8})
            
            if boll and price < boll.get("lower", 0):
                signals.append({"type": "buy", "reason": "触及布林带下轨", "strength": 0.6})
            elif boll and price > boll.get("upper", 9999):
                signals.append({"type": "sell", "reason": "触及布林带上轨", "strength": 0.6})
                
        elif strategy_type == "mean_reversion":
            # 均值回归策略
            if rsi and rsi < 30:
                signals.append({"type": "buy", "reason": "RSI超卖", "strength": 0.7})
            elif rsi and rsi > 70:
                signals.append({"type": "sell", "reason": "RSI超买", "strength": 0.7})
                
        elif strategy_type == "breakout":
            # 突破策略
            if boll:
                if price > boll.get("upper", 0) * 1.02:
                    signals.append({"type": "buy", "reason": "突破布林带上轨", "strength": 0.9})
                elif price < boll.get("lower", 0) * 0.98:
                    signals.append({"type": "sell", "reason": "跌破布林带下轨", "strength": 0.9})
        
        return signals
    
    def execute_trade(self, signal: Dict, current_price: float) -> Optional[Trade]:
        """执行交易"""
        side = signal["type"]
        
        if side == "buy" and self.cash > 0:
            # 计算仓位
            position_size = self.cash * 0.95  # 使用95%资金
            quantity = position_size / current_price
            fees = position_size * self.commission
            
            self.trades.append({
                "timestamp": datetime.now().isoformat(),
                "symbol": signal.get("symbol", "BTC/USDT"),
                "side": "buy",
                "price": current_price,
                "quantity": quantity,
                "fees": fees,
                "signal_reason": signal.get("reason", ""),
                "signal_strength": signal.get("strength", 0.5)
            })
            
            self.cash -= (position_size + fees)
            return True
            
        elif side == "sell" and self.positions.get("quantity", 0) > 0:
            quantity = self.positions.get("quantity", 0)
            proceeds = quantity * current_price
            fees = proceeds * self.commission
            pnl = (current_price - self.positions.get("entry_price", current_price)) * quantity - fees
            
            self.trades.append({
                "timestamp": datetime.now().isoformat(),
                "symbol": signal.get("symbol", "BTC/USDT"),
                "side": "sell",
                "price": current_price,
                "quantity": quantity,
                "fees": fees,
                "pnl": pnl,
                "signal_reason": signal.get("reason", "")
            })
            
            self.cash += (proceeds - fees)
            self.positions = {}
            return True
            
        return False
    
    def run_backtest(self, strategy_config: Dict) -> BacktestResult:
        """运行回测"""
        symbol = strategy_config.get("symbol", "BTC/USDT")
        strategy_type = strategy_config.get("strategy", "trend")
        days = strategy_config.get("backtest_days", 30)
        
        # 生成数据
        data = self.generate_mock_data(symbol, days)
        
        # 重置状态
        self.trades = []
        self.equity_curve = [self.initial_capital]
        self.cash = self.initial_capital
        self.positions = {}
        
        # 执行回测
        for i in range(1, len(data)):
            # 计算指标
            indicators = self.calculate_indicators(data[:i+1], symbol)
            
            # 生成信号
            signals = self.generate_signals(indicators, strategy_type)
            
            # 执行交易
            for signal in signals:
                if self.execute_trade(signal, data[i]["close"]):
                    break
            
            # 记录权益
            current_value = self.cash
            if self.positions.get("quantity", 0) > 0:
                current_value += self.positions["quantity"] * data[i]["close"]
            self.equity_curve.append(current_value)
        
        # 计算绩效指标
        final_capital = self.equity_curve[-1]
        total_return = (final_capital - self.initial_capital) / self.initial_capital * 100
        
        # 胜率
        profitable_trades = [t for t in self.trades if t.get("pnl", 0) > 0]
        losing_trades = [t for t in self.trades if t.get("pnl", 0) <= 0]
        win_rate = len(profitable_trades) / len(self.trades) * 100 if self.trades else 0
        
        # 最大回撤
        peak = self.initial_capital
        max_dd = 0
        for equity in self.equity_curve:
            if equity > peak:
                peak = equity
            dd = (peak - equity) / peak * 100
            if dd > max_dd:
                max_dd = dd
        
        # 夏普比率
        returns = []
        for i in range(1, len(self.equity_curve)):
            ret = (self.equity_curve[i] - self.equity_curve[i-1]) / self.equity_curve[i-1]
            returns.append(ret)
        
        if returns:
            avg_return = sum(returns) / len(returns)
            std_return = math.sqrt(sum((r - avg_return)**2 for r in returns) / len(returns)) if len(returns) > 1 else 0.001
            sharpe = (avg_return / std_return) * math.sqrt(365 * 24 * 60) if std_return > 0 else 0
        else:
            sharpe = 0
        
        # 盈亏比
        gross_profit = sum(t.get("pnl", 0) for t in profitable_trades)
        gross_loss = abs(sum(t.get("pnl", 0) for t in losing_trades))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
        
        return BacktestResult(
            strategy_id=strategy_config.get("id", "unknown"),
            symbol=symbol,
            start_date=data[0]["timestamp"][:10],
            end_date=data[-1]["timestamp"][:10],
            initial_capital=self.initial_capital,
            final_capital=final_capital,
            total_return=round(total_return, 2),
            win_rate=round(win_rate, 2),
            total_trades=len(self.trades),
            winning_trades=len(profitable_trades),
            losing_trades=len(losing_trades),
            max_drawdown=round(max_dd, 2),
            sharpe_ratio=round(sharpe, 2),
            profit_factor=round(profit_factor, 2),
            trades=self.trades,
            equity_curve=self.equity_curve[-100:],  # 限制长度
            **strategy_config
        )

# 预置策略
STRATEGIES = {
    "trend_ema": {
        "id": "trend_ema",
        "name": "EMA趋势跟踪",
        "type": "trend",
        "symbol": "BTC/USDT",
        "backtest_days": 30,
        "description": "基于EMA金叉死叉的趋势跟踪策略"
    },
    "rsi_mean_reversion": {
        "id": "rsi_mean_reversion",
        "name": "RSI均值回归",
        "type": "mean_reversion",
        "symbol": "ETH/USDT",
        "backtest_days": 30,
        "description": "RSI超买超卖均值回归策略"
    },
    "bollinger_breakout": {
        "id": "bollinger_breakout",
        "name": "布林带突破",
        "type": "breakout",
        "symbol": "SOL/USDT",
        "backtest_days": 30,
        "description": "布林带突破策略"
    }
}

def run_backtest(strategy_id: str, initial_capital: float = 10000.0) -> Dict:
    """运行回测的便捷函数"""
    engine = BacktestEngine(initial_capital=initial_capital)
    strategy = STRATEGIES.get(strategy_id)
    if not strategy:
        return {"error": f"策略 {strategy_id} 不存在"}
    
    result = engine.run_backtest(strategy)
    return result.to_dict()

if __name__ == "__main__":
    # 测试回测
    print("GBT 策略回测引擎 v1.0")
    print("=" * 50)
    
    for sid in STRATEGIES:
        result = run_backtest(sid)
        print(f"\n策略: {result.get('symbol', 'N/A')}")
        print(f"  收益率: {result.get('total_return', 0):.2f}%")
        print(f"  胜率: {result.get('win_rate', 0):.2f}%")
        print(f"  最大回撤: {result.get('max_drawdown', 0):.2f}%")
        print(f"  夏普比率: {result.get('sharpe_ratio', 0):.2f}")
        print(f"  交易次数: {result.get('total_trades', 0)}")
