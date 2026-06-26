# LineageAI — AI Data Lineage & Catalog Explorer
# App 4 of 10: AI_COMPLETE + OBJECT_DEPENDENCIES + ACCESS_HISTORY

import streamlit as st
import pandas as pd
from snowflake.snowpark.context import get_active_session
from snowflake.cortex import Complete, CortexSearch

session = get_active_session()
st.set_page_config(page_title="LineageAI", page_icon="🔗", layout="wide")
st.title("🔗 LineageAI — Intelligent Data Lineage")

tab1, tab2, tab3 = st.tabs(["🔍 Explore Lineage", "📚 AI Data Catalog", "💥 Impact Analysis"])

with tab1:
    st.subheader("Upstream / Downstream Lineage")
    table_input = st.text_input("Enter table name (e.g. SALES_ORDERS):", "")
    direction = st.radio("Direction:", ["Upstream (what feeds this)", "Downstream (what this feeds)"], horizontal=True)

    if table_input:
        if "Upstream" in direction:
            query = f"""
                SELECT REFERENCED_OBJECT_NAME AS related_table,
                       REFERENCED_OBJECT_TYPE AS object_type,
                       DEPENDENCY_TYPE
                FROM SNOWFLAKE.ACCOUNT_USAGE.OBJECT_DEPENDENCIES
                WHERE OBJECT_NAME ILIKE '%{table_input}%'
                LIMIT 50"""
        else:
            query = f"""
                SELECT OBJECT_NAME AS related_table,
                       OBJECT_TYPE AS object_type, DEPENDENCY_TYPE
                FROM SNOWFLAKE.ACCOUNT_USAGE.OBJECT_DEPENDENCIES
                WHERE REFERENCED_OBJECT_NAME ILIKE '%{table_input}%'
                LIMIT 50"""
        df = session.sql(query).to_pandas()
        if df.empty:
            st.info("No dependencies found. Check table name or ACCOUNT_USAGE availability.")
        else:
            st.dataframe(df, use_container_width=True)
            st.caption(f"Found {len(df)} {'upstream' if 'Upstream' in direction else 'downstream'} dependencies")

with tab2:
    st.subheader("AI-Generated Data Catalog")
    search_q = st.text_input("Search catalog by meaning:", placeholder="find all customer PII tables")

    if search_q:
        results = CortexSearch.search(
            service="LINEAGE_AI.PUBLIC.CATALOG_SEARCH",
            query=search_q,
            columns=["TABLE_NAME", "SCHEMA_NAME", "AI_DESCRIPTION", "SENSITIVITY_LEVEL"],
            limit=10
        )
        for r in (results.results if results else []):
            badge = {"PII": "🔴", "FINANCIAL": "🟠", "OPERATIONAL": "🟢", "REFERENCE": "🔵"}.get(
                r.get("SENSITIVITY_LEVEL", ""), "⚪")
            with st.expander(f"{badge} {r['SCHEMA_NAME']}.{r['TABLE_NAME']}"):
                st.write(r["AI_DESCRIPTION"])
                st.caption(f"Sensitivity: {r.get('SENSITIVITY_LEVEL', 'Unknown')}")
    else:
        catalog = session.sql(
            "SELECT DB_NAME, SCHEMA_NAME, TABLE_NAME, LEFT(AI_DESCRIPTION, 120) AS description, "
            "SENSITIVITY_LEVEL FROM LINEAGE_AI.PUBLIC.TABLE_CATALOG ORDER BY CATALOGUED_AT DESC LIMIT 50"
        ).to_pandas()
        st.dataframe(catalog, use_container_width=True)

    if st.button("🤖 Auto-catalog new tables"):
        with st.spinner("AI is describing your tables..."):
            session.sql("""
                INSERT INTO LINEAGE_AI.PUBLIC.TABLE_CATALOG
                    (DB_NAME, SCHEMA_NAME, TABLE_NAME, AI_DESCRIPTION, SENSITIVITY_LEVEL)
                SELECT TABLE_CATALOG, TABLE_SCHEMA, TABLE_NAME,
                    TRY_PARSE_JSON(SNOWFLAKE.CORTEX.AI_COMPLETE(
                        'claude-sonnet-4-5',
                        'Write a 2-sentence description of what this Snowflake table contains '
                        'and its business purpose. Return ONLY JSON: '
                        '{"description": "...", "sensitivity": "PII|FINANCIAL|OPERATIONAL|REFERENCE"}. '
                        'Table name: ' || TABLE_CATALOG || '.' || TABLE_SCHEMA || '.' || TABLE_NAME,
                        {}))::VARIANT:description::STRING,
                    TRY_PARSE_JSON(SNOWFLAKE.CORTEX.AI_COMPLETE(
                        'claude-sonnet-4-5',
                        'Classify this table. Return ONLY JSON: {"sensitivity": "PII|FINANCIAL|OPERATIONAL|REFERENCE"}. '
                        'Table: ' || TABLE_NAME, {}))::VARIANT:sensitivity::STRING
                FROM INFORMATION_SCHEMA.TABLES
                WHERE TABLE_TYPE = 'BASE TABLE'
                AND TABLE_NAME NOT IN (SELECT TABLE_NAME FROM LINEAGE_AI.PUBLIC.TABLE_CATALOG)
                LIMIT 20
            """).collect()
            st.success("Catalog updated.")

with tab3:
    st.subheader("Impact Analysis — What Breaks If I Change This?")
    target = st.text_input("Table or view to analyse:", placeholder="SALES_ORDERS")
    if target and st.button("Run Impact Analysis"):
        downstream = session.sql(f"""
            WITH RECURSIVE deps AS (
                SELECT OBJECT_NAME AS obj, 1 AS depth
                FROM SNOWFLAKE.ACCOUNT_USAGE.OBJECT_DEPENDENCIES
                WHERE REFERENCED_OBJECT_NAME ILIKE '%{target}%'
                UNION ALL
                SELECT od.OBJECT_NAME, d.depth + 1
                FROM deps d JOIN SNOWFLAKE.ACCOUNT_USAGE.OBJECT_DEPENDENCIES od
                ON d.obj = od.REFERENCED_OBJECT_NAME
                WHERE d.depth < 8
            )
            SELECT DISTINCT obj AS affected_object, depth AS hops FROM deps ORDER BY depth
        """).to_pandas()

        if downstream.empty:
            st.success(f"✅ No downstream dependencies found for {target}.")
        else:
            st.error(f"⚠️ Changing {target} affects {len(downstream)} downstream objects")
            st.dataframe(downstream, use_container_width=True)
            impact = Complete(
                "claude-sonnet-4-5",
                f"Summarise the risk of modifying or dropping {target} in Snowflake. "
                f"It has {len(downstream)} downstream dependencies across up to {downstream['HOPS'].max()} hops. "
                f"Affected objects: {', '.join(downstream['AFFECTED_OBJECT'].head(10).tolist())}. "
                "Give a 2-sentence risk summary and one recommendation."
            )
            st.info(f"**AI Risk Summary:** {impact}")
