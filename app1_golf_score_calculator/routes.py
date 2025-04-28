from app1_golf_score_calculator.excel_cache import ExcelCache
from app1_golf_score_calculator.callaway_logic import calculate_callaway_score

from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, send_from_directory
from . import score_calc_bp
from app1_golf_score_calculator.excel_cache import ExcelCache
from datetime import datetime
import logging
from .logic import extract_course_name_and_today
from app2_golf_script_runner.app import execute_scripts
from app1_golf_score_calculator.callaway_logic import calculate_callaway_score
import mysql.connector

import subprocess
import sys
import os
import time
from dotenv import load_dotenv
import mysql.connector

load_dotenv()
logger = logging.getLogger(__name__)

def run_script(script_name, args=None):
    try:
        # Manually set the path to app2_golf_script_runner
        working_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "app2_golf_script_runner"))
        os.chdir(working_dir)

        script_path = os.path.join(working_dir, script_name)
        print(f"📁 Checking script at: {script_path}", flush=True)

        if not os.path.isfile(script_path):
            print(f"❌ Script not found: {script_path}", flush=True)
            return f"❌ Script not found: {script_path}"

        command = [sys.executable, script_path]
        if args:
            command.extend(args)

        print(f"🚀 Running command: {' '.join(command)}", flush=True)
        process = subprocess.run(command, check=False, text=True, capture_output=True)
        print(f"📤 STDOUT:\n{process.stdout[:300]}", flush=True)
        print(f"📥 STDERR:\n{process.stderr[:300]}", flush=True)
        return process.stdout

    except Exception as e:
        return f"❌ Error running {script_name}: {str(e)}"


def mysql_connection():
    import os
    import mysql.connector
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME")
    )

@score_calc_bp.route('/', strict_slashes=False)
def index():
    wb = ExcelCache.get_workbook()
    if wb is None:
        logger.error("Workbook is not initialized. Please check the file path or initialization.")
        return "Error: Workbook not found or failed to load", 500
    ws = ExcelCache.get_sheet()

    submitted_count = 0
    total_count = 0

    for row in range(4, 200):
        name = ws.Cells(row, 2).Value
        if not name:
            break
        total_count += 1
        if ws.Cells(row, 25).Value:
            submitted_count += 1

    players_left = total_count - submitted_count

    # ✅ Use session-based course name, not extracted again
    course_name = session.get("course_name", "Unknown")
    course_date = datetime.today().strftime("%B %d, %Y")

    return render_template(
        "index.html",
        submitted_count=submitted_count,
        total_count=total_count,
        players_left=players_left,
        course_name=course_name,
        course_date=course_date
    )

@score_calc_bp.route('/test')
def test_page():
    return render_template('test.html')

@score_calc_bp.route('/get_course_name', methods=['GET'])
def get_course_name():
    return jsonify({
        "course_name": session.get("course_name", "Unknown"),
        "date": datetime.today().strftime("%B %d, %Y")
    })

@score_calc_bp.route('/get_names')
def get_names():
    try:
        wb = ExcelCache.get_workbook()
        sheet = wb.Sheets("Scores")

        # Load names from Excel roster (A4:B...)
        name_data = sheet.Range("A4:B153").Value
        all_names = []
        for row in name_data:
            if row[0] is None or row[1] is None:
                continue
            full_name = f"{row[0].strip()} {row[1].strip()}"
            all_names.append(full_name)

        # ✅ Get submitted names from MySQL
        db_config = {
            "host": os.getenv("DB_HOST"),
            "user": os.getenv("DB_USER"),
            "password": os.getenv("DB_PASSWORD"),
            "database": os.getenv("DB_NAME")
        }
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT CONCAT(first_name, ' ', last_name) FROM scores")
        submitted_names = set(name.strip().lower() for name, in cursor.fetchall())
        cursor.close()
        conn.close()

        # 🎯 Mark players as submitted/not
        results = []
        for name in all_names:
            is_submitted = name.strip().lower() in submitted_names
            results.append({"name": name, "is_submitted": is_submitted})

        return jsonify(results)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@score_calc_bp.route("/golf_score_calculator/submit", methods=["POST"])
