"""
Verification Engine: Evaluates source credibility, corroboration strength, and factual claim integrity.
"""
import re
from typing import Dict, Any, List, Tuple
from config import CREDIBILITY_TIERS, MIN_CREDIBILITY_THRESHOLD

# Regex patterns for identifying marketing hype / unverified claims vs verified facts
UNVERIFIED_HYPE_PATTERNS = [
    r"\bclaims? to be the world['’]s first\b",
    r"\bunbeatable\b",
    r"\brevolutionize everything\b",
    r"\b100x faster than\b",
    r"\bagi achieved\b",
    r"\brumor(ed)?\b",
    r"\bleaked\b"
]

OFFICIAL_ANNOUNCEMENT_KEYWORDS = [
    "pib.gov.in", "arxiv.org", "openai.com", "googleblog.com", "deepmind.google",
    "blogs.microsoft.com", "meta.com", "huggingface.co", "meity.gov.in", "indiaai.gov.in"
]


def classify_verification_status(article: Dict[str, Any]) -> Dict[str, Any]:
    """
    Evaluates an article's credibility tier, corroboration count, and content signals to assign:
    - verification_status: ("Verified (Primary)", "Reputable Reporting", "Claimed by Organization", "Corroborated Multi-Source", "Unverified")
    - credibility_score: float (0.0 to 1.0)
    - evidence_strength_score: float (0.0 to 1.0)
    - is_eligible: bool (meets minimum credibility threshold)
    - verification_rationale: str
    """
    tier = article.get("tier", "tier_3_coverage")
    cred_score = CREDIBILITY_TIERS.get(tier, 0.50)
    corrob_count = article.get("corroboration_count", 0)
    url = article.get("url", "").lower()
    headline = article.get("headline", "").lower()
    desc = article.get("description", "").lower()

    # Check if primary source (official or academic)
    is_primary_domain = any(domain in url for domain in OFFICIAL_ANNOUNCEMENT_KEYWORDS)
    if tier == "tier_1_primary" or is_primary_domain:
        cred_score = max(cred_score, 1.0)
        status = "Verified (Primary Source / Paper)"
        evidence_score = 1.0
        rationale = "Direct primary publication, institutional release, or peer-reviewed archive."
    elif corrob_count >= 2:
        # Multiple independent outlets reporting the same event
        cred_score = min(1.0, cred_score + 0.15)
        status = "Corroborated (Multi-Source)"
        evidence_score = 0.90
        rationale = f"Corroborated across {corrob_count + 1} independent news organizations."
    elif tier == "tier_2_reputable":
        status = "Reputable Reporting"
        evidence_score = 0.80
        rationale = f"Published by trusted tech journalism outlet ({article.get('source', 'Reputable Source')})."
    elif tier == "tier_3_coverage":
        status = "Industry Coverage"
        evidence_score = 0.65
        rationale = "Reported by specialized industry media."
    else:
        status = "Unverified / Emerging"
        evidence_score = 0.40
        rationale = "Single-source or unverified coverage."

    # Check for hype / speculative flags
    hype_matches = [p for p in UNVERIFIED_HYPE_PATTERNS if re.search(p, headline) or re.search(p, desc)]
    if hype_matches and not is_primary_domain:
        evidence_score = max(0.3, evidence_score - 0.25)
        status = "Claimed / Speculative"
        rationale += " Contains unverified superlative or speculative claims."

    is_eligible = cred_score >= MIN_CREDIBILITY_THRESHOLD

    return {
        "verification_status": status,
        "credibility_score": round(cred_score, 3),
        "evidence_strength_score": round(evidence_score, 3),
        "is_eligible": is_eligible,
        "verification_rationale": rationale
    }


def verify_all_events(canonical_events: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Applies verification logic across all candidate canonical events.
    
    Returns:
        (eligible_events, rejected_events)
    """
    eligible = []
    rejected = []

    for event in canonical_events:
        v_result = classify_verification_status(event)
        event.update(v_result)
        
        if event["is_eligible"]:
            eligible.append(event)
        else:
            rejection_record = event.copy()
            rejection_record["rejection_reason"] = f"Failed credibility threshold (Score: {event['credibility_score']} < {MIN_CREDIBILITY_THRESHOLD})"
            rejected.append(rejection_record)

    return eligible, rejected
