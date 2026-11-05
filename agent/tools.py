# -*- coding: utf-8 -*-
"""
第四周 · Agent 工具封装模块
把价格查询、预测、告警查询、阈值配置封装成独立工具函数，
每个工具通过 HTTP 调用 Java 后端接口获取真实数据。

任务书约束：所有数据库读写必须封装为独立工具，Agent 按需调用，
禁止 LLM 直接输出业务数据。
"""
import datetime

import requests

import config


def _get(url, params=None):
    """GET 请求后端，返回 JSON"""
    resp = requests.get(config.BACKEND_BASE + url, params=params, timeout=15)
    resp.raise_for_status()
    return resp.json()


def _post(url, json_data):
    """POST 请求后端，返回 JSON"""
    resp = requests.post(config.BACKEND_BASE + url, json=json_data, timeout=15)
    resp.raise_for_status()
    return resp.json()


# ===== 工具 1：价格查询 =====
def query_price(goods_id, days=30):
    """
    查询某商品最近 N 天的价格
    返回结构化的价格列表（日期 + 价格 + 涨跌幅）
    """
    end = datetime.date.today()
    start = end - datetime.timedelta(days=days)
    data = _get("/api/price", params={
        "goodsId": goods_id,
        "startDate": start.isoformat(),
        "endDate": end.isoformat(),
    })
    return data


# ===== 工具 2：价格预测 =====
def query_forecast(goods_id):
    """
    查询某商品的未来 7 天预测（ARIMA 模型）
    返回预测列表（预测日期 + 预测价格 + 置信度等）
    """
    return _get("/api/forecast", params={"goodsId": goods_id})


# ===== 工具 3：告警查询 =====
def query_alerts(goods_id=None):
    """
    查询告警记录，goods_id 为 None 时查全部
    """
    params = {}
    if goods_id is not None:
        params["goodsId"] = goods_id
    return _get("/api/alert", params=params)


# ===== 工具 4：阈值查询 =====
def get_threshold(goods_id=None):
    """
    查询阈值配置，goods_id 为 None 时查全部
    """
    params = {}
    if goods_id is not None:
        params["goodsId"] = goods_id
    return _get("/api/alert/threshold", params=params)


# ===== 工具 5：阈值配置 =====
def set_threshold(goods_id, up_threshold, down_threshold):
    """
    设置某商品的上涨/下跌预警阈值
    """
    return _post("/api/alert/threshold", {
        "goodsId": goods_id,
        "upThreshold": up_threshold,
        "downThreshold": down_threshold,
    })


# 工具注册表：供 Agent 状态机调用
TOOLS = {
    "query_price": query_price,
    "query_forecast": query_forecast,
    "query_alerts": query_alerts,
    "get_threshold": get_threshold,
    "set_threshold": set_threshold,
}


if __name__ == "__main__":
    # 自测：查猪肉最近30天价格
    print("=== 查猪肉最近30天价格 ===")
    prices = query_price(4, days=30)
    print(f"返回 {len(prices)} 条")
    if prices:
        print("最近3条：")
        for p in prices[-3:]:
            print(f"  {p.get('priceDate')}  价格={p.get('price')}  涨跌={p.get('changeRate')}")

    print("\n=== 查猪肉预测 ===")
    forecast = query_forecast(4)
    print(f"返回 {len(forecast)} 条预测")
    if forecast:
        for f in forecast[:3]:
            print(f"  {f.get('forecastDate')}  预测={f.get('forecastPrice')}")

    print("\n=== 查告警 ===")
    alerts = query_alerts()
    print(f"返回 {len(alerts)} 条告警")
