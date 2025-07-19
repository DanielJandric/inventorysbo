// analytics.js - Page Analytics avec Treemap
let allItems = [];
let selectedCategories = new Set();
let categoryChart = null;

// Couleurs glassmorphiques pour le diagramme
const chartColors = [
    'rgba(255, 215, 0, 0.6)',     // Or doré
    'rgba(192, 192, 192, 0.6)',   // Argent
    'rgba(255, 140, 0, 0.6)',     // Orange doré
    'rgba(255, 69, 0, 0.6)',      // Rouge-orange
    'rgba(138, 43, 226, 0.6)',    // Violet
    'rgba(75, 0, 130, 0.6)',      // Indigo
    'rgba(0, 128, 128, 0.6)',     // Teal
    'rgba(34, 139, 34, 0.6)',     // Forest green
    'rgba(255, 20, 147, 0.6)',    // Deep pink
    'rgba(220, 20, 60, 0.6)',     // Crimson
    'rgba(255, 165, 0, 0.6)',     // Orange
    'rgba(255, 215, 0, 0.6)',     // Gold
    'rgba(218, 165, 32, 0.6)',    // Goldenrod
    'rgba(184, 134, 11, 0.6)',    // Dark goldenrod
    'rgba(139, 69, 19, 0.6)',     // Saddle brown
    'rgba(160, 82, 45, 0.6)',     // Sienna
    'rgba(205, 92, 92, 0.6)',     // Indian red
    'rgba(233, 150, 122, 0.6)',   // Dark salmon
    'rgba(255, 160, 122, 0.6)',   // Light salmon
    'rgba(255, 182, 193, 0.6)'    // Light pink
];

// Initialisation
document.addEventListener('DOMContentLoaded', function() {
    console.log('Page Analytics démarrée');
    loadAnalytics();
});

// Charger les données et initialiser les analytics
async function loadAnalytics() {
    try {
        const response = await fetch('/api/items');
        if (response.ok) {
            allItems = await response.json();
            console.log('Données chargées:', allItems.length, 'items');
            console.log('Exemple d\'item Actions:', allItems.find(item => item.category === 'Actions'));
            initializeAnalytics();
        } else {
            console.error('Erreur lors du chargement des données');
        }
    } catch (error) {
        console.error('Erreur:', error);
    }
}

// Initialiser les analytics
function initializeAnalytics() {
    updateStatistics();
    createCategorySelector();
    initializeChart();
    updateTopCategories();
    updateRecentActivity();
}

// Mettre à jour les statistiques
function updateStatistics() {
    const totalItems = allItems.length;
    const availableItems = allItems.filter(item => item.status === 'Available').length;
    const forSaleItems = allItems.filter(item => item.status === 'Available' && item.for_sale === true).length;
    const soldItems = allItems.filter(item => item.status === 'Sold').length;
    
    // Calculer la valeur totale (exclure les objets vendus, inclure les actions)
    const totalValue = allItems.reduce((sum, item) => {
        if (item.status === 'Sold') {
            return sum; // Exclure les objets vendus
        }
        
        if (item.category === 'Actions' && item.current_price && item.stock_quantity) {
            const actionValue = item.current_price * item.stock_quantity;
            console.log(`Action ${item.name}: ${item.current_price} × ${item.stock_quantity} = ${actionValue}`);
            return sum + actionValue;
        } else if (item.status === 'Available' && item.asking_price) {
            return sum + item.asking_price;
        }
        return sum;
    }, 0);
    
    console.log('Valeur totale calculée:', totalValue);
    
    // Compter les catégories uniques
    const categories = new Set(allItems.map(item => item.category).filter(Boolean));
    const totalCategories = categories.size;
    
    // Mettre à jour l'affichage
    document.getElementById('total-items').textContent = totalItems;
    document.getElementById('available-items').textContent = availableItems;
    document.getElementById('for-sale-items').textContent = forSaleItems;
    document.getElementById('sold-items').textContent = soldItems;
    document.getElementById('total-value').textContent = formatPrice(totalValue);
    document.getElementById('total-categories').textContent = totalCategories;
}

// Créer le sélecteur de catégories
function createCategorySelector() {
    const categories = [...new Set(allItems.map(item => item.category).filter(Boolean))];
    const container = document.getElementById('category-selector');
    
    container.innerHTML = categories.map(category => `
        <div class="category-chip" onclick="toggleCategory('${category}')" data-category="${category}">
            ${category}
        </div>
    `).join('');
}

