import json
import pandas as pd
import streamlit as st
from rdkit import Chem
from rdkit.Chem import Draw
from solubility_pipeline import predict_for_web
from solubility_workflows import render_batch_prediction, render_manual_comparison

st.set_page_config(
    page_title="分子水溶解度预测",
    page_icon="🧪",
    layout="wide"
)


# VISUAL_DESIGN_V1
st.markdown("""
<style>
.stApp {
    background: radial-gradient(ellipse at top left, #152e46, #080f1d 65%);
    color: #e8eef7;
}
[data-testid="stHeader"] {background: transparent;}
[data-testid="stMainBlockContainer"] {
    max-width: 1450px;
    padding-top: 2.5rem;
}
h1, h2, h3 {color: #eff7ff !important;}
[data-testid="stCaptionContainer"] {color: #a8bbd0;}
[data-testid="stMetric"] {
    background: #132237;
    border: 1px solid #294058;
    border-radius: 18px;
    padding: 20px;
}
[data-testid="stMetricValue"] {color: #67e4dc;}
[data-testid="stBaseButton-primary"] {
    background: #55d6ce;
    color: #081827;
    border: none;
    border-radius: 12px;
    font-weight: 700;
}
[data-testid="stExpander"] {
    background: #101e30;
    border: 1px solid #294058;
    border-radius: 12px;
}
.lab-heading {
    color: #67e4dc;
    font-size: 12px;
    letter-spacing: 3px;
    margin-bottom: 12px;
}

[data-testid="stMetricLabel"],
[data-testid="stMetricLabel"] p {
    color: #dceaf7 !important;
}
[data-testid="stCaptionContainer"],
[data-testid="stCaptionContainer"] p {
    color: #b4c6d9 !important;
}
button[data-baseweb="tab"] {
    color: #b4c6d9 !important;
}
button[data-baseweb="tab"][aria-selected="true"] {
    color: #67e4dc !important;
}


[data-testid="stMetricValue"] {
    font-size: clamp(20px, 2.2vw, 34px) !important;
}


/* DOWNLOAD_BUTTON_STYLE_V1 */
.stApp [data-testid="stDownloadButton"] button {
    background-color: #55d6ce !important;
    color: #081827 !important;
    border: 1px solid #55d6ce !important;
    border-radius: 12px !important;
    font-weight: 700 !important;
}
.stApp [data-testid="stDownloadButton"] button p,
.stApp [data-testid="stDownloadButton"] button span {
    color: #081827 !important;
}
.stApp [data-testid="stDownloadButton"] button:hover {
    background-color: #7be7df !important;
    border-color: #7be7df !important;
}


/* SEARCH_LABEL_CONTRAST_V1 */
.stApp [data-testid="stWidgetLabel"],
.stApp [data-testid="stWidgetLabel"] p,
.stApp [data-testid="stRadio"] label p {
    color: #edf5ff !important;
}
.stApp [data-testid="stCaptionContainer"],
.stApp [data-testid="stCaptionContainer"] p {
    color: #c4d4e5 !important;
}
.stApp [data-testid="stTextInput"] input {
    color: #172337 !important;
    background-color: #eef3f9 !important;
    -webkit-text-fill-color: #172337 !important;
}
.stApp [data-testid="stTextInput"] input::placeholder {
    color: #586a80 !important;
    -webkit-text-fill-color: #586a80 !important;
}
.stApp [data-testid="stSelectbox"] [data-baseweb="select"] > div {
    background-color: #eef3f9 !important;
    color: #172337 !important;
}
.stApp [data-testid="stSelectbox"] [data-baseweb="select"] span,
.stApp [data-testid="stSelectbox"] [data-baseweb="select"] input {
    color: #172337 !important;
    -webkit-text-fill-color: #172337 !important;
}


/* ONLINE_BUTTON_CONTRAST_V1 */
.stApp [data-testid="stBaseButton-primary"] {
    background: #55d6ce !important;
    color: #081827 !important;
    border: none !important;
}
.stApp [data-testid="stBaseButton-primary"] p,
.stApp [data-testid="stBaseButton-primary"] span {
    color: #081827 !important;
}
.stApp [data-testid="stBaseButton-primary"]:disabled {
    opacity: 0.55 !important;
}
/* 左侧导航栏背景 */
[data-testid="stSidebar"] {
    background-color: #101e30 !important;
    border-right: 1px solid #294058;
}

/* 左侧导航栏文字 */
[data-testid="stSidebar"] * {
    color: #edf5ff !important;
}

/* 当前页面的选中背景 */
[data-testid="stSidebarNav"] a[aria-current="page"] {
    background-color: #20364d !important;
    border-radius: 8px;
}

/* WEB_FINISH_CONTRAST_V1 */
.stApp [data-testid="stExpander"] summary {
    background-color: #20364d !important;
    color: #edf5ff !important;
}
.stApp [data-testid="stExpander"] summary p,
.stApp [data-testid="stExpander"] summary span,
.stApp [data-testid="stExpander"] summary svg {
    color: #edf5ff !important;
}
.stApp [data-testid="stFormSubmitButton"] button,
.stApp [data-testid="stBaseButton-secondaryFormSubmit"] {
    background-color: #55d6ce !important;
    border-color: #55d6ce !important;
    color: #081827 !important;
    font-weight: 700 !important;
}
.stApp [data-testid="stFormSubmitButton"] button p,
.stApp [data-testid="stFormSubmitButton"] button span {
    color: #081827 !important;
}
/* 提高提示框文字对比度 */
.stApp [data-testid="stAlert"] p,
.stApp [data-testid="stAlert"] li,
.stApp [data-testid="stAlertContent"] {
    color: #edf5ff !important;
}
</style>
<div class="lab-heading">MOLECULAR SOLUBILITY LAB</div>
""", unsafe_allow_html=True)

