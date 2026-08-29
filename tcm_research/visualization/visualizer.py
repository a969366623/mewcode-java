"""
实验结果可视化模块
训练曲线、混淆矩阵、ROC曲线、特征分布等
"""

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import confusion_matrix, roc_curve, auc
from sklearn.preprocessing import label_binarize
import os

plt.rcParams["font.sans-serif"] = ["SimHei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

OUTPUT_DIR = "results/figures"


def ensure_dir():
    os.makedirs(OUTPUT_DIR, exist_ok=True)


def plot_training_curves(history, model_name="MLP"):
    """绘制训练损失和准确率曲线"""
    ensure_dir()
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    epochs = range(1, len(history["train_loss"]) + 1)

    axes[0].plot(epochs, history["train_loss"], "b-", linewidth=2, label="训练损失")
    axes[0].set_xlabel("Epoch")
    axes[0].set_ylabel("Loss")
    axes[0].set_title(f"{model_name} - 训练损失曲线")
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)

    axes[1].plot(epochs, history["train_acc"], "r-", linewidth=2, label="训练准确率")
    axes[1].set_xlabel("Epoch")
    axes[1].set_ylabel("Accuracy")
    axes[1].set_title(f"{model_name} - 训练准确率曲线")
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)

    plt.tight_layout()
    path = os.path.join(OUTPUT_DIR, "training_curves.png")
    plt.savefig(path, dpi=200, bbox_inches="tight")
    plt.close()
    print(f"训练曲线已保存: {path}")


def plot_confusion_matrix(results, model_name="MLP"):
    """绘制混淆矩阵"""
    ensure_dir()
    cm = confusion_matrix(results["y_true"], results["y_pred"])
    class_names = results["class_names"]

    fig, ax = plt.subplots(figsize=(8, 6))
    sns.heatmap(
        cm, annot=True, fmt="d", cmap="Blues",
        xticklabels=class_names, yticklabels=class_names,
        ax=ax, cbar=True,
    )
    ax.set_xlabel("预测标签", fontsize=12)
    ax.set_ylabel("真实标签", fontsize=12)
    ax.set_title(f"{model_name} - 混淆矩阵 (Acc={results['accuracy']:.4f})", fontsize=14)

    plt.tight_layout()
    path = os.path.join(OUTPUT_DIR, "confusion_matrix.png")
    plt.savefig(path, dpi=200, bbox_inches="tight")
    plt.close()
    print(f"混淆矩阵已保存: {path}")


def plot_roc_curves(results, model_name="MLP"):
    """绘制多分类ROC曲线（One-vs-Rest）"""
    ensure_dir()
    y_true = results["y_true"]
    y_prob = results["y_prob"]
    class_names = results["class_names"]
    n_classes = len(class_names)

    y_true_bin = label_binarize(y_true, classes=list(range(n_classes)))

    fig, ax = plt.subplots(figsize=(8, 6))
    colors = ["#e74c3c", "#2ecc71", "#3498db"]

    for i in range(n_classes):
        fpr, tpr, _ = roc_curve(y_true_bin[:, i], y_prob[:, i])
        roc_auc = auc(fpr, tpr)
        ax.plot(fpr, tpr, color=colors[i % len(colors)], linewidth=2,
                label=f"{class_names[i]} (AUC = {roc_auc:.4f})")

    ax.plot([0, 1], [0, 1], "k--", linewidth=1, label="随机分类器")
    ax.set_xlabel("假阳性率 (FPR)")
    ax.set_ylabel("真阳性率 (TPR)")
    ax.set_title(f"{model_name} - ROC曲线 (One-vs-Rest)")
    ax.legend(loc="lower right")
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    path = os.path.join(OUTPUT_DIR, "roc_curves.png")
    plt.savefig(path, dpi=200, bbox_inches="tight")
    plt.close()
    print(f"ROC曲线已保存: {path}")


def plot_model_comparison(mlp_results, cnn_results=None):
    """绘制不同模型的准确率对比柱状图"""
    ensure_dir()
    models = ["MLP"]
    accs = [mlp_results["accuracy"]]

    if cnn_results is not None:
        models.append("CNN")
        accs.append(cnn_results["accuracy"])

    fig, ax = plt.subplots(figsize=(6, 5))
    bars = ax.bar(models, accs, color=["#3498db", "#e74c3c"][:len(models)],
                  width=0.5, edgecolor="black", linewidth=0.5)

    for bar, acc in zip(bars, accs):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.01,
                f"{acc:.4f}", ha="center", va="bottom", fontsize=12, fontweight="bold")

    ax.set_ylabel("准确率", fontsize=12)
    ax.set_title("模型准确率对比", fontsize=14)
    ax.set_ylim(0, 1.1)
    ax.grid(True, alpha=0.3, axis="y")

    plt.tight_layout()
    path = os.path.join(OUTPUT_DIR, "model_comparison.png")
    plt.savefig(path, dpi=200, bbox_inches="tight")
    plt.close()
    print(f"模型对比图已保存: {path}")


def visualize_all(history, results, model_name="MLP"):
    """生成全部可视化图表"""
    print("=" * 50)
    print("开始生成可视化图表")
    print("=" * 50)
    plot_training_curves(history, model_name)
    plot_confusion_matrix(results, model_name)
    plot_roc_curves(results, model_name)
    print("所有图表生成完毕！")


if __name__ == "__main__":
    history = {"train_loss": np.random.rand(50), "train_acc": np.linspace(0.5, 0.9, 50)}
    results = {
        "y_true": np.random.randint(0, 3, 100),
        "y_pred": np.random.randint(0, 3, 100),
        "y_prob": np.random.rand(100, 3),
        "accuracy": 0.85,
        "class_names": ["寒凉", "热温", "平"],
    }
    visualize_all(history, results)
