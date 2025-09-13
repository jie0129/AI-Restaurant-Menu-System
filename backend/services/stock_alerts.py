from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
from models.stock_alert import StockAlert
from models.ingredient import Ingredient
from models.inventory_item import InventoryItem
from models import db
from config import Config
import math

def custom_round(value):
    """Custom rounding function: round up for .54 and above, round down for .08 and below."""
    if value is None:
        return None
    
    decimal_part = value - math.floor(value)
    
    # Round up for decimals >= 0.5
    if decimal_part >= 0.5:
        return math.ceil(value)
    # Round down for decimals < 0.5
    else:
        return math.floor(value)

def check_low_stock_alerts():
    """Check for ingredients that have fallen below their reorder point."""
    alerts_created = []
    
    try:
        # Query ingredients with their current inventory levels
        results = db.session.query(
            InventoryItem.id,
            Ingredient.id.label('ingredient_id'),
            Ingredient.name,
            Ingredient.min_threshold,
            InventoryItem.quantity
        ).join(Ingredient, InventoryItem.ingredient_id == Ingredient.id).all()
        
        for row in results:
            current_quantity = float(row.quantity)
            raw_reorder_point = float(row.min_threshold) if row.min_threshold else 0
            reorder_point = custom_round(raw_reorder_point)
            
            # Check if current stock is below reorder point
            if current_quantity <= reorder_point:
                # Check if combined alert already exists for this ingredient
                combined_alert = StockAlert.query.filter_by(
                    item_id=row.ingredient_id,
                    item_type='ingredient',
                    alert_type='low_stock_and_predicted_stockout'
                ).first()
                
                # Skip if combined alert exists
                if combined_alert:
                    continue
                
                # Check if alert already exists
                existing_alert = StockAlert.query.filter_by(
                    item_id=row.ingredient_id,
                    item_type='ingredient',
                    alert_type='low_stock'
                ).first()
                
                if existing_alert:
                    # Update existing alert with current values
                    existing_alert.current_quantity = current_quantity
                    existing_alert.reorder_point = reorder_point
                    existing_alert.alert_message = f"Low stock alert: {row.name} has {current_quantity} {row.name} remaining, which is at or below the reorder point of {reorder_point}."
                    alerts_created.append(existing_alert.to_dict())
                else:
                    # Create new alert
                    alert_message = f"Low stock alert: {row.name} has {current_quantity} {row.name} remaining, which is at or below the reorder point of {reorder_point}."
                    
                    new_alert = StockAlert(
                        item_id=row.ingredient_id,
                        item_type='ingredient',
                        item_name=row.name,
                        alert_type='low_stock',
                        current_quantity=current_quantity,
                        reorder_point=reorder_point,
                        alert_message=alert_message
                    )
                    
                    db.session.add(new_alert)
                    alerts_created.append(new_alert.to_dict())
        
        db.session.commit()
        return {'success': True, 'alerts_created': len(alerts_created), 'alerts': alerts_created}
        
    except Exception as e:
        db.session.rollback()
        return {'success': False, 'error': str(e)}

