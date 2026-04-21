from fastapi import APIRouter
import requests
from datetime import datetime, timedelta

router = APIRouter(prefix="/api/trending", tags=["trending"])

GITHUB_API_URL = "https://api.github.com/search/repositories"


def get_date_range(period: str) -> str:
    """Get the date range for GitHub trending period"""
    now = datetime.now()
    if period == "daily":
        start_date = now - timedelta(days=1)
    elif period == "weekly":
        start_date = now - timedelta(days=7)
    elif period == "monthly":
        start_date = now - timedelta(days=30)
    else:
        start_date = now - timedelta(days=7)
    return start_date.strftime("%Y-%m-%d")


@router.get("/github")
def get_github_trending(language: str = "", period: str = "weekly"):
    """Get GitHub trending repositories"""
    try:
        date_range = get_date_range(period)

        query = f"created:>{date_range}"
        if language:
            query += f" language:{language}"

        params = {"q": query, "sort": "stars", "order": "desc", "per_page": 30}

        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "LimitUpMonitor/1.0",
        }

        response = requests.get(
            GITHUB_API_URL, params=params, headers=headers, timeout=30
        )

        if response.status_code != 200:
            return {"error": f"GitHub API error: {response.status_code}", "items": []}

        data = response.json()
        items = []

        for repo in data.get("items", []):
            items.append(
                {
                    "id": str(repo.get("id", "")),
                    "title": repo.get("full_name", ""),
                    "url": repo.get("html_url", ""),
                    "author": repo.get("owner", {}).get("login", ""),
                    "score": repo.get("stargazers_count", 0),
                    "comments": repo.get("comments", 0),
                    "metadata": {
                        "description": repo.get("description", ""),
                        "language": repo.get("language", ""),
                        "new_stars_today": 0,
                    },
                }
            )

        return {"items": items}
    except Exception as e:
        return {"error": str(e), "items": []}
