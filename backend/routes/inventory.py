from flask import Blueprint, request, jsonify
from models.inventory_item import db, InventoryItem
from datetime import datetime
from sqlalchemy import func, create_engine
from config import Config
from services.alert_scheduler import check_low_stock_with_context
from services.demand_forecasting_service import generate_forecast_from_csv
from services.unified_restaurant_demand_system import RestaurantDemandPredictor
import os
import pandas as pd
import logging
from sqlalchemy.orm import aliased
from sqlalchemy.exc import IntegrityError
from sqlalchemy import and_, text
from datetime import datetime, timedelta
import json

logging.basicConfig(level=logging.DEBUG)
forecast_bp = Blueprint('forecast', __name__)
forecasting_bp = Blueprint('forecasting', __name__)  # New blueprint for forecasting endpoints
inventory_bp = Blueprint('inventory', __name__)
alerts_bp = Blueprint('alerts', __name__)


@inventory_bp.route('/', methods=['GET'])
def get_inventory():
    items = InventoryItem.query.all()
    return jsonify([item.to_dict() for item in items]), 200

@inventory_bp.route('/', methods=['POST'])
def add_inventory():
    """
    新增食材库存项。支持设置最小阈值。
    前端需传递：name, category, quantity, unit, min_threshold（可选）
    """
    data = request.get_json()
    new_item = InventoryItem(
        name=data.get('name'),
        category=data.get('category'),
        quantity=data.get('quantity'),
        unit=data.get('unit'),
        min_threshold=data.get('min_threshold', 0),
        last_updated=datetime.utcnow()
    )
    db.session.add(new_item)
    db.session.commit()
    return jsonify(new_item.to_dict()), 201

@inventory_bp.route('/<int:item_id>', methods=['PUT'])
def update_inventory(item_id):
    """
    编辑食材库存项。支持更新最小阈值。
    """
    from services.stock_alerts import run_all_alert_checks
    
    item = InventoryItem.query.get_or_404(item_id)
    data = request.get_json()
    item.name = data.get('name', item.name)
    item.category = data.get('category', item.category)
    item.quantity = data.get('quantity', item.quantity)
    item.unit = data.get('unit', item.unit)
    item.min_threshold = data.get('min_threshold', item.min_threshold)
    item.last_updated = datetime.utcnow()
    db.session.commit()
    
    # Trigger alert checks after inventory update
    try:
        run_all_alert_checks()
    except Exception as e:
        logging.warning(f"Alert check failed after inventory update: {str(e)}")
    
    return jsonify(item.to_dict()), 200

@inventory_bp.route('/<int:item_id>/threshold', methods=['PATCH'])
def update_min_threshold(item_id):
    """
    单独设置/更新某个食材的最小阈值。
    前端需传递：min_threshold
    """
    from services.stock_alerts import run_all_alert_checks
    
    item = InventoryItem.query.get_or_404(item_id)
    data = request.get_json()
    if 'min_threshold' not in data:
        return jsonify({'error': 'min_threshold is required'}), 400
    item.min_threshold = data['min_threshold']
    db.session.commit()
    
    # Trigger alert checks after threshold update
    try:
        run_all_alert_checks()
    except Exception as e:
        logging.warning(f"Alert check failed after threshold update: {str(e)}")
    
    return jsonify({'id': item.id, 'min_threshold': item.min_threshold}), 200

@inventory_bp.route('/categories', methods=['GET'])
def get_categories():
    """
    获取所有已存在的食材分类（去重）。
    """
    from models.ingredient import Ingredient
    categories = db.session.query(Ingredient.category).distinct().all()
    return jsonify([c[0] for c in categories if c[0]]), 200

@inventory_bp.route('/<int:item_id>', methods=['DELETE'])
def delete_inventory(item_id):
    item = InventoryItem.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    return jsonify({'message': 'Item deleted successfully'}), 200

@inventory_bp.route('/aggregated', methods=['GET'])
def get_aggregated_inventory():
    """
    Returns items grouped by (name, category, unit) with summed quantity
    and the most recent 'last_updated'.
    """
    # Group the query by name, category, and unit
    results = db.session.query(
        Ingredient.name,
        Ingredient.category,
        func.sum(InventoryItem.quantity).label('quantity'),
        Ingredient.unit,
        # If you want the most recent last_updated among duplicates:
        func.max(InventoryItem.last_updated).label('last_updated')
    ).join(Ingredient).group_by(
        Ingredient.name,
        Ingredient.category,
        Ingredient.unit
    ).all()

    # Convert query results into a list of dicts
    aggregated_data = []
    for row in results:
        aggregated_data.append({
            'name': row.name,
            'category': row.category,
            'quantity': int(row.quantity),
            'unit': row.unit,
            'last_updated': (
                row.last_updated.isoformat() 
                if row.last_updated else None
            )
        })

    return jsonify(aggregated_data), 200

#low Stock Alert
@alerts_bp.route('/low-stock', methods=['GET'])
def get_low_stock_alerts():
    low_stock_items = check_low_stock_with_context()  # returns the list
    results = [
        {
            'id': item.id,
            'name': item.name,
            'quantity': item.quantity,
            'threshold': Config.LOW_STOCK_THRESHOLD,
        }
        for item in low_stock_items
    ]
    return jsonify(results), 200


#Forecasting
@forecast_bp.route('/', methods=['GET'])
def forecast_inventory():
    logging.info("Forecast API was hit")
    merged_df = generate_forecast_from_csv('Food_Sales.csv')
    logging.info(f"Forecast data: {merged_df.head().to_dict()}")
    forecast_json = merged_df[['ds', 'actual', 'yhat', 'yhat_lower', 'yhat_upper']].to_dict(orient='records')
    return jsonify(forecast_json), 200

