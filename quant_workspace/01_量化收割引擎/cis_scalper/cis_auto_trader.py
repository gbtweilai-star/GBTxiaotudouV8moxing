#!/usr/bin/env python3
"""CIS 自动化快进快出交易系统 v3 - Binance Klines + Momentum"""
import asyncio, json, logging, time, uuid
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class CISTraderConfig:
    MOMENTUM_PERIOD: int = 14
    MOMENTUM_THRESHOLD: float = 0.02
    MAX_HOLD_TIME: int = 600
    STOP_LOSS_PCT: float = 0.05
    TAKE_PROFIT_PCT: float = 0.10
    INITIAL_CAPITAL: float = 100000.0
    RISK_PER_TRADE: float = 0.02
    MAX_POSITION_PCT: float = 0.10
    MAX_OPEN_POSITIONS: int = 5
    BINANCE_API: str = "https://api.binance.com"
    SYMBOLS: List[str] = None
    AUTO_TRADE: bool = True
    DRY_RUN: bool = True
    def __post_init__(self):
        if self.SYMBOLS is None:
            self.SYMBOLS = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT"]

class Position(BaseModel):
    position_id: str; symbol: str; entry_price: float; entry_time: float
    size: float; stop_loss: float; take_profit: float; high_watermark: float
    momentum_at_entry: float; atr: float = 0.0

class TradeRecord(BaseModel):
    type: str; position_id: str; symbol: str; price: float; size: float
    pnl_pct: float = 0.0; pnl_amount: float = 0.0; reason: str = ""
    hold_time: int = 0; momentum: float = 0.0; time: str

