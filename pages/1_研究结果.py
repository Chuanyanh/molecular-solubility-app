"""Research evidence page; displays saved experiments without retraining."""
from pathlib import Path
import io
import zipfile

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data_research"
st.set_page_config(page_title="研究结果 · 小分子水溶解度", page_icon="📊", layout="wide")
st.markdown("""<style>
.stApp {background: radial-gradient(ellipse at top left, #152e46, #080f1d 65%); color:#e8eef7;}
[data-testid="stHeader"] {background:transparent;}
h1,h2,h3 {color:#eff7ff !important;}
[data-testid="stCaptionContainer"] {color:#b5c8d9;}
[data-testid="stMetric"] {background:#132237;border:1px solid #294058;border-radius:16px;padding:18px;}
[data-testid="stMetricValue"] {color:#67e4dc;}
button[data-baseweb="tab"],
button[data-baseweb="tab"] p {
    color: #edf5ff !important;
    font-size: 17px !important;
    font-weight: 600 !important;
}
button[data-baseweb="tab"] {
    background-color: #132237 !important;
    border-radius: 8px 8px 0 0;
    padding: 12px 18px !important;
}
button[data-baseweb="tab"][aria-selected="true"],
button[data-baseweb="tab"][aria-selected="true"] p {
    color: #67e4dc !important;
    background-color: #20364d !important;
}
[data-testid="stCaptionContainer"],
[data-testid="stCaptionContainer"] p {
    color: #c4d4e5 !important;
}
/* 指标卡片上方的标题 */
[data-testid="stMetricLabel"],
[data-testid="stMetricLabel"] * {
    color: #edf5ff !important;
    font-weight: 600 !important;
}

/* 页面说明文字 */
[data-testid="stCaptionContainer"],
[data-testid="stCaptionContainer"] * {
    color: #c4d4e5 !important;
}
/* 左侧导航栏背景 */
[data-testid="stSidebar"] {
    background-color: #101e30 !important;
    border-right: 1px solid #294058;
}

/* 导航栏文字 */
[data-testid="stSidebar"] * {
    color: #edf5ff !important;
}

/* 当前选中的页面 */
[data-testid="stSidebarNav"] a[aria-current="page"] {
    background-color: #20364d !important;
    border-radius: 8px;
}
/* 下载按钮：绿色背景 */
[data-testid="stDownloadButton"] button {
    background-color: #67e4b0 !important;
    color: #08251c !important;
    border: 1px solid #67e4b0 !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
}

/* 下载按钮文字 */
[data-testid="stDownloadButton"] button * {
    color: #08251c !important;
}

/* 鼠标放上去时 */
[data-testid="stDownloadButton"] button:hover {
    background-color: #8af0c5 !important;
    border-color: #8af0c5 !important;
}
</style>""", unsafe_allow_html=True)
st.title("小分子水溶解度 · 研究结果")
st.write("研究问题：同一模型遇到训练时未见过的分子骨架，预测表现如何变化？")
st.caption("本页面展示上传文件中已保存的结果及由预测表重新计算的指标，不在网页中重新训练模型。")


def read_table(name):
    return pd.read_csv(DATA / name)


def show_table(table):
    st.dataframe(table, hide_index=True, width="stretch")


def plot_style(fig, title=None):
    fig.update_layout(title=title, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#101e30",
                      font=dict(color="#e8eef7"), margin=dict(l=20,r=20,t=50,b=45),
                      legend=dict(orientation="h", y=1.1))
    fig.update_xaxes(gridcolor="#294058")
    fig.update_yaxes(gridcolor="#294058")
    return fig


try:
    splits = read_table("split_comparison.csv")
    cv = read_table("grouped_cv_summary.csv")
    reps = read_table("representation_summary.csv")
    external = read_table("external_predictions.csv")
    holdout = read_table("cqr_current_env_holdout_intervals.csv")
    summary = read_table("cqr_current_env_evaluation_summary.csv")
