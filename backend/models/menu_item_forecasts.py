from models.inventory_item import db
from datetime import datetime

class MenuItemForecast(db.Model):
    __tablename__ = 'menu_item_forecasts'
    
    id = db.Column(db.Integer, primary_key=True)
    model_version = db.Column(db.String(100), nullable=False)
    menu_item_id = db.Column(db.Integer, nullable=False)
    date = db.Column(db.Date, nullable=False)
    predicted_quantity = db.Column(db.Float, nullable=False)
    lower_bound = db.Column(db.Float, nullable=True)  # Confidence interval lower bound
    upper_bound = db.Column(db.Float, nullable=True)  # Confidence interval upper bound
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Create indexes for efficient queries
    __table_args__ = (
        db.Index('idx_menu_item_forecasts_item', 'menu_item_id'),
        db.Index('idx_menu_item_forecasts_date', 'date'),
        db.Index('idx_menu_item_forecasts_model', 'model_version'),
        db.Index('idx_menu_item_forecasts_item_date', 'menu_item_id', 'date'),
        # Unique constraint to prevent duplicate forecasts for same item/date/model
        db.UniqueConstraint('model_version', 'menu_item_id', 'date', name='uq_menu_item_forecast'),
    )
    
    def __repr__(self):
        return f'<MenuItemForecast {self.menu_item_id} on {self.date} - {self.predicted_quantity}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'model_version': self.model_version,
            'menu_item_id': self.menu_item_id,
            'date': self.date.isoformat() if self.date else None,
            'predicted_quantity': self.predicted_quantity,
            'lower_bound': self.lower_bound,
            'upper_bound': self.upper_bound,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }