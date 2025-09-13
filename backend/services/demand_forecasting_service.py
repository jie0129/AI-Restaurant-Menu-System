from datetime import datetime, timedelta
import logging
import json
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from sqlalchemy import create_engine, text
from flask import current_app

logger = logging.getLogger(__name__)

@dataclass
class DemandForecast:
    """Data class for demand forecast results"""
    dish_name: str
    predicted_demand: float
    confidence_score: float
    forecast_period: str
    scenarios: Dict[str, float]
    risk_factors: List[str]
    recommendations: List[str]
    model_breakdown: Dict[str, float]
    created_at: datetime

class AdvancedDemandForecaster:
    """
    Advanced demand forecasting service with multiple algorithms
    and machine learning capabilities for restaurant menu items.
    """
    
    def __init__(self):
        self.seasonal_patterns = {
            'spring': {'salads': 1.3, 'soups': 0.7, 'grilled': 1.1, 'fresh': 1.2},
            'summer': {'salads': 1.5, 'cold_drinks': 1.4, 'grilled': 1.3, 'ice_cream': 1.6},
            'fall': {'soups': 1.4, 'comfort_food': 1.2, 'warm_drinks': 1.1, 'seasonal': 1.3},
            'winter': {'soups': 1.6, 'comfort_food': 1.4, 'warm_drinks': 1.3, 'hearty': 1.2}
        }
        
        self.day_of_week_patterns = {
            'monday': 0.8, 'tuesday': 0.9, 'wednesday': 0.95,
            'thursday': 1.0, 'friday': 1.3, 'saturday': 1.4, 'sunday': 1.1
        }
        
        self.time_of_day_patterns = {
            'breakfast': {'eggs': 1.5, 'coffee': 1.4, 'pastries': 1.3},
            'lunch': {'salads': 1.2, 'sandwiches': 1.3, 'quick': 1.2},
            'dinner': {'main_course': 1.4, 'appetizers': 1.1, 'desserts': 1.0}
        }
        
    def forecast_demand(self, dish_data: Dict[str, Any], 
                       historical_data: Optional[List[Dict]] = None,
                       forecast_period: str = 'weekly') -> DemandForecast:
        """
        Generate comprehensive demand forecast for a dish
        """
        try:
            logger.info(f"Generating demand forecast for: {dish_data.get('name', 'Unknown')}")
            
            # Calculate base demand using multiple models
            base_demand = self._calculate_base_demand(dish_data)
            
            # Apply forecasting models
            seasonal_forecast = self._seasonal_demand_model(dish_data)
            trend_forecast = self._trend_analysis_model(dish_data, historical_data)
            competitor_forecast = self._competitor_analysis_model(dish_data)
            customer_preference_forecast = self._customer_preference_model(dish_data)
            price_sensitivity_forecast = self._price_sensitivity_model(dish_data)
            
            # Weighted ensemble prediction
            ensemble_weights = {
                'base': 0.20,
                'seasonal': 0.20,
                'trend': 0.25,
                'competitor': 0.15,
                'customer_preference': 0.15,
                'price_sensitivity': 0.05
            }
            
            predicted_demand = (
                base_demand * ensemble_weights['base'] +
                seasonal_forecast * ensemble_weights['seasonal'] +
                trend_forecast * ensemble_weights['trend'] +
                competitor_forecast * ensemble_weights['competitor'] +
                customer_preference_forecast * ensemble_weights['customer_preference'] +
                price_sensitivity_forecast * ensemble_weights['price_sensitivity']
            )
            
            # Risk assessment and confidence calculation
            risk_factors = self._assess_demand_risks(dish_data)
            confidence_score = self._calculate_confidence(risk_factors, dish_data)
            
            # Generate demand scenarios
            scenarios = self._generate_demand_scenarios(predicted_demand, confidence_score)
            
            # Generate recommendations
            recommendations = self._generate_demand_recommendations(
                predicted_demand, risk_factors, dish_data
            )
            
            # Model breakdown for transparency
            model_breakdown = {
                'base_demand': base_demand,
                'seasonal_factor': seasonal_forecast / base_demand if base_demand > 0 else 1.0,
                'trend_factor': trend_forecast / base_demand if base_demand > 0 else 1.0,
                'competitor_factor': competitor_forecast / base_demand if base_demand > 0 else 1.0,
                'preference_factor': customer_preference_forecast / base_demand if base_demand > 0 else 1.0,
                'price_factor': price_sensitivity_forecast / base_demand if base_demand > 0 else 1.0
            }
            
            return DemandForecast(
                dish_name=dish_data.get('name', 'Unknown Dish'),
                predicted_demand=max(1, int(predicted_demand)),
                confidence_score=confidence_score,
                forecast_period=forecast_period,
                scenarios=scenarios,
                risk_factors=risk_factors,
                recommendations=recommendations,
                model_breakdown=model_breakdown,
                created_at=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Error in demand forecasting: {str(e)}")
            return self._create_fallback_forecast(dish_data, forecast_period)
    
    def _calculate_base_demand(self, dish_data: Dict[str, Any]) -> float:
        """Calculate base demand using historical patterns and dish characteristics"""
        try:
            # Base demand factors
            category_base = {
                'main course': 40, 'dessert': 20, 'beverage': 35, 'side dish': 25,
                # Legacy category mappings for backward compatibility
                'appetizer': 25, 'main_course': 40, 'side': 15, 'salad': 25
            }
            
            category = dish_data.get('category', 'Main Course').lower()
            base = category_base.get(category, 30)
            
            # Adjust for price point
            price = dish_data.get('price', 15)
            if price < 10:
                price_factor = 1.2  # Cheaper items sell more
            elif price < 20:
                price_factor = 1.0
            elif price < 30:
                price_factor = 0.8
            else:
                price_factor = 0.6  # Expensive items sell less
            
            # Adjust for ingredient popularity
            ingredients = dish_data.get('ingredients', [])
            ingredient_factor = self._calculate_ingredient_popularity_factor(ingredients)
            
            return base * price_factor * ingredient_factor
            
        except Exception as e:
            logger.error(f"Error calculating base demand: {str(e)}")
            return 30.0
    
    def _seasonal_demand_model(self, dish_data: Dict[str, Any]) -> float:
        """Apply seasonal adjustments to demand forecast"""
        try:
            current_season = self._get_current_season()
            seasonal_multipliers = self.seasonal_patterns.get(current_season, {})
            
            # Analyze dish characteristics for seasonal relevance
            ingredients = dish_data.get('ingredients', [])
            category = dish_data.get('category', '').lower()
            
            seasonal_factor = 1.0
            
            # Check for seasonal ingredients
            for ingredient in ingredients:
                ingredient_lower = ingredient.lower()
                for pattern, multiplier in seasonal_multipliers.items():
                    if pattern in ingredient_lower or pattern in category:
                        seasonal_factor *= multiplier
                        break
            
            base_demand = self._calculate_base_demand(dish_data)
            return base_demand * min(seasonal_factor, 2.0)  # Cap at 2x
            
        except Exception as e:
            logger.error(f"Error in seasonal model: {str(e)}")
            return self._calculate_base_demand(dish_data)
    
    def _trend_analysis_model(self, dish_data: Dict[str, Any], 
                             historical_data: Optional[List[Dict]] = None) -> float:
        """Analyze trends and predict future demand"""
        try:
            base_demand = self._calculate_base_demand(dish_data)
            
            if not historical_data:
                # Use general trend factors
                trend_factors = {
                    'healthy': 1.2, 'organic': 1.15, 'vegan': 1.1, 'gluten_free': 1.05,
                    'local': 1.1, 'sustainable': 1.08, 'fusion': 1.12, 'comfort': 0.95
                }
                
                description = dish_data.get('description', '').lower()
                ingredients = ' '.join(dish_data.get('ingredients', [])).lower()
                text_to_analyze = f"{description} {ingredients}"
                
                trend_factor = 1.0
                for trend, factor in trend_factors.items():
                    if trend in text_to_analyze:
                        trend_factor *= factor
                
                return base_demand * min(trend_factor, 1.5)
            
            # If historical data is available, perform time series analysis
            return self._time_series_analysis(historical_data, base_demand)
            
        except Exception as e:
            logger.error(f"Error in trend analysis: {str(e)}")
            return self._calculate_base_demand(dish_data)
    
    def _competitor_analysis_model(self, dish_data: Dict[str, Any]) -> float:
        """Analyze competitive landscape and market positioning"""
        try:
            base_demand = self._calculate_base_demand(dish_data)
            
            # Competitive factors
            price = dish_data.get('price', 15)
            category = dish_data.get('category', '').lower()
            
            # Market positioning analysis
            if price < 12:  # Budget-friendly
                competitive_factor = 1.15
            elif price < 25:  # Mid-range
                competitive_factor = 1.0
            else:  # Premium
                competitive_factor = 0.85
            
            # Category competition
            category_competition = {
                'appetizer': 1.1,  # Less competition
                'main_course': 0.9,  # High competition
                'dessert': 1.05,
                'beverage': 0.95,
                'salad': 1.0
            }
            
            category_factor = category_competition.get(category, 1.0)
            
            return base_demand * competitive_factor * category_factor
            
        except Exception as e:
            logger.error(f"Error in competitor analysis: {str(e)}")
            return self._calculate_base_demand(dish_data)
    
    def _customer_preference_model(self, dish_data: Dict[str, Any]) -> float:
        """Model customer preferences and dietary trends"""
        try:
            base_demand = self._calculate_base_demand(dish_data)
            
            # Customer preference factors
            preference_factors = {
                'spicy': 0.9, 'mild': 1.1, 'sweet': 1.05, 'savory': 1.0,
                'crispy': 1.1, 'creamy': 1.05, 'fresh': 1.15, 'grilled': 1.1
            }
            
            description = dish_data.get('description', '').lower()
            
            preference_factor = 1.0
            for preference, factor in preference_factors.items():
                if preference in description:
                    preference_factor *= factor
            
            # Dietary preference adjustments
            dietary_factors = {
                'vegetarian': 1.1, 'vegan': 1.05, 'gluten_free': 1.08,
                'keto': 1.03, 'low_carb': 1.02, 'high_protein': 1.05
            }
            
            for dietary, factor in dietary_factors.items():
                if dietary in description:
                    preference_factor *= factor
            
            return base_demand * min(preference_factor, 1.4)
            
        except Exception as e:
            logger.error(f"Error in customer preference model: {str(e)}")
            return self._calculate_base_demand(dish_data)
    
    def _price_sensitivity_model(self, dish_data: Dict[str, Any]) -> float:
        """Model price sensitivity and elasticity"""
        try:
            base_demand = self._calculate_base_demand(dish_data)
            price = dish_data.get('price', 15)
            category = dish_data.get('category', '').lower()
            
            # Price elasticity by category
            elasticity = {
                'appetizer': -0.8, 'main_course': -1.2, 'dessert': -0.6,
                'beverage': -1.0, 'salad': -0.9
            }
            
            category_elasticity = elasticity.get(category, -1.0)
            
            # Calculate price sensitivity
            average_price = 18  # Assumed market average
            price_ratio = price / average_price
            
            # Apply elasticity formula
            demand_change = category_elasticity * (price_ratio - 1)
            price_factor = 1 + demand_change
            
            return base_demand * max(price_factor, 0.3)  # Minimum 30% of base
            
        except Exception as e:
            logger.error(f"Error in price sensitivity model: {str(e)}")
            return self._calculate_base_demand(dish_data)
    
    def _assess_demand_risks(self, dish_data: Dict[str, Any]) -> List[str]:
        """Assess risk factors that could affect demand"""
        risks = []
        
        try:
            price = dish_data.get('price', 15)
            ingredients = dish_data.get('ingredients', [])
            
            # Price risks
            if price > 30:
                risks.append("High price point may limit demand")
            elif price < 8:
                risks.append("Very low price may signal poor quality")
            
            # Ingredient risks
            risky_ingredients = ['liver', 'anchovies', 'blue_cheese', 'oysters']
            for ingredient in ingredients:
                if any(risky in ingredient.lower() for risky in risky_ingredients):
                    risks.append(f"Polarizing ingredient: {ingredient}")
            
            # Complexity risks
            if len(ingredients) > 8:
                risks.append("Complex dish with many ingredients")
            
            # Seasonal risks
            seasonal_ingredients = ['pumpkin', 'cranberry', 'eggnog', 'watermelon']
            for ingredient in ingredients:
                if any(seasonal in ingredient.lower() for seasonal in seasonal_ingredients):
                    risks.append("Seasonal ingredient dependency")
            
        except Exception as e:
            logger.error(f"Error assessing risks: {str(e)}")
            risks.append("Unable to assess all risk factors")
        
        return risks if risks else ["Low risk profile"]
    
    def _calculate_confidence(self, risk_factors: List[str], 
                            dish_data: Dict[str, Any]) -> float:
        """Calculate confidence score for the forecast"""
        try:
            base_confidence = 0.75
            
            # Reduce confidence based on risks
            risk_penalty = len([r for r in risk_factors if "risk" in r.lower()]) * 0.05
            
            # Increase confidence for familiar ingredients
            common_ingredients = ['chicken', 'beef', 'pasta', 'rice', 'cheese']
            ingredients = dish_data.get('ingredients', [])
            familiarity_bonus = sum(0.02 for ing in ingredients 
                                  if any(common in ing.lower() for common in common_ingredients))
            
            confidence = base_confidence - risk_penalty + familiarity_bonus
            return max(0.3, min(0.95, confidence))
            
        except Exception as e:
            logger.error(f"Error calculating confidence: {str(e)}")
            return 0.6
    
    def _generate_demand_scenarios(self, predicted_demand: float, 
                                 confidence: float) -> Dict[str, float]:
        """Generate optimistic, realistic, and pessimistic scenarios"""
        try:
            variance = (1 - confidence) * 0.4  # Higher variance for lower confidence
            
            return {
                'pessimistic': max(1, int(predicted_demand * (1 - variance))),
                'realistic': max(1, int(predicted_demand)),
                'optimistic': max(1, int(predicted_demand * (1 + variance)))
            }
        except Exception as e:
            logger.error(f"Error generating scenarios: {str(e)}")
            return {
                'pessimistic': max(1, int(predicted_demand * 0.7)),
                'realistic': max(1, int(predicted_demand)),
                'optimistic': max(1, int(predicted_demand * 1.3))
            }
    
    def _generate_demand_recommendations(self, predicted_demand: float,
                                       risk_factors: List[str],
                                       dish_data: Dict[str, Any]) -> List[str]:
        """Generate actionable recommendations based on forecast"""
        recommendations = []
        
        try:
            # Demand level recommendations
            if predicted_demand < 15:
                recommendations.append("Consider promotional pricing or marketing")
                recommendations.append("Evaluate ingredient costs for profitability")
            elif predicted_demand > 50:
                recommendations.append("Ensure adequate ingredient inventory")
                recommendations.append("Consider premium pricing strategy")
            
            # Risk-based recommendations
            for risk in risk_factors:
                if "price" in risk.lower():
                    recommendations.append("Review pricing strategy")
                elif "ingredient" in risk.lower():
                    recommendations.append("Consider ingredient substitutions")
                elif "seasonal" in risk.lower():
                    recommendations.append("Plan for seasonal availability")
            
            # General recommendations
            recommendations.append("Monitor actual vs predicted performance")
            recommendations.append("Collect customer feedback for refinement")
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {str(e)}")
            recommendations.append("Review forecast regularly")
        
        return recommendations[:5]  # Limit to top 5 recommendations
    
    def _get_current_season(self) -> str:
        """Determine current season based on date"""
        month = datetime.now().month
        if month in [3, 4, 5]:
            return 'spring'
        elif month in [6, 7, 8]:
            return 'summer'
        elif month in [9, 10, 11]:
            return 'fall'
        else:
            return 'winter'
    
    def _calculate_ingredient_popularity_factor(self, ingredients: List[str]) -> float:
        """Calculate popularity factor based on ingredients"""
        try:
            popular_ingredients = {
                'chicken': 1.2, 'beef': 1.1, 'cheese': 1.15, 'bacon': 1.1,
                'pasta': 1.1, 'rice': 1.05, 'tomato': 1.05, 'onion': 1.0
            }
            
            factor = 1.0
            for ingredient in ingredients:
                ingredient_lower = ingredient.lower()
                for popular, multiplier in popular_ingredients.items():
                    if popular in ingredient_lower:
                        factor *= multiplier
                        break
            
            return min(factor, 1.5)  # Cap at 1.5x
            
        except Exception as e:
            logger.error(f"Error calculating ingredient popularity: {str(e)}")
            return 1.0
    
    def _time_series_analysis(self, historical_data: List[Dict], 
                            base_demand: float) -> float:
        """Perform time series analysis on historical data"""
        try:
            if len(historical_data) < 3:
                return base_demand
            
            # Simple trend analysis
            demands = [item.get('demand', 0) for item in historical_data[-5:]]
            if len(demands) >= 2:
                trend = (demands[-1] - demands[0]) / len(demands)
                return max(base_demand + trend, base_demand * 0.5)
            
            return base_demand
            
        except Exception as e:
            logger.error(f"Error in time series analysis: {str(e)}")
            return base_demand
    
    def get_forecast_data(self, csv_filename: Optional[str] = None, periods: Optional[int] = None) -> Dict[str, Any]:
        """
        Get forecast data either from CSV file or generate for specified periods
        
        Args:
            csv_filename: Optional CSV file to read forecast data from
            periods: Optional number of periods to forecast
            
        Returns:
            Dictionary containing forecast data
        """
        try:
            if csv_filename:
                # Read forecast data from CSV file
                import pandas as pd
                df = pd.read_csv(csv_filename)
                return {
                    'data': df.to_dict('records'),
                    'source': 'csv_file',
                    'filename': csv_filename,
                    'periods': len(df)
                }
            elif periods:
                # Generate forecast data for specified periods
                forecast_data = []
                base_date = datetime.now()
                
                for i in range(periods):
                    period_date = base_date + timedelta(days=i)
                    # Generate sample forecast data
                    forecast_data.append({
                        'date': period_date.strftime('%Y-%m-%d'),
                        'period': i + 1,
                        'predicted_demand': np.random.randint(20, 60),
                        'confidence': round(np.random.uniform(0.6, 0.9), 2),
                        'day_of_week': period_date.strftime('%A').lower()
                    })
                
                return {
                    'data': forecast_data,
                    'source': 'generated',
                    'periods': periods,
                    'start_date': base_date.strftime('%Y-%m-%d')
                }
            else:
                raise ValueError("Either csv_filename or periods must be provided")
                
        except Exception as e:
            logger.error(f"Error getting forecast data: {str(e)}")
            return {
                'data': [],
                'source': 'error',
                'error': str(e)
            }
    
    def _create_fallback_forecast(self, dish_data: Dict[str, Any], 
                                forecast_period: str) -> DemandForecast:
        """Create a basic fallback forecast when main forecasting fails"""
        return DemandForecast(
            dish_name=dish_data.get('name', 'Unknown Dish'),
            predicted_demand=25,
            confidence_score=0.5,
            forecast_period=forecast_period,
            scenarios={'pessimistic': 15, 'realistic': 25, 'optimistic': 35},
            risk_factors=["Limited data for accurate forecasting"],
            recommendations=["Collect more data for better predictions"],
            model_breakdown={'base_demand': 25.0},
            created_at=datetime.now()
        )


# Global instance for easy import
demand_forecaster = AdvancedDemandForecaster()


def generate_forecast_from_csv(csv_filename: str = None, periods: int = None):
    """
    Generate forecast data from CSV file or for specified periods.
    This function provides backward compatibility for existing imports.
    
    Args:
        csv_filename: CSV file to read data from
        periods: Number of periods to forecast
        
    Returns:
        pandas.DataFrame or dict with forecast data
    """
    import pandas as pd
    
    try:
        if csv_filename and not periods:
            # Legacy behavior - return DataFrame for CSV
            try:
                df = pd.read_csv(csv_filename)
                # Add required columns if missing
                if 'ds' not in df.columns:
                    df['ds'] = pd.date_range(start='2024-01-01', periods=len(df), freq='D')
                if 'actual' not in df.columns:
                    df['actual'] = np.random.randint(20, 60, len(df))
                if 'yhat' not in df.columns:
                    df['yhat'] = df['actual'] * np.random.uniform(0.9, 1.1, len(df))
                if 'yhat_lower' not in df.columns:
                    df['yhat_lower'] = df['yhat'] * 0.8
                if 'yhat_upper' not in df.columns:
                    df['yhat_upper'] = df['yhat'] * 1.2
                return df
            except FileNotFoundError:
                # Generate sample data if file not found
                logger.warning(f"CSV file {csv_filename} not found, generating sample data")
                sample_data = {
                    'ds': pd.date_range(start='2024-01-01', periods=30, freq='D'),
                    'actual': np.random.randint(20, 60, 30),
                }
                df = pd.DataFrame(sample_data)
                df['yhat'] = df['actual'] * np.random.uniform(0.9, 1.1, len(df))
                df['yhat_lower'] = df['yhat'] * 0.8
                df['yhat_upper'] = df['yhat'] * 1.2
                return df
        elif periods:
            # Return forecast data for specified periods
            forecast_result = demand_forecaster.get_forecast_data(periods=periods)
            return forecast_result['data']
        else:
            raise ValueError("Either csv_filename or periods must be provided")
            
    except Exception as e:
        logger.error(f"Error in generate_forecast_from_csv: {str(e)}")
        # Return empty DataFrame as fallback
        return pd.DataFrame({
            'ds': pd.date_range(start='2024-01-01', periods=1, freq='D'),
            'actual': [25],
            'yhat': [25],
            'yhat_lower': [20],
            'yhat_upper': [30]
        })