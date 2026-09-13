"""
Unit tests for Transparent Multi-Factor Ranking Engine
"""
import time
import pytest
from engine.ranker import (
    calculate_india_relevance, calculate_recency_score, rank_articles
)


def test_calculate_india_relevance_high():
    art = {
        "headline": "IndiaAI Mission awards compute grants to domestic startups in Bengaluru",
        "description": "MeitY announces GPU subsidization for Indian researchers.",
        "is_india_focused": True
    }
    score, matched = calculate_india_relevance(art)
    assert score >= 0.70
    assert "indiaai" in matched or "india" in matched or "bengaluru" in matched


def test_calculate_india_relevance_global():
    art = {
        "headline": "Anthropic updates Claude 3.5 Sonnet safety benchmarks",
        "description": "New evaluations demonstrate reduced hallucination rates.",
        "is_india_focused": False
    }
    score, matched = calculate_india_relevance(art)
    assert score == 0.0
    assert len(matched) == 0


def test_calculate_recency_decay():
    now_ts = time.time()
    fresh = calculate_recency_score(now_ts - 3600)      # 1 hour ago
    one_day = calculate_recency_score(now_ts - 86400)    # 24 hours ago
    three_days = calculate_recency_score(now_ts - 259200) # 72 hours ago
    
    assert fresh > one_day
    assert one_day > three_days


def test_rank_articles_priority():
    articles = [
        {
            "headline": "Minor gaming update released",
            "credibility_score": 0.5,
            "evidence_strength_score": 0.5,
            "is_india_focused": False,
            "description": "Patch notes for video game.",
            "published_timestamp": time.time() - 86400,
            "corroboration_count": 0,
            "cluster_size": 1
        },
        {
            "headline": "India Semiconductor Mission selects 3 new chip design startups in Hyderabad",
            "credibility_score": 0.95,
            "evidence_strength_score": 0.95,
            "is_india_focused": True,
            "description": "MeitY and IndiaAI provide funding for domestic RISC-V processors.",
            "published_timestamp": time.time() - 3600,
            "corroboration_count": 3,
            "cluster_size": 4
        }
    ]

    ranked = rank_articles(articles, limit=2)
    assert len(ranked) == 2
    assert ranked[0]["rank"] == 1
    assert "India Semiconductor" in ranked[0]["headline"]
    assert ranked[0]["scores"]["composite"] > ranked[1]["scores"]["composite"]
