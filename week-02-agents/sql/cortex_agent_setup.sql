-- ============================================================
-- Article 3: Cortex Agent + Streamlit BI Dashboard
-- Days 5–10 of The Snowflake AI Practitioner's Playbook
-- ============================================================
-- Series: https://github.com/yelpz04/snowflake-ai-practitioners-playbook
-- Folder: week-02-agents/sql/
--
-- What this file covers (Article 3):
--   - Create the REVENUE_OPS_AGENT Cortex Agent
--   - Wire it to the SALES_METRICS_SV semantic view (02_semantic_view.sql)
--   - Define tool permissions (SQL executor + doc search)
--   - Enable the agent in Snowflake CoWork
--   - System prompt with safety constraints
--
-- Run order within week-02-agents/sql/:
--   1. 01_sales_orders.sql       — core tables
--   2. 02_semantic_view.sql      — semantic view with synonyms and metrics
--   3. 03_tags_and_lineage.sql   — governance tags
--   4. cortex_agent_setup.sql    — THIS FILE — agent creation
--
-- Prerequisite: Semantic view SALES_METRICS_SV must exist
-- Docs: https://docs.snowflake.com/en/user-guide/cortex-agents
-- ============================================================

USE DATABASE REVENUE_OPS_AI;
USE SCHEMA ANALYTICS;

-- ============================================================
-- Step 1: Create the Cortex Agent
-- ============================================================

CREATE OR REPLACE CORTEX AGENT REVENUE_OPS_AGENT
    COMMENT = 'Revenue Operations AI Assistant — answers natural-language questions
               about deals, customers, churn risk, and support. Article 3 of the
               Snowflake AI Practitioner''s Playbook.'
    SYSTEM_PROMPT = $$
        You are a Revenue Operations AI Assistant for a B2B SaaS company.
        You have access to sales pipeline data, customer health scores,
        support ticket history, and call sentiment analysis.

        Guidelines:
        - Always cite the specific data source for your answer (table or view name)
        - If you cannot answer confidently from the data, say so explicitly
        - Do not fabricate metrics, percentages, or customer names
        - Round monetary values to 2 decimal places
        - For churn risk questions, always include the supporting signals
        - Keep answers concise — lead with the direct answer, then supporting detail
        - Never execute DROP, DELETE, TRUNCATE, or ALTER statements
    $$
    TOOLS = (
        SNOWFLAKE.CORTEX.SQL_EXECUTOR(
            SEMANTIC_VIEWS = ('REVENUE_OPS_AI.ANALYTICS.SALES_METRICS_SV'),
            MAX_ROWS = 1000
        ),
        SNOWFLAKE.CORTEX.DOCUMENT_SEARCH(
            STAGE = '@REVENUE_OPS_AI.RAW.MEDIA_FILES_STAGE',
            FILE_TYPES = ('pdf', 'txt')
        )
    );

-- ============================================================
-- Step 2: Grant access to the agent
-- ============================================================

-- Allow data analysts to query the agent
GRANT USAGE ON CORTEX AGENT REVENUE_OPS_AGENT
    TO ROLE DATA_ANALYST;

-- Allow the agent to read from the semantic view
GRANT SELECT ON VIEW REVENUE_OPS_AI.ANALYTICS.SALES_METRICS_SV
    TO ROLE REVENUE_OPS_AGENT_ROLE;

-- ============================================================
-- Step 3: Test the agent with representative queries
-- ============================================================

-- Basic pipeline query (should use SALES_METRICS_SV)
SELECT SNOWFLAKE.CORTEX.AGENT_COMPLETE(
    'REVENUE_OPS_AGENT',
    'How many open deals do we have and what is the total pipeline value?'
) AS answer;

-- Churn risk query (should join call insights + customer health)
SELECT SNOWFLAKE.CORTEX.AGENT_COMPLETE(
    'REVENUE_OPS_AGENT',
    'Which customers are most at risk of churning in the next 30 days?
     Include their recent support and call sentiment signals.'
) AS answer;

-- Deal risk query (should reference specific deals)
SELECT SNOWFLAKE.CORTEX.AGENT_COMPLETE(
    'REVENUE_OPS_AGENT',
    'Which deals in our pipeline have the highest risk of being lost?
     Rank the top 5 with reasons.'
) AS answer;

-- Regional performance (should filter by REGION column)
SELECT SNOWFLAKE.CORTEX.AGENT_COMPLETE(
    'REVENUE_OPS_AGENT',
    'What is our win rate in the Northeast region compared to the national average?'
) AS answer;

-- ============================================================
-- Step 4: Enable Deep Research Mode (Summit 2026+)
-- For complex multi-source questions — see bonus-summit-2026/sql/
-- ============================================================

ALTER CORTEX AGENT REVENUE_OPS_AGENT
    SET DEEP_RESEARCH_MODE = ENABLED;