def check_predicted_stockout_alerts(forecast_days=7):
    """Check for predicted stockouts based on forecast data.
    Only creates alerts for ingredients with meaningful demand predictions.
    """
    alerts_created = []
    
    try:
        engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
        
        # Get current date and forecast end date
        current_date = datetime.now().date()
        forecast_end_date = current_date + timedelta(days=forecast_days)
        
        # Define ingredients that should have predicted stockout alerts
        # Only these ingredients have meaningful demand predictions
        meaningful_forecast_ingredients = [
            'Milk', 'Coconut Milk',  # Original ingredients
            'Beef patty', 'Cheese', 'Lettuce', 'Tomato', 'Bun',  # Cheeseburger ingredients
            'Onions', 'Ketchup', 'Mustard', 'Pickles'  # Additional burger ingredients
        ]  # Add more as needed
        
        # Query ingredient forecasts for the next forecast_days
        # Only for ingredients with meaningful predictions
        with engine.connect() as conn:
            forecast_query = text("""
                SELECT 
                    inf.ingredient_id,
                    i.name as ingredient_name,
                    i.min_threshold,
                    SUM(inf.predicted_quantity) as total_predicted_demand,
                    inv.quantity as current_quantity
                FROM ingredient_forecasts inf
                JOIN ingredients i ON inf.ingredient_id = i.id
                LEFT JOIN inventory inv ON inv.ingredient_id = i.id
                WHERE inf.date BETWEEN :start_date AND :end_date
                    AND i.name IN :ingredient_names
                GROUP BY inf.ingredient_id, i.name, i.min_threshold, inv.quantity
            """)
            
            result = conn.execute(forecast_query, {
                'start_date': current_date,
                'end_date': forecast_end_date,
                'ingredient_names': tuple(meaningful_forecast_ingredients)
            })
            
            forecast_data = result.fetchall()
            
            for row in forecast_data:
                ingredient_id = row[0]
                ingredient_name = row[1]
                min_threshold = float(row[2]) if row[2] else 0
                predicted_demand = float(row[3]) if row[3] else 0
                current_quantity = float(row[4]) if row[4] else 0
                
                # New reorder point calculation: max(predicted_demand, min_threshold) - current_stock
                effective_threshold = max(predicted_demand, min_threshold)
                raw_reorder_point = effective_threshold - current_quantity
                reorder_point = custom_round(raw_reorder_point)
                
                # Check if reorder point is positive (indicating need for restocking)
                if reorder_point > 0:
                    # Check if combined alert already exists for this ingredient
                    combined_alert = StockAlert.query.filter_by(
                        item_id=ingredient_id,
                        item_type='ingredient',
                        alert_type='low_stock_and_predicted_stockout'
                    ).first()
                    
                    # Skip if combined alert exists
                    if combined_alert:
                        continue
                    
                    # Check if alert already exists
                    existing_alert = StockAlert.query.filter_by(
                        item_id=ingredient_id,
                        item_type='ingredient',
                        alert_type='predicted_stockout'
                    ).first()
                    
                    if existing_alert:
                        # Update existing alert with current values
                        existing_alert.current_quantity = current_quantity
                        existing_alert.reorder_point = reorder_point
                        existing_alert.predicted_demand = math.ceil(predicted_demand)
                        existing_alert.forecast_date = forecast_end_date
                        existing_alert.alert_message = f"Predicted stockout alert: {ingredient_name} needs restocking. Predicted demand: {math.ceil(predicted_demand)}, Min threshold: {min_threshold:.2f}, Current stock: {current_quantity:.2f}. Reorder point: {reorder_point}."
                        alerts_created.append(existing_alert.to_dict())
                    else:
                        # Create new alert
                        alert_message = f"Predicted stockout alert: {ingredient_name} needs restocking. Predicted demand: {math.ceil(predicted_demand)}, Min threshold: {min_threshold:.2f}, Current stock: {current_quantity:.2f}. Reorder point: {reorder_point}."
                        
                        new_alert = StockAlert(
                            item_id=ingredient_id,
                            item_type='ingredient',
                            item_name=ingredient_name,
                            alert_type='predicted_stockout',
                            current_quantity=current_quantity,
                            reorder_point=reorder_point,
                            predicted_demand=math.ceil(predicted_demand),
                            forecast_date=forecast_end_date,
                            alert_message=alert_message
                        )
                        
                        db.session.add(new_alert)
                        alerts_created.append(new_alert.to_dict())
        
        db.session.commit()
        return {'success': True, 'alerts_created': len(alerts_created), 'alerts': alerts_created}
        
    except Exception as e:
        db.session.rollback()
        return {'success': False, 'error': str(e)}

def get_all_alerts():
    """Get all stock alerts."""
    try:
        alerts = StockAlert.query.order_by(StockAlert.created_at.desc()).all()
        return {'success': True, 'alerts': [alert.to_dict() for alert in alerts]}
    except Exception as e:
        return {'success': False, 'error': str(e)}

