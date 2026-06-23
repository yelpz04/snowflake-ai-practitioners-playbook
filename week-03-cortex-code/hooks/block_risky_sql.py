"""
Cortex Code Hook — Block Risky SQL Operations
======================================================
Docs: https://docs.snowflake.com/en/user-guide/cortex-code-agent-sdk/hooks

This hook intercepts tool calls and blocks dangerous SQL operations
before they are executed. It can:
- Block: DROP TABLE, TRUNCATE, DELETE without WHERE
- Warn: CREATE OR REPLACE on production schemas
- Audit: Log all intercepted operations
"""


def on_tool_call(tool_name: str, tool_input: dict, context: dict) -> dict:
    """
    Hook that intercepts SQL execution tool calls.

    Args:
        tool_name: Name of the tool being called (e.g., 'execute_sql')
        tool_input: The input parameters for the tool
        context: Additional context (user, session, etc.)

    Returns:
        dict with:
          - 'action': 'allow', 'block', or 'warn'
          - 'message': Explanation shown to the user
          - 'modified_input': Optional modified tool input
    """

    # Only intercept SQL execution tools
    if tool_name not in ('execute_sql', 'run_query', 'snowflake_query'):
        return {'action': 'allow'}

    sql = tool_input.get('query', '') or tool_input.get('sql', '')
    sql_upper = sql.upper().strip()

    # --- BLOCK: DROP TABLE / DROP SCHEMA / DROP DATABASE ---
    if any(keyword in sql_upper for keyword in ['DROP TABLE', 'DROP SCHEMA', 'DROP DATABASE']):
        return {
            'action': 'block',
            'message': (
                '🚫 BLOCKED: DROP operation detected.\n'
                f'SQL: {sql[:200]}...\n\n'
                'To proceed, first create a backup or use DCM to manage object lifecycle.\n'
                'If this is intentional, run the SQL directly in Snowsight.'
            )
        }

    # --- BLOCK: TRUNCATE ---
    if 'TRUNCATE' in sql_upper:
        return {
            'action': 'block',
            'message': (
                '🚫 BLOCKED: TRUNCATE operation detected.\n'
                f'SQL: {sql[:200]}...\n\n'
                'Truncating tables removes all data irreversibly.\n'
                'If intentional, run directly in Snowsight with explicit confirmation.'
            )
        }

    # --- BLOCK: DELETE without WHERE ---
    if 'DELETE' in sql_upper and 'WHERE' not in sql_upper:
        return {
            'action': 'block',
            'message': (
                '🚫 BLOCKED: DELETE without WHERE clause detected.\n'
                f'SQL: {sql[:200]}...\n\n'
                'This would delete ALL rows from the table.\n'
                'Add a WHERE clause to target specific rows.'
            )
        }

    # --- WARN: CREATE OR REPLACE on production schemas ---
    production_schemas = ['RAW', 'ANALYTICS', 'AI_OUTPUTS']
    if 'CREATE OR REPLACE' in sql_upper:
        for schema in production_schemas:
            if schema in sql_upper:
                return {
                    'action': 'warn',
                    'message': (
                        f'⚠️ WARNING: CREATE OR REPLACE on production schema ({schema}).\n'
                        f'SQL: {sql[:200]}...\n\n'
                        'This will drop and recreate the object, losing any data.\n'
                        'Consider using ALTER or DCM for safe changes.\n\n'
                        'Proceeding anyway...'
                    )
                }

    # --- WARN: GRANT ALL ---
    if 'GRANT ALL' in sql_upper:
        return {
            'action': 'warn',
            'message': (
                '⚠️ WARNING: GRANT ALL detected. This grants overly broad privileges.\n'
                'Consider granting specific privileges instead.\n\n'
                'Proceeding anyway...'
            )
        }

    # Allow everything else
    return {'action': 'allow'}
