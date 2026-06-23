# Day 15: Cortex Code Hooks

## Goal
Add safety hooks that intercept and block dangerous SQL before execution.

## References
- [Hooks docs](https://docs.snowflake.com/en/user-guide/cortex-code-agent-sdk/hooks)

## What to Do
1. Review `hooks/block_risky_sql.py`
2. Test: ask Cortex Code to "DROP TABLE SALES_ORDERS" — should be blocked
3. Test: ask it to "DELETE FROM CUSTOMER_FEEDBACK" (no WHERE) — should be blocked
4. Test: ask it to "CREATE OR REPLACE TABLE" on RAW schema — should warn
5. Test: normal SELECT queries — should pass through

## Hook Capabilities
- **Intercept**: inspect tool calls before execution
- **Block**: prevent dangerous operations
- **Warn**: allow but flag risky operations
- **Audit**: log all intercepted operations
- **Modify**: inject context or alter inputs
- **Control flow**: conditional execution

## LinkedIn Post Angle
"My AI agent tried to DROP a production table. The hook blocked it. Cortex Code hooks = guardrails for your AI developer. You wouldn't let a junior dev run DROP TABLE without review — why let an AI?"

## Medium Article Section
"Day 15: Safety nets for AI agents — building hooks that prevent your Cortex Code agent from going rogue."
