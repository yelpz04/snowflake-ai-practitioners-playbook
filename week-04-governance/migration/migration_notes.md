# Migration Notes

## Day 19/20: Agentic ML + Migration Agent Observations

### What to Document After Running the Migration

- [ ] Which syntax patterns were auto-converted correctly?
- [ ] Which patterns required manual intervention?
- [ ] Data type mapping accuracy (Oracle NUMBER → Snowflake NUMBER, etc.)
- [ ] Procedure/function conversion quality
- [ ] Temp table handling (# tables → CTEs or transient tables)
- [ ] Error handling conversion (EXCEPTION → TRY/CATCH)
- [ ] Performance of converted queries vs. originals

### Migration Agent Capabilities
- Connection to source databases
- Code conversion (DDL + DML + stored procedures)
- Deployment to target Snowflake account
- Data migration (row-level)
- Validation (schema + data comparison)
