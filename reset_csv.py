import csv, shutil, os, datetime

CSV_PATH = os.path.join('all excels', 'all_applied_applications_history.csv')
BACKUP_PATH = CSV_PATH + '.backup_' + datetime.datetime.now().strftime('%Y%m%d%H%M%S')

# Backup the original CSV
shutil.copy(CSV_PATH, BACKUP_PATH)

# Reset Status and Date Applied columns
with open(CSV_PATH, 'r', newline='', encoding='utf-8') as src, \
     open(CSV_PATH + '.tmp', 'w', newline='', encoding='utf-8') as dst:
    reader = csv.DictReader(src)
    fieldnames = reader.fieldnames
    writer = csv.DictWriter(dst, fieldnames=fieldnames)
    writer.writeheader()
    for row in reader:
        row['Status'] = ''
        row['Date Applied'] = ''
        writer.writerow(row)

os.replace(CSV_PATH + '.tmp', CSV_PATH)
print('CSV reset complete. Backup saved to', BACKUP_PATH)
