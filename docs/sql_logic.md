# SQL Logic — CX Analytics Dashboard

Engine: **PostgreSQL 14+**. Three scripts, run in order:

```
psql -d your_db -f sql/01_schema.sql
psql -d your_db -f sql/02_clean_transform.sql
psql -d your_db -f sql/03_analysis_queries.sql
```

## 1. `01_schema.sql` — staging + normalized model

- `stg_support_tickets`: an all-`TEXT` staging table so a messy CSV load can never fail on type
  mismatches — cleaning and casting happen deliberately, in SQL, not silently at load time.
- `customers`, `agents`, `tickets`: the 3 normalized tables the dashboard reads from, with
  primary keys, foreign keys, `CHECK` constraints (e.g. `csat_score BETWEEN 1 AND 5`), and
  indexes on the columns the analysis queries filter/group by most (`channel`, `category`,
  `created_at`).

## 2. `02_clean_transform.sql` — load, profile, dedupe, normalize, validate

1. **Load** the raw 10,300-row CSV into staging with `\copy`.
2. **Profile** it first — count rows, duplicates, and incomplete records *before* touching
   anything, so the before/after is provable, not asserted.
3. **Clean** with a 3-stage CTE:
   - `ranked` — `ROW_NUMBER() OVER (PARTITION BY ticket_id ORDER BY created_at)` tags every copy
     of a duplicated ticket.
   - `deduped` — keep only `rn = 1` (−300 rows).
   - `complete` — drop rows missing any required field (−130 rows).
   The final `SELECT` also trims text and casts every column to its proper type in one pass.
4. **Normalize**: `INSERT ... SELECT DISTINCT` populates `customers` and `agents` from the
   cleaned data, then `tickets` is populated with the foreign keys already in place.
5. **Validate**: row-count check (10,300 → 9,870, difference = 430 = 300 + 130) and an orphan
   check (`LEFT JOIN ... WHERE ... IS NULL`, expected to return 0).
6. A `v_ticket_detail` view joins all three tables plus a `resolution_bucket` calculated column,
   used as the export source for Power BI and Excel.

## 3. `03_analysis_queries.sql` — 8 queries, every clause type used at least once

| # | Question answered | SQL techniques |
|---|---|---|
| Q1 | Ticket volume & share by channel — **Chat = 34.3%** | Window function `SUM() OVER ()` |
| Q2 | CSAT within vs after 24h — **4.03 vs 2.90, −28.1%** | CTE, `CROSS JOIN` |
| Q3 | Monthly volume with month-over-month change | CTE, window `LAG()` |
| Q4 | Agent leaderboard | `JOIN`, CTE, window `RANK()` / `NTILE()` |
| Q5 | Top 2 categories inside each channel | CTE, window `ROW_NUMBER() PARTITION BY` |
| Q6 | Categories that breach the 24h SLA most | CTE, `FILTER (WHERE ...)`, `DENSE_RANK()` |
| Q7 | Regional CSAT vs company average | `JOIN`, window `AVG() OVER ()`, scalar subquery |
| Q8 | Channel × resolution-bucket CSAT matrix (dashboard heat-map) | Conditional aggregation with `FILTER` |

Every number quoted on the dashboard, in the Excel workbook, and in the walkthrough script traces
back to one of these queries (or the equivalent DAX measure — see `dax_measures.md`).
