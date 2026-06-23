# Publish Once, Available Everywhere: The Open Protocol That Fixes Enterprise Agent Discovery

### You built a Cortex Agent that answers revenue questions perfectly. A sales rep in another team asks CoWork the same question. They get a generic answer — because nobody told CoWork your agent exists. ARD fixes that.

*Part of **The Snowflake AI Practitioner's Playbook** — a series of deep dives into production-ready Snowflake AI. [Start from Part 1 →](https://medium.com/@YOUR_MEDIUM_USERNAME/snowflake-ai-day-01)*

---

By Day 9 of this series, I had built a Revenue Ops Cortex Agent that could answer deep questions about pipeline, churn, and deal risk. It worked great — for me, in my Snowsight session.

Meanwhile, the sales team was using Snowflake CoWork and getting generic answers. The analytics team built their own agent. The finance team built theirs. Three teams, three agents, all answering overlapping questions. None of them knew the others existed.

That's the agent discovery problem. It's not technical — it's organizational. And at Summit 2026, Snowflake announced their solution: the **Agentic Resource Discovery (ARD) Specification**, co-built with Microsoft and GoDaddy.

This article explains why ARD matters, how it works, and how to publish your Cortex Agent to the enterprise registry.

---

## The problem: agents are invisible to each other

MCP (Model Context Protocol) solved invocation. If you know a tool's endpoint, you can call it. But knowing the endpoint is the problem.

Right now, when you build a Cortex Agent, the only people who can use it are the ones you manually tell about it. There's no registry, no search, no way for another AI interface to find it automatically.

The result in most enterprises:

```
What happens without ARD:
──────────────────────────────────────────────────────
Revenue team builds:  Revenue Ops Agent
Analytics team builds: Analytics Agent (answers same questions)
Finance team builds:   Finance Agent (some overlap again)
Sales team uses:       CoWork generic AI (doesn't know any of these exist)
IT admin configures:   Manually wires each agent into each tool (weeks)

Result:
- Duplicated agent work
- Inconsistent answers
- Knowledge workers using generic AI instead of specialized agents
- IT bottleneck for every new integration
```

**ARD changes this model:**

```
What happens with ARD:
──────────────────────────────────────────────────────
Revenue team builds Revenue Ops Agent → publishes to ARD registry
Sales rep asks CoWork: "Which APAC accounts have renewal risk?"
CoWork queries ARD registry → finds Revenue Ops Agent → invokes it
Sales rep gets the specialized answer

IT did nothing after the first registry setup.
The agent team did nothing after publishing.
```

---

## How ARD works — the four steps

The specification is intentionally lightweight. Four steps:

### 1. Describe

Every agent publishes a manifest file at a standard path on its domain:

```
https://your-snowflake-domain.snowflakeapp.com/.well-known/ai-catalog.json
```

The manifest describes what the agent does, what tasks it handles, and how to invoke it:

```json
{
  "version": "1.0",
  "agents": [
    {
      "id": "revenue-ops-agent",
      "name": "Revenue Operations AI",
      "description": "Answers questions about sales pipeline, deal risk, customer churn, renewal rates, and revenue forecasting using live Snowflake data.",
      "provider": {
        "name": "Revenue Analytics Team",
        "contact": "rev-ops-data@company.com"
      },
      "capabilities": [
        "pipeline analysis",
        "deal risk scoring",
        "churn prediction",
        "renewal forecasting",
        "sales rep performance"
      ],
      "example_queries": [
        "Which APAC accounts have renewal risk above 70%?",
        "What is our net revenue retention for Q2?",
        "Show me the top 10 deals at risk of churn",
        "Compare deal velocity enterprise vs SMB this quarter"
      ],
      "invocation": {
        "protocol": "mcp",
        "endpoint": "https://revenue-ops-agent.snowflakeapp.com/mcp",
        "auth": "snowflake-oauth"
      },
      "governance": {
        "data_classification": "confidential",
        "access_policy": "REVOPS_READ_ROLE",
        "pii_handling": "masked"
      }
    }
  ]
}
```

The manifest lives on your domain. You control it. ARD never stores a copy.

### 2. Curate

A discovery service (your IT team runs one, or Snowflake hosts it for you) builds its collection by crawling published catalogs:

