"""
Tests pour le Markets Chat Worker amélioré v2.0
Démonstration de toutes les nouvelles fonctionnalités
"""

import os
import sys
import json
from datetime import datetime

# Import des modules améliorés
from enhanced_markets_chat_worker import (
    EnhancedMarketsChatWorker,
    get_enhanced_markets_chat_worker
)
from markets_visualizations import MarketsVisualizer

# Configuration
os.environ['OPENAI_API_KEY'] = os.getenv('OPENAI_API_KEY', '')


def test_market_intent_analysis():
    """Test l'analyse d'intention pour les requêtes de marché"""
    print("\n" + "="*60)
    print("TEST 1: Analyse d'Intention de Marché")
    print("="*60)
    
    worker = EnhancedMarketsChatWorker()
    
    test_queries = [
        "Quel est le prix du Bitcoin ?",
        "Prédis l'évolution du S&P 500 pour les 3 prochains mois",
        "Analyse technique de l'EUR/USD",
        "Quelle stratégie adopter sur les actions tech ?",
        "Alerte-moi si le VIX dépasse 30",
        "Analyse fondamentale d'Apple",
        "Quel est le sentiment de marché actuel ?"
    ]
    
    for query in test_queries:
        print(f"\n📝 Query: {query}")
        analysis = worker.analyze_market_intent(query)
        
        print(f"  🎯 Type de prompt: {analysis['prompt_type']}")
        print(f"  ⚡ Urgence: {analysis['urgency']}")
        print(f"  📊 Complexité: {analysis['complexity']}")
        
        # Afficher les intentions détectées
        intents_detected = [k for k, v in analysis['intents'].items() if v]
        if intents_detected:
            print(f"  🔍 Intentions: {', '.join(intents_detected)}")
        
        # Afficher les entités
        if analysis['entities']['assets']:
            print(f"  💰 Assets: {', '.join(analysis['entities']['assets'])}")
        if analysis['entities']['timeframes']:
            print(f"  ⏱️ Timeframes: {', '.join(analysis['entities']['timeframes'])}")


def test_market_sentiment():
    """Test le calcul du sentiment de marché"""
    print("\n" + "="*60)
    print("TEST 2: Analyse de Sentiment de Marché")
    print("="*60)
    
    worker = EnhancedMarketsChatWorker()
    
    test_scenarios = [
        {
            "text": "Les marchés sont en forte hausse, momentum bullish confirmé, breakout sur les résistances",
            "momentum": "strong",
            "volume": "high"
        },
        {
            "text": "Crash imminent, baisse généralisée, risque élevé de correction",
            "momentum": "weak",
            "volume": "high"
        },
        {
            "text": "Marché stable, peu de volatilité, trading en range",
            "momentum": "neutral",
            "volume": "normal"
        }
    ]
    
    for scenario in test_scenarios:
        print(f"\n📄 Texte: {scenario['text'][:50]}...")
        sentiment = worker.calculate_market_sentiment(scenario)
        
        print(f"  {sentiment['emoji']} Sentiment: {sentiment['sentiment']}")
        print(f"  📊 Score: {sentiment['score']}")
        print(f"  🎯 Confiance: {sentiment['confidence']:.0%}")
        print(f"  💡 Recommandation: {sentiment['recommendation']}")


def test_market_predictions():
    """Test les prédictions de marché"""
    print("\n" + "="*60)
    print("TEST 3: Prédictions de Marché")
    print("="*60)
    
    worker = EnhancedMarketsChatWorker()
    
    assets = ["S&P 500", "Bitcoin", "EUR/USD", "Gold"]
    timeframes = ["1D", "1W", "1M"]
    
    for asset in assets[:2]:  # Test 2 assets
        for timeframe in timeframes[:2]:  # Test 2 timeframes
            print(f"\n📈 Prédiction pour {asset} - {timeframe}")
            
            prediction = worker.generate_market_prediction(asset, timeframe)
            
            # Afficher les scénarios
            for scenario_name, scenario_data in prediction['scenarios'].items():
                print(f"\n  📊 Scénario {scenario_name.upper()}:")
                print(f"    • Probabilité: {scenario_data['probability']:.0%}")
                print(f"    • Target: {scenario_data['target']:.2f}")
                print(f"    • Range: {scenario_data['range'][0]:.2f} - {scenario_data['range'][1]:.2f}")
                print(f"    • Description: {scenario_data['description']}")
            
            print(f"\n  🎯 Confiance globale: {prediction['confidence']:.0%}")


