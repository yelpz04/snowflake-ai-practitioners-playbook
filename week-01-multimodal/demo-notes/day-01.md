# Day 1: Project Repo + AI-Readiness Baseline

## Goal
Set up the repo, create base tables, and define an AI-readiness checklist.

## References
- [snowflake-demo-notebooks](https://github.com/Snowflake-Labs/snowflake-demo-notebooks)
- [ai-ready-data](https://github.com/Snowflake-Labs/ai-ready-data)

## What to Do
1. Create GitHub repo: `30-days-practical-snowflake-ai-pocs`
2. Run `01_create_feedback_tables.sql` to set up base tables
3. Verify sample data loaded correctly
4. Review the AI-ready-data repo for inspiration on data preparation patterns

## AI-Readiness Checklist
- [ ] Data is in Snowflake (tables, not just files)
- [ ] Columns have clear, descriptive names
- [ ] No orphan/junk columns
- [ ] Date/timestamp columns are properly typed
- [ ] Sensitive columns are identified for governance (Week 3)
- [ ] Media files are on Snowflake stages (not external URLs)
- [ ] A VARIANT/ARRAY column exists for AI output storage
- [ ] Row-level tenant identifiers exist for multi-tenant demos (Week 4)
