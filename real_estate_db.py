#!/usr/bin/env python3
"""
Gestionnaire de base de données pour les annonces immobilières.
"""

import os
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class RealEstateListing:
    """Modèle de données pour une annonce immobilière."""
    id: Optional[int] = None
    source_url: str = ''
    source_site: Optional[str] = None
    title: Optional[str] = None
    location: Optional[str] = None
    price: Optional[int] = None
    rental_income_yearly: Optional[int] = None
    yield_percentage: Optional[float] = None
    number_of_apartments: Optional[int] = None
    living_space_m2: Optional[int] = None
    plot_surface_m2: Optional[int] = None
    image_url: Optional[str] = None
    description_summary: Optional[str] = None
    status: str = 'new'
    scraped_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convertit en dictionnaire pour Supabase, en excluant les champs None."""
        return {k: v for k, v in asdict(self).items() if v is not None}
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RealEstateListing':
        """Crée une instance à partir d'un dictionnaire de Supabase."""
        valid_fields = {k: v for k, v in data.items() if k in cls.__annotations__}
        return cls(**valid_fields)

class RealEstateDB:
    """Gestionnaire pour la table real_estate_listings."""

    def __init__(self):
        try:
            supabase_url = os.getenv('SUPABASE_URL')
            supabase_key = os.getenv('SUPABASE_KEY')
            if not supabase_url or not supabase_key:
                raise ValueError("Variables d'environnement Supabase manquantes")
            self.supabase: Client = create_client(supabase_url, supabase_key)
            logger.info("✅ Connexion à Supabase établie pour RealEstateDB.")
        except Exception as e:
            logger.error(f"❌ Erreur de connexion Supabase pour RealEstateDB: {e}")
            self.supabase = None

    def is_connected(self) -> bool:
        return self.supabase is not None

    def save_listing(self, listing: RealEstateListing) -> Optional[int]:
        """Sauvegarde une nouvelle annonce. Ignore si l'URL source existe déjà."""
        try:
            if not self.is_connected(): return None
            
            # La contrainte UNIQUE sur 'source_url' gère les doublons
            result = self.supabase.table('real_estate_listings')\
                .insert(listing.to_dict(), on_conflict='source_url')\
                .execute()

            if result.data:
                listing_id = result.data[0]['id']
                logger.info(f"✅ Annonce sauvegardée/ignorée avec l'ID: {listing_id}")
                return listing_id
            return None
        except Exception as e:
            logger.error(f"❌ Erreur lors de la sauvegarde de l'annonce: {e}")
            return None

    def get_all_listings(self, limit: int = 100) -> List[RealEstateListing]:
        """Récupère toutes les annonces, les plus récentes d'abord."""
        try:
            if not self.is_connected(): return []
            
            result = self.supabase.table('real_estate_listings')\
                .select('*')\
                .order('scraped_at', desc=True)\
                .limit(limit)\
                .execute()

            return [RealEstateListing.from_dict(data) for data in result.data]
        except Exception as e:
            logger.error(f"❌ Erreur lors de la récupération des annonces: {e}")
            return []

    def update_listing_status(self, listing_id: int, status: str) -> bool:
        """Met à jour le statut d'une annonce."""
        try:
            if not self.is_connected(): return False
            
            result = self.supabase.table('real_estate_listings')\
                .update({'status': status})\
                .eq('id', listing_id)\
                .execute()
            
            return bool(result.data)
        except Exception as e:
            logger.error(f"❌ Erreur lors de la mise à jour du statut: {e}")
            return False

# Instance globale
real_estate_db = RealEstateDB()

def get_real_estate_db() -> RealEstateDB:
    return real_estate_db
