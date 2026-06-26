-- LineageAI Setup SQL — App 4 of 10
CREATE DATABASE IF NOT EXISTS LINEAGE_AI; CREATE SCHEMA IF NOT EXISTS LINEAGE_AI.PUBLIC;
USE DATABASE LINEAGE_AI; USE SCHEMA PUBLIC;

CREATE OR REPLACE TABLE TABLE_CATALOG (
    CATALOG_ID       STRING DEFAULT UUID_STRING(),
    DB_NAME          STRING, SCHEMA_NAME STRING, TABLE_NAME STRING,
    AI_DESCRIPTION   STRING, SENSITIVITY_LEVEL STRING,
    ROW_COUNT        INT,    COLUMN_COUNT INT,
    LAST_QUERIED_AT  TIMESTAMP_NTZ,
    CATALOGUED_AT    TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

CREATE OR REPLACE CORTEX SEARCH SERVICE CATALOG_SEARCH
    ON COLUMN AI_DESCRIPTION
    ATTRIBUTES TABLE_NAME, SCHEMA_NAME, DB_NAME, SENSITIVITY_LEVEL
    WAREHOUSE = COMPUTE_WH TARGET_LAG = '1 hour'
    AS (SELECT AI_DESCRIPTION, TABLE_NAME, SCHEMA_NAME, DB_NAME, SENSITIVITY_LEVEL FROM TABLE_CATALOG);

-- Lineage summary view (upstream + downstream counts)
CREATE OR REPLACE VIEW LINEAGE_SUMMARY AS
SELECT
    o.OBJECT_NAME   AS table_name,
    COUNT(DISTINCT d1.REFERENCED_OBJECT_NAME) AS upstream_count,
    COUNT(DISTINCT d2.OBJECT_NAME)            AS downstream_count
FROM SNOWFLAKE.ACCOUNT_USAGE.OBJECT_DEPENDENCIES o
LEFT JOIN SNOWFLAKE.ACCOUNT_USAGE.OBJECT_DEPENDENCIES d1 ON o.OBJECT_NAME = d1.OBJECT_NAME
LEFT JOIN SNOWFLAKE.ACCOUNT_USAGE.OBJECT_DEPENDENCIES d2 ON o.OBJECT_NAME = d2.REFERENCED_OBJECT_NAME
GROUP BY o.OBJECT_NAME;

-- ── Sample catalog entries (pre-populated for demo without ACCOUNT_USAGE) ────
INSERT INTO TABLE_CATALOG (DB_NAME, SCHEMA_NAME, TABLE_NAME, AI_DESCRIPTION, SENSITIVITY_LEVEL, ROW_COUNT, COLUMN_COUNT) VALUES
('PROD_DB', 'RAW',       'RAW_ORDERS',
 'Raw orders ingested from the e-commerce platform via Snowpipe. Contains all order events including cart abandons and failed payments. Source of truth for the orders pipeline.',
 'FINANCIAL', 2400000, 18),
('PROD_DB', 'STAGING',   'STG_ORDERS',
 'Cleaned and deduplicated orders. NULL order_ids removed, currency normalised to USD, timestamps converted to UTC. Feeds FACT_ORDERS downstream.',
 'FINANCIAL', 2390000, 15),
('PROD_DB', 'ANALYTICS', 'FACT_ORDERS',
 'Conformed fact table for orders. Joined with DIM_CUSTOMER, DIM_PRODUCT, DIM_DATE. Used by the revenue dashboard and all BI tools.',
 'FINANCIAL', 2390000, 22),
('PROD_DB', 'ANALYTICS', 'DIM_CUSTOMER',
 'Customer dimension table. Contains PII: email, phone, home address. Masked for non-privileged roles via column-level masking policy. SCD Type 2.',
 'PII', 85000, 14),
('PROD_DB', 'ANALYTICS', 'DIM_PRODUCT',
 'Product catalogue dimension. Contains product names, SKUs, categories, and pricing tiers. No PII. Updated nightly from the product catalog API.',
 'REFERENCE', 12000, 10),
('PROD_DB', 'ML',        'CHURN_PREDICTIONS',
 'ML model output: churn probability per customer for the next 30 days. Generated weekly by the Snowpark ML pipeline. Used by the Customer Success team for outreach prioritisation.',
 'OPERATIONAL', 85000, 6),
('PROD_DB', 'OUTBOUND',  'SFDC_ACCOUNT_SYNC',
 'Export table synced to Salesforce nightly. Contains account health scores, contract values, and renewal dates. PII fields masked before export.',
 'PII', 85000, 8);
