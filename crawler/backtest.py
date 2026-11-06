# -*- coding: utf-8 -*-
"""
第四周 · 预测模型回测脚本（验证 ARIMA 预测准不准）
思路：滚动回测 —— 对每个品种，用"前 N 天"训练模型，预测"后 7 天"，
      再和真实值对比，算出误差指标，客观评价模型准不准。

误差指标：
  MAE   平均绝对误差（元/吨）
  MAPE  平均绝对百分比误差（%，最直观，<5% 算不错，>10% 基本瞎猜）
  RMSE  均方根误差（元/吨，惩罚大误差）

用法：
  python backtest.py                    # 对全部期货品种回测
  python backtest.py --goods 4          # 只回测某个商品（goods_id）
  python backtest.py --roll 3           # 滚动回测最近 3 段（更严谨）
"""
import os
import sys
import warnings

import numpy as np
import pandas as pd
from statsmodels.tsa.arima.model import ARIMA

warnings.filterwarnings("ignore")
os.environ["NO_PROXY"] = "*"
os.environ["no_proxy"] = "*"

import forecast_arima  # noqa: E402  复用其 load_price_series / auto_arima_order

HOLD_OUT_DAYS = 7   # 留出最后 7 天做测试集


def backtest_once(goods_id, goods_name, roll_count=1):
    """
    单次回测：留出最后 7 天，用前面的数据训练并预测，对比真实值
    返回 dict：包含误差指标和对比明细
    """
    df = forecast_arima.load_price_series(goods_id)
    if df.empty or len(df) < 40:
        return None

    series = df["price"].astype(float)

    results = []
    # 滚动回测：从最后往前滑 roll_count 次，每次留出 7 天测试集
    for i in range(roll_count):
        # 测试集 = 最后 7 天（每次往前挪 7 天）
        train_end = len(series) - HOLD_OUT_DAYS * (i + 1)
        test_start = train_end
        test_end = test_start + HOLD_OUT_DAYS
        if train_end < 30:
            break

        train = series.iloc[:train_end]
        test = series.iloc[test_start:test_end]

        # 训练（自动定阶）
        order, aic = forecast_arima.auto_arima_order(train)
        model = ARIMA(train, order=order)
        fit = model.fit()

        # 预测测试集长度
        forecast_result = fit.get_forecast(steps=len(test))
        pred = forecast_result.predicted_mean.values

        # 对比
        actual = test.values
        mae = np.mean(np.abs(pred - actual))
        # MAPE：真实值不为 0 才计算
        mask = actual != 0
        mape = np.mean(np.abs((pred[mask] - actual[mask]) / actual[mask])) * 100
        rmse = np.sqrt(np.mean((pred - actual) ** 2))

        results.append({
            "段": i + 1,
            "order": order,
            "mae": mae,
            "mape": mape,
            "rmse": rmse,
            "实际区间": f"{test.index[0].date()} ~ {test.index[-1].date()}",
        })

    if not results:
        return None

    # 汇总：多段取平均
    return {
        "goods_id": goods_id,
        "goods_name": goods_name,
        "mae_avg": np.mean([r["mae"] for r in results]),
        "mape_avg": np.mean([r["mape"] for r in results]),
        "rmse_avg": np.mean([r["rmse"] for r in results]),
        "details": results,
    }


def main():
    # 解析参数
    args = sys.argv[1:]
    roll_count = 1
    goods_filter = None
    if "--roll" in args:
        roll_count = int(args[args.index("--roll") + 1])
    if "--goods" in args:
        goods_filter = int(args[args.index("--goods") + 1])

    # 读期货农产品分类下的商品
    sql = """
        SELECT id, goods_name FROM goods
        WHERE category_id = (SELECT id FROM goods_category WHERE category_code='FUTURES')
        ORDER BY id
    """
    with forecast_arima.get_conn() as conn:
        goods_list = pd.read_sql(sql, conn)

    if goods_filter is not None:
        goods_list = goods_list[goods_list["id"] == goods_filter]

    print(f"{'='*70}")
    print(f"ARIMA 预测回测报告（留出最后 {HOLD_OUT_DAYS} 天，滚动 {roll_count} 段）")
    print(f"{'='*70}")

    all_results = []
    for _, row in goods_list.iterrows():
        gid = int(row["id"])
        name = row["goods_name"]
        r = backtest_once(gid, name, roll_count)
        if r is None:
            print(f"\n{name}: 数据不足，跳过")
            continue
        all_results.append(r)
        # 打印单个品种结果
        print(f"\n【{name}】(goods_id={gid})")
        for d in r["details"]:
            print(f"  第{d['段']}段 {d['实际区间']}  ARIMA{d['order']}  "
                  f"MAE={d['mae']:.1f}  MAPE={d['mape']:.2f}%  RMSE={d['rmse']:.1f}")
        print(f"  → 平均 MAPE = {r['mape_avg']:.2f}%")

    # 汇总表
    if all_results:
        print(f"\n{'='*70}")
        print("汇总：按 MAPE 排序（越小越准）")
        print(f"{'='*70}")
        all_results.sort(key=lambda x: x["mape_avg"])
        print(f"{'品种':<10} {'平均MAE':>10} {'平均MAPE':>12} {'平均RMSE':>12}  评价")
        for r in all_results:
            if r["mape_avg"] < 3:
                grade = "优秀"
            elif r["mape_avg"] < 5:
                grade = "良好"
            elif r["mape_avg"] < 10:
                grade = "一般"
            else:
                grade = "较差"
            print(f"{r['goods_name']:<10} {r['mae_avg']:>10.1f} {r['mape_avg']:>11.2f}% "
                  f"{r['rmse_avg']:>12.1f}  {grade}")

        # 总体平均
        overall_mape = np.mean([r["mape_avg"] for r in all_results])
        print(f"\n总体平均 MAPE = {overall_mape:.2f}%")


if __name__ == "__main__":
    main()
