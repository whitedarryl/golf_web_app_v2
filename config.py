from app1_golf_score_calculator.app import app as app1
from app2_golf_script_runner.app import app as app2
from callaway_results_app import create_app
from app4_five_results.app import app as app4
from app5_historical_data.app import app as app5

# Create the Callaway Results app instance
app3 = create_app()

# Define route mappings for DispatcherMiddleware
ROUTES = {
    '/golf_score_calculator': app1,
    '/golf_script_runner': app2,
    '/callaway_results': app3,
    '/five_results': app4,
    '/historical_data': app5,
}