def test_pattern_detection():
    """Test la détection de patterns techniques"""
    print("\n" + "="*60)
    print("TEST 4: Détection de Patterns Techniques")
    print("="*60)
    
    worker = EnhancedMarketsChatWorker()
    
    # Générer des données de prix simulées
    import numpy as np
    
    # Tendance haussière
    uptrend_data = list(100 + np.cumsum(np.random.randn(100) + 0.1))
    # Tendance baissière
    downtrend_data = list(100 + np.cumsum(np.random.randn(100) - 0.1))
    
    datasets = {
        "Tendance Haussière": uptrend_data,
        "Tendance Baissière": downtrend_data
    }
    
    for name, data in datasets.items():
        print(f"\n📊 Analyse: {name}")
        patterns = worker.detect_market_patterns(data)
        
        if patterns.get('patterns'):
            print("  🔍 Patterns détectés:")
            for pattern in patterns['patterns']:
                print(f"    • {pattern['emoji']} {pattern['name']}")
                print(f"      Force: {pattern['strength']}")
                print(f"      Action: {pattern['action']}")
        
        print(f"\n  📈 Tendance générale: {patterns.get('trend', 'N/A')}")
        print(f"  💡 Recommandation: {patterns.get('recommendation', 'N/A')}")


def test_trading_alerts():
    """Test la génération d'alertes de trading"""
    print("\n" + "="*60)
    print("TEST 5: Génération d'Alertes de Trading")
    print("="*60)
    
    worker = EnhancedMarketsChatWorker()
    
    market_scenarios = [
        {
            "name": "Haute Volatilité",
            "volatility": 45,
            "momentum": 85,
            "volume_ratio": 2.5,
            "correlation_break": False
        },
        {
            "name": "Marché Calme",
            "volatility": 12,
            "momentum": 50,
            "volume_ratio": 1.1,
            "correlation_break": False
        },
        {
            "name": "Décorrélation",
            "volatility": 25,
            "momentum": 60,
            "volume_ratio": 1.5,
            "correlation_break": True
        }
    ]
    
    for scenario in market_scenarios:
        print(f"\n🎬 Scénario: {scenario['name']}")
        alerts = worker.generate_trading_alerts(scenario)
        
        if alerts:
            print("  🔔 Alertes générées:")
            for alert in alerts:
                urgency_emoji = "🔴" if alert['urgency'] == "HIGH" else "🟡" if alert['urgency'] == "MEDIUM" else "🟢"
                print(f"\n    {urgency_emoji} [{alert['type']}] Urgence: {alert['urgency']}")
                print(f"    {alert['message']}")
                print(f"    → Action: {alert['action']}")
        else:
            print("  ✅ Pas d'alertes - Conditions normales")


def test_market_summary():
    """Test la génération de résumé de marché"""
    print("\n" + "="*60)
    print("TEST 6: Résumé de Marché Complet")
    print("="*60)
    
    worker = EnhancedMarketsChatWorker()
    
    # Données de marché simulées
    market_data = {
        "indices": {
            "S&P 500": {"price": 4500, "change": 1.2},
            "NASDAQ": {"price": 14000, "change": -0.5},
            "DOW": {"price": 35000, "change": 0.8}
        },
        "volatility": 22,
        "momentum": 65,
        "volume_ratio": 1.8,
        "opportunities": [
            "Tech stocks showing breakout patterns",
            "Gold approaching support levels",
            "EUR/USD forming reversal pattern"
        ],
        "upcoming_events": [
            "Fed Meeting - Wednesday 2:00 PM",
            "CPI Data - Thursday 8:30 AM",
            "Earnings: AAPL, MSFT - Friday"
        ]
    }
    
    summary = worker.create_market_summary(market_data)
    print(summary)