// Basculer la sélection d'une catégorie
function toggleCategory(category) {
    const chip = document.querySelector(`[data-category="${category}"]`);
    
    if (selectedCategories.has(category)) {
        selectedCategories.delete(category);
        chip.classList.remove('selected');
    } else {
        selectedCategories.add(category);
        chip.classList.add('selected');
    }
    
    updateChart();
}

// Initialiser le Treemap avec D3.js
function initializeChart() {
    const container = document.getElementById('categoryChart');
    container.innerHTML = ''; // Nettoyer le contenu
    
    // Créer un SVG pour le Treemap
    const svg = d3.select(container)
        .append('svg')
        .attr('width', '100%')
        .attr('height', '400px')
        .style('background', 'transparent');
    
    categoryChart = { svg: svg, container: container };
    
    updateChart();
}

// Mettre à jour le Treemap avec D3.js
function updateChart() {
    console.log('🔄 updateChart() appelée');
    console.log('categoryChart:', categoryChart);
    console.log('categoryChart.svg:', categoryChart?.svg);
    
    if (!categoryChart || !categoryChart.svg) {
        console.error('❌ categoryChart ou svg manquant');
        return;
    }
    
    let filteredItems = allItems;
    
    // Filtrer par catégories sélectionnées
    if (selectedCategories.size > 0) {
        filteredItems = allItems.filter(item => selectedCategories.has(item.category));
    }
    
    // Grouper par catégorie et calculer les valeurs monétaires
    const categoryData = {};
    filteredItems.forEach(item => {
        if (item.category && item.status !== 'Sold') {
            if (!categoryData[item.category]) {
                categoryData[item.category] = 0;
            }
            
            let value = 0;
            if (item.category === 'Actions' && item.current_price && item.stock_quantity) {
                value = item.current_price * item.stock_quantity;
                console.log(`Treemap - Action ${item.name}: ${item.current_price} × ${item.stock_quantity} = ${value}`);
            } else if (item.status === 'Available' && item.asking_price) {
                value = item.asking_price;
            }
            
            categoryData[item.category] += value;
        }
    });
    
    console.log('📊 Données par catégorie:', categoryData);
    
    // Calculer le total pour les pourcentages
    const totalValue = Object.values(categoryData).reduce((sum, value) => sum + value, 0);
    
    // Préparer les données pour le Treemap
    const treeData = Object.entries(categoryData).map(([category, value]) => ({
        name: category,
        value: value,
        percentage: totalValue > 0 ? ((value / totalValue) * 100).toFixed(1) : 0
    }));
    
    // S'assurer que les Actions apparaissent en premier si elles existent
    const sortedData = treeData.sort((a, b) => {
        // Priorité aux Actions
        if (a.name === 'Actions' && b.name !== 'Actions') return -1;
        if (b.name === 'Actions' && a.name !== 'Actions') return 1;
        // Sinon trier par valeur décroissante
        return b.value - a.value;
    });
    
    // Nettoyer le SVG
    categoryChart.svg.selectAll('*').remove();
    
    // Si pas de données, afficher un message
    if (sortedData.length === 0) {
        console.log('⚠️ Aucune donnée pour le Treemap');
        categoryChart.svg.append('text')
            .attr('x', '50%')
            .attr('y', '50%')
            .attr('text-anchor', 'middle')
            .attr('dominant-baseline', 'middle')
            .attr('fill', '#88a0a8')
            .style('font-family', 'Inter')
            .style('font-size', '16px')
            .text('Aucune donnée disponible');
        return;
    }
    
    console.log('📈 Données pour Treemap:', sortedData);
    
    // Vérifier que D3.js est disponible
    if (typeof d3 === 'undefined') {
        console.error('❌ D3.js non disponible');
        return;
    }
    
    console.log('✅ D3.js disponible:', d3);
    
    // Créer la hiérarchie pour D3 avec un seul root
    const hierarchyData = {
        name: 'root',
        children: sortedData
    };
    
    console.log('🌳 Hiérarchie D3:', hierarchyData);
    
    const root = d3.hierarchy(hierarchyData)
        .sum(d => d.value || 0);
    
    console.log('🌳 Root D3:', root);
    
    // Créer le Treemap
    const treemap = d3.treemap()
        .size([categoryChart.container.clientWidth || 600, 400])
        .padding(2);
    
    treemap(root);
    
    // Créer les rectangles
    const nodes = categoryChart.svg.selectAll('g')
        .data(root.leaves())
        .enter()
        .append('g')
        .attr('transform', d => `translate(${d.x0},${d.y0})`);
    
    // Ajouter les rectangles avec effet glassmorphique
    nodes.append('rect')
        .attr('width', d => d.x1 - d.x0)
        .attr('height', d => d.y1 - d.y0)
        .attr('fill', (d, i) => chartColors[i % chartColors.length])
        .attr('stroke', 'rgba(255, 255, 255, 0.2)')
        .attr('stroke-width', 1)
        .style('cursor', 'pointer')
        .style('backdrop-filter', 'blur(10px)')
        .style('filter', 'drop-shadow(0 8px 32px rgba(0, 0, 0, 0.3))')
        .on('mouseover', function(event, d) {
            d3.select(this)
                .attr('stroke', 'rgba(255, 215, 0, 0.8)')
                .attr('stroke-width', 3)
                .style('filter', 'drop-shadow(0 12px 40px rgba(255, 215, 0, 0.4)) brightness(1.1)');
        })
        .on('mouseout', function(event, d) {
            d3.select(this)
                .attr('stroke', 'rgba(255, 255, 255, 0.2)')
                .attr('stroke-width', 1)
                .style('filter', 'drop-shadow(0 8px 32px rgba(0, 0, 0, 0.3))');
        });
    
    // Ajouter les labels avec effet glassmorphique
    nodes.append('text')
        .attr('x', 10)
        .attr('y', 20)
        .attr('fill', '#ffffff')
        .style('font-family', 'Inter')
        .style('font-size', '12px')
        .style('font-weight', '700')
        .style('text-shadow', '0 2px 4px rgba(0, 0, 0, 0.8)')
        .style('filter', 'drop-shadow(0 1px 2px rgba(0, 0, 0, 0.5))')
        .text(d => d.data.name);
    
    nodes.append('text')
        .attr('x', 10)
        .attr('y', 35)
        .attr('fill', '#f0f0f0')
        .style('font-family', 'Inter')
        .style('font-size', '10px')
        .style('font-weight', '600')
        .style('text-shadow', '0 1px 3px rgba(0, 0, 0, 0.8)')
        .text(d => formatPrice(d.data.value));
    
    nodes.append('text')
        .attr('x', 10)
        .attr('y', 50)
        .attr('fill', '#d4d4d4')
        .style('font-family', 'Inter')
        .style('font-size', '9px')
        .style('font-weight', '500')
        .style('text-shadow', '0 1px 2px rgba(0, 0, 0, 0.8)')
        .text(d => `(${d.data.percentage}%)`);
    
    // Mettre à jour le pourcentage
    const totalSelected = Object.values(categoryData).reduce((sum, value) => sum + value, 0);
    const totalAllValue = allItems.reduce((sum, item) => {
        if (item.status === 'Sold') {
            return sum; // Exclure les objets vendus
        }
        
        if (item.category === 'Actions' && item.current_price && item.stock_quantity) {
            return sum + (item.current_price * item.stock_quantity);
        } else if (item.status === 'Available' && item.asking_price) {
            return sum + item.asking_price;
        }
        return sum;
    }, 0);
    
    const percentage = totalAllValue > 0 ? ((totalSelected / totalAllValue) * 100).toFixed(1) : 0;
    document.getElementById('selected-percentage').textContent = `${percentage}%`;
}

