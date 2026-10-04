#!/usr/bin/env python3
"""CIS v4.0 — 多维度快进快出收割系统
架构: 信号生成 → 确认过滤 → 仓位管理 → 退出决策 → 风控保护
"""
import asyncio, json, logging, time, uuid, math
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

# ==================== 数据结构 ====================

@dataclass
class CISTraderConfig:
    # 动量参数
    MOMENTUM_PERIOD: int = 14
    MOMENTUM_THRESHOLD: float = 0.0002  # 0.02%
    # 时间框架
    TF_1M: str = "1m"
    TF_5M: str = "5m"
    # 止损止盈 (动态)
    STOP_LOSS_MULT: float = 1.5   # ATR倍数
    TAKE_PROFIT_MULT: float = 2.0  # 盈亏比 2:1
    MIN_STOP_PCT: float = 0.003   # 最低0.3%
    # 持仓
    MAX_HOLD_TIME: int = 300
    MAX_OPEN_POSITIONS: int = 3
    INITIAL_CAPITAL: float = 100000.0
    RISK_PER_TRADE: float = 0.02
    # 成交量
    VOL_CONFIRM_RATIO: float = 0.4
    # RSI
    RSI_PERIOD: int = 14
    RSI_OVERBOUGHT: float = 70
    RSI_OVERSOLD: float = 30
    # 布林
    BB_PERIOD: int = 20
    BB_STD: int = 2
    # 风控
    MAX_CONSECUTIVE_LOSSES: int = 3
    LOSS_PAUSE_MINUTES: int = 10
    DAILY_LOSS_LIMIT: float = 0.05
    # 交易对
    SYMBOLS: List[str] = None
    AUTO_TRADE: bool = True
    DRY_RUN: bool = True
    BINANCE_API: str = "https://api.binance.com"
    
    def __post_init__(self):
        if self.SYMBOLS is None:
            self.SYMBOLS = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT"]


@dataclass
class Signal:
    symbol: str
    action: str  # BUY
    confidence: float
    momentum_1m: float
    momentum_5m: float
    rsi: float
    atr: float
    atr_pct: float
    bb_position: float  # 0-100
    vol_ratio: float
    trend: str  # UP/DN
    reasons: List[str]
    price: float = 0.0  # Entry price


@dataclass
class Position:
    position_id: str
    symbol: str
    entry_price: float
    entry_time: float
    size: float
    stop_loss: float
    take_profit: float
    high_watermark: float
    atr: float
    momentum_at_entry: float
    is_adaptive_stop: bool  # 移动止盈标记


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
    time: str


@dataclass
class RiskState:
    consecutive_losses: int
    total_losses: int
    total_wins: int
    daily_pnl: float
    daily_trades: int
    is_paused: bool
    pause_reason: str
    pause_until: float


# ==================== 市场数据服务 ====================

