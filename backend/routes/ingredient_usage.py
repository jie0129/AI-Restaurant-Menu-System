from flask import Blueprint, jsonify, request
import pandas as pd
import os
import re
from datetime import datetime, timedelta, date
from sqlalchemy import create_engine, text
from config import Config
from models.customer_order import CustomerOrder

bp = Blueprint('ingredient_usage', __name__)

def parse_ingredient_string(ingredient_str):
    unit_map = {
        'slice': 'slices', 'slices': 'slices',
        'pcs': 'pcs', 'piece': 'pcs', 'pieces': 'pcs',
        'tbsp': 'tbsp', 'tablespoon': 'tbsp', 'tablespoons': 'tbsp',
        'tsp': 'tsp', 'teaspoon': 'tsp', 'teaspoons': 'tsp',
        'g': 'g', 'gram': 'g', 'grams': 'g',
        'ml': 'ml', 'milliliter': 'ml', 'milliliters': 'ml',
        'mg': 'mg', 'milligram': 'mg', 'milligrams': 'mg',
        'leaf': 'leaves', 'leaves': 'leaves',
        'ring': 'rings', 'rings': 'rings',
        'base': 'bases', 'bases': 'bases'
    }
    result = {}
    for item in ingredient_str.split(','):
        name, qty = item.strip().rsplit('(', 1)
        name = name.strip()
        qty = qty.strip(')').strip()
        match = re.match(r"([\d.]+)\s*([a-zA-Z]+)", qty)
        if match:
            amount, unit = match.groups()
            unit = unit.lower()
            unit = unit_map.get(unit, unit)  # 标准化单位
            result[name] = {'amount': float(amount), 'unit': unit}
        else:
            result[name] = {'amount': 0, 'unit': ''}
    return result

@bp.route('/api/ingredient-usage-trends', methods=['GET'])
def ingredient_usage_trends():
    """Get ingredient usage trends from customer orders."""
    try:
        range_type = request.args.get('range', 'daily')
        unit_filter = request.args.get('unit')
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        
        # Parse date parameters
        start_date = None
        end_date = None
        if start_date_str:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        if end_date_str:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        
        # Default to last 30 days if no dates provided
        if not start_date and not end_date:
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=30)
        
        if range_type == 'daily':
            # Get daily usage trends
            result = []
            current_date = start_date
            while current_date <= end_date:
                daily_usage = CustomerOrder.get_daily_ingredient_usage(current_date)
                for usage in daily_usage:
                    if unit_filter and unit_filter != 'all' and usage['unit'] != unit_filter:
                        continue
                    result.append({
                        'date': current_date.strftime('%Y-%m-%d'),
                        'ingredient': usage['ingredient_name'],
                        'usage': float(usage['total_quantity']),
                        'unit': usage['unit'],
                        'category': usage['category']
                    })
                current_date += timedelta(days=1)
            return jsonify({'daily': result})
        
        elif range_type == 'weekly':
            # Get weekly aggregated usage
            result = []
            current_date = start_date
            while current_date <= end_date:
                week_start = current_date - timedelta(days=current_date.weekday())
                week_end = week_start + timedelta(days=6)
                week_usage = {}
                
                # Aggregate usage for the week
                for day in range(7):
                    day_date = week_start + timedelta(days=day)
                    if day_date > end_date:
                        break
                    daily_usage = CustomerOrder.get_daily_ingredient_usage(day_date)
                    for usage in daily_usage:
                        if unit_filter and unit_filter != 'all' and usage['unit'] != unit_filter:
                            continue
                        key = usage['ingredient_name']
                        if key not in week_usage:
                            week_usage[key] = {
                                'usage': 0,
                                'unit': usage['unit'],
                                'category': usage['category']
                            }
                        week_usage[key]['usage'] += usage['total_quantity']
                
                week_str = f"{week_start.year}-W{week_start.isocalendar()[1]:02d}"
                for ingredient, data in week_usage.items():
                    result.append({
                        'week': week_str,
                        'ingredient': ingredient,
                        'usage': float(data['usage']),
                        'unit': data['unit'],
                        'category': data['category']
                    })
                
                current_date = week_end + timedelta(days=1)
            return jsonify({'weekly': result})
        
        elif range_type == 'monthly':
            # Get monthly aggregated usage
            result = []
            current_date = start_date.replace(day=1)  # Start from first day of month
            
            while current_date <= end_date:
                # Get last day of current month
                if current_date.month == 12:
                    next_month = current_date.replace(year=current_date.year + 1, month=1)
                else:
                    next_month = current_date.replace(month=current_date.month + 1)
                month_end = next_month - timedelta(days=1)
                
                if month_end > end_date:
                    month_end = end_date
                
                # Get category distribution for the month
                month_usage, month_units = CustomerOrder.get_ingredient_category_distribution(current_date, month_end)
                
                month_str = current_date.strftime('%Y-%m')
                for category, usage in month_usage.items():
                    if unit_filter and unit_filter != 'all':
                        # For monthly view, we'll show all categories but note the filter
                        pass
                    result.append({
                        'month': month_str,
                        'category': category,
                        'usage': float(usage)
                    })
                
                # Move to next month
                if current_date.month == 12:
                    current_date = current_date.replace(year=current_date.year + 1, month=1)
                else:
                    current_date = current_date.replace(month=current_date.month + 1)
            
            return jsonify({'monthly': result})
        
        else:
            return jsonify({'error': 'Invalid range. Use daily, weekly, or monthly'}), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/api/ingredient-category-distribution', methods=['GET'])
