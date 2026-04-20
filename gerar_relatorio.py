"""Gera relatorio HTML comparando Top 1 / Top 5 / Top 10 do repediu entre Mar/2025 e Mar/2026."""
from pathlib import Path
from collections import defaultdict
from html import escape
import json

BASE = Path(r"C:\Users\Usuario\OneDrive\Documentos\seo 2026")
F_2025 = BASE / "repediu marco 2025.txt"
F_2026 = BASE / "repediu marco 2026.txt"
OUT = BASE / "relatorio_repediu_2025_vs_2026.html"


def load(path: Path):
    """Retorna dict {keyword: best_position} e lista raw [(keyword, position)]."""
    raw = []
    best = {}
    with path.open("r", encoding="utf-8") as f:
        next(f)  # header
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split("\t")
            if len(parts) < 2:
                continue
            kw = parts[0].strip().lower()
            try:
                pos = int(parts[1].strip())
            except ValueError:
                continue
            raw.append((kw, pos))
            if kw not in best or pos < best[kw]:
                best[kw] = pos
    return best, raw


d2025, raw2025 = load(F_2025)
d2026, raw2026 = load(F_2026)


def bucket(d, limit):
    return {k: v for k, v in d.items() if v <= limit}


buckets_2025 = {1: bucket(d2025, 1), 5: bucket(d2025, 5), 10: bucket(d2025, 10)}
buckets_2026 = {1: bucket(d2026, 1), 5: bucket(d2026, 5), 10: bucket(d2026, 10)}

all_kws = set(d2025) | set(d2026)
kws_mantidos_top10 = set(buckets_2025[10]) & set(buckets_2026[10])
kws_novos_top10 = set(buckets_2026[10]) - set(buckets_2025[10])
kws_perdidos_top10 = set(buckets_2025[10]) - set(buckets_2026[10])

kws_novos_top5 = set(buckets_2026[5]) - set(buckets_2025[5])
kws_perdidos_top5 = set(buckets_2025[5]) - set(buckets_2026[5])

kws_novos_top1 = set(buckets_2026[1]) - set(buckets_2025[1])
kws_perdidos_top1 = set(buckets_2025[1]) - set(buckets_2026[1])

# Changes nas posicoes para palavras comuns
comuns = set(d2025) & set(d2026)
mudancas = []
for k in comuns:
    p25 = d2025[k]
    p26 = d2026[k]
    mudancas.append((k, p25, p26, p25 - p26))  # positivo = subiu
mudancas_subiu = sorted([m for m in mudancas if m[3] > 0], key=lambda x: -x[3])
mudancas_caiu = sorted([m for m in mudancas if m[3] < 0], key=lambda x: x[3])

total_2025 = len(d2025)
total_2026 = len(d2026)

dados_chart = {
    "labels": ["Top 1", "Top 5", "Top 10"],
    "v2025": [len(buckets_2025[1]), len(buckets_2025[5]), len(buckets_2025[10])],
    "v2026": [len(buckets_2026[1]), len(buckets_2026[5]), len(buckets_2026[10])],
}


def tabela(linhas, cols, max_linhas=None, empty_msg="(nenhum)"):
    if not linhas:
        return f'<p class="empty">{empty_msg}</p>'
    html_parts = ['<table><thead><tr>']
    html_parts.extend(f"<th>{escape(c)}</th>" for c in cols)
    html_parts.append("</tr></thead><tbody>")
    limit = max_linhas or len(linhas)
    for row in linhas[:limit]:
        html_parts.append("<tr>")
        for v in row:
            html_parts.append(f"<td>{escape(str(v))}</td>")
        html_parts.append("</tr>")
    html_parts.append("</tbody></table>")
    if max_linhas and len(linhas) > max_linhas:
        html_parts.append(f'<p class="more">... e mais {len(linhas)-max_linhas} termos.</p>')
    return "".join(html_parts)


# Tabelas auxiliares
top1_novos = sorted(kws_novos_top1)
top1_perdidos = [(k, d2025[k]) for k in sorted(kws_perdidos_top1)]
top1_perdidos_agora = [(k, d2025[k], d2026[k]) for k in kws_perdidos_top1 if k in d2026]
top1_perdidos_fora = [(k, d2025[k]) for k in kws_perdidos_top1 if k not in d2026]

