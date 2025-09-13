from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
from models.customer_order import CustomerOrder
from models.menu_item import MenuItem
from models.inventory_item import InventoryItem
from models.ingredient import Ingredient
from models.recipe import Recipe
from models.menu_nutrition import MenuNutrition
from models.menu_item_image import MenuItemImage
from models.stock_alert import StockAlert
from sqlalchemy import func, text
from datetime import datetime, timedelta
from models import db
import logging

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/api/dashboard')

@dashboard_bp.route('/orders', methods=['GET'])
@cross_origin(origins="*")
def get_dashboard_orders():
    """Get recent orders for dashboard display"""
    try:
        # Get recent orders (last 10) with menu item details
        orders = db.session.query(
            CustomerOrder.id,
            CustomerOrder.order_number,
            CustomerOrder.quantity_ordered,
            CustomerOrder.total_price,
            CustomerOrder.order_status,
            CustomerOrder.order_date,
            CustomerOrder.customer_name,
            MenuItem.menu_item_name
        ).join(
            MenuItem, CustomerOrder.menu_item_id == MenuItem.id
        ).order_by(
            CustomerOrder.order_date.desc()
        ).limit(10).all()
        
        # Group orders by order_number to combine items
        order_groups = {}
        for order in orders:
            order_num = order.order_number
            if order_num not in order_groups:
                order_groups[order_num] = {
                    'id': order.id,
                    'orderNumber': order_num,
                    'tableNumber': f"Table {(order.id % 20) + 1}",  # Simulate table numbers
                    'items': [],
                    'total': 0,
                    'status': order.order_status,
                    'time': order.order_date.strftime('%H:%M') if order.order_date else '',
                    'customer': order.customer_name or 'Guest'
                }
            
            order_groups[order_num]['items'].append({
                'name': order.menu_item_name,
                'quantity': order.quantity_ordered
            })
            order_groups[order_num]['total'] += order.total_price
        
        # Convert to list and format
        formatted_orders = []
        for order_data in list(order_groups.values())[:5]:  # Limit to 5 for dashboard
            formatted_orders.append({
                'id': order_data['id'],
                'orderNumber': order_data['orderNumber'],
                'tableNumber': order_data['tableNumber'],
                'items': ', '.join([f"{item['name']} x{item['quantity']}" for item in order_data['items']]),
                'total': f"{order_data['total']:.2f}",
                'status': order_data['status'],
                'time': order_data['time']
            })
        
        return jsonify(formatted_orders), 200
        
    except Exception as e:
        logging.error(f"Error fetching dashboard orders: {str(e)}")
        return jsonify({'error': str(e)}), 500

@dashboard_bp.route('/pending-menu', methods=['GET'])
@cross_origin(origins="*")
def get_pending_menu_items():
    """Get menu items that are missing essential information"""
    try:
        # Find menu items missing nutrition info, pricing, or recipes
        pending_items = []
        
        # Get all menu items
        menu_items = MenuItem.query.all()
        
        for item in menu_items:
            missing_components = []
            
            # Check for missing price
            if not item.menu_price or item.menu_price <= 0:
                missing_components.append('Price')
            
            # Check for missing images
            images = MenuItemImage.query.filter_by(menu_item_id=item.id).all()
            if not images:
                missing_components.append('Image')
            
            # Check for missing nutrition info
            nutrition = MenuNutrition.query.filter_by(menu_item_id=item.id).first()
            if not nutrition:
                missing_components.append('Nutrition Info')
            
            # Check for missing recipes
            recipes = Recipe.query.filter_by(dish_id=item.id).all()
            if not recipes:
                missing_components.append('Recipe')
            
            if missing_components:
                completion_percentage = max(0, 100 - (len(missing_components) * 25))
                pending_items.append({
                    'name': item.menu_item_name,
                    'missingComponents': ', '.join(missing_components),
                    'completionPercentage': completion_percentage
                })
        
        return jsonify(pending_items), 200  # Return all pending items
        
    except Exception as e:
        logging.error(f"Error fetching pending menu items: {str(e)}")
        return jsonify({'error': str(e)}), 500

