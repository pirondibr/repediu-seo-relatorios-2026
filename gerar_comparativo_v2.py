#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Relatorio SEO v2 - design em abas + coluna Destaque."""

import html as html_escape
import json
import os
import re
from datetime import datetime
from urllib.parse import urlparse

BASE = r"C:\Users\Usuario\OneDrive\Documentos\seo 2026"
FILE_2025 = os.path.join(BASE, "repediu marco 2025.txt")
FILE_2026 = os.path.join(BASE, "repediu marco 2026.txt")
FILE_GSC = os.path.join(BASE, "Desempenho repediu 2026.htm")
OUT = os.path.join(BASE, "relatorio_v2_destaques_2025_vs_2026.html")

# Destaques adicionais na aba (pos. 2025 tratada como ausente: coluna "—", delta NOVA).
# Se a palavra ja existir no export com "sim", a entrada manual substitui a linha (usa a posicao abaixo).
MANUAL_EXTRA_DESTAQUES = [
    ("Crm food delivery", 2),
    ("marketing pizzaria delivery", 4),
    ("marketing para hamburgueria delivery", 4),
    ("como aumentar o lucro do seu restaurante", 7),
    ("marketing para delivery", 15),
    ("sistema para lanchonete delivery", 15),
    ("sistema para hamburgueria delivery", 15),
]

# SERP de exemplo por termo: dominios que aparecem abaixo da Repediu (adicione blocos para mais termos).
SERPS_ULTRAPASSADOS = [
    {
        "termo": "CRM para restaurantes",
        "rows": [
            {"url": "https://repediu.com.br/", "pos": 1, "ours": True},
            {"url": "https://www.pipedrive.com/", "pos": 2, "ours": False},
            {"url": "https://www.kommo.com/", "pos": 3, "ours": False},
            {"url": "https://www.bitrix24.com.br/", "pos": 4, "ours": False},
            {"url": "https://saipos.com/", "pos": 5, "ours": False},
            {"url": "https://www.salesforce.com/", "pos": 6, "ours": False},
        ],
    },
]


def _display_host(url: str) -> str:
    p = urlparse(url)
    return p.netloc if p.netloc else url


def render_ultrapassados_html(serps):
    chunks = []
    for block in serps:
        termo = html_escape.escape(block["termo"])
        chunks.append('<article class="serp-block">')
        chunks.append(f'<h3 class="serp-term-title">Termo: <strong>{termo}</strong></h3>')
        chunks.append('<ul class="serp-results">')
        for row in block["rows"]:
            pos = int(row["pos"])
            url = row["url"]
            ours = row.get("ours", False)
            safe_href = html_escape.escape(url, quote=True)
            host = html_escape.escape(_display_host(url))
            li_cls = "serp-line ours" if ours else "serp-line"
            crown = '<span class="trophy" aria-hidden="true">&#127942;</span> ' if ours else ""
            chunks.append(
                f'<li class="{li_cls}">'
                f'<span class="serp-rank">#{pos}</span>'
                f'<div class="serp-cell">{crown}'
                f'<a class="serp-link" href="{safe_href}" target="_blank" rel="noopener noreferrer">{host}</a>'
                f"</div></li>"
            )
        chunks.append("</ul></article>")
    return "\n".join(chunks)


def _pt_int(n):
    return f"{int(round(n)):,}".replace(",", ".")


def _pt_pct(x):
    return f"{x:.2f}".replace(".", ",") + "%"


def _parse_gsc_numeric_cell(val):
    val = val.replace(",", ".").replace("%", "").strip()
    if val in ("", "—", "-", "–"):
        return None
    try:
        return float(val)
    except ValueError:
        return None


def parse_gsc_saved_html(path):
    """Extrai tabela comparativa (consulta x periodos) de export HTML salvo do Search Console."""
    if not os.path.isfile(path):
        return None
    try:
        text = open(path, encoding="utf-8", errors="replace").read()
    except OSError:
        return None

    fq = re.search(r"\[2,\[&quot;([^&]*?)&quot;\],2,true\]", text)
    filter_query = fq.group(1).strip() if fq else None

    # Periodos do export (comparacao marco a marco)
    period_new = "01/03/2026 – 31/03/2026"
    period_old = "01/03/2025 – 31/03/2025"

    idx = text.find("<tbody>")
    if idx == -1:
        return None
    chunk = text[idx:]
    end = chunk.find("</tbody>")
    if end > 0:
        chunk = chunk[:end]

    trs = re.findall(
        r'<tr[^>]*data-rowid="(\d+)"[^>]*>(.*?)</tr>',
        chunk,
        flags=re.DOTALL | re.IGNORECASE,
    )
    rows_out = []
    sum_c26 = sum_c25 = sum_i26 = sum_i25 = 0

    for _rid, inner in trs:
        kw_m = re.search(r"PkjLuf[^>]*>\s*([^<]+)", inner)
        if not kw_m:
            continue
        kw = kw_m.group(1).strip()
        nums = re.findall(r'data-numeric-value="([^"]+)"', inner)
        if len(nums) < 6:
            continue

        def to_int(x):
            f = _parse_gsc_numeric_cell(x)
            if f is None:
                return None
            return int(round(f))

        c26, c25 = to_int(nums[0]), to_int(nums[1])
        i26, i25 = to_int(nums[3]), to_int(nums[4])
        if c26 is not None and c25 is not None:
            sum_c26 += c26
            sum_c25 += c25
        if i26 is not None and i25 is not None:
            sum_i26 += i26
            sum_i25 += i25

        rows_out.append(
            {
                "kw": kw,
                "c26": c26 or 0,
                "c25": c25 or 0,
                "i26": i26 or 0,
                "i25": i25 or 0,
                "gain_c": (c26 or 0) - (c25 or 0),
            }
        )

    if not rows_out:
        return None

    top_clicks = sorted(rows_out, key=lambda r: r["c26"], reverse=True)[:35]
    top_gain = sorted(rows_out, key=lambda r: r["gain_c"], reverse=True)[:20]

    ctr26 = (100.0 * sum_c26 / sum_i26) if sum_i26 else 0.0
    ctr25 = (100.0 * sum_c25 / sum_i25) if sum_i25 else 0.0

    return {
        "path": path,
        "period_new": period_new,
        "period_old": period_old,
        "filter_query": filter_query,
        "n_rows": len(rows_out),
        "sum_clicks_new": sum_c26,
        "sum_clicks_old": sum_c25,
        "sum_impr_new": sum_i26,
        "sum_impr_old": sum_i25,
        "ctr_new_pct": ctr26,
        "ctr_old_pct": ctr25,
        "top_clicks": top_clicks,
        "top_gain": top_gain,
    }


