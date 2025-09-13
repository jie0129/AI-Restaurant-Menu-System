from flask import Blueprint, request, jsonify
import logging
from datetime import datetime
from typing import Dict, Any, Optional

# Import AutoGen AI Agent services
from services.autogen_ai_agent import autogen_ai
from services.demand_forecasting_service import AdvancedDemandForecaster

logger = logging.getLogger(__name__)

# Create Blueprint for AI Agent routes
ai_agent_bp = Blueprint('ai_agent', __name__, url_prefix='/api/ai-agent')

# Use AutoGen AI Agent instance
ai_agent = autogen_ai

@ai_agent_bp.route('/forecast-demand', methods=['POST'])
def forecast_demand():
    """
    API endpoint for demand forecasting using AI Agent
    
    Expected JSON payload:
    {
        "dish_data": {
            "name": "Dish Name",
            "category": "main_course",
            "price": 18.99,
            "ingredients": ["ingredient1", "ingredient2"],
            "description": "Dish description",
            "cuisine_type": "Italian"
        },
        "historical_data": [...],  // Optional
        "forecast_period": "weekly"  // Optional, defaults to 'weekly'
    }
    """
    try:
        # Get request data
        data = request.get_json()
        
        if not data:
            return jsonify({
                'status': 'error',
                'message': 'No JSON data provided'
            }), 400
        
        # Validate required fields
        dish_data = data.get('dish_data')
        if not dish_data:
            return jsonify({
                'status': 'error',
                'message': 'dish_data is required'
            }), 400
        
        # Validate dish_data structure
        required_fields = ['name', 'category', 'price']
        missing_fields = [field for field in required_fields if field not in dish_data]
        if missing_fields:
            return jsonify({
                'status': 'error',
                'message': f'Missing required fields in dish_data: {", ".join(missing_fields)}'
            }), 400
        
        # Get optional parameters
        historical_data = data.get('historical_data')
        forecast_period = data.get('forecast_period', 'weekly')
        
        logger.info(f"Processing demand forecast request for: {dish_data.get('name')}")
        
        # Call AI Agent forecast method
        forecast_result = ai_agent.forecast_demand(
            dish_data=dish_data,
            historical_data=historical_data,
            forecast_period=forecast_period
        )
        
        # Add metadata
        forecast_result['metadata'] = {
            'request_timestamp': datetime.now().isoformat(),
            'ai_agent_version': '1.0',
            'forecast_method': 'advanced_ensemble'
        }
        
        logger.info(f"Demand forecast completed successfully for: {dish_data.get('name')}")
        return jsonify(forecast_result), 200
        
    except ValueError as e:
        logger.error(f"Validation error in demand forecasting: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Validation error: {str(e)}'
        }), 400
        
    except Exception as e:
        logger.error(f"Error in demand forecasting endpoint: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Internal server error during demand forecasting',
            'error_details': str(e)
        }), 500

