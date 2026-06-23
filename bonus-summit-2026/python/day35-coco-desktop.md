# I Ditched My IDE for CoCo Desktop. Here's What a Data Engineering Agent That Outscores Claude Code Actually Looks Like.

### Snowflake Summit 2026 shipped CoCo Desktop, Cloud Agents, and an Agent SDK. I spent a week with all three. This is what changed — and what it means for how data teams build in 2026.

*Part of **The Snowflake AI Practitioner's Playbook** — a series of deep dives into production-ready Snowflake AI. [Start from Part 1 →](link)*

---

I've been building on Snowflake for 35 days straight. Until last week, my workflow was the same as most data engineers: Snowsight for SQL, VS Code for Python, Streamlit for apps, and Claude Code or Cursor for the AI assist. Context switching constantly. Never quite in flow.

Then I installed CoCo Desktop.

I don't want to oversell this. Desktop IDEs for data work have been promised before and under-delivered. But something is genuinely different here, and I want to show you exactly what — with code, not marketing copy.

---

## First, the benchmark that matters

Before I show you the product, you need to know why this is worth your attention.

At Summit 2026, Snowflake published results from [ADE-Bench](https://www.getdbt.com/blog/ade-bench-dbt-data-benchmarking) — dbt Labs' framework for evaluating AI agents on real-world analytics and data engineering tasks:

| Agent | ADE-Bench Pass Rate |
|-------|---------------------|
| **CoCo** | **72.1%** |
| Claude Code | 65.1% |
| OpenAI Codex | 65.1% |

That's a 7 percentage point gap against the best alternatives. On Snowflake-native dbt tasks, the gap widens further.

But the efficiency numbers are what actually surprised me:

> **CoCo uses 51% fewer tokens and takes 8% less time than Claude Code running on Opus 4.7 to complete the same tasks.**

The reason: CoCo doesn't scan everything to figure out your environment. It navigates directly to the data that matters using Snowflake's native catalog, lineage, and RBAC. Generic agents fall back on bash-based exploration. CoCo uses platform-native tools.

That's not a prompt engineering trick. It's architecture.

---

## What CoCo Desktop actually is

CoCo is available in four surfaces:

```
CoCo Desktop   → Native macOS/Windows IDE (the new thing)
CoCo CLI       → Terminal-native, connects local dev to Snowflake
CoCo Snowsight → Persistent agent in the browser UI
CoCo SDK       → Embed the same engine into your Python/JS apps
```

**CoCo Desktop** is the one that changes the workflow:

- **One surface for everything.** Pipelines, apps, agents, notebooks, Streamlit — without switching windows
- **Always-on AI agent.** Persistent across sessions. It remembers where you left off. No re-explaining your project
- **Automations.** Schedule agents to run recurring jobs: DQ checks, pipeline refreshes, model retraining. All governed by your RBAC
- **MCP integrations + skills catalog.** Connect to Jira, GitHub, dbt, Airflow from inside the agent
- **Cloud Agents.** Every browser session gets an isolated container — shell access, Python execution, dbt builds — from any browser tab, zero local setup

---

## Getting started with CoCo Desktop

**Download:**
```
Mac (Apple Silicon): https://sfc-repo.snowflakecomputing.com/coco-desktop/downloads/latest/Cortex-Code-darwin-arm64.dmg
Mac (Intel):         https://sfc-repo.snowflakecomputing.com/coco-desktop/downloads/latest/Cortex-Code-darwin-x64.dmg
Windows (x64):       https://sfc-repo.snowflakecomputing.com/coco-desktop/downloads/latest/Cortex-Code-win32-x64-user-setup.exe
```

Or install the CLI first:
```bash
# Mac/Linux
curl -LsS https://ai.snowflake.com/static/cc-scripts/install.sh | sh

# Windows
irm https://ai.snowflake.com/static/cc-scripts/install.ps1 | iex
```

Once installed, CoCo connects to your Snowflake account and immediately has context: your catalogs, lineage, RBAC, schemas, dbt models, running warehouses. You don't configure anything. It reads your environment.

---

## Building the Revenue Ops pipeline from a conversation

Here's the session I ran when I first opened CoCo Desktop. No special setup — just the context from our 35-day project already in Snowflake.

**Prompt 1: Understand the environment**
```
> Profile the REVENUE_OPS_AI database. What tables do I have, 
  what's their freshness, and are there any quality issues?
```

CoCo's response (abridged): it ran schema discovery, queried `INFORMATION_SCHEMA`, checked `LAST_ALTERED` timestamps, and found that `SUPPORT_TICKETS` hadn't been refreshed in 4 days. It drafted a Dynamic Table refresh command and asked if I wanted to run it.

That's what "grounded in your stack" means. It didn't hallucinate a table name. It found the real one.

**Prompt 2: Build something new**
```
> I need a pipeline that:
  1. Pulls new SALES_ORDERS every 15 minutes
  2. Enriches each order with AI_CLASSIFY for deal risk
  3. Flags high-risk orders to a RISK_ALERTS table
  
  Use Dynamic Tables. Make it production-ready.
```

CoCo scaffolded:
- A Stream on `SALES_ORDERS`
- A Dynamic Table with `AI_CLASSIFY` enrichment
- A downstream `RISK_ALERTS` table with an alert rule
- A Streamlit monitoring dashboard to watch it

Full working SQL, zero boilerplate errors. It referenced actual column names from my schema.

**The output (you can run this directly):**

```sql
-- CoCo-generated pipeline for Revenue Ops deal risk enrichment

-- Step 1: Stream captures new orders
CREATE OR REPLACE STREAM REVENUE_OPS_AI.RAW.SALES_ORDERS_STREAM
    ON TABLE REVENUE_OPS_AI.RAW.SALES_ORDERS
    APPEND_ONLY = TRUE;

-- Step 2: Dynamic Table enriches with AI classification
CREATE OR REPLACE DYNAMIC TABLE REVENUE_OPS_AI.ANALYTICS.ORDERS_RISK_ENRICHED
    TARGET_LAG = '15 minutes'
    WAREHOUSE = REVOPS_AI_WH
AS
SELECT
    s.ORDER_ID,
    s.ACCOUNT_ID,
    s.ACCOUNT_NAME,
    s.ACV,
    s.STAGE,
    s.REGION,
    s.SALES_REP,
    s.CREATED_AT,

    -- AI risk classification
    SNOWFLAKE.CORTEX.AI_CLASSIFY(
        'Deal: ' || s.STAGE ||
        ' | ACV: $' || s.ACV::STRING ||
        ' | Account: ' || s.ACCOUNT_NAME ||
        ' | Region: ' || s.REGION,
        ['high_risk', 'on_track', 'upsell_opportunity', 'needs_attention']
    ):label::STRING AS RISK_LABEL,

    SNOWFLAKE.CORTEX.AI_CLASSIFY(
        'Deal: ' || s.STAGE ||
        ' | ACV: $' || s.ACV::STRING,
        ['high_risk', 'on_track', 'upsell_opportunity', 'needs_attention']
    ):score::FLOAT AS RISK_CONFIDENCE,

    CURRENT_TIMESTAMP() AS ENRICHED_AT

FROM REVENUE_OPS_AI.RAW.SALES_ORDERS s;

-- Step 3: Risk alerts table (append-only)
CREATE OR REPLACE TABLE REVENUE_OPS_AI.ANALYTICS.RISK_ALERTS (
    ALERT_ID        STRING DEFAULT UUID_STRING(),
    ORDER_ID        STRING,
    ACCOUNT_NAME    STRING,
    ACV             FLOAT,
    RISK_LABEL      STRING,
    RISK_CONFIDENCE FLOAT,
    ALERTED_AT      TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

-- Step 4: Task to populate alerts from enriched orders
CREATE OR REPLACE TASK REVENUE_OPS_AI.ANALYTICS.POPULATE_RISK_ALERTS
    WAREHOUSE = REVOPS_AI_WH
    SCHEDULE = '15 MINUTE'
AS
INSERT INTO REVENUE_OPS_AI.ANALYTICS.RISK_ALERTS
    (ORDER_ID, ACCOUNT_NAME, ACV, RISK_LABEL, RISK_CONFIDENCE)
SELECT
    ORDER_ID,
    ACCOUNT_NAME,
    ACV,
    RISK_LABEL,
    RISK_CONFIDENCE
FROM REVENUE_OPS_AI.ANALYTICS.ORDERS_RISK_ENRICHED
WHERE RISK_LABEL = 'high_risk'
  AND RISK_CONFIDENCE > 0.75
  AND ENRICHED_AT > DATEADD('minute', -15, CURRENT_TIMESTAMP());

ALTER TASK REVENUE_OPS_AI.ANALYTICS.POPULATE_RISK_ALERTS RESUME;
```

---

## CoCo Cloud Agents — full CLI power in any browser tab

Cloud Agents is the feature most people will overlook and then later realize was the most useful one.

**The problem it solves:** The CoCo CLI is powerful but requires local setup. Cloud Agents bring the exact same runtime — shell access, Python execution, dbt builds, file read/write — into any Snowsight browser session.

Every session gets its own isolated container:

```
Cloud Agent session:
├── Shell access (bash commands)
├── Python runtime (install packages on the fly)
├── dbt profile (auto-generated for your Snowflake account)
├── File system (read/write project files)
├── Web search capability
└── Your full Snowflake RBAC context
```

What this enables in practice:

```
# In a Cloud Agent session (no local setup needed):

User: Run dbt tests on my revenue models and fix any failures.

CoCo:
1. Provisions container with dbt installed
2. Generates your snowflake profile automatically
3. Runs: dbt test --select revenue_*
4. Finds 2 failing tests (null check on ACCOUNT_ID, referential integrity on CUSTOMERS)
5. Shows you the failures
6. Proposes SQL fixes
7. Runs dbt test again after your approval — all green
```

This is what "agentic" actually means in practice. Not a chatbot. An agent that takes a sequence of actions, validates each one, and reports results.

---

## CoCo Agent SDK — embed the same engine in your apps

For platform engineers, the SDK is the most interesting piece. You get the same tools and agent loop that CoCo uses in production, as an installable library.

```python
# Install
# pip install cortex-code-agent-sdk

import asyncio
from cortex_code_agent_sdk import query

async def profile_revenue_data():
    """
    Use CoCo's full agent engine programmatically.
    Same tools CoCo uses in Snowsight/Desktop — in your Python code.
    """
    async for message in query(
        prompt="""
        Profile the REVENUE_OPS_AI.RAW.SALES_ORDERS table:
        - Total row count and date range
        - Null rate for each column
        - Top 5 regions by deal count
        - Any obvious data quality issues
        Summarize in plain English with action recommendations.
        """,
        options={
            "cwd": ".",
            "connection": "my-snowflake-connection"
        }
    ):
        if message["type"] == "assistant":
            for block in message["content"]:
                if block["type"] == "text":
                    print(block["text"], end="", flush=True)

asyncio.run(profile_revenue_data())
```

**What the SDK supports:**

```python
# Multi-turn sessions (stateful conversations)
session = CoCoSession(connection="my-connection")
await session.query("What tables are in REVENUE_OPS_AI?")
await session.query("Which ones have data quality issues?")  # Remembers context

# Structured output (typed, schema-validated JSON)
result = await query(
    prompt="List all high-risk accounts as JSON",
    output_schema={
        "type": "array",
        "items": {
            "account_id": "string",
            "risk_score": "number",
            "risk_reason": "string"
        }
    }
)

# Hooks (intercept and control agent behavior)
async def pre_execution_hook(action):
    """Block any DROP or DELETE commands."""
    if "DROP" in action.sql.upper() or "DELETE" in action.sql.upper():
        raise PermissionError(f"Blocked: {action.sql[:80]}")
    return action

await query(
    prompt="Clean up old test tables",
    hooks={"before_execute": pre_execution_hook}
)

# MCP server integration
await query(
    prompt="Create a Jira ticket for the pipeline failure",
    mcp_servers=["jira-mcp-server", "slack-mcp-server"]
)
```

**Use cases:**
- **CI/CD pipelines:** Run CoCo-powered data quality checks on every PR
- **Internal tools:** Build data portals with AI that understands your actual schema
- **Automation:** Replace cron scripts with agent-driven workflows that adapt to failures
- **ISV products:** Ship data products that use CoCo as the AI backbone

---

## Automations — when CoCo works while you sleep

The feature that makes CoCo Desktop feel like a team member, not a tool.

Automations let you schedule agents to run recurring workflows, governed by Snowflake RBAC with full audit trails.

```
# Set up in CoCo Desktop → Automations panel

Name: Daily Revenue Health Check
Schedule: Every day at 7:00 AM IST
Role: REVOPS_AI_AGENT_ROLE
Prompt: |
  Run a full health check on REVENUE_OPS_AI:
  1. Check Dynamic Table freshness (alert if >2 hours behind)
  2. Run DMF checks on SALES_ORDERS (null rates, duplicates)
  3. Check for any high-risk deals added in the last 24 hours
  4. Post summary to #revenue-ops Slack channel

On completion: Send email to payalchauhan@company.com
```

What runs at 7 AM:
- CoCo spins up a Cloud Agent session
- Executes each check using your Snowflake RBAC
- Posts formatted Slack message with findings
- Logs the full run to `SNOWFLAKE.ACCOUNT_USAGE.CORTEX_CODE_HISTORY`

No infrastructure. No separate scheduler. No credentials to manage. It's Airflow-style scheduling but the "DAG" is a natural language prompt and a governed agent.

---

## Where CoCo fits vs other tools

```
│ Task                          │ Use                              │
│──────────────────────────────│──────────────────────────────────│
│ Quick SQL query               │ Snowsight worksheet              │
│ Python notebook exploration   │ Snowflake Notebooks              │
│ Build a pipeline from scratch │ CoCo Desktop / Cloud Agents ✅   │
│ Debug a failing dbt model     │ CoCo Desktop ✅                   │
│ Scheduled data quality check  │ CoCo Automations ✅               │
│ Embed AI in an internal app   │ CoCo Agent SDK ✅                 │
│ CI/CD data validation         │ CoCo Agent SDK ✅                 │
│ Generic code completion       │ Claude Code / Copilot            │
```

CoCo's edge is always the same: **it knows your actual Snowflake environment**. Generic agents don't. That's why the benchmark gap is 7 points, not 0.5.

---

## Key takeaways

1. **CoCo Desktop isn't a chatbot wrapper.** It's a data-native agent harness that reads your catalog, lineage, and RBAC from the first prompt. That's why it beats Claude Code on data engineering benchmarks despite using 51% fewer tokens.

2. **Cloud Agents give you CLI power in any browser.** No local setup. Isolated container per session. dbt, Python, shell — all there, all governed.

3. **Automations replace cron scripts for data ops.** Natural language prompts + RBAC + audit trails. Schedule recurring DQ checks, pipeline refreshes, and report generation without any infrastructure.

4. **The SDK makes CoCo embeddable.** Same tools, same agent loop, same Snowflake grounding — inside your Python scripts, CI pipelines, and internal tools.

5. **72.1% on ADE-Bench.** That's 7 points above Claude Code on the same tasks, with 51% fewer tokens. For production data engineering, that gap is meaningful.

---

*→ Next: [Day 36 — Snowflake App Runtime: From Conversation to Live URL in 5 Minutes](link)*

*← Previous: [Day 34 — The Agentic Enterprise Security Framework](link)*

---

*🔗 Sources: [CoCo Summit 2026 blog](https://www.snowflake.com/en/blog/snowflake-coco-ai-coding-agent-modern-data-stack/) | [CoCo product page](https://www.snowflake.com/en/product/snowflake-coco/) | [Cloud Agents docs](https://docs.snowflake.com/en/user-guide/cortex-code/cortex-code-snowsight/cloud-agents) | [Agent SDK docs](https://docs.snowflake.com/en/user-guide/cortex-code-agent-sdk/cortex-code-agent-sdk)*

---

**About the Author:** *Payal Chauhan is a Data Engineer specializing in Snowflake AI, Cortex Agents, and agentic data systems. She has hands-on experience with 20+ cutting-edge Snowflake features — from multimodal AI to multi-agent architectures. This series represents 37 end-to-end implementations built publicly to help data teams go from Snowflake announcement to production without the guesswork. Follow on [Medium](link) · [LinkedIn](link)*


*Tags: `Snowflake` `CoCo` `Data Engineering` `AI Coding Agent` `CoCo Desktop` `Cloud Agents` `Agentic AI` `dbt` `Summit 2026`*
