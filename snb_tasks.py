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


@celery.task(bind=True, name='snb_tasks.snb_explain_task')
def snb_explain_task(self, model_json: dict, tone: str = 'concise', lang: str = 'fr-CH'):
    """
    Tâche Celery pour générer l'explication GPT-5 en background
    Évite le timeout Gunicorn worker (GPT-5 reasoning_effort=high prend 7-10s)
    
    Args:
        model_json: JSON du modèle BNS
        tone: Ton de l'explication
        lang: Langue (fr-CH par défaut)
    
    Returns:
        dict avec success, explanation (JSON)
    """
    try:
        import os
        import json
        from openai import OpenAI
        
        self.update_state(state='PROGRESS', meta={'step': 'calling_gpt5', 'pct': 30})
        
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return {
                "success": False,
                "error": "OpenAI API key not configured"
            }
        
        client = OpenAI(api_key=api_key)
        
        # Prompt système
        system_prompt = f"""Tu es un stratégiste senior de banque centrale spécialisé dans la politique monétaire suisse (BNS).

Tu dois analyser les résultats du modèle quantitatif de prévision des taux BNS et fournir une explication structurée en {lang}.

STRUCTURE OBLIGATOIRE (JSON strict):
{{
  "headline": "Titre principal de 60-80 caractères résumant la décision probable",
  "bullets": [
    "Point clé 1: Analyse de l'inflation et écart vs cible BNS (1%)",
    "Point clé 2: Analyse de l'output gap et activité économique",
    "Point clé 3: Analyse des anticipations de marché (OIS/Futures)",
    "Point clé 4: Contexte macro (CHF, commerce international, croissance)",
    "Point clé 5 (optionnel): Facteurs techniques ou calendrier"
  ],
  "risks": [
    "Risque 1: Appréciation CHF",
    "Risque 2: Ralentissement conjoncture mondiale",
    "Risque 3-4: Autres risques pertinents"
  ],
  "next_steps": [
    "Action 1: Indicateurs à surveiller (CPI mensuel, KOF)",
    "Action 2: Événements macro à suivre",
    "Action 3 (optionnel): Ajustements potentiels"
  ],
  "one_liner": "Synthèse ultra-concise de 100-140 caractères (tweet-ready)"
}}

INSTRUCTIONS:
- Ton: {tone}, professionnel, factuel
- Contexte: Utilise les données BNS officielles (MPA sept 2025: taux 0%, prévisions 0.2%/0.5%/0.7%)
- Chiffres: Cite précisément les valeurs du modèle (%, points de base)
- Probabilités: Interprète les probs (cut/hold/hike) de manière claire
- Format: JSON STRICT, pas de texte avant/après, UTF-8

RÉPONDS UNIQUEMENT EN JSON VALIDE. Pas de markdown, pas de ```json```, juste le JSON pur.
"""
        
        user_prompt = f"Voici le JSON du modèle BNS à analyser:\n\n{json.dumps(model_json, indent=2, ensure_ascii=False)}"
        
        self.update_state(state='PROGRESS', meta={'step': 'gpt5_reasoning', 'pct': 50})
        
        print("=" * 80)
        print("📡 APPEL OPENAI GPT-5 (Background Worker)")
        print(f"Model: gpt-5 | Reasoning: high | Max tokens: 10000")
        print("-" * 80)
        
        # Appel OpenAI GPT-5
        response = client.responses.create(
            model="gpt-5",
            reasoning={"effort": "high"},
            max_output_tokens=10000,
            instructions=system_prompt,
            input=user_prompt
        )
        
        response_text = response.output_text
        
        print(f"✅ GPT-5 réponse reçue")
        print(f"   Tokens: input={response.usage.input_tokens}, output={response.usage.output_tokens}")
        if hasattr(response.usage, 'reasoning_tokens'):
            print(f"   Reasoning tokens: {response.usage.reasoning_tokens}")
        print("=" * 80)
        
        self.update_state(state='PROGRESS', meta={'step': 'parsing_json', 'pct': 90})
        
        # Parse JSON
        try:
            explanation = json.loads(response_text)
        except json.JSONDecodeError:
            import re
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                explanation = json.loads(json_match.group(0))
            else:
                raise ValueError("GPT response is not valid JSON")
        
        # Validation
        required_keys = ["headline", "bullets", "risks", "next_steps", "one_liner"]
        for key in required_keys:
            if key not in explanation:
                explanation[key] = f"[{key} manquant]"
        
        self.update_state(state='PROGRESS', meta={'step': 'completed', 'pct': 100})
        
        return {
            "success": True,
            "explanation": explanation,
            "tokens": {
                "input": response.usage.input_tokens,
                "output": response.usage.output_tokens,
                "total": response.usage.total_tokens,
                "reasoning": getattr(response.usage, 'reasoning_tokens', 0)
            }
        }
    
    except Exception as e:
        import traceback
        self.update_state(state='FAILURE', meta={'error': str(e)})
        return {
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }

