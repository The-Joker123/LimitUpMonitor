"""
GitHub Trending 爬虫服务
爬取 github.com/trending 获取热门项目
"""

import requests
from bs4 import BeautifulSoup
import time
import hashlib


BASE_URL = "https://github.com/trending"

# User-Agent 列表，轮换使用
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
]

# 请求间隔（秒），避免频率过高
MIN_REQUEST_INTERVAL = 5


def get_headers():
    """生成随机 headers"""
    import random
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }


def parse_stars_count(text: str) -> int:
    """解析 star 数量文本"""
    text = text.strip().replace(",", "")
    if not text:
        return 0
    if text.endswith("k"):
        try:
            return int(float(text[:-1]) * 1000)
        except:
            return 0
    if text.endswith("M"):
        try:
            return int(float(text[:-1]) * 1000000)
        except:
            return 0
    try:
        return int(text)
    except:
        return 0


def parse_relative_time(text: str) -> float:
    """解析相对时间为 unix timestamp"""
    text = text.strip().lower()
    now = time.time()

    if "today" in text:
        return now
    elif "yesterday" in text:
        return now - 86400
    elif "days ago" in text:
        try:
            days = int(text.split()[0])
            return now - days * 86400
        except:
            return now - 86400
    elif "weeks ago" in text:
        try:
            weeks = int(text.split()[0])
            return now - weeks * 7 * 86400
        except:
            return now - 7 * 86400
    elif "months ago" in text:
        try:
            months = int(text.split()[0])
            return now - months * 30 * 86400
        except:
            return now - 30 * 86400
    return now


async def get_github_trending(language: str = "", period: str = "daily") -> dict:
    """
    获取 GitHub Trending 列表

    Args:
        language: 编程语言筛选，如 python, javascript
        period: 时间范围 daily, weekly, monthly

    Returns:
        {"source": "github", "items": [...], "error": None}
    """
    items = []
    error = None

    try:
        # 构建 URL
        url = BASE_URL
        if language:
            url = f"{BASE_URL}/{language}"
        if period and period != "daily":
            url = f"{url}?since={period}"

        headers = get_headers()
        response = requests.get(url, headers=headers, timeout=15)

        if response.status_code != 200:
            return {
                "source": "github",
                "items": [],
                "error": f"HTTP {response.status_code}"
            }

        soup = BeautifulSoup(response.content, "html.parser")

        # 查找所有仓库条目
        articles = soup.find_all("article", class_="Box-row")

        for article in articles:
            try:
                # 仓库名和作者
                repo_link = article.find("h2", class_="h3")
                if not repo_link:
                    continue

                repo_full_name = repo_link.get_text(strip=True)
                parts = repo_full_name.split("/")
                if len(parts) != 2:
                    continue

                author, repo_name = parts

                # 仓库 URL
                repo_url_tag = repo_link.find("a")
                repo_url = f"https://github.com{repo_url_tag['href']}" if repo_url_tag else ""

                # 描述
                desc_tag = article.find("p")
                description = desc_tag.get_text(strip=True) if desc_tag else ""

                # 编程语言
                lang_tag = article.find("span", itemprop="programmingLanguage")
                lang = lang_tag.get_text(strip=True) if lang_tag else ""

                # Stars 和 Forks
                stars_text = ""
                forks_text = ""
                for a_tag in article.find_all("a"):
                    href = a_tag.get("href", "")
                    if "/stargazers" in href:
                        stars_text = a_tag.get_text(strip=True)
                    elif "/network/members" in href:
                        forks_text = a_tag.get_text(strip=True)

                stars = parse_stars_count(stars_text)
                forks = parse_stars_count(forks_text)

                # 新增 stars（今日）
                new_stars_tag = article.find("span", class_="d-inline-block")
                new_stars = 0
                if new_stars_tag:
                    new_stars_text = new_stars_tag.get_text(strip=True)
                    if "stars" in new_stars_text.lower():
                        new_stars = parse_stars_count(new_stars_text)

                # 生成唯一 ID
                item_id = hashlib.md5(repo_full_name.encode()).hexdigest()[:12]

                items.append({
                    "id": item_id,
                    "title": repo_name,
                    "url": repo_url,
                    "score": stars,
                    "comments": forks,
                    "author": author,
                    "created_at": time.time(),  # trending 不提供创建时间，用当前时间
                    "metadata": {
                        "repo_full_name": repo_full_name,
                        "description": description,
                        "language": lang,
                        "new_stars_today": new_stars,
                        "author_url": f"https://github.com/{author}",
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
        "source": "github",
        "items": items,
        "error": error
    }
