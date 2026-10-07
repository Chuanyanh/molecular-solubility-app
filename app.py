"""Bilingual entry point. Model fitting stays in the research notebooks."""
import streamlit as st
from presentation import shell, sidebar_notes, choose

st.set_page_config(page_title='Molecular Solubility · Chuanyan He',
                   page_icon=':material/science:', layout='wide')
shell()
pages = [
    st.Page('prediction_page.py',title=choose('分子预测','Molecule explorer'),icon=':material/science:',default=True,url_path='explorer'),
    st.Page('pages/1_研究结果.py',title=choose('研究结果','Research evidence'),icon=':material/query_stats:',url_path='research'),
    st.Page('guide_page.py',title=choose('使用引导','User guide'),icon=':material/menu_book:',url_path='guide'),
    st.Page('pipeline_page.py',title=choose('项目原理图','Project workflow'),icon=':material/account_tree:',url_path='workflow'),
]
page=st.navigation(pages)
sidebar_notes()
page.run()
