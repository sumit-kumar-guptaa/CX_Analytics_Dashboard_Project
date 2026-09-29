# Power BI — Data Model & 6 DAX Measures

## Data model

Import `v_ticket_detail` (or the three tables `tickets` / `customers` / `agents` with
relationships `tickets[customer_id] → customers[customer_id]` and
`tickets[agent_id] → agents[agent_id]`, both **one-to-many, single direction**).

Add a **Date** table (`CALENDAR(DATE(2025,1,1), DATE(2025,12,31))`) marked as the official date
table, related to `tickets[created_at]`, so month/quarter slicers and time-intelligence work
correctly.

## 6 measures

```DAX
Total Tickets =
COUNTROWS ( tickets )

Avg CSAT =
AVERAGE ( tickets[csat_score] )

Avg Resolution Hours =
AVERAGE ( tickets[resolution_hours] )

Avg First Response Min =
AVERAGE ( tickets[first_response_minutes] )

Pct After 24h =
DIVIDE (
    CALCULATE ( COUNTROWS ( tickets ), tickets[resolution_hours] > 24 ),
    [Total Tickets]
)

CSAT Drop After 24h % =
VAR CsatWithin =
    CALCULATE ( [Avg CSAT], tickets[resolution_hours] <= 24 )
VAR CsatAfter =
    CALCULATE ( [Avg CSAT], tickets[resolution_hours] > 24 )
RETURN
    DIVIDE ( CsatWithin - CsatAfter, CsatWithin )
```

Verified results against the cleaned 9,870-row table: `Total Tickets` = 9,870;
`Avg CSAT` = 3.78; `Pct After 24h` = 22.0%; `CSAT Drop After 24h %` = 28.1%
(4.03 within 24h vs 2.90 after) — matching SQL query Q2 and Excel `Pivot3_Resolution` exactly.

## 3 report pages

| Page | Visuals |
|---|---|
| **Overview** | KPI cards (5 measures above), monthly trend line, CSAT-by-bucket bar, tickets-by-channel bar, tickets-by-category bar |
| **Channel & Category** | Top-2-categories-per-channel table, SLA-breach-rate-by-category table, regional CSAT diverging bar, channel × bucket CSAT heat-map |
| **Agent Performance** | Agent leaderboard table, CSAT-quartile distribution |

## 4 slicers

`channel`, `category`, `customer_region`, and `Date[Month]` — placed on the Overview page and
synced to the Channel & Category page (**Format → Edit interactions** / **Sync slicers** pane).

## Note on the deliverable in this repo

A native `.pbix` can only be authored inside Power BI Desktop, which isn't available in this
environment. `powerbi/dashboard.html` is a self-contained, interactive reproduction of the same
3-page report — same filters, same measures, same numbers — built so the design and the numbers
can be reviewed without installing Power BI. It is not a substitute for actually building the
`.pbix` in Desktop using the model and measures above before this goes on a resume as a
Power BI deliverable — see `docs/dashboard_usage_guide.md` for the rebuild steps.
