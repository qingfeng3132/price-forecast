# -*- coding: utf-8 -*-
"""
第四周 · 统一离线预测定时任务（每日批处理）
功能：把三个环节串成一条完整流水线，每天定时自动执行
    ① 拉取最新数据（fetch_history：akshare 拉期货日K入库）
    ② 训练预测（forecast_arima：ARIMA 训练 + 未来7天预测写库）
    ③ 监控告警（monitor：月度变化率超10%触发告警）

运行方式：
    python daily_job.py            # 立即跑一次，然后每天 18:00 自动跑
    python daily_job.py --once     # 只跑一次，不进入定时循环
"""
import os
import sys
import time
import datetime

# ① 禁用系统代理（爬虫需要）
os.environ["NO_PROXY"] = "*"
os.environ["no_proxy"] = "*"

import schedule  # noqa: E402

# ② 复用三个模块（import 时不会触发它们的 main，因为有 __main__ 保护）
import fetch_history   # noqa: E402
import forecast_arima  # noqa: E402
import monitor         # noqa: E402


def run_pipeline():
    """
    完整流水线：拉数据 -> 训练预测 -> 监控告警
    每步独立 try，单步失败不影响后续步骤
    """
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n{'='*60}")
    print(f"[{now}] ===== 开始每日离线预测流水线 =====")

    # 步骤①：拉最新数据
    print(f"\n[步骤1/3] 拉取最新期货数据...")
    try:
        fetch_history.main()
        print("[步骤1/3] ✅ 数据拉取完成")
    except Exception as e:
        print(f"[步骤1/3] ❌ 数据拉取失败: {e}")

    # 步骤②：训练 ARIMA + 预测
    print(f"\n[步骤2/3] 训练 ARIMA 模型并预测...")
    try:
        forecast_arima.main()
        print("[步骤2/3] ✅ 预测完成")
    except Exception as e:
        print(f"[步骤2/3] ❌ 预测失败: {e}")

    # 步骤③：监控告警
    print(f"\n[步骤3/3] 检查月度变化率并触发告警...")
    try:
        monitor.main()
        print("[步骤3/3] ✅ 监控完成")
    except Exception as e:
        print(f"[步骤3/3] ❌ 监控失败: {e}")

    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n[{now}] ===== 流水线执行完毕 =====")


def main():
    """入口：先跑一次，然后每天定时跑"""
    # 立即先跑一次
    run_pipeline()

    # 如果是 --once 参数，跑完就退出（用于手动触发/测试）
    if "--once" in sys.argv:
        print("\n（--once 模式，执行一次后退出）")
        return

    # 每天 18:00 自动跑（期货收盘后，数据已更新）
    schedule.every().day.at("18:00").do(run_pipeline)
    print("\n定时任务已启动：每天 18:00 自动执行离线预测流水线")
    print("按 Ctrl+C 停止")

    # 常驻循环
    while True:
        schedule.run_pending()
        time.sleep(60)


if __name__ == "__main__":
    main()
