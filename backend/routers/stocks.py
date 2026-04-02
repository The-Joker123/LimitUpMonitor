from fastapi import APIRouter
from typing import Dict, Optional
import akshare as ak
from datetime import datetime

router = APIRouter(prefix="/api", tags=["stocks"])


@router.get("/limit-up")
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
            except (ValueError, TypeError):
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


@router.get("/stock/profile")
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
