# From CoCo Chat to Live URL in 5 Minutes: Snowflake App Runtime Is Genuinely Different

### Every "build apps without infrastructure" promise has failed data teams. Snowflake App Runtime is the first one that actually delivers — because your app runs inside Snowflake, next to your data, with your governance already attached.

*Part of **The Snowflake AI Practitioner's Playbook** — a series of deep dives into production-ready Snowflake AI. [Start from Part 1 →](link)*

---

I've shipped internal data apps before. Streamlit in Docker. Dash behind a reverse proxy. Flask with a secrets manager and 400 lines of IAM policy. The apps work. The path to production doesn't.

The pattern is always the same: the data is in Snowflake, the app is somewhere else, and you spend three weeks building the bridge — credentials, network policies, access controls, deployment pipelines — before a single business user can click anything.

**Snowflake App Runtime flips this.** Your app lives inside Snowflake, next to your data. Governance is inherited. There's no bridge to build.

This article walks through every new app capability announced at Summit 2026 — App Runtime, Vercel integration, Streamlit GA upgrades — with working code throughout.

---

## What shipped at Summit 2026

Four things changed for app builders on Snowflake this month:

**1. Snowflake App Runtime (Public Preview)** — Full-stack Node.js apps that run inside Snowflake. No Docker. No infra. Deploy with one command.

**2. Vercel integration (Public Preview)** — Generate a full-stack app with v0's natural language builder, connect to Snowflake, deploy with one click.

**3. Streamlit in Workspaces (GA)** — Browser-based editor, Git integration, AI coding assist. No local Python setup required.

**4. Next-Gen Streamlit Runtime (GA)** — Same-day Python library availability, faster load times, full parity with open-source Streamlit.

**5. Business User Access for Streamlit (GA)** — Non-technical users land directly in Streamlit apps via SSO, no Snowflake account required.

---

## The problem these solve

Here's what enterprise app deployment looked like before:

```
The old path (6–12 weeks):
1. Build prototype locally          → Week 1
2. Containerize it                  → Week 2
3. Security review                  → Weeks 3–5
4. Set up cloud infrastructure      → Week 6
5. Configure secrets manager        → Week 7
6. Wire up SSO                      → Week 8–9
7. Deploy to staging                → Week 10
8. Performance testing              → Week 11
9. Production deploy                → Week 12
   
And your data was in Snowflake the whole time.
```

**The new path (< 1 day):**
```
1. Talk to CoCo Desktop             → Minutes
2. CoCo scaffolds the project       → Minutes
3. Deploy to Snowflake App Runtime  → 1 command
4. Business user accesses via SSO   → Works immediately
   
Governance: inherited from Snowflake (RBAC, masking, lineage)
Infrastructure: zero
Security review: the data never left Snowflake
```

That's not an exaggeration. Let me show you the actual workflow.

---

## Building a Revenue Ops decision portal with App Runtime

### Step 1: Scaffold from a CoCo conversation

Open CoCo Desktop and start a session:

```
You: Build me an internal web app for revenue operations.
     It should:
     - Show a real-time pipeline view of SALES_ORDERS from REVENUE_OPS_AI
     - Let sales managers filter by region and date range
     - Flag high-risk deals (from RISK_ALERTS table) in red
     - Include an "Ask AI" button that queries our data in natural language
     
     Use Snowflake App Runtime (Node.js). Make it production-ready.
```

CoCo:
1. Reads your REVENUE_OPS_AI schema
2. Generates the project structure
3. Wires up your tables with correct column names and RBAC
4. Deploys to App Runtime

**Generated project structure:**
```
revenue-ops-portal/
├── app.js                 # Entry point (Express)
├── package.json
├── public/
│   └── index.html         # React frontend
├── routes/
│   ├── pipeline.js        # GET /api/pipeline
│   ├── risk-alerts.js     # GET /api/risk-alerts
│   └── ai-query.js        # POST /api/ask
└── snowflake.config.json  # Auto-generated connection config
```

### Step 2: The backend — connecting to your Snowflake data

