"""
主程序入口
完整流程：爬取数据 -> 数据清洗 -> 特征提取 -> 模型训练 -> 结果可视化
"""

from crawler.tcm_spider import crawl_tcmsp
from data.data_cleaner import clean_data
from features.feature_extractor import extract_features, save_features
from models.tcm_classifier import run_pipeline
from visualization.visualizer import visualize_all


def main():
    # Step 1: 爬取数据
    crawl_tcmsp(output_path="data/raw_herbs.csv")

    # Step 2: 数据清洗
    clean_data(input_path="data/raw_herbs.csv", output_path="data/clean_herbs.csv")

    # Step 3: 特征提取
    import pandas as pd
    df = pd.read_csv("data/clean_herbs.csv", encoding="utf-8-sig")
    X, y, valid_df = extract_features(df)
    save_features(X, y, output_path="data/features.npz")

    # Step 4: 模型训练与评估
    model, history, results = run_pipeline(feature_path="data/features.npz", model_type="mlp")

    # Step 5: 结果可视化
    visualize_all(history, results, model_name="MLP")


if __name__ == "__main__":
    main()
