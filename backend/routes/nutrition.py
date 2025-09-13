from flask import Blueprint, jsonify, request
from models.menu_nutrition import MenuNutrition, db
from models.menu_item import MenuItem
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

nutrition_bp = Blueprint('nutrition', __name__)

@nutrition_bp.route('/menu-nutrition', methods=['GET'])
def get_all_nutrition():
    """Get nutrition information for all menu items"""
    try:
        nutrition_data = MenuNutrition.query.all()
        return jsonify({
            'success': True,
            'data': [item.to_dict() for item in nutrition_data]
        }), 200
    except Exception as e:
        logger.error(f"Error getting nutrition data: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to get nutrition data'
        }), 500

@nutrition_bp.route('/menu-nutrition/<int:menu_item_id>', methods=['GET'])
def get_nutrition_by_menu_item(menu_item_id):
    """Get nutrition information for a specific menu item"""
    try:
        nutrition = MenuNutrition.query.filter_by(menu_item_id=menu_item_id).first()
        
        if not nutrition:
            return jsonify({
                'success': False,
                'error': f'No nutrition information found for menu item ID {menu_item_id}'
            }), 404
            
        return jsonify({
            'success': True,
            'data': nutrition.to_dict()
        }), 200
    except Exception as e:
        logger.error(f"Error getting nutrition data: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to get nutrition data'
        }), 500

@nutrition_bp.route('/menu-nutrition', methods=['POST'])
def save_nutrition_info():
    """Save or update nutrition information for a menu item"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if 'menu_item_id' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing required field: menu_item_id'
            }), 400
            
        # Check if menu item exists
        menu_item = MenuItem.query.get(data['menu_item_id'])
        if not menu_item:
            return jsonify({
                'success': False,
                'error': f'Menu item with ID {data["menu_item_id"]} not found'
            }), 404
            
        # Check if nutrition info already exists for this menu item
        existing_nutrition = MenuNutrition.query.filter_by(menu_item_id=data['menu_item_id']).first()
        
        if existing_nutrition:
            # Update existing record
            if 'calories' in data:
                existing_nutrition.calories = data['calories']
            if 'protein' in data:
                existing_nutrition.protein = data['protein']
            if 'carbohydrates' in data:
                existing_nutrition.carbohydrates = data['carbohydrates']
            if 'fat' in data:
                existing_nutrition.fat = data['fat']
            if 'fiber' in data:
                existing_nutrition.fiber = data['fiber']
            if 'sugar' in data:
                existing_nutrition.sugar = data['sugar']
            if 'sodium' in data:
                existing_nutrition.sodium = data['sodium']
            if 'allergens' in data:
                existing_nutrition.allergens = data['allergens']
            if 'is_vegetarian' in data:
                existing_nutrition.is_vegetarian = data['is_vegetarian']
            if 'is_vegan' in data:
                existing_nutrition.is_vegan = data['is_vegan']
            if 'is_gluten_free' in data:
                existing_nutrition.is_gluten_free = data['is_gluten_free']
            if 'analysis_text' in data:
                existing_nutrition.analysis_text = data['analysis_text']
            if 'vitamins' in data:
                existing_nutrition.vitamins = data['vitamins']
            if 'minerals' in data:
                existing_nutrition.minerals = data['minerals']
                
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Nutrition information updated successfully',
                'data': existing_nutrition.to_dict()
            }), 200
        else:
            # Create new record
            new_nutrition = MenuNutrition(
                menu_item_id=data['menu_item_id'],
                calories=data.get('calories'),
                protein=data.get('protein'),
                carbohydrates=data.get('carbohydrates'),
                fat=data.get('fat'),
                fiber=data.get('fiber'),
                sugar=data.get('sugar'),
                sodium=data.get('sodium'),
                allergens=data.get('allergens'),
                is_vegetarian=data.get('is_vegetarian', False),
                is_vegan=data.get('is_vegan', False),
                is_gluten_free=data.get('is_gluten_free', False),
                analysis_text=data.get('analysis_text'),
                vitamins=data.get('vitamins'),
                minerals=data.get('minerals')
            )
            
            db.session.add(new_nutrition)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Nutrition information saved successfully',
                'data': new_nutrition.to_dict()
            }), 201
            
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error saving nutrition data: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Failed to save nutrition data: {str(e)}'
        }), 500

@nutrition_bp.route('/menu-nutrition/<int:nutrition_id>', methods=['DELETE'])
def delete_nutrition(nutrition_id):
    """Delete nutrition information"""
    try:
        nutrition = MenuNutrition.query.get(nutrition_id)
        
        if not nutrition:
            return jsonify({
                'success': False,
                'error': f'Nutrition information with ID {nutrition_id} not found'
            }), 404
            
        db.session.delete(nutrition)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Nutrition information with ID {nutrition_id} deleted successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting nutrition data: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Failed to delete nutrition data: {str(e)}'
        }), 500
