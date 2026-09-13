"""
Unit tests for Deduplication & Event Clustering Engine
"""
import pytest
from engine.deduplicator import (
    compute_headline_hash, calculate_similarity, deduplicate_and_cluster
)


def test_compute_headline_hash():
    h1 = "Google Releases New Gemini 1.5 Model!"
    h2 = "google releases new gemini 15 model"
    assert compute_headline_hash(h1) == compute_headline_hash(h2)


def test_calculate_similarity_near_duplicates():
    h1 = "India launches national AI mission with Rs 10000 crore outlay"
    h2 = "Cabinet approves IndiaAI Mission with budget of over Rs 10,300 crore"
    sim = calculate_similarity(h1, h2)
    assert sim > 0.45


def test_calculate_similarity_distinct_events():
    h1 = "Nvidia reports record data center revenue"
    h2 = "ISRO prepares for Chandrayaan-4 lunar sample return mission"
    sim = calculate_similarity(h1, h2)
    assert sim < 0.25


def test_deduplicate_and_cluster_groups_multi_source():
    articles = [
        {
            "headline": "Tata Electronics starts construction on Gujarat chip fab",
            "url": "https://example.com/news1",
            "tier": "tier_2_reputable",
            "publisher": "TechDaily",
            "source": "TechDaily",
            "published_timestamp": 1000,
            "description": "Tata begins work on Dholera semiconductor fab."
        },
        {
            "headline": "Tata begins building massive semiconductor fab in Dholera Gujarat",
            "url": "https://example.com/news2",
            "tier": "tier_1_primary",
            "publisher": "Official PIB",
            "source": "Official PIB",
            "published_timestamp": 1050,
            "description": "Government confirms ground breaking for Tata Dholera semiconductor plant."
        },
        {
            "headline": "OpenAI releases new reasoning model o3",
            "url": "https://example.com/news3",
            "tier": "tier_1_primary",
            "publisher": "OpenAI Blog",
            "source": "OpenAI Blog",
            "published_timestamp": 1100,
            "description": "New frontier reasoning capabilities announced."
        }
    ]

    canonical, dup_log = deduplicate_and_cluster(articles, similarity_threshold=0.50)
    
    # Should result in 2 canonical events
    assert len(canonical) == 2
    # The Tata cluster should pick the tier 1 source as primary
    tata_event = next(e for e in canonical if "Tata" in e["headline"] or "semiconductor" in e["headline"])
    assert tata_event["tier"] == "tier_1_primary"
    assert tata_event["corroboration_count"] == 1
    assert len(dup_log) == 1
