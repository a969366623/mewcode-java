"""
数据清洗模块
对爬取的原始数据进行去重、缺失值处理、药性标签标准化
"""

import pandas as pd
import numpy as np
import ast
import os


# 药性分类映射：将寒热温凉平归为两大类
# 寒/凉 -> 0（寒性）
# 热/温 -> 1（热性）
# 平    -> 2（平性）
NATURE_MAP = {
    "寒": 0, "凉": 0,
    "热": 1, "温": 1,
    "平": 2,
}


def load_raw_data(path="data/raw_herbs.csv"):
    df = pd.read_csv(path, encoding="utf-8-sig")
    print(f"加载原始数据: {len(df)} 条记录")
    return df


def parse_smiles_list(df):
    """将smiles_list字段从字符串解析为Python列表"""
    def _parse(val):
        if isinstance(val, list):
            return val
        if pd.isna(val):
            return []
        try:
            result = ast.literal_eval(val)
            return result if isinstance(result, list) else [str(result)]
        except (ValueError, SyntaxError):
            return [str(val)]

    df["smiles_list"] = df["smiles_list"].apply(_parse)
    return df


def remove_duplicates(df):
    before = len(df)
    df = df.drop_duplicates(subset=["name"], keep="first")
    after = len(df)
    print(f"去重: {before} -> {after} 条记录")
    return df


def handle_missing(df):
    """处理缺失值"""
    before = len(df)
    df = df.dropna(subset=["nature"])
    df = df[df["nature"].isin(NATURE_MAP.keys())]
    df = df[df["smiles_list"].apply(len) > 0]
    after = len(df)
    print(f"移除无效记录: {before} -> {after} 条记录")
    return df


def encode_labels(df):
    """将药性文本标签编码为数字标签"""
    df["nature_label"] = df["nature"].map(NATURE_MAP)
    return df


def explode_compounds(df):
    """将每味药材的多个化学成分展开为独立行（一个成分一行）"""
    df = df.explode("smiles_list").reset_index(drop=True)
    df.rename(columns={"smiles_list": "smiles"}, inplace=True)
    df["smiles"] = df["smiles"].astype(str)
    df = df[df["smiles"].str.len() > 2]
    print(f"展开化学成分后: {len(df)} 条记录")
    return df


def clean_data(input_path="data/raw_herbs.csv", output_path="data/clean_herbs.csv"):
    print("=" * 50)
    print("开始数据清洗")
    print("=" * 50)

    df = load_raw_data(input_path)
    df = parse_smiles_list(df)
    df = remove_duplicates(df)
    df = handle_missing(df)
    df = encode_labels(df)
    df = explode_compounds(df)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False, encoding="utf-8-sig")
    print(f"清洗完成，保存至 {output_path}")

    print("\n药性分布:")
    print(df["nature"].value_counts())
    print("\n标签分布:")
    print(df["nature_label"].value_counts())
    return df


if __name__ == "__main__":
    clean_data()
