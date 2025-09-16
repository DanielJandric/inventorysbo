"""
Script d'intégration du chatbot amélioré dans l'application BONVIN
Ce script facilite l'intégration des nouvelles fonctionnalités
"""

import os
import sys
import logging
from typing import Dict, Any, List, Optional

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_dependencies():
    """Vérifie que toutes les dépendances sont installées"""
    required_packages = {
        'matplotlib': 'matplotlib',
        'seaborn': 'seaborn',
        'pandas': 'pandas',
        'reportlab': 'reportlab',
        'xlsxwriter': 'xlsxwriter',
        'numpy': 'numpy'
    }
    
    missing = []
    for import_name, package_name in required_packages.items():
        try:
            __import__(import_name)
            logger.info(f"✅ {package_name} installé")
        except ImportError:
            missing.append(package_name)
            logger.warning(f"❌ {package_name} manquant")
    
    if missing:
        logger.error(f"Packages manquants: {', '.join(missing)}")
        logger.info(f"Installer avec: pip install {' '.join(missing)}")
        return False
    
    return True


def integrate_chatbot_routes(app):
    """
    Intègre les nouvelles routes du chatbot dans l'application Flask
    """
    from flask import jsonify, request, send_file
    from enhanced_chatbot_manager import EnhancedChatbotManager, ConversationOptimizer
    from chatbot_visualizations import ChatbotVisualizer, ReportGenerator
    from prompts.enhanced_prompts import get_contextual_prompt, format_response_with_template
    import io
    
    # Initialisation des composants
    enhanced_chatbot = EnhancedChatbotManager()
    visualizer = ChatbotVisualizer()
    report_generator = ReportGenerator()
    optimizer = ConversationOptimizer()
    
    @app.route("/api/chatbot/analyze-intent", methods=["POST"])
    def analyze_intent():
        """Analyse l'intention d'une requête utilisateur"""
        try:
            data = request.get_json()
            query = data.get("query", "")
            
            if not query:
                return jsonify({"error": "Query required"}), 400
            
            analysis = enhanced_chatbot.analyze_user_intent(query)
            
            return jsonify({
                "success": True,
                "analysis": analysis
            })
            
        except Exception as e:
            logger.error(f"Erreur analyse intention: {e}")
            return jsonify({"error": str(e)}), 500
    
    @app.route("/api/chatbot/predict-value", methods=["POST"])
    def predict_value():
        """Prédit la valeur future d'un item"""
        try:
            data = request.get_json()
            item_data = data.get("item", {})
            months = data.get("months", 12)
            
            if not item_data:
                return jsonify({"error": "Item data required"}), 400
            
            predictions = enhanced_chatbot.predict_future_value(item_data, months)
            
            return jsonify({
                "success": True,
                "predictions": predictions
            })
            
        except Exception as e:
            logger.error(f"Erreur prédiction: {e}")
            return jsonify({"error": str(e)}), 500
    
    @app.route("/api/chatbot/generate-chart", methods=["POST"])
    def generate_chart():
        """Génère un graphique de visualisation"""
        try:
            data = request.get_json()
            chart_type = data.get("type", "portfolio")
            items = data.get("items", [])
            
            if not items:
                return jsonify({"error": "Items required"}), 400
            
            if chart_type == "portfolio":
                chart = visualizer.generate_portfolio_chart(items)
            elif chart_type == "performance":
                chart = visualizer.generate_performance_chart(items)
            else:
                return jsonify({"error": "Invalid chart type"}), 400
            
            return jsonify({
                "success": True,
                "chart": chart
            })
            
        except Exception as e:
            logger.error(f"Erreur génération graphique: {e}")
            return jsonify({"error": str(e)}), 500
    
    @app.route("/api/chatbot/export-pdf", methods=["POST"])
    def export_pdf():
        """Génère et télécharge un rapport PDF"""
        try:
            data = request.get_json()
            report_data = data.get("data", {})
            
            if not report_data:
                return jsonify({"error": "Report data required"}), 400
            
            pdf_bytes = report_generator.generate_portfolio_report(report_data)
            
            # Créer un buffer pour le téléchargement
            buffer = io.BytesIO(pdf_bytes)
            buffer.seek(0)
            
            return send_file(
                buffer,
                mimetype='application/pdf',
                as_attachment=True,
                download_name=f'rapport_bonvin_{datetime.now().strftime("%Y%m%d")}.pdf'
            )
            
        except Exception as e:
            logger.error(f"Erreur export PDF: {e}")
            return jsonify({"error": str(e)}), 500
    
    @app.route("/api/chatbot/export-excel", methods=["POST"])
    def export_excel():
        """Génère et télécharge un export Excel"""
        try:
            data = request.get_json()
            items = data.get("items", [])
            
            if not items:
                return jsonify({"error": "Items required"}), 400
            
            excel_bytes = report_generator.generate_excel_export(items)
            
            # Créer un buffer pour le téléchargement
            buffer = io.BytesIO(excel_bytes)
            buffer.seek(0)
            
            return send_file(
                buffer,
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                as_attachment=True,
                download_name=f'inventaire_bonvin_{datetime.now().strftime("%Y%m%d")}.xlsx'
            )
            
        except Exception as e:
            logger.error(f"Erreur export Excel: {e}")
            return jsonify({"error": str(e)}), 500
    
    @app.route("/api/chatbot/smart-suggestions", methods=["POST"])
    def get_smart_suggestions():
        """Génère des suggestions intelligentes"""
        try:
            data = request.get_json()
            context = data.get("context", {})
            
            suggestions = enhanced_chatbot.generate_smart_suggestions(context)
            
            return jsonify({
                "success": True,
                "suggestions": suggestions
            })
            
        except Exception as e:
            logger.error(f"Erreur suggestions: {e}")
            return jsonify({"error": str(e)}), 500
    
    @app.route("/api/chatbot/portfolio-metrics", methods=["POST"])
    def get_portfolio_metrics():
        """Calcule les métriques avancées du portefeuille"""
        try:
            data = request.get_json()
            items = data.get("items", [])
            
            if not items:
                return jsonify({"error": "Items required"}), 400
            
            metrics = enhanced_chatbot.calculate_portfolio_metrics(items)
            
            return jsonify({
                "success": True,
                "metrics": metrics
            })
            
        except Exception as e:
            logger.error(f"Erreur métriques: {e}")
            return jsonify({"error": str(e)}), 500
    
    logger.info("✅ Routes du chatbot amélioré intégrées avec succès")
    return True


