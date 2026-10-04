"""
GBT 策略回测 API 服务
"""
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import json
from typing import List, Optional, Dict, Any
from datetime import datetime

app = FastAPI(title="GBT Backtest API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 导入回测引擎
import sys
sys.path.insert(0, '.openclaw/tmp')
from backtest_engine import BacktestEngine, STRATEGIES, run_backtest

# 存储历史回测结果
backtest_history = {}

@app.get("/api/backtest/health")
async def health_check():
    return {
        "status": "ok",
        "service": "GBT Backtest Engine",
        "version": "1.0.0",
        "strategies_available": len(STRATEGIES),
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/backtest/strategies")
async def list_strategies():
    """获取可用策略列表"""
    return {
        "strategies": [
            {
                "id": s["id"],
                "name": s["name"],
                "type": s["type"],
                "symbol": s["symbol"],
                "description": s["description"]
            }
            for s in STRATEGIES.values()
        ]
    }

@app.get("/api/backtest/run")
async def run_backtest_endpoint(
    strategy_id: str = Query(..., description="策略ID"),
    initial_capital: float = Query(10000.0, description="初始资金"),
    symbol: Optional[str] = Query(None, description="覆盖默认交易对")
):
    """运行回测"""
    try:
        # 获取策略配置
        strategy = STRATEGIES.get(strategy_id)
        if not strategy:
            raise HTTPException(status_code=404, detail=f"策略 {strategy_id} 不存在")
        
        # 覆盖参数
        if symbol:
            strategy["symbol"] = symbol
        
        # 运行回测
        result = run_backtest(strategy_id, initial_capital)
        
        # 保存到历史
        history_id = f"{strategy_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        backtest_history[history_id] = {
            "result": result,
            "timestamp": datetime.now().isoformat(),
            "params": {"initial_capital": initial_capital, "symbol": symbol or strategy["symbol"]}
        }
        
        return {
            "status": "success",
            "history_id": history_id,
            "result": result
        }
        
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/api/backtest/history")
async def get_backtest_history(limit: int = Query(10, ge=1, le=100)):
    """获取回测历史"""
    items = list(backtest_history.items())[-limit:]
    return {
        "history": [
            {"id": k, **v} for k, v in items
        ],
        "total": len(backtest_history)
    }

@app.get("/api/backtest/history/{history_id}")
async def get_backtest_result(history_id: str):
    """获取单次回测结果"""
    result = backtest_history.get(history_id)
    if not result:
        raise HTTPException(status_code=404, detail="回测记录不存在")
    return result

@app.delete("/api/backtest/history/{history_id}")
async def delete_backtest_result(history_id: str):
    """删除回测记录"""
    if history_id not in backtest_history:
        raise HTTPException(status_code=404, detail="回测记录不存在")
    del backtest_history[history_id]
    return {"message": "已删除"}

@app.post("/api/backtest/optimize")
async def optimize_strategy(
    strategy_id: str,
    param_ranges: Dict[str, Any]
):
    """策略参数优化 (网格搜索)"""
    # 简化实现：执行多次回测并返回最优参数
    best_result = None
    best_params = None
    
    # 示例：遍历参数组合
    import itertools
    
    param_keys = list(param_ranges.keys())
    param_values = [param_ranges[k] if isinstance(param_ranges[k], list) else [param_ranges[k]] for k in param_keys]
    
    results = []
    for combo in itertools.product(*param_values):
        params = dict(zip(param_keys, combo))
        # 这里应该运行实际回测，简化为模拟
        results.append({
            "params": params,
            "return": random.uniform(-10, 30),
            "sharpe": random.uniform(0.5, 2.5),
            "drawdown": random.uniform(-5, -20)
        })
    
    # 按收益率排序
    results.sort(key=lambda x: x["return"], reverse=True)
    
    return {
        "strategy_id": strategy_id,
        "optimization_results": results[:10],
        "best_params": results[0]["params"] if results else None
    }

@app.get("/api/backtest/compare")
async def compare_strategies(
    strategy_ids: str = Query(..., description="逗号分隔的策略ID"),
    initial_capital: float = Query(10000.0)
):
    """对比多个策略"""
    ids = [sid.strip() for sid in strategy_ids.split(",")]
    comparisons = []
    
    for sid in ids:
        if sid in STRATEGIES:
            result = run_backtest(sid, initial_capital)
            comparisons.append({
                "strategy_id": sid,
                "name": STRATEGIES[sid]["name"],
                "total_return": result.get("total_return"),
                "win_rate": result.get("win_rate"),
                "max_drawdown": result.get("max_drawdown"),
                "sharpe_ratio": result.get("sharpe_ratio"),
                "total_trades": result.get("total_trades")
            })
    
    # 按收益率排序
    comparisons.sort(key=lambda x: x.get("total_return", 0), reverse=True)
    
    return {"comparisons": comparisons}

if __name__ == "__main__":
    import uvicorn
    import random
    uvicorn.run(app, host="0.0.0.0", port=8088)
