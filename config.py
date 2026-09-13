# Configuration for AI Morning Research Agent
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Base directories
BASE_DIR = Path(__file__).resolve().parent
REPORTS_DIR = BASE_DIR / "reports"
HISTORY_DIR = REPORTS_DIR / "history"
DATA_DIR = BASE_DIR / "data"

REPORTS_DIR.mkdir(parents=True, exist_ok=True)
HISTORY_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)

# File paths
LATEST_REPORT_FILE = REPORTS_DIR / "latest.json"
PREFERENCES_FILE = DATA_DIR / "preferences.json"
SEEN_STORIES_FILE = DATA_DIR / "seen_stories.json"

# Project metadata
PROJECT_NAME = "AI Morning Research Agent"
TIMEZONE = "Asia/Kolkata"
SCHEDULE_TIME = "07:00 AM IST"
TARGET_STORY_COUNT = 5
MAX_BRIEFING_WORDS = 99  # Strict word cap for the combined 5 headlines and explanations

# AI Provider Configuration
# Supported providers: "gemini", "openai", "none" (extractive fallback)
AI_PROVIDER = os.getenv("AI_PROVIDER", "gemini").lower()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
AI_MODEL_NAME = os.getenv("AI_MODEL_NAME", "gemini-1.5-flash" if AI_PROVIDER == "gemini" else "gpt-4o-mini")

# Credibility Score Tiers (0.0 to 1.0)
CREDIBILITY_TIERS = {
    "tier_1_primary": 1.0,    # arXiv, Official AI Labs (OpenAI, Google, DeepMind, Meta), Govt (MeitY, IndiaAI, PIB)
    "tier_2_reputable": 0.85,  # Reuters, Bloomberg, TechCrunch, The Verge, MIT Tech Review, The Hindu, Mint, ET
    "tier_3_coverage": 0.70,   # Inc42, YourStory, Analytics India Magazine, NDTV Tech, VentureBeat
    "tier_4_aggregator": 0.50, # General syndicates, community blogs
    "tier_5_unverified": 0.30  # Unknown, low-trust blogs
}

MIN_CREDIBILITY_THRESHOLD = 0.65  # Stories below this credibility are rejected from the top 5 briefing

# Ranking Weights
RANKING_WEIGHTS = {
    "credibility": 0.25,
    "evidence_strength": 0.20,
    "india_relevance": 0.25,
    "recency": 0.15,
    "trend_momentum": 0.10,
    "user_preference": 0.05
}

# India Relevance Keywords and Weight Multipliers
INDIA_KEYWORDS = [
    "india", "indian", "bengaluru", "bangalore", "delhi", "mumbai", "hyderabad", "chennai", "pune",
    "meity", "indiaai", "iit", "iisc", "bhashini", "sarvam", "krutrim", "tata", "reliance", "jio",
    "infosys", "wipro", "isro", "dpi", "digital public infrastructure", "upi", "indic", "indic llm",
    "semiconductor india", "dronacharya", "bharat", "ai mission", "gujarat dholera", "assam chip",
    "aicte", "ugc ai", "nasscom", "cdac"
]

# High Significance Tech Keywords
TECH_SIGNIFICANCE_KEYWORDS = [
    "breakthrough", "release", "benchmark", "open-source", "weights", "chip", "semiconductor",
    "architecture", "agentic", "quantum", "frontier", "reasoning model", "safety regulation",
    "data center", "energy", "autonomous", "multimodal", "robotics", "healthcare", "agriculture"
]

