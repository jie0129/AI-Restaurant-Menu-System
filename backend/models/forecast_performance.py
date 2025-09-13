from models.inventory_item import db
from datetime import datetime

class ForecastPerformance(db.Model):
    __tablename__ = 'forecast_performance'
    
    id = db.Column(db.Integer, primary_key=True)
    model_version = db.Column(db.String(100), nullable=False)
    forecast_type = db.Column(db.String(50), nullable=False)  # 'menu_item' or 'ingredient'
    item_id = db.Column(db.Integer, nullable=True)  # Specific item ID or NULL for overall performance
    evaluation_date = db.Column(db.Date, nullable=False)
    mae = db.Column(db.Float, nullable=True)  # Mean Absolute Error
    rmse = db.Column(db.Float, nullable=True)  # Root Mean Square Error
    mape = db.Column(db.Float, nullable=True)  # Mean Absolute Percentage Error
    r2_score = db.Column(db.Float, nullable=True)  # R-squared score

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Create indexes for efficient queries
    __table_args__ = (
        db.Index('idx_forecast_performance_model', 'model_version'),
        db.Index('idx_forecast_performance_type', 'forecast_type'),
        db.Index('idx_forecast_performance_date', 'evaluation_date'),
        db.Index('idx_forecast_performance_item', 'forecast_type', 'item_id'),
    )
    
    def __repr__(self):
        return f'<ForecastPerformance {self.model_version} - {self.forecast_type} on {self.evaluation_date}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'model_version': self.model_version,
            'forecast_type': self.forecast_type,
            'item_id': self.item_id,
            'evaluation_date': self.evaluation_date.isoformat() if self.evaluation_date else None,
            'mae': self.mae,
            'rmse': self.rmse,
            'mape': self.mape,
            'r2_score': self.r2_score,

            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }