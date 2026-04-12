"""
Streamlit app for the Post-Generation Citation System.
Run with: streamlit run src/app.py
"""

import json
import os
import re
import streamlit as st
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
</style>
""", unsafe_allow_html=True)


# ──────────────────────────────────────────────
# Sidebar
# ──────────────────────────────────────────────

st.sidebar.markdown("### 📚 Citation Pipeline")
page = st.sidebar.radio(
    "Sezione",
    ["🔬 Pipeline interattivo", "📂 Esplora risultati", "📊 Metriche"],
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

def run_generate(query: str, model: str) -> str:
    from llm_client import call_llm
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


def run_retrieve(claims: list[str], passages: list[dict], method: str, threshold: float, top_k: int) -> list[dict]:
    from retrieve import match_with_nli, match_with_similarity, match_with_llm, extract_evidence
    from retrieve import _split_passage_with_spans, _load_nli_model
    import numpy as np

    matched = []
    for claim in claims:

        if method == "nli":
            matches = match_with_nli(claim, passages, threshold=threshold, top_k=top_k)
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
    return matched

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

            // Fallback: word overlap sui sentence
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
                    response = run_generate(query, model)
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
            skip_retrieve = True
        else:
            skip_retrieve = False
            st.write(f"{len(passages)} passages disponibili.")

        if not skip_retrieve and st.button("▶ Retrieve", key="btn_retrieve"):
            with st.spinner("Matching claims → passages..."):
                try:
                    matched = run_retrieve(st.session_state["claims"], passages, retrieve_method, nli_threshold, top_k)
                    st.session_state["matched"] = matched
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
                    with st.spinner("Calcolo metriche NLI..."):
                        try:
                            from evaluate import citation_precision_nli, citation_recall_nli
                            matched = st.session_state["matched"]
                            precision = citation_precision_nli(matched)
                            recall = citation_recall_nli(matched)
                            st.session_state["eval_metrics"] = {
                                "citation_precision": precision,
                                "citation_recall": recall,
                            }
                        except Exception as e:
                            st.error(f"Errore nella valutazione: {e}")

                if "eval_metrics" in st.session_state:
                    metrics = st.session_state["eval_metrics"]
                    prec = metrics["citation_precision"]
                    rec = metrics["citation_recall"]

                    col1, col2 = st.columns(2)
                    with col1:
                        color_p = "#10B981" if prec >= 0.7 else "#F59E0B" if prec >= 0.4 else "#EF4444"
                        render_metric_card("Citation Precision", prec, color_p)
                    with col2:
                        color_r = "#10B981" if rec >= 0.7 else "#F59E0B" if rec >= 0.4 else "#EF4444"
                        render_metric_card("Citation Recall", rec, color_r)

                    st.markdown("")
                    if prec >= 0.8 and rec >= 0.8:
                        st.success("Ottimo: citazioni precise e con buona copertura.")
                    elif prec >= 0.8:
                        st.warning("Citazioni precise, ma alcune frasi non sono supportate.")
                    elif rec >= 0.8:
                        st.warning("Buona copertura, ma alcune citazioni non supportano la frase.")
                    else:
                        st.error("Sia precisione che recall sono basse — le citazioni vanno migliorate.")

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