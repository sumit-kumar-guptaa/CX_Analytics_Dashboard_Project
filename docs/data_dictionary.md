# Data Dictionary — CX Analytics Dashboard

Source table: `cx.tickets` (PostgreSQL) / `Clean_Data` (Excel) / `fact_tickets.csv`.
11 fields, 9,870 clean rows (from a 10,300-row raw extract with 300 duplicates and 130 incomplete records removed).

| # | Field                     | Type          | Description                                                          |
|---|---------------------------|---------------|------------------------------------------------------------------------|
| 1 | `ticket_id`                | Text (PK)     | Unique ticket identifier, `TKT000001`–`TKT010000`                    |
| 2 | `customer_id`               | Text (FK)     | Links to the customer who raised the ticket (`customers` table)      |
| 3 | `customer_region`           | Text          | Customer's region — North / South / East / West / Central            |
| 4 | `agent_id`                  | Text (FK)     | Links to the agent who handled the ticket (`agents` table)           |
| 5 | `agent_name`                | Text          | Agent's display name                                                  |
| 6 | `channel`                   | Text          | Intake channel — Chat, Email, Phone, Social Media, Web Form           |
| 7 | `category`                  | Text          | Issue category — Technical Issue, Billing, Account Access, Delivery, Refund, Product Inquiry |
| 8 | `created_at`                | Timestamp     | When the ticket was opened (2025)                                     |
| 9 | `first_response_minutes`    | Numeric(7,1)  | Minutes from creation to the agent's first response                   |
| 10| `resolution_hours`          | Numeric(6,1)  | Hours from creation to resolution                                      |
| 11| `csat_score`                | Smallint      | Post-resolution satisfaction score, 1–5                               |

## Related tables (normalized model)

- **`customers`** — `customer_id` (PK), `customer_region`
- **`agents`** — `agent_id` (PK), `agent_name`
- **`tickets`** — the 11-field fact table above, with `customer_id` / `agent_id` as foreign keys

## Data quality rules applied during cleaning

| Rule | Raw → Clean |
|---|---|
| Exact duplicate rows removed (kept earliest `created_at` per `ticket_id`) | −300 rows |
| Rows missing any of `agent_id`, `channel`, `first_response_minutes`, `resolution_hours`, `csat_score` dropped | −130 rows |
| Text fields trimmed and case-normalized (`customer_region`) | — |
| Numeric fields cast to `NUMERIC`/`SMALLINT`, timestamps cast to `TIMESTAMP` | — |
| Referential integrity enforced (`FOREIGN KEY` to `customers`/`agents`, orphan check = 0) | — |

**Result:** 10,300 raw rows → **9,870 clean rows**, 3 related tables.
