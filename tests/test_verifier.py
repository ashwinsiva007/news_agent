"""
Unit tests for Verification and Credibility Engine
"""
import pytest
from engine.verifier import classify_verification_status, verify_all_events
from config import MIN_CREDIBILITY_THRESHOLD


def test_classify_tier_1_primary():
    art = {
        "url": "https://arxiv.org/abs/2405.12345",
        "tier": "tier_1_primary",
        "headline": "Scaling Laws for Frontier Reasoning",
        "description": "Research paper on inference-time compute scaling."
    }
    result = classify_verification_status(art)
    assert result["is_eligible"] is True
    assert result["credibility_score"] == 1.0
    assert "Primary Source" in result["verification_status"]


def test_classify_corroborated_multi_source():
    art = {
        "url": "https://techcrunch.com/2026/09/ai-update",
        "tier": "tier_2_reputable",
        "corroboration_count": 3,
        "headline": "Major AI Company Launches Open Weights Model",
        "description": "Open weights release confirmed by several reporters."
    }
    result = classify_verification_status(art)
    assert result["is_eligible"] is True
    assert result["credibility_score"] >= 0.90
    assert "Corroborated" in result["verification_status"]


def test_classify_unverified_rejection():
    art = {
        "url": "https://random-anonymous-blog.com/post/123",
        "tier": "tier_5_unverified",
        "headline": "Anonymous rumor claims AGI achieved in secret lab",
        "description": "Rumored breakthrough revolutionary claim unbeatable.",
        "corroboration_count": 0
    }
    result = classify_verification_status(art)
    assert result["is_eligible"] is False
    assert result["credibility_score"] < MIN_CREDIBILITY_THRESHOLD


def test_verify_all_events_splits_eligible_and_rejected():
    events = [
        {"url": "https://pib.gov.in/release1", "tier": "tier_1_primary", "headline": "Govt initiative"},
        {"url": "https://fake.net/post", "tier": "tier_5_unverified", "headline": "Unverified rumor"}
    ]
    eligible, rejected = verify_all_events(events)
    assert len(eligible) == 1
    assert len(rejected) == 1
    assert eligible[0]["tier"] == "tier_1_primary"
    assert "Failed credibility" in rejected[0]["rejection_reason"]
