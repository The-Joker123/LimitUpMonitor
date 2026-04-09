"""
雪球热榜爬虫服务
获取雪球热门股票列表
雪球 API 需要模拟请求头来获取数据
"""

import requests
import hashlib
import time
import random


# 雪球 API 端点
XUEQIU_API_BASE = "https://stock.xueqiu.com"
XUEQIU_HOT_URL = f"{XUEQIU_API_BASE}/v5/stock/hot_stock/list.json"

# User-Agent 列表
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1",
]


def get_headers(token: str = None) -> dict:
    """生成雪球请求头"""
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "application/json",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Referer": "https://xueqiu.com/",
        "Origin": "https://xueqiu.com",
        "Cookie": f"xq_a_token={token}" if token else "",
    }


async def get_xueqiu_trending() -> dict:
    """
    获取雪球热门股票

    Returns:
        {"source": "xueqiu", "items": [...], "error": None}
    """
    items = []
    error = None

    try:
        # 雪球热门股票 API
        params = {
            "size": 20,
            "_type": 12,
            "type": 12,
        }

        headers = get_headers()
        response = requests.get(
            XUEQIU_HOT_URL,
            params=params,
            headers=headers,
            timeout=15
        )

        if response.status_code == 401:
            # 需要 token，尝试无 token 获取（可能有限制）
            return {
                "source": "xueqiu",
                "items": [],
                "error": "雪球 API 需要认证，请访问 https://xueqiu.com 获取 Cookie"
            }
        elif response.status_code != 200:
            return {
                "source": "xueqiu",
                "items": [],
                "error": f"HTTP {response.status_code}"
            }

        data = response.json()

        # 检查 API 返回状态
        if data.get("error_code") or data.get("error"):
            error_msg = data.get("error_description") or data.get("error") or "未知错误"
            return {
                "source": "xueqiu",
                "items": [],
                "error": error_msg
            }

        # 解析数据
        stocks = data.get("data", {}).get("items", [])

        for stock in stocks:
            try:
                symbol = stock.get("symbol", "")  # like SH600000, SZ000001
                name = stock.get("name", "")
                current_price = stock.get("current_price", 0)
                percent = stock.get("percent", 0)  # 涨跌幅百分比
                volume = stock.get("volume", 0)  # 成交量
                market_cap = stock.get("market_capital", 0)  # 市值

                # 确定市场（SH/SZ）
                market = "SH" if symbol.startswith("SH") else "SZ" if symbol.startswith("SZ") else ""

                # 生成唯一 ID
                item_id = hashlib.md5(symbol.encode()).hexdigest()[:12]

                # 雪球股票 URL
                stock_url = f"https://xueqiu.com/S/{symbol}"

                items.append({
                    "id": item_id,
                    "title": name,
                    "url": stock_url,
                    "score": int(abs(percent * 100)),  # 用涨跌幅作为热度
                    "comments": 0,
                    "author": symbol,
                    "created_at": time.time(),
                    "metadata": {
                        "symbol": symbol,
                        "name": name,
                        "current_price": current_price,
                        "change_pct": percent,
                        "volume": volume,
                        "market_capital": market_cap,
                        "market": market,
                        "stock_url": stock_url,
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
        "source": "xueqiu",
        "items": items,
        "error": error
    }


async def get_xueqiu_by_token(token: str) -> dict:
    """
    使用 Token 获取雪球热门股票

    Args:
        token: 雪球 xq_a_token

    Returns:
        {"source": "xueqiu", "items": [...], "error": None}
    """
    items = []
    error = None

    try:
        params = {
            "size": 30,
            "_type": 12,
            "type": 12,
        }

        headers = get_headers(token)
        response = requests.get(
            XUEQIU_HOT_URL,
            params=params,
            headers=headers,
            timeout=15
        )

        if response.status_code != 200:
            return {
                "source": "xueqiu",
                "items": [],
                "error": f"HTTP {response.status_code}"
            }

        data = response.json()

        if data.get("error_code"):
            return {
                "source": "xueqiu",
                "items": [],
                "error": data.get("error_description", "未知错误")
            }

        stocks = data.get("data", {}).get("items", [])

        for stock in stocks:
            try:
                symbol = stock.get("symbol", "")
                name = stock.get("name", "")
                current_price = stock.get("current_price", 0)
                percent = stock.get("percent", 0)
                volume = stock.get("volume", 0)

                market = "SH" if symbol.startswith("SH") else "SZ" if symbol.startswith("SZ") else ""
                item_id = hashlib.md5(symbol.encode()).hexdigest()[:12]

                items.append({
                    "id": item_id,
                    "title": name,
                    "url": f"https://xueqiu.com/S/{symbol}",
                    "score": int(abs(percent * 100)),
                    "comments": 0,
                    "author": symbol,
                    "created_at": time.time(),
                    "metadata": {
                        "symbol": symbol,
                        "name": name,
                        "current_price": current_price,
                        "change_pct": percent,
                        "volume": volume,
                        "market": market,
                    }
                })
            except Exception as e:
                continue

    except Exception as e:
        error = str(e)

    return {
        "source": "xueqiu",
        "items": items,
        "error": error
    }
