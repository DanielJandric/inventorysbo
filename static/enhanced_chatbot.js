
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