st.title("探索分子，了解水溶解度")
st.caption(
    "搜索一种物质，探索它的立体结构，比较两种机器学习模型的水溶解度估计。"
)


# WEB_FINISH_BATCH_V1
render_batch_prediction(predict_for_web)

# COMPOUND_SEARCH_V2
from compound_library import search_compounds, load_compounds
from pubchem_search import search_pubchem, PubChemSearchError
from rdkit.Chem import rdMolDescriptors

@st.cache_data(ttl=86400, max_entries=256, show_spinner=False)
def cached_pubchem_search(query):
    import time

    query = query.strip()
    last_error = None

    for attempt in range(3):
        try:
            records = search_pubchem(query)
        except PubChemSearchError as error:
            last_error = error
        else:
            if records:
                return records

            last_error = PubChemSearchError(
                "PubChem 本次未返回可用的分子结构。"
                "这不一定表示数据库没有该物质。"
                "请核对名称、改用 CID，或再次点击在线查询。"
                "本次空结果不会缓存。"
            )

        if attempt < 2:
            time.sleep(attempt + 1)

    raise last_error

def clear_previous_prediction():
    st.session_state.pop("prediction", None)

mode = st.radio("查询方式", ["按物质名称搜索", "输入分子结构"],
                horizontal=True, on_change=clear_previous_prediction)
smiles = ""
submitted = False

