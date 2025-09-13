import os
import logging
from dotenv import load_dotenv
from flask import Flask, send_from_directory, jsonify
from flask_migrate import Migrate
from flask_apscheduler import APScheduler
from flask_cors import CORS
from config import Config
from models.inventory_item import db
# Import forecast models to register them with SQLAlchemy
from models.current_forecasts import CurrentForecast
from models.forecast_performance import ForecastPerformance
from models.menu_item_forecasts import MenuItemForecast
# Import menu models to ensure relationships are established
from models.menu_item import MenuItem
from models.menu_item_image import MenuItemImage
from routes import inventory, menu_planning, pricing, nutrition, order, register_routes, alerts, new_item_prediction, metrics, dashboard
from routes.chatbot import chatbot_bp
from routes.ai_agent import ai_agent_bp
from services.alert_scheduler import check_low_stock_with_context

# Load environment variables from .env file
load_dotenv()


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Configure logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Configure JSON encoding to handle Unicode characters (emojis)
    app.config['JSON_AS_ASCII'] = False
    app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True
    
    db.init_app(app)
    Migrate(app, db)
    CORS(app, supports_credentials=True)

    with app.app_context():
        db.create_all()  # creates tables if they don't exist

    # Register blueprints
    app.register_blueprint(inventory.inventory_bp, url_prefix='/api/inventory')

    app.register_blueprint(inventory.alerts_bp, url_prefix='/api/alerts')
    app.register_blueprint(inventory.forecast_bp, url_prefix='/api/forecast')
    app.register_blueprint(inventory.forecasting_bp, url_prefix='/api/forecasting')
    app.register_blueprint(menu_planning.menu_bp, url_prefix='/api/menu')
    app.register_blueprint(pricing.pricing_bp, url_prefix='/api/pricing')
    app.register_blueprint(nutrition.nutrition_bp, url_prefix='/api/nutrition')
    app.register_blueprint(order.order_bp, url_prefix='/api/order')
    app.register_blueprint(alerts.alerts_bp, url_prefix='/api/alerts') # New stock alerts system
    app.register_blueprint(new_item_prediction.new_item_bp)  # New item demand prediction
    app.register_blueprint(metrics.metrics_bp, url_prefix='/api/metrics')  # Nutrition metrics tracking
    app.register_blueprint(chatbot_bp, url_prefix='/api/chatbot') 
    app.register_blueprint(ai_agent_bp)  # AI Agent endpoints
    
    # Import and register test gemini blueprints
    try:
        from routes.test_gemini_route import test_gemini_bp
        app.register_blueprint(test_gemini_bp, url_prefix='/api/test')
        print("✅ Gemini test blueprints registered successfully")
    except Exception as e:
        print(f"❌ Failed to register Gemini test blueprints: {e}")
    
    # Register additional routes
    register_routes(app)
    
    # Setup APScheduler for periodic tasks (e.g., low-stock alerts)
    scheduler = APScheduler()
    scheduler.init_app(app)
    scheduler.start()
    
    # Wrapper function to ensure Flask app context
    def scheduled_stock_check():
        with app.app_context():
            return check_low_stock_with_context()
    
    scheduler.add_job(id='LowStockCheck', func=scheduled_stock_check, trigger='interval', minutes=1)

    @app.route("/")
    def index():
        return "Flask API is running!"
    
    @app.route('/api/debug/test', methods=['GET', 'POST'])
    def debug_test():
        from flask import request, jsonify
        return jsonify({'success': True, 'message': 'Debug test endpoint working', 'method': request.method})

    @app.route('/api/scheduler/status')
    def scheduler_status():
        """Check APScheduler status and jobs"""
        try:
            jobs = scheduler.get_jobs()
            job_info = []
            for job in jobs:
                job_info.append({
                    'id': job.id,
                    'name': job.name,
                    'next_run_time': job.next_run_time.isoformat() if job.next_run_time else None,
                    'trigger': str(job.trigger)
                })
            
            return {
                'status': 'running' if scheduler.running else 'stopped',
                'jobs': job_info,
                'total_jobs': len(jobs)
            }
        except Exception as e:
            return {'status': 'error', 'message': str(e)}, 500

    @app.route('/api/config/api-key')
    def get_api_key():
        """Provide API key to frontend"""
        api_key = os.environ.get('GEMINI_API_KEY')
        if not api_key:
            return {'error': 'API key not configured'}, 500
        
        response = jsonify({'api_key': api_key})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        return response

    @app.route('/static/<path:filename>')
    def serve_static(filename):
        """Serve static files (including menu images)"""
        response = send_from_directory('static', filename)
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        return response

    @app.route('/menu_images/<path:filename>')
    def serve_menu_images(filename):
        """Serve menu images directly from /menu_images/ path"""
        response = send_from_directory('static/menu_images', filename)
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        return response

    return app

if __name__ == '__main__':
    app = create_app()
    port = int(os.environ.get('PORT', 5001))
    
    # Get debug mode from environment variable, default to False for production
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'

    # Print all registered routes for debugging
    print('Registered Flask routes:')
    for rule in app.url_map.iter_rules():
        print(rule)
    
    print(f"Starting Flask server on port {port} with debug={debug_mode}")
    app.run(debug=debug_mode, port=port, use_reloader=debug_mode)