except (OSError, ValueError) as error:
    st.error(f"研究结果文件无法读取：{error}。请检查 data_research 文件夹是否完整上传。")
    st.stop()

a,b,c = st.columns(3)
a.metric("ESOL 清洗后记录", "1,106")
b.metric("骨架划分 · 训练 / 留出", "920 / 186")
c.metric("外部区间评价记录", f"{len(external):,}")
st.caption("ESOL = Estimated SOLubility（估算溶解度数据集，标签为公开实验溶解度）。原始 1128 条，排除 22 条规范化结构重复记录后为 1106 条。AqSolDB 为汇编的水溶解度数据库。")

tabs = st.tabs(["随机与骨架划分", "模型与分子表示", "外部验证与预测区间", "失败案例", "方法与下载"])

with tabs[0]:
    st.subheader("相同描述符与模型设置，不同划分方式")
    st.write("随机划分按分子记录取约 20% 测试集；骨架划分按结构分组划分，训练与测试间非空 Murcko 骨架交集为 0。无环分子以各自规范化结构分别分组，因此骨架划分仍不保证所有局部结构或同系物完全不同。")
    shown = splits.drop(columns=["source", "source_cell_1_based"]).rename(columns={
        "split":"划分", "model":"模型", "train_count":"训练数", "test_count":"测试数"})
    shown["划分"] = shown["划分"].map({"random":"随机划分", "scaffold":"骨架划分"})
    show_table(shown)
    fig=go.Figure()
    for split,label,color in [("random","随机划分","#67e4dc"),("scaffold","骨架划分","#b29aff")]:
        part=splits[splits.split==split]
        fig.add_bar(x=part.model,y=part.MAE,name=label,marker_color=color)
    fig.update_layout(barmode="group",yaxis_title="MAE · logS（越低越好）")
    st.plotly_chart(plot_style(fig),width="stretch",key="split_plot")
    st.write("随机森林 MAE 从随机划分的 0.567 增至骨架划分的 0.597；岭回归从 0.771 增至 0.856。该结果来自一次固定划分，不足以证明所有新骨架上的性能下降幅度相同。")
    st.caption("来源：01_explore_ESOL-2.ipynb 第 22–31 个单元格的代码和已保存输出。当前随机／骨架留出比较未包含普通梯度提升模型；其训练集内部交叉验证结果在下一页签。")

with tabs[1]:
    st.subheader("训练集内部：四种模型使用同一五折骨架分组")
    st.caption("仅使用原 920 条训练记录。以下 MAE、RMSE、R² 为各折指标的算术平均；MAE 标准差为样本标准差，不是置信区间。")
    show_table(cv.drop(columns=["source","source_cell_1_based"]).rename(columns={
        "model":"模型","train_MAE_mean":"平均训练 MAE","val_MAE_mean":"平均验证 MAE",
        "val_MAE_std":"验证 MAE 标准差","val_RMSE_mean":"平均验证 RMSE","val_R2_mean":"平均验证 R²"}))
    fig=go.Figure(go.Bar(x=cv.model,y=cv.val_MAE_mean,error_y=dict(type="data",array=cv.val_MAE_std),marker_color="#67e4dc"))
    fig.update_layout(yaxis_title="五折平均 MAE ± 标准差 · logS")
    st.plotly_chart(plot_style(fig),width="stretch",key="cv_plot")
    st.write("随机森林与梯度提升的平均 MAE 为 0.591 和 0.594，表现接近；梯度提升的平均 RMSE 略低。当前结果不足以宣称随机森林在所有评价指标上都最好。")
    with st.expander("术语和各折结果"):
        st.write("Dummy：均值基线；Ridge Regression：岭回归；Random Forest（RF）：随机森林；Gradient Boosting：梯度提升。MAE = Mean Absolute Error（平均绝对误差）；RMSE = Root Mean Squared Error（均方根误差）；R² = Coefficient of Determination（决定系数）。")
        show_table(read_table("grouped_cv_folds.csv").drop(columns=["source","source_cell_1_based"]))
    st.subheader("三种分子表示 × 三种模型")
    st.write("Descriptors 为七个描述符；Morgan 为半径 2、512 位的 Morgan 分子指纹；Combined 为二者合并。以下使用同一五折划分，岭回归为固定 alpha=1。")
    show_table(reps.drop(columns=["source","source_cell_1_based"]))
    st.write("当前随机森林实验中，合并指纹后的平均 MAE 为 0.593，七描述符为 0.591，未观察到明显改善；不能据此推广为分子指纹无效。")
    st.caption("Notebook 还做了岭回归嵌套调参：指纹模型平均 MAE 从 2.270 降至 1.358，合并表示从 1.465 降至 0.971；七描述符从 0.786 变为 0.788。固定参数与调参结果应分别报告。")
    st.caption("七个描述符：分子量、LogP（辛醇／水分配系数的对数）、TPSA（Topological Polar Surface Area，拓扑极性表面积）、氢键供体数、氢键受体数、可旋转键数、环数。来源：Notebook 第 69–72 个单元格。")

