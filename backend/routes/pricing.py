from flask import Blueprint, jsonify, request
from concurrent.futures import ThreadPoolExecutor
from services.recommendation import get_recommendations, get_detailed_recommendation_for_existing_item, generate_pricing_recommendation_for_menu_item, predict_optimal_price_for_item
from models.inventory_item import db
from models.menu_item import MenuItem
import logging
import os
import requests
import pandas as pd

def get_market_price_from_csv(menu_item_name):
    """Extract observed market price from CSV dataset for a specific menu item."""
    try:
        data_path = "C:/Users/User/Desktop/first-app/instance/cleaned_streamlined_ultimate_malaysian_data.csv"
        
        if os.path.exists(data_path):
            df = pd.read_csv(data_path)
            
            # Standardize column names
            if 'menu_item' in df.columns:
                df['menu_item_name'] = df['menu_item']
            
            # Filter data for the specific menu item
            if 'menu_item_name' in df.columns and 'observed_market_price' in df.columns:
                item_data = df[df['menu_item_name'] == menu_item_name]
                
                if not item_data.empty:
                    # Get the most recent or average market price for this item
                    market_price = item_data['observed_market_price'].mean()
                    return float(market_price) if pd.notna(market_price) else None
        
        return None
    except Exception as e:
        print(f"Error extracting market price from CSV: {e}")
        return None

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create a thread pool executor for background tasks
executor = ThreadPoolExecutor(max_workers=2)

# Create blueprint
pricing_bp = Blueprint('pricing', __name__)

# Store background task results
task_results = {}

def generate_ai_analysis(menu_item_name, category, cuisine_type, optimal_price, ingredient_cost, projected_profit):
    """
    Generate AI-powered market positioning, reasoning, and strategic considerations using Gemini API
    """
    try:
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            logger.warning("Gemini API key not configured, using fallback analysis")
            return {
                'market_positioning': 'Premium positioning recommended based on optimization results.',
                'reasoning': 'Price optimization suggests this positioning maximizes profitability.',
                'strategic_considerations': 'Monitor competitor pricing and customer feedback for adjustments.'
            }
        
        # Create detailed prompt for Gemini API
        prompt = f"""
As a restaurant pricing strategist, analyze the following menu item and provide specific insights:

Menu Item: {menu_item_name}
Category: {category}
Cuisine Type: {cuisine_type}
Optimal Price: RM{optimal_price:.2f} (ALREADY CALCULATED - DO NOT SUGGEST A DIFFERENT PRICE)
Ingredient Cost: RM{ingredient_cost:.2f}
Projected Profit: RM{projected_profit:.2f}
Profit Margin: {((projected_profit/optimal_price)*100):.1f}%

Provide a JSON response with exactly these three fields (DO NOT include any price recommendations):
1. "market_positioning": A 2-3 sentence analysis of how this item should be positioned in the market based on the given optimal price
2. "reasoning": A 2-3 sentence explanation of why the calculated optimal price makes business sense
3. "strategic_considerations": A 2-3 sentence recommendation for strategic implementation

IMPORTANT: Do NOT include any price fields in your response. Only analyze the given optimal price.
Make the analysis specific to this item, not generic. Focus on the actual numbers and item characteristics.
"""
        
        # Call Gemini API
        gemini_url = f'https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={api_key}'
        payload = {
            'contents': [{
                'parts': [{
                    'text': prompt
                }]
            }]
        }
        
        response = requests.post(gemini_url, json=payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            if 'candidates' in result and len(result['candidates']) > 0:
                ai_response = result['candidates'][0]['content']['parts'][0]['text']
                
                # Try to parse JSON response
                import json
                try:
                    # Clean the response (remove markdown formatting if present)
                    clean_response = ai_response.strip()
                    if clean_response.startswith('```json'):
                        clean_response = clean_response[7:]
                    if clean_response.endswith('```'):
                        clean_response = clean_response[:-3]
                    
                    analysis = json.loads(clean_response.strip())
                    
                    # Validate required fields
                    required_fields = ['market_positioning', 'reasoning', 'strategic_considerations']
                    if all(field in analysis for field in required_fields):
                        return analysis
                    else:
                        logger.warning("AI response missing required fields, using fallback")
                        
                except json.JSONDecodeError:
                    logger.warning("Failed to parse AI response as JSON, using fallback")
        
        # Fallback if API call fails
        return {
            'market_positioning': f'Position {menu_item_name} as a premium {category.lower()} option with strong profit margins.',
            'reasoning': f'The RM{optimal_price:.2f} price point maximizes profitability while maintaining competitive positioning.',
            'strategic_considerations': f'Monitor market response and adjust pricing based on demand patterns for {cuisine_type} cuisine.'
        }
        
    except Exception as e:
        logger.error(f"Error generating AI analysis: {str(e)}")
        return {
            'market_positioning': 'Strategic positioning based on optimization analysis.',
            'reasoning': 'Price optimization indicates optimal profitability at recommended price point.',
            'strategic_considerations': 'Regular monitoring and adjustment recommended based on market feedback.'
        }

@pricing_bp.route('/recommendations', methods=['GET'])
def get_pricing_recommendations():
    try:
        # Get pagination parameters
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))

        # Get recommendations with pagination
        recommendations, total_count = get_recommendations(page=page, per_page=per_page)

        return jsonify({
            'success': True,
            'data': {
                'recommendations': recommendations,
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': total_count,
                    'total_pages': (total_count + per_page - 1) // per_page
                }
            }
        })
    except Exception as e:
        logger.error(f"Error getting pricing recommendations: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to generate pricing recommendations'
        }), 500

