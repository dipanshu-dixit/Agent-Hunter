import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import subprocess
import time

API_BASE = "http://localhost:8000"

st.set_page_config(page_title="AgentScout", page_icon="🔭", layout="wide")

def fetch_data():
    try:
        agents_response = requests.get(f"{API_BASE}/agents?limit=1000", timeout=5)
        stats_response = requests.get(f"{API_BASE}/stats", timeout=5)
        
        if agents_response.status_code == 200 and stats_response.status_code == 200:
            return agents_response.json(), stats_response.json()
    except:
        pass
    return None, None

def main():
    st.title("🔭 AgentScout - Live AI Agent Radar")
    
    # Health check button
    if st.button("🔍 Check Agent Health"):
        with st.spinner("Checking agent health..."):
            subprocess.run(["python", "scanners/health_checker.py"], cwd=".")
        st.success("Health check completed!")
        st.rerun()
    
    agents_data, stats_data = fetch_data()
    
    if not agents_data or not stats_data:
        st.error("❌ Cannot connect to API. Make sure the server is running on localhost:8000")
        return
    
    df = pd.DataFrame(agents_data)
    
    # Handle missing columns for backward compatibility
    if 'status' not in df.columns:
        df['status'] = 'unchecked'
    if 'response_time_ms' not in df.columns:
        df['response_time_ms'] = None
    
    # Status counts
    status_counts = df['status'].value_counts().to_dict()
    
    # Metrics row 1
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Agents", len(df))
    with col2:
        st.metric("Unique Models", len([k for k in stats_data["models"].keys() if k != "unknown"]))
    with col3:
        st.metric("Unique Frameworks", len([k for k in stats_data["frameworks"].keys() if k != "unknown"]))
    
    # Metrics row 2
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("🟢 Online", status_counts.get("online", 0))
    with col2:
        st.metric("🔴 Dead", status_counts.get("dead", 0))
    with col3:
        st.metric("⚪ Unchecked", status_counts.get("unchecked", 0))
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Models Distribution")
        model_df = pd.DataFrame(list(stats_data["models"].items()), columns=["Model", "Count"])
        fig = px.pie(model_df, values="Count", names="Model")
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Frameworks Distribution")
        framework_df = pd.DataFrame(list(stats_data["frameworks"].items()), columns=["Framework", "Count"])
        fig = px.bar(framework_df, x="Framework", y="Count")
        st.plotly_chart(fig, use_container_width=True)
    
    # Sidebar filters
    st.sidebar.header("Filters")
    model_filter = st.sidebar.selectbox("Model", ["All"] + list(stats_data["models"].keys()))
    framework_filter = st.sidebar.selectbox("Framework", ["All"] + list(stats_data["frameworks"].keys()))
    status_filter = st.sidebar.selectbox("Show only", ["All", "Online", "Dead", "Unknown", "Unchecked"])
    
    # Filter dataframe
    filtered_df = df.copy()
    if model_filter != "All":
        filtered_df = filtered_df[filtered_df["model_detected"] == model_filter]
    if framework_filter != "All":
        filtered_df = filtered_df[filtered_df["framework"] == framework_filter]
    if status_filter != "All":
        filtered_df = filtered_df[filtered_df["status"] == status_filter.lower()]
    
    # Add status badges
    def format_status(status):
        badges = {
            "online": "🟢 online",
            "dead": "🔴 dead", 
            "unknown": "🟡 unknown",
            "unchecked": "⚪ unchecked",
            "redirected": "🟠 redirected"
        }
        return badges.get(status, status)
    
    filtered_df["status_badge"] = filtered_df["status"].apply(format_status)
    
    # Dataframe
    st.subheader("Agent Database")
    display_df = filtered_df[["name", "model_detected", "framework", "agent_type", "stars", "source_platform", "status_badge", "response_time_ms", "source_url"]]
    display_df.columns = ["Name", "Model", "Framework", "Type", "Stars", "Platform", "Status", "Response (ms)", "URL"]
    st.dataframe(display_df, use_container_width=True)
    
    # Auto-refresh
    time.sleep(60)
    st.rerun()

if __name__ == "__main__":
    main()