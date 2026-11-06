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

import requests
from openai import OpenAI

import config


# 别名映射：任务书/口语里的词 -> 实际期货品种名（用于归一化）
# 这些词在数据库 goods 表里没有，但用户可能这么说
ALIAS_MAP = {
    "小麦": "玉米",      # 小麦无期货，用玉米替代
    "蔬菜": "鲜苹果",    # 蔬菜无期货，用鲜苹果替代
    "生猪": "猪肉",      # 生猪 = 猪肉（goods 表叫"猪肉"）
    "苹果": "鲜苹果",    # 苹果 = 鲜苹果（口语简称）
}

# 动态商品映射缓存：商品名 -> goods_id（首次使用时从后端加载）
_goods_map_cache = None


def load_goods_map():
    """
    从后端动态加载"期货农产品"分类下的商品 -> goods_id 映射
    （categoryId=5 是"期货农产品"，即有预测数据的 21 个品种）
    返回 dict：{商品名: goods_id}
    """
    global _goods_map_cache
    if _goods_map_cache is not None:
        return _goods_map_cache

    resp = requests.get(config.BACKEND_BASE + "/api/goods", timeout=15)
    resp.raise_for_status()
    goods_list = resp.json()

    goods_map = {}
    for g in goods_list:
        if g.get("categoryId") == 5:  # 只保留"期货农产品"分类
            goods_map[g["goodsName"]] = g["id"]

    # 加上别名映射（别名指向同一 id）
    for alias, target in ALIAS_MAP.items():
        if target in goods_map:
            goods_map[alias] = goods_map[target]

    _goods_map_cache = goods_map
    return goods_map


# 意图识别的 system prompt：要求模型输出严格 JSON
SYSTEM_PROMPT = """你是商品价格预测系统的意图识别模块。请把用户的自然语言转成结构化意图，只输出一个 JSON 对象，不要输出其他内容。

系统支持查询的商品有：{GOODS_LIST}

JSON 字段说明：
- intent_type: 意图类型，只能是 price_query(价格查询) / forecast(价格预测) / alert_query(告警查询) / threshold(阈值配置) / chat(闲聊)
- goods_name: 用户提到的商品名（尽量用上面支持列表里的标准名称），没提到则为 null
- time_range: 时间范围描述（如 "最近30天" "未来7天" "最近一周"），没提到则为 null
- days: 时间范围换算成天数（数字），无法确定则为 null

示例：
输入："查猪肉最近30天价格" -> {"intent_type":"price_query","goods_name":"猪肉","time_range":"最近30天","days":30}
输入："预测一下豆粕未来7天走势" -> {"intent_type":"forecast","goods_name":"豆粕","time_range":"未来7天","days":7}
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
    商品列表动态从后端加载，注入到 prompt 中，让模型知道可查哪些商品
    """
    # 动态拼商品列表，告诉模型可查的商品名
    goods_names = "、".join(load_goods_map().keys())
    dynamic_prompt = SYSTEM_PROMPT.replace("{GOODS_LIST}", goods_names)

    client = _get_client()
    resp = client.chat.completions.create(
        model=config.DEEPSEEK_MODEL,
        messages=[
            {"role": "system", "content": dynamic_prompt},
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
    用动态加载的商品映射（含别名）+ 模糊匹配兜底
    """
    if not goods_name:
        return None
    goods_map = load_goods_map()
    name = goods_name.strip()

    # 1. 精确匹配（含别名）
    if name in goods_map:
        return goods_map[name]

    # 2. 模糊匹配：商品名包含用户输入，或用户输入包含商品名
    for gname, gid in goods_map.items():
        if gname in name or name in gname:
            return gid

    return None


def list_goods_names():
    """返回所有可查的商品名列表（用于追问时提示用户）"""
    return list(load_goods_map().keys())


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