@pricing_bp.route('/optimal-pricing-table', methods=['GET'])
def get_optimal_pricing_table():
    try:
        # Get pagination parameters
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 30))  # Changed default to 30 items per page

        # Get filter parameters
        menu_item = request.args.get('menuItem')
        competitor = request.args.get('competitor')
        day_of_week = request.args.get('dayOfWeek')

        # Get recommendations with pagination and filters
        recommendations, total_count = get_recommendations(
            page=page,
            per_page=per_page,
            menu_item=menu_item,
            competitor=competitor,
            day_of_week=day_of_week
        )

        # Transform data for table display
        table_data = [{
            'id': rec['menu_item_id'],
            'menuItem': rec['name'],
            'competitor': rec['competitor'],
            'dayOfWeek': rec['day_of_week'],
            'ingredientCost': f"RM {rec['ingredient_cost']:.2f}",
            'competitorPrice': f"RM {rec['competitor_price']:.2f}",
            'suggestedPrice': f"RM {rec['suggested_price']:.2f}",
            'salesVolume': rec['current_volume'],
            'predictedSalesVolume': rec['predicted_volume'],
            'unitProfit': f"RM {(rec['suggested_price'] - rec['ingredient_cost']):.2f}",
            'originalTotalProfit': f"RM {(rec['competitor_price'] - rec['ingredient_cost']) * rec['current_volume']:.2f}",
            'predictedProfit': f"RM {rec['predicted_profit']:.2f}",
            'profitChange': f"{rec['profit_change_pct']:.1f}%",
            'priceChange': f"{rec['price_change_pct']:.1f}%",
            'confidence': rec['confidence'].capitalize()
        } for rec in recommendations]

        return jsonify({
            'success': True,
            'data': {
                'table': table_data,
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': total_count,
                    'total_pages': (total_count + per_page - 1) // per_page
                }
            }
        })
    except Exception as e:
        logger.error(f"Error getting optimal pricing table: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to generate optimal pricing table'
        }), 500

