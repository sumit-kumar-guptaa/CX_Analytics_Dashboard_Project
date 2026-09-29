-- =====================================================================
-- 03_analysis_queries.sql : 7 analysis queries (joins, CTEs, window fns)
-- =====================================================================
SET search_path = cx;

-- Q1 | Ticket volume & share by channel  [JOIN-free, WINDOW: SUM() OVER ()]
--    Finding: Chat = 34.3 % of all tickets
SELECT channel,
       COUNT(*)                                                        AS tickets,
       ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1)              AS pct_of_tickets,
       ROUND(AVG(csat_score), 2)                                       AS avg_csat,
       ROUND(AVG(first_response_minutes), 1)                           AS avg_first_response_min
FROM tickets
GROUP BY channel
ORDER BY tickets DESC;

-- Q2 | CSAT: resolved within 24h vs after 24h  [CTE]
--    Finding: 2.90 vs 4.03  ->  ~28.1 % lower CSAT after 24h
WITH bucketed AS (
    SELECT CASE WHEN resolution_hours > 24 THEN 'after_24h' ELSE 'within_24h' END AS bucket,
           csat_score
    FROM tickets
),
agg AS (
    SELECT bucket, COUNT(*) AS tickets, AVG(csat_score) AS avg_csat
    FROM bucketed GROUP BY bucket
)
SELECT a.bucket,
       a.tickets,
       ROUND(a.avg_csat, 2)                                            AS avg_csat,
       ROUND(100.0 * (w.avg_csat - a.avg_csat) / w.avg_csat, 1)        AS pct_lower_vs_within_24h
FROM agg a
CROSS JOIN (SELECT avg_csat FROM agg WHERE bucket = 'within_24h') w
ORDER BY a.bucket DESC;

-- Q3 | Monthly volume with month-over-month change  [WINDOW: LAG]
WITH monthly AS (
    SELECT DATE_TRUNC('month', created_at)::DATE AS month,
           COUNT(*)                              AS tickets,
           ROUND(AVG(csat_score), 2)             AS avg_csat
    FROM tickets
    GROUP BY 1
)
SELECT month, tickets, avg_csat,
       tickets - LAG(tickets) OVER (ORDER BY month)                                   AS mom_change,
       ROUND(100.0 * (tickets - LAG(tickets) OVER (ORDER BY month))
             / NULLIF(LAG(tickets) OVER (ORDER BY month), 0), 1)                      AS mom_pct
FROM monthly
ORDER BY month;

-- Q4 | Agent leaderboard  [JOIN + CTE + WINDOW: RANK, NTILE]
WITH agent_stats AS (
    SELECT a.agent_id, a.agent_name,
           COUNT(*)                              AS tickets,
           AVG(t.csat_score)                     AS avg_csat,
           AVG(t.resolution_hours)               AS avg_resolution_hrs,
           AVG(t.first_response_minutes)         AS avg_frt_min
    FROM tickets t
    JOIN agents  a ON a.agent_id = t.agent_id
    GROUP BY a.agent_id, a.agent_name
)
SELECT agent_id, agent_name, tickets,
       ROUND(avg_csat, 2)                         AS avg_csat,
       ROUND(avg_resolution_hrs, 1)               AS avg_resolution_hrs,
       ROUND(avg_frt_min, 1)                      AS avg_frt_min,
       RANK()  OVER (ORDER BY avg_csat DESC)      AS csat_rank,
       NTILE(4) OVER (ORDER BY avg_csat DESC)     AS csat_quartile
FROM agent_stats
ORDER BY csat_rank
LIMIT 15;

-- Q5 | Top problem categories inside every channel  [WINDOW: ROW_NUMBER PARTITION BY]
WITH cat_channel AS (
    SELECT channel, category,
           COUNT(*)                   AS tickets,
           AVG(csat_score)            AS avg_csat,
           AVG(resolution_hours)      AS avg_resolution_hrs
    FROM tickets
    GROUP BY channel, category
),
ranked AS (
    SELECT *, ROW_NUMBER() OVER (PARTITION BY channel ORDER BY tickets DESC) AS rn
    FROM cat_channel
)
SELECT channel, category, tickets,
       ROUND(avg_csat, 2)             AS avg_csat,
       ROUND(avg_resolution_hrs, 1)   AS avg_resolution_hrs
FROM ranked
WHERE rn <= 2
ORDER BY channel, rn;

-- Q6 | Which categories breach the 24h line most?  [CTE + conditional aggregation]
WITH cat AS (
    SELECT category,
           COUNT(*)                                             AS tickets,
           COUNT(*) FILTER (WHERE resolution_hours > 24)        AS late_tickets,
           AVG(csat_score)                                      AS avg_csat
    FROM tickets
    GROUP BY category
)
SELECT category, tickets, late_tickets,
       ROUND(100.0 * late_tickets / tickets, 1)                 AS pct_late,
       ROUND(avg_csat, 2)                                       AS avg_csat,
       DENSE_RANK() OVER (ORDER BY late_tickets::NUMERIC / tickets DESC) AS lateness_rank
FROM cat
ORDER BY lateness_rank;

-- Q7 | Regional CSAT vs company average  [JOIN + WINDOW: AVG() OVER ()]
SELECT c.customer_region,
       COUNT(*)                                                             AS tickets,
       ROUND(AVG(t.csat_score), 2)                                          AS region_csat,
       ROUND(AVG(AVG(t.csat_score)) OVER (), 2)                             AS avg_of_region_csat,
       ROUND(AVG(t.csat_score)
             - (SELECT AVG(csat_score) FROM tickets), 3)                    AS diff_vs_company
FROM tickets   t
JOIN customers c ON c.customer_id = t.customer_id
GROUP BY c.customer_region
ORDER BY region_csat DESC;

-- Q8 (bonus) | Channel x resolution bucket CSAT matrix used by the Power BI heat-map
SELECT channel,
       ROUND(AVG(csat_score) FILTER (WHERE resolution_hours <= 24), 2) AS csat_within_24h,
       ROUND(AVG(csat_score) FILTER (WHERE resolution_hours >  24), 2) AS csat_after_24h
FROM tickets
GROUP BY channel
ORDER BY channel;
