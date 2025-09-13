from datetime import datetime
from models import db

class IngredientUsage(db.Model):
    __tablename__ = 'ingredient_usage'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    ingredient_id = db.Column(db.Integer, db.ForeignKey('ingredients.id'), nullable=False)
    menu_item_id = db.Column(db.Integer, db.ForeignKey('menu_item.id'), nullable=False)
    quantity_used = db.Column(db.Numeric(15, 6), nullable=False)
    unit = db.Column(db.String(20), nullable=True)  # Unit for the quantity used
    used_on = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'ingredient_id': self.ingredient_id,
            'menu_item_id': self.menu_item_id,
            'quantity_used': float(self.quantity_used),
            'unit': self.unit,
            'used_on': self.used_on.isoformat() if self.used_on else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }