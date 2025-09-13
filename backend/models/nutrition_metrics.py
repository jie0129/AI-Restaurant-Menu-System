from datetime import datetime, timezone
from models.inventory_item import db

class NutritionMetrics(db.Model):
    __tablename__ = 'nutrition_metrics'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    
    # Tracking identifiers
    menu_item_id = db.Column(db.Integer, db.ForeignKey('menu_item.id'), nullable=True)
    session_id = db.Column(db.String(100), nullable=True)  # For tracking user sessions
    
    # USDA Integration Metrics
    usda_api_called = db.Column(db.Boolean, default=False)
    usda_data_found = db.Column(db.Boolean, default=False)
    # usda_match_confidence, usda_food_code, usda_response_time_ms removed (optimized)
    
    # Quality and Accuracy Metrics (optimized - removed serving size and cooking method columns)
    nutrition_completeness_score = db.Column(db.Float, nullable=True)  # 0.0 to 1.0
    # analysis_accuracy_rating removed (optimized)
    
    # Performance Metrics
    total_processing_time_ms = db.Column(db.Integer, nullable=True)
    gemini_api_response_time_ms = db.Column(db.Integer, nullable=True)
    analysis_success = db.Column(db.Boolean, default=True)
    # error_message removed (optimized)
    
    # Usage Tracking
    # analysis_type removed (optimized)
    # user_feedback_rating removed (optimized)
    
    # Timestamps
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    menu_item = db.relationship('MenuItem', backref=db.backref('nutrition_metrics', lazy=True))
    
    def to_dict(self):
        return {
            'id': self.id,
            'menu_item_id': self.menu_item_id,
            'session_id': self.session_id,
            
            # USDA metrics
            'usda_api_called': self.usda_api_called,
            'usda_data_found': self.usda_data_found,
            # usda_match_confidence, usda_food_code, usda_response_time_ms removed (optimized)
            
            # Quality metrics (optimized - removed serving size and cooking method fields)
            'nutrition_completeness_score': self.nutrition_completeness_score,
            # analysis_accuracy_rating removed (optimized)
            
            # Performance metrics
            'total_processing_time_ms': self.total_processing_time_ms,
            'gemini_api_response_time_ms': self.gemini_api_response_time_ms,
            'analysis_success': self.analysis_success,
            # error_message removed (optimized)
            
            # Usage tracking
            # analysis_type removed (optimized)
            # user_feedback_rating removed (optimized)
            
            'created_at': self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else None
        }
    
    @classmethod
    def get_accuracy_metrics(cls, days=30):
        """Get accuracy and quality metrics for the last N days"""
        from datetime import timedelta
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        metrics = cls.query.filter(cls.created_at >= cutoff_date).all()
        
        total_analyses = len(metrics)
        if total_analyses == 0:
            return {}
        
        # Calculate aggregate metrics (optimized - removed serving size and cooking method metrics)
        usda_usage_rate = sum(1 for m in metrics if m.usda_api_called) / total_analyses
        usda_success_rate = sum(1 for m in metrics if m.usda_data_found and m.usda_api_called) / max(1, sum(1 for m in metrics if m.usda_api_called))
        
        avg_completeness = sum(m.nutrition_completeness_score or 0 for m in metrics) / total_analyses
        avg_processing_time = sum(m.total_processing_time_ms or 0 for m in metrics) / total_analyses
        
        return {
            'total_analyses': total_analyses,
            'usda_usage_rate': round(usda_usage_rate * 100, 2),
            'usda_success_rate': round(usda_success_rate * 100, 2),
            'avg_completeness_score': round(avg_completeness, 2),
            'avg_processing_time_ms': round(avg_processing_time, 2),
            'success_rate': round(sum(1 for m in metrics if m.analysis_success) / total_analyses * 100, 2)
        }