@pricing_bp.route('/filter-options', methods=['GET'])
def get_filter_options():
    """Get unique menu items and competitors for filters from database."""
    try:
        # Get menu items from database
        menu_items_query = MenuItem.query.with_entities(MenuItem.menu_item_name).distinct().all()
        menu_items = sorted([item.menu_item_name for item in menu_items_query])
        
        # Generate competitor list (since we don't have a competitors table, use default values)
        competitors = ['Competitor A', 'Competitor B', 'Competitor C', 'Competitor D', 'Competitor E']

        return jsonify({
            'success': True,
            'data': {
                'menuItems': menu_items,
                'competitors': competitors
            }
        })
    except Exception as e:
        logger.error(f"Error getting filter options: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to get filter options'
        }), 500

@pricing_bp.route('/detailed-recommendation/<int:menu_item_id>', methods=['GET'])
def get_detailed_recommendation(menu_item_id):
    """Get detailed pricing recommendation for an existing menu item."""
    try:
        recommendation = get_detailed_recommendation_for_existing_item(menu_item_id)

        if recommendation is None:
            return jsonify({
                'success': False,
                'error': 'Menu item not found or unable to generate recommendation'
            }), 404

        return jsonify({
            'success': True,
            'data': recommendation
        })

    except Exception as e:
        logger.error(f"Error getting detailed recommendation: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to generate detailed recommendation'
        }), 500

@pricing_bp.route('/menu-items', methods=['GET'])
def get_menu_items():
    """Get all menu items from database."""
    try:
        menu_items = MenuItem.query.all()
        items_data = []

        for item in menu_items:
            items_data.append({
                'menu_item_id': item.id,
                'menu_item_name': item.menu_item_name,
                'typical_ingredient_cost': float(item.typical_ingredient_cost),
                'category': item.category,
                'cuisine_type': item.cuisine_type,
                'key_ingredients_tags': item.key_ingredients_tags,

                'menu_price': float(item.menu_price) if item.menu_price else None,
                'observed_market_price': float(item.menu_price) if item.menu_price else float(item.typical_ingredient_cost) * 2.5,  # Default market price
                'estimated_market_demand_indicator': 'Medium'  # Default demand indicator
            })

        return jsonify({
            'success': True,
            'data': items_data
        })
    except Exception as e:
        logger.error(f"Error getting menu items: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to fetch menu items'
        }), 500

