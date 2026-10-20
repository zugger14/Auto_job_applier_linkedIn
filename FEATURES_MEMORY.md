# 🤖 Auto Job Applier LinkedIn — Features Memory

> **Version:** `26.01.20.5.08`  
> **Author:** Sai Vignesh Golla  
> **License:** GNU Affero General Public License v3  
> **Last Updated:** 2026-10-20  
> **Local Config Owner:** Shirish Maharjan

---

## 📋 Table of Contents
- [Core Architecture](#core-architecture)
- [LinkedIn Easy Apply Automation](#linkedin-easy-apply-automation)
- [Job Search & Filtering](#job-search--filtering)
- [AI Integration](#ai-integration)
- [External Job Applications](#external-job-applications)
- [Gmail Application Status Tracker](#gmail-application-status-tracker)
- [Web Dashboard (Flask)](#web-dashboard-flask)
- [Configuration System](#configuration-system)
- [Bot Behavior & Safety Settings](#bot-behavior--safety-settings)
- [Logging & History Tracking](#logging--history-tracking)
- [Anti-Bot Detection](#anti-bot-detection)
- [Utility Scripts](#utility-scripts)
- [Shell Launch Scripts](#shell-launch-scripts)
- [In-Development / Upcoming Features](#in-development--upcoming-features)

---

## 🏗️ Core Architecture

| File | Purpose |
|------|---------|
| `runAiBot.py` | Main bot entrypoint — Selenium-based LinkedIn scraper and Easy Apply automator |
| `app.py` | Flask web dashboard for viewing applied jobs history |
| `apply_external_jobs.py` | Batch processor for external (non-Easy Apply) job links |
| `modules/external_apply_engine.py` | Intelligent Playwright engine for external form filling |
| `modules/crewai_agent.py` | Compatibility alias to `modules/external_apply_engine.py` |
| `modules/gmail_tracker.py` | Gmail OAuth2 integration — AI-powered email parser for application status updates |
| `modules/ai/` | Multi-provider AI connections (OpenAI, DeepSeek, Gemini) |
| `modules/helpers.py` | Shared utilities, logging helpers |
| `modules/clickers_and_finders.py` | Selenium element interaction utilities |
| `modules/validator.py` | Validates all config variables before bot starts |

---

## 🚀 LinkedIn Easy Apply Automation

- **Automated login** using saved credentials or manual login fallback
- **Answers all question types** in Easy Apply forms:
  - Text input fields
  - Numeric fields (salary, notice period, years of experience)
  - `<select>` dropdowns
  - Radio button questions
  - Checkbox / acknowledgement questions
  - Textarea questions (summary, cover letter)
  - Address input fields
  - City/location fields (auto-fills from job posting if `current_city` is empty)
- **Smart salary handling**: Auto-converts to lakhs, monthly, yearly as question requires
- **Smart notice period handling**: Converts days to months or weeks based on question context
- **Saves previous answers**: Reuses previously answered questions; `overwrite_previous_answers` flag to force re-answer
- **Resume upload**: Uploads a default PDF resume to each application
- **Company follow toggle**: Configurable option to follow/unfollow companies on submit (`follow_companies`)
- **Pause before submit**: Optionally pauses to let you review before clicking Submit
- **Pause at failed question**: Optionally pauses if the bot can't answer a question, instead of randomly guessing
- **Random fallback answers**: If pausing is disabled, bot guesses randomly and logs the question
- **Discard application**: Supports discarding from the pause-at-submission dialog
- Can apply **100+ jobs in under 1 hour**
- **Daily limit enforcement**: `MAX_APPLY_PER_DAY` cap (currently set to 10) to avoid LinkedIn bans

---

## 🔍 Job Search & Filtering

### Search Configuration (`config/search.py`)

- **Multiple search terms**: Rotates through a list of job titles (e.g., DevOps Engineer, SRE, AI Engineer)
- **Switch number**: Applies `switch_number` jobs per search term before rotating
- **Randomize search order**: Optional shuffling of search term list
- **Search location**: Fills the "City, state, or zip code" field (e.g., "Worldwide", "United States")

### LinkedIn Filters

| Filter | Description |
|--------|-------------|
| `sort_by` | "Most recent" or "Most relevant" |
| `date_posted` | Any time / Past month / Past week / Past 24 hours |
| `salary` | Minimum salary filter ($40K–$200K+) |
| `easy_apply_only` | True/False |
| `experience_level` | Multiple select: Internship, Entry, Mid-Senior, Director, Executive |
| `job_type` | Multiple select: Full-time, Part-time, Contract, etc. |
| `on_site` | Multiple select: On-site, Remote, Hybrid |
| `companies` | Target specific companies |
| `location` | Additional location filters |
| `industry` | Industry filters |
| `job_function` | Job function filters |
| `job_titles` | Specific title filters |
| `benefits` | Benefits filters |
| `commitments` | Commitment filters |
| `under_10_applicants` | Filter for low-competition jobs |
| `in_your_network` | Filter for network-adjacent jobs |
| `fair_chance_employer` | Filter for fair-chance employers |

### Smart Job Skipping

- **`about_company_bad_words`**: Skip companies whose "About" section contains blacklisted words (e.g., "Crossover", "Staffing")
- **`about_company_good_words`**: Whitelist exceptions to the above blacklist
- **`bad_words`**: Skip jobs whose description contains specific phrases (e.g., "US Citizen", "clearance required", "No C2C")
- **Experience filter**: Skips jobs requiring more than `current_experience` years
- **Security clearance filter**: Skips clearance-required jobs if `security_clearance = False`
- **Masters filter**: Applies `did_masters` logic to appropriately handle masters-level job descriptions
- **Alternate sort cycling**: Alternates between Most Recent and Most Relevant to discover more jobs
- **Date posted cycling**: Cycles through date filters; stops at 24h when `stop_date_cycle_at_24hr = True`
- **Pause after filters**: Allows manual filter adjustment before bot proceeds

---

## 🤖 AI Integration

### Supported AI Providers (`config/secrets.py`)

| Provider | Module |
|----------|--------|
| OpenAI (GPT models) | `modules/ai/openaiConnections.py` |
| OpenAI-compatible (Ollama, LM Studio, Jan) | Same, via `llm_api_url` |
| Google Gemini | `modules/ai/geminiConnections.py` |

**Current local config**:
- Main Bot Easy Apply Answering: `qwen2.5:7b` via local Ollama at `http://localhost:11434/v1/`
- Gmail Status Tracking: `qwen3:1.7b` via local Ollama at `http://localhost:11434/v1/`

### AI Capabilities

- **Skill extraction**: Extracts required skills from job descriptions (`ai_extract_skills`)
- **Question answering**: AI answers unknown application form questions (`ai_answer_question`)
- **Stream output toggle**: Configurable streaming vs. batch response
- **Error alerts**: Optional pop-up dialogs when AI connection fails (`showAiErrorAlerts`)
- **Prompts**: Centralized prompt templates in `modules/ai/prompts.py`
- **Local LLM support**: Full compatibility with Ollama, LM Studio, llama.cpp, Jan

---

## 🌐 External Job Applications

### `apply_external_jobs.py` + `modules/external_apply_engine.py`

- **Batch processing**: Reads all "Apply Externally" links from the CSV history file
- **Intelligent Playwright Engine**: Autonomously parses external ATS portals (Greenhouse, Ashby, Lever, Teamtailor, etc.)
- **Form filling**: Passes full CV/resume text to the AI agent to fill every form field
- **URL reachability check**: Skips dead/unreachable URLs before attempting
- **Retry mechanism**: Up to 3 attempts per external job with exponential backoff (2^n seconds)
- **Failed attempts tracking**: Logs failure count per job in CSV; skips jobs exceeding `MAX_RETRIES = 3`
- **Daily limit**: Max 20 external applications per day via `monitor_counts.json`
- **Human escalation**: AI calls `ask_human_for_help` if truly confused; auto-fills "N/A" as placeholder
- **Headful/headless mode**: `--headful` flag for debugging in browser
- **Application logs**: Each session saves a detailed log under `logs/external_applications/`
- **Status update**: Marks jobs as `Externally Applied` in CSV upon success

---

## 📧 Gmail Application Status Tracker

### `modules/gmail_tracker.py`

- **OAuth2 Gmail integration**: Uses Google API with `credentials.json` + `token.json`
- **Email scanning**: Queries Gmail for job-related emails from last N days
- **AI-powered email analysis**: Sends email subject + body to LLM to classify status
- **Status categories**: `In Review`, `Interview`, `Rejected`, `Unknown`
- **LinkedIn URL parsing**: Reads tracking URLs in emails to detect status (`application_rejected`, `application_viewed`)
- **CSV status update**: Updates the applications history CSV with the detected status
- **Fallback matching**: If AI fails to extract company name, falls back to direct text search in email
- **Priority ordering**: Status only advances (Rejected > Interview > In Review), never regresses
- **Gemini rate-limiting**: Automatically adds 4.5s sleep to respect 15 RPM Gemini quota
- **CLI usage**: `python modules/gmail_tracker.py --days 7` to scan last 7 days

---

## 🖥️ Web Dashboard (Flask)

### `app.py` — runs at `http://localhost:5001`

- **Applied jobs history view**: Displays all applications from `all_applied_applications_history.csv`
- **Job status display**: Shows Smart status — `Applied`, `Apply Externally`, `External Site`, `Rejected`
- **Job details**: Job ID, Title, Company, HR Name, HR Link, Job Link, External Link, Date Applied
- **Update date applied**: `PUT /applied-jobs/<job_id>` endpoint to manually update date
- **REST API**: JSON endpoints (`/applied-jobs` GET, `/applied-jobs/<id>` PUT) for external integrations
- **Frontend template**: `templates/index.html` — web UI for the dashboard
- **CORS enabled**: Flask-CORS for cross-origin access
- **Error handling**: Returns `404` for missing CSV, `500` for unexpected errors

---

## ⚙️ Configuration System

All configuration lives in `config/`:

| File | What It Configures |
|------|--------------------|
| `personals.py` | Name, phone, city, address, ethnicity, gender, disability, veteran status |
| `questions.py` | Resume path, experience, visa, salary, CTC, notice period, cover letter, summary, `user_information_all` (full CV text for AI) |
| `search.py` | Search terms, filters, bad words, experience threshold |
| `secrets.py` | LinkedIn credentials, AI provider, API key, model name, LLM URL |
| `settings.py` | Bot behavior toggles, file paths, click intervals |

### Validation
- All config variables are validated at startup by `modules/validator.py`
- Type and value checks prevent misconfiguration from crashing mid-run

---

## 🛡️ Bot Behavior & Safety Settings

| Setting | Description |
|---------|-------------|
| `stealth_mode = True` | Uses Undetected Chromedriver to bypass bot detection |
| `run_in_background = False` | Headless Chrome mode (disables pause options when True) |
| `safe_mode = True` | Opens Chrome in guest profile (avoids multi-profile conflicts) |
| `keep_screen_awake = True` | Prevents PC from sleeping during run |
| `smooth_scroll = False` | Disables smooth scroll for performance |
| `disable_extensions = False` | Can disable browser extensions |
| `close_tabs = False` | Keeps external application tabs open |
| `click_gap = 5` | Max seconds between clicks (randomized to simulate human behavior) |
| `run_non_stop = False` | Runs continuously until manually stopped (Beta) |
| `alternate_sortby = True` | Alternates search sort method each cycle |
| `cycle_date_posted = True` | Cycles through date filters each round |
| `pause_after_filters = False` | Pauses after applying search filters for manual review |

---

## 📊 Logging & History Tracking

- **Applied jobs CSV**: `all excels/all_applied_applications_history.csv`  
  Fields: `Job ID`, `Title`, `Company`, `HR Name`, `HR Link`, `Job Link`, `External Job link`, `Date Applied`, `Status`, `Failed Attempts`
- **Failed jobs CSV**: `all excels/all_failed_applications_history.csv`
- **Session logs**: Saved to `logs/` directory with timestamps
- **External app logs**: Saved to `logs/external_applications/<url>.txt`
- **Daily counters**: `monitor_counts.json` tracks LinkedIn + external application counts per day
- **CSV field size limit**: Set to 1MB to handle long job descriptions without errors

---

## 🕵️ Anti-Bot Detection

- **Undetected Chromedriver** (`stealth_mode`): Evades LinkedIn's bot detection
- **Randomized click intervals**: Simulates human-like delays between actions
- **Guest profile mode** (`safe_mode`): Avoids fingerprint conflicts from personal profiles
- **PyAutoGUI failsafe disabled**: `pyautogui.FAILSAFE = False` for unattended background runs
- **Simultaneous Chrome usage**: Jan 2026 update allows running Chrome normally while bot applies in a new window

---

## 🛠️ Utility Scripts

| Script | Purpose |
|--------|---------|
| `clear_dashboard_data.py` | Clears all applied jobs history data |
| `reset_csv.py` | Resets the applications CSV file |

---

## 🐚 Shell Launch Scripts

| Script | Purpose |
|--------|---------|
| `start_job.sh` | Starts the main LinkedIn bot |
| `start_job_bot.sh` | Extended bot startup with logging |
| `start_dashboard.sh` | Starts the Flask web dashboard |
| `start_external_applications.sh` | Starts the external jobs applier |

---

## 🔮 In-Development / Upcoming Features

| Feature | Status |
|---------|--------|
| Resume generator (AI-tailored resumes per job) | `In Development` — `generated_resume_path` placeholder exists |
| HR connection requests with custom message | Commented out in `settings.py` |
| Currency tag for salary answers | `In Development` |
| About company extraction for AI context | `TODO` in `runAiBot.py` |
| ChatGPT-based resume building via web | Experimental — CloudFlare blocked |

---

## 🔑 Current Local Configuration Summary (Shirish Maharjan)

| Setting | Value |
|---------|-------|
| **Job Titles Searched** | DevOps, Platform, Infrastructure, Cloud, SRE, AI Engineer, Linux Engineer |
| **Location** | Worldwide, Remote only |
| **AI Provider** | OpenAI-compatible (`deepseek-r1:14b` via Ollama local) |
| **Experience** | 5 years / `did_masters = True` |
| **Daily Apply Limit** | 10 LinkedIn Easy Apply |
| **Stealth Mode** | Enabled |
| **Background Mode** | Disabled (visible Chrome) |
| **Gmail Tracker** | Configured (credentials.json + token.json present) |
| **Bad Words Filter** | US Citizen, No C2C, clearance required, EU/UK/US residents only |
| **Company Blacklist** | Crossover |

---

*This file is auto-generated from codebase analysis. Update after major feature additions.*
