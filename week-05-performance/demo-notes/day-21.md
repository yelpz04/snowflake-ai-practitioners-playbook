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
