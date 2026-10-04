#!/usr/bin/env python3
"""
CIS v41 - Crypto Fast In Fast Out Harvesting System
CIS Stock Trading Doctrine Applied to Crypto
Multi-factor resonance + Pyramid building + Dynamic stop loss
"""
import asyncio, json, logging, time, uuid, math
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("cis_v41")

@dataclass
class CISConfig:
    MOMENTUM_PERIOD: int = 14
    MOMENTUM_THRESHOLD: float = 0.0003
    MOMENTUM_MULTI_TF: bool = True
    RSI_PERIOD: int = 14
    STOP_LOSS_ATR_MULT: float = 1.5
    TAKE_PROFIT_ATR_MULT: float = 2.5
    MIN_STOP_PCT: float = 0.003
    MAX_HOLD_SECONDS: int = 600
    INITIAL_POSITION_PCT: float = 0.30
    MAX_ADDITIONS: int = 3
    MAX_OPEN_POSITIONS: int = 5
    CAPITAL: float = 100000.0
    RISK_PER_TRADE: float = 0.02
    VOL_RATIO_THRESHOLD: float = 0.3
    VOL_MA_PERIOD: int = 20
    MAX_CONSECUTIVE_LOSSES: int = 3
    LOSS_PAUSE_MINUTES: int = 15
    DAILY_LOSS_LIMIT_PCT: float = 0.05
    WIN_PAUSE_MINUTES: int = 5
    SYMBOLS: List[str] = None
    AUTO_SCAN_INTERVAL: int = 3
    DRY_RUN: bool = True
    BINANCE_API: str = "https://api.binance.com"
    
    def __post_init__(self):
        if self.SYMBOLS is None:
            self.SYMBOLS = [
                "BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT",
                "XRPUSDT", "DOGEUSDT", "ADAUSDT", "AVAXUSDT",
                "DOTUSDT", "LINKUSDT", "MATICUSDT", "LTCUSDT"
            ]

@dataclass
class MarketData:
    symbol: str
    price: float
    momentum_1m: float
    momentum_5m: float
    momentum_15m: float
    rsi: float
    bb_position: float
    vol_ratio: float
    atr: float
    atr_pct: float
    trend: str
    high_1m: float
    low_1m: float
    volume: float
    timestamp: float

@dataclass
class Signal:
    symbol: str
    direction: str
    confidence: float
    factors: List[str]
    momentum_1m: float
    momentum_5m: float
    rsi: float
    bb_pos: float
    vol_ratio: float
    entry_price: float
    suggested_sl: float
    suggested_tp: float

@dataclass
class Position:
    position_id: str
    symbol: str
    direction: str
    entry_price: float
    current_price: float
    size: float
    stop_loss: float
    take_profit: float
    high_watermark: float
    atr: float
    momentum_at_entry: float
    entry_time: float
    add_count: int = 0
    avg_entry: float = 0.0
    
    @property
    def pnl_pct(self):
        return (self.current_price - self.avg_entry) / self.avg_entry * 100
    
    @property
    def pnl_amount(self):
        return self.size * self.pnl_pct / 100
    
    @property
    def hold_time(self):
        return int(time.time() - self.entry_time)

@dataclass
class TradeRecord:
    type: str
    position_id: str
    symbol: str
    price: float
    size: float
    pnl_pct: float
    pnl_amount: float
    reason: str
    hold_time: int
    momentum: float
    timestamp: str

@dataclass
class RiskState:
    consecutive_losses: int = 0
    total_wins: int = 0
    total_losses: int = 0
    daily_pnl: float = 0.0
    daily_trades: int = 0
    is_paused: bool = False
    pause_reason: str = ""
    pause_until: float = 0.0
    last_win_time: float = 0.0

