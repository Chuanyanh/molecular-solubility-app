"""Display verified saved GINE predictions without training."""
import json
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from presentation import ui as st


def render_gnn_research(data, plot_style, show_table):
    st.subheader('图神经网络与随机森林：同一 920 条训练记录')
    st.write('GNN = Graph Neural Network（图神经网络）；本实验使用带键特征的 GINE 卷积。先在 487 条拟合、433 条内部验证记录上选择 43 个训练轮次，再用全部 920 条训练记录重训；186 条留出记录用于评价。种子 42、43、44 使用固定方案，没有按外部结果选择最佳种子。')
    metrics = pd.read_csv(data/'gine_seed_stability_metrics.csv')
    summary = pd.read_csv(data/'gine_seed_stability_summary.csv')
    show_table(summary.rename(columns={'dataset':'评价数据集','seed_count':'种子数','MAE_mean':'平均 MAE','MAE_std':'MAE 样本标准差','RMSE_mean':'平均 RMSE','RMSE_std':'RMSE 样本标准差','R2_mean':'平均 R²','R2_std':'R² 样本标准差'}))
    rows=[]
    for filename,dataset,target,rfcol in [('esol_holdout_gine_three_seeds.csv','ESOL_holdout','measured_logS','RF_predicted_logS'),('aqsoldb_gine_three_seeds.csv','AqSolDB_primary','Solubility','RF_refit_predicted_logS')]:
        df=pd.read_csv(data/filename)
        e=df[rfcol]-df[target]
        rows.append({'dataset':dataset,'model':'RF · 固定种子 42','MAE':e.abs().mean(),'RMSE':np.sqrt((e**2).mean()),'R2':1-(e**2).sum()/((df[target]-df[target].mean())**2).sum(),'record_count':len(df)})
    rf=pd.DataFrame(rows)
    show_table(rf)
    fig=go.Figure()
    fig.add_bar(x=summary.dataset,y=summary.MAE_mean,error_y=dict(type='data',array=summary.MAE_std),name='GINE · 三个种子平均',marker_color='#67e4dc')
    fig.add_bar(x=rf.dataset,y=rf.MAE,name='RF · 固定种子 42',marker_color='#b29aff')
    fig.update_layout(barmode='group',yaxis_title='MAE · logS（越低越好）')
    fig = plot_style(fig)
    fig.update_layout(
        title=dict(text="GINE 与随机森林的误差比较"),
        font=dict(color="#edf5ff", size=16),
        legend=dict(
            font=dict(color="#edf5ff", size=16),
            bgcolor="#20364d",
            title=dict(text="")
          )
    )
    fig.update_xaxes(
        tickfont=dict(color="#edf5ff", size=15),
        title=dict(font=dict(color="#edf5ff", size=16))
    )
    fig.update_yaxes(
        tickfont=dict(color="#edf5ff", size=15),
        title=dict(font=dict(color="#edf5ff", size=16))
    )
    fig.update_traces(
        error_y=dict(color="#edf5ff"),
        selector=dict(type="bar")
    )
    st.plotly_chart(
        fig,
        width="stretch",
        theme=None,
        key="gnn_seed_comparison"
    )
    st.caption('MAE = Mean Absolute Error（平均绝对误差）；RMSE = Root Mean Squared Error（均方根误差）；R² 为决定系数。标准差描述三个训练种子的波动，不是置信区间，也不是三个独立测试集。RF 目前只报告一个种子。')
    st.write('GINE 留出平均 MAE 为 0.554，低于 RF 的 0.597；外部平均 MAE 为 0.855，与 RF 的 0.865 接近，但 GINE 平均 RMSE 为 1.252，高于 RF 的 1.177。当前证据不能说明图神经网络在所有指标上都更好。')
    with st.expander('查看三个种子的各次结果与训练设置'):
        show_table(metrics)
        manifest=json.loads((data/'esol_gine_run_manifest.json').read_text())
        st.json({k:manifest[k] for k in ['counts','model_config','training','max_training_graph_atoms','model_reload_checks']})
    st.subheader('外部失败分析：超过训练分子大小的 48 条记录')
    size=pd.read_csv(data/'gine_three_seeds_size_summary.csv')
    show_table(size)
    st.write('训练图最大为 55 个原子节点。超过此大小的 48 条外部记录，GINE 三种子平均 MAE 为 4.008，RF 为 1.229；其余 6530 条记录分别为 0.832 和 0.863。大分子组中 GINE 平均偏差为 −3.753，呈明显预测偏低。')
    st.caption('该分组是查看外部误差后的探索性诊断。大小可能与结构、元素、标签及实验条件共同变化，不能据此证明分子大小是唯一原因；训练范围内也不保证准确。')
    external=pd.read_csv(data/'aqsoldb_gine_three_seeds.csv')
    external['GINE_three_seed_mean_abs_error']=np.mean([np.abs(external[f'GINE_seed{s}']-external.Solubility) for s in [42,43,44]],axis=0)
    with st.expander('查看 GINE 三个种子平均绝对误差最大的 10 条记录'):
        cols=['ID','Name','canonical_smiles','Solubility','atom_count','size_status','GINE_seed42','GINE_seed43','GINE_seed44','GINE_three_seed_mean_abs_error','RF_refit_predicted_logS']
        show_table(external.nlargest(10,'GINE_three_seed_mean_abs_error')[cols])
    st.info('以上指标来自保存的逐分子预测。RF/GINE 模型文件已与 Anaconda 导出版本做哈希比较，预测核对表也已检查；原始实验来源独立性仍未确认。')
