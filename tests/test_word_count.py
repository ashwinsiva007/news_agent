"""
Unit tests for Word Count & <= 99 Words Limit Enforcement
"""
import pytest
from engine.summarizer import (
    count_words, count_briefing_words, enforce_word_limit
)
from config import MAX_BRIEFING_WORDS


def test_count_words_basic():
    assert count_words("Hello world this is a test.") == 6
    assert count_words("   Multiple   spaces   and   punctuation!  ") == 4
    assert count_words("") == 0


def test_count_briefing_words():
    stories = [
        {"headline": "AI Mission Approved", "explanation": "Government allocates funds for compute infrastructure."},
        {"headline": "New Chip Fab", "explanation": "Construction starts in Gujarat."},
    ]
    # headline 1: 3, exp 1: 6 = 9
    # headline 2: 3, exp 2: 4 = 7
    # total = 16
    assert count_briefing_words(stories) == 16


def test_enforce_word_limit_under_cap():
    stories = [
        {"headline": f"Story {i}", "explanation": "Short sentence explaining key event."}
        for i in range(5)
    ]
    compressed, total_words = enforce_word_limit(stories, max_words=99)
    assert total_words <= 99
    assert len(compressed) == 5


def test_enforce_word_limit_heavily_over_cap():
    verbose_stories = [
        {
            "headline": f"Extremely Long And Complex Headline Describing Breakthrough Model Release Number {i}",
            "explanation": "This is a very long and detailed paragraph with extensive explanations about the architecture, benchmarks, parameters, training runs, compute clusters, evaluation methodologies, and multiple reasons why this matters to Indian students and engineers in great detail."
        }
        for i in range(5)
    ]
    
    # Verify input is way over 99 words
    initial_words = count_briefing_words(verbose_stories)
    assert initial_words > 150

    # Run enforcement
    compressed, final_words = enforce_word_limit(verbose_stories, max_words=MAX_BRIEFING_WORDS)
    
    assert final_words <= MAX_BRIEFING_WORDS
    assert final_words <= 99
    assert len(compressed) == 5
    for s in compressed:
        assert len(s["headline"]) > 0
        assert len(s["explanation"]) > 0
