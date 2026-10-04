#!/usr/bin/env python3
"""
GBT CIS Quantitative Harvesting Engine v1.0
CIS股票交易术驱动的量化快进快出收割系统

核心理念:
- 强者恒强，弱者恒弱
- 顺势而为，买涨不买跌
- 止损果断，浮盈加仓
- 简单规则胜过复杂系统
- 输是常态，正期望长期盈利
"""

import asyncio
import json
import logging
import time
import random
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum

import requests
import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CISDirection(Enum):
    LONG = "long"
    SHORT = "short"
    HOLD = "hold"


class CISEnterSignal(Enum):
    MOMENTUM_BREAKOUT = "momentum_breakout"
    PULLBACK_ENTRY = "pullback_entry"
    TREND_FOLLOWING = "trend_following"


class CISExitSignal(Enum):
    STOP_LOSS = "stop_loss"
    TAKE_PROFIT = "take_profit"
    TREND_REVERSAL = "trend_reversal"
    TIME_EXIT = "time_exit"


@dataclass
class CISPosition:
    """CIS持仓模型"""
    symbol: str
    direction: str
    entry_price: float
    current_price: float
    position_size: float  # 占总资产比例
    stop_loss: float
    take_profit: float
    entry_time: datetime
    high_watermark: float = 0.0
    atr: float = 0.0
    pnl_pct: float = 0.0
    
    def update_price(self, price: float):
        self.current_price = price
        self.pnl_pct = (price - self.entry_price) / self.entry_price * 100
        
        # 更新最高水位
        if price > self.high_watermark:
            self.high_watermark = price
            
    def should_stop_loss(self) -> bool:
        """CIS法则：亏损立刻砍"""
        return self.current_price <= self.stop_loss
    
    def should_take_profit(self) -> bool:
        """CIS法则：趋势结束才走"""
        return self.current_price >= self.take_profit


@dataclass
class CISConfig:
    """CIS交易配置"""
    # 动量因子参数
    momentum_lookback: int = 14  # 动量观察周期
    momentum_threshold: float = 0.03  # 动量阈值（3%）
    
    # 止损参数（CIS风格：动态ATR止损）
    atr_period: int = 14
    sl_atr_multiplier: float = 1.5  # 止损距离 = ATR * 1.5
    max_sl_pct: float = 0.05  # 最大止损比例5%
    
    # 加仓参数（CIS法则：浮盈加仓）
    add_position_threshold: float = 0.02  # 浮盈2%时加仓
    add_position_pct: float = 0.3  # 加仓量为原仓位的30%
    max_additions: int = 3  # 最多加仓3次
    
    # 持仓周期（CIS超短线）
    max_hold_days: int = 3  # 最长持仓3天
    min_profit_target: float = 0.03  # 最低盈利目标3%
    
    # 资金管理（CIS集中火力）
    base_position_pct: float = 0.10  # 基础仓位10%
    max_position_pct: float = 0.30  # 最大仓位30%
    
    # 多资产组合
    symbols: List[str] = None
    
    def __post_init__(self):
        if self.symbols is None:
            self.symbols = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT"]