def ingredient_category_distribution():
    """Get ingredient usage distribution by category from customer orders."""
    try:
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        month_str = request.args.get('month')  # Format: YYYY-MM
        unit_filter = request.args.get('unit', 'all')  # Unit filter parameter
        
        # Parse date parameters
        start_date = None
        end_date = None
        
        if month_str:
            # Parse month parameter (YYYY-MM format)
            try:
                year, month = map(int, month_str.split('-'))
                start_date = date(year, month, 1)
                # Get last day of the month
                if month == 12:
                    end_date = date(year + 1, 1, 1) - timedelta(days=1)
                else:
                    end_date = date(year, month + 1, 1) - timedelta(days=1)
            except (ValueError, IndexError):
                return jsonify({'error': 'Invalid month format. Use YYYY-MM'}), 400
        elif start_date_str and end_date_str:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        else:
            # Default to current month (August 2025)
            current_date = date(2025, 8, 1)  # August 2025
            start_date = current_date
            end_date = date(2025, 8, 31)  # Last day of August 2025
        
        # Get category distribution from customer orders with unit filtering
        category_usage, category_units = CustomerOrder.get_ingredient_category_distribution(start_date, end_date, unit_filter)
        
        # Format result for frontend
        result = []
        for category, total_usage in category_usage.items():
            result.append({
                'name': category or 'Unknown',
                'value': round(float(total_usage), 2),
                'units': category_units.get(category, [])
            })
        
        # Sort by usage amount (descending)
        result.sort(key=lambda x: x['value'], reverse=True)
        
        return jsonify({
            'categoryDistribution': result,
            'period': {
                'start_date': start_date.strftime('%Y-%m-%d') if start_date else None,
                'end_date': end_date.strftime('%Y-%m-%d') if end_date else None
            },
            'unit_filter': unit_filter
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/api/forecasted-demand', methods=['GET'])
def forecasted_demand():
    ingredient_id = request.args.get('ingredient_id')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    if not ingredient_id:
        return {'error': 'ingredient_id is required'}, 400
    engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
    with engine.connect() as conn:
        # 历史 usage
        actual_sql = """
            SELECT used_on as date, SUM(quantity_used) as actual
            FROM ingredient_usage
            WHERE ingredient_id = :ingredient_id
        """
        if start_date:
            actual_sql += " AND used_on >= :start_date"
        if end_date:
            actual_sql += " AND used_on <= :end_date"
        actual_sql += " GROUP BY used_on"
        params = {'ingredient_id': ingredient_id}
        if start_date:
            params['start_date'] = start_date
        if end_date:
            params['end_date'] = end_date
        actual_rows = conn.execute(text(actual_sql), params).fetchall()
        actual_map = {str(row[0]): float(row[1]) for row in actual_rows}
        # 预测
        forecast_sql = """
            SELECT date, predicted_quantity as forecast
            FROM forecasted_demand
            WHERE ingredient_id = :ingredient_id
        """
        if start_date:
            forecast_sql += " AND date >= :start_date"
        if end_date:
            forecast_sql += " AND date <= :end_date"
        forecast_sql += " ORDER BY date"
        forecast_rows = conn.execute(text(forecast_sql), params).fetchall()
        result = []
        for row in forecast_rows:
            date = str(row[0])
            forecast = float(row[1])
            actual = actual_map.get(date)
            result.append({'date': date, 'actual': actual, 'forecast': forecast})
    return jsonify(result)

@bp.route('/api/ingredient-list', methods=['GET'])
def ingredient_list():
    engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
    with engine.connect() as conn:
        rows = conn.execute(text("SELECT id, name FROM ingredients ORDER BY name")).fetchall()
        result = [{'id': row[0], 'name': row[1]} for row in rows]
    return jsonify(result)