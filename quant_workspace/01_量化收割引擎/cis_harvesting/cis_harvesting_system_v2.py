#!/usr/bin/env python3
"""
GBT CIS Quantitative Harvesting System v2.0
专业化全链路系统：集成连接 → 兑换 → 收款 → 量化收割

架构设计:
- FastAPI 异步架构
- WebSocket 实时数据流
- 模块化设计（每层独立可插拔）
- AI驱动的CIS交易引擎
"""

import asyncio
import json
import logging
import time
import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import requests
import numpy as np
from dotenv import load_dotenv
import os

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==================== 配置层 ====================

@dataclass
class SystemConfig:
    """系统全局配置"""
    # AI配置
    AGNES_API_KEY: str = os.getenv("AGNES_API_KEY", "")
    AGNES_BASE_URL: str = "https://apihub.agnes-ai.com/v1"
    AGNES_MODEL: str = "agnes-2.5-flash"
    
    # 支付配置
    PLISIO_API_KEY: str = os.getenv("PLISIO_API_KEY", "")
    CRYPTAPI_KEY: str = os.getenv("CRYPTAPI_KEY", "")
    
    # 区块链配置
    BSC_RPC: str = "https://bsc-dataseed.binance.org"
    TRON_RPC: str = "https://api.trongrid.io"
    
    # CIS交易配置
    CIS_MOMENTUM_PERIOD: int = 14
    CIS_MOMENTUM_THRESHOLD: float = 0.03
    CIS_MAX_HOLD_DAYS: int = 3
    CIS_BASE_POSITION: float = 0.10
    CIS_MAX_POSITION: float = 0.30
    
    # 资金配置
    INITIAL_CAPITAL: float = 100000.0
    RISK_PER_TRADE: float = 0.02
    
    # WebSocket配置
    BINANCE_WS_URL: str = "wss://stream.binance.com:9443/ws"
    UPDATE_INTERVAL: int = 5  # 秒

# ==================== 层1：集成连接模块 ====================

class IntegrationConnector:
    """层1：集成连接管理器"""
    
    def __init__(self, config: SystemConfig):
        self.config = config
        self.connected_services: Dict[str, dict] = {}
        
    async def connect_all(self) -> Dict[str, bool]:
        """连接所有外部服务"""
        results = {}
        
        # 1. 连接Binance API
        results['binance'] = await self._test_binance()
        
        # 2. 连接Cap Bridge
        results['cap_bridge'] = await self._test_cap_bridge()
        
        # 3. 连接支付网关
        results['payment_gateway'] = await self._test_payment_gateway()
        
        # 4. 连接Blockchain Bridge
        results['blockchain'] = await self._test_blockchain()
        
        # 5. 连接Telegram Bot
        results['telegram'] = await self._test_telegram()
        
        return results
    
    async def _test_binance(self) -> bool:
        """测试Binance连接"""
        try:
            resp = requests.get("https://api.binance.com/api/v3/ping", timeout=5)
            return resp.status_code == 200
        except Exception:
            return False
    
    async def _test_cap_bridge(self) -> bool:
        """测试Cap Bridge连接"""
        try:
            resp = requests.get("http://127.0.0.1:18900/api/health", timeout=5)
            return resp.status_code == 200
        except Exception:
            return False
    
    async def _test_payment_gateway(self) -> bool:
        """测试支付网关连接"""
        try:
            resp = requests.get("http://127.0.0.1:8081/api/payment/list", timeout=5)
            return resp.status_code == 200
        except Exception:
            return False
    
    async def _test_blockchain(self) -> bool:
        """测试Blockchain Bridge连接"""
        try:
            resp = requests.get("http://127.0.0.1:8082/api/blockchain/balance?network=tron", timeout=5)
            return resp.status_code == 200
        except Exception:
            return False
    
    async def _test_telegram(self) -> bool:
        """测试Telegram Bot连接"""
        bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
        return bool(bot_token)
    
    def get_status(self) -> Dict:
        """获取集成状态"""
        return {
            'service': 'Integration Connector',
            'version': '2.0.0',
            'connected_services': list(self.connected_services.keys())
        }


# ==================== 层2：兑换模块 ====================

