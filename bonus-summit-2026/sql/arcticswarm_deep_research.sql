-- ============================================================
-- ArcticSwarm — Multi-Agent Deep Research
-- ============================================================
-- Docs: https://docs.snowflake.com/en/user-guide/cortex-agents
-- Requires: Cortex Agent with Deep Research Mode enabled (Summit 2026+)

USE DATABASE REVENUE_OPS_AI;
USE SCHEMA ANALYTICS;

-- ============================================================
-- Enable Deep Research Mode on the Revenue Ops Agent
-- ============================================================

ALTER CORTEX AGENT REVENUE_OPS_AGENT
    SET DEEP_RESEARCH_MODE = ENABLED;

-- ============================================================
-- Deep Research Query — multi-source, cited answer
-- ============================================================

SELECT SNOWFLAKE.CORTEX.AGENT_COMPLETE(
    'REVENUE_OPS_AGENT',
    'Comprehensive analysis: Why did Q1 revenue underperform in the Northeast region?
     Cross-reference: our internal sales data, support ticket patterns, customer
     sentiment from call recordings, and any relevant market context you can access.
     Provide a cited, multi-source conclusion with confidence level.'
) AS deep_research_answer;

-- ============================================================
-- Custom parallel workflow — isolation then synthesis
-- ============================================================

-- Agent 1: SQL analyst (isolation mode)
SELECT SNOWFLAKE.CORTEX.AGENT_COMPLETE(
    'REVENUE_OPS_AGENT',
    OBJECT_CONSTRUCT(
        'task', 'Analyse Q1 revenue underperformance in Northeast from sales data only.
                 Do not generalise — cite specific orders, customers, and dates.',
        'mode', 'isolated',
        'output_to_bulletin', 'northeast_q1_analysis'
    )
) AS sql_agent_findings;

-- Agent 2: Sentiment analyst (isolation mode)
SELECT SNOWFLAKE.CORTEX.AGENT_COMPLETE(
    'REVENUE_OPS_AGENT',
    OBJECT_CONSTRUCT(
        'task', 'Analyse customer sentiment and escalation patterns in Northeast Q1.
                 Use only call intelligence and feedback data. Cite specific customers.',
        'mode', 'isolated',
        'output_to_bulletin', 'northeast_q1_sentiment'
    )
) AS sentiment_agent_findings;

-- Agent 3: Synthesis (collaborative mode — reads both bulletins)
SELECT SNOWFLAKE.CORTEX.AGENT_COMPLETE(
    'REVENUE_OPS_AGENT',
    OBJECT_CONSTRUCT(
        'task', 'Reconcile the SQL revenue analysis and sentiment analysis from the bulletin.
                 Identify where they agree and where they conflict.
                 Produce a final synthesis with confidence score.',
        'mode', 'collaborative',
        'read_from_bulletin', ARRAY_CONSTRUCT(
            'northeast_q1_analysis',
            'northeast_q1_sentiment'
        )
    )
) AS synthesised_answer;
