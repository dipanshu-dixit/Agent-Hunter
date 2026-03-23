import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
from pathlib import Path
from collections import Counter

st.set_page_config(
    page_title="AgentHunter",
    page_icon="🔭",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Space+Grotesk:wght@300;400;600;700&display=swap');
html, body, [class*="css"] {
    font-family: 'Space Grotesk', sans-serif;
    background-color: #0a0a0f;
    color: #e2e8f0;
}
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 1.5rem 2rem 2rem; max-width: 100%; }
[data-testid="metric-container"] {
    background: linear-gradient(135deg, #13131f 0%, #1a1a2e 100%);
    border: 1px solid #2d2d4e;
    border-radius: 12px;
    padding: 1.2rem 1.5rem;
}
[data-testid="stMetricValue"] {
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 2.2rem !important;
    font-weight: 700 !important;
    color: #a5b4fc !important;
}
[data-testid="stMetricLabel"] {
    font-size: 0.72rem !important;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: #64748b !important;
}
[data-testid="stSidebar"] { background: #0d0d1a !important; border-right: 1px solid #1e1e3a; }
.stButton > button {
    background: linear-gradient(135deg, #4f46e5, #7c3aed);
    color: white; border: none; border-radius: 8px;
    padding: 0.5rem 1.5rem; font-weight: 600; width: 100%;
}
div[data-testid="stDataFrame"] { border: 1px solid #2d2d4e; border-radius: 10px; }
.marquee { overflow:hidden; white-space:nowrap; background:#1a1a2e; padding:8px; border-radius:8px; font-family:'JetBrains Mono',monospace; color:#34d399; }
@keyframes marquee-scroll { 0%{transform:translateX(100%)} 100%{transform:translateX(-100%)} }
.marquee span { display:inline-block; animation:marquee-scroll 40s linear infinite; }
</style>
""", unsafe_allow_html=True)

BG     = "#0d0d1a"
COLORS = ["#4f46e5","#7c3aed","#2563eb","#0891b2","#059669","#d97706","#dc2626","#db2777","#0d9488","#ea580c"]


def calculate_pit_score(row):
    stars    = row.get("stars", 0) or 0
    rt       = row.get("response_time_ms", 1000) or 1000
    status_b = {"active": 1.5, "experimental": 1.2, "inactive": 0.6}.get(str(row.get("status", "")), 1.0)
    risk_b   = {"low": 1.2, "medium": 1.0, "high": 0.6}.get(str(row.get("risk_level", "")), 1.0)
    return round(stars * (1000 / max(rt, 10)) * status_b * risk_b, 1)


@st.cache_data(ttl=300)
def load_data():
    try:
        base = Path(__file__).resolve().parent
        with open(base / "agents_data.json") as f:
            agents = json.load(f)
        with open(base / "stats_data.json") as f:
            stats = json.load(f)
        return agents, stats
    except Exception as e:
        st.error(f"Data loading failed: {e}")
        return [], {}


agents, stats = load_data()
df = pd.DataFrame(agents) if agents else pd.DataFrame()

models_stat = stats.get("models", stats.get("by_model", {}))
fw_stat     = stats.get("frameworks", stats.get("by_framework", {}))
types_stat  = stats.get("agent_types", stats.get("by_agent_type", {}))


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style='text-align:center;padding:1rem 0 0.5rem'>
        <div style='font-size:2.2rem'>🔭</div>
        <div style='font-family:JetBrains Mono,monospace;font-size:1.1rem;font-weight:700;color:#a5b4fc;'>AgentHunter</div>
        <div style='font-size:0.65rem;color:#4f46e5;letter-spacing:.15em;text-transform:uppercase;margin-top:2px'>Live AI Agent Radar</div>
    </div>
    """, unsafe_allow_html=True)

    page = st.radio("Navigate", ["Main Dashboard", "Agent Pit 🥊"], label_visibility="collapsed")
    st.markdown("---")

    if page == "Main Dashboard":
        st.markdown("### 🔎 Filters")

        q = st.text_input("Search", placeholder="name, description, framework…", label_visibility="collapsed")

        models_opts = ["All"] + sorted([k for k in models_stat if k and k != "unknown"])
        fw_opts     = ["All"] + sorted([k for k in fw_stat     if k and k != "unknown"])
        type_opts   = ["All"] + sorted([k for k in types_stat  if k and k != "unknown"])
        plat_opts   = ["All"] + (sorted(df["source_platform"].dropna().unique().tolist()) if not df.empty else [])

        sel_model    = st.selectbox("🧠 Model",      models_opts)
        sel_fw       = st.selectbox("⚙️ Framework",  fw_opts)
        sel_type     = st.selectbox("🤖 Agent Type", type_opts)
        sel_platform = st.selectbox("📡 Platform",   plat_opts)

        max_stars  = int(df["stars"].max()) if not df.empty else 0
        star_range = st.slider("⭐ Min Stars", 0, min(max_stars, 50000), 0, step=100)

        sort_by = st.selectbox("↕️ Sort By", ["stars ↓", "first_seen ↓", "name ↑"])

        st.markdown("---")

    st.markdown("""
    <div style='font-size:0.78rem;line-height:2.2;color:#475569'>
        <a href='https://github.com/dipanshu-dixit/Agent-Hunter' target='_blank' style='color:#4f46e5'>🐙 GitHub Repo</a><br>
        <a href='https://huggingface.co/spaces/dipanshudixit/agent-hunter' target='_blank' style='color:#4f46e5'>🤗 HF Space</a><br>
        <span style='color:#334155;font-size:0.68rem'>
            Code: MIT License<br>
            Dataset: Personal Use Only
        </span>
    </div>
    """, unsafe_allow_html=True)


# ── Apply filters (Main Dashboard only) ──────────────────────────────────────
filtered = df.copy() if not df.empty else df

if page == "Main Dashboard" and not filtered.empty:
    if q:
        mask = (
            filtered["name"].astype(str).str.contains(q, case=False, na=False) |
            filtered["raw_description"].astype(str).str.contains(q, case=False, na=False) |
            filtered["framework"].astype(str).str.contains(q, case=False, na=False)
        )
        filtered = filtered[mask]
    if sel_model    != "All": filtered = filtered[filtered["model_detected"]  == sel_model]
    if sel_fw       != "All": filtered = filtered[filtered["framework"]        == sel_fw]
    if sel_type     != "All": filtered = filtered[filtered["agent_type"]       == sel_type]
    if sel_platform != "All": filtered = filtered[filtered["source_platform"]  == sel_platform]
    filtered = filtered[filtered["stars"] >= star_range]

    sort_map = {"stars ↓": ("stars", False), "first_seen ↓": ("first_seen", False), "name ↑": ("name", True)}
    col, asc = sort_map[sort_by]
    if col in filtered.columns:
        filtered = filtered.sort_values(col, ascending=asc)


# ══════════════════════════════════════════════════════════════════════════════
# MAIN DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════
if page == "Main Dashboard":

    # ── Header ────────────────────────────────────────────────────────────────
    st.markdown(f"""
<h1 style='font-family:JetBrains Mono,monospace;font-size:1.7rem;font-weight:700;color:#e2e8f0;margin:0;'>
    🔭 AgentHunter
    <span style='font-size:0.8rem;color:#34d399;background:#0d1f17;border:1px solid #34d399;border-radius:6px;padding:2px 10px;margin-left:8px;'>● LIVE</span>
</h1>
<p style='color:#64748b;font-size:0.82rem;margin:3px 0 16px'>
    Automated AI agent discovery &nbsp;·&nbsp;
    <b style='color:#a5b4fc'>{len(df):,}</b> agents catalogued &nbsp;·&nbsp;
    GitHub · HuggingFace · PyPI · npm
</p>
""", unsafe_allow_html=True)

    # ── Metrics ───────────────────────────────────────────────────────────────
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("🤖 Showing",    f"{len(filtered):,}")
    c2.metric("💾 Total DB",   f"{len(df):,}")
    c3.metric("🧠 Models",     len([k for k in models_stat if k and k != "unknown"]))
    c4.metric("⚙️ Frameworks", len([k for k in fw_stat     if k and k != "unknown"]))
    c5.metric("⭐ Top Stars",  f"{int(filtered['stars'].max()):,}" if not filtered.empty and filtered['stars'].max() > 0 else "0")
    c6.metric("📡 Platforms",  filtered["source_platform"].nunique() if not filtered.empty else 0)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Row 1: Models pie + Frameworks bar ────────────────────────────────────
    ch1, ch2 = st.columns(2)

    with ch1:
        st.markdown("#### 🧠 Models Distribution")
        mdf = pd.DataFrame([(k, v) for k, v in models_stat.items() if k], columns=["Model", "Count"])
        mdf = mdf.sort_values("Count", ascending=False).head(10)
        fig = px.pie(mdf, values="Count", names="Model", color_discrete_sequence=COLORS, hole=0.45)
        fig.update_traces(textposition="inside", textinfo="percent+label")
        fig.update_layout(paper_bgcolor=BG, plot_bgcolor=BG, font_color="#e2e8f0",
                          legend=dict(font=dict(size=11)), margin=dict(t=10, b=10))
        st.plotly_chart(fig, use_container_width=True)

    with ch2:
        st.markdown("#### ⚙️ Frameworks Distribution")
        fdf = pd.DataFrame([(k, v) for k, v in fw_stat.items() if k and k != "unknown"], columns=["Framework", "Count"])
        fdf = fdf.sort_values("Count", ascending=False).head(10)
        fig2 = px.bar(fdf, x="Framework", y="Count", color="Count",
                      color_continuous_scale=["#1e1e3a", "#4f46e5", "#a5b4fc"])
        fig2.update_layout(paper_bgcolor=BG, plot_bgcolor=BG, font_color="#e2e8f0",
                           coloraxis_showscale=False, margin=dict(t=10, b=10),
                           xaxis=dict(gridcolor="#1e1e3a"), yaxis=dict(gridcolor="#1e1e3a"))
        st.plotly_chart(fig2, use_container_width=True)

    # ── Row 2: Agent types + Capabilities ─────────────────────────────────────
    ch3, ch4 = st.columns(2)

    with ch3:
        st.markdown("#### 🤖 Agent Types")
        tdf = pd.DataFrame([(k, v) for k, v in types_stat.items() if k], columns=["Type", "Count"])
        tdf = tdf.sort_values("Count", ascending=True)
        fig3 = px.bar(tdf, x="Count", y="Type", orientation="h", color="Count",
                      color_continuous_scale=["#1e1e3a", "#7c3aed", "#a5b4fc"])
        fig3.update_layout(paper_bgcolor=BG, plot_bgcolor=BG, font_color="#e2e8f0",
                           coloraxis_showscale=False, margin=dict(t=10, b=10),
                           xaxis=dict(gridcolor="#1e1e3a"), yaxis=dict(gridcolor="#1e1e3a"))
        st.plotly_chart(fig3, use_container_width=True)

    with ch4:
        st.markdown("#### 🛠️ Capabilities Detected")
        if not filtered.empty:
            all_caps = Counter(
                c for caps in filtered["capabilities"]
                if isinstance(caps, list)
                for c in caps
            )
            if all_caps:
                cdf = pd.DataFrame(all_caps.most_common(10), columns=["Capability", "Count"])
                fig4 = px.bar(cdf, x="Count", y="Capability", orientation="h", color="Count",
                              color_continuous_scale=["#1e1e3a", "#0891b2", "#67e8f9"])
                fig4.update_layout(paper_bgcolor=BG, plot_bgcolor=BG, font_color="#e2e8f0",
                                   coloraxis_showscale=False, margin=dict(t=10, b=10),
                                   xaxis=dict(gridcolor="#1e1e3a"), yaxis=dict(gridcolor="#1e1e3a"))
                st.plotly_chart(fig4, use_container_width=True)
            else:
                st.info("No capabilities detected in current filter.")

    # ── Row 3: Stars histogram + Top 15 starred ───────────────────────────────
    ch5, ch6 = st.columns(2)

    with ch5:
        st.markdown("#### ⭐ Stars Distribution")
        if not filtered.empty:
            star_df = filtered[filtered["stars"] > 0][["stars"]].copy()
            if not star_df.empty:
                fig5 = px.histogram(star_df, x="stars", nbins=40, color_discrete_sequence=["#4f46e5"])
                fig5.update_layout(paper_bgcolor=BG, plot_bgcolor=BG, font_color="#e2e8f0",
                                   margin=dict(t=10, b=10),
                                   xaxis=dict(gridcolor="#1e1e3a", title="Stars"),
                                   yaxis=dict(gridcolor="#1e1e3a", title="Agents"))
                st.plotly_chart(fig5, use_container_width=True)

    with ch6:
        st.markdown("#### 🏆 Top 15 by Stars")
        if not filtered.empty:
            top = filtered.nlargest(15, "stars")[["name", "stars", "framework", "model_detected"]].copy()
            top["name"] = top["name"].str.split("/").str[-1]
            fig6 = px.bar(top.sort_values("stars"), x="stars", y="name", orientation="h",
                          color="framework", color_discrete_sequence=COLORS)
            fig6.update_layout(paper_bgcolor=BG, plot_bgcolor=BG, font_color="#e2e8f0",
                               margin=dict(t=10, b=10), showlegend=True,
                               xaxis=dict(gridcolor="#1e1e3a"), yaxis=dict(gridcolor="#1e1e3a"))
            st.plotly_chart(fig6, use_container_width=True)

    # ── Discovery timeline ─────────────────────────────────────────────────────
    st.markdown("#### 📅 Discovery Timeline")
    if not filtered.empty and "first_seen" in filtered.columns:
        tl = filtered.copy()
        tl["date"] = pd.to_datetime(tl["first_seen"], errors="coerce").dt.date
        tl = tl.dropna(subset=["date"])
        if not tl.empty:
            daily = tl.groupby("date").size().reset_index(name="new_agents")
            daily["cumulative"] = daily["new_agents"].cumsum()
            fig7 = go.Figure()
            fig7.add_trace(go.Bar(
                x=daily["date"], y=daily["new_agents"],
                name="New per day", marker_color="#4f46e5", opacity=0.7
            ))
            fig7.add_trace(go.Scatter(
                x=daily["date"], y=daily["cumulative"],
                name="Cumulative", line=dict(color="#34d399", width=2), yaxis="y2"
            ))
            fig7.update_layout(
                paper_bgcolor=BG, plot_bgcolor=BG, font_color="#e2e8f0",
                margin=dict(t=10, b=10),
                xaxis=dict(gridcolor="#1e1e3a"),
                yaxis=dict(gridcolor="#1e1e3a", title="New Agents"),
                yaxis2=dict(overlaying="y", side="right", title="Cumulative", showgrid=False),
                legend=dict(orientation="h", y=1.05),
            )
            st.plotly_chart(fig7, use_container_width=True)

    # ── Agent table ────────────────────────────────────────────────────────────
    st.markdown(f"#### 🗄️ Agent Database — {len(filtered):,} results")

    if not filtered.empty:
        display = filtered[[
            "name", "source_platform", "model_detected", "framework",
            "agent_type", "stars", "status", "source_url", "raw_description"
        ]].copy().head(1000)

        display.columns = ["Name", "Platform", "Model", "Framework",
                           "Type", "Stars", "Status", "URL", "Description"]
        display["Description"] = display["Description"].astype(str).str[:80] + "…"

        st.dataframe(
            display,
            use_container_width=True,
            height=440,
            column_config={
                "URL":         st.column_config.LinkColumn("URL", display_text="🔗 Open"),
                "Stars":       st.column_config.NumberColumn("⭐ Stars", format="%d"),
                "Description": st.column_config.TextColumn("Description", width="large"),
            },
            hide_index=True,
        )
    else:
        st.info("No agents match the current filters.")


# ══════════════════════════════════════════════════════════════════════════════
# AGENT PIT 🥊
# ══════════════════════════════════════════════════════════════════════════════
elif page == "Agent Pit 🥊":
    st.markdown("""
<h1 style='font-family:JetBrains Mono,monospace;font-size:2rem;font-weight:700;
           background:linear-gradient(90deg,#4f46e5,#db2777);-webkit-background-clip:text;
           -webkit-text-fill-color:transparent;margin:0 0 4px'>⚔️ AGENT PIT</h1>
<p style='color:#64748b;font-size:0.82rem;margin:0 0 1.5rem'>
    Head-to-head arena &nbsp;·&nbsp; Composite scoring &nbsp;·&nbsp; Purely data-driven
</p>
""", unsafe_allow_html=True)

    if df.empty:
        st.warning("No agent data loaded.")
    else:
        df["pit_score"] = df.apply(calculate_pit_score, axis=1)
        df_pit = df.sort_values("pit_score", ascending=False).head(20)

        # Build display_name: "repo-name (model • 12,400★ • framework)"
        def _make_display(row):
            short = str(row.get("name", "")).split("/")[-1]
            model = row.get("model_detected") or "?"
            stars = int(row.get("stars", 0) or 0)
            fw    = row.get("framework") or "?"
            return f"{short} ({model} • {stars:,}★ • {fw})"

        df["display_name"]  = df.apply(_make_display, axis=1)
        name_to_display     = dict(zip(df["name"], df["display_name"]))
        display_to_name     = dict(zip(df["display_name"], df["name"]))
        all_displays        = df["display_name"].tolist()

        # ── Leaderboard ───────────────────────────────────────────────────────
        st.markdown("#### 🏆 PIT LEADERBOARD — Top 20")
        lb = df_pit[["name", "pit_score", "stars", "model_detected", "framework", "status"]].copy()
        lb["Agent"] = lb["name"].map(name_to_display)
        lb = lb[["Agent", "pit_score", "stars", "model_detected", "framework", "status"]]
        lb.columns = ["Agent", "Pit Score", "⭐ Stars", "Model", "Framework", "Status"]
        st.dataframe(
            lb,
            use_container_width=True,
            height=380,
            column_config={"Pit Score": st.column_config.NumberColumn("🔥 Pit Score", format="%.1f")},
            hide_index=True,
        )

        st.markdown("<br>", unsafe_allow_html=True)

        # ── Head-to-Head Arena ────────────────────────────────────────────────
        st.markdown("#### ⚔️ HEAD-TO-HEAD ARENA")

        # Quick-pick buttons
        btn1, btn2, btn3, btn4, btn5 = st.columns(5)
        with btn1:
            if st.button("🎲 Random", use_container_width=True):
                a, b = df.sample(2)["name"].tolist()
                st.session_state["sel_a"] = name_to_display[a]
                st.session_state["sel_b"] = name_to_display[b]
                st.rerun()
        with btn2:
            if st.button("🏆 Top vs #10", use_container_width=True):
                top10 = df.nlargest(10, "pit_score")["name"].tolist()
                if len(top10) >= 10:
                    st.session_state["sel_a"] = name_to_display[top10[0]]
                    st.session_state["sel_b"] = name_to_display[top10[9]]
                    st.rerun()
        with btn3:
            if st.button("⚖️ Closest Score", use_container_width=True):
                top1_score = df_pit["pit_score"].iloc[0]
                top1_name  = df_pit["name"].iloc[0]
                rest = df[df["name"] != top1_name].copy()
                closest = rest.iloc[(rest["pit_score"] - top1_score).abs().argsort().iloc[0]]["name"]
                st.session_state["sel_a"] = name_to_display[top1_name]
                st.session_state["sel_b"] = name_to_display[closest]
                st.rerun()
        with btn4:
            if st.button("🔀 Framework Clash", use_container_width=True):
                top1_name = df_pit["name"].iloc[0]
                top1_fw   = df[df["name"] == top1_name]["framework"].iloc[0]
                diff_fw   = df[df["framework"] != top1_fw]
                if not diff_fw.empty:
                    b = diff_fw.sample(1)["name"].iloc[0]
                    st.session_state["sel_a"] = name_to_display[top1_name]
                    st.session_state["sel_b"] = name_to_display[b]
                    st.rerun()
        with btn5:
            if st.button("🔥 Surprise Me", use_container_width=True, type="primary"):
                a, b = df.sample(2)["name"].tolist()
                st.session_state["sel_a"] = name_to_display[a]
                st.session_state["sel_b"] = name_to_display[b]
                st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)

        # Searchable fighter selectors
        col_a, col_b = st.columns(2)
        with col_a:
            search_a  = st.text_input("🔍 Search Agent A", key="search_a", placeholder="type name, model, framework…")
            opts_a    = [d for d in all_displays if search_a.lower() in d.lower()] if search_a else all_displays
            slice_a   = opts_a[:200]
            saved_a   = st.session_state.get("sel_a")
            default_a = slice_a.index(saved_a) if saved_a in slice_a else 0
            agent_a_display = st.selectbox("🟣 Agent A", slice_a, index=default_a, key="sel_a")

        with col_b:
            search_b  = st.text_input("🔍 Search Agent B", key="search_b", placeholder="type name, model, framework…")
            opts_b    = [d for d in all_displays if search_b.lower() in d.lower()] if search_b else all_displays
            slice_b   = opts_b[:200]
            saved_b   = st.session_state.get("sel_b")
            default_b = slice_b.index(saved_b) if saved_b in slice_b else min(1, len(slice_b) - 1)
            agent_b_display = st.selectbox("🩷 Agent B", slice_b, index=default_b, key="sel_b")

        agent_a = display_to_name.get(agent_a_display)
        agent_b = display_to_name.get(agent_b_display)

        if agent_a and agent_b and agent_a != agent_b:
            row_a = df[df["name"] == agent_a].iloc[0]
            row_b = df[df["name"] == agent_b].iloc[0]

            def _caps_len(row):
                caps = row.get("capabilities", [])
                return len(caps) if isinstance(caps, list) else 0

            def _reliability(row):
                return {"active": 100, "experimental": 75, "inactive": 30}.get(str(row.get("status", "")), 50)

            def _safety(row):
                return {"low": 100, "medium": 70, "high": 30}.get(str(row.get("risk_level", "")), 60)

            raw = {
                "Popularity":  (row_a.get("stars", 0) or 0,      row_b.get("stars", 0) or 0),
                "Speed":       (1000 / max(row_a.get("response_time_ms", 1000) or 1000, 10),
                                1000 / max(row_b.get("response_time_ms", 1000) or 1000, 10)),
                "Versatility": (_caps_len(row_a), _caps_len(row_b)),
                "Reliability": (_reliability(row_a), _reliability(row_b)),
                "Safety":      (_safety(row_a), _safety(row_b)),
            }

            dims = list(raw.keys())
            norm_a, norm_b = [], []
            for d in dims:
                va, vb = raw[d]
                mx = max(va, vb, 1)
                norm_a.append(round(va / mx * 100, 1))
                norm_b.append(round(vb / mx * 100, 1))

            label_a = agent_a_display.split(" (")[0]
            label_b = agent_b_display.split(" (")[0]

            fig_radar = go.Figure()
            for vals, name, color, fill in [
                (norm_a, label_a, "#4f46e5", "rgba(79,70,229,0.15)"),
                (norm_b, label_b, "#db2777", "rgba(219,39,119,0.15)"),
            ]:
                fig_radar.add_trace(go.Scatterpolar(
                    r=vals + [vals[0]],
                    theta=dims + [dims[0]],
                    fill="toself",
                    name=name,
                    line=dict(color=color, width=2),
                    fillcolor=fill,
                    opacity=0.9,
                ))

            fig_radar.update_layout(
                polar=dict(
                    bgcolor="#13131f",
                    radialaxis=dict(visible=True, range=[0, 100], gridcolor="#2d2d4e",
                                    tickfont=dict(color="#64748b", size=9)),
                    angularaxis=dict(gridcolor="#2d2d4e", tickfont=dict(color="#e2e8f0", size=11)),
                ),
                paper_bgcolor=BG,
                font_color="#e2e8f0",
                legend=dict(orientation="h", y=-0.12, font=dict(size=12)),
                margin=dict(t=30, b=40, l=60, r=60),
                height=420,
            )
            st.plotly_chart(fig_radar, use_container_width=True)

            # ── Winner banner ─────────────────────────────────────────────────
            score_a = sum(norm_a)
            score_b = sum(norm_b)
            if score_a > score_b:
                winner, w_color = label_a, "#4f46e5"
            elif score_b > score_a:
                winner, w_color = label_b, "#db2777"
            else:
                winner, w_color = "TIE", "#f59e0b"

            st.markdown(f"""
<div style='text-align:center;padding:1rem;background:linear-gradient(135deg,#13131f,#1a1a2e);
            border:1px solid {w_color};border-radius:12px;margin-top:0.5rem'>
    <span style='font-family:JetBrains Mono,monospace;font-size:1.3rem;font-weight:700;color:{w_color}'>
        🏆 WINNER: {winner}
    </span>
    <span style='color:#64748b;font-size:0.8rem;display:block;margin-top:4px'>
        {label_a}: {score_a:.0f} pts &nbsp;vs&nbsp; {label_b}: {score_b:.0f} pts
    </span>
</div>
""", unsafe_allow_html=True)

        elif agent_a == agent_b:
            st.info("Select two different agents to compare.")


# ══════════════════════════════════════════════════════════════════════════════
# LIVE TICKER — shown on both pages
# ══════════════════════════════════════════════════════════════════════════════
if not df.empty and "first_seen" in df.columns:
    recent = (
        df.sort_values("first_seen", ascending=False)
        .head(12)["name"]
        .str.split("/").str[-1]
        .tolist()
    )
    ticker_text = " 🔥 ".join(recent)
    st.markdown(f"""
<div class="marquee" style="margin-top:2rem">
    <span>🛰️ LIVE DISCOVERIES → {ticker_text} ← LIVE DISCOVERIES 🛰️</span>
</div>
""", unsafe_allow_html=True)
