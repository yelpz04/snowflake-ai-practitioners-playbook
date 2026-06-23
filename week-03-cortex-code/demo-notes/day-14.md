# Day 14: Cortex Code Skills as Plugins, Not Prompts

## Goal
Create your own reusable custom skill and understand the plugin model.

## References
- [sfrt.io](https://www.sfrt.io/cortex-code-skills-90-days-in-plugins-not-prompts/)
- [Cortex Code extensibility docs](https://docs.snowflake.com/en/user-guide/cortex-code/extensibility)

## What to Do
1. Review `.cortex/skills/snowflake-sql-reviewer/SKILL.md`
2. Review `.cortex/skills/governance-checker/SKILL.md`
3. Test the SQL reviewer skill: write some bad SQL and see if it catches it
4. Understand the plugin model: skills, subagents, commands, hooks, MCP servers

## Plugin Model Components
```
.cortex/
├── skills/          → Reusable SKILL.md instructions
├── agents/          → Subagent definitions
├── commands/        → Custom CLI commands
├── hooks/           → Intercept and control tool calls
└── mcp-servers/     → Model Context Protocol integrations
```

## Key Insight
Skills are NOT one-off prompts. They are:
- Versioned in Git
- Reusable across projects
- Composable (skill calls skill)
- Testable (verify behavior with test cases)