with tabs[2]:
    st.subheader("外部预测表中的随机森林点预测")
    err=external.predicted_logS-external.measured_logS
    mae=float(err.abs().mean());rmse=float(np.sqrt((err**2).mean()))
    r2=float(1-(err**2).sum()/((external.measured_logS-external.measured_logS.mean())**2).sum())
    a,b,c=st.columns(3)
    a.metric("外部 MAE · logS",f"{mae:.3f}");b.metric("外部 RMSE · logS",f"{rmse:.3f}");c.metric("外部 R²",f"{r2:.3f}")
    st.info("这些指标由上传的 cqr_current_env_external_intervals.csv 中 predicted_logS 列重算。原始外部预测模型与当前网页 RF 模型的版本一致性尚未核对，因此不将其直接标为当前部署模型的外部性能。")
    fig=go.Figure(go.Scattergl(x=external.measured_logS,y=external.predicted_logS,mode="markers",text=external.ID,
        marker=dict(size=4,opacity=.35,color="#67e4dc"),hovertemplate="%{text}<br>参考 logS=%{x:.3f}<br>预测 logS=%{y:.3f}<extra></extra>"))
    lo=min(external.measured_logS.min(),external.predicted_logS.min());hi=max(external.measured_logS.max(),external.predicted_logS.max())
    fig.add_trace(go.Scatter(x=[lo,hi],y=[lo,hi],mode="lines",line=dict(color="#f5c96a",dash="dash"),name="预测 = 参考"))
    fig.update_layout(xaxis_title="AqSolDB 参考 logS",yaxis_title="文件中 RF 预测 logS",height=450,showlegend=False)
    st.plotly_chart(plot_style(fig),width="stretch",key="external_parity")
    st.subheader("CQR 预测区间：目标与实际覆盖率")
    st.write("CQR = Conformalized Quantile Regression（共形化分位数回归）。覆盖率为参考标签落在区间内的记录比例；区间宽度以 logS 计。")
    show_table(summary.rename(columns={"dataset":"数据集","molecule_count":"记录数","target_coverage":"目标覆盖率",
        "actual_coverage":"实际覆盖率","mean_width_logS":"平均宽度 · logS"}))
    fig=go.Figure()
    fig.add_bar(x=summary.dataset,y=summary.actual_coverage*100,name="实际覆盖率",marker_color="#67e4dc")
    fig.add_scatter(x=summary.dataset,y=summary.target_coverage*100,mode="lines+markers",name="目标覆盖率",line=dict(color="#f5c96a",dash="dash"))
    fig.update_layout(yaxis_title="覆盖率 · %",yaxis_range=[0,100])
    st.plotly_chart(plot_style(fig),width="stretch",key="coverage_plot")
    st.write("留出集实际覆盖率约 86.0%，外部约 79.6%，均低于 90% 目标；不应解释为每个输入分子有 90% 的保证。骨架划分和跨数据集变化也会影响区间校准的适用性。")
    st.caption("Notebook 的训练集内部五折校准覆盖率 92.4% 属于另一组实验；本页没有用它替代留出集或外部结果。GNN 完整外部评价表尚未上传，此页暂不报告其整体指标。结构去重也不等于已确认所有原始实验来源相互独立。")

