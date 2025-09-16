
# ========== CHATBOT AMÉLIORÉ V2 - STABLE ET INTELLIGENT ==========

@app.route("/api/chatbot", methods=["POST"])
def chatbot():
    """Chatbot AMÉLIORÉ v2.0 - Stable, rapide et intelligent"""
    try:
        start_time = time.time()
        data = request.get_json()
        if not data:
            return jsonify({"error": "Données requises"}), 400
        
        query = data.get("message", "").strip()
        if not query:
            return jsonify({"error": "Message requis"}), 400
        
        # NOUVEAU: Détection intelligente d'intention
        intent = detect_chat_intent(query)
        
        # DÉSACTIVÉ: Celery pour éviter les timeouts
        # Traitement SYNCHRONE direct pour stabilité
        
        # Session et historique
        session_id = data.get("session_id", str(uuid.uuid4()))
        history = data.get("history", [])[-5:]  # Limiter l'historique
        
        # Récupérer les items avec cache
        items = smart_cache.get('items')
        if items is None:
            items = AdvancedDataManager.fetch_all_items()
            smart_cache.set('items', items, ttl=60)
        
        # Analyse rapide des données
        analytics = AdvancedDataManager.calculate_advanced_analytics(items)
        
        # AMÉLIORATION 1: Réponses rapides pour questions simples
        quick_response = get_quick_response(query, items, analytics)
        if quick_response:
            return jsonify({
                "reply": quick_response,
                "metadata": {
                    "mode": "quick",
                    "response_time": time.time() - start_time,
                    "intent": intent
                }
            })
        
        # AMÉLIORATION 2: Utiliser l'IA améliorée avec timeout court
        try:
            # Import des nouvelles capacités
            from enhanced_chatbot_manager import EnhancedChatbotManager
            enhanced_bot = EnhancedChatbotManager()
            
            # Analyse d'intention avancée
            intent_analysis = enhanced_bot.analyze_user_intent(query)
            
            # Générer suggestions intelligentes
            context = {
                "last_category": get_last_category(items),
                "high_value_items": len([i for i in items if getattr(i, 'current_value', 0) > 100000]) > 0
            }
            suggestions = enhanced_bot.generate_smart_suggestions(context)
            
            # Si demande de prédiction
            if intent_analysis['intents'].get('prediction'):
                # Obtenir l'item concerné
                item_name = extract_item_name(query)
                item = next((i for i in items if item_name.lower() in getattr(i, 'name', '').lower()), None)
                if item:
                    prediction = enhanced_bot.predict_future_value({
                        'name': getattr(item, 'name', ''),
                        'category': getattr(item, 'category', ''),
                        'current_value': getattr(item, 'current_value', 0)
                    })
                    
                    response = format_prediction_response(prediction, item)
                    return jsonify({
                        "reply": response,
                        "suggestions": suggestions,
                        "metadata": {
                            "mode": "prediction",
                            "response_time": time.time() - start_time
                        }
                    })
            
            # Si demande d'export
            if intent_analysis['intents'].get('export'):
                return jsonify({
                    "reply": "📥 Export disponible ! Utilisez les boutons ci-dessous:",
                    "actions": [
                        {"type": "export_pdf", "label": "📄 Télécharger PDF"},
                        {"type": "export_excel", "label": "📊 Télécharger Excel"}
                    ],
                    "suggestions": suggestions,
                    "metadata": {"mode": "export"}
                })
            
        except ImportError:
            # Fallback si enhanced_chatbot_manager n'existe pas
            pass
        except Exception as e:
            logger.warning(f"Enhanced chatbot error: {e}")
        
        # AMÉLIORATION 3: Utiliser GPT avec timeout strict
        if ai_engine:
            try:
                # Timeout de 10 secondes max
                with timeout(10):
                    response = generate_smart_response(query, items, analytics, history)
            except TimeoutError:
                response = "⚡ Réponse rapide: J'ai {} objets d'une valeur totale de {:,.0f} CHF dans votre collection.".format(
                    len(items),
                    sum(getattr(i, 'current_value', 0) for i in items)
                )
            
            return jsonify({
                "reply": response,
                "suggestions": get_contextual_suggestions(query, response),
                "metadata": {
                    "items_analyzed": len(items),
                    "mode": "ai_optimized",
                    "response_time": time.time() - start_time,
                    "stable": True
                }
            })
        else:
            # Fallback intelligent sans IA
            return jsonify({
                "reply": generate_fallback_response(query, items, analytics),
                "metadata": {
                    "mode": "fallback",
                    "response_time": time.time() - start_time
                }
            })
    
    except Exception as e:
        logger.error(f"Erreur chatbot: {e}")
        # Réponse d'erreur informative
        return jsonify({
            "reply": "😊 Je rencontre un petit souci technique. En attendant, voici un résumé: Vous avez {} objets dans votre collection.".format(
                len(AdvancedDataManager.fetch_all_items()) if 'items' not in locals() else len(items)
            ),
            "error": str(e),
            "metadata": {"mode": "error_recovery"}
        }), 200  # Retour 200 pour éviter les erreurs côté client


