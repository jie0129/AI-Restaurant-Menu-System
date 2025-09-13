import requests
import json
import time
from typing import Dict, List, Optional
from models.ingredient import Ingredient
from models.nutrition_metrics import NutritionMetrics
from models import db

class USDANutritionService:
    """
    Service for integrating with USDA FoodData Central API
    to fetch accurate nutrition data for ingredients.
    """
    
    def __init__(self, api_key: str = None):
        self.base_url = "https://api.nal.usda.gov/fdc/v1"
        self.api_key = api_key or "DEMO_KEY"  # Replace with actual API key
        
        # Cooking method adjustment factors
        self.cooking_adjustments = {
            'raw': {'calories': 1.0, 'protein': 1.0, 'carbs': 1.0, 'fat': 1.0, 'fiber': 1.0, 'vitamins': 1.0},
            'boiled': {'calories': 0.95, 'protein': 0.98, 'carbs': 1.0, 'fat': 1.0, 'fiber': 0.95, 'vitamins': 0.85},
            'steamed': {'calories': 0.98, 'protein': 0.99, 'carbs': 1.0, 'fat': 1.0, 'fiber': 0.98, 'vitamins': 0.92},
            'grilled': {'calories': 0.92, 'protein': 0.95, 'carbs': 1.0, 'fat': 0.85, 'fiber': 1.0, 'vitamins': 0.88},
            'fried': {'calories': 1.25, 'protein': 0.98, 'carbs': 1.0, 'fat': 1.8, 'fiber': 1.0, 'vitamins': 0.75},
            'baked': {'calories': 0.95, 'protein': 0.97, 'carbs': 1.0, 'fat': 1.0, 'fiber': 0.98, 'vitamins': 0.90},
            'roasted': {'calories': 0.93, 'protein': 0.96, 'carbs': 1.0, 'fat': 0.90, 'fiber': 1.0, 'vitamins': 0.87}
        }
    
    def search_food(self, query: str, page_size: int = 10, track_metrics: bool = False, session_id: str = None) -> tuple[List[Dict], Dict]:
        """
        Search for foods in USDA database by name.
        """
        url = f"{self.base_url}/foods/search"
        params = {
            'query': query,
            'pageSize': page_size,
            'api_key': self.api_key
        }
        
        start_time = time.time() * 1000  # Convert to milliseconds
        metrics_data = {
            'usda_api_called': True,
            'usda_data_found': False,
            # usda_response_time_ms removed (optimized)
            'session_id': session_id
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            foods = data.get('foods', [])
            
            # Update metrics
            end_time = time.time() * 1000
            # usda_response_time_ms removed (optimized)
            metrics_data['usda_data_found'] = len(foods) > 0
            
            if track_metrics:
                return foods, metrics_data
            return foods, {}
        except requests.RequestException as e:
            print(f"Error searching USDA database: {e}")
            end_time = time.time() * 1000
            # usda_response_time_ms removed (optimized)
            metrics_data['analysis_success'] = False
            # error_message removed (optimized)
            
            if track_metrics:
                return [], metrics_data
            return [], {}
    
    def get_food_details(self, fdc_id: str) -> Optional[Dict]:
        """
        Get detailed nutrition information for a specific food by FDC ID.
        """
        url = f"{self.base_url}/food/{fdc_id}"
        params = {'api_key': self.api_key}
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error fetching food details: {e}")
            return None
    
    def extract_nutrients(self, food_data: Dict) -> Dict[str, float]:
        """
        Extract key nutrients from USDA food data and convert to per 100g values.
        """
        nutrients = {}
        nutrient_mapping = {
            '208': 'calories',      # Energy (kcal)
            '203': 'protein',       # Protein (g)
            '205': 'carbs',         # Carbohydrate (g)
            '204': 'fat',           # Total lipid (fat) (g)
            '291': 'fiber',         # Fiber, total dietary (g)
            '269': 'sugar',         # Sugars, total (g)
            '307': 'sodium'         # Sodium (mg)
        }
        
        food_nutrients = food_data.get('foodNutrients', [])
        
        for nutrient in food_nutrients:
            nutrient_id = str(nutrient.get('nutrient', {}).get('id', ''))
            if nutrient_id in nutrient_mapping:
                value = nutrient.get('amount', 0)
                nutrients[nutrient_mapping[nutrient_id]] = float(value)
        
        return nutrients
    
    def apply_cooking_adjustments(self, nutrients: Dict[str, float], cooking_method: str) -> Dict[str, float]:
        """
        Apply cooking method adjustments to nutrient values.
        """
        if cooking_method not in self.cooking_adjustments:
            return nutrients
        
        adjustments = self.cooking_adjustments[cooking_method]
        adjusted_nutrients = {}
        
        # Map nutrients to adjustment categories
        nutrient_categories = {
            'calories': 'calories',
            'protein': 'protein',
            'carbs': 'carbs',
            'fat': 'fat',
            'fiber': 'fiber',
            'sugar': 'carbs',  # Sugar follows carbs adjustment
            'sodium': 'vitamins'  # Sodium follows vitamins (water-soluble) adjustment
        }
        
        for nutrient, value in nutrients.items():
            category = nutrient_categories.get(nutrient, 'calories')
            adjustment_factor = adjustments.get(category, 1.0)
            adjusted_nutrients[nutrient] = value * adjustment_factor
        
        return adjusted_nutrients

    def get_nutrition_data(self, ingredient_name: str) -> Optional[Dict]:
        """
        Get nutrition data for an ingredient by name
        
        Args:
            ingredient_name (str): Name of the ingredient
            
        Returns:
            Dict: Nutrition data with nutrients key containing nutrition values
        """
        try:
            # Search for the ingredient
            search_results, _ = self.search_food(ingredient_name, page_size=1)
            
            if not search_results:
                return None
                
            # Get the first result
            best_match = search_results[0]
            fdc_id = str(best_match.get('fdcId', ''))
            
            # Get detailed nutrition data
            food_details = self.get_food_details(fdc_id)
            if not food_details:
                return None
                
            # Extract nutrients
            nutrients = self.extract_nutrients(food_details)
            
            return {
                'nutrients': nutrients,
                'fdc_id': fdc_id,
                'description': best_match.get('description', ingredient_name)
            }
            
        except Exception as e:
            print(f"Error getting nutrition data for {ingredient_name}: {e}")
            return None

    def update_ingredient_nutrition(self, ingredient_id: int, force_update: bool = False, 
                                  track_metrics: bool = False, session_id: str = None) -> tuple[bool, Dict]:
        """
        Update nutrition data for an ingredient from USDA database.
        """
        ingredient = Ingredient.query.get(ingredient_id)
        if not ingredient:
            return False
        
        # Skip if already has USDA data and not forcing update
        if ingredient.usda_fdc_id and not force_update:
            return True
        
        # Initialize metrics tracking
        start_time = time.time() * 1000
        metrics_data = {
            'session_id': session_id,
            'usda_api_called': True,
            # cooking_method_applied removed (optimized)
            'cooking_method': ingredient.cooking_method,
            'analysis_success': True
        }
        
        # Search for the ingredient in USDA database
        if track_metrics:
            search_results, search_metrics = self.search_food(ingredient.name, track_metrics=True, session_id=session_id)
            metrics_data.update(search_metrics)
        else:
            search_results, _ = self.search_food(ingredient.name)
            
        if not search_results:
            print(f"No USDA data found for ingredient: {ingredient.name}")
            metrics_data['analysis_success'] = False
            # error_message removed (optimized)
            if track_metrics:
                return False, metrics_data
            return False, {}
        
        # Use the first result (most relevant)
        best_match = search_results[0]
        fdc_id = str(best_match.get('fdcId', ''))
        
        # Get detailed nutrition data
        food_details = self.get_food_details(fdc_id)
        if not food_details:
            metrics_data['analysis_success'] = False
            # error_message removed (optimized)
            if track_metrics:
                return False, metrics_data
            return False, {}
        
        # Extract nutrients
        nutrients = self.extract_nutrients(food_details)
        
        # Apply cooking method adjustments
        cooking_method = ingredient.cooking_method or 'raw'
        adjusted_nutrients = self.apply_cooking_adjustments(nutrients, cooking_method)
        
        # Update metrics with cooking method info
        if cooking_method != 'raw':
            metrics_data['cooking_adjustment_applied'] = True
            # Calculate average retention factor
            retention_factors = list(self.cooking_adjustments.get(cooking_method, {}).values())
            if retention_factors:
                metrics_data['nutrient_retention_factor'] = sum(retention_factors) / len(retention_factors)
        
        # Update ingredient with nutrition data
        ingredient.usda_fdc_id = fdc_id
        ingredient.calories_per_100g = adjusted_nutrients.get('calories')
        ingredient.protein_per_100g = adjusted_nutrients.get('protein')
        ingredient.carbs_per_100g = adjusted_nutrients.get('carbs')
        ingredient.fat_per_100g = adjusted_nutrients.get('fat')
        ingredient.fiber_per_100g = adjusted_nutrients.get('fiber')
        ingredient.sugar_per_100g = adjusted_nutrients.get('sugar')
        ingredient.sodium_per_100g = adjusted_nutrients.get('sodium')
        
        try:
            db.session.commit()
            print(f"Updated nutrition data for ingredient: {ingredient.name}")
            
            # Calculate completeness score
            nutrient_count = sum(1 for v in adjusted_nutrients.values() if v is not None and v > 0)
            metrics_data['nutrition_completeness_score'] = nutrient_count / 7.0  # 7 main nutrients tracked
            # usda_food_code removed (optimized)
            
            # Calculate total processing time
            end_time = time.time() * 1000
            metrics_data['total_processing_time_ms'] = int(end_time - start_time)
            
            if track_metrics:
                return True, metrics_data
            return True, {}
        except Exception as e:
            db.session.rollback()
            print(f"Error updating ingredient nutrition: {e}")
            metrics_data['analysis_success'] = False
            # error_message removed (optimized)
            
            if track_metrics:
                return False, metrics_data
            return False, {}
    
    def calculate_recipe_nutrition(self, recipe_data: List[Dict], serving_size: str = "1 serving", 
                                 track_metrics: bool = False, session_id: str = None, 
                                 menu_item_id: int = None) -> tuple[Dict[str, float], Dict]:
        """
        Calculate total nutrition for a recipe based on ingredient quantities.
        recipe_data format: [{'ingredient_id': int, 'quantity_per_unit': float}, ...]
        """
        total_nutrition = {
            'calories': 0,
            'protein': 0,
            'carbs': 0,
            'fat': 0,
            'fiber': 0,
            'sugar': 0,
            'sodium': 0
        }
        
        for recipe_item in recipe_data:
            ingredient = Ingredient.query.get(recipe_item['ingredient_id'])
            if not ingredient:
                continue
            
            quantity_g = float(recipe_item['quantity_per_unit'])  # Assuming quantity is in grams
            
            # Calculate nutrition contribution (per 100g * quantity / 100)
            multiplier = quantity_g / 100.0
            
            if ingredient.calories_per_100g:
                total_nutrition['calories'] += float(ingredient.calories_per_100g) * multiplier
            if ingredient.protein_per_100g:
                total_nutrition['protein'] += float(ingredient.protein_per_100g) * multiplier
            if ingredient.carbs_per_100g:
                total_nutrition['carbs'] += float(ingredient.carbs_per_100g) * multiplier
            if ingredient.fat_per_100g:
                total_nutrition['fat'] += float(ingredient.fat_per_100g) * multiplier
            if ingredient.fiber_per_100g:
                total_nutrition['fiber'] += float(ingredient.fiber_per_100g) * multiplier
            if ingredient.sugar_per_100g:
                total_nutrition['sugar'] += float(ingredient.sugar_per_100g) * multiplier
            if ingredient.sodium_per_100g:
                total_nutrition['sodium'] += float(ingredient.sodium_per_100g) * multiplier
        
        # Calculate metrics if tracking
        metrics_data = {}
        if track_metrics:
            metrics_data = {
                'session_id': session_id,
                'menu_item_id': menu_item_id,
                'recipe_data_available': True,
                'ingredient_count': len(recipe_data),
                # analysis_type and analysis_accuracy_rating removed (optimized)
                'analysis_success': True
            }
            
            # Calculate nutrition completeness score
            non_zero_nutrients = sum(1 for v in total_nutrition.values() if v > 0)
            metrics_data['nutrition_completeness_score'] = non_zero_nutrients / len(total_nutrition)
        
        if track_metrics:
            return total_nutrition, metrics_data
        return total_nutrition, {}
    
    def adjust_nutrition_for_serving_size(self, nutrition: Dict[str, float], 
                                        current_serving: str, target_serving: str,
                                        track_metrics: bool = False) -> tuple[Dict[str, float], Dict]:
        """
        Adjust nutrition values based on serving size changes.
        This is a simplified implementation - in practice, you'd need more sophisticated
        parsing of serving size strings.
        """
        # Simple multiplier calculation (this would need to be more sophisticated)
        # For now, assume serving sizes are in grams or simple multipliers
        try:
            if 'g' in current_serving and 'g' in target_serving:
                current_g = float(current_serving.replace('g', '').strip())
                target_g = float(target_serving.replace('g', '').strip())
                multiplier = target_g / current_g
            elif current_serving == target_serving:
                multiplier = 1.0
            else:
                # Default to 1:1 if we can't parse
                multiplier = 1.0
            
            adjusted_nutrition = {}
            for key, value in nutrition.items():
                adjusted_nutrition[key] = value * multiplier
            
            # Track serving size adjustment metrics
            metrics_data = {}
            if track_metrics:
                metrics_data = {
                    # serving_size_adjusted removed (optimized)
                    'original_serving_size': current_serving,
                    'adjusted_serving_size': target_serving,
                    'serving_adjustment_factor': multiplier
                }
            
            if track_metrics:
                return adjusted_nutrition, metrics_data
            return adjusted_nutrition, {}
        except:
            metrics_data = {}
            if track_metrics:
                metrics_data = {
                    # serving_size_adjusted removed (optimized)
                    'original_serving_size': current_serving,
                    'adjusted_serving_size': target_serving,
                    'serving_adjustment_factor': 1.0
                }
                return nutrition, metrics_data
            return nutrition, {}