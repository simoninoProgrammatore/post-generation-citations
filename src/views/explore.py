"""Pagina 2 — Esplora risultati."""

import json
import streamlit as st

from ui.components import render_claim, support_badge


def render():
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