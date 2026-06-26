# 10 Practical Snowflake AI Apps — Build Log

10 standalone Streamlit-in-Snowflake apps, each demonstrating a distinct Snowflake AI capability stack (GA as of June 2026). Every app has a Medium article, full Streamlit code, and setup SQL.

## The 10 Apps

| # | App | Snowflake AI Capabilities | Domain |
|---|-----|--------------------------|--------|
| 1 | [SnowCost AI](./app-01-snowcost-ai/) | Cortex Analyst + AI_COMPLETE + Account Usage | FinOps / Cost Intelligence |
| 2 | [DocMind](./app-02-docmind/) | Cortex Search + Multimodal AI + Stage | Enterprise Doc Q&A |
| 3 | [ChurnRadar](./app-03-churnradar/) | Snowpark ML + Cortex AI + Semantic Views | Customer Churn Prediction |
| 4 | [LineageAI](./app-04-lineage-ai/) | AI_COMPLETE + Access History + Object Dependencies | Data Lineage Explorer |
| 5 | [SemanticRec](./app-05-semantic-rec/) | Arctic Embed + Vector Search + Cortex Search | Content Recommendation |
| 6 | [MediaIntel](./app-06-media-intel/) | AI_COMPLETE Multimodal (image/audio/video) | Media Asset Intelligence |
| 7 | [NL-BI](./app-07-nl-bi/) | Cortex Analyst + Semantic Views + CoWork | Natural Language BI |
| 8 | [SQLGuardian](./app-08-sql-guardian/) | Cortex Code + AI_COMPLETE + Query History | AI SQL Code Review |
| 9 | [DQ-AI](./app-09-dq-ai/) | DMF + Anomaly Detection + AI_COMPLETE | Self-Healing Data Quality |
| 10 | [SnowTrivia](./app-10-snow-trivia/) | AI_COMPLETE + Cortex Search + Streamlit | AI Quiz Game |

## Each App Contains

```
app-XX-name/
├── article.md      ← Full Medium article (title, hook, architecture, code walkthrough)
├── app.py          ← Streamlit in Snowflake app (copy-paste ready)
└── sql/
    └── setup.sql   ← Everything needed to run: tables, stages, views, roles
```

## Snowflake AI Features Covered (GA/Preview as of June 2026)

- `SNOWFLAKE.CORTEX.AI_COMPLETE` — text + multimodal (image, audio, video)
- `SNOWFLAKE.CORTEX.COMPLETE` — fast completions
- `SNOWFLAKE.CORTEX.EMBED_TEXT_768` — semantic embeddings (Arctic Embed)
- `VECTOR_INNER_PRODUCT` — vector similarity search
- Cortex Search — managed RAG search service
- Cortex Analyst — natural language to SQL
- Cortex Agents — autonomous multi-step AI agents
- Snowpark ML — in-Snowflake ML training and inference
- Data Metric Functions (DMF) — continuous data quality monitoring
- Semantic Views — business-friendly query layer for AI agents
- Declarative Content Management (DCM) — pipeline-as-code
- Cortex Guard — AI safety and guardrails
- Access History + Object Dependencies — lineage metadata
- Streamlit in Snowflake — native app hosting
- ArcticSwarm / CoCoEvolve / ARD — Summit 2026 preview capabilities

## GitHub

Full series: [github.com/yelpz04/snowflake-ai-practitioners-playbook](https://github.com/yelpz04/snowflake-ai-practitioners-playbook)
