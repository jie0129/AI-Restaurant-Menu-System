from flask import Blueprint, jsonify, request
from models.menu_item import MenuItem, db
from models.menu_item_image import MenuItemImage
from services.recommendation import get_recommendations as get_pricing_recommendations
from utils.image_handler import ImageHandler
import logging
import os
import google.generativeai as genai
from models.recipe import Recipe
from models.ingredient import Ingredient

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize image handler
image_handler = ImageHandler()

menu_bp = Blueprint('menu', __name__)

@menu_bp.route('/recommendations', methods=['GET'])
def menu_recommendations():
    recommendations = get_menu_recommendations()
    return jsonify(recommendations), 200

@menu_bp.route('/items', methods=['GET'])
def get_menu_items():
    try:
        items = MenuItem.query.all()
        items_data = []

        for item in items:
            item_dict = item.to_dict()
            # Add images information
            if item.images:
                item_dict['images'] = [img.to_dict() for img in item.images]
                item_dict['primary_image'] = next((img.to_dict() for img in item.images if img.is_primary), None)
            else:
                item_dict['images'] = []
                item_dict['primary_image'] = None
            items_data.append(item_dict)

        return jsonify({
            'success': True,
            'data': items_data
        }), 200
    except Exception as e:
        logger.error(f"Error getting menu items: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to get menu items'
        }), 500

@menu_bp.route('/items', methods=['POST'])
def add_menu_item():
    try:
        data = request.get_json()

        # Validate required fields (removed menu_item_id as it's auto-generated)
        required_fields = ['menu_item_name', 'typical_ingredient_cost',
                          'category', 'cuisine_type', 'key_ingredients_tags']

        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }), 400

        # Check if menu item with the same name already exists
        existing_item = MenuItem.query.filter_by(menu_item_name=data['menu_item_name']).first()
        if existing_item:
            return jsonify({
                'success': False,
                'error': f'Menu item with name "{data["menu_item_name"]}" already exists'
            }), 409

        # Create new menu item (ID will be auto-generated)
        new_item = MenuItem(
            menu_item_name=data['menu_item_name'],
            typical_ingredient_cost=float(data['typical_ingredient_cost']),
            category=data['category'],
            cuisine_type=data['cuisine_type'],
            key_ingredients_tags=data['key_ingredients_tags']
        )

        db.session.add(new_item)
        db.session.flush()  # Flush to get the ID without committing

        # Handle image if provided
        if 'menu_image_path' in data and data['menu_image_path']:
            image_data = data['menu_image_path']

            # Check if it's base64 data (AI-generated image)
            if image_handler.is_base64_image(image_data):
                try:
                    # Save base64 image to file
                    file_path = image_handler.save_base64_image(
                        image_data,
                        new_item.id,
                        'ai_generated'
                    )
                    image_type = 'ai_generated'
                    image_path = file_path
                except Exception as e:
                    logger.error(f"Error saving AI-generated image: {str(e)}")
                    # Continue without image if saving fails
                    image_path = None
                    image_type = None
            else:
                # Regular file path for uploaded images
                image_type = 'uploaded'
                image_path = image_data

            # Create image record if we have a valid path
            if image_path:
                new_image = MenuItemImage(
                    menu_item_id=new_item.id,
                    image_path=image_path,
                    image_type=image_type,
                    is_primary=True
                )
                db.session.add(new_image)

        db.session.commit()

        # Get the complete item data with images
        item_dict = new_item.to_dict()
        if new_item.images:
            item_dict['images'] = [img.to_dict() for img in new_item.images]
            item_dict['primary_image'] = next((img.to_dict() for img in new_item.images if img.is_primary), None)

        return jsonify({
            'success': True,
            'message': 'Menu item added successfully',
            'data': item_dict
        }), 201

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error adding menu item: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Failed to add menu item: {str(e)}'
        }), 500