@ai_agent_bp.route('/create-dish', methods=['POST'])
def create_innovative_dish():
    """
    API endpoint for creating innovative dishes using AI Agent
    
    Expected JSON payload:
    {
        "available_ingredients": ["ingredient1", "ingredient2"],
        "dietary_preferences": ["vegetarian", "gluten_free"],  // Optional
        "cuisine_style": "Italian",  // Optional
        "target_price_range": [15.0, 25.0],  // Optional
        "creativity_level": 0.8  // Optional, 0.0-1.0
    }
    """
    try:
        # Get request data
        data = request.get_json()
        
        if not data:
            return jsonify({
                'status': 'error',
                'message': 'No JSON data provided'
            }), 400
        
        # Validate required fields
        available_ingredients = data.get('available_ingredients')
        if not available_ingredients or not isinstance(available_ingredients, list):
            return jsonify({
                'status': 'error',
                'message': 'available_ingredients must be a non-empty list'
            }), 400
        
        # Get optional parameters
        dietary_preferences = data.get('dietary_preferences')
        cuisine_style = data.get('cuisine_style')
        target_price_range = data.get('target_price_range')
        creativity_level = data.get('creativity_level')
        
        # Convert target_price_range to tuple if provided
        if target_price_range and isinstance(target_price_range, list) and len(target_price_range) == 2:
            target_price_range = tuple(target_price_range)
        
        logger.info(f"Processing dish creation request with {len(available_ingredients)} ingredients")
        
        # Call AutoGen AI Agent workflow
        workflow_results = ai_agent.automate_full_workflow(
            ingredients=available_ingredients,
            auto_apply=False
        )
        
        # Extract dish suggestion from workflow results
        dish_suggestion = None
        if 'results' in workflow_results and 'results' in workflow_results['results']:
            for step_name, step_data in workflow_results['results']['results'].items():
                if 'dish_name' in step_data:
                    # Import DishSuggestion class for proper object creation
                    from services.autogen_ai_agent import DishSuggestion, autogen_ai
                    dish_suggestion = DishSuggestion(
                        name=step_data.get('dish_name', 'AutoGen Generated Dish'),
                        description=step_data.get('description', 'An innovative fusion dish'),
                        category=autogen_ai._determine_dish_category(available_ingredients, step_data.get('dish_name')),
                        cuisine_type=cuisine_style or 'Fusion',
                        ingredients=available_ingredients,
                        estimated_cost=12.0,
                        suggested_price=target_price_range[1] if target_price_range else 22.0,
                        predicted_demand=30.0,
                        nutrition_score=0.8,
                        creativity_score=creativity_level or 0.8,
                        feasibility_score=0.8,
                        overall_score=0.82
                    )
                    break
        
        # Fallback if no dish found in results
        if not dish_suggestion:
            from services.autogen_ai_agent import DishSuggestion, autogen_ai
            main_ingredient = available_ingredients[0] if available_ingredients else 'Mixed Ingredients'
            dish_name = f'AutoGen {main_ingredient.title()} Creation'
            dish_suggestion = DishSuggestion(
                name=dish_name,
                description=f'An innovative dish featuring {', '.join(available_ingredients[:3])}',
                category=autogen_ai._determine_dish_category(available_ingredients, dish_name),
                cuisine_type=cuisine_style or 'Fusion',
                ingredients=available_ingredients,
                estimated_cost=12.0,
                suggested_price=target_price_range[1] if target_price_range else 22.0,
                predicted_demand=30.0,
                nutrition_score=0.8,
                creativity_score=creativity_level or 0.8,
                feasibility_score=0.8,
                overall_score=0.82
            )
        
        # Convert DishSuggestion to dict for JSON response
        dish_dict = {
            'name': dish_suggestion.name,
            'description': dish_suggestion.description,
            'category': dish_suggestion.category,
            'cuisine_type': dish_suggestion.cuisine_type,
            'ingredients': dish_suggestion.ingredients,
            'estimated_cost': dish_suggestion.estimated_cost,
            'suggested_price': dish_suggestion.suggested_price,
            'predicted_demand': dish_suggestion.predicted_demand,
            'nutrition_score': dish_suggestion.nutrition_score,
            'creativity_score': dish_suggestion.creativity_score,
            'feasibility_score': dish_suggestion.feasibility_score,
            'overall_score': dish_suggestion.overall_score,
            'recipe_instructions': dish_suggestion.recipe_instructions,
            'nutrition_data': dish_suggestion.nutrition_data,
            'market_analysis': dish_suggestion.market_analysis
        }
        
        response = {
            'status': 'success',
            'dish_suggestion': dish_dict,
            'metadata': {
                'request_timestamp': datetime.now().isoformat(),
                'ai_agent_version': '1.0',
                'creation_method': 'innovative_ai_generation'
            }
        }
        
        logger.info(f"Dish creation completed successfully: {dish_suggestion.name}")
        return jsonify(response), 200
        
    except ValueError as e:
        logger.error(f"Validation error in dish creation: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Validation error: {str(e)}'
        }), 400
        
    except Exception as e:
        logger.error(f"Error in dish creation endpoint: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Internal server error during dish creation',
            'error_details': str(e)
        }), 500

