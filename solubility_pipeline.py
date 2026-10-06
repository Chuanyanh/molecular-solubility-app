
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from rdkit import Chem, DataStructs
from rdkit.Chem import Descriptors, Crippen, Lipinski
from rdkit.Chem import rdMolDescriptors, rdFingerprintGenerator

FEATURE_COLUMNS = [
    "MolWt", "LogP", "TPSA", "HDonors",
    "HAcceptors", "RotatableBonds", "RingCount"
]
ALLOWED_ELEMENTS = {
    "H", "B", "C", "N", "O", "F",
    "Si", "P", "S", "Cl", "Br", "I"
}

model_path = (
    Path(__file__).resolve().parent
    / "data_pipeline"
    / "esol_rf_920train_bundle.joblib"
)
prediction_bundle = joblib.load(model_path)

fingerprint_generator = rdFingerprintGenerator.GetMorganGenerator(
    radius=2, fpSize=512, includeChirality=False
)

training_smiles = prediction_bundle["training_smiles"]
training_mols = [
    Chem.MolFromSmiles(smiles) for smiles in training_smiles
]
assert all(molecule is not None for molecule in training_mols)

training_fingerprints = [
    fingerprint_generator.GetFingerprint(molecule)
    for molecule in training_mols
]
training_canonical_smiles = [
    Chem.MolToSmiles(
        molecule, canonical=True, isomericSmiles=True
    )
    for molecule in training_mols
]


def prepare_molecule(smiles):
    """检查输入结构，并计算与此前模型一致的描述符。"""
    if not isinstance(smiles, str) or not smiles.strip():
        raise ValueError("请输入非空的 SMILES 字符串")

    molecule = Chem.MolFromSmiles(smiles.strip())
    if molecule is None or molecule.GetNumAtoms() == 0:
        raise ValueError("无法解析该 SMILES，请检查拼写")

    if len(Chem.GetMolFrags(molecule)) != 1:
        raise ValueError("当前模型适用于单一组分，请勿输入盐或混合物")

    if any(atom.GetFormalCharge() != 0 for atom in molecule.GetAtoms()):
        raise ValueError("当前模型适用于无形式电荷的分子")

    elements = {atom.GetSymbol() for atom in molecule.GetAtoms()}
    if "C" not in elements:
        raise ValueError("当前模型适用于含碳分子")

    unsupported = elements - ALLOWED_ELEMENTS
    if unsupported:
        raise ValueError(
            "含有项目范围之外的元素：" + ", ".join(sorted(unsupported))
        )

    canonical_smiles = Chem.MolToSmiles(
        molecule, canonical=True, isomericSmiles=True
    )

    features = {
        "MolWt": Descriptors.MolWt(molecule),
        "LogP": Crippen.MolLogP(molecule),
        "TPSA": rdMolDescriptors.CalcTPSA(molecule),
        "HDonors": Lipinski.NumHDonors(molecule),
        "HAcceptors": Lipinski.NumHAcceptors(molecule),
        "RotatableBonds": Lipinski.NumRotatableBonds(molecule),
        "RingCount": Lipinski.RingCount(molecule),
    }

    return {
        "molecule": molecule,
        "canonical_smiles": canonical_smiles,
        "atom_count": molecule.GetNumAtoms(),
        "elements": sorted(elements),
        "features": pd.DataFrame([features], columns=FEATURE_COLUMNS),
    }

