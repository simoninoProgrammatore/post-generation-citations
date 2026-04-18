"""Streamlit app for the Post-Generation Citation System.
Run with: streamlit run src/app.py
"""

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="Citation Pipeline",
    page_icon="📚",
    layout="wide",
)

from ui.styles import inject_css
from views import pipeline, explore, metrics, attention, interpretability

inject_css()

# Sidebar
st.sidebar.markdown("### 📚 Citation Pipeline")
page = st.sidebar.radio(
    "Sezione",
    [
        "🔬 Pipeline interattivo",
        "📂 Esplora risultati",
        "📊 Metriche",
        "📡 Attention Analysis",
        "🔬 Interpretability",
    ],
    label_visibility="collapsed",
)
st.sidebar.divider()
st.sidebar.caption("Post-Generation Citation System — Tesi triennale")

# Page dispatch
if page == "🔬 Pipeline interattivo":
    pipeline.render()
elif page == "📂 Esplora risultati":
    explore.render()
elif page == "📊 Metriche":
    metrics.render()
elif page == "📡 Attention Analysis":
    attention.render()
elif page == "🔬 Interpretability":
    interpretability.render()