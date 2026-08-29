"""
分子特征提取模块
使用RDKit提取分子指纹(Morgan Fingerprint)和分子描述符
"""

import pandas as pd
import numpy as np
from rdkit import Chem
from rdkit.Chem import AllChem, Descriptors
from tqdm import tqdm

FINGERPRINT_SIZE = 2048
DESCRIPTOR_NAMES = [
    "MolWt", "LogP", "NumHDonors", "NumHAcceptors",
    "NumRotatableBonds", "NumAromaticRings", "TPSA",
]


def smiles_to_mol(smiles):
    """SMILES字符串转RDKit Mol对象"""
    mol = Chem.MolFromSmiles(smiles)
    return mol


def compute_morgan_fingerprint(mol, radius=2, n_bits=FINGERPRINT_SIZE):
    """计算Morgan分子指纹（ECFP4）"""
    fp = AllChem.GetMorganFingerprintAsBitVect(mol, radius, nBits=n_bits)
    arr = np.zeros((n_bits,), dtype=np.float32)
    from rdkit.DataStructs import ConvertToNumpyArray
    ConvertToNumpyArray(fp, arr)
    return arr


def compute_descriptors(mol):
    """计算分子描述符"""
    desc_funcs = {
        "MolWt": Descriptors.MolWt,
        "LogP": Descriptors.MolLogP,
        "NumHDonors": Descriptors.NumHDonors,
        "NumHAcceptors": Descriptors.NumHAcceptors,
        "NumRotatableBonds": Descriptors.NumRotatableBonds,
        "NumAromaticRings": Descriptors.NumAromaticRings,
        "TPSA": Descriptors.TPSA,
    }
    return np.array([func(mol) for func in desc_funcs.values()], dtype=np.float32)


def extract_features(df, use_fingerprint=True, use_descriptors=True):
    print("=" * 50)
    print("开始分子特征提取")
    print("=" * 50)

    fps = []
    descs = []
    valid_indices = []

    for idx, row in tqdm(df.iterrows(), total=len(df), desc="提取特征"):
        mol = smiles_to_mol(row["smiles"])
        if mol is None:
            continue

        valid_indices.append(idx)

        if use_fingerprint:
            fp = compute_morgan_fingerprint(mol)
            fps.append(fp)

        if use_descriptors:
            desc = compute_descriptors(mol)
            descs.append(desc)

    valid_df = df.loc[valid_indices].reset_index(drop=True)

    features = []
    feature_names = []

    if use_fingerprint:
        fp_array = np.array(fps)
        features.append(fp_array)
        feature_names.extend([f"fp_{i}" for i in range(FINGERPRINT_SIZE)])

    if use_descriptors:
        desc_array = np.array(descs)
        features.append(desc_array)
        feature_names.extend(DESCRIPTOR_NAMES)

    feature_matrix = np.hstack(features) if features else np.array([])

    print(f"特征矩阵形状: {feature_matrix.shape}")
    print(f"有效样本数: {len(valid_df)} (原始: {len(df)})")

    return feature_matrix, valid_df["nature_label"].values, valid_df


def save_features(feature_matrix, labels, output_path="data/features.npz"):
    np.savez(output_path, X=feature_matrix, y=labels)
    print(f"特征已保存至 {output_path}")


if __name__ == "__main__":
    df = pd.read_csv("data/clean_herbs.csv", encoding="utf-8-sig")
    X, y, valid_df = extract_features(df)
    save_features(X, y)
