# Day 16: AI Agent Identity and Governance

## Goal
Understand the agent identity problem and create an identity model for your AI agents.

## References
- [Agent identity blog](https://www.snowflake.com/en/blog/ai-agent-identity-governance-enterprise-trust/)

## What to Do
1. Read the blog post on AI agent identity
2. Map the identity model for your POC:
   - Who is the user?
   - What role does the agent use?
   - Is there a service principal?
   - What data can the agent access?
   - What actions can the agent take?
   - How are agent actions audited?
3. Create a diagram (for LinkedIn/Medium)

## Agent Identity Model

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐
│   USER      │────→│   ROLE       │────→│  AGENT OBJECT   │
│ (human)     │     │ (SYSADMIN,   │     │ (Cortex Agent,  │
│             │     │  ANALYST)    │     │  Intelligence)  │
└─────────────┘     └──────────────┘     └────────┬────────┘
                                                   │
                         ┌────────────────────────┼────────────────┐
                         │                        │                │
                    ┌────▼────┐            ┌──────▼──────┐   ┌────▼────┐
                    │ POLICY  │            │ AUDIT TRAIL │   │ TOOLS   │
                    │ BOUNDARY│            │ (who did    │   │ (SQL,   │
                    │ (RAP,   │            │  what,      │   │  API,   │
                    │  masking)│            │  when)      │   │  search)│
                    └─────────┘            └─────────────┘   └─────────┘
```

## Key Questions
- If an AI agent queries customer PII, who is accountable?
- If an agent makes a wrong recommendation and someone acts on it, who owns that?
- How do you differentiate between "user asked the agent" vs. "agent acted autonomously"?

## LinkedIn Post Angle
"Your AI agent has access to your data, your tools, and your customers' information. But does it have an identity? Does it have an audit trail? Does it have policy boundaries? If not, you have a governance gap."

## Medium Article Section
"Day 16: The identity crisis of AI agents — why governance is the missing layer in enterprise AI."
