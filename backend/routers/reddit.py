from fastapi import APIRouter
import requests

router = APIRouter(prefix="/api", tags=["reddit"])

ALLOWED_SUBREDDITS = [
    "worldnews", "technology", "programming",
    "science", "business", "stocks"
]


@router.get("/reddit/{subreddit}")
def get_reddit_hot(subreddit: str):
    """获取 Reddit 指定版块的热门帖子"""
    if subreddit not in ALLOWED_SUBREDDITS:
        return {"error": "不允许访问该版块", "posts": []}

    try:
        url = f"https://www.reddit.com/r/{subreddit}/hot.json"
        headers = {"User-Agent": "LimitUpMonitor/1.0"}
        response = requests.get(url, headers=headers, params={"limit": 20}, timeout=15)
        if response.status_code != 200:
            return {"error": f"Reddit API error: {response.status_code}", "posts": []}

        data = response.json()
        posts = []
        for child in data.get("data", {}).get("children", []):
            post = child.get("data", {})
            posts.append({
                "id": post.get("id"),
                "title": post.get("title"),
                "url": post.get("url"),
                "permalink": f"https://reddit.com{post.get('permalink')}",
                "score": post.get("score"),
                "num_comments": post.get("num_comments"),
                "author": post.get("author"),
                "created_utc": post.get("created_utc"),
                "subreddit": post.get("subreddit"),
                "selftext": post.get("selftext"),
            })
        return {"subreddit": subreddit, "posts": posts}
    except Exception as e:
        return {"error": str(e), "posts": []}