# Configurable RSS Feeds
# Each feed has: name, url, tier, default_category, is_india_focused
RSS_FEEDS = [
    # --- Tier 1: Primary & Research ---
    {
        "name": "arXiv Computer Science & AI",
        "url": "https://rss.arxiv.org/rss/cs.AI",
        "tier": "tier_1_primary",
        "category": "Research Breakthroughs",
        "is_india_focused": False
    },
    {
        "name": "arXiv Computation and Language",
        "url": "https://rss.arxiv.org/rss/cs.CL",
        "tier": "tier_1_primary",
        "category": "LLMs & NLP",
        "is_india_focused": False
    },
    {
        "name": "MIT Technology Review AI",
        "url": "https://www.technologyreview.com/topic/artificial-intelligence/feed",
        "tier": "tier_1_primary",
        "category": "AI Research & Policy",
        "is_india_focused": False
    },
    {
        "name": "Press Information Bureau (PIB) Science & Tech",
        "url": "https://pib.gov.in/RssMain.aspx?ModId=4&Lang=1",
        "tier": "tier_1_primary",
        "category": "India Policy & Initiatives",
        "is_india_focused": True
    },

    # --- Tier 2: Reputable Tech Journalism ---
    {
        "name": "TechCrunch AI",
        "url": "https://techcrunch.com/category/artificial-intelligence/feed/",
        "tier": "tier_2_reputable",
        "category": "AI Industry & Startups",
        "is_india_focused": False
    },
    {
        "name": "The Verge Tech & AI",
        "url": "https://www.theverge.com/rss/index.xml",
        "tier": "tier_2_reputable",
        "category": "Technology & AI",
        "is_india_focused": False
    },
    {
        "name": "The Hindu - Technology",
        "url": "https://www.thehindu.com/sci-tech/technology/feeder/default.rss",
        "tier": "tier_2_reputable",
        "category": "India Tech & AI",
        "is_india_focused": True
    },
    {
        "name": "Livemint AI & Technology",
        "url": "https://www.livemint.com/rss/technology",
        "tier": "tier_2_reputable",
        "category": "India Tech & Economy",
        "is_india_focused": True
    },
    {
        "name": "Economic Times Tech & AI",
        "url": "https://economictimes.indiatimes.com/tech/rssfeeds/13357270.cms",
        "tier": "tier_2_reputable",
        "category": "India Tech & Business",
        "is_india_focused": True
    },

    # --- Tier 3: Industry & India Tech Specialized ---
    {
        "name": "Analytics India Magazine",
        "url": "https://analyticsindiamag.com/feed/",
        "tier": "tier_3_coverage",
        "category": "India AI & Analytics",
        "is_india_focused": True
    },
    {
        "name": "Inc42 Indian Startups & AI",
        "url": "https://inc42.com/feed/",
        "tier": "tier_3_coverage",
        "category": "Indian Startups & AI",
        "is_india_focused": True
    },
    {
        "name": "VentureBeat AI",
        "url": "https://venturebeat.com/category/ai/feed/",
        "tier": "tier_3_coverage",
        "category": "AI Enterprise & Models",
        "is_india_focused": False
    },

    # --- Google News Targeted Discovery Feeds (RSS) ---
    {
        "name": "Google News: India Artificial Intelligence",
        "url": "https://news.google.com/rss/search?q=India+Artificial+Intelligence+when:2d&hl=en-IN&gl=IN&ceid=IN:en",
        "tier": "tier_2_reputable",
        "category": "India AI Developments",
        "is_india_focused": True
    },
    {
        "name": "Google News: India Semiconductor Chips",
        "url": "https://news.google.com/rss/search?q=India+Semiconductor+AI+Chip+when:3d&hl=en-IN&gl=IN&ceid=IN:en",
        "tier": "tier_2_reputable",
        "category": "Semiconductors & Hardware",
        "is_india_focused": True
    },
    {
        "name": "Google News: AI Breakthroughs & Models",
        "url": "https://news.google.com/rss/search?q=AI+model+breakthrough+release+when:2d&hl=en-US&gl=US&ceid=US:en",
        "tier": "tier_2_reputable",
        "category": "Global AI Releases",
        "is_india_focused": False
    }
]

# Topic Taxonomy
CATEGORIES = [
    "All",
    "AI Models & Releases",
    "India AI & DPI",
    "Semiconductors & Hardware",
    "Robotics & Automation",
    "AI Safety & Governance",
    "Research Breakthroughs",
    "Enterprise & Startups"
]