class MarketDataService:
    def __init__(self, config):
        self.config = config
        self.kline_cache = {}
    
    def fetch_klines(self, sym, interval, limit=100):
        try:
            r = requests.get(
                f"{self.config.BINANCE_API}/api/v3/klines",
                params={"symbol": sym, "interval": interval, "limit": limit},
                timeout=8
            )
            if r.status_code == 200:
                return r.json()
        except Exception as e:
            logger.debug(f"[KLINE] {sym} {interval}: {e}")
        return []
    
    def update_symbol(self, sym):
        k1 = self.fetch_klines(sym, "1m", 100)
        k5 = self.fetch_klines(sym, "5m", 50)
        k15 = self.fetch_klines(sym, "15m", 30)
        if not k1:
            return None
        c1 = [float(k[4]) for k in k1]
        h1 = [float(k[2]) for k in k1]
        l1 = [float(k[3]) for k in k1]
        v1 = [float(k[5]) for k in k1]
        c5 = [float(k[4]) for k in k5] if k5 else []
        c15 = [float(k[4]) for k in k15] if k15 else []
        price = c1[-1]
        mom1 = (c1[-1] - c1[-self.config.MOMENTUM_PERIOD]) / c1[-self.config.MOMENTUM_PERIOD] if len(c1) >= self.config.MOMENTUM_PERIOD else 0
        mom5 = (c5[-1] - c5[-5]) / c5[-5] if len(c5) >= 5 else 0
        mom15 = (c15[-1] - c15[-5]) / c15[-5] if len(c15) >= 5 else 0
        rsi = self._calc_rsi(c1[-self.config.RSI_PERIOD * 2:], self.config.RSI_PERIOD)
        atr = self._calc_atr(h1, l1, c1, self.config.RSI_PERIOD)
        atr_pct = atr / price * 100 if price > 0 else 0
        bb = self._calc_bb(c1, 20, 2.0)
        vol_avg = sum(v1[-20:]) / 20 if len(v1) >= 20 else sum(v1) / len(v1) if v1 else 1
        vr = v1[-1] / vol_avg if vol_avg > 0 else 1.0
        ma20 = sum(c1[-20:]) / 20
        ma50 = sum(c1[-50:]) / 50 if len(c1) >= 50 else ma20
        trend = "UP" if price > ma20 > ma50 else ("DN" if price < ma20 < ma50 else "FLAT")
        data = MarketData(sym, price, mom1, mom5, mom15, rsi, bb, vr, atr, atr_pct, trend, h1[-1], l1[-1], v1[-1], time.time())
        self.kline_cache[sym] = {"1m": k1, "5m": k5, "15m": k15, "data": data}
        return data
    
    def _calc_rsi(self, prices, period):
        if len(prices) < period + 1:
            return 50.0
        gains = [max(prices[i] - prices[i-1], 0) for i in range(1, len(prices))]
        losses = [max(prices[i-1] - prices[i], 0) for i in range(1, len(prices))]
        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period
        if avg_loss == 0:
            return 100.0
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))
    
    def _calc_atr(self, highs, lows, closes, period):
        if len(highs) < period + 1:
            return 0.0
        trs = []
        for i in range(-period, 0):
            h, l, pc = highs[i], lows[i], closes[i-1] if i > -len(closes) else highs[i]
            tr = max(h - l, abs(h - pc), abs(l - pc))
            trs.append(tr)
        return sum(trs) / len(trs)
    
    def _calc_bb(self, prices, period, mult):
        if len(prices) < period:
            return 50.0
        r = prices[-period:]
        m = sum(r) / period
        s = math.sqrt(sum((x - m)**2 for x in r) / period)
        if s == 0:
            return 50.0
        return (prices[-1] - (m - mult * s)) / (2 * mult * s) * 100