if mode == "按物质名称搜索":
    query = st.text_input("输入中文、英文名称、别名或 PubChem CID",
                          placeholder="例如：愈创木酚、酒精、guaiacol、2244",
                          on_change=clear_previous_prediction)
    st.caption("内置 6578 条 AqSolDB 名称—结构记录和 40 种常用物质。常用物质支持中文及别名，其余记录主要支持英文。")
    local_matches = search_compounds(query)
    online_query = query.strip()
    # Use an exact curated alias only; do not translate partial or ambiguous names.
    exact = [item for item in load_compounds() if item.get("name_zh") and
             any(query.strip().casefold() == name.casefold() for name in
                 [item["name_zh"], item["name_en"], *item["aliases"]])]
    if len(exact) == 1:
        online_query = exact[0]["name_en"]
    st.caption("在线查询支持英文名称或 CID；已收录的中文别名会转换为英文查询。其他中文名称可能查不到，可尝试英文名称。")
    if st.button("到 PubChem 在线查询", type="primary", disabled=not query.strip()):
        clear_previous_prediction()
        st.session_state.pop("pubchem_lookup", None)
        try:
            with st.spinner("正在查询 PubChem……"):
                online = cached_pubchem_search(online_query)
            st.session_state["pubchem_lookup"] = {"query": query.strip(), "matches": online}
        except PubChemSearchError as error:
            st.error(str(error))
    lookup = st.session_state.get("pubchem_lookup", {})
    online_matches = lookup.get("matches", []) if lookup.get("query") == query.strip() else []
    if lookup.get("query") == query.strip() and not online_matches:
        st.info("PubChem 未找到匹配物质。请尝试准确的英文名称或 CID。")
    matches = online_matches + local_matches
    if matches:
        by_id = {item["id"]: item for item in matches}
        def compound_label(key):
            item = by_id[key]
            name = f"{item['name_zh']} · {item['name_en']}" if item["name_zh"] else item["name_en"]
            return f"{name} · {item.get('formula') or '分子式见下方'} · {item['id']}"
        selected_id = st.selectbox("选择物质", options=list(by_id), format_func=compound_label,
                                   on_change=clear_previous_prediction)
        selected = by_id[selected_id]
        smiles = selected["smiles"]
        mol = Chem.MolFromSmiles(smiles)
        st.caption(f"找到 {len(matches)} 条记录；同一物质可能在不同来源重复出现。请确认名称与结构。")
        if mol is None:
            st.error("所选记录的分子结构无法解析，请选择其他记录。")
        else:
            formula = rdMolDescriptors.CalcMolFormula(mol)
            st.caption(f"分子式：{formula} · 来源：{selected.get('source', '内置常用物质库')}")
            if selected.get("source_url"):
                st.markdown(f"[查看 PubChem 物质记录]({selected['source_url']})")
            with st.expander("预测前确认二维结构"):
                st.image(Draw.MolToImage(mol, size=(450, 280)), caption=compound_label(selected_id))
            st.caption("在线查询用于获取物质结构；下面的溶解度仍由模型估计。")
            submitted = st.button("预测水溶解度", type="primary")
    else:
        st.info("内置库没有匹配记录。可点击在线查询，或切换到输入分子结构。")