# XGBoost Forecasting Endpoints
@forecast_bp.route('/xgboost/run', methods=['POST'])
def run_xgboost_forecast_api():
    """Run XGBoost forecast for Menu Items only with auto-derived ingredient demand."""
    try:
        data = request.get_json() or {}
        
        # Force forecast_type to 'menu_items' only
        forecast_type = 'menu_items'
        forecast_days = int(data.get('forecast_days', 28))
        start_date_str = data.get('start_date')
        selected_item = data.get('selected_item')  # Add selected item parameter
        
        # Parse start date if provided
        start_date = None
        if start_date_str:
            try:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            except ValueError:
                return jsonify({'error': 'Invalid start_date format. Use YYYY-MM-DD'}), 400
        
        # Run the unified forecast system
        data_path = "C:/Users/User/Desktop/first-app/instance/cleaned_streamlined_ultimate_malaysian_data.csv"
        predictor = RestaurantDemandPredictor(data_path)
        results = predictor.run_complete_analysis()
        
        if results is None or 'error' in results:
            return jsonify({'error': 'Forecast analysis failed'}), 500
        
        # Extract model version and performance metrics
        model_version = results.get('summary', {}).get('model_version', f'unified_{datetime.now().strftime("%Y%m%d_%H%M%S")}')
        best_model = results.get('summary', {}).get('best_model', 'unknown')
        best_r2_score = results.get('summary', {}).get('best_r2_score', 0.0)
        
        # Create database engine for additional operations
        from sqlalchemy import create_engine
        engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
        
        # 1. Insert forecast performance data
        try:
            from models.forecast_performance import ForecastPerformance
            from models.inventory_item import db
            
            performance_record = ForecastPerformance(
                model_version=model_version,
                forecast_type='menu_item',
                item_id=None,  # Overall performance
                evaluation_date=datetime.now().date(),
                r2_score=best_r2_score,
                mae=results.get('performance', {}).get('mae'),
                rmse=results.get('performance', {}).get('rmse'),
                mape=results.get('performance', {}).get('mape')
            )
            db.session.add(performance_record)
            db.session.commit()
            logging.info(f"Forecast performance saved for model {model_version}")
        except Exception as e:
            logging.error(f"Error saving forecast performance: {str(e)}")
        
        # 2. Insert current forecasts data (copy from menu_item_forecasts to current_forecasts)
        try:
            with engine.begin() as conn:
                # Delete existing current forecasts for menu items
                delete_query = text("DELETE FROM current_forecasts WHERE item_type = 'menu_item'")
                conn.execute(delete_query)
                
                # Insert new current forecasts from latest menu_item_forecasts
                insert_query = text("""
                    INSERT INTO current_forecasts (item_id, item_type, item_name, forecast_date, predicted_quantity, confidence_lower, confidence_upper, model_version)
                    SELECT 
                        mif.menu_item_id,
                        'menu_item' as item_type,
                        mi.name as item_name,
                        mif.date as forecast_date,
                        mif.predicted_quantity,
                        mif.lower_bound as confidence_lower,
                        mif.upper_bound as confidence_upper,
                        mif.model_version
                    FROM menu_item_forecasts mif
                    JOIN menu_items mi ON mif.menu_item_id = mi.id
                    WHERE mif.model_version = :model_version
                """)
                conn.execute(insert_query, {'model_version': model_version})
                logging.info(f"Current forecasts updated for model {model_version}")
        except Exception as e:
            logging.error(f"Error updating current forecasts: {str(e)}")
        
        # 3. Calculate and insert ingredient forecasts
        try:
            # Get menu item forecasts from database
            with engine.connect() as conn:
                query = text("""
                    SELECT menu_item_id, date, predicted_quantity 
                    FROM menu_item_forecasts 
                    WHERE model_version = :model_version
                    ORDER BY menu_item_id, date
                """)
                result_forecasts = conn.execute(query, {'model_version': model_version})
                menu_forecasts = [{
                    'menu_item_id': row[0],
                    'date': row[1].strftime('%Y-%m-%d') if hasattr(row[1], 'strftime') else str(row[1]),
                    'predicted_quantity': float(row[2])
                } for row in result_forecasts]
            
            if menu_forecasts:
                # Calculate ingredient demand from menu item forecasts
                from services.unified_restaurant_demand_system import calculate_ingredient_demand_from_menu_forecasts, save_ingredient_forecasts_to_database
                ingredient_demands = calculate_ingredient_demand_from_menu_forecasts(
                    menu_forecasts, engine, model_version
                )
                
                if ingredient_demands:
                    # Save ingredient forecasts to database
                    save_ingredient_forecasts_to_database(ingredient_demands, model_version, engine)
                    logging.info(f"Ingredient forecasts calculated and saved for model {model_version}")
                else:
                    logging.warning("No ingredient demands calculated")
            else:
                logging.warning("No menu forecasts found to calculate ingredient demands")
        except Exception as e:
            logging.error(f"Error calculating ingredient forecasts: {str(e)}")
        
        # Helper function to convert numpy arrays and other non-serializable objects
        def make_serializable(obj):
            import numpy as np
            if isinstance(obj, np.ndarray):
                return obj.tolist()
            elif isinstance(obj, np.integer):
                return int(obj)
            elif isinstance(obj, np.floating):
                return float(obj)
            elif isinstance(obj, dict):
                return {k: make_serializable(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [make_serializable(item) for item in obj]
            else:
                return obj
        
        # Remove non-serializable objects (models) from results
        serializable_results = {
            'performance': make_serializable(results.get('performance', {})),
            'summary': make_serializable(results.get('summary', {}))
        }
        
        # Convert feature importance DataFrames to serializable format
        feature_importance = results.get('feature_importance', {})
        if feature_importance:
            serializable_results['feature_importance'] = {
                model_name: make_serializable(df.to_dict('records') if hasattr(df, 'to_dict') else df)
                for model_name, df in feature_importance.items()
            }
        
        # Filter new item predictions to exclude non-serializable objects
        new_item_predictions = results.get('new_item_predictions', {})
        if new_item_predictions:
            serializable_results['new_item_predictions'] = {
                item_name: {
                    'predictions': make_serializable(pred_data.get('predictions', {})),
                    'confidence': make_serializable(pred_data.get('confidence', 0)),
                    'estimated_r2': make_serializable(pred_data.get('estimated_r2', 0)),
                    'baseline_demand': make_serializable(pred_data.get('baseline_demand', 0))
                }
                for item_name, pred_data in new_item_predictions.items()
            }
        
        return jsonify(serializable_results), 200
        
    except Exception as e:
        logging.error(f"Error in XGBoost forecast: {str(e)}")
        return jsonify({'error': str(e)}), 500

@forecast_bp.route('/xgboost/data', methods=['GET'])
def get_xgboost_forecast_data():
    """Get forecast data from database for visualization."""
    try:
        forecast_type = request.args.get('forecast_type', 'menu_items')
        item_id = request.args.get('item_id')
        model_version = request.args.get('model_version')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        from sqlalchemy import create_engine
        from config import Config
        
        engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
        
        # Build query based on forecast type
        if forecast_type == 'menu_items':
            table_name = 'menu_item_forecasts'
            id_column = 'menu_item_id'
        else:
            table_name = 'ingredient_forecasts'
            id_column = 'ingredient_id'
        
        query = f"SELECT * FROM {table_name} WHERE 1=1"
        params = {}
        
        if item_id:
            query += f" AND {id_column} = :item_id"
            params['item_id'] = item_id
        
        if model_version:
            query += " AND model_version = :model_version"
            params['model_version'] = model_version
        
        if start_date:
            query += " AND date >= :start_date"
            params['start_date'] = start_date
        
        if end_date:
            query += " AND date <= :end_date"
            params['end_date'] = end_date
        
        query += " ORDER BY date"
        
        with engine.connect() as conn:
            result = conn.execute(text(query), params)
            data = [dict(row._mapping) for row in result]
        
        return jsonify(data), 200
        
    except Exception as e:
        logging.error(f"Error getting forecast data: {str(e)}")
        return jsonify({'error': str(e)}), 500

@forecast_bp.route('/xgboost/latest', methods=['GET'])
def get_latest_xgboost_forecast():
    """Get the latest forecast data for a specific item."""
    try:
        forecast_type = request.args.get('forecast_type', 'menu_items')
        item_id = request.args.get('item_id')
        
        if not item_id:
            return jsonify({'error': 'item_id is required'}), 400
        
        from sqlalchemy import create_engine
        from config import Config
        
        engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
        
        # Build query based on forecast type
        if forecast_type == 'menu_items':
            table_name = 'menu_item_forecasts'
            id_column = 'menu_item_id'
        else:
            table_name = 'ingredient_forecasts'
            id_column = 'ingredient_id'
        
        # Get the latest model version for this item
        query = f"""
            SELECT * FROM {table_name} 
            WHERE {id_column} = :item_id 
            AND model_version = (
                SELECT model_version FROM {table_name} 
                WHERE {id_column} = :item_id 
                ORDER BY updated_at DESC 
                LIMIT 1
            )
            ORDER BY date ASC
        """
        
        with engine.connect() as conn:
            result = conn.execute(text(query), {'item_id': item_id})
            rows = result.fetchall()
            columns = result.keys()
            
            data = [dict(zip(columns, row)) for row in rows]
            
            # Format the data for frontend consumption
            formatted_data = []
            for row in data:
                formatted_data.append({
                    'date': row['date'].strftime('%Y-%m-%d') if hasattr(row['date'], 'strftime') else str(row['date']),
                    'predicted': float(row['predicted_quantity']) if row['predicted_quantity'] is not None else 0,
                    'lower_bound': float(row['lower_bound']) if row.get('lower_bound') is not None else None,
                    'upper_bound': float(row['upper_bound']) if row.get('upper_bound') is not None else None,
                    'model_version': row['model_version']
                })
            
            return jsonify(formatted_data), 200
        
    except Exception as e:
        logging.error(f"Error getting latest forecast: {str(e)}")
        return jsonify({'error': str(e)}), 500

@forecast_bp.route('/current', methods=['GET'])
def get_current_forecasts():
    """Get current forecasts from appropriate table based on item_type."""
    try:
        item_type = request.args.get('item_type')  # 'menu_item' or 'ingredient'
        item_id = request.args.get('item_id')
        
        from sqlalchemy import create_engine
        from config import Config
        
        engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
        
        # Choose table and build query based on item_type
        if item_type == 'ingredient':
            # Use ingredient_forecasts table for ingredients
            query = """
                SELECT 
                    inf.id,
                    inf.ingredient_id as item_id,
                    'ingredient' as item_type,
                    i.name as item_name,
                    inf.date as forecast_date,
                    inf.predicted_quantity,
                    inf.lower_bound as confidence_lower,
                    inf.upper_bound as confidence_upper,
                    inf.model_version
                FROM ingredient_forecasts inf
                JOIN ingredients i ON inf.ingredient_id = i.id
                WHERE 1=1
            """
            params = {}
            
            if item_id:
                query += " AND inf.ingredient_id = :item_id"
                params['item_id'] = item_id
                
            query += " ORDER BY inf.date ASC"
            
        else:
            # Use current_forecasts table for menu items
            query = "SELECT * FROM current_forecasts WHERE 1=1"
            params = {}
            
            if item_type:
                query += " AND item_type = :item_type"
                params['item_type'] = item_type
                
            if item_id:
                query += " AND item_id = :item_id"
                params['item_id'] = item_id
                
            query += " ORDER BY forecast_date ASC"
        
        with engine.connect() as conn:
            result = conn.execute(text(query), params)
            rows = result.fetchall()
            columns = result.keys()
            
            data = [dict(zip(columns, row)) for row in rows]
            
            # Format the data for frontend consumption
            formatted_data = []
            for row in data:
                formatted_data.append({
                    'id': row['id'],
                    'item_id': row['item_id'],
                    'item_type': row['item_type'],
                    'item_name': row['item_name'],
                    'date': row['forecast_date'].strftime('%Y-%m-%d') if hasattr(row['forecast_date'], 'strftime') else str(row['forecast_date']),
                    'predicted': float(row['predicted_quantity']) if row['predicted_quantity'] is not None else 0,
                    'confidence_lower': float(row['confidence_lower']) if row.get('confidence_lower') is not None else None,
                    'confidence_upper': float(row['confidence_upper']) if row.get('confidence_upper') is not None else None,
                    'model_version': row['model_version']
                })
            
            return jsonify(formatted_data), 200
        
    except Exception as e:
        logging.error(f"Error getting current forecasts: {str(e)}")
        return jsonify({'error': str(e)}), 500

@forecast_bp.route('/current/update', methods=['POST'])
def update_current_forecasts():
    """Update current forecasts table with selected forecast data."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
            
        forecast_type = data.get('forecast_type')
        model_version = data.get('model_version')
        item_id = data.get('item_id')
        
        logging.info(f"Updating current forecasts - forecast_type: {forecast_type}, model_version: {model_version}, item_id: {item_id}")
        
        if not all([forecast_type, model_version, item_id]):
            return jsonify({'error': 'forecast_type, model_version, and item_id are required'}), 400
        
        from sqlalchemy import create_engine
        from config import Config
        
        engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
        
        # Determine source table and columns
        if forecast_type == 'menu_items':
            source_table = 'menu_item_forecasts'
            id_column = 'menu_item_id'
            item_type = 'menu_item'
        else:
            source_table = 'ingredient_forecasts'
            id_column = 'ingredient_id'
            item_type = 'ingredient'
        
        with engine.begin() as conn:
            # First, check if source forecast data exists
            check_query = f"SELECT COUNT(*) as count FROM {source_table} WHERE {id_column} = :item_id AND model_version = :model_version"
            check_result = conn.execute(text(check_query), {'item_id': item_id, 'model_version': model_version})
            count = check_result.fetchone()[0]
            
            if count == 0:
                return jsonify({'error': f'No forecast data found for {forecast_type} item {item_id} with model version {model_version}'}), 404
            
            logging.info(f"Found {count} forecast records to copy")
            
            # Delete existing records for this item
            delete_query = "DELETE FROM current_forecasts WHERE item_type = :item_type AND item_id = :item_id"
            conn.execute(text(delete_query), {'item_type': item_type, 'item_id': item_id})
            
            # Then insert new records from the selected forecast
            if forecast_type == 'menu_items':
                insert_query = """
                INSERT INTO current_forecasts (item_id, item_type, item_name, forecast_date, predicted_quantity, confidence_lower, confidence_upper, model_version)
                SELECT 
                    mif.menu_item_id,
                    'menu_item' as item_type,
                    CONCAT('Menu Item ', mif.menu_item_id) as item_name,
                    mif.date,
                    mif.predicted_quantity,
                    mif.lower_bound,
                    mif.upper_bound,
                    mif.model_version
                FROM menu_item_forecasts mif
                WHERE mif.menu_item_id = :item_id AND mif.model_version = :model_version
                ORDER BY mif.date ASC
                """
            else:
                insert_query = """
                INSERT INTO current_forecasts (item_id, item_type, item_name, forecast_date, predicted_quantity, confidence_lower, confidence_upper, model_version)
                SELECT 
                    inf.ingredient_id,
                    'ingredient' as item_type,
                    i.name as item_name,
                    inf.date,
                    inf.predicted_quantity,
                    inf.lower_bound,
                    inf.upper_bound,
                    inf.model_version
                FROM ingredient_forecasts inf
                JOIN ingredients i ON inf.ingredient_id = i.id
                WHERE inf.ingredient_id = :item_id AND inf.model_version = :model_version
                ORDER BY inf.date ASC
                """
            
            result = conn.execute(text(insert_query), {'item_id': item_id, 'model_version': model_version})
            
            # Check if any records were inserted
            if result.rowcount == 0:
                return jsonify({'error': f'No records were inserted. Check if forecast data exists for {forecast_type} item {item_id} with model version {model_version}'}), 400
            
            logging.info(f"Successfully updated {result.rowcount} forecast records for {item_type} {item_id}")
            
            return jsonify({
                'success': True,
                'message': f'Updated {result.rowcount} forecast records for {item_type} {item_id}'
            }), 200
        
    except Exception as e:
        logging.error(f"Error updating current forecasts: {str(e)}")
        logging.error(f"Request data: forecast_type={forecast_type}, model_version={model_version}, item_id={item_id}")
        return jsonify({'error': f'Database error: {str(e)}'}), 500

@forecast_bp.route('/xgboost/history', methods=['GET'])
def get_xgboost_forecast_history():
    """Get forecast history with enhanced filtering."""
    try:
        forecast_type = request.args.get('forecast_type', 'both')
        limit = int(request.args.get('limit', 10))
        selected_item = request.args.get('selected_item')
        forecast_horizon = request.args.get('forecast_horizon')
        
        # Convert selected_item to int if provided
        if selected_item:
            try:
                selected_item = int(selected_item)
            except ValueError:
                selected_item = None
        
        # Convert forecast_horizon to int if provided
        if forecast_horizon:
            try:
                forecast_horizon = int(forecast_horizon)
            except ValueError:
                forecast_horizon = None
        
        from services.unified_restaurant_demand_system import get_forecast_history
        history = get_forecast_history(
            forecast_type=forecast_type, 
            limit=limit, 
            selected_item=selected_item,
            forecast_horizon=forecast_horizon
        )
        return jsonify(history), 200
        
    except Exception as e:
        logging.error(f"Error getting forecast history: {str(e)}")
        return jsonify({'error': str(e)}), 500

@forecast_bp.route('/xgboost/compare', methods=['POST'])
def compare_xgboost_forecasts():
    """Compare multiple forecast versions with enhanced filtering."""
    try:
        data = request.get_json()
        model_versions = data.get('model_versions', [])
        forecast_type = data.get('forecast_type', 'menu_items')
        selected_item = data.get('selected_item')
        forecast_horizon = data.get('forecast_horizon')
        
        if not model_versions:
            return jsonify({'error': 'model_versions is required'}), 400
        
        # Convert selected_item to int if provided
        if selected_item:
            try:
                selected_item = int(selected_item)
            except ValueError:
                selected_item = None
        
        # Convert forecast_horizon to int if provided
        if forecast_horizon:
            try:
                forecast_horizon = int(forecast_horizon)
            except ValueError:
                forecast_horizon = None
        
        from services.unified_restaurant_demand_system import compare_forecasts
        comparison_data = compare_forecasts(
            model_versions, 
            forecast_type, 
            selected_item=selected_item,
            forecast_horizon=forecast_horizon
        )
        
        # Convert DataFrame to dict for JSON response
        result = comparison_data.to_dict(orient='records') if not comparison_data.empty else []
        
        return jsonify(result), 200
        
    except Exception as e:
        logging.error(f"Error comparing forecasts: {str(e)}")
        return jsonify({'error': str(e)}), 500

@forecast_bp.route('/xgboost/export', methods=['GET'])
def export_xgboost_forecast():
    """Export forecast data to CSV."""
    try:
        forecast_type = request.args.get('forecast_type', 'menu_items')
        model_version = request.args.get('model_version')
        
        from sqlalchemy import create_engine
        from config import Config
        import io
        from flask import make_response
        
        engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
        
        # Build query
        if forecast_type == 'menu_items':
            table_name = 'menu_item_forecasts'
        else:
            table_name = 'ingredient_forecasts'
        
        query = f"SELECT * FROM {table_name}"
        params = {}
        
        if model_version:
            query += " WHERE model_version = :model_version"
            params['model_version'] = model_version
        
        query += " ORDER BY date"
        
        with engine.connect() as conn:
            df = pd.read_sql(text(query), conn, params=params)
        
        # Create CSV response
        output = io.StringIO()
        df.to_csv(output, index=False)
        output.seek(0)
        
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = f'attachment; filename={forecast_type}_forecast_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        
        return response
        
    except Exception as e:
        logging.error(f"Error exporting forecast: {str(e)}")
        return jsonify({'error': str(e)}), 500

@forecast_bp.route('/xgboost/menu-items', methods=['GET'])
def get_menu_items_for_forecast():
    """Get available menu items for forecasting from MySQL database."""
    try:
        from models.menu_item import MenuItem
        
        # Get all menu items from the database
        menu_items_query = MenuItem.query.all()
        
        # Format the data for the frontend
        menu_items = []
        for item in menu_items_query:
            menu_items.append({
                'menu_item_id': item.id,
                'menu_item_name': item.menu_item_name
            })
        
        return jsonify(menu_items), 200
        
    except Exception as e:
        logging.error(f"Error getting menu items: {str(e)}")
        return jsonify({'error': str(e)}), 500

@forecast_bp.route('/xgboost/ingredients', methods=['GET'])
def get_ingredients_for_forecast():
    """Get available ingredients for forecasting."""
    try:
        from sqlalchemy import create_engine
        from config import Config
        
        engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
        
        with engine.connect() as conn:
            result = conn.execute(text("SELECT id, name FROM ingredients ORDER BY name"))
            ingredients = [{'id': row[0], 'name': row[1]} for row in result]
        
        return jsonify(ingredients), 200
        
    except Exception as e:
        logging.error(f"Error getting ingredients: {str(e)}")
        return jsonify({'error': str(e)}), 500

@forecast_bp.route('/xgboost/ingredient-demand', methods=['POST'])
def calculate_ingredient_demand_from_menu():
    """Calculate ingredient demand from menu item forecasts using recipes."""
    try:
        from sqlalchemy import create_engine
        
        data = request.get_json() or {}
        model_version = data.get('model_version')
        forecast_date = data.get('forecast_date')
        
        if not model_version:
            return jsonify({'error': 'model_version is required'}), 400
            
        # Create database engine
        engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
        
        # Get menu item forecasts from database
        with engine.connect() as conn:
            query = text("""
                SELECT menu_item_id, date, predicted_quantity 
                FROM menu_item_forecasts 
                WHERE model_version = :model_version
                ORDER BY menu_item_id, date
            """)
            result = conn.execute(query, {'model_version': model_version})
            menu_forecasts = [{
                'menu_item_id': row[0],
                'date': row[1].strftime('%Y-%m-%d') if hasattr(row[1], 'strftime') else str(row[1]),
                'predicted_quantity': float(row[2])
            } for row in result]
        
        if not menu_forecasts:
            return jsonify({'error': f'No menu item forecasts found for model_version: {model_version}'}), 404
            
        # Calculate ingredient demand from menu item forecasts using Recipe table
        from services.unified_restaurant_demand_system import calculate_ingredient_demand_from_menu_forecasts, save_ingredient_forecasts_to_database
        results = calculate_ingredient_demand_from_menu_forecasts(
            menu_forecasts, engine, model_version
        )
        
        if not results:
            return jsonify({'error': 'Failed to calculate ingredient demand'}), 500
        
        # Save ingredient forecasts to database
        save_ingredient_forecasts_to_database(results, model_version, engine)
            
        return jsonify({
            'message': 'Ingredient demand calculated and saved successfully',
            'model_version': model_version,
            'ingredients_processed': len(results),
            'ingredient_demands': results
        }), 200
        
    except Exception as e:
        logging.error(f"Error calculating ingredient demand: {str(e)}")
        return jsonify({'error': str(e)}), 500


@forecast_bp.route('/menu-item/<int:menu_item_id>/ingredients', methods=['GET'])
def get_ingredients_for_menu_item(menu_item_id):
    """Get ingredients used in a specific menu item based on recipes."""
    try:
        from models.recipe import Recipe
        from models.ingredient import Ingredient
        
        # Get recipes for the menu item
        recipes = Recipe.query.filter_by(dish_id=menu_item_id).all()
        
        if not recipes:
            return jsonify([]), 200
        
        # Get ingredient details for each recipe
        ingredients = []
        for recipe in recipes:
            ingredient = Ingredient.query.get(recipe.ingredient_id)
            if ingredient:
                ingredients.append({
                    'id': ingredient.id,
                    'name': ingredient.name,
                    'category': ingredient.category,
                    'unit': ingredient.unit,
                    'quantity_per_unit': recipe.quantity_per_unit
                })
        
        return jsonify(ingredients), 200
        
    except Exception as e:
        logging.error(f"Error getting ingredients for menu item {menu_item_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@forecast_bp.route('/xgboost/ingredient-demand-data', methods=['GET'])
def get_ingredient_demand_data():
    """Get ingredient demand forecast data for display."""
    try:
        from sqlalchemy import create_engine
        from config import Config
        
        engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
        ingredient_id = request.args.get('ingredient_id')
        model_version = request.args.get('model_version')
        
        if not ingredient_id:
            return jsonify({'error': 'ingredient_id is required'}), 400
            
        with engine.connect() as conn:
            # Get ingredient demand forecast data
            query = text("""
                SELECT date, predicted_quantity, ingredient_id
                FROM ingredient_forecasts 
                WHERE ingredient_id = :ingredient_id
                AND (:model_version IS NULL OR model_version = :model_version)
                ORDER BY date
            """)
            
            result = conn.execute(query, {
                'ingredient_id': ingredient_id,
                'model_version': model_version
            })
            
            demand_data = []
            for row in result:
                demand_data.append({
                    'date': row[0].strftime('%Y-%m-%d') if row[0] else None,
                    'predicted_demand': float(row[1]) if row[1] else 0,
                    'ingredient_id': row[2]
                })
        
        return jsonify(demand_data), 200
        
    except Exception as e:
        logging.error(f"Error getting ingredient demand data: {str(e)}")
        return jsonify({'error': str(e)}), 500

@forecast_bp.route('/xgboost/comprehensive-ingredient-demand', methods=['GET'])
def get_comprehensive_ingredient_demand():
    """Get comprehensive ingredient demand analysis aggregated across all menu items."""
    try:
        from sqlalchemy import create_engine
        from config import Config
        
        engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
        model_version = request.args.get('model_version')
        days = int(request.args.get('days', 7))  # Default to 7 days
        
        with engine.connect() as conn:
            # Get all ingredient demand forecasts, aggregated by ingredient and date
            query = text("""
                SELECT 
                    i.id as ingredient_id,
                    i.name as ingredient_name,
                    i.unit as ingredient_unit,
                    inf.date,
                    SUM(inf.predicted_quantity) as total_predicted_demand,
                    COUNT(DISTINCT inf.ingredient_id) as menu_items_count
                FROM ingredient_forecasts inf
                JOIN ingredients i ON inf.ingredient_id = i.id
                WHERE (:model_version IS NULL OR inf.model_version = :model_version)
                AND inf.date >= CURDATE()
                AND inf.date <= DATE_ADD(CURDATE(), INTERVAL :days DAY)
                GROUP BY i.id, i.name, i.unit, inf.date
                ORDER BY i.name, inf.date
            """)
            
            result = conn.execute(query, {
                'model_version': model_version,
                'days': days
            })
            
            # Organize data by ingredient
            ingredient_demands = {}
            for row in result:
                ingredient_id = row[0]
                ingredient_name = row[1]
                ingredient_unit = row[2]
                date = row[3]
                total_demand = float(row[4]) if row[4] else 0
                menu_items_count = row[5]
                
                if ingredient_id not in ingredient_demands:
                    ingredient_demands[ingredient_id] = {
                        'ingredient_id': ingredient_id,
                        'ingredient_name': ingredient_name,
                        'ingredient_unit': ingredient_unit,
                        'daily_demands': [],
                        'total_demand': 0,
                        'peak_demand': 0,
                        'avg_daily_demand': 0,
                        'menu_items_using': menu_items_count
                    }
                
                ingredient_demands[ingredient_id]['daily_demands'].append({
                    'date': date.strftime('%Y-%m-%d') if date else None,
                    'predicted_demand': total_demand
                })
                
                ingredient_demands[ingredient_id]['total_demand'] += total_demand
                ingredient_demands[ingredient_id]['peak_demand'] = max(
                    ingredient_demands[ingredient_id]['peak_demand'], 
                    total_demand
                )
            
            # Calculate averages
            for ingredient_data in ingredient_demands.values():
                if ingredient_data['daily_demands']:
                    ingredient_data['avg_daily_demand'] = (
                        ingredient_data['total_demand'] / len(ingredient_data['daily_demands'])
                    )
            
            # Get menu items that use each ingredient for context
            menu_items_query = text("""
                SELECT 
                    i.id as ingredient_id,
                    i.name as ingredient_name,
                    mi.id as menu_item_id,
                    mi.menu_item_name,
                    r.quantity_per_unit,
                    r.recipe_unit
                FROM ingredients i
                JOIN recipes r ON i.id = r.ingredient_id
                JOIN menu_item mi ON r.dish_id = mi.id
                WHERE i.id IN :ingredient_ids
                ORDER BY i.name, mi.menu_item_name
            """)
            
            ingredient_ids = tuple(ingredient_demands.keys()) if ingredient_demands else (0,)
            menu_items_result = conn.execute(menu_items_query, {
                'ingredient_ids': ingredient_ids
            })
            
            # Add menu items context to each ingredient
            for row in menu_items_result:
                ingredient_id = row[0]
                if ingredient_id in ingredient_demands:
                    if 'menu_items' not in ingredient_demands[ingredient_id]:
                        ingredient_demands[ingredient_id]['menu_items'] = []
                    
                    ingredient_demands[ingredient_id]['menu_items'].append({
                        'menu_item_id': row[2],
                        'menu_item_name': row[3],
                        'quantity_per_unit': float(row[4]) if row[4] else 0,
                        'recipe_unit': row[5]
                    })
        
        # Convert to list format
        result_data = list(ingredient_demands.values())
        
        return jsonify({
            'ingredients': result_data,
            'total_ingredients': len(result_data),
            'model_version': model_version,
            'forecast_days': days
        }), 200
        
    except Exception as e:
        logging.error(f"Error getting comprehensive ingredient demand: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Unified Restaurant Demand System Endpoints
@forecast_bp.route('/unified/run', methods=['POST'])
def run_unified_forecast_api():
    """Run unified restaurant demand system forecast for selected menu item."""
    try:
        data = request.get_json() or {}
        
        # Get parameters from request
        forecast_days = int(data.get('forecast_days', 28))
        selected_item = data.get('selected_item')  # Item ID for specific forecasting
        
        if not selected_item:
            return jsonify({'error': 'selected_item parameter is required'}), 400
        
        # Get menu item details from database
        from models.menu_item import MenuItem
        menu_item = MenuItem.query.get(selected_item)
        if not menu_item:
            return jsonify({'error': f'Menu item with ID {selected_item} not found'}), 404
        
        # Initialize the unified predictor
        data_path = "C:/Users/User/Desktop/first-app/instance/cleaned_streamlined_ultimate_malaysian_data.csv"
        predictor = RestaurantDemandPredictor(data_path)
        
        # Run item-specific analysis
        results = predictor.run_item_specific_analysis(selected_item, menu_item.menu_item_name, forecast_days)
        
        if not results:
            return jsonify({'error': 'Failed to generate forecast'}), 500
        
        # Generate model version
        model_version = f'unified_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
        
        # Save forecast results to database
        from services.unified_restaurant_demand_system import save_forecast_to_database, save_performance_metrics
        
        # Save forecast data to menu_item_forecasts table
        if 'forecasts' in results:
            save_forecast_to_database(
                model_version=model_version,
                item_id=selected_item,
                item_name=menu_item.menu_item_name,
                forecasts=results['forecasts'],
                forecast_type='menu_item'
            )
        
        # Save performance metrics to forecast_performance table
        if 'performance' in results:
            # Extract the actual metrics from the nested performance structure
            performance_data = results['performance']
            print(f"DEBUG: Performance data for item {selected_item}: {performance_data}")
            if isinstance(performance_data, dict) and performance_data:
                # Get the first (and likely only) model's metrics
                best_model_metrics = next(iter(performance_data.values()))
                print(f"DEBUG: Best model metrics for item {selected_item}: {best_model_metrics}")
                
                # Convert numpy values to regular Python types for database compatibility
                converted_metrics = {}
                for key, value in best_model_metrics.items():
                    if key == 'predictions':  # Skip predictions array
                        continue
                    elif hasattr(value, 'item') and hasattr(value, 'shape') and value.shape == ():  # numpy scalar
                        converted_metrics[key] = float(value.item())
                    elif isinstance(value, (int, float)):
                        converted_metrics[key] = float(value)
                    else:
                        converted_metrics[key] = value
                
                print(f"Converted metrics: {converted_metrics}")
                save_performance_metrics(
                    model_version=model_version,
                    forecast_type='menu_item',
                    item_id=selected_item,
                    metrics=converted_metrics,
                    engine=create_engine(Config.SQLALCHEMY_DATABASE_URI)
                )
            else:
                print(f"Warning: Performance data structure unexpected for item {selected_item}: {performance_data}")
        
        # 2. Update current_forecasts table from menu_item_forecasts
        try:
            engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
            with engine.begin() as conn:
                # Delete existing current forecasts for this item
                delete_query = text("DELETE FROM current_forecasts WHERE item_type = 'menu_item' AND item_id = :item_id")
                conn.execute(delete_query, {'item_id': selected_item})
                
                # Insert new current forecasts from latest menu_item_forecasts
                insert_query = text("""
                    INSERT INTO current_forecasts (item_id, item_type, item_name, forecast_date, predicted_quantity, confidence_lower, confidence_upper, model_version)
                    SELECT 
                        mif.menu_item_id,
                        'menu_item' as item_type,
                        mi.menu_item_name as item_name,
                        mif.date as forecast_date,
                        mif.predicted_quantity,
                        mif.lower_bound as confidence_lower,
                        mif.upper_bound as confidence_upper,
                        mif.model_version
                    FROM menu_item_forecasts mif
                    JOIN menu_item mi ON mif.menu_item_id = mi.id
                    WHERE mif.model_version = :model_version AND mif.menu_item_id = :item_id
                """)
                conn.execute(insert_query, {'model_version': model_version, 'item_id': selected_item})
                logging.info(f"Current forecasts updated for menu item {selected_item} with model {model_version}")
        except Exception as e:
            logging.error(f"Error updating current forecasts: {str(e)}")
        
        # 3. Calculate and insert ingredient forecasts
        try:
            from services.unified_restaurant_demand_system import calculate_ingredient_demand_from_menu_forecasts, save_ingredient_forecasts_to_database
            
            # Get menu forecasts for this model version
            engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
            with engine.connect() as conn:
                query = text("""
                    SELECT menu_item_id, date, predicted_quantity 
                    FROM menu_item_forecasts 
                    WHERE model_version = :model_version
                    ORDER BY menu_item_id, date
                """)
                result_forecasts = conn.execute(query, {'model_version': model_version})
                menu_forecasts = [{
                    'menu_item_id': row[0],
                    'date': row[1].strftime('%Y-%m-%d') if hasattr(row[1], 'strftime') else str(row[1]),
                    'predicted_quantity': float(row[2])
                } for row in result_forecasts]
            
            if menu_forecasts:
                # Calculate ingredient demand from menu item forecasts
                ingredient_demands = calculate_ingredient_demand_from_menu_forecasts(
                    menu_forecasts, engine, model_version
                )
                
                if ingredient_demands:
                    # Save ingredient forecasts to database
                    save_ingredient_forecasts_to_database(ingredient_demands, model_version, engine)
                    logging.info(f"Ingredient forecasts calculated and saved for model {model_version}")
                else:
                    logging.warning("No ingredient demands calculated")
            else:
                logging.warning("No menu forecasts found to calculate ingredient demands")
        except Exception as e:
            logging.error(f"Error calculating ingredient forecasts: {str(e)}")
        
        # Convert numpy arrays to lists for JSON serialization
        def convert_numpy_to_list(obj):
            if isinstance(obj, dict):
                return {k: convert_numpy_to_list(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_numpy_to_list(item) for item in obj]
            elif hasattr(obj, 'tolist'):  # numpy array
                return obj.tolist()
            elif hasattr(obj, 'item'):  # numpy scalar
                return obj.item()
            else:
                return obj
        
        # Format response for frontend compatibility
        menu_items_data = {
            menu_item.menu_item_name: {
                'metrics': convert_numpy_to_list(results.get('performance', {})),
                'forecasts': convert_numpy_to_list(results.get('forecasts', []))
            }
        }
        
        response_data = {
            'menu_items': menu_items_data,
            'ingredients': {},  # Will be calculated from menu items
            'metrics': convert_numpy_to_list(results.get('summary', {})),
            'model_version': model_version,
            'forecast_days': forecast_days,
            'best_model': results.get('best_model', 'Random Forest'),
            'best_r2_score': float(results.get('performance', {}).get('r2_score', 0)) if results.get('performance', {}).get('r2_score') is not None else 0,
            'selected_item_id': selected_item,
            'selected_item_name': menu_item.menu_item_name
        }
        
        return jsonify(response_data), 200
        
    except Exception as e:
        logging.error(f"Error in unified forecast: {str(e)}")
        return jsonify({'error': str(e)}), 500

# --- New endpoints for full inventory management (ingredients + inventory) ---

@inventory_bp.route('/full', methods=['GET'])
def get_full_inventory():
    """
    Get all inventory items with joined ingredient info.
    Returns: id, name, category, unit, min_threshold, quantity, last_updated
    """
    # Assuming InventoryItem is mapped to inventory table, and Ingredient model exists
    from models.ingredient import Ingredient
    results = db.session.query(
        InventoryItem.id,
        Ingredient.name,
        Ingredient.category,
        Ingredient.unit,
        Ingredient.min_threshold,
        InventoryItem.quantity,
        InventoryItem.last_updated
    ).join(Ingredient, InventoryItem.ingredient_id == Ingredient.id).all()
    data = []
    for row in results:
        data.append({
            'id': row.id,
            'name': row.name,
            'category': row.category,
            'unit': row.unit,
            'min_threshold': float(row.min_threshold) if row.min_threshold is not None else 0,
            'quantity': float(row.quantity),
            'last_updated': row.last_updated.isoformat() if row.last_updated else None
        })
    return jsonify(data), 200

@inventory_bp.route('/full', methods=['POST'])
def add_full_inventory():
    """
    Add a new ingredient and inventory record, or update inventory if ingredient exists.
    Expects: name, category, unit, min_threshold, quantity
    """
    from models.ingredient import Ingredient
    data = request.get_json()
    name = data.get('name')
    category = data.get('category')
    unit = data.get('unit')
    min_threshold = data.get('min_threshold', 0)
    quantity = data.get('quantity', 0)
    if not name or not unit:
        return jsonify({'error': 'Name and unit are required.'}), 400
    # Check if ingredient exists
    ingredient = Ingredient.query.filter_by(name=name, category=category, unit=unit).first()
    if not ingredient:
        # Create new ingredient
        ingredient = Ingredient(
            name=name,
            category=category,
            unit=unit,
            min_threshold=min_threshold
        )
        db.session.add(ingredient)
        db.session.commit()
    else:
        # Update min_threshold if changed
        if min_threshold != ingredient.min_threshold:
            ingredient.min_threshold = min_threshold
            db.session.commit()
    # Add inventory record
    inventory_item = InventoryItem(
        ingredient_id=ingredient.id,
        quantity=quantity,
        last_updated=datetime.utcnow()
    )
    db.session.add(inventory_item)
    db.session.commit()
    
    # Trigger alert checks after adding new inventory
    from services.stock_alerts import run_all_alert_checks
    try:
        run_all_alert_checks()
    except Exception as e:
        logging.warning(f"Alert check failed after adding inventory: {str(e)}")
    
    return jsonify({'message': 'Inventory item added successfully.'}), 201

@inventory_bp.route('/full/<int:item_id>', methods=['DELETE'])
def delete_full_inventory(item_id):
    """
    删除指定 id 的库存项（基于 InventoryItem.id）。
    """
    item = InventoryItem.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    return jsonify({'message': 'Inventory item deleted successfully.'}), 200

@inventory_bp.route('/full/<int:item_id>', methods=['PUT'])
def update_full_inventory(item_id):
    """
    更新指定 id 的库存项（基于 InventoryItem.id），可更新 quantity、min_threshold。
    """
    from models.ingredient import Ingredient
    from services.stock_alerts import run_all_alert_checks
    
    item = InventoryItem.query.get_or_404(item_id)
    data = request.get_json()
    # 更新库存数量
    if 'quantity' in data:
        item.quantity = data['quantity']
    # 更新 last_updated
    item.last_updated = datetime.utcnow()
    # 更新 ingredient 的 min_threshold（如有）
    if 'min_threshold' in data:
        ingredient = Ingredient.query.get(item.ingredient_id)
        if ingredient:
            ingredient.min_threshold = data['min_threshold']
            db.session.commit()
    db.session.commit()
    
    # Trigger alert checks after inventory update
    try:
        run_all_alert_checks()
    except Exception as e:
        logging.warning(f"Alert check failed after inventory update: {str(e)}")
    
    return jsonify({'message': 'Inventory item updated successfully.'}), 200

# Forecasting check endpoint
@forecasting_bp.route('/check-prediction/<int:menu_item_id>', methods=['GET'])
def check_prediction_data(menu_item_id):
    """
    Check if a menu item has prediction data in current_forecasts table.
    """
    try:
        engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
        
        with engine.connect() as conn:
            # Check if there's forecast data for this menu item
            query = text("""
                SELECT COUNT(*) as count
                FROM current_forecasts 
                WHERE item_type = 'menu_item' AND item_id = :item_id
            """)
            
            result = conn.execute(query, {'item_id': menu_item_id})
            row = result.fetchone()
            
            has_prediction = row[0] > 0 if row else False
            
            return jsonify({
                'success': True,
                'hasPrediction': has_prediction,
                'menu_item_id': menu_item_id
            }), 200
            
    except Exception as e:
        logging.error(f"Error checking prediction data for menu item {menu_item_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'hasPrediction': False
        }), 500