class MarketDataService:
    def __init__(self, config: CISTraderConfig):
        self.config = config
        self.price_cache: Dict[str, float] = {}
        self.kline_cache: Dict[str, Dict] = {}
        self.last_update: Dict[str, float] = {}
    
    def fetch_klines(self, symbol: str, interval: str, limit: int = 100) -> List[Dict]:
        try:
            resp = requests.get(f"{self.config.BINANCE_API}/api/v3/klines",
                params={"symbol": symbol, "interval": interval, "limit": limit}, timeout=10)
            if resp.status_code == 200:
                return [{
                    'close': float(k[4]), 'high': float(k[2]), 'low': float(k[3]),
                    'volume': float(k[5]), 'time': k[0]
                } for k in resp.json()]
        except Exception as e:
            logger.error(f"[KLINE] {symbol} {interval}: {e}")
        return []
    
    def update_market_data(self, symbol: str):
        klines_1m = self.fetch_klines(symbol, self.config.TF_1M, 100)
        klines_5m = self.fetch_klines(symbol, self.config.TF_5M, 30)
        if klines_1m:
            self.kline_cache[symbol] = {'1m': klines_1m, '5m': klines_5m}
            self.price_cache[symbol] = klines_1m[-1]['close']
            self.last_update[symbol] = time.time()
    
    def get_indicators(self, symbol: str) -> Dict:
        """计算所有技术指标"""
        data = self.kline_cache.get(symbol, {})
        if not data.get('1m'):
            return {}
        klines = data['1m']
        klines5 = data.get('5m', [])
        
        closes = [k['close'] for k in klines]
        highs = [k['high'] for k in klines]
        lows = [k['low'] for k in klines]
        volumes = [k['volume'] for k in klines]
        
        # 动量
        mom_1m = (closes[-1] - closes[-self.config.MOMENTUM_PERIOD]) / closes[-self.config.MOMENTUM_PERIOD] if len(closes) >= self.config.MOMENTUM_PERIOD else 0
        mom_5m = (klines5[-1]['close'] - klines5[-5]['close']) / klines5[-5]['close'] if len(klines5) >= 5 else 0
        
        # RSI
        gains = [max(closes[i] - closes[i-1], 0) for i in range(1, min(self.config.RSI_PERIOD + 1, len(closes)))]
        losses = [max(closes[i-1] - closes[i], 0) for i in range(1, min(self.config.RSI_PERIOD + 1, len(closes)))]
        avg_gain = sum(gains) / self.config.RSI_PERIOD if gains else 0
        avg_loss = sum(losses) / self.config.RSI_PERIOD if losses else 0.001
        rsi = 100 - (100 / (1 + avg_gain / avg_loss))
        
        # ATR
        trs = []
        for i in range(-self.config.RSI_PERIOD, 0):
            high, low = highs[i], lows[i]
            prev_close = closes[i-1] if i > -len(closes) else high
            tr = max(high - low, abs(high - prev_close), abs(low - prev_close))
            trs.append(tr)
        atr = sum(trs) / len(trs) if trs else 0
        atr_pct = atr / closes[-1] * 100 if closes[-1] > 0 else 0
        
        # 布林带
        std = (sum((c - closes[-1])**2 for c in closes[-self.config.BB_PERIOD:]) / self.config.BB_PERIOD) ** 0.5
        bb_upper = closes[-1] + self.config.BB_STD * std
        bb_lower = closes[-1] - self.config.BB_STD * std
        bb_mid = closes[-1]  # 简化为中轨
        bb_position = (closes[-1] - bb_lower) / (bb_upper - bb_lower) * 100 if bb_upper != bb_lower else 50
        
        # 成交量比
        vol_avg = sum(volumes[-20:]) / 20 if len(volumes) >= 20 else sum(volumes) / len(volumes)
        vol_ratio = volumes[-1] / vol_avg if vol_avg > 0 else 1
        
        # 均线趋势
        ma20 = sum(closes[-20:]) / 20
        ma50 = sum(closes[-50:]) / 50 if len(closes) >= 50 else ma20
        trend = "UP" if closes[-1] > ma20 > ma50 else ("DN" if closes[-1] < ma20 < ma50 else "FLAT")
        
        return {
            'momentum_1m': mom_1m, 'momentum_5m': mom_5m,
            'rsi': rsi, 'atr': atr, 'atr_pct': atr_pct,
            'bb_position': bb_position, 'vol_ratio': vol_ratio,
            'trend': trend, 'price': closes[-1]
        }
    
    def get_market_snapshot(self) -> Dict:
        snap = {}
        for sym in self.config.SYMBOLS:
            self.update_market_data(sym)
            ind = self.get_indicators(sym)
            if ind:
                snap[sym] = ind
        return snap


# ==================== 信号生成器 ====================