else:
    with st.form("prediction_form"):
        smiles = st.text_input("SMILES（Simplified Molecular Input Line Entry System，简化分子线性输入规范）",
                               value="CC(=O)Oc1ccccc1C(=O)O")
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
    with st.expander("查看本次预测使用的分子结构编码"):
        st.code(result["canonical_smiles"], language=None)

    structure_column, result_column = st.columns([1.35, 1])

    with structure_column:
        mol = Chem.MolFromSmiles(result["canonical_smiles"])


        import streamlit.components.v1 as components
        from molecule_viewer import molecule_html

        view_3d, view_2d, view_appearance = st.tabs(["三维分子", "二维结构", "物质外观"])

        with view_3d:
            try:
                components.html(
                    molecule_html(result["canonical_smiles"]),
                    height=525,
                    scrolling=False
                )
                st.caption(
                    "计算生成的一个三维构象。"
                    "颜色代表元素；球体大小用于展示。"
                )
            except ValueError as error:
                st.info(str(error))
                st.image(Draw.MolToImage(mol, size=(450, 300)))

        with view_2d:
            st.image(Draw.MolToImage(mol, size=(450, 300)))


        # SUBSTANCE_APPEARANCE_V1
        with view_appearance:
            from substance_appearance import get_appearance, appearance_html
            appearance = get_appearance(result["canonical_smiles"])
            if appearance is None:
                st.info("外观资料暂缺。这种物质仍可查看分子结构和预测结果。")
            else:
                components.html(appearance_html(appearance), height=490, scrolling=False)
                st.markdown(f"**资料描述：{appearance['description']}**")
                st.caption("适用情境：常温、常压下的纯物质。来源未给出这段外观描述的具体测定温度；此处不模拟温度变化。")
                st.markdown(f"[资料来源：{appearance['source']}]({appearance['url']})")
                st.caption("外观资料独立于溶解度模型，不随预测浓度变化。")

    with result_column:
        rf_column, gnn_column = st.columns(2)

        with rf_column:
            st.metric("随机森林估计 · mg/L", f"{result['rf']['mg_L']:,.2f}" if result["rf"]["mg_L"] < 100000 else f"{result['rf']['mg_L']:.3e}")
            st.caption(f"RF（Random Forest，随机森林） · logS {result['rf']['logS']:.4f}")

        with gnn_column:
            st.metric("图神经网络估计 · mg/L", f"{result['gnn']['mg_L']:,.2f}" if result["gnn"]["mg_L"] < 100000 else f"{result['gnn']['mg_L']:.3e}")
            st.caption(
                f"GNN（Graph Neural Network，图神经网络） · logS {result['gnn']['logS']:.4f}"
            )


        st.caption(
            "mg/L 表示每升溶液中物质的毫克数。"
            "这些数值是模型估计，尚未指定温度和 pH，不能直接视为实验结果。"
        )

        interval = result["cqr"]

        st.subheader("预测范围与模型比较")
        import plotly.graph_objects as go

        lower = interval["lower_mg_L"]
        upper = interval["upper_mg_L"]

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=[lower, upper], y=[0, 0],
            mode="lines+markers",
            line=dict(color="#f5c96a", width=8),
            marker=dict(size=9),
            name="独立区间模型",
            hovertemplate="%{x:,.2f} mg/L<extra>区间端点</extra>"
        ))

        for key, label, color, row in [
            ("rf", "随机森林", "#67e4dc", 0.3),
            ("gnn", "图神经网络", "#b29aff", -0.3)
        ]:
            fig.add_trace(go.Scatter(
                x=[result[key]["mg_L"]], y=[row],
                mode="markers",
                marker=dict(size=16, color=color),
                name=label,
                hovertemplate="%{x:,.2f} mg/L<extra>" + label + "</extra>"
            ))

        fig.update_layout(
            height=230,
            margin=dict(l=15, r=15, t=15, b=45),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#dceaf7"),
            xaxis=dict(
                type="log",
                title="预测浓度 mg/L · 对数刻度",
                gridcolor="#263b52",
                zeroline=False
            ),
            yaxis=dict(visible=False, range=[-0.8, 0.8]),
            legend=dict(
                orientation="h",
                y=1.25,
                x=0
            )
        )
        fig.update_traces(visible=True, opacity=1)
        fig.update_layout(
            font=dict(color="#edf5ff", size=15),
            legend=dict(
                font=dict(color="#edf5ff", size=15),
                bgcolor="#132237",
                bordercolor="#35516b",
                borderwidth=1,
                itemclick=False,
                itemdoubleclick=False
            ),
            xaxis=dict(
                tickfont=dict(color="#d5e4f5", size=13),
                title=dict(
                    text="预测浓度 mg/L · 对数刻度",
                    font=dict(color="#edf5ff", size=14)
                )
            )
        )
        st.plotly_chart(
            fig,
            width="stretch",
            theme=None,
            config={"displayModeBar": False}
        )
        st.write(
            f"区间模型给出的范围：**{lower:,.2f}–{upper:,.2f} mg/L**"
        )
        st.caption(
            "横轴每跨一个数量级，浓度增加 10 倍。"
            "范围越宽，估计越不精确。"
            "区间来自独立模型，不是两个预测值的上下限。"
        )
        st.caption(
            "目标覆盖率为 90%；已记录的留出集实际覆盖率为 86.0%，"
            "外部数据集为 79.6%。这些是数据集层面的评价，"
            "不代表当前物质有 90% 的概率落在区间内。"
        )

        with st.expander("了解 logS 与区间方法"):
            st.write(
                "logS 是以 mol/L（摩尔／升）表示的溶解度"
                "取以 10 为底的对数；数值越大，对应浓度越高。"
            )
            st.write(
                f"当前区间：[{interval['lower_logS']:.4f}, "
                f"{interval['upper_logS']:.4f}] logS"
            )
            st.write(
                "CQR（Conformalized Quantile Regression，"
                "保形化分位数回归）使用单独的分位数模型与校准集生成区间。"
            )

    # EXPERIMENTAL_REFERENCES_V1
    from experimental_references import render_experimental_references
    render_experimental_references(result)

    # WEB_FINISH_MANUAL_V1
    render_manual_comparison(result)

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

with st.expander("了解预测依据 · 研究方法、模型评价与数据来源"):
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
    CQR（Conformalized Quantile Regression，保形化分位数回归）
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

        st.dataframe(evaluation, hide_index=True, width="stretch")
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


# CREATOR_FOOTER_V1
st.markdown(
    """
    <div style="
        text-align:right;
        padding:24px 0 8px;
        margin-top:24px;
        border-top:1px solid #294058;
        color:#b4c6d9;
        font-size:13px;
    ">
        制作者：chuanyanh
    </div>
    """,
    unsafe_allow_html=True
)
