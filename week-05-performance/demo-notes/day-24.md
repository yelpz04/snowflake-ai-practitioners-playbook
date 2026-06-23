# Day 24: AI Observability Playbook for Cortex Code

## Goal
Query AI observability events and build a prompt/tool/cost telemetry dashboard.

## References
- [Playbook article](https://medium.com/@rahul.reddy.ai/the-ai-observability-playbook-for-cortex-code-seeing-every-prompt-tool-call-and-dollar-in-your-cdf5a5eb4c8f)

## What to Do
1. Run `ai_observability_queries.sql`
2. Review: prompts, tools, tokens, latency, errors, blocked prompts
3. Build a simple dashboard (Streamlit or Snowsight) showing:
   - Daily prompt volume
   - Token usage by user
   - Tool call success/failure rates
   - Cost attribution estimates

## Key Tables
- `SNOWFLAKE.LOCAL.AI_OBSERVABILITY_EVENTS` (or via `GET_AI_OBSERVABILITY_EVENTS`)
- `SNOWFLAKE.ACCOUNT_USAGE.CORTEX_CODE_CLI_USAGE_HISTORY`

## LinkedIn Post Angle
"Every Cortex Code prompt is now logged. Not just 'who used it' — the actual prompt, model, tools called, latency, and tokens. All queryable with SQL. Here's the playbook for governing AI usage."

## Medium Article Section
"Day 24: The AI observability playbook — seeing every prompt, tool call, and dollar in Snowflake."
