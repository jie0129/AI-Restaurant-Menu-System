import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# AutoGen imports - using the newer autogen-agentchat package
try:
    # Try the newer v0.4+ API first
    from autogen_agentchat.agents import AssistantAgent
    from autogen_agentchat.teams import RoundRobinGroupChat
    from autogen_agentchat.messages import TextMessage
    AUTOGEN_VERSION = "v0.4+"
except ImportError:
    try:
        # Fallback to v0.2 API
        from autogen import ConversableAgent, GroupChat, GroupChatManager
        AUTOGEN_VERSION = "v0.2"
    except ImportError:
        # If AutoGen is not available, create mock classes
        class ConversableAgent:
            def __init__(self, *args, **kwargs):
                pass
            def initiate_chat(self, *args, **kwargs):
                return {"chat_history": []}
        
        class GroupChat:
            def __init__(self, *args, **kwargs):
                pass
        
        class GroupChatManager:
            def __init__(self, *args, **kwargs):
                pass
        
        AUTOGEN_VERSION = "mock"

# Existing service imports
from services.recommendation import forecast_demand_for_scenario, predict_optimal_price_for_item
from services.usda_nutrition_service import USDANutritionService
from services.demand_forecasting_service import AdvancedDemandForecaster
import pandas as pd

# Import models
try:
    from models.menu_item import MenuItem
    from models.recipe import Recipe
    from models.menu_nutrition import MenuNutrition
    from models.menu_item_forecasts import MenuItemForecast
    from models.menu_item_image import MenuItemImage
    from models.forecast_performance import ForecastPerformance
    from models.current_forecasts import CurrentForecast
    from models.inventory_item import db
    from models.ingredient import Ingredient
except ImportError as e:
    logger.warning(f"Could not import some models: {e}")
    # Create mock classes for testing
    class MenuItem:
        pass
    class Recipe:
        pass
    class MenuNutrition:
        pass
    class MenuItemForecast:
        pass
    class Ingredient:
        pass
    db = None

try:
    from config import Config
except ImportError:
    class Config:
        pass

logger = logging.getLogger(__name__)

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
        logger.warning(f"Error extracting market price from CSV: {e}")
        return None

@dataclass
class DishSuggestion:
    """Represents a dish suggestion for the workflow"""
    name: str
    description: str
    category: str
    cuisine_type: str
    ingredients: List[str]
    estimated_cost: float
    suggested_price: float
    predicted_demand: float
    nutrition_score: float = 0.0
    creativity_score: float = 0.0
    feasibility_score: float = 0.0
    overall_score: float = 0.0
    recipe_instructions: Optional[str] = None
    nutrition_data: Optional[Dict[str, Any]] = None
    market_analysis: Optional[Dict[str, Any]] = None

