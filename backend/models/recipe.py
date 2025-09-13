from models import db

class Recipe(db.Model):
    __tablename__ = 'recipes'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    dish_id = db.Column(db.Integer, db.ForeignKey('menu_item.id'), nullable=False)
    ingredient_id = db.Column(db.Integer, db.ForeignKey('ingredients.id'), nullable=False)
    quantity_per_unit = db.Column(db.Float, nullable=False)
    recipe_unit = db.Column(db.String(20), nullable=True)  # Unit used in recipe (e.g., 'tsp', 'cup', 'piece')

    def to_dict(self):
        return {
            'id': self.id,
            'dish_id': self.dish_id,
            'ingredient_id': self.ingredient_id,
            'quantity_per_unit': self.quantity_per_unit,
            'recipe_unit': self.recipe_unit
        }