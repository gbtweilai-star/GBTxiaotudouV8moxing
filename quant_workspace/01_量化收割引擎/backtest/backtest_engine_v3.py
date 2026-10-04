"""
GBT 量化策略优化版
改进信号生成逻辑，增加更多交易机会
"""
import json
import numpy as np
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from datetime import datetime
import random

@dataclass
class Position:
    symbol: str
    side: str
    quantity: float
    entry_price: float
    timestamp: str
    stop_loss: float = 0

@dataclass
class Trade:
    timestamp: str
    symbol: str
    side: str
    price: float
    quantity: float
    strategy: str
    pnl: float = 0

class BaseStrategy:
    def __init__(self, name: str, style: str, symbol: str, description: str):
        self.name = name
        self.style = style
        self.symbol = symbol
        self.description = description
    
    def generate_signal(self, prices: List[float]) -> Optional[str]:
        raise NotImplementedError

class MACDStrategy(BaseStrategy):
    def __init__(self, fast=12, slow=26, signal=9, threshold=0.001):
        super().__init__("MACD趋势跟踪", "trend", "BTC/USDT", "双EMA交叉+MACD确认")
        self.fast = fast
        self.slow = slow
        self.signal = signal
        self.threshold = threshold
    
    def generate_signal(self, prices: List[float]) -> Optional[str]:
        if len(prices) < self.slow + self.signal:
            return None
        ema_fast = np.mean(prices[-self.fast:])
        ema_slow = np.mean(prices[-self.slow:])
        macd = ema_fast - ema_slow
        prev_ema_fast = np.mean(prices[-self.fast-1:-1])
        prev_ema_slow = np.mean(prices[-self.slow-1:-1])
        prev_macd = prev_ema_fast - prev_ema_slow
        
        # More sensitive crossover detection
        if prev_macd <= self.threshold and macd > self.threshold:
            return "buy"
        elif prev_macd >= -self.threshold and macd < -self.threshold:
            return "sell"
        return None

class RSIStrategy(BaseStrategy):
    def __init__(self, period=14, oversold=30, overbought=70):
        super().__init__("RSI均值回归", "mean_reversion", "ETH/USDT", "超卖超买策略")
        self.period = period
        self.oversold = oversold
        self.overbought = overbought
    
    def generate_signal(self, prices: List[float]) -> Optional[str]:
        if len(prices) < self.period:
            return None
        rsi = self._calc_rsi(prices)
        if rsi < self.oversold:
            return "buy"
        elif rsi > self.overbought:
            return "sell"
        return None
    
    def _calc_rsi(self, prices: List[float]) -> float:
        changes = [prices[i] - prices[i-1] for i in range(1, len(prices))]
        gains = [c for c in changes[-self.period:] if c > 0]
        losses = [-c for c in changes[-self.period:] if c < 0]
        avg_gain = np.mean(gains) if gains else 0
        avg_loss = np.mean(losses) if losses else 0.001
        return 100 - (100 / (1 + avg_gain / avg_loss))

class BollingerStrategy(BaseStrategy):
    def __init__(self, period=20, std_dev=2):
        super().__init__("布林带突破", "breakout", "SOL/USDT", "上下轨突破策略")
        self.period = period
        self.std_dev = std_dev
    
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

class KDJStrategy(BaseStrategy):
    def __init__(self, n=9, m1=3, m2=3):
        super().__init__("KDJ随机指标", "oscillator", "BNB/USDT", "KDJ超卖超买")
        self.n = n
        self.m1 = m1
        self.m2 = m2
    
    def generate_signal(self, prices: List[float]) -> Optional[str]:
        if len(prices) < self.n:
            return None
        low_n = min(prices[-self.n:])
        high_n = max(prices[-self.n:])
        current = prices[-1]
        rsv = (current - low_n) / (high_n - low_n) * 100 if high_n != low_n else 50
        k = 2/3 * 50 + 1/3 * rsv
        d = 2/3 * 50 + 1/3 * k
        j = 3 * k - 2 * d
        if k < 20 and k > d:
            return "buy"
        elif k > 80 and k < d:
            return "sell"
        return None

class ATRStopStrategy(BaseStrategy):
    def __init__(self, period=14, multiplier=2):
        super().__init__("ATR动态止损", "risk_management", "BTC/USDT", "ATR跟踪止损")
        self.period = period
        self.multiplier = multiplier
    
    def generate_signal(self, prices: List[float]) -> Optional[str]:
        if len(prices) < self.period + 5:
            return None
        atr = self._calc_atr(prices)
        current = prices[-1]
        high_n = max(prices[-self.period:])
        low_n = min(prices[-self.period:])
        
        # ATR breakout signals
        if current <= low_n - atr * self.multiplier * 0.5:
            return "sell"
        elif current >= high_n + atr * self.multiplier * 0.5:
            return "buy"
        return None
    
    def _calc_atr(self, prices: List[float]) -> float:
        trs = []
        for i in range(1, len(prices)):
            tr = max(prices[i] - prices[i-1], abs(prices[i] - prices[i-1]), abs(prices[i-1] - prices[i-1]))
            trs.append(tr)
        return np.mean(trs[-self.period:]) if trs else 0

