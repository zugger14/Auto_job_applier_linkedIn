# 🤖 Auto Job Applier LinkedIn — Features Memory

> **Version:** `26.01.20.5.08` (Modern 2026 Enhanced Edition)  
> **Original Upstream Author:** Sai Vignesh Golla ([GodsScion/Auto_job_applier_linkedIn](https://github.com/GodsScion/Auto_job_applier_linkedIn))  
> **License:** GNU Affero General Public License v3 (AGPLv3)  
> **Last Updated:** 2026-10-20  
> **Local Config Owner:** Shirish Maharjan  

---

## 📋 Table of Contents
- [Core Architecture](#core-architecture)
- [LinkedIn Easy Apply Automation](#linkedin-easy-apply-automation)
- [Job Search & Filtering](#job-search--filtering)
- [AI Integration & Local Model Roles](#ai-integration--local-model-roles)
- [Autonomous External Job Applications (Playwright + Vision LLM)](#autonomous-external-job-applications-playwright--vision-llm)
- [Gmail Application Status Tracker](#gmail-application-status-tracker)
- [Modern Web Dashboard (Flask + Glassmorphism UI)](#modern-web-dashboard-flask--glassmorphism-ui)
- [Configuration System](#configuration-system)
- [Bot Behavior & Safety Settings](#bot-behavior--safety-settings)
- [Logging & History Tracking](#logging--history-tracking)
- [Anti-Bot Detection](#anti-bot-detection)
- [Utility Scripts & Launchers](#utility-scripts--launchers)
- [Current Local Configuration Summary](#current-local-configuration-summary-shirish-maharjan)

---

## 🏗️ Core Architecture

| File | Purpose |
|------|---------|
| `runAiBot.py` | Main LinkedIn Easy Apply bot entrypoint — Selenium stealth scraper and form automator |
| `app.py` | Modern Flask web dashboard (`http://localhost:5001`) with live stats, log streaming modal, and background runner |
| `apply_external_jobs.py` | Batch orchestrator for external company jobs (ATS portals like Greenhouse, Lever, Ashby, Workday, etc.) |
| `modules/external_apply_engine.py` | Playwright-based autonomous engine powered by local Vision LLM (`qwen3.5:2b`) with CAPTCHA detection, tab switching, iframe querying, and multi-step form progression |
| `modules/gmail_tracker.py` | Google OAuth2 integration with local LLM (`qwen3:1.7b`) for automatic application status classification |
| `modules/ai/openaiConnections.py` | Direct Ollama / OpenAI-compatible API connection wrapper |
| `modules/helpers.py` | Shared utilities, date formatting, CSV handling, and logging helpers |
| `modules/clickers_and_finders.py` | Selenium element interaction utilities |
| `modules/validator.py` | Validates all configuration variables before bot startup |
| `start_job_bot.sh` | One-click unified launch script managing dashboard and runner processes |

---

## 🚀 LinkedIn Easy Apply Automation

- **Automated Login**: Uses saved profile credentials with manual fallback if needed.
- **Answers All Question Types**:
  - Text input fields
  - Numeric fields (salary, notice period, years of experience)
  - `<select>` dropdowns and custom styled dropdowns
  - Radio button questions
  - Checkbox / acknowledgement questions
  - Textarea questions (summary, cover letter)
  - Address input fields
  - City/location fields (auto-fills from job posting if `current_city` is empty)
- **Smart Salary Handling**: Auto-converts between annual, monthly, or CTC based on question text.
- **Smart Notice Period Handling**: Converts days to months or weeks based on context.
- **Saves Previous Answers**: Reuses previously answered questions; `overwrite_previous_answers` flag to force re-answer.
- **Resume Upload**: Uploads default PDF resume to each application (`default_resume_path`).
- **Company Follow Toggle**: Configurable option to follow/unfollow companies on submit (`follow_companies`).
- **Pause Before Submit**: Optionally pauses to let the user review before clicking Submit.
- **Daily Limit Enforcement**: `MAX_APPLY_PER_DAY` cap (configured in settings) to prevent LinkedIn restrictions.

---

## 🔍 Job Search & Filtering

### Search Configuration (`config/search.py`)
- **Multiple Search Terms**: Rotates through a list of job titles (e.g., DevOps Engineer, Cloud Engineer, Platform Engineer, SRE, AI Engineer).
- **Switch Number**: Applies `switch_number` jobs per search term before rotating.
- **Search Location**: Fills the "City, state, or zip code" search box (e.g., `"Worldwide"`, `"China"`).
- **Work Types**: Configurable filters (`"Remote"`, `"On-site"`, `"Hybrid"`).

### Smart Job Skipping
- **`bad_words`**: Skips jobs containing disqualifying terms (e.g., `"US Citizen"`, `"clearance required"`, `"No C2C"`, `"EU citizens only"`, `"UK residents only"`).
- **`about_company_bad_words`**: Skips blacklisted companies (e.g., `"Crossover"`).
- **Experience Filter**: Skips jobs requiring more than `current_experience` years.
- **Alternate Sort Cycling**: Alternates between "Most Recent" and "Most Relevant" to discover new postings.

---

## 🤖 AI Integration & Local Model Roles

All AI tasks run via local **Ollama** instances for privacy, zero cost, and low latency:

| Component | Model | Purpose | Details |
| :--- | :--- | :--- | :--- |
| **LinkedIn Easy Apply** | `qwen2.5:7b` | Question answering | Rapid, accurate answers for salary, notice period, and technical screening questions |
| **Gmail Tracker** | `qwen3:1.7b` | Email status parsing | Lightweight, ultra-fast classification of incoming job updates |
| **External Vision Engine** | `qwen3.5:2b` | Visual page reasoning | Evaluates full-page screenshots to detect closed jobs, CAPTCHAs, apply buttons, and multi-step forms |

*Legacy frameworks (`deepseek`, `crewai`) have been fully decommissioned in favor of direct, robust Ollama inference.*

---

## 🌐 Autonomous External Job Applications (Playwright + Vision LLM)

### `apply_external_jobs.py` & `modules/external_apply_engine.py`

- **Batch Processing**: Reads all `Apply Externally` entries from `all_applied_applications_history.csv`.
- **Pre-Form Visual Evaluation (`qwen3.5:2b`)**:
  - Automatically captures full-page viewport screenshots on load.
  - Classifies page state into one of four actions:
    - `NO_JOB`: Postings that are expired, closed, filled, or returning 404/not found. Marks failed immediately without redundant retries.
    - `CLICK_APPLY`: Landing pages with description where an initial "Apply" / "Apply on company website" button must be clicked before form fields appear.
    - `CAPTCHA`: Detects Cloudflare Turnstile or human verification challenges.
    - `FORM_READY`: Validates that application fields are visible and proceeds with form filling.
- **Tab & Popup Handling**: Detects links opening in separate tabs (`target="_blank"` or `window.open`) via `context.pages` and switches active control to the new application tab.
- **Embedded Iframe Support**: Automatically searches and queries ATS forms embedded inside company `<iframe>` wrappers (e.g. `#grnhse_iframe`).
- **Multi-Step Wizard Progression**: Automatically loops through up to 5 multi-step wizard stages (`Next`, `Continue`, `Proceed`, `Review & Submit`, `Save & Next`, `Step 2/3/4`), filling intermediate questions until final submission is reached.
- **Fast Local Vision Reasoning**: Uses `num_predict: 350` and reasoning tag extraction to ensure complete sub-12s vision reasoning without timeouts.
- **Post-Submission Verification**: Captures final screenshots and uses the Vision LLM to verify application submission confirmation.

---

## 📧 Gmail Application Status Tracker

### `modules/gmail_tracker.py`

- **Google OAuth2 Integration**: Authenticates securely using `credentials.json` and cached `token.json` with auto-refresh.
- **Inbox Scanning**: Queries Gmail for application-related messages from the last N days.
- **Local LLM Parsing**: Uses `qwen3:1.7b` to extract company name and status (`In Review`, `Interview`, `Rejected`).
- **CSV Status Synchronization**: Automatically updates `all_applied_applications_history.csv` with updated statuses.
- **Priority Progression**: Status only advances forward (Rejected > Interview > In Review) and never regresses.

---

## 🖥️ Modern Web Dashboard (Flask + Glassmorphism UI)

### `app.py` — runs at `http://localhost:5001`

- **Real-Time Analytics Grid**:
  - Total Applications
  - LinkedIn Easy Apply Count
  - External Applications Count
  - Daily Limit Status
  - In Review Count
  - Rejected Count
- **One-Click Action Triggers**:
  - `Start LinkedIn Bot`: Launches `runAiBot.py` in the background.
  - `Apply Externally`: Launches `apply_external_jobs.py` in the background.
  - `Scan Gmail`: Triggers `gmail_tracker.py` to sync statuses.
- **Live Log Stream Modal**:
  - Streams real-time stdout and stderr output from background tasks via Server-Sent Events (`/logs/stream`).
  - Auto-scrolls and displays formatted log output directly in the browser.
- **Job History Table**:
  - Searchable, filterable table of all applications.
  - Direct links to job listings and external ATS URLs.
  - **1-Click Gmail Search Links**: Direct multi-account Gmail queries (`u/0`, `u/1`, etc.) tailored to each specific company name.
- **Granular Data Reset Controls**:
  - Confirmation modal offering choices:
    - Clear Current Month
    - Clear Previous Month
    - Delete Records Older than 1 Year
    - Full Reset

---

## ⚙️ Configuration System

All user configuration files reside in `config/`:

| File | Configuration Purpose |
|------|-----------------------|
| `personals.py` | Candidate profile: name, email, phone, city, address, LinkedIn, GitHub, portfolio |
| `questions.py` | Resume path (`default_resume_path`), salary, notice period, work authorization, visa sponsorship, full CV text |
| `search.py` | Target job titles, locations (`"Worldwide"`, `"China"`), work types (`["Remote"]`), blacklist keywords |
| `secrets.py` | LinkedIn credentials, LLM API endpoint (`http://localhost:11434/v1`), model names |
| `settings.py` | Stealth mode, delay intervals, daily application caps, headless toggles |

---

## 🛡️ Bot Behavior & Safety Settings

| Setting | Value / Purpose |
|---------|-----------------|
| `stealth_mode = True` | Uses Undetected Chromedriver to bypass bot detection |
| `run_in_background = False` | Allows visible monitoring in browser window |
| `safe_mode = True` | Uses dedicated Chrome profile to avoid multi-profile conflicts |
| `keep_screen_awake = True` | Prevents operating system sleep during application batches |
| `click_gap = 5` | Randomized delays between clicks to mimic human behavior |
| `MAX_APPLY_PER_DAY = 10` | Daily LinkedIn application limit to protect account reputation |

---

## 📊 Logging & History Tracking

- **Applied Jobs CSV**: `all excels/all_applied_applications_history.csv`
  - Columns: `Job ID`, `Title`, `Company`, `HR Name`, `HR Link`, `Job Link`, `External Job link`, `Date Applied`, `Status`, `Failed Attempts`
- **Failed Jobs CSV**: `all excels/all_failed_applications_history.csv`
- **Session Logs**: Timestamped execution logs stored in `logs/`
- **External Application Logs & Screenshots**:
  - Form filling logs: `logs/external_applications/`
  - Viewport screenshots: Captured before, during, and after submission for Vision LLM auditing
- **Daily Counters**: `monitor_counts.json` tracking daily application quotas

---

## 🕵️ Anti-Bot Detection

- **Undetected Chromedriver**: Eliminates automated flags from standard Selenium webdrivers.
- **Randomized Delays**: Human-like pacing across page transitions and input keystrokes.
- **Playwright Stealth Attributes**: Uses custom viewport sizing and realistic user-agent headers.
- **Independent Chrome Windows**: Allows normal browser usage while the bot operates in a separate session.

---

## 🛠️ Utility Scripts & Launchers

| Script | Purpose |
|--------|---------|
| `./start_job_bot.sh` | Main all-in-one launcher (activates `./venv`, starts dashboard, and readies bot) |
| `./start_dashboard.sh` | Starts the Flask Web Dashboard on port 5001 |
| `./start_job.sh` | Starts the LinkedIn Easy Apply Selenium bot |
| `./start_external_applications.sh` | Starts the Playwright external application engine |
| `clear_dashboard_data.py` | CLI utility for resetting application history |
| `reset_csv.py` | CLI utility for recreating CSV files with clean headers |

---

## 🔑 Current Local Configuration Summary (Shirish Maharjan)

| Setting | Configured Value |
|---------|------------------|
| **Target Roles** | DevOps Engineer, Platform Engineer, Infrastructure Engineer, Cloud Engineer, SRE, AI Engineer, Linux Engineer |
| **Search Scope** | Worldwide Remote (with optional China on-site switch) |
| **Easy Apply AI Model** | `qwen2.5:7b` (local Ollama) |
| **Gmail Tracker AI Model** | `qwen3:1.7b` (local Ollama) |
| **External Vision AI Model** | `qwen3.5:2b` (local Ollama) |
| **Candidate Experience** | 5 years (`did_masters = True`) |
| **Default Resume** | `Shirish_Maharjan_CV copy.pdf` |
| **Python Environment** | Unified `./venv` with Playwright Chromium |
| **Web Dashboard** | `http://localhost:5001` |
