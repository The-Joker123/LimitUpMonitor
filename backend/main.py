"""
A股涨停连板监控系统 V1 - 后端
使用akshare获取东方财富涨停池数据
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import akshare as ak
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dotenv import load_dotenv
import os
import requests

load_dotenv()

app = FastAPI(title="A股涨停连板监控系统 V1")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def group_industry(industry: str) -> str:
    """将细分行业映射到大致分类"""
    if not industry:
        return "其他"

    industry_map = {
        "电力": [
            "电力",
            "电网设备",
            "光伏设备",
            "风电设备",
            "储能",
            "电池",
            "电机",
            "电工电网",
            "环境治理",
        ],
        "医药": ["化学制药", "中药", "医疗器械", "生物制品", "医药商业", "医疗服务"],
        "科技": [
            "半导体",
            "电子元件",
            "光学光电",
            "消费电子",
            "软件服务",
            "IT设备",
            "通信设备",
        ],
        "汽车": [
            "汽车零部件",
            "汽车整车",
            "摩托车",
            "船舶制造",
            "航空航天",
            "铁路公路",
        ],
        "化工": ["化学制品", "化学工程", "塑料橡胶", "石油开采", "石化", "化纤"],
        "金融": ["证券", "保险", "银行", "多元金融"],
        "消费": [
            "食品饮料",
            "纺织服装",
            "家电",
            "家居用品",
            "零售",
            "旅游",
            "酒店餐饮",
        ],
        "基建": [
            "基础建设",
            "专业工程",
            "工程咨询",
            "装修装饰",
            "园林工程",
            "房地产",
            "水泥",
            "钢铁",
            "煤炭开采",
        ],
        "农业": ["农业", "渔业", "林业", "牧业"],
        "传媒": ["广告包装", "传媒", "文化娱乐", "教育"],
    }

    for category, keywords in industry_map.items():
        for keyword in keywords:
            if keyword in industry:
                return category

    return "其他"


@app.get("/api/limit-up")
def get_limit_up_stocks(date: Optional[str] = None, time_range: str = "all") -> Dict:
    """
    获取东方财富涨停池数据（akshare）
    date: 可选，格式YYYYMMDD，不传则默认今天
    time_range: 可选，"all" 或 "morning"，morning 表示 9:15-10:30 时段
    返回：涨停股列表 + 板块连板统计
    """
    try:
        if date is None:
            date = datetime.now().strftime("%Y%m%d")
        df = ak.stock_zt_pool_em(date=date)

        stocks = []
        for _, row in df.iterrows():
            try:
                limit_days = int(row.iloc[14]) if str(row.iloc[14]) != "-" else 1
            except Exception:
                limit_days = 1
            industry = str(row.iloc[15]) if len(row) > 15 else ""

            first_seal_time = str(row.iloc[10]) if str(row.iloc[10]) != "-" else ""

            stocks.append(
                {
                    "code": str(row.iloc[1]),
                    "name": str(row.iloc[2]),
                    "pct_chg": round(float(row.iloc[3]), 2),
                    "limit_up_days": limit_days,
                    "industry": industry,
                    # 扩展字段
                    "turnover_rate": round(float(row.iloc[8]), 2)
                    if row.iloc[8] != "-"
                    else 0,  # 换手率
                    "seal_fund": int(row.iloc[9])
                    if str(row.iloc[9]) != "-"
                    else 0,  # 封板资金
                    "first_seal_time": first_seal_time,  # 首次封板时间
                    "last_seal_time": str(row.iloc[11])
                    if str(row.iloc[11]) != "-"
                    else "",  # 最后封板时间
                    "amount": int(row.iloc[5])
                    if str(row.iloc[5]) != "-"
                    else 0,  # 成交额
                    "flow_market_cap": round(float(row.iloc[6]) / 1e8, 2)
                    if str(row.iloc[6]) != "-"
                    else 0,  # 流通市值(亿)
                    "bomb_count": int(row.iloc[12])
                    if str(row.iloc[12]) != "-"
                    else 0,  # 炸板次数
                }
            )

        # 时段过滤
        if time_range == "morning":
            stocks = [
                s
                for s in stocks
                if s["first_seal_time"] >= "0915" and s["first_seal_time"] <= "1030"
            ]

        # 从stocks列表计算板块统计
        industry_count = {}  # 全部
        industry_boards = {i: {} for i in range(1, 11)}  # 1-10板
        for s in stocks:
            ind = s["industry"]
            industry_count[ind] = industry_count.get(ind, 0) + 1
            days = s["limit_up_days"]
            if days in industry_boards:
                industry_boards[days][ind] = industry_boards[days].get(ind, 0) + 1

        stocks.sort(key=lambda x: (x["pct_chg"], x["limit_up_days"]), reverse=True)

        industry_stats = [
            {"industry": k, "count": v} for k, v in industry_count.items()
        ]
        industry_stats.sort(key=lambda x: x["count"], reverse=True)

        board_stats = {}
        for days, counts in industry_boards.items():
            if counts:
                stats = [{"industry": k, "count": v} for k, v in counts.items()]
                stats.sort(key=lambda x: x["count"], reverse=True)
                board_stats[f"board_{days}"] = stats

        return {
            "stocks": stocks,
            "industry_stats": industry_stats,
            **board_stats,
        }

    except Exception as e:
        print(f"获取涨停数据失败: {e}")
        return {"stocks": [], "industry_stats": []}


@app.get("/api/health")
def health_check():
    """健康检查"""
    return {"status": "ok"}


@app.get("/api/emotion-history")
def get_emotion_history(
    days: int = 10, time_range: str = "all", industry: Optional[str] = None
) -> Dict:
    """
    获取情绪指数历史数据
    days: 获取最近多少天的数据，默认10天
    time_range: 可选，"all" 或 "morning"，morning 表示 9:15-10:30 时段
    industry: 可选，板块名称过滤
    返回：每日情绪指数数据（含上证指数）
    """
    # 获取上证指数数据
    sh_index_data = {}
    try:
        url = "http://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData"
        params = {
            "symbol": "sh000001",
            "scale": 240,
            "ma": "no",
            "datalen": days,
        }
        response = requests.get(url, params=params, timeout=5)
        sh_data = response.json()
        if sh_data:
            prev_close = None
            for item in sh_data:
                date_str = item.get("day", "")
                close = float(item.get("close", 0))
                if prev_close is not None and prev_close != 0:
                    change = round((close - prev_close) / prev_close * 100, 2)
                else:
                    change = 0.0
                sh_index_data[date_str[5:10].replace("/", "-")] = {
                    "close": close,
                    "change": change,
                }
                prev_close = close
    except Exception as e:
        print(f"获取上证指数数据失败: {e}")

    result = []
    today = datetime.now()

    for i in range(days):
        date = (today - timedelta(days=i)).strftime("%Y%m%d")
        try:
            df = ak.stock_zt_pool_em(date=date)

            if df is None or len(df) == 0:
                continue

            stocks = []
            for _, row in df.iterrows():
                try:
                    limit_days = int(row.iloc[14]) if str(row.iloc[14]) != "-" else 1
                except:
                    limit_days = 1
                first_seal_time = str(row.iloc[10]) if str(row.iloc[10]) != "-" else ""
                ind = str(row.iloc[15]) if len(row) > 15 else ""
                stocks.append(
                    {
                        "limit_up_days": limit_days,
                        "first_seal_time": first_seal_time,
                        "industry": ind,
                    }
                )

            # 时段过滤
            if time_range == "morning":
                stocks = [
                    s
                    for s in stocks
                    if s["first_seal_time"] >= "0915" and s["first_seal_time"] <= "1030"
                ]

            # 板块过滤
            if industry:
                stocks = [s for s in stocks if s["industry"] == industry]

            lb_count = len([s for s in stocks if s["limit_up_days"] >= 2])
            high_count = len([s for s in stocks if s["limit_up_days"] >= 3])
            max_board = max([s["limit_up_days"] for s in stocks], default=0)
            zt_count = len(stocks)
            emotion_score = lb_count * 0.3 + high_count * 0.5 + pow(max_board, 2) * 2

            date_key = date[4:6] + "-" + date[6:8]
            sh_info = sh_index_data.get(date_key, {})

            result.append(
                {
                    "date": date_key,
                    "lbCount": lb_count,
                    "highCount": high_count,
                    "maxBoard": max_board,
                    "emotionScore": emotion_score,
                    "ztCount": zt_count,
                    "shClose": sh_info.get("close"),
                    "shChange": sh_info.get("change"),
                }
            )
        except Exception as e:
            print(f"获取 {date} 数据失败: {e}")

    result.reverse()
    return {"data": result}


@app.get("/api/sh-index")
def get_sh_index(days: int = 10) -> Dict:
    """
    获取上证指数历史数据
    返回：每日上证指数涨跌幅数据
    """
    result = []

    try:
        # 使用新浪财经接口获取上证指数历史数据
        url = "http://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData"
        params = {
            "symbol": "sh000001",
            "scale": 240,  # 日K
            "ma": "no",
            "datalen": days,
        }
        response = requests.get(url, params=params, timeout=5)
        data = response.json()
        if data:
            prev_close = None
            for item in data:
                date_str = item.get("day", "")
                close = float(item.get("close", 0))
                if prev_close is not None and prev_close != 0:
                    change = round((close - prev_close) / prev_close * 100, 2)
                else:
                    change = 0.0
                result.append(
                    {
                        "date": date_str[5:10].replace("/", "-"),
                        "close": close,
                        "change": change,
                    }
                )
                prev_close = close
    except Exception as e:
        print(f"获取上证指数数据失败: {e}")

    return {"data": result}


class ChatRequest(BaseModel):
    messages: list


@app.post("/api/ai-chat")
def ai_chat(request: ChatRequest) -> Dict:
    """
    代理AI聊天请求到 MiniMax Coding Plan API
    """
    api_key = os.getenv("MINIMAX_API_KEY")
    group_id = os.getenv("MINIMAX_GROUP_ID")
    if not api_key:
        return {"error": "MINIMAX_API_KEY 未配置，请在 .env 文件中设置"}
    if not group_id:
        return {"error": "MINIMAX_GROUP_ID 未配置，请在 .env 文件中设置"}

    try:
        response = requests.post(
            "https://api.minimax.chat/v1/text/chatcompletion_pro",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            },
            json={
                "group_id": group_id,
                "model": "MiniMax-Text-01",
                "messages": request.messages,
                "reply_constraints": {"sender_type": "BOT", "receiver_type": "USER"},
                "bot_setting": [
                    {
                        "bot_name": "AI助手",
                        "content": "你是一个有用的AI助手，请用中文回答用户问题。",
                    }
                ],
            },
            timeout=30,
        )
        return response.json()
    except Exception as e:
        return {"error": str(e)}


@app.get("/api/twitter/trending")
def get_twitter_trending(woeid: int = 1) -> Dict:
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
                    "error": f"Failed to get bearer token: {token_response.text}",
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
                "error": f"Failed to get trends: {trends_response.text}",
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


@app.get("/api/stock/profile")
def get_stock_profile(code: str) -> Dict:
    """
    获取股票公司简介（从巨潮资讯获取）
    code: 股票代码，如 "000001"
    """
    try:
        df = ak.stock_profile_cninfo(symbol=code)
        if df is None or len(df) == 0:
            return {"error": "未找到该股票信息"}

        row = df.iloc[0]
        # 提取关键字段
        profile = {
            "code": code,
            "name": str(row.get("公司名称", "")),
            "shortName": str(row.get("A股简称", "")),
            "industry": str(row.get("所属行业", "")),
            "legalRep": str(row.get("法人代表", "")),  # 法人代表
            "registeredCapital": str(row.get("注册资金", "")),  # 注册资金
            "establishDate": str(row.get("成立日期", "")),  # 成立日期
            "listingDate": str(row.get("上市日期", "")),  # 上市日期
            "website": str(row.get("官方网站", "")),
            "phone": str(row.get("联系电话", "")),
            "registeredAddr": str(row.get("注册地址", "")),
            "officeAddr": str(row.get("办公地址", "")),
            "mainBusiness": str(row.get("主营业务", "")),
            "businessScope": str(row.get("经营范围", "")),
            "description": str(row.get("机构简介", "")),
        }
        return profile
    except Exception as e:
        print(f"获取股票简介失败: {e}")
        return {"error": str(e)}


@app.get("/api/translate")
def translate_text(text: str, from_lang: str = "en", to_lang: str = "zh") -> Dict:
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


if __name__ == "__main__":
    import uvicorn
    import json
    from pathlib import Path

    config_path = Path(__file__).parent.parent / "config.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    backend_config = config["backend"]

    uvicorn.run(app, host=backend_config["host"], port=backend_config["port"])
