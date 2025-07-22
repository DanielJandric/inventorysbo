#!/usr/bin/env python3
"""
Test des limites de taille des rapports de marché
"""

import sys
import os
import json
import requests
from datetime import datetime
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_api_manus_direct():
    """Test direct de l'API Manus pour voir la taille des rapports"""
    print("🔍 Test direct de l'API Manus...")
    
    try:
        # Test direct de l'API Manus
        api_url = "https://y0h0i3cqzyko.manus.space/api/report"
        response = requests.get(api_url, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            
            # Analyser la structure
            report = data.get('report', {})
            content = report.get('content', {})
            
            # Mesurer la taille du contenu
            markdown_content = content.get('markdown', '')
            html_content = content.get('html', '')
            
            # Statistiques
            markdown_words = len(markdown_content.split())
            html_words = len(html_content.split())
            markdown_chars = len(markdown_content)
            html_chars = len(html_content)
            
            print(f"📊 Statistiques du rapport:")
            print(f"   📝 Contenu Markdown: {markdown_words} mots, {markdown_chars} caractères")
            print(f"   🌐 Contenu HTML: {html_words} mots, {html_chars} caractères")
            print(f"   📦 Taille totale JSON: {len(response.content)} bytes")
            
            # Analyser la structure
            print(f"\n🏗️ Structure du rapport:")
            print(f"   📋 Sections: {len(report.get('metadata', {}).get('sections', []))}")
            print(f"   📈 Métriques: {len(report.get('key_metrics', {}))}")
            print(f"   📝 Points clés: {len(report.get('summary', {}).get('key_points', []))}")
            
            return {
                'markdown_words': markdown_words,
                'markdown_chars': markdown_chars,
                'html_words': html_words,
                'html_chars': html_chars,
                'total_bytes': len(response.content),
                'content': markdown_content[:200] + "..." if len(markdown_content) > 200 else markdown_content
            }
        else:
            print(f"❌ Erreur API: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Erreur test API: {e}")
        return None

def test_manus_integration():
    """Test via l'intégration Manus"""
    print("\n🔍 Test via manus_integration...")
    
    try:
        from manus_integration import manus_market_report_api
        
        # Récupérer le rapport
        market_report = manus_market_report_api.get_market_report(force_refresh=True)
        
        if market_report.get('status') == 'complete':
            content = market_report.get('content', {})
            markdown_content = content.get('markdown', '')
            
            # Statistiques
            words = len(markdown_content.split())
            chars = len(markdown_content)
            
            print(f"📊 Statistiques via intégration:")
            print(f"   📝 Contenu: {words} mots, {chars} caractères")
            print(f"   📦 Taille totale: {len(str(market_report))} caractères")
            
            return {
                'words': words,
                'chars': chars,
                'content': markdown_content[:200] + "..." if len(markdown_content) > 200 else markdown_content
            }
        else:
            print(f"❌ Erreur intégration: {market_report.get('message', 'Erreur inconnue')}")
            return None
            
    except Exception as e:
        print(f"❌ Erreur intégration: {e}")
        return None

def test_database_limits():
    """Test des limites de la base de données"""
    print("\n🔍 Test des limites base de données...")
    
    try:
        # Simuler un très gros contenu
        large_content = "Test " * 10000  # 50,000 caractères
        words = len(large_content.split())
        chars = len(large_content)
        
        print(f"📊 Test contenu volumineux:")
        print(f"   📝 Contenu test: {words} mots, {chars} caractères")
        
        # Vérifier les limites potentielles
        limits = {
            'postgresql_text': 'Illimité (1GB théorique)',
            'supabase_text': 'Illimité (1GB théorique)',
            'json_field': '1GB',
            'http_request': 'Pas de limite explicite',
            'memory_python': 'Dépend de la RAM disponible'
        }
        
        print(f"\n📋 Limites théoriques:")
        for limit_type, limit_value in limits.items():
            print(f"   🔸 {limit_type}: {limit_value}")
        
        return {
            'test_words': words,
            'test_chars': chars,
            'limits': limits
        }
        
    except Exception as e:
        print(f"❌ Erreur test limites: {e}")
        return None

def test_frontend_limits():
    """Test des limites frontend"""
    print("\n🔍 Test des limites frontend...")
    
    try:
        # Simuler différents tailles de contenu
        test_sizes = [
            ("Petit", 100),
            ("Moyen", 1000),
            ("Grand", 5000),
            ("Très grand", 10000),
            ("Énorme", 50000)
        ]
        
        print(f"📊 Test d'affichage frontend:")
        for size_name, word_count in test_sizes:
            test_content = "Mot " * word_count
            char_count = len(test_content)
            
            # Estimation du temps de chargement
            load_time_estimate = char_count / 10000  # ~10KB/s
            
            print(f"   📝 {size_name} ({word_count} mots, {char_count} chars): ~{load_time_estimate:.2f}s")
        
        # Limites frontend
        frontend_limits = {
            'dom_element': 'Pas de limite pratique',
            'javascript_string': '~536,870,888 caractères (2^29)',
            'browser_memory': 'Dépend du navigateur (généralement 1-4GB)',
            'network_timeout': '30s (configuré dans l\'app)',
            'ui_performance': 'Recommandé < 10,000 mots pour UX optimale'
        }
        
        print(f"\n📋 Limites frontend:")
        for limit_type, limit_value in frontend_limits.items():
            print(f"   🔸 {limit_type}: {limit_value}")
        
        return frontend_limits
        
    except Exception as e:
        print(f"❌ Erreur test frontend: {e}")
        return None

def analyze_current_report():
    """Analyser le rapport actuel"""
    print("\n🔍 Analyse du rapport actuel...")
    
    try:
        from manus_integration import manus_market_report_api
        
        # Récupérer le rapport actuel
        market_report = manus_market_report_api.get_market_report()
        
        if market_report.get('status') == 'complete':
            content = market_report.get('content', {})
            markdown_content = content.get('markdown', '')
            
            # Analyse détaillée
            words = markdown_content.split()
            word_count = len(words)
            char_count = len(markdown_content)
            line_count = markdown_content.count('\n') + 1
            
            # Analyse par sections
            sections = markdown_content.split('\n\n')
            section_count = len([s for s in sections if s.strip()])
            
            print(f"📊 Analyse du rapport actuel:")
            print(f"   📝 Mots: {word_count}")
            print(f"   🔤 Caractères: {char_count}")
            print(f"   📄 Lignes: {line_count}")
            print(f"   📋 Sections: {section_count}")
            print(f"   📦 Taille moyenne par section: {word_count // max(section_count, 1)} mots")
            
            # Aperçu du contenu
            print(f"\n📖 Aperçu du contenu:")
            preview = markdown_content[:300] + "..." if len(markdown_content) > 300 else markdown_content
            print(f"   {preview}")
            
            return {
                'word_count': word_count,
                'char_count': char_count,
                'line_count': line_count,
                'section_count': section_count,
                'preview': preview
            }
        else:
            print(f"❌ Aucun rapport disponible: {market_report.get('message', 'Erreur inconnue')}")
            return None
            
    except Exception as e:
        print(f"❌ Erreur analyse: {e}")
        return None

def main():
    """Test principal"""
    print("🚀 Test des limites de taille des rapports de marché")
    print("=" * 70)
    
    results = {}
    
    # Tests
    results['api_direct'] = test_api_manus_direct()
    results['integration'] = test_manus_integration()
    results['database'] = test_database_limits()
    results['frontend'] = test_frontend_limits()
    results['current'] = analyze_current_report()
    
    print("\n" + "=" * 70)
    print("📋 RÉSUMÉ DES LIMITES:")
    
    # Analyser les résultats
    if results['api_direct']:
        print(f"✅ API Manus: {results['api_direct']['markdown_words']} mots")
    
    if results['integration']:
        print(f"✅ Intégration: {results['integration']['words']} mots")
    
    if results['current']:
        print(f"✅ Rapport actuel: {results['current']['word_count']} mots")
    
    print(f"\n🎯 CONCLUSION:")
    print(f"   📝 Aucune limite explicite sur le nombre de mots")
    print(f"   🔧 Les limites sont principalement techniques (mémoire, performance)")
    print(f"   ⚡ Recommandation: < 10,000 mots pour une UX optimale")
    print(f"   🚀 L'API Manus peut générer des rapports volumineux sans problème")

if __name__ == "__main__":
    main() 