def resolve_alert(alert_id, restock_quantity=None):
    """Completely remove an alert and optionally update inventory. 
    Also checks all alerts for the same item and removes them if quantity is above reorder point."""
    try:
        alert = StockAlert.query.get_or_404(alert_id)
        item_id = alert.item_id
        item_type = alert.item_type
        
        # If restock quantity is provided, update the inventory
        if restock_quantity is not None and restock_quantity > 0:
            inventory_item = InventoryItem.query.filter_by(ingredient_id=alert.item_id).first()
            if inventory_item:
                inventory_item.quantity = float(inventory_item.quantity) + float(restock_quantity)
                db.session.add(inventory_item)
        
        # Get current inventory and ingredient info after potential restock
        inventory_item = InventoryItem.query.filter_by(ingredient_id=item_id).first()
        ingredient = Ingredient.query.get(item_id)
        
        if inventory_item and ingredient:
            current_quantity = float(inventory_item.quantity)
            min_threshold = float(ingredient.min_threshold) if ingredient.min_threshold else 0
            reorder_point = custom_round(min_threshold)
            
            # If current quantity is above reorder point, remove ALL alerts for this item
            if current_quantity > reorder_point:
                alerts_to_remove = StockAlert.query.filter_by(
                    item_id=item_id,
                    item_type=item_type
                ).all()
                
                removed_count = len(alerts_to_remove)
                for alert_to_remove in alerts_to_remove:
                    db.session.delete(alert_to_remove)
                    
                db.session.commit()
                
                message = f'Resolved and removed {removed_count} alert(s) for {ingredient.name}'
                if restock_quantity is not None and restock_quantity > 0:
                    message += f' after restocking {restock_quantity} units'
                    
                return {'success': True, 'message': message, 'removed_count': removed_count}
            else:
                # If still below reorder point, just remove the specific alert
                db.session.delete(alert)
                db.session.commit()
                
                message = 'Alert resolved and removed (quantity still below reorder point)'
                if restock_quantity is not None and restock_quantity > 0:
                    message += f' after restocking {restock_quantity} units'
                    
                return {'success': True, 'message': message, 'removed_count': 1}
        else:
            # Fallback: just remove the specific alert if we can't get inventory info
            db.session.delete(alert)
            db.session.commit()
            
            message = 'Alert resolved and removed successfully'
            if restock_quantity is not None and restock_quantity > 0:
                message += f' and inventory updated with {restock_quantity} units'
                
            return {'success': True, 'message': message, 'removed_count': 1}
    except Exception as e:
        db.session.rollback()
        return {'success': False, 'error': str(e)}

def check_combined_alerts():
    """Check for ingredients that have both low stock and predicted stockout conditions."""
    alerts_created = []
    
    try:
        engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
        
        # Get current date and forecast end date
        current_date = datetime.now().date()
        forecast_end_date = current_date + timedelta(days=7)
        
        # Query to find ingredients with both low stock and predicted stockout conditions
        with engine.connect() as conn:
            combined_query = text("""
                SELECT 
                    i.id as ingredient_id,
                    i.name as ingredient_name,
                    i.min_threshold,
                    inv.quantity as current_quantity,
                    COALESCE(SUM(inf.predicted_quantity), 0) as total_predicted_demand
                FROM ingredients i
                LEFT JOIN inventory inv ON inv.ingredient_id = i.id
                LEFT JOIN ingredient_forecasts inf ON inf.ingredient_id = i.id 
                    AND inf.date BETWEEN :start_date AND :end_date
                GROUP BY i.id, i.name, i.min_threshold, inv.quantity
                HAVING (inv.quantity <= i.min_threshold) 
                    AND (COALESCE(SUM(inf.predicted_quantity), 0) > inv.quantity)
            """)
            
            result = conn.execute(combined_query, {
                'start_date': current_date,
                'end_date': forecast_end_date
            })
            
            combined_data = result.fetchall()
            
            for row in combined_data:
                ingredient_id = row[0]
                ingredient_name = row[1]
                min_threshold = float(row[2]) if row[2] else 0
                current_quantity = float(row[3]) if row[3] else 0
                predicted_demand = float(row[4]) if row[4] else 0
                
                # For combined alerts: reorder_point = predicted_demand - current_stock
                raw_reorder_point = predicted_demand - current_quantity
                reorder_point = custom_round(raw_reorder_point)
                
                # Check if combined alert already exists
                existing_alert = StockAlert.query.filter_by(
                    item_id=ingredient_id,
                    item_type='ingredient',
                    alert_type='low_stock_and_predicted_stockout'
                ).first()
                
                if existing_alert:
                    # Update existing alert with new calculation
                    existing_alert.current_quantity = current_quantity
                    existing_alert.reorder_point = reorder_point
                    existing_alert.predicted_demand = math.ceil(predicted_demand)
                    existing_alert.forecast_date = forecast_end_date
                    existing_alert.alert_message = f"Combined alert: {ingredient_name} has both low stock ({current_quantity} <= {min_threshold}) and predicted stockout (demand: {math.ceil(predicted_demand)}). Reorder point: {reorder_point}."
                    alerts_created.append(existing_alert.to_dict())
                else:
                    # Delete individual alerts for this ingredient
                    individual_alerts = StockAlert.query.filter_by(
                        item_id=ingredient_id,
                        item_type='ingredient'
                    ).filter(
                        StockAlert.alert_type.in_(['low_stock', 'predicted_stockout'])
                    ).all()
                    
                    for alert in individual_alerts:
                        db.session.delete(alert)
                    
                    alert_message = f"Combined alert: {ingredient_name} has both low stock ({current_quantity} <= {min_threshold}) and predicted stockout (demand: {math.ceil(predicted_demand)}). Reorder point: {reorder_point}."
                    
                    new_alert = StockAlert(
                        item_id=ingredient_id,
                        item_type='ingredient',
                        item_name=ingredient_name,
                        alert_type='low_stock_and_predicted_stockout',
                        current_quantity=current_quantity,
                        reorder_point=reorder_point,
                        predicted_demand=math.ceil(predicted_demand),
                        forecast_date=forecast_end_date,
                        alert_message=alert_message
                    )
                    
                    db.session.add(new_alert)
                    alerts_created.append(new_alert.to_dict())
        
        db.session.commit()
        return {'success': True, 'alerts_created': len(alerts_created), 'alerts': alerts_created}
        
    except Exception as e:
        db.session.rollback()
        return {'success': False, 'error': str(e)}

