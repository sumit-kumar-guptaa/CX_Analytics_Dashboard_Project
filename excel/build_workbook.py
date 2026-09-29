"""
Build CX_Analytics_Workbook.xlsx
- Raw_Data        : all 10,300 rows exactly as extracted (dupes + incomplete rows included)
- Clean_Data      : the 9,870-row cleaned table, formatted as a real Excel Table (for native PivotTables)
- Data_Dictionary : 11-field data dictionary
- 4 pivot-style summary sheets (openpyxl cannot write native PivotTable XML, so these are built
  with SUMIFS/COUNTIFS/AVERAGEIFS formulas against the Clean_Data table — same numbers a real
  PivotTable would show. Instructions sheet explains the one-click conversion to native PivotTables.)
- Lookup_Agent    : INDEX/MATCH ticket lookup (XLOOKUP-equivalent — see note)
- Insights        : the two headline findings, written as formulas off the summary sheets
"""
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.worksheet.table import Table, TableStyleInfo
from openpyxl.utils import get_column_letter
from openpyxl.chart import BarChart, LineChart, Reference
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
OUT = ROOT / "excel" / "CX_Analytics_Workbook.xlsx"

FONT = "Arial"
HEAD_FILL = PatternFill("solid", fgColor="1F4E78")
HEAD_FONT = Font(name=FONT, bold=True, color="FFFFFF", size=11)
TITLE_FONT = Font(name=FONT, bold=True, size=14, color="1F4E78")
SUB_FONT = Font(name=FONT, italic=True, size=10, color="595959")
BODY_FONT = Font(name=FONT, size=10)
THIN = Side(style="thin", color="D9D9D9")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)

raw = pd.read_csv(DATA / "raw_support_tickets.csv")
clean = pd.read_csv(DATA / "clean_support_tickets.csv")

wb = openpyxl.Workbook()
wb.remove(wb.active)


def style_header(ws, row=1, ncols=None):
    ncols = ncols or ws.max_column
    for c in range(1, ncols + 1):
        cell = ws.cell(row=row, column=c)
        cell.font = HEAD_FONT
        cell.fill = HEAD_FILL
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)


def autosize(ws, widths):
    for i, w in enumerate(widths, start=1):
        ws.column_dimensions[get_column_letter(i)].width = w


def write_df(ws, df, start_row=1):
    for j, col in enumerate(df.columns, start=1):
        ws.cell(row=start_row, column=j, value=col)
    for i, row in enumerate(df.itertuples(index=False), start=start_row + 1):
        for j, val in enumerate(row, start=1):
            ws.cell(row=i, column=j, value=None if pd.isna(val) else val)
    return start_row + len(df)  # last data row


# ============================================================ README ======
ws = wb.create_sheet("ReadMe")
ws.sheet_view.showGridLines = False
ws["B2"] = "Customer Experience (CX) Analytics Dashboard"
ws["B2"].font = TITLE_FONT
ws["B3"] = "SQL (PostgreSQL) -> Power BI -> Advanced Excel  |  simulated 10,300-row support dataset"
ws["B3"].font = SUB_FONT
notes = [
    "",
    "WHAT'S IN THIS WORKBOOK",
    "  Raw_Data          Exactly what SQL staging receives: 10,300 rows, 11 columns (300 duplicate + 130 incomplete rows included).",
    "  Clean_Data        The 9,870-row cleaned table (deduped + complete rows only), loaded as a real Excel Table 'tbl_Clean'.",
    "  Data_Dictionary   All 11 fields, types, and descriptions.",
    "  Pivot1_Channel    Ticket volume & share by channel        -> Chat = 34.3% of all tickets.",
    "  Pivot2_Category   Ticket volume & CSAT by category.",
    "  Pivot3_Resolution CSAT within 24h vs after 24h             -> 4.03 vs 2.90 (28.1% lower after 24h).",
    "  Pivot4_Monthly    Monthly ticket volume trend, 2025.",
    "  Lookup_Agent      Single-lookup agent scorecard (XLOOKUP-equivalent, see note on that sheet).",
    "  Insights          The write-up used in the 5-minute stakeholder walkthrough.",
    "",
    "WHY THESE ARE 'PIVOTTABLE-STYLE' SHEETS, NOT NATIVE PIVOTTABLES",
    "  Native Excel PivotTable objects are a binary/XML structure that only Excel itself (or VBA) can",
    "  write — this workbook was generated with Python (openpyxl), which cannot create that structure.",
    "  Every number on Pivot1-Pivot4 is computed with SUMIFS/COUNTIFS/AVERAGEIFS against tbl_Clean, so",
    "  the figures are identical to what a real PivotTable produces. To get native, drag-and-drop",
    "  PivotTables (e.g. for your own further exploration), do this once in Excel:",
    "    1. Click any cell inside Clean_Data's table (tbl_Clean).",
    "    2. Insert -> PivotTable -> New Worksheet.",
    "    3. Build the 4 views using the field layout given at the top of each Pivot sheet.",
    "  This keeps the resume claim ('4 Pivot Tables') accurate to how the workbook is actually used —",
    "  say this plainly if an interviewer asks how the file was produced.",
    "",
    "DATA SOURCE",
    "  Simulated data generated with a seeded Python script (data/generate_data.py, seed=42) so every",
    "  number in this workbook, the Power BI report, and the SQL outputs reproduce exactly.",
]
for i, line in enumerate(notes, start=4):
    ws.cell(row=i, column=2, value=line).font = BODY_FONT if not line.isupper() and ":" not in line[:2] else Font(name=FONT, bold=True, size=10)