class SignalGenerator:
    def __init__(self, config, market):
        self.config = config
        self.market = market
    
    def generate(self, sym):
        cached = self.market.kline_cache.get(sym)
        if not cached or not cached.get("data"):
            return None
        d = cached["data"]
        ls, lf = self._score_long(d)
        ss, sf = self._score_short(d)
        if ls >= 0.55 and ls > ss:
            sl = d.price - max(d.atr * self.config.STOP_LOSS_ATR_MULT, d.price * self.config.MIN_STOP_PCT)
            tp = d.price + max(d.atr * self.config.TAKE_PROFIT_ATR_MULT, d.price * 0.01)
            return Signal(sym, "LONG", min(ls, 1.0), lf, d.momentum_1m, d.momentum_5m, d.rsi, d.bb_position, d.vol_ratio, d.price, sl, tp)
        if ss >= 0.55 and ss > ls:
            sl = d.price + max(d.atr * self.config.STOP_LOSS_ATR_MULT, d.price * self.config.MIN_STOP_PCT)
            tp = d.price - max(d.atr * self.config.TAKE_PROFIT_ATR_MULT, d.price * 0.01)
            return Signal(sym, "SHORT", min(ss, 1.0), sf, d.momentum_1m, d.momentum_5m, d.rsi, d.bb_position, d.vol_ratio, d.price, sl, tp)
        return None
    
    def _score_long(self, d):
        f, s = [], 0.0
        if d.momentum_1m >= self.config.MOMENTUM_THRESHOLD:
            f.append(f"动量+{d.momentum_1m*100:.2f}%")
            s += 0.18
        elif d.momentum_1m >= 0:
            f.append(f"动量弱+{d.momentum_1m*100:.2f}%")
            s += 0.06
        if self.config.MOMENTUM_MULTI_TF:
            if d.momentum_5m > 0 and d.momentum_15m > 0:
                f.append("多TF动量确认")
                s += 0.12
            elif d.momentum_5m > 0:
                s += 0.05
        if 40 <= d.rsi <= 65:
            f.append(f"RSI={d.rsi:.0f}中性偏多")
            s += 0.15
        elif 30 <= d.rsi < 40:
            f.append(f"RSI={d.rsi:.0f}超卖机会")
            s += 0.20
        elif d.rsi > 70:
            f.append(f"RSI={d.rsi:.0f}超买危险")
            s -= 0.15
        if 20 <= d.bb_position <= 60:
            f.append(f"BB位{d.bb_position:.0f}%合理")
            s += 0.12
        elif d.bb_position > 80:
            f.append("BB顶部警戒")
            s -= 0.15
        elif d.bb_position < 20:
            f.append("BB底部机会")
            s += 0.10
        if d.vol_ratio >= 0.5:
            f.append(f"量比{d.vol_ratio:.1f}x")
            s += 0.10
        if d.trend == "UP":
            f.append("趋势向上")
            s += 0.10
        elif d.trend == "DN":
            s -= 0.08
        return max(s, 0.0), f
    
    def _score_short(self, d):
        f, s = [], 0.0
        if d.momentum_1m <= -self.config.MOMENTUM_THRESHOLD:
            f.append(f"动量-{abs(d.momentum_1m)*100:.2f}%")
            s += 0.18
        elif d.momentum_1m <= 0:
            s += 0.06
        if self.config.MOMENTUM_MULTI_TF:
            if d.momentum_5m < 0 and d.momentum_15m < 0:
                f.append("多TF动量空头")
                s += 0.12
        if 35 <= d.rsi <= 60:
            s += 0.15
        elif d.rsi < 30:
            f.append(f"RSI={d.rsi:.0f}超卖反弹风险")
            s -= 0.15
        elif d.rsi > 70:
            f.append(f"RSI={d.rsi:.0f}超买确认")
            s += 0.20
        if d.bb_position >= 60 and d.bb_position <= 80:
            s += 0.12
        elif d.bb_position > 85:
            f.append("BB顶部")
            s += 0.10
        if d.vol_ratio >= 0.5:
            s += 0.08
        if d.trend == "DN":
            f.append("趋势向下")
            s += 0.10
        elif d.trend == "UP":
            s -= 0.08
        return max(s, 0.0), f

