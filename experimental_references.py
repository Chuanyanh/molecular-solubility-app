"""Display traceable, curated water-solubility annotations by exact structure."""
from pathlib import Path
import json
import math

import pandas as pd
from rdkit import Chem
from presentation import ui as st

DATA_PATH = Path(__file__).resolve().parent / "data_library" / "experimental_references.csv"


def canonical_key(smiles):
    mol = Chem.MolFromSmiles(str(smiles))
    return Chem.MolToSmiles(mol, isomericSmiles=True) if mol is not None else None


def load_references(path=DATA_PATH):
    frame = pd.read_csv(path)
    frame["structure_key"] = frame["canonical_smiles"].map(canonical_key)
    frame = frame[frame["structure_key"].notna()].copy()
    for field in ["solubility_mg_L", "molecular_weight_g_mol", "converted_logS"]:
        frame[field] = pd.to_numeric(frame[field], errors="raise")
    for row in frame.itertuples():
        if not (math.isfinite(row.solubility_mg_L) and row.solubility_mg_L > 0
                and math.isfinite(row.molecular_weight_g_mol) and row.molecular_weight_g_mol > 0):
            raise ValueError("参考记录的浓度或分子量无效。")
        expected = math.log10(row.solubility_mg_L / 1000 / row.molecular_weight_g_mol)
        if not math.isclose(expected, row.converted_logS, abs_tol=1e-6):
            raise ValueError("参考记录的单位换算不一致。")
    return frame


def find_references(smiles, frame):
    key = canonical_key(smiles)
    if key is None:
        return frame.iloc[:0].copy()
    return frame.loc[frame["structure_key"] == key].copy()


def condition_text(value, suffix=""):
    return "未报告" if pd.isna(value) else f"{float(value):g}{suffix}"


def review_note(value):
    notes = {
        "form_and_pH_require_review": "物质形态与 pH 仍需核查",
        "source_and_stereochemistry_require_review": "来源与立体化学仍需核查",
    }
    return notes.get(value, str(value)) if pd.notna(value) else "暂无额外标记"


def render_experimental_references(result):
    st.subheader("实验参考值与模型预测对照")
    st.caption("公开水溶解度记录由 PubChem 注释转录。按包含立体化学的规范化结构匹配；不自动合并盐型或互变异构体。")
    try:
        frame = load_references()
    except (OSError, ValueError, KeyError) as error:
        st.info(f"参考数据暂时无法读取：{error}。模型预测仍可查看。")
        return
    records = find_references(result["canonical_smiles"], frame)
    if records.empty:
        st.info("当前整理的参考库中没有与本次结构完全匹配的记录。暂无参考值不表示该物质没有公开实验数据。")
        st.caption(f"当前参考库：{len(frame)} 条记录，{frame['structure_key'].nunique()} 个规范化结构。")
        return

    st.warning("这些记录尚未逐条核查原始实验，来源独立性也尚未确认，不能据此宣称模型通过独立验证。模型预测未指定温度和 pH；下方差值仅作数值对照。")
    display = pd.DataFrame({
        "记录": [f"R{i+1}" for i in range(len(records))],
        "公开参考 · mg/L": records["solubility_mg_L"].tolist(),
        "参考 logS": records["converted_logS"].tolist(),
        "温度": [condition_text(x, " °C") for x in records["temperature_C"]],
        "pH": [condition_text(x) for x in records["pH"]],
        "溶解度类型": ["未报告"] * len(records),
        "测量方法": ["未报告"] * len(records),
        "来源": records["source_names"].tolist(),
    })
    for key, label in [("rf", "RF"), ("gnn", "GNN")]:
        display[f"{label} 预测 · mg/L"] = result[key]["mg_L"]
        display[f"{label} − 参考 · logS"] = result[key]["logS"] - display["参考 logS"]
    st.dataframe(display, hide_index=True, width="stretch")
    st.caption("RF = Random Forest（随机森林）；GNN = Graph Neural Network（图神经网络）。logS 差值为正表示预测更高，为负表示预测更低。不同温度或来源的记录分别保留。")

    import plotly.graph_objects as go
    fig = go.Figure()
    labels = [f"R{i+1} · {condition_text(r.temperature_C, ' °C')}" for i, r in enumerate(records.itertuples())]
    fig.add_trace(go.Scatter(x=records["converted_logS"], y=labels, mode="markers",
                            name="公开参考", marker=dict(size=12, color="#f5c96a")))
    for key, label, color in [("rf", "RF 预测", "#67e4dc"), ("gnn", "GNN 预测", "#b29aff")]:
        fig.add_vline(x=result[key]["logS"], line_color=color, line_dash="dash")
        fig.add_trace(go.Scatter(x=[result[key]["logS"]], y=[labels[0]], mode="markers",
                                name=label, marker=dict(color=color, size=10)))
    fig.update_layout(xaxis_title="logS · mol/L 的以 10 为底对数", yaxis_title="参考记录",
                      height=max(260, 180+len(records)*35), margin=dict(l=10,r=10,t=25,b=40),
                      legend=dict(orientation="h"))
    st.plotly_chart(fig, width="stretch", key="experimental_reference_plot")

    for i, row in enumerate(records.itertuples()):
        with st.expander(f"R{i+1} · 来源、原文和核查状态"):
            st.write(f"物质：{row.name}；PubChem CID（化合物编号）：{row.CID}")
            st.write(f"原始注释：{row.annotation_text}")
            st.write(f"溶剂：水；温度：{condition_text(row.temperature_C, ' °C')}；pH：{condition_text(row.pH)}")
            st.write("溶解度类型与测量方法：本模块尚未从原始实验核查。盐型、晶型与立体化学需结合原始来源确认。")
            st.write(f"补充核查标记：{review_note(row.additional_review_note)}")
            st.write(f"数据获取时间（UTC）：{row.requested_at_utc}")
            st.markdown(f"[查看 PubChem 记录](https://pubchem.ncbi.nlm.nih.gov/compound/{int(row.CID)}#section=Solubility)")
            for j, url in enumerate(str(row.source_urls).split(" | ")):
                if url.startswith("https://") and not any(c in url for c in "\n\r ()"):
                    st.markdown(f"[查看来源页面 {j+1}]({url})")
            try:
                citations = json.loads(row.citation_json)
            except (ValueError, TypeError):
                citations = []
            if citations:
                st.write("注释列出的引用：")
                for citation in citations:
                    st.write(str(citation))
            else:
                st.write("注释未列出单独的原始实验引用。")
            st.caption(f"换算：logS = log10(mg/L ÷ 1000 ÷ 分子量)。本条换算使用的分子量为 {row.molecular_weight_g_mol:g} g/mol。")

    exported = records.drop(columns=["structure_key"]).copy()
    for key in ["rf", "gnn"]:
        exported[f"{key}_predicted_logS"] = result[key]["logS"]
        exported[f"{key}_predicted_mg_L"] = result[key]["mg_L"]
        exported[f"{key}_minus_reference_logS"] = result[key]["logS"] - exported["converted_logS"]
    st.download_button("下载参考记录与预测对照 CSV", exported.to_csv(index=False).encode("utf-8-sig"),
                       file_name="experimental_reference_comparison.csv", mime="text/csv",
                       key="download_experimental_references")
