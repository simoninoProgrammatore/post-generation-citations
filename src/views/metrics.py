"""Pagina 3 — Metriche."""

import json
import streamlit as st

from ui.components import render_metric_card


def render():
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