class PositionManager:
    def __init__(self, config):
        self.config = config
        self.positions = {}
    
    def open_position(self, signal, is_add=False):
        if not is_add and len(self.positions) >= self.config.MAX_OPEN_POSITIONS:
            return None
        price = signal.entry_price
        if price <= 0:
            return None
        if is_add:
            pos = self.positions.get(signal.symbol)
            if not pos or pos.add_count >= self.config.MAX_ADDITIONS:
                return None
            add_size = pos.size * 0.5
            new_size = pos.size + add_size
            if new_size > self.config.CAPITAL * self.config.INITIAL_POSITION_PCT * 1.5:
                return None
            pos.avg_entry = (pos.avg_entry * pos.size + price * add_size) / new_size
            pos.size = new_size
            pos.add_count += 1
            pos.stop_loss = max(pos.stop_loss, price * 0.997)
            return pos
        atr = abs(price - signal.suggested_sl) if signal.suggested_sl else price * 0.005
        if atr == 0:
            atr = price * 0.005
        risk_amt = self.config.CAPITAL * self.config.RISK_PER_TRADE
        size = min(risk_amt / atr * price * 0.1, self.config.CAPITAL * self.config.INITIAL_POSITION_PCT)
        sl = signal.suggested_sl if signal.suggested_sl else price * 0.997
        tp = signal.suggested_tp if signal.suggested_tp else price * 1.005
        pos = Position(str(uuid.uuid4())[:8], signal.symbol, signal.direction, price, price, size, sl, tp, price, atr, signal.momentum_1m, time.time(), 0, price)
        self.positions[pos.position_id] = pos
        return pos
    
    def get_open_symbols(self):
        return {p.symbol for p in self.positions.values()}
    
    def get_position(self, sym):
        for p in self.positions.values():
            if p.symbol == sym:
                return p
        return None

class ExitDecision:
    def __init__(self, config):
        self.config = config
    
    def check_exit(self, pos, data):
        if pos.direction == "LONG":
            pnl_pct = (data.price - pos.avg_entry) / pos.avg_entry * 100
        else:
            pnl_pct = (pos.avg_entry - data.price) / pos.avg_entry * 100
        hold_time = time.time() - pos.entry_time
        if data.price > pos.high_watermark:
            pos.high_watermark = data.price
        if pos.direction == "LONG" and data.price <= pos.stop_loss:
            return f"止损 {pnl_pct:.2f}%"
        if pos.direction == "SHORT" and data.price >= pos.stop_loss:
            return f"止损 {pnl_pct:.2f}%"
        if pos.direction == "LONG" and data.price >= pos.take_profit:
            return f"止盈 {pnl_pct:.2f}%"
        if pos.direction == "SHORT" and data.price <= pos.take_profit:
            return f"止盈 {pnl_pct:.2f}%"
        if hold_time >= self.config.MAX_HOLD_SECONDS:
            return f"时间截止 {int(hold_time)}s"
        if pos.direction == "LONG":
            if pos.momentum_at_entry > 0.005 and data.momentum_1m < -0.003:
                return f"动量反转 {data.momentum_1m*100:.2f}%"
            dd = (pos.high_watermark - data.price) / pos.high_watermark
            if dd > pos.atr / pos.entry_price * 2 and pnl_pct > 0:
                return f"移动止盈 回撤{dd*100:.1f}%"
            if data.trend == "DN" and pnl_pct > 0.5:
                return "趋势逆转锁利"
        else:
            if pos.momentum_at_entry < -0.005 and data.momentum_1m > 0.003:
                return f"动量反转 {data.momentum_1m*100:.2f}%"
            dd = (data.price - pos.high_watermark) / pos.high_watermark if pos.high_watermark > 0 else 0
            if dd > pos.atr / pos.entry_price * 2 and pnl_pct > 0:
                return f"移动止盈 回撤{dd*100:.1f}%"
            if data.trend == "UP" and pnl_pct > 0.5:
                return "趋势逆转锁利"
        return None

class RiskController:
    def __init__(self, config):
        self.config = config
        self.state = RiskState()
        self.last_reset = time.time()
    
    def should_allow(self):
        now = time.time()
        if now - self.last_reset > 86400:
            self.state.daily_pnl = 0.0
            self.state.daily_trades = 0
            self.last_reset = now
        if self.state.is_paused:
            if now >= self.state.pause_until:
                self.state.is_paused = False
                self.state.consecutive_losses = 0
                return True, "暂停结束"
            return False, self.state.pause_reason
        if self.state.daily_pnl <= -self.config.CAPITAL * self.config.DAILY_LOSS_LIMIT_PCT:
            self.state.is_paused = True
            self.state.pause_reason = f"日亏损${abs(self.state.daily_pnl):.0f}"
            self.state.pause_until = now + 3600
            return False, self.state.pause_reason
        return True, "允许交易"
    
    def record(self, pnl_pct, is_win):
        if is_win:
            self.state.total_wins += 1
            self.state.consecutive_losses = 0
            self.state.last_win_time = time.time()
        else:
            self.state.total_losses += 1
            self.state.consecutive_losses += 1
            if self.state.consecutive_losses >= self.config.MAX_CONSECUTIVE_LOSSES:
                self.state.is_paused = True
                self.state.pause_reason = f"连续{self.state.consecutive_losses}次亏损"
                self.state.pause_until = time.time() + self.config.LOSS_PAUSE_MINUTES * 60
    
    def update_pnl(self, pnl):
        self.state.daily_pnl += pnl
        self.state.daily_trades += 1