class CISAlphaModel:
    """CIS动量选股引擎"""
    
    def __init__(self, config: CISConfig):
        self.config = config
        self.price_cache: Dict[str, List[float]] = {}
        
    def calculate_momentum(self, symbol: str, prices: List[float]) -> float:
        """计算动量（价格变化率）"""
        if len(prices) < self.config.momentum_lookback:
            return 0.0
        
        recent = prices[-self.config.momentum_lookback:]
        momentum = (recent[-1] - recent[0]) / recent[0]
        return momentum
    
    def calculate_trend_strength(self, prices: List[float]) -> float:
        """计算趋势强度（连续涨跌幅度的绝对值之和）"""
        if len(prices) < 10:
            return 0.0
        
        returns = [(prices[i] - prices[i-1]) / prices[i-1] for i in range(1, len(prices))]
        
        # 趋势强度 = 连续同向变化的幅度
        strength = sum(abs(r) for r in returns) / len(returns)
        direction = np.sign(sum(returns))
        
        return strength * direction
    
    def calculate_volatility(self, prices: List[float], period: int = 20) -> float:
        """计算波动率（标准差）"""
        if len(prices) < period:
            return 0.0
        
        recent_returns = [(prices[i] - prices[i-1]) / prices[i-1] 
                         for i in range(-period, 0)]
        return np.std(recent_returns)
    
    def get_momentum_ranking(self, market_data: Dict[str, dict]) -> List[str]:
        """对所有币种按动量排序，返回强势币列表"""
        rankings = []
        
        for symbol, data in market_data.items():
            prices = data.get('prices', [])
            if not prices:
                continue
            
            momentum = self.calculate_momentum(symbol, prices)
            trend_strength = self.calculate_trend_strength(prices)
            volatility = self.calculate_volatility(prices)
            
            rankings.append({
                'symbol': symbol,
                'momentum': momentum,
                'trend_strength': trend_strength,
                'volatility': volatility,
                'score': momentum * 0.5 + abs(trend_strength) * 0.3 - volatility * 0.2
            })
        
        # 按得分排序，返回强势币
        rankings.sort(key=lambda x: x['score'], reverse=True)
        return [r['symbol'] for r in rankings if r['score'] > 0]
    
    def find_entry_opportunity(self, symbol: str, prices: List[float]) -> Optional[Dict]:
        """寻找CIS式入场机会（强势股回调）"""
        if len(prices) < self.config.momentum_lookback + 10:
            return None
        
        momentum = self.calculate_momentum(symbol, prices)
        
        # CIS法则：只做强势股
        if momentum < self.config.momentum_threshold:
            return None
        
        # 入场信号1：动量突破（强势延续）
        if momentum > 0.05:  # 14日涨幅超过5%
            return {
                'type': CISEnterSignal.MOMENTUM_BREAKOUT.value,
                'confidence': min(momentum * 10, 1.0),  # 动量越强信心越高
                'reason': f'强势突破：14日动量{momentum*100:.1f}%'
            }
        
        # 入场信号2：回调买入（强势股小幅回调）
        recent_returns = [
            (prices[i] - prices[i-1]) / prices[i-1] 
            for i in range(-10, 0)
        ]
        
        if len(recent_returns) >= 3:
            # 之前强势，最近小幅回调
            if np.mean(recent_returns[:7]) > 0.03 and np.mean(recent_returns[-3:]) < 0:
                pullback_depth = abs(min(recent_returns[-3:]))
                if 0.01 < pullback_depth < 0.05:  # 回调1-5%
                    return {
                        'type': CISEnterSignal.PULLBACK_ENTRY.value,
                        'confidence': min(pullback_depth * 20, 0.9),
                        'reason': f'强势回调买入：前7日涨{np.mean(recent_returns[:7])*100:.1f}%，回调{pullback_depth*100:.1f}%'
                    }
        
        return None