def build_gsc_tab_body(gsc):
    if not gsc:
        miss = html_escape.escape(os.path.basename(FILE_GSC))
        return f"""
    <section class="card">
      <h2>Google Search Console</h2>
      <p>Arquivo nao encontrado: <strong>{miss}</strong></p>
      <p>Exporte o relatorio de <em>Desempenho</em> (comparacao de periodos) no Search Console e salve como HTML
      na pasta do projeto com esse nome para gerar esta aba automaticamente.</p>
    </section>"""

    fq = gsc.get("filter_query")
    fq_note = (
        f'Filtro de consultas contendo <strong>{html_escape.escape(fq)}</strong> (export original do Search Console).'
        if fq
        else "Nenhum filtro de texto de consulta detectado no HTML exportado."
    )

    def pct(old, new):
        if old == 0:
            return "NOVO" if new > 0 else "—"
        p = (new - old) / old * 100.0
        cls = "up" if p > 0 else "down" if p < 0 else "flat"
        sign = "+" if p > 0 else ""
        return f'<span class="{cls}">{sign}{p:.1f}%</span>'

    rows_html = []
    for i, r in enumerate(gsc["top_clicks"], 1):
        kw = html_escape.escape(r["kw"])
        rows_html.append(
            f"<tr><td class='idx'>{i}</td><td>{kw}</td>"
            f"<td class='num'>{_pt_int(r['c26'])}</td><td class='num'>{_pt_int(r['c25'])}</td>"
            f"<td class='num'>{fmt_delta(r['gain_c'])}</td>"
            f"<td class='num'>{_pt_int(r['i26'])}</td><td class='num'>{_pt_int(r['i25'])}</td></tr>"
        )
    rows_table = "\n".join(rows_html)

    gain_rows = []
    positives = [r for r in gsc["top_gain"] if r["gain_c"] > 0][:20]
    for i, r in enumerate(positives, 1):
        kw = html_escape.escape(r["kw"])
        gain_rows.append(
            f"<tr><td class='idx'>{i}</td><td>{kw}</td>"
            f"<td class='num'>{_pt_int(r['c25'])}</td><td class='num'>{_pt_int(r['c26'])}</td>"
            f"<td class='num up'>+{_pt_int(r['gain_c'])}</td></tr>"
        )
    gain_table = "\n".join(gain_rows) if gain_rows else "<tr><td colspan='5'>Nenhum ganho positivo neste recorte.</td></tr>"

    return f"""
    <section class="card">
      <h2>Search Console &mdash; visitas (cliques) e impressoes</h2>
      <p>Comparacao entre <strong>{html_escape.escape(gsc['period_old'])}</strong> e
      <strong>{html_escape.escape(gsc['period_new'])}</strong>, propriedade <strong>repediu.com.br</strong>
      (Pesquisa na Web).</p>
      <div class="banner info" style="margin-top:14px;">
        {fq_note}
      </div>
      <div class="banner gold" style="margin-top:12px;">
        <strong>Metodo:</strong> os totais abaixo somam as <strong>{_pt_int(gsc['n_rows'])}</strong> linhas da tabela exportada
        (uma por consulta). Esse somatorio pode diferir levemente do total agregado do painel do GSC por
        limites de privacidade e arredondamento; serve como comparativo direto ano a ano no mesmo export.
      </div>
    </section>

    <div class="stats">
      <div class="stat">
        <div class="label">Cliques &mdash; periodo novo</div>
        <div class="val">{_pt_int(gsc['sum_clicks_new'])}</div>
        <div class="sub">{pct(gsc['sum_clicks_old'], gsc['sum_clicks_new'])} vs periodo anterior</div>
      </div>
      <div class="stat">
        <div class="label">Cliques &mdash; periodo antigo</div>
        <div class="val">{_pt_int(gsc['sum_clicks_old'])}</div>
        <div class="sub">Base de comparacao</div>
      </div>
      <div class="stat">
        <div class="label">Impressoes &mdash; periodo novo</div>
        <div class="val">{_pt_int(gsc['sum_impr_new'])}</div>
        <div class="sub">{pct(gsc['sum_impr_old'], gsc['sum_impr_new'])} vs periodo anterior</div>
      </div>
      <div class="stat">
        <div class="label">Impressoes &mdash; periodo antigo</div>
        <div class="val">{_pt_int(gsc['sum_impr_old'])}</div>
        <div class="sub">Base de comparacao</div>
      </div>
      <div class="stat gold">
        <div class="label">CTR medio (linhas somadas)</div>
        <div class="val">{_pt_pct(gsc['ctr_new_pct'])}</div>
        <div class="sub">antes {_pt_pct(gsc['ctr_old_pct'])}</div>
      </div>
    </div>

    <section class="card">
      <h2>Grafico: cliques e impressoes</h2>
      <div class="grid2">
        <div class="chart-wrap sm"><canvas id="chartGscClicks"></canvas></div>
        <div class="chart-wrap sm"><canvas id="chartGscImpr"></canvas></div>
      </div>
    </section>

    <section class="card">
      <h2>Maiores ganhos de cliques (consulta)</h2>
      <table>
        <thead>
          <tr>
            <th>#</th><th>Consulta</th>
            <th class="num">Cliques (antigo)</th><th class="num">Cliques (novo)</th><th class="num">Ganho</th>
          </tr>
        </thead>
        <tbody>{gain_table}</tbody>
      </table>
    </section>

    <section class="card">
      <h2>Top consultas por cliques no periodo novo</h2>
      <div class="scroll-area">
        <table>
          <thead>
            <tr>
              <th>#</th><th>Consulta</th>
              <th class="num">Cliques novo</th><th class="num">Cliques antigo</th><th class="num">Delta</th>
              <th class="num">Impr. novo</th><th class="num">Impr. antigo</th>
            </tr>
          </thead>
          <tbody>{rows_table}</tbody>
        </table>
      </div>
    </section>
    """


def load(path, has_destaque=False):
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            line = line.rstrip("\n")
            if not line.strip() or i == 0:
                continue
            parts = line.split("\t")
            if len(parts) < 2:
                continue
            kw = parts[0].strip()
            try:
                pos = int(parts[1].strip())
            except ValueError:
                continue
            destaque = False
            if has_destaque and len(parts) >= 3:
                destaque = parts[2].strip().lower() == "sim"
            rows.append({"kw": kw, "pos": pos, "destaque": destaque})
    return rows


def bucket(rows):
    b = {"top1": 0, "top3": 0, "top5": 0, "top10": 0, "top20": 0, "top50": 0, "top100": 0}
    for r in rows:
        p = r["pos"]
        if p <= 1: b["top1"] += 1
        if p <= 3: b["top3"] += 1
        if p <= 5: b["top5"] += 1
        if p <= 10: b["top10"] += 1
        if p <= 20: b["top20"] += 1
        if p <= 50: b["top50"] += 1
        if p <= 100: b["top100"] += 1
    return b