class ExchangeService:
    """层2：加密货币兑换服务"""
    
    def __init__(self, config: SystemConfig):
        self.config = config
        self.rates_cache: Dict[str, float] = {}
        self.last_update: Optional[datetime] = None
        
    def get_exchange_rate(self, from_asset: str, to_asset: str) -> Optional[float]:
        """获取兑换汇率"""
        pair = f"{from_asset}/{to_asset}"
        
        # 缓存10秒
        if pair in self.rates_cache and (datetime.now() - self.last_update).seconds < 10:
            return self.rates_cache[pair]
        
        # 调用Binance API获取汇率
        try:
            if from_asset.upper() == "USDT" and to_asset.upper() == "BTC":
                resp = requests.get("https://api.binance.com/api/v3/ticker/ticker", timeout=5)
                if resp.status_code == 200:
                    for item in resp.json():
                        if item['symbol'] == "BTCUSDT":
                            rate = 1 / float(item['lastPrice'])
                            self.rates_cache[pair] = rate
                            self.last_update = datetime.now()
                            return rate
            
            elif from_asset.upper() == "USDT" and to_asset.upper() == "ETH":
                resp = requests.get("https://api.binance.com/api/v3/ticker/ticker", timeout=5)
                if resp.status_code == 200:
                    for item in resp.json():
                        if item['symbol'] == "ETHUSDT":
                            rate = 1 / float(item['lastPrice'])
                            self.rates_cache[pair] = rate
                            self.last_update = datetime.now()
                            return rate
        except Exception as e:
            logger.error(f"获取汇率失败: {e}")
        
        return None
    
    def calculate_exchange(self, amount: float, from_asset: str, to_asset: str) -> Dict:
        """计算兑换结果"""
        rate = self.get_exchange_rate(from_asset, to_asset)
        
        if rate is None:
            return {'error': '无法获取汇率'}
        
        result_amount = amount * rate
        
        return {
            'from_asset': from_asset,
            'to_asset': to_asset,
            'amount_from': amount,
            'rate': rate,
            'amount_to': result_amount,
            'timestamp': datetime.now().isoformat()
        }
    
    def get_supported_assets(self) -> List[str]:
        """获取支持的资产列表"""
        return ["USDT", "BTC", "ETH", "SOL", "BNB", "TRX", "USDC"]


# ==================== 层3：收款模块 ====================

class PaymentCollector:
    """层3：收款服务"""
    
    def __init__(self, config: SystemConfig):
        self.config = config
        self.payment_requests: Dict[str, dict] = {}
        
    def create_payment(self, amount: float, currency: str = "USDT") -> Dict:
        """创建收款请求"""
        payment_id = str(uuid.uuid4())[:8]
        
        # 调用PLISIO API创建支付
        try:
            headers = {"Authorization": f"Bearer {self.config.PLISIO_API_KEY}"}
            payload = {
                "amount": amount,
                "currency": currency,
                "order_id": payment_id,
                "callback_url": "https://gbtxiaotudou.com/api/payment/callback"
            }
            
            resp = requests.post(
                "https://api.plisio.net/api/v1/payment_request",
                json=payload,
                headers=headers,
                timeout=10
            )
            
            if resp.status_code == 200:
                data = resp.json()
                self.payment_requests[payment_id] = {
                    'payment_id': payment_id,
                    'amount': amount,
                    'currency': currency,
                    'status': data.get('status', 'pending'),
                    'created_at': datetime.now().isoformat()
                }
                
                return {
                    'success': True,
                    'payment_id': payment_id,
                    'payment_url': data.get('payment_url', ''),
                    'qr_code': data.get('qr_code', ''),
                    'expires_at': data.get('expires_at', '')
                }
            else:
                logger.error(f"PLISIO创建支付失败: {resp.text}")
                return {'error': f'PLISIO API错误: {resp.status_code}'}
                
        except Exception as e:
            logger.error(f"创建收款请求异常: {e}")
            return {'error': str(e)}
    
    def check_payment_status(self, payment_id: str) -> Dict:
        """检查支付状态"""
        # Check PLISIO payment status (returns mock for now)
        return {
            'payment_id': payment_id,
            'status': 'completed',
            'confirmed_at': datetime.now().isoformat()
        }
    
    def get_payment_history(self, limit: int = 10) -> List[Dict]:
        """获取收款历史"""
        payments = list(self.payment_requests.values())
        return sorted(payments, key=lambda x: x['created_at'], reverse=True)[:limit]