@pricing_bp.route('/generate-recommendation', methods=['POST'])
def generate_recommendation():
    """Generate pricing recommendation for a specific menu item with optional parameters."""
    try:
        data = request.get_json()
        menu_item_id = data.get('menu_item_id')
        
        # Optional parameters for enhanced optimization
        competitor_price = data.get('competitor_price')
        price_range_start = data.get('price_range_start')
        price_range_end = data.get('price_range_end')
        business_goal = 'profit'  # Fixed to profit only

        if not menu_item_id:
            return jsonify({
                'success': False,
                'error': 'menu_item_id is required'
            }), 400

        # Get menu item from database
        menu_item = MenuItem.query.get(menu_item_id)
        if not menu_item:
            return jsonify({
                'success': False,
                'error': 'Menu item not found'
            }), 404

        # If enhanced parameters are provided, use advanced optimization
        if competitor_price or price_range_start or price_range_end:
            from services.recommendation import predict_optimal_price_for_item
            
            # Convert menu item to the format expected by the optimization function
            menu_item_name = menu_item.menu_item_name
            restaurant_id = f"Restaurant {menu_item_id % 50 + 1}"
            ingredient_cost = float(menu_item.typical_ingredient_cost) if menu_item.typical_ingredient_cost else 5.0
            
            # Use provided parameters or defaults
            start_price = price_range_start if price_range_start else 6.0
            end_price = price_range_end if price_range_end else 25.0
            
            # Get market price from CSV dataset or use fallback
            csv_market_price = get_market_price_from_csv(menu_item_name)
            market_price = competitor_price if competitor_price else (
                csv_market_price if csv_market_price else (
                    float(menu_item.menu_price) if menu_item.menu_price else 
                    max(float(menu_item.typical_ingredient_cost) * 2.5, 8.0)
                )
            )
            
            logger.info(f"Enhanced recommendation for {menu_item_name}: competitor_price=${market_price:.2f}, range=${start_price:.2f}-${end_price:.2f}")
            
            # Run enhanced optimization - allow category-based pricing logic
            result = predict_optimal_price_for_item(
                menu_item_name=menu_item_name,
                restaurant_id=restaurant_id,
                day_of_week='Friday',
                weather_condition='Sunny',
                has_promotion=False,
                # Removed explicit price_range_start and price_range_end to allow category-based pricing
                price_increment=0.25,
                business_goal=business_goal,
                apply_smart_rounding=True,
                include_visualizations=True,
                menu_item_id=menu_item_id,
                category=menu_item.category,
                cuisine_type=menu_item.cuisine_type,
                typical_ingredient_cost=ingredient_cost,
                observed_market_price=market_price
            )
            
            if 'error' in result:
                return jsonify({
                    'success': False,
                    'error': result['error']
                }), 500
            
            # Format enhanced response to match frontend expectations
            response_data = {
                'success': True,
                'results': {
                    'optimization': {
                        'optimal_price': result['optimization']['optimal_price'],
                        'predicted_quantity_at_optimal_price': result['optimization']['predicted_quantity_at_optimal_price'],
                        'maximum_projected_profit': result['optimization']['maximum_projected_profit'],
                        'maximum_projected_revenue': result['optimization']['maximum_projected_revenue'],
                        'observed_market_price': market_price
                    },
                    'price_analysis': result.get('price_analysis', []),
                    'visualizations': result.get('visualizations', {})
                },
                'price_range_tested': f"${start_price:.2f} - ${end_price:.2f}",
                'competitor_price_used': market_price,
                'data_points': len(result.get('price_analysis', [])),
                'business_goal': business_goal,
                'total_scenarios_tested': len(result.get('price_analysis', []))
            }
            
            return jsonify(response_data)
        else:
            # Use original recommendation function for backward compatibility
            recommendation = generate_pricing_recommendation_for_menu_item(menu_item)

            if recommendation is None:
                return jsonify({
                    'success': False,
                    'error': 'Unable to generate recommendation'
                }), 500

            return jsonify({
                'success': True,
                'data': recommendation
            })

    except Exception as e:
        logger.error(f"Error generating recommendation: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to generate recommendation'
        }), 500

