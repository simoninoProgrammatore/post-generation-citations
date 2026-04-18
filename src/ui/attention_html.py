"""HTML per le visualizzazioni della pagina Attention Analysis."""

import json


def build_ranking_html(records: list[dict]) -> str:
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


def build_layer_chart_html(record: dict) -> str:
    layers_data = record.get("layer_dominance", [])
    cross = record.get("cross_attention", {})

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


def build_heatmap_html(record: dict) -> str:
    matrix = record.get("attention_matrix", [])
    tokens = record.get("tokens", [])
    segments = record.get("segments", {})

    if not matrix or not tokens:
        return "<p style='color:#94a3b8;font-size:13px;'>Matrice non disponibile.</p>"

    n = min(len(tokens), len(matrix), 48)
    tokens_trunc = tokens[:n]
    matrix_trunc = [row[:n] for row in matrix[:n]]

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