```python
# discovery_service.py
# A simple ARD discovery service — curate and index your agent catalog

import json
import httpx
import asyncio
from datetime import datetime
from typing import List, Dict

TRUSTED_DOMAINS = [
    "revenue-ops.snowflakeapp.com",
    "analytics.snowflakeapp.com",
    "finance-team.snowflakeapp.com",
    # Add domains as teams publish their agents
]

async def crawl_catalog(domain: str) -> List[Dict]:
    """Fetch and validate an agent catalog from a domain."""
    url = f"https://{domain}/.well-known/ai-catalog.json"
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            catalog = resp.json()

            # Validate structure
            if "agents" not in catalog:
                print(f"Invalid catalog at {domain}: missing 'agents'")
                return []

            # Add provenance info
            for agent in catalog["agents"]:
                agent["_domain"] = domain
                agent["_crawled_at"] = datetime.utcnow().isoformat()
                agent["_status"] = "active"

            print(f"Found {len(catalog['agents'])} agent(s) at {domain}")
            return catalog["agents"]

    except Exception as e:
        print(f"Error crawling {domain}: {e}")
        return []

async def build_registry() -> List[Dict]:
    """Build the full agent registry from all trusted domains."""
    tasks = [crawl_catalog(domain) for domain in TRUSTED_DOMAINS]
    results = await asyncio.gather(*tasks)

    # Flatten and deduplicate
    all_agents = []
    seen_ids = set()
    for agents in results:
        for agent in agents:
            agent_id = f"{agent['_domain']}/{agent['id']}"
            if agent_id not in seen_ids:
                all_agents.append(agent)
                seen_ids.add(agent_id)

    print(f"\nRegistry built: {len(all_agents)} total agents")
    return all_agents

# Store in Snowflake for governance + querying
import snowflake.connector

def store_registry_in_snowflake(agents: List[Dict]):
    """Persist the agent registry in Snowflake for audit + governance."""
    conn = snowflake.connector.connect(
        account="YOUR_ACCOUNT",
        user="YOUR_USER",
        authenticator="externalbrowser",
        database="REVENUE_OPS_AI"
    )
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS REVENUE_OPS_AI.AGENTS.REGISTRY (
            AGENT_ID         STRING,
            AGENT_NAME       STRING,
            DESCRIPTION      TEXT,
            PROVIDER_NAME    STRING,
            CAPABILITIES     ARRAY,
            EXAMPLE_QUERIES  ARRAY,
            INVOCATION       VARIANT,
            GOVERNANCE       VARIANT,
            DOMAIN           STRING,
            CRAWLED_AT       TIMESTAMP_NTZ,
            STATUS           STRING
        )
    """)

    for agent in agents:
        cur.execute("""
            MERGE INTO REVENUE_OPS_AI.AGENTS.REGISTRY t
            USING (SELECT %s AS id) s ON t.AGENT_ID = s.id
            WHEN MATCHED THEN UPDATE SET
                STATUS = 'active',
                CRAWLED_AT = %s
            WHEN NOT MATCHED THEN INSERT
                (AGENT_ID, AGENT_NAME, DESCRIPTION, PROVIDER_NAME,
                 CAPABILITIES, EXAMPLE_QUERIES, INVOCATION, GOVERNANCE,
                 DOMAIN, CRAWLED_AT, STATUS)
            VALUES (%s, %s, %s, %s, %s, %s, PARSE_JSON(%s), PARSE_JSON(%s), %s, %s, 'active')
        """, (
            f"{agent['_domain']}/{agent['id']}",
            agent['_crawled_at'],
            f"{agent['_domain']}/{agent['id']}",
            agent['name'],
            agent.get('description', ''),
            agent.get('provider', {}).get('name', ''),
            json.dumps(agent.get('capabilities', [])),
            json.dumps(agent.get('example_queries', [])),
            json.dumps(agent.get('invocation', {})),
            json.dumps(agent.get('governance', {})),
            agent['_domain'],
            agent['_crawled_at']
        ))

    conn.commit()
    cur.close()
    conn.close()
    print("Registry stored in Snowflake")

if __name__ == "__main__":
    agents = asyncio.run(build_registry())
    store_registry_in_snowflake(agents)
```

