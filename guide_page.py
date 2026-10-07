"""Beginner-friendly, bilingual guide tied to the existing application controls."""
import html
import streamlit as st
from presentation import choose, heading

heading('FIELD GUIDE · 5 MINUTES',choose('先认清分子，再读懂预测','Meet the molecule. Then read the prediction.'),choose('第一次使用也没关系。用阿司匹林走一遍，按钮在哪里、为什么点，都写在这里。','New here? Walk through aspirin: what to click, what you obtain, and why it matters.'),'book')
st.page_link('prediction_page.py',label=choose('打开分子预测页面','Open the molecule explorer'),icon=':material/science:')
steps = [
('输入一个名字','Start with a name',
 '在「查询方式」选择「按物质名称搜索」，输入 aspirin。也可以输入 PubChem CID：2244。支持的中文别名可以用，但英文名或 CID 通常更方便追溯。',
 'Choose “Search by compound name” under Search method. Enter aspirin, or its PubChem Compound ID (CID): 2244. Curated Chinese aliases work too; an English name or CID is usually easier to trace.',
 '为什么先用名称或 CID？','Why start with a name or CID?',
 '名称适合找分子，CID 适合准确指向一条记录。名字可能有别名或歧义；我们要把日常名字换成机器能理解的化学结构。就像查护照：先确认是谁，再讨论它的性格。',
 'Names are convenient; a CID identifies a particular PubChem record. Aliases can be ambiguous, so the goal is to resolve a human-readable name to a chemical structure. Think of it as checking the molecule’s passport before discussing its behaviour.',
 'https://pubchem.ncbi.nlm.nih.gov/compound/2244','PubChem · aspirin / 阿司匹林'),
('找不到？点在线查询','No local match? Search online',
 '先看内置匹配记录；没有合适结果时，点击「到 PubChem 在线查询」。等待返回后，在「选择物质」下拉框中选记录。网络失败时，可改用英文名、CID 或直接输入 SMILES。',
 'Inspect local matches first. If none is suitable, click “Search PubChem”. Wait for the response, then select a record in “Select a compound”. If the network fails, try an English name or CID, or enter SMILES directly.',
 '为什么本地与在线都有？','Why use both local and online lookup?',
 '本地库让常见查询不依赖网络；PubChem 扩大结构查找范围。在线检索得到的是结构身份，不是已经被实验证明的溶解度答案。搜索引擎负责带路，模型负责估计。',
 'Local records support routine lookup without a network request; PubChem broadens the structure search. Online lookup supplies chemical identity, not experimentally validated solubility. The search finds the molecule; the models estimate the property.',
 'https://pubchem.ncbi.nlm.nih.gov/','PubChem · structure lookup / 结构查询'),
('确认名称与二维结构','Confirm the name and 2D structure',
 '查看分子式与来源链接，展开「预测前确认二维结构」。确认选中的是目标物质，尤其注意盐型、组分和立体化学。拿不准时先查来源，不要急着预测。',
 'Check the formula and source link. Expand “Confirm the 2D structure before prediction”. Verify the target compound, especially salt form, components and stereochemistry. If uncertain, check the source before proceeding.',
 '为什么这一步不能省？','Why not skip structure confirmation?',
 '相近名字不一定代表同一个结构。当前模型接受含碳、单组分、无形式电荷的分子；盐或混合物可能被拒绝。三维外观漂亮，也不能替代身份核对。',
 'Similar names need not denote the same structure. The current model accepts carbon-containing, single-component molecules without formal charges; salts or mixtures may be rejected. An attractive 3D view is no substitute for identity checking.',
 'https://pubchem.ncbi.nlm.nih.gov/compound/2244#section=2D-Structure','Aspirin · 2D structure / 二维结构'),
('点击预测，比较两种模型','Predict and compare two models',
 '点击「预测水溶解度」。结果会展示随机森林与图神经网络的 mg/L 和 logS。切换「三维分子」「二维结构」查看结构；三维窗口可拖动旋转、滚轮缩放。',
 'Click “Predict solubility”. Results show Random Forest and the graph neural network in mg/L and logS. Switch between 3D molecule and 2D structure; drag to rotate and scroll to zoom in the 3D viewer.',
 '为什么要放两种模型？','Why show two models?',
 '随机森林读取七个分子描述符，GINE 读取原子和化学键构成的图。它们从不同表示中学习，比较有助于提出问题；一致不等于正确，不一致也不自动告诉我们谁错了。',
 'Random Forest learns from seven molecular descriptors; GINE learns from atom–bond graphs. Comparing representations can reveal useful questions. Agreement does not prove correctness, and disagreement does not identify the wrong model by itself.',
 'https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.RandomForestRegressor.html','Random Forest · official documentation / 官方文档'),
('读区间，也读适用范围','Read the interval and domain checks',
 '查看「预测范围与模型比较」及「结构与适用范围」。横轴是对数刻度；展开 logS 说明、相似分子、描述符与区间实际评价。不要只抄一个大数字。',
 'Inspect Prediction interval & model comparison, then Structure & applicability. The concentration axis is logarithmic. Open the logS explanation, nearest training molecules, descriptors and observed coverage. Resist the temptation to copy just one impressive number.',
 '为什么区间与警告值得看？','Why inspect intervals and warnings?',
 'CQR 区间由独立分位数模型和校准集生成，不是两个点预测的上下限。目标覆盖率 90%，实际留出与外部覆盖率为 86.0% / 79.6%。相似度高或无警告都不能保证可靠；温度和 pH 未作为模型输入。',
 'CQR uses a separate quantile model and calibration set; its interval is not the span between point estimates. Nominal coverage is 90%, but observed holdout/external coverage is 86.0%/79.6%. High similarity or no warning does not guarantee reliability. Temperature and pH are not model inputs.',
 'https://arxiv.org/abs/1905.03222','Conformalized Quantile Regression · original paper / 原始论文'),
('有实测值？记录条件再比较','Have a measurement? Record its conditions',
 '预测后展开「手动输入实验值」，选择单位，填数值。温度、pH 与来源不知道就留空，点击比较。文献参考区保留公开注释；不要把不同条件的结果强行当成同一次实验。',
 'After predicting, open Compare a measured value. Select units and enter the measurement. Leave temperature, pH or source blank if unknown, then compare. Literature references retain public annotations; values measured under different conditions are not interchangeable experiments.',
 '为什么要记录温度和来源？','Why record conditions and provenance?',
 '溶解度会受到测量条件与物质形态影响。记录条件帮助解释偏差，但不会重新训练模型或改变当前预测。一个实测值落在区间里，只说明这一次比较覆盖了它。',
 'Solubility depends on measurement conditions and chemical form. Recording provenance helps interpret discrepancies; it neither retrains the model nor adjusts the current prediction. One observation inside an interval establishes coverage only for that comparison.',
 'https://github.com/Chuanyanh/molecular-solubility-app/blob/main/RESEARCH_REPORT.md','Project report · limitations / 项目报告与局限'),
('导出结果，保留研究线索','Export and keep the research trail',
 '单分子结果点击「下载本次预测 JSON」。多个分子则展开批量 CSV：下载示例、填入 SMILES、上传、选择结构列、运行、下载结果。每批最多 200 行、5 MB；失败行也会保留。',
 'Download prediction JSON for one molecule. For multiple molecules, open Batch prediction: download the example, add SMILES, upload, select the structure column, run, then download results. The limit is 200 rows and 5 MB; failed rows are retained.',
 '为什么保留失败行与原始字段？','Why retain failed rows and input fields?',
 '这样可以知道哪一行输入导致失败，修正后重试，也能把预测与原始样品编号对应起来。研究记录不该在下载时偷偷“少几个分子”。',
 'Retaining errors makes problematic inputs visible and allows corrected retries. Original fields keep predictions linked to sample IDs. A research export should not quietly lose a few molecules along the way.',
 'https://github.com/Chuanyanh/molecular-solubility-app','Project repository / 项目代码与记录'),
]
for i,(zt,et,zd,ed,zw,ew,ze,ee,url,link) in enumerate(steps,1):
 st.markdown(f'<div class="guide-step"><div class="step-number">{i:02}</div><div><h3>{html.escape(choose(zt,et))}</h3><p>{html.escape(choose(zd,ed))}</p></div></div>',unsafe_allow_html=True)
 with st.expander(choose(zw,ew)):
  st.write(choose(ze,ee))
  st.markdown(f'[{choose(link, link.split(" / ")[0])}]({url})')
 st.divider()
st.info(choose('面试演示建议：用 aspirin 走一遍查询、结构确认、预测、区间与局限，再打开研究结果讲外部评价。约 3–5 分钟，不必现场重新训练。','Interview demo: use aspirin to show lookup, structure confirmation, prediction, intervals and limitations; then discuss external evaluation in Research evidence. Allow 3–5 minutes; no live retraining is needed.'))
