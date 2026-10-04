"""
GBT 回测 API 服务 - 修复版
修复: 端口冲突 + STRATEGIES 字典类型
"""
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional, Dict, Any
from datetime import datetime
import sys
import os

# 确保当前目录在 path 中
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from backtest_engine_v2 import STRATEGIES, run_backtest, compare_strategies

app = FastAPI(title="GBT Backtest API", version="1.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 存储历史回测结果
backtest_history = {}

@app.get("/api/backtest/health")
async def health_check():
    strategies_list = list(STRATEGIES.values()) if isinstance(STRATEGIES, dict) else STRATEGIES
    return {
        "status": "ok",
        "service": "GBT Backtest Engine",
        "version": "1.1.0",
        "strategies_count": len(strategies_list),
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/backtest/strategies")
async def list_strategies():
    strategies_list = list(STRATEGIES.values()) if isinstance(STRATEGIES, dict) else STRATEGIES
    return {"strategies": strategies_list}

@app.get("/api/backtest/run")
async def run_backtest_endpoint(strategy_id: str, symbol: str = "BTCUSDT", initial_capital: float = 10000.0):
    try:
        result = run_backtest(strategy_id, initial_capital)
        history_id = f"{strategy_id}_{symbol}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        backtest_history[history_id] = result
        return {
            "status": "ok",
            "history_id": history_id,
            "result": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/backtest/history")
async def get_history():
    return {"history": list(backtest_history.keys())}

@app.get("/api/backtest/history/{history_id}")
async def get_history_item(history_id: str):
    if history_id not in backtest_history:
        raise HTTPException(status_code=404, detail="History not found")
    return backtest_history[history_id]

@app.delete("/api/backtest/history/{history_id}")
async def delete_history(history_id: str):
    if history_id in backtest_history:
        del backtest_history[history_id]
        return {"status": "deleted"}
    raise HTTPException(status_code=404, detail="History not found")

@app.get("/api/backtest/compare")
async def compare_strategies():
    return compare_strategies()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8088)  # 改用 8088 避免冲突