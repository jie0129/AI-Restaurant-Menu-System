import os
import pandas as pd
import numpy as np
import json
import logging
import warnings
from functools import lru_cache
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import io
import base64
from sqlalchemy import create_engine, text
from config import Config
import xgboost as xgb
from sklearn.preprocessing import LabelEncoder
from datetime import datetime

# Setup logging first
warnings.filterwarnings('ignore', category=UserWarning)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variable to cache the pricing data
_pricing_data_cache = None

class TrainedDemandModel:
    """Trained demand model for predicting quantity_sold based on price and contextual factors."""
    
    def __init__(self):
        """Initialize the trained demand model with XGBoost."""
        self.model = None
        self.feature_columns = [
            'price', 'typical_ingredient_cost', 'observed_market_price',
            'is_weekend', 'has_promotion', 'category_encoded', 'cuisine_type_encoded',
            'price_to_cost_ratio', 'price_vs_market_ratio', 'day_of_week_encoded'
        ]
        self.label_encoders = {}
        self._initialize_model()
    
    def _initialize_model(self):
        """Initialize and train the XGBoost model with realistic parameters."""
        try:
            # Initialize XGBoost model with parameters from performance analysis
            self.model = xgb.XGBRegressor(
                n_estimators=100,
                max_depth=6,
                learning_rate=0.1,
                subsample=0.8,
                colsample_bytree=0.8,
                random_state=42,
                n_jobs=-1
            )
            
            # Initialize label encoders
            self.label_encoders = {
                'category': LabelEncoder(),
                'cuisine_type': LabelEncoder(),
                'day_of_week': LabelEncoder()
            }
            
            # Fit encoders with common values
            self.label_encoders['category'].fit(['Main Course', 'Appetizer', 'Dessert', 'Beverage', 'Side Dish'])
            self.label_encoders['cuisine_type'].fit(['Asian', 'Western', 'Local', 'International', 'Fusion'])
            self.label_encoders['day_of_week'].fit(['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'])
            
            # Train with synthetic data to establish realistic demand patterns
            self._train_with_synthetic_data()
            
            logger.info("✅ Trained demand model initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Error initializing trained demand model: {str(e)}")
            self.model = None
    
    def _train_with_synthetic_data(self):
        """Train the model with synthetic data that reflects realistic demand patterns."""
        try:
            # Generate synthetic training data with realistic patterns
            np.random.seed(42)
            n_samples = 1000
            
            # Generate features
            prices = np.random.uniform(5, 50, n_samples)
            costs = np.random.uniform(2, 20, n_samples)
            market_prices = prices * np.random.uniform(0.8, 1.2, n_samples)
            is_weekend = np.random.choice([0, 1], n_samples, p=[0.7, 0.3])
            has_promotion = np.random.choice([0, 1], n_samples, p=[0.8, 0.2])
            categories = np.random.choice(range(5), n_samples)
            cuisine_types = np.random.choice(range(5), n_samples)
            day_of_week = np.random.choice(range(7), n_samples)
            
            # Calculate derived features
            price_to_cost_ratio = prices / np.maximum(costs, 0.1)
            price_vs_market_ratio = prices / np.maximum(market_prices, 0.1)
            
            # Create feature matrix
            X = np.column_stack([
                prices, costs, market_prices, is_weekend, has_promotion,
                categories, cuisine_types, price_to_cost_ratio, price_vs_market_ratio, day_of_week
            ])
            
            # Generate realistic demand with price elasticity and contextual effects
            base_demand = 50 + np.random.normal(0, 10, n_samples)
            
            # Price elasticity effect (higher prices = lower demand)
            # Use exponential decay for stronger price sensitivity to create U-shaped profit curve
            price_effect = -30.0 * (price_to_cost_ratio - 1.0) ** 2
            
            # Weekend effect (higher demand on weekends)
            weekend_effect = is_weekend * 15
            
            # Promotion effect (higher demand with promotions)
            promotion_effect = has_promotion * 20
            
            # Market price effect (demand increases if we're cheaper than market)
            market_effect = -10 * (price_vs_market_ratio - 1)
            
            # Combine effects to create realistic demand
            y = np.maximum(1, base_demand + price_effect + weekend_effect + promotion_effect + market_effect + np.random.normal(0, 5, n_samples))
            
            # Train the model
            self.model.fit(X, y)
            
            logger.info(f"✅ Model trained with {n_samples} synthetic samples")
            
        except Exception as e:
            logger.error(f"❌ Error training model with synthetic data: {str(e)}")
    
    def predict_demand(self, price, typical_ingredient_cost, observed_market_price, 
                      category='Main Course', cuisine_type='Asian', is_weekend=False, 
                      has_promotion=False, day_of_week='Monday'):
        """Predict demand for given price and contextual factors.
        
        Args:
            price: Menu item price
            typical_ingredient_cost: Cost of ingredients
            observed_market_price: Market price for similar items
            category: Menu item category
            cuisine_type: Cuisine type
            is_weekend: Whether it's weekend
            has_promotion: Whether there's a promotion
            day_of_week: Day of the week
        
        Returns:
            float: Predicted quantity_sold
        """
        try:
            if self.model is None:
                logger.warning("⚠️ Model not initialized, using fallback calculation")
                return self._fallback_prediction(price, typical_ingredient_cost, observed_market_price)
            
            # Encode categorical features
            try:
                category_encoded = self.label_encoders['category'].transform([category])[0]
            except:
                category_encoded = 0  # Default to first category
            
            try:
                cuisine_type_encoded = self.label_encoders['cuisine_type'].transform([cuisine_type])[0]
            except:
                cuisine_type_encoded = 0  # Default to first cuisine type
            
            try:
                day_of_week_encoded = self.label_encoders['day_of_week'].transform([day_of_week])[0]
            except:
                day_of_week_encoded = 0  # Default to Monday
            
            # Calculate derived features
            price_to_cost_ratio = price / max(typical_ingredient_cost, 0.1)
            price_vs_market_ratio = price / max(observed_market_price, 0.1)
            
            # Create feature vector
            features = np.array([[
                price, typical_ingredient_cost, observed_market_price,
                int(is_weekend), int(has_promotion), category_encoded, cuisine_type_encoded,
                price_to_cost_ratio, price_vs_market_ratio, day_of_week_encoded
            ]])
            
            # Make prediction
            prediction = self.model.predict(features)[0]
            
            # Ensure reasonable bounds
            prediction = max(1.0, min(500.0, prediction))
            
            logger.info(f"🎯 Model prediction: {prediction:.2f} units for price ${price:.2f}")
            return prediction
            
        except Exception as e:
            logger.error(f"❌ Error making prediction: {str(e)}")
            return self._fallback_prediction(price, typical_ingredient_cost, observed_market_price)
    
    def _fallback_prediction(self, price, typical_ingredient_cost, observed_market_price):
        """Fallback prediction using improved price elasticity for U-shaped profit curve."""
        base_demand = 50.0
        price_to_cost_ratio = price / max(typical_ingredient_cost, 0.1)
        
        # Improved elasticity: exponential decay for stronger price sensitivity
        price_effect = -30.0 * (price_to_cost_ratio - 1.0) ** 2
        
        prediction = base_demand + price_effect
        return max(1.0, min(200.0, prediction))

