"""Pagina 5 — Interpretability (IG + Activation Patching)."""

import json
import time
import numpy as np
import streamlit as st


PRESETS_IG = {
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


def _attr_color(val: float) -> str:
    if val > 0:
        alpha = min(abs(val), 1.0)
        return f"rgba(16, 185, 129, {alpha:.2f})"
    else:
        alpha = min(abs(val), 1.0)
        return f"rgba(239, 68, 68, {alpha:.2f})"


def _render_ig_tab():
    st.markdown("### Token-level attribution")
    st.caption(
        "Integrated Gradients misura quanto ogni token dell'input contribuisce allo score di entailment. "
        "Token con attribuzione alta sono quelli che il modello 'usa' di più per decidere."
    )

    with st.expander("📋 Preset casi noti", expanded=False):
        preset_case = st.selectbox(
            "Carica un preset",
            ["— nessun preset —"] + list(PRESETS_IG.keys()) + ["Custom"],
            key="ig_preset",
        )

    if preset_case in PRESETS_IG:
        default_p, default_h = PRESETS_IG[preset_case]
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
        _render_ig_results(st.session_state["ig_result"])


def _render_ig_results(result: dict):
    st.divider()

    col_m1, col_m2, col_m3 = st.columns(3)
    with col_m1:
        st.metric("Entailment", f"{result['probs']['entailment']:.4f}")
    with col_m2:
        st.metric("Contradiction", f"{result['probs']['contradiction']:.4f}")
    with col_m3:
        st.metric("Neutral", f"{result['probs']['neutral']:.4f}")

    st.caption(f"Predicted class: **{result['predicted']}** · convergence delta: `{result['convergence_delta']:.4f}`")

    st.markdown("#### Token-level attribution")
    st.caption("Verde = contributo positivo verso la classe target, rosso = contributo negativo.")

    tokens = result["tokens"]
    attributions = result["token_attributions_normalized"]

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

    if "layerwise_attributions" in result and result["layerwise_attributions"]:
        st.markdown("#### Layer-wise attribution heatmap")
        st.caption(
            "Righe = layer (0 = input, n = output). Colonne = token. "
            "Intensità = magnitudo dell'attribuzione. Mostra a che layer si forma la decisione."
        )

        layer_data = result["layerwise_attributions"]
        valid_layers = [l for l in layer_data if "error" not in l]

        if valid_layers:
            n_tokens_show = min(len(tokens), 48)
            cell_size = 14

            heatmap_rows = ""
            for layer_info in valid_layers:
                attrs = layer_info["token_attributions_normalized"][:n_tokens_show]
                cells = ""
                for val in attrs:
                    color = _attr_color(val)
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

            st.markdown("#### Layer importance (mean absolute attribution)")
            import pandas as pd
            df_layers = pd.DataFrame([
                {"layer": l["layer"], "importance": l["mean_abs_attribution"]}
                for l in valid_layers
            ])
            st.bar_chart(df_layers.set_index("layer"))

    st.download_button(
        "⬇ Scarica risultato IG (JSON)",
        data=json.dumps(result, indent=2, ensure_ascii=False),
        file_name="ig_result.json",
        mime="application/json",
        key="download_ig",
    )


def _render_patch_tab():
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
            progress_bar = st.progress(0.0)
            status_text = st.empty()
            time_text = st.empty()
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
        _render_patch_results(st.session_state["patch_result"])


def _render_patch_results(result: dict):
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
            intensity = min(abs(val) / max_abs, 1.0)
            if val > 0:
                color = f"rgba(239, 68, 68, {intensity:.2f})"
            else:
                color = f"rgba(59, 130, 246, {intensity:.2f})"
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

    st.download_button(
        "⬇ Scarica risultato patching (JSON)",
        data=json.dumps(result, indent=2, ensure_ascii=False),
        file_name="patching_result.json",
        mime="application/json",
        key="download_patch",
    )


def render():
    st.markdown(
        '<div class="page-header">'
        '<h1>🔬 Interpretability</h1>'
        '<p>Integrated Gradients e Activation Patching per analizzare dove e come DeBERTa prende decisioni biased.</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    tab_ig, tab_patch = st.tabs(["🎯 Integrated Gradients", "🔀 Activation Patching"])

    with tab_ig:
        _render_ig_tab()

    with tab_patch:
        _render_patch_tab()