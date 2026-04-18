"""
Streamlit app for the Post-Generation Citation System.
Run with: streamlit run src/app.py
"""

import json
import os
import re
import streamlit as st
import numpy as np
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="Citation Pipeline",
    page_icon="📚",
    layout="wide",
)

# ──────────────────────────────────────────────
# Custom CSS
# ──────────────────────────────────────────────

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


# ──────────────────────────────────────────────
# Sidebar
# ──────────────────────────────────────────────

st.sidebar.markdown("### 📚 Citation Pipeline")
page = st.sidebar.radio(
    "Sezione",
    ["🔬 Pipeline interattivo", "📂 Esplora risultati", "📊 Metriche", "📡 Attention Analysis", "🔬 Interpretability"],
    label_visibility="collapsed",
)
st.sidebar.divider()
st.sidebar.caption("Post-Generation Citation System — Tesi triennale")

# ──────────────────────────────────────────────
# Helpers (UI)
# ──────────────────────────────────────────────

def step_header(num: int, title: str):
    st.markdown(
        f'<div class="step-badge">'
        f'<span class="step-num">{num}</span>'
        f'<span class="step-label">{title}</span>'
        f'</div>',
        unsafe_allow_html=True,
    )


def render_claim(idx: int, text: str):
    st.markdown(
        f'<div class="claim-pill">'
        f'<span class="claim-idx">{idx:02d}</span>{text}'
        f'</div>',
        unsafe_allow_html=True,
    )


def render_metric_card(label: str, value: float, color: str = "#3B82F6"):
    pct = int(value * 100)
    st.markdown(
        f'<div class="metric-card">'
        f'<div class="metric-value">{value:.3f}</div>'
        f'<div class="metric-label">{label}</div>'
        f'<div class="metric-bar"><div class="metric-bar-fill" style="width:{pct}%;background:{color};"></div></div>'
        f'</div>',
        unsafe_allow_html=True,
    )


def support_badge(has_support: bool) -> str:
    if has_support:
        return '<span class="support-yes">✓ Supported</span>'
    return '<span class="support-no">✗ Unsupported</span>'


