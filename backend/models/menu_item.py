from datetime import datetime, timezone
from models.inventory_item import db

class MenuItem(db.Model):
    __tablename__ = 'menu_item'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    menu_item_name = db.Column(db.String(100), nullable=False)
    typical_ingredient_cost = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    cuisine_type = db.Column(db.String(50), nullable=False)
    key_ingredients_tags = db.Column(db.Text, nullable=False)

    menu_price = db.Column(db.Float, nullable=True)  # Price can be null, will be updated from PricingAdjustmentPage
    serving_size = db.Column(db.String(50), nullable=True, default='1 serving')  # e.g., '100g', '1 cup', '1 piece'
    cooking_method = db.Column(db.String(50), nullable=True, default='as prepared')  # e.g., 'raw', 'boiled', 'fried', 'grilled'
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            'id': self.id,
            'menu_item_name': self.menu_item_name,
            'typical_ingredient_cost': self.typical_ingredient_cost,
            'category': self.category,
            'cuisine_type': self.cuisine_type,
            'key_ingredients_tags': self.key_ingredients_tags,

            'menu_price': self.menu_price,  # Include the new menu_price field
            'serving_size': self.serving_size,
            'cooking_method': self.cooking_method,
            'created_at': self.created_at.strftime("%Y-%m-%d %H:%M"),
            'updated_at': self.updated_at.strftime("%Y-%m-%d %H:%M")
        }