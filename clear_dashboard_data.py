import csv, shutil, os, datetime

# Paths to CSV files
APPLIED_CSV = os.path.join('all excels', 'all_applied_applications_history.csv')
FAILED_CSV = os.path.join('all excels', 'all_failed_applications_history.csv')

def backup_and_truncate(csv_path):
    # Create timestamped backup
    backup_path = csv_path + '.backup_' + datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    shutil.copy(csv_path, backup_path)
    # Read header only
    with open(csv_path, 'r', newline='', encoding='utf-8') as src:
        header = src.readline()
    # Overwrite file with only header
    with open(csv_path, 'w', newline='', encoding='utf-8') as dst:
        dst.write(header)
    print(f"Cleared data in {csv_path}. Backup saved to {backup_path}")

backup_and_truncate(APPLIED_CSV)
backup_and_truncate(FAILED_CSV)
