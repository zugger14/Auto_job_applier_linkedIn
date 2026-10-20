import csv
import os
import json
import warnings
import time
import multiprocessing
import requests

multiprocessing.set_start_method("spawn", force=True)
warnings.filterwarnings('ignore', message='resource_tracker: There appear to.*', category=UserWarning)

from datetime import datetime
import config.questions as cq
import config.secrets as cs
from modules.external_apply_engine import run_external_apply

COUNTER_FILE = os.path.join(os.path.abspath(os.path.dirname(__file__)), "monitor_counts.json")

MAX_RETRIES = 3  # Max attempts per external job

def is_url_reachable(url: str, timeout: int = 5) -> bool:
    """Check if a URL is reachable using a HEAD request."""
    try:
        resp = requests.head(url, allow_redirects=True, timeout=timeout)
        return resp.status_code < 400
    except Exception:
        return False

def load_counters():
    if not os.path.exists(COUNTER_FILE):
        # initialise with zero counts for today
        data = {"date": datetime.now().strftime("%Y-%m-%d"), "linkedin": 0, "external": 0}
        with open(COUNTER_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f)
        return data
    try:
        with open(COUNTER_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        data = {"date": datetime.now().strftime("%Y-%m-%d"), "linkedin": 0, "external": 0}
    # reset if day changed
    if data.get("date") != datetime.now().strftime("%Y-%m-%d"):
        data = {"date": datetime.now().strftime("%Y-%m-%d"), "linkedin": 0, "external": 0}
    return data

def save_counters(data):
    with open(COUNTER_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f)

def run_batch_apply():
    csv_path = 'all excels/all_applied_applications_history.csv'

    if not os.path.exists(csv_path):
        print(f"Error: {csv_path} not found.")
        return

    try:
        with open(csv_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            fieldnames = reader.fieldnames
            rows = list(reader)
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return

    # Ensure CSV has a 'Failed Attempts' column and clean rows
    if 'Failed Attempts' not in fieldnames:
        fieldnames.append('Failed Attempts')
        for row in rows:
            row['Failed Attempts'] = '0'
    else:
        for row in rows:
            val = row.get('Failed Attempts')
            if val is None or not str(val).strip().isdigit():
                row['Failed Attempts'] = '0'

    def get_failed_attempts(row_dict):
        raw_val = row_dict.get('Failed Attempts')
        if raw_val is None:
            return 0
        try:
            return int(str(raw_val).strip())
        except (ValueError, TypeError):
            return 0

    external_jobs = []
    for i, row in enumerate(rows):
        ext_link = row.get('External Job link', '')
        status = row.get('Status', '')
        failed_attempts = get_failed_attempts(row)
        # Only apply if it hasn't been applied externally yet, not closed, and hasn't exceeded max retries
        if ext_link and ext_link != 'Easy Applied' and status not in ['Externally Applied', 'Position Closed'] and failed_attempts < MAX_RETRIES:
            # Clean and ensure URL scheme
            sanitized_link = ext_link.strip()
            if not sanitized_link.lower().startswith(('http://', 'https://')):
                sanitized_link = f"https://{sanitized_link}"
            if is_url_reachable(sanitized_link):
                if 'example.com' in sanitized_link:
                    print(f"⚠️ Skipping placeholder URL: {sanitized_link}")
                    row['Failed Attempts'] = str(failed_attempts + 1)
                    continue
                external_jobs.append((i, sanitized_link))
            else:
                print(f"⚠️ Skipping unreachable URL: {sanitized_link}")
                row['Failed Attempts'] = str(failed_attempts + 1)
                # Write out the updated failure count immediately
                with open(csv_path, 'w', encoding='utf-8', newline='') as file:
                    writer = csv.DictWriter(file, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(rows)

    print(f"Found {len(external_jobs)} external jobs to apply to.")

    counters = load_counters()
    for count, (row_idx, link) in enumerate(external_jobs):
        # Enforce daily external limit (20)
        if counters.get('external', 0) >= 20:
            print("⚡ Daily limit of 20 external jobs reached. Stopping further applications.")
            break
        print(f"\n[{count+1}/{len(external_jobs)}] Starting External Apply Engine for: {link}")
        comp = rows[row_idx].get('Company Name', '')
        title = rows[row_idx].get('Job Title', '')
        attempt_success = False
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                result = run_external_apply(link, cv_data=cq.user_information_all, company_name=comp, job_title=title)
                if isinstance(result, bool):
                    result = {"success": result, "message": "Form submitted" if result else "Failed"}

                if result.get("expired"):
                    print(f"🚫 Position closed or no application form found on company portal.")
                    print(f"   Marked as 'Position Closed'. Skipping retries.")
                    rows[row_idx]['Status'] = 'Position Closed'
                    rows[row_idx]['Failed Attempts'] = '0'
                    attempt_success = True
                    break

                if result.get("success"):
                    print(f"✅ Successfully applied externally on attempt {attempt}! ({result.get('message', 'Applied')})")
                    rows[row_idx]['Status'] = 'Externally Applied'
                    rows[row_idx]['Date Applied'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    rows[row_idx]['Failed Attempts'] = '0'
                    # Increment external counter and persist
                    counters['external'] = counters.get('external', 0) + 1
                    save_counters(counters)
                    attempt_success = True
                    break
                else:
                    msg = result.get('message', 'Form incomplete or submission error')
                    print(f"⚠️ Attempt {attempt}/{MAX_RETRIES} did not complete: {msg}")
            except Exception as e:
                print(f"⚠️ Attempt {attempt} error: {e}")
            # exponential backoff before next retry
            time.sleep(2 ** attempt)
        if not attempt_success:
            # Increment failed attempts counter
            failed = get_failed_attempts(rows[row_idx]) + 1
            rows[row_idx]['Failed Attempts'] = str(failed)
            print(f"⚠️ All {MAX_RETRIES} attempts failed. Marked Failed Attempts = {failed}")
        # Write back to CSV after each job (whether success or not)
        with open(csv_path, 'w', encoding='utf-8', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        print("Waiting 5 seconds before next application...")
        time.sleep(5)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Apply to external job links.')
    parser.add_argument('--headful', action='store_true', help='Run Playwright in headed mode for debugging')
    args = parser.parse_args()
    # Set environment variable for headless mode used by crewai_agent
    os.environ['HEADLESS_MODE'] = 'False' if args.headful else 'True'
    try:
        run_batch_apply()
    finally:
        for child in multiprocessing.active_children():
            child.terminate()
            child.join()
