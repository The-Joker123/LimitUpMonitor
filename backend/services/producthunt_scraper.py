"""
Product Hunt 热榜爬虫服务
获取 Product Hunt 热门产品
网址: https://www.producthunt.com
"""

import requests
from bs4 import BeautifulSoup
import hashlib
import time
import random
import re


# Product Hunt URL
PRODUCTHUNT_BASE = "https://www.producthunt.com"
PRODUCTHUNT_HOT = f"{PRODUCTHUNT_BASE}/posts"

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
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }


def parse_relative_time(text: str) -> float:
    """解析相对时间"""
    if not text:
        return time.time()

    text = text.strip().lower()

    minute_match = re.search(r'(\d+)\s*minute', text)
    if minute_match:
        return time.time() - int(minute_match.group(1)) * 60

    hour_match = re.search(r'(\d+)\s*hour', text)
    if hour_match:
        return time.time() - int(hour_match.group(1)) * 3600

    day_match = re.search(r'(\d+)\s*day', text)
    if day_match:
        return time.time() - int(day_match.group(1)) * 86400

    week_match = re.search(r'(\d+)\s*week', text)
    if week_match:
        return time.time() - int(week_match.group(1)) * 7 * 86400

    return time.time()


async def get_producthunt_trending() -> dict:
    """
    获取 Product Hunt 热门产品

    Returns:
        {"source": "producthunt", "items": [...], "error": None}
    """
    items = []
    error = None

    try:
        headers = get_headers()

        # 尝试获取首页
        response = requests.get(
            PRODUCTHUNT_BASE,
            headers=headers,
            timeout=15
        )

        if response.status_code != 200:
            return {
                "source": "producthunt",
                "items": [],
                "error": f"HTTP {response.status_code} - Product Hunt 暂时无法访问"
            }

        soup = BeautifulSoup(response.content, "html.parser")

        # Product Hunt 的文章结构
        # 查找所有产品卡片
        posts = soup.find_all("a", href=re.compile(r"^/posts/"))[:20]

        for post in posts:
            try:
                # 获取标题
                title_tag = post.find("h3") or post.find("h2") or post.find("span")
                title = title_tag.get_text(strip=True) if title_tag else ""

                if not title:
                    continue

                # 获取 URL
                href = post.get("href", "")
                if not href.startswith("http"):
                    url = PRODUCTHUNT_BASE + href
                else:
                    url = href

                # 获取 tagline（副标题）
                tagline_tag = post.find("p") or post.find("div", class_=re.compile(r"tagline|desc"))
                tagline = tagline_tag.get_text(strip=True) if tagline_tag else ""

                # 获取投票数
                vote_tag = post.find("div", class_=re.compile(r"vote|score|rank"))
                score = 0
                if vote_tag:
                    vote_text = vote_tag.get_text(strip=True)
                    vote_match = re.search(r'([\d,]+)', vote_text.replace(",", ""))
                    if vote_match:
                        score = int(vote_match.group(1))

                # 获取评论数
                comment_tag = post.find("span", class_=re.compile(r"comment"))
                comments = 0
                if comment_tag:
                    comment_text = comment_tag.get_text(strip=True)
                    comment_match = re.search(r'([\d,]+)', comment_text.replace(",", ""))
                    if comment_match:
                        comments = int(comment_match.group(1))

                # 生成唯一 ID
                item_id = hashlib.md5(url.encode()).hexdigest()[:12]

                items.append({
                    "id": item_id,
                    "title": title,
                    "url": url,
                    "score": score,
                    "comments": comments,
                    "author": "",
                    "created_at": time.time(),
                    "metadata": {
                        "tagline": tagline,
                        "source": "producthunt",
                    }
                })
            except Exception as e:
                continue

        # 如果没找到，尝试热榜页面
        if not items:
            return await get_producthunt_hot_page()

    except requests.Timeout:
        error = "请求超时，Product Hunt 暂时无法访问"
    except requests.RequestException as e:
        error = f"网络错误: {str(e)}"
    except Exception as e:
        error = str(e)

    return {
        "source": "producthunt",
        "items": items,
        "error": error
    }


