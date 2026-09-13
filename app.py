"""
AI Morning Brief - Streamlit Web Dashboard
A daily India-focused AI and technology intelligence briefing dashboard.
Optimized for Desktop and Mobile screens.
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
    initial_sidebar_state="collapsed"
)

# Custom Styling (Vanilla CSS with rich aesthetics & mobile responsiveness)
st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Plus Jakarta Sans', sans-serif;
}

/* Header Container */
.main-header {
    background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 50%, #0f172a 100%);
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 16px;
    padding: 20px 24px;
    margin-bottom: 20px;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.35);
}

.brand-title {
    font-size: 1.9rem;
    font-weight: 800;
    background: linear-gradient(90deg, #38bdf8, #818cf8, #c084fc);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin: 0;
    line-height: 1.25;
}

.brand-subtitle {
    color: #94a3b8;
    font-size: 0.95rem;
    font-weight: 500;
    margin-top: 6px;
    margin-bottom: 0;
}

.metric-chip-container {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-top: 14px;
}

.metric-chip {
    background: rgba(255, 255, 255, 0.07);
    border: 1px solid rgba(255, 255, 255, 0.12);
    padding: 5px 12px;
    border-radius: 20px;
    font-size: 0.8rem;
    font-weight: 600;
    color: #e2e8f0;
    display: inline-flex;
    align-items: center;
    gap: 6px;
}

.metric-chip.success {
    border-color: rgba(52, 211, 153, 0.4);
    background: rgba(16, 185, 129, 0.12);
    color: #34d399;
}

/* Card Styling */
.card-header-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 8px;
}

.rank-badge {
    background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
    color: #ffffff !important;
    font-size: 0.78rem;
    font-weight: 800;
    padding: 3px 10px;
    border-radius: 8px;
    letter-spacing: 0.5px;
    display: inline-block;
}

.status-badge {
    font-size: 0.75rem;
    font-weight: 600;
    padding: 3px 10px;
    border-radius: 20px;
    background: rgba(56, 189, 248, 0.12);
    color: #38bdf8;
    border: 1px solid rgba(56, 189, 248, 0.3);
    display: inline-block;
}

.story-title {
    font-size: 1.15rem;
    font-weight: 700;
    color: #f8fafc;
    margin: 6px 0 8px 0;
    line-height: 1.35;
}

.story-body {
    font-size: 0.95rem;
    color: #cbd5e1;
    line-height: 1.5;
    margin-bottom: 12px;
}

.meta-tags-container {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    align-items: center;
    margin-bottom: 6px;
}

.meta-tag {
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.08);
    padding: 3px 8px;
    border-radius: 6px;
    font-size: 0.78rem;
    color: #94a3b8;
}

/* Streamlit button customizations for mobile */
div.stButton > button {
    border-radius: 8px;
    font-weight: 600;
    transition: all 0.2s ease;
}

/* Mobile responsive adjustments */
@media (max-width: 768px) {
    .brand-title {
        font-size: 1.5rem;
    }
    .main-header {
        padding: 16px;
    }
    .metric-chip {
        font-size: 0.75rem;
        padding: 4px 10px;
    }
    .story-title {
        font-size: 1.05rem;
    }
}
</style>""", unsafe_allow_html=True)


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

