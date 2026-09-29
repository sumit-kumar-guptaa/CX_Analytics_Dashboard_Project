-- =====================================================================
-- CX Analytics Dashboard | PostgreSQL 14+
-- 01_schema.sql : staging table + 3 normalized tables
-- =====================================================================
DROP SCHEMA IF EXISTS cx CASCADE;
CREATE SCHEMA cx;
SET search_path = cx;

-- ---------------------------------------------------------------------
-- STAGING: raw CSV lands here exactly as-is (10,300 rows, 11 columns).
-- Everything is TEXT so a dirty file can never fail the load.
-- ---------------------------------------------------------------------
CREATE TABLE stg_support_tickets (
    ticket_id               TEXT,
    customer_id             TEXT,
    customer_region         TEXT,
    agent_id                TEXT,
    agent_name              TEXT,
    channel                 TEXT,
    category                TEXT,
    created_at              TEXT,
    first_response_minutes  TEXT,
    resolution_hours        TEXT,
    csat_score              TEXT
);

-- ---------------------------------------------------------------------
-- NORMALIZED MODEL (3 related tables, star-style)
--   customers (1) ──< tickets >── (1) agents
-- ---------------------------------------------------------------------
CREATE TABLE customers (
    customer_id      VARCHAR(10) PRIMARY KEY,
    customer_region  VARCHAR(20) NOT NULL
);

CREATE TABLE agents (
    agent_id    VARCHAR(10) PRIMARY KEY,
    agent_name  VARCHAR(60) NOT NULL
);

CREATE TABLE tickets (
    ticket_id               VARCHAR(12) PRIMARY KEY,
    customer_id             VARCHAR(10) NOT NULL REFERENCES customers (customer_id),
    agent_id                VARCHAR(10) NOT NULL REFERENCES agents (agent_id),
    channel                 VARCHAR(20) NOT NULL
                            CHECK (channel IN ('Chat','Email','Phone','Social Media','Web Form')),
    category                VARCHAR(30) NOT NULL,
    created_at              TIMESTAMP   NOT NULL,
    first_response_minutes  NUMERIC(7,1) NOT NULL CHECK (first_response_minutes > 0),
    resolution_hours        NUMERIC(6,1) NOT NULL CHECK (resolution_hours > 0),
    csat_score              SMALLINT    NOT NULL CHECK (csat_score BETWEEN 1 AND 5)
);

CREATE INDEX idx_tickets_channel  ON tickets (channel);
CREATE INDEX idx_tickets_category ON tickets (category);
CREATE INDEX idx_tickets_created  ON tickets (created_at);
