"""
CoCoEvolve Runner — Autonomous Agent Self-Optimisation
Docs: https://docs.snowflake.com/en/user-guide/cortex-code
Requires: Cortex Code + CoCoEvolve (Summit 2026+)

Usage:
    python cocoevolve_runner.py

Prerequisites:
    - REVENUE_OPS_AI.ANALYTICS.AGENT_EVAL_SET table populated
    - REVENUE_OPS_AGENT deployed in your Snowflake account
    - pip install snowflake-snowpark-python snowflake-cortex
"""

from snowflake.cortex import CoCoEvolve, AgentComplete, Complete
from snowflake.snowpark import Session


def build_session() -> Session:
    return Session.builder.configs({
        "account": "YOUR_ACCOUNT",
        "user": "YOUR_USER",
        "authenticator": "externalbrowser",
        "database": "REVENUE_OPS_AI",
        "schema": "ANALYTICS",
        "warehouse": "REVOPS_AI_WH"
    }).create()


def evaluate_agent(agent_name: str, question: str, expected_answer: str) -> float:
    """Grade the agent's response — returns 1.0 (correct) or 0.0 (incorrect)."""
    response = AgentComplete(
        agent=agent_name,
        messages=[{"role": "user", "content": question}]
    )
    grade = Complete(
        "claude-haiku-4-5",
        f"""Grade this agent response as 1 (correct) or 0 (incorrect).
Question: {question}
Expected: The answer should contain: {expected_answer}
Agent response: {response}
Return only the number 1 or 0."""
    )
    try:
        return float(grade.strip())
    except ValueError:
        return 0.0


def main():
    session = build_session()

    # Load eval set from Snowflake
    eval_rows = session.sql("""
        SELECT QUESTION, EXPECTED_ANSWER, DIFFICULTY
        FROM AGENT_EVAL_SET
    """).collect()

    print(f"Loaded {len(eval_rows)} eval questions")

    evolve_config = {
        "agent_name": "REVENUE_OPS_AGENT",
        "eval_set": [
            {"question": row["QUESTION"], "expected": row["EXPECTED_ANSWER"]}
            for row in eval_rows
        ],
        "evaluation_function": evaluate_agent,
        "max_iterations": 20,
        "target_accuracy": 0.85,
        "mutation_types": [
            "refine_system_prompt",     # improve instruction clarity
            "add_semantic_synonyms",    # add missing synonyms to semantic view
            "tune_query_templates",     # add example queries for common patterns
            "adjust_tool_selection"     # improve tool selection behaviour
        ]
    }

    result = CoCoEvolve.run(**evolve_config)

    print(f"\nCoCoEvolve complete")
    print(f"  Baseline accuracy:  {result.baseline_accuracy:.1%}")
    print(f"  Evolved accuracy:   {result.final_accuracy:.1%}")
    print(f"  Improvement:        +{result.improvement:.1%}")
    print(f"  Iterations run:     {result.iterations}")
    print(f"\nKey changes made:")
    for change in result.changes:
        print(f"  - {change}")

    # Persist result summary to Snowflake
    session.sql(f"""
        INSERT INTO ANALYTICS.AGENT_EVOLUTION_LOG
            (RUN_AT, BASELINE_ACCURACY, FINAL_ACCURACY, ITERATIONS, CHANGES)
        VALUES (
            CURRENT_TIMESTAMP(),
            {result.baseline_accuracy},
            {result.final_accuracy},
            {result.iterations},
            PARSE_JSON('{result.changes}')
        )
    """).collect()
    print("\nResult logged to ANALYTICS.AGENT_EVOLUTION_LOG")


if __name__ == "__main__":
    main()
