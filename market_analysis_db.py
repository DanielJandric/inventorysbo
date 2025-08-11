#!/usr/bin/env python3
"""
Gestionnaire de base de données pour les analyses de marché du Background Worker
"""

import os
import json
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from supabase import create_client, Client

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class MarketAnalysis:
    """Modèle de données pour une analyse de marché"""
    id: Optional[int] = None
    timestamp: Optional[str] = None
    analysis_type: str = 'automatic'
    prompt: Optional[str] = None
    executive_summary: Optional[List[str]] = None
    summary: Optional[str] = None
    key_points: Optional[List[str]] = None
    structured_data: Optional[Dict[str, Any]] = None
    geopolitical_analysis: Optional[Dict[str, Any]] = None
    economic_indicators: Optional[Dict[str, Any]] = None
    insights: Optional[List[str]] = None
    risks: Optional[List[str]] = None
    opportunities: Optional[List[str]] = None
    sources: Optional[List[Dict[str, str]]] = None
    confidence_score: Optional[float] = None
    worker_status: str = 'completed'
    processing_time_seconds: Optional[int] = None
    error_message: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convertit en dictionnaire pour Supabase"""
        data = asdict(self)
        # Convertir les listes en JSONB pour Supabase
        if self.executive_summary:
            data['executive_summary'] = json.dumps(self.executive_summary)
        if self.key_points:
            data['key_points'] = json.dumps(self.key_points)
        if self.insights:
            data['insights'] = json.dumps(self.insights)
        if self.risks:
            data['risks'] = json.dumps(self.risks)
        if self.opportunities:
            data['opportunities'] = json.dumps(self.opportunities)
        if self.sources:
            data['sources'] = json.dumps(self.sources)
        if self.structured_data:
            data['structured_data'] = json.dumps(self.structured_data)
        if self.geopolitical_analysis:
            data['geopolitical_analysis'] = json.dumps(self.geopolitical_analysis)
        if self.economic_indicators:
            data['economic_indicators'] = json.dumps(self.economic_indicators)
        
        # Supprimer les champs None
        return {k: v for k, v in data.items() if v is not None}

    def to_frontend_dict(self) -> Dict[str, Any]:
        """Convertit en dictionnaire pour le frontend (JSON valide)."""
        data = asdict(self)
        # Assurer que les champs JSON sont des listes/dict et non des strings
        json_fields = ['executive_summary', 'key_points', 'insights', 'risks', 'opportunities', 'sources', 'structured_data', 'geopolitical_analysis', 'economic_indicators']
        dict_fields = {'structured_data', 'geopolitical_analysis', 'economic_indicators'}
        for field in json_fields:
            if isinstance(data.get(field), str):
                try:
                    data[field] = json.loads(data[field])
                except (json.JSONDecodeError, TypeError):
                    logger.warning(f"Impossible de décoder le JSON pour le champ {field}")
                    # Remplacer par une valeur par défaut en cas d'erreur
                    if field in dict_fields:
                        data[field] = {}
                    elif field == 'sources':
                        data[field] = []
                    else:
                        data[field] = []
        
        return {k: v for k, v in data.items() if v is not None}


    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MarketAnalysis':
        """Crée une instance depuis un dictionnaire de Supabase"""
        # Convertir les JSONB en listes/dictionnaires
        if isinstance(data.get('executive_summary'), str):
            data['executive_summary'] = json.loads(data['executive_summary'])
        if isinstance(data.get('key_points'), str):
            data['key_points'] = json.loads(data['key_points'])
        if isinstance(data.get('insights'), str):
            data['insights'] = json.loads(data['insights'])
        if isinstance(data.get('risks'), str):
            data['risks'] = json.loads(data['risks'])
        if isinstance(data.get('opportunities'), str):
            data['opportunities'] = json.loads(data['opportunities'])
        if isinstance(data.get('sources'), str):
            data['sources'] = json.loads(data['sources'])
        if isinstance(data.get('structured_data'), str):
            data['structured_data'] = json.loads(data['structured_data'])
        if isinstance(data.get('geopolitical_analysis'), str):
            data['geopolitical_analysis'] = json.loads(data['geopolitical_analysis'])
        if isinstance(data.get('economic_indicators'), str):
            data['economic_indicators'] = json.loads(data['economic_indicators'])
        
        return cls(**data)

class MarketAnalysisDB:
    """Gestionnaire de base de données pour les analyses de marché"""
    
    def __init__(self):
        """Initialise la connexion à Supabase"""
        try:
            supabase_url = os.getenv('SUPABASE_URL')
            supabase_key = os.getenv('SUPABASE_KEY')
            
            if not supabase_url or not supabase_key:
                raise ValueError("Variables d'environnement Supabase manquantes")
            
            self.supabase: Client = create_client(supabase_url, supabase_key)
            logger.info("✅ Connexion à Supabase établie pour Market Analysis DB")
            
        except Exception as e:
            logger.error(f"❌ Erreur connexion Supabase: {e}")
            self.supabase = None
    
    def is_connected(self) -> bool:
        """Vérifie si la connexion est établie"""
        return self.supabase is not None
    
    def save_analysis(self, analysis: MarketAnalysis) -> Optional[int]:
        """Sauvegarde une analyse de marché"""
        try:
            if not self.is_connected():
                logger.error("❌ Pas de connexion à Supabase")
                return None
            
            # Préparer les données
            data = analysis.to_dict()
            if not analysis.timestamp:
                data['timestamp'] = datetime.now(timezone.utc).isoformat()
            
            # Insérer dans la base de données
            result = self.supabase.table('market_analyses').insert(data).execute()
            
            if result.data:
                analysis_id = result.data[0]['id']
                logger.info(f"✅ Analyse sauvegardée avec l'ID: {analysis_id}")
                return analysis_id
            else:
                logger.error("❌ Erreur lors de la sauvegarde de l'analyse")
                return None
                
        except Exception as e:
            logger.error(f"❌ Erreur sauvegarde analyse: {e}")
            return None
    
    def get_latest_analysis(self) -> Optional[MarketAnalysis]:
        """Récupère la dernière analyse de marché"""
        try:
            if not self.is_connected():
                logger.error("❌ Pas de connexion à Supabase")
                return None
            
            result = self.supabase.table('market_analyses')\
                .select('*')\
                .order('timestamp', desc=True)\
                .limit(1)\
                .execute()
            
            if result.data:
                analysis_data = result.data[0]
                analysis = MarketAnalysis.from_dict(analysis_data)
                logger.info(f"✅ Dernière analyse récupérée (ID: {analysis.id})")
                return analysis
            else:
                logger.info("ℹ️ Aucune analyse trouvée dans la base de données")
                return None
                
        except Exception as e:
            logger.error(f"❌ Erreur récupération dernière analyse: {e}")
            return None
    
    def get_analyses_by_type(self, analysis_type: str, limit: int = 10) -> List[MarketAnalysis]:
        """Récupère les analyses par type"""
        try:
            if not self.is_connected():
                logger.error("❌ Pas de connexion à Supabase")
                return []
            
            result = self.supabase.table('market_analyses')\
                .select('*')\
                .eq('analysis_type', analysis_type)\
                .order('timestamp', desc=True)\
                .limit(limit)\
                .execute()
            
            analyses = []
            for data in result.data:
                analysis = MarketAnalysis.from_dict(data)
                analyses.append(analysis)
            
            logger.info(f"✅ {len(analyses)} analyses de type '{analysis_type}' récupérées")
            return analyses
                
        except Exception as e:
            logger.error(f"❌ Erreur récupération analyses par type: {e}")
            return []

    def get_pending_analysis(self) -> Optional[MarketAnalysis]:
        """Récupère la plus ancienne analyse en attente."""
        try:
            if not self.is_connected(): return None
            
            result = self.supabase.table('market_analyses')\
                .select('*')\
                .eq('worker_status', 'pending')\
                .order('created_at', desc=False)\
                .limit(1)\
                .execute()
                
            if result.data:
                analysis = MarketAnalysis.from_dict(result.data[0])
                logger.info(f"ℹ️ Tâche en attente trouvée: ID {analysis.id}")
                return analysis
            return None
        except Exception as e:
            logger.error(f"❌ Erreur get_pending_analysis: {e}")
            return None

    def update_analysis_status(self, analysis_id: int, status: str):
        """Met à jour uniquement le statut d'une analyse."""
        self.update_analysis(analysis_id, {'worker_status': status})

    def update_analysis(self, analysis_id: int, data: Dict[str, Any]) -> bool:
        """Met à jour une analyse avec de nouvelles données."""
        try:
            if not self.is_connected(): return False
            
            # Assurer la mise à jour de 'updated_at'
            data['updated_at'] = datetime.now(timezone.utc).isoformat()
            
            result = self.supabase.table('market_analyses')\
                .update(data)\
                .eq('id', analysis_id)\
                .execute()

            if result.data:
                logger.info(f"✅ Analyse ID {analysis_id} mise à jour.")
                return True
            else:
                logger.error(f"❌ Échec de la mise à jour de l'analyse ID {analysis_id}")
                return False
        except Exception as e:
            logger.error(f"❌ Erreur update_analysis: {e}")
            return False

    def get_analysis_by_id(self, analysis_id: int) -> Optional[MarketAnalysis]:
        """Récupère une analyse spécifique par son ID."""
        try:
            if not self.is_connected():
                logger.error("❌ Pas de connexion à Supabase")
                return None
            
            result = self.supabase.table('market_analyses')\
                .select('*')\
                .eq('id', analysis_id)\
                .execute()
            
            if result.data:
                analysis_data = result.data[0]
                analysis = MarketAnalysis.from_dict(analysis_data)
                logger.info(f"✅ Analyse #{analysis_id} récupérée")
                return analysis
            else:
                logger.warning(f"⚠️ Aucune analyse trouvée avec l'ID {analysis_id}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Erreur récupération analyse #{analysis_id}: {e}")
            return None

    
    def get_worker_status(self) -> Dict[str, Any]:
        """Récupère le statut du Background Worker"""
        try:
            if not self.is_connected():
                return {"available": False, "error": "Pas de connexion à Supabase"}
            
            # Vérifier la dernière analyse
            latest = self.get_latest_analysis()
            if not latest:
                return {
                    "available": True,
                    "status": "no_analysis",
                    "message": "Aucune analyse disponible",
                    "last_check": datetime.now(timezone.utc).isoformat()
                }
            
            # Vérifier si l'analyse est récente (moins de 6 heures)
            if latest.timestamp:
                analysis_time = datetime.fromisoformat(latest.timestamp.replace('Z', '+00:00'))
                now = datetime.now(timezone.utc)
                hours_since_analysis = (now - analysis_time).total_seconds() / 3600
                
                if hours_since_analysis < 6:
                    return {
                        "available": True,
                        "status": "recent_analysis",
                        "last_analysis": latest.timestamp,
                        "hours_since_analysis": round(hours_since_analysis, 1),
                        "last_check": now.isoformat()
                    }
                else:
                    return {
                        "available": True,
                        "status": "stale_analysis",
                        "last_analysis": latest.timestamp,
                        "hours_since_analysis": round(hours_since_analysis, 1),
                        "message": "Dernière analyse ancienne",
                        "last_check": now.isoformat()
                    }
            
            return {
                "available": True,
                "status": "unknown",
                "last_check": datetime.now(timezone.utc).isoformat()
            }
                
        except Exception as e:
            logger.error(f"❌ Erreur vérification statut worker: {e}")
            return {"available": False, "error": str(e)}
    
    def create_test_analysis(self) -> Optional[int]:
        """Crée une analyse de test pour vérifier la base de données"""
        try:
            test_analysis = MarketAnalysis(
                analysis_type='test',
                summary='Analyse de test générée automatiquement',
                key_points=[
                    'Test de la base de données',
                    'Vérification de la connexion',
                    'Test des fonctionnalités'
                ],
                structured_data={
                    'prix': 'Test',
                    'tendance': 'Test',
                    'volumes': 'Test'
                },
                insights=['Test de la base de données'],
                risks=['Aucun risque'],
                opportunities=['Test réussi'],
                sources=[{'title': 'Test Analysis', 'url': '#'}],
                confidence_score=0.95,
                worker_status='completed'
            )
            
            return self.save_analysis(test_analysis)
            
        except Exception as e:
            logger.error(f"❌ Erreur création analyse de test: {e}")
            return None

# Instance globale
market_analysis_db = MarketAnalysisDB()

def get_market_analysis_db() -> MarketAnalysisDB:
    """Retourne l'instance globale du gestionnaire de base de données"""
    return market_analysis_db 