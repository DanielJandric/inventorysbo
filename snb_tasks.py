"""
Tâches Celery pour le module SNB
Permet l'exécution en background du scraping
"""

import os
import sys
import subprocess
from celery_app import celery


@celery.task(bind=True, name='snb_tasks.snb_collect_task')
def snb_collect_task(self, mode: str = 'monthly'):
    """
    Tâche Celery pour la collecte SNB (background worker)
    
    Args:
        mode: 'daily', 'monthly', 'quarterly', ou 'all'
    
    Returns:
        dict avec success, message, output
    """
    try:
        self.update_state(state='PROGRESS', meta={'step': 'starting', 'mode': mode, 'pct': 10})
        
        # Lancer le scraper en subprocess
        cmd = [sys.executable, "snb_auto_scraper.py", f"--{mode}"]
        
        self.update_state(state='PROGRESS', meta={'step': 'scraping', 'mode': mode, 'pct': 30})
        
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Attendre max 180 secondes (3 minutes pour scraping complexe)
        try:
            stdout, stderr = process.communicate(timeout=180)
            
            self.update_state(state='PROGRESS', meta={'step': 'completed', 'pct': 100})
            
            if process.returncode == 0:
                return {
                    "success": True,
                    "message": f"Collecte {mode} terminee avec succes",
                    "output": stdout,
                    "errors": stderr if stderr else None
                }
            else:
                return {
                    "success": False,
                    "error": f"Scraper failed with code {process.returncode}",
                    "output": stdout,
                    "stderr": stderr
                }
                
        except subprocess.TimeoutExpired:
            process.kill()
            self.update_state(state='FAILURE', meta={'error': 'Timeout'})
            return {
                "success": False,
                "error": "Timeout: La collecte a pris plus de 180 secondes"
            }
    
    except Exception as e:
        import traceback
        self.update_state(state='FAILURE', meta={'error': str(e)})
        return {
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }


@celery.task(bind=True, name='snb_tasks.snb_neer_collect_task')
def snb_neer_collect_task(self):
    """
    Tâche Celery pour collecter le NEER depuis data.snb.ch
    
    Returns:
        dict avec success, neer_change_3m_pct
    """
    try:
        from snb_neer_collector import collect_neer_from_snb_api
        
        self.update_state(state='PROGRESS', meta={'step': 'fetching_neer', 'pct': 50})
        
        result = collect_neer_from_snb_api()
        
        self.update_state(state='PROGRESS', meta={'step': 'completed', 'pct': 100})
        
        return {
            "success": True,
            "neer_change_3m_pct": result.get("neer_change_3m_pct"),
            "neer_value": result.get("neer_value")
        }
    
    except Exception as e:
        import traceback
        self.update_state(state='FAILURE', meta={'error': str(e)})
        return {
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }

