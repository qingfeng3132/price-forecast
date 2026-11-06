# -*- coding: utf-8 -*-
"""
第三周 · ARIMA 离线预测模型
功能：
    1) 从 price_data 表读取某商品的日价格序列
    2) 训练 ARIMA 模型（自动定阶）
    3) 预测未来 7 天价格 + 置信区间
    4) 结果写入 forecast 表
模型：statsmodels.tsa.arima.model.ARIMA
"""
import os
import datetime
import warnings

import pymysql
import pandas as pd
import numpy as np
from statsmodels.tsa.arima.model import ARIMA

warnings.filterwarnings("ignore")

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

MODEL_NAME = "ARIMA"
FORECAST_DAYS = 7  # 预测未来 7 天


def get_conn():
    return pymysql.connect(**DB_CONFIG)


def load_price_series(goods_id):
    """读取某商品的日价格序列（按天聚合，取日均价）"""
    sql = """
        SELECT price_date, AVG(price) AS price
        FROM price_data
        WHERE goods_id = %s
        GROUP BY price_date
        ORDER BY price_date
    """
    with get_conn() as conn:
        df = pd.read_sql(sql, conn, params=(goods_id,))
    df["price_date"] = pd.to_datetime(df["price_date"])
    df = df.set_index("price_date")
    return df


def auto_arima_order(series, max_p=5, max_q=5):
    """
    简单自动定阶：用 AIC 网格搜索 p、q（d 固定为 1，先差分一次消趋势）
    返回 (p, d, q)
    """
    best_aic = np.inf
    best_order = (1, 1, 1)
    d = 1
    for p in range(max_p + 1):
        for q in range(max_q + 1):
            if p == 0 and q == 0:
                continue
            try:
                model = ARIMA(series, order=(p, d, q))
                fit = model.fit()
                if fit.aic < best_aic:
                    best_aic = fit.aic
                    best_order = (p, d, q)
            except Exception:
                continue
    return best_order, best_aic


def train_and_forecast(goods_id):
    """
    训练 ARIMA 并预测未来 7 天
    返回 dict：order / aic / forecast_df(日期,预测值,置信区间)
    """
    df = load_price_series(goods_id)
    if df.empty:
        raise ValueError("该商品无价格数据")

    series = df["price"].astype(float)

    # 数据太少则无法训练
    if len(series) < 30:
        raise ValueError(f"数据点不足({len(series)}条)，ARIMA 至少需要 30 个点")

    # 自动定阶
    order, aic = auto_arima_order(series)

    # 用最优阶数重新训练
    model = ARIMA(series, order=order)
    fit = model.fit()

    # 预测未来 7 天
    forecast_result = fit.get_forecast(steps=FORECAST_DAYS)
    forecast_mean = forecast_result.predicted_mean
    conf_int = forecast_result.conf_int(alpha=0.05)  # 95% 置信区间

    # 构造预测日期：从最后一天往后推，跳过周末（期货周六日不交易）
    last_date = df.index[-1]
    forecast_dates = _next_trading_days(last_date, FORECAST_DAYS)

    forecast_df = pd.DataFrame({
        "forecast_date": forecast_dates,
        "forecast_price": forecast_mean.values,
        "lower": conf_int.iloc[:, 0].values,
        "upper": conf_int.iloc[:, 1].values,
    })

    return {
        "order": order,
        "aic": aic,
        "forecast_df": forecast_df,
        "last_price": float(series.iloc[-1]),
        "last_date": last_date,
    }


def _next_trading_days(start_date, n):
    """
    生成从 start_date 之后开始的 n 个交易日（跳过周六、周日）
    期货市场只在周一到周五交易
    """
    days = []
    d = start_date + datetime.timedelta(days=1)
    while len(days) < n:
        if d.weekday() < 5:  # 0=周一 ... 4=周五，5=周六 6=周日
            days.append(d)
        d += datetime.timedelta(days=1)
    return days


def save_forecast(goods_id, result):
    """
    把预测结果写入 forecast 表
    唯一约束 (goods_id, model_name, forecast_date) 冲突时更新
    """
    df = result["forecast_df"]
    basis = (
        f"ARIMA{result['order']} 模型，AIC={result['aic']:.2f}，"
        f"基于 {result['last_date'].date()} 前历史日价训练，"
        f"最新价 {result['last_price']:.2f} 元/吨"
    )
    # 置信度：用 AIC 反推一个 0~1 的简单置信度（AIC 越小越可信）
    confidence = max(0.0, min(1.0, 1.0 / (1.0 + abs(result["aic"]) / 1000.0)))

    with get_conn() as conn:
        with conn.cursor() as cur:
            # 先删除该商品该模型的旧预测（避免历史预测残留）
            cur.execute(
                "DELETE FROM forecast WHERE goods_id=%s AND model_name=%s",
                (goods_id, MODEL_NAME),
            )
            for _, row in df.iterrows():
                sql = """
                    INSERT INTO forecast
                        (goods_id, forecast_date, forecast_price, model_name, confidence, basis_summary)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """
                cur.execute(sql, (
                    goods_id,
                    row["forecast_date"].date(),
                    float(row["forecast_price"]),
                    MODEL_NAME,
                    confidence,
                    basis,
                ))
        conn.commit()
    return len(df)


def main():
    """主流程：对"期货农产品"分类下的所有品种逐个训练并预测"""
    # 动态读 goods 表：category_id=5（期货农产品）的所有商品
    sql = """
        SELECT id, goods_name FROM goods
        WHERE category_id = (SELECT id FROM goods_category WHERE category_code='FUTURES')
        ORDER BY id
    """
    with get_conn() as conn:
        goods_list = pd.read_sql(sql, conn)

    if goods_list.empty:
        print("无期货农产品品种，请先运行 init_catalog.py 初始化")
        return

    print(f"共 {len(goods_list)} 个品种需要预测\n")
    for _, row in goods_list.iterrows():
        gid = int(row["id"])
        name = row["goods_name"]
        print(f"{'='*50}")
        print(f"=== 训练 {name}(goods_id={gid}) ===")
        try:
            result = train_and_forecast(gid)
            print(f"  定阶 ARIMA{result['order']}，AIC={result['aic']:.2f}")
            print(f"  最新价 {result['last_price']:.2f}（{result['last_date'].date()}）")
            print(f"  未来 7 天预测：")
            for _, r in result["forecast_df"].iterrows():
                print(f"    {r['forecast_date'].date()}  {r['forecast_price']:.2f}  "
                      f"[{r['lower']:.2f} ~ {r['upper']:.2f}]")
            n = save_forecast(gid, result)
            print(f"  已写入 forecast 表 {n} 条")
        except Exception as e:
            print(f"  [失败] {type(e).__name__}: {e}")

    print("\n全部预测完成！")


if __name__ == "__main__":
    main()
