"""Genera l'HTML interattivo per la risposta citata."""

import json
import re


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