#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Gera relatorio HTML comparativo SEO 2025 vs 2026 para repediu.com.br."""

import json
import os
from collections import Counter

BASE = r"C:\Users\Usuario\OneDrive\Documentos\seo 2026"
FILE_2025 = os.path.join(BASE, "repediu marco 2025.txt")
FILE_2026 = os.path.join(BASE, "repediu marco 2026.txt")
OUT = os.path.join(BASE, "relatorio_comparativo_2025_vs_2026.html")


def load(path):
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            line = line.strip()
            if not line or i == 0:
                continue
            parts = line.split("\t")
            if len(parts) < 2:
                continue
            kw = parts[0].strip()
            try:
                pos = int(parts[1].strip())
            except ValueError:
                continue
            rows.append((kw, pos))
    return rows


def bucket(rows):
    b = {"top1": 0, "top3": 0, "top5": 0, "top10": 0, "top20": 0, "top50": 0, "top100": 0}
    for _, p in rows:
        if p <= 1:
            b["top1"] += 1
        if p <= 3:
            b["top3"] += 1
        if p <= 5:
            b["top5"] += 1
        if p <= 10:
            b["top10"] += 1
        if p <= 20:
            b["top20"] += 1
        if p <= 50:
            b["top50"] += 1
        if p <= 100:
            b["top100"] += 1
    return b


def keywords_in(rows, lo, hi):
    return sorted([(k, p) for k, p in rows if lo <= p <= hi], key=lambda x: x[1])


def format_delta(n):
    if n > 0:
        return f'<span class="up">+{n}</span>'
    if n < 0:
        return f'<span class="down">{n}</span>'
    return '<span class="flat">0</span>'


def format_pct(old, new):
    if old == 0 and new == 0:
        return '<span class="flat">—</span>'
    if old == 0:
        return '<span class="up">NOVO</span>'
    pct = ((new - old) / old) * 100
    if pct > 0:
        return f'<span class="up">+{pct:.0f}%</span>'
    if pct < 0:
        return f'<span class="down">{pct:.0f}%</span>'
    return '<span class="flat">0%</span>'


def report_nav_html(active: str) -> str:
    """Links relativos entre relatorios. active: idx|v2|v1|legacy."""
    links = [
        ("idx", "index.html", "Indice"),
        ("v2", "relatorio_v2_destaques_2025_vs_2026.html", "Relatorio v2 (abas)"),
        ("v1", "relatorio_comparativo_2025_vs_2026.html", "Relatorio v1 (claro)"),
        ("legacy", "relatorio_repediu_2025_vs_2026.html", "Relatorio legado"),
    ]
    parts = ['<nav class="page-links" aria-label="Navegacao entre relatorios">']
    parts.append('<span class="page-links-title">Relatorios</span>')
    for key, href, label in links:
        if key == active:
            parts.append(
                f'<a class="is-current" href="{href}" aria-current="page">{label}</a>'
            )
        else:
            parts.append(f'<a href="{href}">{label}</a>')
    parts.append("</nav>")
    return "\n  " + "\n  ".join(parts) + "\n"


data_2025 = load(FILE_2025)
data_2026 = load(FILE_2026)

b25 = bucket(data_2025)
b26 = bucket(data_2026)

total_25 = len(data_2025)
total_26 = len(data_2026)

kws_25 = set(k for k, _ in data_2025)
kws_26 = set(k for k, _ in data_2026)
common = kws_25 & kws_26
new_kws = kws_26 - kws_25
lost_kws = kws_25 - kws_26

pos_25 = {}
for k, p in data_2025:
    if k not in pos_25 or p < pos_25[k]:
        pos_25[k] = p
pos_26 = {}
for k, p in data_2026:
    if k not in pos_26 or p < pos_26[k]:
        pos_26[k] = p

movers = []
for k in common:
    delta = pos_25[k] - pos_26[k]
    movers.append((k, pos_25[k], pos_26[k], delta))

big_gains = sorted([m for m in movers if m[3] > 0], key=lambda x: -x[3])[:20]
big_losses = sorted([m for m in movers if m[3] < 0], key=lambda x: x[3])[:20]

