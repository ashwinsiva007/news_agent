"""
AI Morning Brief - Streamlit Web Dashboard
A daily India-focused AI and technology intelligence briefing dashboard.
"""
import os
import json
import streamlit as st
from datetime import datetime
from pathlib import Path

from config import (
    PROJECT_NAME, SCHEDULE_TIME, MAX_BRIEFING_WORDS, CATEGORIES, AI_PROVIDER
)
from engine.normalizer import get_current_ist_time, get_current_ist_date
from engine.storage import (
    load_latest_report, load_historical_report, list_historical_reports,
    load_preferences, record_user_feedback, save_preferences
)
from research import run_research_pipeline

# Configure Streamlit page
st.set_page_config(
    page_title="AI Morning Brief | India Tech Intelligence",
    page_icon="🌅",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling (Vanilla CSS with rich aesthetics)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
    
    .main-header {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        padding: 24px 30px;
        margin-bottom: 24px;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.2);
    }
    
    .brand-title {
        font-size: 2.2rem;
        font-weight: 800;
        background: linear-gradient(90deg, #38bdf8, #818cf8, #c084fc);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0;
        line-height: 1.2;
    }
    
    .brand-subtitle {
        color: #94a3b8;
        font-size: 1.05rem;
        font-weight: 500;
        margin-top: 6px;
        margin-bottom: 0;
    }
    
    .metric-chip-container {
        display: flex;
        flex-wrap: wrap;
        gap: 12px;
        margin-top: 18px;
    }
    
    .metric-chip {
        background: rgba(255, 255, 255, 0.06);
        border: 1px solid rgba(255, 255, 255, 0.12);
        padding: 6px 14px;
        border-radius: 30px;
        font-size: 0.85rem;
        font-weight: 600;
        color: #e2e8f0;
        display: inline-flex;
        align-items: center;
        gap: 6px;
    }
    
    .metric-chip.success {
        border-color: rgba(52, 211, 153, 0.4);
        background: rgba(16, 185, 129, 0.1);
        color: #34d399;
    }

    .story-card {
        background: rgba(30, 41, 59, 0.7);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 14px;
        padding: 20px 24px;
        margin-bottom: 18px;
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    
    .story-card:hover {
        border-color: rgba(99, 102, 241, 0.4);
        transform: translateY(-2px);
    }
    
    .story-top-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 10px;
    }
    
    .rank-badge {
        background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
        color: #ffffff;
        font-size: 0.8rem;
        font-weight: 700;
        padding: 4px 10px;
        border-radius: 8px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .status-badge {
        font-size: 0.75rem;
        font-weight: 600;
        padding: 3px 10px;
        border-radius: 20px;
        background: rgba(56, 189, 248, 0.12);
        color: #38bdf8;
        border: 1px solid rgba(56, 189, 248, 0.25);
    }
    
    .story-headline {
        font-size: 1.22rem;
        font-weight: 700;
        color: #f8fafc;
        margin: 6px 0 10px 0;
        line-height: 1.35;
    }
    
    .story-explanation {
        font-size: 0.98rem;
        color: #cbd5e1;
        line-height: 1.5;
        margin-bottom: 14px;
    }
    
    .meta-row {
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        gap: 12px;
        font-size: 0.8rem;
        color: #94a3b8;
        margin-bottom: 12px;
    }
    
    .meta-pill {
        background: rgba(255, 255, 255, 0.05);
        padding: 2px 8px;
        border-radius: 6px;
    }
    
    .source-btn {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        font-size: 0.85rem;
        font-weight: 600;
        color: #38bdf8;
        text-decoration: none;
        padding: 6px 12px;
        border-radius: 6px;
        background: rgba(56, 189, 248, 0.08);
        border: 1px solid rgba(56, 189, 248, 0.2);
    }
    
    .source-btn:hover {
        background: rgba(56, 189, 248, 0.18);
        color: #7dd3fc;
    }
</style>
""", unsafe_allow_html=True)


# --- Sidebar Navigation & Actions ---
st.sidebar.markdown("### 🧭 Controls & Archive")

# Manual Research Trigger
if st.sidebar.button("⚡ Research Now (Live Run)", type="primary", use_container_width=True):
    with st.spinner("Executing 8-stage research pipeline (RSS Discovery, Deduplication, Verification, Ranking, <=99 Words Cap)..."):
        report_result = run_research_pipeline(lookback_hours=24, force_fresh=True)
        if report_result.get("status") == "success":
            st.sidebar.success(f"Briefing updated! {report_result['story_count']} stories ({report_result['briefing_word_count']} words).")
            st.rerun()
        else:
            st.sidebar.error(f"Research run notice: {report_result.get('message')}")

st.sidebar.markdown("---")

# Historical Archive Selection
history_dates = list_historical_reports()
selected_date = None
if history_dates:
    st.sidebar.markdown("#### 📅 Report Archive")
    date_options = ["Latest Active Briefing"] + history_dates
    selected_option = st.sidebar.selectbox("Select Report Date", date_options, index=0)
    if selected_option != "Latest Active Briefing":
        selected_date = selected_option

# Topic Filter
st.sidebar.markdown("#### 🔍 Filter by Topic")
selected_category = st.sidebar.selectbox("Category", CATEGORIES, index=0)

# Sidebar System Specs
st.sidebar.markdown("---")
st.sidebar.markdown("#### ℹ️ System Details")
st.sidebar.caption(f"**Schedule:** Daily at {SCHEDULE_TIME}")
st.sidebar.caption(f"**Timezone:** Asia/Kolkata (IST)")
st.sidebar.caption(f"**Briefing Word Cap:** {MAX_BRIEFING_WORDS} words combined")
st.sidebar.caption(f"**AI Engine Mode:** {AI_PROVIDER.title() if AI_PROVIDER != 'none' else 'Deterministic Extractive'}")


# --- Load Report Data ---
if selected_date:
    report = load_historical_report(selected_date)
else:
    report = load_latest_report()

# If no report exists yet, provide an initial generator trigger
if not report or not report.get("stories"):
    st.info("👋 Welcome to AI Morning Brief! No briefing report has been generated yet.")
    if st.button("🚀 Run First Morning Research", type="primary"):
        with st.spinner("Initializing first research run..."):
            report = run_research_pipeline(lookback_hours=48, force_fresh=True)
            st.rerun()
    st.stop()


# --- Dashboard Header ---
ist_now = get_current_ist_time()
report_date = report.get("report_date", "Today")
generated_at = report.get("generated_at_ist", ist_now)
story_count = report.get("story_count", len(report.get("stories", [])))
word_count = report.get("briefing_word_count", 0)
word_status = report.get("word_limit_status", "Passed")
lookback = report.get("lookback_period_hours", 24)

st.markdown(f"""
<div class="main-header">
    <h1 class="brand-title">🌅 AI Morning Brief</h1>
    <p class="brand-subtitle">Your daily India-focused AI and technology intelligence report.</p>
    <div class="metric-chip-container">
        <div class="metric-chip">📅 Date: {report_date} (IST)</div>
        <div class="metric-chip">⏰ Generated: {generated_at}</div>
        <div class="metric-chip success">📊 Verified Stories: {story_count}</div>
        <div class="metric-chip success">📝 Word Count: {word_count} / {MAX_BRIEFING_WORDS} ({word_status})</div>
        <div class="metric-chip">⏱️ Lookback: {lookback}h</div>
    </div>
</div>
""", unsafe_allow_html=True)


# --- Tabs: Main Briefing & Full Inspector ---
tab_briefing, tab_inspector, tab_preferences = st.tabs([
    "📰 Daily Intelligence Brief",
    "🔬 Full Research Inspector",
    "⚙️ Preferences & Topic Weights"
])

# ==========================================
# TAB 1: Main Briefing Cards
# ==========================================
with tab_briefing:
    stories = report.get("stories", [])
    
    # Filter by category if selected
    if selected_category != "All":
        filtered_stories = [
            s for s in stories
            if selected_category.lower() in s.get("category", "").lower() or
               any(selected_category.lower() in kw.lower() for kw in s.get("matched_india_keywords", []))
        ]
    else:
        filtered_stories = stories

    if not filtered_stories:
        st.warning(f"No stories in category '{selected_category}' in this edition.")
    else:
        for idx, story in enumerate(filtered_stories):
            rank = story.get("rank", idx + 1)
            headline = story.get("headline", "")
            explanation = story.get("explanation", "")
            publisher = story.get("publisher", story.get("source", "Unknown Source"))
            pub_date = story.get("published_ist", "")
            status = story.get("verification_status", "Verified")
            url = story.get("url", "#")
            matched_kws = story.get("matched_india_keywords", [])
            corrob_count = story.get("corroboration_count", 0)

            # Card Container
            card_container = st.container()
            with card_container:
                col_main, col_feed = st.columns([4, 1.2])
                
                with col_main:
                    st.markdown(f"""
                    <div class="story-card">
                        <div class="story-top-row">
                            <span class="rank-badge">Story #{rank}</span>
                            <span class="status-badge">{status}</span>
                        </div>
                        <div class="story-headline">{headline}</div>
                        <div class="story-explanation">{explanation}</div>
                        <div class="meta-row">
                            <span class="meta-pill">🏢 {publisher}</span>
                            <span class="meta-pill">📅 {pub_date}</span>
                            {"<span class='meta-pill'>🇮🇳 " + ", ".join(matched_kws) + "</span>" if matched_kws else ""}
                            {"<span class='meta-pill'>🔗 " + str(corrob_count) + " corroborations</span>" if corrob_count > 0 else ""}
                        </div>
                        <a href="{url}" target="_blank" class="source-btn">
                            Direct Source Link ↗
                        </a>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col_feed:
                    st.caption("Feedback on this Story:")
                    fb_col1, fb_col2 = st.columns(2)
                    with fb_col1:
                        if st.button("👍 Useful", key=f"fb_use_{rank}_{idx}", use_container_width=True):
                            record_user_feedback(headline, story.get("category", ""), "useful", url)
                            st.toast("Marked as Useful! Topic weight boosted.", icon="👍")
                    with fb_col2:
                        if st.button("👎 Irrelevant", key=f"fb_not_{rank}_{idx}", use_container_width=True):
                            record_user_feedback(headline, story.get("category", ""), "not_relevant", url)
                            st.toast("Marked as Irrelevant! Topic weight reduced.", icon="👎")
                            
                    fb_col3, fb_col4 = st.columns(2)
                    with fb_col3:
                        if st.button("👀 Known", key=f"fb_kno_{rank}_{idx}", use_container_width=True):
                            record_user_feedback(headline, story.get("category", ""), "already_known", url)
                            st.toast("Saved preference.", icon="👀")
                    with fb_col4:
                        if st.button("🚩 Misleading", key=f"fb_mis_{rank}_{idx}", use_container_width=True):
                            record_user_feedback(headline, story.get("category", ""), "misleading", url)
                            st.toast("Flagged misleading claim.", icon="🚩")
                
                st.markdown("<div style='margin-bottom: 12px;'></div>", unsafe_allow_html=True)

    # Download Report JSON button
    st.markdown("---")
    st.download_button(
        label="📥 Download Briefing JSON",
        data=json.dumps(report, indent=2, ensure_ascii=False),
        file_name=f"ai_morning_brief_{report_date}.json",
        mime="application/json"
    )

# ==========================================
# TAB 2: Full Research Inspector
# ==========================================
with tab_inspector:
    st.markdown("### 🔬 Transparent Research & Verification Pipeline Inspector")
    metadata = report.get("research_metadata", {})
    
    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    with col_m1:
        st.metric("Raw Articles Collected", metadata.get("total_raw_fetched", 0))
    with col_m2:
        st.metric("Within Lookback Window", metadata.get("total_after_lookback", 0))
    with col_m3:
        st.metric("Canonical Events (Deduplicated)", metadata.get("canonical_events_count", 0))
    with col_m4:
        st.metric("Eligible Verified Stories", metadata.get("eligible_events_count", 0))

    st.markdown("#### 1. Candidate Stories Ranking Matrix")
    st.caption("Transparent multi-factor score breakdown for the top selected stories:")
    
    score_rows = []
    for s in report.get("stories", []):
        sc = s.get("scores", {})
        score_rows.append({
            "Rank": f"#{s.get('rank')}",
            "Headline": s.get("headline")[:40] + "...",
            "Composite Score": sc.get("composite"),
            "Credibility": sc.get("credibility"),
            "Evidence": sc.get("evidence_strength"),
            "India Relevance": sc.get("india_relevance"),
            "Recency": sc.get("recency"),
            "Trend Momentum": sc.get("trend_momentum"),
            "User Preference": sc.get("user_preference"),
            "Publisher": s.get("publisher", "")
        })
    st.dataframe(score_rows, use_container_width=True)

    # Duplicate Clustering Details
    st.markdown("#### 2. Deduplication & Corroboration Clusters")
    dup_groups = metadata.get("duplicate_groups", [])
    if dup_groups:
        st.write(f"Detected {len(dup_groups)} multi-source duplicate clusters:")
        for dg in dup_groups:
            st.markdown(f"- **{dg.get('canonical_headline')}**: merged {dg.get('duplicates_merged_count')} additional source(s) ({', '.join(dg.get('corroborating_publishers', []))})")
    else:
        st.write("All collected stories in this window were distinct single-source events.")

    # Rejected Stories Log
    st.markdown("#### 3. Rejected Stories & Quality Filter Log")
    rejected = metadata.get("rejected_stories", [])
    if rejected:
        st.write(f"{len(rejected)} stories filtered out by credibility or relevance thresholds:")
        for r in rejected:
            st.markdown(f"- **{r.get('headline')}** ({r.get('source')}): *{r.get('reason')}*")
    else:
        st.write("No stories were rejected in this cycle.")

    # Feed Errors Log
    if metadata.get("feed_errors"):
        st.markdown("#### ⚠️ Feed Network Notices")
        for err in metadata["feed_errors"]:
            st.warning(err)

# ==========================================
# TAB 3: Preferences & Learning Memory
# ==========================================
with tab_preferences:
    st.markdown("### 🧠 Learning & Topic Memory")
    st.write("The agent dynamically tunes ranking weights based on your feedback while strictly maintaining credibility standards.")
    
    prefs = load_preferences()
    weights = prefs.get("topic_weights", {})
    
    st.markdown("#### Active Topic Ranking Weights")
    cols = st.columns(2)
    updated_weights = {}
    for idx, (topic, w) in enumerate(weights.items()):
        col = cols[idx % 2]
        with col:
            new_val = st.slider(f"{topic}", min_value=0.4, max_value=2.0, value=float(w), step=0.05, key=f"slider_{topic}")
            updated_weights[topic] = round(new_val, 3)
            
    if st.button("💾 Save Custom Topic Weights"):
        prefs["topic_weights"] = updated_weights
        save_preferences(prefs)
        st.success("Topic weights saved successfully!")
        
    st.markdown("#### Recent Feedback History")
    feedback_history = prefs.get("feedback_history", [])
    if feedback_history:
        st.dataframe(feedback_history[-10:], use_container_width=True)
    else:
        st.write("No user feedback submitted yet.")