@menu_bp.route('/items/<int:item_id>', methods=['PUT'])
def update_menu_item(item_id):
    try:
        item = MenuItem.query.get(item_id)
        if not item:
            return jsonify({
                'success': False,
                'error': f'Menu item with ID {item_id} not found'
            }), 404

        data = request.get_json()

        # Update fields if provided
        if 'menu_item_name' in data:
            item.menu_item_name = data['menu_item_name']
        if 'typical_ingredient_cost' in data:
            item.typical_ingredient_cost = float(data['typical_ingredient_cost'])
        if 'category' in data:
            item.category = data['category']
        if 'cuisine_type' in data:
            item.cuisine_type = data['cuisine_type']
        if 'key_ingredients_tags' in data:
            item.key_ingredients_tags = data['key_ingredients_tags']
        if 'menu_price' in data:
            item.menu_price = float(data['menu_price']) if data['menu_price'] is not None else None


        # Handle image update if provided
        if 'menu_image_path' in data and data['menu_image_path']:
            image_data = data['menu_image_path']

            # Remove existing primary image and its file
            existing_primary = MenuItemImage.query.filter_by(menu_item_id=item.id, is_primary=True).first()
            if existing_primary:
                # Delete the old image file if it's AI-generated
                if existing_primary.image_type == 'ai_generated':
                    image_handler.delete_image(existing_primary.image_path)
                db.session.delete(existing_primary)

            # Check if it's base64 data (AI-generated image)
            if image_handler.is_base64_image(image_data):
                try:
                    # Save base64 image to file
                    file_path = image_handler.save_base64_image(
                        image_data,
                        item.id,
                        'ai_generated'
                    )
                    image_type = 'ai_generated'
                    image_path = file_path
                except Exception as e:
                    logger.error(f"Error saving AI-generated image: {str(e)}")
                    # Continue without image if saving fails
                    image_path = None
                    image_type = None
            else:
                # Regular file path for uploaded images
                image_type = 'uploaded'
                image_path = image_data

            # Create image record if we have a valid path
            if image_path:
                new_image = MenuItemImage(
                    menu_item_id=item.id,
                    image_path=image_path,
                    image_type=image_type,
                    is_primary=True
                )
                db.session.add(new_image)

        db.session.commit()

        # Get the complete item data with images
        item_dict = item.to_dict()
        if item.images:
            item_dict['images'] = [img.to_dict() for img in item.images]
            item_dict['primary_image'] = next((img.to_dict() for img in item.images if img.is_primary), None)
        else:
            item_dict['images'] = []
            item_dict['primary_image'] = None

        return jsonify({
            'success': True,
            'message': 'Menu item updated successfully',
            'data': item_dict
        }), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating menu item: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Failed to update menu item: {str(e)}'
        }), 500

@menu_bp.route('/items/<int:item_id>', methods=['DELETE'])
def delete_menu_item(item_id):
    try:
        from models.customer_order import CustomerOrder
        
        item = MenuItem.query.get(item_id)
        if not item:
            return jsonify({
                'success': False,
                'error': f'Menu item with ID {item_id} not found'
            }), 404

        # Check if there are any customer orders associated with this menu item
        associated_orders = CustomerOrder.query.filter_by(menu_item_id=item_id).count()
        if associated_orders > 0:
            return jsonify({
                'success': False,
                'error': f'Cannot delete menu item. It has {associated_orders} associated customer orders. Please handle these orders first.'
            }), 400

        # Check if there are any recipes associated with this menu item
        associated_recipes = Recipe.query.filter_by(dish_id=item_id).all()
        if associated_recipes:
            # Delete associated recipes first
            for recipe in associated_recipes:
                db.session.delete(recipe)
            logger.info(f"Deleted {len(associated_recipes)} associated recipes for menu item {item_id}")

        # Delete associated image files before deleting the item
        for image in item.images:
            if image.image_type == 'ai_generated':
                image_handler.delete_image(image.image_path)

        db.session.delete(item)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': f'Menu item with ID {item_id} deleted successfully'
        }), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting menu item: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Failed to delete menu item: {str(e)}'
        }), 500

