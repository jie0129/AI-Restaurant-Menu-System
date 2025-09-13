from datetime import datetime, timezone
from models.inventory_item import db

class MenuNutrition(db.Model):
    __tablename__ = 'menu_nutrition'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    menu_item_id = db.Column(db.Integer, db.ForeignKey('menu_item.id'), nullable=False)
    calories = db.Column(db.Float, nullable=True)
    protein = db.Column(db.Float, nullable=True)
    carbohydrates = db.Column(db.Float, nullable=True)
    fat = db.Column(db.Float, nullable=True)
    fiber = db.Column(db.Float, nullable=True)
    sugar = db.Column(db.Float, nullable=True)
    sodium = db.Column(db.Float, nullable=True)
    
    # Vitamins and minerals as comma-separated text
    vitamins = db.Column(db.Text, nullable=True)  # Comma-separated list of vitamins
    minerals = db.Column(db.Text, nullable=True)  # Comma-separated list of minerals
    
    allergens = db.Column(db.Text, nullable=True)  # Comma-separated list of allergens
    is_vegetarian = db.Column(db.Boolean, nullable=True, default=False)
    is_vegan = db.Column(db.Boolean, nullable=True, default=False)
    is_gluten_free = db.Column(db.Boolean, nullable=True, default=False)
    analysis_text = db.Column(db.Text, nullable=True)  # Full text of the AI analysis
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationship with MenuItem
    menu_item = db.relationship('MenuItem', backref=db.backref('nutrition', lazy=True, cascade='all, delete-orphan'))

    def to_dict(self):
        return {
            'id': self.id,
            'menu_item_id': self.menu_item_id,
            'calories': self.calories,
            'protein': self.protein,
            'carbohydrates': self.carbohydrates,
            'fat': self.fat,
            'fiber': self.fiber,
            'sugar': self.sugar,
            'sodium': self.sodium,
            'vitamins': self.vitamins,
            'minerals': self.minerals,
            'allergens': self.allergens,
            'is_vegetarian': self.is_vegetarian,
            'is_vegan': self.is_vegan,
            'is_gluten_free': self.is_gluten_free,
            'analysis_text': self.analysis_text,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

