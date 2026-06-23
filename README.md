# The Snowflake AI Practitioner's Playbook

## 37 Working Snowflake AI Implementations — Revenue Ops AI Assistant

A connected, portfolio-ready project built in public — one cohesive system, not random demos.

All 37 articles are on Medium. All code is in this repo. Everything is updated through Summit 2026.

> **Payal Chauhan** — Data Engineer specializing in Snowflake AI, Cortex Agents, and agentic data systems.
> [Medium Series](https://medium.com/@YOUR_MEDIUM_USERNAME) · [LinkedIn](https://www.linkedin.com/in/YOUR_LINKEDIN_HANDLE)

---

## Quick Start

```bash
git clone https://github.com/YOUR_USERNAME/snowflake-ai-practitioners-playbook
cd snowflake-ai-practitioners-playbook

# Set up Snowflake database
snowsql -f data/seed_data.sql

# Or run in Snowflake UI
# Open data/seed_data.sql → Run all
```

**Minimum requirement:** Snowflake Enterprise Edition (for DMF + row access policies)

```sql
-- Enable Cortex AI cross-region (required for some models)
ALTER ACCOUNT SET CORTEX_ENABLED_CROSS_REGION = 'ANY_REGION';

-- Enable change tracking for Dynamic Tables
ALTER TABLE REVENUE_OPS_AI.RAW.SALES_ORDERS SET CHANGE_TRACKING = TRUE;
ALTER TABLE REVENUE_OPS_AI.RAW.CUSTOMERS SET CHANGE_TRACKING = TRUE;
```

---

## What Gets Built

```
Sales + customer feedback + media files
        ↓
Snowflake tables, stages, semantic views
        ↓
Cortex AI Functions + Multimodal AI
        ↓
Cortex Agents + Snowflake CoWork
        ↓
Streamlit app
        ↓
Cortex Code / CoCo skills, hooks, governance
        ↓
DMF, observability, performance, production-readiness
        ↓
ArcticSwarm + CoCoEvolve + App Runtime + ARD (Summit 2026)
```

---

## Series Arc

| Week | Theme | Days | POC Output |
|------|-------|------|------------|
| 1 | Multimodal AI + Streamlit | 1–5 | Media + Feedback AI Analyzer |
| 2 | Cortex Agents + CoWork + Semantic Views | 6–10 | Sales Analyst Agent |
| 3 | Cortex Code / CoCo, Skills, DCM, Hooks | 11–15 | AI-Governed Snowflake Project Builder |
| 4 | Agent Governance, Tenant Isolation, ML, Migration | 16–20 | Governed Multi-Tenant AI Agent |
| 5 | Performance, Observability, Ecosystem | 21–25 | Production Monitoring + Performance Layer |
| 6 | DMF, Documentation, Pipelines, Recap | 26–30 | Production-Ready AI Assistant |
| **Bonus** | **Summit 2026 — ArcticSwarm, CoCoEvolve, App Runtime, ARD** | **31–37** | **Production AI — multi-agent, self-optimizing, discoverable** |

---

## Day-by-Day Schedule

### Week 1 — Start with Exciting AI POCs

| Day | Topic | Reference Items |
|-----|-------|-----------------|
| 1 | Project repo + AI-readiness baseline | [snowflake-demo-notebooks](https://github.com/Snowflake-Labs/snowflake-demo-notebooks), [ai-ready-data](https://github.com/Snowflake-Labs/ai-ready-data) |
| 2 | Cortex AI Multimodal — document/image extraction | [Multimodal docs](https://docs.snowflake.com/en/user-guide/snowflake-cortex/ai-multimodal) |
| 3 | Cortex AI Multimodal — audio sentiment | [Audio sentiment](https://docs.snowflake.com/en/user-guide/snowflake-cortex/ai-multimodal#audio-based-sentiment-analytics) |
| 4 | Cortex AI Multimodal — video metadata | [Video extraction](https://docs.snowflake.com/en/user-guide/snowflake-cortex/ai-multimodal#video-metadata-extraction) |
| 5 | Streamlit in Snowflake Workspaces | [Workspaces overview](https://docs.snowflake.com/en/developer-guide/streamlit/streamlit-in-workspaces/streamlit-in-workspaces-overview) |

### Week 2 — Cortex Agents, Semantic Views, Intelligence

| Day | Topic | Reference Items |
|-----|-------|-----------------|
| 6 | Cortex Agents over structured data | [Cortex Agents docs](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-agents) |
| 7 | Semantic views for business-friendly answers | [Semantic views overview](https://docs.snowflake.com/en/user-guide/views-semantic/overview) |
| 8 | Semantic view tagging + lineage | [Object tagging release](https://docs.snowflake.com/en/release-notes/2026/other/2026-05-05-semantic-views-object-tagging) |
| 9 | Snowflake CoWork: answers to action | [CoWork blog](https://www.snowflake.com/en/blog/snowflake-cowork-personal-work-agent/) |
| 10 | Snowflake CoWork Artifacts | Artifacts feature (charts, tables, shareable outputs) |

### Week 3 — Cortex Code, Skills, DCM, Hooks

| Day | Topic | Reference Items |
|-----|-------|-----------------|
| 11 | Cortex Code skill for DCM Projects | [DCM blog](https://www.snowflake.com/en/blog/declarative-snowflake-pipelines-dcm-projects-cortex-code/) |
| 12 | Cortex Code data engineering skills | [Cortex Code governed agent](https://www.snowflake.com/en/blog/cortex-code-governed-agent-data-stack/) |
| 13 | Data Governance Skills for Cortex Code | [Governance skills blog](https://www.snowflake.com/en/blog/engineering/cortex-code-governance-skills/) |
| 14 | Cortex Code skills as plugins, not prompts | [sfrt.io](https://www.sfrt.io/cortex-code-skills-90-days-in-plugins-not-prompts/) |
| 15 | Cortex Code hooks | [Hooks docs](https://docs.snowflake.com/en/user-guide/cortex-code-agent-sdk/hooks) |

### Week 4 — Agent Governance, Tenant Isolation, ML, Migration

| Day | Topic | Reference Items |
|-----|-------|-----------------|
| 16 | AI agent identity and governance | [Agent identity blog](https://www.snowflake.com/en/blog/ai-agent-identity-governance-enterprise-trust/) |
| 17 | Cortex AI Guardrails | [Guardrails blog](https://www.snowflake.com/en/engineering-blog/cortex-ai-guardrails-prompt-injection-prevention/) |
| 18 | Multi-tenant Cortex Agents | [Multi-tenancy docs](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-agents-multi-tenancy) |
| 19 | Agentic ML in Snowflake | [Agentic ML blog](https://www.snowflake.com/en/blog/agentic-ml-snowflake-predictive-insights/) |
| 20 | Snowflake Migration Agent | [Migration skill docs](https://docs.snowflake.com/en/migrations/migration-skill/skill) |

### Week 5 — Performance, Observability, Ecosystem

| Day | Topic | Reference Items |
|-----|-------|-----------------|
| 21 | Query Acceleration Service | [QAS blog](https://www.snowflake.com/en/blog/engineering/query-acceleration-service-enabled-by-default/) |
| 22 | Interactive Analytics Spring 2026 | [Spring 2026 blog](https://www.snowflake.com/en/blog/engineering/snowflake-interactive-analytics-spring-2026-updates/) |
| 23 | Observe by Snowflake | [Observe blog](https://www.snowflake.com/en/blog/observe-by-snowflake-ai-observability-at-scale/) |
| 24 | AI Observability Playbook for Cortex Code | [Playbook article](https://medium.com/@rahul.reddy.ai/the-ai-observability-playbook-for-cortex-code-seeing-every-prompt-tool-call-and-dollar-in-your-cdf5a5eb4c8f) |
| 25 | Claude Code + Cortex Code delegation | [sfrt.io](https://www.sfrt.io/two-ai-agents-one-repo-delegating-snowflake-work-from-claude-code-to-cortex-code/), [NamiLink](https://blog.namilink.com/i-intercepted-snowflake-cortex-codes-system-prompt-here-s-why-it-writes-broken-sql-b7168ba7e5f7) |

### Week 6 — DMF, Documentation, Pipelines, Recap

| Day | Topic | Reference Items |
|-----|-------|-----------------|
| 26 | Snowflake DMF for AI input quality | [DMF anomaly docs](https://docs.snowflake.com/en/user-guide/data-quality-anomaly), [DMF articles](https://medium.com/@arihant.shashank01/native-custom-data-quality-monitoring-in-snowflake-fcf002ec9afb) |
| 27 | DMF anomaly detection + DQ Manager + Streamlit DQ | [DQ Manager guide](https://snowflake.com/en/developers/guides/getting-started-with-the-data-quality-manager/), [Streamlit DQ](https://adrianleexinhan.medium.com/building-a-no-code-data-quality-management-system-with-streamlit-and-snowflake-dmfs-and-genai-9458cec9c100) |
| 28 | Snowflake docs for AI agents and LLMs | [Agent-friendly docs](https://docs.snowflake.com/en/release-notes/2026/other/2026-04-15-agent-friendly-docs) |
| 29 | Autonomous SQL pipelines for AI agents | [HOL](https://www.snowflake.com/en/webinars/virtual-hands-on-lab/autonomous-sql-pipelines-for-ai-agents-0527-vhol-2026-05-27/) |
| 30 | New features + final portfolio recap | [Release notes](https://docs.snowflake.com/en/release-notes/new-features) |

### Bonus Week — Summit 2026 (Days 31–37)

| Day | Topic | Code |
|-----|-------|------|
| 31 | ArcticSwarm multi-agent deep research | [sql/bonus-summit-2026/day31-arcticswarm-bbs.py](sql/bonus-summit-2026/) |
| 32 | CoCoEvolve evolutionary AI optimization | [sql/bonus-summit-2026/day32-cocoevolve-fitness.py](sql/bonus-summit-2026/) |
| 33 | Snowpipe Streaming HPA + Cortex AI enrichment | [sql/bonus-summit-2026/day33-snowpipe-streaming-hpa.py](sql/bonus-summit-2026/) |
| 34 | Data-Model-Agent security framework | [sql/bonus-summit-2026/day34-security-framework.sql](sql/bonus-summit-2026/) |
| 35 | CoCo Desktop, Cloud Agents, Agent SDK | [sql/bonus-summit-2026/day35-coco-agent-sdk.py](sql/bonus-summit-2026/) |
| 36 | Snowflake App Runtime + Vercel + Streamlit GA | [sql/bonus-summit-2026/day36-app-runtime-node.js](sql/bonus-summit-2026/) |
| 37 | ARD — Agentic Resource Discovery | [sql/bonus-summit-2026/day37-ard-catalog.json](sql/bonus-summit-2026/) |

---

## Repo Structure

```
snowflake-ai-practitioners-playbook/
├── README.md
├── data/
│   └── seed_data.sql              ← run this first
├── sql/
│   ├── week1-multimodal/          ← Days 1–5
│   ├── week2-agents/              ← Days 6–10
│   ├── week3-cortex-code/         ← Days 11–15
│   ├── week4-governance/          ← Days 16–20
│   ├── week5-performance/         ← Days 21–25
│   ├── week6-dmf/                 ← Days 26–30
│   └── bonus-summit-2026/         ← Days 31–37 (ArcticSwarm, CoCoEvolve, App Runtime, ARD)
├── streamlit/
│   ├── revenue-ops-app.py         ← Day 5 full app
│   └── production-portal.py       ← Day 36 full app
└── python/
    ├── cortex-agent-client.py
    └── cocoevolve-harness.py
```

---

## Prerequisites

- Snowflake Enterprise Edition (required for DMF anomaly detection + row access policies)
- Python 3.9+ (for Streamlit apps and Python scripts)
- GitHub account for repo hosting
- LinkedIn / Medium accounts for publishing

---

## Hashtags

`#Snowflake` `#CortexAI` `#DataEngineering` `#AI` `#SnowflakeAIDaily` `#Summit2026` `#DataSuperhero`

---

## Coverage Audit

Every raw topic from the original list is mapped to a specific day. See [COVERAGE_AUDIT.md](COVERAGE_AUDIT.md) for the full mapping.
