import os
import sys
import time
import base64
import csv
import json
import warnings
from datetime import datetime, timedelta

# Suppress annoying Python 3.9 & API deprecation warnings from Google libraries
warnings.filterwarnings('ignore')

# Ensure the root directory is in the path so we can import 'config'
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    from bs4 import BeautifulSoup
except ImportError:
    raise Exception("❌ Missing Gmail dependencies. Please run: ./venv/bin/pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib beautifulsoup4")

from config.secrets import llm_api_key, llm_model, ai_provider, llm_api_url
try:
    from config.secrets import gmail_ai_model
except ImportError:
    gmail_ai_model = "qwen3:1.7b"

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
CSV_PATH = os.path.join(PROJECT_ROOT, 'all excels', 'all_applied_applications_history.csv')
TOKEN_PATH = os.path.join(PROJECT_ROOT, 'token.json')
CREDENTIALS_PATH = os.path.join(PROJECT_ROOT, 'credentials.json')

def get_gmail_service():
    creds = None
    if os.path.exists(TOKEN_PATH):
        try:
            creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
        except Exception as e:
            print(f"⚠️ Error reading {TOKEN_PATH}: {e}", flush=True)
            creds = None

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                print("🔄 Refreshing expired Gmail OAuth token...", flush=True)
                creds.refresh(Request())
                print("✅ Gmail OAuth token refreshed successfully.", flush=True)
            except Exception as e:
                print(f"⚠️ Gmail token refresh failed: {e}. Clearing stale token and re-authenticating...", flush=True)
                creds = None
                if os.path.exists(TOKEN_PATH):
                    try:
                        os.remove(TOKEN_PATH)
                    except OSError:
                        pass

        if not creds or not creds.valid:
            if not os.path.exists(CREDENTIALS_PATH):
                print(f"❌ ERROR: credentials.json not found at {CREDENTIALS_PATH}!", flush=True)
                print("Please download it from Google Cloud Console and place it in the project root.", flush=True)
                return None
            print("🔐 Opening browser for Gmail authorization. Please approve access...", flush=True)
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)
            print("✅ Gmail authorization completed! Saving fresh token.json...", flush=True)
            with open(TOKEN_PATH, 'w') as token:
                token.write(creds.to_json())

    return build('gmail', 'v1', credentials=creds)

def extract_body(payload):
    if 'parts' in payload:
        for part in payload['parts']:
            if part['mimeType'] == 'text/plain':
                return base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
            elif part['mimeType'] == 'text/html':
                html = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                return BeautifulSoup(html, 'html.parser').get_text()
    elif 'body' in payload and 'data' in payload['body']:
        return base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8')
    return ""

def analyze_email_with_ai(subject, body):
    prompt = f"""Classify this recruitment email into JSON.
Subject: {subject}
Body: {body[:3500]}

Choose status from: "In Review", "Interview", "Accepted", "Rejected", "Unknown".
- "In Review": application sent, received, under review, or viewed
- "Interview": invitation to interview, screening, assessment, or test
- "Accepted": job offer received, welcome aboard
- "Rejected": not moving forward, application declined, position filled

Example output:
{{"company": "Acme Corp", "title": "DevOps Engineer", "status": "In Review"}}

Output ONLY JSON:"""

    model_name = os.environ.get("GMAIL_OLLAMA_MODEL", gmail_ai_model or "qwen3:1.7b")
    api_base = os.environ.get("OLLAMA_API_URL", "http://localhost:11434")

    try:
        if ai_provider == "gemini":
            time.sleep(4.5)
            import google.generativeai as genai
            genai.configure(api_key=llm_api_key)
            model = genai.GenerativeModel(llm_model)
            response = model.generate_content(prompt)
            text = response.text.strip()
        else:
            import urllib.request
            base_endpoint = api_base.rstrip('/').replace('/v1', '')
            ollama_url = f"{base_endpoint}/api/generate"
            payload = {
                "model": model_name,
                "prompt": prompt,
                "stream": False,
                "format": "json"
            }
            req = urllib.request.Request(
                ollama_url,
                data=json.dumps(payload).encode('utf-8'),
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                resp_data = json.loads(resp.read().decode('utf-8'))
                text = resp_data.get('response', '').strip()

        # Robust JSON extraction (strips <think> tags if model produces reasoning)
        import re
        text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL).strip()
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            text = json_match.group(0)
            
        return json.loads(text)
    except Exception as e:
        error_msg = str(e)
        print(f"⚠️ Error parsing email with AI ({model_name}): {error_msg.splitlines()[0]}")
        return None

