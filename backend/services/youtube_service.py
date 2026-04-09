"""
YouTube 热榜服务
使用 YouTube Data API v3 获取热门视频
需要 GOOGLE_API_KEY 环境变量
"""

import os
import requests
import hashlib
import time


# YouTube Data API v3 配置
YOUTUBE_API_KEY = os.getenv("GOOGLE_API_KEY") or os.getenv("YOUTUBE_API_KEY", "")
YOUTUBE_API_BASE = "https://www.googleapis.com/youtube/v3"

# 视频分类映射（部分）
VIDEO_CATEGORIES = {
    "1": "Film & Animation",
    "2": "Autos & Vehicles",
    "10": "Music",
    "15": "Pets & Animals",
    "17": "Sports",
    "18": "Short Movies",
    "19": "Travel & Events",
    "20": "Gaming",
    "21": "Videoblogging",
    "22": "People & Blogs",
    "23": "Comedy",
    "24": "Entertainment",
    "25": "News & Politics",
    "26": "Howto & Style",
    "27": "Education",
    "28": "Science & Technology",
    "29": "Nonprofits & Activism",
    "30": "Movies",
    "31": "Anime/Animation",
    "32": "Action/Adventure",
    "33": "Classics",
    "34": "Comedy",
    "35": "Documentary",
    "36": "Drama",
    "37": "Family",
    "38": "Foreign",
    "39": "Horror",
    "40": "Sci-Fi/Fantasy",
    "41": "Thriller",
    "42": "Shorts",
    "43": "Shows",
    "44": "Trailers",
}


def parse_duration_to_seconds(duration: str) -> int:
    """解析 ISO 8601 持续时间到秒数"""
    import re
    if not duration:
        return 0
    # PT1H30M15S -> 1*3600 + 30*60 + 15
    match = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', duration)
    if not match:
        return 0
    hours = int(match.group(1) or 0)
    minutes = int(match.group(2) or 0)
    seconds = int(match.group(3) or 0)
    return hours * 3600 + minutes * 60 + seconds


async def get_youtube_trending(region: str = "US", category: str = None) -> dict:
    """
    获取 YouTube 热门视频

    Args:
        region: 地区代码，如 US, CN, JP
        category: 视频分类 ID，不传则获取全部热门

    Returns:
        {"source": "youtube", "items": [...], "error": None}
    """
    items = []
    error = None

    if not YOUTUBE_API_KEY:
        return {
            "source": "youtube",
            "items": [],
            "error": "未配置 YouTube API Key，请设置 GOOGLE_API_KEY 或 YOUTUBE_API_KEY 环境变量"
        }

    try:
        # 构建 API 请求 URL
        params = {
            "part": "snippet,statistics,contentDetails",
            "chart": "mostPopular",
            "regionCode": region,
            "maxResults": 30,
            "key": YOUTUBE_API_KEY,
        }

        if category:
            params["videoCategoryId"] = category

        url = f"{YOUTUBE_API_BASE}/videos"
        response = requests.get(url, params=params, timeout=10)

        if response.status_code == 403:
            return {
                "source": "youtube",
                "items": [],
                "error": "API 配额超限或无效的 API Key"
            }
        elif response.status_code == 400:
            return {
                "source": "youtube",
                "items": [],
                "error": "无效的请求参数"
            }
        elif response.status_code != 200:
            return {
                "source": "youtube",
                "items": [],
                "error": f"HTTP {response.status_code}"
            }

        data = response.json()

        for item in data.get("items", []):
            try:
                video_id = item.get("id", "")
                snippet = item.get("snippet", {})
                statistics = item.get("statistics", {})
                content_details = item.get("contentDetails", {})

                # 解析发布时间
                published_at = snippet.get("publishedAt", "")
                try:
                    from datetime import datetime
                    dt = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
                    created_at = dt.timestamp()
                except:
                    created_at = 0

                # 获取缩略图
                thumbnails = snippet.get("thumbnails", {})
                thumbnail_url = ""
                for size in ["maxres", "high", "medium", "default"]:
                    if size in thumbnails:
                        thumbnail_url = thumbnails[size].get("url", "")
                        break

                # 视频时长
                duration = content_details.get("duration", "")
                duration_secs = parse_duration_to_seconds(duration)

                # 构建视频 URL
                video_url = f"https://www.youtube.com/watch?v={video_id}"

                # 生成唯一 ID
                item_id = hashlib.md5(video_id.encode()).hexdigest()[:12]

                items.append({
                    "id": item_id,
                    "title": snippet.get("title", ""),
                    "url": video_url,
                    "score": int(statistics.get("viewCount", 0)),
                    "comments": int(statistics.get("commentCount", 0)),
                    "author": snippet.get("channelTitle", ""),
                    "created_at": created_at,
                    "metadata": {
                        "video_id": video_id,
                        "channel_id": snippet.get("channelId", ""),
                        "description": snippet.get("description", ""),
                        "tags": snippet.get("tags", []),
                        "category_id": snippet.get("categoryId", ""),
                        "likes": int(statistics.get("likeCount", 0)),
                        "thumbnail": thumbnail_url,
                        "duration": duration_secs,
                        "duration_text": duration,
                        "region": region,
                    }
                })
            except Exception as e:
                continue

    except requests.Timeout:
        error = "请求超时，请稍后重试"
    except requests.RequestException as e:
        error = f"网络错误: {str(e)}"
    except Exception as e:
        error = str(e)

    return {
        "source": "youtube",
        "items": items,
        "error": error
    }


