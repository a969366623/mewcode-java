"""
中药数据爬虫模块
从TCMSP等数据库爬取中药信息：药名、药性（寒/热/温/凉）、化学成分SMILES等
"""

import requests
import pandas as pd
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import time
import os
import re

BASE_URL = "https://tcmspwe.com"
HERB_LIST_URL = f"{BASE_URL}/herbs.php"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}

REQUEST_DELAY = 1.0
MAX_RETRIES = 3


def fetch_page(url, params=None):
    for attempt in range(MAX_RETRIES):
        try:
            resp = requests.get(url, headers=HEADERS, params=params, timeout=15)
            resp.raise_for_status()
            resp.encoding = resp.apparent_encoding or "utf-8"
            return resp.text
        except requests.RequestException as e:
            print(f"  请求失败(第{attempt+1}次): {e}")
            time.sleep(REQUEST_DELAY * (attempt + 1))
    return None


def parse_herb_list(html):
    """从药材列表页解析药材名称和链接"""
    soup = BeautifulSoup(html, "lxml")
    herbs = []
    rows = soup.select("table tbody tr")
    for row in rows:
        cols = row.find_all("td")
        if len(cols) < 2:
            continue
        link = cols[0].find("a")
        if not link:
            continue
        name = link.get_text(strip=True)
        href = link.get("href", "")
        herbs.append({"name": name, "detail_url": urljoin(BASE_URL, href)})
    return herbs


def parse_herb_detail(html, herb_name):
    """从药材详情页解析药性信息（寒/热/温/凉/平）"""
    soup = BeautifulSoup(html, "lxml")
    properties = {"name": herb_name, "nature": None, "smiles_list": []}

    text = soup.get_text()

    nature_patterns = [
        (r"药性[：:\s]*(寒|热|温|凉|平)", "nature"),
    ]
    for pattern, key in nature_patterns:
        m = re.search(pattern, text)
        if m:
            properties[key] = m.group(1)

    ingredient_rows = soup.select("table tbody tr")
    for row in ingredient_rows:
        cols = row.find_all("td")
        for col in cols:
            text_col = col.get_text(strip=True)
            if len(text_col) > 5:
                properties["smiles_list"].append(text_col)
    return properties


def crawl_tcmsp(output_path="data/raw_herbs.csv"):
    """主爬取流程"""
    print("=" * 50)
    print("开始爬取TCMSP中药数据")
    print("=" * 50)

    print("[1/3] 获取药材列表...")
    html = fetch_page(HERB_LIST_URL)
    if not html:
        print("无法获取药材列表页，使用本地示例数据。")
        return generate_sample_data(output_path)

    herbs = parse_herb_list(html)
    print(f"  共发现 {len(herbs)} 味药材")

    print("[2/3] 逐个获取药材详情...")
    results = []
    for i, herb in enumerate(herbs):
        print(f"  ({i+1}/{len(herbs)}) {herb['name']}")
        html = fetch_page(herb["detail_url"])
        if html:
            info = parse_herb_detail(html, herb["name"])
            results.append(info)
        time.sleep(REQUEST_DELAY)

    print("[3/3] 保存数据...")
    df = pd.DataFrame(results)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False, encoding="utf-8-sig")
    print(f"  已保存至 {output_path}，共 {len(df)} 条记录")
    return df


def generate_sample_data(output_path="data/raw_herbs.csv"):
    """生成示例数据，供离线开发使用"""
    import random

    natures = ["寒", "热", "温", "凉", "平"]
    herb_names = [
        "黄芩", "黄连", "黄柏", "大黄", "栀子", "石膏", "知母", "牡丹皮",
        "附子", "干姜", "肉桂", "吴茱萸", "花椒", "丁香", "小茴香",
        "麻黄", "桂枝", "紫苏", "荆芥", "防风", "羌活", "白芷", "细辛",
        "金银花", "连翘", "蒲公英", "板蓝根", "大青叶", "青黛", "贯众",
        "生地黄", "玄参", "麦冬", "天冬", "沙参", "石斛", "玉竹", "百合",
        "人参", "黄芪", "白术", "山药", "甘草", "大枣", "蜂蜜", "饴糖",
    ]

    sample_smiles = [
        "CC1=CC2=C(C=C1O)C(=O)C=C(O2)C3=CC=C(C=C3)O",
        "C1=CC=C2C(=C1)C=CC=C2O",
        "CC(C)CC1=CC=C(C=C1)C(=O)O",
        "C1=CC=C(C=C1)C2=CC(=O)C3=C(C=C(C=C3O2)O)O",
        "CC(=O)OC1=CC=CC=C1C(=O)O",
    ]

    random.seed(42)
    results = []
    for name in herb_names:
        nature = random.choice(natures)
        n_compounds = random.randint(3, 8)
        smiles_list = random.choices(sample_smiles, k=n_compounds)
        results.append({
            "name": name,
            "nature": nature,
            "smiles_list": smiles_list,
        })

    df = pd.DataFrame(results)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False, encoding="utf-8-sig")
    print(f"  已生成示例数据至 {output_path}，共 {len(df)} 条记录")
    return df


if __name__ == "__main__":
    crawl_tcmsp()
