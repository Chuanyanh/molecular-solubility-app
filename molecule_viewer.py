import json
from pathlib import Path
from functools import lru_cache
from rdkit import Chem
from rdkit.Chem import AllChem

@lru_cache(maxsize=64)
def molecule_html(smiles, english=False):
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        raise ValueError("无法解析分子结构。")
    mol = Chem.AddHs(mol)
    params = AllChem.ETKDGv3()
    params.randomSeed = 42
    if AllChem.EmbedMolecule(mol, params) != 0:
        raise ValueError("三维构象生成失败，请查看二维结构。")
    if AllChem.MMFFHasAllMoleculeParams(mol):
        AllChem.MMFFOptimizeMolecule(mol, maxIters=300)

    sdf = json.dumps(Chem.MolToMolBlock(mol))
    js = (
        Path(__file__).resolve().parent / "assets" / "3Dmol-min.js"
    ).read_text(encoding="utf-8")
    js = js.replace("</script", r"<\/script")

    template = """
<!doctype html>
<html>
<head>
<meta charset="utf-8">
<style>
body {margin:0;background:#080d18;color:#e9eff8;
      font-family:Arial,sans-serif;}
#stage {height:430px;width:100%;position:relative;}
.tools {display:flex;gap:8px;padding:10px;flex-wrap:wrap;}
button {background:#19263b;border:1px solid #35465e;
        color:#e9eff8;padding:8px 12px;border-radius:9px;
        cursor:pointer;}
button:hover {background:#284461;}
#note {padding:0 12px 12px;font-size:12px;color:#a9b9ce;}
</style>
<script>__LIBRARY__</script>
</head>
<body>
<div class="tools">
<button onclick="setMode('ball')">球棍模型</button>
<button onclick="setMode('space')">空间填充</button>
<button onclick="toggleSpin()">旋转 / 暂停</button>
<button onclick="resetView()">重置视角</button>
</div>
<div id="stage"></div>
<div id="note">拖动旋转 · 滚轮缩放 · 点击原子查看元素</div>
<script>
let viewer;
let spinning = false;
try {
    viewer = $3Dmol.createViewer(
        document.getElementById('stage'),
        {backgroundColor:'#080d18', antialias:true}
    );
    viewer.addModel(__SDF__, 'sdf');

    window.setMode = function(mode) {
        viewer.setStyle({}, mode === 'space'
            ? {sphere:{colorscheme:'Jmol'}}
            : {
                sphere:{scale:0.30,colorscheme:'Jmol'},
                stick:{radius:0.14,colorscheme:'Jmol'}
              });
        viewer.render();
    };
    window.toggleSpin = function() {
        spinning = !spinning;
        viewer.spin(spinning ? 'y' : false);
    };
    window.resetView = function() {
        viewer.zoomTo();
        viewer.zoom(1.8);
        viewer.render();
    };
    viewer.setClickable({}, true, function(atom) {
        document.getElementById('note').textContent =
            '所选原子：' + atom.elem +
            ' · 拖动旋转 · 滚轮缩放';
    });
    setMode('ball');
    viewer.zoomTo();
        viewer.zoom(1.8);
    viewer.render();
    window.addEventListener('resize', function() {
        viewer.resize();
        viewer.render();
    });
} catch(error) {
    document.getElementById('note').textContent =
        '三维显示失败，请查看二维结构：' + error.message;
}
</script>
</body>
</html>
"""
    if english:
        import json as _json
        translations = _json.loads((Path(__file__).resolve().parent / "locales" / "en.json").read_text())
        for key in sorted(translations, key=len, reverse=True):
            template = template.replace(key, translations[key])
    template = template.replace("#080d18", "#F7F5F0").replace("#e9eff8", "#24332F").replace("#19263b", "#FFFFFF").replace("#35465e", "#D6DDD4").replace("#284461", "#EAF0E8").replace("#a9b9ce", "#596C63")
    return template.replace("__LIBRARY__", js).replace("__SDF__", sdf)