// Mettre à jour les top catégories par valeur
function updateTopCategories() {
    const categoryValues = {};
    
    allItems.forEach(item => {
        if (!item.category || item.status === 'Sold') return;
        
        let value = 0;
        if (item.category === 'Actions' && item.current_price && item.stock_quantity) {
            value = item.current_price * item.stock_quantity;
        } else if (item.status === 'Available' && item.asking_price) {
            value = item.asking_price;
        }
        
        if (!categoryValues[item.category]) {
            categoryValues[item.category] = 0;
        }
        categoryValues[item.category] += value;
    });
    
    // S'assurer que les Actions apparaissent dans le top 5
    let sortedCategories = Object.entries(categoryValues)
        .sort(([,a], [,b]) => b - a);
    
    // Si Actions n'est pas dans le top 5, l'ajouter
    const actionsIndex = sortedCategories.findIndex(([category]) => category === 'Actions');
    if (actionsIndex > 4) {
        // Retirer Actions de sa position actuelle
        const actionsEntry = sortedCategories.splice(actionsIndex, 1)[0];
        // L'ajouter en position 4 (5ème place)
        sortedCategories.splice(4, 0, actionsEntry);
    }
    
    // Prendre les 5 premiers
    sortedCategories = sortedCategories.slice(0, 5);
    
    const container = document.getElementById('top-categories');
    container.innerHTML = sortedCategories.map(([category, value], index) => `
        <div class="flex items-center justify-between p-3 glass-subtle rounded-lg">
            <div class="flex items-center gap-3">
                <div class="w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold" 
                     style="background: ${chartColors[index % chartColors.length]}; color: white;">
                    ${index + 1}
                </div>
                <div>
                    <div class="font-medium">${category}</div>
                    <div class="text-sm text-slate-400">${formatPrice(value)}</div>
                </div>
            </div>
            <div class="text-right">
                <div class="text-sm text-cyan-300 font-medium">
                    ${allItems.filter(item => item.category === category).length} items
                </div>
            </div>
        </div>
    `).join('');
}

