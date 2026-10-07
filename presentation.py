"""Local bilingual presentation layer. Never mutates predictions or export payloads."""
from pathlib import Path
from functools import lru_cache
import json
import re
import html
import streamlit as _st

ROOT = Path(__file__).resolve().parent

@lru_cache(maxsize=1)
def catalogue():
    return json.loads((ROOT / 'locales' / 'en.json').read_text(encoding='utf-8'))

def english():
    return _st.session_state.get('language', '中文') == 'English'

def choose(zh, en):
    return en if english() else zh

@lru_cache(maxsize=1)
def pattern():
    # One replacement pass avoids applying shorter entries to translated text.
    return re.compile('|'.join(re.escape(k) for k in sorted((k for k in catalogue() if len(k) > 1), key=len, reverse=True)))

def tr(value, language=None):
    if not isinstance(value, str) or not (english() if language is None else language):
        return value
    if not re.search(r"[\u4e00-\u9fff]", value):
        return value
    values = catalogue()
    if value in values:
        return values[value]
    # Preserve structured identifiers, URLs and user strings unless a known phrase matches.
    return pattern().sub(lambda m: values[m.group(0)], value)

def display_value(value):
    import pandas as pd
    if isinstance(value, str):
        return tr(value)
    if isinstance(value, pd.DataFrame):
        table = value.copy(deep=True)
        table.columns = [tr(c) for c in table.columns]
        for column in table.select_dtypes(include=['object', 'string']).columns:
            table[column] = table[column].map(tr)
        return table
    if isinstance(value, (list, tuple)):
        return type(value)(display_value(x) for x in value)
    return value

PALETTE = {'#67e4dc':'#246655', '#55d6ce':'#246655', '#b29aff':'#B76547',
           '#f5c96a':'#B88B36', '#edf5ff':'#24332F', '#dceaf7':'#24332F',
           '#d5e4f5':'#42564F', '#101e30':'#F7F5F0', '#132237':'#F7F5F0',
           '#20364d':'#ECEFE8', '#294058':'#D6DDD4', '#263b52':'#D6DDD4',
           '#35516b':'#D6DDD4'}

