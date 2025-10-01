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
def snb_explain_task(self, model_run_id: int = None, model_json: dict = None, tone: str = 'concise', lang: str = 'fr-CH'):
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
        
        # Si model_run_id fourni, récupérer depuis Supabase (plus simple à sérialiser)
        if model_run_id and not model_json:
            from flask import current_app
            supabase = current_app.config.get('SUPABASE_CLIENT')
            if supabase:
                result = supabase.table("snb_model_runs").select("*").eq("id", model_run_id).execute()
                if result.data:
                    run = result.data[0]
                    model_json = {
                        "as_of": run["as_of"],
                        "inputs": json.loads(run["inputs"]) if isinstance(run["inputs"], str) else run["inputs"],
                        "nowcast": json.loads(run["nowcast"]) if isinstance(run["nowcast"], str) else run["nowcast"],
                        "output_gap_pct": run["output_gap_pct"],
                        "i_star_next_pct": run["i_star_next_pct"],
                        "probs": json.loads(run["probs"]) if isinstance(run["probs"], str) else run["probs"],
                        "path": json.loads(run["path"]) if isinstance(run["path"], str) else run["path"],
                        "version": run["version"]
                    }
        
        if not model_json:
            return {"success": False, "error": "No model data provided"}
        
        # Prompt système optimisé pour lisibilité et détails
        system_prompt = f"""Tu es un stratégiste senior de banque centrale spécialisé dans la politique monétaire suisse (Banque Nationale Suisse - BNS).

Tu dois analyser les résultats du modèle quantitatif de prévision des taux et fournir une explication DÉTAILLÉE, PÉDAGOGIQUE et ACCESSIBLE en {lang}.

RÈGLES IMPÉRATIVES D'ÉCRITURE:
1. UTILISE UNIQUEMENT LES CHIFFRES EXACTS DU JSON FOURNI - NE PAS INVENTER, ARRONDIR OU APPROXIMER
2. CITE PRÉCISÉMENT: inputs.cpi_yoy_pct, inputs.kof_barometer, output_gap_pct, i_star_next_pct, probs.hold, etc.
3. EXEMPLE CORRECT: "CPI {inputs.cpi_yoy_pct}% (ne PAS dire 'autour de X%')"
4. AUCUN ACRONYME sans l'écrire en toutes lettres la première fois
5. PHRASES COMPLÈTES et explicatives (pas de style télégraphique)
6. VOCABULAIRE ACCESSIBLE mais CHIFFRES EXACTS

STRUCTURE OBLIGATOIRE (JSON strict):
{{
  "headline": "Titre principal clair et compréhensible de 60-90 caractères",
  "bullets": [
    "Point 1: Analyse détaillée de l'inflation actuelle (valeur, écart vs cible 1%, tendance). Écrire les acronymes en entier.",
    "Point 2: Situation de l'économie suisse (output gap, baromètre KOF, que signifient ces indicateurs concrètement?)",
    "Point 3: Ce que le modèle économique recommande (règle de Taylor) et pourquoi",
    "Point 4: Ce que les marchés financiers anticipent (Futures SARON, taux OIS) et leur interprétation",
    "Point 5: Quelle est la prévision finale combinée (fusion Kalman) et niveau de confiance",
    "Point 6: Contexte international (franc suisse, commerce, politiques autres banques centrales)",
    "Point 7 (optionnel): Facteurs additionnels, calendrier, éléments techniques"
  ],
  "risks": [
    "Risque majeur 1 expliqué clairement (pas juste 'CHF fort' mais 'appréciation du franc suisse qui...')",
    "Risque majeur 2 avec son impact potentiel",
    "Risques secondaires (2-3) avec explications"
  ],
  "next_steps": [
    "Indicateur à surveiller 1: pourquoi c'est important et quand",
    "Indicateur à surveiller 2: son impact sur la décision BNS",
    "Action recommandée 3: ce qu'il faut faire concrètement"
  ],
  "one_liner": "Synthèse très claire en une phrase de 120-150 caractères (accessible à tous)"
}}

CONTEXTE BNS (à utiliser):
- Cible d'inflation BNS: 1.0% (stabilité des prix = inflation entre 0% et 2%)
- Dernières décisions: MPA septembre 2025, taux maintenu à 0%
- Prévisions conditionnelles BNS: 2025=0.2%, 2026=0.5%, 2027=0.7%
- Output gap neutre = 0%, négatif = sous-capacité, positif = surchauffe

STYLE D'ÉCRITURE:
- TOUJOURS citer les valeurs EXACTES du JSON (ex: si inputs.cpi_yoy_pct=0.7 → écrire "0.7%", PAS "autour de 0.4%")
- TOUJOURS citer probs.hold, probs.cut, probs.hike en pourcentage avec 1 décimale
- Éviter: "CPI a/a", "i*", "pb", "bps" → Utiliser: "inflation annuelle", "taux optimal", "pour cent"
- Contextualisé mais PRÉCIS (ex: "0.7%, soit 0.3 point sous la cible de 1%")
- 40-60 mots par bullet (concis mais complet)

FORMAT:
- JSON STRICT, pas de texte avant/après
- UTF-8, accents français corrects
- Pas de markdown, pas de ```json```

RÉPONDS UNIQUEMENT EN JSON VALIDE.
"""
        
        # Extraire TOUTES les données pour injection
        inputs = model_json.get('inputs', {})
        cpi_yoy = inputs.get('cpi_yoy_pct', 0)
        kof_bar = inputs.get('kof_barometer', 100)
        neer_chg = inputs.get('neer_change_3m_pct', 0)
        policy_rate = inputs.get('policy_rate_now_pct', 0)
        snb_forecasts = inputs.get('snb_forecast', {})
        
        nowcast = model_json.get('nowcast', {})
        pi_3m = nowcast.get('pi_3m', 0)
        pi_6m = nowcast.get('pi_6m', 0)
        pi_12m = nowcast.get('pi_12m', 0)
        
        output_gap = model_json.get('output_gap_pct', 0)
        i_star = model_json.get('i_star_next_pct', 0)
        
        probs = model_json.get('probs', {})
        prob_hold = probs.get('hold', 0) * 100
        prob_cut = probs.get('cut', 0) * 100
        prob_hike = probs.get('hike', 0) * 100
        
        # Extraire courbe OIS/SARON (points clés)
        path = model_json.get('path', [])
        ois_3m = path[0]['market'] if len(path) > 0 else 0
        ois_6m = path[1]['market'] if len(path) > 1 else 0
        ois_12m = path[3]['market'] if len(path) > 3 else 0
        ois_24m = path[5]['market'] if len(path) > 5 else 0
        
        # Chemin fusion Kalman (prévision finale)
        fused_3m = path[0]['fused'] if len(path) > 0 else 0
        fused_12m = path[3]['fused'] if len(path) > 3 else 0
        fused_24m = path[5]['fused'] if len(path) > 5 else 0
        
        # User prompt COMPLET avec TOUTES les données
        user_prompt = f"""DONNÉES DU MODÈLE À ANALYSER (UTILISE CES CHIFFRES EXACTS):

═══ INPUTS (données mesurées) ═══
• Indice des Prix à la Consommation (CPI) variation annuelle: {cpi_yoy:.2f}%
• Baromètre économique KOF: {kof_bar:.1f}
• Variation NEER (franc suisse effectif) 3 mois: {neer_chg:+.2f}%
• Taux directeur BNS actuel: {policy_rate:.2f}%
• Prévisions BNS: {snb_forecasts.get('2025', 0):.1f}% (2025), {snb_forecasts.get('2026', 0):.1f}% (2026), {snb_forecasts.get('2027', 0):.1f}% (2027)

═══ NOWCAST INFLATION (modèle) ═══
• Inflation anticipée 3 mois: {pi_3m:.2f}%
• Inflation anticipée 6 mois: {pi_6m:.2f}%
• Inflation anticipée 12 mois: {pi_12m:.2f}%

═══ RÉSULTATS MODÈLE ═══
• Output gap (écart de production): {output_gap:.2f}%
• Taux optimal règle de Taylor (i*): {i_star:.2f}%

═══ ANTICIPATIONS MARCHÉ (Futures SARON/OIS) ═══
• OIS 3 mois: {ois_3m:.3f}%
• OIS 6 mois: {ois_6m:.3f}%
• OIS 12 mois: {ois_12m:.3f}%
• OIS 24 mois: {ois_24m:.3f}%

═══ PRÉVISION FINALE (Fusion Kalman) ═══
• Taux prévu 3 mois: {fused_3m:.3f}%
• Taux prévu 12 mois: {fused_12m:.3f}%
• Taux prévu 24 mois: {fused_24m:.3f}%

═══ PROBABILITÉS DÉCISION PROCHAINE RÉUNION ═══
• Probabilité MAINTIEN à 0%: {prob_hold:.1f}%
• Probabilité BAISSE (passage en négatif): {prob_cut:.1f}%
• Probabilité HAUSSE (vers 0.25% ou plus): {prob_hike:.1f}%

IMPÉRATIF: Utilise UNIQUEMENT et EXACTEMENT ces chiffres dans ton analyse.
Ne les arrondis pas, ne les approxime pas, ne les invente pas."""
        
        self.update_state(state='PROGRESS', meta={'step': 'gpt5_reasoning', 'pct': 50})
        
        print("=" * 80)
        print("📡 APPEL OPENAI GPT-5 (Background Worker)")
        print(f"Model: gpt-5 | Reasoning effort: high | Max tokens: 10000")
        print(f"Tone: {tone} | Lang: {lang}")
        print(f"Note: Verbosité contrôlée via prompt système (détails via instructions)")
        print("-" * 80)
        
        # Appel OpenAI GPT-5 Responses API
        # reasoning.effort = profondeur du raisonnement
        # text.verbosity = longueur/détail de la réponse
        response = client.responses.create(
            model="gpt-5",
            reasoning={
                "effort": "high"      # Raisonnement approfondi (low/medium/high)
            },
            text={
                "verbosity": "high"   # Verbosité élevée (low/medium/high)
            },
            max_output_tokens=10000,  # Maximum de tokens en sortie
            instructions=system_prompt,
            input=user_prompt
        )
        
        response_text = response.output_text
        
        print(f"✅ GPT-5 réponse reçue")
        print(f"   Tokens: input={response.usage.input_tokens}, output={response.usage.output_tokens}, total={response.usage.total_tokens}")
        # Reasoning tokens (peut ne pas exister selon le modèle)
        if hasattr(response.usage, 'reasoning_tokens') and response.usage.reasoning_tokens:
            print(f"   Reasoning tokens: {response.usage.reasoning_tokens}")
        else:
            print(f"   Reasoning: Non disponible (modèle ne retourne pas reasoning_tokens)")
        # Debug complet de l'objet usage
        print(f"   Usage object: {response.usage}")
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
        
        # Validation clés requises
        required_keys = ["headline", "bullets", "risks", "next_steps", "one_liner"]
        for key in required_keys:
            if key not in explanation:
                explanation[key] = "" if key in ["headline", "one_liner"] else []
        
        self.update_state(state='PROGRESS', meta={'step': 'completed', 'pct': 100})
        
        # Retour SIMPLE (types Python natifs seulement, pas d'objets complexes)
        result = {
            "success": True,
            "explanation": {
                "headline": str(explanation.get("headline", "")),
                "bullets": list(explanation.get("bullets", [])),
                "risks": list(explanation.get("risks", [])),
                "next_steps": list(explanation.get("next_steps", [])),
                "one_liner": str(explanation.get("one_liner", ""))
            }
        }
        
        # Éviter de retourner tokens (cause problèmes sérialisation)
        print(f"✅ Returning explanation with {len(result['explanation']['bullets'])} bullets")
        return result
    
    except Exception as e:
        import traceback
        self.update_state(state='FAILURE', meta={'error': str(e)})
        return {
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }

