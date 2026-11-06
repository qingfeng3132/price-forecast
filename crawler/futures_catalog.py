# -*- coding: utf-8 -*-
"""
第四周 · 期货品种目录（82 个主力连续品种的统一分类）
这是品种分类的"单一真相源"，供拉数/预测/监控脚本复用。

分类规则（按品种性质分 4 大类）：
  AGRICULTURE  农产品
  ENERGY_CHEM  能源化工
  METAL        金属
  FINANCE      金融

字段说明：每个品种 = (symbol, 中文名, 分类代码)
symbol 是新浪主力连续代码（末尾 0），中文名去掉"连续"后缀。
"""
import os
import sys

import akshare as ak  # noqa: E402

# 分类代码常量
AGRICULTURE = "AGRICULTURE"
ENERGY_CHEM = "ENERGY_CHEM"
METAL = "METAL"
FINANCE = "FINANCE"

# 分类代码 -> 分类中文名（写进 goods_category）
CATEGORY_NAMES = {
    AGRICULTURE: "农产品",
    ENERGY_CHEM: "能源化工",
    METAL: "金属",
    FINANCE: "金融",
}

# 期货品种 symbol -> 现有 goods_code 的映射（能对上现有商品的复用，避免重复建）
SYMBOL_TO_EXISTING_GOODS = {
    "LH0": "G001",  # 生猪 -> 猪肉
    "JD0": "G006",  # 鸡蛋 -> 鸡蛋
    "C0": "G031",   # 玉米 -> 玉米
    "AP0": "G032",  # 苹果 -> 鲜苹果
}

# 退市/无主力连续数据的品种（新浪拉不到数据，直接排除）
DELISTED_SYMBOLS = {
    "WH0",  # 强麦（已退市）
    "JR0",  # 粳稻（流动性极低）
    "RI0",  # 早籼稻（流动性极低）
    "LR0",  # 晚籼稻（流动性极低）
}