def plot_value(value):
    if isinstance(value, str):
        return PALETTE.get(value, tr(value))
    if isinstance(value, dict):
        return {k: plot_value(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [plot_value(v) for v in value]
    # Plotly stores axis labels as numpy arrays; translate only string arrays.
    if hasattr(value, 'dtype') and value.dtype.kind in 'OU':
        import numpy as np
        return np.array([tr(x) for x in value])
    return value

class UI:
    """Translate display arguments while preserving widget values and session keys."""
    def __init__(self, target):
        self.target = target
    def __getattr__(self, name):
        real = getattr(self.target, name)
        if name == 'sidebar':
            return UI(real)
        if name == 'columns':
            return lambda *a, **k: [UI(c) for c in real(*a, **k)]
        if name in {'session_state','cache_data','cache_resource','stop','rerun','code','json',
                    'container','empty','progress','divider','form','set_page_config','page_link'}:
            return real
        if not callable(real):
            return real
        def call(*args, **kwargs):
            a = list(args); k = dict(kwargs)
            if name in {'radio','selectbox','select_slider','multiselect'}:
                # Raw option values must stay stable across language changes.
                formatter = k.get('format_func', str)
                current_language = english()
                k['format_func'] = lambda value: tr(formatter(value), current_language)
                if a: a[0] = tr(a[0])
            elif name == 'plotly_chart':
                import plotly.graph_objects as go
                original = a[0] if a else k['figure_or_data']
                fig = go.Figure(plot_value(original.to_plotly_json()))
                fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='#FFFFFF',
                    font=dict(family='Arial, sans-serif',color='#24332F'),
                    legend=dict(bgcolor='#FFFFFF',font=dict(color='#24332F')))
                fig.update_xaxes(gridcolor='#E2E7DF', tickfont=dict(color='#42564F'),
                                 title=dict(font=dict(color='#24332F')))
                fig.update_yaxes(gridcolor='#E2E7DF', tickfont=dict(color='#42564F'),
                                 title=dict(font=dict(color='#24332F')))
                if a: a[0] = fig
                else: k['figure_or_data'] = fig
                k['theme'] = None
            elif name == 'download_button':
                # Translate the label only, never the CSV/JSON bytes.
                if a: a[0] = tr(a[0])
            elif name == 'tabs':
                if a: a[0] = [tr(v) for v in a[0]]
            elif name in {'write','dataframe','table'}:
                a = [display_value(v) for v in a]
            elif a:
                a[0] = tr(a[0])
            for field in ['label','help','placeholder','caption','body']:
                if field in k: k[field] = tr(k[field])
            return real(*a, **k)
        return call
    def __enter__(self):
        self.target.__enter__()
        return self
    def __exit__(self, *args):
        return self.target.__exit__(*args)

ui = UI(_st)

def icon(kind):
    paths = {
        'molecule':'<circle cx="6" cy="7" r="3"/><circle cx="18" cy="6" r="2.5"/><circle cx="14" cy="18" r="3"/><path d="m9 7 6-1M8 10l4 5m5-6-2 6"/>',
        'book':'<path d="M3 4h7a3 3 0 0 1 2 2 3 3 0 0 1 2-2h7v15h-7a3 3 0 0 0-2 2 3 3 0 0 0-2-2H3zM12 6v15"/>',
        'route':'<circle cx="5" cy="5" r="2"/><circle cx="19" cy="19" r="2"/><path d="M7 5h9a4 4 0 0 1 0 8H8a3 3 0 0 0 0 6h9"/>',
        'chart':'<path d="M4 3v17h17M8 16v-5m5 5V6m5 10v-8"/>',
        'database':'<ellipse cx="12" cy="5" rx="8" ry="3"/><path d="M4 5v14c0 4 16 4 16 0V5M4 12c0 4 16 4 16 0"/>',
    }
    return '<svg class="line-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'+paths[kind]+'</svg>'

def heading(kicker, title, subtitle, kind='molecule'):
    _st.markdown(f'<div class="masthead"><div class="eyebrow">{icon(kind)} {html.escape(kicker)}</div><h1>{html.escape(title)}</h1><p>{html.escape(subtitle)}</p></div>',unsafe_allow_html=True)

def shell():
    _st.markdown((ROOT/'assets'/'interview.css').read_text(),unsafe_allow_html=True)
    # Language value is separate from widget state, which Streamlit cleans on page switches.
    _st.session_state.setdefault('language', '中文')
    _st.session_state['language_picker'] = _st.session_state['language']
    def changed():
        _st.session_state['language'] = _st.session_state['language_picker']
    with _st.sidebar:
        _st.markdown('<div class="brand">'+icon('molecule')+'<span>SOLUBILITY<br><small>Chuanyan He · Research notebook</small></span></div>',unsafe_allow_html=True)
        _st.selectbox('Language / 语言', ['中文','English'],key='language_picker',on_change=changed)

def sidebar_notes():
    with _st.sidebar:
        _st.divider()
        with _st.expander(choose('快速上手 · 先看这一张便签','Quick start · your lab note')):
            _st.markdown(choose('**① 输入** `aspirin` 或 `2244`\n\n**② 确认** 名称与二维结构\n\n**③ 点击**「预测水溶解度」\n\n**④ 阅读** 两个估计、区间和适用范围\n\n分子先认对，预测才有讨论价值。','**① Enter** `aspirin` or `2244`\n\n**② Confirm** the name and 2D structure\n\n**③ Click** “Predict solubility”\n\n**④ Read** both estimates, the interval and domain checks\n\nFirst get the molecule right. Then discuss the prediction.'))
            _st.page_link('guide_page.py',label=choose('打开完整操作指南','Open the full user guide'),icon=':material/menu_book:')
        with _st.expander(choose('从数据到网页 · 项目路线','From data to browser · project route')):
            _st.caption(choose('Anaconda：整理数据、训练与评价\n\nGitHub：保存代码与模型\n\nStreamlit：加载模型、交互展示','Anaconda: preparation, training and evaluation\n\nGitHub: code and saved models\n\nStreamlit: model loading and interactive display'))
            _st.page_link('pipeline_page.py',label=choose('展开原理图与选择理由','Explore the workflow and rationale'),icon=':material/account_tree:')
        _st.caption(choose('结构给出线索，实验给出答案。','Structure offers clues. Experiments give answers.'))