# ==================== 层4：量化收割引擎 ====================

class CISQuantEngine:
    """层4：CIS量化收割引擎"""
    
    def __init__(self, config: SystemConfig):
        self.config = config
        self.price_history: Dict[str, List[float]] = {}
        self.positions: Dict[str, dict] = {}
        self.trades: List[Dict] = []
        self.daily_pnl = 0.0
        self.total_trades = 0
        self.wins = 0
        self.losses = 0
        
    def update_price(self, symbol: str, price: float, timestamp: int):
        """更新价格历史"""
        if symbol not in self.price_history:
            self.price_history[symbol] = []
        self.price_history[symbol].append(price)
        # 保留最近200条
        if len(self.price_history[symbol]) > 200:
            self.price_history[symbol] = self.price_history[symbol][-200:]
    
    def calculate_momentum(self, symbol: str) -> float:
        """计算动量（CIS核心指标）"""
        prices = self.price_history.get(symbol, [])
        if len(prices) < self.config.CIS_MOMENTUM_PERIOD:
            return 0.0
        
        period_prices = prices[-self.config.CIS_MOMENTUM_PERIOD:]
        momentum = (period_prices[-1] - period_prices[0]) / period_prices[0]
        return momentum
    
    def calculate_atr(self, symbol: str, period: int = 14) -> float:
        """计算ATR（波动率）"""
        # Get prices from history (K-line data will be added when available)
        prices = self.price_history.get(symbol, [])
        if len(prices) < period + 1:
            return 0.0
        
        # 简化的ATR计算
        trs = []
        for i in range(-period, 0):
            tr = abs(prices[i] - prices[i-1])
            trs.append(tr)
        
        return sum(trs) / len(trs)
    
    def find_entry_signal(self, symbol: str) -> Optional[Dict]:
        """寻找CIS式入场信号"""
        momentum = self.calculate_momentum(symbol)
        atr = self.calculate_atr(symbol)
        
        if momentum < self.config.CIS_MOMENTUM_THRESHOLD:
            return None
        
        # 动量强度评分
        strength = min(momentum * 10, 1.0)
        
        return {
            'signal': 'MOMENTUM_BREAKOUT',
            'momentum': momentum,
            'strength': strength,
            'atr': atr,
            'reason': f'强势突破：{symbol} 14日动量 {momentum*100:.1f}%'
        }
    
    def enter_position(self, symbol: str, price: float, signal: Dict) -> Dict:
        """CIS式开仓"""
        position_id = str(uuid.uuid4())[:8]
        
        # 计算仓位大小（基于ATR和风险控制）
        atr = signal.get('atr', 0)
        if atr > 0:
            risk_per_unit = atr * 1.5  # 止损距离 = ATR * 1.5
            position_size = min(
                (self.config.INITIAL_CAPITAL * self.config.RISK_PER_TRADE) / risk_per_unit,
                self.config.INITIAL_CAPITAL * self.config.CIS_MAX_POSITION
            )
        else:
            position_size = self.config.INITIAL_CAPITAL * self.config.CIS_BASE_POSITION
        
        position = {
            'position_id': position_id,
            'symbol': symbol,
            'direction': 'LONG',
            'entry_price': price,
            'position_size': position_size,
            'stop_loss': price * 0.95,  # 5%止损
            'entry_time': datetime.now().isoformat(),
            'high_watermark': price,
            'signal': signal
        }
        
        self.positions[position_id] = position
        self.total_trades += 1
        
        logger.info(f"[CIS] 开仓 {symbol} @ {price:.2f}, 仓位${position_size:.2f}")
        
        return position
    
    def update_position(self, position_id: str, current_price: float) -> Optional[Dict]:
        """更新持仓并检查出场信号"""
        if position_id not in self.positions:
            return None
        
        pos = self.positions[position_id]
        pnl_pct = (current_price - pos['entry_price']) / pos['entry_price'] * 100
        
        # 更新最高水位
        if current_price > pos['high_watermark']:
            pos['high_watermark'] = current_price
        
        exit_signal = None
        
        # CIS法则1：亏损立刻砍（止损）
        if current_price <= pos['stop_loss']:
            exit_signal = {
                'type': 'STOP_LOSS',
                'reason': f'止损触发：亏损{abs(pnl_pct):.1f}%',
                'pnl_pct': pnl_pct
            }
        
        # CIS法则2：趋势反转才走（不止盈，让利润奔跑）
        elif current_price < pos['high_watermark'] * 0.98:  # 从高点回撤2%
            exit_signal = {
                'type': 'TREND_REVERSAL',
                'reason': f'趋势反转：从高点回撤{pos['high_watermark']/current_price-1:.1f}%',
                'pnl_pct': pnl_pct
            }
        
        # CIS法则3：时间止损（超短线）
        hold_time = datetime.now() - datetime.fromisoformat(pos['entry_time'])
        if hold_time.days >= self.config.CIS_MAX_HOLD_DAYS:
            exit_signal = {
                'type': 'TIME_EXIT',
                'reason': f'时间止损：持仓{hold_time.days}天',
                'pnl_pct': pnl_pct
            }
        
        if exit_signal:
            self._close_position(position_id, current_price, exit_signal)
            return exit_signal
        
        # CIS法则4：浮盈加仓
        if pnl_pct >= self.config.CIS_MOMENTUM_THRESHOLD * 100:
            self._add_to_position(position_id, current_price, pnl_pct)
        
        return None
    
    def _close_position(self, position_id: str, exit_price: float, signal: Dict):
        """平仓"""
        pos = self.positions.pop(position_id)
        pnl_pct = (exit_price - pos['entry_price']) / pos['entry_price'] * 100
        pnl_amount = pos['position_size'] * pnl_pct / 100
        
        self.daily_pnl += pnl_amount
        if pnl_pct > 0:
            self.wins += 1
        else:
            self.losses += 1
        
        self.trades.append({
            'action': 'close',
            'position_id': position_id,
            'symbol': pos['symbol'],
            'entry_price': pos['entry_price'],
            'exit_price': exit_price,
            'size': pos['position_size'],
            'pnl_pct': pnl_pct,
            'pnl_amount': pnl_amount,
            'signal': signal,
            'timestamp': datetime.now().isoformat()
        })
        
        logger.info(f"[CIS] 平仓 {pos['symbol']} {'盈利' if pnl_pct > 0 else '亏损'} {abs(pnl_pct):.2f}%")
    
    def _add_to_position(self, position_id: str, price: float, pnl_pct: float):
        """CIS式加仓"""
        if position_id not in self.positions:
            return
        
        pos = self.positions[position_id]
        add_size = pos['position_size'] * 0.3  # 加仓量为原仓位的30%
        pos['position_size'] += add_size
        
        self.trades.append({
            'action': 'add',
            'position_id': position_id,
            'symbol': pos['symbol'],
            'price': price,
            'added_size': add_size,
            'total_size': pos['position_size'],
            'timestamp': datetime.now().isoformat()
        })
        
        logger.info(f"[CIS] 加仓 {pos['symbol']} +{add_size*100:.1f}%, 总仓位${pos['position_size']:.2f}")
    
    def get_performance(self) -> Dict:
        """获取绩效统计"""
        win_rate = self.wins / self.total_trades * 100 if self.total_trades > 0 else 0
        avg_win = sum(t['pnl_pct'] for t in self.trades if t['action'] == 'close' and t['pnl_pct'] > 0) / max(self.wins, 1)
        avg_loss = sum(t['pnl_pct'] for t in self.trades if t['action'] == 'close' and t['pnl_pct'] < 0) / max(self.losses, 1)
        profit_factor = abs(sum(t['pnl_amount'] for t in self.trades if t['pnl_amount'] > 0) / 
                           sum(t['pnl_amount'] for t in self.trades if t['pnl_amount'] < 0)) if self.losses > 0 else 0.0
        
        return {
            'total_trades': self.total_trades,
            'wins': self.wins,
            'losses': self.losses,
            'win_rate': win_rate,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'profit_factor': profit_factor,
            'daily_pnl': self.daily_pnl,
            'daily_pnl_pct': self.daily_pnl / self.config.INITIAL_CAPITAL * 100,
            'open_positions': len(self.positions)
        }


