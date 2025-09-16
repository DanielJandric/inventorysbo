"""
Tests complets pour le chatbot amélioré BONVIN
Démonstration de toutes les nouvelles fonctionnalités
"""

import os
import sys
import json
import asyncio
from datetime import datetime, timedelta

# Import des modules améliorés
from enhanced_chatbot_manager import EnhancedChatbotManager, ConversationOptimizer
from chatbot_visualizations import ChatbotVisualizer, ReportGenerator
from prompts.enhanced_prompts import (
    get_contextual_prompt, 
    format_response_with_template,
    get_smart_suggestions,
    enhance_with_markdown
)

# Configuration
os.environ['OPENAI_API_KEY'] = os.getenv('OPENAI_API_KEY', '')

def test_intent_analysis():
    """Test l'analyse d'intention avancée"""
    print("\n" + "="*50)
    print("TEST 1: Analyse d'Intention")
    print("="*50)
    
    manager = EnhancedChatbotManager()
    
    test_queries = [
        "Quelle est la valeur totale de ma collection ?",
        "Ajoute une Ferrari 488 GTB achetée 350000 CHF",
        "Exporte mon inventaire en PDF",
        "Prédis la valeur de mes montres dans 2 ans",
        "Recommande-moi les meilleures ventes à faire",
        "Compare ma performance avec le S&P 500"
    ]
    
    for query in test_queries:
        print(f"\n📝 Query: {query}")
        analysis = manager.analyze_user_intent(query)
        
        print(f"  🎯 Intentions détectées:")
        for intent, detected in analysis['intents'].items():
            if detected:
                print(f"    ✓ {intent}")
        
        print(f"  📊 Confiance: {analysis['confidence']:.2%}")
        print(f"  🏷️ Entités: {analysis['entities']}")
        print(f"  📈 Complexité: {analysis['complexity']}")


def test_smart_suggestions():
    """Test les suggestions intelligentes"""
    print("\n" + "="*50)
    print("TEST 2: Suggestions Intelligentes")
    print("="*50)
    
    manager = EnhancedChatbotManager()
    
    contexts = [
        {
            "last_category": "Actions",
            "recent_sale": False,
            "high_value_items": True
        },
        {
            "last_category": "Voitures", 
            "trending_up": True,
            "recent_sale": True
        }
    ]
    
    for i, context in enumerate(contexts, 1):
        print(f"\n🔍 Contexte {i}: {context}")
        suggestions = manager.generate_smart_suggestions(context)
        print("💡 Suggestions générées:")
        for j, suggestion in enumerate(suggestions, 1):
            print(f"  {j}. {suggestion}")


def test_value_predictions():
    """Test les prédictions de valeur"""
    print("\n" + "="*50)
    print("TEST 3: Prédictions de Valeur")
    print("="*50)
    
    manager = EnhancedChatbotManager()
    
    test_items = [
        {
            "name": "Porsche 911 GT3",
            "category": "Voitures",
            "current_value": 250000
        },
        {
            "name": "Rolex Daytona",
            "category": "Montres",
            "current_value": 45000
        },
        {
            "name": "Apple Inc.",
            "category": "Actions",
            "current_value": 100000
        }
    ]
    
    for item in test_items:
        print(f"\n📦 Item: {item['name']}")
        print(f"  Catégorie: {item['category']}")
        print(f"  Valeur actuelle: {item['current_value']:,} CHF")
        
        predictions = manager.predict_future_value(item, months=12)
        
        print(f"\n  📈 Prédictions à 12 mois:")
        print(f"    • Pessimiste: {predictions['pessimistic']:,.0f} CHF")
        print(f"    • Réaliste: {predictions['realistic']:,.0f} CHF")
        print(f"    • Optimiste: {predictions['optimistic']:,.0f} CHF")
        print(f"    • Confiance: {predictions['confidence']:.0%}")
        print(f"  \n  📊 Facteurs influençants:")
        for factor in predictions['factors']:
            print(f"    - {factor}")


