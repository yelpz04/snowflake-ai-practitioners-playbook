-- ============================================================
-- Day 14 UPDATE: Cortex Code Security Skills
-- ============================================================
-- Reference: https://www.snowflake.com/en/blog/engineering/security-management-cortex-code/

-- ============================================================
-- SKILL 1: Access Troubleshooter
-- ============================================================
-- Ask Cortex Code:
-- "Help me troubleshoot an access control error I got while trying to run:
--  SELECT * FROM REVENUE_OPS_AI.RAW.SALES_ORDERS"
--
-- Cortex Code will:
-- 1. Explain which privileges are missing
-- 2. Recommend least-privilege roles
-- 3. Suggest alternate existing roles that work

-- Example: Check what privileges a role has
SHOW GRANTS TO ROLE REVENUE_OPS_AGENT_READER;

-- Example: Check which roles can access a table
SHOW GRANTS ON TABLE REVENUE_OPS_AI.RAW.SALES_ORDERS;

-- ============================================================
-- SKILL 2: Network Security
-- ============================================================
-- Ask Cortex Code:
-- "Recommend a network policy for this account based on the last 90 days
--  of login history"
--
-- Cortex Code will:
-- 1. Inspect INGRESS_NETWORK_ACCESS_HISTORY
-- 2. Propose an allowlist based on real traffic
-- 3. Simulate "who would be blocked" before enforcement

-- Example: Review recent login IPs
SELECT
    USER_NAME,
    CLIENT_IP,
    REPORTED_CLIENT_TYPE,
    FIRST_AUTHENTICATION_FACTOR,
    IS_SUCCESS
FROM SNOWFLAKE.ACCOUNT_USAGE.LOGIN_HISTORY
WHERE EVENT_TIMESTAMP > DATEADD('day', -90, CURRENT_TIMESTAMP())
ORDER BY EVENT_TIMESTAMP DESC
LIMIT 100;

-- ============================================================
-- SKILL 3: Key and Secret Management (TSS/BYOK)
-- ============================================================
-- Ask Cortex Code:
-- "Is Tri-Secret Secure fully enabled for this account?"
-- "Show me recent TSS operations and who initiated them"
-- "Rotate to a new CMK and ensure all data is protected"
--
-- Cortex Code guides through:
-- 1. Key activation
-- 2. Validation (reachability + permissions)
-- 3. Reference update across accounts/regions
-- 4. Rekeying progress monitoring
