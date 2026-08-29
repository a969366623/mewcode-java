# 基于深度学习的中药寒热药性研究

## 项目结构

```
tcm_research/
├── main.py                      # 主程序入口
├── requirements.txt             # 依赖
├── crawler/
│   └── tcm_spider.py            # 中药数据爬虫（TCMSP）
├── data/
│   ├── data_cleaner.py          # 数据清洗
│   └── (数据文件)
├── features/
│   └── feature_extractor.py     # 分子特征提取（RDKit）
├── models/
│   └── tcm_classifier.py        # 深度学习模型（MLP/CNN, PyTorch）
├── visualization/
│   └── visualizer.py            # 实验结果可视化
├── checkpoints/                 # 模型权重
└── results/figures/             # 可视化图表
```

## 环境配置

```bash
pip install -r requirements.txt
```

## 运行

```bash
cd tcm_research
python main.py
```

## 流程说明

1. **数据爬取** - 从TCMSP数据库爬取药材信息，包含药名、药性、化学成分SMILES。网络不可用时自动生成示例数据。
2. **数据清洗** - 去重、缺失值处理、药性标签编码（寒凉=0, 热温=1, 平=2）、化学成分展开。
3. **特征提取** - 使用RDKit计算Morgan分子指纹（2048维）和7个分子描述符（分子量、LogP等）。
4. **模型训练** - 支持MLP和1D-CNN两种模型，训练50轮，输出准确率和分类报告。
5. **结果可视化** - 训练曲线、混淆矩阵、ROC曲线、模型对比图。
