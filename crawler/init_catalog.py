# -*- coding: utf-8 -*-
"""
第四周 · 数据库目录初始化脚本
把 25 个农产品期货品种映射到 goods 表：
  - 能对上的复用现有 goods（生猪→猪肉G001、鸡蛋→鸡蛋G006、玉米→G031、苹果→G032）
  - 其余新建（goods_code 用期货 symbol，如 M0/P0/SR0）
并统一归入"期货农产品"分类。
"""
import os
import sys

os.environ["NO_PROXY"] = "*"
os.environ["no_proxy"] = "*"

import pymysql  # noqa: E402

from futures_catalog import get_catalog, AGRICULTURE, SYMBOL_TO_EXISTING_GOODS  # noqa: E402

DB_CONFIG = {
    "host": "localhost",
    "port": 3306,
    "user": "root",
    "password": "Price@2026",
    "database": "price_forecast",
    "charset": "utf8mb4",
}

# 新分类：期货农产品
FUTURES_CATEGORY = "期货农产品"
FUTURES_CATEGORY_CODE = "FUTURES"

SOURCE_PLATFORM = "东方财富-期货"
UPDATE_FREQ = "每日"


def get_conn():
    return pymysql.connect(**DB_CONFIG)


def ensure_category(conn):
    """确保"期货农产品"分类存在，返回其 id"""
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id FROM goods_category WHERE category_code=%s",
            (FUTURES_CATEGORY_CODE,),
        )
        row = cur.fetchone()
        if row:
            return row[0]
        cur.execute(
            "INSERT INTO goods_category(category_name, category_code, description) VALUES (%s, %s, %s)",
            (FUTURES_CATEGORY, FUTURES_CATEGORY_CODE, "农产品期货主力连续品种"),
        )
        conn.commit()
        return cur.lastrowid


def init_catalog():
    conn = get_conn()
    try:
        category_id = ensure_category(conn)
        print(f"分类「{FUTURES_CATEGORY}」id={category_id}")

        catalog = get_catalog()
        agri = [c for c in catalog if c["category_code"] == AGRICULTURE]
        print(f"农产品期货品种共 {len(agri)} 个\n")

        reused = 0
        created = 0
        result = []  # 记录 symbol -> goods_id 的最终映射

        with conn.cursor() as cur:
            for c in agri:
                symbol = c["symbol"]
                name = c["name"]

                existing_code = SYMBOL_TO_EXISTING_GOODS.get(symbol)
                if existing_code:
                    # 复用现有商品：把它的分类更新为"期货农产品"，来源标记为期货
                    cur.execute(
                        "SELECT id FROM goods WHERE goods_code=%s",
                        (existing_code,),
                    )
                    row = cur.fetchone()
                    if row:
                        goods_id = row[0]
                        cur.execute(
                            "UPDATE goods SET category_id=%s, source_platform=%s, update_frequency=%s WHERE id=%s",
                            (category_id, SOURCE_PLATFORM, UPDATE_FREQ, goods_id),
                        )
                        print(f"  [复用] {symbol} {name} -> {existing_code}(id={goods_id})")
                        result.append((symbol, goods_id))
                        reused += 1
                        continue

                # 新建商品：goods_code 用 symbol
                cur.execute(
                    "INSERT INTO goods(goods_code, goods_name, category_id, source_platform, update_frequency) "
                    "VALUES (%s, %s, %s, %s, %s)",
                    (symbol, name, category_id, SOURCE_PLATFORM, UPDATE_FREQ),
                )
                goods_id = cur.lastrowid
                print(f"  [新建] {symbol} {name} -> {symbol}(id={goods_id})")
                result.append((symbol, goods_id))
                created += 1

        conn.commit()
        print(f"\n完成：复用 {reused} 个，新建 {created} 个，共 {len(result)} 个品种")
        return result
    finally:
        conn.close()


if __name__ == "__main__":
    init_catalog()