top1_26 = keywords_in(data_2026, 1, 1)
top3_26 = keywords_in(data_2026, 2, 3)
top5_26 = keywords_in(data_2026, 4, 5)
top10_26 = keywords_in(data_2026, 6, 10)

top1_25 = keywords_in(data_2025, 1, 1)
top5_25 = keywords_in(data_2025, 1, 5)
top10_25 = keywords_in(data_2025, 6, 10)

new_top10 = sorted([k for k in new_kws if pos_26[k] <= 10], key=lambda k: pos_26[k])


def row(label, v25, v26):
    delta = v26 - v25
    return f"""
    <tr>
      <td class="label">{label}</td>
      <td class="num">{v25}</td>
      <td class="num">{v26}</td>
      <td class="num">{format_delta(delta)}</td>
      <td class="num">{format_pct(v25, v26)}</td>
    </tr>"""


def kw_table(items, limit=None):
    rows_html = []
    for i, (k, p) in enumerate(items):
        if limit and i >= limit:
            break
        rows_html.append(f"<tr><td>{i+1}</td><td>{k}</td><td class='num'>{p}</td></tr>")
    return "\n".join(rows_html)


def mover_table(items):
    rows_html = []
    for k, p25, p26, d in items:
        cls = "up" if d > 0 else "down"
        sign = "+" if d > 0 else ""
        rows_html.append(
            f"<tr><td>{k}</td><td class='num'>{p25}</td><td class='num'>{p26}</td>"
            f"<td class='num {cls}'>{sign}{d}</td></tr>"
        )
    return "\n".join(rows_html)


chart_labels = ["Top 1", "Top 3", "Top 5", "Top 10", "Top 20", "Top 50", "Top 100"]
chart_25 = [b25["top1"], b25["top3"], b25["top5"], b25["top10"], b25["top20"], b25["top50"], b25["top100"]]
chart_26 = [b26["top1"], b26["top3"], b26["top5"], b26["top10"], b26["top20"], b26["top50"], b26["top100"]]

