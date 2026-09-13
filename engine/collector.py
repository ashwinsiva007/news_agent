"""
Article Collector: Fetches news from configured RSS feeds, Google News, and research repositories.
"""
import logging
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
import feedparser
import requests
from config import RSS_FEEDS
from engine.normalizer import clean_url, normalize_headline, parse_date

logger = logging.getLogger(__name__)

USER_AGENT = "AIMorningResearchAgent/1.0 (+https://github.com/yourusername/ai-morning-agent)"


def fetch_feed_articles(feed_cfg: Dict[str, Any], timeout: int = 10) -> List[Dict[str, Any]]:
    """
    Fetches and parses a single RSS feed safely with a timeout and custom User-Agent.
    """
    articles = []
    feed_url = feed_cfg["url"]
    feed_name = feed_cfg["name"]
    tier = feed_cfg.get("tier", "tier_3_coverage")
    default_cat = feed_cfg.get("category", "Technology & AI")
    is_india = feed_cfg.get("is_india_focused", False)

    try:
        # Use requests first to handle HTTP timeouts and headers reliably
        headers = {"User-Agent": USER_AGENT}
        resp = requests.get(feed_url, headers=headers, timeout=timeout)
        if resp.status_code != 200:
            logger.warning(f"Feed {feed_name} returned status {resp.status_code}")
            return []
        
        parsed = feedparser.parse(resp.content)
        
        for entry in parsed.entries:
            raw_title = entry.get("title", "")
            raw_link = entry.get("link", "")
            if not raw_title or not raw_link:
                continue
            
            headline = normalize_headline(raw_title)
            article_url = clean_url(raw_link)
            
            # Date handling
            date_struct = entry.get("published_parsed") or entry.get("updated_parsed")
            raw_date_str = entry.get("published") or entry.get("updated") or ""
            dt_utc, ist_str = parse_date(date_struct or raw_date_str)
            
            # Description / summary
            summary_raw = entry.get("summary") or entry.get("description") or ""
            # Strip html tags from summary
            import re, html
            summary_clean = re.sub(r"<[^>]+>", " ", html.unescape(summary_raw))
            summary_clean = re.sub(r"\s+", " ", summary_clean).strip()
            
            # Publisher / Author
            publisher = entry.get("source", {}).get("title") or entry.get("author") or feed_name
            
            article = {
                "headline": headline,
                "raw_headline": raw_title,
                "url": article_url,
                "source": feed_name,
                "publisher": publisher,
                "published_utc": dt_utc.isoformat(),
                "published_ist": ist_str,
                "published_timestamp": dt_utc.timestamp(),
                "description": summary_clean[:600],
                "tier": tier,
                "category": default_cat,
                "is_india_focused": is_india,
                "raw_feed_url": feed_url
            }
            articles.append(article)
            
    except Exception as e:
        logger.error(f"Error collecting feed '{feed_name}' from {feed_url}: {e}")
        
    return articles


def collect_all_articles(
    custom_feeds: Optional[List[Dict[str, Any]]] = None,
    lookback_hours: int = 24
) -> Dict[str, Any]:
    """
    Collects articles across all configured feeds and filters by lookback window.
    If the lookback yields fewer than 5 reliable stories, callers can expand lookback.
    
    Returns:
        {
            "articles": List of collected articles,
            "total_fetched": int,
            "errors": List of error messages,
            "lookback_hours": int
        }
    """
    feeds = custom_feeds if custom_feeds is not None else RSS_FEEDS
    collected = []
    errors = []
    
    cutoff_utc = datetime.now(timezone.utc) - timedelta(hours=lookback_hours)
    
    for feed in feeds:
        try:
            feed_articles = fetch_feed_articles(feed)
            collected.extend(feed_articles)
        except Exception as e:
            msg = f"Failed to fetch {feed.get('name', 'unknown')}: {str(e)}"
            errors.append(msg)
            logger.error(msg)
            
    # Filter by lookback
    filtered_articles = []
    for art in collected:
        try:
            pub_dt = datetime.fromisoformat(art["published_utc"])
            if pub_dt >= cutoff_utc:
                filtered_articles.append(art)
        except Exception:
            # If date parse fails, include as safe fallback
            filtered_articles.append(art)
            
    return {
        "articles": filtered_articles,
        "total_fetched": len(collected),
        "total_after_lookback": len(filtered_articles),
        "lookback_hours": lookback_hours,
        "errors": errors
    }
