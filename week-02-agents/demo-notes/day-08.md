# Day 8: Semantic View Tagging + Lineage

## Goal
Add governance tags to semantic views and explore lineage/impact analysis.

## References
- [Object tagging release](https://docs.snowflake.com/en/release-notes/2026/other/2026-05-05-semantic-views-object-tagging)

## What to Do
1. Run `03_tags_and_lineage.sql`
2. Tag the semantic view: DATA_OWNER, DATA_SENSITIVITY
3. Tag individual columns: PII on CUSTOMER_NAME
4. Tag metrics: KPI vs OPERATIONAL
5. Query lineage to show what feeds the semantic view

## Governance Maturity Stages (for LinkedIn narrative)
1. Learn the basics → create semantic views
2. Add advanced modeling → metrics, relationships
3. Integrate into dev tooling → Cortex Code, Git
4. Scale to managed data products → tagging, lineage, sharing
