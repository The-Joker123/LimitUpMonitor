from fastapi import APIRouter
from typing import Dict, Optional
import akshare as ak
import requests
from datetime import datetime, timedelta

from services.emotion import EMOTION_WEIGHT_LB, EMOTION_WEIGHT_HIGH, EMOTION_WEIGHT_BOARD_SQUARED

router = APIRouter(prefix="/api", tags=["market"])


@router.get("/emotion-history")
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
                except (ValueError, TypeError):
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
            emotion_score = lb_count * EMOTION_WEIGHT_LB + high_count * EMOTION_WEIGHT_HIGH + pow(max_board, 2) * EMOTION_WEIGHT_BOARD_SQUARED

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


@router.get("/sh-index")
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