def render_nli_debug(debug_data: list[dict]):
    """Renderizza il pannello debug NLI con tutti gli entailment scores per frase."""
    st.markdown("#### 🔬 Debug NLI — Entailment scores per frase")
    st.caption("Per ogni claim, mostra lo score di entailment di ogni frase di ogni passaggio candidato.")

    for debug_item in debug_data:
        claim_text = debug_item["claim"]
        sentence_scores = debug_item.get("sentence_scores", [])

        if not sentence_scores:
            continue

        # Conta quante frasi superano threshold
        all_sents = [s for p in sentence_scores for s in p["sentences"]]
        best_overall = max((s["score"] for s in all_sents), default=0)

        with st.expander(
            f"📌 {claim_text[:85]}{'...' if len(claim_text) > 85 else ''}  "
            f"— best score: `{best_overall:.4f}`"
        ):
            for passage_entry in sentence_scores:
                p_title = passage_entry["title"]
                sents = passage_entry["sentences"]

                st.markdown(f"**📄 {p_title}**")

                # Ordina per score decrescente
                for s in sorted(sents, key=lambda x: x["score"], reverse=True):
                    score = s["score"]
                    is_best = s["is_best"]

                    # Colore basato sullo score
                    if score >= 0.7:
                        color = "#10B981"
                        bg = "#F0FDF4"
                        border = "#86EFAC"
                    elif score >= 0.4:
                        color = "#F59E0B"
                        bg = "#FFFBEB"
                        border = "#FCD34D"
                    else:
                        color = "#94A3B8"
                        bg = "#F8FAFC"
                        border = "#E2E8F0"

                    # Barra proporzionale (max 25 caratteri)
                    bar_filled = int(score * 25)
                    bar_empty = 25 - bar_filled
                    bar_html = (
                        f'<span style="color:{color};">{"█" * bar_filled}</span>'
                        f'<span style="color:#E2E8F0;">{"█" * bar_empty}</span>'
                    )

                    best_badge = (
                        '<span style="background:#DCFCE7;color:#166534;font-size:10px;'
                        'font-weight:700;padding:1px 7px;border-radius:20px;margin-left:6px;">⭐ BEST</span>'
                        if is_best else ""
                    )

                    sentence_preview = s["text"][:140] + ("…" if len(s["text"]) > 140 else "")

                    st.markdown(
                        f'<div style="margin:4px 0; padding:8px 12px; border-radius:7px; '
                        f'background:{bg}; border:1px solid {border}; font-size:13px;">'
                        f'<div style="display:flex; align-items:center; gap:8px; margin-bottom:4px;">'
                        f'<span style="font-family:\'JetBrains Mono\',monospace; font-weight:700; color:{color}; font-size:13px;">'
                        f'[{score:.4f}]</span>'
                        f'<span style="font-family:\'JetBrains Mono\',monospace; font-size:12px;">{bar_html}</span>'
                        f'{best_badge}'
                        f'</div>'
                        f'<div style="color:#475569; line-height:1.5;">"{sentence_preview}"</div>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )

                st.divider()


# ──────────────────────────────────────────────
# Cached model loaders
# ──────────────────────────────────────────────

@st.cache_resource
def get_nli_model(model_name: str):
    from sentence_transformers import CrossEncoder
    return CrossEncoder(model_name)


@st.cache_resource
def get_embedding_model(model_name: str):
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer(model_name)


# ──────────────────────────────────────────────
# Pipeline functions
# ──────────────────────────────────────────────

def run_generate(query: str, model: str, passages: list[dict] = None) -> str:
    from llm_client import call_llm

    if passages:
        passages_text = "\n\n".join([
            f"[{i+1}] {p.get('title', 'N/A')}:\n{p.get('text', '')}"
            for i, p in enumerate(passages[:10])
        ])
        prompt = (
            "You are a knowledgeable assistant. "
            "Answer the question ONLY using the information provided in the passages below. "
            "Do NOT use any external knowledge. "
            "If the passages do not contain enough information to answer, say so. "
            "Do NOT include any citations or references in your response. "
            "Write in plain text without markdown formatting.\n\n"
            f"Passages:\n{passages_text}\n\n"
            f"Question: {query}\n\nAnswer:"
        )
    else:
        prompt = (
            "You are a knowledgeable assistant. "
            "Answer the question clearly and factually in plain text. "
            "Do NOT use markdown formatting, headers, or bullet points. "
            "Do NOT include any citations or references in your response.\n\n"
            f"Question: {query}\n\nAnswer:"
        )

    return call_llm(prompt, model=model)


def run_decompose(response: str, model: str) -> list[str]:
    from llm_client import call_llm_json
    prompt = f"""\
Break the following text into independent atomic facts.
Each fact must:
- Contain exactly one piece of information
- Be self-contained and understandable without context
- Be a complete declarative sentence

Return ONLY a JSON array of strings, no preamble.

Text:
{response}
"""
    return call_llm_json(prompt, model=model)


def run_retrieve(
    claims: list[str],
    passages: list[dict],
    method: str,
    threshold: float,
    top_k: int,
) -> tuple[list[dict], list[dict]]:
    """
    Restituisce (matched, debug_data).
    debug_data è una lista di dict con 'claim' e 'sentence_scores'
    (popolato solo per method='nli').
    """
    from retrieve import match_with_nli, match_with_similarity, match_with_llm, extract_evidence

    matched = []
    debug_data = []

    for claim in claims:
        sentence_scores = []

        if method == "nli":
            matches, sentence_scores = match_with_nli(
                claim, passages, threshold=threshold, top_k=top_k, return_all_scores=True
            )
        elif method == "llm":
            matches = match_with_llm(claim, passages, threshold=threshold, top_k=top_k)
        else:
            matches = match_with_similarity(claim, passages, top_k=top_k)

        for match in matches:
            ev = extract_evidence(
                claim,
                match.get("text", ""),
                best_sentence=match.get("best_sentence", ""),
                extraction_start=match.get("extraction_start", -1),
                extraction_end=match.get("extraction_end", -1),
            )
            match["extraction"] = ev["extraction"]
            match["extraction_start"] = ev["extraction_start"]
            match["extraction_end"] = ev["extraction_end"]
            match["summary"] = ev["summary"]

        matches = [m for m in matches if m.get("extraction", "").strip()]
        matched.append({"claim": claim, "supporting_passages": matches})
        debug_data.append({"claim": claim, "sentence_scores": sentence_scores})

    return matched, debug_data


def run_cite(response: str, matched_claims: list[dict]) -> tuple[str, list[dict]]:
    from cite import build_citation_map, insert_citations
    citation_map = build_citation_map(matched_claims)
    cited, refs = insert_citations(response, matched_claims, citation_map)
    return cited, refs


# ──────────────────────────────────────────────
# Cited HTML
# ──────────────────────────────────────────────

def build_cited_html(cited: str, matched: list[dict], refs: list[dict]) -> str:

    claim_support = {}
    for m in matched:
        if m["supporting_passages"]:
            claim_support[m["claim"]] = m["supporting_passages"]

    citation_map = {}
    counter = 1
    for m in matched:
        for p in m["supporting_passages"]:
            pid = p.get("id") or p.get("title", "")
            if pid not in citation_map:
                citation_map[pid] = counter
                counter += 1

    sentences = re.split(r'(?<=[.!?])(?:\[\d+\])*\s+', cited.strip())

    def find_matching_claims(sentence: str) -> list[tuple]:
        sent_words = set(re.sub(r'[^\w\s]', '', sentence.lower()).split())
        results = []
        for claim, passages in claim_support.items():
            claim_words = set(re.sub(r'[^\w\s]', '', claim.lower()).split())
            stopwords = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'in', 'on',
                         'at', 'to', 'for', 'of', 'and', 'or', 'but', 'with', 'as',
                         'his', 'her', 'their', 'its', 'has', 'have', 'had', 'by'}
            claim_words -= stopwords
            sent_words_clean = sent_words - stopwords
            if not claim_words:
                continue
            overlap = len(claim_words & sent_words_clean) / len(claim_words)
            if overlap >= 0.4:
                results.append((claim, passages, overlap))
        results.sort(key=lambda x: x[2], reverse=True)
        return [(c, p) for c, p, _ in results]

    sentences_html = ""
    sentence_data = []

    for i, sent in enumerate(sentences):
        clean_sent = re.sub(r'\[\d+\]', '', sent).strip()
        matching = find_matching_claims(clean_sent)

        if matching:
            cite_nums = []
            for claim, passages in matching:
                for p in passages:
                    pid = p.get("id") or p.get("title", "")
                    if pid in citation_map:
                        cite_nums.append(citation_map[pid])
            cite_nums = sorted(set(cite_nums))
            cite_markers = "".join(f'<sup class="cite-marker">[{n}]</sup>' for n in cite_nums)

            sentence_data.append({
                "idx": i,
                "claims": [
                    {
                        "claim": claim,
                        "passages": [
                            {
                                "title": p.get("title", "N/A"),
                                "text": p.get("text", ""),
                                "score": p.get("entailment_score", p.get("similarity_score", 0)),
                                "cite_num": citation_map.get(p.get("id") or p.get("title", ""), "?"),
                                "extraction": p.get("extraction", ""),
                                "extraction_start": p.get("extraction_start", -1),
                                "extraction_end": p.get("extraction_end", -1),
                            }
                            for p in passages
                        ]
                    }
                    for claim, passages in matching
                ]
            })

            sentences_html += f'<span class="sentence supported" data-idx="{i}">{clean_sent}{cite_markers}</span> '
        else:
            sentence_data.append({"idx": i, "claims": []})
            sentences_html += f'<span class="sentence">{clean_sent}</span> '

    refs_html = ""
    for ref in refs:
        refs_html += f"""
        <div class="ref-item">
            <span class="ref-num">[{ref['citation_number']}]</span>
            <span class="ref-title">{ref.get('title', 'N/A')}</span>
            <div class="ref-text">{ref.get('text', '')}</div>
        </div>"""

    sentence_data_json = json.dumps(sentence_data)

    html = f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{ font-family: 'DM Sans', sans-serif; background: transparent; }}

        .cited-container {{
            font-size: 15px;
            line-height: 2;
            padding: 24px;
            background: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-radius: 12px;
            margin-bottom: 16px;
            color: #1E293B;
        }}
        .sentence {{ border-radius: 4px; padding: 2px 4px; transition: all 0.2s ease; }}
        .sentence.supported {{ background: #F0FDF4; cursor: pointer; border-bottom: 2px solid #86EFAC; }}
        .sentence.supported:hover {{ background: #DCFCE7; }}
        .sentence.active {{ background: #BBF7D0; }}
        .cite-marker {{ color: #059669; font-weight: 700; font-size: 11px; font-family: 'JetBrains Mono', monospace; margin-left: 1px; }}

        .panel {{ display: none; margin: 10px 0 16px 0; border-left: 3px solid #10B981; padding: 16px 20px; background: #F0FDF9; border-radius: 0 10px 10px 0; font-size: 13px; }}
        .panel.visible {{ display: block; }}
        .panel-breadcrumb {{ font-size: 11px; color: #94A3B8; margin-bottom: 12px; font-weight: 500; text-transform: uppercase; letter-spacing: 0.5px; }}

        .claim-card {{ background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 10px; padding: 14px 18px; margin-bottom: 8px; cursor: pointer; transition: all 0.2s ease; display: flex; align-items: center; gap: 12px; }}
        .claim-card:hover {{ border-color: #10B981; background: #F0FDF4; transform: translateX(4px); }}
        .claim-card.active {{ border-color: #10B981; background: #ECFDF5; box-shadow: 0 0 0 1px #10B981; }}
        .claim-icon {{ width: 28px; height: 28px; border-radius: 8px; background: #F0F9FF; border: 1px solid #BAE6FD; display: flex; align-items: center; justify-content: center; font-size: 12px; flex-shrink: 0; color: #0369A1; font-weight: 700; font-family: 'JetBrains Mono', monospace; }}
        .claim-text-label {{ flex: 1; color: #334155; font-size: 13px; line-height: 1.5; }}
        .claim-arrow {{ color: #94A3B8; font-size: 16px; flex-shrink: 0; transition: transform 0.2s; }}
        .claim-card:hover .claim-arrow {{ transform: translateX(3px); color: #10B981; }}
        .claim-passage-count {{ font-size: 11px; color: #64748B; background: #F1F5F9; padding: 2px 8px; border-radius: 20px; flex-shrink: 0; font-family: 'JetBrains Mono', monospace; }}

        .sources-panel {{ display: none; margin-top: 10px; padding: 16px 20px; background: #FAFFFE; border: 1px solid #D1FAE5; border-radius: 10px; animation: slideDown 0.25s ease; }}
        .sources-panel.visible {{ display: block; }}
        @keyframes slideDown {{ from {{ opacity: 0; transform: translateY(-8px); }} to {{ opacity: 1; transform: translateY(0); }} }}

        .back-btn {{ display: inline-flex; align-items: center; gap: 6px; font-size: 12px; color: #64748B; cursor: pointer; margin-bottom: 12px; padding: 4px 10px; border-radius: 6px; transition: all 0.15s; border: none; background: none; font-family: 'DM Sans', sans-serif; }}
        .back-btn:hover {{ background: #F1F5F9; color: #0F172A; }}
        .source-claim-label {{ font-size: 13px; color: #0F172A; font-weight: 600; margin-bottom: 12px; padding-bottom: 10px; border-bottom: 1px solid #D1FAE5; }}

        .passage-card {{ background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 10px; padding: 0; margin-bottom: 10px; overflow: hidden; }}
        .passage-header {{ display: flex; justify-content: space-between; align-items: center; padding: 12px 16px; background: #F8FAFC; border-bottom: 1px solid #E2E8F0; }}
        .passage-title {{ font-weight: 600; color: #0F172A; font-size: 13px; }}
        .score-pill {{ background: #10B981; color: white; border-radius: 20px; padding: 2px 10px; font-size: 11px; font-family: 'JetBrains Mono', monospace; font-weight: 500; }}
        .cite-pill {{ background: #0F172A; color: white; border-radius: 20px; padding: 2px 10px; font-size: 11px; font-family: 'JetBrains Mono', monospace; font-weight: 500; margin-left: 4px; }}
        .passage-body {{ max-height: 220px; overflow-y: auto; padding: 14px 16px; scroll-behavior: smooth; }}
        .passage-text {{ color: #64748B; font-size: 13px; line-height: 1.8; }}
        .evidence-highlight {{ background: linear-gradient(180deg, transparent 55%, #FDE68A 55%); color: #1E293B; font-weight: 600; padding: 0 2px; border-radius: 2px; scroll-margin-top: 20px; }}

        .refs-section {{ margin-top: 20px; padding-top: 16px; border-top: 2px solid #E2E8F0; font-size: 13px; }}
        .refs-section strong {{ font-size: 15px; color: #0F172A; }}
        .ref-item {{ margin-top: 10px; padding: 12px 16px; background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; }}
        .ref-num {{ font-family: 'JetBrains Mono', monospace; font-weight: 700; color: #059669; margin-right: 6px; }}
        .ref-title {{ font-weight: 600; color: #0F172A; }}
        .ref-text {{ color: #64748B; font-size: 12px; margin-top: 6px; line-height: 1.7; }}
    </style>

    <div class="cited-container">{sentences_html}</div>
    <div id="panels-container"></div>
    {f'<div class="refs-section"><strong>References</strong>{refs_html}</div>' if refs_html else ''}

    <script>
        const sentenceData = {sentence_data_json};
        const dataMap = {{}};
        sentenceData.forEach(s => dataMap[s.idx] = s);

        function highlightEvidence(fullText, extraction, extractionStart, extractionEnd, passageId) {{
            if (!extraction || !extraction.trim()) {{
                return '<span class="passage-text">' + fullText + '</span>';
            }}

            let idx = (extractionStart >= 0) ? extractionStart : fullText.indexOf(extraction);
            let endIdx = (extractionEnd >= 0) ? extractionEnd : (idx !== -1 ? idx + extraction.length : -1);

            if (idx !== -1 && endIdx !== -1) {{
                const before = fullText.substring(0, idx);
                const match = fullText.substring(idx, endIdx);
                const after = fullText.substring(endIdx);
                return '<span class="passage-text">' + before +
                    '<span class="evidence-highlight" id="ev-' + passageId + '">' + match + '</span>' +
                    after + '</span>';
            }}

            const extWords = extraction.toLowerCase().split(/\s+/);
            const sents = fullText.split(/(?<=[.!?])\s+/);
            let bestSent = '', bestScore = 0;
            sents.forEach(s => {{
                const sWords = s.toLowerCase().split(/\s+/);
                const overlap = extWords.filter(w => sWords.includes(w)).length / extWords.length;
                if (overlap > bestScore) {{ bestScore = overlap; bestSent = s; }}
            }});
            if (bestScore >= 0.5 && bestSent) {{
                const bIdx = fullText.indexOf(bestSent);
                if (bIdx !== -1) {{
                    return '<span class="passage-text">' + fullText.substring(0, bIdx) +
                        '<span class="evidence-highlight" id="ev-' + passageId + '">' + bestSent + '</span>' +
                        fullText.substring(bIdx + bestSent.length) + '</span>';
                }}
            }}
            return '<span class="passage-text">' + fullText + '</span>';
        }}

        function buildSourcesView(sentIdx, claimIdx, claim) {{
            const wrapper = document.createElement('div');
            wrapper.className = 'sources-panel visible';
            const backBtn = document.createElement('button');
            backBtn.className = 'back-btn';
            backBtn.innerHTML = '← Torna ai claims';
            backBtn.addEventListener('click', () => {{
                wrapper.remove();
                const panel = document.querySelector('.panel[data-sent="' + sentIdx + '"]');
                if (panel) {{
                    panel.querySelectorAll('.claim-card').forEach(c => c.classList.remove('active'));
                    panel.querySelector('.claims-list').style.display = 'block';
                }}
            }});
            wrapper.appendChild(backBtn);
            const label = document.createElement('div');
            label.className = 'source-claim-label';
            label.innerHTML = '🔍 ' + claim.claim;
            wrapper.appendChild(label);
            claim.passages.forEach((p, pIdx) => {{
                const passageId = sentIdx + '-' + claimIdx + '-' + pIdx;
                const highlighted = highlightEvidence(
                    p.text,
                    p.extraction || '',
                    p.extraction_start ?? -1,
                    p.extraction_end ?? -1,
                    passageId
                );
                const card = document.createElement('div');
                card.className = 'passage-card';
                card.innerHTML = `
                    <div class="passage-header">
                        <span class="passage-title">${{p.title}}</span>
                        <span>
                            <span class="score-pill">${{p.score.toFixed(3)}}</span>
                            <span class="cite-pill">[${{p.cite_num}}]</span>
                        </span>
                    </div>
                    <div class="passage-body">${{highlighted}}</div>
                `;
                wrapper.appendChild(card);
                setTimeout(() => {{
                    const evEl = document.getElementById('ev-' + passageId);
                    if (evEl) {{
                        const container = evEl.closest('.passage-body');
                        if (container) {{ container.scrollTop = evEl.offsetTop - container.offsetTop - 20; }}
                    }}
                }}, 150);
            }});
            return wrapper;
        }}

        document.querySelectorAll('.sentence.supported').forEach(el => {{
            el.addEventListener('click', function() {{
                const idx = parseInt(this.dataset.idx);
                const isActive = this.classList.contains('active');
                document.querySelectorAll('.sentence.active').forEach(s => s.classList.remove('active'));
                document.querySelectorAll('.panel').forEach(p => p.remove());
                if (!isActive) {{
                    this.classList.add('active');
                    const data = dataMap[idx];
                    if (!data || !data.claims.length) return;
                    const panel = document.createElement('div');
                    panel.className = 'panel visible';
                    panel.setAttribute('data-sent', idx);
                    const breadcrumb = document.createElement('div');
                    breadcrumb.className = 'panel-breadcrumb';
                    breadcrumb.textContent = 'Claims associati — clicca per vedere le fonti';
                    panel.appendChild(breadcrumb);
                    const claimsList = document.createElement('div');
                    claimsList.className = 'claims-list';
                    data.claims.forEach((c, cIdx) => {{
                        const card = document.createElement('div');
                        card.className = 'claim-card';
                        const icon = document.createElement('div');
                        icon.className = 'claim-icon';
                        icon.textContent = (cIdx + 1);
                        const text = document.createElement('div');
                        text.className = 'claim-text-label';
                        text.textContent = c.claim;
                        const count = document.createElement('span');
                        count.className = 'claim-passage-count';
                        count.textContent = c.passages.length + ' fonti';
                        const arrow = document.createElement('span');
                        arrow.className = 'claim-arrow';
                        arrow.textContent = '→';
                        card.appendChild(icon);
                        card.appendChild(text);
                        card.appendChild(count);
                        card.appendChild(arrow);
                        card.addEventListener('click', () => {{
                            claimsList.style.display = 'none';
                            card.classList.add('active');
                            const sourcesView = buildSourcesView(idx, cIdx, c);
                            panel.appendChild(sourcesView);
                        }});
                        claimsList.appendChild(card);
                    }});
                    panel.appendChild(claimsList);
                    this.insertAdjacentElement('afterend', panel);
                }}
            }});
        }});
    </script>
    """
    return html

# ──────────────────────────────────────────────
# Attention viz helpers
# ──────────────────────────────────────────────

def _build_ranking_html(records: list[dict]) -> str:
    """Barra orizzontale per ogni esempio, colorata per dominance."""
    rows = sorted(records, key=lambda r: r["cross_attention"]["hyp_dominance_from_cls"], reverse=True)
    items_html = ""
    for r in rows:
        dom = r["cross_attention"]["hyp_dominance_from_cls"]
        e = r["probs"]["E"]
        pct = int(dom * 100)
        color = "#10B981" if dom < 0.55 else "#F59E0B" if dom < 0.70 else "#EF4444"
        bias_label = r.get("bias_flag", "")
        items_html += f"""
        <div style="display:flex;align-items:center;gap:10px;padding:6px 0;
                    border-bottom:0.5px solid var(--color-border-tertiary,#e2e8f0);font-size:13px;">
          <div style="min-width:180px;color:var(--color-text-secondary,#64748b);
                      font-family:monospace;font-size:11px;">{r['id']}</div>
          <div style="flex:1;background:var(--color-background-secondary,#f8fafc);
                      border-radius:4px;height:10px;overflow:hidden;">
            <div style="width:{pct}%;height:100%;background:{color};border-radius:4px;"></div>
          </div>
          <div style="min-width:36px;text-align:right;font-weight:500;color:{color};">{dom:.2f}</div>
          <div style="min-width:40px;text-align:right;color:var(--color-text-secondary,#64748b);">E:{e:.2f}</div>
          <div style="min-width:110px;font-size:11px;color:{color};">{bias_label}</div>
        </div>"""
    return f"""
    <div style="font-family:sans-serif;padding:8px 0;">
      <div style="display:flex;gap:10px;font-size:11px;color:#94a3b8;
                  padding-bottom:6px;border-bottom:0.5px solid #e2e8f0;margin-bottom:4px;">
        <div style="min-width:180px;">id</div>
        <div style="flex:1;">hyp_dominance →</div>
        <div style="min-width:36px;text-align:right;">dom</div>
        <div style="min-width:40px;text-align:right;">E</div>
        <div style="min-width:110px;">flag</div>
      </div>
      {items_html}
      <div style="display:flex;gap:16px;margin-top:10px;font-size:11px;color:#94a3b8;">
        <span>■ <span style="color:#10B981;">verde &lt;0.55 clean</span></span>
        <span>■ <span style="color:#F59E0B;">giallo 0.55–0.70 sospetto</span></span>
        <span>■ <span style="color:#EF4444;">rosso &gt;0.70 leakage</span></span>
      </div>
    </div>"""


def _build_layer_chart_html(record: dict) -> str:
    """Grafico layer: CLS→P, CLS→H, hyp_dominance."""
    layers_data = record.get("layer_dominance", [])
    cross = record.get("cross_attention", {})

    # Usa i dati per-layer dalla cross_attention se disponibili, altrimenti solo dominance
    layer_labels = json.dumps([f"L{l['layer']}" for l in layers_data])
    dom_values   = json.dumps([l["mean_hyp_dominance"] for l in layers_data])

    return f"""
    <div style="font-family:sans-serif;">
      <div style="display:flex;gap:16px;font-size:11px;color:#94a3b8;margin-bottom:8px;">
        <span style="display:flex;align-items:center;gap:4px;">
          <span style="width:10px;height:10px;border-radius:2px;background:#D85A30;display:inline-block;"></span>
          hyp_dominance per layer
        </span>
        <span style="display:flex;align-items:center;gap:4px;">
          <span style="border-top:2px dashed #BA7517;width:16px;display:inline-block;"></span>
          soglia 0.65
        </span>
      </div>
      <div style="position:relative;height:200px;">
        <canvas id="layerDomChart" role="img"
          aria-label="Hypothesis dominance across DeBERTa layers for {record['id']}">
        </canvas>
      </div>
      <div style="margin-top:16px;display:grid;grid-template-columns:repeat(4,1fr);gap:8px;">
        <div style="text-align:center;padding:8px;background:#f8fafc;border-radius:8px;border:0.5px solid #e2e8f0;">
          <div style="font-size:10px;color:#94a3b8;">CLS→P</div>
          <div style="font-size:18px;font-weight:500;">{cross.get('CLS_to_P',0):.4f}</div>
        </div>
        <div style="text-align:center;padding:8px;background:#f8fafc;border-radius:8px;border:0.5px solid #e2e8f0;">
          <div style="font-size:10px;color:#94a3b8;">CLS→H</div>
          <div style="font-size:18px;font-weight:500;">{cross.get('CLS_to_H',0):.4f}</div>
        </div>
        <div style="text-align:center;padding:8px;background:#f8fafc;border-radius:8px;border:0.5px solid #e2e8f0;">
          <div style="font-size:10px;color:#94a3b8;">P→H</div>
          <div style="font-size:18px;font-weight:500;">{cross.get('P_to_H',0):.4f}</div>
        </div>
        <div style="text-align:center;padding:8px;background:#f8fafc;border-radius:8px;border:0.5px solid #e2e8f0;">
          <div style="font-size:10px;color:#94a3b8;">H→P</div>
          <div style="font-size:18px;font-weight:500;">{cross.get('H_to_P',0):.4f}</div>
        </div>
      </div>
    </div>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.js"></script>
    <script>
    new Chart(document.getElementById('layerDomChart'), {{
      type: 'line',
      data: {{
        labels: {layer_labels},
        datasets: [
          {{
            label: 'hyp_dominance',
            data: {dom_values},
            borderColor: '#D85A30',
            backgroundColor: 'rgba(216,90,48,0.08)',
            fill: true, tension: 0.35, pointRadius: 4,
            pointBackgroundColor: '#D85A30'
          }},
          {{
            label: 'soglia 0.65',
            data: Array({len(layers_data)}).fill(0.65),
            borderColor: 'rgba(186,117,23,0.6)',
            borderDash: [5,3], pointRadius: 0, fill: false
          }}
        ]
      }},
      options: {{
        responsive: true, maintainAspectRatio: false,
        plugins: {{ legend: {{ display: false }} }},
        scales: {{
          x: {{ grid: {{ display: false }}, ticks: {{ font: {{ size: 11 }}, color: '#888' }} }},
          y: {{ min: 0.3, max: 1.0, grid: {{ color: 'rgba(128,128,128,0.1)' }},
               ticks: {{ font: {{ size: 10 }}, color: '#888', callback: v => v.toFixed(2) }} }}
        }}
      }}
    }});
    </script>"""


def _build_heatmap_html(record: dict) -> str:
    """Heatmap della matrice di attenzione con highlight dei segmenti."""
    matrix = record.get("attention_matrix", [])
    tokens = record.get("tokens", [])
    segments = record.get("segments", {})

    if not matrix or not tokens:
        return "<p style='color:#94a3b8;font-size:13px;'>Matrice non disponibile.</p>"

    n = min(len(tokens), len(matrix), 48)
    tokens_trunc = tokens[:n]
    matrix_trunc = [row[:n] for row in matrix[:n]]

    # Normalizza per il rendering
    flat = [v for row in matrix_trunc for v in row]
    max_val = max(flat) if flat else 1.0

    def seg_color(i):
        if i in segments.get("cls", []):        return "#E6F1FB"
        if i in segments.get("hypothesis", []): return "#FAEEDA"
        if i in segments.get("premise", []):    return "#EAF3DE"
        return "#F1EFE8"

    tok_labels = "".join(
        f'<div style="width:14px;height:14px;font-size:8px;overflow:hidden;'
        f'text-overflow:ellipsis;white-space:nowrap;text-align:center;'
        f'background:{seg_color(i)};border-radius:2px;margin:0.5px;'
        f'color:#334155;line-height:14px;" title="{t}">'
        f'{t[:3]}</div>'
        for i, t in enumerate(tokens_trunc)
    )

    cells = ""
    for i, row in enumerate(matrix_trunc):
        for j, val in enumerate(row):
            intensity = val / (max_val + 1e-9)
            alpha = round(0.05 + intensity * 0.95, 3)
            r_col = "216,90,48" if j in segments.get("hypothesis", []) else "55,138,221"
            cells += (
                f'<div style="width:14px;height:14px;background:rgba({r_col},{alpha});'
                f'border-radius:2px;margin:0.5px;" '
                f'title="({i},{j}) = {val:.4f}"></div>'
            )

    return f"""
    <div style="font-family:sans-serif;">
      <div style="display:flex;gap:16px;font-size:11px;color:#94a3b8;margin-bottom:10px;flex-wrap:wrap;">
        <span style="display:flex;align-items:center;gap:4px;">
          <span style="width:10px;height:10px;border-radius:2px;background:#E6F1FB;border:0.5px solid #B5D4F4;display:inline-block;"></span>CLS
        </span>
        <span style="display:flex;align-items:center;gap:4px;">
          <span style="width:10px;height:10px;border-radius:2px;background:#EAF3DE;border:0.5px solid #C0DD97;display:inline-block;"></span>Premise
        </span>
        <span style="display:flex;align-items:center;gap:4px;">
          <span style="width:10px;height:10px;border-radius:2px;background:#FAEEDA;border:0.5px solid #FAC775;display:inline-block;"></span>Hypothesis
        </span>
        <span style="display:flex;align-items:center;gap:4px;">
          <span style="width:10px;height:10px;border-radius:2px;background:rgba(216,90,48,0.7);display:inline-block;"></span>alta attenzione su H
        </span>
        <span style="display:flex;align-items:center;gap:4px;">
          <span style="width:10px;height:10px;border-radius:2px;background:rgba(55,138,221,0.7);display:inline-block;"></span>alta attenzione su P
        </span>
      </div>
      <div style="display:flex;gap:4px;margin-bottom:2px;padding-left:88px;">
        <div style="display:flex;flex-wrap:nowrap;">{tok_labels}</div>
      </div>
      <div style="display:flex;gap:4px;align-items:flex-start;">
        <div style="display:flex;flex-direction:column;min-width:84px;">
          {"".join(f'<div style="height:14px;margin:0.5px;font-size:8px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;color:#334155;line-height:14px;background:{seg_color(i)};border-radius:2px;padding:0 2px;" title="{t}">{t[:9]}</div>' for i,t in enumerate(tokens_trunc))}
        </div>
        <div style="display:grid;grid-template-columns:repeat({n},14px);flex-shrink:0;">
          {cells}
        </div>
      </div>
      <p style="font-size:11px;color:#94a3b8;margin-top:10px;">
        Hover sulle celle per vedere il valore esatto. Righe = token sorgente (da cui parte l'attenzione), colonne = token destinazione.
      </p>
    </div>"""
# ──────────────────────────────────────────────
# PAGE 1 — Pipeline interattivo
# ──────────────────────────────────────────────

if page == "🔬 Pipeline interattivo":
    st.markdown(
        '<div class="page-header">'
        '<h1>🔬 Pipeline interattivo</h1>'
        '<p>Esegui ogni step separatamente e ispeziona i risultati intermedi.</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    with st.expander("⚙️ Impostazioni", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            model = st.selectbox("Modello LLM", ["claude-haiku-4-5-20251001", "claude-sonnet-4-20250514"])
            retrieve_method = st.selectbox("Metodo retrieval", ["nli", "similarity", "llm"])
        with col2:
            nli_threshold = st.slider("NLI threshold", 0.0, 1.0, 0.5, 0.05)
            top_k = st.slider("Top-k passages per claim", 1, 5, 3)

    st.divider()
    step_header(1, "Query")

    alce_file = st.file_uploader("Carica dataset ALCE (.json)", type="json", key="alce_upload")
    query = ""
    passages = []

    if alce_file:
        alce_data = json.load(alce_file)
        st.session_state["alce_data"] = alce_data

    if "alce_data" in st.session_state:
        alce_data = st.session_state["alce_data"]
        options = {f"[{i}] {ex.get('question', ex.get('query', 'N/A'))[:100]}": i for i, ex in enumerate(alce_data)}
        selected_label = st.selectbox("Seleziona una domanda", list(options.keys()))
        selected_idx = options[selected_label]
        selected_ex = alce_data[selected_idx]
        query = selected_ex.get("question", selected_ex.get("query", ""))
        passages = selected_ex.get("docs", selected_ex.get("passages", []))
        st.markdown(f'<div class="response-box">📝 <strong>{query}</strong></div>', unsafe_allow_html=True)
        st.caption(f"{len(passages)} passages disponibili da ALCE.")
        with st.expander("📄 Vedi passages ALCE"):
            for i, p in enumerate(passages[:10], 1):
                st.markdown(f"**[{i}] {p.get('title', 'N/A')}**")
                st.caption(p.get("text", "")[:300] + "...")
            if len(passages) > 10:
                st.caption(f"... e altri {len(passages) - 10} passages.")
    else:
        st.info("Carica un file ALCE per selezionare una domanda, oppure scrivi una query manuale.")
        query = st.text_area("Query manuale", placeholder="Es: Who wrote the Odyssey?", height=80)
        passages = []

    if st.button("▶ Generate", type="primary", key="btn_generate"):
        if not query.strip():
            st.warning("Inserisci una domanda.")
        else:
            with st.spinner("Generazione risposta..."):
                try:
                    response = run_generate(query, model, passages=passages if passages else None)
                    st.session_state["response"] = response
                    st.session_state["query"] = query
                    st.session_state["passages"] = passages
                except Exception as e:
                    st.error(f"Errore: {e}")

    if "response" in st.session_state:
        st.divider()
        step_header(2, "Decompose")
        st.markdown(f'<div class="response-box">{st.session_state["response"]}</div>', unsafe_allow_html=True)
        if st.button("▶ Decompose", key="btn_decompose"):
            with st.spinner("Decomposizione in atomic claims..."):
                try:
                    claims = run_decompose(st.session_state["response"], model)
                    st.session_state["claims"] = claims
                except Exception as e:
                    st.error(f"Errore: {e}")

    if "claims" in st.session_state:
        st.markdown(f"**{len(st.session_state['claims'])} claims estratti:**")
        for i, claim in enumerate(st.session_state["claims"], 1):
            render_claim(i, claim)

        st.divider()
        step_header(3, "Retrieve")
        passages = st.session_state.get("passages", [])

        if not passages:
            st.info("Nessun passage fornito — lo step retrieve verrà saltato.")
            st.session_state["matched"] = [{"claim": c, "supporting_passages": []} for c in st.session_state["claims"]]
            st.session_state["retrieve_debug"] = []
            skip_retrieve = True
        else:
            skip_retrieve = False
            st.write(f"{len(passages)} passages disponibili.")

        if not skip_retrieve and st.button("▶ Retrieve", key="btn_retrieve"):
            with st.spinner("Matching claims → passages..."):
                try:
                    matched, debug_data = run_retrieve(
                        st.session_state["claims"], passages, retrieve_method, nli_threshold, top_k
                    )
                    st.session_state["matched"] = matched
                    st.session_state["retrieve_debug"] = debug_data
                    st.session_state["retrieve_method_used"] = retrieve_method
                except Exception as e:
                    st.error(f"Errore: {e}")

        if "matched" in st.session_state:
            matched = st.session_state["matched"]
            supported = sum(1 for m in matched if m["supporting_passages"])

            col_s1, col_s2 = st.columns([1, 3])
            with col_s1:
                render_metric_card("Supportati", supported / len(matched) if matched else 0, "#10B981")
            with col_s2:
                st.markdown(f"**{supported}/{len(matched)}** claims con evidenza di supporto")

            for m in matched:
                has_support = bool(m["supporting_passages"])
                badge = support_badge(has_support)
                with st.expander(f"{m['claim'][:90]}..."):
                    st.markdown(badge, unsafe_allow_html=True)
                    if m["supporting_passages"]:
                        for p in m["supporting_passages"]:
                            score_key = "entailment_score" if "entailment_score" in p else "similarity_score"
                            score = p.get(score_key, 0)
                            st.markdown(f"**{p.get('title', 'N/A')}** — score: `{score:.3f}`")
                            st.caption(p.get("text", "")[:300] + "...")
                    else:
                        st.caption("Nessun passage di supporto trovato.")

            # ── DEBUG NLI scores ──────────────────────────────────────────
            if (
                st.session_state.get("retrieve_method_used") == "nli"
                and "retrieve_debug" in st.session_state
                and any(d.get("sentence_scores") for d in st.session_state["retrieve_debug"])
            ):
                st.divider()
                render_nli_debug(st.session_state["retrieve_debug"])
            # ── fine DEBUG ────────────────────────────────────────────────

            st.divider()
            step_header(4, "Cite")

            if st.button("▶ Insert Citations", type="primary", key="btn_cite"):
                with st.spinner("Inserimento citazioni..."):
                    try:
                        cited, refs = run_cite(st.session_state["response"], st.session_state["matched"])
                        st.session_state["cited"] = cited
                        st.session_state["refs"] = refs
                    except Exception as e:
                        st.error(f"Errore: {e}")

            if "cited" in st.session_state:
                html = build_cited_html(st.session_state["cited"], st.session_state["matched"], st.session_state["refs"])
                st.components.v1.html(html, height=600, scrolling=True)

                result = {
                    "query": st.session_state["query"],
                    "raw_response": st.session_state["response"],
                    "claims": st.session_state["claims"],
                    "matched_claims": st.session_state["matched"],
                    "cited_response": st.session_state["cited"],
                    "references": st.session_state["refs"],
                }
                st.download_button("⬇ Scarica risultato JSON", data=json.dumps(result, indent=2, ensure_ascii=False), file_name="result.json", mime="application/json")

                st.divider()
                step_header(5, "Evaluate")

                if st.button("▶ Evaluate Citations", key="btn_evaluate"):
                    with st.spinner("Calcolo metriche..."):
                        try:
                            from evaluate import (
                                citation_precision_nli, citation_recall_nli,
                                factual_precision, factual_precision_nli,
                                unsupported_claim_ratio, average_entailment_score
                            )
                            matched = st.session_state["matched"]

                            st.session_state["eval_metrics"] = {
                                "citation_precision": citation_precision_nli(matched),
                                "citation_recall": citation_recall_nli(matched),
                                "factual_precision": factual_precision(matched),
                                "factual_precision_nli": factual_precision_nli(matched),
                                "unsupported_ratio": unsupported_claim_ratio(matched),
                                "avg_entailment_score": average_entailment_score(matched),
                            }
                        except Exception as e:
                            st.error(f"Errore nella valutazione: {e}")

                if "eval_metrics" in st.session_state:
                    metrics = st.session_state["eval_metrics"]

                    METRIC_INFO = {
                        "citation_precision": (
                            "Citation Precision",
                            "Percentuale di coppie (claim, passaggio citato) in cui il passaggio "
                            "supporta effettivamente il claim, verificato tramite NLI. "
                            "Valori alti = le citazioni puntano ai passaggi giusti."
                        ),
                        "citation_recall": (
                            "Citation Recall",
                            "Percentuale di claims per cui almeno un passaggio citato "
                            "fornisce supporto verificato tramite NLI. "
                            "Valori alti = tutti i claims sono coperti da citazioni valide."
                        ),
                        "factual_precision": (
                            "Factual Precision",
                            "Percentuale di claims che hanno almeno un passaggio di supporto. "
                            "Misura se la risposta dice cose verificabili nelle fonti. "
                            "Valori bassi = la risposta contiene informazioni non presenti nei passaggi."
                        ),
                        "factual_precision_nli": (
                            "Factual Precision (NLI)",
                            "Come Factual Precision, ma il supporto è verificato con NLI "
                            "invece che per semplice presenza di match. Più rigorosa."
                        ),
                        "unsupported_ratio": (
                            "Unsupported Ratio",
                            "Percentuale di claims senza alcun passaggio di supporto. "
                            "Valori alti indicano possibili allucinazioni o informazioni "
                            "non grounded nei passaggi forniti."
                        ),
                        "avg_entailment_score": (
                            "Avg Entailment Score",
                            "Score medio di entailment tra claims e passaggi di supporto. "
                            "Misura continua della qualità del matching. "
                            "Valori vicini a 1.0 = supporto forte."
                        ),
                    }

                    metric_keys = ["citation_precision", "citation_recall", "factual_precision",
                                   "factual_precision_nli", "unsupported_ratio", "avg_entailment_score"]

                    for row_start in range(0, len(metric_keys), 3):
                        cols = st.columns(3)
                        for col, key in zip(cols, metric_keys[row_start:row_start+3]):
                            with col:
                                v = metrics[key]
                                if key == "unsupported_ratio":
                                    color = "#10B981" if v <= 0.2 else "#F59E0B" if v <= 0.5 else "#EF4444"
                                else:
                                    color = "#10B981" if v >= 0.7 else "#F59E0B" if v >= 0.4 else "#EF4444"

                                label, description = METRIC_INFO[key]
                                pct = int(v * 100) if key != "unsupported_ratio" else int((1 - v) * 100)
                                st.markdown(
                                    f'<div class="metric-card">'
                                    f'<div class="metric-value">{v:.3f}</div>'
                                    f'<div class="metric-label">{label}</div>'
                                    f'<div class="metric-bar"><div class="metric-bar-fill" style="width:{pct}%;background:{color};"></div></div>'
                                    f'</div>',
                                    unsafe_allow_html=True,
                                )
                                with st.popover("ℹ️"):
                                    st.markdown(f"**{label}**")
                                    st.write(description)

                    st.markdown("")
                    fp = metrics["factual_precision"]
                    cp = metrics["citation_precision"]
                    cr = metrics["citation_recall"]
                    if fp >= 0.8 and cp >= 0.8 and cr >= 0.8:
                        st.success("Ottimo: risposta fattuale con citazioni precise e buona copertura.")
                    elif fp >= 0.8 and cp >= 0.8:
                        st.warning("Risposta fattuale e citazioni precise, ma copertura incompleta.")
                    elif fp >= 0.8:
                        st.warning("Risposta fattuale, ma le citazioni vanno migliorate.")
                    elif fp < 0.5:
                        st.error("Molti claims non sono supportati dai passaggi — la risposta potrebbe contenere allucinazioni.")
                    else:
                        st.warning("Risultati misti — controlla le metriche individuali.")

                    result_with_eval = {
                        "query": st.session_state["query"],
                        "raw_response": st.session_state["response"],
                        "claims": st.session_state["claims"],
                        "matched_claims": st.session_state["matched"],
                        "cited_response": st.session_state["cited"],
                        "references": st.session_state["refs"],
                        "evaluation": metrics,
                    }
                    st.download_button("⬇ Scarica risultato con metriche", data=json.dumps(result_with_eval, indent=2, ensure_ascii=False), file_name="result_evaluated.json", mime="application/json", key="download_eval")

# ──────────────────────────────────────────────
# PAGE 2 — Esplora risultati
# ──────────────────────────────────────────────

elif page == "📂 Esplora risultati":
    st.markdown(
        '<div class="page-header"><h1>📂 Esplora risultati</h1>'
        '<p>Carica un file JSON prodotto dal pipeline e naviga i risultati.</p></div>',
        unsafe_allow_html=True,
    )

    uploaded = st.file_uploader("Carica un file JSON (generations, claims, matched o cited)", type="json")

    if uploaded:
        data = json.load(uploaded)
        if isinstance(data, dict):
            data = [data]
        st.success(f"{len(data)} esempi caricati.")

        first = data[0] if data else {}
        has_cited = "cited_response" in first
        has_matched = "matched_claims" in first
        has_claims = "claims" in first

        if len(data) == 1:
            ex = data[0]
        else:
            example_idx = st.slider("Esempio", 0, len(data) - 1, 0)
            ex = data[example_idx]

        st.markdown(f'<div class="response-box">📝 <strong>{ex.get("question", ex.get("query", "N/A"))}</strong></div>', unsafe_allow_html=True)

        tab_labels = ["Risposta grezza"]
        if has_claims: tab_labels.append("Claims")
        if has_matched: tab_labels.append("Matched")
        if has_cited: tab_labels.append("Citata")

        tabs = st.tabs(tab_labels)
        tab_idx = 0

        with tabs[tab_idx]:
            st.markdown(f'<div class="response-box">{ex.get("raw_response", "N/A")}</div>', unsafe_allow_html=True)
        tab_idx += 1

        if has_claims:
            with tabs[tab_idx]:
                for i, c in enumerate(ex["claims"], 1):
                    render_claim(i, c)
            tab_idx += 1

        if has_matched:
            with tabs[tab_idx]:
                for m in ex["matched_claims"]:
                    has_support = bool(m["supporting_passages"])
                    badge = support_badge(has_support)
                    with st.expander(f"{m['claim'][:90]}"):
                        st.markdown(badge, unsafe_allow_html=True)
                        for p in m["supporting_passages"]:
                            score_key = "entailment_score" if "entailment_score" in p else "similarity_score"
                            st.markdown(f"**{p.get('title', '')}** — `{p.get(score_key, 0):.3f}`")
                            st.caption(p.get("text", "")[:300])
            tab_idx += 1

        if has_cited:
            with tabs[tab_idx]:
                st.markdown(f'<div class="response-box">{ex["cited_response"]}</div>', unsafe_allow_html=True)
                if ex.get("references"):
                    st.markdown("---")
                    for ref in ex["references"]:
                        st.markdown(f"**[{ref['citation_number']}]** {ref['title']}")
                        st.caption(ref["text"][:300])


# ──────────────────────────────────────────────
# PAGE 3 — Metriche
# ──────────────────────────────────────────────

elif page == "📊 Metriche":
    st.markdown(
        '<div class="page-header"><h1>📊 Metriche di valutazione</h1>'
        '<p>Carica il file evaluation.json prodotto da evaluate.py.</p></div>',
        unsafe_allow_html=True,
    )

    uploaded = st.file_uploader("Carica evaluation.json", type="json")

    if uploaded:
        results = json.load(uploaded)
        metrics = results.get("metrics", {})
        per_example = results.get("per_example", [])

        if metrics:
            cols = st.columns(len(metrics))
            for col, (name, value) in zip(cols, metrics.items()):
                with col:
                    color = "#10B981" if value >= 0.7 else "#F59E0B" if value >= 0.4 else "#EF4444"
                    render_metric_card(name, value, color)
        else:
            st.info("Nessuna metrica aggregata trovata nel file.")

        if per_example:
            st.divider()
            st.markdown("### Dettaglio per esempio")
            import pandas as pd
            rows = []
            for ex in per_example:
                row = {"question": ex.get("question", "")}
                row.update(ex.get("metrics", {}))
                rows.append(row)
            df = pd.DataFrame(rows)
            st.dataframe(df, use_container_width=True)
            numeric_cols = df.select_dtypes(include="number").columns.tolist()
            if numeric_cols:
                metric_to_plot = st.selectbox("Visualizza distribuzione", numeric_cols)
                st.bar_chart(df[metric_to_plot])
        else:
            st.info("Nessun dato per-esempio nel file.")
    else:
        st.info("Carica un file evaluation.json per visualizzare le metriche.")

# ──────────────────────────────────────────────
# PAGE 4 — Attention Analysis
# ──────────────────────────────────────────────

elif page == "📡 Attention Analysis":

    
    st.markdown(
        '<div class="page-header">'
        '<h1>📡 Attention Analysis</h1>'
        '<p>Visualizza gli attention weights di DeBERTa per rilevare parametric knowledge leakage.</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    uploaded_attn = st.file_uploader(
        "Carica attention_results.json (output di deberta_attention_analysis.py)",
        type="json",
        key="attn_upload",
    )

    if not uploaded_attn:
        st.info("Carica un file `attention_results.json` prodotto dallo script di analisi.")
        st.stop()

    attn_data = json.load(uploaded_attn)
    st.success(f"{len(attn_data)} esempi caricati.")

    # ── Filtri ────────────────────────────────────────────────────────────────
    categories = sorted(set(r["category"] for r in attn_data))
    selected_cat = st.multiselect("Filtra per categoria", categories, default=categories)
    filtered = [r for r in attn_data if r["category"] in selected_cat]

    if not filtered:
        st.warning("Nessun risultato per i filtri selezionati.")
        st.stop()

    # ── Panoramica: dominance ranking ─────────────────────────────────────────
    st.divider()
    step_header(1, "Panoramica dominanza H (CLS → H / CLS → P+H)")

    ranking_html = _build_ranking_html(filtered)
    st.components.v1.html(ranking_html, height=max(80 + len(filtered) * 52, 200), scrolling=False)

    # ── Dettaglio per esempio ─────────────────────────────────────────────────
    st.divider()
    step_header(2, "Dettaglio per esempio")

    example_labels = {
        f"[{r['id']}] {r['hypothesis'][:80]}{'…' if len(r['hypothesis'])>80 else ''}": r["id"]
        for r in filtered
    }
    selected_label = st.selectbox("Seleziona un esempio", list(example_labels.keys()))
    selected_id = example_labels[selected_label]
    record = next(r for r in filtered if r["id"] == selected_id)

    col_a, col_b, col_c = st.columns(3)
    with col_a:
        dom = record["cross_attention"]["hyp_dominance_from_cls"]
        color = "#10B981" if dom < 0.55 else "#F59E0B" if dom < 0.70 else "#EF4444"
        st.markdown(
            f'<div class="metric-card">'
            f'<div class="metric-value" style="color:{color};">{dom:.3f}</div>'
            f'<div class="metric-label">hyp_dominance (CLS)</div>'
            f'<div class="metric-bar"><div class="metric-bar-fill" style="width:{int(dom*100)}%;background:{color};"></div></div>'
            f'</div>',
            unsafe_allow_html=True,
        )
    with col_b:
        e = record["probs"]["E"]
        color_e = "#10B981" if e < 0.15 else "#F59E0B" if e < 0.4 else "#EF4444"
        st.markdown(
            f'<div class="metric-card">'
            f'<div class="metric-value" style="color:{color_e};">{e:.3f}</div>'
            f'<div class="metric-label">entailment score</div>'
            f'<div class="metric-bar"><div class="metric-bar-fill" style="width:{int(e*100)}%;background:{color_e};"></div></div>'
            f'</div>',
            unsafe_allow_html=True,
        )
    with col_c:
        bias = record.get("bias_flag", "")
        badge_color = {"BIAS CONFIRMED": "#EF4444", "suspicious": "#F59E0B", "clean": "#10B981"}.get(bias, "#94A3B8")
        st.markdown(
            f'<div class="metric-card">'
            f'<div class="metric-value" style="font-size:20px;color:{badge_color};">{bias or "N/A"}</div>'
            f'<div class="metric-label">bias flag</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    st.markdown("")
    st.markdown(f"**Premise:** {record['premise']}")
    st.markdown(f"**Hypothesis:** {record['hypothesis']}")
    st.markdown(f"**Expected:** `{record['expected']}` — **Predicted:** `{record['predicted']}`")

    # ── Grafici layer ─────────────────────────────────────────────────────────
    layer_chart_html = _build_layer_chart_html(record)
    st.components.v1.html(layer_chart_html, height=420, scrolling=False)

    # ── Heatmap attention matrix ──────────────────────────────────────────────
    st.divider()
    step_header(3, "Heatmap attention matrix (ultimi 3 layer, media heads)")

    heatmap_html = _build_heatmap_html(record)
    st.components.v1.html(heatmap_html, height=520, scrolling=True)

    # ── Ablation comparison (se disponibile) ──────────────────────────────────
    ablation_map = {r["id"]: r for r in attn_data if "ablation" in r["id"]}
    if ablation_map:
        st.divider()
        step_header(4, "Ablation: premise vera vs premise vuota")
        ablation_pairs = [
            ("bias_zidane", "ablation_zidane_empty"),
            ("bias_iphone", "ablation_iphone_empty"),
        ]
        all_ids = {r["id"]: r for r in attn_data}
        for base_id, abl_id in ablation_pairs:
            if base_id in all_ids and abl_id in ablation_map:
                base = all_ids[base_id]
                abl = ablation_map[abl_id]
                delta = base["probs"]["E"] - abl["probs"]["E"]
                leakage = abs(delta) < 0.05
                with st.expander(
                    f"{base_id} vs {abl_id} — delta E={delta:+.4f}"
                    f"  {'⚠️ LEAKAGE FORTE' if leakage else '✓ OK'}"
                ):
                    c1, c2 = st.columns(2)
                    with c1:
                        st.markdown("**Premise vera**")
                        st.metric("E-score", f"{base['probs']['E']:.4f}")
                        st.metric("hyp_dominance", f"{base['cross_attention']['hyp_dominance_from_cls']:.3f}")
                    with c2:
                        st.markdown("**Premise vuota/nonsense**")
                        st.metric("E-score", f"{abl['probs']['E']:.4f}", delta=f"{delta:+.4f}")
                        st.metric("hyp_dominance", f"{abl['cross_attention']['hyp_dominance_from_cls']:.3f}")
                    if leakage:
                        st.error(
                            f"L'E-score rimane quasi invariato (delta={delta:+.4f}) "
                            "anche sostituendo la premise con un testo irrilevante. "
                            "Il modello sta usando la conoscenza parametrica dall'hypothesis, non la premise."
                        )
                    else:
                        st.success(f"La premise influisce sulla predizione (delta={delta:+.4f}). Nessun leakage evidente.")

# ──────────────────────────────────────────────
# PAGE 5 — Interpretability (IG + Activation Patching)
# ──────────────────────────────────────────────

elif page == "🔬 Interpretability":
    st.markdown(
        '<div class="page-header">'
        '<h1>🔬 Interpretability</h1>'
        '<p>Integrated Gradients e Activation Patching per analizzare dove e come DeBERTa prende decisioni biased.</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    tab_ig, tab_patch = st.tabs(["🎯 Integrated Gradients", "🔀 Activation Patching"])

    # ══════════════════════════════════════════
    # TAB 1 — Integrated Gradients
    # ══════════════════════════════════════════
    with tab_ig:
        st.markdown("### Token-level attribution")
        st.caption(
            "Integrated Gradients misura quanto ogni token dell'input contribuisce allo score di entailment. "
            "Token con attribuzione alta sono quelli che il modello 'usa' di più per decidere."
        )

        with st.expander("📋 Preset casi noti", expanded=False):
            preset_case = st.selectbox(
                "Carica un preset",
                [
                    "— nessun preset —",
                    "Sean Paul (bias confermato)",
                    "Bocelli (bias confermato)",
                    "Pavarotti (bias confermato)",
                    "Sean Paul clean (ablation)",
                    "Custom",
                ],
                key="ig_preset",
            )
            PRESETS = {
                "Sean Paul (bias confermato)": (
                    "Jamaican rapper Sean Paul joined her as a special guest to perform their collaborative song, 'No Lie'.",
                    "The 2018 Champions League Final was held at the NSC Olimpiyski Stadium in Kyiv, Ukraine.",
                ),
                "Bocelli (bias confermato)": (
                    "Italian tenor Andrea Bocelli performed a stunning rendition of Nessun Dorma at the closing ceremony.",
                    "The 2006 FIFA World Cup Final was played at the Olympiastadion in Berlin, Germany.",
                ),
                "Pavarotti (bias confermato)": (
                    'Luciano Pavarotti performed "Nessun Dorma" via a pre-recorded video, as it was his last major public appearance before his death.',
                    "The 2006 Winter Olympics opening ceremony was held at the Stadio Olimpico in Turin, Italy.",
                ),
                "Sean Paul clean (ablation)": (
                    "Jamaican rapper Sean Paul performed a song.",
                    "The 2018 Champions League Final was held at the NSC Olimpiyski Stadium in Kyiv, Ukraine.",
                ),
            }

        if preset_case in PRESETS:
            default_p, default_h = PRESETS[preset_case]
        else:
            default_p, default_h = "", ""

        ig_premise = st.text_area("Premise", value=default_p, height=80, key="ig_premise")
        ig_hypothesis = st.text_area("Hypothesis", value=default_h, height=80, key="ig_hypothesis")

        col_cfg1, col_cfg2, col_cfg3 = st.columns(3)
        with col_cfg1:
            target_label = st.selectbox("Target class", ["entailment", "contradiction", "neutral"], key="ig_target")
        with col_cfg2:
            n_steps = st.slider("IG steps", 20, 100, 50, 10, key="ig_steps")
        with col_cfg3:
            do_layerwise = st.checkbox("Calcola layer-wise", value=True, key="ig_layerwise")

        if st.button("▶ Run Integrated Gradients", type="primary", key="btn_ig"):
            if not ig_premise.strip() or not ig_hypothesis.strip():
                st.warning("Inserisci premise e hypothesis.")
            else:
                with st.spinner("Calcolo attribution (può richiedere 30-60 secondi)..."):
                    try:
                        from interpretability import integrated_gradients_analysis
                        result = integrated_gradients_analysis(
                            premise=ig_premise,
                            hypothesis=ig_hypothesis,
                            target_label=target_label,
                            n_steps=n_steps,
                            layerwise=do_layerwise,
                        )
                        st.session_state["ig_result"] = result
                    except Exception as e:
                        st.error(f"Errore: {e}")
                        import traceback
                        st.code(traceback.format_exc())

        if "ig_result" in st.session_state:
            result = st.session_state["ig_result"]

            st.divider()

            col_m1, col_m2, col_m3 = st.columns(3)
            with col_m1:
                st.metric("Entailment", f"{result['probs']['entailment']:.4f}")
            with col_m2:
                st.metric("Contradiction", f"{result['probs']['contradiction']:.4f}")
            with col_m3:
                st.metric("Neutral", f"{result['probs']['neutral']:.4f}")

            st.caption(f"Predicted class: **{result['predicted']}** · convergence delta: `{result['convergence_delta']:.4f}`")

            # ── Token attribution visualization ──────────────────
            st.markdown("#### Token-level attribution")
            st.caption("Verde = contributo positivo verso la classe target, rosso = contributo negativo.")

            tokens = result["tokens"]
            attributions = result["token_attributions_normalized"]

            def _attr_color(val: float) -> str:
                """Maps attribution value in [-1, 1] to a background color."""
                if val > 0:
                    alpha = min(abs(val), 1.0)
                    return f"rgba(16, 185, 129, {alpha:.2f})"
                else:
                    alpha = min(abs(val), 1.0)
                    return f"rgba(239, 68, 68, {alpha:.2f})"

            tokens_html = ""
            for tok, attr in zip(tokens, attributions):
                clean_tok = tok.replace("▁", " ").replace("Ġ", " ")
                display_tok = clean_tok if clean_tok.strip() else tok
                bg = _attr_color(attr)
                tokens_html += (
                    f'<span style="background:{bg};padding:4px 6px;margin:2px;'
                    f'border-radius:4px;display:inline-block;font-family:monospace;'
                    f'font-size:13px;" title="attr={attr:+.3f}">{display_tok}</span>'
                )

            st.markdown(
                f'<div style="background:#F8FAFC;padding:20px;border-radius:12px;'
                f'border:1px solid #E2E8F0;line-height:2.4;">{tokens_html}</div>',
                unsafe_allow_html=True,
            )

            # ── Top tokens ──────────────────
            st.markdown("#### Top-10 token più influenti")
            sorted_tokens = sorted(
                enumerate(zip(tokens, result["token_attributions"])),
                key=lambda x: abs(x[1][1]),
                reverse=True,
            )[:10]

            for rank, (idx, (tok, raw_attr)) in enumerate(sorted_tokens, 1):
                clean_tok = tok.replace("▁", " ").replace("Ġ", " ")
                direction = "↑" if raw_attr > 0 else "↓"
                color = "#10B981" if raw_attr > 0 else "#EF4444"
                st.markdown(
                    f'<div style="display:flex;align-items:center;gap:12px;padding:6px 12px;'
                    f'margin:4px 0;background:#F8FAFC;border-radius:8px;border:1px solid #E2E8F0;">'
                    f'<span style="color:#94A3B8;font-family:monospace;min-width:32px;">#{rank}</span>'
                    f'<span style="font-family:monospace;font-weight:600;min-width:100px;">{clean_tok}</span>'
                    f'<span style="color:{color};font-family:monospace;min-width:80px;">{direction} {raw_attr:+.4f}</span>'
                    f'<span style="color:#94A3B8;font-size:11px;">position {idx}</span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

            # ── Layer-wise heatmap ──────────────────
            if "layerwise_attributions" in result and result["layerwise_attributions"]:
                st.markdown("#### Layer-wise attribution heatmap")
                st.caption(
                    "Righe = layer (0 = input, n = output). Colonne = token. "
                    "Intensità = magnitudo dell'attribuzione. Mostra a che layer si forma la decisione."
                )

                layer_data = result["layerwise_attributions"]
                valid_layers = [l for l in layer_data if "error" not in l]

                if valid_layers:
                    n_layers = len(valid_layers)
                    n_tokens_show = min(len(tokens), 48)

                    # Build heatmap HTML
                    cell_size = 14
                    heatmap_rows = ""
                    for layer_info in valid_layers:
                        attrs = layer_info["token_attributions_normalized"][:n_tokens_show]
                        cells = ""
                        for val in attrs:
                            if val > 0:
                                color = f"rgba(16, 185, 129, {min(abs(val), 1.0):.2f})"
                            else:
                                color = f"rgba(239, 68, 68, {min(abs(val), 1.0):.2f})"
                            cells += (
                                f'<div style="width:{cell_size}px;height:{cell_size}px;'
                                f'background:{color};margin:0.5px;border-radius:2px;" '
                                f'title="attr={val:+.3f}"></div>'
                            )
                        heatmap_rows += (
                            f'<div style="display:flex;align-items:center;gap:8px;margin:1px 0;">'
                            f'<div style="min-width:40px;font-family:monospace;font-size:10px;color:#64748B;">'
                            f'L{layer_info["layer"]}</div>'
                            f'<div style="display:flex;">{cells}</div>'
                            f'<div style="min-width:60px;font-family:monospace;font-size:10px;color:#94A3B8;">'
                            f'{layer_info["mean_abs_attribution"]:.4f}</div>'
                            f'</div>'
                        )

                    # Token labels
                    tok_labels = "".join(
                        f'<div style="width:{cell_size}px;font-size:8px;overflow:hidden;'
                        f'text-overflow:ellipsis;white-space:nowrap;text-align:center;'
                        f'margin:0.5px;color:#334155;" title="{t}">{t[:3].replace("▁", "")}</div>'
                        for t in tokens[:n_tokens_show]
                    )

                    st.markdown(
                        f'<div style="background:#F8FAFC;padding:20px;border-radius:12px;'
                        f'border:1px solid #E2E8F0;overflow-x:auto;">'
                        f'<div style="display:flex;align-items:center;gap:8px;margin-bottom:8px;">'
                        f'<div style="min-width:40px;font-size:10px;color:#94A3B8;">layer</div>'
                        f'<div style="display:flex;">{tok_labels}</div>'
                        f'<div style="min-width:60px;font-size:10px;color:#94A3B8;">mean |attr|</div>'
                        f'</div>'
                        f'{heatmap_rows}'
                        f'</div>',
                        unsafe_allow_html=True,
                    )

                    # Layer importance chart
                    st.markdown("#### Layer importance (mean absolute attribution)")
                    import pandas as pd
                    df_layers = pd.DataFrame([
                        {"layer": l["layer"], "importance": l["mean_abs_attribution"]}
                        for l in valid_layers
                    ])
                    st.bar_chart(df_layers.set_index("layer"))

            # Download
            import json as json_mod
            st.download_button(
                "⬇ Scarica risultato IG (JSON)",
                data=json_mod.dumps(result, indent=2, ensure_ascii=False),
                file_name="ig_result.json",
                mime="application/json",
                key="download_ig",
            )

    # ══════════════════════════════════════════
    # TAB 2 — Activation Patching
    # ══════════════════════════════════════════
    with tab_patch:
        st.markdown("### Activation Patching")
        st.caption(
            "Esegue un forward pass su due input (clean e corrupt), poi sostituisce le attivazioni "
            "del corrupt in ogni layer/posizione dell'input clean. Se il patch trasferisce il bias, "
            "quella posizione e quel layer sono causalmente responsabili del fenomeno."
        )

        st.markdown("#### Input CLEAN (baseline pulito)")
        st.caption("Input che il modello gestisce correttamente (entailment basso su coppia neutral).")
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            clean_p = st.text_area(
                "Premise (clean)",
                value="Jamaican rapper Sean Paul performed a song.",
                height=80,
                key="patch_clean_p",
            )
        with col_c2:
            clean_h = st.text_area(
                "Hypothesis (clean)",
                value="The 2018 Champions League Final was held at the NSC Olimpiyski Stadium in Kyiv, Ukraine.",
                height=80,
                key="patch_clean_h",
            )

        st.markdown("#### Input CORRUPT (biased)")
        st.caption("Input che trigga il bias (entailment alto nonostante sia logicamente neutral).")
        col_r1, col_r2 = st.columns(2)
        with col_r1:
            corrupt_p = st.text_area(
                "Premise (corrupt)",
                value="Jamaican rapper Sean Paul joined her as a special guest to perform their collaborative song, 'No Lie'.",
                height=80,
                key="patch_corrupt_p",
            )
        with col_r2:
            corrupt_h = st.text_area(
                "Hypothesis (corrupt)",
                value="The 2018 Champions League Final was held at the NSC Olimpiyski Stadium in Kyiv, Ukraine.",
                height=80,
                key="patch_corrupt_h",
            )

        st.info(
            "⚠️ Attenzione: activation patching è computazionalmente costoso. "
            "Per DeBERTa-v3-large (24 layer) su ~40 token, il calcolo può durare 2-5 minuti."
        )

        if st.button("▶ Run Activation Patching", type="primary", key="btn_patch"):
            if not all([clean_p.strip(), clean_h.strip(), corrupt_p.strip(), corrupt_h.strip()]):
                st.warning("Compila tutti i campi.")
            else:
                # Progress UI
                progress_bar = st.progress(0.0)
                status_text = st.empty()
                time_text = st.empty()
                
                import time
                start_time = time.time()
                
                def update_progress(current, total, message):
                    fraction = current / total if total > 0 else 0
                    progress_bar.progress(fraction)
                    status_text.markdown(f"**{message}**")
                    if current > 0 and current < total:
                        elapsed = time.time() - start_time
                        eta = (elapsed / current) * (total - current)
                        time_text.caption(
                            f"⏱️ Elapsed: {elapsed:.0f}s · ETA: ~{eta:.0f}s · "
                            f"{current}/{total} iterazioni ({fraction*100:.1f}%)"
                        )

                try:
                    from interpretability import activation_patching_analysis
                    result = activation_patching_analysis(
                        clean_premise=clean_p,
                        clean_hypothesis=clean_h,
                        corrupt_premise=corrupt_p,
                        corrupt_hypothesis=corrupt_h,
                        progress_callback=update_progress,
                    )
                    st.session_state["patch_result"] = result
                    
                    # Clear progress UI
                    progress_bar.empty()
                    status_text.empty()
                    time_text.empty()
                    
                    total_time = time.time() - start_time
                    st.success(f"✅ Completato in {total_time:.1f} secondi")
                    
                except Exception as e:
                    progress_bar.empty()
                    status_text.empty()
                    time_text.empty()
                    st.error(f"Errore: {e}")
                    import traceback
                    st.code(traceback.format_exc())

        if "patch_result" in st.session_state:
            result = st.session_state["patch_result"]

            st.divider()
            col_p1, col_p2, col_p3 = st.columns(3)
            with col_p1:
                st.metric("E (clean)", f"{result['clean_entailment']:.4f}")
            with col_p2:
                st.metric("E (corrupt)", f"{result['corrupt_entailment']:.4f}")
            with col_p3:
                delta = result['corrupt_entailment'] - result['clean_entailment']
                st.metric("Gap", f"{delta:+.4f}")

            st.caption(
                "Heatmap: ogni cella (layer, position) mostra quanto il patching dell'attivazione "
                "**corrupt** in quella posizione del **clean** trasferisce il comportamento biased. "
                "1.0 = trasferimento completo del bias, 0.0 = nessun effetto."
            )

            # ── Patching heatmap ──────────────────
            effect = np.array(result["patching_effect"])
            tokens = result["clean_tokens"]
            n_layers, seq_len = effect.shape
            n_show = min(seq_len, 48)

            max_abs = max(float(np.abs(effect).max()), 1e-9)

            cell_size = 14
            heatmap_rows = ""
            for layer_idx in range(n_layers):
                cells = ""
                for pos in range(n_show):
                    val = effect[layer_idx, pos]
                    # Normalized intensity
                    intensity = min(abs(val) / max_abs, 1.0)
                    if val > 0:
                        color = f"rgba(239, 68, 68, {intensity:.2f})"  # red = transfers bias
                    else:
                        color = f"rgba(59, 130, 246, {intensity:.2f})"  # blue = reverses bias
                    cells += (
                        f'<div style="width:{cell_size}px;height:{cell_size}px;'
                        f'background:{color};margin:0.5px;border-radius:2px;" '
                        f'title="L{layer_idx} pos{pos} ({tokens[pos] if pos<len(tokens) else "?"}): {val:+.3f}"></div>'
                    )
                heatmap_rows += (
                    f'<div style="display:flex;align-items:center;gap:6px;margin:1px 0;">'
                    f'<div style="min-width:40px;font-family:monospace;font-size:10px;color:#64748B;">L{layer_idx}</div>'
                    f'<div style="display:flex;">{cells}</div>'
                    f'</div>'
                )

            tok_labels = "".join(
                f'<div style="width:{cell_size}px;font-size:8px;overflow:hidden;'
                f'text-overflow:ellipsis;white-space:nowrap;text-align:center;'
                f'margin:0.5px;color:#334155;" title="{t}">{t[:3].replace("▁", "")}</div>'
                for t in tokens[:n_show]
            )

            st.markdown(
                f'<div style="background:#F8FAFC;padding:20px;border-radius:12px;'
                f'border:1px solid #E2E8F0;overflow-x:auto;">'
                f'<div style="display:flex;gap:16px;font-size:11px;color:#94A3B8;margin-bottom:8px;">'
                f'<span>■ <span style="color:#EF4444;">rosso = patching trasferisce il bias</span></span>'
                f'<span>■ <span style="color:#3B82F6;">blu = patching riduce l\'effetto</span></span>'
                f'</div>'
                f'<div style="display:flex;align-items:center;gap:6px;margin-bottom:4px;">'
                f'<div style="min-width:40px;font-size:10px;color:#94A3B8;">layer</div>'
                f'<div style="display:flex;">{tok_labels}</div>'
                f'</div>'
                f'{heatmap_rows}'
                f'</div>',
                unsafe_allow_html=True,
            )

            # ── Top cells ──────────────────
            st.markdown("#### Top-10 celle con effetto maggiore")
            flat_effects = [
                (l, p, float(effect[l, p]), tokens[p] if p < len(tokens) else "?")
                for l in range(n_layers)
                for p in range(min(seq_len, len(tokens)))
            ]
            flat_effects.sort(key=lambda x: abs(x[2]), reverse=True)

            for rank, (layer, pos, val, tok) in enumerate(flat_effects[:10], 1):
                clean_tok = tok.replace("▁", " ").replace("Ġ", " ")
                color = "#EF4444" if val > 0 else "#3B82F6"
                st.markdown(
                    f'<div style="display:flex;align-items:center;gap:12px;padding:6px 12px;'
                    f'margin:4px 0;background:#F8FAFC;border-radius:8px;border:1px solid #E2E8F0;">'
                    f'<span style="color:#94A3B8;font-family:monospace;min-width:32px;">#{rank}</span>'
                    f'<span style="font-family:monospace;min-width:60px;">L{layer}</span>'
                    f'<span style="font-family:monospace;min-width:50px;color:#64748B;">pos {pos}</span>'
                    f'<span style="font-family:monospace;font-weight:600;min-width:100px;">{clean_tok}</span>'
                    f'<span style="color:{color};font-family:monospace;">{val:+.4f}</span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

            import json as json_mod
            st.download_button(
                "⬇ Scarica risultato patching (JSON)",
                data=json_mod.dumps(result, indent=2, ensure_ascii=False),
                file_name="patching_result.json",
                mime="application/json",
                key="download_patch",
            )                        