class CISHarvestingV41:
    def __init__(self, config=None):
        self.config = config or CISConfig()
        self.market = MarketDataService(self.config)
        self.signal_gen = SignalGenerator(self.config, self.market)
        self.pos_mgr = PositionManager(self.config)
        self.exit_dec = ExitDecision(self.config)
        self.risk_ctrl = RiskController(self.config)
        self.history = []
        self.wins = 0
        self.losses = 0
        self.total_pnl = 0.0
        self.scan_count = 0
    
    def scan_all(self):
        self.scan_count += 1
        for sym in self.config.SYMBOLS:
            self.market.update_symbol(sym)
        allowed, reason = self.risk_ctrl.should_allow()
        if not allowed:
            return {"warning": reason, "signals": [], "exits": [], "market": self._fmt_market(), "status": self.get_status()}
        signals, exits = [], []
        for sym in self.config.SYMBOLS:
            sig = self.signal_gen.generate(sym)
            if sig and sym not in self.pos_mgr.get_open_symbols():
                signals.append(self._fmt_sig(sig))
            elif sig and sym in self.pos_mgr.get_open_symbols():
                pos = self.pos_mgr.get_position(sym)
                if pos and pos.add_count < self.config.MAX_ADDITIONS and pos.pnl_pct >= 1.0:
                    signals.append({"symbol": sym, "action": "ADD", "confidence": 0.7, "reason": f"浮盈{pos.pnl_pct:.1f}%加仓机会"})
        for pid, pos in list(self.pos_mgr.positions.items()):
            data = self.market.update_symbol(pos.symbol)
            if data:
                ex = self.exit_dec.check_exit(pos, data)
                if ex:
                    pnl_pct = pos.pnl_pct
                    pnl_amt = pos.pnl_amount
                    hold = pos.hold_time
                    self.history.append(TradeRecord("EXIT", pid, pos.symbol, data.price, pos.size, pnl_pct, pnl_amt, ex, hold, data.momentum_1m, datetime.now().isoformat()))
                    self.total_pnl += pnl_amt
                    is_win = pnl_pct > 0
                    if is_win:
                        self.wins += 1
                    else:
                        self.losses += 1
                    self.risk_ctrl.record(pnl_pct, is_win)
                    self.risk_ctrl.update_pnl(pnl_amt)
                    exits.append({"position_id": pid, "symbol": pos.symbol, "direction": pos.direction, "price": data.price, "pnl_pct": pnl_pct, "pnl_amount": pnl_amt, "reason": ex, "hold_time": hold})
                    logger.info(f"[CIS] EXIT {pos.symbol} {'WIN' if is_win else 'LOSS'} {pnl_pct:+.2f}% | {ex}")
                    del self.pos_mgr.positions[pid]
        return {"signals": signals, "exits": exits, "market": self._fmt_market(), "status": self.get_status(), "scan_count": self.scan_count}
    
    def execute_signal(self, req):
        sym = req.get("symbol")
        action = req.get("action", "BUY")
        allowed, reason = self.risk_ctrl.should_allow()
        if not allowed:
            return {"ok": False, "error": reason}
        data = self.market.update_symbol(sym)
        if not data:
            return {"ok": False, "error": "无法获取市场数据"}
        if action == "ADD":
            pos = self.pos_mgr.get_position(sym)
            if not pos:
                return {"ok": False, "error": "无对应持仓"}
            add_size = pos.size * 0.5
            pos.size += add_size
            pos.avg_entry = (pos.avg_entry * (pos.size - add_size) + data.price * add_size) / pos.size
            pos.add_count += 1
            pos.stop_loss = max(pos.stop_loss, data.price * 0.997)
            self.history.append(TradeRecord("ADD", pos.position_id, sym, data.price, add_size, pos.pnl_pct, pos.pnl_amount, f"浮盈加仓 #{pos.add_count}", pos.hold_time, data.momentum_1m, datetime.now().isoformat()))
            logger.info(f"[CIS] ADD {sym} #{pos.add_count} @ ${data.price:.2f}")
            return {"ok": True, "type": "ADD", "position_id": pos.position_id, "size": pos.size, "dry_run": self.config.DRY_RUN}
        sig = self.signal_gen.generate(sym)
        if not sig:
            return {"ok": False, "error": "无有效信号"}
        if sym in self.pos_mgr.get_open_symbols():
            return {"ok": False, "error": f"{sym} 已有持仓"}
        pos = self.pos_mgr.open_position(sig)
        if not pos:
            return {"ok": False, "error": "仓位超限"}
        self.history.append(TradeRecord("ENTRY", pos.position_id, sym, pos.entry_price, pos.size, 0, 0, "开仓", 0, sig.momentum_1m, datetime.now().isoformat()))
        logger.info(f"[CIS] ENTRY {sym} {sig.direction} @ ${pos.entry_price:.2f} SL ${pos.stop_loss:.2f} Conf {sig.confidence*100:.0f}%")
        return {"ok": True, "dry_run": self.config.DRY_RUN, "position": self._fmt_pos(pos)}
    
    def close_position(self, pid):
        if pid not in self.pos_mgr.positions:
            return {"ok": False, "error": "持仓不存在"}
        pos = self.pos_mgr.positions[pid]
        data = self.market.update_symbol(pos.symbol)
        cp = data.price if data else pos.entry_price
        pnl_pct = pos.pnl_pct
        pnl_amt = pos.pnl_amount
        self.history.append(TradeRecord("EXIT", pid, pos.symbol, cp, pos.size, pnl_pct, pnl_amt, "手动平仓", pos.hold_time, data.momentum_1m if data else 0, datetime.now().isoformat()))
        is_win = pnl_pct > 0
        self.total_pnl += pnl_amt
        if is_win:
            self.wins += 1
        else:
            self.losses += 1
        self.risk_ctrl.record(pnl_pct, is_win)
        self.risk_ctrl.update_pnl(pnl_amt)
        del self.pos_mgr.positions[pid]
        logger.info(f"[CIS] CLOSE {pos.symbol} {'WIN' if is_win else 'LOSS'} {pnl_pct:+.2f}%")
        return {"ok": True, "symbol": pos.symbol, "pnl_pct": pnl_pct, "pnl_amount": pnl_amt}
    
    def close_all(self):
        pids = list(self.pos_mgr.positions.keys())
        for pid in pids:
            self.close_position(pid)
        return {"ok": True, "closed": len(pids)}
    
    def get_status(self):
        positions = []
        for p in self.pos_mgr.positions.values():
            cd = self.market.kline_cache.get(p.symbol, {}).get("data")
            cp = cd.price if cd else p.entry_price
            positions.append(self._fmt_pos(p, cp))
        perf = {"total_trades": self.wins + self.losses, "open_positions": len(positions), "wins": self.wins, "losses": self.losses, "win_rate": self.wins / max(self.wins + self.losses, 1) * 100, "total_pnl": self.total_pnl, "scan_count": self.scan_count}
        rs = self.risk_ctrl.state
        risk = {"consecutive_losses": rs.consecutive_losses, "is_paused": rs.is_paused, "pause_reason": rs.pause_reason, "daily_pnl": rs.daily_pnl, "daily_trades": rs.daily_trades}
        return {**perf, "positions": positions, "risk": risk, "dry_run": self.config.DRY_RUN}
    
    def _fmt_market(self):
        result = {}
        for sym in self.config.SYMBOLS:
            cd = self.market.kline_cache.get(sym, {}).get("data")
            if cd:
                result[sym] = {"price": cd.price, "momentum_1m": cd.momentum_1m * 100, "rsi": cd.rsi, "atr_pct": cd.atr_pct, "trend": cd.trend}
        return result
    
    def _fmt_sig(self, s):
        return {"symbol": s.symbol, "action": s.direction, "confidence": round(s.confidence, 3), "momentum_1m": round(s.momentum_1m * 100, 3), "momentum_5m": round(s.momentum_5m * 100, 3), "rsi": round(s.rsi, 1), "bb_pos": round(s.bb_pos, 1), "vol_ratio": round(s.vol_ratio, 2), "reasons": s.factors, "entry_price": round(s.entry_price, 4), "suggested_sl": round(s.suggested_sl, 4), "suggested_tp": round(s.suggested_tp, 4)}
    
    def _fmt_pos(self, p, cp=None):
        c = cp or p.current_price
        return {"position_id": p.position_id, "symbol": p.symbol, "direction": p.direction, "entry_price": round(p.entry_price, 4), "current_price": round(c, 4), "avg_entry": round(p.avg_entry, 4), "stop_loss": round(p.stop_loss, 4), "take_profit": round(p.take_profit, 4), "size_usdt": round(p.size, 2), "pnl_pct": round(p.pnl_pct, 2), "pnl_amount": round(p.pnl_amount, 2), "hold_time": p.hold_time, "add_count": p.add_count, "high_watermark": round(p.high_watermark, 4)}