html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Relatorio SEO Comparativo - Repediu | Marco 2025 vs Marco 2026</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background: #f5f7fa;
    color: #1a202c;
    line-height: 1.6;
  }}
  .container {{ max-width: 1200px; margin: 0 auto; padding: 40px 20px; }}
  header {{
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: #fff;
    padding: 50px 20px;
    text-align: center;
    border-radius: 12px;
    margin-bottom: 30px;
    box-shadow: 0 10px 30px rgba(0,0,0,0.1);
  }}
  header h1 {{ font-size: 2.5rem; margin-bottom: 10px; }}
  header p {{ font-size: 1.1rem; opacity: 0.95; }}
  .subtitle {{ font-size: 0.95rem; opacity: 0.85; margin-top: 8px; }}

  .cards {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 20px; margin-bottom: 30px; }}
  .card {{
    background: #fff;
    padding: 24px;
    border-radius: 12px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.06);
    border-left: 4px solid #667eea;
  }}
  .card h3 {{ font-size: 0.85rem; color: #718096; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 8px; }}
  .card .value {{ font-size: 2.2rem; font-weight: 700; color: #1a202c; }}
  .card .delta {{ font-size: 0.95rem; margin-top: 6px; font-weight: 600; }}

  section {{
    background: #fff;
    padding: 30px;
    border-radius: 12px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.06);
    margin-bottom: 30px;
  }}
  section h2 {{
    font-size: 1.6rem;
    margin-bottom: 20px;
    color: #2d3748;
    padding-bottom: 12px;
    border-bottom: 2px solid #edf2f7;
  }}
  section h3 {{ font-size: 1.1rem; margin: 20px 0 12px; color: #4a5568; }}

  table {{ width: 100%; border-collapse: collapse; margin-top: 12px; font-size: 0.92rem; }}
  th, td {{ padding: 10px 12px; text-align: left; border-bottom: 1px solid #edf2f7; }}
  th {{ background: #f7fafc; font-weight: 600; color: #4a5568; text-transform: uppercase; font-size: 0.78rem; letter-spacing: 0.3px; }}
  td.num {{ text-align: right; font-variant-numeric: tabular-nums; font-weight: 600; }}
  td.label {{ font-weight: 600; }}
  tr:hover {{ background: #f7fafc; }}

  .up {{ color: #38a169; font-weight: 700; }}
  .down {{ color: #e53e3e; font-weight: 700; }}
  .flat {{ color: #718096; }}

  .chart-wrap {{ position: relative; height: 380px; }}

  .grid2 {{ display: grid; grid-template-columns: 1fr 1fr; gap: 24px; }}
  @media (max-width: 768px) {{
    .grid2 {{ grid-template-columns: 1fr; }}
    header h1 {{ font-size: 1.8rem; }}
  }}

  .highlight {{
    background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
    color: #fff;
    padding: 20px;
    border-radius: 10px;
    margin: 20px 0;
    font-size: 1.05rem;
  }}
  .success {{
    background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
    color: #1a202c;
    padding: 20px;
    border-radius: 10px;
    margin: 20px 0;
    font-weight: 600;
  }}

  footer {{ text-align: center; color: #718096; padding: 20px; font-size: 0.88rem; }}

  .legend-25 {{ color: #e53e3e; font-weight: 700; }}
  .legend-26 {{ color: #667eea; font-weight: 700; }}

  .page-links {{
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 10px 14px;
    padding: 14px 18px;
    margin-bottom: 20px;
    background: #2d3748;
    border-radius: 12px;
    font-size: 0.88rem;
  }}
  .page-links-title {{
    color: #a0aec0;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    font-size: 0.72rem;
  }}
  .page-links a {{
    color: #90cdf4;
    font-weight: 600;
    text-decoration: none;
    padding: 6px 12px;
    border-radius: 8px;
  }}
  .page-links a:hover {{ background: rgba(255,255,255,0.08); color: #e2e8f0; }}
  .page-links a.is-current {{
    background: rgba(102, 126, 234, 0.45);
    color: #fff;
    pointer-events: none;
    cursor: default;
  }}
</style>
</head>
<body>
<div class="container">
{report_nav_html("v1")}

  <header>
    <h1>Relatorio SEO Comparativo</h1>
    <p>repediu.com.br</p>
    <p class="subtitle">Marco 2025 vs Marco 2026 &middot; Analise de Performance de Palavras-Chave</p>
  </header>

  <div class="cards">
    <div class="card">
      <h3>Total de Palavras</h3>
      <div class="value">{total_26}</div>
      <div class="delta up">+{total_26 - total_25} ({format_pct(total_25, total_26)})</div>
    </div>
    <div class="card">
      <h3>Top 1 (Posicao #1)</h3>
      <div class="value">{b26["top1"]}</div>
      <div class="delta">{format_delta(b26["top1"] - b25["top1"])} vs {b25["top1"]} em 2025</div>
    </div>
    <div class="card">
      <h3>Top 5</h3>
      <div class="value">{b26["top5"]}</div>
      <div class="delta">{format_delta(b26["top5"] - b25["top5"])} vs {b25["top5"]} em 2025</div>
    </div>
    <div class="card">
      <h3>Top 10</h3>
      <div class="value">{b26["top10"]}</div>
      <div class="delta">{format_delta(b26["top10"] - b25["top10"])} vs {b25["top10"]} em 2025</div>
    </div>
  </div>

  <section>
    <h2>Resumo Executivo</h2>
    <div class="success">
      Em 12 meses, o dominio saltou de <strong>{total_25}</strong> para <strong>{total_26}</strong> palavras-chave rankeadas
      ({format_pct(total_25, total_26)}), com forte ganho em todas as faixas de Top.
      O site agora possui <strong>{b26["top1"]}</strong> palavras em 1a posicao (vs {b25["top1"]} em 2025)
      e <strong>{b26["top10"]}</strong> palavras no Top 10 (vs {b25["top10"]} em 2025).
    </div>
    <p>A marca <strong>&ldquo;repediu&rdquo;</strong> conquistou a posicao #1 no Google, consolidando o reconhecimento
    do novo posicionamento (antes marca diferente). O crescimento mais expressivo foi em termos de <em>marketing para restaurantes,
    delivery e WhatsApp Business</em>, alinhado com o reposicionamento da empresa.</p>
  </section>

  <section>
    <h2>Distribuicao por Faixa de Posicao</h2>
    <div class="chart-wrap">
      <canvas id="chartBars"></canvas>
    </div>
    <table>
      <thead>
        <tr>
          <th>Faixa</th>
          <th class="num"><span class="legend-25">Mar/2025</span></th>
          <th class="num"><span class="legend-26">Mar/2026</span></th>
          <th class="num">Variacao Absoluta</th>
          <th class="num">Variacao %</th>
        </tr>
      </thead>
      <tbody>
        {row("Top 1", b25["top1"], b26["top1"])}
        {row("Top 3", b25["top3"], b26["top3"])}
        {row("Top 5", b25["top5"], b26["top5"])}
        {row("Top 10", b25["top10"], b26["top10"])}
        {row("Top 20", b25["top20"], b26["top20"])}
        {row("Top 50", b25["top50"], b26["top50"])}
        {row("Top 100", b25["top100"], b26["top100"])}
      </tbody>
    </table>
  </section>

  <section>
    <h2>Evolucao Visual - Top 1, Top 5 e Top 10</h2>
    <div class="chart-wrap">
      <canvas id="chartKey"></canvas>
    </div>
  </section>

  <section>
    <h2>Palavras-Chave em Posicao #1 (Mar/2026)</h2>
    <p>Total: <strong>{b26["top1"]}</strong> palavras em 1o lugar.</p>
    <table>
      <thead><tr><th>#</th><th>Palavra-Chave</th><th class="num">Posicao</th></tr></thead>
      <tbody>{kw_table(top1_26)}</tbody>
    </table>
  </section>

  <section>
    <h2>Palavras-Chave no Top 2-5 (Mar/2026)</h2>
    <p>Total de novas posicoes entre 2 e 5: <strong>{len(top3_26) + len(top5_26)}</strong> palavras.</p>
    <h3>Posicoes 2 e 3</h3>
    <table>
      <thead><tr><th>#</th><th>Palavra-Chave</th><th class="num">Posicao</th></tr></thead>
      <tbody>{kw_table(top3_26)}</tbody>
    </table>
    <h3>Posicoes 4 e 5</h3>
    <table>
      <thead><tr><th>#</th><th>Palavra-Chave</th><th class="num">Posicao</th></tr></thead>
      <tbody>{kw_table(top5_26)}</tbody>
    </table>
  </section>

  <section>
    <h2>Palavras-Chave no Top 6-10 (Mar/2026)</h2>
    <table>
      <thead><tr><th>#</th><th>Palavra-Chave</th><th class="num">Posicao</th></tr></thead>
      <tbody>{kw_table(top10_26)}</tbody>
    </table>
  </section>

  <section>
    <h2>Comparativo 2025: Palavras no Top 10 (Referencia)</h2>
    <p>Em marco de 2025, apenas <strong>{b25["top10"]}</strong> palavras estavam no Top 10 e <strong>{b25["top1"]}</strong> em 1o lugar.</p>
    <h3>Top 5 em 2025</h3>
    <table>
      <thead><tr><th>#</th><th>Palavra-Chave</th><th class="num">Posicao</th></tr></thead>
      <tbody>{kw_table(top1_25 + top5_25)}</tbody>
    </table>
    <h3>Posicoes 6-10 em 2025</h3>
    <table>
      <thead><tr><th>#</th><th>Palavra-Chave</th><th class="num">Posicao</th></tr></thead>
      <tbody>{kw_table(top10_25)}</tbody>
    </table>
  </section>

  <section>
    <h2>Maiores Ganhos em Ranking (palavras presentes em ambos os periodos)</h2>
    <p>Palavras que mais subiram de posicao de 2025 para 2026.</p>
    <table>
      <thead><tr><th>Palavra-Chave</th><th class="num">Pos. 2025</th><th class="num">Pos. 2026</th><th class="num">Delta (posicoes)</th></tr></thead>
      <tbody>{mover_table(big_gains)}</tbody>
    </table>
  </section>

  <section>
    <h2>Maiores Perdas em Ranking</h2>
    <table>
      <thead><tr><th>Palavra-Chave</th><th class="num">Pos. 2025</th><th class="num">Pos. 2026</th><th class="num">Delta (posicoes)</th></tr></thead>
      <tbody>{mover_table(big_losses)}</tbody>
    </table>
  </section>

  <section>
    <h2>Novas Palavras no Top 10 em 2026 (nao existiam em 2025)</h2>
    <p>Total: <strong>{len(new_top10)}</strong> novas palavras conquistaram o Top 10.</p>
    <table>
      <thead><tr><th>#</th><th>Palavra-Chave</th><th class="num">Posicao 2026</th></tr></thead>
      <tbody>{kw_table([(k, pos_26[k]) for k in new_top10])}</tbody>
    </table>
  </section>

  <section>
    <h2>Insights e Recomendacoes</h2>
    <ul style="padding-left: 22px; line-height: 1.9;">
      <li><strong>Crescimento explosivo:</strong> +{total_26 - total_25} novas palavras rankeadas em 12 meses representa um crescimento muito acima da media do mercado.</li>
      <li><strong>Consolidacao de marca:</strong> A palavra &ldquo;repediu&rdquo; agora ocupa a 1a posicao, indicando que o rebranding foi bem-sucedido pelo Google.</li>
      <li><strong>Autoridade tematica:</strong> Termos como &ldquo;food marketing agency&ldquo;, &ldquo;crm para restaurantes&ldquo; e &ldquo;whatsapp business&rdquo; no topo mostram que o site se posicionou em clusters de alto valor comercial.</li>
      <li><strong>Oportunidade Top 3:</strong> Existem {b26["top10"] - b26["top3"]} palavras entre a posicao 4 e 10 que podem ser trabalhadas com conteudo e links internos para entrar no Top 3.</li>
      <li><strong>Monitoramento de perdas:</strong> Analise os termos com queda de ranking para reforcar conteudo e experiencia na pagina.</li>
      <li><strong>Top 100 expandindo:</strong> {b26["top100"]} palavras no Top 100 sao a base para trabalhar nos proximos ciclos e promover muitas delas para o Top 20/10.</li>
    </ul>
  </section>

  <footer>
    Relatorio gerado automaticamente em {__import__("datetime").datetime.now().strftime("%d/%m/%Y %H:%M")} &middot;
    Fonte: exports Semrush (marco 2025 e marco 2026)
  </footer>

</div>

<script>
const labels = {json.dumps(chart_labels)};
const d25 = {json.dumps(chart_25)};
const d26 = {json.dumps(chart_26)};

new Chart(document.getElementById('chartBars'), {{
  type: 'bar',
  data: {{
    labels: labels,
    datasets: [
      {{ label: 'Mar/2025', data: d25, backgroundColor: '#e53e3e' }},
      {{ label: 'Mar/2026', data: d26, backgroundColor: '#667eea' }}
    ]
  }},
  options: {{
    responsive: true, maintainAspectRatio: false,
    plugins: {{ legend: {{ position: 'top' }}, title: {{ display: false }} }},
    scales: {{ y: {{ beginAtZero: true, ticks: {{ stepSize: 50 }} }} }}
  }}
}});

new Chart(document.getElementById('chartKey'), {{
  type: 'bar',
  data: {{
    labels: ['Top 1', 'Top 5', 'Top 10'],
    datasets: [
      {{ label: 'Mar/2025', data: [{b25["top1"]}, {b25["top5"]}, {b25["top10"]}], backgroundColor: '#e53e3e' }},
      {{ label: 'Mar/2026', data: [{b26["top1"]}, {b26["top5"]}, {b26["top10"]}], backgroundColor: '#667eea' }}
    ]
  }},
  options: {{
    responsive: true, maintainAspectRatio: false,
    plugins: {{ legend: {{ position: 'top' }} }},
    scales: {{ y: {{ beginAtZero: true }} }}
  }}
}});
</script>
</body>
</html>
"""

with open(OUT, "w", encoding="utf-8") as f:
    f.write(html)

print(f"[OK] {total_25} keywords em 2025 / {total_26} keywords em 2026")
print(f"[OK] Top 1:  2025={b25['top1']:>4}  |  2026={b26['top1']:>4}")
print(f"[OK] Top 5:  2025={b25['top5']:>4}  |  2026={b26['top5']:>4}")
print(f"[OK] Top 10: 2025={b25['top10']:>4}  |  2026={b26['top10']:>4}")
print(f"[OK] HTML salvo: {OUT}")