@menu_bp.route('/generate-image', methods=['POST'])
def generate_ai_image():
    """Generate AI image for menu item using Gemini API"""
    try:
        data = request.get_json()
        menu_item_name = data.get('menu_item_name')
        key_ingredients_tags = data.get('key_ingredients_tags', '')

        if not menu_item_name:
            return jsonify({
                'success': False,
                'error': 'Menu item name is required'
            }), 400

        # Configure Gemini API
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            return jsonify({
                'success': False,
                'error': 'Gemini API key not configured'
            }), 500

        genai.configure(api_key=api_key)

        # Create the model
        model = genai.GenerativeModel(
            model_name='gemini-2.0-flash-preview-image-generation',
            generation_config={
                'response_modalities': ['TEXT', 'IMAGE']
            }
        )

        # Generate image with enhanced prompt including key ingredients
        if key_ingredients_tags:
            prompt = f"Generate a high-quality, appetizing food image of {menu_item_name} featuring key ingredients: {key_ingredients_tags}. The image should be professional, well-lit, and suitable for a restaurant menu. Make sure the key ingredients are visible and prominent in the dish."
        else:
            prompt = f"Generate a high-quality, appetizing food image of {menu_item_name}. The image should be professional, well-lit, and suitable for a restaurant menu."

        response = model.generate_content(prompt)

        # Process response to extract image
        if response.candidates and len(response.candidates) > 0:
            candidate = response.candidates[0]
            if candidate.content and candidate.content.parts:
                for part in candidate.content.parts:
                    if hasattr(part, 'inline_data') and part.inline_data:
                        # Convert image data to base64
                        import base64
                        image_data = part.inline_data.data
                        mime_type = part.inline_data.mime_type

                        # Create data URL
                        base64_image = base64.b64encode(image_data).decode('utf-8')
                        data_url = f"data:{mime_type};base64,{base64_image}"

                        return jsonify({
                            'success': True,
                            'image_data': data_url,
                            'message': f'AI image generated successfully for {menu_item_name}'
                        }), 200

        return jsonify({
            'success': False,
            'error': 'Failed to generate image from AI response'
        }), 500

    except Exception as e:
        logger.error(f"Error generating AI image: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Failed to generate AI image: {str(e)}'
        }), 500

@menu_bp.route('/recipes/<int:dish_id>', methods=['GET'])
def get_recipes_for_dish(dish_id):
    recipes = Recipe.query.filter_by(dish_id=dish_id).all()
    return jsonify({'success': True, 'data': [r.to_dict() for r in recipes]})

@menu_bp.route('/recipes', methods=['POST'])
def save_recipes():
    data = request.get_json()
    dish_id = data.get('dish_id')
    recipe_list = data.get('recipe', [])  # [{ingredient_id, quantity_per_unit, recipe_unit}]
    if not dish_id or not recipe_list:
        return jsonify({'success': False, 'error': 'dish_id and recipe are required'}), 400

    # 删除旧配方
    Recipe.query.filter_by(dish_id=dish_id).delete()
    # 新增新配方
    for r in recipe_list:
        recipe = Recipe(
            dish_id=dish_id, 
            ingredient_id=r['ingredient_id'], 
            quantity_per_unit=r['quantity_per_unit'],
            recipe_unit=r.get('recipe_unit')
        )
        db.session.add(recipe)
    db.session.flush()

    # 自动生成key_ingredients_tags
    ingredient_ids = [r['ingredient_id'] for r in recipe_list]
    ingredients = Ingredient.query.filter(Ingredient.id.in_(ingredient_ids)).all()
    tags = ', '.join([i.name for i in ingredients])
    menu_item = MenuItem.query.get(dish_id)
    if menu_item:
        menu_item.key_ingredients_tags = tags
    db.session.commit()
    return jsonify({'success': True, 'message': 'Recipe saved and tags updated.'})

@menu_bp.route('/ingredients', methods=['GET'])
def get_ingredients():
    ingredients = Ingredient.query.all()
    return jsonify({'success': True, 'data': [
        {
            'id': ing.id,
            'name': ing.name,
            'unit': ing.unit,
            'stock_unit': ing.unit,  # Add stock_unit field for frontend compatibility
            'category': ing.category,
            'min_threshold': ing.min_threshold
        } for ing in ingredients
    ]})

def get_menu_recommendations():
    # This is a placeholder function that would be implemented with actual recommendation logic
    return [
        {
            "item": "Chicken Curry",
            "reason": "High profit margin and customer demand",
            "confidence": 0.85
        },
        {
            "item": "Vegetable Stir Fry",
            "reason": "Low ingredient cost and trending",
            "confidence": 0.78
        }
    ]
