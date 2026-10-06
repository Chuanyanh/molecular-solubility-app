import json
import pandas as pd
import streamlit as st
from rdkit import Chem
from rdkit.Chem import Draw
from solubility_pipeline import predict_for_web

st.set_page_config(
    page_title="分子水溶解度预测",
    page_icon="🧪",
    layout="wide"
)

st.title("分子水溶解度预测")
st.caption(
    "比较随机森林 RF（Random Forest）与图神经网络 "
    "GNN（Graph Neural Network）的预测，查看预测区间和结构范围提示。"
)

with st.form("prediction_form"):
    smiles = st.text_input(
        "SMILES（Simplified Molecular Input Line Entry System，"
        "简化分子线性输入规范）",
        value="CC(=O)Oc1ccccc1C(=O)O"
    )
    submitted = st.form_submit_button("预测水溶解度")

if submitted:
    # 清除上次结果，避免错误输入后仍显示旧预测
    st.session_state.pop("prediction", None)
    try:
        with st.spinner("正在计算分子结构与预测……"):
            st.session_state["prediction"] = predict_for_web(smiles)
    except ValueError as error:
        st.error(str(error))
    except Exception as error:
        st.error(f"预测运行失败：{type(error).__name__}：{error}")

result = st.session_state.get("prediction")

if result is not None:
    st.caption("以下结果对应的规范化结构：")
    st.code(result["canonical_smiles"], language=None)

    structure_column, result_column = st.columns([1, 2])

    with structure_column:
        mol = Chem.MolFromSmiles(result["canonical_smiles"])
        st.image(Draw.MolToImage(mol, size=(450, 300)))

    with result_column:
        rf_column, gnn_column = st.columns(2)

        with rf_column:
            st.metric("RF 预测 logS", f"{result['rf']['logS']:.4f}")
            st.caption(f"{result['rf']['mg_L']:,.2f} mg/L")

        with gnn_column:
            st.metric("GNN 预测 logS", f"{result['gnn']['logS']:.4f}")
            st.caption(
                f"{result['gnn']['mg_L']:,.2f} mg/L；种子 42"
            )

        interval = result["cqr"]
        st.subheader("预测区间")
        st.write(
            f"[{interval['lower_logS']:.4f}, "
            f"{interval['upper_logS']:.4f}] logS"
        )
        st.write(
            f"对应浓度：[{interval['lower_mg_L']:,.2f}, "
            f"{interval['upper_mg_L']:,.2f}] mg/L"
        )
        st.caption(
            "CQR（Conformalized Quantile Regression，共形化分位数回归）"
            "区间来自单独的分位数模型。"
        )

    st.subheader("结构与适用范围")
    checks = result["checks"]
    st.write(
        f"原子数：{checks['atom_count']}；"
        f"最大训练集结构相似度："
        f"{checks['max_training_similarity']:.4f}"
    )
    st.write(
        "相同规范化结构出现在训练集中："
        + ("是" if checks["exact_structure_in_training"] else "否")
    )

    if checks["warnings"]:
        for warning in checks["warnings"]:
            st.warning(warning)
    else:
        st.info("未触发已有范围检查；这不代表预测一定可靠。")

    with st.expander("查看分子描述符"):
        st.dataframe(pd.DataFrame(
            result["descriptors"].items(),
            columns=["描述符", "数值"]
        ))

    with st.expander("查看训练集中最相似的分子"):
        neighbors = pd.DataFrame(result["training_neighbors"])
        neighbors = neighbors.rename(columns={
            "training_position": "训练表位置",
            "training_smiles": "分子结构",
            "tanimoto_similarity": "结构相似度"
        })
        st.dataframe(neighbors)

    with st.expander("查看区间的实际评价"):
        evaluation = pd.DataFrame(result["interval_evaluation"])
        st.dataframe(evaluation.round(4))
        st.caption(
            "目标覆盖率为 90%；实际覆盖率以表中评价结果为准。"
            "这些是数据集整体结果，不是当前分子的可靠概率。"
        )

    st.download_button(
        "下载本次预测 JSON",
        data=json.dumps(
            result, ensure_ascii=False, indent=2, allow_nan=False
        ),
        file_name="solubility_prediction.json",
        mime="application/json"
    )