def test_executive_summary():
    """Test la génération de résumé exécutif"""
    print("\n" + "="*50)
    print("TEST 4: Résumé Exécutif")
    print("="*50)
    
    manager = EnhancedChatbotManager()
    
    # Données de test
    test_items = [
        {"name": "Ferrari F8 Tributo", "category": "Voitures", "current_value": 450000},
        {"name": "Patek Philippe Nautilus", "category": "Montres", "current_value": 120000},
        {"name": "Appartement Genève", "category": "Immobilier", "current_value": 2500000},
        {"name": "Tableau Picasso", "category": "Art", "current_value": 800000},
        {"name": "Portfolio Actions", "category": "Actions", "current_value": 500000}
    ]
    
    analytics = {
        "total_value": sum(item['current_value'] for item in test_items),
        "average_value": sum(item['current_value'] for item in test_items) / len(test_items),
        "unrealized_gains": 250000,
        "average_roi": 15.5,
        "turnover_rate": 8.2
    }
    
    summary = manager.generate_executive_summary(test_items, analytics)
    print(summary)


def test_portfolio_metrics():
    """Test le calcul des métriques de portefeuille"""
    print("\n" + "="*50)
    print("TEST 5: Métriques de Portefeuille")
    print("="*50)
    
    manager = EnhancedChatbotManager()
    
    test_items = [
        {"current_value": 100000},
        {"current_value": 250000},
        {"current_value": 75000},
        {"current_value": 180000},
        {"current_value": 320000}
    ]
    
    metrics = manager.calculate_portfolio_metrics(test_items)
    
    print("\n📊 Métriques calculées:")
    print(f"  • Valeur moyenne: {metrics.get('average_value', 0):,.0f} CHF")
    print(f"  • Écart-type: {metrics.get('std_deviation', 0):,.0f}")
    print(f"  • Value at Risk (5%): {metrics.get('value_at_risk', 0):,.0f} CHF")
    print(f"  • Sharpe Ratio: {metrics.get('sharpe_ratio', 0):.3f}")


def test_conversation_optimizer():
    """Test l'optimiseur de conversation"""
    print("\n" + "="*50)
    print("TEST 6: Optimisation de Conversation")
    print("="*50)
    
    optimizer = ConversationOptimizer()
    
    # Test d'optimisation de réponse
    response = "Votre collection vaut 3500000 CHF avec 25000 de plus-value."
    context = {"category": "Voitures", "success": True}
    
    optimized = optimizer.optimize_response(response, context)
    print(f"\n📝 Réponse originale:\n{response}")
    print(f"\n✨ Réponse optimisée:\n{optimized}")
    
    # Test de suggestions de suivi
    conversation = [
        {"role": "user", "content": "Quelle est la valeur de mes actions ?"},
        {"role": "assistant", "content": "Vos actions valent 500000 CHF au total."}
    ]
    
    follow_ups = optimizer.suggest_follow_up_questions(conversation)
    print(f"\n💬 Questions de suivi suggérées:")
    for q in follow_ups:
        print(f"  • {q}")


def test_visualizations():
    """Test la génération de visualisations"""
    print("\n" + "="*50)
    print("TEST 7: Visualisations")
    print("="*50)
    
    visualizer = ChatbotVisualizer()
    
    # Données de test
    test_items = [
        {"category": "Voitures", "current_value": 850000},
        {"category": "Montres", "current_value": 320000},
        {"category": "Actions", "current_value": 500000},
        {"category": "Immobilier", "current_value": 2500000},
        {"category": "Art", "current_value": 450000}
    ]
    
    # Test génération graphique camembert
    chart_base64 = visualizer.generate_portfolio_chart(test_items)
    if chart_base64:
        print("✅ Graphique de portefeuille généré avec succès")
        print(f"   Taille de l'image encodée: {len(chart_base64)} caractères")
    
    # Test génération graphique de performance
    performance_data = [
        {"date": "Jan", "value": 4000000},
        {"date": "Fév", "value": 4100000},
        {"date": "Mar", "value": 4250000},
        {"date": "Avr", "value": 4200000},
        {"date": "Mai", "value": 4400000},
        {"date": "Jun", "value": 4620000}
    ]
    
    perf_chart = visualizer.generate_performance_chart(performance_data)
    if perf_chart:
        print("✅ Graphique de performance généré avec succès")