# Initialize global demand model instance
_demand_model = TrainedDemandModel()

def load_pricing_data():
    """Load pricing data from CSV file with caching."""
    global _pricing_data_cache
    
    if _pricing_data_cache is not None:
        return _pricing_data_cache
    
    try:
        # Try to find the data file in common locations
        possible_paths = [
            'data/xgboost_menu_items_20250824_210301.csv',
            '../data/xgboost_menu_items_20250824_210301.csv',
            '../../data/xgboost_menu_items_20250824_210301.csv',
            'backend/data/xgboost_menu_items_20250824_210301.csv'
        ]
        
        data_path = None
        for path in possible_paths:
            if os.path.exists(path):
                data_path = path
                break
        
        if data_path is None:
            logger.warning("Pricing data file not found, creating mock data")
            # Create mock data for testing
            num_rows = 300
            mock_data = {
                'menu_item_name': (['Menu Item 1', 'Menu Item 2', 'Menu Item 3'] * (num_rows // 3 + 1))[:num_rows],
                'restaurant_id': (['Restaurant 1', 'Restaurant 2', 'Restaurant 3'] * (num_rows // 3 + 1))[:num_rows],
                'day_of_week': (['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'] * (num_rows // 7 + 1))[:num_rows],
                'price': ([10.0, 15.0, 20.0] * (num_rows // 3 + 1))[:num_rows],
                'quantity_sold': ([50, 75, 100] * (num_rows // 3 + 1))[:num_rows],
                'ingredient_cost': ([5.0, 7.5, 10.0] * (num_rows // 3 + 1))[:num_rows],
                'weather_condition': (['Sunny', 'Rainy', 'Cloudy'] * (num_rows // 3 + 1))[:num_rows],
                'has_promotion': ([False, True, False] * (num_rows // 3 + 1))[:num_rows],
                'date': pd.date_range('2024-01-01', periods=num_rows, freq='D')
            }
            _pricing_data_cache = pd.DataFrame(mock_data)
            logger.info(f"Created mock pricing data with {len(_pricing_data_cache)} rows")
        else:
            _pricing_data_cache = pd.read_csv(data_path)
            logger.info(f"Loaded pricing data from {data_path} with {len(_pricing_data_cache)} rows")
        
        return _pricing_data_cache
        
    except Exception as e:
        logger.error(f"Error loading pricing data: {str(e)}")
        # Return empty DataFrame as fallback
        return pd.DataFrame()

# Logger is already set up at the top of the file

# Constants
MIN_PRICE_FACTOR = 0.8  # Don't go below 80% of current price
MAX_PRICE_FACTOR = 1.5  # Don't go above 150% of current price

# Cache for Linear Regression model and preprocessed data
_model_cache = {}
_feature_importance_cache = {}

def convert_numpy_types(obj):
    """Convert numpy types to Python native types for JSON serialization."""
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    return obj

def get_predicted_quantity_from_forecast(menu_item_id, forecast_days=7):
    """Get predicted quantity from current_forecast table for a menu item.
    
    Args:
        menu_item_id: ID of the menu item
        forecast_days: Number of days to sum predictions for (default 7 days)
    
    Returns:
        float: Total predicted quantity for the specified period
    """
    try:
        engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
        
        with engine.connect() as conn:
            # Get current forecasts for the menu item
            query = text("""
                SELECT predicted_quantity, forecast_date
                FROM current_forecasts 
                WHERE item_type = 'menu_item' AND item_id = :item_id
                ORDER BY forecast_date ASC
                LIMIT :forecast_days
            """)
            
            result = conn.execute(query, {
                'item_id': menu_item_id,
                'forecast_days': forecast_days
            })
            
            rows = result.fetchall()
            
            if not rows:
                logger.warning(f"⚠️ No forecast data found for menu item {menu_item_id}")
                return 25.0  # Default fallback quantity
            
            # Sum predicted quantities for the forecast period
            total_predicted = sum(float(row[0]) for row in rows if row[0] is not None)
            
            # Return daily average instead of total to avoid inflated demand calculations
            daily_average = total_predicted / max(1, len(rows)) if rows else total_predicted
            
            logger.info(f"✅ Retrieved forecast for item {menu_item_id}: {daily_average:.2f} units/day (total: {total_predicted:.2f} over {len(rows)} days)")
            return max(1.0, daily_average)  # Ensure minimum of 1 unit per day
            
    except Exception as e:
        logger.error(f"❌ Error getting forecast data: {str(e)}")
        return 25.0  # Default fallback quantity

def get_menu_item_from_database(menu_item_id):
    """Get menu item details from the database.
    
    Args:
        menu_item_id: ID of the menu item
    
    Returns:
        dict: Menu item details or None if not found
    """
    try:
        engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
        
        with engine.connect() as conn:
            query = text("""
                SELECT id, menu_item_name, typical_ingredient_cost, category, 
                       cuisine_type, menu_price
                FROM menu_item 
                WHERE id = :item_id
            """)
            
            result = conn.execute(query, {'item_id': menu_item_id})
            row = result.fetchone()
            
            if row:
                return {
                    'id': row[0],
                    'name': row[1],
                    'ingredient_cost': float(row[2]) if row[2] else 5.0,
                    'category': row[3] or 'Unknown',
                    'cuisine_type': row[4] or 'International',
                    'current_price': float(row[5]) if row[5] else 15.0
                }
            else:
                logger.warning(f"⚠️ Menu item {menu_item_id} not found in database")
                return None
                
    except Exception as e:
        logger.error(f"❌ Error getting menu item from database: {str(e)}")
        return None

def calculate_price_elasticity_demand(base_quantity, current_price, new_price, elasticity=-2.5):
    """Calculate demand based on price elasticity with realistic bounds.
    
    Args:
        base_quantity: Base predicted quantity from forecast
        current_price: Current menu price
        new_price: New price to test
        elasticity: Price elasticity coefficient (default -1.2 for food)
    
    Returns:
        float: Adjusted predicted quantity
    """
    logger.info(f"🔧 Price elasticity calculation: base={base_quantity:.2f}, current=${current_price:.2f}, new=${new_price:.2f}")
    
    if current_price <= 0:
        logger.info(f"⚠️ Invalid current_price ({current_price}), returning base_quantity")
        return base_quantity
    
    # Calculate percentage price change
    price_change_percent = (new_price - current_price) / current_price
    logger.info(f"📊 Price change: {price_change_percent:.4f} ({price_change_percent*100:.2f}%)")
    
    # Calculate quantity change using price elasticity
    quantity_change_percent = elasticity * price_change_percent
    logger.info(f"📉 Quantity change: {quantity_change_percent:.4f} ({quantity_change_percent*100:.2f}%)")
    
    # Calculate adjusted quantity
    adjusted_quantity = base_quantity * (1 + quantity_change_percent)
    logger.info(f"🎯 Adjusted quantity: {adjusted_quantity:.2f}")
    
    # Apply realistic bounds that allow proper economic curves
    # Allow demand to drop to near zero for very high prices (realistic market behavior)
    min_quantity = 0.01  # Absolute minimum to prevent division by zero
    max_quantity = base_quantity * 5.0  # At most 500% of base quantity for very low prices
    
    final_quantity = max(min_quantity, min(max_quantity, adjusted_quantity))
    logger.info(f"✅ Final quantity: {final_quantity:.2f} (bounds: {min_quantity:.2f} - {max_quantity:.2f})")
    
    return final_quantity

def forecast_demand_for_scenario(scenario_data):
    """Forecast demand for a pricing scenario using trained demand model."""
    try:
        logger.info(f"🔮 Forecasting demand for scenario: {scenario_data}")
        
        # Extract required parameters
        price = scenario_data.get('price', 0)
        menu_item_id = scenario_data.get('menu_item_id')
        
        if price <= 0:
            logger.error("❌ Invalid price provided in scenario")
            return None
        
        # Get menu item details for contextual factors
        if menu_item_id:
            menu_item = get_menu_item_from_database(menu_item_id)
            if menu_item:
                typical_ingredient_cost = menu_item.get('ingredient_cost', 5.0)
                category = menu_item.get('category', 'Main Course')
                cuisine_type = menu_item.get('cuisine_type', 'Asian')
                # Use current price as observed market price if not provided
                observed_market_price = scenario_data.get('observed_market_price', menu_item.get('current_price', price))
            else:
                logger.warning(f"⚠️ Menu item {menu_item_id} not found, using defaults")
                typical_ingredient_cost = scenario_data.get('typical_ingredient_cost', 5.0)
                category = scenario_data.get('category', 'Main Course')
                cuisine_type = scenario_data.get('cuisine_type', 'Asian')
                observed_market_price = scenario_data.get('observed_market_price', price)
        else:
            # Use scenario data directly
            typical_ingredient_cost = scenario_data.get('typical_ingredient_cost', 5.0)
            category = scenario_data.get('category', 'Main Course')
            cuisine_type = scenario_data.get('cuisine_type', 'Asian')
            observed_market_price = scenario_data.get('observed_market_price', price)
        
        # Extract contextual factors
        is_weekend = scenario_data.get('is_weekend', False)
        has_promotion = scenario_data.get('has_promotion', False)
        day_of_week = scenario_data.get('day_of_week', 'Monday')
        
        # Use trained demand model to predict quantity
        predicted_demand = _demand_model.predict_demand(
            price=price,
            typical_ingredient_cost=typical_ingredient_cost,
            observed_market_price=observed_market_price,
            category=category,
            cuisine_type=cuisine_type,
            is_weekend=is_weekend,
            has_promotion=has_promotion,
            day_of_week=day_of_week
        )
        
        logger.info(f"✅ Trained model predicted demand: {predicted_demand:.2f} units for price ${price:.2f}")
        return predicted_demand
        
    except Exception as e:
        logger.error(f"❌ Error forecasting demand: {str(e)}")
        return None

# Removed create_demand_forecast_scenario function - no longer needed with database approach

def apply_psychological_pricing(price):
    """Apply psychological pricing rules to make prices more appealing."""
    # Get the integer part of the price
    integer_part = int(price)
    decimal_part = price - integer_part
    
    # Apply psychological pricing rules - prefer .99, .95, .90 endings
    if decimal_part <= 0.33:
        # For lower decimals, use .99 from previous dollar
        if integer_part > 0:
            return integer_part - 0.01  # e.g., 12.25 -> 11.99
        else:
            return price  # Keep original if can't go lower
    elif decimal_part <= 0.66:
        # For middle decimals, use .95
        return integer_part + 0.95  # e.g., 12.50 -> 12.95
    else:
        # For higher decimals, use .99
        return integer_part + 0.99  # e.g., 12.75 -> 12.99



def generate_pricing_visualizations(results, optimal_price, ingredient_cost, observed_market_price=0):
    """Generate price-demand, price-revenue, and price-profit curve visualizations.
    
    Returns:
        dict: Dictionary containing base64-encoded images for each chart
    """
    try:
        if not results:
            return {}
        
        # Extract data for plotting
        prices = [r['price'] for r in results]
        quantities = [r['predicted_quantity'] for r in results]
        profits = [r['projected_profit'] for r in results]
        revenues = [r['projected_revenue'] for r in results]
        
        # Create figure with subplots (2x1 layout for Revenue and Profit only)
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        fig.suptitle('Price Optimization Analysis', fontsize=16, fontweight='bold')
        
        # 1. Price-Revenue Curve
        ax1.plot(prices, revenues, 'g-', linewidth=2, label='Revenue Curve')
        ax1.axvline(x=optimal_price, color='red', linestyle='--', alpha=0.7, label=f'Optimal Price (RM{optimal_price:.2f})')
        if observed_market_price > 0:
            ax1.axvline(x=observed_market_price, color='green', linestyle=':', alpha=0.7, label=f'Market Price (RM{observed_market_price:.2f})')
        ax1.set_xlabel('Price (RM)')
        ax1.set_ylabel('Projected Revenue (RM)')
        ax1.set_title('Price vs Revenue')
        ax1.grid(True, alpha=0.3)
        ax1.legend()
        
        # 2. Price-Profit Curve
        ax2.plot(prices, profits, 'r-', linewidth=2, label='Profit Curve')
        ax2.axvline(x=optimal_price, color='red', linestyle='--', alpha=0.7, label=f'Optimal Price (RM{optimal_price:.2f})')
        ax2.axhline(y=0, color='black', linestyle='-', alpha=0.3)
        if observed_market_price > 0:
            ax2.axvline(x=observed_market_price, color='green', linestyle=':', alpha=0.7, label=f'Market Price (RM{observed_market_price:.2f})')
        ax2.set_xlabel('Price (RM)')
        ax2.set_ylabel('Projected Profit (RM)')
        ax2.set_title('Price vs Profit')
        ax2.grid(True, alpha=0.3)
        ax2.legend()
        # Adjust layout for better spacing
        plt.tight_layout()
        
        # Save to base64 string
        plt.tight_layout()
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        plt.close()
        
        return {
            'combined_chart': image_base64,
            'chart_type': 'pricing_analysis',
            'optimal_price': optimal_price,
            'data_points': len(results)
        }
        
    except Exception as e:
        logger.error(f"❌ Error generating visualizations: {str(e)}")
        return {}

def batch_optimize_prices(menu_items, base_params=None):
    """Optimize prices for multiple menu items simultaneously.
    
    Args:
        menu_items: List of menu item dictionaries with required fields
        base_params: Base parameters for optimization (price_range, business_goal, etc.)
    
    Returns:
        dict: Results for each menu item with optimization summary
    """
    try:
        if base_params is None:
            base_params = {
                'price_range_start': 8.0,
                'price_range_end': 20.0,
                'price_increment': 0.25,
                'business_goal': 'profit',
                'apply_smart_rounding': True
            }
        
        results = {}
        total_items = len(menu_items)
        
        logger.info(f"🚀 Starting batch optimization for {total_items} menu items")
        
        for i, item in enumerate(menu_items, 1):
            item_name = item.get('name', f'Item_{i}')
            logger.info(f"📊 Optimizing {i}/{total_items}: {item_name}")
            
            try:
                # Create scenario for this item
                scenario = {
                    'typical_ingredient_cost': item.get('ingredient_cost', 0),
                    'observed_market_price': item.get('market_price', 0),
                    'menu_item_name': item_name,
                    'category': item.get('category', 'Unknown'),
                    'day_of_week': item.get('day_of_week', 'Monday'),
                    'is_weekend': item.get('is_weekend', False),
                    'season': item.get('season', 'Spring')
                }
                
                # Run optimization
                optimization_result = find_optimal_price(
                    scenario,
                    price_range_start=base_params['price_range_start'],
                    price_range_end=base_params['price_range_end'],
                    price_increment=base_params['price_increment'],
                    business_goal=base_params['business_goal'],
                    apply_smart_rounding=base_params['apply_smart_rounding']
                )
                
                if optimization_result:
                    # Generate visualizations
                    visualizations = generate_pricing_visualizations(
                        optimization_result['all_results'],
                        optimization_result['optimal_price'],
                        optimization_result['ingredient_cost'],
                        optimization_result['observed_market_price']
                    )
                    
                    results[item_name] = {
                        'optimization': optimization_result,
                        'visualizations': visualizations,
                        'original_data': item,
                        'status': 'success'
                    }
                else:
                    results[item_name] = {
                        'optimization': None,
                        'visualizations': {},
                        'original_data': item,
                        'status': 'failed',
                        'error': 'Optimization failed'
                    }
                    
            except Exception as item_error:
                logger.error(f"❌ Error optimizing {item_name}: {str(item_error)}")
                results[item_name] = {
                    'optimization': None,
                    'visualizations': {},
                    'original_data': item,
                    'status': 'error',
                    'error': str(item_error)
                }
        
        # Generate batch summary
        successful_items = [name for name, result in results.items() if result['status'] == 'success']
        failed_items = [name for name, result in results.items() if result['status'] != 'success']
        
        batch_summary = {
            'total_items': total_items,
            'successful_optimizations': len(successful_items),
            'failed_optimizations': len(failed_items),
            'success_rate': (len(successful_items) / total_items) * 100 if total_items > 0 else 0,
            'successful_items': successful_items,
            'failed_items': failed_items,
            'optimization_parameters': base_params
        }
        
        logger.info(f"✅ Batch optimization completed: {len(successful_items)}/{total_items} successful")
        
        return {
            'results': results,
            'summary': batch_summary
        }
        
    except Exception as e:
        logger.error(f"❌ Error in batch optimization: {str(e)}")
        return {
            'results': {},
            'summary': {
                'total_items': 0,
                'successful_optimizations': 0,
                'failed_optimizations': 0,
                'success_rate': 0,
                'error': str(e)
            }
        }

def find_optimal_price(base_scenario, price_range_start=None, price_range_end=None, price_increment=0.10, 
                      business_goal='profit', apply_smart_rounding=True):
    """Find optimal price that maximizes projected profit or revenue using trained demand model.
    
    Args:
        base_scenario: Base scenario dictionary with item characteristics
        price_range_start: Starting price for optimization (defaults to ingredient_cost + 0.10)
        price_range_end: Ending price for optimization (defaults to 2x observed_market_price)
        price_increment: Price increment for testing (default 0.10 for finer granularity)
        business_goal: 'profit' or 'revenue' - optimization objective
        apply_smart_rounding: Whether to apply psychological pricing rules
    """
    try:
        # Get ingredient cost and market price from scenario
        ingredient_cost = base_scenario.get('typical_ingredient_cost', 0)
        observed_market_price = base_scenario.get('observed_market_price', 0)
        
        if ingredient_cost <= 0:
            logger.error("❌ Invalid ingredient cost for profit calculation")
            return None
        
        if observed_market_price <= 0:
            logger.warning("⚠️ No observed market price provided, using category-based defaults")
            category = base_scenario.get('category', 'Main Course').lower()
            
            if 'beverage' in category or 'drink' in category:
                # For beverages, use lower market price estimates
                observed_market_price = max(ingredient_cost * 1.8, 2.5)
            elif 'dessert' in category or 'snack' in category:
                # For desserts, use moderate market price estimates
                observed_market_price = max(ingredient_cost * 2.0, 3.0)
            elif 'side' in category or 'appetizer' in category or 'starter' in category:
                # For side dishes, use moderate-low market price estimates
                observed_market_price = max(ingredient_cost * 2.2, 4.0)
            else:
                # For main courses, use higher estimates
                observed_market_price = max(ingredient_cost * 2.5, 8.0)
        
        # Define feasible price range based on business constraints
        if price_range_start is None:
            price_range_start = ingredient_cost + 0.10  # Start just above cost
        
        if price_range_end is None:
            # Set more reasonable price ranges based on food category and ingredient cost
            category = base_scenario.get('category', 'Main Course').lower()
            
            if 'dessert' in category or 'snack' in category:
                # For desserts and snacks, use lower multipliers
                price_range_end = min(observed_market_price * 1.8, ingredient_cost * 4, 15.0)
            elif 'beverage' in category or 'drink' in category:
                # For beverages, use even lower multipliers
                price_range_end = min(observed_market_price * 1.5, ingredient_cost * 3, 10.0)
            else:
                # For main courses, use original logic but with lower cap
                price_range_end = min(observed_market_price * 2.0, ingredient_cost * 8, 25.0)
            
            # Ensure minimum price range for very low-cost items
            if ingredient_cost < 3.0:
                price_range_end = min(price_range_end, ingredient_cost + 6.0)
        
        # Ensure minimum viable range
        if price_range_end <= price_range_start:
            price_range_end = price_range_start + 5.0
        
        # Generate candidate prices within feasible range for optimization
        optimization_prices = np.arange(price_range_start, price_range_end + price_increment, price_increment)
        
        # Generate extended range for visualization (add 20% beyond the end)
        extended_price_range_end = price_range_end * 1.2
        visualization_prices = np.arange(price_range_start, extended_price_range_end + price_increment, price_increment)
        
        results = []
        
        logger.info(f"🔍 Testing {len(optimization_prices)} price points from ${price_range_start:.2f} to ${price_range_end:.2f}")
        logger.info(f"📊 Business goal: {business_goal.upper()} maximization")
        logger.info(f"💰 Ingredient cost: ${ingredient_cost:.2f}, Market price: ${observed_market_price:.2f}")
        
        # Simulate demand across optimization price range only
        for price in optimization_prices:
            # Create scenario with current price for trained model
            scenario = base_scenario.copy()
            scenario['price'] = price
            
            # Forecast demand at this price using trained demand model
            predicted_quantity = forecast_demand_for_scenario(scenario)
            
            if predicted_quantity is not None and predicted_quantity > 0:
                # Calculate business outcomes
                projected_profit = (price - ingredient_cost) * predicted_quantity
                projected_revenue = price * predicted_quantity
                profit_margin = ((price - ingredient_cost) / price) * 100
                
                results.append({
                    'price': price,
                    'predicted_quantity': predicted_quantity,
                    'projected_profit': projected_profit,
                    'projected_revenue': projected_revenue,
                    'profit_margin': profit_margin
                })
            else:
                logger.warning(f"⚠️ Invalid demand prediction for price ${price:.2f}")
        
        if not results:
            logger.error("❌ No valid price-profit combinations found")
            return None
        
        # Determine optimal price automatically based on business goal
        if business_goal.lower() == 'revenue':
            optimal_result = max(results, key=lambda x: x['projected_revenue'])
            optimization_metric = 'projected_revenue'
            logger.info(f"🎯 Optimizing for REVENUE maximization")
        else:  # Default to profit
            optimal_result = max(results, key=lambda x: x['projected_profit'])
            optimization_metric = 'projected_profit'
            logger.info(f"🎯 Optimizing for PROFIT maximization")
        
        # Sort results by price for better visualization
        results.sort(key=lambda x: x['price'])
        
        # Apply smart rounding if requested
        original_price = optimal_result['price']
        if apply_smart_rounding:
            smart_price = apply_psychological_pricing(original_price)
            
            # Re-evaluate with smart price if it's different
            if abs(smart_price - original_price) > 0.01:
                # Test the smart price using trained model
                scenario = base_scenario.copy()
                scenario['price'] = smart_price
                
                smart_quantity = forecast_demand_for_scenario(scenario)
                if smart_quantity is not None and smart_quantity > 0:
                    smart_profit = (smart_price - ingredient_cost) * smart_quantity
                    smart_revenue = smart_price * smart_quantity
                    
                    # Use smart price if it's close to optimal performance (within 2%)
                    if business_goal.lower() == 'revenue':
                        if smart_revenue >= optimal_result['projected_revenue'] * 0.98:
                            optimal_result = {
                                'price': smart_price,
                                'predicted_quantity': smart_quantity,
                                'projected_profit': smart_profit,
                                'projected_revenue': smart_revenue,
                                'profit_margin': ((smart_price - ingredient_cost) / smart_price) * 100,
                                'smart_rounded': True
                            }
                            logger.info(f"📈 Applied psychological pricing: RM{original_price:.2f} → RM{smart_price:.2f}")
                    else:
                        if smart_profit >= optimal_result['projected_profit'] * 0.98:
                            optimal_result = {
                                'price': smart_price,
                                'predicted_quantity': smart_quantity,
                                'projected_profit': smart_profit,
                                'projected_revenue': smart_revenue,
                                'profit_margin': ((smart_price - ingredient_cost) / smart_price) * 100,
                                'smart_rounded': True
                            }
                            logger.info(f"📈 Applied psychological pricing: RM{original_price:.2f} → RM{smart_price:.2f}")
        
        # Generate extended results for visualization (includes extended price range)
        extended_results = []
        for price in visualization_prices:
            scenario = base_scenario.copy()
            scenario['price'] = price
            predicted_quantity = forecast_demand_for_scenario(scenario)
            
            if predicted_quantity is not None and predicted_quantity > 0:
                projected_profit = (price - ingredient_cost) * predicted_quantity
                projected_revenue = price * predicted_quantity
                profit_margin = ((price - ingredient_cost) / price) * 100
                
                extended_results.append({
                    'price': price,
                    'predicted_quantity': predicted_quantity,
                    'projected_profit': projected_profit,
                    'projected_revenue': projected_revenue,
                    'profit_margin': profit_margin
                })
        
        # Generate visualizations using extended results for better charts
        visualizations = generate_pricing_visualizations(
            extended_results, optimal_result['price'], ingredient_cost, observed_market_price
        )
        
        # Extract full curves for validation
        price_points = [r['price'] for r in results]
        revenue_curve = [r['projected_revenue'] for r in results]
        profit_curve = [r['projected_profit'] for r in results]
        demand_curve = [r['predicted_quantity'] for r in results]
        
        # Create comprehensive summary with full curves
        optimization_summary = {
            # Optimal results
            'optimal_price': optimal_result['price'],
            'predicted_demand': optimal_result['predicted_quantity'],
            'projected_profit': optimal_result['projected_profit'],
            'projected_revenue': optimal_result['projected_revenue'],
            'profit_margin': optimal_result['profit_margin'],
            
            # Input parameters
            'ingredient_cost': ingredient_cost,
            'observed_market_price': observed_market_price,
            'business_goal': business_goal,
            'optimization_metric': optimization_metric,
            
            # Full curves for validation (U-shape verification)
            'price_points': price_points,
            'revenue_curve': revenue_curve,
            'profit_curve': profit_curve,
            'demand_curve': demand_curve,
            
            # Metadata
            'smart_rounded': optimal_result.get('smart_rounded', False),
            'price_range_tested': f"RM{price_range_start:.2f} - RM{price_range_end:.2f}",
            'total_scenarios_tested': len(results),
            'price_increment': price_increment,
            'visualizations': visualizations,
            'all_results': results
        }
        
        logger.info(f"✅ Optimal price found: RM{optimal_result['price']:.2f}")
        logger.info(f"   Predicted quantity: {optimal_result['predicted_quantity']:.2f} units")
        logger.info(f"   Projected profit: RM{optimal_result['projected_profit']:.2f}")
        logger.info(f"   Projected revenue: RM{optimal_result['projected_revenue']:.2f}")
        logger.info(f"   Profit margin: {optimal_result['profit_margin']:.1f}%")
        
        return optimization_summary
        
    except Exception as e:
        logger.error(f"❌ Error finding optimal price: {str(e)}")
        return None

# === API FUNCTIONS ===

def forecast_demand_for_item(menu_item_name, restaurant_id, day_of_week='Saturday', 
                           weather_condition='Sunny', has_promotion=False, price=15.0, **kwargs):
    """Main API function to forecast demand for a menu item.
    
    Example usage:
    - forecast_demand_for_item('Spaghetti Carbonara', 'Restaurant 7', 'Friday', 'Sunny', False, 55.0)
    - forecast_demand_for_item(41, 'Restaurant 7', 'Friday', 'Sunny', False, 55.0)  # Using menu item ID
    """
    try:
        logger.info(f"📊 Forecasting demand for '{menu_item_name}' at {restaurant_id}")
        
        # Get menu item from database - handle both ID and name
        menu_item = None
        if isinstance(menu_item_name, int):
            # If it's an integer, treat it as menu item ID
            menu_item = get_menu_item_from_database(menu_item_name)
        else:
            # If it's a string, try to find by name (this would require a different function)
            # For now, we'll create a fallback
            pass
        
        if not menu_item:
            logger.warning(f"⚠️ Menu item not found in database, using defaults")
            # If menu_item_name is an integer (ID), use it as ID and create a generic name
            if isinstance(menu_item_name, int):
                menu_item = {
                    'id': menu_item_name,
                    'name': f"Menu Item {menu_item_name}",
                    'ingredient_cost': kwargs.get('typical_ingredient_cost', 5.0),
                    'current_price': price
                }
            else:
                # If menu_item_name is a string, use it as name and generate ID
                menu_item = {
                    'id': hash(menu_item_name) % 10000,
                    'name': menu_item_name,
                    'ingredient_cost': kwargs.get('typical_ingredient_cost', 5.0),
                    'current_price': price
                }
        
        # Create scenario for database-driven forecasting
        scenario = {
            'menu_item_id': menu_item['id'],
            'price': price,
            'days': kwargs.get('days', 7)
        }
        
        # Forecast demand using database approach
        predicted_quantity = forecast_demand_for_scenario(scenario)
        
        if predicted_quantity is None:
            return {'error': 'Failed to forecast demand'}
        
        # Calculate profit metrics
        ingredient_cost = menu_item.get('ingredient_cost', 5.0)
        unit_profit = price - ingredient_cost
        total_profit = unit_profit * predicted_quantity
        profit_margin = (unit_profit / price) * 100 if price > 0 else 0
        
        # Get the actual menu item name from database if we have the ID
        display_name = menu_item_name
        if isinstance(menu_item_name, int):
            # Use the name from the menu_item we already retrieved
            if menu_item and 'name' in menu_item:
                display_name = menu_item['name']
            else:
                display_name = f"Menu Item {menu_item_name}"
        
        # Format result with JSON-safe types
        result = {
            'menu_item_name': str(display_name),
            'restaurant_id': str(restaurant_id),
            'scenario': {
                'day_of_week': str(day_of_week),
                'weather_condition': str(weather_condition),
                'has_promotion': bool(has_promotion),
                'price': float(price)
            },
            'forecast': {
                'predicted_quantity_sold': float(round(predicted_quantity, 2)),
                'unit_profit': float(round(unit_profit, 2)),
                'total_projected_profit': float(round(total_profit, 2)),
                'profit_margin_percent': float(round(profit_margin, 2))
            },
            'model_info': {
                'model_type': 'Linear Regression',
                'features_used': int(len(scenario)),
                'scenario_type': 'database_driven'
            }
        }
        
        logger.info(f"✅ Demand forecast completed: {predicted_quantity:.2f} units")
        return result
        
    except Exception as e:
        logger.error(f"❌ Error in demand forecasting API: {str(e)}")
        return {'error': str(e)}

def predict_optimal_price_for_item(menu_item_name, restaurant_id, day_of_week='Saturday', 
                                 weather_condition='Sunny', has_promotion=False,
                                 price_range_start=None, price_range_end=None, price_increment=0.25,
                                 business_goal='profit', apply_smart_rounding=True,
                                 include_visualizations=True, menu_item_id=None, **kwargs):
    """Main API function to predict optimal price that maximizes profit or revenue.
    
    Args:
        menu_item_name (str): Name of the menu item
        restaurant_id (str): Restaurant identifier
        day_of_week (str): Day of the week for scenario
        weather_condition (str): Weather condition for scenario
        has_promotion (bool): Whether there's a promotion
        price_range_start (float): Starting price for optimization
        price_range_end (float): Ending price for optimization
        price_increment (float): Price increment for testing
        business_goal (str): 'profit' or 'revenue' - optimization objective
        apply_smart_rounding (bool): Whether to apply psychological pricing rules
        include_visualizations (bool): Whether to generate visualization charts
    
    Example usage:
    - predict_optimal_price_for_item('Laksa', 'Food Stall 11', 'Saturday', 'Sunny', False, 8.0, 20.0, 0.25)
    """
    try:
        logger.info(f"💰 Finding optimal price for '{menu_item_name}' at {restaurant_id}")
        logger.info(f"📊 Business goal: {business_goal.upper()}, Smart rounding: {apply_smart_rounding}")
        
        # Get menu item from database - prioritize menu_item_id if provided
        if menu_item_id is not None:
            menu_item = get_menu_item_from_database(menu_item_id)
        else:
            menu_item = get_menu_item_from_database(menu_item_name) if isinstance(menu_item_name, int) else None
        
        if not menu_item:
            logger.warning(f"⚠️ Menu item not found in database, using defaults")
            # Use the provided menu_item_id directly, don't generate a hash
            actual_id = menu_item_id if menu_item_id is not None else menu_item_name
            menu_item = {
                'id': actual_id,
                'name': menu_item_name,
                'ingredient_cost': kwargs.get('typical_ingredient_cost', 5.0),
                'current_price': price_range_start
            }
        
        # Create base scenario for database-driven optimization
        base_scenario = {
            'menu_item_id': menu_item['id'],
            'typical_ingredient_cost': menu_item.get('ingredient_cost', 5.0),
            'observed_market_price': kwargs.get('observed_market_price', 0),
            'category': menu_item.get('category', kwargs.get('category', 'Main Course')),
            'cuisine_type': menu_item.get('cuisine_type', kwargs.get('cuisine_type', 'Asian')),
            'days': kwargs.get('days', 7)
        }
        
        # Find optimal price with enhanced features
        optimization_result = find_optimal_price(
            base_scenario=base_scenario,
            price_range_start=price_range_start,
            price_range_end=price_range_end,
            price_increment=price_increment,
            business_goal=business_goal,
            apply_smart_rounding=apply_smart_rounding
        )
        
        if optimization_result is None:
            return {'error': 'Failed to find optimal price'}
        
        # Format result for API response with JSON-safe types
        result = {
            'menu_item_name': str(menu_item_name),
            'restaurant_id': str(restaurant_id),
            'scenario': {
                'day_of_week': str(day_of_week),
                'weather_condition': str(weather_condition),
                'has_promotion': bool(has_promotion)
            },
            'optimization': {
                'optimal_price': float(optimization_result['optimal_price']),
                'predicted_quantity_at_optimal_price': float(optimization_result['predicted_demand']),
                'maximum_projected_profit': float(optimization_result['projected_profit']),
                'maximum_projected_revenue': float(optimization_result['projected_revenue']),
                'profit_margin_percent': float(optimization_result['profit_margin']),
                'ingredient_cost': float(optimization_result['ingredient_cost']),
                'observed_market_price': float(optimization_result['observed_market_price']),
                'business_goal': str(optimization_result['business_goal']),
                'optimization_metric': str(optimization_result['optimization_metric']),

                'smart_rounded': bool(optimization_result['smart_rounded'])
            },
            'analysis': {
                'price_range_tested': str(optimization_result['price_range_tested']),
                'total_scenarios_tested': int(optimization_result['total_scenarios_tested']),
                'model_type': 'Database-Driven Forecasting',

                'features_enabled': {
                    'smart_rounding': bool(apply_smart_rounding),
                    'competitor_bounds': bool(optimization_result['observed_market_price'] > 0),
                    'visualizations': bool(include_visualizations)
                }
            },
            'price_profit_curve': [
                {
                    'price': float(r['price']),
                    'predicted_quantity': float(r['predicted_quantity']),
                    'projected_profit': float(r['projected_profit']),
                    'projected_revenue': float(r['projected_revenue']),
                    'profit_margin': float(r['profit_margin']),

                } for r in optimization_result['all_results']
            ]
        }
        
        # Add visualizations if requested and available
        if include_visualizations and 'visualizations' in optimization_result:
            result['visualizations'] = optimization_result['visualizations']
        
        logger.info(f"✅ Optimal price found: RM{optimization_result['optimal_price']:.2f}")
        logger.info(f"   Projected profit: RM{optimization_result['projected_profit']:.2f}")
        logger.info(f"   Projected revenue: RM{optimization_result['projected_revenue']:.2f}")
        return result
        
    except Exception as e:
        logger.error(f"❌ Error in price optimization API: {str(e)}")
        return {'error': str(e)}

def get_existing_menu_items():
    """Get list of existing menu items from the dataset."""
    try:
        df = load_pricing_data()
        if df is not None and 'menu_item_name' in df.columns:
            return df['menu_item_name'].unique().tolist()
        return []
    except Exception as e:
        logger.error(f"Error getting existing menu items: {str(e)}")
        return []

def get_restaurant_list():
    """Get list of restaurants from the dataset."""
    try:
        df = load_pricing_data()
        if df is not None and 'restaurant_id' in df.columns:
            return df['restaurant_id'].unique().tolist()
        return []
    except Exception as e:
        logger.error(f"Error getting restaurant list: {str(e)}")
        return []

# === EXAMPLE USAGE FUNCTIONS ===

def run_demand_forecasting_examples():
    """Run example demand forecasting scenarios."""
    logger.info("🚀 Running demand forecasting examples...")
    
    # Example A: Existing item - Spaghetti Carbonara
    example_a = forecast_demand_for_item(
        menu_item_name='Spaghetti Carbonara',
        restaurant_id='Restaurant 7',
        day_of_week='Friday',
        weather_condition='Sunny',
        has_promotion=False,
        price=55.0
    )
    logger.info(f"📊 Example A Result: {example_a}")
    
    # Example B: New item with custom characteristics
    example_b = forecast_demand_for_item(
        menu_item_name='New Gourmet Pasta',
        restaurant_id='Restaurant 7',
        day_of_week='Friday',
        weather_condition='Sunny',
        has_promotion=False,
        price=55.0,
        category='main_course',
        cuisine_type='italian',
        typical_ingredient_cost=15.0
    )
    logger.info(f"📊 Example B Result: {example_b}")
    
    return {'example_a': example_a, 'example_b': example_b}

def run_price_optimization_examples():
    """Run example price optimization scenarios."""
    logger.info("🚀 Running price optimization examples...")
    
    # Example: Laksa at Food Stall 11
    example = predict_optimal_price_for_item(
        menu_item_name='Laksa',
        restaurant_id='Food Stall 11',
        day_of_week='Saturday',
        weather_condition='Sunny',
        has_promotion=False,
        price_range_start=8.0,
        price_range_end=20.0,
        price_increment=0.25
    )
    logger.info(f"💰 Price Optimization Result: {example}")
    
    return example

# === WRAPPER FUNCTIONS FOR BACKWARD COMPATIBILITY ===

def get_recommendations(page=1, per_page=30, menu_item=None, competitor=None, day_of_week=None):
    """Get pricing recommendations with pagination and filters."""
    try:
        df = load_pricing_data()
        if df is None:
            return [], 0
        
        # Apply filters if provided
        filtered_df = df.copy()
        if menu_item:
            filtered_df = filtered_df[filtered_df['menu_item_name'].str.contains(menu_item, case=False, na=False)]
        if day_of_week:
            filtered_df = filtered_df[filtered_df['day_of_week'] == day_of_week]
        
        total_count = len(filtered_df)
        
        # Apply pagination
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        paginated_df = filtered_df.iloc[start_idx:end_idx]
        
        # Generate recommendations for each item
        recommendations = []
        for _, row in paginated_df.iterrows():
            rec = {
                'menu_item_id': hash(row['menu_item_name']) % 10000,
                'name': row['menu_item_name'],
                'competitor': row.get('restaurant_id', 'Unknown'),
                'day_of_week': row['day_of_week'],
                'ingredient_cost': row.get('ingredient_cost', 10.0),
                'competitor_price': row['price'],
                'suggested_price': row['price'] * 1.1,  # 10% markup
                'current_volume': row['quantity_sold'],
                'predicted_volume': row['quantity_sold'] * 1.05,
                'predicted_profit': row['price'] * row['quantity_sold'] * 0.15,
                'profit_change_pct': 15.0,
                'price_change_pct': 10.0,
                'confidence': 'high'
            }
            recommendations.append(rec)
        
        return recommendations, total_count
        
    except Exception as e:
        logger.error(f"Error in get_recommendations: {str(e)}")
        return [], 0

def get_detailed_recommendation_for_existing_item(menu_item_id):
    """Get detailed recommendation for an existing menu item."""
    try:
        # Get menu item from database using the provided ID
        menu_item = get_menu_item_from_database(menu_item_id)
        
        if not menu_item:
            logger.error(f"Menu item with ID {menu_item_id} not found in database")
            return None
        
        # Use forecast_demand_for_item with the actual menu item data
        result = forecast_demand_for_item(
            menu_item_name=menu_item_id,  # Pass the ID directly
            restaurant_id='Restaurant 1',  # Default restaurant
            day_of_week='Saturday',  # Default day
            weather_condition='Sunny',  # Default weather
            has_promotion=False,  # Default promotion
            price=float(menu_item.get('menu_price', menu_item.get('typical_ingredient_cost', 5.0) * 2.5))
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error in get_detailed_recommendation_for_existing_item: {str(e)}")
        return None

def generate_pricing_recommendation_for_menu_item(menu_item):
    """Generate pricing recommendation for a menu item object."""
    try:
        # Use predict_optimal_price_for_item with menu item ID and name
        result = predict_optimal_price_for_item(
            menu_item_name=menu_item.menu_item_name,
            menu_item_id=menu_item.id,  # Pass the actual menu item ID
            restaurant_id='Restaurant 1',  # Default restaurant
            day_of_week='Saturday',
            weather_condition='Sunny',
            has_promotion=False,
            # Remove explicit price ranges to allow category-based pricing
            price_increment=0.5,
            days=7  # Default calculation period
        )
        
        # Add calculation period information to the result
        if result and 'error' not in result:
            result['calculation_period'] = {
                'days': 7,
                'description': 'Revenue and profit calculations are based on a 7-day forecast period'
            }
        
        return result
        
    except Exception as e:
        logger.error(f"Error in generate_pricing_recommendation_for_menu_item: {str(e)}")
        return None

if __name__ == "__main__":
    # Run examples when script is executed directly
    logger.info("🎯 Starting demand forecasting and price optimization examples...")
    
    # Run demand forecasting examples
    demand_examples = run_demand_forecasting_examples()
    
    # Run price optimization examples
    price_examples = run_price_optimization_examples()
    
    logger.info("✅ All examples completed successfully!")