class CISAutoTrader:
    def __init__(self, config: CISTraderConfig):
        self.config = config
        self.positions: Dict[str, Position] = {}
        self.trade_history: List[TradeRecord] = []
        self.daily_pnl = 0.0
        self.total_trades = 0
        self.wins = 0
        self.losses = 0
        self.price_cache: Dict[str, float] = {}
        self.kline_cache: Dict[str, List[Dict]] = {}
        self.last_kline_update: Dict[str, float] = {}

    def fetch_klines(self, symbol: str, interval: str = "1m", limit: int = 20) -> List[Dict]:
        try:
            resp = requests.get(f"{self.config.BINANCE_API}/api/v3/klines",
                params={"symbol": symbol, "interval": interval, "limit": limit}, timeout=10)
            if resp.status_code == 200:
                return [{'close': float(k[4]), 'high': float(k[2]), 'low': float(k[3]), 'time': k[0]} for k in resp.json()]
        except Exception as e:
            logger.error(f"[KLINE] {symbol}: {e}")
        return []

    def update_market_data(self, symbol: str):
        klines = self.fetch_klines(symbol, "1m", 20)
        if klines:
            self.kline_cache[symbol] = klines
            self.price_cache[symbol] = klines[-1]['close']
            self.last_kline_update[symbol] = time.time()

    def calculate_momentum(self, symbol: str, period: int = None) -> float:
        if period is None:
            period = self.config.MOMENTUM_PERIOD
        klines = self.kline_cache.get(symbol, [])
        if len(klines) < period:
            period = min(len(klines), self.config.MOMENTUM_PERIOD)
        if period < 2:
            return 0.0
        first_close = klines[-period]['close']
        last_close = klines[-1]['close']
        return (last_close - first_close) / first_close

    def calculate_atr(self, symbol: str, period: int = 14) -> float:
        klines = self.kline_cache.get(symbol, [])
        if len(klines) < period + 1:
            return 0.0
        trs = []
        for i in range(-period, 0):
            high, low = klines[i]['high'], klines[i]['low']
            prev_close = klines[i-1]['close'] if i > -len(klines) else high
            tr = max(high - low, abs(high - prev_close), abs(low - prev_close))
            trs.append(tr)
        return sum(trs) / len(trs) if trs else 0.0

    def get_signal(self, symbol: str) -> Optional[Dict]:
        self.update_market_data(symbol)
        momentum = self.calculate_momentum(symbol)
        price = self.price_cache.get(symbol, 0)
        if momentum < self.config.MOMENTUM_THRESHOLD or price == 0:
            return None
        for pos in self.positions.values():
            if pos.symbol == symbol:
                return None
        strength = min(momentum / self.config.MOMENTUM_THRESHOLD, 1.0)
        atr = self.calculate_atr(symbol)
        return {'symbol': symbol, 'action': 'BUY', 'momentum': momentum, 'strength': strength,
                'price': price, 'atr': atr, 'confidence': min(momentum * 15, 0.95),
                'reason': f'{symbol} momentum {momentum*100:.2f}%'}

    def enter_position(self, signal: Dict) -> Optional[Position]:
        symbol = signal['symbol']
        price = signal['price']
        atr = signal.get('atr', price * 0.01)
        if len(self.positions) >= self.config.MAX_OPEN_POSITIONS:
            return None
        risk_per_unit = atr * 2 if atr > 0 else price * 0.01
        risk_amount = self.config.INITIAL_CAPITAL * self.config.RISK_PER_TRADE
        position_size_units = min(risk_amount / risk_per_unit, self.config.INITIAL_CAPITAL * self.config.MAX_POSITION_PCT / price)
        pos = Position(position_id=str(uuid.uuid4())[:8], symbol=symbol, entry_price=price,
                       entry_time=time.time(), size=position_size_units,
                       stop_loss=price * (1 - self.config.STOP_LOSS_PCT),
                       take_profit=price * (1 + self.config.TAKE_PROFIT_PCT),
                       high_watermark=price, momentum_at_entry=signal['momentum'], atr=atr)
        self.positions[pos.position_id] = pos
        self.total_trades += 1
        logger.info(f"[CIS] ENTRY {symbol} @ ${price:.2f} | ${position_size_units*price:.0f} | SL ${pos.stop_loss:.2f} | Mom {signal['momentum']*100:.1f}%")
        self.trade_history.append(TradeRecord(type='ENTRY', position_id=pos.position_id, symbol=symbol,
                                               price=price, size=position_size_units*price, momentum=signal['momentum'],
                                               time=datetime.now().isoformat()))
        return pos

    def check_exits(self) -> List[Dict]:
        exits = []
        for pid, pos in list(self.positions.items()):
            current_price = self.price_cache.get(pos.symbol, pos.entry_price)
            pnl_pct = (current_price - pos.entry_price) / pos.entry_price * 100
            hold_time = time.time() - pos.entry_time
            if current_price > pos.high_watermark:
                pos.high_watermark = current_price
            exit_reason = None
            if current_price <= pos.stop_loss:
                exit_reason = f"止损 {abs(pnl_pct):.1f}%"
            elif pnl_pct >= self.config.TAKE_PROFIT_PCT:
                exit_reason = f"止盈 {pnl_pct:.1f}%"
            elif hold_time >= self.config.MAX_HOLD_TIME:
                exit_reason = f"时间止盈 {int(hold_time)}s"
            else:
                cur_mom = self.calculate_momentum(pos.symbol)
                if pos.momentum_at_entry > 0.03 and cur_mom < -0.01:
                    exit_reason = f"动量反转 {cur_mom*100:.1f}%"
            if exit_reason:
                pnl_amount = pos.size * pnl_pct / 100
                self.daily_pnl += pnl_amount
                if pnl_pct > 0: self.wins += 1
                else: self.losses += 1
                self.trade_history.append(TradeRecord(type='EXIT', position_id=pid, symbol=pos.symbol,
                                                       price=current_price, size=pos.size*current_price,
                                                       pnl_pct=pnl_pct, pnl_amount=pnl_amount,
                                                       reason=exit_reason, hold_time=int(hold_time),
                                                       time=datetime.now().isoformat()))
                exits.append({'position_id': pid, 'symbol': pos.symbol, 'exit_price': current_price,
                              'pnl_pct': pnl_pct, 'pnl_amount': pnl_amount, 'reason': exit_reason, 'hold_time': int(hold_time)})
                logger.info(f"[CIS] EXIT {pos.symbol} {'PnL' if pnl_pct>0 else 'LOSS'} {abs(pnl_pct):.1f}% | {exit_reason}")
                del self.positions[pid]
        return exits

    def get_performance(self) -> Dict:
        exits = [t for t in self.trade_history if t.type == 'EXIT']
        total_pnl = sum(t.pnl_amount for t in exits)
        wins_list = [t for t in exits if t.pnl_amount > 0]
        losses_list = [t for t in exits if t.pnl_amount <= 0]
        return {'total_trades': self.total_trades, 'open_positions': len(self.positions),
                'wins': self.wins, 'losses': self.losses,
                'win_rate': self.wins / max(self.total_trades, 1) * 100,
                'daily_pnl': self.daily_pnl, 'total_pnl': total_pnl,
                'avg_win': sum(t.pnl_amount for t in wins_list) / max(len(wins_list), 1),
                'avg_loss': sum(t.pnl_amount for t in losses_list) / max(len(losses_list), 1),
                'profit_factor': abs(total_pnl / max(sum(abs(t.pnl_amount) for t in losses_list), 1))}