async def search_youtube_videos(q: str, region: str = "US", max_results: int = 20) -> dict:
    """
    搜索 YouTube 视频

    Args:
        q: 搜索关键词
        region: 地区代码
        max_results: 最大结果数

    Returns:
        {"source": "youtube_search", "items": [...], "error": None}
    """
    items = []
    error = None

    if not YOUTUBE_API_KEY:
        return {
            "source": "youtube_search",
            "items": [],
            "error": "未配置 YouTube API Key"
        }

    try:
        params = {
            "part": "snippet",
            "q": q,
            "type": "video",
            "order": "viewCount",
            "regionCode": region,
            "maxResults": min(max_results, 50),
            "key": YOUTUBE_API_KEY,
        }

        url = f"{YOUTUBE_API_BASE}/search"
        response = requests.get(url, params=params, timeout=10)

        if response.status_code != 200:
            return {
                "source": "youtube_search",
                "items": [],
                "error": f"HTTP {response.status_code}"
            }

        data = response.json()

        for item in data.get("items", []):
            try:
                video_id = item.get("id", {}).get("videoId", "")
                snippet = item.get("snippet", {})

                published_at = snippet.get("publishedAt", "")
                try:
                    from datetime import datetime
                    dt = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
                    created_at = dt.timestamp()
                except:
                    created_at = 0

                thumbnails = snippet.get("thumbnails", {})
                thumbnail_url = thumbnails.get("high", {}).get("url", "") or \
                               thumbnails.get("medium", {}).get("url", "")

                item_id = hashlib.md5(video_id.encode()).hexdigest()[:12]

                items.append({
                    "id": item_id,
                    "title": snippet.get("title", ""),
                    "url": f"https://www.youtube.com/watch?v={video_id}",
                    "score": 0,
                    "comments": 0,
                    "author": snippet.get("channelTitle", ""),
                    "created_at": created_at,
                    "metadata": {
                        "video_id": video_id,
                        "channel_id": snippet.get("channelId", ""),
                        "thumbnail": thumbnail_url,
                    }
                })
            except Exception as e:
                continue

    except Exception as e:
        error = str(e)

    return {
        "source": "youtube_search",
        "items": items,
        "error": error
    }
