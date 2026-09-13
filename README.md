# 🌅 AI Morning Research Agent

[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.35+-FF4B4B.svg)](https://streamlit.io/)
[![Schedule](https://img.shields.io/badge/Schedule-07%3A00%20AM%20IST-brightgreen.svg)]()
[![Tests](https://img.shields.io/badge/Tests-25%20Passed-success.svg)]()

> A personal AI-powered morning research intelligence agent built for engineering students and tech professionals. Automatically scours top global AI research repositories, reputable tech journalism, and Indian tech publications, verifies claims, removes duplicates, filters marketing hype, ranks developments with an **India-first perspective**, and delivers an **ultra-concise 5-story briefing under 99 words**.

---

## 🌟 Key Features

1. **8-Stage Autonomous Pipeline**:
   - **Discovery**: Collects from top AI feeds (arXiv, PIB India, MIT Tech Review, TechCrunch, The Verge, Livemint, The Hindu, Analytics India Mag, Inc42, Google News RSS).
   - **Normalization**: Cleans tracking parameters from URLs, strips media suffixes, and standardizes timestamps to Indian Standard Time (IST).
   - **Claim Extraction**: Isolates key factual developments from noise.
   - **Verification & Hierarchy**: Evaluates primary sources vs. secondary reporting and gates out unverified rumors.
   - **Event Deduplication**: Clusters near-duplicates across different publishers under a single canonical story with corroboration links.
   - **Trend Momentum**: Quantifies multi-source publisher coverage to detect genuinely rising trends.
   - **India-First Transparent Ranking**: Multi-factor scoring weighting domestic semiconductor fab progress, DPI, Indic LLMs, startup initiatives, and global frontier breakthroughs.
   - **Strict Word Limit Enforcement**: Rigorously verifies that total briefing words across all 5 headlines and explanations are **strictly $\le 99$ words**.
2. **Interactive Streamlit Web Dashboard**:
   - Responsive cards with verification badges, direct source links, and instant feedback buttons.
   - Historical date archive explorer.
   - Transparent **Research Inspector** detailing candidate stories, scoring matrix, and duplicate clusters.
   - Dynamic **Learning & Memory System** where feedback tunes future topic weights.
3. **Daily Cloud Automation**:
   - Automated via GitHub Actions at **7:00 AM Indian Standard Time** (`30 1 * * *` UTC).
   - Ready for one-click deployment to **Streamlit Community Cloud**.
4. **Flexible AI & Offline Mode**:
   - Supports Google Gemini API (free tier) and OpenAI API.
   - **100% functional in free rule-based extractive mode** if no API key is provided.

---

## 📂 Project Structure

```
ai-morning-agent/
├── app.py                     # Streamlit interactive web dashboard
├── research.py                # Research engine & CLI runner
├── config.py                  # Sources, topics, scoring weights, API settings
├── requirements.txt           # Python package dependencies
├── README.md                  # Beginner-friendly guide and documentation
├── .gitignore                 # Version control ignores
├── .env.example               # Template for environment variables
├── engine/                    # Modular research engine
│   ├── collector.py           # RSS feed parsing & lookback window filtering
│   ├── normalizer.py          # URL cleaning, headline cleaning, IST date parsing
│   ├── deduplicator.py        # Exact hash & near-duplicate event clustering
│   ├── verifier.py            # Evidence hierarchy & credibility eligibility gate
│   ├── ranker.py              # India relevance & multi-factor scoring
│   ├── summarizer.py          # AI synthesis & strict <=99 words loop
│   └── storage.py             # Safe atomic JSON persistence & memory
├── reports/
│   ├── latest.json            # Active briefing report
│   └── history/               # Daily report archive (YYYY-MM-DD.json)
├── data/
│   ├── preferences.json       # User learning preferences and topic weights
│   └── seen_stories.json      # Memory tracking to prevent duplicate coverage
├── tests/                     # Comprehensive test suite (25 tests)
│   ├── test_collector.py
│   ├── test_deduplication.py
│   ├── test_ranking.py
│   ├── test_verifier.py
│   ├── test_word_count.py
│   ├── test_storage.py
│   └── test_report.py
└── .github/
    └── workflows/
        └── daily_research.yml # 7:00 AM IST daily GitHub Action
```

---

## 🚀 Quickstart Guide (Windows PowerShell)

Follow these simple step-by-step instructions to run the application on your computer.

### Step 1: Open the Project Directory
Open **PowerShell** or VS Code in your project folder:
```powershell
cd b:\antigravity\agent
```

### Step 2: Create and Activate a Virtual Environment
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```
*(If PowerShell displays an execution policy error, run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned` first)*.

### Step 3: Install Required Dependencies
```powershell
pip install -r requirements.txt
```

### Step 4: Configure API Key (Optional)
If you wish to use Google Gemini AI summaries, create a `.env` file:
```powershell
Copy-Item .env.example .env
```
Open `.env` and add your free Gemini API key:
```env
AI_PROVIDER=gemini
GEMINI_API_KEY=your_gemini_api_key_here
```
> **Note**: If you don't provide an API key, the system automatically uses the built-in deterministic extractive engine at zero cost!

---

## 💻 Running the Application

### 1. Launch the Streamlit Web Dashboard
Run the dashboard in your browser:
```powershell
streamlit run app.py
```
Open your browser at **http://localhost:8501**.

### 2. Run the Research Engine Manually via CLI
To fetch the latest news and generate a fresh report directly from the terminal:
```powershell
python research.py --lookback 24
```
Options:
- `--lookback 48`: Expands news search window to 48 hours.
- `--dry-run`: Tests the pipeline without saving to disk.
- `--force`: Forces a fresh refresh.

### 3. Run Automated Unit Tests
To verify all 25 unit tests:
```powershell
pytest -v
```

---

## ⏰ Daily Automation with GitHub Actions

The repository includes a pre-configured GitHub Actions workflow located in `.github/workflows/daily_research.yml`.

### How it Works:
1. Every morning at **01:30 UTC (7:00 AM IST)**, GitHub Actions wakes up a virtual machine.
2. It executes `python research.py --schedule`.
3. It fetches news, verifies claims, and saves `reports/latest.json` and `reports/history/YYYY-MM-DD.json`.
4. It automatically commits and pushes the updated briefing files back to your GitHub repository.
5. Your deployed Streamlit dashboard displays the latest report seamlessly!

### Setting Up on GitHub:
1. Initialize Git and push your repository to GitHub:
   ```powershell
   git init
   git add .
   git commit -m "Initial commit of AI Morning Research Agent"
   git branch -M main
   git remote add origin https://github.com/your-username/ai-morning-agent.git
   git push -u origin main
   ```
2. Enable Workflow Permissions:
   - In your GitHub repository, go to **Settings** -> **Actions** -> **General**.
   - Under **Workflow permissions**, select **"Read and write permissions"** and click **Save**.
3. (Optional) Add API Key Secret:
   - Go to **Settings** -> **Secrets and variables** -> **Actions** -> **New repository secret**.
   - Name: `GEMINI_API_KEY`, Value: `your-api-key`.

---

## 🌐 Deploying to Streamlit Community Cloud (Free)

1. Go to [share.streamlit.io](https://share.streamlit.io/) and log in with your GitHub account.
2. Click **"New app"**.
3. Select your repository: `your-username/ai-morning-agent`.
4. Main file path: `app.py`.
5. Under **Advanced settings** -> **Secrets**, paste any optional environment variables:
   ```toml
   AI_PROVIDER = "gemini"
   GEMINI_API_KEY = "your_gemini_api_key_here"
   ```
6. Click **"Deploy!"**. Your dashboard will be live on a public URL!

---

## ⚙️ Customization & Source Configuration

You can easily adjust the sources, keywords, and weights in [`config.py`](file:///b:/antigravity/agent/config.py):

- **Add a News Feed**: Append an item to `RSS_FEEDS`:
  ```python
  {
      "name": "Custom Tech RSS",
      "url": "https://example.com/rss",
      "tier": "tier_2_reputable",
      "category": "Technology & AI",
      "is_india_focused": True
  }
  ```
- **Adjust India Relevance Keywords**: Add new initiatives or companies to `INDIA_KEYWORDS` in `config.py`.
- **Change the Daily Schedule**: Edit the cron expression in `.github/workflows/daily_research.yml`.

---

## 🛡️ Factual Integrity and Verification Architecture

The agent strictly prevents hallucinations and fake news through:
1. **Credibility Gate**: Excludes sources below the credibility threshold.
2. **Corroboration Multiplier**: Elevates developments confirmed by 2 or more independent news organizations.
3. **Deterministic Extractive Safeguards**: Extracts verified dates and direct URLs from RSS headers.
4. **Python-Enforced Word Count**: Post-generation token counting ensures the combined briefing remains crisp, concise, and under 99 words.
