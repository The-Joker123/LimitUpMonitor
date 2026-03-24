"""
A股涨停连板监控系统 V1 - 后端
使用akshare获取东方财富涨停池数据
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import akshare as ak
from datetime import datetime
from typing import List, Dict, Optional

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
def get_limit_up_stocks(date: Optional[str] = None) -> Dict:
    """
    获取东方财富涨停池数据（akshare）
    date: 可选，格式YYYYMMDD，不传则默认今天
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
            except:
                limit_days = 1
            industry = str(row.iloc[15]) if len(row) > 15 else ""

            stocks.append(
                {
                    "code": str(row.iloc[1]),
                    "name": str(row.iloc[2]),
                    "pct_chg": round(float(row.iloc[3]), 2),
                    "limit_up_days": limit_days,
                    "industry": industry,
                }
            )

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


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8080)
