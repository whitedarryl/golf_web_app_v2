from flask import Blueprint

score_calc_bp = Blueprint(
    'score_calc',
    __name__,
    template_folder='templates',
    static_folder='static',
)

# ✅ Import routes AFTER defining blueprint
from . import routes

# ✅ Attach the blueprint to the app (done in main.py or elsewhere)
# app.register_blueprint(score_calc_bp, url_prefix="/golf_score_calculator")
