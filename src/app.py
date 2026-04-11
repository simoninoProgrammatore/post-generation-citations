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

st.sidebar.title("📚 Citation Pipeline")
page = st.sidebar.radio(
    "Sezione",
    ["🔬 Pipeline interattivo", "📂 Esplora risultati", "📊 Metriche"],
)
st.sidebar.divider()
st.sidebar.caption("Post-Generation Citation System — Tesi triennale")


@st.cache_resource
def get_nli_model(model_name: str):
    from sentence_transformers import CrossEncoder
    return CrossEncoder(model_name)


@st.cache_resource
def get_embedding_model(model_name: str):
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer(model_name)


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
    from retrieve import match_with_nli, match_with_similarity, match_with_llm
    matched = []
    for claim in claims:
        if method == "nli":
            matches = match_with_nli(claim, passages, threshold=threshold, top_k=top_k)
        elif method == "llm":
            matches = match_with_llm(claim, passages, threshold=threshold, top_k=top_k)
        else:
            matches = match_with_similarity(claim, passages, top_k=top_k)
        matched.append({"claim": claim, "supporting_passages": matches})
    return matched


def run_cite(response: str, matched_claims: list[dict]) -> tuple[str, list[dict]]:
    from cite import build_citation_map, insert_citations
    citation_map = build_citation_map(matched_claims)
    cited, refs = insert_citations(response, matched_claims, citation_map)
    return cited, refs


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

    sentences = re.split(r'(?<=[.!?])\s+', cited.strip())

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
            <strong>[{ref['citation_number']}]</strong> <em>{ref.get('title', 'N/A')}</em>
            <div class="ref-text">{ref.get('text', '')}</div>
        </div>"""

    sentence_data_json = json.dumps(sentence_data)

    html = f"""
    <style>
        * {{ box-sizing: border-box; }}
        body {{ margin: 0; padding: 0; }}
        .cited-container {{
            font-family: Georgia, serif;
            font-size: 15px;
            line-height: 2;
            padding: 16px;
            background: #ffffff;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            margin-bottom: 12px;
        }}
        .sentence {{
            border-radius: 3px;
            padding: 1px 3px;
            transition: background 0.15s;
        }}
        .sentence.supported {{
            background: #e8f5e9;
            cursor: pointer;
            border-bottom: 2px solid #66bb6a;
        }}
        .sentence.supported:hover {{
            background: #c8e6c9;
        }}
        .sentence.active {{
            background: #a5d6a7;
        }}
        .cite-marker {{
            color: #2e7d32;
            font-weight: bold;
            font-size: 11px;
            margin-left: 1px;
        }}
        .panel {{
            display: none;
            margin: 8px 0 12px 0;
            border-left: 3px solid #66bb6a;
            padding: 10px 14px;
            background: #f9fbe7;
            border-radius: 0 6px 6px 0;
            font-family: sans-serif;
            font-size: 13px;
        }}
        .panel.visible {{ display: block; }}
        .claim-text {{
            font-style: italic;
            color: #333;
            margin-bottom: 8px;
        }}
        .passage-card {{
            background: white;
            border: 1px solid #dcedc8;
            border-radius: 6px;
            padding: 8px 10px;
            margin-top: 6px;
            max-height: 200px;
            overflow-y: auto;
        }}
        .passage-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 4px;
            position: sticky;
            top: 0;
            background: white;
            padding-bottom: 4px;
            border-bottom: 1px solid #f0f0f0;
        }}
        .passage-title {{
            font-weight: bold;
            color: #1b5e20;
            font-size: 13px;
        }}
        .score-pill {{
            background: #81c784;
            color: white;
            border-radius: 10px;
            padding: 1px 8px;
            font-size: 11px;
        }}
        .cite-pill {{
            background: #2e7d32;
            color: white;
            border-radius: 10px;
            padding: 1px 8px;
            font-size: 11px;
            margin-left: 4px;
        }}
        .passage-text {{
            color: #555;
            font-size: 12px;
            line-height: 1.6;
            margin-top: 6px;
        }}
        .refs-section {{
            margin-top: 16px;
            padding-top: 12px;
            border-top: 2px solid #e0e0e0;
            font-family: sans-serif;
            font-size: 13px;
        }}
        .ref-item {{
            margin-bottom: 10px;
            padding: 8px;
            background: #f5f5f5;
            border-radius: 4px;
        }}
        .ref-text {{
            color: #666;
            font-size: 12px;
            margin-top: 3px;
            line-height: 1.6;
        }}
    </style>

    <div class="cited-container">{sentences_html}</div>
    <div id="panels-container"></div>

    {f'<div class="refs-section"><strong>References</strong>{refs_html}</div>' if refs_html else ''}

    <script>
        const sentenceData = {sentence_data_json};
        const dataMap = {{}};
        sentenceData.forEach(s => dataMap[s.idx] = s);

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

                    data.claims.forEach(c => {{
                        const claimDiv = document.createElement('div');
                        claimDiv.className = 'claim-text';
                        claimDiv.innerHTML = '🔍 <strong>Claim:</strong> ' + c.claim;
                        panel.appendChild(claimDiv);

                        c.passages.forEach(p => {{
                            const card = document.createElement('div');
                            card.className = 'passage-card';
                            card.innerHTML = `
                                <div class="passage-header">
                                    <span class="passage-title">${{p.title}}</span>
                                    <span>
                                        <span class="score-pill">score ${{p.score.toFixed(3)}}</span>
                                        <span class="cite-pill">[${{p.cite_num}}]</span>
                                    </span>
                                </div>
                                <div class="passage-text">${{p.text}}</div>
                            `;
                            panel.appendChild(card);
                        }});
                    }});

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
    st.title("🔬 Pipeline interattivo")
    st.caption("Esegui ogni step separatamente e ispeziona i risultati intermedi.")

    with st.expander("⚙️ Impostazioni", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            model = st.selectbox(
                "Modello LLM",
                ["claude-haiku-4-5-20251001", "claude-sonnet-4-20250514"],
            )
            retrieve_method = st.selectbox("Metodo retrieval", ["nli", "similarity", "llm"])
        with col2:
            nli_threshold = st.slider("NLI threshold", 0.0, 1.0, 0.5, 0.05)
            top_k = st.slider("Top-k passages per claim", 1, 5, 3)

    st.divider()
    st.subheader("Step 1 — Query")

    alce_file = st.file_uploader("Carica dataset ALCE (.json)", type="json", key="alce_upload")

    query = ""
    passages = []

    if alce_file:
        alce_data = json.load(alce_file)
        st.session_state["alce_data"] = alce_data

    if "alce_data" in st.session_state:
        alce_data = st.session_state["alce_data"]

        options = {
            f"[{i}] {ex.get('question', ex.get('query', 'N/A'))[:100]}": i
            for i, ex in enumerate(alce_data)
        }
        selected_label = st.selectbox("Seleziona una domanda", list(options.keys()))
        selected_idx = options[selected_label]
        selected_ex = alce_data[selected_idx]

        query = selected_ex.get("question", selected_ex.get("query", ""))
        passages = selected_ex.get("docs", selected_ex.get("passages", []))

        st.markdown(f"**Query:** {query}")
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

    if st.button("▶ Generate", type="primary"):
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
        st.subheader("Step 2 — Decompose")
        st.text_area("Risposta grezza", st.session_state["response"], height=150, disabled=True)

        if st.button("▶ Decompose"):
            with st.spinner("Decomposizione in atomic claims..."):
                try:
                    claims = run_decompose(st.session_state["response"], model)
                    st.session_state["claims"] = claims
                except Exception as e:
                    st.error(f"Errore: {e}")

        if "claims" in st.session_state:
            st.write(f"**{len(st.session_state['claims'])} claims estratti:**")
            for i, claim in enumerate(st.session_state["claims"], 1):
                st.markdown(f"`{i}.` {claim}")

            st.divider()
            st.subheader("Step 3 — Retrieve")
            passages = st.session_state.get("passages", [])

            if not passages:
                st.info("Nessun passage fornito — lo step retrieve verrà saltato.")
                st.session_state["matched"] = [
                    {"claim": c, "supporting_passages": []}
                    for c in st.session_state["claims"]
                ]
                skip_retrieve = True
            else:
                skip_retrieve = False
                st.write(f"{len(passages)} passages disponibili.")

            if not skip_retrieve and st.button("▶ Retrieve"):
                with st.spinner("Matching claims → passages..."):
                    try:
                        matched = run_retrieve(
                            st.session_state["claims"],
                            passages,
                            retrieve_method,
                            nli_threshold,
                            top_k,
                        )
                        st.session_state["matched"] = matched
                    except Exception as e:
                        st.error(f"Errore: {e}")

            if "matched" in st.session_state:
                matched = st.session_state["matched"]
                supported = sum(1 for m in matched if m["supporting_passages"])
                st.write(f"**{supported}/{len(matched)} claims con supporto:**")

                for m in matched:
                    has_support = bool(m["supporting_passages"])
                    icon = "✅" if has_support else "❌"
                    with st.expander(f"{icon} {m['claim'][:90]}..."):
                        if m["supporting_passages"]:
                            for p in m["supporting_passages"]:
                                score_key = "entailment_score" if "entailment_score" in p else "similarity_score"
                                score = p.get(score_key, 0)
                                st.markdown(f"**{p.get('title', 'N/A')}** — score: `{score:.3f}`")
                                st.caption(p.get("text", "")[:300] + "...")
                        else:
                            st.caption("Nessun passage di supporto trovato.")

                st.divider()
                st.subheader("Step 4 — Cite")

                if st.button("▶ Insert Citations", type="primary"):
                    with st.spinner("Inserimento citazioni..."):
                        try:
                            cited, refs = run_cite(
                                st.session_state["response"],
                                st.session_state["matched"],
                            )
                            st.session_state["cited"] = cited
                            st.session_state["refs"] = refs
                        except Exception as e:
                            st.error(f"Errore: {e}")

                if "cited" in st.session_state:
                    html = build_cited_html(
                        st.session_state["cited"],
                        st.session_state["matched"],
                        st.session_state["refs"],
                    )
                    st.components.v1.html(html, height=600, scrolling=True)

                    result = {
                        "query": st.session_state["query"],
                        "raw_response": st.session_state["response"],
                        "claims": st.session_state["claims"],
                        "matched_claims": st.session_state["matched"],
                        "cited_response": st.session_state["cited"],
                        "references": st.session_state["refs"],
                    }
                    st.download_button(
                        "⬇ Scarica risultato JSON",
                        data=json.dumps(result, indent=2, ensure_ascii=False),
                        file_name="result.json",
                        mime="application/json",
                    )


# ──────────────────────────────────────────────
# PAGE 2 — Esplora risultati
# ──────────────────────────────────────────────

elif page == "📂 Esplora risultati":
    st.title("📂 Esplora risultati")
    st.caption("Carica un file JSON prodotto dal pipeline e naviga i risultati.")

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

        st.subheader(f"Q: {ex.get('question', ex.get('query', 'N/A'))}")

        tab_labels = ["Risposta grezza"]
        if has_claims:
            tab_labels.append("Claims")
        if has_matched:
            tab_labels.append("Matched")
        if has_cited:
            tab_labels.append("Citata")

        tabs = st.tabs(tab_labels)
        tab_idx = 0

        with tabs[tab_idx]:
            st.write(ex.get("raw_response", "N/A"))
        tab_idx += 1

        if has_claims:
            with tabs[tab_idx]:
                for i, c in enumerate(ex["claims"], 1):
                    st.markdown(f"`{i}.` {c}")
            tab_idx += 1

        if has_matched:
            with tabs[tab_idx]:
                for m in ex["matched_claims"]:
                    has_support = bool(m["supporting_passages"])
                    icon = "✅" if has_support else "❌"
                    with st.expander(f"{icon} {m['claim'][:90]}"):
                        for p in m["supporting_passages"]:
                            score_key = "entailment_score" if "entailment_score" in p else "similarity_score"
                            st.markdown(f"**{p.get('title', '')}** — `{p.get(score_key, 0):.3f}`")
                            st.caption(p.get("text", "")[:300])
            tab_idx += 1

        if has_cited:
            with tabs[tab_idx]:
                st.success(ex["cited_response"])
                if ex.get("references"):
                    st.markdown("---")
                    for ref in ex["references"]:
                        st.markdown(f"**[{ref['citation_number']}]** {ref['title']}")
                        st.caption(ref["text"][:300])


# ──────────────────────────────────────────────
# PAGE 3 — Metriche
# ──────────────────────────────────────────────

elif page == "📊 Metriche":
    st.title("📊 Metriche di valutazione")
    st.caption("Carica il file evaluation.json prodotto da evaluate.py.")

    uploaded = st.file_uploader("Carica evaluation.json", type="json")

    if uploaded:
        results = json.load(uploaded)
        metrics = results.get("metrics", {})
        per_example = results.get("per_example", [])

        st.subheader("Aggregate")
        if metrics:
            cols = st.columns(len(metrics))
            for col, (name, value) in zip(cols, metrics.items()):
                col.metric(name, f"{value:.3f}")
        else:
            st.info("Nessuna metrica aggregata trovata nel file.")

        if per_example:
            st.divider()
            st.subheader("Per esempio")

            import pandas as pd
            df = pd.DataFrame(per_example)
            st.dataframe(df, use_container_width=True)

            numeric_cols = df.select_dtypes(include="number").columns.tolist()
            if numeric_cols:
                metric_to_plot = st.selectbox("Visualizza distribuzione", numeric_cols)
                st.bar_chart(df[metric_to_plot])
        else:
            st.info("Nessun dato per-esempio nel file.")
    else:
        st.info("Carica un file evaluation.json per visualizzare le metriche.")