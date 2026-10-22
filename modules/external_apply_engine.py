import os
import sys
import re
import time
import json
from datetime import datetime
import requests
import base64
import io
from PIL import Image
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config.personals as cp
import config.secrets as cs
import config.questions as cq

def get_candidate_profile():
    resume_path = os.path.abspath(getattr(cq, "default_resume_path", "Shirish_Maharjan_CV copy.pdf"))
    if not os.path.exists(resume_path):
        root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        for fname in ["Shirish_Maharjan_CV copy.pdf", "Shirish_Maharjan_CV.pdf", "resume.pdf"]:
            p = os.path.join(root_dir, fname)
            if os.path.exists(p):
                resume_path = p
                break

    first = getattr(cp, "first_name", "Shirish")
    last = getattr(cp, "last_name", "Maharjan")
    full_name = f"{first} {last}".strip()
    email = getattr(cs, "username", "shirishmaharjan0@gmail.com")
    phone = getattr(cp, "phone_number", "9803341626")
    city = getattr(cp, "current_city", "Kathmandu")
    state = getattr(cp, "state", "Bagmati")
    country = getattr(cp, "country", "Nepal")
    zipcode = getattr(cp, "zipcode", "44600")
    linkedin = getattr(cq, "linkedIn", "https://www.linkedin.com/in/shirish-maharjan")
    website = getattr(cq, "website", "https://github.com/shirishmaharjan")
    headline = getattr(cq, "linkedin_headline", "DevOps Engineer / Site Reliability Engineer")
    summary = getattr(cq, "linkedin_summary", (
        "DevOps Engineer with 5+ years of experience in CI/CD, Kubernetes, Docker, AWS, "
        "Terraform, Python automation, Linux administration, and scalable cloud infrastructure."
    ))

    return {
        "first_name": first,
        "last_name": last,
        "full_name": full_name,
        "email": email,
        "phone": phone,
        "city": city,
        "state": state,
        "country": country,
        "zipcode": zipcode,
        "location": f"{city}, {country}",
        "address": getattr(cp, "street", f"{city}, {country}"),
        "linkedin": linkedin,
        "website": website,
        "github": website,
        "headline": headline,
        "summary": summary,
        "years_experience": str(getattr(cq, "years_of_experience", 5)),
        "desired_salary": str(getattr(cq, "desired_salary", 95000)),
        "current_ctc": str(getattr(cq, "current_ctc", 75000)),
        "notice_period": str(getattr(cq, "notice_period", 15)),
        "work_authorization": "Yes",
        "visa_sponsorship": "No" if not getattr(cq, "require_visa", False) else "Yes",
        "resume_path": resume_path,
        "gender": getattr(cp, "gender", "Male"),
        "ethnicity": getattr(cp, "ethnicity", "Asian"),
        "veteran": getattr(cp, "veteran_status", "No"),
        "disability": getattr(cp, "disability_status", "No")
    }

