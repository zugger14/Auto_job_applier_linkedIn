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

## 🔧 How to Configure (Must Complete Before Running)

> [!IMPORTANT]
> **Mandatory Setup Checklist:**  
> Because credentials and personal data are protected by `.gitignore`, you must set up your local configuration files before starting the bot or dashboard.

### 1. Create Your Configuration Files from Examples
Run the following commands to create your local config files:
```bash
cp config/secrets.example.py config/secrets.py
cp config/personals.example.py config/personals.py
```

### 2. Configure Each File in `/config`

1. **`config/secrets.py`**:
   - Enter your LinkedIn email/username and password (optional; if left blank, you can log in manually in the browser).
   - Set `use_AI = True` and configure your local Ollama endpoint (`llm_api_url = "http://localhost:11434/v1/"`).
   - Specify your model names (`llm_model = "qwen2.5:7b"`, `gmail_ai_model = "qwen3:1.7b"`, `browser_vision_model = "qwen3.5:2b"`).

2. **`config/personals.py`**:
   - Enter your personal details (first name, last name, email, phone number, address, city, state, country, zipcode).
   - Add your LinkedIn profile URL, GitHub profile URL, and portfolio link.

3. **`config/questions.py`**:
   - **Resume Path**: Set `default_resume_path = "your_resume.pdf"` to match the PDF resume you place in the project root.
   - **Screening Answers**: Provide default answers for common application questions (expected salary, current CTC, notice period, work authorization, visa sponsorship).
   - **AI Context (`user_information_all`)**: Paste your full CV/resume text into the `user_information_all` string. The local AI models use this context to answer open-ended and technical application questions.

4. **`config/search.py`**:
   - Set your target job titles (e.g., `DevOps Engineer`, `Cloud Engineer`, `Platform Engineer`, `SRE`, `AI Engineer`).
   - Choose your search location (e.g., `"Worldwide"`, `"United States"`, `"China"`) and work type (`["Remote"]`, `["On-site", "Hybrid"]`).
   - Define blacklist keywords in `bad_words` to skip postings requiring clearances, specific citizenships, or residency restrictions.

5. **`config/settings.py`**:
   - Adjust operational settings (daily application limit, click intervals, stealth mode).

6. **Add Your Resume File**:
   - Place your resume PDF in the repository root directory matching the name configured in `default_resume_path` (e.g., `resume.pdf`).

7. **`credentials.json` (Setting Up Gmail Application Tracker)**:
   The automated Gmail tracker uses Google's official Gmail API (`gmail.readonly`) to inspect incoming job responses. Follow these simple steps to generate your `credentials.json`:

   #### 🔑 Step-by-Step Guide to Get `credentials.json`:
   1. **Open Google Cloud Console**: Go to [console.cloud.google.com](https://console.cloud.google.com/) and log in with your Gmail account.
   2. **Create a New Project**:
      - Click the project dropdown at the top-left > **New Project**.
      - Give it a name (e.g., `Job-Applier-Tracker`) and click **Create**.
   3. **Enable the Gmail API**:
      - In the left sidebar, navigate to **APIs & Services > Library**.
      - In the search bar, type **Gmail API** and click on it.
      - Click the blue **Enable** button.
   4. **Configure the OAuth Consent Screen**:
      - In the left sidebar, click **APIs & Services > OAuth consent screen**.
      - Select **External** and click **Create**.
      - Fill in **App Name** (e.g., `Auto Job Applier`) and enter your email under **User support email** and **Developer contact information**.
      - Click **Save and Continue** on the Scopes screen (no custom scopes needed here).
      - On the **Test users** screen, click **+ Add Users**, enter your Gmail address, and click **Save and Continue**.
   5. **Create OAuth Desktop Client Credentials**:
      - Navigate to **APIs & Services > Credentials**.
      - Click **+ Create Credentials** at the top > select **OAuth client ID**.
      - Set **Application type** to **Desktop app**.
      - Set **Name** to `Desktop Client` and click **Create**.
   6. **Download and Place the File**:
      - A modal will appear confirming creation. Click **Download JSON** (or click the download icon next to your client ID in the credentials table).
      - Rename the downloaded file to exactly `credentials.json`.
      - Move `credentials.json` directly into the root folder of this repository:
        ```bash
        # Place credentials.json in the repository root:
        mv ~/Downloads/client_secret_*.json ./credentials.json
        ```

   #### 🚀 First-Time Sign-In:
   - When you click **Scan Gmail with AI** on the Web Dashboard (or run `python modules/gmail_tracker.py`), a Google login window will automatically pop up in your browser.
   - Choose your account and grant read permissions.
   - A `token.json` file will automatically be created in your directory so you stay authenticated without needing to log in again.

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
