# -*- coding: utf-8 -*-
"""
第三周 · 趋势指标计算模块
功能：从 price_data 表读取数据，计算各品种的
    1) 日均价
    2) 周均价
    3) 月度变化率（当月均价 vs 上月均价的涨跌幅 %）
作为独立模块，供 ARIMA 预测和价格监控模块复用。
"""
import os
import datetime

import pymysql
import pandas as pd

os.environ["NO_PROXY"] = "*"
os.environ["no_proxy"] = "*"

DB_CONFIG = {
    "host": "localhost",
    "port": 3306,
    "user": "root",
    "password": "Price@2026",
    "database": "price_forecast",
    "charset": "utf8mb4",
}


def get_conn():
    return pymysql.connect(**DB_CONFIG)


def load_price_series(goods_id):
    """
    从 price_data 表读取某个商品的日价格序列
    返回 DataFrame：price_date(索引) / price
    说明：一个商品同一天可能有多个地区，这里取"全国"或均值做日价。
    """
    sql = """
        SELECT price_date, AVG(price) AS price
        FROM price_data
        WHERE goods_id = %s
        GROUP BY price_date
        ORDER BY price_date
    """
    df = pd.read_sql(sql, get_conn(), params=(goods_id,))
    df["price_date"] = pd.to_datetime(df["price_date"])
    df = df.set_index("price_date")
    return df


def daily_avg(df):
    """日均价：直接返回日价格序列（按天已聚合）"""
    return df


def weekly_avg(df):
    """周均价：按周(周一为起点)重采样取均值"""
    return df["price"].resample("W-MON").mean().dropna()


def monthly_avg(df):
    """月均价：按月重采样取均值"""
    return df["price"].resample("ME").mean().dropna()


def monthly_change_rate(df):
    """
    月度变化率(%)：当月均价相对上月均价的涨跌幅
    返回 Series：日期(月末) -> 变化率(%)
    """
    m = monthly_avg(df)
    # pct_change 是 (本月-上月)/上月
    return m.pct_change() * 100


def get_indicators(goods_id):
    """
    汇总计算某个商品的全部趋势指标，返回 dict：
      daily_avg    -> DataFrame
      weekly_avg   -> Series
      monthly_avg  -> Series
      monthly_chg  -> Series（月度变化率 %）
    """
    df = load_price_series(goods_id)
    if df.empty:
        return None
    return {
        "daily_avg": daily_avg(df),
        "weekly_avg": weekly_avg(df),
        "monthly_avg": monthly_avg(df),
        "monthly_chg": monthly_change_rate(df),
    }


if __name__ == "__main__":
    # 自测：打印猪肉(goods_id=4)的各项指标
    gid = 4
    ind = get_indicators(gid)
    if ind is None:
        print("无数据")
    else:
        print("=== 猪肉(goods_id=4) 趋势指标 ===")
        print(f"日均价：共 {len(ind['daily_avg'])} 天，最近5天：")
        print(ind["daily_avg"].tail(5).to_string())
        print(f"\n周均价：最近5周：")
        print(ind["weekly_avg"].tail(5).to_string())
        print(f"\n月均价：最近6个月：")
        print(ind["monthly_avg"].tail(6).to_string())
        print(f"\n月度变化率(%)：最近6个月：")
        print(ind["monthly_chg"].tail(6).to_string())
