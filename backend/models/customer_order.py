from datetime import datetime, timezone
from models import db

class CustomerOrder(db.Model):
    __tablename__ = 'customer_orders'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    order_number = db.Column(db.String(50), nullable=False, unique=True)
    menu_item_id = db.Column(db.Integer, db.ForeignKey('menu_item.id'), nullable=False)
    quantity_ordered = db.Column(db.Integer, nullable=False, default=1)
    unit_price = db.Column(db.Float, nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    order_date = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    customer_name = db.Column(db.String(100), nullable=True)
    customer_phone = db.Column(db.String(20), nullable=True)
    order_status = db.Column(db.String(20), nullable=False, default='pending')  # pending, confirmed, preparing, completed, cancelled
    restaurant_id = db.Column(db.String(50), nullable=True)  # For multi-restaurant support
    day_of_week = db.Column(db.String(10), nullable=True)
    meal_type = db.Column(db.String(20), nullable=True)  # breakfast, lunch, dinner, snack
    weather_condition = db.Column(db.String(20), nullable=True)
    has_promotion = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationship to menu item
    menu_item = db.relationship('MenuItem', backref='orders', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'order_number': self.order_number,
            'menu_item_id': self.menu_item_id,
            'menu_item_name': self.menu_item.menu_item_name if self.menu_item else None,
            'quantity_ordered': self.quantity_ordered,
            'unit_price': self.unit_price,
            'total_price': self.total_price,
            'order_date': self.order_date.strftime("%Y-%m-%d %H:%M:%S"),
            'customer_name': self.customer_name,
            'customer_phone': self.customer_phone,
            'order_status': self.order_status,
            'restaurant_id': self.restaurant_id,
            'day_of_week': self.day_of_week,
            'meal_type': self.meal_type,
            'weather_condition': self.weather_condition,
            'has_promotion': self.has_promotion,
            'created_at': self.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            'updated_at': self.updated_at.strftime("%Y-%m-%d %H:%M:%S")
        }

    def get_ingredient_usage(self):
        """Get ingredient usage for this order based on recipe."""
        if not self.menu_item:
            return []
        
        from models.recipe import Recipe
        from models.ingredient import Ingredient
        
        recipes = Recipe.query.filter_by(dish_id=self.menu_item_id).all()
        ingredient_usage = []
        
        for recipe in recipes:
            ingredient = Ingredient.query.get(recipe.ingredient_id)
            if ingredient:
                usage_amount = recipe.quantity_per_unit * self.quantity_ordered
                ingredient_usage.append({
                    'ingredient_id': ingredient.id,
                    'ingredient_name': ingredient.name,
                    'quantity_used': usage_amount,
                    'unit': ingredient.unit,
                    'category': ingredient.category
                })
        
        return ingredient_usage

    @staticmethod
    def get_daily_ingredient_usage(date=None):
        """Get aggregated ingredient usage for a specific date."""
        if date is None:
            date = datetime.now(timezone.utc).date()
        
        from models.recipe import Recipe
        from models.ingredient import Ingredient
        from sqlalchemy import func
        
        # Get all orders for the specified date
        orders = CustomerOrder.query.filter(
            func.date(CustomerOrder.order_date) == date,
            CustomerOrder.order_status.in_(['confirmed', 'preparing', 'completed'])
        ).all()
        
        ingredient_usage = {}
        
        for order in orders:
            usage_data = order.get_ingredient_usage()
            for usage in usage_data:
                ingredient_id = usage['ingredient_id']
                if ingredient_id not in ingredient_usage:
                    ingredient_usage[ingredient_id] = {
                        'ingredient_name': usage['ingredient_name'],
                        'total_quantity': 0,
                        'unit': usage['unit'],
                        'category': usage['category']
                    }
                ingredient_usage[ingredient_id]['total_quantity'] += usage['quantity_used']
        
        return list(ingredient_usage.values())

    @staticmethod
    def get_ingredient_category_distribution(start_date=None, end_date=None, unit_filter=None):
        """Get ingredient usage distribution by category with optional unit filtering."""
        from models.recipe import Recipe
        from models.ingredient import Ingredient
        from sqlalchemy import func
        
        query = CustomerOrder.query.filter(
            CustomerOrder.order_status.in_(['confirmed', 'preparing', 'completed'])
        )
        
        if start_date:
            query = query.filter(func.date(CustomerOrder.order_date) >= start_date)
        if end_date:
            query = query.filter(func.date(CustomerOrder.order_date) <= end_date)
        
        orders = query.all()
        category_usage = {}
        category_units = {}  # Track units for each category
        
        for order in orders:
            usage_data = order.get_ingredient_usage()
            for usage in usage_data:
                # Apply unit filter if specified
                if unit_filter and unit_filter != 'all' and usage['unit'] != unit_filter:
                    continue
                    
                category = usage['category']
                unit = usage['unit']
                
                if category not in category_usage:
                    category_usage[category] = 0
                    category_units[category] = set()
                
                category_usage[category] += usage['quantity_used']
                category_units[category].add(unit)
        
        # Convert sets to lists for JSON serialization
        for category in category_units:
            category_units[category] = list(category_units[category])
        
        return category_usage, category_units