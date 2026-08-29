"""
深度学习模型模块
基于PyTorch构建MLP/1D-CNN分类器，对中药寒热药性进行分类
"""

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, classification_report
import os

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
NUM_CLASSES = 3
BATCH_SIZE = 64
EPOCHS = 50
LEARNING_RATE = 1e-3


class TCMClassifier(nn.Module):
    """基于MLP的中药药性分类器"""

    def __init__(self, input_dim, num_classes=NUM_CLASSES, hidden_dims=None):
        super().__init__()
        if hidden_dims is None:
            hidden_dims = [512, 256, 128]

        layers = []
        prev_dim = input_dim
        for h in hidden_dims:
            layers.extend([
                nn.Linear(prev_dim, h),
                nn.BatchNorm1d(h),
                nn.ReLU(),
                nn.Dropout(0.3),
            ])
            prev_dim = h
        layers.append(nn.Linear(prev_dim, num_classes))
        self.network = nn.Sequential(*layers)

    def forward(self, x):
        return self.network(x)


class CNNClassifier(nn.Module):
    """基于1D-CNN的分类器，适用于分子指纹输入"""

    def __init__(self, input_dim, num_classes=NUM_CLASSES):
        super().__init__()
        self.conv1 = nn.Conv1d(1, 32, kernel_size=7, padding=3)
        self.conv2 = nn.Conv1d(32, 64, kernel_size=5, padding=2)
        self.conv3 = nn.Conv1d(64, 128, kernel_size=3, padding=1)
        self.pool = nn.MaxPool1d(2)
        self.relu = nn.ReLU()
        self.dropout = nn.Dropout(0.4)

        reduced_dim = input_dim // 8
        self.fc1 = nn.Linear(128 * reduced_dim, 256)
        self.fc2 = nn.Linear(256, num_classes)

    def forward(self, x):
        x = x.unsqueeze(1)
        x = self.pool(self.relu(self.conv1(x)))
        x = self.pool(self.relu(self.conv2(x)))
        x = self.pool(self.relu(self.conv3(x)))
        x = x.view(x.size(0), -1)
        x = self.dropout(self.relu(self.fc1(x)))
        return self.fc2(x)


def load_features(path="data/features.npz"):
    data = np.load(path)
    X, y = data["X"], data["y"]
    print(f"加载特征: X={X.shape}, y={y.shape}")
    return X, y


def prepare_data(X, y, test_size=0.2, random_state=42):
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, stratify=y, random_state=random_state
    )

    scaler = StandardScaler()
    X_train = scaler.fit_transform(X_train)
    X_test = scaler.transform(X_test)

    X_train_t = torch.FloatTensor(X_train).to(DEVICE)
    y_train_t = torch.LongTensor(y_train).to(DEVICE)
    X_test_t = torch.FloatTensor(X_test).to(DEVICE)
    y_test_t = torch.LongTensor(y_test).to(DEVICE)

    train_loader = DataLoader(TensorDataset(X_train_t, y_train_t),
                              batch_size=BATCH_SIZE, shuffle=True)
    test_loader = DataLoader(TensorDataset(X_test_t, y_test_t),
                             batch_size=BATCH_SIZE, shuffle=False)
    return train_loader, test_loader, X_test_t, y_test_t


def train_model(model, train_loader, epochs=EPOCHS, lr=LEARNING_RATE):
    model = model.to(DEVICE)
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=lr)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, mode="min", factor=0.5, patience=5)

    history = {"train_loss": [], "train_acc": []}

    for epoch in range(epochs):
        model.train()
        total_loss = 0.0
        correct = 0
        total = 0

        for X_batch, y_batch in train_loader:
            optimizer.zero_grad()
            outputs = model(X_batch)
            loss = criterion(outputs, y_batch)
            loss.backward()
            optimizer.step()

            total_loss += loss.item() * X_batch.size(0)
            preds = outputs.argmax(dim=1)
            correct += (preds == y_batch).sum().item()
            total += X_batch.size(0)

        epoch_loss = total_loss / total
        epoch_acc = correct / total
        history["train_loss"].append(epoch_loss)
        history["train_acc"].append(epoch_acc)
        scheduler.step(epoch_loss)

        if (epoch + 1) % 10 == 0:
            print(f"  Epoch {epoch+1}/{epochs} - Loss: {epoch_loss:.4f}, Acc: {epoch_acc:.4f}")

    return model, history


def evaluate_model(model, X_test, y_test, class_names=None):
    model.eval()
    with torch.no_grad():
        outputs = model(X_test)
        probs = torch.softmax(outputs, dim=1).cpu().numpy()
        preds = outputs.argmax(dim=1).cpu().numpy()
        y_true = y_test.cpu().numpy()

    acc = accuracy_score(y_true, preds)
    print(f"\n测试集准确率: {acc:.4f}")
    print("\n分类报告:")
    print(classification_report(
        y_true, preds,
        target_names=class_names or ["寒凉", "热温", "平"],
        zero_division=0))

    return {
        "accuracy": acc,
        "y_true": y_true,
        "y_pred": preds,
        "y_prob": probs,
        "class_names": class_names or ["寒凉", "热温", "平"],
    }


def run_pipeline(feature_path="data/features.npz", model_type="mlp"):
    print("=" * 50)
    print(f"开始模型训练 (模型类型: {model_type.upper()})")
    print("=" * 50)

    X, y = load_features(feature_path)
    input_dim = X.shape[1]
    train_loader, test_loader, X_test, y_test = prepare_data(X, y)

    if model_type == "cnn":
        model = CNNClassifier(input_dim)
    else:
        model = TCMClassifier(input_dim)

    total_params = sum(p.numel() for p in model.parameters())
    print(f"模型参数量: {total_params:,}")

    model, history = train_model(model, train_loader)
    results = evaluate_model(model, X_test, y_test)

    os.makedirs("checkpoints", exist_ok=True)
    torch.save(model.state_dict(), f"checkpoints/tcm_{model_type}.pth")
    print(f"\n模型已保存至 checkpoints/tcm_{model_type}.pth")
    return model, history, results


if __name__ == "__main__":
    run_pipeline(model_type="mlp")
