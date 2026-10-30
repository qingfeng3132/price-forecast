# -*- coding: utf-8 -*-
"""
爬取中国价格信息网的农产品价格数据
数据源：https://www.chinaprice.cn/slkjzsjcqkbg/61705.jhtml
"""
import requests
import urllib3
from bs4 import BeautifulSoup
from pandas.plotting import table

# ① 禁用 SSL 警告（网站证书不被 requests 信任，跳过校验）
urllib3.disable_warnings()

# ② 目标 URL
URL = "https://www.chinaprice.cn/slkjzsjcqkbg/61705.jhtml"

# ③ 伪装成浏览器（反爬第一招：加 User-Agent）
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
}

def fetch_html(url):
    resp = requests.get(url, headers=HEADERS,timeout=15,verify=False)
    resp.encoding = "utf-8"
    return resp.text

def parse_price(html):
    soup = BeautifulSoup(html, "lxml")
    table = soup.find("table")

    result = []
    for tr in table.find_all("tr")[1:]:
        cells = [td.get_text(strip=True) for td in tr.find_all("td")]
        if len(cells) >= 5:
            result.append({
                "品种": cells[0],
                "规格": cells[1],
                "单位": cells[2],
                "地区": cells[3],
                "价格": cells[4],

            })
    return result

def main():
    html = fetch_html(URL)
    data = parse_price(html)
    print(f"共解析到{len(data)}条价格数据")
    for item in data[:10]:
        print(item)

if __name__ == "__main__":
    main()



