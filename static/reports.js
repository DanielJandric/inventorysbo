// Classification bancaire des actifs
const ASSET_CLASSIFICATION = {
    'Actions': {
        bankClass: 'Actions cotées',
        subCategory: 'Titres cotés en bourse (actions)',
        icon: '📈',
        color: '#1f2937'
    },
    'Voitures': {
        bankClass: 'Actifs réels',
        subCategory: 'Automobiles (véhicules de collection ou de luxe)',
        icon: '🚗',
        color: '#dc2626'
    },
    'Appartements / maison': {
        bankClass: 'Immobilier direct ou indirect',
        subCategory: 'Immobilier résidentiel (logements)',
        icon: '🏠',
        color: '#059669'
    },
    'Be Capital': {
        bankClass: 'Immobilier direct ou indirect',
        subCategory: 'Immobilier de rendement (biens générant des revenus locatifs)',
        icon: '🏢',
        color: '#7c3aed'
    },
    'Bateaux': {
        bankClass: 'Actifs réels',
        subCategory: 'Bateaux (yachts, bateaux de plaisance)',
        icon: '⛵',
        color: '#0891b2'
    },
    'Avions': {
        bankClass: 'Actifs réels',
        subCategory: 'Avions (jets privés, aviation d\'affaires)',
        icon: '✈️',
        color: '#6b7280'
    },
    'Start-ups': {
        bankClass: 'Private Equity / Venture Capital',
        subCategory: 'Start-ups (jeunes entreprises non cotées)',
        icon: '🚀',
        color: '#f59e0b'
    },
    'Investis services': {
        bankClass: 'Private Equity / Venture Capital',
        subCategory: 'Sociétés de rénovation (services immobiliers)',
        icon: '🔧',
        color: '#10b981'
    },
    'Saanen': {
        bankClass: 'Immobilier direct ou indirect',
        subCategory: 'Projet immobilier à Saanen (type d\'actif immobilier non précisé)',
        icon: '🏔️',
        color: '#8b5cf6'
    },
    'Dixence Resort': {
        bankClass: 'Immobilier direct ou indirect',
        subCategory: 'Immobilier hôtelier (complexe resort touristique)',
        icon: '🏨',
        color: '#ec4899'
    },
    'Investis properties': {
        bankClass: 'Immobilier direct ou indirect',
        subCategory: 'Immobilier de rendement (portefeuille d\'immeubles locatifs)',
        icon: '🏘️',
        color: '#f97316'
    },
    'Mibo': {
        bankClass: 'Immobilier direct ou indirect',
        subCategory: 'Actif immobilier (précision non fournie)',
        icon: '🏗️',
        color: '#84cc16'
    },
    'Portfolio Rhône Hotels': {
        bankClass: 'Immobilier direct ou indirect',
        subCategory: 'Immobilier hôtelier (portefeuille d\'hôtels, rendement locatif)',
        icon: '🏩',
        color: '#06b6d4'
    },
    'Rhône Property – Portfolio IAM': {
        bankClass: 'Immobilier direct ou indirect',
        subCategory: 'Immobilier de rendement (portefeuille immobilier)',
        icon: '🏢',
        color: '#8b5cf6'
    },
    'Be Capital Activities': {
        bankClass: 'Private Equity / Venture Capital',
        subCategory: 'Sociétés de e-commerce (participations non cotées)',
        icon: '🛒',
        color: '#ef4444'
    },
    'IB': {
        bankClass: 'Immobilier direct ou indirect',
        subCategory: 'Actif immobilier (précision non fournie)',
        icon: '🏢',
        color: '#6b7280'
    }
};

// Variables globales
let allItems = [];
let assetClassData = {};

// Initialisation
document.addEventListener('DOMContentLoaded', function() {
    loadReportsData();
});

// Charger les données des rapports
async function loadReportsData() {
    try {
        console.log('📊 Chargement des données des rapports...');
        
        const response = await fetch('/api/items');
        if (!response.ok) {
            throw new Error(`Erreur HTTP: ${response.status}`);
        }
        
        allItems = await response.json();
        console.log(`✅ ${allItems.length} items chargés`);
        
        processAssetClasses();
        updateStatistics();
        displayAssetClasses();
        
    } catch (error) {
        console.error('❌ Erreur lors du chargement des données:', error);
        showNotification('Erreur lors du chargement des données', true);
    }
}

