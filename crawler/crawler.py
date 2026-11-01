# -*- coding: utf-8 -*-
"""
爬取中国价格信息网的农产品价格数据
数据源：https://www.chinaprice.cn/slkjzsjcqkbg/61705.jhtml
流程：抓取 -> 解析 -> 清洗(去重/单位统一/类型转换) -> 入库
"""
import os
import re
import requests
import urllib3
from bs4 import BeautifulSoup

# ① 禁用系统代理（本机代理会干扰 SSL 握手，导致连接被中断）
#    反爬第二招：直连目标站，不走本地代理
os.environ["NO_PROXY"] = "*"
os.environ["no_proxy"] = "*"

# ② 禁用 SSL 警告（网站证书不被 requests 信任，跳过校验）
urllib3.disable_warnings()

# ② 伪装成浏览器（反爬第一招：加 User-Agent）
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
}

# ③ 周报详情页 URL 模板：末尾的 ID 是递增的，每个 ID 对应一周的数据
URL_TEMPLATE = "https://www.chinaprice.cn/slkjzsjcqkbg/{}.jhtml"

# ④ 品种名映射：数据源带括号的名字 -> goods 表的干净名字
NAME_MAP = {
    "洋葱(元葱)": "洋葱",
    "花菜(菜花)": "花菜",
}

# ⑤ 后端服务地址（入库接口）
BACKEND_BASE = "http://localhost:8080"


def fetch_html(url):
    """下载网页，返回 HTML 文本"""
    resp = requests.get(url, headers=HEADERS, timeout=15, verify=False)
    resp.encoding = "utf-8"
    return resp.text


def extract_date(html):
    """
    从 HTML 里提取价格日期
    表头形如 "20261014数值"，正则匹配 20 开头的 8 位日期，转成 "2026-10-14"
    """
    m = re.search(r"20\d{6}", html)
    if m:
        s = m.group()  # "20261014"
        return f"{s[0:4]}-{s[4:6]}-{s[6:8]}"
    return None


def parse_price(html):
    """解析 HTML 表格，返回原始价格数据列表"""
    soup = BeautifulSoup(html, "lxml")
    table = soup.find("table")
    if table is None:
        return []
    rows = []
    for tr in table.find_all("tr")[1:]:  # 跳过表头行
        cells = [td.get_text(strip=True) for td in tr.find_all("td")]
        if len(cells) >= 5:
            rows.append({
                "name": cells[0],     # 品种名称
                "unit": cells[2],     # 计量单位
                "region": cells[3],   # 地区
                "price": cells[4],    # 价格
            })
    return rows


def clean_data(raw_rows):
    """
    清洗数据：
    ① 统一品种名（去掉括号）
    ② 价格字符串转 float
    ③ 单位统一：元/500克 -> 元/公斤（价格 × 2）
    ④ 去重：同一品种 + 地区 只保留一条
    """
    result = []
    seen = set()  # 去重用的集合
    for row in raw_rows:
        # ① 统一品种名
        name = NAME_MAP.get(row["name"], row["name"])

        # ② 价格转 float，转失败(空值/非数字)就跳过这一行
        try:
            price = float(row["price"])
        except (ValueError, TypeError):
            continue

        # ③ 单位统一
        if row["unit"] == "元/500克":
            price = price * 2
            unit = "元/公斤"
        else:
            unit = row["unit"]

        # ④ 去重
        key = (name, row["region"])
        if key in seen:
            continue
        seen.add(key)

        result.append({
            "name": name,
            "unit": unit,
            "region": row["region"],
            "price": round(price, 2),
        })
    return result


def crawl_one(report_id):
    """抓取并清洗一个周报页，返回 (日期, 清洗后的数据列表)"""
    url = URL_TEMPLATE.format(report_id)
    html = fetch_html(url)
    date = extract_date(html)
    raw = parse_price(html)
    clean = clean_data(raw)
    return date, clean


def crawl_history(start_id, count):
    """
    遍历抓取历史数据：从 start_id 开始，向前抓 count 个周报
    每个周报是一个日期的价格快照，串起来就是时间序列
    """
    all_data = []
    for i in range(count):
        report_id = start_id - i
        try:
            date, clean = crawl_one(report_id)
            if clean:
                all_data.append({"date": date, "rows": clean})
                print(f"[{report_id}] {date} 抓到 {len(clean)} 条")
        except Exception as e:
            print(f"[{report_id}] 抓取失败: {e}")
    return all_data


def get_goods_id_map():
    """
    从后端拿到 商品名 -> goods_id 的映射
    调用 GET /api/goods 返回全部商品，建 {名称: id} 字典
    """
    resp = requests.get(f"{BACKEND_BASE}/api/goods", timeout=10)
    goods_list = resp.json()
    return {g["goodsName"]: g["id"] for g in goods_list}


def save_to_backend(date, clean_rows):
    """
    把清洗后的数据入库：
    ① 拿到 商品名->id 映射
    ② 把每条数据的 name 换成 goodsId
    ③ POST 到后端 /api/price/import
    """
    id_map = get_goods_id_map()
    payload = []
    for row in clean_rows:
        goods_id = id_map.get(row["name"])
        if goods_id is None:
            continue  # 商品不在库里，跳过
        payload.append({
            "goodsId": goods_id,
            "price": row["price"],
            "priceUnit": row["unit"],
            "region": row["region"],
            "priceDate": date,  # "2026-10-14"
        })
    if not payload:
        print("没有可入库的数据")
        return 0
    resp = requests.post(
        f"{BACKEND_BASE}/api/price/import",
        json=payload,
        headers={"Content-Type": "application/json"},
        timeout=30,
    )
    result = resp.json()
    print(f"入库请求返回: {result}")
    return result.get("count", 0)


def main():
    # 单页抓取：验证流程
    date, clean = crawl_one(61705)
    print(f"日期: {date}，清洗后 {len(clean)} 条")
    for item in clean[:5]:
        print(item)
    # 入库
    save_to_backend(date, clean)


if __name__ == "__main__":
    main()
