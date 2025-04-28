import os
import subprocess
import sys
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_from_directory

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/run_tournament_scripts", methods=["POST"])
def run_tournament_scripts():
    print("🚀 /run_tournament_scripts POST request received")
    try:
        course_name = request.form.get("course_name")
        course_date = request.form.get("course_date")
        print(f"⚙️ Executing tournament scripts for course: {course_name}, date: {course_date}")

        logs, progress_updates, log_path = execute_scripts(course_name, course_date)

        return jsonify({
            "success": True,
            "logs": logs,
            "progress": progress_updates,
            "log_path": log_path
        })

    except Exception as e:
        return jsonify(success=False, message=f"Error: {str(e)}"), 500

def execute_scripts(course_name, course_date):
    logs = []
    try:
        logs.append("🧪 [DEBUG] execute_scripts() was called.")
        logs.append(f"📂 Working directory is: {os.getcwd()}")

        logs_dir = "logs"
        os.makedirs(logs_dir, exist_ok=True)
        logs.append(f"📁 Creating logs in folder: {logs_dir}")

        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        log_file_path = os.path.join(logs_dir, f"tournament_log_{timestamp}.txt")

        with open(log_file_path, "w", encoding="utf-8") as logfile:
            if not course_name or not course_date:
                raise ValueError("Missing course name or course date")

            script_path = "app2_golf_script_runner/convert_and_import_all.py"

            try:
                logs.append(f"▶️ Running: {script_path}")
                result = subprocess.run(
                    [sys.executable, script_path, course_name, course_date],
                    capture_output=True,
                    text=True,
                    check=True
                )
                logs.append(result.stdout.strip())
            except subprocess.CalledProcessError as e:
                error_msg = f"❌ ERROR in {script_path}:\n{e.stderr}\n{e.stdout}"
                logs.append(error_msg)

            # ✅ Write to the log file
            logfile.write("\n".join(logs) + "\n")

        # ✅ Return expected values
        return logs, ["✅ All scripts completed."], log_file_path

    except Exception as e:
        logs.append(f"🔥 ERROR while executing scripts: {str(e)}")
        return logs, ["❌ Execution failed"], None

@app.route('/logs/<path:filename>')
def download_log(filename):
    return send_from_directory("logs", filename, as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)