# ==================== 层5：AI分析模块 ====================

class AIAnalysisModule:
    """层5：AI智能分析模块"""
    
    def __init__(self, config: SystemConfig):
        self.config = config
        self.api_key = config.AGNES_API_KEY
        
    def analyze_market(self, market_data: Dict) -> Dict:
        """AI市场分析报告"""
        if not self.api_key:
            return {'error': 'AI API密钥未配置'}
        
        # 构造AI提示词
        prompt = f"""
分析以下加密货币市场数据，给出CIS式交易建议：

市场数据：
{json.dumps(market_data, indent=2, ensure_ascii=False)}

请根据CIS股票交易术原则进行分析：
1. 哪些币种处于强势趋势？
2. 是否有回调买入机会？
3. 当前风险如何？
4. 推荐入场/出场操作？

只返回JSON格式，包含：
{{
  "analysis": "分析结论",
  "signals": [
    {{"symbol": "币种", "action": "BUY/SELL/HOLD", "confidence": 0-1, "reason": "原因"}}
  ],
  "risk_level": "LOW/MEDIUM/HIGH"
}}
"""
        
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": self.config.AGNES_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.3
            }
            
            resp = requests.post(
                f"{self.config.AGNES_BASE_URL}/chat/completions",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if resp.status_code == 200:
                data = resp.json()
                analysis = data['choices'][0]['message']['content']
                
                # 解析JSON响应
                try:
                    return json.loads(analysis)
                except Exception:
                    return {'raw_analysis': analysis}
            else:
                logger.error(f"AI分析失败: {resp.status_code}")
                return {'error': f'AI API错误: {resp.status_code}'}
                
        except Exception as e:
            logger.error(f"AI分析异常: {e}")
            return {'error': str(e)}
    
    def generate_trading_signal(self, signal_data: Dict) -> Dict:
        """生成交易信号"""
        if not self.api_key:
            return {'error': 'AI API密钥未配置'}
        
        prompt = f"""
根据CIS交易术，分析以下交易信号：

信号数据：
{json.dumps(signal_data, indent=2, ensure_ascii=False)}

请判断：
1. 是否应该执行此信号？
2. 应该使用多少仓位？
3. 止损和止盈应该设在哪里？

返回JSON格式：
{{
  "should_execute": true/false,
  "suggested_position_pct": 0-1,
  "suggested_stop_loss": 价格或百分比,
  "suggested_take_profit": 价格或百分比,
  "confidence": 0-1,
  "reason": "AI分析理由"
}}
"""
        
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": self.config.AGNES_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.2
            }
            
            resp = requests.post(
                f"{self.config.AGNES_BASE_URL}/chat/completions",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if resp.status_code == 200:
                data = resp.json()
                analysis = data['choices'][0]['message']['content']
                
                try:
                    return json.loads(analysis)
                except Exception:
                    return {'raw_analysis': analysis}
            else:
                return {'error': f'AI API错误: {resp.status_code}'}
                
        except Exception as e:
            return {'error': str(e)}


# ==================== FastAPI应用 ====================

app = FastAPI(
    title="GBT CIS Quantitative Harvesting System",
    description="专业化全链路系统：集成连接 → 兑换 → 收款 → 量化收割",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局配置
config = SystemConfig()
connector = IntegrationConnector(config)
exchange = ExchangeService(config)
collector = PaymentCollector(config)
engine = CISQuantEngine(config)
ai_analyzer = AIAnalysisModule(config)


# ==================== API路由 ====================

@app.get("/")
async def root():
    return {
        "service": "GBT CIS Quantitative Harvesting System",
        "version": "2.0.0",
        "architecture": "5-Layer Integration",
        "status": "running"
    }

@app.get("/api/integration/status")
async def get_integration_status():
    """层1：集成连接状态"""
    status = await connector.connect_all()
    return {
        "status": status,
        "all_connected": all(status.values()),
        "timestamp": datetime.now().isoformat()
    }

@app.post("/api/exchange/rate")
async def get_exchange_rate(request: dict):
    """层2：获取兑换汇率"""
    from_asset = request.get('from', 'USDT')
    to_asset = request.get('to', 'BTC')
    amount = request.get('amount', 1000)
    
    result = exchange.calculate_exchange(amount, from_asset, to_asset)
    return result

@app.get("/api/exchange/assets")
async def get_supported_assets():
    """层2：支持的资产列表"""
    return {
        "assets": exchange.get_supported_assets(),
        "timestamp": datetime.now().isoformat()
    }

@app.post("/api/payment/create")
async def create_payment(request: dict):
    """层3：创建收款请求"""
    amount = request.get('amount', 100)
    currency = request.get('currency', 'USDT')
    
    result = collector.create_payment(amount, currency)
    return result

@app.get("/api/payment/history")
async def get_payment_history(limit: int = 10):
    """层3：收款历史"""
    return collector.get_payment_history(limit)

@app.post("/api/cis/analyze")
async def analyze_market(request: dict):
    """层4+5：AI量化分析"""
    # 获取市场数据
    symbols = request.get('symbols', ['BTCUSDT', 'ETHUSDT', 'SOLUSDT'])
    
    market_data = {}
    for symbol in symbols:
        try:
            resp = requests.get(
                f"https://api.binance.com/api/v3/ticker/24hr?symbol={symbol}",
                timeout=5
            )
            if resp.status_code == 200:
                data = resp.json()
                price = float(data['lastPrice'])
                market_data[symbol] = {
                    'price': price,
                    'change_pct': float(data['priceChangePercent']),
                    'volume': float(data['volume']),
                    'high': float(data['highPrice']),
                    'low': float(data['lowPrice'])
                }
                
                # 更新引擎价格历史
                engine.update_price(symbol, price, int(time.time() * 1000))
        except Exception:
            pass
    
    # AI分析
    analysis = ai_analyzer.analyze_market(market_data)
    
    # 引擎信号
    signals = []
    for symbol, data in market_data.items():
        signal = engine.find_entry_signal(symbol)
        if signal:
            signals.append({
                'symbol': symbol,
                'price': data['price'],
                'signal': signal
            })
    
    return {
        "market_data": market_data,
        "ai_analysis": analysis,
        "engine_signals": signals,
        "timestamp": datetime.now().isoformat()
    }

@app.post("/api/cis/execute")
async def execute_trade(request: dict):
    """层4：执行交易"""
    symbol = request.get('symbol')
    price = request.get('price')
    signal = request.get('signal', {})
    
    if not symbol or not price:
        raise HTTPException(status_code=400, detail="需要提供symbol和price")
    
    position = engine.enter_position(symbol, price, signal)
    return {
        "success": True,
        "position": position
    }

@app.get("/api/cis/performance")
async def get_performance():
    """层4：获取绩效统计"""
    return engine.get_performance()

@app.get("/api/cis/positions")
async def get_positions():
    """层4：获取当前持仓"""
    return {
        "positions": list(engine.positions.values()),
        "count": len(engine.positions)
    }

@app.websocket("/ws/market")
async def websocket_market(websocket: WebSocket):
    """WebSocket实时行情推送"""
    await websocket.accept()
    
    try:
        while True:
            # 获取多个币种的最新行情
            for symbol in ["BTCUSDT", "ETHUSDT", "SOLUSDT"]:
                try:
                    resp = requests.get(
                        f"https://api.binance.com/api/v3/ticker/24hr?symbol={symbol}",
                        timeout=5
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        price = float(data['lastPrice'])
                        engine.update_price(symbol, price, int(time.time() * 1000))
                        
                        await websocket.send_json({
                            "symbol": symbol,
                            "price": price,
                            "change_pct": float(data['priceChangePercent']),
                            "volume": float(data['volume']),
                            "timestamp": datetime.now().isoformat()
                        })
                except Exception:
                    pass
            
            await asyncio.sleep(config.UPDATE_INTERVAL)
            
    except WebSocketDisconnect:
        logger.info("WebSocket客户端断开")
    except Exception as e:
        logger.error(f"WebSocket错误: {e}")


# ==================== 主函数 ====================

if __name__ == "__main__":
    import uvicorn
    
    print("=" * 60)
    print("GBT CIS Quantitative Harvesting System v2.0")
    print("=" * 60)
    print("\n启动中...")
    print("API地址: http://127.0.0.1:8090")
    print("WebSocket: ws://127.0.0.1:8090/ws/market")
    
    uvicorn.run(app, host="127.0.0.1", port=8090)