top5_novos = [(k, d2026[k]) for k in sorted(kws_novos_top5, key=lambda x: d2026[x])]
top5_perdidos = [(k, d2025[k], d2026.get(k, "Fora")) for k in sorted(kws_perdidos_top5, key=lambda x: d2025[x])]

top10_novos = [(k, d2026[k]) for k in sorted(kws_novos_top10, key=lambda x: d2026[x])]
top10_perdidos = [(k, d2025[k], d2026.get(k, "Fora")) for k in sorted(kws_perdidos_top10, key=lambda x: d2025[x])]

top_subiu = [(k, p25, p26, f"+{diff}") for k, p25, p26, diff in mudancas_subiu]
top_caiu = [(k, p25, p26, f"{diff}") for k, p25, p26, diff in mudancas_caiu]

# Dados estaticos para o chart
chart_data_json = json.dumps(dados_chart)


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
    return "\n".join(parts)


html = f"""<!DOCTYPE html>
<html lang="pt-br">
<head>
<meta charset="utf-8">
<title>Relatorio SEO: Repediu Mar/2025 vs Mar/2026</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<style>
  :root {{
    --primary: #ff642d;
    --dark: #1a1f2e;
    --light: #f6f7fb;
    --gray: #6b7280;
    --green: #10b981;
    --red: #ef4444;
    --border: #e5e7eb;
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    background: var(--light);
    color: var(--dark);
    line-height: 1.55;
  }}
  header {{
    background: linear-gradient(135deg, #1a1f2e 0%, #3b4056 100%);
    color: #fff;
    padding: 48px 32px;
    text-align: center;
  }}
  header h1 {{ margin: 0 0 8px; font-size: 2.1rem; }}
  header p {{ margin: 0; opacity: 0.85; font-size: 1.05rem; }}
  main {{ max-width: 1200px; margin: -40px auto 48px; padding: 0 24px; }}
  .section {{
    background: #fff;
    border-radius: 14px;
    padding: 32px;
    margin-bottom: 24px;
    box-shadow: 0 4px 24px rgba(0,0,0,0.06);
  }}
  h2 {{
    margin: 0 0 20px; font-size: 1.4rem; color: var(--dark);
    border-left: 4px solid var(--primary); padding-left: 12px;
  }}
  h3 {{ margin: 24px 0 12px; font-size: 1.1rem; color: var(--dark); }}
  .kpi-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    gap: 16px;
    margin-bottom: 24px;
  }}
  .kpi {{
    background: linear-gradient(135deg, #ffffff 0%, #f9fafb 100%);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 20px;
    position: relative;
  }}
  .kpi .label {{ font-size: 0.78rem; text-transform: uppercase; color: var(--gray); letter-spacing: 0.5px; }}
  .kpi .value {{ font-size: 2rem; font-weight: 700; margin: 4px 0; }}
  .kpi .delta {{ font-size: 0.9rem; font-weight: 600; }}
  .kpi .delta.up {{ color: var(--green); }}
  .kpi .delta.down {{ color: var(--red); }}
  .kpi.kpi-25 {{ border-top: 3px solid #94a3b8; }}
  .kpi.kpi-26 {{ border-top: 3px solid var(--primary); }}
  .two-col {{ display: grid; grid-template-columns: 1fr 1fr; gap: 24px; }}
  @media (max-width: 800px) {{ .two-col {{ grid-template-columns: 1fr; }} }}
  table {{
    width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 0.92rem;
  }}
  th {{
    text-align: left; padding: 10px 12px; background: #f3f4f6;
    border-bottom: 2px solid var(--border); font-size: 0.82rem;
    text-transform: uppercase; letter-spacing: 0.3px; color: #4b5563;
  }}
  td {{ padding: 8px 12px; border-bottom: 1px solid var(--border); }}
  tbody tr:hover {{ background: #fafafa; }}
  .empty {{ color: var(--gray); font-style: italic; }}
  .more {{ color: var(--gray); font-size: 0.85rem; margin-top: 8px; }}
  .chart-wrap {{ position: relative; height: 360px; }}
  .badge {{
    display: inline-block; padding: 2px 10px; border-radius: 12px;
    font-size: 0.8rem; font-weight: 600;
  }}
  .badge.up {{ background: #d1fae5; color: #065f46; }}
  .badge.down {{ background: #fee2e2; color: #991b1b; }}
  .tabs {{ display: flex; gap: 4px; margin-bottom: 16px; border-bottom: 2px solid var(--border); }}
  .tab {{
    padding: 10px 18px; cursor: pointer; background: transparent; border: 0;
    font-weight: 600; color: var(--gray); font-size: 0.95rem; position: relative; bottom: -2px;
    border-bottom: 2px solid transparent;
  }}
  .tab.active {{ color: var(--primary); border-bottom-color: var(--primary); }}
  .pane {{ display: none; }}
  .pane.active {{ display: block; }}
  .tag {{
    display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 0.82rem; font-weight: 600;
    background: #e0e7ff; color: #3730a3;
  }}
  .page-links {{
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 10px 14px;
    max-width: 1200px;
    margin: 0 auto;
    padding: 16px 24px 0;
    font-size: 0.88rem;
  }}
  .page-links-title {{
    color: var(--gray);
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    font-size: 0.72rem;
  }}
  .page-links a {{
    color: #2563eb;
    font-weight: 600;
    text-decoration: none;
    padding: 6px 12px;
    border-radius: 8px;
  }}
  .page-links a:hover {{ background: #eff6ff; }}
  .page-links a.is-current {{
    background: #1a1f2e;
    color: #fff;
    pointer-events: none;
    cursor: default;
  }}
</style>
</head>
<body>
{report_nav_html("legacy")}

<header>
  <h1>Relatorio SEO - repediu.com.br</h1>
  <p>Comparativo de posicoes organicas: <strong>Marco 2025</strong> vs <strong>Marco 2026</strong></p>
</header>

<main>

<section class="section">
  <h2>Visao Geral</h2>
  <div class="kpi-grid">
    <div class="kpi kpi-25">
      <div class="label">Total de keywords - Mar/2025</div>
      <div class="value">{total_2025}</div>
    </div>
    <div class="kpi kpi-26">
      <div class="label">Total de keywords - Mar/2026</div>
      <div class="value">{total_2026}</div>
      <div class="delta {'up' if total_2026 > total_2025 else 'down'}">
        {'+' if total_2026 >= total_2025 else ''}{total_2026 - total_2025} ({((total_2026-total_2025)/max(total_2025,1)*100):+.1f}%)
      </div>
    </div>
    <div class="kpi">
      <div class="label">Keywords comuns (aparecem nos 2 periodos)</div>
      <div class="value">{len(comuns)}</div>
    </div>
    <div class="kpi">
      <div class="label">Keywords novas em Mar/2026</div>
      <div class="value">{len(set(d2026) - set(d2025))}</div>
    </div>
  </div>

  <h3>Comparativo Top 1 / Top 5 / Top 10</h3>
  <div class="kpi-grid">
    <div class="kpi kpi-25">
      <div class="label">Top 1 - Mar/2025</div>
      <div class="value">{len(buckets_2025[1])}</div>
    </div>
    <div class="kpi kpi-26">
      <div class="label">Top 1 - Mar/2026</div>
      <div class="value">{len(buckets_2026[1])}</div>
      <div class="delta {'up' if len(buckets_2026[1]) >= len(buckets_2025[1]) else 'down'}">
        {'+' if len(buckets_2026[1]) >= len(buckets_2025[1]) else ''}{len(buckets_2026[1]) - len(buckets_2025[1])}
      </div>
    </div>
    <div class="kpi kpi-25">
      <div class="label">Top 5 - Mar/2025</div>
      <div class="value">{len(buckets_2025[5])}</div>
    </div>
    <div class="kpi kpi-26">
      <div class="label">Top 5 - Mar/2026</div>
      <div class="value">{len(buckets_2026[5])}</div>
      <div class="delta {'up' if len(buckets_2026[5]) >= len(buckets_2025[5]) else 'down'}">
        {'+' if len(buckets_2026[5]) >= len(buckets_2025[5]) else ''}{len(buckets_2026[5]) - len(buckets_2025[5])}
      </div>
    </div>
    <div class="kpi kpi-25">
      <div class="label">Top 10 - Mar/2025</div>
      <div class="value">{len(buckets_2025[10])}</div>
    </div>
    <div class="kpi kpi-26">
      <div class="label">Top 10 - Mar/2026</div>
      <div class="value">{len(buckets_2026[10])}</div>
      <div class="delta {'up' if len(buckets_2026[10]) >= len(buckets_2025[10]) else 'down'}">
        {'+' if len(buckets_2026[10]) >= len(buckets_2025[10]) else ''}{len(buckets_2026[10]) - len(buckets_2025[10])}
      </div>
    </div>
  </div>

  <div class="chart-wrap">
    <canvas id="chartCounts"></canvas>
  </div>
</section>

<section class="section">
  <h2>Top 1 - Keywords em 1a posicao</h2>
  <div class="two-col">
    <div>
      <h3>Novas em Top 1 (Mar/2026)</h3>
      {tabela([(k, d2026[k]) for k in sorted(kws_novos_top1, key=lambda x: d2026[x])], ["Keyword", "Posicao 2026"], max_linhas=50, empty_msg="Nenhuma keyword nova em Top 1.")}
    </div>
    <div>
      <h3>Perdeu a 1a posicao (estava em Top 1 em Mar/2025)</h3>
      {tabela([(k, d2025[k], d2026.get(k, "Fora")) for k in sorted(kws_perdidos_top1)], ["Keyword", "Pos 2025", "Pos 2026"], max_linhas=50, empty_msg="Nao tinha nenhuma em Top 1 em Mar/2025.")}
    </div>
  </div>
</section>

<section class="section">
  <h2>Top 5 - Keywords nas posicoes 1-5</h2>
  <div class="two-col">
    <div>
      <h3>Entraram no Top 5 em Mar/2026</h3>
      {tabela(top5_novos, ["Keyword", "Posicao 2026"], max_linhas=60, empty_msg="Nenhuma keyword nova em Top 5.")}
    </div>
    <div>
      <h3>Sairam do Top 5 (estavam em Mar/2025)</h3>
      {tabela(top5_perdidos, ["Keyword", "Pos 2025", "Pos 2026"], max_linhas=60, empty_msg="Nao tinha nenhuma em Top 5 em Mar/2025.")}
    </div>
  </div>
</section>

<section class="section">
  <h2>Top 10 - Keywords nas posicoes 1-10</h2>
  <div class="two-col">
    <div>
      <h3>Entraram no Top 10 em Mar/2026</h3>
      {tabela(top10_novos, ["Keyword", "Posicao 2026"], max_linhas=80, empty_msg="Nenhuma keyword nova em Top 10.")}
    </div>
    <div>
      <h3>Sairam do Top 10 (estavam em Mar/2025)</h3>
      {tabela(top10_perdidos, ["Keyword", "Pos 2025", "Pos 2026"], max_linhas=80, empty_msg="Nao tinha nenhuma em Top 10 em Mar/2025.")}
    </div>
  </div>
</section>

<section class="section">
  <h2>Movimentacao de Posicoes (keywords comuns)</h2>
  <p style="color:var(--gray);margin-top:0">Palavras-chave que apareciam em ambos os periodos e suas variacoes de ranking.</p>

  <div class="tabs">
    <button class="tab active" data-pane="subiu">Subiram ({len(mudancas_subiu)})</button>
    <button class="tab" data-pane="caiu">Cairam ({len(mudancas_caiu)})</button>
  </div>

  <div class="pane active" id="pane-subiu">
    {tabela(top_subiu, ["Keyword", "Pos 2025", "Pos 2026", "Variacao"], max_linhas=50, empty_msg="Nenhuma.")}
  </div>
  <div class="pane" id="pane-caiu">
    {tabela(top_caiu, ["Keyword", "Pos 2025", "Pos 2026", "Variacao"], max_linhas=50, empty_msg="Nenhuma.")}
  </div>
</section>

<section class="section">
  <h2>Resumo Analitico</h2>
  <ul>
    <li><strong>Volume total de keywords</strong> passou de <strong>{total_2025}</strong> (Mar/2025) para <strong>{total_2026}</strong> (Mar/2026) — variacao de <strong>{total_2026 - total_2025:+d}</strong> termos ({((total_2026-total_2025)/max(total_2025,1)*100):+.1f}%).</li>
    <li><strong>Top 1:</strong> de <strong>{len(buckets_2025[1])}</strong> para <strong>{len(buckets_2026[1])}</strong> keywords ({len(buckets_2026[1]) - len(buckets_2025[1]):+d}). Das que eram Top 1, <strong>{len(kws_perdidos_top1)}</strong> perderam a 1a posicao.</li>
    <li><strong>Top 5:</strong> de <strong>{len(buckets_2025[5])}</strong> para <strong>{len(buckets_2026[5])}</strong> keywords ({len(buckets_2026[5]) - len(buckets_2025[5]):+d}). Entraram <strong>{len(kws_novos_top5)}</strong>, sairam <strong>{len(kws_perdidos_top5)}</strong>.</li>
    <li><strong>Top 10:</strong> de <strong>{len(buckets_2025[10])}</strong> para <strong>{len(buckets_2026[10])}</strong> keywords ({len(buckets_2026[10]) - len(buckets_2025[10]):+d}). Entraram <strong>{len(kws_novos_top10)}</strong>, sairam <strong>{len(kws_perdidos_top10)}</strong>, mantiveram-se <strong>{len(kws_mantidos_top10)}</strong>.</li>
    <li><strong>Keywords comuns</strong> entre os dois periodos: <strong>{len(comuns)}</strong>. Destas, <strong>{len(mudancas_subiu)}</strong> subiram e <strong>{len(mudancas_caiu)}</strong> cairam.</li>
  </ul>
</section>

<footer style="text-align:center; color:var(--gray); padding: 24px; font-size: 0.85rem;">
  Fonte: Semrush - Organic Positions - db=br - subdomain repediu.com.br. Gerado automaticamente.
</footer>

</main>

<script>
const data = {chart_data_json};
new Chart(document.getElementById('chartCounts'), {{
  type: 'bar',
  data: {{
    labels: data.labels,
    datasets: [
      {{ label: 'Marco 2025', data: data.v2025, backgroundColor: '#94a3b8', borderRadius: 6 }},
      {{ label: 'Marco 2026', data: data.v2026, backgroundColor: '#ff642d', borderRadius: 6 }}
    ]
  }},
  options: {{
    responsive: true,
    maintainAspectRatio: false,
    plugins: {{
      legend: {{ position: 'top' }},
      title: {{ display: true, text: 'Quantidade de keywords em Top 1 / Top 5 / Top 10' }}
    }},
    scales: {{ y: {{ beginAtZero: true, ticks: {{ stepSize: 5 }} }} }}
  }}
}});

document.querySelectorAll('.tab').forEach(tab => {{
  tab.addEventListener('click', () => {{
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.pane').forEach(p => p.classList.remove('active'));
    tab.classList.add('active');
    document.getElementById('pane-' + tab.dataset.pane).classList.add('active');
  }});
}});
</script>
</body>
</html>
"""

OUT.write_text(html, encoding="utf-8")
print(f"Relatorio salvo em: {OUT}")
print(f"Tamanho: {OUT.stat().st_size} bytes")
print("")
print("=== Resumo ===")
print(f"Mar/2025: {total_2025} keywords | Top1={len(buckets_2025[1])} Top5={len(buckets_2025[5])} Top10={len(buckets_2025[10])}")
print(f"Mar/2026: {total_2026} keywords | Top1={len(buckets_2026[1])} Top5={len(buckets_2026[5])} Top10={len(buckets_2026[10])}")
print(f"Entraram no Top 10: {len(kws_novos_top10)} | Sairam: {len(kws_perdidos_top10)} | Mantidas: {len(kws_mantidos_top10)}")
print(f"Keywords comuns: {len(comuns)} | Subiram: {len(mudancas_subiu)} | Cairam: {len(mudancas_caiu)}")