header_html = (
    f'<div class="main-header">'
    f'<h1 class="brand-title">🌅 AI Morning Brief</h1>'
    f'<p class="brand-subtitle">Your daily India-focused AI and technology intelligence report.</p>'
    f'<div class="metric-chip-container">'
    f'<div class="metric-chip">📅 Date: {report_date} (IST)</div>'
    f'<div class="metric-chip">⏰ Generated: {generated_at}</div>'
    f'<div class="metric-chip success">📊 Verified Stories: {story_count}</div>'
    f'<div class="metric-chip success">📝 Word Count: {word_count} / {MAX_BRIEFING_WORDS} ({word_status})</div>'
    f'<div class="metric-chip">⏱️ Lookback: {lookback}h</div>'
    f'</div>'
    f'</div>'
)
st.markdown(header_html, unsafe_allow_html=True)


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
        st.warning(f"No stories found in category '{selected_category}' for this edition.")
    else:
        for idx, story in enumerate(filtered_stories):
            rank = story.get("rank", idx + 1)
            headline = story.get("headline", "")
            explanation = story.get("explanation", "")
            publisher = story.get("publisher", story.get("source", "Authoritative Source"))
            pub_date = story.get("published_ist", "")
            status = story.get("verification_status", "Verified")
            url = story.get("url", "#")
            matched_kws = story.get("matched_india_keywords", [])
            corrob_count = story.get("corroboration_count", 0)

            # Render story using Streamlit Container with native cards
            with st.container(border=True):
                # Header row with badges
                badge_html = (
                    f'<div class="card-header-row">'
                    f'<span class="rank-badge">STORY #{rank}</span>'
                    f'<span class="status-badge">{status}</span>'
                    f'</div>'
                    f'<div class="story-title">{headline}</div>'
                    f'<div class="story-body">{explanation}</div>'
                )
                st.markdown(badge_html, unsafe_allow_html=True)

                # Meta tags
                meta_parts = [
                    f'<span class="meta-tag">🏢 {publisher}</span>',
                    f'<span class="meta-tag">📅 {pub_date}</span>'
                ]
                if matched_kws:
                    meta_parts.append(f'<span class="meta-tag">🇮🇳 {", ".join(matched_kws[:3])}</span>')
                if corrob_count > 0:
                    meta_parts.append(f'<span class="meta-tag">🔗 {corrob_count} corroboration(s)</span>')

                tags_html = f'<div class="meta-tags-container">{"".join(meta_parts)}</div>'
                st.markdown(tags_html, unsafe_allow_html=True)

                st.markdown("<div style='margin-bottom: 8px;'></div>", unsafe_allow_html=True)

                # Action row: Direct Link + Feedback
                col_btn, col_actions = st.columns([1.5, 3.5])
                
                with col_btn:
                    st.link_button("🔗 Read Source Article ↗", url, use_container_width=True)
                
                with col_actions:
                    # Feedback bar responsive across mobile
                    with st.popover("💬 Give Feedback on Story", use_container_width=True):
                        st.caption(f"Adjust future ranking for: **{headline[:45]}...**")
                        f_col1, f_col2 = st.columns(2)
                        with f_col1:
                            if st.button("👍 Useful Story", key=f"fb_use_{rank}_{idx}", use_container_width=True):
                                record_user_feedback(headline, story.get("category", ""), "useful", url)
                                st.success("Marked as Useful! Boosted topic priority.")
                            if st.button("👀 Already Known", key=f"fb_kno_{rank}_{idx}", use_container_width=True):
                                record_user_feedback(headline, story.get("category", ""), "already_known", url)
                                st.info("Saved preference.")
                        with f_col2:
                            if st.button("👎 Not Relevant", key=f"fb_not_{rank}_{idx}", use_container_width=True):
                                record_user_feedback(headline, story.get("category", ""), "not_relevant", url)
                                st.warning("Marked as Irrelevant. Reduced topic priority.")
                            if st.button("🚩 Misleading", key=f"fb_mis_{rank}_{idx}", use_container_width=True):
                                record_user_feedback(headline, story.get("category", ""), "misleading", url)
                                st.error("Flagged as Misleading.")

    # Download Report JSON button
    st.markdown("---")
    st.download_button(
        label="📥 Download Briefing JSON",
        data=json.dumps(report, indent=2, ensure_ascii=False),
        file_name=f"ai_morning_brief_{report_date}.json",
        mime="application/json",
        use_container_width=True
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
            
    if st.button("💾 Save Custom Topic Weights", use_container_width=True):
        prefs["topic_weights"] = updated_weights
        save_preferences(prefs)
        st.success("Topic weights saved successfully!")
        
    st.markdown("#### Recent Feedback History")
    feedback_history = prefs.get("feedback_history", [])
    if feedback_history:
        st.dataframe(feedback_history[-10:], use_container_width=True)
    else:
        st.write("No user feedback submitted yet.")