def fetch_recent_emails(service, days_to_scan=1):
    # Fetch emails from the specified number of days back
    date_query = (datetime.now() - timedelta(days=days_to_scan)).strftime('%Y/%m/%d')
    query = f"after:{date_query} (application OR interview OR rejected OR offer OR update OR applicant)"
    results = service.users().messages().list(userId='me', q=query).execute()
    messages = results.get('messages', [])
    parsed_emails = []

    for msg in messages:
        try:
            msg_data = service.users().messages().get(userId='me', id=msg['id'], format='full').execute()
            headers = msg_data['payload']['headers']
            subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), 'No Subject')
            body = extract_body(msg_data['payload'])
            # Direct permanent link to open the exact email in Gmail web UI
            raw_msg_id = next((h['value'] for h in headers if h['name'].lower() == 'message-id'), '')
            if raw_msg_id:
                clean_msg_id = raw_msg_id.strip('<> ')
                import urllib.parse
                email_link = f"https://mail.google.com/mail/?authuser=shirishmaharjan0@gmail.com#search/rfc822msgid%3A{urllib.parse.quote(clean_msg_id)}"
            else:
                import urllib.parse
                quoted_subject = urllib.parse.quote('"' + subject + '"')
                email_link = f"https://mail.google.com/mail/?authuser=shirishmaharjan0@gmail.com#search/subject%3A{quoted_subject}"
            
            analysis = analyze_email_with_ai(subject, body)
            if analysis and analysis.get('status') in ['Accepted', 'Interview', 'In Review', 'Rejected']:
                analysis['raw_text'] = (subject + " " + body).lower()
                analysis['email_link'] = email_link
                analysis['email_subject'] = subject
                parsed_emails.append(analysis)
                print(f"Detected update: {analysis.get('company')} -> {analysis.get('status')} (Subject: {subject})", flush=True)
        except Exception as err:
            print(f"⚠️ Could not parse message: {err}", flush=True)
            
    return parsed_emails

def update_csv_statuses(updates):
    if not updates or not os.path.exists(CSV_PATH):
        return 0
        
    rows = []
    updated_count = 0
    with open(CSV_PATH, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames or [])
        if 'Status' not in fieldnames:
            fieldnames.append('Status')
        if 'Email Link' not in fieldnames:
            fieldnames.append('Email Link')
        if 'Email Subject' not in fieldnames:
            fieldnames.append('Email Subject')
            
        for row in reader:
            ext = (row.get('External Job link') or '').strip()
            current_status = (row.get('Status') or '').strip()
            
            # External jobs must never default to 'Applied' (Easy Applied)
            if not current_status or (ext != 'Easy Applied' and current_status == 'Applied'):
                if ext == 'Easy Applied':
                    row['Status'] = 'Applied'
                elif ext:
                    row['Status'] = 'Apply Externally'
                else:
                    row['Status'] = 'Applied'
            if 'Email Link' not in row:
                row['Email Link'] = ''
            if 'Email Subject' not in row:
                row['Email Subject'] = ''
                
            for update in updates:
                company_name = update.get('company', '').strip()
                csv_company = (row.get('Company') or '').lower()
                is_match = False
                
                if company_name and (company_name.lower() in csv_company or csv_company in company_name.lower()):
                    is_match = True
                # Fallback: if AI failed to get company, check if the CSV company name is directly in the raw email text
                elif len(csv_company) > 3 and csv_company in update.get('raw_text', ''):
                    is_match = True
                    
                if is_match:
                    current_status = row.get('Status', 'Applied')
                    matched = False
                    
                    if update['status'] == 'Accepted':
                        row['Status'] = 'Accepted'
                        matched = True
                    elif update['status'] == 'Rejected':
                        row['Status'] = 'Rejected'
                        matched = True
                    elif update['status'] == 'Interview' and current_status != 'Rejected' and current_status != 'Accepted':
                        row['Status'] = 'Interview'
                        matched = True
                    elif update['status'] == 'In Review' and current_status not in ['Rejected', 'Interview', 'Accepted']:
                        row['Status'] = 'In Review'
                        matched = True
                        
                    if matched:
                        row['Email Link'] = update.get('email_link', '')
                        row['Email Subject'] = update.get('email_subject', '')
                        updated_count += 1
                        break
                        
            rows.append(row)
            
    if updated_count > 0:
        with open(CSV_PATH, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        print(f"✅ Updated {updated_count} application statuses in CSV based on Gmail.", flush=True)
    return updated_count

def run_gmail_tracker(days_to_scan=1):
    print(f"\n--- Running Gmail Application Status Tracker (Last {days_to_scan} Days) ---", flush=True)
    try:
        service = get_gmail_service()
        if not service:
            print("❌ Skipping Gmail tracker: could not initialize Gmail service.", flush=True)
            return {"success": False, "error": "Could not initialize Gmail service. Check credentials.json / token.json", "updated": 0}
            
        print(f"Scanning recent emails from the last {days_to_scan} day(s) for application updates...", flush=True)
        updates = fetch_recent_emails(service, days_to_scan)
        count = update_csv_statuses(updates)
        print("--- Gmail Tracker Complete ---\n", flush=True)
        return {"success": True, "updated": count or 0, "found_updates": len(updates)}
    except Exception as e:
        import traceback
        print(f"❌ Error in Gmail Tracker: {e}", flush=True)
        traceback.print_exc()
        return {"success": False, "error": str(e), "updated": 0}

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Gmail Application Status Tracker')
    parser.add_argument('--days', type=int, default=1, help='Number of days to scan back for emails')
    args = parser.parse_args()
    
    run_gmail_tracker(args.days)
