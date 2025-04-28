import sys
import os
import logging
from flask import Flask, request
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from werkzeug.serving import run_simple
from landing_page.app import app as landing_app
from config import ROUTES
from settings import CSS_FILE_PATH, STATIC_DIR  # Import paths from settings.py
from app1_golf_score_calculator import score_calc_bp  # ✅ This is the correct import
from callaway_results_app import create_app as create_callaway_app
print("✅ callaway_results route registered")

from app1_golf_score_calculator.app import create_app
app = create_app()

ROUTES["/golf_score_calculator"] = app  # Or another suitable path
callaway_app = create_callaway_app()  # ✅ ADD THIS
ROUTES["/callaway_results"] = callaway_app  # ✅ ADD THIS TOO

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Validate critical files and directories
if not os.path.exists(STATIC_DIR):
    logger.error("Static directory not found: %s", STATIC_DIR)
    sys.exit(1)  # Exit the application if the static directory is missing

if not os.path.exists(CSS_FILE_PATH):
    logger.warning("CSS file not found: %s", CSS_FILE_PATH)  # Log a warning but don't exit

# Log the existence of the CSS file
logger.debug("🧪 File exists at %s? %s", CSS_FILE_PATH, os.path.exists(CSS_FILE_PATH))

# Log the static directory being used
logger.debug("Static directory being used: %s", landing_app.static_folder)

# Log the Flask static folder
logger.debug("Flask static folder: %s", landing_app.static_folder)
logger.debug("Flask static folder: %s", app.static_folder)

logger.debug("Fonts directory exists: %s", os.path.exists(os.path.join(STATIC_DIR, 'fonts')))
logger.debug("Font file exists: %s", os.path.exists(os.path.join(STATIC_DIR, 'fonts', 'Satisfy-Regular.woff2')))
logger.debug("Images directory exists: %s", os.path.exists(os.path.join(STATIC_DIR, 'images')))
logger.debug("Background image exists: %s", os.path.exists(os.path.join(STATIC_DIR, 'images', 'background.jpg')))

@app.before_request
def log_static_requests():
    if request.path.startswith('/static'):
        logger.debug("Static file requested: %s", request.path)

# Combine the landing app with other apps using DispatcherMiddleware
application = DispatcherMiddleware(landing_app, ROUTES)

with landing_app.app_context():
    print("\n📋 Registered Routes:")
    if hasattr(application, 'url_map'):
        for rule in application.url_map.iter_rules():
            print(f"{rule.methods} {rule.rule}")
    else:
        print("🚫 application has no 'url_map'.")

from config import ROUTES  # or wherever ROUTES is defined

print("\n📋 Registered Flask Apps and Their Routes:")
for path, app in ROUTES.items():
    print(f"\n🔹 App mounted at: {path}")
    try:
        for rule in app.url_map.iter_rules():
            print(f"  {rule.methods} {rule.rule}")
    except Exception as e:
        print(f"  🚫 Could not inspect app at {path}: {e}")


if __name__ == '__main__':
    # Determine the environment (default to 'production')
    environment = os.getenv('FLASK_ENV', 'production').lower()
    is_debug = True
    # is_debug = environment == 'development'

    logger.info("Starting the application in %s mode on http://0.0.0.0:5000", environment)
    print("🚀 Registered Blueprints:", app.blueprints)
    run_simple(
        '0.0.0.0',
        5000,
        application,
        use_reloader=is_debug,  # Enable reloader only in development
        use_debugger=is_debug   # Enable debugger only in development
    )