class QuantEngine:
    def __init__(self, capital=100000.0):
        self.capital = capital
        self.cash = capital
        self.positions = {}
        self.trades = []
        self.equity_curve = [capital]
    
    def run_backtest(self, strategy, prices: List[float], days=90) -> Dict:
        self.cash = self.capital
        self.positions.clear()
        self.trades.clear()
        self.equity_curve = [self.capital]
        
        pos_opened = False
        
        for i in range(len(prices)):
            price = prices[i]
            ts = f"2024-01-{min(i%28+1,28):02d}T{(i%24):02d}:00:00"
            
            signal = strategy.generate_signal(prices[:i+1])
            
            if pos_opened and strategy.symbol in self.positions:
                pos = self.positions[strategy.symbol]
                if price <= pos.stop_loss:
                    pnl = (price - pos.entry_price) * pos.quantity
                    self.cash += pos.quantity * price
                    self.trades.append(Trade(ts, strategy.symbol, "sell", price, pos.quantity, strategy.name, pnl))
                    del self.positions[strategy.symbol]
                    pos_opened = False
            
            if signal == "buy" and not pos_opened:
                qty = min(self.cash * 0.1 / price, 1.0)
                stop_loss = price * 0.98
                self.cash -= qty * price
                self.positions[strategy.symbol] = Position(strategy.symbol, "long", qty, price, ts, stop_loss)
                self.trades.append(Trade(ts, strategy.symbol, "buy", price, qty, strategy.name))
                pos_opened = True
            
            elif signal == "sell" and pos_opened:
                pos = self.positions[strategy.symbol]
                pnl = (price - pos.entry_price) * pos.quantity
                self.cash += pos.quantity * price
                self.trades.append(Trade(ts, strategy.symbol, "sell", price, pos.quantity, strategy.name, pnl))
                del self.positions[strategy.symbol]
                pos_opened = False
            
            equity = self.cash
            if pos_opened and strategy.symbol in self.positions:
                equity += self.positions[strategy.symbol].quantity * price
            self.equity_curve.append(equity)
        
        if pos_opened and strategy.symbol in self.positions:
            fp = prices[-1]
            pos = self.positions[strategy.symbol]
            pnl = (fp - pos.entry_price) * pos.quantity
            self.cash += pos.quantity * fp
            self.trades.append(Trade(f"2024-{len(prices)}T23:00", strategy.symbol, "sell", fp, pos.quantity, strategy.name, pnl))
            del self.positions[strategy.symbol]
        
        final = self.equity_curve[-1]
        total_return = ((final - self.capital) / self.capital) * 100
        peak = self.capital
        max_dd = 0
        for e in self.equity_curve:
            if e > peak: peak = e
            dd = (peak - e) / peak
            if dd > max_dd: max_dd = dd
        
        wins = sum(1 for t in self.trades if t.pnl > 0)
        losses = sum(1 for t in self.trades if t.pnl < 0)
        win_rate = (wins / (wins + losses) * 100) if (wins + losses) > 0 else 0
        
        daily_returns = []
        for i in range(1, len(self.equity_curve)):
            daily_returns.append((self.equity_curve[i] - self.equity_curve[i-1]) / self.equity_curve[i-1])
        
        sharpe = 0
        if len(daily_returns) > 1:
            std = np.std(daily_returns)
            if std > 0:
                sharpe = (np.mean(daily_returns) / std) * np.sqrt(252)
        
        return {
            "strategy": strategy.name,
            "style": strategy.style,
            "symbol": strategy.symbol,
            "total_return": round(total_return, 2),
            "max_drawdown": round(max_dd * 100, 2),
            "win_rate": round(win_rate, 1),
            "sharpe_ratio": round(sharpe, 2),
            "total_trades": len([t for t in self.trades if t.side == "buy"]),
            "final_equity": round(final, 2)
        }
    
    def _gen_prices(self, symbol: str, days: int) -> List[float]:
        bases = {"BTC/USDT": 65000, "ETH/USDT": 3500, "SOL/USDT": 140, "BNB/USDT": 600, "XRP/USDT": 0.62}
        base = bases.get(symbol, 100)
        prices = [base]
        trend = random.choice([-0.0001, 0, 0.0001])
        for _ in range(days * 24):
            change = np.exp(trend + 0.02 * np.random.randn())
            prices.append(prices[-1] * change)
        return prices

def main():
    engine = QuantEngine(capital=100000.0)
    strategies = [
        MACDStrategy(),
        RSIStrategy(),
        BollingerStrategy(),
        KDJStrategy(),
        ATRStopStrategy()
    ]
    
    print("=" * 70)
    print("GBT Quantitative Trading System v3.2 - Optimized")
    print(f"Period: 90 days | Capital: ${engine.capital:,.2f}")
    print("=" * 70)
    
    results = []
    for s in strategies:
        prices = engine._gen_prices(s.symbol, 90)
        r = engine.run_backtest(s, prices, 90)
        results.append(r)
        trade_status = f"Trades: {r['total_trades']}" if r['total_trades'] > 0 else "No trades"
        print(f"\n{r['strategy']} ({r['symbol']})")
        print(f"  Return: {r['total_return']:+.2f}% | DD: {r['max_drawdown']:.2f}% | Win: {r['win_rate']:.1f}%")
        print(f"  Sharpe: {r['sharpe_ratio']:.2f} | {trade_status}")
    
    print("\n" + "=" * 70)
    print("RANKING BY SHARPE:")
    for i, r in enumerate(sorted(results, key=lambda x: x['sharpe_ratio'], reverse=True), 1):
        status = "[+]" if r['total_trades'] > 0 else "[ ]"
        print(f"  {i}. {status} {r['strategy']}: {r['sharpe_ratio']:.2f} ({r['total_return']:+.2f}%)")
    
    # Save results
    with open(r'C:\Users\ADMIN\.openclaw-autoclaw\agents\gbt\workspace\.openclaw\tmp\backtest_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\nResults saved to backtest_results.json")

if __name__ == "__main__":
    main()