def detect_chat_intent(query: str) -> str:
    """Détecte rapidement l'intention de l'utilisateur"""
    query_lower = query.lower()
    
    if any(word in query_lower for word in ['valeur', 'total', 'combien', 'prix']):
        return 'value_analysis'
    elif any(word in query_lower for word in ['ajouter', 'créer', 'nouveau']):
        return 'create_item'
    elif any(word in query_lower for word in ['vendre', 'vente', 'sold']):
        return 'sales_analysis'
    elif any(word in query_lower for word in ['prédire', 'futur', 'sera', 'évolution']):
        return 'prediction'
    elif any(word in query_lower for word in ['export', 'pdf', 'excel', 'rapport']):
        return 'export'
    elif any(word in query_lower for word in ['meilleur', 'top', 'plus']):
        return 'top_items'
    else:
        return 'general'


def get_quick_response(query: str, items: list, analytics: dict) -> str:
    """Génère des réponses rapides pour les questions simples"""
    query_lower = query.lower()
    
    # Questions sur la valeur totale
    if 'valeur total' in query_lower or 'combien vaut' in query_lower:
        total_value = analytics.get('total_value', 0)
        return f"💰 **Valeur totale de votre collection**: {total_value:,.0f} CHF\n\n"                f"📊 Répartition:\n"                f"• {analytics.get('available_count', 0)} objets disponibles\n"                f"• {analytics.get('sold_count', 0)} objets vendus\n"                f"• {analytics.get('for_sale_count', 0)} objets en vente"
    
    # Questions sur le nombre d'objets
    if 'combien' in query_lower and ('objet' in query_lower or 'item' in query_lower):
        return f"📦 Vous avez **{len(items)} objets** dans votre collection:\n\n"                f"• Disponibles: {analytics.get('available_count', 0)}\n"                f"• En vente: {analytics.get('for_sale_count', 0)}\n"                f"• Vendus: {analytics.get('sold_count', 0)}"
    
    # Questions sur les ventes
    if 'vente' in query_lower or 'vendu' in query_lower:
        sold_value = analytics.get('total_sold_value', 0)
        sold_count = analytics.get('sold_count', 0)
        return f"💸 **Analyse des ventes**:\n\n"                f"• Objets vendus: {sold_count}\n"                f"• Valeur totale des ventes: {sold_value:,.0f} CHF\n"                f"• Plus-value réalisée: {analytics.get('realized_gains', 0):,.0f} CHF"
    
    # Questions sur les catégories
    for category in ['voiture', 'montre', 'bateau', 'action', 'immobilier']:
        if category in query_lower:
            cat_items = [i for i in items if category in getattr(i, 'category', '').lower()]
            if cat_items:
                cat_value = sum(getattr(i, 'current_value', 0) for i in cat_items)
                return f"🏷️ **{category.capitalize()}s dans votre collection**:\n\n"                        f"• Nombre: {len(cat_items)}\n"                        f"• Valeur totale: {cat_value:,.0f} CHF\n"                        f"• Valeur moyenne: {cat_value/len(cat_items):,.0f} CHF"
    
    return None


