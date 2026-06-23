# Day 5: Streamlit in Snowflake Workspaces

## Goal
Build and deploy a Streamlit app inside Snowflake Workspaces showing all Week 1 AI outputs.

## References
- [Streamlit in Workspaces overview](https://docs.snowflake.com/en/developer-guide/streamlit/streamlit-in-workspaces/streamlit-in-workspaces-overview)

## What to Do
1. Open Snowsight → Workspaces
2. Create a new workspace, connect to your Git repo or upload files manually
3. Use the `app/app.py` and `app/environment.yml` from this week's folder
4. Deploy and test all 4 tabs: Feedback, Images, Calls, Videos

## Key Features (Public Preview)
1. **File-based Workspaces**: standard files (`.py`, `.sql`, config) in an IDE
2. **Cortex Code Agent**: AI agent that reads/modifies your files and folders
3. **Containerized Streamlit**: runs using containerized compute — any Python library

## App Architecture
```
app.py              → Main Streamlit app (4 tabs)
environment.yml     → Snowflake conda dependencies
sql/                → SQL scripts (reference only, run separately)
```