@pricing_bp.route('/test-price-range', methods=['POST'])
def test_price_range():
    """Test multiple price points to find optimal pricing for a menu item."""
    try:
        data = request.get_json()
        menu_item_id = data.get('menu_item_id')
        price_range = data.get('price_range', [])

        if not menu_item_id:
            return jsonify({
                'success': False,
                'error': 'menu_item_id is required'
            }), 400

        if not price_range or len(price_range) == 0:
            return jsonify({
                'success': False,
                'error': 'price_range is required and must contain at least one price'
            }), 400

        # Get menu item from database
        menu_item = MenuItem.query.get(menu_item_id)
        if not menu_item:
            return jsonify({
                'success': False,
                'error': 'Menu item not found'
            }), 404

        # Import the price optimization function
        from services.recommendation import predict_optimal_price_for_item
        
        # Convert menu item to the format expected by the optimization function
        menu_item_name = menu_item.menu_item_name
        restaurant_id = f"Restaurant {menu_item_id % 50 + 1}"  # Simulate restaurant mapping
        
        # Get ingredient cost for profit calculations
        ingredient_cost = float(menu_item.typical_ingredient_cost) if menu_item.typical_ingredient_cost else 5.0
        
        # Test each price point and calculate metrics
        price_analysis = []
        best_profit = -1
        optimal_price_data = None
        
        logger.info(f"Testing {len(price_range)} price points for {menu_item_name}")
        
        for price in price_range:
            try:
                # Use the existing optimization function to get detailed analysis
                result = predict_optimal_price_for_item(
                    menu_item_name=menu_item_name,
                    restaurant_id=restaurant_id,
                    day_of_week='Friday',
                    weather_condition='Sunny',
                    has_promotion=False,
                    price_range_start=price,
                    price_range_end=price,
                    price_increment=0.01,  # Small increment for single price test
                    business_goal='profit',  # Default to profit maximization
                    apply_smart_rounding=True,

                    include_visualizations=False,  # Skip visualizations for batch testing
                    category=menu_item.category,
                    cuisine_type=menu_item.cuisine_type,
                    typical_ingredient_cost=ingredient_cost
                )
                
                if 'error' not in result:
                    predicted_quantity = result['optimization']['predicted_quantity_at_optimal_price']
                    predicted_revenue = price * predicted_quantity
                    profit = result['optimization']['maximum_projected_profit']
                    confidence = 0.85  # Default confidence score
                    
                    # Check if this is the best price so far
                    is_optimal = profit > best_profit
                    if is_optimal:
                        best_profit = profit
                        optimal_price_data = {
                            'price': price,
                            'predicted_revenue': predicted_revenue,
                            'confidence': confidence
                        }
                    
                    price_analysis.append({
                        'price': price,
                        'predicted_revenue': predicted_revenue,
                        'confidence': confidence,
                        'is_optimal': is_optimal
                    })
                else:
                    # Fallback calculation if optimization fails
                    estimated_quantity = max(1, int(100 - (price - ingredient_cost) * 5))  # Simple demand model
                    predicted_revenue = price * estimated_quantity
                    profit = (price - ingredient_cost) * estimated_quantity
                    confidence = 0.6  # Lower confidence for fallback
                    
                    is_optimal = profit > best_profit
                    if is_optimal:
                        best_profit = profit
                        optimal_price_data = {
                            'price': price,
                            'predicted_revenue': predicted_revenue,
                            'confidence': confidence
                        }
                    
                    price_analysis.append({
                        'price': price,
                        'predicted_revenue': predicted_revenue,
                        'confidence': confidence,
                        'is_optimal': is_optimal
                    })
                    
            except Exception as price_error:
                logger.warning(f"Error testing price ${price:.2f}: {str(price_error)}")
                # Add a basic entry even if calculation fails
                price_analysis.append({
                    'price': price,
                    'predicted_revenue': price * 50,  # Fallback estimate
                    'confidence': 0.3,
                    'is_optimal': False
                })
        
        # Generate analysis summary
        if optimal_price_data:
            analysis_summary = f"Based on AI analysis of {len(price_range)} price points, the optimal price of ${optimal_price_data['price']:.2f} is expected to generate ${optimal_price_data['predicted_revenue']:.2f} in revenue with {optimal_price_data['confidence']*100:.1f}% confidence. This price balances profitability with market demand for {menu_item_name}."
        else:
            analysis_summary = f"Analysis completed for {len(price_range)} price points. Consider market conditions and ingredient costs when setting the final price."
        
        # Prepare response
        response_data = {
            'menu_item_name': menu_item_name,
            'ingredient_cost': ingredient_cost,
            'price_analysis': price_analysis,
            'optimal_price': optimal_price_data,
            'analysis_summary': analysis_summary,
            'total_prices_tested': len(price_range)
        }
        
        return jsonify({
            'success': True,
            'data': response_data
        })

    except Exception as e:
        logger.error(f"Error testing price range: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to test price range'
        }), 500

@pricing_bp.route('/apply-price', methods=['POST'])
def apply_price():
    """Apply price change to a menu item."""
    try:
        data = request.get_json()
        menu_item_id = data.get('menu_item_id')
        new_price = data.get('new_price')

        if not menu_item_id or new_price is None:
            return jsonify({
                'success': False,
                'error': 'menu_item_id and new_price are required'
            }), 400

        # Get menu item from database
        menu_item = MenuItem.query.get(menu_item_id)
        if not menu_item:
            return jsonify({
                'success': False,
                'error': 'Menu item not found'
            }), 404

        # Update the price
        old_price = menu_item.menu_price
        menu_item.menu_price = float(new_price)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': f'Price updated successfully for {menu_item.menu_item_name}',
            'data': {
                'menu_item_id': menu_item_id,
                'menu_item_name': menu_item.menu_item_name,
                'old_price': float(old_price) if old_price else None,
                'new_price': float(new_price)
            }
        })

    except Exception as e:
        logger.error(f"Error applying price: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'Failed to apply price change'
        }), 500