@dashboard_bp.route('/unavailable-items', methods=['GET'])
@cross_origin(origins="*")
def get_unavailable_items():
    """Get menu items that are unavailable due to low stock"""
    try:
        unavailable_items = []
        
        # Get all menu items
        menu_items = MenuItem.query.all()
        
        for menu_item in menu_items:
            # Get recipes for this menu item
            recipes = Recipe.query.filter_by(dish_id=menu_item.id).all()
            
            is_available = True
            missing_ingredients = []
            
            for recipe in recipes:
                # Check if ingredient has sufficient stock
                inventory = InventoryItem.query.filter_by(ingredient_id=recipe.ingredient_id).first()
                ingredient = Ingredient.query.get(recipe.ingredient_id)
                
                if not inventory or not ingredient:
                    is_available = False
                    missing_ingredients.append(ingredient.name if ingredient else f'Ingredient {recipe.ingredient_id}')
                else:
                    # Convert recipe quantity to inventory unit for proper comparison
                    from routes.order import convert_recipe_to_inventory_unit
                    converted_required = convert_recipe_to_inventory_unit(
                        recipe.quantity_per_unit, 
                        recipe.recipe_unit, 
                        ingredient
                    )
                    
                    if float(inventory.quantity) < converted_required:
                        is_available = False
                        missing_ingredients.append(ingredient.name)
            
            if not is_available:
                reason = f"Low stock: {', '.join(missing_ingredients[:2])}"
                if len(missing_ingredients) > 2:
                    reason += f" and {len(missing_ingredients) - 2} more"
                
                unavailable_items.append({
                    'name': menu_item.menu_item_name,
                    'reason': reason,
                    'estimatedRestock': '2-3 days'  # Default estimate
                })
        
        return jsonify(unavailable_items[:5]), 200  # Limit to 5 for dashboard
        
    except Exception as e:
        logging.error(f"Error fetching unavailable items: {str(e)}")
        return jsonify({'error': str(e)}), 500

@dashboard_bp.route('/daily-sales', methods=['GET'])
@cross_origin(origins="*")
def get_daily_sales():
    """Get daily sales metrics"""
    try:
        today = datetime.now().date()
        yesterday = today - timedelta(days=1)
        
        # Get today's sales
        today_orders = db.session.query(
            func.count(CustomerOrder.id).label('order_count'),
            func.sum(CustomerOrder.total_price).label('total_revenue')
        ).filter(
            func.date(CustomerOrder.order_date) == today
        ).first()
        
        # Get yesterday's sales for comparison
        yesterday_orders = db.session.query(
            func.count(CustomerOrder.id).label('order_count'),
            func.sum(CustomerOrder.total_price).label('total_revenue')
        ).filter(
            func.date(CustomerOrder.order_date) == yesterday
        ).first()
        
        # Calculate metrics
        today_revenue = float(today_orders.total_revenue or 0)
        today_count = int(today_orders.order_count or 0)
        today_avg = today_revenue / today_count if today_count > 0 else 0
        
        yesterday_revenue = float(yesterday_orders.total_revenue or 0)
        yesterday_count = int(yesterday_orders.order_count or 0)
        yesterday_avg = yesterday_revenue / yesterday_count if yesterday_count > 0 else 0
        
        # Calculate changes
        revenue_change = ((today_revenue - yesterday_revenue) / yesterday_revenue * 100) if yesterday_revenue > 0 else 0
        orders_change = ((today_count - yesterday_count) / yesterday_count * 100) if yesterday_count > 0 else 0
        avg_change = ((today_avg - yesterday_avg) / yesterday_avg * 100) if yesterday_avg > 0 else 0
        
        sales_data = {
            'today': {
                'revenue': f"{today_revenue:.2f}",
                'orders': today_count,
                'avgOrder': f"{today_avg:.2f}"
            },
            'change': {
                'revenue': f"{'+' if revenue_change >= 0 else ''}{revenue_change:.1f}%",
                'orders': f"{'+' if orders_change >= 0 else ''}{orders_change:.1f}%",
                'avgOrder': f"{'+' if avg_change >= 0 else ''}{avg_change:.1f}%"
            }
        }
        
        return jsonify(sales_data), 200
        
    except Exception as e:
        logging.error(f"Error fetching daily sales: {str(e)}")
        return jsonify({'error': str(e)}), 500

