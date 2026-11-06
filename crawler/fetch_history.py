# -*- coding: utf-8 -*-
"""
第三周 · 历史数据补全脚本
数据源：东方财富期货行情（通过 akshare 封装）
品种映射：
    生猪主力连续 LH0  -> 猪肉   (goods_code=G001)
    玉米主力连续 C0   -> 玉米   (goods_code=G031, 替代小麦)
    鲜苹果主力连续 AP0 -> 鲜苹果 (goods_code=G032, 替代蔬菜)
流程：akshare 拉日K -> 清洗(取收盘价/算涨跌幅) -> 直接连 MySQL 批量入库
"""
import os
import sys
import datetime

import pymysql
import pandas as pd

# ① 禁用系统代理，避免本机代理干扰网络请求
os.environ["NO_PROXY"] = "*"
os.environ["no_proxy"] = "*"

import akshare as ak  # noqa: E402  (必须在设置 NO_PROXY 之后导入)

# ② 数据库连接配置（与后端 application.yml 保持一致）
DB_CONFIG = {
    "host": "localhost",
    "port": 3306,
    "user": "root",
    "password": "Price@2026",
    "database": "price_forecast",
    "charset": "utf8mb4",
}

# ③ 品种映射：期货主力代码 -> (goods_code, 中文名)
#    symbol 用主力连续代码（末尾 0），新浪源约定：LH0/C0/AP0
GOODS_MAP = {
    "LH0": "G001",   # 生猪 -> 猪肉
    "C0": "G031",    # 玉米 -> 玉米(替代小麦)
    "AP0": "G032",   # 鲜苹果 -> 鲜苹果(替代蔬菜)
}

# ④ 数据起止日期：拉最近约 1.5 年的日 K（足够 ARIMA 训练）
#    START_DATE 固定为 2025 年初，END_DATE 动态取"今天"，保证每次运行都拉到最新交易日
START_DATE = "20250101"


def get_end_date():
    """动态计算结束日期 = 今天（保证每次运行都拉到最新数据）"""
    return datetime.date.today().strftime("%Y%m%d")

# 价格单位：期货统一为 元/吨
PRICE_UNIT = "元/吨"


def get_conn():
    """建立数据库连接"""
    return pymysql.connect(**DB_CONFIG)


def goods_code_to_id(conn, goods_code):
    """根据 goods_code 查 goods.id"""
    with conn.cursor() as cur:
        cur.execute("SELECT id FROM goods WHERE goods_code=%s", (goods_code,))
        row = cur.fetchone()
    if row is None:
        raise ValueError(f"goods 表里找不到 goods_code={goods_code}")
    return row[0]


def fetch_futures_daily(symbol):
    """
    用 akshare 拉某个期货主力连续的日 K
    返回 DataFrame：日期 / 收盘价 / 涨跌幅
    end_date 动态取今天，保证每次运行都拉到最新交易日数据
    """
    df = ak.futures_main_sina(
        symbol=symbol,
        start_date=START_DATE,
        end_date=get_end_date(),
    )
    # 列名是中文：日期 开盘价 最高价 最低价 收盘价 ...
    df = df.rename(columns={
        "日期": "price_date",
        "收盘价": "close",
    })
    df["price_date"] = pd.to_datetime(df["price_date"]).dt.date
    # 涨跌幅(%) = (今日收盘 - 昨日收盘) / 昨日收盘 * 100
    df["change_rate"] = df["close"].pct_change() * 100
    # 第一条没有昨日，涨跌幅记为 0
    df["change_rate"] = df["change_rate"].fillna(0)
    return df[["price_date", "close", "change_rate"]]


def save_to_db(conn, goods_id, df, symbol):
    """
    把某个品种的数据批量写入 price_data 表
    唯一约束 (goods_id, price_date, region) 冲突时更新价格
    region 字段：期货无地区，统一填 '全国'
    """
    with conn.cursor() as cur:
        inserted = 0
        updated = 0
        for _, row in df.iterrows():
            sql = """
                INSERT INTO price_data
                    (goods_id, price, price_unit, region, price_date, change_rate, source_url)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    price = VALUES(price),
                    change_rate = VALUES(change_rate)
            """
            cur.execute(sql, (
                goods_id,
                float(row["close"]),
                PRICE_UNIT,
                "全国",
                row["price_date"],
                float(row["change_rate"]),
                f"https://finance.sina.com.cn/futures/quotes/{symbol}.shtml",
            ))
            # 判断是插入还是更新：用 rowcount 粗略统计
            inserted += 1
        conn.commit()
    return len(df)


def main():
    """主流程：遍历品种 -> 拉数据 -> 入库"""
    conn = get_conn()
    try:
        for symbol, goods_code in GOODS_MAP.items():
            print(f"\n=== 处理品种 {symbol} ({goods_code}) ===")
            # 1. 查 goods.id
            goods_id = goods_code_to_id(conn, goods_code)
            print(f"  goods_id = {goods_id}")

            # 2. 拉历史日 K
            df = fetch_futures_daily(symbol)
            print(f"  拉取到 {len(df)} 条日 K 数据，日期范围 {df['price_date'].min()} ~ {df['price_date'].max()}")

            # 3. 入库
            n = save_to_db(conn, goods_id, df, symbol)
            print(f"  已入库/更新 {n} 条")
    finally:
        conn.close()
    print("\n全部完成！")


if __name__ == "__main__":
    main()