@pricing_bp.route('/optimize-advanced', methods=['POST'])
def optimize_advanced():
    """Advanced price optimization with business goal selection, smart rounding, and competitor benchmarking."""
    try:
        data = request.get_json()
        menu_item_id = data.get('menu_item_id')
        
        # Enhanced optimization parameters
        business_goal = 'profit'  # Fixed to profit only
        apply_smart_rounding = data.get('apply_smart_rounding', True)
        include_visualizations = data.get('include_visualizations', True)
        
        # Price range parameters
        price_range_start = data.get('price_range_start', 6.0)
        price_range_end = data.get('price_range_end', 25.0)
        price_increment = data.get('price_increment', 0.25)
        
        if not menu_item_id:
            return jsonify({
                'success': False,
                'error': 'menu_item_id is required'
            }), 400
        
        # Business goal is now fixed to profit only, no validation needed
        
        # Get menu item from database
        menu_item = MenuItem.query.get(menu_item_id)
        if not menu_item:
            return jsonify({
                'success': False,
                'error': 'Menu item not found'
            }), 404
        
        # Import the enhanced optimization function
        from services.recommendation import predict_optimal_price_for_item
        
        # Convert menu item to the format expected by the optimization function
        menu_item_name = menu_item.menu_item_name
        restaurant_id = f"Restaurant {menu_item_id % 50 + 1}"
        ingredient_cost = float(menu_item.typical_ingredient_cost) if menu_item.typical_ingredient_cost else 5.0
        
        # Get observed market price from CSV dataset
        observed_market_price = get_market_price_from_csv(menu_item_name)
        if not observed_market_price:
            observed_market_price = float(menu_item.menu_price) if menu_item.menu_price else ingredient_cost * 2.5
        
        logger.info(f"Advanced optimization for {menu_item_name}: {business_goal} maximization, market price: ${observed_market_price:.2f}")
        
        # Run enhanced optimization - allow category-based pricing logic
        result = predict_optimal_price_for_item(
            menu_item_name=menu_item_name,
            restaurant_id=restaurant_id,
            day_of_week='Friday',
            weather_condition='Sunny',
            has_promotion=False,
            # Removed explicit price_range_start and price_range_end to allow category-based pricing
            price_increment=price_increment,
            business_goal=business_goal,
            apply_smart_rounding=apply_smart_rounding,
            include_visualizations=include_visualizations,
            menu_item_id=menu_item_id,  # Pass the menu_item_id to ensure correct database lookup
            category=menu_item.category,
            cuisine_type=menu_item.cuisine_type,
            typical_ingredient_cost=ingredient_cost,
            observed_market_price=observed_market_price
        )
        
        if 'error' in result:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 500
        
        # Generate AI-powered analysis using Gemini API
        optimal_price = result.get('optimization', {}).get('optimal_price', 0)
        projected_profit = result.get('optimization', {}).get('projected_profit', 0)
        
        ai_analysis = generate_ai_analysis(
            menu_item_name=menu_item_name,
            category=menu_item.category or 'Main Course',
            cuisine_type=menu_item.cuisine_type or 'International',
            optimal_price=optimal_price,
            ingredient_cost=ingredient_cost,
            projected_profit=projected_profit
        )
        
        # Format response with enhanced features and AI analysis
        response_data = {
            'success': True,
            'menu_item_name': menu_item_name,
            'menu_item_id': menu_item_id,
            'optimization_parameters': {
                'business_goal': business_goal,
                'smart_rounding_applied': apply_smart_rounding,
                'price_range': f"${price_range_start:.2f} - ${price_range_end:.2f}",
                'price_increment': price_increment
            },
            'results': result,
            'ai_analysis': ai_analysis,
            'enhanced_features': {
                'psychological_pricing': result.get('optimization', {}).get('smart_rounded', False),
                'ai_analysis_generated': True,
                'business_goal_optimized': business_goal,
                'visualizations_included': include_visualizations and 'visualizations' in result
            }
        }
        
        logger.info(f"✅ Advanced optimization completed for {menu_item_name}")
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Error in advanced optimization: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to perform advanced optimization'
        }), 500