app = FastAPI(title="CIS v41 Crypto Harvesting", version="41.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

cfg = CISConfig()
trader = CISHarvestingV41(cfg)
auto_running = False

@app.on_event("startup")
async def startup():
    logger.info("[CIS] v41 started successfully")

@app.get("/")
async def root():
    return {"service": "CIS v41 Crypto Harvesting", "version": "41.0.0", "mode": "DRY-RUN" if cfg.DRY_RUN else "LIVE", "architecture": "多因子共振 -> 金字塔建仓 -> 动态止损 -> 快进快出"}

@app.get("/api/status")
async def status():
    return trader.get_status()

@app.get("/api/market")
async def market():
    return trader._fmt_market()

@app.get("/api/signal/{symbol}")
async def signal(symbol: str):
    trader.market.update_symbol(symbol)
    sig = trader.signal_gen.generate(symbol)
    return {"symbol": symbol, "signal": trader._fmt_sig(sig) if sig else None}

@app.post("/api/trade/scan")
async def scan_all():
    return trader.scan_all()

@app.post("/api/trade/execute")
async def execute(req: dict):
    return trader.execute_signal(req)

@app.post("/api/trade/close/{position_id}")
async def close(position_id: str):
    return trader.close_position(position_id)

@app.post("/api/trade/close-all")
async def close_all():
    return trader.close_all()

@app.post("/api/trade/auto-scan/start")
async def start_auto():
    global auto_running
    auto_running = True
    asyncio.create_task(_auto_loop())
    return {"ok": True, "message": "自动扫描已启动"}

@app.post("/api/trade/auto-scan/stop")
async def stop_auto():
    global auto_running
    auto_running = False
    return {"ok": True, "message": "自动扫描已停止"}

@app.get("/api/history")
async def history(limit: int = 50):
    trades = trader.history[-limit:]
    return {"trades": [asdict(t) for t in trades], "total": len(trader.history), "wins": trader.wins, "losses": trader.losses, "win_rate": trader.wins / max(trader.wins + trader.losses, 1) * 100}

@app.get("/api/risk/status")
async def risk_status():
    s = trader.risk_ctrl.state
    return {"consecutive_losses": s.consecutive_losses, "is_paused": s.is_paused, "pause_reason": s.pause_reason, "daily_pnl": s.daily_pnl, "daily_trades": s.daily_trades}

@app.post("/api/config")
async def update_config(req: dict):
    for key, value in req.items():
        if hasattr(cfg, key):
            setattr(cfg, key, value)
    return {"ok": True, "config": {k: getattr(cfg, k) for k in dir(cfg) if not k.startswith("_")}}

@app.get("/api/performance")
async def performance():
    exits = [t for t in trader.history if t.type == "EXIT"]
    if not exits:
        return {"total_trades": 0, "win_rate": 0, "total_pnl": 0, "avg_hold_time": 0}
    wins = [t for t in exits if t.pnl_pct > 0]
    losses = [t for t in exits if t.pnl_pct <= 0]
    return {"total_trades": len(exits), "wins": len(wins), "losses": len(losses), "win_rate": len(wins) / len(exits) * 100 if exits else 0, "total_pnl": sum(t.pnl_amount for t in exits), "avg_pnl_pct": sum(t.pnl_pct for t in exits) / len(exits), "avg_hold_time": sum(t.hold_time for t in exits) / len(exits), "avg_win": sum(t.pnl_pct for t in wins) / len(wins) if wins else 0, "avg_loss": sum(t.pnl_pct for t in losses) / len(losses) if losses else 0}

async def _auto_loop():
    global auto_running
    while auto_running:
        try:
            trader.scan_all()
        except Exception as e:
            logger.error(f"[AUTO] {e}")
        await asyncio.sleep(cfg.AUTO_SCAN_INTERVAL)

connected_clients = {}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    client_id = f"client_{int(time.time()*1000)}"
    connected_clients[client_id] = websocket
    logger.info(f"[WS] Client {client_id} connected")
    try:
        market = trader._fmt_market()
        status = trader.get_status()
        signals = {}
        for sym in cfg.SYMBOLS:
            sig = trader.signal_gen.generate(sym)
            if sig:
                signals[sym] = trader._fmt_sig(sig)
        await websocket.send_json({"type": "init", "market": market, "status": status, "signals": signals, "timestamp": int(time.time() * 1000)})
        last_push = 0
        while True:
            try:
                msg = await asyncio.wait_for(websocket.receive_text(), timeout=5)
                if msg == "ping":
                    await websocket.send_json({"type": "pong"})
            except asyncio.TimeoutError:
                pass
            now = time.time()
            if now - last_push >= cfg.AUTO_SCAN_INTERVAL:
                last_push = now
                try:
                    market = trader._fmt_market()
                    status = trader.get_status()
                    new_signals = {}
                    for sym in cfg.SYMBOLS:
                        sig = trader.signal_gen.generate(sym)
                        if sig:
                            new_signals[sym] = trader._fmt_sig(sig)
                    await websocket.send_json({"type": "update", "market": market, "status": status, "signals": new_signals, "timestamp": int(now * 1000)})
                except Exception as e:
                    logger.error(f"[WS] Push error: {e}")
            await asyncio.sleep(0.1)
    except WebSocketDisconnect:
        connected_clients.pop(client_id, None)
        logger.info(f"[WS] Client {client_id} disconnected")
    except Exception as e:
        logger.error(f"[WS] Error: {e}")
        try:
            await websocket.close()
        except:
            pass

if __name__ == "__main__":
    import uvicorn
    print("=" * 60)
    print("  CIS v41 - Crypto Fast In Fast Out Harvesting System")
    print("  CIS Stock Trading Doctrine Applied to Crypto")
    print("=" * 60)
    print(f"  Mode: {'DRY-RUN (模拟)' if cfg.DRY_RUN else 'LIVE (实盘)'}")
    print(f"  API:  http://127.0.0.1:8092")
    print(f"  WS:   ws://127.0.0.1:8092/ws")
    print(f"  交易对: {', '.join(cfg.SYMBOLS[:6])} ...")
    print(f"  动量周期: {cfg.MOMENTUM_PERIOD}K | 阈值: {cfg.MOMENTUM_THRESHOLD*100:.2f}%")
    print(f"  止损: ATRx{cfg.STOP_LOSS_ATR_MULT} | 止盈: ATRx{cfg.TAKE_PROFIT_ATR_MULT}")
    print(f"  最大持仓: {cfg.MAX_HOLD_SECONDS}s | 最多{cfg.MAX_OPEN_POSITIONS}个")
    print(f"  风控: 连续{cfg.MAX_CONSECUTIVE_LOSSES}亏暂停{cfg.LOSS_PAUSE_MINUTES}min | 日亏{cfg.DAILY_LOSS_LIMIT_PCT*100:.0f}%")
    print("=" * 60)
    uvicorn.run(app, host="127.0.0.1", port=8092)
