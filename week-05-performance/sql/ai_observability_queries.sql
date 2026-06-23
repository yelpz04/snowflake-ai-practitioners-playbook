-- ============================================================
-- Day 24: AI Observability Queries for Cortex Code
-- ============================================================
-- Reference: https://medium.com/@rahul.reddy.ai/the-ai-observability-playbook-for-cortex-code
-- Tables: SNOWFLAKE.LOCAL.AI_OBSERVABILITY_EVENTS
--         SNOWFLAKE.ACCOUNT_USAGE.CORTEX_CODE_CLI_USAGE_HISTORY

-- ============================================================
-- 1. Recent Cortex Code prompts and responses
-- ============================================================
SELECT
    TIMESTAMP,
    EVENT_TYPE,
    MODEL_NAME,
    USER_NAME,
    PROMPT_TEXT,
    RESPONSE_TEXT,
    INPUT_TOKENS,
    OUTPUT_TOKENS,
    TOTAL_TOKENS,
    LATENCY_MS
FROM TABLE(SNOWFLAKE.LOCAL.GET_AI_OBSERVABILITY_EVENTS(
    DATEADD('day', -7, CURRENT_TIMESTAMP()),
    CURRENT_TIMESTAMP()
))
ORDER BY TIMESTAMP DESC
LIMIT 50;

-- ============================================================
-- 2. Token usage and cost attribution by user
-- ============================================================
SELECT
    USER_NAME,
    MODEL_NAME,
    COUNT(*) AS PROMPT_COUNT,
    SUM(INPUT_TOKENS) AS TOTAL_INPUT_TOKENS,
    SUM(OUTPUT_TOKENS) AS TOTAL_OUTPUT_TOKENS,
    SUM(TOTAL_TOKENS) AS TOTAL_TOKENS,
    AVG(LATENCY_MS) AS AVG_LATENCY_MS,
    MIN(TIMESTAMP) AS FIRST_PROMPT,
    MAX(TIMESTAMP) AS LAST_PROMPT
FROM TABLE(SNOWFLAKE.LOCAL.GET_AI_OBSERVABILITY_EVENTS(
    DATEADD('day', -30, CURRENT_TIMESTAMP()),
    CURRENT_TIMESTAMP()
))
GROUP BY 1, 2
ORDER BY TOTAL_TOKENS DESC;

-- ============================================================
-- 3. Tool usage analysis
-- ============================================================
SELECT
    TOOL_NAME,
    COUNT(*) AS CALL_COUNT,
    AVG(LATENCY_MS) AS AVG_LATENCY_MS,
    SUM(CASE WHEN STATUS = 'SUCCESS' THEN 1 ELSE 0 END) AS SUCCESS_COUNT,
    SUM(CASE WHEN STATUS = 'ERROR' THEN 1 ELSE 0 END) AS ERROR_COUNT
FROM TABLE(SNOWFLAKE.LOCAL.GET_AI_OBSERVABILITY_EVENTS(
    DATEADD('day', -30, CURRENT_TIMESTAMP()),
    CURRENT_TIMESTAMP()
))
WHERE EVENT_TYPE = 'TOOL_CALL'
GROUP BY 1
ORDER BY CALL_COUNT DESC;

-- ============================================================
-- 4. Failed/blocked prompts (governance/compliance)
-- ============================================================
SELECT
    TIMESTAMP,
    USER_NAME,
    PROMPT_TEXT,
    STATUS,
    ERROR_MESSAGE
FROM TABLE(SNOWFLAKE.LOCAL.GET_AI_OBSERVABILITY_EVENTS(
    DATEADD('day', -30, CURRENT_TIMESTAMP()),
    CURRENT_TIMESTAMP()
))
WHERE STATUS IN ('BLOCKED', 'ERROR')
ORDER BY TIMESTAMP DESC;

-- ============================================================
-- 5. Daily usage trend
-- ============================================================
SELECT
    DATE_TRUNC('day', TIMESTAMP) AS USAGE_DATE,
    COUNT(*) AS PROMPT_COUNT,
    COUNT(DISTINCT USER_NAME) AS UNIQUE_USERS,
    SUM(TOTAL_TOKENS) AS DAILY_TOKENS,
    AVG(LATENCY_MS) AS AVG_LATENCY
FROM TABLE(SNOWFLAKE.LOCAL.GET_AI_OBSERVABILITY_EVENTS(
    DATEADD('day', -30, CURRENT_TIMESTAMP()),
    CURRENT_TIMESTAMP()
))
GROUP BY 1
ORDER BY 1;
