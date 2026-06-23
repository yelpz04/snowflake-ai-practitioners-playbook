# Day 7: Semantic Views for Business-Friendly Agent Answers

## Goal
Create a semantic view that gives the agent business context, then compare answers with and without it.

## References
- [Semantic views overview](https://docs.snowflake.com/en/user-guide/views-semantic/overview)

## What to Do
1. Run `02_semantic_view.sql` to create `SALES_METRICS_SV`
2. Ask the agent a question WITHOUT the semantic view (raw tables only)
3. Ask the SAME question WITH the semantic view as a tool
4. Compare: accuracy, metric definitions, terminology used

## Key Takeaway
Semantic views store business definitions (what "revenue" means, what "win rate" means) in the database, so the AI agent doesn't have to guess.

## LinkedIn Post Angle
"Without semantic views, the agent guessed what 'revenue' means. With semantic views, it used the exact business definition. Same question, different quality."

## Medium Article Section
"Day 7: Why semantic views are the secret weapon for AI agents — teaching your data warehouse to speak business."