```javascript
// routes/pipeline.js
// CoCo generates this with YOUR actual column names
const snowflake = require('snowflake-sdk');
const { getConnection } = require('../lib/snowflake-client');

module.exports = async function pipelineRoutes(fastify) {
  fastify.get('/api/pipeline', async (request, reply) => {
    const { region, start_date, end_date, limit = 100 } = request.query;
    const conn = await getConnection();

    // App Runtime: connection runs under the requesting user's RBAC
    // No hardcoded credentials — Snowflake handles auth
    let query = `
      SELECT
        o.ORDER_ID,
        o.ACCOUNT_NAME,
        o.ACV,
        o.STAGE,
        o.REGION,
        o.SALES_REP,
        o.CREATED_AT,
        r.RISK_LABEL,
        r.RISK_CONFIDENCE
      FROM REVENUE_OPS_AI.RAW.SALES_ORDERS o
      LEFT JOIN REVENUE_OPS_AI.ANALYTICS.RISK_ALERTS r
        ON o.ORDER_ID = r.ORDER_ID
      WHERE 1=1
    `;

    const binds = [];
    if (region) {
      query += ` AND o.REGION = ?`;
      binds.push(region);
    }
    if (start_date) {
      query += ` AND o.CREATED_AT >= ?`;
      binds.push(start_date);
    }
    if (end_date) {
      query += ` AND o.CREATED_AT <= ?`;
      binds.push(end_date);
    }

    query += ` ORDER BY o.CREATED_AT DESC LIMIT ?`;
    binds.push(parseInt(limit));

    const rows = await conn.execute(query, binds);
    return { data: rows, count: rows.length };
  });
};
```

```javascript
// routes/ai-query.js
// Natural language → SQL → results, using CoCo Agent SDK
const { query: cocoQuery } = require('cortex-code-agent-sdk');

module.exports = async function aiQueryRoutes(fastify) {
  fastify.post('/api/ask', async (request, reply) => {
    const { question } = request.body;

    if (!question || question.length > 500) {
      return reply.status(400).send({ error: 'Invalid question' });
    }

    // Use CoCo Agent SDK to answer the question
    // Runs under the app's Snowflake RBAC — no extra permissions needed
    let answer = '';
    for await (const message of cocoQuery({
      prompt: `You are a revenue operations AI assistant. 
               Database: REVENUE_OPS_AI. 
               Answer this question using SQL and explain the result: ${question}`,
      options: { connection: 'app-runtime-connection' }
    })) {
      if (message.type === 'assistant') {
        for (const block of message.content) {
          if (block.type === 'text') answer += block.text;
        }
      }
    }

    return { answer };
  });
};
```

### Step 3: Deploy to App Runtime

```bash
# One command. That's it.
snowflake app deploy --project ./revenue-ops-portal

# Output:
# ✓ Building project...
# ✓ Uploading to Snowflake App Runtime...
# ✓ Configuring RBAC...
# ✓ Setting up SSO...
# 
# App deployed: https://app-xyz.snowflakeapp.com/revenue-ops-portal
# 
# RBAC: Inherits from REVOPS_READ_ROLE
# Access logs: SNOWFLAKE.ACCOUNT_USAGE.ACCESS_HISTORY
# Cost budget: $50/month (set in snowflake.config.json)
```

The URL is live. SSO configured. Access logs running. Cost bounded. No infra decision made.

---

## Vercel integration — generate, connect, deploy

For teams already using Vercel's v0 for UI generation, the Snowflake integration makes the full workflow seamless:

