import os
import sys
import re
import time
import json
from datetime import datetime
import requests
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
        self.log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs", "external_applications")
        os.makedirs(self.log_dir, exist_ok=True)

    def apply_to_job(self, application_url: str, job_title: str = "", company_name: str = "") -> dict:
        print(f"\n=======================================================", flush=True)
        print(f"🚀 [ExternalApplyEngine] Processing: {application_url}", flush=True)
        print(f"Candidate: {self.profile['full_name']} ({self.profile['email']})", flush=True)
        print(f"Resume: {self.profile['resume_path']}", flush=True)
        print(f"=======================================================", flush=True)

        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=self.headless,
                args=["--disable-blink-features=AutomationControlled"]
            )
            context = browser.new_context(
                viewport={"width": 1280, "height": 900},
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
            )
            page = context.new_page()

            try:
                # 1. Navigate to the job application URL
                try:
                    page.goto(application_url, wait_until="domcontentloaded", timeout=35000)
                except PlaywrightTimeoutError:
                    print("⚠️ Page load timed out on domcontentloaded, continuing...", flush=True)

                time.sleep(2)

                # 2. Handle initial Apply button if on job description page
                self._handle_initial_apply_button(page)

                # 3. Wait for dynamic form hydration (Manatal, Greenhouse, Ashby, Lever, etc.)
                self._wait_for_form_hydration(page)

                # 4. Upload Resume
                uploaded = self._upload_resume(page)
                print(f"📄 Resume upload: {'Success' if uploaded else 'None found/already attached'}", flush=True)

                # 5. Fill Text, Tel, and Email Fields
                filled_count = self._fill_text_inputs(page)
                print(f"✍️ Filled {filled_count} text/email/tel inputs", flush=True)

                # 6. Handle React-Select and Custom UI Comboboxes
                custom_selects = self._handle_react_and_custom_selects(page)
                print(f"🔽 Handled {custom_selects} custom/React selects", flush=True)

                # 7. Handle Native Dropdowns (<select>)
                native_selects = self._fill_native_dropdowns(page)
                print(f"🔽 Handled {native_selects} native dropdown selects", flush=True)

                # 8. Handle Checkboxes, Toggles, and Radios
                cb_count = self._handle_checkboxes_and_radios(page)
                print(f"☑️ Checked {cb_count} consent/authorization options", flush=True)

                # 9. Handle Checkbox question groups (e.g. Salary ranges, preferences)
                self._handle_question_checkbox_groups(page)

                # 10. Fill any remaining invalid / required fields with defaults
                self._fill_remaining_required_fields(page)

                # 11. Pre-submission screenshot
                ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                safe_slug = re.sub(r'[^a-zA-Z0-9]', '_', company_name or "external_job")[:25]
                pre_screen = os.path.join(self.log_dir, f"{ts}_{safe_slug}_filled.png")
                page.screenshot(path=pre_screen, full_page=True)
                print(f"📸 Saved pre-submission screenshot: {pre_screen}", flush=True)

                # 12. Submit & Verify
                submit_res = self._submit_and_verify(page, company_name, job_title)

                # 13. Post-submission screenshot
                post_screen = os.path.join(self.log_dir, f"{ts}_{safe_slug}_submitted.png")
                try:
                    page.screenshot(path=post_screen, full_page=True)
                except Exception:
                    pass

                browser.close()
                submit_res["screenshot"] = post_screen
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

    def _handle_initial_apply_button(self, page):
        has_form = page.locator('input[type="file"], input[name*="name" i], #first_name, #_systemfield_name').count() > 0
        if not has_form:
            for sel in [
                'button:has-text("Apply for this job")', 'a:has-text("Apply for this job")',
                'button:has-text("Apply now")', 'a:has-text("Apply now")',
                'button:has-text("Apply")', 'a:has-text("Apply")',
                '[data-qa="apply-button"]', '#apply_button', '.apply-button'
            ]:
                try:
                    btn = page.locator(sel).first
                    if btn.is_visible(timeout=1500):
                        print(f"👉 Clicking landing page Apply button: '{btn.inner_text().strip()}'", flush=True)
                        btn.click()
                        time.sleep(2)
                        break
                except Exception:
                    continue

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
                time.sleep(1.5)
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

                if any(k in full_desc for k in ["first name", "firstname", "given name", "first_name"]):
                    val = self.profile["first_name"]
                elif any(k in full_desc for k in ["last name", "lastname", "family name", "surname", "last_name"]):
                    val = self.profile["last_name"]
                elif any(k in full_desc for k in ["full name", "fullname", "your name", "_systemfield_name", "candidate name"]) or (
                    "name" in full_desc and not any(x in full_desc for x in ["company", "user", "file", "school", "hr"])
                ):
                    val = self.profile["full_name"]
                elif any(k in full_desc for k in ["email", "e-mail", "@"]):
                    val = self.profile["email"]
                elif any(k in full_desc for k in ["phone", "mobile", "telephone", "tel", "cell"]):
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
                elif ctx["tag"] == "textarea" or any(k in full_desc for k in ["cover letter", "about yourself", "summary", "additional information"]):
                    val = self.profile["summary"]

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

        # B. Custom dropdown buttons (Radix UI / Careers-page)
        custom_triggers = page.locator('button[role="combobox"], button:has-text("-"), [class*="select-trigger"]').all()
        for trigger in custom_triggers:
            try:
                if not trigger.is_visible():
                    continue
                btn_text = trigger.inner_text().strip()
                if btn_text and btn_text not in ["-", "Select...", "Select", "Please select", "Choose option"]:
                    continue

                trigger.click()
                time.sleep(0.5)

                menu_options = page.locator('[role="option"]:visible, [role="menuitem"]:visible, li.select2-results__option:visible').all()
                if menu_options:
                    picked = False
                    for opt in menu_options:
                        txt = opt.inner_text().strip().lower()
                        if any(good in txt for good in ["linkedin", "yes", "website", "authorized", "referral"]):
                            opt.click()
                            picked = True
                            handled += 1
                            break
                    if not picked and len(menu_options) > 1:
                        menu_options[1].click()
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

        radios = page.locator('input[type="radio"]').all()
        for r in radios:
            try:
                if not r.is_visible():
                    continue
                label_txt = r.evaluate('''el => {
                    let p = el.closest('label') || el.parentElement;
                    return (p ? p.innerText : '').toLowerCase();
                }''')
                if label_txt in ["yes", "true", "authorized"]:
                    r.click()
                    checked += 1
            except Exception:
                pass

        return checked

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

    def _submit_and_verify(self, page, company_name: str, job_title: str) -> dict:
        submit_selectors = [
            'button[type="submit"]',
            'input[type="submit"]',
            'button:has-text("Submit Application")',
            'button:has-text("Submit application")',
            'button:has-text("Apply now")',
            'button:has-text("Submit")',
            'button:has-text("Send Application")',
            '#submit_app'
        ]

        submit_btn = None
        for sel in submit_selectors:
            try:
                btn = page.locator(sel).first
                if btn.is_visible(timeout=1000):
                    submit_btn = btn
                    break
            except Exception:
                continue

        if not submit_btn:
            return {"success": False, "message": "Submit button not found on page"}

        try:
            if submit_btn.is_disabled():
                print("⚠️ Submit button initially disabled. Waiting 2s for validation...", flush=True)
                time.sleep(2)
                if submit_btn.is_disabled():
                    return {"success": False, "message": "Submit button remained disabled (required fields missing)"}
        except Exception:
            pass

        print(f"🚀 Clicking Submit button: '{submit_btn.inner_text().strip()}'", flush=True)
        submit_btn.click()

        print("⏳ Waiting for submission confirmation...", flush=True)
        for _ in range(15):
            time.sleep(1)
            curr_url = page.url.lower()
            if any(k in curr_url for k in ["confirmation", "thank-you", "thank_you", "submitted", "success", "applied"]):
                print(f"🎉 Confirmed submission via URL: {curr_url}", flush=True)
                return {
                    "success": True,
                    "message": f"Application confirmed via URL: {curr_url}",
                    "confirmation_type": "url"
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
                    "confirmation_type": "screen_text"
                }

        body_text = page.locator("body").inner_text().lower()
        if "error" in body_text and any(e in body_text for e in ["required", "missing", "invalid", "captcha"]):
            return {"success": False, "message": "Submission error or captcha present on page"}

        return {
            "success": True,
            "message": "Form submitted successfully (submission initiated without errors)",
            "confirmation_type": "form_submitted"
        }

def run_external_apply(application_link: str, cv_data: str = "", company_name: str = "", job_title: str = "") -> bool:
    headless_setting = os.environ.get("HEADLESS_MODE", "True").lower() == "true"
    engine = ExternalApplyEngine(headless=headless_setting)
    res = engine.apply_to_job(application_link, job_title=job_title, company_name=company_name)
    print(f"🏁 Final Result: {res}", flush=True)
    return res.get("success", False)

if __name__ == "__main__":
    test_url = sys.argv[1] if len(sys.argv) > 1 else "https://job-boards.greenhouse.io/particle41llc/jobs/4499232008?gh_src=f730200f8us"
    engine = ExternalApplyEngine(headless=True)
    result = engine.apply_to_job(test_url, company_name="Particle41", job_title="DevOps Engineer")
    print("Result:", result, flush=True)
