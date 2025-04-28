from flask import Flask

def create_app():
    print("✅ create_app() called")
    app = Flask(__name__)
    from .views import callaway_app
    app.register_blueprint(callaway_app)  # ❌ remove the url_prefix!
    return app
