from datetime import datetime
from models import db

class StockAlert(db.Model):
    __tablename__ = 'stock_alerts'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    item_id = db.Column(db.Integer, nullable=False)  # ingredient_id or menu_item_id
    item_type = db.Column(db.String(20), nullable=False)  # 'ingredient' or 'menu_item'
    item_name = db.Column(db.String(100), nullable=False)
    alert_type = db.Column(db.String(30), nullable=False)  # 'low_stock' or 'predicted_stockout'
    current_quantity = db.Column(db.Numeric(10, 2), nullable=True)
    reorder_point = db.Column(db.Numeric(10, 2), nullable=True)
    predicted_demand = db.Column(db.Numeric(10, 2), nullable=True)
    forecast_date = db.Column(db.Date, nullable=True)  # For predicted stockout alerts

    alert_message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'item_id': self.item_id,
            'item_type': self.item_type,
            'item_name': self.item_name,
            'alert_type': self.alert_type,
            'current_quantity': float(self.current_quantity) if self.current_quantity is not None else None,
            'reorder_point': float(self.reorder_point) if self.reorder_point is not None else None,
            'predicted_demand': float(self.predicted_demand) if self.predicted_demand is not None else None,
            'forecast_date': self.forecast_date.strftime('%Y-%m-%d') if self.forecast_date else None,

            'alert_message': self.alert_message,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }