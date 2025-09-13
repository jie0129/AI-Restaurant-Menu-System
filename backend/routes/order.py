from flask import Blueprint, request, jsonify
from models import db
from models.recipe import Recipe
from models.inventory_item import InventoryItem
from models.ingredient_usage import IngredientUsage
from models.menu_item import MenuItem
from models.ingredient import Ingredient
from models.customer_order import CustomerOrder
from datetime import datetime, timezone
from flask_cors import cross_origin
import uuid
import sys
import logging

# Unit conversion mappings for recipe units to inventory units
RECIPE_UNIT_CONVERSIONS = {
    # Weight conversions to kg (inventory unit)
    'g': 0.001,
    'gram': 0.001,
    'mg': 0.000001,
    'kg': 1,
    
    # Volume conversions to L (inventory unit)
    'ml': 0.001,
    'L': 1,
    'l': 1,
    'tsp': 0.00493,
    'tbsp': 0.01479,
    'cup': 0.237,
    
    # Count conversions (no conversion needed)
    'piece': 1,
    'pcs': 1,
    'slice': 1,
    'leaf': 1,
}

def convert_recipe_to_inventory_unit(recipe_quantity, recipe_unit, ingredient):
    """
    Convert recipe quantity to inventory unit using the recipe unit and conversion table.
    """
    logging.info(f"CONVERSION DEBUG: Input - quantity: {recipe_quantity}, recipe_unit: {recipe_unit}, inventory_unit: {ingredient.unit if ingredient else 'None'}")
    
    if not ingredient or not recipe_unit:
        logging.info(f"CONVERSION DEBUG: Early return - ingredient: {ingredient}, recipe_unit: {recipe_unit}")
        return recipe_quantity
    
    recipe_unit_lower = recipe_unit.lower()
    inventory_unit_lower = ingredient.unit.lower()
    
    # If units are the same, no conversion needed
    if recipe_unit_lower == inventory_unit_lower:
        logging.info(f"CONVERSION DEBUG: Same units, no conversion needed")
        return recipe_quantity
    
    # Get conversion factor from recipe unit to base unit (kg for weight, L for volume)
    recipe_to_base = RECIPE_UNIT_CONVERSIONS.get(recipe_unit_lower, 1.0)
    inventory_to_base = RECIPE_UNIT_CONVERSIONS.get(inventory_unit_lower, 1.0)
    
    logging.info(f"CONVERSION DEBUG: recipe_to_base: {recipe_to_base}, inventory_to_base: {inventory_to_base}")
    
    # Convert recipe quantity to base unit, then to inventory unit
    base_quantity = recipe_quantity * recipe_to_base
    converted_quantity = base_quantity / inventory_to_base
    
    logging.info(f"CONVERSION DEBUG: base_quantity: {base_quantity}, converted_quantity: {converted_quantity}")
    
    return converted_quantity

order_bp = Blueprint('order', __name__)

@order_bp.route('/test-debug', methods=['GET'])
@cross_origin(origins="*")
def test_debug():
    """Simple test endpoint to verify debug output works"""
    print("TEST DEBUG: This is a test debug message")
    sys.stdout.flush()
    return jsonify({'message': 'Debug test endpoint called'})

