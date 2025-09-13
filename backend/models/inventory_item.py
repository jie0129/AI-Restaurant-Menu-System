from datetime import datetime
from models import db

class InventoryItem(db.Model):
    __tablename__ = 'inventory'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    ingredient_id = db.Column(db.Integer, db.ForeignKey('ingredients.id'), nullable=False)
    quantity = db.Column(db.Numeric(10, 4), default=0)
    last_updated = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Use string for relationship to avoid circular import
    ingredient = db.relationship('Ingredient', backref=db.backref('inventory_items', lazy=True, cascade='all, delete-orphan'))

    def to_dict(self):
        return {
            'id': self.id,
            'ingredient_id': self.ingredient_id,
            'quantity': float(self.quantity),
            'last_updated': self.last_updated.isoformat() if self.last_updated else None
        }

#Cannot add new item if the item name is same alphabet no matter lower case or upper case