**In v0 (Vercel's natural language app builder):**
```
Prompt: Build a revenue pipeline dashboard with:
- Table showing recent deals colored by risk level
- Bar chart of revenue by region  
- Filter dropdowns for date range and sales rep
- Dark mode, clean design, works on mobile
```

v0 generates the full React component. Then:

```bash
# In your terminal (Vercel CLI):
vercel deploy --provider snowflake

# This:
# 1. Creates a Snowflake App Runtime instance
# 2. Wires up OAuth to your Snowflake account
# 3. Inherits your RBAC automatically
# 4. Deploys to a governed Snowflake URL

# No manual OAuth setup. No credentials in environment variables.
# The app talks to Snowflake as the authenticated user.
```

**The governance piece is what makes this real:**

```
With generic Vercel deploy:
App → API Key → Snowflake (key has broad access, stored in env var)
Problem: Key gets rotated → app breaks, Key gets leaked → data breach

With Snowflake-integrated Vercel deploy:
App → OAuth (user's own token) → Snowflake (user's RBAC applies)
Result: App can only see what the user is allowed to see
        No stored credentials. No rotation problem. No blast radius.
```

---

## Streamlit GA upgrades — what actually changed

Streamlit in Snowflake has been around for a while. Three features just hit GA that meaningfully change the workflow:

### Streamlit in Workspaces (GA)

Before: Write Streamlit locally, upload to Snowflake, debug in the dark.
Now: Browser-based editor, Git integration, AI coding assist (CoCo), live preview.

```python
# This is still the same Streamlit you know
# The difference is where you write and deploy it

import streamlit as st
import snowflake.snowpark.functions as F
from snowflake.snowpark.context import get_active_session

# In Workspaces, this session is already there — no connection code
session = get_active_session()

st.title("Revenue Ops — Live Pipeline")

# Query your data
df = session.table("REVENUE_OPS_AI.ANALYTICS.ORDERS_RISK_ENRICHED") \
    .filter(F.col("RISK_LABEL") == "high_risk") \
    .order_by(F.col("ENRICHED_AT").desc()) \
    .limit(50) \
    .to_pandas()

# Show it
st.metric("High-Risk Deals", len(df))
st.dataframe(df, use_container_width=True)
```

**Git integration means:**
- Push to `main` → auto-deploys to production Streamlit
- Push to `dev` → preview environment, doesn't affect users
- Full PR review flow for data apps

### Next-Gen Streamlit Runtime (GA)

**What changed:** Same-day Python library availability.

Before: A new version of `pandas`, `plotly`, or `scikit-learn` would take weeks to appear in Snowflake's Streamlit environment.
Now: Available the same day it's on PyPI.

```python
# requirements.txt in your Snowflake Streamlit project
# These are now available same-day as PyPI release:
pandas>=2.2.0
plotly>=5.20.0
scikit-learn>=1.5.0
anthropic>=0.30.0  # Same-day if just released
```

### Business User Access for Streamlit (GA)

This is the quiet one with the biggest enterprise impact.

Before: A business user who wanted to see a Streamlit dashboard needed a Snowflake account, a role, and someone to onboard them.
Now: SSO. They log in with their company Google/Okta/Azure credentials. The Streamlit app appears. No Snowflake account required on their end.

```python
# Nothing changes in your Streamlit code
# The difference is in the deployment settings:

# snowflake.yml (your project config)
streamlit:
  name: revenue-ops-dashboard
  warehouse: REVOPS_AI_WH
  access:
    business_user_access: true  # ← This enables SSO for non-Snowflake users
    allowed_domains:
      - company.com
      - contractor.company.com
```

When `business_user_access: true`, Snowflake provisions SSO-only access tokens mapped to specific roles. Business users get a real app experience. You get full audit logs of who accessed what.

---

## The complete Revenue Ops app (Streamlit, production-ready)

```python
# revenue_ops_dashboard.py
# Snowflake Streamlit in Workspaces — copy-paste ready

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from snowflake.snowpark.context import get_active_session
import snowflake.snowpark.functions as F
import pandas as pd

st.set_page_config(
    page_title="Revenue Ops Command Center",
    page_icon="📊",
    layout="wide"
)

session = get_active_session()

# ── Header ───────────────────────────────────────────────────────────────────
st.title("📊 Revenue Ops Command Center")
st.caption("Live data · Refreshes every 60 seconds · Powered by Snowflake Cortex AI")

# ── Filters ──────────────────────────────────────────────────────────────────
col1, col2, col3 = st.columns(3)
with col1:
    regions = ["All"] + session.table("REVENUE_OPS_AI.RAW.SALES_ORDERS") \
        .select("REGION").distinct().sort("REGION").to_pandas()["REGION"].tolist()
    region = st.selectbox("Region", regions)
with col2:
    stages = ["All", "Prospecting", "Qualified", "Proposal", "Negotiation", "Closed"]
    stage = st.selectbox("Stage", stages)
with col3:
    risk_filter = st.multiselect(
        "Risk Level",
        ["high_risk", "needs_attention", "on_track", "upsell_opportunity"],
        default=["high_risk", "needs_attention"]
    )

# ── Query ────────────────────────────────────────────────────────────────────
df_raw = session.table("REVENUE_OPS_AI.ANALYTICS.ORDERS_RISK_ENRICHED")
if region != "All":
    df_raw = df_raw.filter(F.col("REGION") == region)
if stage != "All":
    df_raw = df_raw.filter(F.col("STAGE") == stage)
if risk_filter:
    df_raw = df_raw.filter(F.col("RISK_LABEL").isin(risk_filter))

df = df_raw.order_by(F.col("ENRICHED_AT").desc()).limit(200).to_pandas()

# ── KPIs ─────────────────────────────────────────────────────────────────────
k1, k2, k3, k4 = st.columns(4)
k1.metric("Pipeline Value", f"${df['ACV'].sum():,.0f}")
k2.metric("Deals", len(df))
k3.metric(
    "High Risk",
    len(df[df["RISK_LABEL"] == "high_risk"]),
    delta=f"{len(df[df['RISK_LABEL']=='high_risk'])} need attention",
    delta_color="inverse"
)
k4.metric(
    "Avg Risk Confidence",
    f"{df['RISK_CONFIDENCE'].mean():.0%}" if len(df) > 0 else "—"
)

st.divider()

# ── Charts ───────────────────────────────────────────────────────────────────
c1, c2 = st.columns(2)

with c1:
    region_data = df.groupby("REGION")["ACV"].sum().reset_index()
    fig = px.bar(
        region_data, x="REGION", y="ACV",
        title="Pipeline by Region",
        color="ACV", color_continuous_scale="Blues"
    )
    fig.update_layout(showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

with c2:
    risk_data = df["RISK_LABEL"].value_counts().reset_index()
    risk_data.columns = ["Risk", "Count"]
    colors = {
        "high_risk": "#FF6B6B",
        "needs_attention": "#FFD43B",
        "on_track": "#51CF66",
        "upsell_opportunity": "#339AF0"
    }
    fig = px.pie(
        risk_data, values="Count", names="Risk",
        title="Deal Distribution by AI Risk Classification",
        color="Risk",
        color_discrete_map=colors
    )
    st.plotly_chart(fig, use_container_width=True)

# ── Deal Table ───────────────────────────────────────────────────────────────
st.subheader("Deal Pipeline")

display_cols = ["ACCOUNT_NAME", "REGION", "STAGE", "ACV", "RISK_LABEL",
                "RISK_CONFIDENCE", "SALES_REP", "ENRICHED_AT"]
df_display = df[display_cols].copy()
df_display["ACV"] = df_display["ACV"].apply(lambda x: f"${x:,.0f}")
df_display["RISK_CONFIDENCE"] = df_display["RISK_CONFIDENCE"].apply(
    lambda x: f"{x:.0%}" if pd.notna(x) else "—"
)

def color_risk_row(row):
    color_map = {
        "high_risk": "background-color: #ffebe9",
        "needs_attention": "background-color: #fff8e1",
        "upsell_opportunity": "background-color: #e8f5e9",
        "on_track": ""
    }
    color = color_map.get(row["RISK_LABEL"], "")
    return [color] * len(row)

st.dataframe(
    df_display.style.apply(color_risk_row, axis=1),
    use_container_width=True,
    height=400
)

# ── Ask AI ───────────────────────────────────────────────────────────────────
st.divider()
st.subheader("Ask the Revenue AI")
question = st.text_input(
    "Ask a question about your pipeline",
    placeholder="Which APAC accounts have the highest renewal risk?"
)

if question and st.button("Ask", type="primary"):
    with st.spinner("Querying Cortex AI..."):
        response = session.sql(f"""
            SELECT SNOWFLAKE.CORTEX.AI_COMPLETE(
                'claude-sonnet-4-6',
                'You are a Revenue Operations AI. Answer this question about 
                 the REVENUE_OPS_AI database in Snowflake. Be specific and 
                 data-driven: {question.replace("'", "\\'")}
                 
                 Base your answer on these tables:
                 - REVENUE_OPS_AI.RAW.SALES_ORDERS (order data)
                 - REVENUE_OPS_AI.ANALYTICS.ORDERS_RISK_ENRICHED (AI-enriched)
                 - REVENUE_OPS_AI.ANALYTICS.RISK_ALERTS (flagged deals)
                 
                 Give a concise answer with specific numbers where possible.'
            )
        """).collect()[0][0]
    st.markdown(response)
```

---

## Which surface should you use?

```
│ What you need                        │ Use                            │
│──────────────────────────────────────│────────────────────────────────│
│ Internal data app, any language      │ Snowflake App Runtime ✅        │
│ Generate UI without writing React    │ Vercel + v0 + Snowflake ✅      │
│ Business users need access (no acct) │ Streamlit + Business User ✅    │
│ Data team building/iterating fast    │ Streamlit in Workspaces ✅      │
│ Distribute to 10K+ customers         │ Snowflake Native App Framework  │
│ Quick internal dashboard             │ Streamlit (still great) ✅      │
│ Full-stack portal, custom UI         │ App Runtime + Node.js ✅        │
```

---

## Key takeaways

1. **App Runtime removes the infra barrier.** Your Node.js app runs inside Snowflake. One deploy command. RBAC inherited. No credentials to rotate.

2. **Vercel integration makes Snowflake the deployment target for AI-generated apps.** Generate with v0, deploy to Snowflake. OAuth handles auth. No env vars with secrets.

3. **Business User Access for Streamlit is the quiet enterprise win.** SSO for non-Snowflake users. Data teams build apps that business stakeholders can actually use, without onboarding anyone to Snowflake.

4. **Same-day Python libraries fix the most frustrating Streamlit limitation.** No more waiting weeks for a new `plotly` version to show up in the managed environment.

5. **The theme across all of these:** Snowflake is collapsing the distance between your data and your app. When they live together, governance is automatic and the "weeks of infrastructure" problem disappears.

---

*→ Next: [Day 37 — Publish Once, Available Everywhere: The Agent Discovery Protocol That Connects Your Cortex Agents to Every AI Interface](link)*

*← Previous: [Day 35 — CoCo Desktop: The Data Engineering Agent That Outscores Claude Code](link)*

---

*🔗 Sources: [Snowflake Apps blog](https://www.snowflake.com/en/blog/snowflake-apps-build-deploy-faster/) | [App Runtime docs](https://docs.snowflake.com/en/developer-guide/snowflake-app-runtime/about-snowflake-app-runtime) | [Streamlit in Workspaces docs](https://docs.snowflake.com/en/developer-guide/streamlit/streamlit-in-workspaces/streamlit-in-workspaces-overview) | [Vercel + Snowflake](https://v0.app/docs/snowflake)*

---

**About the Author:** *Payal Chauhan is a Data Engineer specializing in Snowflake AI, Cortex Agents, and agentic data systems. She has hands-on experience with 20+ cutting-edge Snowflake features — from multimodal AI to multi-agent architectures. This series represents 37 end-to-end implementations built publicly to help data teams go from Snowflake announcement to production without the guesswork. Follow on [Medium](link) · [LinkedIn](link)*


*Tags: `Snowflake` `Streamlit` `App Runtime` `Vercel` `Data Apps` `CoCo` `Summit 2026` `Enterprise Apps` `Node.js`*
