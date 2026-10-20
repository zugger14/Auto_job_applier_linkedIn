# LinkedIn AI Auto Job Applier & Tracker 🤖

An autonomous, local-AI-driven job application automation platform. It features an interactive Web Dashboard, Playwright + Vision LLM for applying to external ATS company portals, stealth Selenium for LinkedIn Easy Apply, and automated OAuth2 Gmail status tracking.

> [!NOTE]
> **Upstream Project & Attribution:**  
> This repository is modified and enhanced from the original open-source project by [Sai Vignesh Golla](https://github.com/GodsScion): [GodsScion/Auto_job_applier_linkedIn](https://github.com/GodsScion/Auto_job_applier_linkedIn). We gratefully acknowledge and credit the original project foundation while significantly extending it with local Vision AI, autonomous multi-step external application filling, an interactive web dashboard with real-time log streaming, and inbox tracking.

---

## ✨ Table of Contents
- [Modern Features & Architecture (2026)](#-modern-features--architecture-2026)
- [How to Install](#️-how-to-install)
- [How to Configure](#-how-to-configure)
- [Running the App](#-running-the-app)
- [Local AI Model Roles (Ollama)](#-streamlined-local-ai-model-roles-ollama)
- [Major Updates](#️-major-updates)
- [Upstream Reference & Credits](#️-upstream-reference--attribution)
- [Disclaimer](#-disclaimer)
- [License](#️-license)

---

## 🚀 Modern Features & Architecture (2026)

### 📊 Modern Web Dashboard (`http://localhost:5001`)
* **Real-Time Analytics**: View live metrics on Total Applied, Easy Applied, Externally Applied, Daily Limits, In Review, and Rejections.
* **One-Click Actions**:
  * **Start LinkedIn Bot**: Launches the Selenium stealth Easy Apply engine.
  * **Apply Externally (Playwright)**: Triggers autonomous Playwright external application runner.
  * **Scan Gmail**: Runs automated OAuth2 scan to sync application statuses directly from your inbox.
* **Live Log Stream Modal**: Streams real-time stdout and stderr output from background tasks directly in your browser.
* **Integrated Job History Table**: Filterable and searchable table with direct links to applied jobs and 1-click **Gmail search links** (supporting multi-account indexing `u/0`, `u/1`, etc.).
* **Granular Data Management**: Safely erase monthly data, prune records older than one year, or clear history with confirmation dialogs.

---

### 👁️ Autonomous External Apply Engine (Playwright + Local Vision LLM)
Automates applications on external company portals and ATS platforms (Greenhouse, Lever, Ashby, Workday, BambooHR, etc.):
* **Vision LLM Primary Evaluator (`qwen3.5:2b`)**:
  * Evaluates full-page screenshots on load to classify:
    * `NO_JOB`: Detects expired, closed, filled, or 404 postings immediately and skips redundant retries.
    * `CLICK_APPLY`: Identifies job description landing pages and clicks the Apply button (`Apply on company website`, `Apply Now`, `Apply for this job`, etc.).
    * `CAPTCHA`: Detects Cloudflare Turnstile or human verification challenges and triggers automated clearance.
    * `FORM_READY`: Validates that application fields are active and proceeds with filling.
* **Tab & Popup Tracking**: Automatically detects external links that open in a new tab (`target="_blank"` or `window.open`) and switches active control to the application form.
* **Embedded Iframe Support**: Automatically locates and queries ATS forms embedded inside company `<iframe>` wrappers (e.g. `#grnhse_iframe`).
* **Multi-Step Form Advancement**: Automatically loops through up to 5 multi-step wizard stages (`Next`, `Continue`, `Proceed`, `Review & Submit`, `Save & Next`, `Step 2/3/4`), filling intermediate questions until the final submission button is reached.
* **Post-Submission Verification**: Captures final screenshots and uses the Vision LLM to verify application confirmation notices.

---

### 📬 Gmail Application Status Tracker (Local LLM)
* Secure Google OAuth2 integration with automatic token refreshing.
* Uses lightweight local LLM (`qwen3:1.7b`) to parse incoming company emails, categorizing statuses (`In Review`, `Rejected`, `Interviewing`) and updating candidate CSV databases automatically.

---

### 🧠 Streamlined Local AI Model Roles (Ollama)
| Component | Local Model | Purpose |
| :--- | :--- | :--- |
| **LinkedIn Easy Apply** | `qwen2.5:7b` | Rapid, accurate application question answering |
| **Gmail Tracker** | `qwen3:1.7b` | Ultra-fast email reading and status classification |
| **External Vision Engine** | `qwen3.5:2b` | Sub-12s vision reasoning for browser screenshots & multi-step forms |

*Legacy frameworks (`deepseek`, `crewai`) have been eliminated in favor of direct local Ollama inference.*

---

### 🛠️ Unified Environment & Scripts
* **Single Environment**: Consolidated all virtual environments into a single, clean `./venv` with Playwright browsers pre-installed.
* **One-Click Launch**: Run `./start_job_bot.sh` to start the bot and dashboard instantly.

---

## ⚙️ How to Install

### Prerequisites
1. **Python 3.10+**: Download and install from [python.org](https://www.python.org/).
2. **Google Chrome**: Ensure the latest Google Chrome browser is installed.
3. **Ollama**: Download and run Ollama from [ollama.com](https://ollama.com).

### Step-by-Step Setup
1. **Clone the repository**:
   ```bash
   git clone git@github.com:zugger14/Auto_job_applier_linkedIn.git
   cd Auto_job_applier_linkedIn
   ```

2. **Set up Python Virtual Environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install undetected-chromedriver pyautogui setuptools openai flask-cors flask playwright requests google-auth google-auth-oauthlib google-api-python-client
   ```

4. **Install Playwright Browsers**:
   ```bash
   playwright install chromium
   ```

5. **Pull Local AI Models via Ollama**:
   ```bash
   ollama pull qwen2.5:7b
   ollama pull qwen3:1.7b
   ollama pull qwen3.5:2b
   ```

---

## 🔧 How to Configure

All configurations are located inside the `/config` folder:

1. **`config/personals.py`**:
   - Fill in your personal details (name, email, phone number, address, LinkedIn profile URL, GitHub URL, portfolio, etc.).
2. **`config/questions.py`**:
   - Provide answers to common application screening questions (notice period, expected compensation, work authorization, visa sponsorship, etc.).
   - Set `default_resume_path` to your resume PDF file (e.g. `"Shirish_Maharjan_CV copy.pdf"`).
3. **`config/search.py`**:
   - Set search terms and target job titles (e.g., `DevOps Engineer`, `Cloud Engineer`, `Platform Engineer`, `AI Engineer`).
   - Configure location (e.g., `"Worldwide"` or `"China"`) and work type (`["Remote"]` or `["On-site", "Hybrid"]`).
   - Define blacklist keywords to exclude unwanted postings (clearances, residency restrictions, etc.).
4. **`config/settings.py`**:
   - Configure bot behaviors (daily application limits, delays, stealth mode, keep-screen-awake).
5. **`credentials.json` (Optional for Gmail Tracker)**:
   - Place your Google Cloud OAuth2 credentials file as `credentials.json` in the project root to enable automated Gmail application sync.

---

## 🚀 Running the App

### Recommended: One-Click Startup
```bash
./start_job_bot.sh
```
This script launches the **Web Dashboard** at **`http://localhost:5001`** and prepares the background runners.

### Running Individual Components Manually
* **Web Dashboard**:
  ```bash
  source venv/bin/activate
  python app.py
  ```
  Open `http://localhost:5001` in your browser.

* **LinkedIn Easy Apply Bot**:
  ```bash
  source venv/bin/activate
  python runAiBot.py
  ```

* **External Application Runner**:
  ```bash
  source venv/bin/activate
  python apply_external_jobs.py
  ```

---

## 🗓️ Major Updates

### Oct 20, 2026
- **Modern Web Dashboard**: Real-time stats, interactive Live Execution Console modal with real-time streaming logs for external applications, top-bar "Live Logs" inspector, multi-account Gmail search links (`u/0`, `u/1`), and granular monthly/annual data deletion.
- **Autonomous External Apply Engine**: Powered by Playwright and local Vision LLM (`qwen3.5:2b`) with automatic CAPTCHA detection, new tab/popup handling, iframe ATS support, multi-step progression, and post-submission verification.
- **Automated Gmail Application Tracker**: Secure OAuth2 inbox scanning using local LLM (`qwen3:1.7b`) to automatically detect and classify application confirmations and rejections.
- **Consolidated Local AI Models**: Switched to fast, direct Ollama inference (`qwen2.5:7b` for Easy Apply, `qwen3:1.7b` for Gmail, `qwen3.5:2b` for Vision) and completely removed deprecated frameworks (`deepseek`, `crewai`, legacy stubs).
- **Unified Environment & Persistent Launch**: Consolidated virtual environments into a single `./venv` with Playwright browsers pre-installed, plus persistent dashboard hosting in `./start_job_bot.sh` and `./start_dashboard.sh`.

*For historical changelogs prior to Oct 2026, refer to the [upstream repository](https://github.com/GodsScion/Auto_job_applier_linkedIn).*

---

## 🏛️ Upstream Reference & Attribution

This project is an enhanced branch based on the open-source bot originally created by **Sai Vignesh Golla**:
* **Upstream Repository**: [GodsScion/Auto_job_applier_linkedIn](https://github.com/GodsScion/Auto_job_applier_linkedIn)

---

## 📜 Disclaimer

**This program is for educational purposes only.** By using this tool, you acknowledge and agree that web scraping and automated applications must comply with applicable website policies and terms of service. Usage is at your own risk. The creators and contributors bear no responsibility or liability for any misuse, damages, account suspensions, or legal consequences resulting from its usage.

---

## ⚖️ License

This project is free software licensed under the **GNU Affero General Public License v3.0 (AGPLv3)**.  
Copyright (C) 2024 Sai Vignesh Golla.  
See the [LICENSE](LICENSE) file for complete details.
