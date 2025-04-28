
import pandas as pd
import mysql.connector
from dotenv import load_dotenv
import os
import sys
import subprocess
from datetime import datetime

print(">>> convert_and_import_all.py started", flush=True)
print(f"[ARGS] {sys.argv}", flush=True)

if len(sys.argv) < 3:
    print("Usage: python convert_and_import_all.py <course_name> <course_date>")
    sys.exit(1)

course_name = sys.argv[1]
course_date = sys.argv[2]

try:
    course_date = datetime.strptime(course_date, "%B %d, %Y").date()
except ValueError as e:
    print(f"❌ Invalid date format: {e}", flush=True)
    sys.exit(1)

load_dotenv()

try:
    db_config = {
        "host": os.getenv("DB_HOST"),
        "user": os.getenv("DB_USER"),
        "password": os.getenv("DB_PASSWORD"),
        "database": os.getenv("DB_NAME")
    }
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    cursor.execute("TRUNCATE TABLE fives;")
    conn.commit()
    cursor.close()
    conn.close()
    print("Fives table truncated successfully.", flush=True)
except Exception as e:
    print(f"⚠️ Database error: {e}", flush=True)

scripts = [
    "convert_xlsx_to_csv.py",
    "convert_xlsx_to_csv_handicap_ranks.py",
    "extract_handicap_order.py",
    "import_golf_scores.py",
    "archive_scores_snapshot.py",
    "import_handicap_ranks.py",
    "fives_import.py"
]

for script in scripts:
    print(f"\n>> Running {script}", flush=True)
    args = [sys.executable, script]

    if script == "import_golf_scores.py":
        csv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "golf_scores.csv"))
        args.extend([str(1), csv_path])  # course_id = 1
    elif script in ["archive_scores_snapshot.py", "import_handicap_ranks.py", "fives_import.py"]:
        args.extend([course_name, str(course_date)])

    result = subprocess.run(args, capture_output=True, text=True)
    print("\n-- STDOUT --\n" + result.stdout, flush=True)
    print("\n-- STDERR --\n" + result.stderr, flush=True)

    if result.returncode != 0:
        print(f"❌ {script} failed with exit code {result.returncode}", flush=True)
