# -*- coding: utf-8 -*-
"""
第四周 · DeepSeek 意图识别模块
功能：把用户自然语言转成结构化意图（商品名 + 时间范围 + 操作类型）
使用 DeepSeek 的 OpenAI 兼容接口（chat/completions + JSON 输出）

意图类型（intent_type）：
  price_query  价格查询（"查猪肉最近30天价格"）
  forecast     价格预测（"预测包菜未来7天走势"）
  alert_query  告警查询（"看看最近的价格告警"）
  threshold    阈值配置（"设置小麦阈值到15%"）
  chat         闲聊/其他（"你好"）
"""
import json

from openai import OpenAI

import config


# 商品名 -> goods_id 映射（与数据库 goods 表一致）
GOODS_ID_MAP = {
    "猪肉": 4,
    "生猪": 4,
    "玉米": 34,
    "小麦": 34,       # 小麦用玉米期货替代
    "鲜苹果": 35,
    "苹果": 35,
    "蔬菜": 35,       # 蔬菜用鲜苹果替代
}


# 意图识别的 system prompt：要求模型输出严格 JSON
SYSTEM_PROMPT = """你是商品价格预测系统的意图识别模块。请把用户的自然语言转成结构化意图，只输出一个 JSON 对象，不要输出其他内容。

JSON 字段说明：
- intent_type: 意图类型，只能是 price_query(价格查询) / forecast(价格预测) / alert_query(告警查询) / threshold(阈值配置) / chat(闲聊)
- goods_name: 用户提到的商品名（如 猪肉/玉米/鲜苹果/小麦/蔬菜），没提到则为 null
- time_range: 时间范围描述（如 "最近30天" "未来7天" "最近一周"），没提到则为 null
- days: 时间范围换算成天数（数字），无法确定则为 null

示例：
输入："查猪肉最近30天价格" -> {"intent_type":"price_query","goods_name":"猪肉","time_range":"最近30天","days":30}
输入："预测一下包菜未来7天走势" -> {"intent_type":"forecast","goods_name":"包菜","time_range":"未来7天","days":7}
输入："看看最近有没有价格告警" -> {"intent_type":"alert_query","goods_name":null,"time_range":null,"days":null}
输入："你好" -> {"intent_type":"chat","goods_name":null,"time_range":null,"days":null}
"""


def _get_client():
    """创建 DeepSeek 客户端"""
    return OpenAI(
        api_key=config.DEEPSEEK_API_KEY,
        base_url=config.DEEPSEEK_BASE_URL,
    )


def recognize_intent(user_text):
    """
    识别用户意图，返回 dict
    形如：{"intent_type": "price_query", "goods_name": "猪肉", "time_range": "最近30天", "days": 30}
    """
    client = _get_client()
    resp = client.chat.completions.create(
        model=config.DEEPSEEK_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_text},
        ],
        temperature=0,          # 温度 0，意图识别要稳定
        response_format={"type": "json_object"},
    )
    content = resp.choices[0].message.content.strip()
    # 解析 JSON（容错：去掉可能的 markdown 代码块包裹）
    content = content.strip("`").strip()
    if content.startswith("json"):
        content = content[4:].strip()
    intent = json.loads(content)
    return intent


def resolve_goods_id(goods_name):
    """
    把商品名转成 goods_id，返回 None 表示未匹配
    """
    if not goods_name:
        return None
    return GOODS_ID_MAP.get(goods_name.strip())


if __name__ == "__main__":
    # 自测
    tests = [
        "查猪肉最近30天价格",
        "预测一下鲜苹果未来7天的价格走势",
        "看看最近有没有价格告警",
        "你好啊",
    ]
    for t in tests:
        intent = recognize_intent(t)
        print(f"输入: {t}")
        print(f"  意图: {intent}")
        print()