def submit_score():
        
    data = request.get_json()

    name = data.get("name", "")
    first_name, *rest = name.strip().split(" ")
    last_name = " ".join(rest) if rest else ""
    scores = data.get("scores", [])
    par = data.get("par")
    total = data.get("total")

    print("📥 Incoming payload:", data)
    print("🧪 first_name:", first_name)
    print("🧪 last_name:", last_name)
    print("🧪 scores length:", len(scores))

    if not first_name or not last_name or len(scores) != 18:
        return jsonify(success=False, message="Invalid data")

    try:
        par = data.get("par")
        if par is None:
            par = ExcelCache.get_par()
        else:
            par = int(par)
        print(f"🧮 Using par for Callaway: {par}")

        gross, deducted, adjustment, net_score = calculate_callaway_score(scores, par)
        print(f"📊 Callaway breakdown → Gross: {gross}, Deducted: {deducted}, Adj: {adjustment}, Net: {net_score}")


        conn = mysql_connection()
        cursor = conn.cursor()

        # Get course_id
        cursor.execute("SELECT MAX(course_id) FROM courses")
        result = cursor.fetchone()
        course_id = result[0] if result and result[0] else 1

        query = """
            INSERT INTO scores (
                first_name, last_name,
                hole_1, hole_2, hole_3, hole_4, hole_5, hole_6, hole_7, hole_8, hole_9,
                hole_10, hole_11, hole_12, hole_13, hole_14, hole_15, hole_16, hole_17, hole_18,
                total, net_score, course_id
            )
            VALUES (%s, %s,
                    %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                hole_1 = VALUES(hole_1), hole_2 = VALUES(hole_2), hole_3 = VALUES(hole_3), hole_4 = VALUES(hole_4),
                hole_5 = VALUES(hole_5), hole_6 = VALUES(hole_6), hole_7 = VALUES(hole_7), hole_8 = VALUES(hole_8),
                hole_9 = VALUES(hole_9), hole_10 = VALUES(hole_10), hole_11 = VALUES(hole_11), hole_12 = VALUES(hole_12),
                hole_13 = VALUES(hole_13), hole_14 = VALUES(hole_14), hole_15 = VALUES(hole_15), hole_16 = VALUES(hole_16),
                hole_17 = VALUES(hole_17), hole_18 = VALUES(hole_18),
                total = VALUES(total), net_score = VALUES(net_score), course_id = VALUES(course_id)
        """

        values = [first_name, last_name] + scores + [total, net_score, course_id]
        cursor.execute(query, values)
        conn.commit()
        cursor.close()
        conn.close()

        return jsonify(success=True, message=f"✅ Score submitted for {name}")

    except Exception as e:
        print("❌ DB Error:", e)
        return jsonify(success=False, message="Database error.")


@score_calc_bp.route("/load_history")
def load_history():
    return render_template("historical_loader.html")

@score_calc_bp.route("/run_history_scripts", methods=["POST"])
def run_history_scripts():
    course_name = request.form.get("course_name")
    course_date = request.form.get("course_date")

    print(f"Loading historical data for {course_name} on {course_date}")
    return jsonify(progress=["Step 1", "Step 2", "Step 3"], logs=["History script started...", "Done."])

@score_calc_bp.route('/run_scripts', methods=['POST'])
def run_scripts():
    print("✅ /run_scripts route triggered", flush=True)
    data = request.get_json()
    course_name = data['course_name']
    course_date = data['course_date']

    print(f"📢 Calling convert_and_import_all.py with: {course_name}, {course_date}", flush=True)

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
        truncate_message = "✅ Fives table truncated successfully."
    except Exception as e:
        truncate_message = f"⚠️ Database error: {e}"

    output = run_script("convert_and_import_all.py", args=[course_name, course_date])
    print(f"📥 Script output received:\n{output[:300]}...", flush=True)
    output_logs = [output.strip()]

    log_dir = os.path.join(os.getcwd(), "logs")
    os.makedirs(log_dir, exist_ok=True)

    timestamp = time.strftime("%Y%m%d-%H%M%S")
    log_filename = f"tournament_log_{timestamp}.txt"
    log_path = os.path.join(log_dir, log_filename)

    with open(log_path, "w") as log_file:
        log_file.write("\n\n".join(output_logs))

    return jsonify({
        "message": truncate_message,
        "logs": output_logs,
        "progress": [],
        "log_path": f"/logs/{log_filename}"
    })

