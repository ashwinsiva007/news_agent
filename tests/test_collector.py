"""
Unit tests for Collector and Normalizer components
"""
import pytest
from datetime import datetime, timezone
from engine.normalizer import clean_url, normalize_headline, parse_date


def test_clean_url_removes_tracking():
    url = "https://techcrunch.com/2026/09/ai-chips?utm_source=twitter&utm_medium=social&fbclid=12345&important_id=99"
    cleaned = clean_url(url)
    assert "utm_source" not in cleaned
    assert "fbclid" not in cleaned
    assert "important_id=99" in cleaned


def test_normalize_headline_removes_suffixes():
    raw = "Sarvam AI launches open-source Indic LLM - TechCrunch"
    cleaned = normalize_headline(raw)
    assert cleaned == "Sarvam AI launches open-source Indic LLM"


def test_normalize_headline_decodes_entities():
    raw = "&quot;India&#39;s AI Future&quot; &amp; Semiconductor Strategy"
    cleaned = normalize_headline(raw)
    assert cleaned == "\"India's AI Future\" & Semiconductor Strategy"


def test_parse_date_rfc2822():
    rfc_date = "Sun, 13 Sep 2026 07:30:00 +0000"
    dt_utc, ist_str = parse_date(rfc_date)
    assert dt_utc.year == 2026
    assert dt_utc.month == 9
    assert "IST" in ist_str
    assert "01:00 PM" in ist_str  # UTC 07:30 + 05:30 = 13:00 (01:00 PM)


def test_parse_date_fallback_on_invalid():
    dt_utc, ist_str = parse_date("not-a-valid-date")
    assert isinstance(dt_utc, datetime)
    assert "IST" in ist_str
