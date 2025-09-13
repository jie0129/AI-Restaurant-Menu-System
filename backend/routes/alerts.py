from flask import Blueprint, jsonify, request
from services.stock_alerts import (
    check_low_stock_alerts,
    check_predicted_stockout_alerts,
    get_all_alerts,
    resolve_alert,
    run_all_alert_checks
)
from models.stock_alert import StockAlert
from models import db

alerts_bp = Blueprint('stock_alerts', __name__, url_prefix='/api/alerts')

@alerts_bp.route('/', methods=['GET'])
def get_alerts():
    """Get all stock alerts."""
    result = get_all_alerts()
    if result['success']:
        return jsonify(result['alerts']), 200
    else:
        return jsonify({'error': result['error']}), 500

@alerts_bp.route('/check', methods=['POST'])
def check_alerts():
    """Manually trigger alert checks."""
    data = request.get_json() or {}
    alert_type = data.get('alert_type', 'all')  # 'low_stock', 'predicted_stockout', or 'all'
    
    if alert_type == 'low_stock':
        result = check_low_stock_alerts()
    elif alert_type == 'predicted_stockout':
        forecast_days = data.get('forecast_days', 7)
        result = check_predicted_stockout_alerts(forecast_days)
    else:
        result = run_all_alert_checks()
    
    return jsonify(result), 200

@alerts_bp.route('/<int:alert_id>/resolve', methods=['PATCH'])
def resolve_stock_alert(alert_id):
    """Mark a specific alert as resolved and optionally restock inventory."""
    data = request.get_json() or {}
    restock_quantity = data.get('restock_quantity')
    
    result = resolve_alert(alert_id, restock_quantity)
    if result['success']:
        return jsonify(result), 200
    else:
        return jsonify({'error': result['error']}), 500

@alerts_bp.route('/stats', methods=['GET'])
def get_alert_stats():
    """Get alert statistics."""
    try:
        total_alerts = StockAlert.query.count()
        low_stock_count = StockAlert.query.filter_by(alert_type='low_stock').count()
        predicted_stockout_count = StockAlert.query.filter_by(alert_type='predicted_stockout').count()
        combined_count = StockAlert.query.filter_by(alert_type='low_stock_and_predicted_stockout').count()
        
        stats = {
            'total_alerts': total_alerts,
            'low_stock_alerts': low_stock_count,
            'predicted_stockout_alerts': predicted_stockout_count,
            'combined_alerts': combined_count
        }
        
        return jsonify(stats), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@alerts_bp.route('/history', methods=['GET'])
def get_alert_history():
    """Get alert history including resolved alerts."""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        alerts = StockAlert.query.order_by(StockAlert.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'alerts': [alert.to_dict() for alert in alerts.items],
            'total': alerts.total,
            'pages': alerts.pages,
            'current_page': page
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@alerts_bp.route('/bulk-resolve', methods=['PATCH'])
def bulk_resolve_alerts():
    """Resolve multiple alerts at once."""
    try:
        data = request.get_json()
        alert_ids = data.get('alert_ids', [])
        
        if not alert_ids:
            return jsonify({'error': 'No alert IDs provided'}), 400
        
        resolved_count = 0
        for alert_id in alert_ids:
            result = resolve_alert(alert_id)
            if result['success']:
                resolved_count += 1
        
        return jsonify({
            'success': True,
            'message': f'Resolved {resolved_count} out of {len(alert_ids)} alerts'
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500