"""CSS globale per l'app Streamlit."""

import streamlit as st


def inject_css():
    st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

    .stApp {
        font-family: 'DM Sans', sans-serif;
        background-color: #F8FAFC;
    }

    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0F172A 0%, #1E293B 100%);
    }
    section[data-testid="stSidebar"] .stMarkdown p,
    section[data-testid="stSidebar"] .stMarkdown span,
    section[data-testid="stSidebar"] .stRadio label,
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3 {
        color: #F1F5F9 !important;
    }
    section[data-testid="stSidebar"] .stRadio label:hover {
        background: rgba(255,255,255,0.06);
        border-radius: 8px;
    }
    section[data-testid="stSidebar"] hr {
        border-color: rgba(255,255,255,0.1);
    }

    .step-badge {
        display: inline-flex;
        align-items: center;
        gap: 10px;
        margin-bottom: 8px;
    }
    .step-num {
        background: linear-gradient(135deg, #0F172A, #334155);
        color: #FFF;
        width: 30px; height: 30px;
        border-radius: 8px;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        font-weight: 700;
        font-size: 13px;
        flex-shrink: 0;
    }
    .step-label {
        font-size: 20px;
        font-weight: 700;
        color: #0F172A;
    }

    .claim-pill {
        background: #F0F9FF;
        border: 1px solid #BAE6FD;
        border-radius: 8px;
        padding: 10px 14px;
        margin-bottom: 6px;
        font-size: 14px;
        color: #0C4A6E;
        line-height: 1.5;
    }
    .claim-pill .claim-idx {
        font-family: 'JetBrains Mono', monospace;
        font-weight: 600;
        color: #0369A1;
        margin-right: 8px;
        font-size: 12px;
    }

    .metric-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 20px 24px;
        text-align: center;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }
    .metric-value {
        font-size: 36px;
        font-weight: 700;
        color: #0F172A;
        line-height: 1.2;
    }
    .metric-label {
        font-size: 13px;
        color: #64748B;
        margin-top: 4px;
        font-weight: 500;
    }
    .metric-bar {
        height: 4px;
        border-radius: 2px;
        margin-top: 12px;
        background: #E2E8F0;
        overflow: hidden;
    }
    .metric-bar-fill {
        height: 100%;
        border-radius: 2px;
        transition: width 0.6s ease;
    }

    .support-yes {
        display: inline-block;
        background: #DCFCE7;
        color: #166534;
        font-size: 11px;
        font-weight: 600;
        padding: 2px 10px;
        border-radius: 20px;
    }
    .support-no {
        display: inline-block;
        background: #FEE2E2;
        color: #991B1B;
        font-size: 11px;
        font-weight: 600;
        padding: 2px 10px;
        border-radius: 20px;
    }

    .page-header {
        margin-bottom: 24px;
    }
    .page-header h1 {
        font-size: 28px !important;
        font-weight: 700 !important;
        color: #0F172A !important;
        margin-bottom: 4px !important;
    }
    .page-header p {
        color: #64748B;
        font-size: 15px;
        margin-top: 0;
    }

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    .streamlit-expanderHeader {
        font-weight: 600 !important;
        font-size: 14px !important;
    }

    .response-box {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-left: 4px solid #3B82F6;
        border-radius: 8px;
        padding: 16px 20px;
        font-size: 14px;
        line-height: 1.8;
        color: #1E293B;
        margin-bottom: 12px;
    }

    .debug-sentence-row {
        margin: 3px 0;
        padding: 6px 10px;
        border-radius: 6px;
        background: #F8FAFC;
        border: 1px solid #E2E8F0;
    }
</style>
""", unsafe_allow_html=True)