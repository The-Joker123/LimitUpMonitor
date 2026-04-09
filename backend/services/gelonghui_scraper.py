"""
格隆汇热榜爬虫服务
获取格隆汇热文列表
网址: https://www.gelonghui.com
"""

import requests
from bs4 import BeautifulSoup
import hashlib
import time
import random
import re


# 格隆汇 API 和 URL
GELONGHUI_BASE = "https://www.gelonghui.com"
GELONGHUI_API = "https://api.gelonghui.com"

# User-Agent 列表
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
]


def get_headers() -> dict:
    """生成请求头"""
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Referer": GELONGHUI_BASE,
    }


def parse_relative_time(text: str) -> float:
    """解析相对时间为 unix timestamp"""
    if not text:
        return time.time()

    text = text.strip().lower()

    # 匹配 "N分钟前", "N小时前", "N天前"
    minute_match = re.search(r'(\d+)\s*分钟前', text)
    if minute_match:
        minutes = int(minute_match.group(1))
        return time.time() - minutes * 60

    hour_match = re.search(r'(\d+)\s*小时前', text)
    if hour_match:
        hours = int(hour_match.group(1))
        return time.time() - hours * 3600

    day_match = re.search(r'(\d+)\s*天前', text)
    if day_match:
        days = int(day_match.group(1))
        return time.time() - days * 86400

    # 匹配日期格式 "2024-01-15"
    date_match = re.search(r'(\d{4})-(\d{2})-(\d{2})', text)
    if date_match:
        try:
            from datetime import datetime
            dt = datetime(
                int(date_match.group(1)),
                int(date_match.group(2)),
                int(date_match.group(3))
            )
            return dt.timestamp()
        except:
            pass

    return time.time()


async def get_gelonghui_trending() -> dict:
    """
    获取格隆汇热文列表

    Returns:
        {"source": "gelonghui", "items": [...], "error": None}
    """
    items = []
    error = None

    try:
        headers = get_headers()

        # 尝试主页面
        response = requests.get(
            GELONGHUI_BASE,
            headers=headers,
            timeout=15
        )

        if response.status_code != 200:
            # 尝试 API 方式
            return await get_gelonghui_api_trending()

        soup = BeautifulSoup(response.content, "html.parser")

        # 查找文章列表（格隆汇结构）
        articles = soup.find_all("article") or soup.find_all("div", class_=re.compile(r"post|article|item"))

        for article in articles[:20]:  # 限制 20 条
            try:
                # 尝试多种选择器
                title_tag = (
                    article.find("h2") or
                    article.find("h3") or
                    article.find("a", class_=re.compile(r"title")) or
                    article.find("a")
                )

                if not title_tag:
                    continue

                title = title_tag.get_text(strip=True)

                # 获取链接
                link_tag = title_tag.find("a") if hasattr(title_tag, "find") else title_tag
                if link_tag and link_tag.get("href"):
                    url = link_tag["href"]
                    if not url.startswith("http"):
                        url = GELONGHUI_BASE + url
                else:
                    continue

                # 获取摘要
                summary_tag = article.find("p") or article.find("div", class_=re.compile(r"excerpt|summary|desc"))
                summary = summary_tag.get_text(strip=True) if summary_tag else ""

                # 获取作者
                author_tag = article.find("span", class_=re.compile(r"author")) or \
                            article.find("a", class_=re.compile(r"author"))
                author = author_tag.get_text(strip=True) if author_tag else "格隆汇"

                # 获取时间
                time_tag = article.find("span", class_=re.compile(r"time|date"))
                time_text = time_tag.get_text(strip=True) if time_tag else ""
                created_at = parse_relative_time(time_text)

                # 获取评论数/点赞数
                engagement_tag = article.find("span", class_=re.compile(r"comment|like|view"))
                score = 0
                if engagement_tag:
                    score_text = engagement_tag.get_text(strip=True)
                    score_match = re.search(r'(\d+)', score_text)
                    if score_match:
                        score = int(score_match.group(1))

                # 生成唯一 ID
                item_id = hashlib.md5(url.encode()).hexdigest()[:12]

                items.append({
                    "id": item_id,
                    "title": title,
                    "url": url,
                    "score": score,
                    "comments": 0,
                    "author": author,
                    "created_at": created_at,
                    "metadata": {
                        "summary": summary[:200] if summary else "",
                        "source": "gelonghui",
                    }
                })
            except Exception as e:
                continue

        # 如果没找到，尝试 API
        if not items:
            return await get_gelonghui_api_trending()

    except requests.Timeout:
        error = "请求超时，请稍后重试"
        return await get_gelonghui_api_trending()
    except requests.RequestException as e:
        error = f"网络错误: {str(e)}"
        return await get_gelonghui_api_trending()
    except Exception as e:
        error = str(e)
        return await get_gelonghui_api_trending()

    return {
        "source": "gelonghui",
        "items": items,
        "error": error
    }


async def get_gelonghui_api_trending() -> dict:
    """
    通过 API 方式获取格隆汇热文
    """
    items = []
    error = None

    try:
        headers = get_headers()
        headers["Accept"] = "application/json"

        # 尝试格隆汇热文 API
        api_url = f"{GELONGHUI_API}/posts/hot"

        response = requests.get(api_url, headers=headers, timeout=10)

        if response.status_code != 200:
            # 返回友好的错误信息
            return {
                "source": "gelonghui",
                "items": [],
                "error": "格隆汇暂时无法访问，请稍后重试"
            }

        try:
            data = response.json()
        except:
            return {
                "source": "gelonghui",
                "items": [],
                "error": "格隆汇数据解析失败"
            }

        posts = data.get("data", []) or data.get("posts", []) or data

        for post in posts[:20]:
            try:
                title = post.get("title", "")
                url = post.get("url") or post.get("link") or post.get("path")
                if not url:
                    post_id = post.get("id", "")
                    url = f"{GELONGHUI_BASE}/community/post/{post_id}"

                author = post.get("author", {}).get("name", "") if isinstance(post.get("author"), dict) else post.get("author", "格隆汇")

                created_at = post.get("created_at") or post.get("published_at") or post.get("timestamp")
                if isinstance(created_at, str):
                    from datetime import datetime
                    try:
                        dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                        created_at = dt.timestamp()
                    except:
                        created_at = time.time()

                score = post.get("likes_count", 0) or post.get("views", 0) or post.get("score", 0)
                comments = post.get("comments_count", 0) or post.get("replies", 0)

                item_id = hashlib.md5(str(post.get("id", url)).encode()).hexdigest()[:12]

                items.append({
                    "id": item_id,
                    "title": title,
                    "url": url,
                    "score": score,
                    "comments": comments,
                    "author": author,
                    "created_at": created_at,
                    "metadata": {
                        "summary": post.get("excerpt", "")[:200] or post.get("summary", "")[:200],
                        "source": "gelonghui_api",
                    }
                })
            except Exception as e:
                continue

    except Exception as e:
        error = f"格隆汇 API 获取失败: {str(e)}"

    return {
        "source": "gelonghui",
        "items": items,
        "error": error if not items else None  # 有数据就不显示错误
    }