def fmt_delta(n):
    if n > 0: return f'<span class="up">+{n}</span>'
    if n < 0: return f'<span class="down">{n}</span>'
    return '<span class="flat">0</span>'


def fmt_pct(old, new):
    if old == 0 and new == 0: return '<span class="flat">—</span>'
    if old == 0: return '<span class="up">NOVO</span>'
    pct = ((new - old) / old) * 100
    cls = "up" if pct > 0 else "down" if pct < 0 else "flat"
    sign = "+" if pct > 0 else ""
    return f'<span class="{cls}">{sign}{pct:.0f}%</span>'


d25 = load(FILE_2025, has_destaque=False)
d26 = load(FILE_2026, has_destaque=True)

b25 = bucket(d25)
b26 = bucket(d26)
total_25, total_26 = len(d25), len(d26)

destaques_raw = [r for r in d26 if r["destaque"]]
_manual_keys = {a[0].lower().strip() for a in MANUAL_EXTRA_DESTAQUES}
destaques_base = [r for r in destaques_raw if r["kw"].lower().strip() not in _manual_keys]
destaques_manual = [
    {"kw": kw, "pos": pos, "destaque": True, "manual": True}
    for kw, pos in MANUAL_EXTRA_DESTAQUES
]
destaques = destaques_base + destaques_manual
destaques.sort(key=lambda x: x["pos"])
dest_bucket = bucket(destaques)

kws_25 = {r["kw"] for r in d25}
kws_26 = {r["kw"] for r in d26}
pos_25 = {}
for r in d25:
    if r["kw"] not in pos_25 or r["pos"] < pos_25[r["kw"]]:
        pos_25[r["kw"]] = r["pos"]
pos_26 = {}
for r in d26:
    if r["kw"] not in pos_26 or r["pos"] < pos_26[r["kw"]]:
        pos_26[r["kw"]] = r["pos"]

common = kws_25 & kws_26
movers = [(k, pos_25[k], pos_26[k], pos_25[k] - pos_26[k]) for k in common]
big_gains = sorted([m for m in movers if m[3] > 0], key=lambda x: -x[3])[:25]
big_losses = sorted([m for m in movers if m[3] < 0], key=lambda x: x[3])[:15]

dest_common = [m for m in movers if m[0] in {r["kw"] for r in destaques}]
dest_new = [r for r in destaques if r["kw"] not in kws_25]


def sorted_in_range(rows, lo, hi):
    out = [(r["kw"], r["pos"], r.get("destaque", False)) for r in rows if lo <= r["pos"] <= hi]
    out.sort(key=lambda x: x[1])
    return out


top1_26 = sorted_in_range(d26, 1, 1)
top2_3_26 = sorted_in_range(d26, 2, 3)
top4_5_26 = sorted_in_range(d26, 4, 5)
top6_10_26 = sorted_in_range(d26, 6, 10)
top1_25 = sorted_in_range(d25, 1, 5)
top6_10_25 = sorted_in_range(d25, 6, 10)


def kw_rows(items, show_star=True):
    out = []
    for i, (k, p, *rest) in enumerate(items, 1):
        star = ""
        if show_star and rest and rest[0]:
            star = '<span class="star" title="Destaque">&#9733;</span> '
        out.append(f"<tr><td class='idx'>{i}</td><td>{star}{k}</td><td class='num'>{p}</td></tr>")
    return "\n".join(out)


def mover_rows(items):
    out = []
    for k, p25, p26, d in items:
        cls = "up" if d > 0 else "down"
        sign = "+" if d > 0 else ""
        out.append(
            f"<tr><td>{k}</td><td class='num'>{p25}</td><td class='num'>{p26}</td>"
            f"<td class='num {cls}'>{sign}{d}</td></tr>"
        )
    return "\n".join(out)


def dest_rows():
    out = []
    for r in destaques:
        k = r["kw"]
        p26 = r["pos"]
        if r.get("manual"):
            delta_cell = "<td class='num up'>NOVA</td>"
            p25_cell = "<td class='num flat'>—</td>"
            status = "Incluida manualmente"
        elif k in pos_25:
            p25 = pos_25[k]
            delta = p25 - p26
            cls = "up" if delta > 0 else "down" if delta < 0 else "flat"
            sign = "+" if delta > 0 else ""
            delta_cell = f"<td class='num {cls}'>{sign}{delta}</td>"
            p25_cell = f"<td class='num'>{p25}</td>"
            status = "Em ambos"
        else:
            delta_cell = "<td class='num up'>NOVA</td>"
            p25_cell = "<td class='num flat'>—</td>"
            status = "Nova em 2026"
        out.append(
            f"<tr><td><span class='star'>&#9733;</span> {k}</td>"
            f"{p25_cell}<td class='num'><strong>{p26}</strong></td>{delta_cell}"
            f"<td><span class='badge'>{status}</span></td></tr>"
        )
    return "\n".join(out)


def report_nav_html(active: str) -> str:
    """Links relativos entre relatorios (file:// ou servidor local). active: idx|v2|v1|legacy."""
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


chart_labels = ["Top 1", "Top 3", "Top 5", "Top 10", "Top 20", "Top 50", "Top 100"]
chart_25 = [b25[k] for k in ["top1","top3","top5","top10","top20","top50","top100"]]
chart_26 = [b26[k] for k in ["top1","top3","top5","top10","top20","top50","top100"]]

now = datetime.now().strftime("%d/%m/%Y %H:%M")

serp_ultrapassados_html = render_ultrapassados_html(SERPS_ULTRAPASSADOS)
n_ultrapassados_termos = len(SERPS_ULTRAPASSADOS)

gsc_data = parse_gsc_saved_html(FILE_GSC)
gsc_tab_body = build_gsc_tab_body(gsc_data)
gsc_pill = _pt_int(gsc_data["n_rows"]) if gsc_data else "—"
if gsc_data:
    gsc_chart_payload = json.dumps(
        {
            "ok": True,
            "clicks25": gsc_data["sum_clicks_old"],
            "clicks26": gsc_data["sum_clicks_new"],
            "impr25": gsc_data["sum_impr_old"],
            "impr26": gsc_data["sum_impr_new"],
        }
    )
else:
    gsc_chart_payload = json.dumps({"ok": False})

nav_block = report_nav_html("v2")