// Traiter les classes d'actifs
function processAssetClasses() {
    assetClassData = {};
    
    allItems.forEach(item => {
        if (!item.category || item.status === 'Sold') return;
        
        const classification = ASSET_CLASSIFICATION[item.category];
        if (!classification) return;
        
        const bankClass = classification.bankClass;
        
        if (!assetClassData[bankClass]) {
            assetClassData[bankClass] = {
                name: bankClass,
                subCategories: {},
                totalValue: 0,
                itemCount: 0,
                availableCount: 0,
                classification: classification
            };
        }
        
        // Calculer la valeur
        let value = 0;
        if (item.category === 'Actions' && item.current_price && item.stock_quantity) {
            value = item.current_price * item.stock_quantity;
        } else if (item.status === 'Available' && item.current_value) {
            value = item.current_value;
        }
        
        assetClassData[bankClass].totalValue += value;
        assetClassData[bankClass].itemCount++;
        
        if (item.status === 'Available') {
            assetClassData[bankClass].availableCount++;
        }
        
        // Organiser par sous-catégorie
        const subCategory = classification.subCategory;
        if (!assetClassData[bankClass].subCategories[subCategory]) {
            assetClassData[bankClass].subCategories[subCategory] = [];
        }
        assetClassData[bankClass].subCategories[subCategory].push(item);
    });
    
    console.log('📊 Classes d\'actifs traitées:', Object.keys(assetClassData));
}

// Mettre à jour les statistiques
function updateStatistics() {
    const totalAssets = allItems.filter(item => item.status !== 'Sold').length;
    const availableAssets = allItems.filter(item => item.status === 'Available').length;
    const assetClassesCount = Object.keys(assetClassData).length;
    
    // Calculer la valeur totale
    const totalValue = allItems.reduce((sum, item) => {
        if (item.status === 'Sold') return sum;
        
        if (item.category === 'Actions' && item.current_price && item.stock_quantity) {
            return sum + (item.current_price * item.stock_quantity);
        } else if (item.status === 'Available' && item.current_value) {
            return sum + item.current_value;
        }
        return sum;
    }, 0);
    
    // Mettre à jour l'affichage
    document.getElementById('total-assets').textContent = totalAssets;
    document.getElementById('total-value').textContent = formatPrice(totalValue);
    document.getElementById('asset-classes').textContent = assetClassesCount;
    document.getElementById('available-assets').textContent = availableAssets;
}

// Afficher les classes d'actifs
function displayAssetClasses() {
    const container = document.getElementById('asset-classes-grid');
    
    const assetClasses = Object.values(assetClassData).sort((a, b) => b.totalValue - a.totalValue);
    
    container.innerHTML = assetClasses.map(assetClass => `
        <div class="asset-class-card">
            <div class="flex items-center justify-between mb-4">
                <div class="flex items-center gap-3">
                    <div class="text-3xl">${assetClass.classification.icon}</div>
                    <div>
                        <h3 class="text-lg font-bold text-gray-800">${assetClass.name}</h3>
                        <p class="text-sm text-gray-600">${assetClass.classification.subCategory}</p>
                    </div>
                </div>
            </div>
            
            <div class="space-y-3 mb-6">
                <div class="flex justify-between">
                    <span class="text-gray-600">Valeur totale:</span>
                    <span class="font-semibold text-gray-800">${formatPrice(assetClass.totalValue)}</span>
                </div>
                <div class="flex justify-between">
                    <span class="text-gray-600">Nombre d'actifs:</span>
                    <span class="font-semibold text-gray-800">${assetClass.itemCount}</span>
                </div>
                <div class="flex justify-between">
                    <span class="text-gray-600">Disponibles:</span>
                    <span class="font-semibold text-gray-800">${assetClass.availableCount}</span>
                </div>
            </div>
            
            <div class="space-y-2">
                <button onclick="generateAssetClassReport('${assetClass.name}')" class="w-full generate-btn">
                    📄 Rapport ${assetClass.name}
                </button>
                <button onclick="showAssetClassDetails('${assetClass.name}')" class="w-full bg-gray-100 text-gray-800 px-4 py-2 rounded-lg font-medium hover:bg-gray-200 transition-colors">
                    👁️ Voir détails
                </button>
            </div>
        </div>
    `).join('');
}

