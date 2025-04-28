from flask import Flask, render_template, request, jsonify, session
from dotenv import load_dotenv
# from app1_golf_score_calculator.routes import score_calc_bp
import os
import re

# Load env vars
load_dotenv()

# Init Flask
app = Flask(
    __name__,
    static_url_path='/static',
    static_folder='../static',
    template_folder='templates'
)

# Config
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY", "golf-dev-key")
app.config['TEMPLATES_AUTO_RELOAD'] = True

# Inject session values before any route
@app.before_request
def set_course():
    if 'course_name' not in session or 'course_date' not in session:
        course_name, course_date = extract_course_name_and_date()
        session['course_name'] = course_name
        session['course_date'] = course_date
        print(f"💾 Session set: course_name = {course_name}, course_date = {course_date}")

# Register Blueprints
# app.register_blueprint(score_calc_bp)

# Root route
@app.route("/")
def landing():
    course_name = session.get("course_name", "Unknown")
    course_date = session.get("course_date", "Unknown")
    return render_template("index.html", course_name=course_name, course_date=course_date)

# Route for AJAX test
@app.route("/run_scripts", methods=["POST"])
def run_scripts():
    data = request.get_json()
    course_name = data.get("course_name")
    course_date = data.get("course_date")

    if not course_name or not course_date:
        return jsonify(success=False, message="Missing course name or date"), 400

    print(f"✅ Running scripts for {course_name} on {course_date}")
    return jsonify(success=True)

def extract_course_name_and_date(folder=None):
    if folder is None:
        folder = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    print("📂 Searching in folder:", folder)

    for filename in os.listdir(folder):
        print("🔎 Found file:", filename)
        if "Callaway scoring sheet" in filename and filename.endswith(".xls"):
            print("✅ Filename matched:", filename)
            parts = filename.split()
            try:
                idx = parts.index("Callaway")
                month = parts[idx - 2]
                year = parts[idx - 1]
                course_name = " ".join(parts[:idx - 2])
                course_date = f"{month} {year}"
                print(f"🎯 Extracted course name: {course_name}")
                print(f"🗓️ Extracted course date: {course_date}")
                return course_name, course_date
            except Exception as e:
                print("⚠️ Failed to parse name/date:", e)
                return "Unknown", "Unknown"
    print("❌ No matching Callaway scoring sheet file found.")
    return "Unknown", "Unknown"

@app.errorhandler(404)
def not_found(e):
    return render_template("404.html"), 404

if __name__ == "__main__":
    app.run(debug=True)