def cleanup_resolved_conditions():
    """Remove alerts that no longer meet alert conditions due to inventory changes."""
    alerts_removed = 0
    
    try:
        # Get all alerts
        all_alerts = StockAlert.query.all()
        
        for alert in all_alerts:
            should_remove = False
            
            if alert.item_type == 'ingredient':
                # Get current inventory for this ingredient
                inventory_item = InventoryItem.query.filter_by(ingredient_id=alert.item_id).first()
                ingredient = Ingredient.query.get(alert.item_id)
                
                if inventory_item and ingredient:
                    current_quantity = float(inventory_item.quantity)
                    reorder_point = custom_round(float(ingredient.min_threshold)) if ingredient.min_threshold else 0
                    
                    # Check if low stock condition is resolved
                    if alert.alert_type in ['low_stock', 'low_stock_and_predicted_stockout']:
                        if current_quantity > reorder_point:
                            # For combined alerts, check if predicted stockout still applies
                            if alert.alert_type == 'low_stock_and_predicted_stockout':
                                # Check predicted demand (simplified check)
                                if not alert.predicted_demand or current_quantity > (reorder_point + float(alert.predicted_demand or 0)):
                                    should_remove = True
                            else:
                                should_remove = True
            
            if should_remove:
                db.session.delete(alert)
                alerts_removed += 1
        
        db.session.commit()
        return {
            'success': True, 
            'alerts_removed': alerts_removed,
            'message': f'Cleaned up {alerts_removed} resolved alerts'
        }
        
    except Exception as e:
        db.session.rollback()
        return {'success': False, 'error': str(e), 'alerts_removed': 0}

def run_all_alert_checks():
    """Run comprehensive inventory checks: low stock, predicted stockout, and combined alerts."""
    try:
        # Step 1: Check for combined alerts (both low stock and predicted stockout)
        combined_result = check_combined_alerts()
        
        # Step 2: Check for individual low stock alerts (excluding items with combined alerts)
        low_stock_result = check_low_stock_alerts()
        
        # Step 3: Check for predicted stockout alerts (excluding items with combined alerts)
        predicted_stockout_result = check_predicted_stockout_alerts()
        
        # Step 4: Clean up any resolved alerts that no longer meet alert conditions
        cleanup_result = cleanup_resolved_conditions()
        
        # Calculate total alerts created
        total_alerts_created = (
            combined_result.get('alerts_created', 0) +
            low_stock_result.get('alerts_created', 0) +
            predicted_stockout_result.get('alerts_created', 0)
        )
        
        return {
            'success': True,
            'total_alerts_created': total_alerts_created,
            'low_stock': low_stock_result,
            'predicted_stockout': predicted_stockout_result,
            'combined': combined_result,
            'cleanup': cleanup_result,
            'message': f'Comprehensive inventory check completed. {total_alerts_created} new alerts created.'
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': f'Comprehensive alert check failed: {str(e)}',
            'low_stock': {'success': False, 'error': str(e)},
            'predicted_stockout': {'success': False, 'error': str(e)},
            'combined': {'success': False, 'error': str(e)}
        }