// Générer un rapport pour une classe d'actif spécifique
async function generateAssetClassReport(assetClassName) {
    try {
        console.log(`📄 Génération du rapport pour: ${assetClassName}`);
        showNotification(`Génération du rapport ${assetClassName}...`, false);
        
        const response = await fetch(`/api/reports/asset-class/${encodeURIComponent(assetClassName)}`);
        
        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `bonvin_${assetClassName.replace(/\s+/g, '_').toLowerCase()}_${new Date().toISOString().slice(0, 10)}.pdf`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
            
            console.log('✅ Rapport généré avec succès');
            showNotification(`Rapport ${assetClassName} généré !`, false);
        } else {
            const error = await response.json();
            console.error('❌ Erreur génération rapport:', error);
            showNotification('Erreur lors de la génération du rapport: ' + (error.error || 'Erreur inconnue'), true);
        }
        
    } catch (error) {
        console.error('❌ Erreur:', error);
        showNotification('Erreur lors de la génération du rapport', true);
    }
}

// Générer tous les rapports
async function generateAllReports() {
    try {
        console.log('📄 Génération de tous les rapports...');
        showNotification('Génération de tous les rapports en cours...', false);
        
        const response = await fetch('/api/reports/all-asset-classes');
        
        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `bonvin_all_asset_classes_${new Date().toISOString().slice(0, 10)}.pdf`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
            
            console.log('✅ Tous les rapports générés avec succès');
            showNotification('Tous les rapports générés !', false);
        } else {
            const error = await response.json();
            console.error('❌ Erreur génération rapports:', error);
            showNotification('Erreur lors de la génération des rapports: ' + (error.error || 'Erreur inconnue'), true);
        }
        
    } catch (error) {
        console.error('❌ Erreur:', error);
        showNotification('Erreur lors de la génération des rapports', true);
    }
}

// Afficher les détails d'une classe d'actif
function showAssetClassDetails(assetClassName) {
    const assetClass = assetClassData[assetClassName];
    if (!assetClass) return;
    
    const subCategories = Object.entries(assetClass.subCategories);
    
    let detailsHTML = `
        <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div class="bg-white rounded-lg p-6 max-w-4xl w-full mx-4 max-h-[90vh] overflow-y-auto">
                <div class="flex justify-between items-center mb-4">
                    <h2 class="text-2xl font-bold text-gray-800">${assetClassName}</h2>
                    <button onclick="closeModal()" class="text-gray-400 hover:text-gray-600 text-2xl">&times;</button>
                </div>
                
                <div class="space-y-4">
    `;
    
    subCategories.forEach(([subCategory, items]) => {
        detailsHTML += `
            <div class="border border-gray-200 rounded-lg p-4">
                <h3 class="text-lg font-semibold text-gray-800 mb-3">${subCategory}</h3>
                <div class="space-y-2">
        `;
        
        items.forEach(item => {
            let value = 0;
            if (item.category === 'Actions' && item.current_price && item.stock_quantity) {
                value = item.current_price * item.stock_quantity;
            } else if (item.status === 'Available' && item.current_value) {
                value = item.current_value;
            }
            
            detailsHTML += `
                <div class="flex justify-between items-center p-2 bg-gray-50 rounded">
                    <div>
                        <div class="font-medium text-gray-800">${item.name}</div>
                        <div class="text-sm text-gray-600">${item.status}</div>
                    </div>
                    <div class="text-right">
                        <div class="font-semibold text-gray-800">${formatPrice(value)}</div>
                    </div>
                </div>
            `;
        });
        
        detailsHTML += `
                </div>
            </div>
        `;
    });
    
    detailsHTML += `
                </div>
            </div>
        </div>
    `;
    
    document.body.insertAdjacentHTML('beforeend', detailsHTML);
}

// Fermer le modal
function closeModal() {
    const modal = document.querySelector('.fixed.inset-0');
    if (modal) {
        modal.remove();
    }
}

// Fonction utilitaire pour formater les prix
function formatPrice(price) {
    if (!price || price === 0) return '0 CHF';
    try {
        return new Intl.NumberFormat('fr-CH', {
            style: 'currency',
            currency: 'CHF',
            minimumFractionDigits: 0,
            maximumFractionDigits: 0
        }).format(price);
    } catch {
        return '0 CHF';
    }
}

// Fonction pour afficher les notifications
function showNotification(message, isError = false) {
    // Créer une notification simple
    const notification = document.createElement('div');
    notification.className = `fixed top-4 right-4 px-6 py-3 rounded-lg text-white font-medium z-50 ${
        isError ? 'bg-red-500' : 'bg-green-500'
    }`;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.remove();
    }, 3000);
}

// Exposer les fonctions globalement
window.generateAssetClassReport = generateAssetClassReport;
window.generateAllReports = generateAllReports;
window.showAssetClassDetails = showAssetClassDetails;
window.closeModal = closeModal; 