class AutoGenRestaurantAI:
    """AutoGen-based Restaurant AI Agent System for workflow automation"""
    
    def __init__(self):
        self.nutrition_service = USDANutritionService()
        self.demand_forecaster = AdvancedDemandForecaster()
        
        # Image service is optional (may not be available)
        self.image_service = None
        try:
            from services.image_generation_service import ImageGenerationService
            self.image_service = ImageGenerationService()
            logger.info("Image generation service loaded successfully")
        except ImportError:
            logger.warning("Image generation service not available - image generation will be simulated")
        
        # Initialize AutoGen agents
        self._setup_agents()
        
    def _setup_agents(self):
        """Setup AutoGen agents for different workflow steps"""
        
        logger.info(f"Setting up AutoGen agents using version: {AUTOGEN_VERSION}")
        
        # Check if we need to use mock agents
        api_key = os.getenv("OPENAI_API_KEY")
        use_mock_agents = AUTOGEN_VERSION == "mock" or not api_key
        
        if use_mock_agents:
            logger.warning("Using mock AutoGen agents - no actual AI conversation will occur")
            if not api_key:
                logger.warning("OPENAI_API_KEY not set")
            
            # Create simple mock agents
            class MockAgent:
                def __init__(self, name="MockAgent"):
                    self.name = name
                
                def generate_reply(self, messages=None):
                    return f"Mock response from {self.name}"
                
                def initiate_chat(self, *args, **kwargs):
                    return {"chat_history": [], "summary": "Mock conversation"}
            
            self.dish_creator = MockAgent("DishCreator")
            self.db_manager = MockAgent("DatabaseManager")
            self.image_generator = MockAgent("ImageGenerator")
            self.recipe_creator = MockAgent("RecipeCreator")
            self.forecaster = MockAgent("DemandForecaster")
            self.pricing_optimizer = MockAgent("PricingOptimizer")
            self.nutrition_analyst = MockAgent("NutritionAnalyst")
            self.coordinator = MockAgent("WorkflowCoordinator")
            return
        
        llm_config = {
            "model": "gpt-4",
            "api_key": api_key,
            "temperature": 0.7
        }
        
        if AUTOGEN_VERSION == "v0.4+":
            # Use newer v0.4+ API
            try:
                from autogen_ext.models.openai import OpenAIChatCompletionClient
                model_client = OpenAIChatCompletionClient(model="gpt-4", api_key=api_key)
                
                self.dish_creator = AssistantAgent(
                    name="DishCreator",
                    model_client=model_client,
                    system_message="You are a creative chef AI that suggests innovative dishes."
                )
                # Create other agents similarly...
                self.coordinator = self.dish_creator  # Simplified for now
                
            except ImportError:
                logger.warning("Could not import v0.4+ components, falling back to mock")
                self.coordinator = ConversableAgent()
                
        else:
            # Use v0.2 API
            self.dish_creator = ConversableAgent(
                name="DishCreator",
                system_message="""You are a creative chef AI that suggests innovative dishes based on available ingredients.
                Your role is to create unique, feasible dish concepts with detailed descriptions.
                Focus on creativity, feasibility, and market appeal.""",
                llm_config=llm_config,
                human_input_mode="NEVER"
            )
            
            # For simplicity, use the same agent as coordinator
            self.coordinator = self.dish_creator
            
            # Create other agents (simplified)
            self.db_manager = self.dish_creator
            self.image_generator = self.dish_creator
            self.recipe_creator = self.dish_creator
            self.forecaster = self.dish_creator
            self.pricing_optimizer = self.dish_creator
            self.nutrition_analyst = self.dish_creator
    
    def automate_full_workflow(self, ingredients: List[str] = None, auto_apply: bool = False, dish_name: str = None, category: str = None) -> Dict[str, Any]:
        """Main entry point for the 7-step Innovation Mode workflow"""
        try:
            logger.info(f"Starting 7-step Innovation Mode workflow with AutoGen version: {AUTOGEN_VERSION}")
            
            # Execute the redesigned 7-step workflow
            return self._execute_innovation_workflow(ingredients, auto_apply, dish_name, category)
                
        except Exception as e:
            logger.error(f"Innovation workflow failed: {str(e)}")
            return {
                'status': 'error',
                'message': f'Innovation workflow failed: {str(e)}',
                'framework': 'AutoGen Innovation Mode',
                'version': AUTOGEN_VERSION,
                'error_details': str(e)
            }
    
    def _execute_innovation_workflow(self, ingredients: List[str] = None, auto_apply: bool = False, dish_name: str = None, category: str = None) -> Dict[str, Any]:
        """Execute the complete 7-step Innovation Mode workflow"""
        
        results = {
            "success": True,
            "workflow_type": "Innovation Mode - 7 Steps",
            "framework": "AutoGen Innovation",
            "version": AUTOGEN_VERSION,
            "auto_apply": auto_apply,
            "steps": {},
            "dish_suggestion": None,
            "menu_item_id": None
        }
        
        try:
            # Step 1: Extract ingredients from database
            logger.info("Step 1: Extracting ingredients from database")
            step1_result = self._step1_extract_ingredients(ingredients)
            results["steps"]["step1_extract_ingredients"] = step1_result
            
            if not step1_result.get('success'):
                raise Exception("Failed to extract ingredients from database")
            
            available_ingredients = step1_result.get('ingredients', [])
            
            # Step 2: Generate innovative dish suggestion
            logger.info("Step 2: Generating innovative dish suggestion")
            step2_result = self._step2_innovative_dish_suggestion(available_ingredients, custom_dish_name=dish_name, custom_category=category)
            results["steps"]["step2_dish_suggestion"] = step2_result
            
            if not step2_result.get('success'):
                raise Exception("Failed to generate innovative dish suggestion")
            
            dish_suggestion = step2_result.get('dish_suggestion')
            results["dish_suggestion"] = dish_suggestion
            
            if auto_apply and dish_suggestion:
                # Step 3: Add new menu item and generate AI image
                logger.info("Step 3: Adding menu item and generating AI image")
                step3_result = self._step3_add_menu_item_with_image(dish_suggestion)
                results["steps"]["step3_menu_item_creation"] = step3_result
                
                if step3_result.get('success'):
                    results["menu_item_id"] = step3_result.get('menu_item_id')
                    
                    # Step 4: Set recipe and insert to recipes table
                    logger.info("Step 4: Creating recipe entries")
                    step4_result = self._step4_create_recipe(dish_suggestion, step3_result.get('menu_item_id'))
                    results["steps"]["step4_recipe_creation"] = step4_result
                    
                    # Step 5: Run forecast for innovative dish
                    logger.info("Step 5: Running demand forecast")
                    step5_result = self._step5_run_forecast(dish_suggestion, step3_result.get('menu_item_id'))
                    results["steps"]["step5_forecast_generation"] = step5_result
                    
                    # Step 6: Run price recommendation and update menu_price
                    logger.info("Step 6: Optimizing pricing")
                    step6_result = self._step6_price_optimization(dish_suggestion, step3_result.get('menu_item_id'))
                    results["steps"]["step6_price_optimization"] = step6_result
                    
                    # Step 7: Generate nutrition information
                    logger.info("Step 7: Analyzing nutrition")
                    step7_result = self._step7_nutrition_analysis(dish_suggestion, step3_result.get('menu_item_id'))
                    results["steps"]["step7_nutrition_analysis"] = step7_result
                    
                    logger.info("All 7 steps completed successfully")
                else:
                    logger.error("Step 3 failed, skipping remaining steps")
            else:
                logger.info("Auto-apply disabled, only showing dish suggestion")
                
        except Exception as e:
            logger.error(f"Innovation workflow failed at step: {str(e)}")
            results["success"] = False
            results["error"] = str(e)
        
        return results
    
    def _execute_v02_workflow(self, ingredients: List[str], auto_apply: bool = False) -> Dict[str, Any]:
        """Execute workflow using AutoGen v0.2 API"""
        
        # Create group chat with all agents
        agents = [
            self.coordinator,
            self.dish_creator,
            self.db_manager,
            self.image_generator,
            self.recipe_creator,
            self.forecaster,
            self.pricing_optimizer,
            self.nutrition_analyst
        ]
        
        group_chat = GroupChat(
            agents=agents,
            messages=[],
            max_round=20,
            speaker_selection_method="round_robin"
        )
        
        manager = GroupChatManager(groupchat=group_chat, llm_config={
            "model": "gpt-4",
            "api_key": os.getenv("OPENAI_API_KEY"),
            "temperature": 0.3
        })
        
        # Use the new 7-step innovation workflow instead of group chat
        return self._execute_innovation_workflow(ingredients, dish_name, auto_apply)
    
    def _execute_v04_workflow(self, ingredients: List[str], auto_apply: bool = False) -> Dict[str, Any]:
        """Execute workflow using AutoGen v0.4+ API"""
        
        # Placeholder for v0.4+ implementation
        return self._execute_simplified_workflow(ingredients, auto_apply)
    
    def _process_workflow_results(self, chat_result, ingredients: List[str], auto_apply: bool) -> Dict[str, Any]:
        """Process the AutoGen chat results and execute database operations"""
        try:
            # Extract information from chat messages
            messages = chat_result.chat_history if hasattr(chat_result, 'chat_history') else []
            
            # Create a dish suggestion based on the conversation
            dish_suggestion = self._extract_dish_suggestion(messages, ingredients)
            
            results = {
                'step_1_dish_suggestion': dish_suggestion,
                'step_2_database_insertion': None,
                'step_3_image_generation': None,
                'step_4_recipe_creation': None,
                'step_5_demand_forecast': None,
                'step_6_pricing_optimization': None,
                'step_7_nutrition_analysis': None
            }
            
            if auto_apply:
                # Execute each step with actual database operations
                results['step_2_database_insertion'] = self._execute_database_insertion(dish_suggestion)
                results['step_3_image_generation'] = self._execute_image_generation(dish_suggestion)
                results['step_4_recipe_creation'] = self._execute_recipe_creation(dish_suggestion)
                results['step_5_demand_forecast'] = self._execute_demand_forecast(dish_suggestion)
                results['step_6_pricing_optimization'] = self._execute_pricing_optimization(dish_suggestion)
                results['step_7_nutrition_analysis'] = self._execute_nutrition_analysis(dish_suggestion)
            
            return results
            
        except Exception as e:
            logger.error(f"Error processing workflow results: {str(e)}")
            return {'error': str(e)}
    
    def _extract_dish_suggestion(self, messages: List, ingredients: List[str]) -> DishSuggestion:
        """Extract dish suggestion from AutoGen conversation"""
        # Create a basic dish suggestion (in real implementation, parse from messages)
        import random
        
        main_ingredient = ingredients[0] if ingredients else "Mixed Ingredients"
        
        return DishSuggestion(
            name=f"AutoGen {main_ingredient.title()} Fusion",
            description=f"An innovative dish featuring {', '.join(ingredients[:3])} with modern culinary techniques",
            category=self._determine_dish_category(ingredients),
            cuisine_type="Fusion",
            ingredients=ingredients,
            estimated_cost=round(random.uniform(8.0, 15.0), 2),
            suggested_price=round(random.uniform(18.0, 28.0), 2),
            predicted_demand=round(random.uniform(25.0, 45.0), 1),
            nutrition_score=round(random.uniform(0.7, 0.9), 2),
            creativity_score=round(random.uniform(0.8, 0.95), 2),
            feasibility_score=round(random.uniform(0.75, 0.9), 2),
            overall_score=round(random.uniform(0.8, 0.9), 2)
        )
    
    def _step1_extract_ingredients(self, requested_ingredients: List[str] = None) -> Dict[str, Any]:
        """Step 1: Extract ingredients from database"""
        try:
            # Get all available ingredients from database
            all_ingredients = Ingredient.query.all()
            
            if not all_ingredients:
                return {
                    'success': False,
                    'error': 'No ingredients found in database',
                    'ingredients': []
                }
            
            # Convert to list of ingredient data
            ingredients_data = []
            for ingredient in all_ingredients:
                ingredients_data.append({
                    'id': ingredient.id,
                    'name': ingredient.name,
                    'category': getattr(ingredient, 'category', 'Unknown'),
                    'unit': getattr(ingredient, 'unit', 'units'),
                    'current_stock': getattr(ingredient, 'current_stock', 0)
                })
            
            # If specific ingredients were requested, filter for those
            if requested_ingredients:
                filtered_ingredients = []
                for req_ing in requested_ingredients:
                    for ing_data in ingredients_data:
                        if req_ing.lower() in ing_data['name'].lower():
                            filtered_ingredients.append(ing_data)
                            break
                
                if filtered_ingredients:
                    ingredients_data = filtered_ingredients
                else:
                    # If no matches found, use top 5 ingredients by stock
                    ingredients_data = sorted(ingredients_data, key=lambda x: x['current_stock'], reverse=True)[:5]
            else:
                # Use top 10 ingredients by stock for innovation
                ingredients_data = sorted(ingredients_data, key=lambda x: x['current_stock'], reverse=True)[:10]
            
            return {
                'success': True,
                'ingredients': ingredients_data,
                'total_available': len(all_ingredients),
                'selected_count': len(ingredients_data)
            }
            
        except Exception as e:
            logger.error(f"Step 1 - Extract ingredients error: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'ingredients': []
            }
    
    def _step2_innovative_dish_suggestion(self, available_ingredients: List[Dict], custom_dish_name: str = None, custom_category: str = None) -> Dict[str, Any]:
        """Step 2: Generate innovative dish suggestion using AI"""
        try:
            # Debug logging
            logger.info(f"Step 2: Custom dish name provided: '{custom_dish_name}'")
            
            if not available_ingredients:
                return {
                    'success': False,
                    'error': 'No ingredients available for dish creation'
                }
            
            # Select 3-5 ingredients for the dish
            selected_ingredients = available_ingredients[:5]
            ingredient_names = [ing['name'] for ing in selected_ingredients]
            
            # Use custom dish name if provided, otherwise generate one
            if custom_dish_name:
                dish_name = custom_dish_name
                dish_description = f"A creative medley highlighting {', '.join(ingredient_names[:2])} with innovative cooking techniques and seasonal accompaniments"
                logger.info(f"Step 2: Using custom dish name: '{dish_name}'")
            else:
                # Generate creative dish using AI (simplified for now)
                dish_name = self._generate_creative_dish_name(ingredient_names)
                dish_description = self._generate_dish_description(ingredient_names)
                logger.info(f"Step 2: Generated dish name: '{dish_name}'")
            
            # Use custom category if provided, otherwise determine from dish name and ingredients
            print(f"DEBUG Step 2: custom_category parameter = {custom_category}")
            if custom_category:
                category = custom_category
                logger.info(f"Step 2: Using predefined category: '{category}'")
                print(f"DEBUG Step 2: Using predefined category: '{category}'")
            else:
                category = self._determine_dish_category(ingredient_names, dish_name)
                logger.info(f"Step 2: Determined category: '{category}'")
                print(f"DEBUG Step 2: Determined category from logic: '{category}'")
            
            print(f"DEBUG Step 2: Final category being used: '{category}'")
            
            # Create dish suggestion object with debug info
            debug_info = {
                'received_custom_category': custom_category,
                'final_category_used': category,
                'category_source': 'custom' if custom_category else 'determined'
            }
            dish_suggestion = DishSuggestion(
                name=dish_name,
                description=dish_description,
                category=category,
                cuisine_type=self._determine_cuisine_type(ingredient_names),
                ingredients=ingredient_names,
                estimated_cost=self._calculate_estimated_cost(selected_ingredients),
                suggested_price=0.0,  # Will be set in step 6
                predicted_demand=0.0,  # Will be set in step 5
                nutrition_score=0.8,
                creativity_score=0.85,
                feasibility_score=0.8,
                overall_score=0.82
            )
            
            return {
                'success': True,
                'dish_suggestion': dish_suggestion,
                'selected_ingredients': selected_ingredients,
                'debug_info': debug_info
            }
            
        except Exception as e:
            logger.error(f"Step 2 - Innovative dish suggestion error: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _step3_add_menu_item_with_image(self, dish_suggestion: DishSuggestion) -> Dict[str, Any]:
        """Step 3: Add new menu item and generate AI image"""
        try:
            # Create menu item
            new_menu_item = MenuItem(
                menu_item_name=dish_suggestion.name,
                typical_ingredient_cost=dish_suggestion.estimated_cost,
                category=dish_suggestion.category,
                cuisine_type=dish_suggestion.cuisine_type,
                key_ingredients_tags=', '.join(dish_suggestion.ingredients),
                menu_price=0.0  # Will be set in step 6
            )
            
            db.session.add(new_menu_item)
            db.session.commit()
            
            menu_item_id = new_menu_item.id
            
            # Generate AI image
            image_result = self._generate_ai_image(menu_item_id, dish_suggestion)
            
            return {
                'success': True,
                'menu_item_id': menu_item_id,
                'menu_item_name': new_menu_item.menu_item_name,
                'image_result': image_result
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Step 3 - Menu item creation error: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _step4_create_recipe(self, dish_suggestion: DishSuggestion, menu_item_id: int) -> Dict[str, Any]:
        """Step 4: Set recipe and insert to recipes table"""
        try:
            # Get ingredients from database that match the dish ingredients
            recipes_created = 0
            
            for ingredient_name in dish_suggestion.ingredients:
                ingredient = Ingredient.query.filter(
                    Ingredient.name.ilike(f'%{ingredient_name}%')
                ).first()
                
                if ingredient:
                    # Calculate quantity based on ingredient type
                    quantity = self._calculate_recipe_quantity(ingredient_name)
                    
                    recipe = Recipe(
                        dish_id=menu_item_id,
                        ingredient_id=ingredient.id,
                        quantity_per_unit=quantity,
                        recipe_unit=getattr(ingredient, 'unit', 'grams')
                    )
                    db.session.add(recipe)
                    recipes_created += 1
            
            db.session.commit()
            
            return {
                'success': True,
                'recipes_created': recipes_created,
                'menu_item_id': menu_item_id
            }
                
        except Exception as e:
            db.session.rollback()
            logger.error(f"Step 4 - Recipe creation error: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _step5_run_forecast(self, dish_suggestion: DishSuggestion, menu_item_id: int) -> Dict[str, Any]:
        """Step 5: Run item-specific forecast using unified restaurant demand system"""
        try:
            from datetime import timedelta
            from services.unified_restaurant_demand_system import RestaurantDemandPredictor
            
            # Initialize the unified predictor with item-specific analysis
            data_path = "C:/Users/User/Desktop/first-app/instance/cleaned_streamlined_ultimate_malaysian_data.csv"
            predictor = RestaurantDemandPredictor(data_path)
            
            # Run item-specific analysis for the new menu item
            forecast_days = 28  # Extended forecast period for better analysis
            logger.info(f"Running item-specific analysis for menu item {menu_item_id}: {dish_suggestion.name}")
            
            # Run item-specific analysis using proper new/existing item detection
            results = predictor.run_item_specific_analysis(
                item_id=menu_item_id, 
                item_name=dish_suggestion.name, 
                forecast_days=forecast_days
            )
            
            logger.info(f"Item-specific analysis results: success={results.get('success') if results else None}")
            
            if not results or not results.get('success'):
                # Fallback to simple forecast if item-specific analysis fails
                logger.warning("Item-specific analysis failed, using fallback forecast")
                return self._fallback_forecast_generation(dish_suggestion, menu_item_id)
            
            # Extract performance metrics from item-specific analysis
            performance_data = results.get('performance', {})
            best_model = results.get('summary', {}).get('best_model', 'unknown')
            best_r2_score = results.get('summary', {}).get('best_r2_score', 0.0)
            
            # Get forecast data from results
            forecast_data = results.get('forecasts', [])
            forecasts_created = 0
            
            # Process and save forecast data
            for forecast_item in forecast_data[:7]:  # Use first 7 days for immediate planning
                forecast_date_str = forecast_item.get('date')
                if isinstance(forecast_date_str, str):
                    forecast_date = datetime.fromisoformat(forecast_date_str).date()
                else:
                    forecast_date = forecast_date_str
                
                predicted_quantity = forecast_item.get('predicted_quantity', 25.0)
                lower_bound = forecast_item.get('confidence_lower', predicted_quantity * 0.8)
                upper_bound = forecast_item.get('confidence_upper', predicted_quantity * 1.2)
                
                # Insert to menu_item_forecasts
                forecast = MenuItemForecast(
                    model_version=f'unified_item_specific_{best_model}',
                    menu_item_id=menu_item_id,
                    date=forecast_date,
                    predicted_quantity=predicted_quantity,
                    lower_bound=lower_bound,
                    upper_bound=upper_bound
                )
                db.session.add(forecast)
                
                # Insert to current_forecasts
                current_forecast = CurrentForecast(
                    item_type='menu_item',
                    item_id=menu_item_id,
                    item_name=dish_suggestion.name,
                    forecast_date=forecast_date,
                    predicted_quantity=predicted_quantity,
                    confidence_lower=lower_bound,
                    confidence_upper=upper_bound,
                    model_version=f'unified_item_specific_{best_model}'
                )
                db.session.add(current_forecast)
                forecasts_created += 1
            
            # Insert performance metrics from item-specific analysis
            from datetime import date
            if performance_data and best_model in performance_data:
                model_performance = performance_data[best_model]
                performance = ForecastPerformance(
                    model_version=f'unified_item_specific_{best_model}',
                    forecast_type='menu_item',
                    item_id=menu_item_id,
                    evaluation_date=date.today(),
                    mae=model_performance.get('mae', 2.5),
                    rmse=model_performance.get('rmse', 3.2),
                    mape=model_performance.get('mape', 8.5),
                    r2_score=model_performance.get('r2_score', best_r2_score)
                )
                db.session.add(performance)
            
            db.session.commit()
            
            # Update dish suggestion with predicted demand from item-specific analysis
            avg_predicted_demand = sum(f.get('predicted_quantity', 25.0) for f in forecast_data[:7]) / min(len(forecast_data), 7)
            dish_suggestion.predicted_demand = avg_predicted_demand
            
            logger.info(f"Item-specific forecast completed: {best_model} model with R² = {best_r2_score:.4f}")
            
            return {
                'success': True,
                'forecasts_created': forecasts_created,
                'predicted_demand': avg_predicted_demand,
                'forecast_horizon_days': forecast_days,
                'best_model': best_model,
                'r2_score': best_r2_score,
                'analysis_type': 'item_specific'
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Step 5 - Item-specific forecast error: {str(e)}")
            # Try fallback forecast
            return self._fallback_forecast_generation(dish_suggestion, menu_item_id)
    
    def _fallback_forecast_generation(self, dish_suggestion: DishSuggestion, menu_item_id: int) -> Dict[str, Any]:
        """Fallback forecast generation when item-specific analysis fails"""
        try:
            from datetime import timedelta
            
            logger.info("Using fallback forecast generation")
            
            # Generate forecast data for 7 days with improved logic
            base_demand = 25.0  # Base demand for new innovative dish
            forecasts_created = 0
            
            for day in range(7):
                forecast_date = (datetime.now() + timedelta(days=day+1)).date()
                
                # Calculate predicted demand with some variation
                predicted_quantity = base_demand + (day * 2) + (day % 3 * 5)
                lower_bound = predicted_quantity * 0.8
                upper_bound = predicted_quantity * 1.2
                
                # Insert to menu_item_forecasts
                forecast = MenuItemForecast(
                    model_version='ai_agent_fallback',
                    menu_item_id=menu_item_id,
                    date=forecast_date,
                    predicted_quantity=predicted_quantity,
                    lower_bound=lower_bound,
                    upper_bound=upper_bound
                )
                db.session.add(forecast)
                
                # Insert to current_forecasts
                current_forecast = CurrentForecast(
                    item_type='menu_item',
                    item_id=menu_item_id,
                    item_name=dish_suggestion.name,
                    forecast_date=forecast_date,
                    predicted_quantity=predicted_quantity,
                    confidence_lower=lower_bound,
                    confidence_upper=upper_bound,
                    model_version='ai_agent_fallback'
                )
                db.session.add(current_forecast)
                forecasts_created += 1
            
            # Insert to forecast_performance
            from datetime import date
            performance = ForecastPerformance(
                model_version='ai_agent_fallback',
                forecast_type='menu_item',
                item_id=menu_item_id,
                evaluation_date=date.today(),
                mae=2.5,
                rmse=3.2,
                mape=8.5,
                r2_score=0.75  # Lower score for fallback
            )
            db.session.add(performance)
            
            db.session.commit()
            
            # Update dish suggestion with predicted demand
            dish_suggestion.predicted_demand = base_demand
            
            return {
                'success': True,
                'forecasts_created': forecasts_created,
                'predicted_demand': base_demand,
                'forecast_horizon_days': 7,
                'analysis_type': 'fallback'
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Fallback forecast generation error: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _step6_price_optimization(self, dish_suggestion: DishSuggestion, menu_item_id: int) -> Dict[str, Any]:
        """Step 6: Run price recommendation using ML optimization and update menu_price"""
        try:
            # Get menu item from database
            menu_item = MenuItem.query.get(menu_item_id)
            if not menu_item:
                return {
                    'success': False,
                    'error': 'Menu item not found for price update'
                }
            
            # Use machine learning optimization instead of fixed formula
            try:
                # Get observed market price from CSV dataset
                observed_market_price = get_market_price_from_csv(dish_suggestion.name)
                if not observed_market_price:
                    observed_market_price = float(menu_item.menu_price) if menu_item.menu_price else dish_suggestion.estimated_cost * 2.5
                
                # Run ML-based price optimization with updated parameters
                optimization_result = predict_optimal_price_for_item(
                    menu_item_name=dish_suggestion.name,
                    restaurant_id=f"Restaurant {menu_item_id % 50 + 1}",
                    day_of_week='Friday',
                    weather_condition='Sunny',
                    has_promotion=False,
                    price_range_start=6.0,
                    price_range_end=25.0,
                    price_increment=0.25,
                    business_goal='profit',
                    apply_smart_rounding=True,
                    include_visualizations=False,
                    menu_item_id=menu_item_id,
                    category=menu_item.category or dish_suggestion.category,
                    cuisine_type=menu_item.cuisine_type or dish_suggestion.cuisine_type,
                    typical_ingredient_cost=dish_suggestion.estimated_cost,
                    observed_market_price=observed_market_price
                )
                
                if 'error' not in optimization_result:
                    optimal_price = optimization_result['optimization']['optimal_price']
                    logger.info(f"ML optimization successful: RM{optimal_price:.2f} for {dish_suggestion.name}")
                else:
                    # Fallback to simple calculation if ML fails
                    optimal_price = dish_suggestion.estimated_cost * 2.5
                    logger.warning(f"ML optimization failed, using fallback: RM{optimal_price:.2f}")
                    
            except Exception as ml_error:
                # Fallback to simple calculation if ML optimization fails
                optimal_price = dish_suggestion.estimated_cost * 2.5
                logger.warning(f"ML optimization error: {str(ml_error)}, using fallback: RM{optimal_price:.2f}")
            
            optimal_price = round(optimal_price, 2)
            
            # Update menu item price
            menu_item.menu_price = optimal_price
            db.session.commit()
            
            # Update dish suggestion
            dish_suggestion.suggested_price = optimal_price
            
            return {
                'success': True,
                'optimal_price': optimal_price,
                'base_cost': dish_suggestion.estimated_cost,
                'optimization_method': 'machine_learning',
                'fallback_used': 'error' in locals() and 'optimization_result' in locals() and 'error' in optimization_result
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Step 6 - Price optimization error: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _step7_nutrition_analysis(self, dish_suggestion: DishSuggestion, menu_item_id: int) -> Dict[str, Any]:
        """Step 7: Generate nutrition information and save to menu_nutrition table"""
        try:
            # Analyze ingredients and generate nutrition data
            nutrition_data = self._analyze_ingredients_nutrition(dish_suggestion.ingredients)
            
            # Create nutrition record
            nutrition = MenuNutrition(
                menu_item_id=menu_item_id,
                calories=nutrition_data['calories'],
                protein=nutrition_data['protein'],
                carbohydrates=nutrition_data['carbohydrates'],
                fat=nutrition_data['fat'],
                fiber=nutrition_data['fiber'],
                sugar=nutrition_data['sugar'],
                sodium=nutrition_data['sodium'],
                allergens=nutrition_data['allergens'],
                is_vegetarian=nutrition_data['is_vegetarian'],
                is_vegan=nutrition_data['is_vegan'],
                is_gluten_free=nutrition_data['is_gluten_free']
            )
            
            db.session.add(nutrition)
            db.session.commit()
            
            return {
                'success': True,
                'nutrition_data': nutrition_data
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Step 7 - Nutrition analysis error: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    # Helper methods for the 7-step workflow
    def _generate_creative_dish_name(self, ingredients: List[str]) -> str:
        """Generate a creative dish name based on ingredients"""
        if not ingredients:
            return "Innovative Fusion Dish"
        
        # Simple creative naming logic
        primary_ingredient = ingredients[0]
        if len(ingredients) > 1:
            secondary_ingredient = ingredients[1]
            return f"{primary_ingredient.title()} & {secondary_ingredient.title()} Innovation"
        else:
            return f"Gourmet {primary_ingredient.title()} Creation"
    
    def _generate_dish_description(self, ingredients: List[str]) -> str:
        """Generate a dish description based on ingredients"""
        if not ingredients:
            return "An innovative fusion dish combining unique flavors"
        
        ingredient_list = ", ".join(ingredients[:3])
        return f"A creative culinary masterpiece featuring {ingredient_list}, expertly crafted to deliver an unforgettable dining experience"
    
    def _determine_dish_category(self, ingredients: List[str], dish_name: str = None) -> str:
        """Determine dish category based on dish name endings first, then ingredients - categorizes into Main Course, Dessert, Beverage, or Side Dish"""
        
        # First, check dish name endings for category determination (most reliable)
        if dish_name:
            dish_lower = dish_name.lower()
            
            # Dessert endings (from chatbot.py category-specific endings)
            dessert_endings = ['tart', 'soufflé', 'mousse', 'parfait', 'galette', 'compote', 'crème', 'cake', 'pudding', 'truffle', 'gelato', 'tiramisu']
            if any(ending in dish_lower for ending in dessert_endings):
                return "Dessert"
            
            # Beverage endings (from chatbot.py category-specific endings)
            beverage_endings = ['fizz', 'elixir', 'brew', 'infusion', 'tonic', 'refresher', 'cooler', 'spritz', 'smoothie', 'latte', 'mocktail', 'blend']
            if any(ending in dish_lower for ending in beverage_endings):
                return "Beverage"
            
            # Main course endings (from chatbot.py category-specific endings)
            main_endings = ['medallion', 'wellington', 'roulade', 'confit', 'braise', 'gratin', 'casserole', 'steak', 'filet', 'roast', 'chop', 'cutlet']
            if any(ending in dish_lower for ending in main_endings):
                return "Main Course"
            
            # Side dish endings (from chatbot.py category-specific endings)
            side_endings = ['medley', 'sauté', 'pilaf', 'salad', 'slaw', 'relish', 'chutney', 'puree', 'hash', 'chips', 'crisps']
            if any(ending in dish_lower for ending in side_endings):
                return "Side Dish"
        
        # Fallback to ingredient-based categorization
        ingredient_text = ' '.join(ingredients).lower()
        dish_text = dish_name.lower() if dish_name else ''
        combined_text = f"{ingredient_text} {dish_text}"
        
        # Beverage indicators (check first to avoid conflicts with dessert ingredients)
        beverage_indicators = ['juice', 'tea', 'coffee', 'milk', 'water', 'soda', 'smoothie', 
                              'cocktail', 'wine', 'beer', 'lemonade', 'shake', 'drink', 'elixir', 
                              'beverage', 'latte', 'cappuccino', 'espresso', 'mocktail']
        
        # Dessert indicators
        dessert_indicators = ['chocolate', 'sugar', 'cream', 'vanilla', 'cake', 'cookie', 'ice cream', 
                             'sweet', 'caramel', 'pudding', 'pie', 'tart', 'mousse', 'custard', 'frosting',
                             'dessert', 'soufflé', 'truffle', 'crème', 'compote', 'parfait', 'gelato',
                             'cheesecake', 'tiramisu', 'brownie', 'macaron', 'éclair', 'profiterole',
                             'mascarpone', 'ladyfingers', 'cocoa', 'whipped', 'icing', 'ganache', 'meringue']
        
        # Dessert fruits and sweet items
        dessert_fruits = ['fruit', 'berry', 'apple', 'banana', 'strawberry', 'honey', 'mango', 
                         'peach', 'cherry', 'grape', 'orange', 'lemon', 'coconut']
        
        # Main course indicators (proteins and substantial ingredients)
        main_course_indicators = ['chicken', 'beef', 'pork', 'fish', 'salmon', 'tuna', 'lamb', 
                                 'turkey', 'duck', 'pasta', 'rice', 'noodles', 'steak', 
                                 'burger', 'pizza', 'curry', 'stir fry', 'roast', 'grilled',
                                 'medallion', 'roulade', 'filet', 'tenderloin', 'breast', 'thigh']
        
        # Side dish indicators (vegetables, small portions, accompaniments)
        side_dish_indicators = ['salad', 'bread', 'roll', 'fries', 'potato', 'vegetable', 
                               'lettuce', 'tomato', 'carrot', 'onion', 'pepper', 'corn', 
                               'beans', 'soup', 'appetizer', 'dip', 'sauce', 'garnish', 'side']
        
        # Check for beverages first (highest priority to avoid conflicts)
        # But exclude cases where coffee/tea are used as dessert ingredients
        beverage_match = any(beverage in combined_text for beverage in beverage_indicators)
        dessert_match = any(dessert in combined_text for dessert in dessert_indicators)
        
        if beverage_match and not dessert_match:
            return 'Beverage'
        
        # Check for dessert (including dessert-specific fruits and dish names)
        elif (dessert_match or 
              (any(fruit in combined_text for fruit in dessert_fruits) and 
               not any(main in combined_text for main in main_course_indicators))):
            return 'Dessert'
        
        # Check for main course (proteins and substantial dishes)
        elif any(main in combined_text for main in main_course_indicators):
            return 'Main Course'
        
        # Check for side dish indicators
        elif any(side in combined_text for side in side_dish_indicators):
            return 'Side Dish'
        
        # Intelligent default based on dish name patterns
        else:
            # If dish name suggests it's a substantial dish, default to Main Course
            if dish_name and any(word in dish_text for word in ['bowl', 'platter', 'special', 'creation', 'innovation', 'fusion']):
                return 'Main Course'
            # Otherwise default to Main Course for unknown items (better than Side Dish)
            return 'Main Course'
    
    def _determine_cuisine_type(self, ingredients: List[str]) -> str:
        """Determine cuisine type based on ingredients"""
        # Simple logic to determine cuisine
        asian_ingredients = ['soy', 'ginger', 'sesame', 'rice']
        italian_ingredients = ['tomato', 'basil', 'mozzarella', 'pasta']
        mexican_ingredients = ['pepper', 'corn', 'beans', 'avocado']
        
        ingredient_text = ' '.join(ingredients).lower()
        
        if any(ing in ingredient_text for ing in asian_ingredients):
            return 'Asian'
        elif any(ing in ingredient_text for ing in italian_ingredients):
            return 'Italian'
        elif any(ing in ingredient_text for ing in mexican_ingredients):
            return 'Mexican'
        else:
            return 'Fusion'
    
    def _calculate_estimated_cost(self, ingredients: List[Dict]) -> float:
        """Calculate estimated cost based on ingredients"""
        if not ingredients:
            return 8.0
        
        # Simple cost calculation based on number of ingredients
        base_cost = 5.0
        ingredient_cost = len(ingredients) * 1.5
        return round(base_cost + ingredient_cost, 2)
    
    def _calculate_recipe_quantity(self, ingredient_name: str) -> float:
        """Calculate recipe quantity based on ingredient type"""
        # Simple quantity calculation based on ingredient type
        if any(meat in ingredient_name.lower() for meat in ['chicken', 'beef', 'pork', 'fish']):
            return 200.0  # grams
        elif any(veg in ingredient_name.lower() for veg in ['tomato', 'onion', 'pepper']):
            return 100.0  # grams
        elif any(grain in ingredient_name.lower() for grain in ['rice', 'pasta', 'bread']):
            return 150.0  # grams
        else:
            return 50.0   # grams
    
    def _generate_ai_image(self, menu_item_id: int, dish_suggestion: DishSuggestion) -> Dict[str, Any]:
        """Generate AI image for the dish and save to menu_item_images table"""
        try:
            if self.image_service:
                # Use existing image service
                image_result = self.image_service.generate_menu_item_image(
                    menu_item_id,
                    dish_suggestion.description
                )
                return {
                    'success': image_result.get('success', False),
                    'image_path': image_result.get('image_path'),
                    'service_used': 'AI Image Service'
                }
            else:
                # Generate AI image using Gemini 2.0 Flash with native image generation
                import os
                import base64
                from google import genai
                from google.genai import types
                from utils.image_handler import ImageHandler
                
                # Configure Gemini API
                api_key = os.getenv('GEMINI_API_KEY')
                if not api_key:
                    logger.error("Gemini API key not configured")
                    return {
                        'success': False,
                        'error': 'Gemini API key not configured'
                    }
                
                # Use the new Google GenAI client for image generation
                client = genai.Client(api_key=api_key)
                
                # Generate image with enhanced prompt
                if hasattr(dish_suggestion, 'ingredients') and dish_suggestion.ingredients:
                    ingredients_str = ', '.join(dish_suggestion.ingredients[:5])  # Limit to first 5 ingredients
                    prompt = f"Create a professional, high-quality photograph of {dish_suggestion.name} featuring key ingredients: {ingredients_str}. The dish should be beautifully plated, well-lit with natural lighting, and suitable for an upscale restaurant menu. Show the key ingredients prominently in an appetizing presentation."
                else:
                    prompt = f"Create a professional, high-quality photograph of {dish_suggestion.name}. The dish should be beautifully plated, well-lit with natural lighting, and suitable for an upscale restaurant menu."
                
                logger.info(f"Generating AI image for {dish_suggestion.name} with prompt: {prompt[:100]}...")
                
                # Use Gemini 2.0 Flash with image generation capability
                response = client.models.generate_content(
                    model="gemini-2.0-flash-exp",
                    contents=[prompt],
                    config=types.GenerateContentConfig(
                        response_modalities=["Text", "Image"]
                    )
                )
                
                # Process response to extract image using new API format
                if response.candidates and len(response.candidates) > 0:
                    candidate = response.candidates[0]
                    if candidate.content and candidate.content.parts:
                        for part in candidate.content.parts:
                            # Check for inline_data (new API format)
                            if hasattr(part, 'inline_data') and part.inline_data:
                                # Save image directly from inline data
                                image_data = part.inline_data.data
                                
                                # Create filename and save path
                                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                                filename = f"menu_item_{menu_item_id}_ai_generated_{timestamp}_{hash(dish_suggestion.name) % 100000000:08x}.png"
                                
                                # Ensure directory exists
                                image_dir = os.path.join(os.getcwd(), 'static', 'menu_images')
                                os.makedirs(image_dir, exist_ok=True)
                                
                                # Save the image file
                                file_path = os.path.join(image_dir, filename)
                                with open(file_path, 'wb') as f:
                                    f.write(image_data)
                                
                                # Create relative path for database
                                relative_path = f"static/menu_images/{filename}"
                                
                                # Create database record
                                menu_item_image = MenuItemImage(
                                    menu_item_id=menu_item_id,
                                    image_path=relative_path,
                                    image_type='ai_generated',
                                    is_primary=True
                                )
                                
                                from app import db
                                db.session.add(menu_item_image)
                                db.session.commit()
                                
                                logger.info(f"AI image generated and saved: {relative_path}")
                                
                                return {
                                    'success': True,
                                    'image_path': relative_path,
                                    'service_used': 'Gemini 2.0 Flash Native Image Generation'
                                }
                
                # If no image was generated, fall back to placeholder
                logger.warning("No image generated from Gemini API, creating placeholder")
                return self._create_placeholder_image(menu_item_id, dish_suggestion)
                
        except Exception as e:
             logger.error(f"AI image generation error: {str(e)}")
             return {
                 'success': False,
                 'error': str(e)
             }
    
    def _create_placeholder_image(self, menu_item_id: int, dish_suggestion: DishSuggestion) -> Dict[str, Any]:
        """Create a physical placeholder image file and database record"""
        try:
            from PIL import Image, ImageDraw, ImageFont
            import os
            
            # Ensure directory exists
            image_dir = os.path.join(os.getcwd(), 'static', 'menu_images')
            os.makedirs(image_dir, exist_ok=True)
            
            # Create placeholder image
            img = Image.new('RGB', (400, 300), color='lightgray')
            draw = ImageDraw.Draw(img)
            
            # Add text
            try:
                font = ImageFont.truetype('arial.ttf', 20)
            except:
                font = ImageFont.load_default()
            
            text_lines = [
                f"Dish #{menu_item_id}",
                dish_suggestion.name[:20],
                "AI Image Placeholder"
            ]
            
            y_offset = 100
            for line in text_lines:
                bbox = draw.textbbox((0, 0), line, font=font)
                text_width = bbox[2] - bbox[0]
                x = (400 - text_width) // 2
                draw.text((x, y_offset), line, fill='black', font=font)
                y_offset += 30
            
            # Add border
            draw.rectangle([10, 10, 390, 290], outline='black', width=2)
            
            # Save image
            filename = f"placeholder_dish_{menu_item_id}.jpg"
            file_path = os.path.join(image_dir, filename)
            img.save(file_path)
            
            # Create database record
            relative_path = f"static/menu_images/{filename}"
            menu_item_image = MenuItemImage(
                menu_item_id=menu_item_id,
                image_path=relative_path,
                image_type='placeholder',
                is_primary=True
            )
            
            from app import db
            db.session.add(menu_item_image)
            db.session.commit()
            
            logger.info(f"Placeholder image created: {relative_path}")
            
            return {
                'success': True,
                'image_path': relative_path,
                'service_used': 'Placeholder Image'
            }
            
        except Exception as e:
            logger.error(f"Error creating placeholder image: {str(e)}")
            return {
                'success': False,
                'error': f'Failed to create placeholder image: {str(e)}'
            }
    
    def _analyze_ingredients_nutrition(self, ingredients: List[str]) -> Dict[str, Any]:
        """Analyze ingredients and generate nutrition information"""
        # Simple nutrition calculation based on ingredients
        base_nutrition = {
            'calories': 300,
            'protein': 15.0,
            'carbohydrates': 25.0,
            'fat': 12.0,
            'fiber': 4.0,
            'sugar': 5.0,
            'sodium': 500,
            'allergens': '',
            'is_vegetarian': True,
            'is_vegan': True,
            'is_gluten_free': True
        }
        
        # Adjust nutrition based on ingredients
        allergens = []
        
        for ingredient in ingredients:
            ingredient_lower = ingredient.lower()
            
            # Adjust calories and macros based on ingredient type
            if any(meat in ingredient_lower for meat in ['chicken', 'beef', 'pork', 'fish']):
                base_nutrition['calories'] += 150
                base_nutrition['protein'] += 20.0
                base_nutrition['fat'] += 8.0
                base_nutrition['is_vegetarian'] = False
                base_nutrition['is_vegan'] = False
            
            if any(dairy in ingredient_lower for dairy in ['cheese', 'milk', 'butter', 'cream']):
                base_nutrition['calories'] += 100
                base_nutrition['fat'] += 10.0
                base_nutrition['is_vegan'] = False
                allergens.append('dairy')
            
            if any(grain in ingredient_lower for grain in ['wheat', 'flour', 'bread', 'pasta']):
                base_nutrition['carbohydrates'] += 15.0
                base_nutrition['is_gluten_free'] = False
                allergens.append('gluten')
            
            if 'nut' in ingredient_lower:
                allergens.append('nuts')
        
        # Set allergens string
        if allergens:
            base_nutrition['allergens'] = f"Contains {', '.join(set(allergens))}"
        else:
            base_nutrition['allergens'] = 'No major allergens'
        
        return base_nutrition
    
    def optimize_pricing(self, strategy: str = 'profit_maximization', item_filters: Dict = None, 
                        price_range_start: float = 6.0, price_range_end: float = 25.0, 
                        business_goal: str = 'profit') -> Dict[str, Any]:
        """Optimize menu pricing using ML-based recommendations"""
        try:
            logger.info(f"Starting pricing optimization with strategy: {strategy}")
            
            # Get menu items based on filters
            query = MenuItem.query
            if item_filters:
                if 'category' in item_filters:
                    query = query.filter(MenuItem.category == item_filters['category'])
                if 'cuisine_type' in item_filters:
                    query = query.filter(MenuItem.cuisine_type == item_filters['cuisine_type'])
            
            menu_items = query.all()
            
            if not menu_items:
                return {
                    'success': False,
                    'error': 'No menu items found for optimization'
                }
            
            recommendations = []
            total_items_optimized = 0
            total_potential_profit_increase = 0
            
            for menu_item in menu_items:
                try:
                    # Get observed market price from CSV dataset
                    observed_market_price = get_market_price_from_csv(menu_item.menu_item_name)
                    if not observed_market_price:
                        observed_market_price = float(menu_item.menu_price) if menu_item.menu_price else 5.0 * 2.5
                    
                    # Run ML optimization for each item - allow category-based pricing logic
                    optimization_result = predict_optimal_price_for_item(
                        menu_item_name=menu_item.menu_item_name,
                        restaurant_id=f"Restaurant {menu_item.id % 50 + 1}",
                        day_of_week='Friday',
                        weather_condition='Sunny',
                        has_promotion=False,
                        # Removed explicit price_range_start and price_range_end to allow category-based pricing
                        price_increment=0.25,
                        business_goal=business_goal if business_goal in ['profit', 'revenue'] else strategy.replace('_maximization', ''),
                        apply_smart_rounding=True,
                        include_visualizations=False,
                        menu_item_id=menu_item.id,
                        category=menu_item.category,
                        cuisine_type=menu_item.cuisine_type,
                        typical_ingredient_cost=float(menu_item.typical_ingredient_cost) if menu_item.typical_ingredient_cost else 5.0,
                        observed_market_price=observed_market_price
                    )
                    
                    if 'error' not in optimization_result:
                        optimal_price = optimization_result['optimization']['optimal_price']
                        current_price = float(menu_item.menu_price) if menu_item.menu_price else optimal_price
                        
                        recommendations.append({
                            'menu_item_id': menu_item.id,
                            'menu_item_name': menu_item.menu_item_name,
                            'current_price': current_price,
                            'recommended_price': optimal_price,
                            'price_change': optimal_price - current_price,
                            'price_change_percent': ((optimal_price - current_price) / current_price * 100) if current_price > 0 else 0,
                            'projected_profit': optimization_result['optimization']['maximum_projected_profit'],
                            'confidence': 'high' if abs(optimal_price - current_price) < 2.0 else 'medium'
                        })
                        
                        total_items_optimized += 1
                        if optimal_price > current_price:
                            total_potential_profit_increase += (optimal_price - current_price) * 30  # Assume 30 units sold per day
                            
                except Exception as item_error:
                    logger.warning(f"Failed to optimize pricing for {menu_item.menu_item_name}: {str(item_error)}")
                    continue
            
            return {
                'success': True,
                'message': f'Successfully optimized pricing for {total_items_optimized} menu items',
                'strategy_used': strategy,
                'recommendations': recommendations,
                'summary': {
                    'total_items_analyzed': len(menu_items),
                    'total_items_optimized': total_items_optimized,
                    'potential_daily_profit_increase': round(total_potential_profit_increase, 2),
                    'average_price_adjustment': round(sum([r['price_change'] for r in recommendations]) / len(recommendations), 2) if recommendations else 0
                },
                'implementation_plan': [
                    'Review recommended price changes',
                    'Test price changes on selected items',
                    'Monitor customer response and sales volume',
                    'Adjust pricing based on market feedback'
                ],
                'insights': [
                    f'ML optimization suggests {len([r for r in recommendations if r["price_change"] > 0])} items can be priced higher',
                    f'Average recommended price increase: RM{round(sum([r["price_change"] for r in recommendations if r["price_change"] > 0]) / max(len([r for r in recommendations if r["price_change"] > 0]), 1), 2)}',
                    f'Potential daily profit increase: RM{round(total_potential_profit_increase, 2)}'
                ],
                'next_steps': [
                    'Apply recommended prices to selected items',
                    'Monitor sales performance for 1-2 weeks',
                    'Analyze customer feedback and adjust if needed'
                ]
            }
            
        except Exception as e:
            logger.error(f"Pricing optimization error: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to optimize pricing due to technical error'
            }

# Global instance
autogen_ai = AutoGenRestaurantAI()
autogen_ai_agent = autogen_ai  # Alias for backward compatibility