# 82 个品种的 symbol -> 分类代码 映射（手工归类，按品种性质）
SYMBOL_CATEGORY = {
    # ===== 农产品（大商所 dce）=====
    "P0": AGRICULTURE,    # 棕榈油
    "B0": AGRICULTURE,    # 豆二
    "M0": AGRICULTURE,    # 豆粕
    "JD0": AGRICULTURE,   # 鸡蛋
    "Y0": AGRICULTURE,    # 豆油
    "C0": AGRICULTURE,    # 玉米
    "A0": AGRICULTURE,    # 豆一
    "CS0": AGRICULTURE,   # 玉米淀粉
    "RR0": AGRICULTURE,   # 粳米
    "LH0": AGRICULTURE,   # 生猪
    "LG0": AGRICULTURE,   # 原木
    "FB0": AGRICULTURE,   # 纤维板
    # ===== 农产品（郑商所 czce）=====
    "OI0": AGRICULTURE,   # 菜油
    "RS0": AGRICULTURE,   # 菜籽
    "RM0": AGRICULTURE,   # 菜粕
    "WH0": AGRICULTURE,   # 强麦
    "JR0": AGRICULTURE,   # 粳稻
    "SR0": AGRICULTURE,   # 白糖
    "CF0": AGRICULTURE,   # 棉花
    "RI0": AGRICULTURE,   # 早籼稻
    "LR0": AGRICULTURE,   # 晚籼稻
    "CY0": AGRICULTURE,   # 棉纱
    "AP0": AGRICULTURE,   # 苹果
    "CJ0": AGRICULTURE,   # 红枣
    "PK0": AGRICULTURE,   # 花生
    # ===== 能源化工（大商所 dce）=====
    "V0": ENERGY_CHEM,    # PVC
    "L0": ENERGY_CHEM,    # 塑料
    "PP0": ENERGY_CHEM,   # 聚丙烯
    "J0": ENERGY_CHEM,    # 焦炭
    "JM0": ENERGY_CHEM,   # 焦煤
    "EG0": ENERGY_CHEM,   # 乙二醇
    "EB0": ENERGY_CHEM,   # 苯乙烯
    "PG0": ENERGY_CHEM,   # 液化石油气
    "BZ0": ENERGY_CHEM,   # 纯苯
    "I0": METAL,          # 铁矿石（归金属）
    # ===== 能源化工（郑商所 czce）=====
    "TA0": ENERGY_CHEM,   # PTA
    "MA0": ENERGY_CHEM,   # 甲醇
    "FG0": ENERGY_CHEM,   # 玻璃
    "UR0": ENERGY_CHEM,   # 尿素
    "SA0": ENERGY_CHEM,   # 纯碱
    "PF0": ENERGY_CHEM,   # 短纤
    "SH0": ENERGY_CHEM,   # 烧碱
    "PX0": ENERGY_CHEM,   # 对二甲苯
    "PR0": ENERGY_CHEM,   # 瓶片
    "PL0": ENERGY_CHEM,   # 丙烯
    "SF0": METAL,         # 硅铁（归金属）
    "SM0": METAL,         # 锰硅（归金属）
    # ===== 金属（上期所 shfe / 上海能源 ine）=====
    "AL0": METAL,         # 铝
    "ZN0": METAL,         # 沪锌
    "CU0": METAL,         # 铜
    "AU0": METAL,         # 黄金
    "RB0": METAL,         # 螺纹钢
    "PB0": METAL,         # 铅
    "AG0": METAL,         # 白银
    "HC0": METAL,         # 热轧卷板
    "SN0": METAL,         # 锡
    "NI0": METAL,         # 镍
    "SS0": METAL,         # 不锈钢
    "AO0": METAL,         # 氧化铝
    "AD0": METAL,         # 铸造铝合金
    "BC0": METAL,         # 国际铜
    "SC0": ENERGY_CHEM,   # 上海原油（归能源化工）
    "FU0": ENERGY_CHEM,   # 燃料油（归能源化工）
    "BU0": ENERGY_CHEM,   # 沥青（归能源化工）
    "LU0": ENERGY_CHEM,   # 低硫燃料油（归能源化工）
    "RU0": ENERGY_CHEM,   # 天然橡胶（归能源化工）
    "NR0": ENERGY_CHEM,   # 20号胶（归能源化工）
    "BR0": ENERGY_CHEM,   # 丁二烯橡胶（归能源化工）
    "SP0": ENERGY_CHEM,   # 纸浆（归能源化工）
    "OP0": ENERGY_CHEM,   # 胶版印刷纸（归能源化工）
    # ===== 金融（中金所 cffex）=====
    "IF0": FINANCE,       # 沪深300指数
    "TF0": FINANCE,       # 5年期国债
    "IH0": FINANCE,       # 上证50指数
    "IC0": FINANCE,       # 中证500指数
    "TS0": FINANCE,       # 2年期国债
    "IM0": FINANCE,       # 中证1000指数
    "EC0": FINANCE,       # 集运指数欧线（归金融，属于航运指数）
    # ===== 新能源金属（广期所 gfex）=====
    "SI0": METAL,         # 工业硅
    "LC0": METAL,         # 碳酸锂
    "PS0": METAL,         # 多晶硅
    "PT0": METAL,         # 铂
    "PD0": METAL,         # 钯
}


def get_catalog():
    """
    从 akshare 拉取全部主力连续品种，结合本地分类映射，
    返回完整目录：list of dict {symbol, name, category_code, category_name, exchange}
    """
    df = ak.futures_display_main_sina()
    catalog = []
    for _, row in df.iterrows():
        symbol = row["symbol"]
        # 跳过退市/无数据品种
        if symbol in DELISTED_SYMBOLS:
            continue
        name = row["name"].replace("连续", "")  # 去掉"连续"后缀
        category_code = SYMBOL_CATEGORY.get(symbol)
        # 未分类的品种跳过（理论上 82 个都应已归类）
        if category_code is None:
            continue
        catalog.append({
            "symbol": symbol,
            "name": name,
            "category_code": category_code,
            "category_name": CATEGORY_NAMES[category_code],
            "exchange": row["exchange"],
        })
    return catalog


if __name__ == "__main__":
    os.environ["NO_PROXY"] = "*"
    os.environ["no_proxy"] = "*"
    sys.stdout.reconfigure(encoding="utf-8")
    catalog = get_catalog()
    print(f"共 {len(catalog)} 个品种")
    from collections import Counter
    cnt = Counter(c["category_name"] for c in catalog)
    print("\n分类统计：")
    for cat, n in cnt.items():
        print(f"  {cat}: {n} 个")