def predict_solubility(smiles):
    prepared = prepare_molecule(smiles)

    features = prepared["features"][
        prediction_bundle["feature_columns"]
    ]

    predicted_logS = float(
        prediction_bundle["model"].predict(features)[0]
    )

    molecular_weight = float(features.iloc[0]["MolWt"])
    predicted_mol_L = 10 ** predicted_logS
    predicted_mg_L = predicted_mol_L * molecular_weight * 1000

    outside_features = []

    for feature in prediction_bundle["feature_columns"]:
        value = float(features.iloc[0][feature])
        minimum = prediction_bundle["training_feature_min"][feature]
        maximum = prediction_bundle["training_feature_max"][feature]

        if value < minimum or value > maximum:
            outside_features.append(feature)

    # 氢通常以隐式形式表示，不将 H 单独作为未见元素提示
    input_elements = set(prepared["elements"]) - {"H"}
    unseen_elements = sorted(
        input_elements - set(prediction_bundle["training_elements"])
    )

    above_training_size = (
        prepared["atom_count"]
        > prediction_bundle["training_max_atom_count"]
    )

    warnings = []

    if outside_features:
        warnings.append(
            "描述符超出训练范围：" + ", ".join(outside_features)
        )

    if unseen_elements:
        warnings.append(
            "含训练中未出现的元素：" + ", ".join(unseen_elements)
        )

    if above_training_size:
        warnings.append(
            f"原子数 {prepared['atom_count']} 超过训练最大值 "
            f"{prediction_bundle['training_max_atom_count']}"
        )

    if any(
        atom.GetNumRadicalElectrons() > 0
        for atom in prepared["molecule"].GetAtoms()
    ):
        warnings.append("含自由基，适用性尚未验证")

    return {
        "canonical_smiles": prepared["canonical_smiles"],
        "predicted_logS": predicted_logS,
        "predicted_mol_L": predicted_mol_L,
        "predicted_mg_L": predicted_mg_L,
        "atom_count": prepared["atom_count"],
        "outside_features": outside_features,
        "unseen_elements": unseen_elements,
        "above_training_size": above_training_size,
        "warnings": warnings,
        "features": features,
        "molecule": prepared["molecule"],
    }

def find_training_neighbors(molecule, top_n=5):
    query_fingerprint = fingerprint_generator.GetFingerprint(molecule)

    similarities = np.asarray(
        DataStructs.BulkTanimotoSimilarity(
            query_fingerprint,
            training_fingerprints
        )
    )

    query_smiles = Chem.MolToSmiles(
        molecule, canonical=True, isomericSmiles=True
    )

    positions = np.argsort(
        -similarities, kind="stable"
    )[:top_n]

    neighbors = pd.DataFrame({
        "training_position": positions,
        "training_smiles": [
            training_canonical_smiles[position]
            for position in positions
        ],
        "tanimoto_similarity": similarities[positions],
    })

    return {
        "max_training_similarity": float(similarities.max()),
        "exact_structure_in_training": (
            query_smiles in training_canonical_smiles
        ),
        "neighbors": neighbors,
    }

def predict_with_checks(smiles):
    result = predict_solubility(smiles)
    similarity_result = find_training_neighbors(result["molecule"])
    result.update(similarity_result)
    return result


cqr_bundle = joblib.load(
    Path(__file__).resolve().parent
    / "data_pipeline"
    / "esol_cqr_current_env_bundle.joblib"
)

def predict_with_interval(smiles):
    # 保留已有的 RF 预测、结构检查和相似分子查询
    result = predict_with_checks(smiles)
    X = result["features"][cqr_bundle["feature_columns"]]

    q05 = float(cqr_bundle["models"][0.05].predict(X)[0])
    q95 = float(cqr_bundle["models"][0.95].predict(X)[0])

    lower = min(q05, q95) - cqr_bundle["correction"]
    upper = max(q05, q95) + cqr_bundle["correction"]

    mol_weight = float(X["MolWt"].iloc[0])

    result.update({
        "cqr_lower_logS": lower,
        "cqr_upper_logS": upper,
        "cqr_lower_mg_L": (10 ** lower) * mol_weight * 1000,
        "cqr_upper_mg_L": (10 ** upper) * mol_weight * 1000,
        "cqr_target_coverage": 1 - cqr_bundle["miscoverage"]
    })
    return result

# === GNN INFERENCE MODULE ===

import torch
from torch import nn
from torch_geometric.data import Data, Batch
from torch_geometric.nn import (
    GINEConv, global_mean_pool, global_add_pool
)

