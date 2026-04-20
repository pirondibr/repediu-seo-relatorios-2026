"""Parse Semrush snapshot YAML files and export to XLSX."""
import re
import openpyxl
from pathlib import Path

SNAPSHOTS = [
    r"C:\Users\Usuario\.cursor\browser-logs\snapshot-2026-04-20T12-04-12-948Z-jcubs7.log",  # page 1
    r"C:\Users\Usuario\.cursor\browser-logs\snapshot-2026-04-20T12-06-30-021Z-ye37ex.log",  # page 2
    r"C:\Users\Usuario\.cursor\browser-logs\snapshot-2026-04-20T12-07-00-867Z-c15662.log",  # page 3
]

OUTPUT = r"C:\Users\Usuario\OneDrive\Documentos\seo 2026\repediu_semrush_positions_202503.xlsx"


def extract_gridcells(path: str):
    """Extract ordered list of gridcell name values from snapshot yaml."""
    text = Path(path).read_text(encoding="utf-8")
    # Find region between columnheader URL and the pagination
    # We look for all gridcell blocks and capture their name
    cells = []
    # Pattern: - role: gridcell\n      name: <value>\n      ref: ...
    pattern = re.compile(
        r"- role: gridcell\s*\n\s+name: (.+?)\n\s+ref: e\d+",
        re.MULTILINE,
    )
    for m in pattern.finditer(text):
        val = m.group(1).strip()
        # strip surrounding quotes if present
        if val.startswith('"') and val.endswith('"'):
            val = val[1:-1]
        cells.append(val)
    return cells


def parse_rows(cells):
    """Convert flat cell list into rows using URL (starts with repediu) as row terminator."""
    rows = []
    current = []
    for c in cells:
        current.append(c)
        if c.startswith("repediu.com.br") or c == "repediu.com.br/":
            rows.append(current)
            current = []
    # Discard trailing leftovers (partial row)
    return rows


def normalize_row(row):
    """Row has 9 (with SF) or 8 (no SF) items.
    Return list of 9 values: [keyword, intent, position, sf, traffic, traffic_pct, volume, kd, url]
    """
    if len(row) == 9:
        return row
    if len(row) == 8:
        # SF missing: insert empty SF after position (index 3)
        return row[:3] + [""] + row[3:]
    # unexpected - pad with empties
    if len(row) < 9:
        return row[:-1] + [""] * (9 - len(row)) + [row[-1]]
    return row[:9]


def main():
    all_rows = []
    for page_idx, snap in enumerate(SNAPSHOTS, 1):
        cells = extract_gridcells(snap)
        rows = parse_rows(cells)
        # Filter out rows where last cell doesn't start with repediu (safety)
        rows = [r for r in rows if r and r[-1].startswith("repediu.com.br")]
        print(f"Page {page_idx}: {len(rows)} rows from {len(cells)} gridcells")
        for r in rows:
            nr = normalize_row(r)
            all_rows.append(nr)
    print(f"Total rows: {len(all_rows)}")

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Positions March 2025"
    headers = [
        "Keyword",
        "Intent",
        "Position",
        "SF",
        "Traffic",
        "Traffic %",
        "Volume",
        "KD %",
        "URL",
    ]
    ws.append(headers)
    for r in all_rows:
        ws.append(r)

    for col_idx, col_cells in enumerate(ws.columns, 1):
        max_len = max((len(str(c.value)) if c.value is not None else 0) for c in col_cells)
        ws.column_dimensions[openpyxl.utils.get_column_letter(col_idx)].width = min(max_len + 2, 60)

    Path(OUTPUT).parent.mkdir(parents=True, exist_ok=True)
    wb.save(OUTPUT)
    print(f"Saved: {OUTPUT}")


if __name__ == "__main__":
    main()