def test_visualizations():
    """Test la génération de visualisations de marché"""
    print("\n" + "="*60)
    print("TEST 7: Visualisations de Marché")
    print("="*60)
    
    visualizer = MarketsVisualizer()
    
    # Test des différents types de graphiques
    charts = [
        ("Price Chart", visualizer.generate_price_chart({})),
        ("Candlestick", visualizer.generate_candlestick_chart([])),
        ("Technical Indicators", visualizer.generate_technical_indicators_chart({})),
        ("Market Heatmap", visualizer.generate_market_heatmap({})),
        ("Risk Gauge", visualizer.generate_risk_gauge(65)),
        ("Sentiment Meter", visualizer.generate_sentiment_meter({"value": 72, "components": {}})),
        ("Market Dashboard", visualizer.generate_market_overview_dashboard({}))
    ]
    
    for name, chart in charts:
        if chart and chart.startswith("data:image"):
            print(f"✅ {name}: Généré avec succès ({len(chart)} caractères)")
        else:
            print(f"❌ {name}: Échec de génération")


def test_enhanced_reply():
    """Test la génération de réponses améliorées"""
    print("\n" + "="*60)
    print("TEST 8: Réponses Améliorées avec Contexte")
    print("="*60)
    
    worker = get_enhanced_markets_chat_worker()
    
    test_messages = [
        "Analyse le S&P 500 avec les indicateurs techniques",
        "Quelle stratégie adopter sur Bitcoin ?",
        "Prédis l'EUR/USD pour la semaine prochaine"
    ]
    
    for message in test_messages[:1]:  # Test 1 message pour économiser les appels API
        print(f"\n💬 Message: {message}")
        print("⏳ Génération de la réponse...")
        
        try:
            # Test avec contexte enrichi
            response = worker.generate_enhanced_reply(
                message=message,
                context="Marché actuel: Volatilité modérée, sentiment bullish",
                history=[
                    {"role": "user", "content": "Contexte du marché ?"},
                    {"role": "assistant", "content": "Tendance haussière confirmée"}
                ]
            )
            
            if response:
                print(f"\n📊 Réponse générée ({len(response)} caractères)")
                print(response[:500] + "..." if len(response) > 500 else response)
            else:
                print("⚠️ Réponse vide")
                
        except Exception as e:
            print(f"❌ Erreur: {e}")


def test_streaming():
    """Test le streaming de réponses"""
    print("\n" + "="*60)
    print("TEST 9: Streaming de Réponses")
    print("="*60)
    
    worker = get_enhanced_markets_chat_worker()
    
    message = "Résumé rapide du marché actuel"
    print(f"💬 Message: {message}")
    print("⏳ Streaming de la réponse...\n")
    
    try:
        chunks = []
        for chunk in worker.stream_enhanced_reply(message):
            chunks.append(chunk)
            # Afficher les premiers chunks
            if len(chunks) <= 3:
                print(f"Chunk {len(chunks)}: {chunk[:50]}..." if len(chunk) > 50 else chunk)
        
        full_response = "".join(chunks)
        print(f"\n✅ Streaming terminé: {len(chunks)} chunks, {len(full_response)} caractères total")
        
    except Exception as e:
        print(f"❌ Erreur streaming: {e}")


def main():
    """Exécute tous les tests"""
    print("\n" + "🚀 " + "="*60)
    print("   TESTS DU MARKETS CHAT AMÉLIORÉ v2.0")
    print("   Analyse de Marchés avec IA Avancée")
    print("="*60 + " 🚀")
    
    tests = [
        test_market_intent_analysis,
        test_market_sentiment,
        test_market_predictions,
        test_pattern_detection,
        test_trading_alerts,
        test_market_summary,
        test_visualizations,
        test_enhanced_reply,
        test_streaming
    ]
    
    for test_func in tests:
        try:
            test_func()
        except Exception as e:
            print(f"\n❌ Erreur dans {test_func.__name__}: {e}")
    
    print("\n" + "="*60)
    print("✅ TOUS LES TESTS TERMINÉS")
    print("="*60)
    
    print("\n📊 RÉSUMÉ DES AMÉLIORATIONS:")
    print("• Analyse d'intention avancée pour requêtes de marché")
    print("• Calcul de sentiment avec indicateurs multiples")
    print("• Prédictions probabilistes avec scénarios")
    print("• Détection de patterns techniques")
    print("• Système d'alertes de trading intelligent")
    print("• 7 types de visualisations de marché")
    print("• Prompts spécialisés par type d'analyse")
    print("• Streaming amélioré avec indicateurs")


if __name__ == "__main__":
    main()