### 3. Search

Any AI client (CoWork, Claude, Copilot, or your own app) can query the discovery service with natural language:

```python
# ard_search.py — Query the enterprise agent registry

import snowflake.connector
import json

conn = snowflake.connector.connect(
    account="YOUR_ACCOUNT",
    user="YOUR_USER",
    authenticator="externalbrowser",
    database="REVENUE_OPS_AI",
    warehouse="REVOPS_AI_WH"
)

def find_best_agent(user_question: str) -> dict:
    """
    Find the best registered agent for a given question.
    Uses Cortex AI to match the question against agent descriptions.
    """
    cur = conn.cursor()

    # Use AI to score each agent's relevance to the question
    cur.execute(f"""
        SELECT
            AGENT_ID,
            AGENT_NAME,
            DESCRIPTION,
            INVOCATION,
            GOVERNANCE,
            SNOWFLAKE.CORTEX.AI_COMPLETE(
                'claude-haiku-4-5',
                'Score how relevant this agent is for the question, 0-100.
                 Question: {user_question.replace("'", "\\'")}
                 Agent: ' || AGENT_NAME || ' — ' || DESCRIPTION || '
                 Return only a number 0-100.'
            )::INTEGER AS RELEVANCE_SCORE
        FROM REVENUE_OPS_AI.AGENTS.REGISTRY
        WHERE STATUS = 'active'
        QUALIFY ROW_NUMBER() OVER (PARTITION BY AGENT_ID ORDER BY CRAWLED_AT DESC) = 1
        ORDER BY RELEVANCE_SCORE DESC
        LIMIT 3
    """)

    results = cur.fetchall()
    cur.close()

    if not results or results[0][5] < 40:
        return None  # No sufficiently relevant agent found

    best = results[0]
    return {
        "agent_id": best[0],
        "agent_name": best[1],
        "description": best[2],
        "invocation": json.loads(best[3]),
        "governance": json.loads(best[4]),
        "relevance_score": best[5]
    }

# Example
question = "Which APAC accounts have renewal risk above 70% this quarter?"
match = find_best_agent(question)

if match:
    print(f"Found: {match['agent_name']} (relevance: {match['relevance_score']}/100)")
    print(f"Endpoint: {match['invocation']['endpoint']}")
    print(f"Access policy: {match['governance']['access_policy']}")
else:
    print("No specialized agent found — falling back to general AI")
```

### 4. Execute

The AI client invokes the matched agent directly over MCP. The discovery service is **never in the invocation path** — authentication and data access stay between the client and the agent:

```python
# invoke_discovered_agent.py

import anthropic
import json
from ard_search import find_best_agent

def route_and_answer(question: str) -> str:
    """
    Route a user question to the best registered agent.
    Falls back to general AI if no specialized agent found.
    """
    # Step 1: Search registry
    agent = find_best_agent(question)

    if agent and agent["relevance_score"] >= 60:
        print(f"Routing to: {agent['agent_name']}")

        # Step 2: Invoke via MCP (the specialist agent handles it)
        client = anthropic.Anthropic()

        # In production: use the actual MCP endpoint
        # Here: show the pattern
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            tools=[{
                "name": "invoke_snowflake_agent",
                "description": f"Invoke {agent['agent_name']} for specialized data questions",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "question": {"type": "string"},
                        "agent_endpoint": {"type": "string"}
                    }
                }
            }],
            messages=[{
                "role": "user",
                "content": f"Use the {agent['agent_name']} to answer: {question}"
            }]
        )
        return f"[via {agent['agent_name']}] {response.content[0].text}"

    else:
        print("No specialized agent found — using general Cortex AI")
        # Fall back to general AI_COMPLETE
        import snowflake.connector
        conn = snowflake.connector.connect(
            account="YOUR_ACCOUNT",
            user="YOUR_USER",
            authenticator="externalbrowser",
            database="REVENUE_OPS_AI",
            warehouse="REVOPS_AI_WH"
        )
        cur = conn.cursor()
        cur.execute(f"""
            SELECT SNOWFLAKE.CORTEX.AI_COMPLETE(
                'claude-sonnet-4-6',
                'Answer this revenue operations question: {question.replace("'", "\\'")}'
            )
        """)
        answer = cur.fetchone()[0]
        cur.close()
        conn.close()
        return f"[general AI] {answer}"

# Test
questions = [
    "Which APAC accounts have renewal risk above 70%?",  # → Revenue Ops Agent
    "What's the weather in San Francisco?",              # → No agent found
    "Summarize Q2 pipeline performance",                 # → Revenue Ops Agent
]

for q in questions:
    print(f"\nQ: {q}")
    answer = route_and_answer(q)
    print(f"A: {answer[:200]}...")
```