class CISPositionManager:
    """CIS仓位管理引擎"""
    
    def __init__(self, config: CISConfig, initial_capital: float = 100000):
        self.config = config
        self.capital = initial_capital
        self.positions: Dict[str, CISPosition] = {}
        self.trade_history: List[Dict] = []
        self.daily_pnl = 0.0
        
    def calculate_position_size(self, symbol: str, entry_price: float, atr: float) -> float:
        """CIS式仓位计算（波动率调整）"""
        # 止损距离
        sl_distance = max(atr * self.config.sl_atr_multiplier, entry_price * self.config.max_sl_pct)
        risk_per_unit = sl_distance
        
        # 单笔风险（总资产的1-2%）
        risk_per_trade = self.capital * 0.02
        
        # 仓位大小
        position_size = risk_per_trade / risk_per_unit if risk_per_unit > 0 else 0
        position_value = position_size * entry_price
        
        # 限制仓位比例
        position_pct = position_value / self.capital
        position_pct = min(position_pct, self.config.max_position_pct)
        position_pct = max(position_pct, self.config.base_position_pct)
        
        return position_pct
    
    def enter_position(self, symbol: str, direction: str, entry_price: float, 
                      atr: float, signal: Dict) -> CISPosition:
        """CIS式开仓"""
        position_pct = self.calculate_position_size(symbol, entry_price, atr)
        
        # 计算止损止盈
        sl_distance = atr * self.config.sl_atr_multiplier
        tp_distance = atr * self.config.tp_multiplier if hasattr(self.config, 'tp_multiplier') else atr * 3
        
        if direction == CISDirection.LONG.value:
            stop_loss = entry_price - sl_distance
            take_profit = entry_price + tp_distance
        else:
            stop_loss = entry_price + sl_distance
            take_profit = entry_price - tp_distance
        
        position = CISPosition(
            symbol=symbol,
            direction=direction,
            entry_price=entry_price,
            current_price=entry_price,
            position_size=position_pct,
            stop_loss=stop_loss,
            take_profit=take_profit,
            entry_time=datetime.now(),
            high_watermark=entry_price,
            atr=atr
        )
        
        self.positions[symbol] = position
        
        # 记录交易
        self.trade_history.append({
            'action': 'open',
            'symbol': symbol,
            'direction': direction,
            'price': entry_price,
            'size_pct': position_pct,
            'signal': signal,
            'timestamp': datetime.now().isoformat()
        })
        
        logger.info(f"[CIS] 开仓 {symbol} {direction} @ {entry_price:.2f}, "
                   f"止损={stop_loss:.2f}, 止盈={take_profit:.2f}")
        
        return position
    
    def update_position(self, symbol: str, current_price: float) -> Optional[Dict]:
        """更新持仓并检查出场信号"""
        if symbol not in self.positions:
            return None
        
        position = self.positions[symbol]
        position.update_price(current_price)
        
        exit_signal = None
        
        # CIS法则：亏损立刻砍
        if position.should_stop_loss():
            exit_signal = {
                'type': CISExitSignal.STOP_LOSS.value,
                'reason': f'止损触发：亏损{position.pnl_pct:.1f}%',
                'pnl_pct': position.pnl_pct
            }
        
        # CIS法则：趋势结束才走（不止盈，让利润奔跑）
        elif position.direction == CISDirection.LONG.value:
            if current_price < position.high_watermark * 0.98:  # 从高点回撤2%
                exit_signal = {
                    'type': CISExitSignal.TREND_REVERSAL.value,
                    'reason': f'趋势反转：从高点回撤{position.high_watermark/current_price-1:.1f}%',
                    'pnl_pct': position.pnl_pct
                }
        
        # 时间止损（CIS超短线）
        hold_time = datetime.now() - position.entry_time
        if hold_time > timedelta(days=self.config.max_hold_days):
            exit_signal = {
                'type': CISExitSignal.TIME_EXIT.value,
                'reason': f'时间止损：持仓{hold_time.days}天',
                'pnl_pct': position.pnl_pct
            }
        
        if exit_signal:
            self._close_position(symbol, current_price, exit_signal)
            return exit_signal
        
        return None
    
    def _close_position(self, symbol: str, price: float, signal: Dict):
        """平仓"""
        position = self.positions.pop(symbol)
        pnl_pct = position.pnl_pct
        
        # 更新资金
        pnl_amount = self.capital * position.position_size * pnl_pct / 100
        self.capital += pnl_amount
        self.daily_pnl += pnl_amount
        
        # 记录交易
        self.trade_history.append({
            'action': 'close',
            'symbol': symbol,
            'direction': position.direction,
            'entry_price': position.entry_price,
            'exit_price': price,
            'size_pct': position.position_size,
            'pnl_pct': pnl_pct,
            'pnl_amount': pnl_amount,
            'signal': signal,
            'timestamp': datetime.now().isoformat()
        })
        
        logger.info(f"[CIS] 平仓 {symbol} {'盈利' if pnl_pct > 0 else '亏损'} {abs(pnl_pct):.2f}%")
    
    def should_add_position(self, symbol: str, current_price: float) -> bool:
        """CIS法则：浮盈加仓"""
        if symbol not in self.positions:
            return False
        
        position = self.positions[symbol]
        
        # 已有浮盈
        if position.pnl_pct < self.config.add_position_threshold:
            return False
        
        # 检查是否已加仓过多
        additions = sum(1 for t in self.trade_history 
                       if t['symbol'] == symbol and t['action'] == 'add')
        
        if additions >= self.config.max_additions:
            return False
        
        return True
    
    def add_to_position(self, symbol: str, current_price: float) -> float:
        """加仓"""
        if symbol not in self.positions:
            return 0.0
        
        position = self.positions[symbol]
        add_size = position.position_size * self.config.add_position_pct
        
        position.position_size += add_size
        
        self.trade_history.append({
            'action': 'add',
            'symbol': symbol,
            'price': current_price,
            'added_size': add_size,
            'total_size': position.position_size,
            'timestamp': datetime.now().isoformat()
        })
        
        logger.info(f"[CIS] 加仓 {symbol} +{add_size*100:.1f}%, 总仓位{position.position_size*100:.1f}%")
        
        return add_size
    
    def get_portfolio_summary(self) -> Dict:
        """获取投资组合摘要"""
        total_value = self.capital
        positions_value = 0
        
        for sym, pos in self.positions.items():
            positions_value += total_value * pos.position_size
        
        return {
            'capital': self.capital,
            'positions_value': positions_value,
            'cash': self.capital - positions_value,
            'open_positions': len(self.positions),
            'daily_pnl': self.daily_pnl,
            'daily_pnl_pct': self.daily_pnl / self.capital * 100,
            'total_trades': len([t for t in self.trade_history if t['action'] == 'close']),
            'win_rate': self._calculate_win_rate(),
            'avg_win': self._calculate_avg_win(),
            'avg_loss': self._calculate_avg_loss(),
            'profit_factor': self._calculate_profit_factor()
        }
    
    def _calculate_win_rate(self) -> float:
        closes = [t for t in self.trade_history if t['action'] == 'close']
        if not closes:
            return 0.0
        wins = sum(1 for t in closes if t['pnl_pct'] > 0)
        return wins / len(closes) * 100
    
    def _calculate_avg_win(self) -> float:
        closes = [t for t in self.trade_history if t['action'] == 'close' and t['pnl_pct'] > 0]
        if not closes:
            return 0.0
        return sum(t['pnl_pct'] for t in closes) / len(closes)
    
    def _calculate_avg_loss(self) -> float:
        closes = [t for t in self.trade_history if t['action'] == 'close' and t['pnl_pct'] < 0]
        if not closes:
            return 0.0
        return sum(t['pnl_pct'] for t in closes) / len(closes)
    
    def _calculate_profit_factor(self) -> float:
        closes = [t for t in self.trade_history if t['action'] == 'close']
        if not closes:
            return 0.0
        gross_profit = sum(t['pnl_amount'] for t in closes if t['pnl_amount'] > 0)
        gross_loss = abs(sum(t['pnl_amount'] for t in closes if t['pnl_amount'] < 0))
        return gross_profit / gross_loss if gross_loss > 0 else float('inf')