class SignalGenerator:
    def __init__(self, config: CISTraderConfig, market: MarketDataService):
        self.config = config
        self.market = market
    
    def generate(self, symbol: str) -> Optional[Signal]:
        """生成原始信号"""
        indicators = self.market.get_indicators(symbol)
        if not indicators:
            return None
        
        mom_1m = indicators['momentum_1m']
        mom_5m = indicators['momentum_5m']
        rsi = indicators['rsi']
        atr_pct = indicators['atr_pct']
        bb_pos = indicators['bb_position']
        vol_ratio = indicators['vol_ratio']
        trend = indicators['trend']
        price = indicators['price']
        
        reasons = []
        score = 0
        
        # 动量脉冲检查
        if mom_1m >= self.config.MOMENTUM_THRESHOLD:
            reasons.append(f"动量+{mom_1m*100:.3f}%")
            score += 1
        elif mom_1m <= -self.config.MOMENTUM_THRESHOLD:
            return None  # 向下动量，不交易
        
        # 多时间框架确认
        if mom_5m > 0:
            reasons.append(f"5分钟动量+{mom_5m*100:.3f}%")
            score += 1
        
        # RSI过滤
        if self.config.RSI_OVERSOLD < rsi < self.config.RSI_OVERBOUGHT:
            reasons.append(f"RSI={rsi:.0f}正常")
            score += 1
        elif rsi >= self.config.RSI_OVERBOUGHT:
            return None  # 超买，不追高
        elif rsi <= self.config.RSI_OVERSOLD:
            reasons.append(f"RSI={rsi:.0f}超卖机会")
            score += 1
        
        # 成交量确认
        if vol_ratio >= self.config.VOL_CONFIRM_RATIO * 0.5:  # Relaxed: 40% threshold
            reasons.append(f"量比{vol_ratio:.1f}x")
            score += 1
        
        # 布林位确认 (不在顶部)
        if bb_pos < 80:
            score += 1
        else:
            reasons.append("BB顶部观望")
        
        # 趋势确认
        if trend == "UP":
            reasons.append("趋势向上")
            score += 1
        
        confidence = score / 6
        if confidence < 0.5:
            return None
        
        return Signal(
            symbol=symbol, action="BUY", confidence=confidence,
            momentum_1m=mom_1m, momentum_5m=mom_5m,
            rsi=rsi, atr=indicators['atr'], atr_pct=atr_pct,
            bb_position=bb_pos, vol_ratio=vol_ratio, trend=trend,
            reasons=reasons, price=indicators['price']
        )


# ==================== 确认过滤器 ====================

class ConfirmationFilter:
    def __init__(self, config: CISTraderConfig):
        self.config = config
    
    def filter(self, signal: Signal, existing_symbols: set) -> Optional[Signal]:
        """多重确认过滤"""
        # 不重复交易同一币种
        if signal.symbol in existing_symbols:
            return None
        
        # 动量强度过滤 (过高可能是假突破)
        if signal.momentum_1m > 0.01:  # 1%以上可能是假突破
            return None
        
        # RSI 极端值过滤
        if signal.rsi > 75 or signal.rsi < 25:
            return None
        
        return signal


# ==================== 仓位管理器 ====================