html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Relatorio SEO v2 - Repediu | Destaques + Comparativo 2025 vs 2026</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<style>
  :root {{
    --bg: #0f172a;
    --panel: #1e293b;
    --panel-2: #334155;
    --text: #e2e8f0;
    --muted: #94a3b8;
    --accent: #38bdf8;
    --accent-2: #a78bfa;
    --gold: #fbbf24;
    --green: #10b981;
    --red: #ef4444;
    --border: #334155;
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background: var(--bg);
    color: var(--text);
    line-height: 1.6;
    min-height: 100vh;
  }}
  .container {{ max-width: 1280px; margin: 0 auto; padding: 30px 20px; }}

  header.hero {{
    background: radial-gradient(circle at top left, #1e3a8a 0%, transparent 50%),
                radial-gradient(circle at bottom right, #7c3aed 0%, transparent 50%),
                #0f172a;
    padding: 60px 30px;
    border-radius: 20px;
    margin-bottom: 30px;
    border: 1px solid var(--border);
    text-align: center;
    position: relative;
    overflow: hidden;
  }}
  .hero h1 {{
    font-size: 2.8rem;
    font-weight: 800;
    background: linear-gradient(135deg, #38bdf8 0%, #a78bfa 50%, #f472b6 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin-bottom: 12px;
  }}
  .hero .domain {{ font-size: 1.3rem; color: var(--accent); font-weight: 600; }}
  .hero .sub {{ color: var(--muted); margin-top: 8px; font-size: 1rem; }}

  nav.tabs {{
    display: flex;
    gap: 4px;
    margin-bottom: 24px;
    background: var(--panel);
    padding: 6px;
    border-radius: 14px;
    border: 1px solid var(--border);
    overflow-x: auto;
  }}
  .tab-btn {{
    padding: 12px 20px;
    background: transparent;
    border: none;
    color: var(--muted);
    font-weight: 600;
    cursor: pointer;
    border-radius: 10px;
    white-space: nowrap;
    transition: all 0.2s;
    font-size: 0.93rem;
    font-family: inherit;
  }}
  .tab-btn:hover {{ color: var(--text); background: rgba(255,255,255,0.03); }}
  .tab-btn.active {{
    background: linear-gradient(135deg, var(--accent) 0%, var(--accent-2) 100%);
    color: #0f172a;
    box-shadow: 0 4px 15px rgba(56, 189, 248, 0.3);
  }}
  .tab-btn .pill {{
    display: inline-block;
    margin-left: 6px;
    padding: 2px 8px;
    background: rgba(0,0,0,0.2);
    border-radius: 10px;
    font-size: 0.75rem;
    font-weight: 700;
  }}
  .tab-btn.active .pill {{ background: rgba(255,255,255,0.25); color: #0f172a; }}
  .tab-btn.gold.active {{ background: linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%); box-shadow: 0 4px 15px rgba(251, 191, 36, 0.4); }}

  .panel {{ display: none; animation: fadeIn 0.3s; }}
  .panel.active {{ display: block; }}
  @keyframes fadeIn {{ from {{ opacity: 0; transform: translateY(6px); }} to {{ opacity: 1; transform: translateY(0); }} }}

  section.card {{
    background: var(--panel);
    border-radius: 16px;
    padding: 28px;
    margin-bottom: 22px;
    border: 1px solid var(--border);
  }}
  section.card h2 {{
    font-size: 1.5rem;
    margin-bottom: 16px;
    color: #fff;
    display: flex;
    align-items: center;
    gap: 10px;
  }}
  section.card h2::before {{
    content: '';
    width: 4px;
    height: 22px;
    background: linear-gradient(135deg, var(--accent) 0%, var(--accent-2) 100%);
    border-radius: 3px;
  }}
  section.card h3 {{ color: #fff; font-size: 1.1rem; margin: 22px 0 12px; }}
  section.card p {{ color: var(--muted); margin-bottom: 10px; }}

  .stats {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 16px;
    margin-bottom: 24px;
  }}
  .stat {{
    background: linear-gradient(135deg, rgba(56,189,248,0.08) 0%, rgba(167,139,250,0.08) 100%);
    border: 1px solid var(--border);
    padding: 22px;
    border-radius: 14px;
    position: relative;
    overflow: hidden;
  }}
  .stat.gold {{ background: linear-gradient(135deg, rgba(251,191,36,0.12) 0%, rgba(245,158,11,0.08) 100%); border-color: rgba(251,191,36,0.3); }}
  .stat .label {{ color: var(--muted); font-size: 0.78rem; text-transform: uppercase; letter-spacing: 1px; font-weight: 600; }}
  .stat .val {{ font-size: 2.3rem; font-weight: 800; color: #fff; margin-top: 6px; line-height: 1; }}
  .stat .sub {{ font-size: 0.85rem; margin-top: 10px; color: var(--muted); }}

  table {{ width: 100%; border-collapse: collapse; font-size: 0.92rem; }}
  th, td {{ padding: 11px 14px; text-align: left; border-bottom: 1px solid var(--border); }}
  th {{
    background: rgba(0,0,0,0.25);
    color: var(--muted);
    font-size: 0.76rem;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    font-weight: 600;
  }}
  td {{ color: var(--text); }}
  td.num {{ text-align: right; font-variant-numeric: tabular-nums; font-weight: 600; }}
  td.idx {{ color: var(--muted); width: 40px; font-size: 0.85rem; }}
  tr:hover td {{ background: rgba(255,255,255,0.02); }}

  .up {{ color: var(--green); font-weight: 700; }}
  .down {{ color: var(--red); font-weight: 700; }}
  .flat {{ color: var(--muted); }}
  .star {{ color: var(--gold); font-size: 1rem; }}

  .badge {{
    display: inline-block;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 600;
    background: rgba(167, 139, 250, 0.15);
    color: var(--accent-2);
    border: 1px solid rgba(167, 139, 250, 0.3);
  }}

  .chart-wrap {{ position: relative; height: 420px; margin-top: 16px; }}
  .chart-wrap.sm {{ height: 320px; }}

  .grid2 {{ display: grid; grid-template-columns: 1fr 1fr; gap: 22px; }}
  @media (max-width: 820px) {{
    .grid2 {{ grid-template-columns: 1fr; }}
    .hero h1 {{ font-size: 2rem; }}
  }}

  .banner {{
    padding: 22px;
    border-radius: 14px;
    margin-bottom: 20px;
    font-size: 1rem;
    border: 1px solid;
  }}
  .banner.success {{
    background: rgba(16, 185, 129, 0.08);
    border-color: rgba(16, 185, 129, 0.3);
    color: #a7f3d0;
  }}
  .banner.info {{
    background: rgba(56, 189, 248, 0.08);
    border-color: rgba(56, 189, 248, 0.3);
    color: #bae6fd;
  }}
  .banner.gold {{
    background: linear-gradient(135deg, rgba(251,191,36,0.1) 0%, rgba(245,158,11,0.05) 100%);
    border-color: rgba(251,191,36,0.35);
    color: #fde68a;
  }}
  .banner strong {{ color: #fff; }}

  .kpi-row {{
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 14px;
    margin: 16px 0;
  }}
  @media (max-width: 720px) {{ .kpi-row {{ grid-template-columns: 1fr; }} }}
  .kpi {{
    background: rgba(0,0,0,0.25);
    border-radius: 12px;
    padding: 16px;
    text-align: center;
    border: 1px solid var(--border);
  }}
  .kpi .k {{ color: var(--muted); font-size: 0.8rem; }}
  .kpi .v {{ color: #fff; font-size: 1.6rem; font-weight: 800; margin-top: 4px; }}

  ul.ins {{ padding-left: 20px; line-height: 2; }}
  ul.ins li {{ color: var(--text); }}
  ul.ins li strong {{ color: var(--accent); }}

  footer.foot {{
    text-align: center;
    color: var(--muted);
    padding: 26px;
    font-size: 0.85rem;
    border-top: 1px solid var(--border);
    margin-top: 20px;
  }}

  .scroll-area {{ max-height: 520px; overflow-y: auto; border-radius: 10px; }}
  .scroll-area::-webkit-scrollbar {{ width: 8px; }}
  .scroll-area::-webkit-scrollbar-track {{ background: rgba(0,0,0,0.2); border-radius: 4px; }}
  .scroll-area::-webkit-scrollbar-thumb {{ background: var(--panel-2); border-radius: 4px; }}

  .tab-btn.ultras.active {{
    background: linear-gradient(135deg, #10b981 0%, #059669 100%);
    box-shadow: 0 4px 15px rgba(16, 185, 129, 0.35);
  }}
  .serp-block {{
    margin-bottom: 28px;
    padding: 22px;
    background: rgba(15, 23, 42, 0.5);
    border: 1px solid var(--border);
    border-radius: 14px;
  }}
  .serp-term-title {{
    font-size: 1.15rem;
    margin-bottom: 16px;
    color: #f1f5f9;
    font-weight: 600;
  }}
  .serp-term-title strong {{ color: #38bdf8; }}
  .serp-results {{ list-style: none; padding: 0; margin: 0; }}
  .serp-line {{
    display: flex;
    align-items: center;
    gap: 14px;
    padding: 12px 14px;
    border-radius: 10px;
    margin-bottom: 8px;
    border: 1px solid var(--border);
    background: rgba(0,0,0,0.2);
  }}
  .serp-line.ours {{
    border-color: rgba(251, 191, 36, 0.55);
    background: linear-gradient(90deg, rgba(251,191,36,0.12) 0%, rgba(15,23,42,0.4) 100%);
  }}
  .serp-rank {{
    flex-shrink: 0;
    min-width: 42px;
    font-weight: 800;
    font-size: 0.95rem;
    color: var(--muted);
    font-variant-numeric: tabular-nums;
  }}
  .serp-line.ours .serp-rank {{ color: #fbbf24; }}
  .serp-cell {{ flex: 1; display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }}
  .serp-link {{ color: var(--accent); font-weight: 600; text-decoration: none; word-break: break-all; }}
  .serp-link:hover {{ text-decoration: underline; color: #7dd3fc; }}
  .trophy {{ font-size: 1.1rem; line-height: 1; }}

  .page-links {{
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 10px 14px;
    padding: 14px 18px;
    margin-bottom: 22px;
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 12px;
    font-size: 0.88rem;
  }}
  .page-links-title {{
    color: var(--muted);
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    font-size: 0.72rem;
  }}
  .page-links a {{
    color: #7dd3fc;
    font-weight: 600;
    text-decoration: none;
    padding: 6px 12px;
    border-radius: 8px;
    border: 1px solid transparent;
  }}
  .page-links a:hover {{
    background: rgba(56, 189, 248, 0.12);
    border-color: rgba(56, 189, 248, 0.25);
    color: #e0f2fe;
  }}
  .page-links a.is-current {{
    background: rgba(167, 139, 250, 0.35);
    color: #f8fafc;
    pointer-events: none;
    cursor: default;
    border-color: rgba(167, 139, 250, 0.5);
  }}

  .tab-btn.gsc.active {{
    background: linear-gradient(135deg, #22d3ee 0%, #0ea5e9 100%);
    box-shadow: 0 4px 15px rgba(14, 165, 233, 0.35);
  }}
</style>
</head>
<body>
<div class="container">
{nav_block}

  <header class="hero">
    <h1>Relatorio SEO v2 &mdash; Destaques &amp; Performance</h1>
    <div class="domain">repediu.com.br</div>
    <div class="sub">Marco 2025 vs Marco 2026 &middot; {len(destaques)} palavras em destaque</div>
  </header>

  <nav class="tabs">
    <button class="tab-btn active" data-tab="visao">Visao Geral</button>
    <button class="tab-btn gold" data-tab="destaques">&#9733; Destaques <span class="pill">{len(destaques)}</span></button>
    <button class="tab-btn" data-tab="top">Top 1 / 5 / 10</button>
    <button class="tab-btn" data-tab="movers">Ganhos &amp; Perdas</button>
    <button class="tab-btn" data-tab="novas">Novas Palavras</button>
    <button class="tab-btn gsc" data-tab="gsc">Search Console <span class="pill">{gsc_pill}</span></button>
    <button class="tab-btn ultras" data-tab="ultrapassados">Ultrapassamos <span class="pill">{n_ultrapassados_termos}</span></button>
    <button class="tab-btn" data-tab="insights">Insights</button>
  </nav>

  <!-- ================== TAB: VISAO GERAL ================== -->
  <div class="panel active" id="tab-visao">

    <div class="stats">
      <div class="stat">
        <div class="label">Total de Keywords</div>
        <div class="val">{total_26}</div>
        <div class="sub">{fmt_delta(total_26 - total_25)} &middot; {fmt_pct(total_25, total_26)} vs 2025</div>
      </div>
      <div class="stat">
        <div class="label">Top 1</div>
        <div class="val">{b26["top1"]}</div>
        <div class="sub">{fmt_delta(b26["top1"] - b25["top1"])} vs {b25["top1"]} em 2025</div>
      </div>
      <div class="stat">
        <div class="label">Top 5</div>
        <div class="val">{b26["top5"]}</div>
        <div class="sub">{fmt_delta(b26["top5"] - b25["top5"])} vs {b25["top5"]} em 2025</div>
      </div>
      <div class="stat">
        <div class="label">Top 10</div>
        <div class="val">{b26["top10"]}</div>
        <div class="sub">{fmt_delta(b26["top10"] - b25["top10"])} vs {b25["top10"]} em 2025</div>
      </div>
      <div class="stat gold">
        <div class="label">&#9733; Destaques</div>
        <div class="val">{len(destaques)}</div>
        <div class="sub">Palavras estrategicas monitoradas</div>
      </div>
    </div>

    <section class="card">
      <h2>Resumo Executivo</h2>
      <div class="banner success">
        Em 12 meses, <strong>repediu.com.br</strong> passou de <strong>{total_25}</strong> para <strong>{total_26}</strong>
        palavras rankeadas ({fmt_pct(total_25, total_26)}), com <strong>{b26["top1"]}</strong> palavras em 1a posicao
        (antes {b25["top1"]}) e <strong>{b26["top10"]}</strong> palavras no Top 10 (antes {b25["top10"]}).
      </div>
      <div class="banner gold">
        <strong>&#9733; {len(destaques)} palavras de destaque</strong> foram selecionadas para acompanhamento estrategico.
        Destas, <strong>{dest_bucket["top5"]}</strong> ja estao no Top 5 e <strong>{dest_bucket["top10"]}</strong> no Top 10.
      </div>
    </section>

    <section class="card">
      <h2>Distribuicao por Faixa de Posicao</h2>
      <div class="chart-wrap">
        <canvas id="chartBars"></canvas>
      </div>
      <table style="margin-top: 20px;">
        <thead>
          <tr>
            <th>Faixa</th>
            <th class="num">Mar/2025</th>
            <th class="num">Mar/2026</th>
            <th class="num">Delta</th>
            <th class="num">Variacao %</th>
          </tr>
        </thead>
        <tbody>
          <tr><td>Top 1</td><td class="num">{b25["top1"]}</td><td class="num">{b26["top1"]}</td><td class="num">{fmt_delta(b26["top1"] - b25["top1"])}</td><td class="num">{fmt_pct(b25["top1"], b26["top1"])}</td></tr>
          <tr><td>Top 3</td><td class="num">{b25["top3"]}</td><td class="num">{b26["top3"]}</td><td class="num">{fmt_delta(b26["top3"] - b25["top3"])}</td><td class="num">{fmt_pct(b25["top3"], b26["top3"])}</td></tr>
          <tr><td>Top 5</td><td class="num">{b25["top5"]}</td><td class="num">{b26["top5"]}</td><td class="num">{fmt_delta(b26["top5"] - b25["top5"])}</td><td class="num">{fmt_pct(b25["top5"], b26["top5"])}</td></tr>
          <tr><td>Top 10</td><td class="num">{b25["top10"]}</td><td class="num">{b26["top10"]}</td><td class="num">{fmt_delta(b26["top10"] - b25["top10"])}</td><td class="num">{fmt_pct(b25["top10"], b26["top10"])}</td></tr>
          <tr><td>Top 20</td><td class="num">{b25["top20"]}</td><td class="num">{b26["top20"]}</td><td class="num">{fmt_delta(b26["top20"] - b25["top20"])}</td><td class="num">{fmt_pct(b25["top20"], b26["top20"])}</td></tr>
          <tr><td>Top 50</td><td class="num">{b25["top50"]}</td><td class="num">{b26["top50"]}</td><td class="num">{fmt_delta(b26["top50"] - b25["top50"])}</td><td class="num">{fmt_pct(b25["top50"], b26["top50"])}</td></tr>
          <tr><td>Top 100</td><td class="num">{b25["top100"]}</td><td class="num">{b26["top100"]}</td><td class="num">{fmt_delta(b26["top100"] - b25["top100"])}</td><td class="num">{fmt_pct(b25["top100"], b26["top100"])}</td></tr>
        </tbody>
      </table>
    </section>

    <section class="card">
      <h2>Comparativo Top 1 / Top 5 / Top 10</h2>
      <div class="chart-wrap sm">
        <canvas id="chartKey"></canvas>
      </div>
    </section>
  </div>

  <!-- ================== TAB: DESTAQUES ================== -->
  <div class="panel" id="tab-destaques">
    <section class="card">
      <h2>&#9733; Palavras-Chave em Destaque</h2>
      <p>Total: <strong>{len(destaques)}</strong> palavras marcadas como estrategicas para o negocio.</p>

      <div class="kpi-row">
        <div class="kpi"><div class="k">Top 1</div><div class="v">{dest_bucket["top1"]}</div></div>
        <div class="kpi"><div class="k">Top 3</div><div class="v">{dest_bucket["top3"]}</div></div>
        <div class="kpi"><div class="k">Top 5</div><div class="v">{dest_bucket["top5"]}</div></div>
        <div class="kpi"><div class="k">Top 10</div><div class="v">{dest_bucket["top10"]}</div></div>
        <div class="kpi"><div class="k">Top 20</div><div class="v">{dest_bucket["top20"]}</div></div>
        <div class="kpi"><div class="k">Novas em 2026</div><div class="v">{len(dest_new)}</div></div>
      </div>

      <div class="banner gold">
        Das <strong>{len(destaques)}</strong> palavras em destaque, <strong>{dest_bucket["top10"]}</strong> ({(dest_bucket["top10"]/len(destaques)*100):.0f}%)
        ja estao no Top 10 e <strong>{dest_bucket["top5"]}</strong> ({(dest_bucket["top5"]/len(destaques)*100):.0f}%) no Top 5.
      </div>

      <h3>Lista completa de destaques com comparativo</h3>
      <table>
        <thead>
          <tr>
            <th>Palavra-Chave</th>
            <th class="num">Pos. 2025</th>
            <th class="num">Pos. 2026</th>
            <th class="num">Delta</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>{dest_rows()}</tbody>
      </table>
    </section>

    <section class="card">
      <h2>Distribuicao das Palavras de Destaque</h2>
      <div class="chart-wrap sm">
        <canvas id="chartDest"></canvas>
      </div>
    </section>
  </div>

  <!-- ================== TAB: TOP ================== -->
  <div class="panel" id="tab-top">
    <section class="card">
      <h2>Top 1 &mdash; Posicao #1 em Marco/2026</h2>
      <p>{b26["top1"]} palavras ocupam a 1a posicao (em 2025 eram {b25["top1"]}).</p>
      <table>
        <thead><tr><th>#</th><th>Palavra-Chave</th><th class="num">Posicao</th></tr></thead>
        <tbody>{kw_rows(top1_26)}</tbody>
      </table>
    </section>

    <section class="card">
      <h2>Top 5 &mdash; Posicoes 2 a 5 (Mar/2026)</h2>
      <p>{len(top2_3_26) + len(top4_5_26)} palavras entre as posicoes 2 e 5.</p>
      <h3>Posicoes 2 e 3</h3>
      <table>
        <thead><tr><th>#</th><th>Palavra-Chave</th><th class="num">Posicao</th></tr></thead>
        <tbody>{kw_rows(top2_3_26)}</tbody>
      </table>
      <h3>Posicoes 4 e 5</h3>
      <table>
        <thead><tr><th>#</th><th>Palavra-Chave</th><th class="num">Posicao</th></tr></thead>
        <tbody>{kw_rows(top4_5_26)}</tbody>
      </table>
    </section>

    <section class="card">
      <h2>Top 10 &mdash; Posicoes 6 a 10 (Mar/2026)</h2>
      <table>
        <thead><tr><th>#</th><th>Palavra-Chave</th><th class="num">Posicao</th></tr></thead>
        <tbody>{kw_rows(top6_10_26)}</tbody>
      </table>
    </section>

    <section class="card">
      <h2>Referencia 2025 &mdash; Top 10 de Marco/2025</h2>
      <h3>Posicoes 1 a 5</h3>
      <table>
        <thead><tr><th>#</th><th>Palavra-Chave</th><th class="num">Posicao</th></tr></thead>
        <tbody>{kw_rows(top1_25, show_star=False)}</tbody>
      </table>
      <h3>Posicoes 6 a 10</h3>
      <table>
        <thead><tr><th>#</th><th>Palavra-Chave</th><th class="num">Posicao</th></tr></thead>
        <tbody>{kw_rows(top6_10_25, show_star=False)}</tbody>
      </table>
    </section>
  </div>

  <!-- ================== TAB: GANHOS & PERDAS ================== -->
  <div class="panel" id="tab-movers">
    <section class="card">
      <h2>Maiores Ganhos de Ranking (2025 &rarr; 2026)</h2>
      <p>Palavras presentes em ambos os periodos que mais subiram posicoes.</p>
      <table>
        <thead>
          <tr>
            <th>Palavra-Chave</th>
            <th class="num">Pos. 2025</th>
            <th class="num">Pos. 2026</th>
            <th class="num">Delta</th>
          </tr>
        </thead>
        <tbody>{mover_rows(big_gains)}</tbody>
      </table>
    </section>

    <section class="card">
      <h2>Maiores Perdas de Ranking</h2>
      <table>
        <thead>
          <tr>
            <th>Palavra-Chave</th>
            <th class="num">Pos. 2025</th>
            <th class="num">Pos. 2026</th>
            <th class="num">Delta</th>
          </tr>
        </thead>
        <tbody>{mover_rows(big_losses)}</tbody>
      </table>
    </section>
  </div>

  <!-- ================== TAB: NOVAS PALAVRAS ================== -->
  <div class="panel" id="tab-novas">
    <section class="card">
      <h2>Novas Palavras no Top 10 em 2026</h2>
      <p>Keywords que nao rankeavam em 2025 e agora estao no Top 10.</p>
      <div class="scroll-area">
        <table>
          <thead><tr><th>#</th><th>Palavra-Chave</th><th class="num">Posicao</th></tr></thead>
          <tbody>{kw_rows([(k, pos_26[k], any(r["destaque"] and r["kw"]==k for r in d26)) for k in sorted(kws_26 - kws_25, key=lambda x: pos_26[x]) if pos_26[k] <= 10])}</tbody>
        </table>
      </div>
    </section>

    <section class="card">
      <h2>Novas Palavras no Top 20 em 2026</h2>
      <div class="scroll-area">
        <table>
          <thead><tr><th>#</th><th>Palavra-Chave</th><th class="num">Posicao</th></tr></thead>
          <tbody>{kw_rows([(k, pos_26[k], any(r["destaque"] and r["kw"]==k for r in d26)) for k in sorted(kws_26 - kws_25, key=lambda x: pos_26[x]) if 11 <= pos_26[k] <= 20])}</tbody>
        </table>
      </div>
    </section>
  </div>

  <!-- ================== TAB: SEARCH CONSOLE (GSC) ================== -->
  <div class="panel" id="tab-gsc">
    {gsc_tab_body}
  </div>

  <!-- ================== TAB: EMPRESAS ULTRAPASSADAS ================== -->
  <div class="panel" id="tab-ultrapassados">
    <section class="card">
      <h2>Empresas que ultrapassamos no SERP</h2>
      <p>Por termo de busca, a posicao da <strong>repediu.com.br</strong> em relacao a outros dominios que aparecem no Google
      (exemplo ilustrativo do ranking organico; complemente com novos termos editando a lista
      <code style="color:var(--accent);">SERPS_ULTRAPASSADOS</code> em <code style="color:var(--accent);">gerar_comparativo_v2.py</code>).</p>
      <div class="banner success" style="margin-top:16px;">
        <strong>Conceito:</strong> mostra em qual posicao o site da Repediu aparece e quais marcas conhecidas do mercado
        ficam logo abaixo &mdash; util para apresentacoes comerciais e prova de autoridade no nicho.
      </div>
    </section>
    <section class="card">
      <h2>Exemplos por termo</h2>
      {serp_ultrapassados_html}
    </section>
  </div>

  <!-- ================== TAB: INSIGHTS ================== -->
  <div class="panel" id="tab-insights">
    <section class="card">
      <h2>Insights Estrategicos</h2>
      <div class="banner success">
        <strong>Crescimento excepcional:</strong> +{total_26 - total_25} novas palavras rankeadas em 12 meses
        ({fmt_pct(total_25, total_26)}) indica mudanca estrutural positiva do site.
      </div>
      <div class="banner info">
        <strong>Consolidacao de marca:</strong> A palavra "repediu" conquistou a 1a posicao, confirmando que o Google
        reconhece o novo branding.
      </div>
      <div class="banner gold">
        <strong>Destaques comerciais:</strong> {dest_bucket["top5"]} das {len(destaques)} palavras estrategicas ja estao no Top 5,
        gerando alta probabilidade de conversao.
      </div>

      <h3>Recomendacoes</h3>
      <ul class="ins">
        <li><strong>Acelerar destaques no Top 6-20:</strong> existem {dest_bucket["top20"] - dest_bucket["top5"]} palavras de destaque que ainda nao estao no Top 5 &mdash; priorizar link building e otimizacao on-page.</li>
        <li><strong>Cluster CRM:</strong> termos como "crm para restaurantes" ja estao no Top 2 &mdash; criar hub de conteudo para dominar todas as variacoes.</li>
        <li><strong>Cluster WhatsApp:</strong> forte performance em "whatsapp business", "lista de transmissao" e "selo verificado" &mdash; ampliar com guias praticos e comparativos.</li>
        <li><strong>Cluster Delivery:</strong> "plataforma de delivery", "empresas de delivery" e "food marketing" no Top 5 reforcam posicionamento B2B.</li>
        <li><strong>Monitorar perdas:</strong> analisar pags com queda de ranking para identificar canibalizacao ou queda de autoridade.</li>
        <li><strong>Expansao Top 100 &rarr; Top 20:</strong> {b26["top100"] - b26["top20"]} palavras entre 21-100 sao o proximo funil de crescimento organico.</li>
      </ul>
    </section>
  </div>

  <footer class="foot">
    Relatorio v2 gerado em {now} &middot; Fonte: exports Semrush (mar/2025 e mar/2026)
  </footer>

</div>

<script>
document.querySelectorAll('.tab-btn').forEach(btn => {{
  btn.addEventListener('click', () => {{
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
    btn.classList.add('active');
    document.getElementById('tab-' + btn.dataset.tab).classList.add('active');
    window.scrollTo({{ top: 0, behavior: 'smooth' }});
  }});
}});

Chart.defaults.color = '#94a3b8';
Chart.defaults.borderColor = '#334155';

new Chart(document.getElementById('chartBars'), {{
  type: 'bar',
  data: {{
    labels: {json.dumps(chart_labels)},
    datasets: [
      {{ label: 'Mar/2025', data: {json.dumps(chart_25)}, backgroundColor: '#ef4444', borderRadius: 6 }},
      {{ label: 'Mar/2026', data: {json.dumps(chart_26)}, backgroundColor: '#38bdf8', borderRadius: 6 }}
    ]
  }},
  options: {{
    responsive: true, maintainAspectRatio: false,
    plugins: {{ legend: {{ position: 'top', labels: {{ color: '#e2e8f0', font: {{ weight: '600' }} }} }} }},
    scales: {{
      y: {{ beginAtZero: true, grid: {{ color: 'rgba(148, 163, 184, 0.1)' }} }},
      x: {{ grid: {{ display: false }} }}
    }}
  }}
}});

new Chart(document.getElementById('chartKey'), {{
  type: 'bar',
  data: {{
    labels: ['Top 1', 'Top 5', 'Top 10'],
    datasets: [
      {{ label: 'Mar/2025', data: [{b25["top1"]}, {b25["top5"]}, {b25["top10"]}], backgroundColor: '#ef4444', borderRadius: 8 }},
      {{ label: 'Mar/2026', data: [{b26["top1"]}, {b26["top5"]}, {b26["top10"]}], backgroundColor: '#a78bfa', borderRadius: 8 }}
    ]
  }},
  options: {{
    responsive: true, maintainAspectRatio: false,
    plugins: {{ legend: {{ position: 'top', labels: {{ color: '#e2e8f0', font: {{ weight: '600' }} }} }} }},
    scales: {{
      y: {{ beginAtZero: true, grid: {{ color: 'rgba(148, 163, 184, 0.1)' }} }},
      x: {{ grid: {{ display: false }} }}
    }}
  }}
}});

new Chart(document.getElementById('chartDest'), {{
  type: 'doughnut',
  data: {{
    labels: ['Top 1', 'Top 2-3', 'Top 4-5', 'Top 6-10', 'Top 11-20', 'Acima de 20'],
    datasets: [{{
      data: [
        {dest_bucket["top1"]},
        {dest_bucket["top3"] - dest_bucket["top1"]},
        {dest_bucket["top5"] - dest_bucket["top3"]},
        {dest_bucket["top10"] - dest_bucket["top5"]},
        {dest_bucket["top20"] - dest_bucket["top10"]},
        {len(destaques) - dest_bucket["top20"]}
      ],
      backgroundColor: ['#fbbf24', '#38bdf8', '#a78bfa', '#34d399', '#f472b6', '#64748b'],
      borderColor: '#1e293b',
      borderWidth: 2
    }}]
  }},
  options: {{
    responsive: true, maintainAspectRatio: false,
    plugins: {{ legend: {{ position: 'right', labels: {{ color: '#e2e8f0', font: {{ weight: '600' }}, padding: 12 }} }} }}
  }}
}});

(function(){{
  var g = __GSC_JSON__;
  if (!g || !g.ok) return;
  var elC = document.getElementById('chartGscClicks');
  var elI = document.getElementById('chartGscImpr');
  if (!elC || !elI) return;
  new Chart(elC, {{
    type: 'bar',
    data: {{
      labels: ['Mar/2025', 'Mar/2026'],
      datasets: [{{
        label: 'Cliques',
        data: [g.clicks25, g.clicks26],
        backgroundColor: ['#ef4444', '#34d399'],
        borderRadius: 8
      }}]
    }},
    options: {{
      responsive: true, maintainAspectRatio: false,
      plugins: {{
        legend: {{ display: false }},
        title: {{ display: true, text: 'Cliques (soma consultas exportadas)', color: '#e2e8f0', font: {{ weight: '600', size: 13 }} }}
      }},
      scales: {{
        y: {{ beginAtZero: true, grid: {{ color: 'rgba(148, 163, 184, 0.1)' }} }},
        x: {{ grid: {{ display: false }} }}
      }}
    }}
  }});
  new Chart(elI, {{
    type: 'bar',
    data: {{
      labels: ['Mar/2025', 'Mar/2026'],
      datasets: [{{
        label: 'Impressoes',
        data: [g.impr25, g.impr26],
        backgroundColor: ['#f97316', '#38bdf8'],
        borderRadius: 8
      }}]
    }},
    options: {{
      responsive: true, maintainAspectRatio: false,
      plugins: {{
        legend: {{ display: false }},
        title: {{ display: true, text: 'Impressoes (soma consultas exportadas)', color: '#e2e8f0', font: {{ weight: '600', size: 13 }} }}
      }},
      scales: {{
        y: {{ beginAtZero: true, grid: {{ color: 'rgba(148, 163, 184, 0.1)' }} }},
        x: {{ grid: {{ display: false }} }}
      }}
    }}
  }});
}})();
</script>
</body>
</html>
"""

html = html.replace("__GSC_JSON__", gsc_chart_payload)

with open(OUT, "w", encoding="utf-8") as f:
    f.write(html)

# Copia sem barra de navegacao local para GitHub Pages (pasta /docs, so index.html).
docs_dir = os.path.join(BASE, "docs")
os.makedirs(docs_dir, exist_ok=True)
out_pages = os.path.join(docs_dir, "index.html")
pages_html = html.replace(nav_block, "", 1)
with open(out_pages, "w", encoding="utf-8") as f:
    f.write(pages_html)
_nojekyll = os.path.join(docs_dir, ".nojekyll")
if not os.path.isfile(_nojekyll):
    open(_nojekyll, "w", encoding="utf-8").close()

print(f"[OK] GitHub Pages (docs/index.html): {out_pages}")

print(f"[OK] 2025: {total_25} keywords  |  2026: {total_26} keywords")
print(f"[OK] Destaques: {len(destaques)} palavras")
print(f"[OK] Destaques Top 5: {dest_bucket['top5']}  |  Top 10: {dest_bucket['top10']}")
if gsc_data:
    print(
        f"[OK] Search Console: {gsc_data['n_rows']} consultas no export | "
        f"cliques {gsc_data['sum_clicks_old']} -> {gsc_data['sum_clicks_new']} | "
        f"impressoes {_pt_int(gsc_data['sum_impr_old'])} -> {_pt_int(gsc_data['sum_impr_new'])}"
    )
else:
    print(f"[!] Search Console: nao leu {os.path.basename(FILE_GSC)}")
print(f"[OK] Arquivo: {OUT}")