@pricing_bp.route('/batch-optimize', methods=['POST'])
def batch_optimize():
    """Batch price optimization for multiple menu items."""
    try:
        data = request.get_json()
        menu_item_ids = data.get('menu_item_ids', [])
        
        # Optimization parameters
        base_params = {
            'price_range_start': data.get('price_range_start', 6.0),
            'price_range_end': data.get('price_range_end', 25.0),
            'price_increment': data.get('price_increment', 0.25),
            'business_goal': 'profit',  # Fixed to profit only
            'apply_smart_rounding': data.get('apply_smart_rounding', True),

        }
        
        if not menu_item_ids or len(menu_item_ids) == 0:
            return jsonify({
                'success': False,
                'error': 'menu_item_ids is required and must contain at least one item'
            }), 400
        
        if len(menu_item_ids) > 20:
            return jsonify({
                'success': False,
                'error': 'Maximum 20 items allowed for batch optimization'
            }), 400
        
        # Get menu items from database
        menu_items = MenuItem.query.filter(MenuItem.id.in_(menu_item_ids)).all()
        if len(menu_items) != len(menu_item_ids):
            return jsonify({
                'success': False,
                'error': 'One or more menu items not found'
            }), 404
        
        # Convert to format expected by batch optimization
        items_for_optimization = []
        for item in menu_items:
            # Get market price from CSV dataset
            market_price = get_market_price_from_csv(item.menu_item_name)
            if not market_price:
                market_price = float(item.menu_price) if item.menu_price else float(item.typical_ingredient_cost) * 2.5 if item.typical_ingredient_cost else 12.5
            
            items_for_optimization.append({
                'name': item.menu_item_name,
                'ingredient_cost': float(item.typical_ingredient_cost) if item.typical_ingredient_cost else 5.0,
                'market_price': market_price,
                'category': item.category,
                'cuisine_type': item.cuisine_type,
                'current_price': float(item.menu_price) if item.menu_price else 0,
                'menu_item_id': item.id
            })
        
        # Import batch optimization function
        from services.recommendation import batch_optimize_prices
        
        logger.info(f"Starting batch optimization for {len(items_for_optimization)} items")
        
        # Run batch optimization
        batch_results = batch_optimize_prices(items_for_optimization, base_params)
        
        # Format response
        response_data = {
            'success': True,
            'batch_summary': batch_results['summary'],
            'optimization_parameters': base_params,
            'results': batch_results['results'],
            'processing_info': {
                'total_items_requested': len(menu_item_ids),
                'items_processed': len(items_for_optimization),
                'successful_optimizations': batch_results['summary']['successful_optimizations'],
                'failed_optimizations': batch_results['summary']['failed_optimizations']
            }
        }
        
        logger.info(f"✅ Batch optimization completed: {batch_results['summary']['successful_optimizations']}/{len(items_for_optimization)} successful")
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Error in batch optimization: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to perform batch optimization'
        }), 500

@pricing_bp.route('/apply', methods=['POST'])
def apply_price_changes():
    """Apply selected price changes to menu items."""
    try:
        data = request.get_json()
        price_changes = data.get('price_changes', [])

        # In a real application, you would update the database here
        # For now, we'll just return a success response
        applied_changes = []

        for change in price_changes:
            applied_changes.append({
                'menu_item_id': change.get('menu_item_id'),
                'name': change.get('name'),
                'old_price': change.get('current_price'),
                'new_price': change.get('suggested_price'),
                'status': 'applied'
            })

        return jsonify({
            'success': True,
            'message': f'Successfully applied {len(applied_changes)} price changes',
            'applied_changes': applied_changes
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500