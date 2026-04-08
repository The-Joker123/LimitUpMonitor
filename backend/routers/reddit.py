from fastapi import APIRouter
import requests
import xml.etree.ElementTree as ET
from datetime import datetime

router = APIRouter(prefix="/api", tags=["reddit"])

ALLOWED_SUBREDDITS = [
    "worldnews", "technology", "programming",
    "science", "business", "stocks"
]


def parse_iso8601(date_str: str) -> float:
    """解析 ISO8601 日期字符串为 unix timestamp"""
    try:
        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        return dt.timestamp()
    except Exception:
        return 0


@router.get("/reddit/{subreddit}")
def get_reddit_hot(subreddit: str, sort: str = "hot"):
    """获取 Reddit 指定版块的帖子（RSS 方式）"""
    if subreddit not in ALLOWED_SUBREDDITS:
        return {"error": "不允许访问该版块", "posts": []}

    sort_map = {"hot": "hot", "new": "new", "top": "top"}
    sort_suffix = sort_map.get(sort, "hot")

    try:
        url = f"https://www.reddit.com/r/{subreddit}/{sort_suffix}.rss"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/rss+xml"
        }
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code != 200:
            return {"error": f"RSS fetch error: {response.status_code}", "posts": []}

        root = ET.fromstring(response.content)
        posts = []

        # Reddit RSS 命名空间
        ns = {
            "feed": "http://www.w3.org/2005/Atom",
            "reddit": "http://reddit.com/atoms/1.0/"
        }

        for entry in root.findall("feed:entry", ns):
            title = entry.find("feed:title", ns)
            link = entry.find("feed:link", ns)
            id_elem = entry.find("feed:id", ns)
            updated = entry.find("feed:updated", ns)
            author = entry.find("feed:author/feed:name", ns)

            # reddit:category 包含评分和评论数
            category = entry.find("feed:category", ns)
            score = 0
            num_comments = 0
            if category is not None:
                for attr in category.attrib:
                    if attr.endswith("label"):
                        pass
                # 从 category 的 term 属性解析，如 "score:123" 或 "comments:456"
                term = category.get("term", "")
                if term.startswith("score:"):
                    score = int(term.split(":")[1]) if term.split(":")[1].isdigit() else 0
                elif term.startswith("comments:"):
                    num_comments = int(term.split(":")[1]) if term.split(":")[1].isdigit() else 0

            # 获取 permalink 和 url
            permalink = ""
            post_url = ""
            if link is not None:
                post_url = link.get("href", "")
                # Reddit RSS 的 link href 就是完整 URL
                permalink = post_url

            # selftext/内容在 content 里
            content = entry.find("feed:content", ns)
            selftext = content.text if content is not None else ""

            posts.append({
                "id": id_elem.text if id_elem is not None else "",
                "title": title.text if title is not None else "",
                "url": post_url,
                "permalink": permalink,
                "score": score,
                "num_comments": num_comments,
                "author": author.text if author is not None else "[deleted]",
                "created_utc": parse_iso8601(updated.text) if updated is not None else 0,
                "subreddit": subreddit,
                "selftext": selftext,
            })

        return {"subreddit": subreddit, "posts": posts}
    except Exception as e:
        return {"error": str(e), "posts": []}
