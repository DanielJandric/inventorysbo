"""
Prompts améliorés pour le chatbot BONVIN
Optimisés pour GPT-5 et GPT-4
"""

SYSTEM_PROMPTS = {
    "main": """Tu es l'Assistant IA BONVIN, un expert en gestion de patrimoine et collections de luxe.

PERSONNALITÉ:
- Professionnel mais chaleureux
- Précis dans les analyses financières
- Proactif dans les recommandations
- Utilise des émojis de manière pertinente (📊 📈 💡 ✅ ⚠️)

CAPACITÉS:
1. Analyse approfondie des collections (valeur, performance, tendances)
2. Recherche sémantique intelligente dans l'inventaire
3. Recommandations stratégiques personnalisées
4. Prédictions basées sur les données historiques
5. Génération de rapports professionnels

RÈGLES:
- Toujours fournir des chiffres précis quand disponibles
- Structurer les réponses avec du Markdown
- Proposer des actions concrètes
- Anticiper les besoins de suivi
- Utiliser le français sauf si demandé autrement

FORMAT PRÉFÉRÉ:
1. **Résumé** : Réponse directe à la question
2. **Détails** : Analyse approfondie si pertinent  
3. **Recommandations** : Actions suggérées
4. **Prochaines étapes** : Questions de suivi pertinentes""",
    
    "analysis": """Tu es un analyste financier expert spécialisé dans les actifs de collection.

MISSION: Fournir des analyses détaillées et actionnables sur la collection.

FOCUS:
- Performance financière (ROI, plus-values, tendances)
- Diversification et gestion des risques
- Opportunités de marché
- Optimisation fiscale
- Stratégies de sortie

TOUJOURS INCLURE:
- Chiffres clés avec comparaisons
- Graphiques conceptuels en ASCII si pertinent
- Top 3 des points d'attention
- Recommandations priorisées""",
    
    "market_expert": """Tu es un expert des marchés spécialisé dans les actifs de collection de luxe.

EXPERTISE:
- Voitures de collection (Ferrari, Porsche, etc.)
- Montres de luxe (Rolex, Patek Philippe, etc.)
- Art et antiquités
- Immobilier de prestige
- Actions et investissements alternatifs

ANALYSE DE MARCHÉ:
- Tendances actuelles et futures
- Valorisations comparatives
- Timing optimal pour achat/vente
- Facteurs macro-économiques
- Événements impactant les prix

STYLE:
- Insights pointus mais accessibles
- Données factuelles avec sources implicites
- Projections prudentes mais informées""",
    
    "creative_assistant": """Tu es un assistant créatif pour la gestion de collections.

CAPACITÉS CRÉATIVES:
- Suggestions d'acquisitions uniques
- Stratégies de mise en valeur
- Storytelling autour des objets
- Organisation d'événements (expositions, ventes)
- Marketing de la collection

APPROCHE:
- Penser "outside the box"
- Proposer des synergies inattendues
- Valoriser l'histoire et l'émotion
- Créer des expériences mémorables"""
}

RESPONSE_TEMPLATES = {
    "value_analysis": """📊 **Analyse de Valeur - {item_name}**

**Valeur Actuelle**: {current_value} CHF
**Évolution**: {evolution}% sur {period}
**Projection 12 mois**: {projection} CHF

**Facteurs Clés**:
• {factor1}
• {factor2}
• {factor3}

💡 **Recommandation**: {recommendation}
""",
    
    "portfolio_summary": """## 📈 Résumé du Portefeuille

**Valeur Totale**: {total_value} CHF
**Nombre d'Actifs**: {asset_count}
**Performance YTD**: {ytd_performance}%

### Répartition par Catégorie
{category_breakdown}

### Top Performers
1. {top1}
2. {top2}
3. {top3}

### Points d'Attention
{attention_points}

### Actions Recommandées
{recommended_actions}
""",
    
    "market_insight": """## 🌍 Insight de Marché - {category}

**Tendance**: {trend_emoji} {trend_description}
**Volatilité**: {volatility_level}
**Momentum**: {momentum}

### Analyse
{analysis}

### Opportunités
{opportunities}

### Risques
{risks}

💡 **Notre Avis**: {expert_opinion}
""",
    
    "quick_answer": """
{emoji} **{title}**

{main_answer}

{details}

{suggestion}
"""
}

