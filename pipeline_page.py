"""Bilingual workflow: platforms, dataset roles, learning paths and inference."""
import html
from pathlib import Path
import streamlit as st
from presentation import choose, heading, icon

heading('THE RESEARCH ROUTE',choose('从数据库到浏览器','From database to browser'),choose('左边看步骤，右边看选择理由。训练在 Notebook 里发生；网页使用保存好的模型。','Follow the steps, inspect the rationale. Training happens in notebooks; the website loads saved models.'),'route')
lang = choose('zh','en')
svg = (Path(__file__).resolve().parent/'assets'/f'workflow_{lang}.svg').read_text()
st.image(svg, width='stretch')
st.download_button(choose('下载项目原理图 SVG','Download workflow SVG'),svg,file_name=f'solubility_workflow_{lang}.svg',mime='image/svg+xml')
st.caption(choose('实线：训练与部署主流程；外部评价与在线结构检索分别接入，外部标签不参与模型训练或区间校准。','Solid arrows trace fitting and deployment. External evaluation and online structure lookup enter separately; external labels are excluded from fitting and interval calibration.'))

stages=[
('01','数据选择','Choose the data','Anaconda · JupyterLab · 01 / 03 notebooks',
 'ESOL 用于训练与留出评价；AqSolDB 用于外部评价；PubChem 用于结构检索与参考注释。',
 'ESOL supplies fitting and holdout data; AqSolDB supplies external evaluation; PubChem supplies structure lookup and reference annotations.',
 'ESOL（Estimated SOLubility，估算溶解度）规模适合先建立可复查的基准，标签是实验水溶解度。AqSolDB（Aqueous Solubility Database，水溶解度数据库）提供更广的汇编记录，帮助检查跨数据集表现。PubChem 很适合确认身份，但不是这两个模型的训练标签库。三个数据库，三份工作，别串岗。',
 'ESOL (Estimated SOLubility) provides a manageable benchmark with experimental aqueous-solubility labels. AqSolDB (Aqueous Solubility Database) provides broader compiled records for cross-dataset evaluation. PubChem resolves chemical identity and supports annotation auditing; it is not the training-label source for the two point models. Three databases, three distinct jobs.',
 [('ESOL data','https://deepchemdata.s3-us-west-1.amazonaws.com/datasets/delaney-processed.csv'),('AqSolDB paper','https://www.nature.com/articles/s41597-019-0151-1'),('PubChem','https://pubchem.ncbi.nlm.nih.gov/')]),
('02','结构清洗与重叠排查','Clean structures & audit overlap','Anaconda · RDKit · pandas · 01 / 03 notebooks',
 '规范化结构、检查组分、电荷与元素；外部记录进行精确结构、去立体化学与互变异构匹配。',
 'Canonicalise structures and check components, charges and elements. Audit external overlap using exact, stereochemistry-removed and canonical-tautomer matching.',
 '原始 ESOL 1128 条，去除 22 条规范化结构重复后为 1106。AqSolDB 按项目适用范围清洗，处理未完成的互变异构枚举，排除与 ESOL 重叠及内部重复互变异构组后，主要外部集为 6578 条。这样减少结构层面的重复影响；不能据此宣称原始实验来源全部独立。',
 'Removing 22 canonical-structure duplicates leaves 1,106 ESOL records from 1,128. AqSolDB is filtered to the project scope, unfinished tautomer enumeration is reviewed, and ESOL overlap plus internal duplicate-tautomer groups are excluded, leaving 6,578 primary external records. This reduces structural duplication; it does not establish independence of every original experimental source.',
 [('RDKit','https://www.rdkit.org/docs/GettingStartedInPython.html')]),
('03','固定划分与分子表示','Fix the split & encode molecules','Anaconda · scikit-learn · RDKit · 01 / 04 notebooks',
 '920 条训练、186 条留出。描述符交给树模型；原子与化学键交给图模型。',
 '920 training and 186 holdout records. Descriptors feed tree models; atoms and bonds feed graph models.',
 '按 Murcko 骨架分组，训练与留出间非空骨架交集为 0；无环分子按各自规范化结构分组。固定划分让模型比较更可追溯，但局部结构可能仍共享。RF 使用七个描述符；GINE 使用原子和键特征。不同表示把“结构”转成可学习的输入，而不是让模型只记住物质名字。',
 'Murcko-scaffold grouping gives zero overlap of nonempty scaffolds; acyclic molecules are grouped by canonical structure. A fixed split supports traceable comparison, although local motifs may still be shared. RF uses seven descriptors; GINE uses atom and bond features. Representations convert structure into learnable inputs instead of asking models to memorise names.',
 [('Murcko scaffolds','https://www.rdkit.org/docs/source/rdkit.Chem.Scaffolds.MurckoScaffold.html')]),
('04','并行建模：两个点估计，一个区间','Parallel learning: two estimates, one interval','Anaconda · scikit-learn · PyTorch Geometric · 01 / 03 / 04 notebooks',
 'RF 与 GINE 用固定训练记录拟合；CQR 在训练池内分出拟合与校准记录。',
 'RF and GINE fit the fixed training records. CQR divides the training pool into fitting and calibration records.',
 'RF（Random Forest，随机森林）提供描述符基线。GINE（Graph Isomorphism Network with Edge features，带边特征的图同构网络）探索原子—键表示：487/433 的内部划分选择 43 轮，再用 920 条重训；比较种子 42/43/44，网页用 42。CQR（Conformalized Quantile Regression，保形化分位数回归）使用 459 条拟合、461 条校准，给出不确定性区间；它是独立模型，不是 RF/GINE 两点的连线范围。',
 'Random Forest provides a descriptor baseline. Bond-aware GINE (Graph Isomorphism Network with Edge features) explores atom–bond representations: an inner 487/433 split selects 43 epochs, then fitting uses all 920 records. Seeds 42/43/44 are evaluated; the website uses 42. CQR (Conformalized Quantile Regression) uses 459 fitting and 461 calibration records to quantify uncertainty. Its separate interval model is not the range between RF and GINE estimates.',
 [('Random Forest','https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.RandomForestRegressor.html'),('GINEConv','https://pytorch-geometric.readthedocs.io/en/latest/generated/torch_geometric.nn.conv.GINEConv.html'),('CQR paper','https://arxiv.org/abs/1905.03222')]),
('05','评价、失败分析与来源核查','Evaluate, inspect failures & audit provenance','Anaconda · saved CSV tables · 01 / 03 / 04 notebooks',
 '检查留出与外部 MAE/RMSE、种子波动、区间覆盖率和大分子失败。',
 'Inspect holdout/external MAE and RMSE, seed variation, interval coverage and larger-molecule failures.',
 '部署 GINE 在留出集优于 RF，但外部 seed 42 误差更高；跨数据集结论比“谁赢了一次”更有信息。CQR 目标覆盖率 90%，实际 86.0% / 79.6%。超过训练最大 55 原子的 48 条外部记录暴露明显 GINE 误差。PubChem 参考注释保留原文、单位与条件，但不作为新增独立验证；外部数据不参与训练或校准。',
 'Deployed GINE outperforms RF on the holdout, but seed-42 external errors are higher. Cross-dataset findings are more informative than declaring a one-off winner. CQR targets 90% coverage; observed coverage is 86.0%/79.6%. Forty-eight external molecules above the training maximum of 55 atoms reveal substantial GINE errors. PubChem references retain text, units and conditions, but are not new independent validation. External data are excluded from training and calibration.',
 [('Research report','https://github.com/Chuanyanh/molecular-solubility-app/blob/main/RESEARCH_REPORT.md')]),
('06','保存模型与版本证据','Save models & version evidence','Anaconda → GitHub',
 '导出 RF、GINE、区间模型及结果表；把应用代码与模型保存在 GitHub。',
 'Export RF, GINE, interval models and result tables; store application code and models on GitHub.',
 'Notebook 负责训练，GitHub 保存可部署文件。RF/GINE 文件与导出版本已做哈希比较，预测核对表也已检查；这不等于所有新输入的预测都已验证。保存环境与训练配置，让面试中“这个结果怎么来的”有据可查。没有必要每点一次按钮就训练一次。',
 'Notebooks fit models; GitHub stores deployable files. RF/GINE files have been compared by hash, and prediction-parity tables checked; this does not validate every future input. Environment and training metadata make results traceable. There is no need to retrain whenever a visitor clicks a button.',
 [('Project repository','https://github.com/Chuanyanh/molecular-solubility-app')]),
('07','网页推理与解释','Serve predictions & explanations','GitHub → Streamlit Community Cloud',
 '查询名称或输入 SMILES → RDKit 检查 → 加载模型 → 换算单位 → 展示结构、估计、区间与导出。',
 'Resolve a name or accept SMILES → validate with RDKit → load saved models → convert units → display structures, estimates, intervals and exports.',
 'Streamlit 负责交互界面与推理调用；PubChem 在线请求只检索结构。mg/L 由 logS 和分子量换算；三维构象用于展示，不是当前模型使用的实验三维结构。温度/pH 记录不调整预测。中英界面共享同一套模型与数值，切换语言不会重新训练。',
 'Streamlit provides the interface and inference calls; PubChem online requests retrieve structure only. logS and molecular weight give mg/L. The generated 3D conformer is illustrative, not an experimental 3D input to these models. Recording temperature/pH does not adjust predictions. Both languages share the same models and numerical results; switching language does not retrain anything.',
 [('Live application','https://chuanyanh-solubility.streamlit.app/')]),
]
for n,zt,et,platform,zs,es,zw,ew,links in stages:
 st.markdown(f'<div class="workflow-stage"><div><div class="platform">{html.escape(platform)}</div><h3>{n} · {html.escape(choose(zt,et))}</h3></div><p>{html.escape(choose(zs,es))}</p></div>',unsafe_allow_html=True)
 with st.expander(choose('为什么这样做？展开选择理由','Why this choice? Explore the rationale')):
  st.write(choose(zw,ew))
  st.markdown(' · '.join(f'[{name}]({url})' for name,url in links))
 if n=='04':
  boxes=[('RF',choose('七个描述符 → 树模型基线','Seven descriptors → tree-model baseline')),('GINE',choose('原子与键 → 图表示学习','Atoms & bonds → graph representation learning')),('CQR',choose('分位数拟合＋校准 → 独立区间','Quantile fitting + calibration → separate intervals'))]
  st.markdown('<div class="method-grid">'+''.join(f'<div class="method-box"><strong>{a}</strong><p>{b}</p></div>' for a,b in boxes)+'</div>',unsafe_allow_html=True)
st.page_link('pages/1_研究结果.py',label=choose('查看对应研究证据','Inspect the supporting research evidence'),icon=':material/query_stats:')
