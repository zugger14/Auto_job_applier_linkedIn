import os
import asyncio
from browser_use.llm.ollama.chat import ChatOllama as BrowserUseChatOllama
from browser_use import Agent as BrowserUseAgent, Controller
from browser_use import browser
from config.secrets import llm_model

# Select a vision-capable Ollama model for Browser-Use
# qwen3.5 (9b/27b) has native vision, tools, and visual grounding for web navigation
VISION_OLLAMA_MODEL = os.environ.get("BROWSER_VISION_MODEL", "qwen3.5:9b")

# Initialize the Ollama model specifically for Browser-Use with vision support
browser_use_llm = BrowserUseChatOllama(
    host="http://localhost:11434",
    model=VISION_OLLAMA_MODEL,
)

# Set up controller to allow the agent to ask the user for help
controller = Controller()

@controller.action("ask_human_for_help")

def ask_human_for_help(question: str) -> str:
    print("\n\a") # Terminal bell sound
    # macOS speech synthesis as an audio cue
    os.system(f'say "The AI needs your input" &')
    # Automatically provide a safe placeholder when the agent is confused
    # This avoids blocking the script when no human input is available.
    placeholder = "N/A"
    print("🤖 Auto‑filled missing info with placeholder: N/A")
    return placeholder


import config.questions as cq
import config.secrets as cs
import config.personals as cp

def get_cv_data(raw_cv_data: str):
    cv = str(raw_cv_data).strip()
    # Build complete candidate profile from config
    profile_info = f"""
Candidate Full Legal Name: {cp.first_name} {cp.middle_name} {cp.last_name}
Email Address: {cs.username}
Phone Number: {cp.phone_number}
Location / City: {cp.current_city}, {cp.state}, {cp.country} (Zipcode: {cp.zipcode})
Street Address: {cp.street}
Ethnicity: {cp.ethnicity}
Gender: {cp.gender}
Disability Status: {cp.disability_status}
Veteran Status: {cp.veteran_status}
LinkedIn: {cq.linkedIn or 'https://www.linkedin.com/in/shirish-maharjan'}
Portfolio / Website: {cq.website or 'https://github.com/shirishmaharjan'}
Years of Experience: {cq.years_of_experience}
Headline: {cq.linkedin_headline}
Summary: {cq.linkedin_summary}
Desired Salary / Rate: {cq.desired_salary} USD
Current CTC: {cq.current_ctc}
Notice Period: {cq.notice_period} days
Visa Sponsorship Required: {cq.require_visa}
US Citizenship: {cq.us_citizenship or 'No / Non-citizen allowed to work'}
Legally Authorized to Work: Yes
"""
    if len(cv) >= 50:
        return f"{profile_info}\n\nAdditional Resume / Experience Details:\n{cv}"
    return profile_info.strip()