class PositionManager:
    def __init__(self, config: CISTraderConfig):
        self.config = config
        self.positions: Dict[str, Position] = {}
        self.market = None  # Will be set by trader
    
    def calculate_position(self, signal: Signal) -> Optional[Position]:
        """计算仓位大小"""
        if len(self.positions) >= self.config.MAX_OPEN_POSITIONS:
            return None
        
        price = signal.price
        if price is None or price <= 0: return None
        atr = signal.atr
        if atr == 0:
            atr = price * 0.001
        
        # ATR动态止损
        stop_pct = max(atr / price * self.config.STOP_LOSS_MULT, self.config.MIN_STOP_PCT)
        take_pct = stop_pct * self.config.TAKE_PROFIT_MULT
        
        # 风险金额
        risk_amount = self.config.INITIAL_CAPITAL * self.config.RISK_PER_TRADE
        risk_per_unit = atr * 2  # 止损距离
        position_size = min(risk_amount / risk_per_unit, self.config.INITIAL_CAPITAL * 0.1 / price)
        
        pos = Position(
            position_id=str(uuid.uuid4())[:8],
            symbol=signal.symbol,
            entry_price=price,
            entry_time=time.time(),
            size=position_size,
            stop_loss=price * (1 - stop_pct),
            take_profit=price * (1 + take_pct),
            high_watermark=price,
            atr=atr,
            momentum_at_entry=signal.momentum_1m,
            is_adaptive_stop=False
        )
        self.positions[pos.position_id] = pos
        return pos
    
    def get_open_symbols(self) -> set:
        return {p.symbol for p in self.positions.values()}


# ==================== 退出决策器 ====================

class ExitDecision:
    def __init__(self, config: CISTraderConfig):
        self.config = config
    
    def check_exit(self, pos: Position, indicators: Dict) -> Optional[str]:
        """检查是否应该退出"""
        current_price = indicators.get('price', pos.entry_price)
        pnl_pct = (current_price - pos.entry_price) / pos.entry_price * 100
        hold_time = time.time() - pos.entry_time
        
        # 更新最高价
        if current_price > pos.high_watermark:
            pos.high_watermark = current_price
        
        # 1. 止损
        if current_price <= pos.stop_loss:
            return f"止损 {pnl_pct:.1f}%"
        
        # 2. 止盈
        if current_price >= pos.take_profit:
            return f"止盈 {pnl_pct:.1f}%"
        
        # 3. 时间限制
        if hold_time >= self.config.MAX_HOLD_TIME:
            return f"时间止盈 {int(hold_time)}s"
        
        # 4. 动量反转
        cur_mom = indicators.get('momentum_1m', pos.momentum_at_entry)
        if pos.momentum_at_entry > 0.03 and cur_mom < -0.01:
            return f"动量反转 {cur_mom*100:.1f}%"
        
        # 5. 移动止盈 (从高点回撤超过ATR×2)
        drawdown = (pos.high_watermark - current_price) / pos.high_watermark
        if drawdown > pos.atr / pos.entry_price * 2:
            return f"移动止盈 回撤{drawdown*100:.1f}%"
        
        # 6. 趋势失效
        if indicators.get('trend') == 'DN' and pnl_pct > 0:
            return "趋势反转锁定利润"
        
        return None


# ==================== 风控控制器 ====================

class RiskController:
    def __init__(self, config: CISTraderConfig):
        self.config = config
        self.state = RiskState(0, 0, 0, 0.0, 0, False, "", 0)
        self.last_reset_time = time.time()
    
    def should_allow_trade(self) -> tuple:
        """检查是否允许交易"""
        # 重置日统计
        if time.time() - self.last_reset_time > 86400:
            self.state.daily_pnl = 0.0
            self.state.daily_trades = 0
            self.last_reset_time = time.time()
        
        # 检查暂停状态
        if self.state.is_paused:
            if time.time() < self.state.pause_until:
                return False, f"连续{self.state.consecutive_losses}次亏损，暂停中"
            else:
                self.state.is_paused = False
                self.state.consecutive_losses = 0
        
        # 检查日亏损限制
        if self.state.daily_pnl <= -self.config.DAILY_LOSS_LIMIT * self.config.INITIAL_CAPITAL:
            return False, f"日亏损{abs(self.state.daily_pnl):.0f} USDT，已达限制"
        
        return True, "允许交易"
    
    def record_loss(self):
        self.state.consecutive_losses += 1
        self.state.total_losses += 1
        if self.state.consecutive_losses >= self.config.MAX_CONSECUTIVE_LOSSES:
            self.state.is_paused = True
            self.state.pause_until = time.time() + self.config.LOSS_PAUSE_MINUTES * 60
            logger.warning(f"[RISK] 连续{self.state.consecutive_losses}次亏损，暂停交易")
    
    def record_win(self):
        self.state.consecutive_losses = 0
        self.state.total_wins += 1
    
    def update_daily_pnl(self, pnl: float):
        self.state.daily_pnl += pnl
        self.state.daily_trades += 1