def one_hot(value, choices):
    return (
        [float(value == choice) for choice in choices]
        + [float(value not in choices)]
    )

def atom_features(atom):
    return (
        one_hot(
            atom.GetSymbol(),
            ["B", "C", "N", "O", "F", "Si", "P", "S", "Cl", "Br", "I"]
        )
        + one_hot(atom.GetDegree(), list(range(6)))
        + one_hot(atom.GetFormalCharge(), [-2, -1, 0, 1, 2])
        + one_hot(atom.GetTotalNumHs(), list(range(5)))
        + one_hot(
            str(atom.GetHybridization()),
            ["SP", "SP2", "SP3", "SP3D", "SP3D2"]
        )
        + [
            float(atom.GetIsAromatic()),
            float(atom.IsInRing()),
            atom.GetMass() / 100.0
        ]
    )

def bond_features(bond):
    return (
        one_hot(
            str(bond.GetBondType()),
            ["SINGLE", "DOUBLE", "TRIPLE", "AROMATIC"]
        )
        + [
            float(bond.GetIsConjugated()),
            float(bond.IsInRing())
        ]
    )

def smiles_to_graph(smiles, measured_logS=None):
    mol = Chem.MolFromSmiles(smiles)

    if mol is None or mol.GetNumAtoms() == 0:
        raise ValueError(f"无法解析分子：{smiles}")

    x = torch.tensor(
        [atom_features(atom) for atom in mol.GetAtoms()],
        dtype=torch.float32
    )

    connections = []
    edge_features = []

    for bond in mol.GetBonds():
        i = bond.GetBeginAtomIdx()
        j = bond.GetEndAtomIdx()
        features = bond_features(bond)

        connections.extend([[i, j], [j, i]])
        edge_features.extend([features, features])

    if connections:
        edge_index = torch.tensor(
            connections, dtype=torch.long
        ).t().contiguous()

        edge_attr = torch.tensor(
            edge_features, dtype=torch.float32
        )
    else:
        # 单原子分子也保留，连接关系为空
        edge_index = torch.empty((2, 0), dtype=torch.long)
        edge_attr = torch.empty((0, 7), dtype=torch.float32)

    graph = Data(x=x, edge_index=edge_index, edge_attr=edge_attr)

    if measured_logS is not None:
        graph.y = torch.tensor(
            [float(measured_logS)], dtype=torch.float32
        )

    graph.validate(raise_on_error=True)
    return graph

class SolubilityGINE(nn.Module):
    def __init__(self, node_dim=40, edge_dim=7,
                 hidden_dim=64, num_layers=3, dropout=0.1):
        super().__init__()

        self.node_encoder = nn.Linear(node_dim, hidden_dim)
        self.convs = nn.ModuleList()
        self.norms = nn.ModuleList()
        self.dropout = nn.Dropout(dropout)

        for _ in range(num_layers):
            mlp = nn.Sequential(
                nn.Linear(hidden_dim, hidden_dim),
                nn.ReLU(),
                nn.Linear(hidden_dim, hidden_dim)
            )
            self.convs.append(
                GINEConv(mlp, edge_dim=edge_dim, train_eps=True)
            )
            self.norms.append(nn.LayerNorm(hidden_dim))

        # 拼接原子表示的平均值与总和
        self.head = nn.Sequential(
            nn.Linear(hidden_dim * 2, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, 1)
        )

    def forward(self, batch):
        h = self.node_encoder(batch.x)

        for conv, norm in zip(self.convs, self.norms):
            update = conv(h, batch.edge_index, batch.edge_attr)
            h = self.dropout(torch.relu(norm(h + update)))

        molecule_features = torch.cat(
            [
                global_mean_pool(h, batch.batch),
                global_add_pool(h, batch.batch)
            ],
            dim=1
        )
        return self.head(molecule_features).view(-1)

torch.set_num_threads(2)

