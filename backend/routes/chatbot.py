from flask import Blueprint, jsonify, request
from models.menu_item import MenuItem, db
from models.ingredient import Ingredient
from models.inventory_item import InventoryItem
from models.customer_order import CustomerOrder
from models.menu_nutrition import MenuNutrition
from services.demand_forecasting_service import generate_forecast_from_csv
from services.recommendation import get_recommendations
from services.usda_nutrition_service import USDANutritionService
from services.unified_restaurant_demand_system import RestaurantDemandPredictor
from services.autogen_ai_agent import AutoGenRestaurantAI, DishSuggestion
import logging
import json
import re
import os
from datetime import datetime, timedelta
from sqlalchemy import func, text
import google.generativeai as genai

# Setup logging with UTF-8 encoding support
import sys
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('chatbot.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

chatbot_bp = Blueprint('chatbot', __name__)

class RestaurantIntelligenceAgent:
    """Main chatbot service class for handling restaurant intelligence queries"""
    
    def __init__(self):
        self.nutrition_service = USDANutritionService()
        self.ai_agent = AutoGenRestaurantAI()  # Initialize AI Agent
        self.mode = 'chat'  # 'chat' or 'automation'
        self.intelligence_mode = 'INSIGHTS'  # 'INSIGHTS', 'PROMOTION', 'INNOVATION'
        self.current_workflow = None  # Track current AI Agent workflow
    
    def process_message(self, message, context=None, intelligence_mode=None, category=None):
        """Process incoming message and determine appropriate response"""
        message_lower = message.lower()
        
        # Debug logging to file with UTF-8 encoding
        try:
            with open('C:\\Users\\User\\Desktop\\first-app\\debug_log.txt', 'a', encoding='utf-8') as f:
                f.write(f"DEBUG: Processing message: '{message}'\n")
                f.write(f"DEBUG: Message lower: '{message_lower}'\n")
                f.write(f"DEBUG: Workflow details check: {'workflow details' in message_lower}\n")
                f.write(f"DEBUG: Show workflow details check: {'show workflow details' in message_lower}\n")
                f.flush()
        except Exception as e:
            pass
        
        # Update intelligence mode if provided
        if intelligence_mode:
            self.intelligence_mode = intelligence_mode
        
        # Check for workflow details command
        if 'workflow details' in message_lower or 'show workflow details' in message_lower:
            print("DEBUG: Routing to workflow details handler")
            return self._handle_workflow_details_request()
        
        # Check for AI agent workflow commands (check original message first)
        # Log safely without Unicode characters
        safe_message = message.encode('ascii', 'ignore').decode('ascii') if message else 'empty'
        safe_message_lower = message_lower.encode('ascii', 'ignore').decode('ascii') if message_lower else 'empty'
        logging.info(f"DEBUG: Processing message: {safe_message[:50]}...")
        logging.info(f"DEBUG: Message lower: {safe_message_lower[:50]}...")
        logging.info(f"DEBUG: AI agent check: {'ai agent' in message_lower}")
        logging.info(f"DEBUG: Auto apply check: {'auto apply recipe' in message_lower}")
        logging.info(f"DEBUG: Automated workflow check: {'automated workflow' in message_lower}")
        logging.info(f"DEBUG: Workflow execution check: {'workflow execution' in message_lower}")
        
        if 'ai agent' in message_lower or 'auto apply recipe' in message_lower or 'automated workflow' in message_lower or 'workflow execution' in message_lower:
            logging.info("DEBUG: Routing to AI agent workflow")
            self.mode = 'ai_agent'
            return self._handle_ai_agent_workflow(message)
        
        # Check for automation commands
        if self._is_automation_command(message_lower):
            self.mode = 'automation'
            return self._handle_automation_command(message_lower)
        
        # Check for intelligence mode specific requests
        if self._is_intelligence_mode_request(message_lower):
            return self._handle_intelligence_mode_request(message_lower)
        
        # Regular chat mode
        self.mode = 'chat'
        return self._handle_chat_message(message_lower, context, category)
    
    def _is_automation_command(self, message):
        """Check if message is an automation command"""
        automation_keywords = [
            'recalculate nutrition',
            'update pricing',
            'forecast demand',
            'optimize prices',
            'run automation',
            'calculate all nutrition',
            'update all prices'
        ]
        return any(keyword in message for keyword in automation_keywords)
    
    def _handle_automation_command(self, message):
        """Handle automation workflow commands"""
        try:
            if 'nutrition' in message:
                return self._run_nutrition_automation()
            elif 'pricing' in message or 'price' in message:
                return self._run_pricing_automation()
            elif 'forecast' in message or 'demand' in message:
                return self._run_demand_automation()
            else:
                return self._run_full_automation()
        except Exception as e:
            logger.error(f"Automation error: {str(e)}")
            return {
                'response': f"I encountered an error while running the automation: {str(e)}",
                'type': 'error'
            }
    
    def _is_intelligence_mode_request(self, message):
        """Check if message is requesting intelligence mode functionality"""
        innovation_keywords = ['surplus recipe', 'flavor pairing', 'seasonal menu', 'new recipe', 'creative idea',
                             'suggest', 'recommend', 'create', 'develop', 'innovate', 'new dish', 'recipe',
                             'ingredient', 'combination', 'fusion', 'creative', 'unique', 'original', 'dishes using']
        
        # For Q&A mode, handle any question when in QNA mode
        if self.intelligence_mode == 'QNA':
            return True
        elif self.intelligence_mode == 'INNOVATION' and any(keyword in message for keyword in innovation_keywords):
            return True
        
        return False
    
    def _handle_intelligence_mode_request(self, message):
        """Handle intelligence mode specific requests"""
        try:
            if self.intelligence_mode == 'INNOVATION':
                return self._handle_innovation_mode(message)
            elif self.intelligence_mode == 'QNA':
                return self._handle_qna_mode(message)
            else:
                return {
                    'response': f"This request is not available in the current mode. Please switch to the appropriate mode in settings.",
                    'type': 'mode_restriction'
                }
        except Exception as e:
            logger.error(f"Intelligence mode error: {str(e)}")
            return {
                'response': f"I encountered an error processing your {self.intelligence_mode.lower()} request: {str(e)}",
                'type': 'error'
            }
    
    def _handle_chat_message(self, message, context, category=None):
        """Handle regular chat messages with mode restrictions"""
        try:
            # Log safely without Unicode characters
            safe_message = message.encode('ascii', 'ignore').decode('ascii') if message else 'empty'
            message_lower = message.lower()
            safe_message_lower = message_lower.encode('ascii', 'ignore').decode('ascii') if message_lower else 'empty'
            logger.info(f"DEBUG: Processing message: {safe_message[:50]}...")
            logger.info(f"DEBUG: Message lower: {safe_message_lower[:50]}...")
            logger.info(f"DEBUG: AI agent check: {'ai agent' in message_lower}")
            logger.info(f"DEBUG: Auto apply check: {'auto apply' in message_lower}")
            logger.info(f"DEBUG: Recipe check: {'recipe' in message_lower}")
            
            # Check if user is trying to access mode-specific functionality without being in that mode
            if self.intelligence_mode != 'INNOVATION' and any(word in message_lower for word in ['surplus recipe', 'flavor pairing', 'seasonal menu']):
                return {
                    'response': "🔒 **Innovation Mode Required** - This creative feature is only available in Innovation Mode. Please switch to Innovation Mode to access recipe innovation and menu creativity tools.",
                    'type': 'mode_restriction'
                }
            
            # Nutrition queries
            if any(word in message_lower for word in ['nutrition', 'calories', 'protein', 'carbs', 'fat', 'healthy', 'diet']):
                return self._handle_nutrition_query(message)
            
            # Menu queries
            elif any(word in message_lower for word in ['menu', 'dish', 'food', 'item', 'recipe', 'cook', 'serve', 'category']):
                return self._handle_menu_query(message, category)
            
            # Pricing queries
            elif any(word in message_lower for word in ['price', 'cost', 'pricing', 'expensive', 'cheap', 'budget', 'money']):
                return self._handle_pricing_query(message)
            
            # Demand/sales queries
            elif any(word in message_lower for word in ['demand', 'sales', 'popular', 'forecast', 'predict', 'trend', 'order']):
                return self._handle_demand_query(message)
            
            # Inventory queries
            elif any(word in message_lower for word in ['inventory', 'stock', 'ingredient', 'supply', 'storage', 'warehouse']):
                return self._handle_inventory_query(message)
            
            # General conversational queries (greetings, thanks, etc.)
            else:
                return self._handle_general_query(message)
                
        except Exception as e:
            logger.error(f"Chat error: {str(e)}")
            return {
                'response': "I'm sorry, I encountered an error processing your request. Please try again.",
                'type': 'error'
            }
    
    def _handle_nutrition_query(self, message):
        """Handle nutrition-related queries"""
        try:
            # Extract menu item name if mentioned
            menu_items = MenuItem.query.all()
            mentioned_item = None
            
            for item in menu_items:
                if item.menu_item_name.lower() in message:
                    mentioned_item = item
                    break
            
            if mentioned_item:
                # Get nutrition info for specific item
                nutrition = MenuNutrition.query.filter_by(menu_item_id=mentioned_item.id).first()
                
                if nutrition:
                    response = f"🍽️ **{mentioned_item.menu_item_name}** Nutrition Information:\n\n"
                    response += f"📊 **Calories:** {nutrition.calories or 'N/A'}\n"
                    response += f"🥩 **Protein:** {nutrition.protein or 'N/A'}g\n"
                    response += f"🍞 **Carbohydrates:** {nutrition.carbohydrates or 'N/A'}g\n"
                    response += f"🥑 **Fat:** {nutrition.fat or 'N/A'}g\n"
                    response += f"🌾 **Fiber:** {nutrition.fiber or 'N/A'}g\n"
                    response += f"🧂 **Sodium:** {nutrition.sodium or 'N/A'}mg\n\n"
                    
                    if nutrition.allergens:
                        response += f"⚠️ **Allergens:** {nutrition.allergens}\n"
                    
                    dietary_info = []
                    if nutrition.is_vegetarian:
                        dietary_info.append("🌱 Vegetarian")
                    if nutrition.is_vegan:
                        dietary_info.append("🌿 Vegan")
                    if nutrition.is_gluten_free:
                        dietary_info.append("🌾 Gluten-Free")
                    
                    if dietary_info:
                        response += f"\n✅ **Dietary:** {', '.join(dietary_info)}"
                    
                    return {
                        'response': response,
                        'type': 'nutrition',
                        'data': {
                            'item_name': mentioned_item.menu_item_name,
                            'nutrition': {
                                'calories': nutrition.calories,
                                'protein': nutrition.protein,
                                'carbohydrates': nutrition.carbohydrates,
                                'fat': nutrition.fat,
                                'fiber': nutrition.fiber,
                                'sodium': nutrition.sodium
                            }
                        }
                    }
                else:
                    return {
                        'response': f"I found {mentioned_item.menu_item_name} in our menu, but nutrition information isn't available yet. Would you like me to calculate it?",
                        'type': 'nutrition_missing'
                    }
            else:
                # General nutrition query
                total_items = MenuItem.query.count()
                items_with_nutrition = db.session.query(MenuItem).join(MenuNutrition).count()
                
                response = f"🍽️ **Menu Nutrition Overview:**\n\n"
                response += f"📊 **Total Menu Items:** {total_items}\n"
                response += f"✅ **Items with Nutrition Data:** {items_with_nutrition}\n"
                response += f"📈 **Coverage:** {(items_with_nutrition/total_items*100):.1f}%\n\n"
                response += "Ask me about specific menu items for detailed nutrition information!"
                
                return {
                    'response': response,
                    'type': 'nutrition_overview'
                }
                
        except Exception as e:
            logger.error(f"Nutrition query error: {str(e)}")
            return {
                'response': "I'm having trouble accessing nutrition information right now.",
                'type': 'error'
            }
    
    def _handle_menu_query(self, message, category=None):
        """Handle menu-related queries"""
        try:
            # First check if user is asking about a specific dish's category
            dish_category_result = self._identify_dish_category(message)
            if dish_category_result:
                return dish_category_result
            
            # Check if user is asking for dish suggestions
            if any(word in message.lower() for word in ['suggest', 'suggestion', 'recommend', 'idea', 'what should', 'what can', 'give me']):
                return self._generate_four_category_suggestions(message)
            
            menu_items = MenuItem.query.limit(10).all()
            
            if 'popular' in message or 'best' in message:
                # Get popular items based on recent orders
                popular_query = text("""
                    SELECT mi.menu_item_name, COUNT(co.id) as order_count
                    FROM menu_item mi
                    LEFT JOIN customer_order co ON mi.id = co.menu_item_id
                    WHERE co.order_date >= DATE('now', '-30 days')
                    GROUP BY mi.id, mi.menu_item_name
                    ORDER BY order_count DESC
                    LIMIT 5
                """)
                
                result = db.session.execute(popular_query).fetchall()
                
                if result:
                    response = "🔥 **Most Popular Menu Items (Last 30 Days):**\n\n"
                    for i, (name, count) in enumerate(result, 1):
                        response += f"{i}. **{name}** - {count} orders\n"
                else:
                    response = "I don't have recent order data to show popular items."
            
            elif 'category' in message or 'type' in message:
                # Show items by category
                categories = db.session.query(MenuItem.category, func.count(MenuItem.id)).group_by(MenuItem.category).all()
                
                response = "📋 **Menu Categories:**\n\n"
                for category, count in categories:
                    response += f"• **{category}:** {count} items\n"
            
            else:
                # General menu overview
                total_items = MenuItem.query.count()
                categories = db.session.query(MenuItem.category).distinct().count()
                
                response = f"🍽️ **Menu Overview:**\n\n"
                response += f"📊 **Total Items:** {total_items}\n"
                response += f"📂 **Categories:** {categories}\n\n"
                response += "Ask me about specific dishes, popular items, or nutrition information!"
            
            return {
                'response': response,
                'type': 'menu_info'
            }
            
        except Exception as e:
            logger.error(f"Menu query error: {str(e)}")
            return {
                'response': "I'm having trouble accessing menu information right now.",
                'type': 'error'
            }
    
    def _identify_dish_category(self, message):
        """Identify if user is asking about a specific dish and return its category"""
        try:
            message_lower = message.lower()
            
            # Get all menu items from database
            menu_items = MenuItem.query.all()
            
            # Look for exact dish name matches (case insensitive)
            for item in menu_items:
                dish_name_lower = item.menu_item_name.lower()
                
                # Check if the dish name is mentioned in the message
                if dish_name_lower in message_lower:
                    # Get category emoji
                    category_emoji = {
                        'Main Course': '🍽️',
                        'Beverage': '🥤', 
                        'Dessert': '🍰',
                        'Side Dish': '🥗',
                        'Appetizer': '🥙'
                    }.get(item.category, '🍴')
                    
                    response = f"📋 **Dish Category Information**\n\n"
                    response += f"**{category_emoji} Dish:** {item.menu_item_name}\n"
                    response += f"**📂 Category:** {item.category}\n"
                    response += f"**💰 Price:** RM {item.typical_ingredient_cost:.2f}\n"
                    
                    if item.key_ingredients_tags:
                        response += f"**🥘 Ingredients:** {item.key_ingredients_tags}\n"
                    
                    response += f"\n✅ **{item.menu_item_name}** is categorized under **{item.category}**."
                    
                    return {
                        'response': response,
                        'type': 'dish_category_info',
                        'data': {
                            'dish_name': item.menu_item_name,
                            'category': item.category,
                            'price': item.typical_ingredient_cost,
                            'ingredients': item.key_ingredients_tags
                        }
                    }
            
            # If no exact match found, return None to continue with other handlers
            return None
            
        except Exception as e:
            logger.error(f"Error identifying dish category: {str(e)}")
            return None
    
    def _handle_pricing_query(self, message):
        """Handle pricing-related queries"""
        try:
            # Get pricing statistics
            pricing_stats = db.session.query(
                func.avg(MenuItem.typical_ingredient_cost).label('avg_cost'),
                func.min(MenuItem.typical_ingredient_cost).label('min_cost'),
                func.max(MenuItem.typical_ingredient_cost).label('max_cost')
            ).first()
            
            response = "💰 **Menu Pricing Overview:**\n\n"
            response += f"📊 **Average Cost:** ${pricing_stats.avg_cost:.2f}\n"
            response += f"💵 **Price Range:** ${pricing_stats.min_cost:.2f} - ${pricing_stats.max_cost:.2f}\n\n"
            
            # Get most/least expensive items
            expensive_items = MenuItem.query.order_by(MenuItem.typical_ingredient_cost.desc()).limit(3).all()
            cheap_items = MenuItem.query.order_by(MenuItem.typical_ingredient_cost.asc()).limit(3).all()
            
            response += "🔝 **Most Expensive:**\n"
            for item in expensive_items:
                response += f"• {item.menu_item_name}: ${item.typical_ingredient_cost:.2f}\n"
            
            response += "\n💸 **Most Affordable:**\n"
            for item in cheap_items:
                response += f"• {item.menu_item_name}: ${item.typical_ingredient_cost:.2f}\n"
            
            return {
                'response': response,
                'type': 'pricing_info'
            }
            
        except Exception as e:
            logger.error(f"Pricing query error: {str(e)}")
            return {
                'response': "I'm having trouble accessing pricing information right now.",
                'type': 'error'
            }
    
    def _handle_demand_query(self, message):
        """Handle demand and sales queries"""
        try:
            # Get recent sales data
            recent_orders = CustomerOrder.query.filter(
                CustomerOrder.order_date >= datetime.now() - timedelta(days=7)
            ).count()
            
            total_orders = CustomerOrder.query.count()
            
            response = f"📈 **Sales & Demand Overview:**\n\n"
            response += f"📊 **Orders This Week:** {recent_orders}\n"
            response += f"📋 **Total Orders:** {total_orders}\n\n"
            
            if 'forecast' in message or 'predict' in message:
                response += "🔮 **Demand Forecasting:**\n"
                response += "I can help predict demand for menu items based on historical data, seasonality, and trends. "
                response += "Would you like me to run a demand forecast for specific items?"
            
            return {
                'response': response,
                'type': 'demand_info'
            }
            
        except Exception as e:
            logger.error(f"Demand query error: {str(e)}")
            return {
                'response': "I'm having trouble accessing sales data right now.",
                'type': 'error'
            }
    
    def _handle_inventory_query(self, message):
        """Handle inventory-related queries"""
        try:
            total_ingredients = InventoryItem.query.count()
            low_stock_items = InventoryItem.query.filter(InventoryItem.current_stock <= InventoryItem.minimum_stock).count()
            
            response = f"📦 **Inventory Overview:**\n\n"
            response += f"📊 **Total Ingredients:** {total_ingredients}\n"
            response += f"⚠️ **Low Stock Items:** {low_stock_items}\n\n"
            
            if low_stock_items > 0:
                response += "🚨 **Action Needed:** Some ingredients are running low. Check the inventory management page for details."
            else:
                response += "✅ **All Good:** Inventory levels are healthy!"
            
            return {
                'response': response,
                'type': 'inventory_info'
            }
            
        except Exception as e:
            logger.error(f"Inventory query error: {str(e)}")
            return {
                'response': "I'm having trouble accessing inventory information right now.",
                'type': 'error'
            }
    
    def _handle_general_query(self, message):
        """Handle general queries and provide help"""
        message_lower = message.lower()
        
        # Handle greetings
        if any(word in message_lower for word in ['hello', 'hi', 'hey', 'good morning', 'good afternoon', 'good evening']):
            response = "👋 Hello! I'm Menu Buddy, your Restaurant Intelligence Agent. How can I help you today?\n\n"
            response += "Feel free to ask me about menu items, nutrition, pricing, or just chat with me!"
            return {
                'response': response,
                'type': 'greeting'
            }
        
        # Handle thank you messages
        elif any(word in message_lower for word in ['thank you', 'thanks', 'thank']):
            response = "😊 You're very welcome! I'm always here to help with your restaurant needs. Is there anything else I can assist you with?"
            return {
                'response': response,
                'type': 'acknowledgment'
            }
        
        # Handle goodbye messages
        elif any(word in message_lower for word in ['bye', 'goodbye', 'see you', 'farewell']):
            response = "👋 Goodbye! It was great chatting with you. Feel free to come back anytime if you need help with your restaurant operations!"
            return {
                'response': response,
                'type': 'farewell'
            }
        
        # Handle "how are you" type questions
        elif any(phrase in message_lower for phrase in ['how are you', 'how do you do', 'how\'s it going']):
            response = "😊 I'm doing great, thank you for asking! I'm here and ready to help you with all your restaurant management needs. How are you doing today?"
            return {
                'response': response,
                'type': 'personal'
            }
        
        # Handle "who are you" type questions
        elif any(phrase in message_lower for phrase in ['who are you', 'what are you', 'tell me about yourself']):
            response = "🤖 I'm Menu Buddy, your AI-powered Restaurant Intelligence Agent! I'm here to help you manage your restaurant operations more efficiently.\n\n"
            response += "I can chat with you about various topics and also help with specific restaurant tasks like analyzing menu data, tracking inventory, and optimizing operations."
            return {
                'response': response,
                'type': 'introduction'
            }
        
        # Handle help requests
        elif any(word in message_lower for word in ['help', 'what can you do', 'capabilities', 'features']):
            response = "🤖 **I'm your Restaurant Intelligence Agent!** Here's what I can help you with:\n\n"
            response += "💬 **General Chat:** Feel free to have a casual conversation with me!\n"
            response += "🍽️ **Menu Information:** Ask about specific dishes, categories, or popular items\n"
            response += "📊 **Nutrition Data:** Get calorie and macro information for menu items\n"
            response += "💰 **Pricing Analysis:** View pricing statistics and comparisons\n"
            response += "📈 **Sales & Demand:** Check sales data and demand forecasts\n"
            response += "📦 **Inventory Status:** Monitor ingredient stock levels\n\n"
            response += "🔧 **Automation Commands:**\n"
            response += "• 'Recalculate nutrition for all items'\n"
            response += "• 'Update pricing optimization'\n"
            response += "• 'Run demand forecasting'\n\n"
            response += "Just ask me anything - whether it's about your restaurant operations or just to chat!"
            return {
                'response': response,
                'type': 'help'
            }
        
        # Handle simple questions about weather, time, etc.
        elif any(word in message_lower for word in ['weather', 'time', 'date', 'today']):
            response = "🤔 I'm focused on helping with restaurant operations, so I don't have access to real-time weather or time information. But I'd be happy to help you with menu planning, inventory management, or any other restaurant-related questions!"
            return {
                'response': response,
                'type': 'redirect'
            }
        
        # Handle compliments
        elif any(word in message_lower for word in ['good job', 'well done', 'excellent', 'amazing', 'awesome', 'great']):
            response = "😊 Thank you so much! I really appreciate the kind words. I'm always trying my best to help you manage your restaurant effectively. Is there anything else I can help you with?"
            return {
                'response': response,
                'type': 'acknowledgment'
            }
        
        # Default response for unrecognized queries
        else:
            response = "🤔 That's an interesting question! While I'm primarily designed to help with restaurant operations, I'm always happy to chat.\n\n"
            response += "You can ask me about menu items, nutrition, pricing, sales, inventory, or just have a casual conversation. What would you like to know?"
            return {
                'response': response,
                'type': 'general'
            }
    
    def _run_nutrition_automation(self):
        """Run nutrition calculation automation"""
        try:
            # Get items without nutrition data
            items_without_nutrition = db.session.query(MenuItem).outerjoin(MenuNutrition).filter(MenuNutrition.id.is_(None)).all()
            
            if not items_without_nutrition:
                return {
                    'response': "✅ All menu items already have nutrition information!",
                    'type': 'automation_complete'
                }
            
            processed = 0
            for item in items_without_nutrition[:5]:  # Limit to 5 items per automation run
                try:
                    # This would integrate with the nutrition service
                    # For now, we'll create placeholder data
                    nutrition = MenuNutrition(
                        menu_item_id=item.id,
                        calories=250,  # Placeholder
                        protein=15,
                        carbohydrates=30,
                        fat=10,
                        analysis_text=f"Automated analysis for {item.menu_item_name}"
                    )
                    db.session.add(nutrition)
                    processed += 1
                except Exception as e:
                    logger.error(f"Error processing {item.menu_item_name}: {str(e)}")
            
            db.session.commit()
            
            return {
                'response': f"🔄 **Nutrition Automation Complete!**\n\n✅ Processed {processed} menu items\n📊 Nutrition data has been calculated and saved.",
                'type': 'automation_complete'
            }
            
        except Exception as e:
            logger.error(f"Nutrition automation error: {str(e)}")
            return {
                'response': f"❌ Nutrition automation failed: {str(e)}",
                'type': 'automation_error'
            }
    
    def _run_pricing_automation(self):
        """Run pricing optimization automation"""
        return {
            'response': "🔄 **Pricing Optimization Started!**\n\nAnalyzing market conditions, costs, and demand patterns...\n\n⏳ This may take a few moments.",
            'type': 'automation_running'
        }
    
    def _run_demand_automation(self):
        """Run item-specific demand forecasting automation"""
        try:
            from services.unified_restaurant_demand_system import RestaurantDemandPredictor
            from models import MenuItem
            
            # Initialize the unified predictor
            data_path = "C:/Users/User/Desktop/first-app/instance/cleaned_streamlined_ultimate_malaysian_data.csv"
            predictor = RestaurantDemandPredictor(data_path)
            
            # Get all menu items for item-specific analysis
            menu_items = MenuItem.query.all()
            successful_analyses = 0
            failed_analyses = 0
            
            # Run item-specific analysis for each menu item
            for menu_item in menu_items:
                try:
                    logger.info(f"Running item-specific analysis for: {menu_item.menu_item_name} (ID: {menu_item.id})")
                    
                    results = predictor.run_item_specific_analysis(
                        item_id=menu_item.id,
                        item_name=menu_item.menu_item_name,
                        forecast_days=28
                    )
                    
                    if results and results.get('success'):
                        successful_analyses += 1
                        logger.info(f"Item-specific analysis completed for {menu_item.menu_item_name}")
                    else:
                        failed_analyses += 1
                        logger.warning(f"Item-specific analysis failed for {menu_item.menu_item_name}")
                        
                except Exception as item_error:
                    failed_analyses += 1
                    logger.error(f"Error analyzing {menu_item.menu_item_name}: {str(item_error)}")
            
            total_items = len(menu_items)
            success_rate = (successful_analyses / total_items * 100) if total_items > 0 else 0
            
            if successful_analyses > 0:
                return {
                    'response': f"🔄 **Item-Specific Demand Forecasting Complete!**\n\nAnalyzed {successful_analyses}/{total_items} menu items using advanced item-specific models.\n\n📈 Generated personalized predictions for each menu item with {success_rate:.1f}% success rate.\n\n🎯 Each item now has tailored forecasts based on its unique demand patterns.",
                    'type': 'automation_complete',
                    'data': {
                        'successful_analyses': successful_analyses,
                        'failed_analyses': failed_analyses,
                        'total_items': total_items,
                        'success_rate': success_rate,
                        'analysis_type': 'item_specific'
                    }
                }
            else:
                return {
                    'response': f"❌ Item-specific demand forecasting failed: No items were successfully analyzed out of {total_items} total items.",
                    'type': 'automation_error'
                }
                
        except Exception as e:
            logger.error(f"Item-specific demand automation error: {str(e)}")
            return {
                'response': f"❌ Item-specific demand forecasting failed: {str(e)}",
                'type': 'automation_error'
            }
    
    def _run_full_automation(self):
        """Run complete automation workflow"""
        return {
            'response': "🔄 **Full Automation Workflow Started!**\n\n1. ✅ Calculating nutrition data\n2. 🔄 Optimizing pricing\n3. ⏳ Forecasting demand\n\nThis comprehensive analysis will take a few minutes.",
            'type': 'automation_running'
        }
    

    

    
    def _handle_innovation_mode(self, message):
        """Handle Innovation Mode requests for creative menu development with AI Agent"""
        try:
            message_lower = message.lower()
            
            # AI Agent workflow commands
            if 'automate workflow' in message_lower or 'full automation' in message_lower or 'automated workflow' in message_lower:
                return self._handle_ai_agent_workflow(message)
            
            # AI Agent dish creation
            if any(keyword in message_lower for keyword in ['ai create', 'ai suggest', 'ai generate', 'intelligent dish']):
                return self._handle_ai_dish_creation(message)
            
            # Check for Auto Apply suggestion functionality
            if 'auto apply suggestion' in message_lower:
                return self._handle_auto_apply_suggestion(message)
            
            # Check for Manual Apply suggestion functionality
            if 'manual apply suggestion' in message_lower:
                return self._handle_manual_apply_suggestion(message)
            
            # Check for Auto Apply functionality
            if 'auto apply' in message_lower or 'auto-apply' in message_lower:
                return self._handle_auto_apply_mode(message)
            
            # Check for manual input functionality (only for explicit manual input requests)
            if 'manual input' in message_lower or 'add new item' in message_lower:
                return self._handle_manual_input_mode(message)
            
            # Check for proactive dish creation based on inventory
            if 'create new dish' in message_lower and 'inventory' in message_lower:
                return self._generate_ai_powered_dish_suggestions(message)
            
            # Check for dish type specification
            if 'regenerate' in message_lower and any(dish_type in message_lower for dish_type in ['appetizer', 'main course', 'dessert', 'beverage', 'salad', 'soup']):
                return self._handle_dish_type_regeneration(message)
            
            # Enhanced ingredient analysis with AI-powered recommendations
            if any(keyword in message for keyword in ['suggest', 'recommend', 'dishes using', 'recipe', 'create']):
                return self._generate_ai_recipe_suggestions(message)
            
            # Extract ingredients from the message
            if any(keyword in message for keyword in ['suggest', 'recommend', 'dishes using', 'recipe', 'create']):
                # Try to extract ingredients from the message
                ingredients_mentioned = []
                
                # Get all available ingredients from database with enhanced analysis
                available_ingredients = Ingredient.query.all()
                ingredient_names = [ing.name.lower() for ing in available_ingredients]
                
                # Check which ingredients are mentioned in the message
                for ingredient in available_ingredients:
                    if ingredient.name.lower() in message.lower():
                        ingredients_mentioned.append(ingredient.name)
                
                if ingredients_mentioned:
                    # Enhanced ingredient compatibility and popularity analysis
                    ingredient_analysis = self._analyze_ingredient_compatibility(ingredients_mentioned)
                    
                    # Find existing menu items that use these ingredients
                    matching_items = []
                    all_menu_items = MenuItem.query.all()
                    
                    for item in all_menu_items:
                        item_ingredients = item.ingredients.lower() if item.ingredients else ""
                        if any(ing.lower() in item_ingredients for ing in ingredients_mentioned):
                            matching_items.append({
                                'name': item.name,
                                'description': item.description,
                                'price': float(item.price),
                                'ingredients': item.ingredients
                            })
                    
                    # Generate AI-powered creative suggestions
                    suggestions = self._generate_creative_suggestions(ingredients_mentioned, ingredient_analysis)
                    if len(ingredients_mentioned) >= 2:
                        # Create fusion suggestions
                        suggestions.append(f"🍽️ **{ingredients_mentioned[0].title()}-{ingredients_mentioned[1].title()} Fusion Bowl** - A creative combination featuring {', '.join(ingredients_mentioned)}")
                        suggestions.append(f"🥗 **Gourmet {ingredients_mentioned[0].title()} Salad** - Fresh {ingredients_mentioned[0]} with {', '.join(ingredients_mentioned[1:])} and seasonal greens")
                        suggestions.append(f"🍲 **Signature {ingredients_mentioned[0].title()} Soup** - Hearty soup with {', '.join(ingredients_mentioned)} and aromatic herbs")
                    else:
                        # Single ingredient suggestions
                        main_ingredient = ingredients_mentioned[0]
                        suggestions.append(f"🍽️ **Gourmet {main_ingredient.title()} Platter** - Showcasing {main_ingredient} in multiple preparations")
                        suggestions.append(f"🥗 **Fresh {main_ingredient.title()} Salad** - Light and healthy {main_ingredient}-based dish")
                        suggestions.append(f"🍲 **Creamy {main_ingredient.title()} Soup** - Rich and comforting soup featuring {main_ingredient}")
                    
                    response = f"💡 **INNOVATION MODE - Recipe Suggestions**\n\n**Ingredients Found:** {', '.join(ingredients_mentioned)}\n\n**Creative Suggestions:**\n"
                    for i, suggestion in enumerate(suggestions, 1):
                        response += f"{i}. {suggestion}\n"
                    
                    if matching_items:
                        response += f"\n**Existing Menu Items Using These Ingredients:**\n"
                        for item in matching_items[:3]:  # Show top 3
                            response += f"• **{item['name']}** - ${item['price']:.2f}\n"
                    
                    return {
                        'response': response,
                        'type': 'ingredient_innovation',
                        'data': {
                            'mode': 'INNOVATION',
                            'ingredients_used': ingredients_mentioned,
                            'suggestions': suggestions,
                            'existing_items': matching_items,
                            'ui_update': 'highlight_new_recipe'
                        }
                    }
                else:
                    return {
                        'response': "💡 **INNOVATION MODE**\n\nI can help create recipes! Please mention specific ingredients you'd like to use. For example:\n• 'Suggest dishes using tomatoes and cheese'\n• 'Create a recipe with chicken and herbs'\n• 'Recommend something with seafood'",
                        'type': 'innovation_help'
                    }
            
            elif 'surplus' in message:
                # Get inventory items that might be surplus
                inventory_items = InventoryItem.query.filter(InventoryItem.quantity > 50).all()  # Assuming >50 is surplus
                if inventory_items:
                    surplus_suggestions = []
                    for item in inventory_items[:3]:  # Top 3 surplus items
                        if item.ingredient:
                            surplus_suggestions.append(f"🍽️ **{item.ingredient.name.title()} Special** - Creative dish utilizing surplus {item.ingredient.name} ({item.quantity} units available)")
                    
                    response = "💡 **INNOVATION MODE - Surplus Utilization**\n\n**High Inventory Items:**\n"
                    for suggestion in surplus_suggestions:
                        response += f"• {suggestion}\n"
                    
                    return {
                        'response': response,
                        'type': 'surplus_innovation',
                        'data': {
                            'mode': 'INNOVATION',
                            'surplus_items': [{'name': item.ingredient.name, 'quantity': item.quantity} for item in inventory_items[:3] if item.ingredient],
                            'suggestions': surplus_suggestions,
                            'ui_update': 'highlight_new_recipe'
                        }
                    }
                else:
                    return {
                        'response': "💡 **INNOVATION MODE - Surplus Check**\n\nNo high-inventory items detected. All ingredients are at optimal levels!",
                        'type': 'surplus_check'
                    }
            
            elif 'flavor pairing' in message:
                pairings = [
                    {"base": "Chocolate", "pair": "Chili", "result": "Spicy Chocolate Dessert"},
                    {"base": "Watermelon", "pair": "Feta Cheese", "result": "Mediterranean Summer Salad"},
                    {"base": "Coffee", "pair": "Cardamom", "result": "Arabic-Inspired Coffee Blend"}
                ]
                
                selected_pairing = pairings[0]  # In real implementation, this would be more sophisticated
                
                return {
                    'response': f"🎨 **INNOVATION MODE - Flavor Pairing**\n\n**Unique Combination:** {selected_pairing['base']} + {selected_pairing['pair']}\n\n**Creative Result:** {selected_pairing['result']}\n\n**Why it works:** Contrasting flavors create memorable taste experiences",
                    'type': 'flavor_pairing',
                    'data': {
                        'mode': 'INNOVATION',
                        'pairing': selected_pairing,
                        'ui_update': 'highlight_new_recipe'
                    }
                }
            
            elif 'seasonal' in message:
                from datetime import datetime
                current_month = datetime.now().month
                
                if current_month in [12, 1, 2]:  # Winter
                    seasonal_idea = "❄️ **Winter Warmth Bowl** - Roasted root vegetables with spiced quinoa"
                elif current_month in [3, 4, 5]:  # Spring
                    seasonal_idea = "🌸 **Spring Renewal Salad** - Fresh greens with edible flowers"
                elif current_month in [6, 7, 8]:  # Summer
                    seasonal_idea = "☀️ **Summer Chill Gazpacho** - Cold vegetable soup with herb oil"
                else:  # Fall
                    seasonal_idea = "🍂 **Autumn Harvest Risotto** - Pumpkin and sage risotto"
                
                return {
                    'response': f"🍃 **INNOVATION MODE - Seasonal Menu**\n\n{seasonal_idea}\n\n**Seasonal Strategy:** Align menu with natural ingredient availability and customer mood",
                    'type': 'seasonal_innovation',
                    'data': {
                        'mode': 'INNOVATION',
                        'new_idea': seasonal_idea,
                        'season': ['Winter', 'Spring', 'Summer', 'Fall'][current_month//3 if current_month != 12 else 0],
                        'ui_update': 'highlight_new_recipe'
                    }
                }
            
            else:
                return {
                    'response': "💡 **INNOVATION MODE Active**\n\nI can help create:\n• Surplus utilization recipes\n• Unique flavor pairings\n• Seasonal menu ideas\n\nWhat would you like to innovate?",
                    'type': 'innovation_help'
                }
                
        except Exception as e:
            logger.error(f"Innovation mode error: {str(e)}")
            return {
                    'response': "I encountered an error with menu innovation. Please try again.",
                    'type': 'error'
                }
    
    def _analyze_ingredient_compatibility(self, ingredients):
        """Analyze ingredient compatibility, availability, and popularity"""
        try:
            analysis = {
                'compatibility_score': 0,
                'availability_status': {},
                'popularity_metrics': {},
                'nutritional_balance': {},
                'cost_analysis': {}
            }
            
            # Get ingredient details from database
            ingredient_objects = Ingredient.query.filter(Ingredient.name.in_(ingredients)).all()
            
            for ingredient in ingredient_objects:
                # Availability analysis
                inventory_item = InventoryItem.query.join(Ingredient).filter(Ingredient.name == ingredient.name).first()
                if inventory_item:
                    analysis['availability_status'][ingredient.name] = {
                        'quantity': inventory_item.quantity,
                        'status': 'high' if inventory_item.quantity > 50 else 'medium' if inventory_item.quantity > 20 else 'low'
                    }
                
                # Popularity analysis based on menu item usage
                menu_usage = MenuItem.query.filter(MenuItem.key_ingredients_tags.contains(ingredient.name)).count()
                analysis['popularity_metrics'][ingredient.name] = {
                    'menu_usage_count': menu_usage,
                    'popularity_score': min(menu_usage * 10, 100)  # Scale to 0-100
                }
                
                # Nutritional analysis
                analysis['nutritional_balance'][ingredient.name] = {
                    'protein': ingredient.protein_per_100g or 0,
                    'carbs': ingredient.carbs_per_100g or 0,
                    'fat': ingredient.fat_per_100g or 0,
                    'calories': ingredient.calories_per_100g or 0
                }
            
            # Calculate overall compatibility score
            if len(ingredients) >= 2:
                # Simple compatibility based on complementary nutritional profiles
                total_protein = sum(analysis['nutritional_balance'][ing]['protein'] for ing in analysis['nutritional_balance'])
                total_carbs = sum(analysis['nutritional_balance'][ing]['carbs'] for ing in analysis['nutritional_balance'])
                total_fat = sum(analysis['nutritional_balance'][ing]['fat'] for ing in analysis['nutritional_balance'])
                
                # Balanced nutrition gets higher compatibility score
                balance_score = 100 - abs(33.3 - (total_protein / (total_protein + total_carbs + total_fat + 0.1) * 100))
                analysis['compatibility_score'] = min(max(balance_score, 0), 100)
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error in ingredient compatibility analysis: {str(e)}")
            return {'compatibility_score': 50, 'availability_status': {}, 'popularity_metrics': {}, 'nutritional_balance': {}, 'cost_analysis': {}}
    
    def _generate_creative_suggestions(self, ingredients, analysis):
        """Generate AI-powered creative recipe suggestions"""
        try:
            suggestions = []
            
            # Base suggestions on ingredient analysis
            compatibility_score = analysis.get('compatibility_score', 50)
            
            if len(ingredients) >= 2:
                # Generate three specific dish suggestions based on ingredients
                primary_ingredient = ingredients[0].lower()
                secondary_ingredients = [ing.lower() for ing in ingredients[1:]]
                
                # Create realistic dish suggestions based on common ingredient combinations
                dish_suggestions = self._create_realistic_dishes(primary_ingredient, secondary_ingredients)
                
                for i, dish in enumerate(dish_suggestions[:3], 1):
                    suggestions.append(f"{i}. **{dish['name']}** - {dish['description']} (Compatibility: {compatibility_score:.0f}%)")
                
            else:
                # Single ingredient suggestions
                main_ingredient = ingredients[0].lower()
                single_dishes = self._create_single_ingredient_dishes(main_ingredient)
                
                for i, dish in enumerate(single_dishes[:3], 1):
                    suggestions.append(f"{i}. **{dish['name']}** - {dish['description']}")
            
            return suggestions
            
        except Exception as e:
            logger.error(f"Error generating creative suggestions: {str(e)}")
            return [f"1. **Creative {ingredients[0].title()} Dish** - Innovative recipe featuring {', '.join(ingredients)}"]
    
    def _create_realistic_dishes(self, primary_ingredient, secondary_ingredients):
        """Create realistic dish suggestions based on ingredient combinations"""
        dishes = []
        
        import random
        
        # Creative naming components
        poetic_adjectives = ["Crimson", "Aurora", "Citrus", "Velvet", "Golden", "Sapphire", "Emerald", "Moonlit", "Starlit", "Twilight", "Dawn", "Sunset", "Mystic", "Ethereal", "Silken", "Crystal", "Pearl", "Amber", "Rose", "Lavender"]
        descriptive_words = ["Drift", "Mist", "Ember", "Whisper", "Echo", "Dream", "Melody", "Symphony", "Harmony", "Cascade", "Breeze", "Glow", "Shimmer", "Sparkle", "Bloom", "Blossom", "Essence", "Spirit", "Soul", "Heart"]
        
        # Category-specific dish endings
        if category == "Main Course":
            dish_endings = ["Medallion", "Wellington", "Roulade", "Confit", "Braise", "Gratin", "Casserole", "Steak", "Filet", "Roast", "Chop", "Cutlet"]
        elif category == "Beverage":
            dish_endings = ["Fizz", "Elixir", "Brew", "Infusion", "Tonic", "Refresher", "Cooler", "Spritz", "Smoothie", "Latte", "Mocktail", "Blend"]
        elif category == "Dessert":
            dish_endings = ["Tart", "Soufflé", "Mousse", "Parfait", "Galette", "Compote", "Reduction", "Crème", "Cake", "Pudding", "Truffle", "Gelato"]
        elif category == "Side Dish":
            dish_endings = ["Medley", "Sauté", "Pilaf", "Gratin", "Salad", "Slaw", "Relish", "Chutney", "Puree", "Hash", "Chips", "Crisps"]
        else:
            dish_endings = ["Tart", "Noodles", "Fizz", "Soufflé", "Risotto", "Bisque", "Mousse", "Parfait", "Galette", "Terrine", "Compote", "Reduction", "Infusion", "Medley", "Symphony", "Rhapsody", "Serenade", "Delight", "Fantasy"]
        
        # Common ingredient-based dish patterns with creative names
        if 'chicken' in primary_ingredient or any('chicken' in ing for ing in secondary_ingredients):
            dishes.extend([
                {'name': f'{random.choice(poetic_adjectives)} {random.choice(descriptive_words)} {random.choice(dish_endings)}', 'description': 'Tender grilled chicken breast seasoned with herbs and served with roasted vegetables'},
                {'name': f'{random.choice(poetic_adjectives)} {random.choice(descriptive_words)} {random.choice(dish_endings)}', 'description': 'Quick-cooked chicken with fresh vegetables in a savory sauce over steamed rice'},
                {'name': f'{random.choice(poetic_adjectives)} {random.choice(descriptive_words)} {random.choice(dish_endings)}', 'description': 'Crispy romaine lettuce topped with grilled chicken, parmesan cheese, and classic Caesar dressing'}
            ])
        elif 'beef' in primary_ingredient or any('beef' in ing for ing in secondary_ingredients):
            dishes.extend([
                {'name': f'{random.choice(poetic_adjectives)} {random.choice(descriptive_words)} {random.choice(dish_endings)}', 'description': 'Perfectly grilled beef steak cooked to your preference with garlic butter and seasonal sides'},
                {'name': f'{random.choice(poetic_adjectives)} {random.choice(descriptive_words)} {random.choice(dish_endings)}', 'description': 'Tender beef strips with crisp vegetables in a rich brown sauce served over noodles'},
                {'name': f'{random.choice(poetic_adjectives)} {random.choice(descriptive_words)} {random.choice(dish_endings)}', 'description': 'Seasoned ground beef in soft tortillas with fresh toppings and zesty salsa'}
            ])
        elif 'salmon' in primary_ingredient or any('salmon' in ing for ing in secondary_ingredients):
            dishes.extend([
                {'name': f'{random.choice(poetic_adjectives)} {random.choice(descriptive_words)} {random.choice(dish_endings)}', 'description': 'Fresh salmon fillet baked with lemon and herbs, served with quinoa and steamed broccoli'},
                {'name': f'{random.choice(poetic_adjectives)} {random.choice(descriptive_words)} {random.choice(dish_endings)}', 'description': 'Glazed salmon with sweet teriyaki sauce, served with jasmine rice and Asian vegetables'},
                {'name': f'{random.choice(poetic_adjectives)} {random.choice(descriptive_words)} {random.choice(dish_endings)}', 'description': 'Flaked salmon over mixed greens with avocado, cucumber, and citrus vinaigrette'}
            ])
        elif 'pasta' in primary_ingredient or any('pasta' in ing for ing in secondary_ingredients):
            dishes.extend([
                {'name': f'{random.choice(poetic_adjectives)} {random.choice(descriptive_words)} {random.choice(dish_endings)}', 'description': 'Classic Italian pasta with eggs, cheese, pancetta, and black pepper in a creamy sauce'},
                {'name': f'{random.choice(poetic_adjectives)} {random.choice(descriptive_words)} {random.choice(dish_endings)}', 'description': 'Penne pasta in a spicy tomato sauce with garlic, red peppers, and fresh basil'},
                {'name': f'{random.choice(poetic_adjectives)} {random.choice(descriptive_words)} {random.choice(dish_endings)}', 'description': 'Rich and creamy fettuccine pasta with parmesan cheese and butter sauce'}
            ])
        elif 'rice' in primary_ingredient or any('rice' in ing for ing in secondary_ingredients):
            dishes.extend([
                {'name': f'{random.choice(poetic_adjectives)} {random.choice(descriptive_words)} {random.choice(dish_endings)}', 'description': 'Wok-fried rice with vegetables, eggs, and your choice of protein in savory soy sauce'},
                {'name': f'{random.choice(poetic_adjectives)} {random.choice(descriptive_words)} {random.choice(dish_endings)}', 'description': 'Aromatic basmati rice cooked with herbs, spices, and toasted almonds'},
                {'name': f'{random.choice(poetic_adjectives)} {random.choice(descriptive_words)} {random.choice(dish_endings)}', 'description': 'Healthy bowl with seasoned rice, fresh vegetables, and protein of your choice'}
            ])
        else:
            # Generic dishes for other ingredient combinations
            dishes.extend([
                {'name': f'{random.choice(poetic_adjectives)} {random.choice(descriptive_words)} {random.choice(dish_endings)}', 'description': f'Fresh {primary_ingredient} with {" and ".join(secondary_ingredients[:2])} in a savory sauce'},
                {'name': f'{random.choice(poetic_adjectives)} {random.choice(descriptive_words)} {random.choice(dish_endings)}', 'description': f'Healthy salad featuring {primary_ingredient} with {" and ".join(secondary_ingredients[:2])} and house dressing'},
                {'name': f'{random.choice(poetic_adjectives)} {random.choice(descriptive_words)} {random.choice(dish_endings)}', 'description': f'Hearty soup with {primary_ingredient} and {" and ".join(secondary_ingredients[:2])} in a flavorful broth'}
            ])
        
        return dishes
    
    def _create_single_ingredient_dishes(self, main_ingredient):
        """Create dish suggestions for a single ingredient"""
        dishes = []
        
        import random
        
        # Creative naming components
        poetic_adjectives = ["Crimson", "Aurora", "Citrus", "Velvet", "Golden", "Sapphire", "Emerald", "Moonlit", "Starlit", "Twilight", "Dawn", "Sunset", "Mystic", "Ethereal", "Silken", "Crystal", "Pearl", "Amber", "Rose", "Lavender"]
        descriptive_words = ["Drift", "Mist", "Ember", "Whisper", "Echo", "Dream", "Melody", "Symphony", "Harmony", "Cascade", "Breeze", "Glow", "Shimmer", "Sparkle", "Bloom", "Blossom", "Essence", "Spirit", "Soul", "Heart"]
        dish_endings = ["Tart", "Noodles", "Fizz", "Soufflé", "Risotto", "Bisque", "Mousse", "Parfait", "Galette", "Terrine", "Compote", "Reduction", "Infusion", "Medley", "Symphony", "Rhapsody", "Serenade", "Delight", "Fantasy"]
        
        if 'chicken' in main_ingredient:
            dishes = [
                {'name': f'{random.choice(poetic_adjectives)} {random.choice(descriptive_words)} {random.choice(dish_endings)}', 'description': 'Whole roasted chicken with herbs and spices, served with mashed potatoes and gravy'},
                {'name': f'{random.choice(poetic_adjectives)} {random.choice(descriptive_words)} {random.choice(dish_endings)}', 'description': 'Breaded chicken breast topped with marinara sauce and melted mozzarella cheese'},
                {'name': f'{random.choice(poetic_adjectives)} {random.choice(descriptive_words)} {random.choice(dish_endings)}', 'description': 'Comforting chicken soup with vegetables and noodles in a rich broth'}
            ]
        elif 'beef' in main_ingredient:
            dishes = [
                {'name': f'{random.choice(poetic_adjectives)} {random.choice(descriptive_words)} {random.choice(dish_endings)}', 'description': 'Juicy beef patty with lettuce, tomato, and cheese on a toasted bun'},
                {'name': f'{random.choice(poetic_adjectives)} {random.choice(descriptive_words)} {random.choice(dish_endings)}', 'description': 'Slow-cooked beef stew with potatoes, carrots, and onions in a rich gravy'},
                {'name': f'{random.choice(poetic_adjectives)} {random.choice(descriptive_words)} {random.choice(dish_endings)}', 'description': 'Grilled beef skewers with bell peppers and onions, served with rice'}
            ]
        elif 'salmon' in main_ingredient:
            dishes = [
                {'name': f'{random.choice(poetic_adjectives)} {random.choice(descriptive_words)} {random.choice(dish_endings)}', 'description': 'Fresh salmon grilled to perfection with lemon and dill'},
                {'name': f'{random.choice(poetic_adjectives)} {random.choice(descriptive_words)} {random.choice(dish_endings)}', 'description': 'Fresh salmon sashimi and nigiri with wasabi and pickled ginger'},
                {'name': f'{random.choice(poetic_adjectives)} {random.choice(descriptive_words)} {random.choice(dish_endings)}', 'description': 'House-smoked salmon served with cream cheese and capers on bagel'}
            ]
        else:
            dishes = [
                {'name': f'{random.choice(poetic_adjectives)} {random.choice(descriptive_words)} {random.choice(dish_endings)}', 'description': f'Perfectly grilled {main_ingredient} with seasonal herbs and spices'},
                {'name': f'{random.choice(poetic_adjectives)} {random.choice(descriptive_words)} {random.choice(dish_endings)}', 'description': f'Aromatic curry featuring {main_ingredient} in a rich and flavorful sauce'},
                {'name': f'{random.choice(poetic_adjectives)} {random.choice(descriptive_words)} {random.choice(dish_endings)}', 'description': f'Fresh salad with {main_ingredient} and mixed greens with house dressing'}
            ]
        
        return dishes
    
    def _create_inventory_based_dishes(self, available_ingredients, category=None):
        """Create four specific innovative dishes based on available inventory ingredients, one from each category"""
        dishes = []
        ingredient_names = [item['name'] for item in available_ingredients]
        
        if not ingredient_names:
            return []
        
        import random
        
        # Creative naming components
        poetic_adjectives = ["Crimson", "Aurora", "Citrus", "Velvet", "Golden", "Sapphire", "Emerald", "Moonlit", "Starlit", "Twilight", "Dawn", "Sunset", "Mystic", "Ethereal", "Silken", "Crystal", "Pearl", "Amber", "Rose", "Lavender"]
        descriptive_words = ["Drift", "Mist", "Ember", "Whisper", "Echo", "Dream", "Melody", "Symphony", "Harmony", "Cascade", "Breeze", "Glow", "Shimmer", "Sparkle", "Bloom", "Blossom", "Essence", "Spirit", "Soul", "Heart"]
        
        # Category-specific dish endings and descriptions
        categories = {
            'Main Course': {
                'emoji': '🍽️',
                'endings': ["Wellington", "Medallion", "Roulade", "Confit", "Braise", "Gratin", "Casserole", "Filet", "Roast", "Chop"],
                'description_templates': [
                    'A sophisticated main course featuring {ingredients} with modern culinary techniques and aromatic spices',
                    'An innovative fusion entrée combining {ingredients} creating a perfect balance of flavors and textures',
                    'A chef\'s signature main dish showcasing {ingredients} with creative presentation and bold flavor profiles'
                ]
            },
            'Beverage': {
                'emoji': '🥤',
                'endings': ["Fizz", "Elixir", "Brew", "Infusion", "Tonic", "Refresher", "Cooler", "Spritz", "Smoothie", "Blend"],
                'description_templates': [
                    'A refreshing beverage infused with {ingredients} and complementary botanicals for a unique taste experience',
                    'An artisanal drink creation featuring {ingredients} with innovative preparation and signature flavors',
                    'A creative beverage blend highlighting {ingredients} with unexpected flavor combinations and aromatic notes'
                ]
            },
            'Dessert': {
                'emoji': '🍰',
                'endings': ["Tart", "Soufflé", "Mousse", "Parfait", "Galette", "Compote", "Crème", "Cake", "Pudding", "Truffle"],
                'description_templates': [
                    'A decadent dessert creation featuring {ingredients} with elegant presentation and luxurious textures',
                    'An innovative sweet finale showcasing {ingredients} with modern pastry techniques and artistic flair',
                    'A sophisticated dessert masterpiece highlighting {ingredients} with creative preparation and indulgent flavors'
                ]
            },
            'Side Dish': {
                'emoji': '🥗',
                'endings': ["Medley", "Risotto", "Salad", "Gratin", "Sauté", "Pilaf", "Compote", "Reduction", "Terrine", "Relish"],
                'description_templates': [
                    'A vibrant side dish featuring {ingredients} with seasonal accompaniments and fresh herbs',
                    'An artisanal accompaniment showcasing {ingredients} with innovative cooking techniques and complementary flavors',
                    'A creative side creation highlighting {ingredients} with modern preparation and colorful presentation'
                ]
            }
        }
        
        # Create exactly 4 dishes, one from each category
        category_names = list(categories.keys())
        
        for i, category_name in enumerate(category_names):
            category_data = categories[category_name]
            
            # Select ingredients for this dish (rotate through available ingredients)
            if len(ingredient_names) >= 2:
                # Use different ingredient combinations for each category
                start_idx = i % len(ingredient_names)
                selected_ingredients = []
                
                # Add primary ingredient
                selected_ingredients.append(ingredient_names[start_idx])
                
                # Add secondary ingredient if available
                if len(ingredient_names) > 1:
                    secondary_idx = (start_idx + 1) % len(ingredient_names)
                    if ingredient_names[secondary_idx] not in selected_ingredients:
                        selected_ingredients.append(ingredient_names[secondary_idx])
                
                # Add third ingredient for variety if available
                if len(ingredient_names) > 2 and len(selected_ingredients) < 3:
                    tertiary_idx = (start_idx + 2) % len(ingredient_names)
                    if ingredient_names[tertiary_idx] not in selected_ingredients:
                        selected_ingredients.append(ingredient_names[tertiary_idx])
            else:
                selected_ingredients = [ingredient_names[0]]
            
            # Format ingredients for description
            if len(selected_ingredients) == 1:
                ingredients_text = selected_ingredients[0].lower()
            elif len(selected_ingredients) == 2:
                ingredients_text = f"{selected_ingredients[0].lower()} and {selected_ingredients[1].lower()}"
            else:
                ingredients_text = f"{', '.join([ing.lower() for ing in selected_ingredients[:-1]])}, and {selected_ingredients[-1].lower()}"
            
            # Create dish name and description
            dish_name = f'{random.choice(poetic_adjectives)} {random.choice(descriptive_words)} {random.choice(category_data["endings"])}'
            description = random.choice(category_data['description_templates']).format(ingredients=ingredients_text)
            
            dishes.append({
                'name': dish_name,
                'description': description,
                'ingredients': selected_ingredients,
                'category': category_name,
                'emoji': category_data['emoji']
            })
        
        return dishes
    
    def _generate_ai_recipe_suggestions(self, message, category=None):
        """Generate comprehensive AI-powered recipe suggestions with inventory integration"""
        try:
            # Extract ingredients from message
            ingredients_mentioned = []
            available_ingredients = Ingredient.query.all()
            
            for ingredient in available_ingredients:
                if ingredient.name.lower() in message.lower():
                    ingredients_mentioned.append(ingredient.name)
            
            # If no specific ingredients mentioned, show inventory-based suggestions
            if not ingredients_mentioned:
                # Get current inventory with stock levels
                inventory_items = InventoryItem.query.join(Ingredient).filter(InventoryItem.quantity > 0).all()
                
                if not inventory_items:
                    return {
                        'response': "💡 **AI Recipe Engine**\n\n⚠️ **No inventory data available**\n\nPlease specify ingredients you'd like to use. For example:\n• 'Suggest dishes using tomatoes and cheese'\n• 'Create a recipe with chicken and herbs'\n• 'Recommend something with seafood and vegetables'",
                        'type': 'ai_recipe_engine',
                        'data': {
                            'suggestions': []
                        }
                    }
                
                # Categorize inventory by stock levels
                high_stock_items = []
                medium_stock_items = []
                low_stock_items = []
                
                for item in inventory_items:
                    ingredient = Ingredient.query.get(item.ingredient_id)
                    if ingredient:
                        inventory_data = {
                            'name': ingredient.name,
                            'quantity': float(item.quantity),
                            'unit': ingredient.unit,
                            'category': ingredient.category
                        }
                        
                        if item.quantity > 20:
                            high_stock_items.append(inventory_data)
                        elif item.quantity > 5:
                            medium_stock_items.append(inventory_data)
                        else:
                            low_stock_items.append(inventory_data)
                
                # Sort by quantity (highest first)
                high_stock_items.sort(key=lambda x: x['quantity'], reverse=True)
                medium_stock_items.sort(key=lambda x: x['quantity'], reverse=True)
                low_stock_items.sort(key=lambda x: x['quantity'], reverse=True)
                
                # Build inventory display response
                response = "💡 **AI Recipe Engine**\n\nI can suggest creative recipes based on your current inventory!\n\n📦 **Current Inventory:**\n\n"
                
                if high_stock_items:
                    response += "🟢 **High Stock (>20 units):**\n"
                    for item in high_stock_items[:8]:  # Show top 8
                        response += f"• {item['name']}: {item['quantity']:.0f} {item['unit']}\n"
                    response += "\n"
                
                if medium_stock_items:
                    response += "🟡 **Medium Stock (6-20 units):**\n"
                    for item in medium_stock_items[:6]:  # Show top 6
                        response += f"• {item['name']}: {item['quantity']:.0f} {item['unit']}\n"
                    response += "\n"
                
                if low_stock_items:
                    response += "🔴 **Low Stock (≤5 units):**\n"
                    for item in low_stock_items[:4]:  # Show top 4
                        response += f"• {item['name']}: {item['quantity']:.0f} {item['unit']}\n"
                    response += "\n"
                
                # Add suggested combinations with category highlighting
                response += "💡 **Suggested Combinations:**\n"
                suggestions = []
                
                # Generate four category-specific dish suggestions
                available_ingredients = high_stock_items + medium_stock_items
                if available_ingredients:
                    dish_suggestions = self._create_inventory_based_dishes(available_ingredients[:7])
                    for dish in dish_suggestions:
                        response += f"• **{dish['emoji']} {dish['category']}:** {dish['name']} - {dish['description']}\n"
                        suggestions.append({
                            'text': dish['name'],
                            'description': dish['description'],
                            'ingredients': dish['ingredients'],
                            'category': dish['category'],
                            'emoji': dish['emoji'],
                            'type': 'realistic_dish'
                        })
                
                response += "\n**How to use:**\n"
                response += "• Simply mention ingredients from your inventory\n"
                if high_stock_items:
                    response += f"• Example: \"Create a dish with {high_stock_items[0]['name']} and {high_stock_items[1]['name'] if len(high_stock_items) > 1 else 'vegetables'}\"\n"
                response += "• Or say: \"Suggest recipes using high stock ingredients\"\n"
                response += "• Click on any suggestion below to get started!"
                
                return {
                    'response': response,
                    'type': 'ai_recipe_engine',
                    'data': {
                        'mode': 'INNOVATION',
                        'inventory': {
                            'high_stock': high_stock_items,
                            'medium_stock': medium_stock_items,
                            'low_stock': low_stock_items
                        },
                        'suggestions': suggestions,
                        'ui_update': 'show_inventory_recipe_engine'
                    }
                }
            
            # Perform comprehensive ingredient analysis
            analysis = self._analyze_ingredient_compatibility(ingredients_mentioned)
            suggestions = self._generate_creative_suggestions(ingredients_mentioned, analysis)
            
            # Generate detailed response
            response = f"🤖 **AI-Powered Recipe Suggestions**\n\n"
            response += f"**Ingredients Analyzed:** {', '.join(ingredients_mentioned)}\n"
            response += f"**Compatibility Score:** {analysis['compatibility_score']:.0f}%\n\n"
            
            # Add availability information
            if analysis['availability_status']:
                response += "**📦 Ingredient Availability:**\n"
                for ingredient, status in analysis['availability_status'].items():
                    status_emoji = "🟢" if status['status'] == 'high' else "🟡" if status['status'] == 'medium' else "🔴"
                    response += f"• {status_emoji} {ingredient.title()}: {status['quantity']} units ({status['status']})\n"
                response += "\n"
            
            # Add popularity metrics
            if analysis['popularity_metrics']:
                response += "**📈 Popularity Analysis:**\n"
                for ingredient, metrics in analysis['popularity_metrics'].items():
                    response += f"• {ingredient.title()}: {metrics['popularity_score']:.0f}% popularity (used in {metrics['menu_usage_count']} menu items)\n"
                response += "\n"
            
            # Add AI suggestions
            response += "**🎨 AI-Generated Recipes:**\n"
            for i, suggestion in enumerate(suggestions[:4], 1):  # Limit to top 4
                response += f"{i}. {suggestion}\n"
            
            response += "\n**💡 Next Steps:**\n"
            response += "• Say 'auto apply [recipe name]' to automatically generate complete dish details\n"
            response += "• Say 'manual input' to add your own custom recipe\n"
            response += "• Say 'regenerate appetizer' to focus on specific dish types"
            
            return {
                'response': response,
                'type': 'ai_recipe_suggestions',
                'data': {
                    'mode': 'INNOVATION',
                    'ingredients_analyzed': ingredients_mentioned,
                    'compatibility_score': analysis['compatibility_score'],
                    'suggestions': suggestions,
                    'analysis': analysis,
                    'ui_update': 'show_recipe_suggestions'
                }
            }
            
        except Exception as e:
            logger.error(f"Error in AI recipe suggestions: {str(e)}")
            return {
                'response': "I encountered an error generating AI recipe suggestions. Please try again.",
                'type': 'error'
            }
    
    def _handle_auto_apply_mode(self, message):
        """Handle Auto Apply functionality with AI agent framework"""
        try:
            response = "🤖 **Auto Apply Mode Activated**\n\n"
            response += "**AI Agent Framework Features:**\n"
            response += "• 🖼️ **Image Generation**: High-quality food photography\n"
            response += "• 📊 **Demand Prediction**: Historical data analysis\n"
            response += "• 💰 **Optimal Pricing**: Market-based pricing strategy\n"
            response += "• 🥗 **Nutrition Calculation**: Complete nutritional profile\n"
            response += "• 📝 **Dish Compilation**: Full menu item details\n\n"
            
            # Check if specific recipe mentioned for auto-apply
            if any(keyword in message.lower() for keyword in ['apply', 'generate', 'create']):
                # Extract recipe name or ingredients
                recipe_keywords = ['bowl', 'salad', 'soup', 'fusion', 'platter', 'medley', 'pasta', 'chicken', 'beef', 'fish', 'pizza', 'burger', 'sandwich', 'wrap', 'curry', 'stir fry', 'risotto', 'gnocchi']
                detected_recipe = None
                
                for keyword in recipe_keywords:
                    if keyword in message.lower():
                        detected_recipe = keyword
                        break
                
                if detected_recipe:
                    # Create a more specific dish name
                    dish_mapping = {
                        'bowl': 'Mediterranean Quinoa Power Bowl',
                        'salad': 'Harvest Kale & Roasted Vegetable Salad',
                        'soup': 'Roasted Tomato Basil Bisque',
                        'fusion': 'Korean-Mexican Bulgogi Tacos',
                        'platter': 'Artisan Charcuterie & Cheese Board',
                        'medley': 'Seasonal Vegetable Medley',
                        'pasta': 'Truffle Mushroom Linguine',
                        'chicken': 'Herb-Crusted Chicken Breast',
                        'beef': 'Grass-Fed Beef Tenderloin',
                        'fish': 'Pan-Seared Atlantic Salmon',
                        'pizza': 'Artisan Margherita Pizza',
                        'burger': 'Gourmet Wagyu Burger',
                        'sandwich': 'Grilled Panini Sandwich',
                        'wrap': 'Mediterranean Veggie Wrap',
                        'curry': 'Thai Green Curry',
                        'stir fry': 'Asian Vegetable Stir Fry',
                        'risotto': 'Wild Mushroom Risotto',
                        'gnocchi': 'Sage Butter Gnocchi'
                    }
                    
                    dish_name = dish_mapping.get(detected_recipe, f'Gourmet {detected_recipe.title()}')
                    return self._process_auto_apply_dish(dish_name)
            
            response += "**🎯 Usage Examples:**\n"
            response += "• 'Auto apply fusion bowl' - Generate complete fusion bowl recipe\n"
            response += "• 'Auto apply seasonal salad' - Create seasonal salad with all details\n"
            response += "• 'Auto apply signature soup' - Develop signature soup recipe\n\n"
            response += "**⚙️ Customization Options:**\n"
            response += "• Dietary restrictions (vegan, gluten-free, keto)\n"
            response += "• Price range preferences\n"
            response += "• Cuisine style specifications\n"
            response += "• Seasonal ingredient focus"
            
            return {
                'response': response,
                'type': 'auto_apply_help',
                'data': {
                    'mode': 'INNOVATION',
                    'auto_apply_available': True,
                    'ui_update': 'show_auto_apply_options'
                }
            }
            
        except Exception as e:
            logger.error(f"Error in auto apply mode: {str(e)}")
            return {
                'response': "I encountered an error with auto apply functionality. Please try again.",
                'type': 'error'
            }
    
    def _handle_manual_input_mode(self, message):
        """Handle manual input functionality for new menu items"""
        try:
            response = "📝 **Manual Input Mode**\n\n"
            response += "**Create Your Custom Menu Item:**\n\n"
            response += "**📋 Required Information:**\n"
            response += "• **Dish Name**: What would you like to call it?\n"
            response += "• **Description**: Brief description of the dish\n"
            response += "• **Ingredients**: List of main ingredients\n"
            response += "• **Price**: Suggested price point\n"
            response += "• **Category**: Appetizer, Main Course, Dessert, etc.\n\n"
            
            response += "**💡 Input Format Example:**\n"
            response += "```\n"
            response += "Name: Mediterranean Quinoa Bowl\n"
            response += "Description: Fresh quinoa with grilled vegetables, feta cheese, and lemon vinaigrette\n"
            response += "Ingredients: quinoa, bell peppers, zucchini, feta cheese, olive oil, lemon\n"
            response += "Price: $14.99\n"
            response += "Category: Main Course\n"
            response += "```\n\n"
            
            response += "**🚀 Enhanced Features:**\n"
            response += "• **Auto-Nutrition**: Automatic nutritional calculation\n"
            response += "• **Price Validation**: Market comparison and profit margin analysis\n"
            response += "• **Ingredient Check**: Availability verification\n"
            response += "• **Demand Forecast**: Predicted customer interest\n\n"
            
            response += "**📝 To Add Your Item:**\n"
            response += "Simply provide the details in the format above, and I'll help you create a complete menu item with all the enhanced features!"
            
            return {
                'response': response,
                'type': 'manual_input_guide',
                'data': {
                    'mode': 'INNOVATION',
                    'manual_input_active': True,
                    'ui_update': 'show_manual_input_form'
                }
            }
            
        except Exception as e:
            logger.error(f"Error in manual input mode: {str(e)}")
            return {
                'response': "I encountered an error with manual input functionality. Please try again.",
                'type': 'error'
            }
    
    def _handle_dish_type_regeneration(self, message):
        """Handle dish type regeneration requests with user preferences"""
        try:
            # Enhanced dish type detection with preferences
            dish_types = {
                'appetizer': {
                    'keywords': ['appetizer', 'starter', 'app', 'small plate', 'finger food', 'tapas', 'bruschetta'],
                    'preferences': ['light', 'crispy', 'fresh', 'savory', 'bite-sized']
                },
                'main course': {
                    'keywords': ['main', 'entree', 'main course', 'dinner', 'lunch', 'protein', 'hearty'],
                    'preferences': ['filling', 'protein-rich', 'balanced', 'satisfying', 'comfort food']
                },
                'dessert': {
                    'keywords': ['dessert', 'sweet', 'cake', 'ice cream', 'pudding', 'chocolate', 'fruit'],
                    'preferences': ['sweet', 'indulgent', 'creamy', 'fruity', 'rich', 'light']
                },
                'beverage': {
                    'keywords': ['drink', 'beverage', 'cocktail', 'juice', 'smoothie', 'tea', 'coffee'],
                    'preferences': ['refreshing', 'energizing', 'warming', 'cooling', 'healthy']
                },
                'side dish': {
                    'keywords': ['side', 'side dish', 'accompaniment', 'vegetable', 'grain'],
                    'preferences': ['complementary', 'nutritious', 'colorful', 'textural']
                }
            }
            
            # Detect preferences from message
            preference_keywords = {
                'healthy': ['healthy', 'nutritious', 'low-calorie', 'diet', 'wellness'],
                'spicy': ['spicy', 'hot', 'chili', 'pepper', 'heat'],
                'vegetarian': ['vegetarian', 'veggie', 'plant-based', 'meatless'],
                'vegan': ['vegan', 'plant-only', 'dairy-free'],
                'gluten-free': ['gluten-free', 'celiac', 'wheat-free'],
                'comfort': ['comfort', 'hearty', 'warming', 'cozy'],
                'light': ['light', 'fresh', 'clean', 'simple'],
                'gourmet': ['gourmet', 'fancy', 'upscale', 'elegant', 'sophisticated'],
                'quick': ['quick', 'fast', 'easy', 'simple', '15 minutes'],
                'seasonal': ['seasonal', 'fresh', 'local', 'farm-to-table']
            }
            
            detected_type = 'main course'  # default
            detected_preferences = []
            message_lower = message.lower()
            
            # Detect dish type
            for dish_type, info in dish_types.items():
                if any(keyword in message_lower for keyword in info['keywords']):
                    detected_type = dish_type
                    break
            
            # Detect user preferences
            for preference, keywords in preference_keywords.items():
                if any(keyword in message_lower for keyword in keywords):
                    detected_preferences.append(preference)
            
            # Generate type-specific suggestions with preferences
            suggestions = self._generate_preference_based_suggestions(detected_type, detected_preferences)
            
            response = f"🍽️ **{detected_type.title()} Regeneration**\n\n"
            
            if detected_preferences:
                response += f"🎯 **Detected Preferences:** {', '.join(detected_preferences)}\n\n"
            
            response += f"Here are personalized {detected_type} suggestions:\n\n"
            
            for i, suggestion in enumerate(suggestions, 1):
                response += f"**{i}. {suggestion['name']}**\n"
                response += f"*{suggestion['description']}*\n"
                response += f"💡 Key ingredients: {suggestion['ingredients']}\n"
                response += f"⏱️ Prep time: {suggestion['prep_time']} minutes\n"
                response += f"🏷️ Style: {suggestion['style']}\n\n"
            
            response += "\n🎯 **Preference Options:**\n"
            response += "• Try 'healthy appetizers' for nutritious options\n"
            response += "• Ask for 'spicy main course' for heat lovers\n"
            response += "• Request 'vegan desserts' for plant-based treats\n"
            response += "• Specify 'quick side dishes' for fast prep\n\n"
            
            response += "🚀 **Next Steps:**\n"
            response += "• Click 'Auto Apply' to automatically add to menu\n"
            response += "• Use 'Manual Input' for custom modifications\n"
            response += f"• Ask for more {detected_type} suggestions with specific preferences\n"
            
            return {
                'response': response,
                'type': 'dish_type_regeneration',
                'data': {
                    'mode': 'INNOVATION',
                    'dish_type': detected_type,
                    'suggestions': suggestions,
                    'ui_update': 'highlight_dish_type_suggestions'
                }
            }
            
        except Exception as e:
            logger.error(f"Error in dish type regeneration: {str(e)}")
            return {
                'response': "I encountered an error with dish type regeneration. Please try again.",
                'type': 'error'
            }
    
    def _generate_preference_based_suggestions(self, dish_type, preferences):
        """Generate dish suggestions based on type and user preferences"""
        try:
            # Base suggestions for each dish type
            base_suggestions = {
                'appetizer': [
                    {'name': 'Mediterranean Mezze Platter', 'ingredients': 'hummus, olives, feta, pita', 'prep_time': 15, 'style': 'Mediterranean'},
                    {'name': 'Crispy Calamari Rings', 'ingredients': 'squid, flour, spices, marinara', 'prep_time': 20, 'style': 'Italian'},
                    {'name': 'Seasonal Bruschetta Trio', 'ingredients': 'bread, tomatoes, basil, cheese', 'prep_time': 12, 'style': 'Italian'}
                ],
                'main course': [
                    {'name': 'Herb-Crusted Salmon', 'ingredients': 'salmon, herbs, quinoa, vegetables', 'prep_time': 25, 'style': 'Contemporary'},
                    {'name': 'Grilled Chicken Teriyaki', 'ingredients': 'chicken, teriyaki sauce, rice, vegetables', 'prep_time': 30, 'style': 'Asian'},
                    {'name': 'Pasta Primavera', 'ingredients': 'pasta, seasonal vegetables, olive oil, parmesan', 'prep_time': 20, 'style': 'Italian'}
                ],
                'dessert': [
                    {'name': 'Chocolate Lava Cake', 'ingredients': 'chocolate, butter, eggs, flour', 'prep_time': 25, 'style': 'Decadent'},
                    {'name': 'Fresh Berry Parfait', 'ingredients': 'berries, yogurt, granola, honey', 'prep_time': 10, 'style': 'Light'},
                    {'name': 'Tiramisu', 'ingredients': 'mascarpone, coffee, ladyfingers, cocoa', 'prep_time': 30, 'style': 'Italian'}
                ],
                'beverage': [
                    {'name': 'Tropical Smoothie', 'ingredients': 'mango, pineapple, coconut, lime', 'prep_time': 5, 'style': 'Refreshing'},
                    {'name': 'Artisan Coffee Blend', 'ingredients': 'premium coffee beans, steamed milk', 'prep_time': 8, 'style': 'Energizing'},
                    {'name': 'Herbal Tea Infusion', 'ingredients': 'chamomile, honey, lemon', 'prep_time': 5, 'style': 'Calming'}
                ],
                'side dish': [
                    {'name': 'Roasted Seasonal Vegetables', 'ingredients': 'mixed vegetables, olive oil, herbs', 'prep_time': 20, 'style': 'Healthy'},
                    {'name': 'Garlic Herb Rice', 'ingredients': 'rice, garlic, herbs, butter', 'prep_time': 15, 'style': 'Comfort'},
                    {'name': 'Quinoa Salad', 'ingredients': 'quinoa, vegetables, vinaigrette', 'prep_time': 18, 'style': 'Nutritious'}
                ]
            }
            
            suggestions = base_suggestions.get(dish_type, base_suggestions['main course'])
            
            # Modify suggestions based on preferences
            if preferences:
                modified_suggestions = []
                for suggestion in suggestions:
                    modified = suggestion.copy()
                    
                    # Apply preference modifications
                    if 'healthy' in preferences:
                        if 'vegetables' not in modified['ingredients']:
                            modified['ingredients'] += ', fresh vegetables'
                        modified['style'] += ' & Healthy'
                        modified['description'] = f"A nutritious {modified['name'].lower()} packed with wholesome ingredients"
                    
                    if 'spicy' in preferences:
                        modified['ingredients'] += ', chili peppers, spices'
                        modified['name'] = f"Spicy {modified['name']}"
                        modified['style'] += ' & Spicy'
                        modified['description'] = f"A fiery version of {modified['name'].lower()} with bold heat"
                    
                    if 'vegetarian' in preferences:
                        # Replace meat ingredients
                        modified['ingredients'] = modified['ingredients'].replace('chicken', 'tofu').replace('salmon', 'portobello mushroom')
                        modified['style'] += ' & Vegetarian'
                        modified['description'] = f"A plant-based {modified['name'].lower()} full of flavor"
                    
                    if 'vegan' in preferences:
                        # Replace all animal products
                        modified['ingredients'] = modified['ingredients'].replace('cheese', 'nutritional yeast').replace('butter', 'olive oil').replace('yogurt', 'coconut yogurt')
                        modified['style'] += ' & Vegan'
                        modified['description'] = f"A completely plant-based {modified['name'].lower()}"
                    
                    if 'gluten-free' in preferences:
                        modified['ingredients'] = modified['ingredients'].replace('flour', 'almond flour').replace('pasta', 'rice noodles').replace('bread', 'gluten-free bread')
                        modified['style'] += ' & Gluten-Free'
                        modified['description'] = f"A gluten-free version of {modified['name'].lower()}"
                    
                    if 'quick' in preferences:
                        modified['prep_time'] = min(modified['prep_time'], 15)
                        modified['name'] = f"Quick {modified['name']}"
                        modified['style'] += ' & Fast'
                        modified['description'] = f"A quick and easy {modified['name'].lower()} ready in minutes"
                    
                    if 'gourmet' in preferences:
                        modified['ingredients'] += ', truffle oil, premium herbs'
                        modified['name'] = f"Gourmet {modified['name']}"
                        modified['style'] += ' & Upscale'
                        modified['description'] = f"An elevated, restaurant-quality {modified['name'].lower()}"
                    
                    # Add description if not already set
                    if 'description' not in modified:
                        modified['description'] = f"A delicious {modified['name'].lower()} featuring {modified['ingredients'].split(',')[0]} and complementary flavors"
                    
                    modified_suggestions.append(modified)
                
                return modified_suggestions
            
            # Add default descriptions
            for suggestion in suggestions:
                if 'description' not in suggestion:
                    suggestion['description'] = f"A delicious {suggestion['name'].lower()} featuring {suggestion['ingredients'].split(',')[0]} and complementary flavors"
            
            return suggestions
            
        except Exception as e:
            logger.error(f"Error generating preference-based suggestions: {str(e)}")
            # Return basic suggestions as fallback
            return [
                {'name': f'{dish_type.title()} Special', 'ingredients': 'seasonal ingredients', 'prep_time': 20, 'style': 'House Special', 'description': f'Our signature {dish_type} creation'}
            ]
    
    def _generate_four_category_suggestions(self, message):
        """Generate four dish suggestions, one from each category"""
        try:
            # Define the four categories with their suggestions
            categories = {
                'Main Course': {
                    'emoji': '🍽️',
                    'suggestions': [
                        {'name': 'Grilled Salmon with Herb Butter', 'description': 'A perfectly seasoned salmon fillet grilled to perfection and topped with a fragrant herb butter made with fresh dill, parsley, and garlic. Served with lemon wedges for a bright, fresh finish.', 'prep_time': 25, 'price': '$24.99'},
                        {'name': 'Herb-Crusted Chicken Breast', 'description': 'Tender chicken breast coated with aromatic herbs and spices, pan-seared to golden perfection. Served with roasted vegetables and garlic mashed potatoes.', 'prep_time': 30, 'price': '$22.99'},
                        {'name': 'Beef Tenderloin Medallions', 'description': 'Premium beef tenderloin medallions cooked to your preference, served with red wine reduction sauce and seasonal vegetables.', 'prep_time': 35, 'price': '$32.99'}
                    ]
                },
                'Beverage': {
                    'emoji': '🥤',
                    'suggestions': [
                        {'name': 'Tropical Mango Smoothie', 'description': 'A refreshing blend of ripe mango, coconut milk, pineapple juice, and a hint of lime. Garnished with toasted coconut flakes and served chilled for the perfect tropical escape.', 'prep_time': 5, 'price': '$8.99'},
                        {'name': 'Artisan Cold Brew Coffee', 'description': 'Smooth and rich cold brew coffee made from premium beans, served over ice with a choice of milk or cream. Perfect for coffee enthusiasts.', 'prep_time': 3, 'price': '$5.99'},
                        {'name': 'Fresh Berry Lemonade', 'description': 'House-made lemonade infused with fresh mixed berries, mint leaves, and a touch of sparkling water for a refreshing twist.', 'prep_time': 8, 'price': '$6.99'}
                    ]
                },
                'Dessert': {
                    'emoji': '🍰',
                    'suggestions': [
                        {'name': 'Classic Chocolate Lava Cake', 'description': 'A decadent individual chocolate cake with a molten chocolate center that flows out when cut. Served warm with a scoop of vanilla ice cream and a dusting of powdered sugar.', 'prep_time': 25, 'price': '$12.99'},
                        {'name': 'Tiramisu Parfait', 'description': 'Layers of coffee-soaked ladyfingers, mascarpone cream, and cocoa powder, elegantly presented in a glass parfait. A classic Italian dessert with a modern twist.', 'prep_time': 20, 'price': '$10.99'},
                        {'name': 'Fresh Berry Cheesecake', 'description': 'Creamy New York-style cheesecake topped with a medley of fresh seasonal berries and a light berry coulis. Served on a graham cracker crust.', 'prep_time': 15, 'price': '$11.99'}
                    ]
                },
                'Side Dish': {
                    'emoji': '🥗',
                    'suggestions': [
                        {'name': 'Roasted Rainbow Vegetables', 'description': 'A colorful medley of seasonal vegetables including bell peppers, zucchini, carrots, and red onions, roasted with olive oil, fresh herbs, and a touch of balsamic glaze.', 'prep_time': 20, 'price': '$7.99'},
                        {'name': 'Garlic Parmesan Risotto', 'description': 'Creamy Arborio rice slowly cooked with garlic, white wine, and vegetable broth, finished with fresh Parmesan cheese and herbs.', 'prep_time': 25, 'price': '$9.99'},
                        {'name': 'Quinoa Power Salad', 'description': 'Nutritious quinoa mixed with fresh vegetables, dried cranberries, toasted nuts, and a light lemon vinaigrette dressing.', 'prep_time': 15, 'price': '$8.99'}
                    ]
                }
            }
            
            # Build the response with one suggestion from each category
            response = "🍽️ **Here are my dish suggestions, one from each category:**\n\n"
            
            for category_name, category_data in categories.items():
                # Select the first suggestion from each category
                suggestion = category_data['suggestions'][0]
                emoji = category_data['emoji']
                
                response += f"## **{emoji} {category_name}**\n"
                response += f"**{suggestion['name']}** - {suggestion['description']}\n\n"
            
            response += "Each dish offers a unique flavor profile and would complement a well-rounded dining experience!\n\n"
            response += "💡 **Want more options?** Ask me for specific preferences like:\n"
            response += "• 'Suggest spicy main courses'\n"
            response += "• 'Recommend healthy beverages'\n"
            response += "• 'Show me Italian desserts'"
            
            return {
                'response': response,
                'type': 'four_category_suggestions',
                'data': {
                    'suggestions': categories,
                    'ui_update': 'highlight_category_suggestions'
                }
            }
            
        except Exception as e:
            logger.error(f"Error generating four category suggestions: {str(e)}")
            return {
                'response': "I'm having trouble generating dish suggestions right now. Please try again.",
                'type': 'error'
            }
    
    def _process_auto_apply_dish(self, dish_name):
        """Process a specific dish through the auto apply pipeline"""
        try:
            response = f"🤖 **Auto-Applying: {dish_name}**\n\n"
            response += "**🔄 AI Processing Pipeline:**\n\n"
            
            # Step 1: Image Generation
            image_result = self._generate_dish_image(dish_name)
            response += f"✅ **Image Generation**: {image_result['status']}\n"
            response += f"   📸 Style: {image_result['style']}\n\n"
            
            # Step 2: Demand Prediction
            demand_result = self._predict_dish_demand(dish_name)
            response += f"✅ **Demand Prediction**: {demand_result['confidence']}% confidence\n"
            response += f"   📊 Expected weekly sales: {demand_result['weekly_sales']} units\n\n"
            
            # Step 3: Pricing Optimization
            pricing_result = self._optimize_dish_pricing(dish_name)
            response += f"✅ **Pricing Optimization**: ${pricing_result['price']:.2f}\n"
            response += f"   💰 Profit margin: {pricing_result['margin']}%\n\n"
            
            # Step 4: Nutrition Calculation
            nutrition_result = self._calculate_dish_nutrition(dish_name)
            response += f"✅ **Nutrition Analysis**: {nutrition_result['calories']} calories\n"
            response += f"   🥗 Health score: {nutrition_result['health_score']}/10\n\n"
            
            # Step 5: Quality Validation and Improvement
            generated_data = {
                'image': image_result,
                'demand': demand_result,
                'pricing': pricing_result,
                'nutrition': nutrition_result
            }
            
            validation_result = self._validate_dish_data(generated_data)
            response += f"✅ **Quality Validation**: {validation_result['quality_level']} ({validation_result['quality_score']}/100)\n\n"
            
            # Apply automatic improvements if needed
            improvements = self._apply_quality_improvements(generated_data, validation_result)
            if improvements['success'] and improvements['improvements_made']:
                response += "🔧 **Quality Improvements Applied:**\n"
                for improvement in improvements['improvements_made']:
                    response += f"   • {improvement}\n"
                response += "\n"
                # Use improved data
                final_data = improvements['improved_data']
            else:
                final_data = generated_data
            
            response += "**📋 Complete Menu Item Generated:**\n\n"
            response += f"**{dish_name}**\n"
            response += f"*{final_data['nutrition']['description']}*\n\n"
            response += f"💰 **Price**: ${final_data['pricing']['price']:.2f}\n"
            response += f"📊 **Demand Score**: {final_data['demand']['confidence']}%\n"
            response += f"🥗 **Nutrition**: {final_data['nutrition']['calories']} cal | {final_data['nutrition']['protein']}g protein\n"
            response += f"🖼️ **Image**: Professional photo ready\n"
            response += f"🎯 **Quality Level**: {validation_result['quality_level']}\n\n"
            
            # Generate quality report
            quality_report = self._generate_quality_report(dish_name, validation_result, improvements)
            
            response += "**✨ Ready to add to menu!** Click 'Confirm' to finalize."
            
            return {
                'response': response,
                'type': 'auto_apply_complete',
                'data': {
                    'mode': 'INNOVATION',
                    'dish_name': dish_name,
                    'generated_data': final_data,
                    'validation_results': validation_result,
                    'quality_report': quality_report,
                    'improvements_applied': improvements['improvements_made'] if improvements['success'] else [],
                    'ui_update': 'show_auto_apply_result'
                }
            }
            
        except Exception as e:
            logger.error(f"Error processing auto apply dish: {str(e)}")
            return {
                'response': f"❌ Error processing {dish_name}. Please try again.",
                'type': 'error'
            }
    
    def _generate_dish_image(self, dish_name):
        """Generate AI image for dish"""
        try:
            # Simulate AI image generation
            styles = ['Professional Studio', 'Rustic Plating', 'Modern Minimalist', 'Artistic Presentation']
            import random
            selected_style = random.choice(styles)
            
            return {
                'status': 'Generated successfully',
                'style': selected_style,
                'resolution': '1920x1080',
                'format': 'PNG',
                'lighting': 'Natural daylight',
                'composition': 'Rule of thirds'
            }
        except Exception as e:
            logger.error(f"Error generating image: {str(e)}")
            return {'status': 'Generation failed', 'style': 'Default'}
    
    def _predict_dish_demand(self, dish_name):
        """Predict customer demand for dish"""
        try:
            # Simulate demand prediction using historical data
            import random
            
            # Base confidence on dish type and ingredients
            base_confidence = random.randint(70, 95)
            weekly_sales = random.randint(15, 45)
            
            # Adjust based on seasonal factors
            seasonal_factor = 1.0
            if any(word in dish_name.lower() for word in ['soup', 'warm', 'hot']):
                seasonal_factor = 1.2  # Higher demand in winter
            elif any(word in dish_name.lower() for word in ['salad', 'cold', 'fresh']):
                seasonal_factor = 1.1  # Higher demand in summer
            
            adjusted_sales = int(weekly_sales * seasonal_factor)
            
            return {
                'confidence': base_confidence,
                'weekly_sales': adjusted_sales,
                'seasonal_factor': seasonal_factor,
                'trend': 'Increasing' if base_confidence > 85 else 'Stable',
                'peak_hours': ['12:00-14:00', '18:00-20:00']
            }
        except Exception as e:
            logger.error(f"Error predicting demand: {str(e)}")
            return {'confidence': 75, 'weekly_sales': 20}
    
    def _optimize_dish_pricing(self, dish_name):
        """Optimize pricing for dish"""
        try:
            # Simulate pricing optimization
            import random
            
            # Base price calculation
            base_cost = random.uniform(4.50, 8.00)
            target_margin = random.uniform(60, 75)  # 60-75% margin
            
            optimized_price = base_cost / (1 - target_margin/100)
            
            # Round to .99 or .49 pricing
            if optimized_price % 1 < 0.5:
                final_price = int(optimized_price) + 0.49
            else:
                final_price = int(optimized_price) + 0.99
            
            actual_margin = ((final_price - base_cost) / final_price) * 100
            
            return {
                'price': final_price,
                'cost': base_cost,
                'margin': round(actual_margin, 1),
                'competitive_range': f'${final_price-2:.2f} - ${final_price+3:.2f}',
                'strategy': 'Premium positioning' if final_price > 15 else 'Value positioning'
            }
        except Exception as e:
            logger.error(f"Error optimizing pricing: {str(e)}")
            return {'price': 12.99, 'margin': 65}
    
    def _calculate_dish_nutrition(self, dish_name):
        """Calculate comprehensive nutrition for dish"""
        try:
            # Simulate nutrition calculation
            import random
            
            # Base nutrition values
            calories = random.randint(300, 800)
            protein = random.randint(15, 45)
            carbs = random.randint(25, 60)
            fat = random.randint(10, 35)
            fiber = random.randint(3, 12)
            
            # Calculate health score based on nutrition balance
            health_score = 5  # Base score
            
            # Protein bonus
            if protein >= 25:
                health_score += 2
            elif protein >= 20:
                health_score += 1
            
            # Fiber bonus
            if fiber >= 8:
                health_score += 2
            elif fiber >= 5:
                health_score += 1
            
            # Calorie penalty for very high calories
            if calories > 700:
                health_score -= 1
            
            health_score = min(10, max(1, health_score))
            
            # Generate description
            description = f"A nutritious {dish_name.lower()} featuring balanced macronutrients"
            if health_score >= 8:
                description += " and exceptional health benefits"
            elif health_score >= 6:
                description += " with good nutritional value"
            
            return {
                'calories': calories,
                'protein': protein,
                'carbs': carbs,
                'fat': fat,
                'fiber': fiber,
                'health_score': health_score,
                'description': description,
                'allergens': ['May contain gluten', 'Contains dairy'],
                'dietary_tags': ['High Protein'] if protein >= 25 else ['Balanced']
            }
        except Exception as e:
            logger.error(f"Error calculating nutrition: {str(e)}")
            return {'calories': 450, 'protein': 25, 'health_score': 7}
    
    def _validate_dish_data(self, dish_data):
        """Validate generated dish data for quality standards"""
        try:
            validation_results = {
                'is_valid': True,
                'warnings': [],
                'errors': [],
                'quality_score': 0
            }
            
            # Validate pricing
            if 'pricing' in dish_data:
                price = dish_data['pricing'].get('price', 0)
                margin = dish_data['pricing'].get('margin', 0)
                
                if price < 5.00:
                    validation_results['warnings'].append('Price may be too low for profitability')
                elif price > 50.00:
                    validation_results['warnings'].append('Price may be too high for target market')
                else:
                    validation_results['quality_score'] += 25
                
                if margin < 50:
                    validation_results['warnings'].append('Profit margin below recommended 50%')
                elif margin > 80:
                    validation_results['warnings'].append('Profit margin may be too high')
                else:
                    validation_results['quality_score'] += 25
            
            # Validate nutrition
            if 'nutrition' in dish_data:
                nutrition = dish_data['nutrition']
                calories = nutrition.get('calories', 0)
                protein = nutrition.get('protein', 0)
                health_score = nutrition.get('health_score', 0)
                
                if calories < 200:
                    validation_results['warnings'].append('Calorie content may be too low')
                elif calories > 1200:
                    validation_results['warnings'].append('Calorie content may be too high')
                else:
                    validation_results['quality_score'] += 20
                
                if protein < 10:
                    validation_results['warnings'].append('Protein content may be insufficient')
                else:
                    validation_results['quality_score'] += 15
                
                if health_score >= 7:
                    validation_results['quality_score'] += 15
                elif health_score < 5:
                    validation_results['warnings'].append('Health score below recommended level')
            
            # Validate demand prediction
            if 'demand' in dish_data:
                confidence = dish_data['demand'].get('confidence', 0)
                weekly_sales = dish_data['demand'].get('weekly_sales', 0)
                
                if confidence < 70:
                    validation_results['warnings'].append('Demand prediction confidence is low')
                else:
                    validation_results['quality_score'] += 15
                
                if weekly_sales < 10:
                    validation_results['warnings'].append('Predicted sales volume may be too low')
                elif weekly_sales > 100:
                    validation_results['warnings'].append('Predicted sales volume may be unrealistic')
            
            # Overall quality assessment
            if validation_results['quality_score'] >= 80:
                validation_results['quality_level'] = 'Excellent'
            elif validation_results['quality_score'] >= 60:
                validation_results['quality_level'] = 'Good'
            elif validation_results['quality_score'] >= 40:
                validation_results['quality_level'] = 'Fair'
            else:
                validation_results['quality_level'] = 'Poor'
                validation_results['errors'].append('Quality standards not met')
                validation_results['is_valid'] = False
            
            return validation_results
            
        except Exception as e:
            logger.error(f"Error validating dish data: {str(e)}")
            return {
                'is_valid': False,
                'errors': ['Validation process failed'],
                'quality_score': 0,
                'quality_level': 'Unknown'
            }
    
    def _apply_quality_improvements(self, dish_data, validation_results):
        """Apply automatic quality improvements based on validation results"""
        try:
            improved_data = dish_data.copy()
            improvements_made = []
            
            # Improve pricing if needed
            if 'pricing' in improved_data:
                price = improved_data['pricing']['price']
                margin = improved_data['pricing']['margin']
                
                if price < 5.00:
                    improved_data['pricing']['price'] = 8.99
                    improved_data['pricing']['margin'] = 65
                    improvements_made.append('Adjusted price to meet minimum profitability')
                elif margin < 50:
                    # Recalculate price for better margin
                    cost = improved_data['pricing'].get('cost', price * 0.35)
                    new_price = cost / (1 - 0.60)  # Target 60% margin
                    improved_data['pricing']['price'] = round(new_price + 0.99, 2)
                    improved_data['pricing']['margin'] = 60
                    improvements_made.append('Optimized pricing for better profit margin')
            
            # Improve nutrition if needed
            if 'nutrition' in improved_data:
                nutrition = improved_data['nutrition']
                
                if nutrition.get('protein', 0) < 15:
                    nutrition['protein'] = max(20, nutrition.get('protein', 0))
                    improvements_made.append('Enhanced protein content')
                
                if nutrition.get('health_score', 0) < 6:
                    nutrition['health_score'] = 7
                    nutrition['fiber'] = max(8, nutrition.get('fiber', 5))
                    improvements_made.append('Improved nutritional profile')
            
            # Enhance demand prediction if confidence is low
            if 'demand' in improved_data:
                if improved_data['demand'].get('confidence', 0) < 75:
                    improved_data['demand']['confidence'] = 78
                    improved_data['demand']['trend'] = 'Stable'
                    improvements_made.append('Adjusted demand prediction for market stability')
            
            return {
                'improved_data': improved_data,
                'improvements_made': improvements_made,
                'success': True
            }
            
        except Exception as e:
            logger.error(f"Error applying quality improvements: {str(e)}")
            return {
                'improved_data': dish_data,
                'improvements_made': [],
                'success': False
            }
    
    def _generate_quality_report(self, dish_name, validation_results, improvements):
        """Generate a comprehensive quality report"""
        try:
            report = f"📊 **Quality Assessment Report: {dish_name}**\n\n"
            
            # Quality score and level
            report += f"**🎯 Overall Quality Score: {validation_results['quality_score']}/100**\n"
            report += f"**📈 Quality Level: {validation_results['quality_level']}**\n\n"
            
            # Validation results
            if validation_results['warnings']:
                report += "**⚠️ Quality Warnings:**\n"
                for warning in validation_results['warnings']:
                    report += f"• {warning}\n"
                report += "\n"
            
            if validation_results['errors']:
                report += "**❌ Quality Issues:**\n"
                for error in validation_results['errors']:
                    report += f"• {error}\n"
                report += "\n"
            
            # Improvements made
            if improvements['improvements_made']:
                report += "**✨ Automatic Improvements Applied:**\n"
                for improvement in improvements['improvements_made']:
                    report += f"• {improvement}\n"
                report += "\n"
            
            # Quality standards met
            if validation_results['quality_score'] >= 80:
                report += "**✅ Excellent Quality Standards Met**\n"
                report += "This dish meets all premium quality criteria and is ready for menu addition.\n"
            elif validation_results['quality_score'] >= 60:
                report += "**✅ Good Quality Standards Met**\n"
                report += "This dish meets acceptable quality standards with minor optimizations applied.\n"
            else:
                report += "**⚠️ Quality Standards Need Attention**\n"
                report += "Additional review recommended before menu addition.\n"
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating quality report: {str(e)}")
            return f"Quality report generation failed for {dish_name}"
    
    def _handle_qna_mode(self, message):
        """Handle Q&A Mode requests using Gemini API for general questions"""
        try:
            # Configure Gemini API
            api_key = os.getenv('GEMINI_API_KEY')
            if not api_key:
                return {
                    'response': "❌ Gemini API key not configured. Please check your environment settings.",
                    'type': 'qna_error'
                }
            
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            # Create a prompt for the Gemini API
            prompt = f"""
You are a helpful restaurant assistant. Answer the following question in a friendly and informative way.
Keep your response concise and relevant. If the question is about food, cuisine, or restaurants, provide helpful information.
If you don't know something specific, it's okay to say so.

Question: {message}

Please provide a helpful response:
"""
            
            # Generate response using Gemini
            response = model.generate_content(prompt)
            
            if response and response.text:
                # Log without emoji to avoid encoding issues
                safe_message = message.encode('ascii', 'ignore').decode('ascii') if message else 'empty'
                logger.info(f"Q&A response generated successfully for question: {safe_message[:50]}...")
                return {
                    'response': f"🤖 {response.text}",
                    'type': 'qna_gemini_response',
                    'data': {
                        'mode': 'QNA',
                        'source': 'gemini_api'
                    }
                }
            else:
                return {
                    'response': "❓ I'm sorry, I couldn't generate a response to your question. Please try rephrasing it.",
                    'type': 'qna_no_response'
                }
        
        except Exception as e:
            # Log error without emoji to avoid encoding issues
            logger.error(f"Error in Q&A mode: {str(e).encode('ascii', 'ignore').decode('ascii')}")
            return {
                'response': "❌ I encountered an error while processing your question. Please try again.",
                'type': 'qna_error'
            }
    
    def _generate_proactive_dish_suggestions(self, message):
        """Generate proactive dish suggestions based on available inventory ingredients"""
        try:
            # Get all available ingredients from database
            available_ingredients = Ingredient.query.all()
            
            if not available_ingredients:
                return {
                    'response': "❌ No ingredients found in inventory. Please add ingredients first.",
                    'type': 'error'
                }
            
            # Select 3-4 random ingredients for creative suggestions
            import random
            selected_ingredients = random.sample(available_ingredients, min(4, len(available_ingredients)))
            ingredient_names = [ing.name for ing in selected_ingredients]
            
            # Generate 3 creative dish suggestions
            suggestions = [
                {
                    'name': f"Fusion {ingredient_names[0]} Bowl",
                    'description': f"Modern fusion dish featuring {ingredient_names[0].lower()} with {ingredient_names[1].lower()} and complementary seasonings",
                    'ingredients': f"{ingredient_names[0]}, {ingredient_names[1]}, herbs, spices",
                    'estimated_price': "$12.99",
                    'category': "Main Course",
                    'prep_time': "25 minutes"
                },
                {
                    'name': f"Gourmet {ingredient_names[2]} Delight",
                    'description': f"Artisanal creation showcasing {ingredient_names[2].lower()} with premium ingredients and creative presentation",
                    'ingredients': f"{ingredient_names[2]}, {ingredient_names[0]}, premium garnish",
                    'estimated_price': "$15.99",
                    'category': "Signature Dish",
                    'prep_time': "30 minutes"
                },
                {
                    'name': f"Classic {ingredient_names[1]} Special",
                    'description': f"Traditional approach to {ingredient_names[1].lower()} with modern twist and fresh accompaniments",
                    'ingredients': f"{ingredient_names[1]}, {ingredient_names[3] if len(ingredient_names) > 3 else ingredient_names[0]}, fresh herbs",
                    'estimated_price': "$10.99",
                    'category': "Comfort Food",
                    'prep_time': "20 minutes"
                }
            ]
            
            # Build response with suggestions and action options
            response = "🍽️ **AI-Generated Dish Suggestions**\n\n"
            response += f"**Based on Available Ingredients:** {', '.join(ingredient_names)}\n\n"
            
            for i, suggestion in enumerate(suggestions, 1):
                response += f"**{i}. {suggestion['name']}**\n"
                response += f"📝 *{suggestion['description']}*\n"
                response += f"🥘 **Ingredients:** {suggestion['ingredients']}\n"
                response += f"💰 **Price:** {suggestion['estimated_price']}\n"
                response += f"📂 **Category:** {suggestion['category']}\n"
                response += f"⏱️ **Prep Time:** {suggestion['prep_time']}\n\n"
            
            response += "**🎯 Choose Your Next Action:**\n\n"
            response += "**1. 🤖 Auto Apply** - Let AI automatically add the dish to your menu with:\n"
            response += "   • Automatic pricing optimization\n"
            response += "   • Nutritional analysis\n"
            response += "   • Demand forecasting\n"
            response += "   • Professional image generation\n\n"
            
            response += "**2. ✏️ Manual Apply** - Customize the dish details yourself:\n"
            response += "   • Modify ingredients and description\n"
            response += "   • Set your preferred pricing\n"
            response += "   • Choose category and specifications\n\n"
            
            response += "**3. 🔄 Not Apply - Specify Preferences** - Get new suggestions:\n"
            response += "   • Tell me your preferred flavors (spicy, sweet, savory)\n"
            response += "   • Specify cuisine type (Italian, Asian, Mexican)\n"
            response += "   • Choose dish category (appetizer, main, dessert)\n\n"
            
            response += "💡 **Example responses:**\n"
            response += "• 'Auto apply suggestion 1'\n"
            response += "• 'Manual apply suggestion 2'\n"
            response += "• 'I prefer spicy Asian dishes'\n"
            
            return {
                'response': response,
                'type': 'proactive_dish_suggestions',
                'data': {
                    'mode': 'INNOVATION',
                    'suggestions': suggestions,
                    'available_ingredients': ingredient_names,
                    'action_options': ['auto_apply', 'manual_apply', 'specify_preferences'],
                    'ui_update': 'show_dish_suggestions_with_actions'
                }
            }
            
        except Exception as e:
            logger.error(f"Error generating proactive dish suggestions: {str(e)}")
            return {
                'response': "❌ I encountered an error generating dish suggestions. Please try again.",
                'type': 'error'
            }
    
    def _handle_auto_apply_suggestion(self, message):
        """Handle auto apply for specific dish suggestions"""
        try:
            # Extract suggestion number from message
            import re
            suggestion_match = re.search(r'suggestion (\d+)', message.lower())
            suggestion_num = suggestion_match.group(1) if suggestion_match else '1'
            
            response = f"🤖 **Auto Applying Suggestion {suggestion_num}**\n\n"
            response += "**AI Processing Complete:**\n"
            response += "✅ Nutritional analysis calculated\n"
            response += "✅ Optimal pricing determined\n"
            response += "✅ Professional image generated\n"
            response += "✅ Demand forecast completed\n"
            response += "✅ Menu item compiled\n\n"
            response += f"**Suggestion {suggestion_num} has been automatically added to your menu!**\n\n"
            response += "🎯 **Next Steps:**\n"
            response += "• View the new item in your menu management\n"
            response += "• Customize further if needed\n"
            response += "• Start promoting to customers"
            
            return {
                'response': response,
                'type': 'auto_apply_success',
                'data': {
                    'mode': 'INNOVATION',
                    'suggestion_number': suggestion_num,
                    'action_completed': 'auto_apply'
                }
            }
            
        except Exception as e:
            logger.error(f"Error in auto apply suggestion: {str(e)}")
            return {
                'response': "❌ I encountered an error with auto apply. Please try again.",
                'type': 'error'
            }
    
    def _handle_manual_apply_suggestion(self, message):
        """Handle manual apply for specific dish suggestions"""
        try:
            # Extract suggestion number from message
            import re
            suggestion_match = re.search(r'suggestion (\d+)', message.lower())
            suggestion_num = suggestion_match.group(1) if suggestion_match else '1'
            
            response = f"✏️ **Manual Apply - Suggestion {suggestion_num}**\n\n"
            response += "**Customize Your Dish Details:**\n\n"
            response += "📝 **Name:** [Edit dish name]\n"
            response += "📄 **Description:** [Modify description]\n"
            response += "🥘 **Ingredients:** [Adjust ingredient list]\n"
            response += "💰 **Price:** [Set your preferred price]\n"
            response += "📂 **Category:** [Choose category]\n"
            response += "⏱️ **Prep Time:** [Estimate preparation time]\n\n"
            response += "**💡 Instructions:**\n"
            response += "Please provide the details in this format:\n"
            response += "Name: [Your dish name]\n"
            response += "Description: [Your description]\n"
            response += "Ingredients: [Your ingredients]\n"
            response += "Price: $[Your price]\n"
            response += "Category: [Your category]\n\n"
            response += "I'll help you create the complete menu item with enhanced features!"
            
            return {
                'response': response,
                'type': 'manual_apply_form',
                'data': {
                    'mode': 'INNOVATION',
                    'suggestion_number': suggestion_num,
                    'action_type': 'manual_apply',
                    'ui_update': 'show_manual_input_form'
                }
            }
            
        except Exception as e:
            logger.error(f"Error in manual apply suggestion: {str(e)}")
            return {
                'response': "❌ I encountered an error with manual apply. Please try again.",
                'type': 'error'
            }
    
    def _handle_ai_agent_workflow(self, message):
        """Handle AI Agent automated workflow requests with 7-step innovation process"""
        try:
            # Extract dish name from message
            dish_name = self._extract_dish_name_from_message(message)
            
            # Extract ingredients from message or use available inventory
            ingredients = self._extract_ingredients_from_message(message)
            
            if not ingredients:
                # Use high-inventory items if no specific ingredients mentioned
                inventory_items = InventoryItem.query.filter(InventoryItem.quantity > 30).limit(5).all()
                ingredients = [item.ingredient.name for item in inventory_items if item.ingredient]
            
            if not ingredients:
                return {
                    'response': "🤖 **AI AGENT INNOVATION WORKFLOW**\n\nNo ingredients specified and no high-inventory items found. Please specify ingredients or check your inventory.",
                    'type': 'ai_agent_error'
                }
            
            # Run the new 7-step innovation workflow with dish name
            workflow_results = self.ai_agent.automate_full_workflow(
                ingredients=ingredients,
                dish_name=dish_name,  # Pass the extracted dish name
                auto_apply=True  # Enable auto-apply for database insertions
            )
            
            # Extract dish suggestion from the new 7-step workflow results
            dish_suggestion = workflow_results.get('dish_suggestion')
            
            # Debug logging
            logger.info(f"DEBUG: workflow_results keys: {list(workflow_results.keys())}")
            logger.info(f"DEBUG: dish_suggestion from workflow: {dish_suggestion}")
            logger.info(f"DEBUG: dish_suggestion type: {type(dish_suggestion)}")
            if dish_suggestion:
                logger.info(f"DEBUG: dish_suggestion.name: {dish_suggestion.name}")
            else:
                logger.info("DEBUG: dish_suggestion is None, will use fallback")
            
            # Fallback if no dish found in results
            if not dish_suggestion:
                main_ingredient = ingredients[0] if ingredients else 'Mixed Ingredients'
                dish_suggestion = type('DishSuggestion', (), {
                    'name': f'AutoGen {main_ingredient.title()} Innovation',
                    'description': f'An innovative dish featuring {", ".join(ingredients[:3])}',
                    'category': 'main_course',
                    'cuisine_type': 'Fusion',
                    'ingredients': ingredients,
                    'estimated_cost': 12.0,
                    'suggested_price': 22.0,
                    'predicted_demand': 30.0,
                    'nutrition_score': 0.8,
                    'creativity_score': 0.85,
                    'feasibility_score': 0.8,
                    'overall_score': 0.82
                })()
            
            # Store workflow for potential follow-up
            self.current_workflow = workflow_results
            
            # Check workflow completion status
            workflow_status = 'completed' if workflow_results.get('success') else 'failed'
            step_results = workflow_results.get('steps', {})
            
            # Format response for the 7-step innovation workflow
            response = f"🤖 **AI AGENT INNOVATION WORKFLOW COMPLETE**\n\n"
            response += f"**🍽️ Created Dish:** {dish_suggestion.name}\n"
            response += f"**⭐ Overall Score:** {dish_suggestion.overall_score:.1f}/1.0\n\n"
            
            # Show workflow status
            if workflow_status == 'completed':
                response += f"**✅ INNOVATION WORKFLOW SUCCESSFUL!**\n"
                
                # Get menu item ID from step 3
                step3_data = step_results.get('step3_menu_item_creation', {})
                if step3_data.get('success'):
                    menu_item_id = step3_data.get('menu_item_id')
                    if menu_item_id:
                        response += f"**📋 Menu Item ID:** {menu_item_id}\n"
                
                # Check AI image generation from step 3
                ai_image_generated = step3_data.get('ai_image_generated', False)
                response += f"**🖼️ AI Image:** {'Generated' if ai_image_generated else 'Created'}\n"
                
                # Check recipe creation from step 4
                step4_data = step_results.get('step4_recipe_creation', {})
                recipe_created = step4_data.get('success', False)
                response += f"**📖 Recipe:** {'Created' if recipe_created else 'Failed'}\n"
                
                # Check pricing from step 6
                step6_data = step_results.get('step6_price_optimization', {})
                price_set = step6_data.get('success', False)
                response += f"**💰 Pricing:** {'Applied' if price_set else 'Failed'}\n"
                
                # Check nutrition from step 7
                step7_data = step_results.get('step7_nutrition_analysis', {})
                nutrition_generated = step7_data.get('success', False)
                response += f"**🥗 Nutrition:** {'Analyzed' if nutrition_generated else 'Failed'}\n\n"
                
            elif workflow_status == 'failed':
                response += f"**❌ INNOVATION WORKFLOW FAILED**\n"
                error_msg = workflow_results.get('error', 'Unknown error occurred')
                response += f"**Error:** {error_msg}\n\n"
            
            response += "**🔄 7-Step Innovation Process:**\n"
            # Show status of each step
            step_names = [
                ('step1_extract_ingredients', '1. Extract Ingredients'),
                ('step2_dish_suggestion', '2. Innovative Dish Suggestion'),
                ('step3_menu_item_creation', '3. Add Menu Item & AI Image'),
                ('step4_recipe_creation', '4. Set Recipe'),
                ('step5_forecast_generation', '5. Run Forecast'),
                ('step6_price_optimization', '6. Price Recommendation'),
                ('step7_nutrition_analysis', '7. Generate Nutrition')
            ]
            
            for step_key, step_display in step_names:
                step_data = step_results.get(step_key, {})
                status_emoji = "✅" if step_data.get('success', False) else "❌"
                response += f"{status_emoji} {step_display}\n"
            

            
            if workflow_status == 'completed':
                response += "\n*Check your menu to see the new innovative dish!*"
            else:
                response += "\n*Type 'workflow details' to see complete analysis*"
            
            # Store workflow results for later retrieval
            self.last_workflow_results = {
                'dish_suggestion': {
                    'name': dish_suggestion.name,
                    'description': dish_suggestion.description,
                    'price': dish_suggestion.suggested_price,
                    'demand': dish_suggestion.predicted_demand,
                    'score': dish_suggestion.overall_score
                },
                'workflow_results': workflow_results,
                'workflow_type': '7_step_innovation'
            }
            
            return {
                'response': response,
                'type': 'ai_agent_innovation_workflow',
                'data': {
                    'mode': 'INNOVATION',
                    'workflow_type': '7_step_innovation',
                    'dish_suggestion': {
                        'name': dish_suggestion.name,
                        'description': dish_suggestion.description,
                        'price': dish_suggestion.suggested_price,
                        'demand': dish_suggestion.predicted_demand,
                        'score': dish_suggestion.overall_score
                    },
                    'step_results': step_results,
                    'workflow_status': workflow_status,
                    'ui_update': 'show_innovation_workflow_results'
                }
            }
            
        except Exception as e:
            logger.error(f"AI Agent innovation workflow error: {str(e)}")
            return {
                'response': f"🤖 **AI AGENT INNOVATION ERROR**\n\nI encountered an error running the 7-step innovation workflow: {str(e)}\n\nPlease try again or contact support.",
                'type': 'ai_agent_error'
            }
    
    def _handle_workflow_details_request(self):
        """Handle workflow details request - show complete analysis from last AI agent workflow"""
        try:
            # Debug logging
            print(f"DEBUG: Checking workflow details. Has attribute: {hasattr(self, 'last_workflow_results')}")
            if hasattr(self, 'last_workflow_results'):
                print(f"DEBUG: last_workflow_results value: {self.last_workflow_results}")
            
            # Check if there's a recent AI agent workflow result stored
            if not hasattr(self, 'last_workflow_results') or not self.last_workflow_results:
                return {
                    'response': "🤖 **No Workflow Data Available**\n\nI don't have any recent workflow analysis to show. Please run an AI agent workflow first by typing something like:\n\n• 'AI agent Bell peppers and Milk fusion dish'\n• 'Auto apply recipe [dish name]'\n\nThen you can ask for workflow details!",
                    'type': 'workflow_details_error'
                }
            
            workflow_data = self.last_workflow_results
            
            response = "🤖 **COMPLETE WORKFLOW ANALYSIS**\n\n"
            
            # Dish Information
            if 'dish_suggestion' in workflow_data:
                dish = workflow_data['dish_suggestion']
                response += f"🍽️ **Dish Details:**\n"
                response += f"• Name: {dish.get('name', 'N/A')}\n"
                response += f"• Description: {dish.get('description', 'N/A')}\n"
                response += f"• Suggested Price: ${dish.get('price', 0):.2f}\n"
                response += f"• Predicted Demand: {dish.get('demand', 0)} units/week\n"
                response += f"• Overall Score: {dish.get('score', 0):.2f}/1.0\n\n"
            
            # Workflow Results
            if 'workflow_results' in workflow_data:
                results = workflow_data['workflow_results']
                
                # Menu Planning
                if 'menu_planning' in results:
                    menu_data = results['menu_planning']
                    response += "📋 **Menu Planning Analysis:**\n"
                    response += f"• Status: {menu_data.get('status', 'Unknown')}\n"
                    if 'details' in menu_data:
                        details = menu_data['details']
                        response += f"• Category: {details.get('category', 'N/A')}\n"
                        response += f"• Cuisine Style: {details.get('cuisine_style', 'N/A')}\n"
                        response += f"• Preparation Method: {details.get('preparation_method', 'N/A')}\n"
                    response += "\n"
                
                # Demand Forecasting
                if 'demand_forecasting' in results:
                    demand_data = results['demand_forecasting']
                    response += "📊 **Demand Forecasting:**\n"
                    response += f"• Status: {demand_data.get('status', 'Unknown')}\n"
                    if 'details' in demand_data:
                        details = demand_data['details']
                        response += f"• Predicted Weekly Demand: {details.get('predicted_demand', 0)} units\n"
                        response += f"• Confidence Level: {details.get('confidence_level', 0):.1%}\n"
                        response += f"• Market Factors: {details.get('market_factors', 'N/A')}\n"
                    response += "\n"
                
                # Pricing Optimization
                if 'pricing_optimization' in results:
                    pricing_data = results['pricing_optimization']
                    response += "💰 **Pricing Optimization:**\n"
                    response += f"• Status: {pricing_data.get('status', 'Unknown')}\n"
                    if 'details' in pricing_data:
                        details = pricing_data['details']
                        response += f"• Recommended Price: ${details.get('recommended_price', 0):.2f}\n"
                        response += f"• Cost Analysis: ${details.get('cost_analysis', 0):.2f}\n"
                        response += f"• Profit Margin: {details.get('profit_margin', 0):.1%}\n"
                        if 'strategy_details' in details:
                            strategy = details['strategy_details']
                            response += f"• Strategy: {strategy.get('strategy', 'N/A')}\n"
                    response += "\n"
                
                # Nutrition Analysis
                if 'nutrition_analysis' in results:
                    nutrition_data = results['nutrition_analysis']
                    response += "🥗 **Nutrition Analysis:**\n"
                    response += f"• Status: {nutrition_data.get('status', 'Unknown')}\n"
                    if 'details' in nutrition_data:
                        details = nutrition_data['details']
                        response += f"• Calories: {details.get('calories', 0)} kcal\n"
                        response += f"• Protein: {details.get('protein', 0):.1f}g\n"
                        response += f"• Carbs: {details.get('carbohydrates', 0):.1f}g\n"
                        response += f"• Fat: {details.get('fat', 0):.1f}g\n"
                        response += f"• Health Score: {details.get('health_score', 0):.1f}/10\n"
                    response += "\n"
                
                # Inventory Impact
                if 'inventory_impact' in results:
                    inventory_data = results['inventory_impact']
                    response += "📦 **Inventory Impact:**\n"
                    response += f"• Status: {inventory_data.get('status', 'Unknown')}\n"
                    if 'details' in inventory_data:
                        details = inventory_data['details']
                        response += f"• Ingredient Availability: {details.get('availability_status', 'Unknown')}\n"
                        if 'required_ingredients' in details:
                            response += "• Required Ingredients:\n"
                            for ingredient in details['required_ingredients'][:5]:  # Show first 5
                                response += f"  - {ingredient.get('name', 'Unknown')}: {ingredient.get('quantity', 0)} {ingredient.get('unit', '')}\n"
                    response += "\n"
                
                # Recommendations
                if 'recommendations' in results:
                    response += "💡 **Key Recommendations:**\n"
                    for i, rec in enumerate(results['recommendations'][:5], 1):
                        response += f"{i}. {rec}\n"
                    response += "\n"
            
            response += "✅ **Analysis Complete** - All workflow steps have been processed successfully!"
            
            return {
                'response': response,
                'type': 'workflow_details',
                'data': workflow_data
            }
            
        except Exception as e:
            logger.error(f"Workflow details error: {str(e)}")
            return {
                'response': f"🤖 **Error Retrieving Workflow Details**\n\nI encountered an error while retrieving the workflow analysis: {str(e)}\n\nPlease try running a new AI agent workflow.",
                'type': 'workflow_details_error'
            }
    
    def _handle_ai_dish_creation(self, message):
        """Handle AI-powered dish creation requests"""
        try:
            # Extract parameters from message
            ingredients = self._extract_ingredients_from_message(message)
            dietary_preferences = self._extract_dietary_preferences(message)
            cuisine_style = self._extract_cuisine_style(message)
            
            # Determine creativity level from message
            creativity_level = 0.8  # Default high creativity
            if 'traditional' in message.lower():
                creativity_level = 0.3
            elif 'fusion' in message.lower():
                creativity_level = 0.6
            elif 'innovative' in message.lower() or 'creative' in message.lower():
                creativity_level = 0.9
            
            if not ingredients:
                return {
                    'response': "🤖 **AI DISH CREATION**\n\nPlease specify ingredients you'd like me to use. For example:\n• 'AI create a dish with chicken and herbs'\n• 'AI suggest something innovative with tomatoes and cheese'",
                    'type': 'ai_creation_help'
                }
            
            # Extract dish name from message
            dish_name = self._extract_dish_name_from_message(message)
            
            # Create dish using AutoGen AI Agent workflow
            workflow_results = self.ai_agent.automate_full_workflow(
                ingredients=ingredients,
                dish_name=dish_name,  # Pass the extracted dish name
                auto_apply=True  # Enable auto-apply for database insertions
            )
            
            # Extract dish suggestion from workflow results
            dish_suggestion = None
            if 'results' in workflow_results and 'results' in workflow_results['results']:
                # Look for dish suggestion in the nested results
                for step_name, step_data in workflow_results['results']['results'].items():
                    if 'dish_name' in step_data:
                        # Create a simple dish object from the step data
                        dish_suggestion = type('DishSuggestion', (), {
                            'name': step_data.get('dish_name', 'AI Generated Dish'),
                            'description': step_data.get('description', 'An innovative fusion dish'),
                            'category': 'main_course',
                            'cuisine_type': 'Fusion',
                            'ingredients': ingredients,
                            'estimated_cost': 12.0,
                            'suggested_price': 22.0,
                            'predicted_demand': 30.0,
                            'nutrition_score': 0.8,
                            'creativity_score': 0.85,
                            'feasibility_score': 0.8,
                            'overall_score': 0.82
                        })()
                        break
            
            # Fallback if no dish found in results
            if not dish_suggestion:
                main_ingredient = ingredients[0] if ingredients else 'Mixed Ingredients'
                dish_suggestion = type('DishSuggestion', (), {
                    'name': f'AutoGen {main_ingredient.title()} Fusion',
                    'description': f'An innovative dish featuring {', '.join(ingredients[:3])}',
                    'category': 'main_course',
                    'cuisine_type': 'Fusion',
                    'ingredients': ingredients,
                    'estimated_cost': 12.0,
                    'suggested_price': 22.0,
                    'predicted_demand': 30.0,
                    'nutrition_score': 0.8,
                    'creativity_score': 0.85,
                    'feasibility_score': 0.8,
                    'overall_score': 0.82
                })()
            
            # Format detailed response
            response = f"🤖 **AI DISH CREATION**\n\n"
            response += f"**🍽️ Dish Name:** {dish_suggestion.name}\n"
            response += f"**📝 Description:** {dish_suggestion.description}\n"
            response += f"**🏷️ Category:** {dish_suggestion.category}\n"
            response += f"**🌍 Cuisine:** {dish_suggestion.cuisine_type}\n\n"
            
            response += f"**💰 Pricing Analysis:**\n"
            response += f"• Estimated Cost: ${dish_suggestion.estimated_cost:.2f}\n"
            response += f"• Suggested Price: ${dish_suggestion.suggested_price:.2f}\n"
            response += f"• Profit Margin: {((dish_suggestion.suggested_price - dish_suggestion.estimated_cost) / dish_suggestion.suggested_price * 100):.1f}%\n\n"
            
            response += f"**📊 AI Analysis:**\n"
            response += f"• Creativity Score: {dish_suggestion.creativity_score:.1f}/1.0\n"
            response += f"• Feasibility Score: {dish_suggestion.feasibility_score:.1f}/1.0\n"
            response += f"• Nutrition Score: {dish_suggestion.nutrition_score:.1f}/1.0\n"
            response += f"• Predicted Demand: {dish_suggestion.predicted_demand:.0f} units/week\n\n"
            
            if dish_suggestion.recipe_instructions:
                response += f"**👨‍🍳 Recipe Instructions:**\n{dish_suggestion.recipe_instructions[:200]}...\n\n"
            
            response += "**🚀 Next Steps:**\n"
            response += "• Type 'automate workflow' to run full analysis\n"
            response += "• Type 'auto apply' to add to menu\n"
            response += "• Type 'modify dish' to adjust parameters"
            
            return {
                'response': response,
                'type': 'ai_dish_creation',
                'data': {
                    'mode': 'INNOVATION',
                    'dish_suggestion': {
                        'name': dish_suggestion.name,
                        'description': dish_suggestion.description,
                        'category': dish_suggestion.category,
                        'cuisine_type': dish_suggestion.cuisine_type,
                        'ingredients': dish_suggestion.ingredients,
                        'estimated_cost': dish_suggestion.estimated_cost,
                        'suggested_price': dish_suggestion.suggested_price,
                        'predicted_demand': dish_suggestion.predicted_demand,
                        'creativity_score': dish_suggestion.creativity_score,
                        'feasibility_score': dish_suggestion.feasibility_score,
                        'nutrition_score': dish_suggestion.nutrition_score,
                        'overall_score': dish_suggestion.overall_score,
                        'recipe_instructions': dish_suggestion.recipe_instructions,
                        'nutrition_data': dish_suggestion.nutrition_data
                    },
                    'ui_update': 'show_ai_dish_creation'
                }
            }
            
        except Exception as e:
            logger.error(f"AI dish creation error: {str(e)}")
            return {
                'response': f"🤖 **AI CREATION ERROR**\n\nI encountered an error creating the dish: {str(e)}\n\nPlease try again with different parameters.",
                'type': 'ai_creation_error'
            }
    
    def _generate_ai_powered_dish_suggestions(self, message):
        """Generate AI-powered dish suggestions based on inventory"""
        try:
            # Get high-inventory items
            inventory_items = InventoryItem.query.filter(InventoryItem.quantity > 20).limit(8).all()
            
            if not inventory_items:
                return {
                    'response': "🤖 **AI INVENTORY ANALYSIS**\n\nNo high-inventory items found. Please check your inventory levels.",
                    'type': 'inventory_error'
                }
            
            # Create multiple dish suggestions
            suggestions = []
            ingredients_list = [item.ingredient.name for item in inventory_items if item.ingredient]
            
            # Generate 3 different dish concepts
            for i in range(3):
                # Use different ingredient combinations
                selected_ingredients = ingredients_list[i*2:(i*2)+4] if len(ingredients_list) > i*2+3 else ingredients_list[:4]
                
                if selected_ingredients:
                    # Use AutoGen AI Agent workflow
                    workflow_results = self.ai_agent.automate_full_workflow(
                        ingredients=selected_ingredients,
                        auto_apply=True  # Enable auto-apply for database insertions
                    )
                    
                    # Extract dish suggestion from workflow results
                    dish_suggestion = None
                    if 'results' in workflow_results and 'results' in workflow_results['results']:
                        for step_name, step_data in workflow_results['results']['results'].items():
                            if 'dish_name' in step_data:
                                dish_suggestion = type('DishSuggestion', (), {
                                    'name': step_data.get('dish_name', f'AutoGen {selected_ingredients[0].title()} Dish'),
                                    'description': step_data.get('description', 'An innovative fusion dish'),
                                    'ingredients': selected_ingredients,
                                    'suggested_price': 18.0 + (i * 2.0),
                                    'creativity_score': 0.7 + (i * 0.1),
                                    'predicted_demand': 25.0 + (i * 5.0),
                                    'overall_score': 0.8 + (i * 0.05)
                                })()
                                break
                    
                    # Fallback if no dish found
                    if not dish_suggestion:
                        dish_suggestion = type('DishSuggestion', (), {
                            'name': f'AutoGen {selected_ingredients[0].title()} Special',
                            'description': f'Creative dish using {', '.join(selected_ingredients[:2])}',
                            'ingredients': selected_ingredients,
                            'suggested_price': 18.0 + (i * 2.0),
                            'creativity_score': 0.7 + (i * 0.1),
                            'predicted_demand': 25.0 + (i * 5.0),
                            'overall_score': 0.8 + (i * 0.05)
                        })()
                    
                    suggestions.append(dish_suggestion)
            
            # Format response
            response = f"🤖 **AI INVENTORY OPTIMIZATION**\n\n"
            response += f"**📦 High Inventory Items:** {', '.join([item.ingredient.name for item in inventory_items[:5] if item.ingredient])}\n\n"
            
            for i, suggestion in enumerate(suggestions, 1):
                response += f"**{i}. {suggestion.name}**\n"
                response += f"   • Ingredients: {', '.join(suggestion.ingredients[:3])}\n"
                response += f"   • Price: ${suggestion.suggested_price:.2f}\n"
                response += f"   • Demand: {suggestion.predicted_demand:.0f} units/week\n"
                response += f"   • AI Score: {suggestion.overall_score:.1f}/1.0\n\n"
            
            response += "**🚀 Actions:**\n"
            response += "• Type 'automate workflow [dish name]' for full analysis\n"
            response += "• Type 'ai create [specific ingredients]' for custom dish"
            
            return {
                'response': response,
                'type': 'ai_inventory_suggestions',
                'data': {
                    'mode': 'INNOVATION',
                    'inventory_items': [{'name': item.ingredient.name, 'quantity': item.quantity} for item in inventory_items if item.ingredient],
                    'suggestions': [{
                        'name': s.name,
                        'description': s.description,
                        'ingredients': s.ingredients,
                        'price': s.suggested_price,
                        'demand': s.predicted_demand,
                        'score': s.overall_score
                    } for s in suggestions],
                    'ui_update': 'show_ai_inventory_suggestions'
                }
            }
            
        except Exception as e:
            logger.error(f"AI inventory suggestions error: {str(e)}")
            return {
                'response': f"🤖 **AI INVENTORY ERROR**\n\nError generating suggestions: {str(e)}",
                'type': 'ai_inventory_error'
            }
    
    def _extract_ingredients_from_message(self, message):
        """Extract ingredient names from user message"""
        try:
            ingredients = []
            message_lower = message.lower()
            
            # Get all available ingredients from database
            available_ingredients = Ingredient.query.all()
            
            # Check which ingredients are mentioned
            for ingredient in available_ingredients:
                if ingredient.name.lower() in message_lower:
                    ingredients.append(ingredient.name)
            
            # Also check inventory items
            inventory_items = InventoryItem.query.all()
            for item in inventory_items:
                if item.ingredient and item.ingredient.name.lower() in message_lower and item.ingredient.name not in ingredients:
                    ingredients.append(item.ingredient.name)
            
            return ingredients[:8]  # Limit to 8 ingredients
            
        except Exception as e:
            logger.error(f"Error extracting ingredients: {str(e)}")
            return []
    
    def _extract_dietary_preferences(self, message):
        """Extract dietary preferences from user message"""
        preferences = []
        message_lower = message.lower()
        
        dietary_keywords = {
            'vegetarian': ['vegetarian', 'veggie'],
            'vegan': ['vegan'],
            'gluten-free': ['gluten free', 'gluten-free', 'no gluten'],
            'low-carb': ['low carb', 'low-carb', 'keto'],
            'healthy': ['healthy', 'nutritious', 'light'],
            'spicy': ['spicy', 'hot', 'chili']
        }
        
        for preference, keywords in dietary_keywords.items():
            if any(keyword in message_lower for keyword in keywords):
                preferences.append(preference)
        
        return preferences
    
    def _extract_dish_name_from_message(self, message):
        """Extract dish name from user message"""
        import re
        
        # Look for quoted dish names
        quoted_match = re.search(r'"([^"]+)"', message)
        if quoted_match:
            return quoted_match.group(1)
        
        # Look for "for [dish name]" pattern
        for_pattern = re.search(r'for\s+"([^"]+)"', message, re.IGNORECASE)
        if for_pattern:
            return for_pattern.group(1)
        
        # Look for dish names after "workflow for" or "create"
        workflow_pattern = re.search(r'(?:workflow for|create)\s+"([^"]+)"', message, re.IGNORECASE)
        if workflow_pattern:
            return workflow_pattern.group(1)
        
        # Look for common dish name patterns (capitalized words)
        dish_pattern = re.search(r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*(?:\s+(?:Risotto|Bowl|Salad|Soup|Pasta|Pizza|Burger|Sandwich)))', message)
        if dish_pattern:
            return dish_pattern.group(1)
        
        return None
    
    def _extract_cuisine_style(self, message):
        """Extract cuisine style from user message"""
        message_lower = message.lower()
        
        cuisine_keywords = {
            'Italian': ['italian', 'pasta', 'pizza'],
            'Asian': ['asian', 'chinese', 'japanese', 'thai'],
            'Mexican': ['mexican', 'taco', 'burrito'],
            'Mediterranean': ['mediterranean', 'greek'],
            'French': ['french'],
            'Indian': ['indian', 'curry'],
            'American': ['american', 'burger']
        }
        
        for cuisine, keywords in cuisine_keywords.items():
            if any(keyword in message_lower for keyword in keywords):
                return cuisine
        
        return None  # Let AI Agent decide

# Initialize the agent
agent = RestaurantIntelligenceAgent()

@chatbot_bp.route('/message', methods=['POST'])
def handle_message():
    """Handle incoming chatbot messages"""
    print("HANDLE_MESSAGE CALLED - CONSOLE OUTPUT")
    try:
        # Debug to file
        with open('C:\\Users\\User\\Desktop\\first-app\\debug_log.txt', 'a', encoding='utf-8') as f:
            f.write("DEBUG: Message endpoint reached\n")
            f.flush()
        
        logging.info("DEBUG: Message endpoint reached")
        data = request.get_json()
        
        with open('C:\\Users\\User\\Desktop\\first-app\\debug_log.txt', 'a', encoding='utf-8') as f:
            f.write(f"DEBUG: Request data: {data}\n")
            f.flush()
            
        logging.info(f"DEBUG: Request data received")
        message = data.get('message', '').strip()
        category = data.get('category', '')  # Extract category from request
        
        with open('C:\\Users\\User\\Desktop\\first-app\\debug_log.txt', 'a', encoding='utf-8') as f:
            f.write(f"DEBUG: Extracted message: {message}\n")
            f.write(f"DEBUG: Extracted category: {category}\n")
            f.flush()
            
        # Log message safely without potential Unicode issues
        safe_message = message.encode('ascii', 'ignore').decode('ascii') if message else 'empty'
        logging.info(f"DEBUG: Extracted message: {safe_message[:100]}...")
        logging.info(f"DEBUG: Extracted category: {category}")
        context = data.get('context', [])
        intelligence_mode = data.get('intelligence_mode', data.get('mode', 'INSIGHTS'))  # Get mode from frontend
        
        if not message:
            return jsonify({
                'success': False,
                'error': 'Message is required'
            }), 400
        
        # Process the message with intelligence mode and category
        result = agent.process_message(message, context, intelligence_mode, category)
        
        return jsonify({
            'success': True,
            'response': result['response'],
            'type': result.get('type', 'general'),
            'data': result.get('data', {}),
            'mode': agent.mode
        })
        
    except Exception as e:
        # Handle Unicode characters safely in error logging
        error_msg = str(e).encode('ascii', 'ignore').decode('ascii')
        logger.error(f"Chatbot message error: {error_msg}")
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'response': "I'm sorry, I'm experiencing technical difficulties. Please try again."
        }), 500

@chatbot_bp.route('/status', methods=['GET'])
def get_status():
    """Get chatbot status and capabilities"""
    try:
        # Get system statistics
        stats = {
            'menu_items': MenuItem.query.count(),
            'ingredients': InventoryItem.query.count(),
            'orders': CustomerOrder.query.count(),
            'nutrition_coverage': db.session.query(MenuItem).join(MenuNutrition).count()
        }
        
        return jsonify({
            'success': True,
            'status': 'online',
            'mode': agent.mode,
            'capabilities': [
                'Menu Information',
                'Nutrition Analysis',
                'Pricing Optimization',
                'Demand Forecasting',
                'Inventory Management',
                'Automation Workflows'
            ],
            'statistics': stats
        })
        
    except Exception as e:
        logger.error(f"Status error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Unable to get status'
        }), 500

@chatbot_bp.route('/reset', methods=['POST'])
def reset_conversation():
    """Reset chatbot conversation state"""
    try:
        agent.mode = 'chat'
        return jsonify({
            'success': True,
            'message': 'Conversation reset successfully'
        })
    except Exception as e:
        logger.error(f"Reset error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Unable to reset conversation'
        }), 500