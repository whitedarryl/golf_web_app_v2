import os
import re
from flask import Flask, session
from . import score_calc_bp
from .utils.excel_session import close_excel

def extract_course_name_from_file(folder=None):
    if folder is None:
        folder = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    print("📂 Scanning directory:", folder)
    for filename in os.listdir(folder):
        print("🔎 Checking file:", filename)
        if filename.endswith("Callaway scoring sheet.xls"):
            parts = filename.split()
            course_name = " ".join(parts[:-5])
            print(f"✅ Matched course name: {course_name}")
            return course_name
    print("❌ No Callaway scoring sheet found.")
    return "Unknown Course"

def create_app():
    app = Flask(__name__)
    app.secret_key = "super-secret-key"

    @app.before_request
    def set_course():
        if 'course_name' not in session:
            session['course_name'] = extract_course_name_from_file()

    app.register_blueprint(score_calc_bp)  # ✅ No prefix here

    return app

app = create_app()

print("\n🔍 Registered routes:")
for rule in app.url_map.iter_rules():
    print(f"{rule.endpoint}: {rule.rule}")
