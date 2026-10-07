"""Source-backed physical descriptions; SVG is illustrative, not a photograph."""
from functools import lru_cache
from html import escape
import random
from rdkit import Chem

RECORDS = [
 ('CC(=O)Oc1ccccc1C(=O)O','阿司匹林','solid','无色至白色结晶性粉末','0010'),
 ('CCO','乙醇','liquid','透明无色液体','0262'),
 ('CC(=O)C','丙酮','liquid','无色液体','0004'),
 ('CO','甲醇','liquid','无色液体','0397'),
 ('CCOCC','乙醚','liquid','无色液体','0277'),
 ('CC#N','乙腈','liquid','无色液体','0006'),
]

@lru_cache(maxsize=1)
def _index():
    return {Chem.MolToSmiles(Chem.MolFromSmiles(s), isomericSmiles=True):
            dict(name=name, state=state, description=description,
                 source='CDC / NIOSH 化学危害袖珍指南',
                 url=f'https://www.cdc.gov/niosh/npg/npgd{code}.html')
            for s,name,state,description,code in RECORDS}

def get_appearance(smiles):
    mol=Chem.MolFromSmiles(smiles)
    return _index().get(Chem.MolToSmiles(mol, isomericSmiles=True)) if mol else None

def appearance_html(record):
    name=escape(record['name'])
    if record['state']=='solid':
        rng=random.Random(42)
        grains=[]
        for _ in range(380):
            x=rng.uniform(150,450)
            top=295+abs(x-300)*0.35
            y=rng.uniform(top,365)
            size=rng.uniform(1,3.5)
            grains.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{size:.1f}" fill="{rng.choice(["#ffffff","#d7e0ea","#aebccd"])}"/>')
        scene='<ellipse cx="300" cy="363" rx="200" ry="42" fill="url(#glass)" stroke="#7b94af"/><path d="M145 363 Q300 260 455 363 Q300 399 145 363" fill="#d7e0ea"/>'+''.join(grains)
        label='结晶性粉末示意'
    else:
        scene='''<path d="M185 90 L185 343 Q185 380 220 380 L380 380 Q415 380 415 343 L415 90" fill="url(#glass)" stroke="#9bb6cc" stroke-width="3"/>
<path d="M190 238 L190 342 Q190 373 220 373 L380 373 Q410 373 410 342 L410 238 Z" fill="url(#liquid)"/>
<ellipse class="surface" cx="300" cy="238" rx="110" ry="12" fill="#cedeea" fill-opacity=".35" stroke="#d7e8f3"/>
<path d="M200 112 L200 330" stroke="white" stroke-width="7" opacity=".35" stroke-linecap="round"/>
<path d="M400 115 L400 325" stroke="white" stroke-width="3" opacity=".2"/>
<ellipse cx="300" cy="90" rx="115" ry="14" fill="none" stroke="#9bb6cc" stroke-width="3"/>
<g stroke="#b8cede" opacity=".55"> <path d="M385 140h20 M385 180h20 M385 220h20 M385 260h20 M385 300h20"/></g>'''
        label='无色液体示意'
    return f'''<!doctype html><html lang="zh"><meta charset="utf-8"><style>
body{{margin:0;background:#F7F5F0;color:#24332F;font-family:Arial,sans-serif}}.card{{border:1px solid #D6DDD4;border-radius:18px;padding:16px;background:#F7F5F0}}
.header{{display:flex;justify-content:space-between;align-items:center}}.tag{{color:#246655;font-size:13px}}svg{{width:100%;height:350px}}.note{{color:#596C63;font-size:13px;line-height:1.6}}button{{background:#FFFFFF;color:#24332F;border:1px solid #D6DDD4;padding:8px 12px;border-radius:9px;cursor:pointer}}
.surface{{animation:ripple 4s ease-in-out infinite;transform-origin:300px 238px}}@keyframes ripple{{50%{{transform:scaleY(.7)}}}}.paused .surface{{animation-play-state:paused}}@media(prefers-reduced-motion:reduce){{.surface{{animation:none}}}}
</style><div class="card"><div class="header"><b>{name}</b><span class="tag">{label}</span></div>
<svg viewBox="0 0 600 430" role="img" aria-label="{name}的{label}"><defs>
<linearGradient id="glass"><stop stop-color="#cde4f5" stop-opacity=".17"/><stop offset=".5" stop-color="#eaf4ff" stop-opacity=".03"/><stop offset="1" stop-color="#b9d7ec" stop-opacity=".22"/></linearGradient>
<linearGradient id="liquid" x2="0" y2="1"><stop stop-color="#d2e5f0" stop-opacity=".12"/><stop offset="1" stop-color="#c7e0f2" stop-opacity=".38"/></linearGradient></defs>
<ellipse cx="300" cy="394" rx="160" ry="12" fill="#000" opacity=".35"/>{scene}</svg>
<div class="note">外观示意，非实物照片。容器、装填量和光影仅用于展示；液体的浅蓝灰效果来自示意光影，不代表物质有颜色。</div>
<button onclick="document.body.classList.toggle('paused');this.textContent=document.body.classList.contains('paused')?'播放动画':'暂停动画'">暂停动画</button></div></html>'''

# SOLID_DISPLAY_FIX_V2
_original_appearance_html = appearance_html

def appearance_html(record):
    import re
    html = _original_appearance_html(record)
    if record["state"] == "solid":
        html = re.sub(r"<button\b[^>]*>.*?</button>", "", html, flags=re.S)
        html = html.replace("；液体的浅蓝灰效果来自示意光影，不代表物质有颜色。", "。")
    return html
