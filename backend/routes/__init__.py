from .ingredient_usage import bp as ingredient_usage_bp
from .dashboard import dashboard_bp
from .metrics import metrics_bp

def register_routes(app):
    app.register_blueprint(ingredient_usage_bp)
    app.register_blueprint(dashboard_bp)
