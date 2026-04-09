"""
Google Trends 服务
使用 pytrends 获取 Google 搜索趋势
"""

import os
import hashlib
import time


async def get_google_trends(keyword: str = "") -> dict:
    """
    获取 Google Trends 数据

    Args:
        keyword: 搜索关键词，不传则获取实时热门搜索

    Returns:
        {"source": "google", "items": [...], "error": None}
    """
    items = []
    error = None

    try:
        from pytrends.request import TrendReq

        pytrends = TrendReq(hl='en-US', tz=360, timeout=(10, 25))

        if keyword:
            # 获取特定关键词的趋势数据
            try:
                pytrends.build_payload([keyword], cat=0, timeframe='now 1-d', geo='')
                interest_over_time = pytrends.interest_over_time()

                if not interest_over_time.empty:
                    for idx, row in interest_over_time.iterrows():
                        ts = idx.timestamp() if hasattr(idx, 'timestamp') else 0
                        if hasattr(ts, 'timestamp'):
                            ts = ts.timestamp()

                        item_id = hashlib.md5(f"{keyword}{idx}".encode()).hexdigest()[:12]
                        items.append({
                            "id": item_id,
                            "title": keyword,
                            "url": f"https://www.google.com/search?q={keyword}",
                            "score": int(row[keyword]) if keyword in row else 0,
                            "comments": 0,
                            "author": "",
                            "created_at": ts,
                            "metadata": {
                                "query": keyword,
                                "traffic": str(row[keyword]) if keyword in row else "0",
                            }
                        })
            except Exception as e:
                error = f"关键词趋势获取失败: {str(e)}"
        else:
            # 获取实时热门搜索 - 使用备用方法
            try:
                # 方法1: 尝试 trending_searches
                trending_searches = pytrends.trending_searches(pn='united_states')

                if not trending_searches.empty:
                    for i, row in trending_searches.iterrows():
                        query = row.iloc[0] if len(row) > 0 else str(row)
                        if not isinstance(query, str):
                            query = str(query)

                        item_id = hashlib.md5(query.encode()).hexdigest()[:12]
                        items.append({
                            "id": item_id,
                            "title": query,
                            "url": f"https://www.google.com/search?q={query}",
                            "score": 100 - i * 2,
                            "comments": 0,
                            "author": "",
                            "created_at": time.time(),
                            "metadata": {
                                "query": query,
                                "traffic": "热",
                                "rank": i + 1,
                            }
                        })
            except Exception as e:
                # 方法2: 尝试使用 search_suggestions
                try:
                    suggestions = pytrends.search_suggestions(keyword='trending')
                    for i, item in enumerate(suggestions):
                        query = item.get('title', '') if isinstance(item, dict) else str(item)
                        item_id = hashlib.md5(query.encode()).hexdigest()[:12]
                        items.append({
                            "id": item_id,
                            "title": query,
                            "url": f"https://www.google.com/search?q={query}",
                            "score": 100 - i * 2,
                            "comments": 0,
                            "author": "",
                            "created_at": time.time(),
                            "metadata": {
                                "query": query,
                                "traffic": "热",
                            }
                        })
                except:
                    error = f"Google Trends 在当前网络环境下无法访问（可能被防火墙拦截）"

    except ImportError:
        error = "pytrends 库未安装，请运行: pip install pytrends"
    except Exception as e:
        error = f"Google Trends 获取失败: {str(e)}"

    return {
        "source": "google",
        "items": items,
        "error": error
    }


async def get_google_trends_by_country(country: str = "US") -> dict:
    """
    获取特定国家的 Google 热门搜索

    Args:
        country: 国家代码，如 US, CN, JP

    Returns:
        {"source": "google_country", "items": [...], "error": None}
    """
    items = []
    error = None

    try:
        from pytrends.request import TrendReq

        # WOEID 映射表（部分）
        WOEID_MAP = {
            "US": 23424977,
            "CN": 23424768,
            "JP": 23424856,
            "GB": 23424975,
            "DE": 23424829,
            "FR": 23424808,
        }

        woeid = WOEID_MAP.get(country.upper(), 23424977)  # 默认美国

        pytrends = TrendReq(hl='en-US', tz=360, timeout=(10, 25))
        pytrends.build_payload([], cat=0, timeframe='now 1-d', geo='')

        # 获取今日热门搜索
        try:
            trending_searches = pytrends.trending_searches(pn=country.lower())
        except:
            trending_searches = pytrends.trending_searches()

        if not trending_searches.empty:
            for i, row in trending_searches.iterrows():
                query = row.iloc[0] if len(row) > 0 else str(row)
                if not isinstance(query, str):
                    query = str(query)

                item_id = hashlib.md5(query.encode()).hexdigest()[:12]
                items.append({
                    "id": item_id,
                    "title": query,
                    "url": f"https://www.google.com/search?q={query}",
                    "score": 100 - i * 2,
                    "comments": 0,
                    "author": "",
                    "created_at": time.time(),
                    "metadata": {
                        "query": query,
                        "country": country,
                        "rank": i + 1,
                    }
                })

    except ImportError:
        error = "pytrends 库未安装"
    except Exception as e:
        error = str(e)

    return {
        "source": "google_country",
        "items": items,
        "error": error
    }


async def get_google_trends_realtime(geo: str = "US") -> dict:
    """
    获取 Google 实时热门搜索（按地区）

    Args:
        geo: 地区代码，如 US, GBR, CHN

    Returns:
        {"source": "google_realtime", "items": [...], "error": None}
    """
    items = []
    error = None

    try:
        from pytrends.request import TrendReq

        pytrends = TrendReq(hl='en-US', tz=360, timeout=(10, 25))

        try:
            # 实时趋势
            trending_searches = pytrends.trending_searches(geo=geo)
        except:
            trending_searches = pytrends.trending_searches()

        if not trending_searches.empty:
            for i, row in trending_searches.iterrows():
                query = row.iloc[0] if len(row) > 0 else str(row)
                if not isinstance(query, str):
                    query = str(query)

                item_id = hashlib.md5(query.encode()).hexdigest()[:12]
                items.append({
                    "id": item_id,
                    "title": query,
                    "url": f"https://www.google.com/search?q={query}",
                    "score": 100 - i * 2,
                    "comments": 0,
                    "author": "",
                    "created_at": time.time(),
                    "metadata": {
                        "query": query,
                        "geo": geo,
                        "rank": i + 1,
                    }
                })

    except ImportError:
        error = "pytrends 库未安装"
    except Exception as e:
        error = str(e)

    return {
        "source": "google_realtime",
        "items": items,
        "error": error
    }
