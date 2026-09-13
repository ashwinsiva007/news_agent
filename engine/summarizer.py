"""
Summarizer Engine: Produces ultra-concise summaries answering "What happened & Why it matters to India",
with strict Python-enforced <= 99 words limit across all 5 stories.
"""
import os
import re
import json
import logging
import requests
from typing import List, Dict, Any, Tuple, Optional
from config import (
    AI_PROVIDER, GEMINI_API_KEY, OPENAI_API_KEY, OPENAI_BASE_URL,
    AI_MODEL_NAME, MAX_BRIEFING_WORDS
)

logger = logging.getLogger(__name__)


def count_words(text: str) -> int:
    """
    Counts words in a string according to Python whitespace splitting rules.
    """
    if not text:
        return 0
    # Clean non-alphanumeric punctuation boundaries if attached
    cleaned = re.sub(r"[^\w\s-]", " ", text)
    tokens = [t for t in cleaned.strip().split() if t]
    return len(tokens)


def count_briefing_words(stories: List[Dict[str, Any]]) -> int:
    """
    Counts total words across all headlines and explanations in the briefing.
    Excludes URLs, publisher names, and metadata.
    """
    total = 0
    for s in stories:
        h = s.get("headline", "")
        exp = s.get("explanation", "")
        total += count_words(h) + count_words(exp)
    return total


def rule_based_extract_summary(story: Dict[str, Any]) -> str:
    """
    Deterministic rule-based summary generator when no AI API is available.
    Answers: What happened and why it matters to India concisely.
    """
    desc = story.get("description", "").strip()
    headline = story.get("headline", "").strip()
    matched_india = story.get("matched_india_keywords", [])
    
    # Extract clean text from description or fallback to headline
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", desc) if len(s.strip()) > 15]
    first_sent = sentences[0] if sentences else headline
    
    # Strip excessively long introductory clauses
    first_sent = re.sub(r"^(According to|In a recent|As per|Reports state that|Earlier:?|New report:?)\s*", "", first_sent, flags=re.IGNORECASE)
    
    # Formulate India relevance context
    if matched_india:
        primary_kw = matched_india[0].title()
        india_clause = f"Key impact for India's {primary_kw} sector."
    elif story.get("is_india_focused", False):
        india_clause = "Expands domestic tech infrastructure."
    else:
        india_clause = "Guides Indian AI research & adoption."

    # Keep initial explanation compact (~8-10 words)
    words = first_sent.split()
    if len(words) > 8:
        concise_event = " ".join(words[:8]).rstrip(".,;:-") + "."
    else:
        concise_event = first_sent.rstrip(".,;:-") + "."
        
    explanation = f"{concise_event} {india_clause}"
    return explanation


def call_gemini_api(prompt: str, api_key: str, model_name: str) -> Optional[str]:
    """Calls Gemini REST API directly without heavy external dependencies."""
    # Support model names like gemini-1.5-flash or gemini-2.0-flash
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.2,
            "maxOutputTokens": 400
        }
    }
    try:
        resp = requests.post(url, json=payload, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            candidates = data.get("candidates", [])
            if candidates:
                return candidates[0]["content"]["parts"][0]["text"]
        else:
            logger.warning(f"Gemini API returned status {resp.status_code}: {resp.text}")
    except Exception as e:
        logger.error(f"Gemini API error: {e}")
    return None


def call_openai_api(prompt: str, api_key: str, base_url: str, model_name: str) -> Optional[str]:
    """Calls OpenAI-compatible REST API directly."""
    url = f"{base_url.rstrip('/')}/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": "You are a concise AI research intelligence writer. Output valid JSON only."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.2,
        "max_tokens": 400
    }
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            return data["choices"][0]["message"]["content"]
        else:
            logger.warning(f"OpenAI API returned status {resp.status_code}: {resp.text}")
    except Exception as e:
        logger.error(f"OpenAI API error: {e}")
    return None


def generate_ai_summaries(stories: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Attempts to generate concise headlines and explanations via AI provider.
    Falls back to rule-based generation if API is unavailable or fails.
    """
    story_inputs = []
    for idx, s in enumerate(stories):
        story_inputs.append({
            "id": idx,
            "headline": s.get("headline"),
            "description": s.get("description", "")[:200],
            "india_focus": s.get("is_india_focused", False),
            "matched_keywords": s.get("matched_india_keywords", [])
        })

    prompt = f"""You are generating a daily 5-story AI intelligence brief for an Indian engineering student.
For each story below, produce:
1. "headline": ultra-short punchy headline (3-5 words max)
2. "explanation": 1 sentence explaining what happened and why it matters to India (8-12 words max).

CRITICAL REQUIREMENT:
The TOTAL combined words of all {len(stories)} headlines and explanations MUST be LESS than {MAX_BRIEFING_WORDS} words (target ~80 words total).

Input stories:
{json.dumps(story_inputs, indent=2)}

Return ONLY a valid JSON list of objects with "id", "headline", and "explanation".
"""

    raw_response = None
    if AI_PROVIDER == "gemini" and GEMINI_API_KEY:
        raw_response = call_gemini_api(prompt, GEMINI_API_KEY, AI_MODEL_NAME)
    elif AI_PROVIDER == "openai" and OPENAI_API_KEY:
        raw_response = call_openai_api(prompt, OPENAI_API_KEY, OPENAI_BASE_URL, AI_MODEL_NAME)

    # Try parsing AI response
    if raw_response:
        try:
            # Extract JSON from code blocks if present
            cleaned_json = raw_response.strip()
            if "```json" in cleaned_json:
                cleaned_json = cleaned_json.split("```json")[1].split("```")[0].strip()
            elif "```" in cleaned_json:
                cleaned_json = cleaned_json.split("```")[1].split("```")[0].strip()
            
            parsed_list = json.loads(cleaned_json)
            if isinstance(parsed_list, list) and len(parsed_list) == len(stories):
                updated_stories = []
                for idx, s in enumerate(stories):
                    ai_item = parsed_list[idx]
                    s_copy = s.copy()
                    s_copy["headline"] = ai_item.get("headline", s["headline"])
                    s_copy["explanation"] = ai_item.get("explanation", rule_based_extract_summary(s))
                    s_copy["summary_method"] = f"AI ({AI_PROVIDER})"
                    updated_stories.append(s_copy)
                return updated_stories
        except Exception as e:
            logger.warning(f"Failed to parse AI response, falling back to rule-based: {e}")

    # Fallback to rule-based
    updated_stories = []
    for s in stories:
        s_copy = s.copy()
        s_copy["explanation"] = rule_based_extract_summary(s)
        s_copy["summary_method"] = "Rule-based Extractive"
        updated_stories.append(s_copy)

    return updated_stories


def enforce_word_limit(stories: List[Dict[str, Any]], max_words: int = MAX_BRIEFING_WORDS) -> Tuple[List[Dict[str, Any]], int]:
    """
    Guarantees that the combined word count of all headlines and explanations
    is strictly <= max_words (99 words).
    If exceeding, applies deterministic compression and truncation.
    """
    if not stories:
        return [], 0

    current_total = count_briefing_words(stories)
    if current_total <= max_words:
        return stories, current_total

    # Need compression
    compressed_stories = [s.copy() for s in stories]
    target_words_per_story = max_words // len(compressed_stories)

    # Pass 1: Shorten explanations
    for s in compressed_stories:
        exp_words = s.get("explanation", "").split()
        hl_words = s.get("headline", "").split()
        
        allowed_exp_words = max(5, target_words_per_story - len(hl_words))
        if len(exp_words) > allowed_exp_words:
            s["explanation"] = " ".join(exp_words[:allowed_exp_words]).rstrip(",;") + "."

    current_total = count_briefing_words(compressed_stories)
    
    # Pass 2: If still exceeding, shorten headlines as well
    if current_total > max_words:
        for s in compressed_stories:
            hl_words = s.get("headline", "").split()
            if len(hl_words) > 5:
                s["headline"] = " ".join(hl_words[:5])
                
            exp_words = s.get("explanation", "").split()
            if len(exp_words) > 8:
                s["explanation"] = " ".join(exp_words[:8]).rstrip(",;") + "."

    # Final hard limit check
    current_total = count_briefing_words(compressed_stories)
    while current_total > max_words:
        # Trim from longest explanation
        longest_idx = max(range(len(compressed_stories)), key=lambda i: len(compressed_stories[i]["explanation"].split()))
        words = compressed_stories[longest_idx]["explanation"].split()
        if len(words) > 3:
            compressed_stories[longest_idx]["explanation"] = " ".join(words[:-1]).rstrip(",;") + "."
        else:
            break
        current_total = count_briefing_words(compressed_stories)

    return compressed_stories, current_total
