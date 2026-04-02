from fastapi import APIRouter
import os
import requests

router = APIRouter(prefix="/api", tags=["util"])


@router.get("/translate")
def translate_text(text: str, from_lang: str = "en", to_lang: str = "zh"):
    """
    翻译文本（使用 MyMemory 免费翻译API）
    """
    try:
        lang_pair = f"{from_lang}|{to_lang}"
        url = "https://api.mymemory.translated.net/get"
        params = {"q": text, "langpair": lang_pair}
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        if data.get("responseStatus") == 200:
            return {
                "translation": data.get("responseData", {}).get("translatedText", text)
            }
        else:
            return {"error": data.get("responseDetails", "翻译失败")}
    except Exception as e:
        return {"error": str(e)}


@router.get("/twitter/trending")
def get_twitter_trending(woeid: int = 1):
    """
    获取Twitter热门话题趋势
    woeid: 地区ID，默认1是全球，其他常用值：23424977(中国)、24591127(纽约)等
    """
    proxy = (
        os.getenv("HTTP_PROXY")
        or os.getenv("http_proxy")
        or os.getenv("HTTPS_PROXY")
        or os.getenv("https_proxy")
    )
    proxies = {"http": proxy, "https": proxy} if proxy else None

    bearer_token = os.getenv("TWITTER_BEARER_TOKEN")

    if not bearer_token:
        api_key = os.getenv("TWITTER_API_KEY")
        api_secret = os.getenv("TWITTER_API_SECRET")
        if not api_key or not api_secret:
            return {"error": "Twitter API key not configured", "trends": []}
        try:
            import base64

            credentials = base64.b64encode(f"{api_key}:{api_secret}".encode()).decode()
            token_response = requests.post(
                "https://api.twitter.com/oauth2/token",
                headers={
                    "Authorization": f"Basic {credentials}",
                    "Content-Type": "application/x-www-form-urlencoded",
                },
                data={"grant_type": "client_credentials"},
                timeout=10,
                proxies=proxies,
            )
            if token_response.status_code != 200:
                return {
                    "error": "Failed to obtain Twitter API credentials",
                    "trends": [],
                }
            bearer_token = token_response.json().get("access_token")
        except Exception as e:
            return {"error": str(e), "trends": []}

    try:
        trends_url = f"https://api.twitter.com/1.1/trends/place.json?id={woeid}"
        trends_response = requests.get(
            trends_url,
            headers={"Authorization": f"Bearer {bearer_token}"},
            timeout=10,
            proxies=proxies,
        )

        if trends_response.status_code != 200:
            return {
                "error": "Failed to fetch Twitter trending topics",
                "trends": [],
            }

        data = trends_response.json()
        if data and len(data) > 0:
            trends = data[0].get("trends", [])
            return {
                "location": data[0].get("name", "Unknown"),
                "trends": [
                    {
                        "name": t["name"],
                        "url": t.get("url", ""),
                        "tweet_volume": t.get("tweet_volume", 0),
                    }
                    for t in trends[:20]
                ],
            }
        return {"trends": []}

    except Exception as e:
        print(f"获取Twitter趋势失败: {e}")
        return {"error": str(e), "trends": []}