def update_frontend_integration():
    """
    Génère le code JavaScript pour intégrer les nouvelles fonctionnalités
    """
    js_code = """
// === INTÉGRATION CHATBOT AMÉLIORÉ v2.0 ===

// Nouvelle classe pour gérer le chatbot amélioré
class EnhancedChatbot {
    constructor() {
        this.apiBase = '/api/chatbot';
        this.currentContext = {};
        this.conversationHistory = [];
    }
    
    // Analyse l'intention de l'utilisateur
    async analyzeIntent(query) {
        try {
            const response = await fetch(`${this.apiBase}/analyze-intent`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({query})
            });
            const data = await response.json();
            return data.analysis;
        } catch (error) {
            console.error('Erreur analyse intention:', error);
            return null;
        }
    }
    
    // Prédit la valeur future
    async predictValue(item, months = 12) {
        try {
            const response = await fetch(`${this.apiBase}/predict-value`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({item, months})
            });
            const data = await response.json();
            return data.predictions;
        } catch (error) {
            console.error('Erreur prédiction:', error);
            return null;
        }
    }
    
    // Génère un graphique
    async generateChart(type, items) {
        try {
            const response = await fetch(`${this.apiBase}/generate-chart`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({type, items})
            });
            const data = await response.json();
            return data.chart;
        } catch (error) {
            console.error('Erreur génération graphique:', error);
            return null;
        }
    }
    
    // Export PDF
    async exportPDF(reportData) {
        try {
            const response = await fetch(`${this.apiBase}/export-pdf`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({data: reportData})
            });
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `rapport_bonvin_${new Date().toISOString().split('T')[0]}.pdf`;
            a.click();
            window.URL.revokeObjectURL(url);
        } catch (error) {
            console.error('Erreur export PDF:', error);
        }
    }
    
    // Export Excel
    async exportExcel(items) {
        try {
            const response = await fetch(`${this.apiBase}/export-excel`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({items})
            });
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `inventaire_bonvin_${new Date().toISOString().split('T')[0]}.xlsx`;
            a.click();
            window.URL.revokeObjectURL(url);
        } catch (error) {
            console.error('Erreur export Excel:', error);
        }
    }
    
    // Obtient des suggestions intelligentes
    async getSmartSuggestions(context) {
        try {
            const response = await fetch(`${this.apiBase}/smart-suggestions`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({context})
            });
            const data = await response.json();
            return data.suggestions;
        } catch (error) {
            console.error('Erreur suggestions:', error);
            return [];
        }
    }
    
    // Affiche un graphique dans le chat
    displayChart(chartBase64) {
        const messagesContainer = document.getElementById('chatbot-messages');
        if (!messagesContainer || !chartBase64) return;
        
        const chartDiv = document.createElement('div');
        chartDiv.className = 'chat-message bot chart-message';
        chartDiv.innerHTML = `
            <img src="${chartBase64}" alt="Graphique" style="max-width: 100%; border-radius: 8px; margin: 10px 0;">
        `;
        messagesContainer.appendChild(chartDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
    
    // Affiche des boutons d'action
    displayActionButtons(actions) {
        const messagesContainer = document.getElementById('chatbot-messages');
        if (!messagesContainer) return;
        
        const actionsDiv = document.createElement('div');
        actionsDiv.className = 'chat-actions';
        actionsDiv.style.cssText = 'display: flex; gap: 10px; margin: 10px 0; flex-wrap: wrap;';
        
        actions.forEach(action => {
            const button = document.createElement('button');
            button.textContent = action.label;
            button.className = 'action-button';
            button.style.cssText = `
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 20px;
                cursor: pointer;
                font-size: 14px;
                transition: transform 0.2s;
            `;
            button.onclick = action.handler;
            button.onmouseenter = () => button.style.transform = 'scale(1.05)';
            button.onmouseleave = () => button.style.transform = 'scale(1)';
            actionsDiv.appendChild(button);
        });
        
        messagesContainer.appendChild(actionsDiv);
    }
}

// Initialisation globale
const enhancedChatbot = new EnhancedChatbot();

// Amélioration de la fonction handleChatSubmit existante
const originalHandleChatSubmit = window.handleChatSubmit;
window.handleChatSubmit = async function(event) {
    event.preventDefault();
    
    const input = document.getElementById('chatbot-input');
    const query = input.value.trim();
    
    if (!query) return;
    
    // Analyse d'intention
    const intent = await enhancedChatbot.analyzeIntent(query);
    
    if (intent) {
        // Si export détecté
        if (intent.intents.export) {
            enhancedChatbot.displayActionButtons([
                {
                    label: '📄 Export PDF',
                    handler: () => enhancedChatbot.exportPDF(getReportData())
                },
                {
                    label: '📊 Export Excel',
                    handler: () => enhancedChatbot.exportExcel(getAllItems())
                }
            ]);
        }
        
        // Si analyse détectée
        if (intent.intents.analysis) {
            const items = getAllItems();
            const chart = await enhancedChatbot.generateChart('portfolio', items);
            if (chart) {
                enhancedChatbot.displayChart(chart);
            }
        }
        
        // Si prédiction détectée
        if (intent.intents.prediction) {
            // Afficher les prédictions pour les items pertinents
            const predictions = await enhancedChatbot.predictValue(getCurrentItem());
            if (predictions) {
                displayPredictions(predictions);
            }
        }
    }
    
    // Appeler la fonction originale
    if (originalHandleChatSubmit) {
        originalHandleChatSubmit.call(this, event);
    }
};

// Fonction helper pour obtenir les données du rapport
function getReportData() {
    const items = getAllItems();
    const categories = {};
    
    items.forEach(item => {
        const cat = item.category || 'Autre';
        categories[cat] = (categories[cat] || 0) + (item.current_value || 0);
    });
    
    return {
        total_value: items.reduce((sum, item) => sum + (item.current_value || 0), 0),
        total_items: items.length,
        ytd_performance: 12.5, // À calculer
        unrealized_gains: 250000, // À calculer
        categories: categories,
        top_items: items.sort((a, b) => (b.current_value || 0) - (a.current_value || 0)).slice(0, 10)
    };
}

// Fonction pour obtenir tous les items
function getAllItems() {
    return window.allItems || [];
}

// Fonction pour obtenir l'item actuel
function getCurrentItem() {
    // Logique pour obtenir l'item actuellement sélectionné
    return window.currentItem || {};
}

// Fonction pour afficher les prédictions
function displayPredictions(predictions) {
    const messagesContainer = document.getElementById('chatbot-messages');
    if (!messagesContainer) return;
    
    const predDiv = document.createElement('div');
    predDiv.className = 'chat-message bot predictions';
    predDiv.innerHTML = `
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 15px; border-radius: 8px; color: white;">
            <h4>📈 Prédictions de Valeur</h4>
            <div style="margin-top: 10px;">
                <div>🔴 Pessimiste: ${predictions.pessimistic.toLocaleString()} CHF</div>
                <div>🟡 Réaliste: ${predictions.realistic.toLocaleString()} CHF</div>
                <div>🟢 Optimiste: ${predictions.optimistic.toLocaleString()} CHF</div>
                <div style="margin-top: 10px; opacity: 0.9;">Confiance: ${(predictions.confidence * 100).toFixed(0)}%</div>
            </div>
        </div>
    `;
    messagesContainer.appendChild(predDiv);
}

console.log('✅ Chatbot amélioré v2.0 chargé avec succès');
"""
    
    # Sauvegarder le code JS
    with open("static/enhanced_chatbot.js", "w", encoding="utf-8") as f:
        f.write(js_code)
    
    logger.info("✅ Code JavaScript généré: static/enhanced_chatbot.js")
    
    # Instructions pour l'intégration HTML
    html_integration = """
    <!-- Ajouter dans index.html avant la fermeture de </body> -->
    <script src="/static/enhanced_chatbot.js"></script>
    
    <!-- Ajouter ces styles CSS dans la section <style> -->
    <style>
        .chart-message img {
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            transition: transform 0.3s;
        }
        
        .chart-message img:hover {
            transform: scale(1.02);
        }
        
        .chat-actions {
            animation: slideIn 0.3s ease-out;
        }
        
        @keyframes slideIn {
            from {
                opacity: 0;
                transform: translateY(10px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        .predictions {
            animation: fadeIn 0.5s ease-out;
        }
        
        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }
    </style>
    """
    
    logger.info("Instructions HTML d'intégration générées")
    return True


def main():
    """Fonction principale d'intégration"""
    logger.info("🚀 Début de l'intégration du chatbot amélioré v2.0")
    
    # Vérifier les dépendances
    if not check_dependencies():
        logger.error("❌ Dépendances manquantes. Installation requise.")
        return False
    
    # Générer le code frontend
    if update_frontend_integration():
        logger.info("✅ Code frontend généré avec succès")
    
    # Instructions finales
    print("\n" + "="*60)
    print("✅ INTÉGRATION PRÊTE")
    print("="*60)
    print("\n📋 ÉTAPES SUIVANTES:")
    print("1. Ajouter les nouvelles routes dans app.py:")
    print("   from integrate_enhanced_chatbot import integrate_chatbot_routes")
    print("   integrate_chatbot_routes(app)")
    print("\n2. Inclure le JavaScript dans index.html:")
    print('   <script src="/static/enhanced_chatbot.js"></script>')
    print("\n3. Redémarrer l'application")
    print("\n4. Tester les nouvelles fonctionnalités:")
    print("   - Analyse d'intention")
    print("   - Prédictions de valeur")
    print("   - Génération de graphiques")
    print("   - Export PDF/Excel")
    print("\n" + "="*60)
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
