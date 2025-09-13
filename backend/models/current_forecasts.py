from models.inventory_item import db
from datetime import datetime

class CurrentForecast(db.Model):
    __tablename__ = 'current_forecasts'
    
    id = db.Column(db.Integer, primary_key=True)
    item_type = db.Column(db.String(50), nullable=False)  # 'menu_item' or 'ingredient'
    item_id = db.Column(db.Integer, nullable=False)
    item_name = db.Column(db.String(255), nullable=False)
    forecast_date = db.Column(db.Date, nullable=False)
    predicted_quantity = db.Column(db.Float, nullable=False)
    confidence_lower = db.Column(db.Float, nullable=True)
    confidence_upper = db.Column(db.Float, nullable=True)
    model_version = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Create composite index for efficient queries
    __table_args__ = (
        db.Index('idx_current_forecasts_item', 'item_type', 'item_id'),
        db.Index('idx_current_forecasts_date', 'forecast_date'),
    )
    
    def __repr__(self):
        return f'<CurrentForecast {self.item_type}:{self.item_id} on {self.forecast_date}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'item_type': self.item_type,
            'item_id': self.item_id,
            'item_name': self.item_name,
            'forecast_date': self.forecast_date.isoformat() if self.forecast_date else None,
            'predicted_quantity': self.predicted_quantity,
            'confidence_lower': self.confidence_lower,
            'confidence_upper': self.confidence_upper,
            'model_version': self.model_version,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }