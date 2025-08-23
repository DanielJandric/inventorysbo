"""
Database module for Supabase operations and data management.
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from supabase import create_client, Client
from core.app_config import Config
from core.models import CollectionItem, MarketUpdate

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages all database operations with Supabase"""
    
    def __init__(self):
        """Initialize database connection"""
        self.supabase: Optional[Client] = None
        self._connect()
    
    def _connect(self):
        """Establish connection to Supabase"""
        try:
            if Config.SUPABASE_URL and Config.SUPABASE_KEY:
                self.supabase = create_client(Config.SUPABASE_URL, Config.SUPABASE_KEY)
                logger.info("✅ Supabase connected successfully")
            else:
                logger.error("❌ Supabase credentials missing")
        except Exception as e:
            logger.error(f"❌ Failed to connect to Supabase: {e}")
            self.supabase = None
    
    def is_connected(self) -> bool:
        """Check if database is connected"""
        return self.supabase is not None
    
    # ============ Collection Items Operations ============
    
    def get_all_items(self) -> List[Dict[str, Any]]:
        """Get all collection items"""
        if not self.is_connected():
            return []
        
        try:
            response = self.supabase.table('collection_items').select('*').execute()
            return response.data if response.data else []
        except Exception as e:
            logger.error(f"Error fetching items: {e}")
            return []
    
    def get_item_by_id(self, item_id: int) -> Optional[Dict[str, Any]]:
        """Get a specific item by ID"""
        if not self.is_connected():
            return None
        
        try:
            response = self.supabase.table('collection_items').select('*').eq('id', item_id).single().execute()
            return response.data
        except Exception as e:
            logger.error(f"Error fetching item {item_id}: {e}")
            return None
    
    def create_item(self, item_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a new collection item"""
        if not self.is_connected():
            return None
        
        try:
            # Clean data
            clean_data = self._clean_item_data(item_data)
            response = self.supabase.table('collection_items').insert(clean_data).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error creating item: {e}")
            return None
    
    def update_item(self, item_id: int, item_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update an existing collection item"""
        if not self.is_connected():
            return None
        
        try:
            # Clean data
            clean_data = self._clean_item_data(item_data)
            clean_data['updated_at'] = datetime.now().isoformat()
            
            response = self.supabase.table('collection_items').update(clean_data).eq('id', item_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error updating item {item_id}: {e}")
            return None
    
    def delete_item(self, item_id: int) -> bool:
        """Delete a collection item"""
        if not self.is_connected():
            return False
        
        try:
            self.supabase.table('collection_items').delete().eq('id', item_id).execute()
            return True
        except Exception as e:
            logger.error(f"Error deleting item {item_id}: {e}")
            return False
    
    def get_items_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Get items by category"""
        if not self.is_connected():
            return []
        
        try:
            response = self.supabase.table('collection_items').select('*').eq('category', category).execute()
            return response.data if response.data else []
        except Exception as e:
            logger.error(f"Error fetching items by category {category}: {e}")
            return []
    
    def get_items_for_sale(self) -> List[Dict[str, Any]]:
        """Get all items marked for sale"""
        if not self.is_connected():
            return []
        
        try:
            response = self.supabase.table('collection_items').select('*').eq('for_sale', True).execute()
            return response.data if response.data else []
        except Exception as e:
            logger.error(f"Error fetching items for sale: {e}")
            return []
    
    def get_sold_items(self) -> List[Dict[str, Any]]:
        """Get all sold items"""
        if not self.is_connected():
            return []
        
        try:
            response = self.supabase.table('collection_items').select('*').eq('status', 'sold').execute()
            return response.data if response.data else []
        except Exception as e:
            logger.error(f"Error fetching sold items: {e}")
            return []
    
    # ============ Stock Items Operations ============
    
    def get_stock_items(self) -> List[Dict[str, Any]]:
        """Get all items with stock symbols"""
        if not self.is_connected():
            return []
        
        try:
            response = self.supabase.table('collection_items').select('*').not_.is_('stock_symbol', 'null').execute()
            return response.data if response.data else []
        except Exception as e:
            logger.error(f"Error fetching stock items: {e}")
            return []
    
    def update_stock_price(self, item_id: int, price_data: Dict[str, Any]) -> bool:
        """Update stock price information for an item"""
        if not self.is_connected():
            return False
        
        try:
            update_data = {
                'current_price': price_data.get('price'),
                'last_price_update': datetime.now().isoformat(),
                'stock_change': price_data.get('change'),
                'stock_change_percent': price_data.get('change_percent'),
                'stock_volume': price_data.get('volume'),
                'stock_pe_ratio': price_data.get('pe_ratio'),
                'stock_52_week_high': price_data.get('week_52_high'),
                'stock_52_week_low': price_data.get('week_52_low'),
                'updated_at': datetime.now().isoformat()
            }
            
            # Remove None values
            update_data = {k: v for k, v in update_data.items() if v is not None}
            
            self.supabase.table('collection_items').update(update_data).eq('id', item_id).execute()
            return True
        except Exception as e:
            logger.error(f"Error updating stock price for item {item_id}: {e}")
            return False
    
    # ============ Market Updates Operations ============
    
    def save_market_update(self, update_data: MarketUpdate) -> Optional[int]:
        """Save a market update to the database"""
        if not self.is_connected():
            return None
        
        try:
            data = update_data.to_dict()
            response = self.supabase.table('market_updates').insert(data).execute()
            return response.data[0]['id'] if response.data else None
        except Exception as e:
            logger.error(f"Error saving market update: {e}")
            return None
    
    def get_recent_market_updates(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent market updates"""
        if not self.is_connected():
            return []
        
        try:
            response = self.supabase.table('market_updates').select('*').order('timestamp', desc=True).limit(limit).execute()
            return response.data if response.data else []
        except Exception as e:
            logger.error(f"Error fetching market updates: {e}")
            return []
    
    def get_market_update_by_id(self, update_id: int) -> Optional[Dict[str, Any]]:
        """Get a specific market update by ID"""
        if not self.is_connected():
            return None
        
        try:
            response = self.supabase.table('market_updates').select('*').eq('id', update_id).single().execute()
            return response.data
        except Exception as e:
            logger.error(f"Error fetching market update {update_id}: {e}")
            return None
    
    # ============ Embeddings Operations ============
    
    def update_item_embedding(self, item_id: int, embedding: List[float]) -> bool:
        """Update embedding for an item"""
        if not self.is_connected():
            return False
        
        try:
            self.supabase.table('collection_items').update({
                'embedding': embedding,
                'updated_at': datetime.now().isoformat()
            }).eq('id', item_id).execute()
            return True
        except Exception as e:
            logger.error(f"Error updating embedding for item {item_id}: {e}")
            return False
    
    def get_items_with_embeddings(self) -> List[Dict[str, Any]]:
        """Get all items that have embeddings"""
        if not self.is_connected():
            return []
        
        try:
            response = self.supabase.table('collection_items').select('*').not_.is_('embedding', 'null').execute()
            return response.data if response.data else []
        except Exception as e:
            logger.error(f"Error fetching items with embeddings: {e}")
            return []
    
    # ============ Chat History Operations ============
    
    def save_chat_message(self, conversation_id: str, role: str, content: str, metadata: Optional[Dict] = None) -> bool:
        """Save a chat message to history"""
        if not self.is_connected():
            return False
        
        try:
            data = {
                'conversation_id': conversation_id,
                'role': role,
                'content': content,
                'timestamp': datetime.now().isoformat(),
                'metadata': metadata or {}
            }
            
            self.supabase.table('chat_history').insert(data).execute()
            return True
        except Exception as e:
            logger.error(f"Error saving chat message: {e}")
            return False
    
    def get_chat_history(self, conversation_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get chat history for a conversation"""
        if not self.is_connected():
            return []
        
        try:
            response = self.supabase.table('chat_history').select('*').eq('conversation_id', conversation_id).order('timestamp', desc=False).limit(limit).execute()
            return response.data if response.data else []
        except Exception as e:
            logger.error(f"Error fetching chat history: {e}")
            return []
    
    # ============ Utility Methods ============
    
    def _clean_item_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Clean and validate item data before database operations"""
        # Remove None values and empty strings
        cleaned = {k: v for k, v in data.items() if v not in [None, '']}
        
        # Ensure numeric fields are properly typed
        numeric_fields = [
            'current_value', 'sold_price', 'acquisition_price', 'current_offer',
            'commission_rate', 'surface_m2', 'rental_income_chf', 'stock_quantity',
            'stock_purchase_price', 'current_price', 'stock_volume', 'stock_pe_ratio',
            'stock_52_week_high', 'stock_52_week_low', 'stock_change', 'stock_change_percent',
            'stock_average_volume'
        ]
        
        for field in numeric_fields:
            if field in cleaned:
                try:
                    cleaned[field] = float(cleaned[field])
                except (ValueError, TypeError):
                    del cleaned[field]
        
        # Ensure integer fields
        integer_fields = ['construction_year', 'stock_quantity', 'stock_volume', 'stock_average_volume']
        for field in integer_fields:
            if field in cleaned:
                try:
                    cleaned[field] = int(cleaned[field])
                except (ValueError, TypeError):
                    del cleaned[field]
        
        # Ensure boolean fields
        if 'for_sale' in cleaned:
            cleaned['for_sale'] = bool(cleaned['for_sale'])
        
        return cleaned
    
    def execute_raw_query(self, query: str, params: Optional[Dict] = None) -> Optional[Any]:
        """Execute a raw SQL query (use with caution)"""
        if not self.is_connected():
            return None
        
        try:
            # Note: Supabase client doesn't directly support raw SQL
            # This is a placeholder for potential RPC calls
            logger.warning("Raw SQL queries not directly supported via Supabase client")
            return None
        except Exception as e:
            logger.error(f"Error executing raw query: {e}")
            return None


# Create singleton instance
db_manager = DatabaseManager()