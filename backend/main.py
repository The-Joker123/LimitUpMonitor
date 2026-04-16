"""
A股涨停连板监控系统 V1 - 后端
使用akshare获取东方财富涨停池数据
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

load_dotenv()

app = FastAPI(title="A股涨停连板监控系统 V1")

# CORS配置 - 仅允许特定前端域名
ALLOWED_ORIGINS = os.getenv(
    "ALLOWED_ORIGINS", "http://localhost:5173,http://localhost:3000"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

# 注册路由
from routers import (
    stocks,
    market,
    ai,
    util,
    health,
    config,
    reddit,
    trending,
    claude_code,
)

app.include_router(stocks.router)
app.include_router(market.router)
app.include_router(ai.router)
app.include_router(util.router)
app.include_router(health.router)
app.include_router(config.router)
app.include_router(reddit.router)
app.include_router(trending.router)
app.include_router(claude_code.router)


if __name__ == "__main__":
    import uvicorn
    import json
    from pathlib import Path

    config_path = Path(__file__).parent.parent / "config.json"
    try:
        config = json.loads(config_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise RuntimeError(f"Config file not found: {config_path}")
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Invalid config JSON: {e}")

    backend_config = config["backend"]
    uvicorn.run(app, host=backend_config["host"], port=backend_config["port"])