@score_calc_bp.route('/run_tournament_scripts_v2', methods=['POST'])
def run_scripts_v2():
    print("✅ /run_tournament_scripts_v2 route triggered", flush=True)

    try:
        data = request.get_json()
        course_name = data['course_name']
        course_date = data['course_date']

        output = run_script("convert_and_import_all.py", args=[course_name, course_date])
        print(f"📥 Script output received:\n{output[:300]}", flush=True)
        output_logs = [output.strip()]

        log_dir = os.path.join(os.getcwd(), "logs")
        os.makedirs(log_dir, exist_ok=True)

        timestamp = time.strftime("%Y%m%d-%H%M%S")
        log_filename = f"tournament_log_{timestamp}.txt"
        log_path = os.path.join(log_dir, log_filename)

        with open(log_path, "w") as log_file:
            log_file.write("\n\n".join(output_logs))

        return jsonify({
            "message": "✅ Scripts executed.",
            "logs": output_logs,
            "progress": [],
            "log_path": f"/logs/{log_filename}"
        })

    except Exception as e:
        print(f"❌ Error in /run_tournament_scripts_v2: {e}", flush=True)
        return jsonify({
            "success": False,
            "error": str(e),
            "logs": [],
            "progress": []
        }), 500

@score_calc_bp.route('/logs/<path:filename>')
def download_log(filename):
    log_dir = os.path.join(os.getcwd(), "logs")
    return send_from_directory(log_dir, filename, as_attachment=True)

@score_calc_bp.route('/score', methods=['POST'])
def score():
    try:
        data = request.get_json()
        scores = data.get("scores")

        if not scores or len(scores) != 18:
            return jsonify({"error": "Exactly 18 scores required"}), 400

        gross, deducted, adjustment, net = calculate_callaway_score(scores)
        return jsonify({
            "gross": gross,
            "deducted": deducted,
            "adjustment": adjustment,
            "net": net
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@score_calc_bp.route('/reset_scores', methods=['POST'])
def reset_scores():
    try:
        db_config = {
            "host": os.getenv("DB_HOST"),
            "user": os.getenv("DB_USER"),
            "password": os.getenv("DB_PASSWORD"),
            "database": os.getenv("DB_NAME")
        }
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        # Clear all rows from the scores table
        cursor.execute("DELETE FROM scores")
        conn.commit()
        cursor.close()
        conn.close()

        return jsonify(success=True, message="Scores cleared.")
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify(success=False, error=str(e)), 500
    
@score_calc_bp.route('/export_to_excel', methods=['POST'])
def export_to_excel():
    def normalize(name):
        return ''.join((name or '').lower().split())

    def canonicalize_name(first, last):
        full = f"{first.strip()} {last.strip()}"
        if full.lower() == "d j patterson":
            return "DJ", last
        if full.lower() == "mike a carroll":
            return "MikeA", last
        if full.lower() == "mike p carroll":
            return "MikeP", last
        return first.strip(), last.strip()

    conn = None
    cursor = None
    try:
        conn = mysql_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT first_name, last_name,
                   hole_1, hole_2, hole_3, hole_4, hole_5, hole_6,
                   hole_7, hole_8, hole_9, hole_10, hole_11, hole_12,
                   hole_13, hole_14, hole_15, hole_16, hole_17, hole_18,
                   total, net_score
            FROM scores
        """)
        rows = cursor.fetchall()

        wb = ExcelCache.get_workbook()
        sheet = ExcelCache.get_sheet()
        name_range = sheet.Range("A4:B153").Value

        matched_count = 0
        unmatched = []

        for db_row in rows:
            db_first, db_last = canonicalize_name(db_row[0], db_row[1])
            db_canon = normalize(f"{db_first} {db_last}")
            match_found = False

            for i, row in enumerate(name_range, start=4):
                xl_canon = normalize(f"{row[0]} {row[1]}")
                if db_canon == xl_canon:
                    data_range = sheet.Range(sheet.Cells(i, 4), sheet.Cells(i, 22))
                    data_range.Value = list(db_row[2:21])
                    sheet.Cells(i, 46).Value = db_row[21]
                    matched_count += 1
                    match_found = True
                    break

            if not match_found:
                unmatched.append(f"{db_row[0]} {db_row[1]}")

        wb.Save()
        print(f"✅ Exported {matched_count} players. Unmatched: {len(unmatched)}")
        if unmatched:
            print("❗ Unmatched entries:", unmatched)

        return jsonify(success=True, message=f"✅ Export complete. Matched: {matched_count}, Unmatched: {len(unmatched)}")

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify(success=False, message=f"❌ Export failed: {e}")

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()