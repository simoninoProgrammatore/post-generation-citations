"""Pagina 4 — Attention Analysis."""

import json
import streamlit as st

from ui.components import step_header
from ui.attention_html import build_ranking_html, build_layer_chart_html, build_heatmap_html


def render():
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

    categories = sorted(set(r["category"] for r in attn_data))
    selected_cat = st.multiselect("Filtra per categoria", categories, default=categories)
    filtered = [r for r in attn_data if r["category"] in selected_cat]

    if not filtered:
        st.warning("Nessun risultato per i filtri selezionati.")
        st.stop()

    st.divider()
    step_header(1, "Panoramica dominanza H (CLS → H / CLS → P+H)")

    ranking_html = build_ranking_html(filtered)
    st.components.v1.html(ranking_html, height=max(80 + len(filtered) * 52, 200), scrolling=False)

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

    layer_chart_html = build_layer_chart_html(record)
    st.components.v1.html(layer_chart_html, height=420, scrolling=False)

    st.divider()
    step_header(3, "Heatmap attention matrix (ultimi 3 layer, media heads)")

    heatmap_html = build_heatmap_html(record)
    st.components.v1.html(heatmap_html, height=520, scrolling=True)

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