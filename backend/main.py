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
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")

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
    claude_code,
    trending,
)

app.include_router(stocks.router)
app.include_router(market.router)
app.include_router(ai.router)
app.include_router(util.router)
app.include_router(health.router)
app.include_router(config.router)
app.include_router(reddit.router)
app.include_router(claude_code.router)
app.include_router(trending.router)

# 生产环境：托管前端静态文件
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path as _Path

FRONTEND_DIR = _Path(__file__).parent.parent / "frontend" / "dist"

if FRONTEND_DIR.exists():
    app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIR / "assets")), name="static-assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        file_path = FRONTEND_DIR / full_path
        if file_path.is_file():
            return FileResponse(str(file_path))
        return FileResponse(str(FRONTEND_DIR / "index.html"))


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
