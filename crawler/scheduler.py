# -*- coding: utf-8 -*-
"""
定时爬取任务：定时抓取最新价格数据并入库
使用 schedule 库实现定时，默认每小时爬一次
"""
import time
import schedule

from crawler import crawl_one, save_to_backend, crawl_history

# 最新的周报 ID（根据之前测试，61705 是最新，实际运行时需要更新）
LATEST_REPORT_ID = 61705


def job():
    """定时任务：抓取最新一周数据并入库"""
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 开始爬取...")
    try:
        date, clean = crawl_one(LATEST_REPORT_ID)
        if clean:
            count = save_to_backend(date, clean)
            print(f"  日期 {date} 入库 {count} 条")
        else:
            print("  未抓到数据")
    except Exception as e:
        print(f"  爬取失败: {e}")


def init_history():
    """
    首次运行：抓取历史数据（用于预测模型训练）
    从最新 ID 往前抓 10 个周报，积累时间序列
    """
    print("开始抓取历史数据（为预测模型积累时间序列）...")
    all_data = crawl_history(LATEST_REPORT_ID, 10)
    total = 0
    for item in all_data:
        total += save_to_backend(item["date"], item["rows"])
    print(f"历史数据抓取完成，共入库 {total} 条")


def main():
    # 先抓一次历史数据（可选，需要时打开注释）
    # init_history()

    # 每小时爬一次
    schedule.every(1).hours.do(job)
    print("定时任务已启动：每小时爬取一次")

    # 立即先跑一次
    job()

    # 死循环，持续运行
    while True:
        schedule.run_pending()
        time.sleep(60)


if __name__ == "__main__":
    main()
