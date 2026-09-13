"""
Unit tests for End-to-End Report Generation and Integrity
"""
import pytest
from unittest.mock import patch
from research import run_research_pipeline
from config import MAX_BRIEFING_WORDS


MOCK_TOPICS = [
    ("India Semiconductor Mission approves Dholera Fab", "Semiconductors & Hardware", "Tata starts semiconductor manufacturing facility in Gujarat."),
    ("OpenAI releases frontier reasoning weights", "AI Models & Releases", "New benchmark scores announced for advanced AI inference models."),
    ("Sarvam AI open-sources Indic language model suite", "India AI & DPI", "Domestic foundational models launched supporting 22 Indian languages."),
    ("ISRO integrates autonomous vision AI for lunar rover", "Robotics & Automation", "Autonomous navigation deployed for future space exploration missions."),
    ("IIT Madras develops AI diagnostic tool for rural clinics", "Healthcare & AI", "Low compute medical screening system deployed across community health centers."),
    ("MeitY publishes national safety framework for generative AI", "AI Safety & Governance", "Comprehensive guidelines issued for responsible deployment of AI."),
    ("India Digital Public Infrastructure expands AI translation layer", "India AI & DPI", "Bhashini translation integrated into national digital public services."),
    ("New deep learning architecture reduces training energy by 40%", "Research Breakthroughs", "Novel algorithmic advance published in peer-reviewed archive.")
]

MOCK_ARTICLES = [
    {
        "headline": topic[0],
        "raw_headline": f"{topic[0]} - TechCrunch",
        "url": f"https://example.com/article/{idx}",
        "source": "TechCrunch AI",
        "publisher": "TechCrunch",
        "published_utc": "2026-09-13T10:00:00+00:00",
        "published_ist": "13 Sep 2026, 03:30 PM IST",
        "published_timestamp": 1789300000,
        "description": topic[2],
        "tier": "tier_1_primary",
        "category": topic[1],
        "is_india_focused": "India" in topic[0] or "Indic" in topic[0] or "IIT" in topic[0] or "MeitY" in topic[0],
        "raw_feed_url": "https://example.com/feed"
    }
    for idx, topic in enumerate(MOCK_TOPICS)
]


def test_run_research_pipeline_mocked():
    with patch("research.collect_all_articles") as mock_collect:
        mock_collect.return_value = {
            "articles": MOCK_ARTICLES,
            "total_fetched": 8,
            "total_after_lookback": 8,
            "lookback_hours": 24,
            "errors": []
        }
        
        report = run_research_pipeline(lookback_hours=24, dry_run=True)
        
        assert report["status"] == "success"
        assert report["story_count"] == 5
        assert report["briefing_word_count"] <= MAX_BRIEFING_WORDS
        assert report["word_limit_status"] == "Passed"
        assert len(report["stories"]) == 5
        
        # Check that ranks are assigned sequentially 1 to 5
        ranks = [s["rank"] for s in report["stories"]]
        assert ranks == [1, 2, 3, 4, 5]


def test_pipeline_handles_empty_collection():
    with patch("research.collect_all_articles") as mock_collect:
        mock_collect.return_value = {
            "articles": [],
            "total_fetched": 0,
            "total_after_lookback": 0,
            "lookback_hours": 24,
            "errors": ["Connection timeout"]
        }
        
        report = run_research_pipeline(lookback_hours=24, dry_run=True)
        assert report["status"] == "error"
        assert len(report["stories"]) == 0
