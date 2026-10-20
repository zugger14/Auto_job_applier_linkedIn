from __future__ import annotations
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import csv
from datetime import datetime, timedelta
import shutil
import os

app = Flask(__name__)
CORS(app)

PATH = 'all excels/'
##> ------ Karthik Sarode : karthik.sarode23@gmail.com - UI for excel files ------
@app.route('/')
def home():
    """Displays the home page of the application."""
    return render_template('index.html')

@app.route('/applied-jobs', methods=['GET'])
def get_applied_jobs():
    '''
    Retrieves a list of applied jobs from the applications history CSV file.
    
    Returns a JSON response containing a list of jobs, each with details such as 
    Job ID, Title, Company, HR Name, HR Link, Job Link, External Job link, and Date Applied.
    
    If the CSV file is not found, returns a 404 error with a relevant message.
    If any other exception occurs, returns a 500 error with the exception message.
    '''

    try:
        jobs = []
        with open(PATH + 'all_applied_applications_history.csv', 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                job_data = {
                    'Job_ID': row.get('Job ID', ''),
                    'Title': row.get('Title', ''),
                    'Company': row.get('Company', ''),
                    'HR_Name': row.get('HR Name', ''),
                    'HR_Link': row.get('HR Link', ''),
                    'Job_Link': row.get('Job Link', ''),
                    'External_Job_link': row.get('External Job link', ''),
                    'Date_Applied': row.get('Date Applied', ''),
                    'Date_Posted': row.get('Date Posted', ''),
                    'Email_Link': row.get('Email Link', '') or row.get('Email_Link', ''),
                    'Email_Subject': row.get('Email Subject', '') or row.get('Email_Subject', ''),
                }
                
                status = (row.get('Status') or '').strip()
                ext_link = (row.get('External Job link') or '').strip()
                
                # Ensure external jobs are never default-labeled as 'Applied' (Easy Applied)
                if ext_link and ext_link != 'Easy Applied':
                    if not status or status == 'Applied':
                        status = 'Apply Externally'
                else:
                    if not status:
                        status = 'Applied'
                
                job_data['Status'] = status
                jobs.append(job_data)
                
        return jsonify(jobs)
    except FileNotFoundError:
        return jsonify({"error": "No applications history found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/applied-jobs/<job_id>', methods=['PUT'])
def update_applied_date(job_id):
    """
    Updates the 'Date Applied' field of a job in the applications history CSV file.

    Args:
        job_id (str): The Job ID of the job to be updated.

    Returns:
        A JSON response with a message indicating success or failure of the update
        operation. If the job is not found, returns a 404 error with a relevant
        message. If any other exception occurs, returns a 500 error with the
        exception message.
    """
    try:
        data = []
        csvPath = PATH + 'all_applied_applications_history.csv'
        
        if not os.path.exists(csvPath):
            return jsonify({"error": f"CSV file not found at {csvPath}"}), 404
            
        # Read current CSV content
        with open(csvPath, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            fieldNames = reader.fieldnames
            found = False
            for row in reader:
                if row['Job ID'] == job_id:
                    row['Date Applied'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    found = True
                data.append(row)
        
        if not found:
            return jsonify({"error": f"Job ID {job_id} not found"}), 404

        with open(csvPath, 'w', encoding='utf-8', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=fieldNames)
            writer.writeheader()
            writer.writerows(data)
        
        return jsonify({"message": "Date Applied updated successfully"}), 200
    except Exception as e:
        print(f"Error updating applied date: {str(e)}")  # Debug log
        return jsonify({"error": str(e)}), 500

@app.route('/failed-jobs', methods=['GET'])
def get_failed_jobs():
    '''
    Retrieves a list of failed applications from the failed applications history CSV file.
    '''
    try:
        failed_jobs = []
        csv_path = os.path.join(PATH, 'all_failed_applications_history.csv')
        if not os.path.exists(csv_path):
            return jsonify([])

        with open(csv_path, 'r', encoding='utf-8', errors='ignore') as file:
            reader = csv.DictReader(file)
            for row in reader:
                failed_jobs.append({
                    'Job_ID': row.get('Job ID', ''),
                    'Job_Link': row.get('Job Link', ''),
                    'Resume_Tried': row.get('Resume Tried', ''),
                    'Date_Listed': row.get('Date listed', ''),
                    'Date_Tried': row.get('Date Tried', ''),
                    'Assumed_Reason': row.get('Assumed Reason', 'Unknown error'),
                    'External_Job_link': row.get('External Job link', ''),
                    'Screenshot_Name': row.get('Screenshot Name', '')
                })
        return jsonify(failed_jobs)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/applied-jobs/<job_id>/status', methods=['PUT'])
def update_job_status(job_id):
    """
    Updates the 'Status' field of a job (e.g., 'Rejected', 'Interview', 'In Review', 'Accepted').
    """
    try:
        req_data = request.get_json() or {}
        new_status = req_data.get('status')
        if not new_status:
            return jsonify({"error": "Missing 'status' in request body"}), 400

        csvPath = os.path.join(PATH, 'all_applied_applications_history.csv')
        if not os.path.exists(csvPath):
            return jsonify({"error": "Applications CSV file not found"}), 404

        data = []
        found = False
        with open(csvPath, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            fieldNames = reader.fieldnames
            if 'Status' not in fieldNames:
                fieldNames.append('Status')
            for row in reader:
                if row.get('Job ID') == job_id:
                    row['Status'] = new_status
                    found = True
                data.append(row)

        if not found:
            return jsonify({"error": f"Job ID {job_id} not found"}), 404

        with open(csvPath, 'w', encoding='utf-8', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=fieldNames)
            writer.writeheader()
            writer.writerows(data)

        return jsonify({"message": f"Status updated to {new_status} successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/stats', methods=['GET'])
def get_stats():
    '''
    Computes summary KPI stats across applied, accepted/interviews, and rejected records.
    '''
    try:
        applied_count = 0
        easy_applied_count = 0
        external_count = 0
        failed_count = 0
        rejected_count = 0
        accepted_count = 0
        in_review_count = 0

        applied_csv = os.path.join(PATH, 'all_applied_applications_history.csv')
        if os.path.exists(applied_csv):
            with open(applied_csv, 'r', encoding='utf-8', errors='ignore') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    applied_count += 1
                    ext = row.get('External Job link', '')
                    status = (row.get('Status') or '').strip().lower()

                    if 'reject' in status:
                        rejected_count += 1
                    elif 'interview' in status or 'accept' in status or 'offer' in status:
                        accepted_count += 1
                    elif 'review' in status:
                        in_review_count += 1

                    if ext == 'Easy Applied':
                        easy_applied_count += 1
                    elif ext:
                        external_count += 1

        failed_csv = os.path.join(PATH, 'all_failed_applications_history.csv')
        if os.path.exists(failed_csv):
            with open(failed_csv, 'r', encoding='utf-8', errors='ignore') as f:
                reader = csv.DictReader(f)
                for _ in reader:
                    failed_count += 1

        total_attempts = applied_count + failed_count
        success_rate = round((applied_count / total_attempts * 100), 1) if total_attempts > 0 else 0

        return jsonify({
            'total_applied': applied_count,
            'easy_applied': easy_applied_count,
            'external_apply': external_count,
            'total_failed': failed_count,
            'rejected': rejected_count,
            'accepted': accepted_count,
            'in_review': in_review_count,
            'success_rate': success_rate
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/scan-gmail', methods=['POST'])
def scan_gmail():
    """
    Triggers the Gmail Application Status Tracker using local Ollama (qwen3:1.7b)
    to classify email updates (Accepted, Interview, In Review, Rejected) and update CSV.
    """
    try:
        from modules.gmail_tracker import run_gmail_tracker
        req = request.get_json() or {}
        days = int(req.get('days', 7))
        print(f"\n[Dashboard] 📨 Received request to scan Gmail with Ollama qwen3:1.7b (last {days} days)...", flush=True)
        result = run_gmail_tracker(days_to_scan=days)
        print(f"[Dashboard] 📨 Gmail Scan Finished. Result: {result}", flush=True)
        if not result.get('success', False):
            return jsonify(result), 400
        return jsonify(result)
    except Exception as e:
        import traceback
        print(f"❌ [Dashboard] Exception in /scan-gmail: {e}", flush=True)
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500

_external_apply_running = False

@app.route('/apply-external', methods=['POST'])
def apply_external():
    """
    Triggers the robust Playwright-based external apply engine in the background.
    """
    global _external_apply_running
    if _external_apply_running:
        return jsonify({"success": True, "running": True, "message": "External application batch is already in progress."})

    def run_worker():
        global _external_apply_running
        _external_apply_running = True
        try:
            print("\n[Dashboard] 🚀 Triggering batch external application worker...", flush=True)
            from apply_external_jobs import run_batch_apply
            run_batch_apply()
            print("[Dashboard] ✅ Batch external application worker finished.", flush=True)
        except Exception as e:
            print(f"❌ [Dashboard] Error in external apply worker: {e}", flush=True)
        finally:
            _external_apply_running = False

    import threading
    t = threading.Thread(target=run_worker, daemon=True)
    t.start()
    return jsonify({"success": True, "running": True, "message": "Started external application worker in background."})

@app.route('/apply-external-status', methods=['GET'])
def apply_external_status():
    global _external_apply_running
    return jsonify({"running": _external_apply_running})

def parse_csv_date(d_str):
    if not d_str or str(d_str).strip().lower() in ['pending', 'unknown', 'none', '']:
        return None
    d_str = str(d_str).strip()
    for fmt in (
        '%Y-%m-%d %H:%M:%S.%f',
        '%Y-%m-%d %H:%M:%S',
        '%Y-%m-%d',
        '%Y/%m/%d %H:%M:%S',
        '%Y/%m/%d',
        '%d-%m-%Y %H:%M:%S',
        '%d/%m/%Y %H:%M:%S',
    ):
        try:
            return datetime.strptime(d_str, fmt)
        except ValueError:
            pass
    return None

@app.route('/reset-data', methods=['POST'])
def reset_data():
    """
    Cleans or resets applications and failed postings data:
    - scope 'month': data older than 30 days
    - scope 'year': data older than 365 days
    - scope 'all': complete reset (clears all rows)
    Supports 'preview': True to inspect counts before deletion.
    Creates safety backups in all excels/backups/ automatically.
    """
    try:
        req_data = request.get_json() or {}
        scope = req_data.get('scope', 'month')  # 'month', 'year', 'all'
        preview = req_data.get('preview', False)
        create_backup = req_data.get('backup', True)
        target = req_data.get('target', 'both')  # 'both', 'applied', 'failed'

        now = datetime.now()
        timestamp = now.strftime('%Y%m%d_%H%M%S')
        backups_dir = os.path.join(PATH, 'backups')

        applied_path = os.path.join(PATH, 'all_applied_applications_history.csv')
        failed_path = os.path.join(PATH, 'all_failed_applications_history.csv')

        cutoff = None
        if scope == 'month':
            cutoff = now - timedelta(days=30)
        elif scope == 'year':
            cutoff = now - timedelta(days=365)

        # 1. Inspect Applied Records
        applied_rows = []
        applied_fieldnames = []
        applied_to_delete = 0
        new_applied = []
        if os.path.exists(applied_path):
            with open(applied_path, 'r', encoding='utf-8', errors='ignore') as f:
                reader = csv.DictReader(f)
                applied_fieldnames = reader.fieldnames or []
                applied_rows = list(reader)

            for row in applied_rows:
                if scope == 'all':
                    applied_to_delete += 1
                else:
                    d = parse_csv_date(row.get('Date Applied')) or parse_csv_date(row.get('Date Posted'))
                    if d and cutoff and d < cutoff:
                        applied_to_delete += 1
                    else:
                        new_applied.append(row)
        else:
            new_applied = []

        # 2. Inspect Failed Records
        failed_rows = []
        failed_fieldnames = []
        failed_to_delete = 0
        new_failed = []
        if os.path.exists(failed_path):
            with open(failed_path, 'r', encoding='utf-8', errors='ignore') as f:
                reader = csv.DictReader(f)
                failed_fieldnames = reader.fieldnames or []
                failed_rows = list(reader)

            for row in failed_rows:
                if scope == 'all':
                    failed_to_delete += 1
                else:
                    d = parse_csv_date(row.get('Date Tried')) or parse_csv_date(row.get('Date listed'))
                    if d and cutoff and d < cutoff:
                        failed_to_delete += 1
                    else:
                        new_failed.append(row)
        else:
            new_failed = []

        # Return preview if requested
        if preview:
            return jsonify({
                "success": True,
                "preview": True,
                "scope": scope,
                "applied_matching": applied_to_delete,
                "applied_total": len(applied_rows),
                "failed_matching": failed_to_delete,
                "failed_total": len(failed_rows)
            }), 200

        # Perform actual reset
        backup_files = []
        if create_backup:
            os.makedirs(backups_dir, exist_ok=True)
            if os.path.exists(applied_path) and target in ['both', 'applied']:
                b_app = os.path.join(backups_dir, f'applied_backup_{timestamp}.csv')
                shutil.copy2(applied_path, b_app)
                backup_files.append(b_app)
            if os.path.exists(failed_path) and target in ['both', 'failed']:
                b_fail = os.path.join(backups_dir, f'failed_backup_{timestamp}.csv')
                shutil.copy2(failed_path, b_fail)
                backup_files.append(b_fail)

        # Write modified applied data
        if target in ['both', 'applied'] and applied_fieldnames:
            with open(applied_path, 'w', encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=applied_fieldnames)
                writer.writeheader()
                if scope != 'all':
                    writer.writerows(new_applied)

        # Write modified failed data
        if target in ['both', 'failed'] and failed_fieldnames:
            with open(failed_path, 'w', encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=failed_fieldnames)
                writer.writeheader()
                if scope != 'all':
                    writer.writerows(new_failed)

        return jsonify({
            "success": True,
            "preview": False,
            "scope": scope,
            "applied_deleted": applied_to_delete if target in ['both', 'applied'] else 0,
            "applied_remaining": len(new_applied) if target in ['both', 'applied'] and scope != 'all' else 0,
            "failed_deleted": failed_to_delete if target in ['both', 'failed'] else 0,
            "failed_remaining": len(new_failed) if target in ['both', 'failed'] and scope != 'all' else 0,
            "backup_created": create_backup,
            "backups": backup_files
        }), 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5001)

##<