# ==================== 主交易引擎 ====================

class CISAutoTraderV4:
    def __init__(self, config: CISTraderConfig):
        self.config = config
        self.market = MarketDataService(config)
        self.signal_gen = SignalGenerator(config, self.market)
        self.filter = ConfirmationFilter(config)
        self.pos_manager = PositionManager(config)
        self.exit_decider = ExitDecision(config)
        self.risk_ctrl = RiskController(config)
        self.trade_history: List[TradeRecord] = []
        self.wins = 0
        self.losses = 0
        self.daily_pnl = 0.0
    
    def scan_all(self) -> Dict:
        """扫描所有交易对"""
        # 更新市场数据
        for sym in self.config.SYMBOLS:
            self.market.update_market_data(sym)
        
        # 风控检查
        allowed, reason = self.risk_ctrl.should_allow_trade()
        if not allowed:
            return {'warning': reason, 'signals': [], 'exits': []}
        
        signals, exits = [], []
        
        # 生成信号
        for sym in self.config.SYMBOLS:
            signal = self.signal_gen.generate(sym)
            if signal:
                filtered = self.filter.filter(signal, self.pos_manager.get_open_symbols())
                if filtered:
                    signals.append({
                        'symbol': filtered.symbol,
                        'action': 'BUY',
                        'confidence': filtered.confidence,
                        'momentum_1m': filtered.momentum_1m * 100,
                        'momentum_5m': filtered.momentum_5m * 100,
                        'rsi': filtered.rsi,
                        'atr_pct': filtered.atr_pct,
                        'vol_ratio': filtered.vol_ratio,
                        'trend': filtered.trend,
                        'reasons': filtered.reasons
                    })
        
        # 检查退出
        for pid, pos in list(self.pos_manager.positions.items()):
            indicators = self.market.get_indicators(pos.symbol)
            if indicators:
                exit_reason = self.exit_decider.check_exit(pos, indicators)
                if exit_reason:
                    current_price = indicators['price']
                    pnl_pct = (current_price - pos.entry_price) / pos.entry_price * 100
                    pnl_amount = pos.size * pnl_pct / 100
                    hold_time = int(time.time() - pos.entry_time)
                    
                    self.trade_history.append(TradeRecord(
                        type='EXIT', position_id=pid, symbol=pos.symbol,
                        price=current_price, size=pos.size * current_price,
                        pnl_pct=pnl_pct, pnl_amount=pnl_amount,
                        reason=exit_reason, hold_time=hold_time,
                        momentum=indicators.get('momentum_1m', 0),
                        time=datetime.now().isoformat()
                    ))
                    
                    self.daily_pnl += pnl_amount
                    if pnl_pct > 0:
                        self.wins += 1
                        self.risk_ctrl.record_win()
                    else:
                        self.losses += 1
                        self.risk_ctrl.record_loss()
                    
                    self.risk_ctrl.update_daily_pnl(pnl_amount)
                    exits.append({
                        'position_id': pid, 'symbol': pos.symbol,
                        'exit_price': current_price, 'pnl_pct': pnl_pct,
                        'pnl_amount': pnl_amount, 'reason': exit_reason,
                        'hold_time': hold_time
                    })
                    logger.info(f"[CIS] EXIT {pos.symbol} {'WIN' if pnl_pct>0 else 'LOSS'} {pnl_pct:.1f}% | {exit_reason}")
                    del self.pos_manager.positions[pid]
        
        return {'signals': signals, 'exits': exits, 'market': self.market.get_market_snapshot()}
    
    def execute_trade(self, symbol: str) -> Dict:
        """执行单笔交易"""
        allowed, reason = self.risk_ctrl.should_allow_trade()
        if not allowed:
            return {'ok': False, 'error': reason}
        
        signal = self.signal_gen.generate(symbol)
        if not signal:
            return {'ok': False, 'error': '无信号'}
        
        filtered = self.filter.filter(signal, self.pos_manager.get_open_symbols())
        if not filtered:
            return {'ok': False, 'error': '信号被过滤'}
        
        pos = self.pos_manager.calculate_position(filtered)
        if not pos:
            return {'ok': False, 'error': '仓位超限'}
        
        self.trade_history.append(TradeRecord(
            type='ENTRY', position_id=pos.position_id, symbol=symbol,
            price=pos.entry_price, size=pos.size * pos.entry_price,
            momentum=filtered.momentum_1m,
            time=datetime.now().isoformat()
        ))
        
        logger.info(f"[CIS] ENTRY {symbol} @ ${pos.entry_price:.2f} | SL ${pos.stop_loss:.2f} | Mom {filtered.momentum_1m*100:.2f}%")
        return {'ok': True, 'dry_run': self.config.DRY_RUN, 'position': pos}
    
    def close_position(self, position_id: str) -> Dict:
        """手动平仓"""
        if position_id not in self.pos_manager.positions:
            return {'ok': False, 'error': '持仓不存在'}
        
        pos = self.pos_manager.positions[position_id]
        indicators = self.market.get_indicators(pos.symbol)
        current_price = indicators.get('price', pos.entry_price) if indicators else pos.entry_price
        
        pnl_pct = (current_price - pos.entry_price) / pos.entry_price * 100
        pnl_amount = pos.size * pnl_pct / 100
        hold_time = int(time.time() - pos.entry_time)
        
        self.trade_history.append(TradeRecord(
            type='EXIT', position_id=position_id, symbol=pos.symbol,
            price=current_price, size=pos.size * current_price,
            pnl_pct=pnl_pct, pnl_amount=pnl_amount,
            reason='手动平仓', hold_time=hold_time,
            time=datetime.now().isoformat()
        ))
        
        self.daily_pnl += pnl_amount
        if pnl_pct > 0:
            self.wins += 1
            self.risk_ctrl.record_win()
        else:
            self.losses += 1
            self.risk_ctrl.record_loss()
        
        self.risk_ctrl.update_daily_pnl(pnl_amount)
        del self.pos_manager.positions[position_id]
        
        return {'ok': True, 'closed': position_id, 'pnl_pct': pnl_pct, 'pnl_amount': pnl_amount}
    
    def get_status(self) -> Dict:
        """获取状态"""
        positions = []
        for p in self.pos_manager.positions.values():
            ind = self.market.get_indicators(p.symbol)
            cp = ind['price'] if ind else p.entry_price
            positions.append({
                'position_id': p.position_id, 'symbol': p.symbol,
                'entry_price': p.entry_price, 'current_price': cp,
                'stop_loss': p.stop_loss, 'take_profit': p.take_profit,
                'size': p.size * p.entry_price,
                'pnl_pct': (cp - p.entry_price) / p.entry_price * 100,
                'hold_time': int(time.time() - p.entry_time),
                'momentum_at_entry': p.momentum_at_entry * 100
            })
        
        perf = {
            'total_trades': self.wins + self.losses,
            'open_positions': len(positions),
            'wins': self.wins, 'losses': self.losses,
            'win_rate': self.wins / max(self.wins + self.losses, 1) * 100,
            'daily_pnl': self.daily_pnl,
            'total_pnl': sum(t.pnl_amount for t in self.trade_history if t.type == 'EXIT')
        }
        
        risk = {
            'consecutive_losses': self.risk_ctrl.state.consecutive_losses,
            'is_paused': self.risk_ctrl.state.is_paused,
            'pause_reason': self.risk_ctrl.state.pause_reason,
            'daily_pnl_usdt': self.risk_ctrl.state.daily_pnl,
            'daily_trades': self.risk_ctrl.state.daily_trades
        }
        
        return {**perf, 'positions': positions, 'risk': risk, 'dry_run': self.config.DRY_RUN}


