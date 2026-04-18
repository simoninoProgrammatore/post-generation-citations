"""Componenti UI riutilizzabili."""

import streamlit as st


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

                for s in sorted(sents, key=lambda x: x["score"], reverse=True):
                    score = s["score"]
                    is_best = s["is_best"]

                    if score >= 0.7:
                        color = "#10B981"; bg = "#F0FDF4"; border = "#86EFAC"
                    elif score >= 0.4:
                        color = "#F59E0B"; bg = "#FFFBEB"; border = "#FCD34D"
                    else:
                        color = "#94A3B8"; bg = "#F8FAFC"; border = "#E2E8F0"

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