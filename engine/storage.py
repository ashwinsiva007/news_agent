"""
Storage Engine: Atomic JSON persistence for daily reports, history, user preferences, and seen stories.
"""
import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from config import (
    LATEST_REPORT_FILE, HISTORY_DIR, PREFERENCES_FILE, SEEN_STORIES_FILE
)

logger = logging.getLogger(__name__)


def atomic_write_json(file_path: Path, data: Any) -> bool:
    """
    Safely writes data to a JSON file using an atomic temp file replacement.
    """
    try:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        temp_path = file_path.with_suffix(".tmp")
        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        temp_path.replace(file_path)
        return True
    except Exception as e:
        logger.error(f"Failed to atomically write JSON to {file_path}: {e}")
        return False


def load_json(file_path: Path, default_factory=None) -> Any:
    """
    Safely loads a JSON file, returning default_factory() or None if missing/corrupt.
    """
    if not file_path.exists():
        return default_factory() if default_factory else None
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading JSON from {file_path}: {e}")
        return default_factory() if default_factory else None


def save_report(report_data: Dict[str, Any]) -> bool:
    """
    Saves report to latest.json and historical archive.
    Refuses to overwrite a good existing report with an empty report unless explicitly forced.
    """
    if not report_data:
        logger.warning("Attempted to save empty report data. Aborted.")
        return False

    date_str = report_data.get("report_date")
    if not date_str:
        import datetime
        date_str = datetime.datetime.now().strftime("%Y-%m-%d")

    # Save to history
    history_file = HISTORY_DIR / f"{date_str}.json"
    atomic_write_json(history_file, report_data)

    # Save to latest
    success = atomic_write_json(LATEST_REPORT_FILE, report_data)
    return success


def load_latest_report() -> Optional[Dict[str, Any]]:
    """Loads the most recent briefing report."""
    return load_json(LATEST_REPORT_FILE)


def load_historical_report(date_str: str) -> Optional[Dict[str, Any]]:
    """Loads a specific historical report by date YYYY-MM-DD."""
    file_path = HISTORY_DIR / f"{date_str}.json"
    return load_json(file_path)


def list_historical_reports() -> List[str]:
    """Returns a sorted list of available historical report dates (newest first)."""
    if not HISTORY_DIR.exists():
        return []
    files = list(HISTORY_DIR.glob("*.json"))
    dates = [f.stem for f in files if f.is_file()]
    dates.sort(reverse=True)
    return dates


# --- Preferences & Memory Management ---

DEFAULT_PREFERENCES = {
    "topic_weights": {
        "AI Models & Releases": 1.1,
        "India AI & DPI": 1.25,
        "Semiconductors & Hardware": 1.15,
        "Robotics & Automation": 1.0,
        "AI Safety & Governance": 1.0,
        "Research Breakthroughs": 1.15,
        "Enterprise & Startups": 1.05
    },
    "feedback_history": []
}


def load_preferences() -> Dict[str, Any]:
    """Loads user preferences and learned topic weights."""
    return load_json(PREFERENCES_FILE, lambda: DEFAULT_PREFERENCES.copy())


def save_preferences(preferences: Dict[str, Any]) -> bool:
    """Saves user preferences to data/preferences.json."""
    return atomic_write_json(PREFERENCES_FILE, preferences)


def record_user_feedback(
    story_headline: str,
    story_category: str,
    feedback_type: str,
    story_url: str = ""
) -> Dict[str, Any]:
    """
    Applies user feedback to adjust topic weights in memory.
    Supported feedback_type: 'useful', 'not_relevant', 'already_known', 'misleading', 'interested'
    """
    prefs = load_preferences()
    topic_weights = prefs.get("topic_weights", {})
    
    # Weight adjustments
    delta = 0.0
    if feedback_type == "useful":
        delta = 0.08
    elif feedback_type == "interested":
        delta = 0.12
    elif feedback_type == "not_relevant":
        delta = -0.10
    elif feedback_type == "misleading":
        delta = -0.15

    # Update matching category
    matched = False
    for cat in topic_weights.keys():
        if cat.lower() in story_category.lower() or story_category.lower() in cat.lower():
            new_w = max(0.4, min(2.0, topic_weights[cat] + delta))
            topic_weights[cat] = round(new_w, 3)
            matched = True
            break
            
    if not matched and story_category:
        topic_weights[story_category] = round(max(0.4, min(2.0, 1.0 + delta)), 3)

    # Append to feedback log
    import datetime
    prefs["feedback_history"].append({
        "timestamp": datetime.datetime.now().isoformat(),
        "headline": story_headline,
        "category": story_category,
        "feedback": feedback_type,
        "url": story_url
    })
    
    # Keep last 100 feedback entries
    if len(prefs["feedback_history"]) > 100:
        prefs["feedback_history"] = prefs["feedback_history"][-100:]

    prefs["topic_weights"] = topic_weights
    save_preferences(prefs)
    return prefs


# --- Seen Stories Tracking ---

def load_seen_stories() -> Dict[str, Any]:
    """Loads seen story URLs and hashes to avoid repetitive coverage."""
    return load_json(SEEN_STORIES_FILE, lambda: {"seen_urls": {}, "seen_hashes": {}})


def record_seen_stories(stories: List[Dict[str, Any]]) -> bool:
    """Records newly published stories into seen_stories.json."""
    seen_data = load_seen_stories()
    import time
    now_ts = time.time()
    
    from engine.deduplicator import compute_headline_hash
    for s in stories:
        url = s.get("url")
        headline = s.get("headline", "")
        if url:
            seen_data["seen_urls"][url] = now_ts
        if headline:
            h_hash = compute_headline_hash(headline)
            seen_data["seen_hashes"][h_hash] = now_ts
            
    return atomic_write_json(SEEN_STORIES_FILE, seen_data)
