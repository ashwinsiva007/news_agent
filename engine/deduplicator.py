"""
Deduplication Engine: Identifies exact and near-duplicate stories, grouping them into unified events.
"""
import re
import hashlib
from difflib import SequenceMatcher
from typing import List, Dict, Any, Tuple
from config import CREDIBILITY_TIERS


def compute_headline_hash(headline: str) -> str:
    """Computes a normalized SHA-256 hash for exact headline matching."""
    cleaned = re.sub(r"[^\w\s]", "", headline.lower())
    tokens = " ".join(cleaned.split())
    return hashlib.sha256(tokens.encode("utf-8")).hexdigest()


STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "with",
    "by", "about", "of", "from", "as", "is", "are", "was", "were", "be", "been",
    "this", "that", "these", "those", "over", "under", "new", "after", "its", "it"
}


def get_token_set(text: str) -> set:
    """Extracts informative word tokens from text, removing common stopwords."""
    if not text:
        return set()
    # Normalize common compounds
    t = text.lower().replace("indiaai", "india ai")
    cleaned = re.sub(r"[^\w\s]", " ", t)
    tokens = {w for w in cleaned.split() if len(w) > 2 and w not in STOPWORDS}
    return tokens


def calculate_similarity(h1: str, h2: str, desc1: str = "", desc2: str = "") -> float:
    """
    Computes hybrid similarity score between two articles using headline sequence matching,
    token set Jaccard similarity, containment overlap, and combined article concept overlap.
    """
    if not h1 or not h2:
        return 0.0
        
    # 1. Headline Sequence Matcher
    seq_sim = SequenceMatcher(None, h1.lower(), h2.lower()).ratio()
    
    # 2. Headline Token Overlap
    tokens1 = get_token_set(h1)
    tokens2 = get_token_set(h2)
    
    jaccard = 0.0
    overlap = 0.0
    if tokens1 and tokens2:
        intersection = tokens1.intersection(tokens2)
        union = tokens1.union(tokens2)
        jaccard = len(intersection) / len(union) if union else 0.0
        min_len = min(len(tokens1), len(tokens2))
        overlap = len(intersection) / min_len if min_len else 0.0
        
    # 3. Combined Text Concept Overlap (Headline + Description)
    comb1 = get_token_set(f"{h1} {desc1}")
    comb2 = get_token_set(f"{h2} {desc2}")
    comb_overlap = 0.0
    if comb1 and comb2:
        comb_inter = comb1.intersection(comb2)
        comb_min = min(len(comb1), len(comb2))
        comb_overlap = len(comb_inter) / comb_min if comb_min else 0.0

    # Max score
    token_score = max(jaccard * 0.4 + overlap * 0.6, comb_overlap)
    total_sim = max(seq_sim, token_score)
    return total_sim


def deduplicate_and_cluster(articles: List[Dict[str, Any]], similarity_threshold: float = 0.58) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Groups duplicate articles into unified event clusters.
    
    Returns:
        (canonical_events, duplicate_clusters_log)
    """
    if not articles:
        return [], []

    # Step 1: Exact Deduplication (by URL or exact normalized headline hash)
    seen_urls = set()
    seen_hashes = set()
    unique_articles = []
    
    for art in articles:
        url = art.get("url", "").strip()
        h_hash = compute_headline_hash(art.get("headline", ""))
        
        if url in seen_urls or h_hash in seen_hashes:
            continue
        
        seen_urls.add(url)
        seen_hashes.add(h_hash)
        unique_articles.append(art)

    # Step 2: Near-Duplicate Event Clustering
    clusters = []  # List of lists of articles belonging to the same event
    
    for art in unique_articles:
        matched_cluster = None
        headline = art.get("headline", "")
        desc = art.get("description", "")
        
        for cluster in clusters:
            # Compare with primary article of this cluster
            primary = cluster[0]
            sim = calculate_similarity(
                headline, primary.get("headline", ""),
                desc, primary.get("description", "")
            )
            
            if sim >= similarity_threshold:
                matched_cluster = cluster
                break
                
        if matched_cluster is not None:
            matched_cluster.append(art)
        else:
            clusters.append([art])

    # Step 3: Select Canonical Primary Story for each cluster and preserve corroborations
    canonical_events = []
    duplicate_log = []

    for cluster in clusters:
        # Sort cluster by Tier credibility score descending, then by publication timestamp ascending (prefer earliest)
        def get_cred(a):
            return CREDIBILITY_TIERS.get(a.get("tier", "tier_3_coverage"), 0.5)

        cluster.sort(key=lambda x: (get_cred(x), -x.get("published_timestamp", 0)), reverse=True)
        primary = cluster[0].copy()
        
        # Corroborating sources
        corroborating = []
        for other in cluster[1:]:
            corroborating.append({
                "source": other.get("source", ""),
                "publisher": other.get("publisher", ""),
                "url": other.get("url", ""),
                "headline": other.get("headline", ""),
                "tier": other.get("tier", "tier_3_coverage")
            })
            
        primary["corroborating_sources"] = corroborating
        primary["corroboration_count"] = len(corroborating)
        primary["cluster_size"] = len(cluster)
        canonical_events.append(primary)
        
        if len(cluster) > 1:
            duplicate_log.append({
                "canonical_headline": primary.get("headline"),
                "source": primary.get("source"),
                "duplicates_merged_count": len(cluster) - 1,
                "corroborating_publishers": [c["publisher"] for c in corroborating]
            })

    return canonical_events, duplicate_log