@ai_agent_bp.route('/automate-workflow', methods=['POST'])
def automate_workflow():
    """
    API endpoint for automating full workflow using AutoGen AI Agent
    
    Expected JSON payload:
    {
        "ingredients": ["ingredient1", "ingredient2", "ingredient3"],
        "auto_apply": false  // Optional, defaults to false
    }
    """
    try:
        # Get request data
        data = request.get_json()
        
        if not data:
            return jsonify({
                'status': 'error',
                'message': 'No JSON data provided'
            }), 400
        
        # Validate required fields
        ingredients = data.get('ingredients')
        if not ingredients:
            return jsonify({
                'status': 'error',
                'message': 'ingredients list is required'
            }), 400
        
        # Validate ingredients structure
        if not isinstance(ingredients, list) or len(ingredients) == 0:
            return jsonify({
                'status': 'error',
                'message': 'ingredients must be a non-empty list'
            }), 400
        
        # Get optional parameters
        auto_apply = data.get('auto_apply', False)
        dish_name = data.get('dish_name')  # Optional dish name parameter
        category = data.get('category')  # Optional category parameter
        
        print(f"DEBUG: Received data: {data}")
        print(f"DEBUG: Extracted category: {category}")
        
        logger.info(f"Processing AutoGen workflow automation request for ingredients: {', '.join(ingredients)}")
        if dish_name:
            logger.info(f"Custom dish name provided: '{dish_name}'")
            print(f"DEBUG: Dish name: '{dish_name}'")
        if category:
            logger.info(f"Predefined category provided: '{category}'")
            print(f"DEBUG: Category parameter found: '{category}'")
        else:
            print("DEBUG: No category parameter provided")
        
        # Call AutoGen AI Agent workflow automation method
        workflow_result = ai_agent.automate_full_workflow(
            ingredients=ingredients,
            auto_apply=auto_apply,
            dish_name=dish_name,
            category=category
        )
        
        # Add metadata
        workflow_result['metadata'] = {
            'request_timestamp': datetime.now().isoformat(),
            'ai_agent_version': '2.0_autogen',
            'workflow_method': 'autogen_full_automation',
            'auto_apply_enabled': auto_apply,
            'ingredients_count': len(ingredients)
        }
        
        logger.info(f"AutoGen workflow automation completed successfully for ingredients: {', '.join(ingredients)}")
        return jsonify(workflow_result), 200
        
    except ValueError as e:
        logger.error(f"Validation error in workflow automation: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Validation error: {str(e)}'
        }), 400
        
    except Exception as e:
        logger.error(f"Error in workflow automation endpoint: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Internal server error during workflow automation',
            'error_details': str(e)
        }), 500

@ai_agent_bp.route('/optimize-pricing', methods=['POST'])
def optimize_pricing():
    """
    Optimize menu pricing using AI analysis
    """
    try:
        data = request.get_json() or {}
        strategy = data.get('strategy', 'profit_maximization')
        item_filters = data.get('filters', {})
        
        # Use AI Agent for pricing optimization
        result = ai_agent.optimize_pricing(
            strategy=strategy,
            item_filters=item_filters
        )
        
        if result.get('success'):
            return jsonify({
                'success': True,
                'message': result['message'],
                'data': {
                    'strategy_used': result['strategy_used'],
                    'recommendations': result['recommendations'],
                    'summary': result['summary'],
                    'implementation_plan': result['implementation_plan'],
                    'insights': result['insights'],
                    'next_steps': result['next_steps']
                }
            })
        else:
            return jsonify({
                'success': False,
                'error': result.get('error', 'Pricing optimization failed'),
                'message': result.get('message', 'Unable to optimize pricing')
            }), 400
            
    except Exception as e:
        logger.error(f"Error in pricing optimization: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Pricing optimization failed due to technical error'
        }), 500

@ai_agent_bp.route('/pricing-insights', methods=['GET'])
def get_pricing_insights():
    """
    Get comprehensive pricing insights for the menu
    """
    try:
        result = ai_agent.get_pricing_insights()
        
        if result.get('success'):
            return jsonify({
                'success': True,
                'message': result['message'],
                'data': {
                    'menu_statistics': result['menu_statistics'],
                    'optimization_opportunities': result['optimization_opportunities'],
                    'market_positioning': result['market_positioning'],
                    'recommendations': result['recommendations'],
                    'action_items': result['action_items']
                }
            })
        else:
            return jsonify({
                'success': False,
                'error': result.get('error', 'Failed to generate insights'),
                'message': result.get('message', 'Unable to analyze pricing data')
            }), 400
            
    except Exception as e:
        logger.error(f"Error getting pricing insights: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Failed to generate pricing insights'
        }), 500

