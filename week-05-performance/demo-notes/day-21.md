# Day 21: Query Acceleration Service

## Goal
Test QAS on analytical queries and measure performance impact.

## References
- [QAS blog](https://www.snowflake.com/en/blog/engineering/query-acceleration-service-enabled-by-default/)

## What to Do
1. Run `qas_test_queries.sql`
2. Check if QAS is enabled on your warehouse
3. Run the heavy analytical query, capture query profile
4. Note QAS scale factor and elapsed time
5. Compare with/without QAS (disable via ALTER WAREHOUSE)

## LinkedIn Post Angle
"QAS is now enabled by default on Snowflake warehouses. I ran the same analytical query with and without it. Here's what happened to my query time."

## Medium Article Section
"Day 21: Turbocharging ad hoc queries — Query Acceleration Service in practice."
