from pydantic import BaseModel
from typing import Optional


class ChatRequest(BaseModel):
    messages: list


# ========== 通用热榜模型 ==========

class HotItem(BaseModel):
    """统一热榜项格式"""
    id: str
    title: str
    url: str
    score: int = 0
    comments: int = 0
    author: str = ""
    created_at: float = 0
    metadata: dict = {}


class TrendingResponse(BaseModel):
    """统一热榜响应"""
    source: str
    items: list[HotItem] = []
    error: Optional[str] = None


# ========== GitHub 模型 ==========

class GitHubRepo(BaseModel):
    """GitHub 仓库"""
    id: str
    repo_name: str
    repo_full_name: str
    description: str
    language: str
    stars: int
    forks: int
    url: str
    author: str
    author_url: str


# ========== YouTube 模型 ==========

class YouTubeVideo(BaseModel):
    """YouTube 视频"""
    video_id: str
    title: str
    channel_title: str
    channel_id: str
    view_count: int = 0
    likes: int = 0
    thumbnail: str
    url: str
    published_at: str = ""


# ========== 雪球模型 ==========

class XueqiuStock(BaseModel):
    """雪球股票"""
    symbol: str
    name: str
    current_price: float
    change_pct: float
    market: str  # SH/SZ
    url: str = ""


# ========== Google Trends 模型 ==========

class TrendItem(BaseModel):
    """Google 趋势项"""
    query: str
    traffic: str  # like "100K+"
    article_title: str = ""
    article_url: str = ""