// Mettre à jour l'activité récente
function updateRecentActivity() {
    // Simuler une activité récente basée sur les données
    const recentItems = allItems
        .filter(item => item.updated_at || item.created_at)
        .sort((a, b) => {
            const dateA = new Date(a.updated_at || a.created_at);
            const dateB = new Date(b.updated_at || b.created_at);
            return dateB - dateA;
        })
        .slice(0, 5);
    
    const container = document.getElementById('recent-activity');
    container.innerHTML = recentItems.map(item => {
        const date = new Date(item.updated_at || item.created_at);
        const timeAgo = getTimeAgo(date);
        
        return `
            <div class="flex items-center gap-3 p-3 glass-subtle rounded-lg">
                <div class="w-2 h-2 rounded-full bg-cyan-400"></div>
                <div class="flex-1">
                    <div class="font-medium">${item.name}</div>
                    <div class="text-sm text-slate-400">${item.category} • ${timeAgo}</div>
                </div>
                <div class="text-right">
                    <div class="text-sm text-cyan-300">
                        ${item.status === 'Available' ? 'Disponible' : 'Vendu'}
                    </div>
                </div>
            </div>
        `;
    }).join('');
}

// Fonction utilitaire pour formater les prix
function formatPrice(price) {
    if (!price || isNaN(price)) return '0 CHF';
    return new Intl.NumberFormat('fr-CH', {
        style: 'currency',
        currency: 'CHF',
        minimumFractionDigits: 0,
        maximumFractionDigits: 0
    }).format(price);
}

// Fonction utilitaire pour calculer le temps écoulé
function getTimeAgo(date) {
    const now = new Date();
    const diffInSeconds = Math.floor((now - date) / 1000);
    
    if (diffInSeconds < 60) return 'À l\'instant';
    if (diffInSeconds < 3600) return `Il y a ${Math.floor(diffInSeconds / 60)} min`;
    if (diffInSeconds < 86400) return `Il y a ${Math.floor(diffInSeconds / 3600)}h`;
    if (diffInSeconds < 2592000) return `Il y a ${Math.floor(diffInSeconds / 86400)}j`;
    
    return date.toLocaleDateString('fr-CH');
}

// Fonction pour rafraîchir les données
async function refreshAnalytics() {
    await loadAnalytics();
}

// Fonction pour générer le PDF
async function generatePDF() {
    try {
        console.log('📄 Génération du PDF...');
        
        // Afficher un indicateur de chargement
        const button = event.target;
        const originalText = button.innerHTML;
        button.innerHTML = '⏳ Génération...';
        button.disabled = true;
        
        // Appeler l'API de génération PDF
        const response = await fetch('/api/portfolio/pdf');
        
        if (response.ok) {
            // Télécharger le PDF
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `bonvin_portfolio_${new Date().toISOString().slice(0, 10)}.pdf`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
            
            console.log('✅ PDF généré et téléchargé avec succès');
        } else {
            const error = await response.json();
            console.error('❌ Erreur génération PDF:', error);
            alert('Erreur lors de la génération du PDF: ' + (error.error || 'Erreur inconnue'));
        }
        
    } catch (error) {
        console.error('❌ Erreur:', error);
        alert('Erreur lors de la génération du PDF');
    } finally {
        // Restaurer le bouton
        const button = event.target;
        button.innerHTML = '📄 Générer PDF';
        button.disabled = false;
    }
}

// Exposer les fonctions globalement
window.toggleCategory = toggleCategory;
window.refreshAnalytics = refreshAnalytics;
window.generatePDF = generatePDF; 