gnn_checkpoint = torch.load(
    Path(__file__).resolve().parent
    / "data_gnn"
    / "esol_gine_920train.pt",
    map_location="cpu",
    weights_only=True
)

assert gnn_checkpoint["training_count"] == 920
assert gnn_checkpoint["seed"] == 42

gnn_predictor = SolubilityGINE(
    **gnn_checkpoint["model_config"]
)
gnn_predictor.load_state_dict(
    gnn_checkpoint["model_state_dict"],
    strict=True
)
gnn_predictor.eval()

gnn_target_mean = float(gnn_checkpoint["target_mean"])
gnn_target_std = float(gnn_checkpoint["target_std"])
assert np.isfinite(gnn_target_mean)
assert np.isfinite(gnn_target_std) and gnn_target_std > 0

def predict_with_gnn(smiles):
    result = predict_with_interval(smiles)

    # 使用与训练时相同的图转换方式
    graph = smiles_to_graph(result["canonical_smiles"])
    assert graph.x.shape[1] == 40
    assert graph.edge_attr.shape[1] == 7

    batch = Batch.from_data_list([graph])

    with torch.inference_mode():
        standardized_prediction = float(
            gnn_predictor(batch).item()
        )

    logS = (
        standardized_prediction * gnn_target_std
        + gnn_target_mean
    )
    if not np.isfinite(logS):
        raise RuntimeError("GNN 预测出现非有限值。")

    mol_weight = float(result["features"]["MolWt"].iloc[0])

    result.update({
        "gnn_predicted_logS": logS,
        "gnn_predicted_mg_L": (10 ** logS) * mol_weight * 1000,
        "gnn_seed": 42,
        "gnn_minus_rf_logS": logS - result["predicted_logS"]
    })
    return result

# === WEB OUTPUT MODULE ===

import json

evaluation_path = (
    Path(__file__).resolve().parent
    / "data_pipeline"
    / "cqr_current_env_evaluation_summary.csv"
)
evaluation_table = pd.read_csv(evaluation_path)

INTERVAL_EVALUATION = json.loads(
    evaluation_table.to_json(orient="records", double_precision=15)
)

def predict_for_web(smiles):
    result = predict_with_gnn(smiles)

    payload = {
        "canonical_smiles": result["canonical_smiles"],
        "rf": {
            "logS": float(result["predicted_logS"]),
            "mg_L": float(result["predicted_mg_L"])
        },
        "gnn": {
            "logS": float(result["gnn_predicted_logS"]),
            "mg_L": float(result["gnn_predicted_mg_L"]),
            "seed": int(result["gnn_seed"])
        },
        "cqr": {
            "lower_logS": float(result["cqr_lower_logS"]),
            "upper_logS": float(result["cqr_upper_logS"]),
            "lower_mg_L": float(result["cqr_lower_mg_L"]),
            "upper_mg_L": float(result["cqr_upper_mg_L"]),
            "target_coverage": float(result["cqr_target_coverage"]),
            "method_note": "区间来自独立的分位数模型"
        },
        "checks": {
            "atom_count": int(result["atom_count"]),
            "above_training_size": bool(result["above_training_size"]),
            "unseen_elements": list(result["unseen_elements"]),
            "outside_features": list(result["outside_features"]),
            "max_training_similarity": float(
                result["max_training_similarity"]
            ),
            "exact_structure_in_training": bool(
                result["exact_structure_in_training"]
            ),
            "warnings": list(result["warnings"])
        },
        "descriptors": {
            key: float(value)
            for key, value in result["features"].iloc[0].items()
        },
        "training_neighbors": json.loads(
            result["neighbors"].to_json(orient="records")
        ),
        "prediction_note": (
            "预测未指定温度和 pH；"
            "未触发范围检查不代表预测一定可靠。"
        )
    }

    # 严格检查：不允许无法传输的对象、NaN 或无限值
    json.dumps(payload, ensure_ascii=False, allow_nan=False)
    payload["interval_evaluation"] = INTERVAL_EVALUATION
    return payload
