from flask import Blueprint, jsonify, request
from models.nutrition_metrics import NutritionMetrics, db
from models.menu_item import MenuItem
from datetime import datetime, timezone, timedelta
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

metrics_bp = Blueprint('metrics', __name__)

@metrics_bp.route('/nutrition-metrics', methods=['POST'])
def save_nutrition_metrics():
    """Save nutrition analysis metrics"""
    try:
        data = request.get_json()
        
        # Create new metrics record
        new_metrics = NutritionMetrics(
            menu_item_id=data.get('menu_item_id'),
            session_id=data.get('session_id'),
            
            # USDA metrics
            usda_api_called=data.get('usda_api_called', False),
            usda_data_found=data.get('usda_data_found', False),
            
            # Quality metrics
            nutrition_completeness_score=data.get('nutrition_completeness_score'),
            
            # Performance metrics
            total_processing_time_ms=data.get('total_processing_time_ms'),
            gemini_api_response_time_ms=data.get('gemini_api_response_time_ms'),
            analysis_success=data.get('analysis_success', True)
        )
        
        db.session.add(new_metrics)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Nutrition metrics saved successfully',
            'data': new_metrics.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error saving nutrition metrics: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Failed to save nutrition metrics: {str(e)}'
        }), 500

@metrics_bp.route('/nutrition-metrics/dashboard', methods=['GET'])
def get_dashboard_metrics():
    """Get dashboard metrics for visualization"""
    try:
        # Get query parameters
        days = request.args.get('days', 30, type=int)
        
        # Get accuracy metrics
        accuracy_metrics = NutritionMetrics.get_accuracy_metrics(days=days)
        
        # Get time series data for charts
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        metrics = NutritionMetrics.query.filter(
            NutritionMetrics.created_at >= cutoff_date
        ).order_by(NutritionMetrics.created_at.asc()).all()
        
        # Group by date for time series
        daily_stats = {}
        for metric in metrics:
            date_key = metric.created_at.strftime('%Y-%m-%d')
            if date_key not in daily_stats:
                daily_stats[date_key] = {
                    'date': date_key,
                    'total_analyses': 0,
                    'usda_calls': 0,
                    'usda_successes': 0,
                    'avg_processing_time': 0,
                    'processing_times': [],
                    'completeness_scores': [],
                    'success_count': 0
                }
            
            daily_stats[date_key]['total_analyses'] += 1
            
            if metric.usda_api_called:
                daily_stats[date_key]['usda_calls'] += 1
                if metric.usda_data_found:
                    daily_stats[date_key]['usda_successes'] += 1
            
            # Removed serving size and cooking method tracking (optimized)
            
            if metric.total_processing_time_ms:
                daily_stats[date_key]['processing_times'].append(metric.total_processing_time_ms)
            
            if metric.nutrition_completeness_score:
                daily_stats[date_key]['completeness_scores'].append(metric.nutrition_completeness_score)
            
            if metric.analysis_success:
                daily_stats[date_key]['success_count'] += 1
        
        # Calculate averages for each day
        for date_key in daily_stats:
            stats = daily_stats[date_key]
            if stats['processing_times']:
                stats['avg_processing_time'] = sum(stats['processing_times']) / len(stats['processing_times'])
            if stats['completeness_scores']:
                stats['avg_completeness'] = sum(stats['completeness_scores']) / len(stats['completeness_scores'])
            else:
                stats['avg_completeness'] = 0
            
            # Calculate rates (optimized - removed serving and cooking method rates)
            total = stats['total_analyses']
            if total > 0:
                stats['usda_usage_rate'] = (stats['usda_calls'] / total) * 100
                stats['success_rate'] = (stats['success_count'] / total) * 100
            
            if stats['usda_calls'] > 0:
                stats['usda_success_rate'] = (stats['usda_successes'] / stats['usda_calls']) * 100
            else:
                stats['usda_success_rate'] = 0
        
        # Convert to list and sort by date
        time_series_data = sorted(daily_stats.values(), key=lambda x: x['date'])
        
        return jsonify({
            'success': True,
            'data': {
                'summary': accuracy_metrics,
                'time_series': time_series_data,
                'period_days': days
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting dashboard metrics: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Failed to get dashboard metrics: {str(e)}'
        }), 500

@metrics_bp.route('/nutrition-metrics/usage-stats', methods=['GET'])
def get_usage_statistics():
    """Get detailed usage statistics"""
    try:
        days = request.args.get('days', 30, type=int)
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        metrics = NutritionMetrics.query.filter(
            NutritionMetrics.created_at >= cutoff_date
        ).all()
        
        if not metrics:
            return jsonify({
                'success': True,
                'data': {
                    'total_analyses': 0,
                    'feature_usage': {},
                    'performance_stats': {},
                    'accuracy_distribution': {}
                }
            }), 200
        
        total_analyses = len(metrics)
        
        # Feature usage statistics
        feature_usage = {
            'usda_integration': {
                'total_calls': sum(1 for m in metrics if m.usda_api_called),
                'successful_calls': sum(1 for m in metrics if m.usda_data_found),
                # avg_confidence and avg_response_time removed (optimized)
            },
            'serving_size_adjustments': {
                # total_adjustments removed (optimized)
                'avg_adjustment_factor': sum(m.serving_adjustment_factor or 1 for m in metrics if m.serving_adjustment_factor) / max(1, sum(1 for m in metrics if m.serving_adjustment_factor))
            },
            'cooking_method_considerations': {
                # total_applications removed (optimized)
                'avg_retention_factor': sum(m.nutrient_retention_factor or 1 for m in metrics if m.nutrient_retention_factor) / max(1, sum(1 for m in metrics if m.nutrient_retention_factor)),
                'methods_used': list(set(m.cooking_method for m in metrics if m.cooking_method))
            }
        }
        
        # Performance statistics
        processing_times = [m.total_processing_time_ms for m in metrics if m.total_processing_time_ms]
        gemini_times = [m.gemini_api_response_time_ms for m in metrics if m.gemini_api_response_time_ms]
        
        performance_stats = {
            'avg_total_processing_time': sum(processing_times) / len(processing_times) if processing_times else 0,
            'avg_gemini_response_time': sum(gemini_times) / len(gemini_times) if gemini_times else 0,
            'success_rate': (sum(1 for m in metrics if m.analysis_success) / total_analyses) * 100,
            'error_rate': (sum(1 for m in metrics if not m.analysis_success) / total_analyses) * 100
        }
        
        # Accuracy distribution
        # accuracy_distribution removed (optimized)
        accuracy_distribution = {}
        
        # Analysis type distribution
        # analysis_types and type_distribution removed (optimized)
        
        return jsonify({
            'success': True,
            'data': {
                'total_analyses': total_analyses,
                'feature_usage': feature_usage,
                'performance_stats': performance_stats,
                'accuracy_distribution': accuracy_distribution,
                # analysis_type_distribution removed (optimized)
                'period_days': days
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting usage statistics: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Failed to get usage statistics: {str(e)}'
        }), 500

@metrics_bp.route('/nutrition-metrics/feedback', methods=['POST'])
def save_user_feedback():
    """Save user feedback for a nutrition analysis"""
    try:
        data = request.get_json()
        
        if 'metrics_id' not in data or 'rating' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing required fields: metrics_id and rating'
            }), 400
        
        metrics = NutritionMetrics.query.get(data['metrics_id'])
        if not metrics:
            return jsonify({
                'success': False,
                'error': f'Metrics record with ID {data["metrics_id"]} not found'
            }), 404
        
        metrics.user_feedback_rating = data['rating']
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'User feedback saved successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error saving user feedback: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Failed to save user feedback: {str(e)}'
        }), 500