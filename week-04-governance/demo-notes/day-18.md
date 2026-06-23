# Day 18: Multi-Tenant Cortex Agents

## Goal
Demonstrate tenant isolation using row access policies + session context with Cortex Agents.

## References
- [Multi-tenancy docs](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-agents-multi-tenancy)
- [Multi-tenant blog](https://medium.com/snowflake/dont-trust-the-llm-with-tenant-isolation-multitenant-cortex-agents-on-snowflake-51267ff08bb8)

## What to Do
1. Run `row_access_policy_multitenant.sql` to set up tenant isolation
2. Run `tenant_test_queries.sql` to verify isolation
3. Call the Cortex Agent API with `TENANT_ID = 'TENANT_A'`
4. Call the same question with `TENANT_ID = 'TENANT_B'`
5. Compare: same question, different (correct) answers

## Architecture

```
One Service Principal
        ↓
  Set TENANT_ID session variable
        ↓
  Row Access Policy filters data
        ↓
  Cortex Agent sees only that tenant's data
        ↓
  Tenant A answer ≠ Tenant B answer (correct!)
```

## Why This Matters
- **Scalability**: 1000s of tenants through one Snowflake connection
- **Simplicity**: no user-per-tenant management
- **Security**: governance built into the platform, not the app layer