async def get_producthunt_hot_page() -> dict:
    """
    获取 Product Hunt 热榜页面的数据
    """
    items = []
    error = None

    try:
        headers = get_headers()

        # 热榜页面，按周排序
        response = requests.get(
            f"{PRODUCTHUNT_BASE}/posts?sort=top",
            headers=headers,
            timeout=15
        )

        if response.status_code != 200:
            return {
                "source": "producthunt",
                "items": [],
                "error": "Product Hunt 页面暂时无法访问"
            }

        soup = BeautifulSoup(response.content, "html.parser")

        # 查找文章链接
        links = soup.find_all("a", href=re.compile(r"/posts/[a-zA-Z0-9-_]+"))

        seen_urls = set()
        for link in links:
            if len(items) >= 20:
                break

            try:
                href = link.get("href", "")
                if href in seen_urls:
                    continue
                seen_urls.add(href)

                if not href.startswith("http"):
                    url = PRODUCTHUNT_BASE + href
                else:
                    url = href

                # 尝试从链接中提取产品名
                product_slug = href.split("/")[-1]

                # 获取标题 - 可能在链接内部或附近的元素
                title = link.get_text(strip=True)
                if not title or len(title) < 2:
                    # 尝试从父元素获取
                    parent = link.find_parent(["article", "div"])
                    if parent:
                        title = parent.get_text(strip=True)[:100]

                if not title or len(title) < 2:
                    title = product_slug.replace("-", " ").title()

                item_id = hashlib.md5(url.encode()).hexdigest()[:12]

                items.append({
                    "id": item_id,
                    "title": title[:100],
                    "url": url,
                    "score": 0,
                    "comments": 0,
                    "author": "",
                    "created_at": time.time(),
                    "metadata": {
                        "slug": product_slug,
                        "source": "producthunt_page",
                    }
                })
            except Exception as e:
                continue

    except Exception as e:
        error = str(e)

    return {
        "source": "producthunt",
        "items": items,
        "error": error if not items else None
    }


async def get_producthunt_json() -> dict:
    """
    尝试获取 Product Hunt 的 JSON 数据
    """
    items = []
    error = None

    try:
        # Product Hunt 有非官方的 JSON 端点
        headers = {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "application/json",
        }

        # 尝试 V1 API
        response = requests.get(
            "https://api.producthunt.com/v1/posts",
            headers=headers,
            timeout=10
        )

        if response.status_code == 401:
            return {
                "source": "producthunt",
                "items": [],
                "error": "Product Hunt API 需要认证"
            }
        elif response.status_code != 200:
            return {
                "source": "producthunt",
                "items": [],
                "error": f"HTTP {response.status_code}"
            }

        data = response.json()
        posts = data.get("posts", [])[:20]

        for post in posts:
            try:
                title = post.get("name", "")
                tagline = post.get("tagline", "")
                url = post.get("discussion_url", "") or f"https://producthunt.com/posts/{post.get('slug', '')}"
                votes = post.get("votes_count", 0)
                comments = post.get("comments_count", 0)

                item_id = hashlib.md5(str(post.get("id", "")).encode()).hexdigest()[:12]

                items.append({
                    "id": item_id,
                    "title": f"{title} - {tagline}" if tagline else title,
                    "url": url,
                    "score": votes,
                    "comments": comments,
                    "author": post.get("creator", {}).get("name", "") if isinstance(post.get("creator"), dict) else "",
                    "created_at": time.time(),
                    "metadata": {
                        "tagline": tagline,
                        "source": "producthunt_api",
                    }
                })
            except Exception as e:
                continue

    except Exception as e:
        error = str(e)

    return {
        "source": "producthunt",
        "items": items,
        "error": error
    }
