"""
Master Research Pipeline for AI Morning Research Agent.
Executes the 8-stage research, verification, ranking, and synthesis workflow.
"""
import sys
import logging
import argparse
from datetime import datetime
from typing import Dict, Any, Optional

from config import (
    PROJECT_NAME, SCHEDULE_TIME, TARGET_STORY_COUNT, MAX_BRIEFING_WORDS
)
from engine.normalizer import get_current_ist_time, get_current_ist_date
from engine.collector import collect_all_articles
from engine.deduplicator import deduplicate_and_cluster
from engine.verifier import verify_all_events
from engine.ranker import rank_articles
from engine.summarizer import generate_ai_summaries, enforce_word_limit, count_briefing_words
from engine.storage import save_report, load_preferences, record_seen_stories, load_latest_report

# Configure clean logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("research_pipeline")


def run_research_pipeline(
    lookback_hours: int = 24,
    force_fresh: bool = False,
    dry_run: bool = False
) -> Dict[str, Any]:
    """
    Executes the complete 8-stage research engine:
    1. News discovery across configured feeds
    2. Metadata and URL normalization
    3. Claim & context extraction
    4. Credibility & verification checking
    5. Exact and near-duplicate clustering
    6. Trend momentum & multi-source corroboration
    7. Multi-factor India-priority ranking
    8. Synthesis & strict <=99 words verification
    """
    logger.info(f"=== Starting {PROJECT_NAME} Pipeline ===")
    ist_time_str = get_current_ist_time()
    ist_date_str = get_current_ist_date()

    # Step 1 & 2: Collect & Normalize
    logger.info(f"Stage 1 & 2: Discovering and normalizing news (lookback: {lookback_hours}h)...")
    collection_res = collect_all_articles(lookback_hours=lookback_hours)
    raw_articles = collection_res["articles"]
    logger.info(f"Fetched {collection_res['total_fetched']} raw entries, {len(raw_articles)} within {lookback_hours}h.")

    # Adaptive lookback: if too few articles, expand window
    if len(raw_articles) < TARGET_STORY_COUNT and lookback_hours < 72:
        logger.info("Insufficient articles in initial window; expanding lookback to 72h...")
        collection_res = collect_all_articles(lookback_hours=72)
        raw_articles = collection_res["articles"]

    if not raw_articles:
        logger.warning("No articles could be collected from feeds.")
        # Return fallback report without destroying latest report
        return {
            "status": "error",
            "message": "No news articles could be collected from configured sources.",
            "report_date": ist_date_str,
            "generated_at_ist": ist_time_str,
            "stories": [],
            "briefing_word_count": 0,
            "errors": collection_res["errors"]
        }

    # Step 5: Deduplicate and cluster near-duplicates into canonical events
    logger.info("Stage 5: Deduplicating and clustering near-duplicate events...")
    canonical_events, duplicate_log = deduplicate_and_cluster(raw_articles)
    logger.info(f"Clustered {len(raw_articles)} articles into {len(canonical_events)} distinct events.")

    # Step 4: Verification & Credibility Eligibility
    logger.info("Stage 4: Verifying claims, evidence hierarchy, and credibility thresholds...")
    eligible_events, rejected_events = verify_all_events(canonical_events)
    logger.info(f"Verified {len(eligible_events)} eligible stories (rejected {len(rejected_events)} below threshold).")

    # Step 6 & 7: Multi-factor Ranking with India-first priority and user preferences
    logger.info("Stage 6 & 7: Ranking stories with India-first weighting and learning memory...")
    user_prefs = load_preferences()
    ranked_stories = rank_articles(eligible_events, user_preferences=user_prefs, limit=TARGET_STORY_COUNT)

    if not ranked_stories:
        logger.warning("No eligible stories met the quality and verification thresholds.")
        return {
            "status": "warning",
            "message": "Insufficient verified stories meeting credibility standards.",
            "report_date": ist_date_str,
            "generated_at_ist": ist_time_str,
            "stories": [],
            "briefing_word_count": 0,
            "rejected_stories": rejected_events
        }

    # Step 8: Ultra-concise synthesis & strict word limit enforcement (<= 99 words)
    logger.info("Stage 8: Generating ultra-concise summaries & enforcing strict <= 99 words cap...")
    summarized_stories = generate_ai_summaries(ranked_stories)
    final_stories, total_words = enforce_word_limit(summarized_stories, max_words=MAX_BRIEFING_WORDS)
    logger.info(f"Final Briefing generated: {len(final_stories)} stories, Total Briefing Word Count: {total_words} words (Limit: {MAX_BRIEFING_WORDS}).")

    # Assemble complete report document
    report_data = {
        "status": "success",
        "project_name": PROJECT_NAME,
        "schedule_time": SCHEDULE_TIME,
        "report_date": ist_date_str,
        "generated_at_ist": ist_time_str,
        "story_count": len(final_stories),
        "briefing_word_count": total_words,
        "word_limit_status": "Passed" if total_words <= MAX_BRIEFING_WORDS else "Exceeded",
        "lookback_period_hours": collection_res["lookback_hours"],
        "stories": final_stories,
        "research_metadata": {
            "total_raw_fetched": collection_res["total_fetched"],
            "total_after_lookback": collection_res["total_after_lookback"],
            "canonical_events_count": len(canonical_events),
            "eligible_events_count": len(eligible_events),
            "rejected_events_count": len(rejected_events),
            "duplicate_groups": duplicate_log,
            "rejected_stories": [
                {
                    "headline": r.get("headline"),
                    "source": r.get("source"),
                    "reason": r.get("rejection_reason")
                }
                for r in rejected_events[:10]
            ],
            "feed_errors": collection_res["errors"]
        }
    }

    # Save to storage unless dry run
    if not dry_run:
        logger.info("Saving report to reports/latest.json and historical archive...")
        save_report(report_data)
        record_seen_stories(final_stories)
        logger.info("Report saved successfully.")

    logger.info("=== Research Pipeline Completed Successfully ===")
    return report_data


def main():
    parser = argparse.ArgumentParser(description="AI Morning Research Agent CLI")
    parser.add_argument("--lookback", type=int, default=24, help="Lookback window in hours (default: 24)")
    parser.add_argument("--force", action="store_true", help="Force fresh research run")
    parser.add_argument("--dry-run", action="store_true", help="Run pipeline without writing to disk")
    parser.add_argument("--schedule", action="store_true", help="Run in scheduled CI/CD mode")
    args = parser.parse_args()

    report = run_research_pipeline(lookback_hours=args.lookback, force_fresh=args.force, dry_run=args.dry_run)
    if report.get("status") == "success":
        print(f"\n[SUCCESS] Briefing generated with {report['story_count']} stories ({report['briefing_word_count']} words).")
        for s in report["stories"]:
            print(f"  #{s['rank']} [{s['publisher']}]: {s['headline']}")
            print(f"     {s['explanation']}")
            print(f"     Source: {s['url']}\n")
        sys.exit(0)
    else:
        print(f"\n[WARNING] Pipeline finished with status: {report.get('status')} - {report.get('message')}")
        sys.exit(0)


if __name__ == "__main__":
    main()