autosize(ws, [3, 118])

# ============================================================ Data Dictionary
ws = wb.create_sheet("Data_Dictionary")
dd = pd.DataFrame([
    ["ticket_id", "Text", "Unique ticket identifier (TKT000001-TKT010000)"],
    ["customer_id", "Text", "Foreign key to the customer who raised the ticket"],
    ["customer_region", "Text", "Customer's region: North / South / East / West / Central"],
    ["agent_id", "Text", "Foreign key to the support agent who handled the ticket"],
    ["agent_name", "Text", "Agent's display name"],
    ["channel", "Text", "Intake channel: Chat, Email, Phone, Social Media, Web Form"],
    ["category", "Text", "Issue category: Technical Issue, Billing, Account Access, Delivery, Refund, Product Inquiry"],
    ["created_at", "Datetime", "Timestamp the ticket was opened (2025)"],
    ["first_response_minutes", "Numeric", "Minutes from ticket creation to first agent response"],
    ["resolution_hours", "Numeric", "Hours from ticket creation to resolution"],
    ["csat_score", "Integer 1-5", "Post-resolution customer satisfaction score"],
], columns=["Field", "Type", "Description"])
ws["B2"] = "Data Dictionary — 11 Fields"; ws["B2"].font = TITLE_FONT
last = write_df(ws, dd.rename(columns={c: c for c in dd.columns}), start_row=4) if False else None
# write starting at A4 with header styling
hdr_row = 4
for j, col in enumerate(dd.columns, start=1):
    ws.cell(row=hdr_row, column=j, value=col)
for i, row in enumerate(dd.itertuples(index=False), start=hdr_row + 1):
    for j, val in enumerate(row, start=1):
        c = ws.cell(row=i, column=j, value=val)
        c.font = BODY_FONT
        c.border = BORDER
        c.alignment = Alignment(vertical="center", wrap_text=True)
style_header(ws, hdr_row, 3)
autosize(ws, [22, 14, 78])
ws.sheet_view.showGridLines = False

# ============================================================ Raw_Data =====
ws = wb.create_sheet("Raw_Data")
last_raw = write_df(ws, raw, start_row=1)
style_header(ws, 1, raw.shape[1])
autosize(ws, [12, 12, 15, 10, 16, 13, 16, 18, 20, 17, 11])
ws.freeze_panes = "A2"

# ============================================================ Clean_Data ===
ws = wb.create_sheet("Clean_Data")
last_clean = write_df(ws, clean, start_row=1)
n_clean = last_clean - 1
tbl = Table(displayName="tbl_Clean", ref=f"A1:{get_column_letter(clean.shape[1])}{last_clean}")
tbl.tableStyleInfo = TableStyleInfo(name="TableStyleMedium2", showRowStripes=True)
ws.add_table(tbl)
autosize(ws, [12, 12, 15, 10, 16, 13, 16, 18, 20, 17, 11])
ws.freeze_panes = "A2"
CR = f"Clean_Data!$G$2:$G${last_clean}"       # channel
CAT = f"Clean_Data!$G$2:$G${last_clean}"      # placeholder, redefined below with correct cols

cols = list(clean.columns)
col_letter = {c: get_column_letter(i + 1) for i, c in enumerate(cols)}
rng = lambda c: f"Clean_Data!${col_letter[c]}$2:${col_letter[c]}${last_clean}"

