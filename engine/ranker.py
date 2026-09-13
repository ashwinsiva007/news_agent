"""
Ranking Engine: Transparent multi-factor scoring prioritizing India relevance, credibility, and technical significance.
"""
import time
import math
from typing import List, Dict, Any, Tuple
from config import RANKING_WEIGHTS, INDIA_KEYWORDS, TECH_SIGNIFICANCE_KEYWORDS, TARGET_STORY_COUNT


def calculate_india_relevance(article: Dict[str, Any]) -> Tuple[float, List[str]]:
    """
    Computes India relevance score (0.0 to 1.0) and matched indicators.
    """
    text = (
        article.get("headline", "") + " " +
        article.get("description", "") + " " +
        article.get("source", "")
    ).lower()

    matched_keywords = []
    for kw in INDIA_KEYWORDS:
        if kw in text:
            matched_keywords.append(kw)

    score = 0.0
    if article.get("is_india_focused", False):
        score += 0.45

    if matched_keywords:
        # Give diminishing returns for keyword matches
        kw_boost = min(0.55, len(matched_keywords) * 0.18)
        score += kw_boost

    final_score = min(1.0, score)
    return round(final_score, 3), list(set(matched_keywords))


def calculate_recency_score(published_timestamp: float) -> float:
    """
    Exponential time-decay score based on hours elapsed since publication.
    Full 1.0 if < 6 hours old, decaying smoothly.
    """
    now_ts = time.time()
    age_hours = max(0.0, (now_ts - published_timestamp) / 3600.0)

    # Half-life of 24 hours
    decay = math.exp(-0.693 * (age_hours / 24.0))
    return round(min(1.0, max(0.1, decay)), 3)


def calculate_trend_momentum(corroboration_count: int, cluster_size: int) -> float:
    """
    Computes trend momentum score based on multi-source publisher coverage.
    """
    if cluster_size >= 4:
        return 1.0
    elif cluster_size == 3:
        return 0.85
    elif cluster_size == 2:
        return 0.65
    return 0.40


def calculate_technical_significance(article: Dict[str, Any]) -> float:
    """
    Computes technical/practical significance based on tech keywords and research indicators.
    """
    text = (article.get("headline", "") + " " + article.get("description", "")).lower()
    matches = [kw for kw in TECH_SIGNIFICANCE_KEYWORDS if kw in text]
    
    score = 0.40
    if matches:
        score += min(0.60, len(matches) * 0.15)
    return round(min(1.0, score), 3)


def get_user_preference_boost(article: Dict[str, Any], user_preferences: Dict[str, Any]) -> float:
    """
    Calculates preference score based on topics user liked or disliked in memory.
    """
    if not user_preferences or "topic_weights" not in user_preferences:
        return 0.5  # Neutral baseline

    category = article.get("category", "")
    headline = article.get("headline", "").lower()
    
    weights = user_preferences.get("topic_weights", {})
    boost = 0.5  # Baseline

    for topic, w in weights.items():
        if topic.lower() in category.lower() or topic.lower() in headline:
            boost += (w - 1.0) * 0.3  # Scale delta

    return round(min(1.0, max(0.0, boost)), 3)


def rank_articles(
    articles: List[Dict[str, Any]],
    user_preferences: Dict[str, Any] = None,
    limit: int = TARGET_STORY_COUNT
) -> List[Dict[str, Any]]:
    """
    Ranks eligible articles using the transparent multi-factor scoring formula.
    Returns the top `limit` stories with full scoring breakdowns.
    """
    if not articles:
        return []

    ranked = []
    
    for art in articles:
        cred_score = art.get("credibility_score", 0.7)
        evid_score = art.get("evidence_strength_score", 0.7)
        india_score, matched_india_kw = calculate_india_relevance(art)
        recency_score = calculate_recency_score(art.get("published_timestamp", time.time()))
        trend_score = calculate_trend_momentum(art.get("corroboration_count", 0), art.get("cluster_size", 1))
        pref_score = get_user_preference_boost(art, user_preferences or {})
        tech_sig = calculate_technical_significance(art)

        # Composite score calculation
        w = RANKING_WEIGHTS
        composite_score = (
            (cred_score * w["credibility"]) +
            (evid_score * w["evidence_strength"]) +
            (india_score * w["india_relevance"]) +
            (recency_score * w["recency"]) +
            (trend_score * w["trend_momentum"]) +
            (pref_score * w["user_preference"])
        )

        # Store transparent score factor breakdown
        art_scored = art.copy()
        art_scored["scores"] = {
            "composite": round(composite_score, 4),
            "credibility": cred_score,
            "evidence_strength": evid_score,
            "india_relevance": india_score,
            "recency": recency_score,
            "trend_momentum": trend_score,
            "user_preference": pref_score,
            "technical_significance": tech_sig
        }
        art_scored["matched_india_keywords"] = matched_india_kw
        art_scored["ranking_rationale"] = (
            f"Composite: {round(composite_score, 2)} | "
            f"India Rel: {india_score} ({', '.join(matched_india_kw) if matched_india_kw else 'Global impact'}) | "
            f"Cred: {cred_score} | Recency: {recency_score}"
        )
        ranked.append(art_scored)

    # Sort descending by composite score
    ranked.sort(key=lambda x: x["scores"]["composite"], reverse=True)

    # Assign rank numbers 1..N
    for idx, story in enumerate(ranked[:limit]):
        story["rank"] = idx + 1

    return ranked[:limit]
