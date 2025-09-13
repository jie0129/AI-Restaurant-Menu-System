from models.inventory_item import db, InventoryItem
from config import Config
from flask import current_app
from services.stock_alerts import run_all_alert_checks
import logging

def check_low_stock():
    """Legacy function for basic low stock checking."""
    low_stock_items = InventoryItem.query.filter(
        InventoryItem.quantity < Config.LOW_STOCK_THRESHOLD
    ).all()
    return low_stock_items  # Return the items so they can be used elsewhere

def check_stock_alerts_job():
    """Comprehensive scheduled job to check for all types of stock alerts."""
    try:
        result = run_all_alert_checks()
        
        # Log the results
        low_stock_alerts = result.get('low_stock', {}).get('alerts_created', 0)
        predicted_alerts = result.get('predicted_stockout', {}).get('alerts_created', 0)
        
        if low_stock_alerts > 0 or predicted_alerts > 0:
            logging.info(f"Stock alerts check completed: {low_stock_alerts} low stock alerts, {predicted_alerts} predicted stockout alerts created")
        else:
            logging.debug("Stock alerts check completed: No new alerts")
            
        return result
    except Exception as e:
        logging.error(f"Error in stock alerts check: {str(e)}")
        return {'error': str(e)}

def check_low_stock_with_context():
    """Updated function that now runs comprehensive stock alerts check."""
    return check_stock_alerts_job()