---

## Publishing your Cortex Agent to the ARD registry

Once you've built a Cortex Agent, publishing to ARD is a one-time setup:

```python
# publish_to_ard.py — Register your Cortex Agent

import json
import os

def generate_ai_catalog(agent_config: dict) -> dict:
    """
    Generate the ai-catalog.json manifest for your Cortex Agent.
    Place this at /.well-known/ai-catalog.json on your agent's domain.
    """
    return {
        "version": "1.0",
        "published_at": "2026-06-23T00:00:00Z",
        "agents": [
            {
                "id": agent_config["id"],
                "name": agent_config["name"],
                "description": agent_config["description"],
                "provider": {
                    "name": agent_config["team"],
                    "contact": agent_config["contact_email"]
                },
                "capabilities": agent_config["capabilities"],
                "example_queries": agent_config["example_queries"],
                "invocation": {
                    "protocol": "mcp",
                    "endpoint": f"https://{agent_config['domain']}/mcp",
                    "auth": "snowflake-oauth",
                    "scopes": agent_config.get("required_scopes", [])
                },
                "governance": {
                    "data_classification": agent_config.get("data_classification", "internal"),
                    "access_policy": agent_config.get("snowflake_role", "PUBLIC"),
                    "pii_handling": agent_config.get("pii_handling", "none"),
                    "approved_by": agent_config.get("data_owner", "")
                }
            }
        ]
    }

# Configure your agent
revenue_ops_agent = {
    "id": "revenue-ops-ai",
    "name": "Revenue Operations AI",
    "description": """
        Specialized AI assistant for revenue operations questions.
        Has deep knowledge of the REVENUE_OPS_AI database including
        sales pipeline, deal risk scoring, churn prediction, renewal
        forecasting, customer segmentation, and sales rep performance.
        Uses live Snowflake data updated every 15 minutes.
    """.strip(),
    "team": "Revenue Analytics Team",
    "contact_email": "rev-analytics@company.com",
    "domain": "revenue-ops-agent.snowflakeapp.com",
    "capabilities": [
        "sales pipeline analysis",
        "deal risk scoring (AI_CLASSIFY)",
        "churn prediction",
        "renewal rate forecasting",
        "customer segmentation",
        "sales rep performance",
        "regional revenue analysis",
        "cohort analysis"
    ],
    "example_queries": [
        "Which APAC accounts have renewal risk above 70%?",
        "What is our NRR for the 2023 cohort?",
        "Compare deal velocity enterprise vs SMB this quarter",
        "Show top 10 at-risk accounts by ACV",
        "Which sales reps are closing fastest in EMEA?",
        "What's driving churn in the SMB segment?"
    ],
    "data_classification": "confidential",
    "snowflake_role": "REVOPS_READ_ROLE",
    "pii_handling": "masked — customer names and emails are masked",
    "data_owner": "payal.chauhan@company.com"
}

# Generate the manifest
catalog = generate_ai_catalog(revenue_ops_agent)

# Write to file (serve this at /.well-known/ai-catalog.json)
with open("ai-catalog.json", "w") as f:
    json.dump(catalog, f, indent=2)

print("✅ ai-catalog.json generated")
print("Next: Host this file at your agent's domain under /.well-known/")
print("Then: Add your domain to your organization's ARD discovery service")
print("\nYour agent will then be discoverable in:")
print("  - Snowflake CoWork")
print("  - Microsoft Copilot")
print("  - Claude")
print("  - Any ARD-compatible AI interface")
```

---

## What this means for the Revenue Ops AI project

Over 37 articles, we built agents that answer revenue questions. Without ARD, these agents are siloed — usable only by people who know they exist.

