分子水溶解度网页 · 面试展示精修版

内容
1. 左侧中文 / English 切换：导航、按钮、解释、图表、研究结果、三维控制。
2. 使用引导：七步入门教程，每步有可展开的“为什么”和资料链接。
3. 项目原理图：中英 SVG、平台分工、数据库与模型选择理由。
4. 统一视觉：暖白、墨绿、陶土色，线条图标、适度圆角、清晰文字。

Mac 上传 GitHub（无需修改代码）
1. 下载并双击 solubility_interview_polish.zip 解压。
2. 在解压后的文件夹按 Command + Shift + . 显示 .streamlit 文件夹。
3. 打开已有 molecular-solubility-app 仓库根目录，Add file → Upload files。
4. 上传解压文件夹中的文件和子文件夹，不上传 ZIP 本身，不套一层总文件夹。
   文件路径必须保留：assets/、locales/、pages/、.streamlit/。
   新包中的 app.py 必须位于仓库根目录。
   子文件夹只包含本次新增或修改的文件；不要删除原有 assets、pages 内容。
5. Commit changes。等待 Streamlit 更新。
6. 应用若没有自动更新，在 Streamlit 应用菜单中执行 Reboot app。
7. 左侧应出现：分子预测、研究结果、使用引导、项目原理图。
   切换 English 后导航为 Molecule explorer、Research evidence、User guide、Project workflow。
8. 先用 aspirin / CID 2244 实测查询和预测，再检查引导与流程图。

同步 Anaconda
把同样文件按原路径上传到项目目录，覆盖同名文件。
不要把新 app.py 单独复制过去：它需要 presentation.py、prediction_page.py、locales 等文件。
原有数据、模型、训练 notebooks 不包含在更新包中，不需要替换。

验证说明
已执行语法检查、中英切换、四页导航、预测结果展示和实测对比交互测试。
交互测试使用固定测试预测器；没有在本机重新运行完整 Torch/GINE 后端或线上 PubChem 请求。
模型文件、solubility_pipeline.py、pubchem_search.py、compound_library.py 未修改。
批量解析、批量预测和单位换算核心函数的 AST 与原版本一致。
英文用于展示层，CSV/JSON 数据与字段保持原样；文献原始注释及来源标识保留其内容。
浏览器端完整视觉检查未完成：远程预览浏览器无法访问本地测试服务。
双语 SVG 原理图已经渲染检查。发布后请用实际网页完成最终视觉验收。

设计与技术参考
https://www.figma.com/resource-library/typography-in-design/
https://www.figma.com/resource-library/creating-accessible-and-inclusive-design/
https://pytorch-geometric.readthedocs.io/en/latest/generated/torch_geometric.nn.conv.GINEConv.html
https://arxiv.org/abs/1905.03222
https://www.nature.com/articles/s41597-019-0151-1

本次没有访问或复制私人 Figma 项目；参考公开的排版、色彩和可读性原则。