app = FastAPI(title="CIS Auto Trader v3", version="3.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
config = CISTraderConfig()
trader = CISAutoTrader(config)

@app.get("/")
async def root():
    return {"service": "CIS Auto Trader v3", "version": "3.0.0", "status": "running",
            "mode": "DRY-RUN", "symbols": config.SYMBOLS,
            "params": {"momentum_period": config.MOMENTUM_PERIOD, "momentum_threshold_pct": config.MOMENTUM_THRESHOLD*100,
                       "max_hold_seconds": config.MAX_HOLD_TIME, "stop_loss_pct": config.STOP_LOSS_PCT*100, "take_profit_pct": config.TAKE_PROFIT_PCT*100}}

@app.get("/api/status")
async def get_status():
    perf = trader.get_performance()
    positions = []
    for p in trader.positions.values():
        d = asdict(p)
        cp = trader.price_cache.get(p.symbol, p.entry_price)
        d['current_price'] = cp
        d['pnl_pct'] = (cp - p.entry_price) / p.entry_price * 100
        positions.append(d)
    return {**perf, "dry_run": config.DRY_RUN, "positions": positions}

@app.get("/api/signal/{symbol}")
async def get_signal(symbol: str):
    trader.update_market_data(symbol)
    momentum = trader.calculate_momentum(symbol)
    price = trader.price_cache.get(symbol, 0)
    signal = trader.get_signal(symbol)
    return {'symbol': symbol, 'price': price, 'momentum': momentum, 'momentum_pct': momentum*100,
            'threshold_pct': config.MOMENTUM_THRESHOLD*100, 'signal': signal}

@app.post("/api/trade/scan")
async def scan_all():
    for sym in config.SYMBOLS:
        trader.update_market_data(sym)
    signals, exits = [], trader.check_exits()
    for sym in config.SYMBOLS:
        s = trader.get_signal(sym)
        if s: signals.append(s)
    return {'entry_signals': signals, 'exit_signals': exits,
            'market_snapshot': {sym: {'price': trader.price_cache.get(sym, 0), 'momentum_pct': trader.calculate_momentum(sym)*100} for sym in config.SYMBOLS},
            'timestamp': datetime.now().isoformat()}

@app.post("/api/trade/execute")
async def execute_trade(request: dict):
    symbol = request.get('symbol')
    if not symbol: raise HTTPException(400, "需要symbol参数")
    trader.update_market_data(symbol)
    signal = trader.get_signal(symbol)
    if not signal:
        mom = trader.calculate_momentum(symbol)
        return {'ok': False, 'error': f'无信号 (momentum: {mom*100:.2f}%)', 'momentum': mom}
    pos = trader.enter_position(signal)
    return {'ok': True, 'dry_run': config.DRY_RUN, 'position': pos.model_dump() if pos else None}

@app.post("/api/trade/close/{position_id}")
async def close_trade(position_id: str):
    if position_id not in trader.positions: raise HTTPException(404, "持仓不存在")
    pos = trader.positions[position_id]
    cp = trader.price_cache.get(pos.symbol, pos.entry_price)
    pnl_pct = (cp - pos.entry_price) / pos.entry_price * 100
    pnl_amount = pos.size * pnl_pct / 100
    ht = int(time.time() - pos.entry_time)
    trader.trade_history.append(TradeRecord(type='EXIT', position_id=position_id, symbol=pos.symbol,
                                            price=cp, size=pos.size*cp, pnl_pct=pnl_pct, pnl_amount=pnl_amount,
                                            reason='手动平仓', hold_time=ht, time=datetime.now().isoformat()))
    if pnl_pct > 0: trader.wins += 1
    else: trader.losses += 1
    trader.daily_pnl += pnl_amount
    del trader.positions[position_id]
    return {'ok': True, 'closed': position_id, 'pnl_pct': pnl_pct, 'pnl_amount': pnl_amount}

@app.post("/api/trade/close-all")
async def close_all():
    pids = list(trader.positions.keys())
    for pid in pids:
        if pid in trader.positions:
            pos = trader.positions[pid]
            cp = trader.price_cache.get(pos.symbol, pos.entry_price)
            pnl_pct = (cp - pos.entry_price) / pos.entry_price * 100
            pnl_amount = pos.size * pnl_pct / 100
            ht = int(time.time() - pos.entry_time)
            trader.trade_history.append(TradeRecord(type='EXIT', position_id=pid, symbol=pos.symbol,
                                                    price=cp, size=pos.size*cp, pnl_pct=pnl_pct, pnl_amount=pnl_amount,
                                                    reason='全部平仓', hold_time=ht, time=datetime.now().isoformat()))
            if pnl_pct > 0: trader.wins += 1
            else: trader.losses += 1
            trader.daily_pnl += pnl_amount
            del trader.positions[pid]
    return {'ok': True, 'closed_count': len(pids)}

@app.get("/api/history")
async def get_history(limit: int = 20):
    return {'trades': [t.model_dump() for t in trader.trade_history[-limit:]], 'total': len(trader.trade_history)}

@app.get("/api/market")
async def get_market():
    for sym in config.SYMBOLS: trader.update_market_data(sym)
    snap = {}
    for sym in config.SYMBOLS:
        mom = trader.calculate_momentum(sym)
        snap[sym] = {'price': trader.price_cache.get(sym, 0), 'momentum_pct': mom*100,
                     'signal': 'BUY' if mom >= config.MOMENTUM_THRESHOLD else 'HOLD'}
    return snap

@app.post("/api/config")
async def update_config(request: dict):
    for key, value in request.items():
        if hasattr(config, key): setattr(config, key, value)
    # Sync to trader
    for key, value in request.items():
        if hasattr(trader.config, key): setattr(trader.config, key, value)
    return {'ok': True, 'config': {k: getattr(config, k) for k in dir(config) if not k.startswith('_')}}

if __name__ == "__main__":
    import uvicorn
    print("=" * 60)
    print("CIS 自动化快进快出交易系统 v3.0")
    print("=" * 60)
    print(f"模式: {'DRY-RUN' if config.DRY_RUN else 'LIVE'}")
    print(f"API: http://127.0.0.1:8092")
    print(f"动量: {config.MOMENTUM_PERIOD}根1mK线 | 阈值: {config.MOMENTUM_THRESHOLD*100:.1f}%")
    print(f"止损: {config.STOP_LOSS_PCT*100:.0f}% | 止盈: {config.TAKE_PROFIT_PCT*100:.0f}%")
    print(f"持仓: {config.MAX_HOLD_TIME}s | 最多: {config.MAX_OPEN_POSITIONS}个")
    print(f"标的: {', '.join(config.SYMBOLS)}")
    uvicorn.run(app, host="127.0.0.1", port=8092)