def generate_smart_response(query: str, items: list, analytics: dict, history: list) -> str:
    """Génère une réponse intelligente avec l'IA"""
    # Limiter le contexte pour éviter les timeouts
    context = {
        "total_items": len(items),
        "total_value": analytics.get('total_value', 0),
        "categories": analytics.get('categories_summary', {}),
        "top_items": analytics.get('top_valued_items', [])[:3]
    }
    
    # Prompt optimisé pour réponses rapides
    prompt = f"""Tu es l'assistant BONVIN. Réponds de manière CONCISE et STRUCTURÉE.

Question: {query}

Contexte:
- Total objets: {context['total_items']}
- Valeur totale: {context['total_value']:,.0f} CHF
- Catégories: {', '.join(context['categories'].keys()) if context['categories'] else 'N/A'}

Règles:
1. Maximum 5 lignes de réponse
2. Utilise des bullets points
3. Inclus des émojis pertinents
4. Sois précis avec les chiffres
5. Termine par une suggestion d'action"""
    
    try:
        if ai_engine and hasattr(ai_engine, 'openai_client'):
            response = ai_engine.openai_client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": "Tu es un assistant de gestion de patrimoine. Sois concis et précis."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=300,
                temperature=0.7,
                timeout=10
            )
            return response.choices[0].message.content
    except Exception as e:
        logger.error(f"AI response error: {e}")
    
    return generate_fallback_response(query, items, analytics)


def generate_fallback_response(query: str, items: list, analytics: dict) -> str:
    """Génère une réponse de fallback intelligente sans IA"""
    total_value = analytics.get('total_value', 0)
    total_items = len(items)
    
    response = f"📊 **Résumé de votre collection**\n\n"
    response += f"• **{total_items} objets** au total\n"
    response += f"• **Valeur totale**: {total_value:,.0f} CHF\n"
    
    # Ajouter les top catégories
    categories = analytics.get('categories_summary', {})
    if categories:
        top_cats = sorted(categories.items(), key=lambda x: x[1].get('total_value', 0), reverse=True)[:3]
        response += f"\n**Top catégories**:\n"
        for cat, data in top_cats:
            response += f"• {cat}: {data.get('count', 0)} objets ({data.get('total_value', 0):,.0f} CHF)\n"
    
    response += f"\n💡 *Posez-moi une question spécifique pour plus de détails !*"
    
    return response


def get_contextual_suggestions(query: str, response: str) -> list:
    """Génère des suggestions contextuelles"""
    suggestions = []
    
    if 'valeur' in query.lower():
        suggestions.extend([
            "Évolution sur 6 mois",
            "Top 5 des plus values",
            "Répartition par catégorie"
        ])
    elif 'vente' in query.lower():
        suggestions.extend([
            "Objets à fort potentiel",
            "Analyse des plus-values",
            "Stratégie de vente optimale"
        ])
    else:
        suggestions.extend([
            "Valeur totale du portefeuille",
            "Objets les plus précieux",
            "Performance des investissements"
        ])
    
    return suggestions[:3]


def format_prediction_response(prediction: dict, item) -> str:
    """Formate une réponse de prédiction"""
    response = f"🔮 **Prédiction pour {getattr(item, 'name', 'cet objet')}**\n\n"
    response += f"Valeur actuelle: {getattr(item, 'current_value', 0):,.0f} CHF\n\n"
    response += "**Scénarios à 12 mois:**\n"
    response += f"• 📉 Pessimiste: {prediction['pessimistic']:,.0f} CHF\n"
    response += f"• 📊 Réaliste: {prediction['realistic']:,.0f} CHF\n"
    response += f"• 📈 Optimiste: {prediction['optimistic']:,.0f} CHF\n\n"
    response += f"Confiance: {prediction['confidence']:.0%}"
    
    return response


def extract_item_name(query: str) -> str:
    """Extrait le nom de l'objet de la requête"""
    # Logique simple d'extraction
    words = query.lower().split()
    # Chercher après "de", "mon", "ma", etc.
    for i, word in enumerate(words):
        if word in ['de', 'mon', 'ma', 'mes', 'le', 'la', 'les']:
            if i + 1 < len(words):
                return ' '.join(words[i+1:])
    return query


def get_last_category(items: list) -> str:
    """Obtient la dernière catégorie utilisée"""
    if items:
        # Trier par date de modification si disponible
        sorted_items = sorted(items, key=lambda x: getattr(x, 'updated_at', ''), reverse=True)
        if sorted_items:
            return getattr(sorted_items[0], 'category', '')
    return ''


# Fonction de timeout pour éviter les blocages
from contextlib import contextmanager
import signal

@contextmanager
def timeout(seconds):
    def timeout_handler(signum, frame):
        raise TimeoutError()
    
    # Setup
    old_handler = signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(seconds)
    
    try:
        yield
    finally:
        # Cleanup
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)