def test_report_generation():
    """Test la génération de rapports"""
    print("\n" + "="*50)
    print("TEST 8: Génération de Rapports")
    print("="*50)
    
    generator = ReportGenerator()
    
    # Données de test complètes
    report_data = {
        "total_value": 4620000,
        "total_items": 45,
        "ytd_performance": 12.5,
        "unrealized_gains": 520000,
        "categories": {
            "Voitures": 1200000,
            "Montres": 450000,
            "Actions": 470000,
            "Immobilier": 2500000
        },
        "top_items": [
            {"name": "Appartement Genève", "category": "Immobilier", "current_value": 2500000},
            {"name": "Ferrari F8 Tributo", "category": "Voitures", "current_value": 450000},
            {"name": "Porsche 911 GT3", "category": "Voitures", "current_value": 350000},
            {"name": "Collection Rolex", "category": "Montres", "current_value": 280000}
        ],
        "recommendations": [
            "Diversifier vers les actifs technologiques",
            "Réaliser les plus-values sur l'immobilier",
            "Renforcer la position en art contemporain"
        ]
    }
    
    # Générer le PDF
    pdf_bytes = generator.generate_portfolio_report(report_data)
    
    if pdf_bytes:
        print(f"✅ Rapport PDF généré avec succès")
        print(f"   Taille du document: {len(pdf_bytes):,} octets")
        
        # Sauvegarder pour test
        with open("test_report.pdf", "wb") as f:
            f.write(pdf_bytes)
        print("   📄 Rapport sauvegardé: test_report.pdf")
    
    # Test export Excel
    test_items = [
        {
            "name": "Ferrari F8",
            "category": "Voitures",
            "current_value": 450000,
            "acquisition_price": 380000
        },
        {
            "name": "Rolex Daytona",
            "category": "Montres", 
            "current_value": 65000,
            "acquisition_price": 45000
        }
    ]
    
    excel_bytes = generator.generate_excel_export(test_items)
    
    if excel_bytes:
        print(f"✅ Export Excel généré avec succès")
        print(f"   Taille du fichier: {len(excel_bytes):,} octets")


def test_async_processing():
    """Test le traitement asynchrone"""
    print("\n" + "="*50)
    print("TEST 9: Traitement Asynchrone")
    print("="*50)
    
    manager = EnhancedChatbotManager()
    
    async def run_async_test():
        request = {
            "need_analysis": True,
            "need_prediction": True,
            "need_recommendations": True
        }
        
        print("⏳ Lancement du traitement parallèle...")
        start_time = datetime.now()
        
        result = await manager.process_async_request(request)
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        print(f"✅ Traitement terminé en {duration:.2f} secondes")
        print(f"   Résultats: {list(result.keys())}")
    
    # Exécuter le test async
    asyncio.run(run_async_test())


def test_enhanced_prompts():
    """Test les prompts améliorés"""
    print("\n" + "="*50)
    print("TEST 10: Prompts Améliorés")
    print("="*50)
    
    # Test prompt contextuel
    context = {
        "category": "Actions",
        "detailed_analysis": True,
        "comparison_needed": True
    }
    
    prompt = get_contextual_prompt("analysis", context)
    print("📝 Prompt généré pour analyse d'actions:")
    print(prompt[:500] + "...")
    
    # Test template de réponse
    data = {
        "item_name": "Ferrari F8 Tributo",
        "current_value": 450000,
        "evolution": 15.5,
        "period": "6 mois",
        "projection": 520000,
        "factor1": "Rareté du modèle",
        "factor2": "État exceptionnel",
        "factor3": "Demande croissante",
        "recommendation": "Conserver - potentiel d'appréciation important"
    }
    
    formatted = format_response_with_template("value_analysis", data)
    print("\n✨ Réponse formatée avec template:")
    print(formatted)
    
    # Test suggestions intelligentes
    suggestions = get_smart_suggestions("valeur de mes actions", context)
    print("\n💡 Suggestions contextuelles:")
    for s in suggestions:
        print(f"  • {s}")


def main():
    """Exécute tous les tests"""
    print("\n" + "🚀 " + "="*50)
    print("   TESTS DU CHATBOT AMÉLIORÉ BONVIN")
    print("   Version 2.0 - Fonctionnalités Avancées")
    print("="*50 + " 🚀")
    
    tests = [
        test_intent_analysis,
        test_smart_suggestions,
        test_value_predictions,
        test_executive_summary,
        test_portfolio_metrics,
        test_conversation_optimizer,
        test_visualizations,
        test_report_generation,
        test_async_processing,
        test_enhanced_prompts
    ]
    
    for test_func in tests:
        try:
            test_func()
        except Exception as e:
            print(f"\n❌ Erreur dans {test_func.__name__}: {e}")
    
    print("\n" + "="*50)
    print("✅ TOUS LES TESTS TERMINÉS")
    print("="*50)


if __name__ == "__main__":
    main()