st.caption(
    "logS = log10(S / (mol/L))。预测未指定温度和 pH。"
    "当前模型未专门判断完全互溶情形；输出为模型预测值。"
)

# PROJECT_METHODS_V1
st.divider()
with st.expander("项目方法与局限", expanded=False):
    st.markdown("""
**研究目标**  
根据分子结构预测水溶解度，并比较模型在训练数据之外的表现。

**模型方法**  
随机森林 RF（Random Forest）使用 7 个分子描述符；
图神经网络 GNN（Graph Neural Network）使用原子和化学键构成的分子图。
两个点预测模型均使用固定的 920 条 ESOL 训练记录。

**预测区间**  
CQR（Conformalized Quantile Regression，共形化分位数回归）
使用单独的分位数模型与校准集构建区间。
目标覆盖率为 90%，实际覆盖率请查看“区间的实际评价”。
这不是当前分子有 90% 概率落入区间的保证。

**适用范围与局限**  
预测未指定温度和 pH；当前模型不专门判断完全互溶。
结构相似度和描述符范围检查用于辅助判断适用范围。
输出为模型预测值，不能替代实验测量。
""")

# MODEL_EVALUATION_V1
with st.expander("模型评价与主要发现", expanded=False):
    st.caption("此前研究流程记录的结果；GNN 为当前网页使用的随机种子 42。")

    evaluation = pd.DataFrame([
        ["ESOL 留出集", 186, "RF", 0.5969, 0.8056],
        ["ESOL 留出集", 186, "GNN（种子 42）", 0.5471, 0.7205],
        ["AqSolDB 外部评价集", 6578, "RF", 0.8652, 1.1770],
        ["AqSolDB 外部评价集", 6578, "GNN（种子 42）", 0.8736, 1.2724],
    ], columns=["评价数据", "分子数", "模型", "MAE（logS）", "RMSE（logS）"])

    st.dataframe(evaluation, hide_index=True, use_container_width=True)
    st.markdown("""
**指标含义**  
MAE（Mean Absolute Error，平均绝对误差）衡量平均预测偏差；
RMSE（Root Mean Squared Error，均方根误差）对较大误差更敏感。
两者越小越好，单位均为 logS。

**主要发现**  
种子 42 的 GNN 在 ESOL 留出集上优于 RF，
但在 AqSolDB 外部评价集上的 MAE 和 RMSE 均高于 RF。
因此，不能仅凭留出集表现认定 GNN 在新数据上更好。

**评价边界**  
两个点预测模型使用相同的固定训练集。
外部评价集经过结构筛查与重叠排查；
结构排查不等于原始实验来源完全独立。
项目还比较了三个 GNN 随机种子，本表展示种子 42。
""")

# DATA_SOURCES_V1
with st.expander("数据来源与注释核查", expanded=False):
    st.markdown("""
**训练与留出评价数据**  
使用 Delaney 水溶解度数据集，通常称为 ESOL
（Estimated SOLubility，估算溶解度）数据集。
清理后共 1,106 条记录，按分子骨架分组划分为
920 条训练记录和 186 条留出记录。

**外部评价数据**  
使用 AqSolDB（Aqueous Solubility Database，水溶解度数据库）。
经过结构有效性、组分、电荷、结构重叠及重复记录筛查，
主要外部评价集包含 6,578 个分子。

**PubChem 注释核查试点**  
对随机抽取的 100 个分子进行结构匹配和溶解度注释查询。
98 个获得精确结构匹配，其中 26 个查到溶解度章节，
共展开 81 条注释。人工筛查后保留
10 个分子的 14 条水溶解度换算记录。

**如何理解核查结果**  
保留原文、来源、引用、温度和单位，便于追溯。
网页注释可能来自同一原始实验，也可能涉及不同条件或化学形式。
这项工作用于来源与数值核查，不能作为新增的独立验证集；
没有据此修改 AqSolDB 标签。
""")
