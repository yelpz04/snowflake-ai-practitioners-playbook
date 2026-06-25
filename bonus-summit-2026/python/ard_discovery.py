"""
ARD — Agentic Resource Discovery
Docs: https://docs.snowflake.com/en/user-guide/ard (Summit 2026+)

Publish your Cortex Agent once. Discover it from any ARD-compatible client
(Snowflake CoWork, Microsoft Copilot, Claude, custom apps).

Usage:
    python ard_discovery.py

Prerequisites:
    - ard_manifest.json uploaded to a public Snowflake stage
    - pip install requests snowflake-snowpark-python
"""

import json
import requests


# ---------------------------------------------------------------------------
# Publish the ai-catalog.json manifest to a Snowflake stage
# ---------------------------------------------------------------------------
# Run this SQL once to host the manifest:
#
#   PUT file:///path/to/ard_manifest.json
#       @REVENUE_OPS_AI.RAW.PUBLIC_ASSETS_STAGE/
#       AUTO_COMPRESS=FALSE;
#
#   SELECT GET_PRESIGNED_URL(
#       '@REVENUE_OPS_AI.RAW.PUBLIC_ASSETS_STAGE', 'ard_manifest.json'
#   );
# ---------------------------------------------------------------------------


def discover_agents(
    discovery_endpoint: str,
    query: str,
    capability_filter: str,
    token: str
) -> list[dict]:
    """Search an ARD discovery endpoint for agents matching a query."""
    response = requests.post(
        f"{discovery_endpoint}/search",
        json={
            "query": query,
            "filters": {
                "capability": capability_filter,
                "type": "cortex-agent"
            }
        },
        headers={"Authorization": f"Bearer {token}"},
        timeout=10
    )
    response.raise_for_status()
    return response.json().get("results", [])


def invoke_agent(agent_endpoint: dict, question: str, token: str) -> str:
    """Invoke a discovered Cortex Agent via its ARD endpoint."""
    account = agent_endpoint["account"]
    agent_name = agent_endpoint["agent_name"]

    response = requests.post(
        f"https://{account}.snowflakecomputing.com/api/v2/cortex/agent:run",
        json={
            "agent": agent_name,
            "messages": [{"role": "user", "content": question}]
        },
        headers={"Authorization": f"Bearer {token}"},
        timeout=30
    )
    response.raise_for_status()
    return response.json().get("answer", "")


def main():
    DISCOVERY_ENDPOINT = "https://your-company.snowflakecomputing.com/.well-known/ard"
    TOKEN = "YOUR_OAUTH_TOKEN"  # replace at runtime — never hardcode

    print("Searching ARD registry for pipeline analysis agents...")
    agents = discover_agents(
        discovery_endpoint=DISCOVERY_ENDPOINT,
        query="customer pipeline risk analysis",
        capability_filter="pipeline_analysis",
        token=TOKEN
    )

    print(f"Found {len(agents)} matching agents:")
    for agent in agents:
        print(f"  - {agent['name']}: {agent['description'][:80]}...")
        print(f"    Endpoint: {agent['endpoint']['agent_name']}")

    if agents:
        first_agent = agents[0]
        print(f"\nInvoking: {first_agent['name']}")
        answer = invoke_agent(
            agent_endpoint=first_agent["endpoint"],
            question="Which deals are most at risk this week?",
            token=TOKEN
        )
        print(f"\nAnswer:\n{answer}")


if __name__ == "__main__":
    main()
