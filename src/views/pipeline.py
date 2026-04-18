"""Pagina 1 — Pipeline interattivo."""

import json
import streamlit as st

from ui.components import step_header, render_claim, render_metric_card, support_badge, render_nli_debug
from ui.cited_html import build_cited_html
from pipeline_runners import run_generate, run_decompose, run_retrieve, run_cite


def render():
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

            if (
                st.session_state.get("retrieve_method_used") == "nli"
                and "retrieve_debug" in st.session_state
                and any(d.get("sentence_scores") for d in st.session_state["retrieve_debug"])
            ):
                st.divider()
                render_nli_debug(st.session_state["retrieve_debug"])

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