# ==================== FastAPI 应用 ====================

app = FastAPI(title="CIS v4.0 快进快出收割系统", version="4.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

config = CISTraderConfig()
trader = CISAutoTraderV4(config)

@app.get("/")
async def root():
    return {"service": "CIS v4.0", "version": "4.0.0", "status": "running",
            "mode": "DRY-RUN", "architecture": "信号生成→确认过滤→仓位管理→退出决策→风控保护"}

@app.get("/api/status")
async def get_status():
    return trader.get_status()

@app.get("/api/market")
async def get_market():
    for sym in config.SYMBOLS:
        trader.market.update_market_data(sym)
    return trader.market.get_market_snapshot()

@app.get("/api/signal/{symbol}")
async def get_signal(symbol: str):
    trader.market.update_market_data(symbol)
    signal = trader.signal_gen.generate(symbol)
    if not signal:
        return {'symbol': symbol, 'signal': None, 'reason': '无信号'}
    return {'symbol': symbol, 'signal': {
        'action': signal.action, 'confidence': signal.confidence,
        'momentum_1m': signal.momentum_1m * 100, 'momentum_5m': signal.momentum_5m * 100,
        'rsi': signal.rsi, 'atr_pct': signal.atr_pct,
        'vol_ratio': signal.vol_ratio, 'trend': signal.trend,
        'reasons': signal.reasons
    }}

@app.post("/api/trade/scan")
async def scan_all():
    return trader.scan_all()

@app.post("/api/trade/execute")
async def execute_trade(request: dict):
    symbol = request.get('symbol')
    if not symbol:
        raise HTTPException(400, "需要symbol参数")
    return trader.execute_trade(symbol)

@app.post("/api/trade/close/{position_id}")
async def close_trade(position_id: str):
    return trader.close_position(position_id)

@app.post("/api/trade/close-all")
async def close_all():
    pids = list(trader.pos_manager.positions.keys())
    for pid in pids:
        trader.close_position(pid)
    return {'ok': True, 'closed_count': len(pids)}

@app.get("/api/history")
async def get_history(limit: int = 50):
    return {'trades': [asdict(t) for t in trader.trade_history[-limit:]], 'total': len(trader.trade_history)}

@app.get("/api/risk/status")
async def risk_status():
    return {
        'consecutive_losses': trader.risk_ctrl.state.consecutive_losses,
        'is_paused': trader.risk_ctrl.state.is_paused,
        'daily_pnl': trader.risk_ctrl.state.daily_pnl,
        'daily_trades': trader.risk_ctrl.state.daily_trades,
        'params': {
            'max_consecutive_losses': config.MAX_CONSECUTIVE_LOSSES,
            'loss_pause_minutes': config.LOSS_PAUSE_MINUTES,
            'daily_loss_limit_pct': config.DAILY_LOSS_LIMIT * 100
        }
    }

@app.post("/api/config")
async def update_config(request: dict):
    for key, value in request.items():
        if hasattr(config, key):
            setattr(config, key, value)
        if hasattr(trader.config, key):
            setattr(trader.config, key, value)
    return {'ok': True, 'config': {k: getattr(config, k) for k in dir(config) if not k.startswith('_')}}

@app.post("/api/trade/auto-scan")
async def auto_scan():
    """定时自动扫描接口"""
    return trader.scan_all()



# ==================== WebSocket Real-time Feed ====================
from fastapi import WebSocket, WebSocketDisconnect
import asyncio
from collections import defaultdict

connected_clients: dict[str, list[WebSocket]] = defaultdict(list)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    client_id = f"client_{int(time.time()*1000)}"
    connected_clients[client_id].append(websocket)
    print(f"[WS] Client connected: {client_id} (total: {len(connected_clients[client_id])})")
    try:
        # Send initial market data
        market_data = trader.market.get_market_snapshot()
        status_data = trader.get_status()
        signal_data = {}
        for sym in config.SYMBOLS:
            trader.market.update_market_data(sym)
            sig = trader.signal_gen.generate(sym)
            if sig:
                signal_data[sym] = {'action': sig.action, 'confidence': sig.confidence, 'reasons': sig.reasons}
        
        await websocket.send_json({
            "type": "init",
            "market": market_data,
            "status": status_data,
            "signals": signal_data
        })
        
        # Keep-alive loop
        last_push_time = 0
        while True:
            # Handle client messages
            try:
                msg = await asyncio.wait_for(websocket.receive_text(), timeout=5)
                if msg == "ping":
                    await websocket.send_json({"type": "pong"})
            except asyncio.TimeoutError:
                pass
            
            # Push updates every 5 seconds
            now = time.time()
            if now - last_push_time >= 5:
                last_push_time = now
                try:
                    # Refresh market data
                    for sym in config.SYMBOLS:
                        trader.market.update_market_data(sym)
                    
                    market_data = trader.market.get_market_snapshot()
                    status_data = trader.get_status()
                    
                    # Check for new signals
                    new_signals = {}
                    for sym in config.SYMBOLS:
                        sig = trader.signal_gen.generate(sym)
                        if sig:
                            new_signals[sym] = {
                                'action': sig.action,
                                'confidence': sig.confidence,
                                'momentum_1m': sig.momentum_1m * 100,
                                'rsi': sig.rsi,
                                'reasons': sig.reasons
                            }
                    
                    await websocket.send_json({
                        "type": "update",
                        "market": market_data,
                        "status": status_data,
                        "signals": new_signals,
                        "timestamp": int(now * 1000)
                    })
                except Exception as e:
                    print(f"[WS] Error pushing update: {e}")
            
            await asyncio.sleep(0.1)
            
    except WebSocketDisconnect:
        connected_clients[client_id].remove(websocket)
        if not connected_clients[client_id]:
            del connected_clients[client_id]
        print(f"[WS] Client disconnected: {client_id}")
    except Exception as e:
        print(f"[WS] Error: {e}")
        try:
            await websocket.close()
        except Exception:
            pass


if __name__ == "__main__":
    import uvicorn
    print("=" * 60)
    print("CIS v4.0 多维度快进快出收割系统")
    print("=" * 60)
    print(f"架构: 信号生成→确认过滤→仓位管理→退出决策→风控保护")
    print(f"模式: {'DRY-RUN' if config.DRY_RUN else 'LIVE'}")
    print(f"API: http://127.0.0.1:8092")
    print(f"动量: {config.MOMENTUM_PERIOD}根K线 | 阈值: {config.MOMENTUM_THRESHOLD*100:.3f}%")
    print(f"时间框架: 1分钟 + 5分钟")
    print(f"止损: ATR×{config.STOP_LOSS_MULT} (最低{config.MIN_STOP_PCT*100:.1f}%)")
    print(f"止盈: 止损×{config.TAKE_PROFIT_MULT} (盈亏比 {config.TAKE_PROFIT_MULT}:1)")
    print(f"持仓: {config.MAX_HOLD_TIME}s | 最多{config.MAX_OPEN_POSITIONS}个")
    print(f"风控: 连续{config.MAX_CONSECUTIVE_LOSSES}亏暂停 | 日亏{config.DAILY_LOSS_LIMIT*100:.0f}%限制")
    print(f"标的: {', '.join(config.SYMBOLS)}")
    uvicorn.run(app, host="127.0.0.1", port=8092)
