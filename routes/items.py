"""
Routes for collection items management.
"""

from flask import Blueprint, jsonify, request
from typing import Dict, Any
import logging
from core.database import db_manager
from core.models import CollectionItem
from services.email_service import email_service
from core.utils import to_numeric_or_none

logger = logging.getLogger(__name__)

items_bp = Blueprint('items', __name__, url_prefix='/api/items')


@items_bp.route('', methods=['GET'])
def get_items():
    """Get all collection items"""
    try:
        items = db_manager.get_all_items()
        return jsonify({
            'success': True,
            'items': items,
            'count': len(items)
        })
    except Exception as e:
        logger.error(f"Error fetching items: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@items_bp.route('', methods=['POST'])
def create_item():
    """Create a new collection item"""
    try:
        data = request.json
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        # Validate required fields
        if 'name' not in data or 'category' not in data:
            return jsonify({
                'success': False,
                'error': 'Name and category are required'
            }), 400
        
        # Set default status if not provided
        if 'status' not in data:
            data['status'] = 'available'
        
        # Clean numeric fields
        numeric_fields = [
            'current_value', 'sold_price', 'acquisition_price',
            'current_offer', 'commission_rate', 'surface_m2',
            'rental_income_chf', 'stock_quantity', 'stock_purchase_price',
            'current_price'
        ]
        
        for field in numeric_fields:
            if field in data:
                data[field] = to_numeric_or_none(data[field])
        
        # Create item in database
        new_item = db_manager.create_item(data)
        
        if new_item:
            # Send email notification if enabled
            email_service.send_notification_async(
                f"New Item Added: {data['name']}",
                f"A new {data['category']} has been added to your collection.",
                new_item
            )
            
            return jsonify({
                'success': True,
                'item': new_item,
                'message': 'Item created successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to create item'
            }), 500
            
    except Exception as e:
        logger.error(f"Error creating item: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@items_bp.route('/<int:item_id>', methods=['GET'])
def get_item(item_id: int):
    """Get a specific item by ID"""
    try:
        item = db_manager.get_item_by_id(item_id)
        
        if item:
            return jsonify({
                'success': True,
                'item': item
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Item not found'
            }), 404
            
    except Exception as e:
        logger.error(f"Error fetching item {item_id}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@items_bp.route('/<int:item_id>', methods=['PUT'])
def update_item(item_id: int):
    """Update an existing collection item"""
    try:
        data = request.json
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        # Get existing item
        existing_item = db_manager.get_item_by_id(item_id)
        if not existing_item:
            return jsonify({'success': False, 'error': 'Item not found'}), 404
        
        # Clean numeric fields
        numeric_fields = [
            'current_value', 'sold_price', 'acquisition_price',
            'current_offer', 'commission_rate', 'surface_m2',
            'rental_income_chf', 'stock_quantity', 'stock_purchase_price',
            'current_price'
        ]
        
        for field in numeric_fields:
            if field in data:
                data[field] = to_numeric_or_none(data[field])
        
        # Update item in database
        updated_item = db_manager.update_item(item_id, data)
        
        if updated_item:
            # Check for significant changes and send notification
            if existing_item.get('status') != updated_item.get('status'):
                email_service.send_notification_async(
                    f"Item Status Changed: {updated_item['name']}",
                    f"Status changed from {existing_item.get('status')} to {updated_item.get('status')}",
                    updated_item
                )
            
            return jsonify({
                'success': True,
                'item': updated_item,
                'message': 'Item updated successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to update item'
            }), 500
            
    except Exception as e:
        logger.error(f"Error updating item {item_id}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@items_bp.route('/<int:item_id>', methods=['DELETE'])
def delete_item(item_id: int):
    """Delete a collection item"""
    try:
        # Get item details before deletion for notification
        item = db_manager.get_item_by_id(item_id)
        if not item:
            return jsonify({'success': False, 'error': 'Item not found'}), 404
        
        # Delete item
        success = db_manager.delete_item(item_id)
        
        if success:
            # Send notification
            email_service.send_notification_async(
                f"Item Deleted: {item['name']}",
                f"The {item['category']} '{item['name']}' has been removed from your collection.",
                item
            )
            
            return jsonify({
                'success': True,
                'message': 'Item deleted successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to delete item'
            }), 500
            
    except Exception as e:
        logger.error(f"Error deleting item {item_id}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@items_bp.route('/category/<category>', methods=['GET'])
def get_items_by_category(category: str):
    """Get items by category"""
    try:
        items = db_manager.get_items_by_category(category)
        return jsonify({
            'success': True,
            'items': items,
            'count': len(items),
            'category': category
        })
    except Exception as e:
        logger.error(f"Error fetching items by category {category}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@items_bp.route('/for-sale', methods=['GET'])
def get_items_for_sale():
    """Get all items marked for sale"""
    try:
        items = db_manager.get_items_for_sale()
        return jsonify({
            'success': True,
            'items': items,
            'count': len(items)
        })
    except Exception as e:
        logger.error(f"Error fetching items for sale: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@items_bp.route('/sold', methods=['GET'])
def get_sold_items():
    """Get all sold items"""
    try:
        items = db_manager.get_sold_items()
        return jsonify({
            'success': True,
            'items': items,
            'count': len(items)
        })
    except Exception as e:
        logger.error(f"Error fetching sold items: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@items_bp.route('/stocks', methods=['GET'])
def get_stock_items():
    """Get all items with stock symbols"""
    try:
        items = db_manager.get_stock_items()
        return jsonify({
            'success': True,
            'items': items,
            'count': len(items)
        })
    except Exception as e:
        logger.error(f"Error fetching stock items: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500