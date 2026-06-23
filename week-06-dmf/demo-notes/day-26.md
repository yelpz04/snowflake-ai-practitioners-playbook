# Day 26: Snowflake DMF for AI Input Quality

## Goal
Add DMFs to all key tables — row count, freshness, nulls, duplicates, and custom business rules.

## References
- [DMF anomaly docs](https://docs.snowflake.com/en/user-guide/data-quality-anomaly)
- [Native DQ monitoring](https://medium.com/@arihant.shashank01/native-custom-data-quality-monitoring-in-snowflake-fcf002ec9afb)
- [Monitor data pipelines](https://towardsdatascience.com/monitor-data-pipelines-using-snowflakes-data-metric-functions-0df71c46f04a/)
- [Automate DQ at scale](https://medium.com/snowflake/automate-data-quality-at-scale-dmfs-and-anomaly-detection-in-snowflake-419a04f3480f)
- [Snowflake demo notebook](https://github.com/Snowflake-Labs/snowflake-demo-notebooks/blob/main/Data%20Pipeline%20Observability/task_graphs_dmf_quality_checks.ipynb)

## What to Do
1. Run `dmf_quality_checks.sql`
2. Verify DMFs are registered on all key tables
3. Trigger a data change and observe DMF results
4. Review custom DMFs: negative amounts, invalid ratings, orphan orders

## Why DMF is Here (Day 26, Not Day 1)
DMF is the quality layer for the AI outputs you already built. Without the AI pipeline, DMF has nothing to monitor. The story is: build exciting demos first, then make them trustworthy.

## LinkedIn Post Angle
"Your AI agent is only as trustworthy as its input data. Today I added 10 Data Metric Functions to monitor the tables feeding my Cortex Agents — row count, freshness, nulls, duplicates, and custom business rules. Trust starts with measurement."

## Medium Article Section
"Day 26: DMF for AI pipelines — why data quality monitoring belongs after you build, not before."