ENHANCED_QUESTIONS = {
    "analysis": [
        "Quelle est la performance de ma collection sur les 6 derniers mois ?",
        "Quels sont mes actifs les plus rentables ?",
        "Comment optimiser la diversification de mon portefeuille ?",
        "Quelle est ma plus-value latente totale ?",
        "Analyse comparative avec les indices de marché"
    ],
    
    "strategy": [
        "Quels objets devrais-je vendre en priorité ?",
        "Quel est le meilleur moment pour vendre mes montres ?",
        "Comment réduire mon exposition au risque ?",
        "Stratégie d'acquisition pour 2025",
        "Plan de sortie optimal sur 5 ans"
    ],
    
    "insights": [
        "Tendances du marché des voitures de collection",
        "Impact de l'inflation sur ma collection",
        "Prévisions pour le marché de l'art",
        "Analyse sectorielle des montres de luxe",
        "Corrélation entre mes actifs"
    ],
    
    "operations": [
        "Ajouter une nouvelle acquisition",
        "Mettre à jour les prix de mes actions",
        "Exporter mon inventaire en PDF",
        "Créer un rapport mensuel",
        "Planifier une vente aux enchères"
    ]
}

def get_contextual_prompt(intent: str, context: dict) -> str:
    """
    Retourne un prompt optimisé selon l'intention et le contexte
    """
    base_prompt = SYSTEM_PROMPTS.get(intent, SYSTEM_PROMPTS["main"])
    
    # Enrichissement contextuel
    if context.get("category"):
        base_prompt += f"\n\nFOCUS CATÉGORIE: {context['category']}"
    
    if context.get("time_sensitive"):
        base_prompt += "\n\n⏰ URGENT: Réponse rapide et actionnable requise."
    
    if context.get("detailed_analysis"):
        base_prompt += "\n\n📊 ANALYSE APPROFONDIE: Fournir des détails complets avec métriques."
    
    if context.get("comparison_needed"):
        base_prompt += "\n\n🔄 COMPARAISON: Inclure des benchmarks et références de marché."
    
    return base_prompt

def format_response_with_template(template_name: str, data: dict) -> str:
    """
    Formate une réponse avec un template prédéfini
    """
    template = RESPONSE_TEMPLATES.get(template_name, RESPONSE_TEMPLATES["quick_answer"])
    
    try:
        return template.format(**data)
    except KeyError as e:
        # Retour gracieux si des clés manquent
        return template.replace("{" + str(e).strip("'") + "}", "N/A")

def get_smart_suggestions(last_interaction: str, context: dict) -> list:
    """
    Génère des suggestions intelligentes basées sur le contexte
    """
    suggestions = []
    
    # Analyse du dernier message
    keywords = last_interaction.lower().split()
    
    if any(word in keywords for word in ["valeur", "prix", "worth"]):
        suggestions.extend([
            "Évolution sur 1 an ?",
            "Comparer avec l'inflation",
            "Top 5 des plus values"
        ])
    
    if any(word in keywords for word in ["vendre", "sell", "vente"]):
        suggestions.extend([
            "Timing optimal de vente",
            "Estimation des frais",
            "Impact fiscal"
        ])
    
    if any(word in keywords for word in ["acheter", "buy", "acquisition"]):
        suggestions.extend([
            "Budget disponible ?",
            "Opportunités du moment",
            "Analyse risque/rendement"
        ])
    
    # Suggestions contextuelles
    if context.get("category") == "Actions":
        suggestions.extend([
            "Dividendes attendus",
            "Comparer au S&P 500",
            "Analyse sectorielle"
        ])
    elif context.get("category") == "Voitures":
        suggestions.extend([
            "Cote Argus",
            "Frais d'entretien annuels",
            "Modèles similaires sur le marché"
        ])
    
    # Limiter et diversifier
    return list(set(suggestions))[:4]

def enhance_with_markdown(text: str) -> str:
    """
    Améliore le formatage Markdown d'un texte
    """
    # Mettre en gras les montants
    text = re.sub(r'(\d+(?:\.\d+)?(?:\s*)?(?:CHF|EUR|USD|k|M))', r'**\1**', text)
    
    # Formater les pourcentages
    text = re.sub(r'(\d+(?:\.\d+)?%)', r'**\1**', text)
    
    # Ajouter des puces pour les listes
    lines = text.split('\n')
    formatted_lines = []
    for line in lines:
        if line.strip().startswith('-'):
            formatted_lines.append('• ' + line.strip()[1:].strip())
        else:
            formatted_lines.append(line)
    
    return '\n'.join(formatted_lines)

# Optimisations spécifiques pour GPT-5
GPT5_OPTIMIZATIONS = {
    "reasoning_mode": "high",
    "response_format": "structured",
    "temperature": 0.7,
    "max_tokens": 2000,
    "stop_sequences": ["---", "User:", "Question:"],
    "presence_penalty": 0.1,
    "frequency_penalty": 0.1
}

# Cache de prompts fréquents
CACHED_PROMPTS = {}

def get_cached_or_generate_prompt(key: str, generator_func, *args, **kwargs):
    """
    Utilise le cache pour les prompts fréquents
    """
    if key not in CACHED_PROMPTS:
        CACHED_PROMPTS[key] = generator_func(*args, **kwargs)
    return CACHED_PROMPTS[key]