@dashboard_bp.route('/price-analytics', methods=['GET'])
@cross_origin(origins="*")
def get_price_analytics():
    """Get price analytics data"""
    try:
        # Calculate average item price from menu items
        avg_price_result = db.session.query(
            func.avg(MenuItem.menu_price).label('avg_price')
        ).filter(
            MenuItem.menu_price.isnot(None),
            MenuItem.menu_price > 0
        ).first()
        
        avg_item_price = float(avg_price_result.avg_price or 0)
        
        # Calculate average revenue per order from recent orders
        avg_revenue_result = db.session.query(
            func.avg(CustomerOrder.total_price).label('avg_revenue')
        ).filter(
            CustomerOrder.order_date >= datetime.now() - timedelta(days=30)
        ).first()
        
        revenue_per_order = float(avg_revenue_result.avg_revenue or 0)
        
        # Get price trends for popular items
        popular_items = db.session.query(
            MenuItem.menu_item_name,
            MenuItem.menu_price,
            func.count(CustomerOrder.id).label('order_count')
        ).join(
            CustomerOrder, MenuItem.id == CustomerOrder.menu_item_id
        ).filter(
            MenuItem.menu_price.isnot(None),
            MenuItem.menu_price > 0
        ).group_by(
            MenuItem.id, MenuItem.menu_item_name, MenuItem.menu_price
        ).order_by(
            func.count(CustomerOrder.id).desc()
        ).limit(4).all()
        
        # Create price trends (simulated previous prices for demo)
        trends = []
        for item in popular_items:
            current_price = float(item.menu_price)
            # Simulate previous price (±10% variation)
            import random
            variation = random.uniform(-0.1, 0.1)
            previous_price = current_price * (1 - variation)
            change_percent = ((current_price - previous_price) / previous_price) * 100
            
            trends.append({
                'item': item.menu_item_name,
                'currentPrice': f"{current_price:.2f}",
                'previousPrice': f"{previous_price:.2f}",
                'change': f"{'+' if change_percent >= 0 else ''}{change_percent:.1f}%"
            })
        
        price_data = {
            'avgItemPrice': f"{avg_item_price:.2f}",
            'revenuePerOrder': f"{revenue_per_order:.2f}",
            'trends': trends
        }
        
        return jsonify(price_data), 200
        
    except Exception as e:
        logging.error(f"Error fetching price analytics: {str(e)}")
        return jsonify({'error': str(e)}), 500

@dashboard_bp.route('/stock-alerts-count', methods=['GET'])
@cross_origin(origins="*")
def get_stock_alerts_count():
    """Get total count of active stock alerts for dashboard display"""
    try:
        # Count all active stock alerts
        total_alerts = StockAlert.query.count()
        
        # Count by alert type for detailed breakdown
        low_stock_count = StockAlert.query.filter_by(alert_type='low_stock').count()
        predicted_stockout_count = StockAlert.query.filter_by(alert_type='predicted_stockout').count()
        combined_count = StockAlert.query.filter_by(alert_type='low_stock_and_predicted_stockout').count()
        
        alerts_data = {
            'total_alerts': total_alerts,
            'breakdown': {
                'low_stock': low_stock_count,
                'predicted_stockout': predicted_stockout_count,
                'combined': combined_count
            }
        }
        
        return jsonify(alerts_data), 200
        
    except Exception as e:
        logging.error(f"Error fetching stock alerts count: {str(e)}")
        return jsonify({'error': str(e)}), 500