class CISBinanceFeed:
    """CIS行情数据源"""
    
    def __init__(self, symbols: List[str]):
        self.symbols = symbols
        self.price_cache: Dict[str, List[float]] = {}
        self._max_history = 200
        
    def get_ticker(self, symbol: str) -> Optional[Dict]:
        """获取实时行情"""
        try:
            url = "https://api.binance.com/api/v3/ticker/24hr"
            params = {"symbol": symbol}
            response = requests.get(url, params=params, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                price = float(data['lastPrice'])
                
                # 更新价格历史
                if symbol not in self.price_cache:
                    self.price_cache[symbol] = []
                self.price_cache[symbol].append(price)
                if len(self.price_cache[symbol]) > self._max_history:
                    self.price_cache[symbol] = self.price_cache[symbol][-self._max_history:]
                
                return {
                    'symbol': symbol,
                    'price': price,
                    'change_pct': float(data['priceChangePercent']),
                    'volume': float(data['volume']),
                    'high': float(data['highPrice']),
                    'low': float(data['lowPrice']),
                    'timestamp': datetime.now().isoformat()
                }
        except Exception as e:
            logger.error(f"获取{symbol}行情失败: {e}")
        
        return None
    
    def get_klines(self, symbol: str, interval: str = "1h", limit: int = 100) -> List[Dict]:
        """获取K线数据"""
        try:
            url = "https://api.binance.com/api/v3/klines"
            params = {
                "symbol": symbol,
                "interval": interval,
                "limit": limit
            }
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                klines = []
                for k in response.json():
                    klines.append({
                        'time': datetime.fromtimestamp(k[0]/1000).isoformat(),
                        'open': float(k[1]),
                        'high': float(k[2]),
                        'low': float(k[3]),
                        'close': float(k[4]),
                        'volume': float(k[5])
                    })
                return klines
        except Exception as e:
            logger.error(f"获取{symbol}K线失败: {e}")
        
        return []
    
    def calculate_atr(self, klines: List[Dict], period: int = 14) -> float:
        """计算ATR"""
        if len(klines) < period + 1:
            return 0.0
        
        trs = []
        for i in range(len(klines)):
            if i == 0:
                tr = klines[i]['high'] - klines[i]['low']
            else:
                tr = max(
                    klines[i]['high'] - klines[i]['low'],
                    abs(klines[i]['high'] - klines[i-1]['close']),
                    abs(klines[i]['low'] - klines[i-1]['close'])
                )
            trs.append(tr)
        
        # Wilder's ATR
        atr = sum(trs[:period]) / period
        for i in range(period, len(trs)):
            atr = (atr * (period - 1) + trs[i]) / period
        
        return atr


class CISHarvestingEngine:
    """CIS量化收割引擎（主引擎）"""
    
    def __init__(self, config: CISConfig = None, capital: float = 100000):
        self.config = config or CISConfig()
        self.alpha_model = CISAlphaModel(self.config)
        self.position_manager = CISPositionManager(self.config, capital)
        self.feed = CISBinanceFeed(self.config.symbols)
        self.running = False
        self.cycle_count = 0
        
    def run_cycle(self) -> Dict:
        """执行一个收割周期"""
        self.cycle_count += 1
        logger.info(f"[CIS] ========== 收割周期 #{self.cycle_count} ==========")
        
        results = {
            'cycle': self.cycle_count,
            'timestamp': datetime.now().isoformat(),
            'signals': [],
            'actions': [],
            'portfolio': {}
        }
        
        # Step 1: 获取市场数据
        market_data = self._fetch_market_data()
        if not market_data:
            return results
        
        # Step 2: 动量排序，找出强势币
        strong_symbols = self.alpha_model.get_momentum_ranking(market_data)
        logger.info(f"[CIS] 强势币: {strong_symbols[:3]}")
        
        # Step 3: 寻找入场机会
        for symbol in strong_symbols[:3]:  # 只关注Top 3强势币
            if symbol in self.position_manager.positions:
                # 更新持仓
                price = market_data[symbol]['price']
                atr = self._get_atr(symbol)
                exit_signal = self.position_manager.update_position(symbol, price)
                
                if exit_signal:
                    results['actions'].append({
                        'type': 'close',
                        'symbol': symbol,
                        'signal': exit_signal
                    })
                
                # CIS法则：浮盈加仓
                if self.position_manager.should_add_position(symbol, price):
                    add_size = self.position_manager.add_to_position(symbol, price)
                    results['actions'].append({
                        'type': 'add',
                        'symbol': symbol,
                        'size': add_size
                    })
            else:
                # 寻找新入场机会
                klines = self.feed.get_klines(symbol, "1h", 100)
                if klines:
                    prices = [k['close'] for k in klines]
                    entry_signal = self.alpha_model.find_entry_opportunity(symbol, prices)
                    
                    if entry_signal and entry_signal['confidence'] > 0.6:
                        atr = self.feed.calculate_atr(klines)
                        position = self.position_manager.enter_position(
                            symbol, CISDirection.LONG.value,
                            market_data[symbol]['price'], atr, entry_signal
                        )
                        results['signals'].append({
                            'symbol': symbol,
                            'type': entry_signal['type'],
                            'confidence': entry_signal['confidence'],
                            'reason': entry_signal['reason']
                        })
                        results['actions'].append({
                            'type': 'open',
                            'symbol': symbol,
                            'price': market_data[symbol]['price'],
                            'signal': entry_signal
                        })
        
        # Step 4: 获取组合摘要
        results['portfolio'] = self.position_manager.get_portfolio_summary()
        
        logger.info(f"[CIS] 组合摘要: {results['portfolio']}")
        
        return results
    
    def _fetch_market_data(self) -> Dict[str, Dict]:
        """批量获取市场数据"""
        data = {}
        for symbol in self.config.symbols:
            ticker = self.feed.get_ticker(symbol)
            if ticker:
                data[symbol] = ticker
        return data
    
    def _get_atr(self, symbol: str) -> float:
        """获取ATR"""
        klines = self.feed.get_klines(symbol, "1h", 50)
        if klines:
            return self.feed.calculate_atr(klines)
        return 0.0
    
    def start_auto_trading(self, interval_seconds: int = 300):
        """启动自动收割"""
        self.running = True
        logger.info(f"[CIS] 启动自动收割，间隔{interval_seconds}秒")
        
        while self.running:
            try:
                result = self.run_cycle()
                
                # 发送通知
                self._send_notification(result)
                
            except Exception as e:
                logger.error(f"[CIS] 收割异常: {e}")
            
            time.sleep(interval_seconds)
    
    def _send_notification(self, result: Dict):
        """发送收割结果通知"""
        # Send notification via Telegram/Discord (placeholder for future integration)
        # if os.getenv("TELEGRAM_BOT_TOKEN"):
        #     await send_telegram_notification(result)
        print(f"[CIS] Notification: {result}")
    
    def get_status(self) -> Dict:
        """获取系统状态"""
        return {
            'service': 'CIS Quantitative Harvesting Engine',
            'version': '1.0.0',
            'running': self.running,
            'cycles': self.cycle_count,
            'portfolio': self.position_manager.get_portfolio_summary(),
            'config': asdict(self.config)
        }


# 主函数
if __name__ == "__main__":
    print("=" * 60)
    print("CIS Quantitative Harvesting Engine v1.0")
    print("=" * 60)
    
    # 创建引擎
    engine = CISHarvestingEngine(capital=100000)
    
    # 运行一次测试
    print("\n[测试模式] 运行一次收割周期...")
    result = engine.run_cycle()
    
    print(f"\n信号: {result['signals']}")
    print(f"操作: {result['actions']}")
    print(f"组合: {result['portfolio']}")
    
    print("\n" + "=" * 60)
    print("测试完成")
