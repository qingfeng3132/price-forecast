# -*- coding: utf-8 -*-
"""
第三周 · 价格监控模块
功能：
    1) 计算各品种月度变化率（复用 indicators 模块）
    2) 判断是否超过阈值（默认 10%，从 alert_threshold 表读取）
    3) 超阈值则写入 price_alert 表触发告警
    4) 防抖：利用 price_alert 唯一约束 (goods_id, alert_type, alert_date)
       同一商品同一告警方向同一天只记录一次，天然避免告警风暴
"""
import os
import datetime

import pymysql

from indicators import get_indicators

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

# 监控的品种：猪肉=4, 玉米=34, 鲜苹果=35
MONITOR_GOODS = [4, 34, 35]

# 默认阈值（%）：alert_threshold 表里没有配置时的兜底
DEFAULT_THRESHOLD = 10.0


def get_conn():
    return pymysql.connect(**DB_CONFIG)


def get_thresholds(conn, goods_id):
    """读取某商品的上涨/下跌阈值，未配置则用默认 10%"""
    with conn.cursor() as cur:
        cur.execute(
            "SELECT up_threshold, down_threshold FROM alert_threshold WHERE goods_id=%s",
            (goods_id,),
        )
        row = cur.fetchone()
    if row is None:
        return DEFAULT_THRESHOLD, DEFAULT_THRESHOLD
    return float(row[0]), float(row[1])


def check_and_alert(conn, goods_id):
    """
    检查某商品的月度变化率，超阈值则写告警
    返回 (触发数, 详情列表)
    """
    ind = get_indicators(goods_id)
    if ind is None or ind["monthly_chg"].empty:
        return 0, []

    # 取最近一个月的月度变化率
    latest_chg = float(ind["monthly_chg"].iloc[-1])
    latest_month = ind["monthly_chg"].index[-1].date()

    up_th, down_th = get_thresholds(conn, goods_id)

    triggered = []
    # 上涨告警
    if latest_chg > up_th:
        triggered.append(("上涨", latest_chg, up_th))
    # 下跌告警（变化率为负，超负阈值）
    elif latest_chg < -down_th:
        triggered.append(("下跌", latest_chg, down_th))

    # 写告警记录（唯一约束天然防抖，冲突则忽略）
    for alert_type, chg, th in triggered:
        sql = """
            INSERT IGNORE INTO price_alert
                (goods_id, alert_type, change_rate, threshold, alert_status, notify_channel, notify_status, alert_date)
            VALUES (%s, %s, %s, %s, '未处理', '站内消息', '待发送', %s)
        """
        with conn.cursor() as cur:
            cur.execute(sql, (goods_id, alert_type, chg, th, latest_month))
        conn.commit()

    return len(triggered), triggered


def main():
    conn = get_conn()
    try:
        print("=== 价格监控巡检 ===")
        for gid in MONITOR_GOODS:
            # 查商品名
            with conn.cursor() as cur:
                cur.execute("SELECT goods_name FROM goods WHERE id=%s", (gid,))
                name = cur.fetchone()[0]

            n, details = check_and_alert(conn, gid)
            if n > 0:
                for alert_type, chg, th in details:
                    print(f"  [告警] {name}(id={gid})：月度变化率 {chg:.2f}%，触发{alert_type}告警（阈值 {th}%）")
            else:
                # 打印当前变化率供参考
                ind = get_indicators(gid)
                chg = float(ind["monthly_chg"].iloc[-1]) if ind and not ind["monthly_chg"].empty else 0
                print(f"  [正常] {name}(id={gid})：月度变化率 {chg:.2f}%，未超阈值")
    finally:
        conn.close()
    print("\n监控完成！")


if __name__ == "__main__":
    main()
