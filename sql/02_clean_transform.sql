-- =====================================================================
-- 02_clean_transform.sql : load -> profile -> dedupe -> drop incomplete
--                          -> populate 3 normalized tables -> validate
-- Run from psql (the \copy meta-command is client-side):
--     psql -d your_db -f 01_schema.sql
--     psql -d your_db -f 02_clean_transform.sql
-- =====================================================================
SET search_path = cx;

-- 1) LOAD ------------------------------------------------------------
\copy stg_support_tickets FROM '../data/raw_support_tickets.csv' WITH (FORMAT csv, HEADER true)

-- 2) PROFILE the raw data (expect: 10,300 / 300 / 130) ----------------
SELECT COUNT(*) AS raw_rows FROM stg_support_tickets;                                   -- 10,300

SELECT COUNT(*) - COUNT(DISTINCT ticket_id) AS duplicate_rows                           -- 300
FROM stg_support_tickets;

SELECT COUNT(*) AS incomplete_rows                                                      -- 130 (unique tickets)
FROM (SELECT DISTINCT * FROM stg_support_tickets) d
WHERE NULLIF(TRIM(agent_id), '')               IS NULL
   OR NULLIF(TRIM(channel), '')                IS NULL
   OR NULLIF(TRIM(first_response_minutes), '') IS NULL
   OR NULLIF(TRIM(resolution_hours), '')       IS NULL
   OR NULLIF(TRIM(csat_score), '')             IS NULL;

-- 3) CLEAN: dedupe (window function) + drop incomplete + normalise types
CREATE TABLE clean_tickets AS
WITH ranked AS (                                    -- CTE 1: rank copies of each ticket
    SELECT s.*,
           ROW_NUMBER() OVER (PARTITION BY ticket_id ORDER BY created_at) AS rn
    FROM stg_support_tickets s
),
deduped AS (                                        -- CTE 2: keep first copy only (-300)
    SELECT * FROM ranked WHERE rn = 1
),
complete AS (                                       -- CTE 3: drop rows with missing key fields (-130)
    SELECT * FROM deduped
    WHERE NULLIF(TRIM(agent_id), '')               IS NOT NULL
      AND NULLIF(TRIM(channel), '')                IS NOT NULL
      AND NULLIF(TRIM(first_response_minutes), '') IS NOT NULL
      AND NULLIF(TRIM(resolution_hours), '')       IS NOT NULL
      AND NULLIF(TRIM(csat_score), '')             IS NOT NULL
)
SELECT TRIM(ticket_id)                       AS ticket_id,
       TRIM(customer_id)                     AS customer_id,
       INITCAP(TRIM(customer_region))        AS customer_region,
       TRIM(agent_id)                        AS agent_id,
       TRIM(agent_name)                      AS agent_name,
       TRIM(channel)                         AS channel,
       TRIM(category)                        AS category,
       created_at::TIMESTAMP                 AS created_at,
       first_response_minutes::NUMERIC(7,1)  AS first_response_minutes,
       resolution_hours::NUMERIC(6,1)        AS resolution_hours,
       csat_score::NUMERIC::SMALLINT         AS csat_score
FROM complete;

-- 4) NORMALISE into 3 related tables ----------------------------------
INSERT INTO customers (customer_id, customer_region)
SELECT DISTINCT customer_id, customer_region FROM clean_tickets;

INSERT INTO agents (agent_id, agent_name)
SELECT DISTINCT agent_id, agent_name FROM clean_tickets;

INSERT INTO tickets (ticket_id, customer_id, agent_id, channel, category, created_at,
                     first_response_minutes, resolution_hours, csat_score)
SELECT ticket_id, customer_id, agent_id, channel, category, created_at,
       first_response_minutes, resolution_hours, csat_score
FROM clean_tickets;

-- 5) VALIDATE ---------------------------------------------------------
SELECT (SELECT COUNT(*) FROM stg_support_tickets)  AS raw_rows,          -- 10,300
       (SELECT COUNT(*) FROM tickets)              AS clean_rows,        -- 9,870
       (SELECT COUNT(*) FROM stg_support_tickets)
     - (SELECT COUNT(*) FROM tickets)              AS total_removed,     -- 430 = 300 + 130
       (SELECT COUNT(*) FROM customers)            AS customers,
       (SELECT COUNT(*) FROM agents)               AS agents;

-- Orphan check (must return 0)
SELECT COUNT(*) AS orphan_tickets
FROM tickets t
LEFT JOIN customers c USING (customer_id)
LEFT JOIN agents    a USING (agent_id)
WHERE c.customer_id IS NULL OR a.agent_id IS NULL;

-- Handy view for Power BI / Excel exports
CREATE OR REPLACE VIEW v_ticket_detail AS
SELECT t.*, c.customer_region, a.agent_name,
       CASE WHEN t.resolution_hours > 24 THEN '> 24 hrs' ELSE '<= 24 hrs' END AS resolution_bucket
FROM tickets t
JOIN customers c USING (customer_id)
JOIN agents    a USING (agent_id);
