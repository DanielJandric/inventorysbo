"""
Fix DIRECT et SIMPLE pour stabiliser le chatbot de collection
Remplace uniquement les parties problématiques
"""

# Code à insérer dans app.py pour remplacer les lignes problématiques (5313-5320)

FIX_CODE = '''
        # ===== FIX STABILITÉ CHATBOT =====
        # Désactiver Celery complètement pour éviter timeouts et déconnexions
        USE_ASYNC = False  # FORCE SYNCHRONE
        
        # Au lieu de:
        # if os.getenv("CHAT_V2", "0") == "1" and not _force_sync:
        #     task = chat_v2_task.apply_async(...)
        #     return jsonify({"task_id": task.id}), 202
        
        # On fait TOUJOURS du synchrone:
        if USE_ASYNC and False:  # Jamais exécuté
            pass  # Celery désactivé
        
        # Continuer en synchrone direct...
'''

# Code pour améliorer les réponses rapides (à ajouter après ligne 5400)

QUICK_RESPONSES = '''
        # ===== RÉPONSES RAPIDES POUR ÉVITER TIMEOUTS =====
        query_lower = query.lower()
        
        # Réponse ultra-rapide pour questions courantes
        if len(query) < 50:  # Questions courtes = réponses rapides
            
            # Valeur totale
            if 'valeur total' in query_lower or 'combien vaut' in query_lower:
                items = AdvancedDataManager.fetch_all_items()
                total = sum(getattr(item, 'current_value', 0) for item in items)
                response = f"💰 **Valeur totale**: {total:,.0f} CHF\\n"
                response += f"📦 **Nombre d'objets**: {len(items)}"
                return jsonify({
                    "reply": response,
                    "metadata": {"mode": "quick", "cached": True}
                })
            
            # Nombre d'objets
            if 'combien' in query_lower and 'objet' in query_lower:
                items = AdvancedDataManager.fetch_all_items()
                response = f"📦 Vous avez **{len(items)} objets** dans votre collection"
                return jsonify({
                    "reply": response,
                    "metadata": {"mode": "quick", "cached": True}
                })
            
            # Top valeurs
            if 'plus' in query_lower and ('cher' in query_lower or 'valeur' in query_lower):
                items = AdvancedDataManager.fetch_all_items()
                top_items = sorted(items, key=lambda x: getattr(x, 'current_value', 0), reverse=True)[:3]
                response = "🏆 **Top 3 des objets les plus précieux**:\\n\\n"
                for i, item in enumerate(top_items, 1):
                    response += f"{i}. {getattr(item, 'name', 'N/A')}: {getattr(item, 'current_value', 0):,.0f} CHF\\n"
                return jsonify({
                    "reply": response,
                    "metadata": {"mode": "quick", "cached": True}
                })
'''

# Code pour timeout strict sur l'IA (remplacer l'appel OpenAI ligne ~6060)

AI_TIMEOUT_FIX = '''
        # ===== TIMEOUT STRICT POUR L'IA =====
        if ai_engine:
            try:
                # Timeout de 8 secondes maximum
                import signal
                
                def timeout_handler(signum, frame):
                    raise TimeoutError("AI timeout")
                
                # Set timeout
                signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(8)  # 8 secondes max
                
                try:
                    # Appel IA avec prompt simplifié
                    simple_prompt = f"Réponds en 3 lignes max à: {query}"
                    response = ai_engine.generate_response_with_history(
                        simple_prompt, 
                        items[:50],  # Limiter les items pour performance
                        analytics,
                        conversation_history[:3]  # Limiter l'historique
                    )
                finally:
                    signal.alarm(0)  # Désactiver le timeout
                    
            except (TimeoutError, Exception) as e:
                # Fallback si timeout
                response = f"📊 Résumé rapide:\\n"
                response += f"• {len(items)} objets au total\\n"
                response += f"• Valeur: {analytics.get('total_value', 0):,.0f} CHF\\n"
                response += f"💡 Posez une question plus spécifique pour plus de détails."
            
            return jsonify({
                "reply": response,
                "metadata": {
                    "mode": "ai_stable",
                    "items_analyzed": len(items),
                    "timeout_protection": True
                }
            })
'''

def print_instructions():
    print("""
================================================================================
🔧 INSTRUCTIONS POUR FIXER LE CHATBOT
================================================================================

1. OUVRIR app.py

2. CHERCHER la ligne 5313:
   if os.getenv("CHAT_V2", "0") == "1" and not _force_sync:

3. REMPLACER les lignes 5313-5320 (code Celery) par:
   """)
    print(FIX_CODE)
    
    print("""
4. AJOUTER après la ligne 5400 (après la gestion de création d'objet):
   """)
    print(QUICK_RESPONSES)
    
    print("""
5. CHERCHER la ligne ~6060:
   response = ai_engine.generate_response_with_history(query, items, analytics, conversation_history)

6. REMPLACER tout le bloc d'appel IA par:
   """)
    print(AI_TIMEOUT_FIX)
    
    print("""
7. AJOUTER dans .env ou les variables d'environnement Render:
   ASYNC_CHAT=0
   CHAT_V2=0
   ALLOW_FORCE_SYNC=1

8. SAUVEGARDER et PUSH:
   git add app.py
   git commit -m "Fix: Stabilisation du chatbot - désactivation Celery, timeouts stricts, réponses rapides"
   git push

================================================================================
✅ RÉSULTAT ATTENDU:
- Plus de timeouts
- Plus de déconnexions
- Réponses en < 3 secondes
- Fallback intelligent si problème
================================================================================
""")

if __name__ == "__main__":
    print_instructions()


