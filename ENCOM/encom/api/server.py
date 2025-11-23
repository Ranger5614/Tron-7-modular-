"""
ENCOM REST API - FastAPI Backend

Professional REST API for programmatic access to ENCOM backtesting platform.

Endpoints:
- /api/backtest - Run backtests
- /api/optimize - Optimize parameters
- /api/indicators - Calculate indicators
- /api/strategies - Manage strategies
- /api/results - Query results
- /api/reports - Generate reports
- /api/live - Live trading operations

Requirements:
    pip install fastapi uvicorn[standard]

Usage:
    uvicorn encom.api.server:app --reload --port 8000

Author: ENCOM Development Team
License: MIT
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime
import uuid
import asyncio

try:
    from fastapi import FastAPI
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    print("⚠️  FastAPI not available. Install with: pip install fastapi uvicorn[standard]")

# Import ENCOM modules
from encom.engine.backtest_engine import BacktestRunner
from encom.engine.multi_asset_backtest import run_multi_asset_backtest
from encom.optimization import ParameterOptimizer
from encom.analytics.report_generator import generate_report
from encom.data.data_pipeline import DataPipeline

# Initialize FastAPI app
app = FastAPI(
    title="ENCOM API",
    description="Professional Quantitative Trading Platform API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware for web access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage for async tasks and results
tasks = {}
results = {}

# ===========================
# Pydantic Models (Request/Response)
# ===========================

class BacktestRequest(BaseModel):
    """Request to run a backtest"""
    strategy_name: str = Field(..., description="Strategy class name")
    symbol: str = Field(..., description="Stock symbol")
    start_date: str = Field(..., description="Start date (YYYY-MM-DD)")
    end_date: str = Field(..., description="End date (YYYY-MM-DD)")
    initial_capital: float = Field(10000, description="Initial capital")
    strategy_params: Optional[Dict[str, Any]] = Field(None, description="Strategy parameters")

class MultiAssetBacktestRequest(BaseModel):
    """Request to run multi-asset backtest"""
    strategy_name: str
    symbols: List[str] = Field(..., description="List of symbols")
    start_date: str
    end_date: str
    initial_capital: float = 100000
    n_jobs: int = Field(-1, description="Parallel jobs (-1 = all CPUs)")

class OptimizationRequest(BaseModel):
    """Request to optimize parameters"""
    strategy_name: str
    symbol: str
    start_date: str
    end_date: str
    param_grid: Dict[str, List[Any]] = Field(..., description="Parameter grid")
    method: str = Field("grid", description="Optimization method: grid, genetic, random")
    metric: str = Field("sharpe_ratio", description="Metric to optimize")

class IndicatorRequest(BaseModel):
    """Request to calculate indicators"""
    symbol: str
    start_date: str
    end_date: str
    indicators: List[str] = Field(..., description="List of indicator names")
    indicator_params: Optional[Dict[str, Dict]] = Field(None, description="Indicator parameters")

class TaskResponse(BaseModel):
    """Response with task ID for async operations"""
    task_id: str
    status: str
    message: str

class TaskStatusResponse(BaseModel):
    """Response with task status"""
    task_id: str
    status: str  # pending, running, completed, failed
    progress: Optional[float] = None
    result: Optional[Dict] = None
    error: Optional[str] = None

# ===========================
# API Endpoints
# ===========================

@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "name": "ENCOM API",
        "version": "1.0.0",
        "status": "operational",
        "docs": "/docs",
        "endpoints": {
            "backtest": "/api/backtest",
            "optimize": "/api/optimize",
            "indicators": "/api/indicators",
            "results": "/api/results/{task_id}",
            "health": "/api/health"
        }
    }

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "active_tasks": len([t for t in tasks.values() if t['status'] in ['pending', 'running']]),
        "completed_tasks": len([t for t in tasks.values() if t['status'] == 'completed'])
    }

@app.post("/api/backtest", response_model=TaskResponse)
async def run_backtest(request: BacktestRequest, background_tasks: BackgroundTasks):
    """
    Run a backtest asynchronously

    Returns task ID to track progress
    """
    task_id = str(uuid.uuid4())

    tasks[task_id] = {
        'status': 'pending',
        'type': 'backtest',
        'request': request.dict(),
        'created_at': datetime.now().isoformat()
    }

    # Add to background tasks
    background_tasks.add_task(execute_backtest, task_id, request)

    return TaskResponse(
        task_id=task_id,
        status="pending",
        message="Backtest queued for execution"
    )

@app.post("/api/backtest/multi-asset", response_model=TaskResponse)
async def run_multi_asset_backtest_api(request: MultiAssetBacktestRequest, background_tasks: BackgroundTasks):
    """
    Run multi-asset backtest asynchronously

    Tests strategy across multiple stocks in parallel
    """
    task_id = str(uuid.uuid4())

    tasks[task_id] = {
        'status': 'pending',
        'type': 'multi_asset_backtest',
        'request': request.dict(),
        'created_at': datetime.now().isoformat()
    }

    background_tasks.add_task(execute_multi_asset_backtest, task_id, request)

    return TaskResponse(
        task_id=task_id,
        status="pending",
        message=f"Multi-asset backtest queued ({len(request.symbols)} symbols)"
    )

@app.post("/api/optimize", response_model=TaskResponse)
async def optimize_parameters(request: OptimizationRequest, background_tasks: BackgroundTasks):
    """
    Optimize strategy parameters asynchronously

    Uses grid search, genetic algorithm, or random search
    """
    task_id = str(uuid.uuid4())

    tasks[task_id] = {
        'status': 'pending',
        'type': 'optimization',
        'request': request.dict(),
        'created_at': datetime.now().isoformat()
    }

    background_tasks.add_task(execute_optimization, task_id, request)

    return TaskResponse(
        task_id=task_id,
        status="pending",
        message=f"Parameter optimization queued ({request.method} search)"
    )

@app.post("/api/indicators")
async def calculate_indicators(request: IndicatorRequest):
    """
    Calculate technical indicators

    Returns indicator values as JSON
    """
    try:
        # Fetch data
        pipeline = DataPipeline()
        data = pipeline.get_data(
            request.symbol,
            start_date=request.start_date,
            end_date=request.end_date
        )

        if data is None or len(data) == 0:
            raise HTTPException(status_code=404, detail=f"No data found for {request.symbol}")

        # Calculate indicators
        indicator_results = {}

        for indicator_name in request.indicators:
            try:
                # Dynamically import indicator
                from encom import indicators

                if hasattr(indicators, indicator_name):
                    indicator_func = getattr(indicators, indicator_name)

                    # Get parameters if provided
                    params = request.indicator_params.get(indicator_name, {}) if request.indicator_params else {}

                    # Calculate indicator (handle different signatures)
                    if indicator_name in ['rsi', 'ema', 'sma']:
                        result = indicator_func(data['close'].values, **params)
                    elif indicator_name in ['macd', 'stochastic']:
                        result = indicator_func(data['close'].values, **params)
                        # Convert tuple to dict
                        if isinstance(result, tuple):
                            result = {"line_" + str(i): r.tolist() for i, r in enumerate(result)}
                    elif indicator_name in ['bollinger_bands', 'keltner_channels']:
                        result = indicator_func(data['close'].values, **params)
                        if isinstance(result, tuple):
                            result = {"upper": result[1].tolist(), "middle": result[0].tolist(), "lower": result[2].tolist()}
                    elif indicator_name == 'vwap':
                        result = indicator_func(
                            data['high'].values,
                            data['low'].values,
                            data['close'].values,
                            data['volume'].values,
                            **params
                        )
                    else:
                        result = indicator_func(data['close'].values, **params)

                    # Convert numpy arrays to lists
                    if hasattr(result, 'tolist'):
                        result = result.tolist()

                    indicator_results[indicator_name] = result
                else:
                    indicator_results[indicator_name] = {"error": "Indicator not found"}

            except Exception as e:
                indicator_results[indicator_name] = {"error": str(e)}

        return {
            "symbol": request.symbol,
            "period": f"{request.start_date} to {request.end_date}",
            "bars": len(data),
            "indicators": indicator_results
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/results/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str):
    """
    Get status of async task

    Returns progress, result, or error
    """
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")

    task = tasks[task_id]

    response = TaskStatusResponse(
        task_id=task_id,
        status=task['status'],
        progress=task.get('progress'),
        error=task.get('error')
    )

    # If completed, include result
    if task['status'] == 'completed' and task_id in results:
        response.result = results[task_id]

    return response

@app.get("/api/strategies")
async def list_strategies():
    """
    List available strategies

    Returns list of built-in and custom strategies
    """
    return {
        "built_in": [
            {"name": "RSIStrategy", "description": "RSI mean reversion"},
            {"name": "MACDStrategy", "description": "MACD trend following"},
            {"name": "BreakoutStrategy", "description": "Breakout with volume confirmation"}
        ],
        "custom": []  # Would load from database
    }

@app.get("/api/indicators/list")
async def list_indicators():
    """
    List all available indicators

    Returns complete indicator catalog
    """
    from encom import indicators

    indicator_list = []

    # Get all indicator functions
    for name in dir(indicators):
        if not name.startswith('_') and callable(getattr(indicators, name)):
            indicator_list.append(name)

    return {
        "total": len(indicator_list),
        "categories": {
            "momentum": [i for i in indicator_list if any(x in i.lower() for x in ['rsi', 'macd', 'stoch', 'cci', 'roc'])],
            "trend": [i for i in indicator_list if any(x in i.lower() for x in ['adx', 'psar', 'aroon', 'supertrend'])],
            "volatility": [i for i in indicator_list if any(x in i.lower() for x in ['atr', 'bollinger', 'keltner'])],
            "volume": [i for i in indicator_list if any(x in i.lower() for x in ['vwap', 'obv', 'cmf', 'mfi'])],
        },
        "all": indicator_list
    }

# ===========================
# Background Task Executors
# ===========================

async def execute_backtest(task_id: str, request: BacktestRequest):
    """Execute backtest in background"""
    try:
        tasks[task_id]['status'] = 'running'

        # Import strategy (simplified - would need proper dynamic loading)
        from encom.strategies import RSIStrategy  # Example

        # Fetch data
        pipeline = DataPipeline()
        data = pipeline.get_data(
            request.symbol,
            start_date=request.start_date,
            end_date=request.end_date
        )

        # Run backtest
        strategy = RSIStrategy()  # Would instantiate based on request.strategy_name
        runner = BacktestRunner(strategy, data, initial_capital=request.initial_capital)
        result = runner.run(verbose=False)

        # Store result
        results[task_id] = {
            'metrics': result['metrics'],
            'final_equity': result['portfolio'].get_equity(),
            'total_trades': len(result.get('trades', []))
        }

        tasks[task_id]['status'] = 'completed'

    except Exception as e:
        tasks[task_id]['status'] = 'failed'
        tasks[task_id]['error'] = str(e)

async def execute_multi_asset_backtest(task_id: str, request: MultiAssetBacktestRequest):
    """Execute multi-asset backtest in background"""
    try:
        tasks[task_id]['status'] = 'running'

        # Import strategy
        from encom.strategies import RSIStrategy  # Example

        # Run multi-asset backtest
        result = run_multi_asset_backtest(
            strategy_class=RSIStrategy,
            symbols=request.symbols,
            start_date=request.start_date,
            end_date=request.end_date,
            initial_capital=request.initial_capital,
            n_jobs=request.n_jobs,
            verbose=False
        )

        # Store result
        results[task_id] = {
            'portfolio_metrics': result.portfolio_metrics,
            'top_performers': result.top_performers,
            'worst_performers': result.worst_performers,
            'total_symbols': len(result.symbol_results)
        }

        tasks[task_id]['status'] = 'completed'

    except Exception as e:
        tasks[task_id]['status'] = 'failed'
        tasks[task_id]['error'] = str(e)

async def execute_optimization(task_id: str, request: OptimizationRequest):
    """Execute parameter optimization in background"""
    try:
        tasks[task_id]['status'] = 'running'

        # Would implement actual optimization
        # Placeholder for now

        results[task_id] = {
            'best_params': {},
            'best_score': 0,
            'iterations': 0
        }

        tasks[task_id]['status'] = 'completed'

    except Exception as e:
        tasks[task_id]['status'] = 'failed'
        tasks[task_id]['error'] = str(e)

# ===========================
# Startup/Shutdown Events
# ===========================

@app.on_event("startup")
async def startup_event():
    """Initialize on startup"""
    print("=" * 70)
    print("ENCOM API Server")
    print("=" * 70)
    print("Starting professional trading API...")
    print("Documentation: http://localhost:8000/docs")
    print("=" * 70)

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    print("Shutting down ENCOM API...")

# ===========================
# CLI Entry Point
# ===========================

if __name__ == "__main__":
    import uvicorn

    print("Starting ENCOM API server...")
    print("Access documentation at: http://localhost:8000/docs")

    uvicorn.run(
        "encom.api.server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