With ARD:

```
Before ARD:
Data team → builds agent → tells colleagues manually
Colleagues → use generic AI → get generic answers
IT → manually wires integrations → takes weeks

After ARD:
Data team → builds agent → publishes to registry (one command)
Any AI interface (CoWork, Claude, Copilot) → finds agent automatically
User → asks question → routed to the right specialized agent
IT → sets up registry once → no further work per agent
```

The compounding effect: every agent your organization builds automatically becomes available to every AI interface your organization uses. The registry is the network layer for enterprise agents.

---

## The open standards pattern

This is the third time Snowflake has shipped or co-built an open standard at a major inflection point:

- **Apache Iceberg** — open table format that prevents data lake lock-in
- **MCP (Model Context Protocol)** — open invocation standard for AI tools
- **ARD** — open discovery standard for AI agents

The pattern: open standards create network effects that benefit the whole ecosystem. When discovery works the same way across Snowflake CoWork, Microsoft Copilot, and Anthropic Claude, every agent you publish becomes useful to every AI interface simultaneously.

That's the real reason ARD matters — not the spec itself, but what becomes possible when the discovery layer is shared and open.

---

## Key takeaways

1. **ARD solves the invisible agent problem.** You built great agents. Nobody outside your team knows they exist. ARD creates the registration and discovery layer that makes them findable by any AI interface.

2. **Publish once, available everywhere.** A Cortex Agent published to your ARD registry can be invoked by CoWork, Claude, Copilot, or any ARD-compatible interface — without re-registration.

3. **The registry is governance.** IT controls what goes in the registry. Only approved agents are discoverable. This makes ARD the place where governance decisions are enforced, not bypassed.

4. **Discovery doesn't touch invocation.** ARD finds the agent and returns the endpoint. The AI client connects directly. No discovery service in the data path.

5. **ai-catalog.json is 30 lines of JSON.** The barrier to publish is extremely low. The benefit — your agent becomes enterprise-wide — is extremely high.

---

## The series is complete — for now

37 articles. One Revenue Ops AI project, built layer by layer:

- **Weeks 1–6:** Multimodal AI → Cortex Agents → Cortex Code → Security → Iceberg → DMF
- **Bonus (June 2026):** ArcticSwarm → CoCoEvolve → Snowpipe Streaming → Agentic Security → CoCo Desktop → App Runtime → ARD

Every article has copy-paste SQL and Python. Every feature was live in Snowflake when I tested it.

The Snowflake AI stack in June 2026 is genuinely impressive — not because any single piece is magical, but because the pieces fit together. Your data, your governance, your agents, your apps — one coherent platform.

**What's next:** I'll add articles as major features ship. Follow the series to be notified.

---

*← Previous: [Day 36 — Snowflake App Runtime](https://github.com/yelpz04/snowflake-ai-practitioners-playbook/blob/main/bonus-summit-2026/python/day36-app-runtime.md)*

*[↑ Back to Series Index](https://github.com/yelpz04/snowflake-ai-practitioners-playbook#series-arc)*

---

*🔗 Sources: [ARD blog](https://www.snowflake.com/en/blog/agentic-resource-discovery-specification/) | [ARD specification](https://agenticresourcediscovery.org/) | [ARD quickstart](https://github.com/ards-project/docs/blob/main/docs/how_to_publish.md) | [Microsoft ARD announcement](https://commandline.microsoft.com/agentic-resource-discovery-specification-ard/)*

---

**About the Author:** *Payal Chauhan is a Data Engineer specializing in Snowflake AI, Cortex Agents, and agentic data systems. She has hands-on experience with 20+ cutting-edge Snowflake features — from multimodal AI to multi-agent architectures. This series represents 37 end-to-end implementations built publicly to help data teams go from Snowflake announcement to production without the guesswork. Follow on [Medium](https://medium.com/@YOUR_MEDIUM_USERNAME) · [LinkedIn](https://www.linkedin.com/in/YOUR_LINKEDIN_HANDLE)*


*Tags: `Snowflake` `ARD` `Agent Discovery` `Agentic AI` `Cortex Agents` `MCP` `CoWork` `Open Standards` `Enterprise AI` `Summit 2026`*