@order_bp.route('/check-availability', methods=['GET'])
@cross_origin(origins="*")
def check_menu_availability():
    """Check which menu items are available based on ingredient stock"""
    print("DEBUG: check_menu_availability function called")
    sys.stdout.flush()
    try:
        # Get all menu items
        menu_items = MenuItem.query.all()
        print(f"DEBUG: Found {len(menu_items)} menu items")
        sys.stdout.flush()
        availability_status = []
        
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
                    missing_ingredients.append({
                        'name': ingredient.name if ingredient else f'Ingredient {recipe.ingredient_id}',
                        'required': recipe.quantity_per_unit,
                        'available': 0,
                        'unit': ingredient.unit if ingredient else 'units'
                    })
                else:
                    # Convert recipe quantity to inventory unit for proper comparison
                    converted_required = convert_recipe_to_inventory_unit(
                        recipe.quantity_per_unit, 
                        recipe.recipe_unit, 
                        ingredient
                    )
                    
                    # Debug logging
                    logging.info(f"API DEBUG: {ingredient.name} - Recipe: {recipe.quantity_per_unit} {recipe.recipe_unit}, Converted: {converted_required} {ingredient.unit}, Available: {inventory.quantity} {ingredient.unit}")
                    print(f"DEBUG: {ingredient.name} - Recipe: {recipe.quantity_per_unit} {recipe.recipe_unit}, Converted: {converted_required} {ingredient.unit}, Available: {inventory.quantity} {ingredient.unit}")
                    sys.stdout.flush()
                    
                    if float(inventory.quantity) < converted_required:
                        is_available = False
                        missing_ingredients.append({
                            'name': ingredient.name,
                            'required': converted_required,
                            'available': float(inventory.quantity),
                            'unit': ingredient.unit
                        })
            
            availability_status.append({
                'menu_item_id': menu_item.id,
                'name': menu_item.menu_item_name,
                'is_available': is_available,
                'missing_ingredients': missing_ingredients
            })
        
        return jsonify({'success': True, 'data': availability_status}), 200
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@order_bp.route('/all', methods=['GET'])
@cross_origin(origins="*")
def get_all_orders():
    """Get all orders with pagination"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        status_filter = request.args.get('status')
        
        # Build query
        query = db.session.query(
            CustomerOrder.id,
            CustomerOrder.order_number,
            CustomerOrder.quantity_ordered,
            CustomerOrder.total_price,
            CustomerOrder.order_status,
            CustomerOrder.order_date,
            CustomerOrder.customer_name,
            CustomerOrder.customer_phone,
            MenuItem.menu_item_name
        ).join(
            MenuItem, CustomerOrder.menu_item_id == MenuItem.id
        )
        
        # Apply status filter if provided
        if status_filter:
            query = query.filter(CustomerOrder.order_status == status_filter)
            
        # Order by most recent first
        query = query.order_by(CustomerOrder.order_date.desc())
        
        # Paginate
        paginated_orders = query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        # Group orders by order_number
        order_groups = {}
        for order in paginated_orders.items:
            order_num = order.order_number
            if order_num not in order_groups:
                order_groups[order_num] = {
                    'id': order.id,
                    'orderNumber': order_num,
                    'tableNumber': f"Table {(order.id % 20) + 1}",
                    'items': [],
                    'total': 0,
                    'status': order.order_status,
                    'orderDate': order.order_date.strftime('%Y-%m-%d %H:%M:%S') if order.order_date else '',
                    'time': order.order_date.strftime('%H:%M') if order.order_date else '',
                    'customer': order.customer_name or 'Guest',
                    'phone': order.customer_phone or ''
                }
            
            order_groups[order_num]['items'].append({
                'name': order.menu_item_name,
                'quantity': order.quantity_ordered,
                'price': order.total_price
            })
            order_groups[order_num]['total'] += order.total_price
        
        # Convert to list
        orders_list = list(order_groups.values())
        
        return jsonify({
            'success': True,
            'data': orders_list,
            'pagination': {
                'page': paginated_orders.page,
                'pages': paginated_orders.pages,
                'per_page': paginated_orders.per_page,
                'total': paginated_orders.total,
                'has_next': paginated_orders.has_next,
                'has_prev': paginated_orders.has_prev
            }
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@order_bp.route('/', methods=['POST', 'OPTIONS'])
@cross_origin(origins="*")
def place_order():
    data = request.get_json()
    items = data.get('items', [])  # [{menu_item_id, quantity}]
    if not items:
        return jsonify({'success': False, 'message': 'No items provided'}), 400
    try:
        ingredient_usage_map = {}  # {ingredient_id: {'quantity': total, 'menu_item_id': ..., 'ingredient_name': ...}}
        order_details = []
        
        # 1. Calculate the total quantity of all raw materials used and collect order details.
        for item in items:
            menu_item_id = item['menu_item_id']
            quantity = item['quantity']
            
            # Get menu item details
            menu_item = MenuItem.query.get(menu_item_id)
            if not menu_item:
                return jsonify({'success': False, 'message': f'Menu item {menu_item_id} not found'}), 400
            
            recipes = Recipe.query.filter_by(dish_id=menu_item_id).all()
            item_ingredients = []
            
            for recipe in recipes:
                total_used = recipe.quantity_per_unit * quantity
                ingredient = Ingredient.query.get(recipe.ingredient_id)
                
                if recipe.ingredient_id not in ingredient_usage_map:
                    ingredient_usage_map[recipe.ingredient_id] = {
                        'quantity': 0, 
                        'menu_item_id': menu_item_id,
                        'ingredient_name': ingredient.name if ingredient else f'Ingredient {recipe.ingredient_id}',
                        'recipe_unit': recipe.recipe_unit
                    }
                ingredient_usage_map[recipe.ingredient_id]['quantity'] += total_used
                
                item_ingredients.append({
                    'name': ingredient.name if ingredient else f'Ingredient {recipe.ingredient_id}',
                    'quantity_used': total_used,
                    'unit': ingredient.unit if ingredient else 'units'
                })
            
            order_details.append({
                'menu_item_id': menu_item_id,
                'menu_item_name': menu_item.menu_item_name,
                'quantity': quantity,
                'price': float(menu_item.menu_price) if menu_item.menu_price else 0,
                'ingredients_used': item_ingredients
            })
        
        # 2. Check if there is enough stock for all ingredients (with unit conversion)
        for ingredient_id, usage in ingredient_usage_map.items():
            inventory = InventoryItem.query.filter_by(ingredient_id=ingredient_id).first()
            ingredient = Ingredient.query.get(ingredient_id)
            
            # Apply unit conversion for stock checking
            converted_required = convert_recipe_to_inventory_unit(usage['quantity'], usage['recipe_unit'], ingredient)
            
            if not inventory or float(inventory.quantity) < converted_required:
                return jsonify({
                    'success': False, 
                    'message': f'Ingredient "{usage["ingredient_name"]}" insufficient stock. Required: {converted_required:.4f} {ingredient.unit if ingredient else "units"}, Available: {float(inventory.quantity) if inventory else 0}'
                }), 400
        
        # 3. Create customer orders
        # Use Malaysia Time for all order processing
        import pytz
        malaysia_tz = pytz.timezone('Asia/Kuala_Lumpur')
        local_time = datetime.now(malaysia_tz)
        order_number = f"ORD-{local_time.strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
        current_time = local_time
        day_of_week = local_time.strftime('%A')
        
        # Determine meal type based on local time
        hour = local_time.hour
        if 6 <= hour < 11:
            meal_type = 'breakfast'
        elif 11 <= hour < 16:
            meal_type = 'lunch'
        elif 16 <= hour < 21:
            meal_type = 'dinner'
        else:
            meal_type = 'snack'
        
        for item in items:
            menu_item_id = item['menu_item_id']
            quantity = item['quantity']
            menu_item = MenuItem.query.get(menu_item_id)
            
            unit_price = float(menu_item.menu_price) if menu_item.menu_price else 0.0
            total_price = unit_price * quantity
            
            customer_order = CustomerOrder(
                order_number=order_number,
                menu_item_id=menu_item_id,
                quantity_ordered=quantity,
                unit_price=unit_price,
                total_price=total_price,
                order_date=current_time,
                customer_name=None,  # Allow empty as requested
                customer_phone=None,  # Allow empty as requested
                order_status='confirmed',
                day_of_week=day_of_week,
                meal_type=meal_type,
                weather_condition=None,  # Allow empty as requested
                has_promotion=False
            )
            db.session.add(customer_order)
        
        # 4. Deduct stock and record usages with unit conversion
        for ingredient_id, usage in ingredient_usage_map.items():
            inventory = InventoryItem.query.filter_by(ingredient_id=ingredient_id).first()
            ingredient = Ingredient.query.get(ingredient_id)
            
            # Apply unit conversion based on ingredient type
            converted_quantity = convert_recipe_to_inventory_unit(usage['quantity'], usage['recipe_unit'], ingredient)
            print(f"DEBUG: Converting {usage['quantity']} {usage['recipe_unit']} to {converted_quantity} {ingredient.unit} for {ingredient.name}")
            
            inventory.quantity = float(inventory.quantity) - converted_quantity
            db.session.add(IngredientUsage(
                ingredient_id=ingredient_id,
                quantity_used=converted_quantity,
                unit=ingredient.unit if ingredient else None,
                used_on=current_time,
                menu_item_id=usage['menu_item_id']
            ))
        
        db.session.commit()
        
        # Calculate total order value
        total_amount = sum(item['quantity'] * item['price'] for item in order_details)
        
        return jsonify({
            'success': True, 
            'message': 'Order placed successfully, inventory updated',
            'order_details': {
                'order_number': order_number,
                'items': order_details,
                'total_amount': total_amount,
                'order_time': local_time.isoformat(),
                'ingredients_deducted': [
                    {
                        'ingredient_name': usage['ingredient_name'],
                        'quantity_deducted': usage['quantity']
                    } for usage in ingredient_usage_map.values()
                ]
            }
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500