from datetime import datetime, timezone
from models.inventory_item import db

class MenuItemImage(db.Model):
    __tablename__ = 'menu_item_images'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    menu_item_id = db.Column(db.Integer, db.ForeignKey('menu_item.id'), nullable=False)
    image_path = db.Column(db.Text, nullable=False)
    image_type = db.Column(db.String(20), nullable=False, default='uploaded')  # 'uploaded' or 'ai_generated'
    is_primary = db.Column(db.Boolean, nullable=False, default=True)  # Primary image for the menu item
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationship with MenuItem
    menu_item = db.relationship('MenuItem', backref=db.backref('images', lazy=True, cascade='all, delete-orphan'))

    def to_dict(self):
        return {
            'id': self.id,
            'menu_item_id': self.menu_item_id,
            'image_path': self.image_path,
            'image_type': self.image_type,
            'is_primary': self.is_primary,
            'created_at': self.created_at.strftime("%Y-%m-%d %H:%M"),
            'updated_at': self.updated_at.strftime("%Y-%m-%d %H:%M")
        }