# ============================================================ Pivot1_Channel
ws = wb.create_sheet("Pivot1_Channel")
ws.sheet_view.showGridLines = False
ws["B2"] = "PivotTable 1 — Ticket Volume & CSAT by Channel"; ws["B2"].font = TITLE_FONT
ws["B3"] = "Native layout: Rows=channel | Values=Count of ticket_id, Average of csat_score, Average of first_response_minutes"
ws["B3"].font = SUB_FONT
hdr = ["Channel", "Tickets", "% of Tickets", "Avg CSAT", "Avg First Response (min)"]
r0 = 5
for j, h in enumerate(hdr, start=2):
    ws.cell(row=r0, column=j, value=h)
style_header(ws, r0, 6)
channels = sorted(clean.channel.unique())
for i, ch in enumerate(channels, start=r0 + 1):
    ws.cell(row=i, column=2, value=ch).border = BORDER
    ws.cell(row=i, column=3, value=f'=COUNTIF({rng("channel")},B{i})').border = BORDER
    ws.cell(row=i, column=4, value=f'=C{i}/SUM($C${r0+1}:$C${r0+len(channels)})').number_format = "0.0%"
    ws.cell(row=i, column=4).border = BORDER
    ws.cell(row=i, column=5, value=f'=AVERAGEIF({rng("channel")},B{i},{rng("csat_score")})').number_format = "0.00"
    ws.cell(row=i, column=5).border = BORDER
    ws.cell(row=i, column=6, value=f'=AVERAGEIF({rng("channel")},B{i},{rng("first_response_minutes")})').number_format = "0.0"
    ws.cell(row=i, column=6).border = BORDER
last1 = r0 + len(channels)
ws.cell(row=last1 + 1, column=2, value="Total").font = Font(name=FONT, bold=True)
ws.cell(row=last1 + 1, column=3, value=f"=SUM(C{r0+1}:C{last1})").font = Font(name=FONT, bold=True)
autosize(ws, [3, 16, 11, 13, 11, 22])
chart = BarChart(); chart.title = "Ticket Volume by Channel"; chart.y_axis.title = "Tickets"; chart.style = 10
data_ref = Reference(ws, min_col=3, min_row=r0, max_row=last1)
cats_ref = Reference(ws, min_col=2, min_row=r0 + 1, max_row=last1)
chart.add_data(data_ref, titles_from_data=True); chart.set_categories(cats_ref)
chart.width, chart.height = 15, 8
ws.add_chart(chart, "B" + str(last1 + 4))

# ============================================================ Pivot2_Category
ws = wb.create_sheet("Pivot2_Category")
ws.sheet_view.showGridLines = False
ws["B2"] = "PivotTable 2 — Ticket Volume, CSAT & Resolution Time by Category"; ws["B2"].font = TITLE_FONT
ws["B3"] = "Native layout: Rows=category | Values=Count of ticket_id, Average of csat_score, Average of resolution_hours"
ws["B3"].font = SUB_FONT
hdr = ["Category", "Tickets", "% of Tickets", "Avg CSAT", "Avg Resolution (hrs)"]
r0 = 5
for j, h in enumerate(hdr, start=2):
    ws.cell(row=r0, column=j, value=h)
style_header(ws, r0, 6)
cats = clean.groupby("category").size().sort_values(ascending=False).index.tolist()
for i, cat in enumerate(cats, start=r0 + 1):
    ws.cell(row=i, column=2, value=cat).border = BORDER
    ws.cell(row=i, column=3, value=f'=COUNTIF({rng("category")},B{i})').border = BORDER
    ws.cell(row=i, column=4, value=f'=C{i}/SUM($C${r0+1}:$C${r0+len(cats)})').number_format = "0.0%"
    ws.cell(row=i, column=4).border = BORDER
    ws.cell(row=i, column=5, value=f'=AVERAGEIF({rng("category")},B{i},{rng("csat_score")})').number_format = "0.00"
    ws.cell(row=i, column=5).border = BORDER
    ws.cell(row=i, column=6, value=f'=AVERAGEIF({rng("category")},B{i},{rng("resolution_hours")})').number_format = "0.0"
    ws.cell(row=i, column=6).border = BORDER
last2 = r0 + len(cats)
autosize(ws, [3, 18, 11, 13, 11, 20])
chart = BarChart(); chart.title = "Tickets by Category"; chart.y_axis.title = "Tickets"; chart.style = 11
data_ref = Reference(ws, min_col=3, min_row=r0, max_row=last2)
cats_ref = Reference(ws, min_col=2, min_row=r0 + 1, max_row=last2)
chart.add_data(data_ref, titles_from_data=True); chart.set_categories(cats_ref)
chart.width, chart.height = 15, 8
ws.add_chart(chart, "B" + str(last2 + 3))

# ============================================================ Pivot3_Resolution
ws = wb.create_sheet("Pivot3_Resolution")
ws.sheet_view.showGridLines = False
ws["B2"] = "PivotTable 3 — CSAT: Resolved Within 24h vs After 24h"; ws["B2"].font = TITLE_FONT
ws["B3"] = "Native layout: a calculated field/column 'Resolution Bucket' (IF resolution_hours>24) as Rows | Values=Count, Average of csat_score"
ws["B3"].font = SUB_FONT
# helper column already implicit via formula bucket test
hdr = ["Resolution Bucket", "Tickets", "Avg CSAT"]
r0 = 5
for j, h in enumerate(hdr, start=2):
    ws.cell(row=r0, column=j, value=h)
style_header(ws, r0, 4)
res_rng = rng("resolution_hours"); csat_rng = rng("csat_score")
ws.cell(row=r0 + 1, column=2, value="Within 24h (<=24)").border = BORDER
ws.cell(row=r0 + 1, column=3, value=f'=COUNTIF({res_rng},"<=24")').border = BORDER
ws.cell(row=r0 + 1, column=4, value=f'=AVERAGEIF({res_rng},"<=24",{csat_rng})').number_format = "0.00"
ws.cell(row=r0 + 1, column=4).border = BORDER
ws.cell(row=r0 + 2, column=2, value="After 24h (>24)").border = BORDER
ws.cell(row=r0 + 2, column=3, value=f'=COUNTIF({res_rng},">24")').border = BORDER
ws.cell(row=r0 + 2, column=4, value=f'=AVERAGEIF({res_rng},">24",{csat_rng})').number_format = "0.00"
ws.cell(row=r0 + 2, column=4).border = BORDER
ws.cell(row=r0 + 4, column=2, value="CSAT drop after 24h").font = Font(name=FONT, bold=True)
ws.cell(row=r0 + 4, column=4, value=f'=(D{r0+1}-D{r0+2})/D{r0+1}').number_format = "0.0%"
ws.cell(row=r0 + 4, column=4).font = Font(name=FONT, bold=True)
autosize(ws, [3, 22, 11, 11])
chart = BarChart(); chart.title = "Avg CSAT: <=24h vs >24h"; chart.y_axis.title = "Avg CSAT"; chart.style = 12
data_ref = Reference(ws, min_col=4, min_row=r0, max_row=r0 + 2)
cats_ref = Reference(ws, min_col=2, min_row=r0 + 1, max_row=r0 + 2)
chart.add_data(data_ref, titles_from_data=True); chart.set_categories(cats_ref)
chart.width, chart.height = 12, 8
ws.add_chart(chart, "B10")

# ============================================================ Pivot4_Monthly
ws = wb.create_sheet("Pivot4_Monthly")
ws.sheet_view.showGridLines = False
ws["B2"] = "PivotTable 4 — Monthly Ticket Volume Trend (2025)"; ws["B2"].font = TITLE_FONT
ws["B3"] = "Native layout: Rows=created_at grouped by Month | Values=Count of ticket_id"
ws["B3"].font = SUB_FONT
hdr = ["Month", "Tickets"]
r0 = 5
for j, h in enumerate(hdr, start=2):
    ws.cell(row=r0, column=j, value=h)
style_header(ws, r0, 3)
clean["_month"] = pd.to_datetime(clean.created_at).dt.to_period("M").astype(str)
months = sorted(clean["_month"].unique())
created_rng = rng("created_at")
for i, m in enumerate(months, start=r0 + 1):
    ws.cell(row=i, column=2, value=m).border = BORDER
    y, mo = m.split("-")
    ws.cell(row=i, column=3,
            value=f'=SUMPRODUCT((YEAR({created_rng})={y})*(MONTH({created_rng})={int(mo)}))').border = BORDER
last4 = r0 + len(months)
autosize(ws, [3, 12, 11])
chart = LineChart(); chart.title = "Monthly Ticket Volume — 2025"; chart.y_axis.title = "Tickets"; chart.style = 13
data_ref = Reference(ws, min_col=3, min_row=r0, max_row=last4)
cats_ref = Reference(ws, min_col=2, min_row=r0 + 1, max_row=last4)
chart.add_data(data_ref, titles_from_data=True); chart.set_categories(cats_ref)
chart.width, chart.height = 16, 8
ws.add_chart(chart, "B" + str(last4 + 3))

# ============================================================ Lookup_Agent (XLOOKUP-equivalent)
ws = wb.create_sheet("Lookup_Agent")
ws.sheet_view.showGridLines = False
ws["B2"] = "Agent Scorecard Lookup"; ws["B2"].font = TITLE_FONT
ws["B3"] = ("Type an Agent ID in D5 (yellow cell) to pull that agent's name, ticket count, avg CSAT,"
            " avg resolution hours and avg first-response minutes.")
ws["B3"].font = SUB_FONT
ws["B5"] = "Enter Agent ID:"; ws["B5"].font = Font(name=FONT, bold=True)
ws["D5"] = clean.agent_id.iloc[0]
ws["D5"].fill = PatternFill("solid", fgColor="FFFF00")
ws["D5"].font = Font(name=FONT, bold=True)
ws["D5"].border = BORDER
labels = ["Agent Name", "Tickets Handled", "Avg CSAT", "Avg Resolution (hrs)", "Avg First Response (min)"]
agent_rng = rng("agent_id")
formulas = [
    f'=INDEX({rng("agent_name")},MATCH($D$5,{agent_rng},0))',
    f'=COUNTIF({agent_rng},$D$5)',
    f'=AVERAGEIF({agent_rng},$D$5,{rng("csat_score")})',
    f'=AVERAGEIF({agent_rng},$D$5,{rng("resolution_hours")})',
    f'=AVERAGEIF({agent_rng},$D$5,{rng("first_response_minutes")})',
]
for i, (lab, f) in enumerate(zip(labels, formulas), start=7):
    ws.cell(row=i, column=2, value=lab).font = Font(name=FONT, bold=True)
    c = ws.cell(row=i, column=4, value=f)
    c.border = BORDER
    if "CSAT" in lab:
        c.number_format = "0.00"
    elif "Resolution" in lab or "Response" in lab:
        c.number_format = "0.0"
note_row = 14
note = [
    "Note on 'XLOOKUP' (resume) vs INDEX/MATCH (this file):",
    "This workbook was generated and formula-checked outside Excel, where XLOOKUP cannot be evaluated.",
    "INDEX/MATCH above returns identical results and is the pre-2019-Excel-compatible equivalent of",
    "XLOOKUP($D$5, agent_id_range, agent_name_range) — swap in XLOOKUP directly if opening in Excel 365.",
]
for i, line in enumerate(note, start=note_row):
    ws.cell(row=i, column=2, value=line).font = Font(name=FONT, italic=True, size=9, color="595959")
autosize(ws, [3, 22, 3, 30])

# ============================================================ Insights =====
ws = wb.create_sheet("Insights")
ws.sheet_view.showGridLines = False
ws["B2"] = "Key Insights — 5-Minute Stakeholder Walkthrough"; ws["B2"].font = TITLE_FONT
ws["B4"] = "1. Channel mix is Chat-heavy"
ws["B4"].font = Font(name=FONT, bold=True, size=11)
ws["B5"] = "=\"   \"&TEXT(Pivot1_Channel!D6,\"0.0%\")&\" of all tickets arrive via Chat — the single largest channel.\""
ws["B6"] = "2. Slow resolution measurably hurts satisfaction"
ws["B6"].font = Font(name=FONT, bold=True, size=11)
ws["B7"] = ('=\"   Tickets resolved after 24 hours average \"&TEXT(Pivot3_Resolution!D7,\"0.00\")&\" CSAT vs \"'
            '&TEXT(Pivot3_Resolution!D6,\"0.00\")&\" for tickets resolved within 24 hours — a \"'
            '&TEXT(Pivot3_Resolution!D9,\"0.0%\")&\" drop.\"')
ws["B9"] = "Recommendation"
ws["B9"].font = Font(name=FONT, bold=True, size=11)
ws["B10"] = ("   Prioritize faster-resolution workflows (auto-routing, staffing) for Technical Issue and Refund"
             " tickets, which breach the 24h line most often (see SQL query Q6) — and for Email, the slowest channel.")
for r in [5, 7, 10]:
    ws.cell(row=r, column=2).font = BODY_FONT
    ws.cell(row=r, column=2).alignment = Alignment(wrap_text=True)
autosize(ws, [3, 100])

wb.save(OUT)
print("saved", OUT, OUT.stat().st_size, "bytes")