class ExternalApplyEngine:
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.profile = get_candidate_profile()
        self.vision_model = getattr(cs, "browser_vision_model", "qwen3.5:2b")
        self.log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs", "external_applications")
        os.makedirs(self.log_dir, exist_ok=True)

    def _analyze_screenshot(self, image_path: str, prompt: str) -> str:
        """Sends a scaled screenshot to the local Ollama vision LLM for visual reasoning."""
        if not os.path.exists(image_path):
            return ""
        try:
            img = Image.open(image_path)
            img.thumbnail((768, 768))
            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=70)
            b64 = base64.b64encode(buf.getvalue()).decode("utf-8")

            payload = {
                "model": self.vision_model,
                "prompt": prompt,
                "images": [b64],
                "stream": False,
                "options": {
                    "num_predict": 350,
                    "temperature": 0.1
                }
            }
            resp = requests.post("http://localhost:11434/api/generate", json=payload, timeout=120)
            if resp.status_code == 200:
                data = resp.json()
                resp_text = (data.get("response") or "").strip()
                think_text = (data.get("thinking") or "").strip()
                if resp_text and think_text:
                    return f"{resp_text}\n{think_text}"
                return resp_text or think_text
        except Exception as e:
            print(f"⚠️ Vision reasoning ({self.vision_model}) notice: {e}", flush=True)
        return ""

    def apply_to_job(self, application_url: str, job_title: str = "", company_name: str = "") -> dict:
        print(f"\n=======================================================", flush=True)
        print(f"🚀 [ExternalApplyEngine] Processing: {application_url}", flush=True)
        print(f"Candidate: {self.profile['full_name']} ({self.profile['email']})", flush=True)
        print(f"Resume: {self.profile['resume_path']}", flush=True)
        print(f"=======================================================", flush=True)

        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=self.headless,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-infobars"
                ]
            )
            context = browser.new_context(
                viewport={"width": 1280, "height": 900},
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
            )
            # Inject stealth script to evade Cloudflare Turnstile and bot detection
            context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
                window.chrome = { runtime: {} };
                Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
                Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
            """)
            page = context.new_page()

            try:
                # 1. Navigate to the job application URL
                try:
                    page.goto(application_url, wait_until="domcontentloaded", timeout=35000)
                except PlaywrightTimeoutError:
                    print("⚠️ Page load timed out on domcontentloaded, continuing...", flush=True)

                time.sleep(2)

                # Check if job is expired or closed
                curr_url = page.url.lower()
                title_lower = page.title().lower()
                body_lower = page.locator("body").inner_text().lower()

                CLOSED_PHRASES = [
                    "job not found", "the job you requested was not found", "page not found",
                    "404 not found", "404 - not found", "404 |", "no longer available",
                    "job has expired", "position has been filled", "no longer accepting applications",
                    "this job has closed", "job opening is closed", "posting has expired",
                    "job does not exist", "oops, you've gone too far",
                    "the page you were trying to access is no longer available",
                    "this position is no longer open", "position closed", "not accepting applications",
                    "job has been removed", "job is inactive", "this job is no longer available"
                ]

                if "error=true" in curr_url or any(t in title_lower for t in ["404", "not found", "error", "expired"]) or any(msg in body_lower for msg in CLOSED_PHRASES):
                    print(f"🚫 Job is expired, closed, or 404 on external portal: {application_url}", flush=True)
                    browser.close()
                    return {"success": False, "expired": True, "message": "Position is closed or no longer accepting applications"}

                # 2. Dismiss cookie dialogs if present
                self._dismiss_cookie_banners(page)

                # 3. Read content & decide: handle Captchas, click Apply button, track new tabs to form
                page, early_res = self._navigate_to_application_form(page, context, company_name)
                if early_res:
                    browser.close()
                    return early_res

                # 4. Wait for dynamic form hydration (Manatal, Greenhouse, Ashby, Lever, etc.)
                self._wait_for_form_hydration(page)

                # 5. Detect form target (page or embedded iframe)
                form_target = self._find_form_target(page)

                # If after hydration there are still no form inputs at all, check with Vision LLM
                input_count = form_target.locator('input, textarea, select').count()
                if input_count == 0:
                    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                    safe_slug = re.sub(r'[^a-zA-Z0-9]', '_', company_name or "external_job")[:25]
                    landing_screen = os.path.join(self.log_dir, f"{ts}_{safe_slug}_landing.png")
                    try:
                        page.screenshot(path=landing_screen)
                        print(f"👁️ [Vision LLM ({self.vision_model})] Reading screenshot to determine job status...", flush=True)
                        vision_check = self._analyze_screenshot(
                            landing_screen,
                            "Analyze this webpage screenshot.\n"
                            "Is this job posting CLOSED/EXPIRED or is it an ACTIVE opening?\n\n"
                            "Reply strictly in this format:\n"
                            "VERDICT: CLOSED\n"
                            "or\n"
                            "VERDICT: ACTIVE"
                        )
                        print(f"👁️ [Vision LLM ({self.vision_model})] Page Decision: {vision_check[:100]}...", flush=True)
                        verdict = ""
                        for line in reversed([l.strip() for l in vision_check.splitlines() if l.strip()]):
                            if line.upper().startswith("VERDICT:"):
                                verdict = line.upper().split("VERDICT:")[-1].strip()
                                break
                        if verdict in ["CLOSED", "EXPIRED", "NOT FOUND"]:
                            browser.close()
                            return {"success": False, "expired": True, "message": f"Vision LLM confirmed closed: {vision_check[:100]}"}
                    except Exception:
                        pass

                    print(f"🚫 No form fields found on page (likely closed or portal index): {application_url}", flush=True)
                    browser.close()
                    return {"success": False, "expired": True, "message": "No application form found on page"}

                # 6. Upload Resume
                uploaded = self._upload_resume(form_target)
                print(f"📄 Resume upload: {'Success' if uploaded else 'None found/already attached'}", flush=True)

                self._dismiss_cookie_banners(page)

                # 7. Fill Text, Tel, and Email Fields
                filled_count = self._fill_text_inputs(form_target)
                print(f"✍️ Filled {filled_count} text/email/tel inputs", flush=True)

                # 8. Handle React-Select and Custom UI Comboboxes
                custom_selects = self._handle_react_and_custom_selects(form_target)
                print(f"🔽 Handled {custom_selects} custom/React selects", flush=True)

                # 9. Handle Native Dropdowns (<select>)
                native_selects = self._fill_native_dropdowns(form_target)
                print(f"🔽 Handled {native_selects} native dropdown selects", flush=True)

                # 10. Handle Checkboxes, Toggles, and Radios
                cb_count = self._handle_checkboxes_and_radios(form_target)
                print(f"☑️ Checked {cb_count} consent/authorization options", flush=True)

                # 11. Handle Checkbox question groups (e.g. Salary ranges, preferences)
                self._handle_question_checkbox_groups(form_target)

                # 12. Handle button-based Yes/No segmented toggles (Ashby / Workday)
                seg_count = self._handle_segmented_button_toggles(form_target)
                if seg_count:
                    print(f"🔘 Selected {seg_count} segmented toggle options (Ashby/Workday)", flush=True)

                # 13. Handle Ashby location combobox and date pickers
                self._handle_ashby_and_specialty_inputs(form_target)

                # 14. Fill any remaining invalid / required fields with defaults
                self._fill_remaining_required_fields(form_target)

                # 13. Pre-submission screenshot
                ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                safe_slug = re.sub(r'[^a-zA-Z0-9]', '_', company_name or "external_job")[:25]
                pre_screen = os.path.join(self.log_dir, f"{ts}_{safe_slug}_filled.png")
                page.screenshot(path=pre_screen, full_page=True)
                print(f"📸 Saved pre-submission screenshot: {pre_screen}", flush=True)

                # 14. Submit & Verify (handles multi-step forms if needed)
                submit_res = self._submit_and_verify(form_target, page, company_name, job_title)

                # 13. Post-submission screenshot & Vision LLM verification
                post_screen = os.path.join(self.log_dir, f"{ts}_{safe_slug}_submitted.png")
                submit_res["screenshot"] = post_screen
                try:
                    page.screenshot(path=post_screen, full_page=True)
                    print(f"📸 Saved final screenshot: {post_screen}", flush=True)

                    if submit_res.get("clicked_submit"):
                        print(f"👁️ [Vision LLM ({self.vision_model})] Reading post-submission screenshot to verify outcome...", flush=True)
                        v_verify = self._analyze_screenshot(
                            post_screen,
                            "Analyze this screenshot taken immediately after clicking submit on a job application. "
                            "Did the application submit successfully (look for thank you message, application received, confirmation notice)? "
                            "Or does it show validation errors (missing required field, red error notice, invalid input)? "
                            "Start your answer with CONFIRMED if successful, or ERRORS if failed, followed by 1 concise sentence."
                        )
                        print(f"👁️ [Vision LLM ({self.vision_model})] Decision: {v_verify[:180]}...", flush=True)
                        if "CONFIRMED" in v_verify.upper() or "APPLICATION SUBMITTED" in v_verify.upper():
                            submit_res["success"] = True
                            submit_res["message"] = f"Confirmed via Vision LLM ({self.vision_model}): {v_verify[:120]}"
                            submit_res["confirmation_type"] = "vision_llm"
                        elif any(err in v_verify.upper() for err in ["VALIDATION ERROR", "FIELD IS REQUIRED", "PLEASE CORRECT", "MISSING REQUIRED"]):
                            submit_res["success"] = False
                            submit_res["message"] = f"Vision LLM detected validation error: {v_verify[:120]}"
                    elif submit_res.get("expired"):
                        print(f"ℹ️ Position closed or portal directory without submit form. Skipping post-submission verification.", flush=True)
                except Exception as e:
                    print(f"⚠️ Vision post-submit check notice: {e}", flush=True)

                browser.close()
                return submit_res

            except Exception as e:
                print(f"❌ Error during application flow: {e}", flush=True)
                err_screen = os.path.join(self.log_dir, f"error_{int(time.time())}.png")
                try:
                    page.screenshot(path=err_screen)
                except Exception:
                    pass
                browser.close()
                return {"success": False, "message": f"Error: {e}", "screenshot": err_screen}

    def _dismiss_cookie_banners(self, page):
        cookie_selectors = [
            'button:has-text("Accept all cookies")',
            'button:has-text("Accept all")',
            'button:has-text("Accept Cookies")',
            'button:has-text("Accept cookies")',
            'button:has-text("I agree")',
            'button:has-text("Allow all")',
            'button:has-text("Got it")',
            'button:has-text("Decline all non-necessary cookies")',
            '#onetrust-accept-btn-handler',
            '.cookie-consent-accept',
            '[aria-label="Accept all cookies"]'
        ]
        for sel in cookie_selectors:
            try:
                btn = page.locator(sel).first
                if btn.is_visible(timeout=500):
                    btn.click()
                    time.sleep(0.5)
                    break
            except Exception:
                pass

        # Close dialogs or cookie popups only (never touch body/html/main)
        try:
            page.evaluate('''() => {
                document.querySelectorAll('dialog, .z-cookie-alert, #onetrust-banner-sdk').forEach(el => {
                    if (['BODY', 'HTML', 'MAIN'].includes(el.tagName)) return;
                    let b = el.querySelector('button');
                    if (b) {
                        try { b.click(); } catch(e) {}
                    }
                    el.style.display = 'none';
                    try { el.remove(); } catch(e) {}
                });
            }''')
        except Exception:
            pass

    def _is_form_active(self, target) -> bool:
        """Checks if an actual application form is currently visible on the target or in any embedded frame."""
        try:
            # 1. Resume upload or name field presence
            if target.locator('input[type="file"], #resume, #first_name, input[name*="resume" i], input[name*="name" i]').count() >= 1:
                return True
            # 2. General form inputs count
            if target.locator('input:not([type="hidden"]), textarea').count() >= 3:
                return True
            # 3. Check child frames
            if hasattr(target, 'frames'):
                for f in target.frames:
                    if f != target.main_frame and f.locator('input[type="file"], #first_name, input[name*="name" i]').count() >= 1:
                        return True
        except Exception:
            pass
        return False

    def _handle_captchas_and_challenges(self, page) -> dict:
        """
        Detects and attempts to solve/clear Cloudflare Turnstile, reCAPTCHA, and bot verification challenges.
        Returns:
            {"handled": bool, "blocked": bool, "message": str}
        """
        try:
            body_text = page.locator("body").inner_text().lower()

            # 1. Cloudflare WAF block detection
            if any(k in body_text for k in ["attention required! | cloudflare", "you have been blocked", "access denied", "ray id:"]):
                if "blocked" in body_text or "access denied" in body_text:
                    print("🛡️ Cloudflare WAF block detected on IP/session.", flush=True)
                    return {"handled": False, "blocked": True, "message": "Blocked by Cloudflare Security WAF (Ray ID Block)"}

            # 2. Cloudflare Turnstile inside frames & main page
            is_cf_challenge = any(k in body_text for k in [
                "verify you are human", "checking if the site connection is secure",
                "just a moment...", "security verification", "cloudflare"
            ])

            # Check frames for Turnstile
            turnstile_clicked = False
            for frame in page.frames:
                f_url = frame.url.lower()
                if any(domain in f_url for domain in ["challenges.cloudflare.com", "turnstile", "cloudflare"]):
                    for cf_sel in ['input[type="checkbox"]', '#challenge-stage', '.ctp-checkbox-label', '#cf-stage', 'body']:
                        try:
                            box = frame.locator(cf_sel).first
                            if box.is_visible(timeout=800):
                                box.click(force=True)
                                print(f"👉 Clicked Cloudflare Turnstile inside iframe ({frame.url[:45]}...)", flush=True)
                                turnstile_clicked = True
                                time.sleep(2)
                                break
                        except Exception:
                            pass
                if turnstile_clicked:
                    break

            # If not in frame, check main page
            if not turnstile_clicked and is_cf_challenge:
                for cf_sel in ['#challenge-stage input[type="checkbox"]', '.ctp-checkbox-label', '#challenge-stage', '.cf-turnstile']:
                    try:
                        el = page.locator(cf_sel).first
                        if el.is_visible(timeout=600):
                            el.click(force=True)
                            print(f"👉 Clicked Cloudflare Turnstile element: {cf_sel}", flush=True)
                            time.sleep(2)
                            break
                    except Exception:
                        pass

            if turnstile_clicked or is_cf_challenge:
                # Poll up to 6s for challenge to clear
                for _ in range(6):
                    time.sleep(1)
                    curr_body = page.locator("body").inner_text().lower()
                    if not any(k in curr_body for k in ["verify you are human", "checking if the site connection is secure", "just a moment..."]):
                        print("✅ Challenge cleared! Application portal loaded.", flush=True)
                        return {"handled": True, "blocked": False, "message": "Turnstile cleared"}

            # 3. Google reCAPTCHA checkbox inside anchor frames
            for frame in page.frames:
                if "recaptcha" in frame.url and "anchor" in frame.url:
                    try:
                        box = frame.locator('#recaptcha-anchor, .recaptcha-checkbox').first
                        if box.is_visible(timeout=800):
                            print("🛡️ reCAPTCHA detected in iframe. Attempting to click checkbox...", flush=True)
                            box.click(force=True)
                            time.sleep(2)
                    except Exception:
                        pass

            # 4. Check if an interactive image challenge puzzle popped up (bframe)
            has_bframe = any("bframe" in f.url for f in page.frames) or page.locator('iframe[src*="bframe"], iframe[title*="recaptcha challenge" i]').count() > 0
            if has_bframe:
                print("🛡️ Interactive image CAPTCHA puzzle detected (e.g. 'Select all squares with buses').", flush=True)
                return {"handled": False, "blocked": True, "message": "Blocked by interactive image CAPTCHA puzzle"}

        except Exception as e:
            pass
        return {"handled": True, "blocked": False, "message": "OK"}

    def _find_form_target(self, page):
        """Returns the page or embedded iframe that contains the application form."""
        try:
            if page.locator('input[type="file"], input[name*="name" i], #first_name, #resume').count() > 0:
                return page

            for frame in page.frames:
                try:
                    if frame != page.main_frame and frame.locator('input[type="file"], input[name*="name" i], #first_name, input[type="email"]').count() > 0:
                        print(f"🖼️ Detected application form inside iframe: {frame.name or frame.url}", flush=True)
                        return frame
                except Exception:
                    continue
        except Exception:
            pass
        return page

    def _find_and_click_apply_button(self, page, context) -> tuple:
        """
        DOM-First Search: Discovers and clicks 'Apply', 'Apply Now', 'Apply on company website',
        handling new tabs/popups, in-page redirects, and dynamic hydration.
        Returns:
            (page, clicked_apply: bool)
        """
        apply_selectors = [
            'button:has-text("Apply on company website")', 'a:has-text("Apply on company website")',
            'button:has-text("Apply on company site")', 'a:has-text("Apply on company site")',
            'button:has-text("Apply for this job")', 'a:has-text("Apply for this job")',
            'button:has-text("Apply to Job")', 'a:has-text("Apply to Job")',
            'button:has-text("Apply Now")', 'a:has-text("Apply Now")',
            'button:has-text("Apply now")', 'a:has-text("Apply now")',
            'button:has-text("Start Application")', 'a:has-text("Start Application")',
            'button:has-text("Apply with Resume")', 'a:has-text("Apply with Resume")',
            'button:has-text("Apply without Resume")', 'a:has-text("Apply without Resume")',
            'button:has-text("Apply Manually")', 'a:has-text("Apply Manually")',
            'button:has-text("Apply")', 'a:has-text("Apply")',
            '[data-qa*="apply" i]', '#apply_button', '.apply-button', '.apply_button',
            'a[href*="/apply"]', 'a[href*="application"]', 'a[href*="apply"]'
        ]

        initial_pages = list(context.pages)

        # Try visible buttons in current fold first; if none, scroll down to check bottom fold
        for scroll_attempt in range(2):
            for sel in apply_selectors:
                try:
                    candidates = page.locator(sel).all()
                    for btn in candidates:
                        if not btn.is_visible():
                            continue
                        btn_text = (btn.inner_text() or btn.get_attribute("value") or btn.get_attribute("aria-label") or "").strip().lower()
                        if any(bad in btn_text for bad in ["cookie", "cancel", "close", "sign in", "log in", "manage", "search"]):
                            continue
                        btn_display = (btn.inner_text() or btn.get_attribute("value") or "Apply").strip()
                        print(f"👉 Found and clicking Apply button: '{btn_display}'", flush=True)

                        # Click with popup listener
                        try:
                            with context.expect_page(timeout=4000) as new_page_info:
                                btn.click(timeout=3000)
                            new_page = new_page_info.value
                            print(f"🔀 Switched to newly opened application tab: {new_page.url}", flush=True)
                            try:
                                new_page.wait_for_load_state("domcontentloaded", timeout=15000)
                            except Exception:
                                pass
                            self._dismiss_cookie_banners(new_page)
                            self._handle_captchas_and_challenges(new_page)
                            return new_page, True
                        except Exception:
                            # If no expect_page event fired, check if pages count grew or navigated
                            time.sleep(2)
                            if len(context.pages) > len(initial_pages):
                                new_page = context.pages[-1]
                                print(f"🔀 Detected new tab in context: {new_page.url}", flush=True)
                                try:
                                    new_page.wait_for_load_state("domcontentloaded", timeout=15000)
                                except Exception:
                                    pass
                                self._dismiss_cookie_banners(new_page)
                                self._handle_captchas_and_challenges(new_page)
                                return new_page, True
                            else:
                                # Navigated on same page or expanded inline form
                                try:
                                    page.wait_for_load_state("domcontentloaded", timeout=8000)
                                except Exception:
                                    pass
                                self._dismiss_cookie_banners(page)
                                self._handle_captchas_and_challenges(page)
                                return page, True
                except Exception:
                    continue

            # Scroll down half page to reveal any sticky or bottom apply buttons
            if scroll_attempt == 0:
                try:
                    page.evaluate("window.scrollBy(0, 600)")
                    time.sleep(1)
                except Exception:
                    pass

        return page, False

    def _navigate_to_application_form(self, page, context, company_name: str) -> tuple:
        """
        DOM-First Navigation with Vision Verification:
        1. Checks for CAPTCHA/bot challenges and handles them.
        2. Checks if an application form is already present on page.
        3. If not, finds and clicks 'Apply' / 'Apply Now' buttons across the DOM (with tab tracking).
        4. If no form and no button found, uses Vision LLM with strict verdict parsing.
        """
        # 1. Dismiss cookies
        self._dismiss_cookie_banners(page)

        # 2. Check and handle CAPTCHA / Cloudflare
        c_status = self._handle_captchas_and_challenges(page)
        if c_status.get("blocked"):
            return page, {"success": False, "captcha_blocked": True, "message": c_status.get("message")}

        # 3. Check if application form is ALREADY open and active
        if self._is_form_active(page):
            print(f"📝 Application form is already active and ready to fill.", flush=True)
            self._wait_for_form_hydration(page)
            return page, None

        # 4. Search for and click 'Apply' button in the DOM (with scroll & tab tracking)
        page, clicked_apply = self._find_and_click_apply_button(page, context)
        if clicked_apply:
            self._wait_for_form_hydration(page)
            if self._is_form_active(page):
                print(f"📝 Successfully reached application form after clicking Apply button.", flush=True)
                return page, None

        # 5. Fallback: If no form and no apply button were found, consult Vision LLM
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_slug = re.sub(r'[^a-zA-Z0-9]', '_', company_name or "external_job")[:25]
        landing_screen = os.path.join(self.log_dir, f"{ts}_{safe_slug}_landing.png")
        try:
            page.screenshot(path=landing_screen)
            print(f"👁️ [Vision LLM ({self.vision_model})] Evaluating page state (no form/apply button found in DOM)...", flush=True)
            v_analysis = self._analyze_screenshot(
                landing_screen,
                "Analyze this webpage screenshot carefully.\n"
                "Determine if this job opening is CLOSED/EXPIRED or if it is an ACTIVE job opening.\n\n"
                "Reply strictly in this format:\n"
                "VERDICT: CLOSED (if 404, closed, expired, filled, or no job exists)\n"
                "or\n"
                "VERDICT: ACTIVE (if open or active application)\n"
                "REASON: 1 short sentence explanation."
            )
            print(f"👁️ [Vision LLM ({self.vision_model})] Page Decision: {v_analysis[:180]}...", flush=True)

            # Strict verdict parsing to avoid chain-of-thought false positives
            verdict = ""
            for line in reversed([l.strip() for l in v_analysis.splitlines() if l.strip()]):
                if line.upper().startswith("VERDICT:"):
                    verdict = line.upper().split("VERDICT:")[-1].strip()
                    break

            if verdict in ["CLOSED", "EXPIRED", "NOT FOUND"]:
                print(f"🚫 [Vision LLM ({self.vision_model})] Confirmed NO ACTIVE JOB on page (closed/expired/404).", flush=True)
                return page, {"success": False, "expired": True, "message": f"Vision LLM: {v_analysis[:120]}"}

        except Exception as e:
            print(f"⚠️ Vision landing check notice: {e}", flush=True)

        return page, None

    def _wait_for_form_hydration(self, page):
        time.sleep(2)
        for loader_sel in ['#application-form-loader', '.loading-spinner', '.loader-spinner']:
            try:
                loader = page.locator(loader_sel).first
                if loader.is_visible():
                    loader.wait_for(state="hidden", timeout=10000)
            except Exception:
                pass
        time.sleep(1)

    def _upload_resume(self, page) -> bool:
        resume_path = self.profile["resume_path"]
        if not os.path.exists(resume_path):
            print(f"⚠️ Resume file not found at: {resume_path}", flush=True)
            return False

        # First priority: find input with id/name resume or cv
        target_input = None
        for sel in [
            'input[type="file"]#resume',
            'input[type="file"]#_systemfield_resume',
            'input[type="file"][name*="resume" i]',
            'input[type="file"][name*="cv" i]',
            'input[type="file"]:not([id*="cover"]):not([name*="cover"])'
        ]:
            candidates = page.locator(sel).all()
            for cand in candidates:
                cand_id = (cand.get_attribute("id") or "").lower()
                cand_name = (cand.get_attribute("name") or "").lower()
                if "cover" not in cand_id and "cover" not in cand_name:
                    target_input = cand
                    break
            if target_input:
                break

        if target_input:
            try:
                target_input.set_input_files(resume_path)
                time.sleep(2)
                # Wait for any upload spinner/progress to finish
                for _ in range(8):
                    busy = page.locator('.filepond--item-state-busy, [class*="uploading" i], [class*="progress-bar" i], .spinner-border:visible').count()
                    if busy == 0:
                        break
                    time.sleep(1)
                return True
            except Exception as e:
                print(f"⚠️ Failed to upload file to target input: {e}", flush=True)

        return False

    def _fill_text_inputs(self, page) -> int:
        inputs = page.locator('input:not([type="hidden"]):not([type="file"]):not([type="checkbox"]):not([type="radio"]):not([type="submit"]), textarea').all()
        filled = 0

        for el in inputs:
            try:
                if not el.is_visible():
                    continue

                ctx = el.evaluate('''el => {
                    let label = '';
                    if (el.id) {
                        let l = document.querySelector("label[for='" + el.id + "']");
                        if (l) label = l.innerText;
                    }
                    if (!label) {
                        let parent = el.closest('label') || el.closest('.form-group') || el.closest('[class*="Field"]') || el.closest('.field-wrapper') || el.parentElement;
                        if (parent) label = parent.innerText;
                    }
                    return {
                        label: (label || '').toLowerCase(),
                        placeholder: (el.placeholder || '').toLowerCase(),
                        name: (el.name || '').toLowerCase(),
                        id: (el.id || '').toLowerCase(),
                        aria: (el.getAttribute('aria-label') || '').toLowerCase(),
                        current_val: el.value || '',
                        tag: el.tagName.toLowerCase()
                    };
                }''')

                if ctx["current_val"].strip():
                    continue

                full_desc = f"{ctx['label']} {ctx['placeholder']} {ctx['name']} {ctx['id']} {ctx['aria']}"
                val = None

                # Full name matched first so 'first and last name' does not get cut to first name only
                if any(k in full_desc for k in ["full name", "fullname", "first and last name", "first & last name", "your name", "_systemfield_name", "candidate name"]):
                    val = self.profile["full_name"]
                elif any(k in full_desc for k in ["first name", "firstname", "given name", "first_name"]):
                    val = self.profile["first_name"]
                elif any(k in full_desc for k in ["last name", "lastname", "family name", "surname", "last_name"]):
                    val = self.profile["last_name"]
                elif any(k in full_desc for k in ["email", "e-mail", "@"]):
                    val = self.profile["email"]
                elif ctx["tag"] != "textarea" and re.search(r'\b(phone|mobile|telephone|cell|cellphone)\b', full_desc, re.I):
                    val = self.profile["phone"]
                elif any(k in full_desc for k in ["linkedin"]):
                    val = self.profile["linkedin"]
                elif any(k in full_desc for k in ["github", "portfolio", "website", "personal site", "url"]):
                    val = self.profile["website"]
                elif any(k in full_desc for k in ["city", "current location", "location", "where are you located"]):
                    val = self.profile["location"]
                elif "address" in full_desc:
                    val = self.profile["address"]
                elif "zip" in full_desc or "postal" in full_desc:
                    val = self.profile["zipcode"]
                elif "country" in full_desc and ctx["tag"] != "input":
                    val = self.profile["country"]
                elif any(k in full_desc for k in ["years of experience", "how many years", "experience in years"]):
                    val = self.profile["years_experience"]
                elif any(k in full_desc for k in ["salary", "compensation", "expected ctc"]):
                    val = self.profile["desired_salary"]
                elif any(k in full_desc for k in ["notice period", "how soon", "when can you start", "start date"]):
                    val = "Immediately / 2 weeks"
                elif ctx["tag"] == "textarea" or any(k in full_desc for k in ["cover letter", "about yourself", "summary", "additional information", "tell us", "why do you want", "experience", "describe"]):
                    val = self.profile["summary"]
                elif ("name" in full_desc and not any(x in full_desc for x in ["company", "user", "file", "school", "hr", "domain"])):
                    val = self.profile["full_name"]

                if val is not None:
                    el.fill(str(val))
                    filled += 1
            except Exception:
                continue

        return filled

    def _handle_react_and_custom_selects(self, page) -> int:
        """Handles React-Select (.select__control), Radix UI buttons, and comboboxes."""
        handled = 0

        # A. React-Select controls (Greenhouse, Ashby, etc.)
        controls = page.locator(".select__control").all()
        for ctrl in controls:
            try:
                if not ctrl.is_visible():
                    continue

                label = ctrl.evaluate('''el => {
                    let p = el.closest('.field-wrapper') || el.closest('.field') || el.parentElement.parentElement;
                    return p ? p.innerText.toLowerCase() : '';
                }''')

                inp = ctrl.locator("input").first
                if inp.count() > 0:
                    inp.focus()
                    # For country combobox next to phone: type "Nepal" or pick country
                    if "country" in label or "phone" in label:
                        inp.press_sequentially(self.profile["country"], delay=50)
                        time.sleep(0.5)
                        page.keyboard.press("Enter")
                        handled += 1
                        time.sleep(0.5)
                        continue

                    # Otherwise, open menu with ArrowDown
                    page.keyboard.press("ArrowDown")
                    time.sleep(0.5)

                    opts = page.locator(".select__option:visible, [role='option']:visible").all()
                    if opts:
                        picked = False
                        # Match label to best option
                        if "experience" in label:
                            for o in opts:
                                if any(yr in o.inner_text() for yr in ["5", "4", "3", "mid", "senior"]):
                                    o.click()
                                    picked = True
                                    handled += 1
                                    break
                        elif any(k in label for k in ["when", "start", "available"]):
                            for o in opts:
                                if any(im in o.inner_text().lower() for im in ["immediately", "1 week", "2 weeks"]):
                                    o.click()
                                    picked = True
                                    handled += 1
                                    break
                        elif "english" in label or "proficiency" in label or "language" in label:
                            for o in opts:
                                if any(en in o.inner_text().lower() for en in ["fluent", "advanced", "professional", "native"]):
                                    o.click()
                                    picked = True
                                    handled += 1
                                    break

                        if not picked:
                            # Pick first valid option
                            opts[0].click()
                            handled += 1
                    else:
                        page.keyboard.press("Escape")
                time.sleep(0.3)
            except Exception:
                continue

        # B. Custom dropdown buttons (Radix UI / Careers-page / Teamtailor)
        custom_triggers = page.locator('button[role="combobox"], button:has-text("-"), [class*="select-trigger"], button[aria-label="Select an option"], button:has-text("Select an option")').all()
        for trigger in custom_triggers:
            try:
                if not trigger.is_visible():
                    continue
                btn_text = trigger.inner_text().strip()
                if btn_text and btn_text not in ["-", "Select...", "Select", "Please select", "Choose option", "Select an option"]:
                    continue

                trigger.click(force=True)
                time.sleep(0.5)

                menu_options = page.locator('[role="option"]:visible, [role="menuitem"]:visible, li.select2-results__option:visible, [role="listbox"] button:visible, [class*="dropdown"] button:visible').all()
                if menu_options:
                    picked = False
                    for opt in menu_options:
                        txt = opt.inner_text().strip().lower()
                        if any(good in txt for good in ["devops", "cloud", "engineer", "software", "nepal", "remote", "latin", "yes", "authorized"]):
                            opt.click(force=True)
                            picked = True
                            handled += 1
                            break
                    if not picked and len(menu_options) > 1:
                        menu_options[1].click(force=True)
                        handled += 1
                    elif not picked and len(menu_options) == 1:
                        menu_options[0].click(force=True)
                        handled += 1
                else:
                    page.locator('body').click(position={"x": 10, "y": 10})
                time.sleep(0.3)
            except Exception:
                continue

        return handled

    def _fill_native_dropdowns(self, page) -> int:
        native_selects = page.locator('select').all()
        handled = 0
        for sel in native_selects:
            try:
                if not sel.is_visible():
                    continue
                label = sel.evaluate('''el => {
                    let l = el.id ? document.querySelector("label[for='" + el.id + "']") : null;
                    return (l ? l.innerText : (el.name || el.id || '')).toLowerCase();
                }''')
                options = sel.evaluate('''el => Array.from(el.options).map(o => ({text: o.innerText.trim(), value: o.value}))''')
                if not options or len(options) <= 1:
                    continue

                best = None
                if any(k in label for k in ["learn about", "hear about", "source"]):
                    for o in options:
                        if "linkedin" in o["text"].lower() or "website" in o["text"].lower():
                            best = o; break
                elif any(k in label for k in ["authorized", "authorization", "eligible"]):
                    for o in options:
                        if o["text"].lower() in ["yes", "authorized", "eligible"]:
                            best = o; break
                elif any(k in label for k in ["sponsorship", "visa"]):
                    for o in options:
                        if o["text"].lower() in ["no", "not required"]:
                            best = o; break

                if not best:
                    for o in options:
                        if o["text"].strip() and o["value"].strip() and o["text"].lower() not in ["select", "choose", "-", "none"]:
                            best = o; break

                if best:
                    sel.select_option(value=best["value"])
                    handled += 1
            except Exception:
                continue
        return handled

    def _handle_checkboxes_and_radios(self, page) -> int:
        checked = 0
        custom_switches = page.locator('button[data-state="unchecked"]').all()
        for sw in custom_switches:
            try:
                if sw.is_visible():
                    sw.click()
                    checked += 1
            except Exception:
                pass

        cbs = page.locator('input[type="checkbox"]:not(:checked)').all()
        for cb in cbs:
            try:
                if not cb.is_visible():
                    continue
                lbl = cb.evaluate('''el => {
                    let p = el.closest('label') || el.closest('.field-wrapper') || el.parentElement;
                    return p ? p.innerText.toLowerCase() : '';
                }''')
                # If this is a question with options (e.g. salary ranges), skip here to handle in question groups
                if any(k in lbl for k in ["per year", "per hour", "range", "annual"]):
                    continue
                cb.click()
                checked += 1
            except Exception:
                pass

        # Robust Radio Button Groups (handles Jobvite, Greenhouse, Workday, Lever)
        radios = page.locator('input[type="radio"]').all()
        radio_groups = {}
        for r in radios:
            try:
                if not r.is_visible():
                    continue
                name = r.get_attribute("name") or "unnamed"
                radio_groups.setdefault(name, []).append(r)
            except Exception:
                continue

        for name, group in radio_groups.items():
            try:
                # Check if an option in this radio group is already checked
                if any(r.is_checked() for r in group):
                    continue

                parent_txt = ""
                try:
                    parent_txt = group[0].evaluate('''el => {
                        let p = el.closest('.form-group, .field-wrapper, fieldset, tr, .radio-group, div') || el.parentElement;
                        return p ? p.innerText.toLowerCase() : '';
                    }''')
                except Exception:
                    pass

                chosen = None
                for r in group:
                    lbl = r.evaluate('''el => {
                        let p = el.closest('label') || el.parentElement;
                        return p ? p.innerText.toLowerCase() : '';
                    }''')
                    if any(k in parent_txt for k in ["sponsorship", "visa", "require sponsor"]):
                        if any(no_k in lbl for no_k in ["no", "never", "not require"]):
                            chosen = r
                            break
                    elif any(k in parent_txt for k in ["authorized", "eligible", "relocate", "driver", "travel", "license", "agree"]):
                        if "yes" in lbl or "authorized" in lbl:
                            chosen = r
                            break
                    elif "yes" in lbl:
                        chosen = r
                        break

                if not chosen and group:
                    # Default to first option so required radio validation passes
                    chosen = group[0]

                if chosen:
                    chosen.click(force=True)
                    checked += 1
            except Exception:
                continue

        return checked

    def _handle_segmented_button_toggles(self, page) -> int:
        """Handles button-based Yes/No toggles common in Ashby and Workday."""
        handled = 0
        try:
            btn_toggles = page.locator('button:has-text("Yes")').all()
            for btn in btn_toggles:
                try:
                    if not btn.is_visible():
                        continue
                    classes = btn.get_attribute("class") or ""
                    aria = btn.get_attribute("aria-pressed") or btn.get_attribute("aria-selected") or ""
                    if "active" in classes.lower() or aria == "true":
                        continue
                    txt = btn.inner_text().strip().lower()
                    if txt == "yes":
                        btn.click(force=True)
                        handled += 1
                except Exception:
                    continue
        except Exception:
            pass
        return handled

    def _handle_ashby_and_specialty_inputs(self, page):
        """Fills Ashby location combobox and date pickers."""
        try:
            # 1. Location combobox (e.g. 'Start typing...')
            loc_inputs = page.locator('input[placeholder*="Start typing" i]').all()
            for inp in loc_inputs:
                try:
                    if inp.is_visible() and not inp.input_value():
                        inp.click()
                        inp.fill(self.profile.get("location") or "Remote")
                        time.sleep(0.5)
                        inp.press("ArrowDown")
                        inp.press("Enter")
                except Exception:
                    pass

            # 2. Date pickers (e.g. 'Pick date...', 'Start date')
            date_inputs = page.locator('input[placeholder*="Pick date" i], input[placeholder*="YYYY" i], input[name*="start_date" i]').all()
            for d_inp in date_inputs:
                try:
                    if d_inp.is_visible() and not d_inp.input_value():
                        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%m/%d/%Y")
                        d_inp.fill(tomorrow)
                        d_inp.press("Enter")
                except Exception:
                    pass
        except Exception:
            pass

    def _handle_question_checkbox_groups(self, page):
        """Ensures question groups (e.g. Compensation range checkboxes on Greenhouse) have an option picked."""
        field_wrappers = page.locator('.field-wrapper, [class*="field"]').all()
        for fw in field_wrappers:
            try:
                if not fw.is_visible():
                    continue
                lbl = fw.inner_text().lower()
                cbs = fw.locator('input[type="checkbox"]').all()
                if len(cbs) > 1 and any(k in lbl for k in ["compensation", "salary", "experience", "required"]):
                    # Check if any is already checked
                    checked_cbs = fw.locator('input[type="checkbox"]:checked').count()
                    if checked_cbs == 0:
                        # Check the last option (e.g. $46,000 or more per year)
                        cbs[-1].click()
            except Exception:
                continue

    def _fill_remaining_required_fields(self, page):
        required_inputs = page.locator('input:invalid, textarea:invalid, [required]:not([type="checkbox"])').all()
        for el in required_inputs:
            try:
                if not el.is_visible():
                    continue
                if not el.input_value():
                    el.fill("N/A")
            except Exception:
                pass

    def _find_submit_button(self, target):
        submit_selectors = [
            'button:has-text("Submit application")',
            'button:has-text("Submit Application")',
            'input[type="submit"][value*="Submit" i]',
            'input[type="submit"][value*="Apply" i]',
            'button:has-text("Submit")',
            'button:has-text("Send Application")',
            'button:has-text("Apply now")',
            'input[type="submit"]',
            'button[type="submit"]',
            '#submit_app'
        ]
        for sel in submit_selectors:
            try:
                candidates = target.locator(sel).all()
                for btn in candidates:
                    if not btn.is_visible():
                        continue
                    btn_text = (btn.inner_text() or btn.get_attribute("value") or "").strip().lower()
                    if any(bad in btn_text for bad in ["log in", "sign in", "cookie", "search", "close", "cancel", "manage"]):
                        continue
                    return btn
            except Exception:
                continue
        return None

    def _find_progression_button(self, target):
        """
        Detects any intermediate progression button that advances a multi-step application form.
        Covers Next, Continue, Proceed, Review, Save & Next, Forward, Step, and dynamic attribute patterns.
        """
        progression_selectors = [
            # Standard explicit words
            'button:has-text("Next")', 'a:has-text("Next")',
            'button:has-text("Continue")', 'a:has-text("Continue")',
            'button:has-text("Proceed")', 'a:has-text("Proceed")',
            'button:has-text("Review and submit")', 'button:has-text("Review & submit")',
            'button:has-text("Review application")', 'button:has-text("Review Application")',
            'button:has-text("Review and continue")', 'button:has-text("Review & continue")',
            'button:has-text("Review")', 'a:has-text("Review")',
            'button:has-text("Save & continue")', 'button:has-text("Save and continue")',
            'button:has-text("Save & next")', 'button:has-text("Save and next")',
            'button:has-text("Save and Proceed")', 'button:has-text("Save & proceed")',
            'button:has-text("Next step")', 'a:has-text("Next step")',
            'button:has-text("Next Step")', 'a:has-text("Next Step")',
            'button:has-text("Next page")', 'button:has-text("Next Page")',
            'button:has-text("Go to next step")', 'button:has-text("Proceed to next step")',
            'button:has-text("Move forward")', 'button:has-text("Advance")',
            'button:has-text("Step 2")', 'button:has-text("Step 3")', 'button:has-text("Step 4")',
            'button:has-text("Agree & continue")', 'button:has-text("Accept & continue")',
            'button:has-text("Agree and continue")', 'button:has-text("Accept and continue")',
            'button:has-text("Next: ")', 'button:has-text("Next :")',
            
            # Form button/input values
            'input[type="button"][value*="Next" i]', 'input[type="submit"][value*="Next" i]',
            'input[type="button"][value*="Continue" i]', 'input[type="submit"][value*="Continue" i]',
            'input[type="button"][value*="Proceed" i]', 'input[type="submit"][value*="Proceed" i]',
            'input[type="button"][value*="Review" i]', 'input[type="submit"][value*="Review" i]',
            'input[type="button"][value*="Save" i]',
            
            # ARIA labels & data attributes
            '[aria-label*="next" i]', '[aria-label*="continue" i]', '[aria-label*="proceed" i]',
            '[aria-label*="forward" i]', '[aria-label*="review" i]',
            '[data-qa*="next" i]', '[data-qa*="continue" i]',
            '[data-testid*="next" i]', '[data-testid*="continue" i]',
            '[data-action*="next" i]', '[data-action*="continue" i]',
            '.btn-next', '.button-next', '.wizard-next', '.step-next',
            '#btn-next', '#button-next', '#next-button', '#next-step'
        ]

        for sel in progression_selectors:
            try:
                candidates = target.locator(sel).all()
                for cand in candidates:
                    if not cand.is_visible():
                        continue
                    txt = (cand.inner_text() or cand.get_attribute("value") or cand.get_attribute("aria-label") or "").strip().lower()
                    if any(bad in txt for bad in ["cookie", "cancel", "close", "sign in", "log in", "back", "previous", "delete"]):
                        continue
                    # Ensure it is not a final submit button
                    if any(s in txt for s in ["submit", "send application"]):
                        continue
                    return cand
            except Exception:
                continue

        # Dynamic DOM scan for any clickable element with progression keywords
        try:
            cand_info = target.evaluate('''() => {
                const elements = Array.from(document.querySelectorAll('button, a, input[type="button"], input[type="submit"], div[role="button"], span[role="button"]'));
                const keywords = ["next", "continue", "proceed", "review", "forward", "advance", "step", "save &", "save and"];
                const excludes = ["cookie", "cancel", "close", "sign in", "log in", "back", "previous", "delete", "clear", "submit"];
                for (let i = 0; i < elements.length; i++) {
                    const el = elements[i];
                    if (!el || el.offsetParent === null) continue;
                    const text = (el.innerText || el.value || el.getAttribute('aria-label') || '').trim().toLowerCase();
                    if (!text || text.length > 40) continue;
                    if (excludes.some(ex => text.includes(ex))) continue;
                    if (keywords.some(kw => text.includes(kw))) {
                        return { text: text, index: i };
                    }
                }
                return null;
            }''')
            if cand_info and cand_info.get("text"):
                found_text = cand_info["text"]
                loc = target.locator(f'button:has-text("{found_text}"), a:has-text("{found_text}"), [role="button"]:has-text("{found_text}")').first
                if loc.is_visible(timeout=500):
                    return loc
        except Exception:
            pass

        return None

    def _vision_detect_progression_button(self, page) -> str:
        """Uses the local Vision LLM to locate any progression button on screen if DOM heuristics missed it."""
        try:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            screen_path = os.path.join(self.log_dir, f"{ts}_multistep_check.png")
            page.screenshot(path=screen_path)
            prompt = (
                "Look at this job application form screenshot.\n"
                "Is there an active button to advance to the next step or review (e.g. Next, Continue, Proceed, Review, Save & Next, Forward, Step 2)?\n"
                "If YES, return ONLY the exact button text (e.g. 'Continue', 'Save & Proceed', 'Next').\n"
                "If NO or if this is the final Submit button, reply NONE."
            )
            resp = self._analyze_screenshot(screen_path, prompt)
            cleaned = resp.strip().strip("'\"").strip()
            if cleaned and "NONE" not in cleaned.upper() and len(cleaned) < 30:
                print(f"👁️ [Vision LLM ({self.vision_model})] Detected progression button text: '{cleaned}'", flush=True)
                return cleaned
        except Exception as e:
            print(f"⚠️ Vision progression check notice: {e}", flush=True)
        return ""

    def _submit_and_verify(self, target, page, company_name: str, job_title: str) -> dict:
        submit_btn = self._find_submit_button(target)

        # Multi-step wizard loop: advance through up to 5 steps while Submit is not yet visible
        step = 1
        max_steps = 5
        while not submit_btn and step <= max_steps:
            prog_btn = self._find_progression_button(target)
            if not prog_btn:
                # Fallback to Vision LLM to see if there is an advancement button
                v_btn_txt = self._vision_detect_progression_button(page)
                if v_btn_txt:
                    try:
                        cand = target.locator(f'button:has-text("{v_btn_txt}"), a:has-text("{v_btn_txt}"), [role="button"]:has-text("{v_btn_txt}")').first
                        if cand.is_visible(timeout=1000):
                            prog_btn = cand
                    except Exception:
                        pass

            if not prog_btn:
                # No more progression buttons found on this step
                break

            btn_txt = (prog_btn.inner_text() or prog_btn.get_attribute("value") or "").strip()
            print(f"⏩ [Step {step}] Advancing multi-step form with button: '{btn_txt}'", flush=True)
            try:
                prog_btn.click(force=True)
                time.sleep(2)
                self._wait_for_form_hydration(page)
                # Fill any new fields appearing on the next step
                self._upload_resume(target)
                self._fill_text_inputs(target)
                self._handle_react_and_custom_selects(target)
                self._fill_native_dropdowns(target)
                self._handle_checkboxes_and_radios(target)
                self._handle_question_checkbox_groups(target)
                self._handle_segmented_button_toggles(target)
                self._handle_ashby_and_specialty_inputs(target)
                self._fill_remaining_required_fields(target)

                # Scroll down to ensure submit button is in view
                try:
                    target.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    time.sleep(0.5)
                except Exception:
                    pass

                # Check if submit button is now visible
                submit_btn = self._find_submit_button(target)
                step += 1
            except Exception as e:
                print(f"⚠️ Error advancing step {step}: {e}", flush=True)
                break

        if not submit_btn:
            # Final scroll down attempt in case submit is at bottom of page
            try:
                target.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                time.sleep(1)
                submit_btn = self._find_submit_button(target)
            except Exception:
                pass
            print("🚫 No submit button found on page (portal directory, external index, or closed).", flush=True)
            return {
                "success": False,
                "message": "Submit button not found on page (not an application form or position closed)",
                "expired": True,
                "clicked_submit": False
            }

        try:
            if submit_btn.is_disabled():
                print("⚠️ Submit button initially disabled. Waiting 2s for validation...", flush=True)
                time.sleep(2)
                if submit_btn.is_disabled():
                    return {
                        "success": False,
                        "message": "Submit button remained disabled (required fields missing)",
                        "clicked_submit": False
                    }
        except Exception:
            pass

        submit_btn_txt = (submit_btn.inner_text() or submit_btn.get_attribute("value") or "").strip()
        print(f"🚀 Clicking Submit button: '{submit_btn_txt}'", flush=True)
        submit_btn.click(force=True)

        print("⏳ Waiting for submission confirmation...", flush=True)
        for _ in range(15):
            time.sleep(1)
            curr_url = page.url.lower()
            if any(k in curr_url for k in ["confirmation", "thank-you", "thank_you", "submitted", "success", "applied"]):
                print(f"🎉 Confirmed submission via URL: {curr_url}", flush=True)
                return {
                    "success": True,
                    "message": f"Application confirmed via URL: {curr_url}",
                    "confirmation_type": "url",
                    "clicked_submit": True
                }

            body_text = page.locator("body").inner_text().lower()
            if any(k in body_text for k in [
                "thank you for applying",
                "application submitted",
                "we have received your application",
                "we've received your application",
                "your application was submitted",
                "successfully applied",
                "application received",
                "thanks for applying"
            ]):
                print("🎉 Confirmed submission via on-screen message!", flush=True)
                return {
                    "success": True,
                    "message": "Application confirmed via on-screen message",
                    "confirmation_type": "screen_text",
                    "clicked_submit": True
                }

        body_text = page.locator("body").inner_text().lower()
        if any(e in body_text for e in [
            "could not be saved", "can't be blank", "please fill in", "field is required",
            "phone is invalid", "invalid phone", "please correct the errors",
            "please review the errors", "there was a problem with your submission"
        ]):
            return {
                "success": False,
                "message": "Form validation error (required fields or phone validation)",
                "clicked_submit": True
            }

        return {
            "success": True,
            "message": "Form submitted successfully (submission initiated without errors)",
            "confirmation_type": "form_submitted",
            "clicked_submit": True
        }

def run_external_apply(application_link: str, cv_data: str = "", company_name: str = "", job_title: str = "") -> dict:
    headless_setting = os.environ.get("HEADLESS_MODE", "True").lower() == "true"
    engine = ExternalApplyEngine(headless=headless_setting)
    res = engine.apply_to_job(application_link, job_title=job_title, company_name=company_name)
    print(f"🏁 Final Result: {res}", flush=True)
    return res

if __name__ == "__main__":
    test_url = sys.argv[1] if len(sys.argv) > 1 else "https://job-boards.greenhouse.io/particle41llc/jobs/4499232008?gh_src=f730200f8us"
    engine = ExternalApplyEngine(headless=True)
    result = engine.apply_to_job(test_url, company_name="Particle41", job_title="DevOps Engineer")
    print("Result:", result, flush=True)
