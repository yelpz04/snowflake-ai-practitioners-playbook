# MediaIntel — Multimodal AI Media Asset Intelligence
# App 6 of 10: AI_COMPLETE (image/audio/video) + Cortex Search

import streamlit as st
import pandas as pd
from snowflake.snowpark.context import get_active_session
from snowflake.cortex import CortexSearch
import json

session = get_active_session()
st.set_page_config(page_title="MediaIntel", page_icon="🎬", layout="wide")
st.title("🎬 MediaIntel — AI-Powered Media Asset Intelligence")
st.caption("One API for images, audio, and video — all inside Snowflake")

tab1, tab2, tab3 = st.tabs(["📤 Upload & Analyse", "🗄️ Asset Catalog", "🔍 Semantic Search"])

PROMPTS = {
    "IMAGE": (
        "Analyse this image. Return ONLY valid JSON with these fields: "
        "category (string), detected_text (array of strings), "
        "dominant_colors (array of strings), brand_present (boolean), "
        "quality_score (integer 1-10), tags (array of strings), "
        "accessibility_description (string), summary (string)."
    ),
    "AUDIO": (
        "Transcribe and analyse this audio. Return ONLY valid JSON: "
        "transcript (string), summary (2 sentences as string), "
        "topics (array), sentiment (positive/neutral/negative), "
        "speaker_count (integer), language (string)."
    ),
    "VIDEO": (
        "Analyse this video. Return ONLY valid JSON: "
        "scene_count (integer), topics (array), mood (string), "
        "text_on_screen (array), compliance_flags (array), "
        "summary (string, 3 sentences), transcript (string or null)."
    )
}

ACCEPT_MAP = {"IMAGE": "image/*", "AUDIO": "audio/*", "VIDEO": "video/*"}

# ── TAB 1: Upload & Analyse ──────────────────────────────────────────────────
with tab1:
    asset_type = st.selectbox("Asset type:", ["IMAGE", "AUDIO", "VIDEO"])
    uploaded   = st.file_uploader(f"Upload a {asset_type.lower()} file:",
                                   type={"IMAGE": ["jpg","jpeg","png","gif","webp"],
                                         "AUDIO": ["mp3","wav","m4a","ogg"],
                                         "VIDEO": ["mp4","mov","avi","webm"]}[asset_type])

    if uploaded and st.button("🤖 Analyse with AI"):
        stage_path = f"@MEDIA_INTEL.PUBLIC.MEDIA_STAGE/{asset_type.lower()}s/{uploaded.name}"
        with st.spinner("Uploading to stage..."):
            session.file.put_stream(uploaded, stage_path, auto_compress=False, overwrite=True)

        with st.spinner(f"Running AI_COMPLETE on {asset_type.lower()}..."):
            result = session.sql(f"""
                SELECT SNOWFLAKE.CORTEX.AI_COMPLETE(
                    'claude-sonnet-4-5',
                    '{PROMPTS[asset_type]}',
                    TO_FILE('{stage_path}')
                ) AS ai_output
            """).collect()[0][0]

        try:
            parsed = json.loads(result)
        except Exception:
            parsed = {"raw": result}

        st.success("Analysis complete!")
        col1, col2 = st.columns(2)
        with col1:
            st.json(parsed)
        with col2:
            if "summary" in parsed:
                st.info(f"**Summary:** {parsed['summary']}")
            if "sentiment" in parsed:
                emoji = {"positive": "😊", "neutral": "😐", "negative": "😟"}.get(parsed["sentiment"], "")
                st.metric("Sentiment", f"{emoji} {parsed['sentiment']}")
            if "compliance_flags" in parsed and parsed["compliance_flags"]:
                st.error(f"⚠️ Compliance flags: {', '.join(parsed['compliance_flags'])}")
            if "quality_score" in parsed:
                st.metric("Quality Score", f"{parsed['quality_score']}/10")
            if "tags" in parsed:
                st.write("**Tags:**", " ".join([f"`{t}`" for t in parsed["tags"]]))

        # Save to catalog
        safe_json = result.replace("'", "''")
        session.sql(f"""
            INSERT INTO MEDIA_INTEL.PUBLIC.MEDIA_CATALOG (ASSET_ID, MEDIA_FILE_NAME, ASSET_TYPE, AI_OUTPUT)
            SELECT UUID_STRING(), '{uploaded.name}', '{asset_type}', PARSE_JSON('{safe_json}')
        """).collect()
        st.caption("✅ Saved to media catalog.")

# ── TAB 2: Asset Catalog ─────────────────────────────────────────────────────
with tab2:
    filter_type = st.selectbox("Filter by type:", ["All", "IMAGE", "AUDIO", "VIDEO"])
    where = f"WHERE ASSET_TYPE = '{filter_type}'" if filter_type != "All" else ""
    catalog = session.sql(f"""
        SELECT MEDIA_FILE_NAME, ASSET_TYPE,
               LEFT(SUMMARY, 150) AS summary_preview,
               SENTIMENT, ANALYSED_AT
        FROM MEDIA_INTEL.PUBLIC.MEDIA_CATALOG {where}
        ORDER BY ANALYSED_AT DESC LIMIT 100
    """).to_pandas()

    if catalog.empty:
        st.info("No assets analysed yet. Upload a file in the 'Upload & Analyse' tab.")
    else:
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Assets", len(catalog))
        c2.metric("Compliance Flags", session.sql(
            "SELECT COUNT(*) FROM MEDIA_INTEL.PUBLIC.MEDIA_CATALOG WHERE ARRAY_SIZE(COMPLIANCE_FLAGS) > 0"
        ).collect()[0][0])
        c3.metric("Positive Sentiment", len(catalog[catalog["SENTIMENT"] == "positive"]))
        st.dataframe(catalog, use_container_width=True)

# ── TAB 3: Semantic Search ───────────────────────────────────────────────────
with tab3:
    q = st.text_input("Search across all media:", placeholder="clips about product launch in Asia")
    if q:
        results = CortexSearch.search(
            service="MEDIA_INTEL.PUBLIC.MEDIA_SEARCH",
            query=q,
            columns=["MEDIA_FILE_NAME", "ASSET_TYPE", "SENTIMENT", "TRANSCRIPT"],
            limit=10
        )
        for r in (results.results if results else []):
            with st.expander(f"**{r['MEDIA_FILE_NAME']}** ({r['ASSET_TYPE']})"):
                st.write(r.get("TRANSCRIPT", "No transcript available.")[:500])
                st.caption(f"Sentiment: {r.get('SENTIMENT', 'n/a')}")
