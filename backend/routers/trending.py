from fastapi import APIRouter, Query
from typing import Optional
import sys
import os

# 添加父目录到路径以便导入 services
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

router = APIRouter(prefix="/api/trending", tags=["trending"])


@router.get("/github")
async def get_github_trending(
    language: str = Query(default="", description="编程语言筛选，如 python, javascript"),
    period: str = Query(default="daily", description="时间范围：daily, weekly, monthly")
):
    """获取 GitHub Trending 列表"""
    try:
        from services.github_scraper import get_github_trending
        return await get_github_trending(language, period)
    except Exception as e:
        return {"source": "github", "items": [], "error": str(e)}


@router.get("/youtube")
async def get_youtube_trending(
    region: str = Query(default="US", description="地区代码，如 US, CN, JP"),
    category: Optional[str] = Query(default=None, description="视频分类ID")
):
    """获取 YouTube 热门视频"""
    try:
        from services.youtube_service import get_youtube_trending
        return await get_youtube_trending(region, category)
    except Exception as e:
        return {"source": "youtube", "items": [], "error": str(e)}


@router.get("/google")
async def get_google_trends(
    keyword: str = Query(default="", description="搜索关键词，不传则获取实时趋势")
):
    """获取 Google Trends 趋势"""
    try:
        from services.trends_service import get_google_trends
        return await get_google_trends(keyword)
    except Exception as e:
        return {"source": "google", "items": [], "error": str(e)}


@router.get("/xueqiu")
async def get_xueqiu_trending():
    """获取雪球热门股票"""
    try:
        from services.xueqiu_scraper import get_xueqiu_trending
        return await get_xueqiu_trending()
    except Exception as e:
        return {"source": "xueqiu", "items": [], "error": str(e)}


@router.get("/gelonghui")
async def get_gelonghui_trending():
    """获取格隆汇热文"""
    try:
        from services.gelonghui_scraper import get_gelonghui_trending
        return await get_gelonghui_trending()
    except Exception as e:
        return {"source": "gelonghui", "items": [], "error": str(e)}


@router.get("/producthunt")
async def get_producthunt_trending():
    """获取 Product Hunt 热门产品"""
    try:
        from services.producthunt_scraper import get_producthunt_trending
        return await get_producthunt_trending()
    except Exception as e:
        return {"source": "producthunt", "items": [], "error": str(e)}
