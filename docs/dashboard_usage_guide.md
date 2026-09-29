# Dashboard Usage Guide

## 1. Reproduce the dataset (optional — CSVs are already in `data/`)

```bash
pip install numpy pandas
python3 data/generate_data.py
```

Seeded (`SEED=42`), so it always regenerates the same 10,300 raw / 9,870 clean rows with the same
headline numbers (34.3% Chat share, 4.03 vs 2.90 CSAT).

## 2. Load into PostgreSQL

```bash
createdb cx_analytics
psql -d cx_analytics -f sql/01_schema.sql
psql -d cx_analytics -f sql/02_clean_transform.sql   # loads data/raw_support_tickets.csv via \copy
psql -d cx_analytics -f sql/03_analysis_queries.sql  # prints the 8 analysis queries
```

If `psql` isn't on your machine, install PostgreSQL locally or point `\copy`'s relative path at
wherever you've placed `raw_support_tickets.csv`.

## 3. Build the Power BI report (native `.pbix`)

1. Open Power BI Desktop → **Get Data → PostgreSQL database** → point at `cx_analytics`,
   import `customers`, `agents`, `tickets` (or the `v_ticket_detail` view).
2. Build the relationships and Date table, then paste in the 6 measures from
   `docs/dax_measures.md`.
3. Build the 3 pages and 4 slicers as described in that same doc.
4. `powerbi/dashboard.html` is a working reference for the exact layout, numbers, and
   interactions to replicate — open it locally in a browser (no install needed) to see the target.

## 4. Open the Excel workbook

`excel/CX_Analytics_Workbook.xlsx` — open normally in Excel. `ReadMe` sheet explains every tab.
The 4 `Pivot*` sheets are formula-driven (SUMIFS/COUNTIFS/AVERAGEIFS against the `tbl_Clean`
table) rather than native PivotTable objects, because this workbook was generated with Python —
the `ReadMe` sheet gives the exact 3-click path to turn them into real drag-and-drop PivotTables
if you want to explore the data further yourself.

## 5. Documentation

- `docs/data_dictionary.md` — all 11 fields
- `docs/sql_logic.md` — what each SQL script does and why
- `docs/dax_measures.md` — the Power BI model, measures, pages, slicers
- `docs/stakeholder_walkthrough_script.md` — the 5-minute talk track for presenting this to
  non-technical stakeholders
