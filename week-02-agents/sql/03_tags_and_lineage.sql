-- ============================================================
-- Day 8: Semantic View Tagging + Lineage
-- ============================================================
-- Docs: https://docs.snowflake.com/en/release-notes/2026/other/2026-05-05-semantic-views-object-tagging

USE SCHEMA REVENUE_OPS_AI.ANALYTICS;

-- Create governance tags
CREATE TAG IF NOT EXISTS REVENUE_OPS_AI.ANALYTICS.DATA_SENSITIVITY
    ALLOWED_VALUES 'PII', 'FINANCIAL', 'INTERNAL', 'PUBLIC'
    COMMENT = 'Classifies the sensitivity level of data attributes';

CREATE TAG IF NOT EXISTS REVENUE_OPS_AI.ANALYTICS.DATA_OWNER
    COMMENT = 'Team or person responsible for this data object';

CREATE TAG IF NOT EXISTS REVENUE_OPS_AI.ANALYTICS.METRIC_TYPE
    ALLOWED_VALUES 'KPI', 'OPERATIONAL', 'DIAGNOSTIC', 'EXPERIMENTAL'
    COMMENT = 'Classification of metric importance and maturity';

-- Tag the semantic view itself
ALTER SEMANTIC VIEW SALES_METRICS_SV SET TAG
    DATA_OWNER = 'Revenue Operations',
    DATA_SENSITIVITY = 'FINANCIAL';

-- Tag individual attributes within the semantic view
-- Tag sensitive columns
ALTER SEMANTIC VIEW SALES_METRICS_SV
  MODIFY TABLE CUSTOMERS
  MODIFY COLUMN CUSTOMER_NAME
  SET TAG DATA_SENSITIVITY = 'PII';

-- Tag metrics
ALTER SEMANTIC VIEW SALES_METRICS_SV
  MODIFY METRIC TOTAL_REVENUE
  SET TAG METRIC_TYPE = 'KPI';

ALTER SEMANTIC VIEW SALES_METRICS_SV
  MODIFY METRIC WIN_RATE
  SET TAG METRIC_TYPE = 'KPI';

ALTER SEMANTIC VIEW SALES_METRICS_SV
  MODIFY METRIC AVG_DISCOUNT
  SET TAG METRIC_TYPE = 'OPERATIONAL';

-- ============================================================
-- Lineage Queries
-- ============================================================

-- Check lineage for the semantic view (what sources feed into it)
-- Via ACCESS_HISTORY (programmatic lineage)
SELECT *
FROM SNOWFLAKE.ACCOUNT_USAGE.ACCESS_HISTORY
WHERE QUERY_START_TIME > DATEADD('day', -7, CURRENT_TIMESTAMP())
  AND ARRAY_SIZE(OBJECTS_MODIFIED) > 0
ORDER BY QUERY_START_TIME DESC
LIMIT 20;

-- Object dependencies (what does the semantic view depend on)
SELECT *
FROM SNOWFLAKE.ACCOUNT_USAGE.OBJECT_DEPENDENCIES
WHERE REFERENCING_OBJECT_NAME = 'SALES_METRICS_SV'
   OR REFERENCED_OBJECT_NAME = 'SALES_METRICS_SV';

-- ============================================================
-- View tags applied
-- ============================================================
SELECT *
FROM TABLE(INFORMATION_SCHEMA.TAG_REFERENCES_ALL_COLUMNS(
    'REVENUE_OPS_AI.ANALYTICS.SALES_METRICS_SV',
    'SEMANTIC VIEW'
));