@ai_agent_bp.route('/analyze-nutrition', methods=['POST'])
def analyze_nutrition():
    """
    API endpoint for nutrition analysis using AI Agent
    
    Expected JSON payload:
    {
        "dish_data": {
            "name": "Dish Name",
            "ingredients": ["ingredient1", "ingredient2"],
            "portions": {"ingredient1": 100, "ingredient2": 50},  // Optional
            "serving_size": 1  // Optional
        }
    }
    """
    try:
        # Get request data
        data = request.get_json()
        
        if not data:
            return jsonify({
                'status': 'error',
                'message': 'No JSON data provided'
            }), 400
        
        # Validate required fields
        dish_data = data.get('dish_data')
        if not dish_data:
            return jsonify({
                'status': 'error',
                'message': 'dish_data is required'
            }), 400
        
        # Validate dish_data structure
        required_fields = ['name', 'ingredients']
        missing_fields = [field for field in required_fields if field not in dish_data]
        if missing_fields:
            return jsonify({
                'status': 'error',
                'message': f'Missing required fields in dish_data: {", ".join(missing_fields)}'
            }), 400
        
        logger.info(f"Processing nutrition analysis request for: {dish_data.get('name')}")
        
        # Call AI Agent nutrition analysis method
        nutrition_result = ai_agent.analyze_nutrition(
             dish_name=dish_data.get('name'),
             ingredients=dish_data.get('ingredients', []),
             recipe_data=dish_data.get('recipe_data', {})
         )
        
        # Add metadata
        nutrition_result['metadata'] = {
            'request_timestamp': datetime.now().isoformat(),
            'ai_agent_version': '1.0',
            'analysis_method': 'comprehensive_nutrition_analysis'
        }
        
        logger.info(f"Nutrition analysis completed successfully for: {dish_data.get('name')}")
        return jsonify(nutrition_result), 200
        
    except ValueError as e:
        logger.error(f"Validation error in nutrition analysis: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Validation error: {str(e)}'
        }), 400
        
    except Exception as e:
        logger.error(f"Error in nutrition analysis endpoint: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Internal server error during nutrition analysis',
            'error_details': str(e)
        }), 500

@ai_agent_bp.route('/gemini-chat', methods=['POST'])
def gemini_chat():
    """
    Gemini API chat endpoint for AI insights
    """
    try:
        import os
        import requests
        
        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify({
                'success': False,
                'error': 'Message is required'
            }), 400
        
        # Get API key from environment
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            return jsonify({
                'success': False,
                'error': 'Gemini API key not configured'
            }), 500
        
        # Call Gemini API (using v1 endpoint with gemini-1.5-flash model)
        gemini_url = f'https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={api_key}'
        
        payload = {
            'contents': [{
                'parts': [{
                    'text': data['message']
                }]
            }]
        }
        
        print(f"DEBUG: Making request to: {gemini_url}")
        print(f"DEBUG: Payload: {payload}")
        response = requests.post(gemini_url, json=payload, timeout=30)
        print(f"DEBUG: Response status: {response.status_code}")
        print(f"DEBUG: Response content: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            if 'candidates' in result and len(result['candidates']) > 0:
                text_response = result['candidates'][0]['content']['parts'][0]['text']
                return jsonify({
                    'success': True,
                    'response': text_response
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'No response from Gemini API'
                })
        else:
            return jsonify({
                'success': False,
                'error': f'Gemini API error: {response.status_code}'
            })
            
    except Exception as e:
        logger.error(f"Gemini chat error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@ai_agent_bp.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint for AI Agent service
    """
    try:
        return jsonify({
            'status': 'healthy',
            'service': 'AI Agent',
            'version': '1.0',
            'timestamp': datetime.now().isoformat(),
            'capabilities': [
                'demand_forecasting',
                'dish_creation',
                'workflow_automation',
                'nutrition_analysis',
                'pricing_optimization',
                'gemini_chat'
            ]
        }), 200
        
    except Exception as e:
        logger.error(f"Error in health check: {str(e)}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500

# Error handlers
@ai_agent_bp.errorhandler(404)
def not_found(error):
    return jsonify({
        'status': 'error',
        'message': 'AI Agent endpoint not found'
    }), 404

@ai_agent_bp.errorhandler(405)
def method_not_allowed(error):
    return jsonify({
        'status': 'error',
        'message': 'Method not allowed for this AI Agent endpoint'
    }), 405

@ai_agent_bp.errorhandler(500)
def internal_error(error):
    return jsonify({
        'status': 'error',
        'message': 'Internal server error in AI Agent service'
    }), 500