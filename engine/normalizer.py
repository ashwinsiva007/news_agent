"""
Text, URL, and Date Normalization Utilities
"""
import re
import html
import urllib.parse
from datetime import datetime, timezone, timedelta
from typing import Optional, Tuple
from email.utils import parsedate_to_datetime
import dateutil.parser

# Target Timezone: IST (UTC+05:30)
IST = timezone(timedelta(hours=5, minutes=30))

TRACKING_PARAMS = {
    "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
    "fbclid", "gclid", "msclkid", "ref", "source", "feature", "ocid",
    "spm", "from", "guccounter", "ncid"
}

PUBLISHER_SUFFIXES = [
    r"\s*[-|–—]\s*TechCrunch.*$",
    r"\s*[-|–—]\s*The Verge.*$",
    r"\s*[-|–—]\s*The Hindu.*$",
    r"\s*[-|–—]\s*The Economic Times.*$",
    r"\s*[-|–—]\s*Livemint.*$",
    r"\s*[-|–—]\s*Analytics India Magazine.*$",
    r"\s*[-|–—]\s*Inc42 Media.*$",
    r"\s*[-|–—]\s*VentureBeat.*$",
    r"\s*[-|–—]\s*MIT Technology Review.*$",
    r"\s*[-|–—]\s*Reuters.*$",
    r"\s*[-|–—]\s*Bloomberg.*$",
    r"\s*[-|–—]\s*Google News.*$"
]


def clean_url(url: str) -> str:
    """
    Remove marketing and tracking parameters from URL while preserving necessary query paths.
    """
    if not url or not isinstance(url, str):
        return ""
    
    url = url.strip()
    try:
        parsed = urllib.parse.urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            return url
        
        # Filter query params
        query_dict = urllib.parse.parse_qs(parsed.query, keep_blank_values=False)
        filtered_query = {
            k: v for k, v in query_dict.items() if k.lower() not in TRACKING_PARAMS
        }
        
        new_query = urllib.parse.urlencode(filtered_query, doseq=True)
        cleaned = urllib.parse.urlunparse((
            parsed.scheme,
            parsed.netloc.lower(),
            parsed.path,
            parsed.params,
            new_query,
            ""  # strip fragment tracking
        ))
        return cleaned.rstrip("/")
    except Exception:
        return url


def normalize_headline(headline: str) -> str:
    """
    Cleans raw RSS headline text:
    - Fixes unicode replacements (e.g. \ufffd, smart quotes)
    - Decodes HTML entities
    - Removes publisher suffixes (e.g., ' - The Verge')
    - Cleans extra whitespace and quotes
    """
    if not headline or not isinstance(headline, str):
        return ""
    
    # Fix common encoding glitches / replacement chars
    text = headline.replace("\ufffd", "'")
    
    # Decode HTML entities (&amp; -> &, &quot; -> ", etc.)
    text = html.unescape(text)
    
    # Replace non-standard quotes
    text = text.replace("“", "\"").replace("”", "\"").replace("‘", "'").replace("’", "'")
    
    # Remove HTML tags if any
    text = re.sub(r"<[^>]+>", " ", text)
    
    # Strip common publisher suffixes
    for suffix_pattern in PUBLISHER_SUFFIXES:
        text = re.sub(suffix_pattern, "", text, flags=re.IGNORECASE)
    
    # Clean trailing fragment words or punctuation
    text = re.sub(r"\s*[-|–—:]\s*$", "", text)
    
    # Clean outer wrapping quotes if the whole title is enclosed in quotes
    if (text.startswith('"') and text.endswith('"')) or (text.startswith("'") and text.endswith("'")):
        text = text[1:-1].strip()
        
    return text.strip()


def parse_date(date_str_or_struct) -> Tuple[datetime, str]:
    """
    Parses various date formats (RFC 2822, ISO 8601, time.struct_time)
    Returns: (datetime_utc, ist_formatted_string)
    """
    now_utc = datetime.now(timezone.utc)
    
    if not date_str_or_struct:
        # Default fallback to now
        dt_utc = now_utc
    elif isinstance(date_str_or_struct, (tuple, list)) and len(date_str_or_struct) >= 6:
        # parsed from feedparser struct_time
        try:
            dt_utc = datetime(*date_str_or_struct[:6], tzinfo=timezone.utc)
        except Exception:
            dt_utc = now_utc
    elif isinstance(date_str_or_struct, datetime):
        if date_str_or_struct.tzinfo is None:
            dt_utc = date_str_or_struct.replace(tzinfo=timezone.utc)
        else:
            dt_utc = date_str_or_struct.astimezone(timezone.utc)
    elif isinstance(date_str_or_struct, str):
        date_str = date_str_or_struct.strip()
        parsed_dt = None
        
        # Try RFC 2822
        try:
            parsed_dt = parsedate_to_datetime(date_str)
        except Exception:
            pass
        
        # Try dateutil parser
        if parsed_dt is None:
            try:
                parsed_dt = dateutil.parser.parse(date_str)
            except Exception:
                pass
        
        if parsed_dt:
            if parsed_dt.tzinfo is None:
                dt_utc = parsed_dt.replace(tzinfo=timezone.utc)
            else:
                dt_utc = parsed_dt.astimezone(timezone.utc)
        else:
            dt_utc = now_utc
    else:
        dt_utc = now_utc

    # Format in IST
    dt_ist = dt_utc.astimezone(IST)
    ist_str = dt_ist.strftime("%d %b %Y, %I:%M %p IST")
    return dt_utc, ist_str


def get_current_ist_time() -> str:
    """Returns the current timestamp in IST."""
    return datetime.now(IST).strftime("%d %b %Y, %I:%M %p IST")


def get_current_ist_date() -> str:
    """Returns today's date in YYYY-MM-DD for IST."""
    return datetime.now(IST).strftime("%Y-%m-%d")