with tabs[3]:
    st.subheader("留出测试集：高误差骨架")
    t=read_table("holdout_scaffold_errors.csv");t=t.rename(columns={t.columns[0]:"骨架 SMILES"})
    show_table(t)
    st.write("三嗪骨架 c1ncncn1 的 16 条留出记录，MAE 约 1.418 logS，并呈平均预测偏高。这说明整体误差较低仍可能掩盖局部结构类别的系统偏差。")
    st.subheader("训练集折外预测：吡啶骨架")
    t=read_table("oof_scaffold_errors.csv");t=t.rename(columns={t.columns[0]:"骨架 SMILES"})
    show_table(t)
    st.write("吡啶骨架 c1ccncc1 的 14 个分子中，13 个预测偏低，MAE 为 1.208、平均偏差为 −1.145 logS。改变背景划分后仍观察到偏低；加入 Morgan 指纹后该组 MAE 为 1.219。")
    st.caption("该骨架在查看误差后选出，属于探索性分析，尚不足以确定化学原因。所有七个描述符均落在背景单项范围内，也不能保证预测可靠。")
    st.subheader("外部预测表：绝对误差最大的 10 条记录")
    largest=external.assign(signed_error=err,absolute_error=err.abs()).nlargest(10,"absolute_error")
    show_table(largest[["ID","Name","canonical_smiles","measured_logS","predicted_logS","signed_error","absolute_error"]])
    st.caption("这些是数据库标签与模型预测的差异；异常可能涉及模型、标签、条件或物质形态，需要逐条核查，不能直接判定某条实验数据错误。")

with tabs[4]:
    st.subheader("结果溯源与复现")
    st.write("内部基准与分子表示比较直接摘自 01_explore_ESOL-2.ipynb 已保存的表格输出（约三位小数），本次没有重新训练。划分比较采用已执行单元格输出：骨架 RF MAE 0.597、RMSE 0.806；早期 markdown 中的 0.596／0.805 未用来覆盖运行输出。")
    st.write("五折指标的简单平均与将所有折外预测合并后计算的指标不同。当前五折 RF 平均 MAE 为 0.591，Notebook 合并折外 MAE 为 0.595，两者需要分别解释。")
    st.write("原 Notebook 环境：Python 3.9.12、scikit-learn 1.0.2、RDKit 2025.9.2；云端网页使用的环境不同，展示旧实验时保留其来源。02 notebook 为预测示例，示例分子不计入独立模型测试指标。")
    st.subheader("尚待补齐的研究证据")
    st.markdown("- 普通梯度提升的随机／骨架留出比较。\n- 当前部署 RF/GNN 与外部评价的模型版本核对。\n- GNN 完整外部指标及多个随机种子的结果。\n- 原始实验条件与来源独立性核查。\n- 最终研究报告、海报和英文演讲材料。")
    buffer=io.BytesIO()
    with zipfile.ZipFile(buffer,"w",zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(DATA.glob("*.csv")): archive.write(path,arcname="data_research/"+path.name)
    st.download_button("下载研究结果表 ZIP",buffer.getvalue(),file_name="solubility_research_results.zip",mime="application/zip")
    for name in ["01_explore_ESOL-2.ipynb","02_predict_ESOL.ipynb"]:
        path=ROOT/"notebooks"/name
        if path.exists():
            st.download_button(f"下载研究记录：{name}",path.read_bytes(),file_name=name,mime="application/x-ipynb+json",key=name)
    st.caption("表中 source 和 source_cell_1_based 字段保留原 notebook 名称及从 1 开始的单元格位置。")