async def execute_browser_use(application_link: str, cv_data: str):
    """
    Spins up Playwright via browser-use to navigate to the external ATS and autonomously fill the form.
    """
    
    task_instruction = f"""
You are an autonomous AI job application agent.
Navigate to {application_link}.

YOUR MISSION:
Autonomously analyze the page layout, locate the job application form, decide what each input field requires, fill every field accurately using the candidate's profile, and navigate through all submission steps until completed.

CANDIDATE INFORMATION:
{cv_data}

AUTONOMOUS DECISION-MAKING RULES:
1. Form & Element Detection:
   - Inspect the page to identify text inputs, email, phone, textareas, dropdowns (<select>), checkboxes, radio buttons, and file uploads.
   - If there is an 'Apply', 'Apply Now', 'Apply for this job', or 'Start Application' button, click it first to reveal the form.
   - Intelligently match field labels/placeholders (e.g., 'Full Name', 'Given Name', 'Family Name', 'Phone', 'Location', 'Salary Expectation', 'LinkedIn URL', 'GitHub') to candidate information.

2. Dropdowns and Choices:
   - For dropdowns (e.g., country, work authorization, gender, veteran status, notice period), select the choice closest to the candidate's profile.
   - If asked about authorization to work, answer 'Yes'. If asked about requiring visa sponsorship, match candidate profile ({cq.require_visa}).

3. Open-ended / Unknown Questions:
   - If an input requires free-form text (e.g., 'Why do you want to work here?', 'Cover Letter', 'Tell us about yourself'):
     Synthesize a concise, professional, tailored 2-4 sentence response using the candidate's experience and headline.
   - If a numeric field is required and unspecified, use 0 or reasonable estimate.

4. Multi-step Navigation:
   - If the application has multiple steps/pages ('Next', 'Continue', 'Save & Continue', 'Review'), click forward autonomously.
   - Verify required validation errors if any field is flagged red, rectify the value, and proceed.
   - Avoid clicking any button that opens a 'Print' dialog or exits the flow.

5. Final Submission:
   - Once all sections are filled, click 'Submit Application' or 'Apply'.
   - Confirm confirmation message or thank-you screen appears.
"""
    
    from browser_use.browser.session import BrowserSession
    headless_setting = os.environ.get('HEADLESS_MODE', 'True').lower() == 'true'
    browser_session = BrowserSession(headless=headless_setting)

    # Explicit initial navigation to the target job application link
    initial_actions = [{'navigate': {'url': application_link, 'new_tab': False}}]

    # Create the Browser Use Agent with explicit initial navigation and vision support
    agent = BrowserUseAgent(
        task=task_instruction,
        llm=browser_use_llm,
        controller=controller,
        browser_session=browser_session,
        initial_actions=initial_actions,
        llm_timeout=900,  # 15 minutes timeout
        step_timeout=1200,
        use_thinking=False,
        use_vision=True,
    )
    
    # Retry execution up to 3 times
    for attempt in range(3):
        try:
            result = await agent.run(max_steps=50)
            return result
        except Exception as e:
            print(f"⚠️ Browser-Use attempt {attempt+1} failed with error: {e}")
            if attempt == 2:
                raise

def run_browser_use_apply(application_link: str, cv_data: str):
    """
    Main synchronous wrapper function called by runAiBot.py.
    """
    # Validate application_link
    if not application_link or not isinstance(application_link, str):
        print("⚠️ No application link provided. Skipping.")
        return False
    if 'example.com' in application_link.lower():
        print(f"⚠️ Skipping placeholder URL in run_browser_use_apply: {application_link}")
        return False
    # Fix empty CV if user didn't populate the big text block
    cv_data = get_cv_data(cv_data)

    print("--- 🚀 Starting Browser-Use Orchestration ---")
    
    # Step 1: Run Browser-Use to Execute the Web Form Filling
    print("🌐 Browser-Use: Opening Playwright to fill the web form using raw CV data...")
    try:
        # We must use asyncio.run to execute the async browser-use inside our sync python script
        # Attempt the browser-use execution with retries
        for attempt in range(3):
            try:
                result = asyncio.run(execute_browser_use(application_link, str(cv_data)))
                print(f"✅ Browser-Use Execution Result (attempt {attempt+1}):\n{result}")
                break
            except Exception as e:
                print(f"⚠️ Attempt {attempt+1} failed with error: {e}")
                if attempt == 2:
                    raise
        
        # --- LOGGING FOR DEBUGGING & ACCURACY CHECKING ---
        log_dir = os.path.join("logs", "external_applications")
        os.makedirs(log_dir, exist_ok=True)
        # Create a safe filename from the URL
        safe_url = "".join([c if c.isalnum() else "_" for c in application_link])[:50]
        log_file_path = os.path.join(log_dir, f"{safe_url}.txt")
        
        with open(log_file_path, "w", encoding="utf-8") as f:
            f.write(f"URL: {application_link}\n")
            f.write("="*50 + "\n")
            f.write("RAW CV PROFILE (What was sent to the form filler):\n")
            f.write(str(cv_data) + "\n\n")
            f.write("="*50 + "\n")
            f.write("BROWSER-USE ACTIONS (What the AI typed and clicked):\n")
            f.write(str(result) + "\n")
            
        print(f"📄 Saved execution log for your review at: {log_file_path}")
        return True
    except Exception as e:
        print(f"❌ Browser-Use encountered an error: {e}")
        return False

# For local testing if you run this script directly
if __name__ == "__main__":
    test_cv = "Name: Shirish. Experience: 5 years Python Developer. Email: test@test.com"
    run_browser_use_apply("https://example.com/apply", test_cv)
