// analytics.js - Page Analytics avec diagramme en anneaux
let allItems = [];
let selectedCategories = new Set();
let categoryChart = null;

// Couleurs pour le diagramme
const chartColors = [
    'rgba(0, 220, 255, 0.8)',   // Cyan
    'rgba(34, 211, 238, 0.8)',  // Light cyan
    'rgba(6, 182, 212, 0.8)',   // Darker cyan
    'rgba(8, 145, 178, 0.8)',   // Blue cyan
    'rgba(21, 94, 117, 0.8)',   // Dark blue
    'rgba(22, 163, 74, 0.8)',   // Green
    'rgba(34, 197, 94, 0.8)',   // Light green
    'rgba(16, 185, 129, 0.8)',  // Emerald
    'rgba(5, 150, 105, 0.8)',   // Dark emerald
    'rgba(168, 85, 247, 0.8)',  // Purple
    'rgba(147, 51, 234, 0.8)',  // Dark purple
    'rgba(236, 72, 153, 0.8)',  // Pink
    'rgba(244, 63, 94, 0.8)',   // Rose
    'rgba(239, 68, 68, 0.8)',   // Red
    'rgba(245, 101, 101, 0.8)', // Light red
    'rgba(251, 146, 60, 0.8)',  // Orange
    'rgba(245, 158, 11, 0.8)',  // Amber
    'rgba(234, 179, 8, 0.8)',   // Yellow
    'rgba(132, 204, 22, 0.8)',  // Lime
    'rgba(34, 197, 94, 0.8)'    // Green
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
    
    // Calculer la valeur totale
    const totalValue = allItems.reduce((sum, item) => {
        if (item.status === 'Sold' && item.sold_price) {
            return sum + item.sold_price;
        } else if (item.status === 'Available' && item.asking_price) {
            return sum + item.asking_price;
        } else if (item.category === 'Actions' && item.current_price && item.stock_quantity) {
            return sum + (item.current_price * item.stock_quantity);
        }
        return sum;
    }, 0);
    
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

// Initialiser le diagramme
function initializeChart() {
    const ctx = document.getElementById('categoryChart').getContext('2d');
    
    categoryChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: [],
            datasets: [{
                data: [],
                backgroundColor: chartColors,
                borderColor: 'rgba(0, 220, 255, 0.3)',
                borderWidth: 2,
                hoverBorderColor: 'rgba(0, 220, 255, 0.8)',
                hoverBorderWidth: 3
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        color: '#e0e6e7',
                        font: {
                            family: 'Inter',
                            size: 12
                        },
                        padding: 20,
                        usePointStyle: true,
                        pointStyle: 'circle'
                    }
                },
                tooltip: {
                    backgroundColor: 'rgba(10, 40, 50, 0.9)',
                    titleColor: '#00e5ff',
                    bodyColor: '#e0e6e7',
                    borderColor: 'rgba(0, 220, 255, 0.3)',
                    borderWidth: 1,
                    cornerRadius: 8,
                    displayColors: true,
                    callbacks: {
                        label: function(context) {
                            const label = context.label || '';
                            const value = context.parsed;
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = ((value / total) * 100).toFixed(1);
                            return `${label}: ${value} (${percentage}%)`;
                        }
                    }
                }
            },
            animation: {
                animateRotate: true,
                animateScale: true,
                duration: 1000,
                easing: 'easeOutQuart'
            },
            cutout: '60%',
            radius: '90%'
        }
    });
    
    updateChart();
}

// Mettre à jour le diagramme
function updateChart() {
    if (!categoryChart) return;
    
    let filteredItems = allItems;
    
    // Filtrer par catégories sélectionnées
    if (selectedCategories.size > 0) {
        filteredItems = allItems.filter(item => selectedCategories.has(item.category));
    }
    
    // Grouper par catégorie
    const categoryData = {};
    filteredItems.forEach(item => {
        if (item.category) {
            if (!categoryData[item.category]) {
                categoryData[item.category] = 0;
            }
            categoryData[item.category]++;
        }
    });
    
    // Préparer les données pour Chart.js
    const labels = Object.keys(categoryData);
    const data = Object.values(categoryData);
    
    // Mettre à jour le diagramme
    categoryChart.data.labels = labels;
    categoryChart.data.datasets[0].data = data;
    categoryChart.data.datasets[0].backgroundColor = labels.map((_, index) => 
        chartColors[index % chartColors.length]
    );
    
    categoryChart.update();
    
    // Mettre à jour le pourcentage
    const totalSelected = data.reduce((sum, value) => sum + value, 0);
    const totalAll = allItems.length;
    const percentage = totalAll > 0 ? ((totalSelected / totalAll) * 100).toFixed(1) : 0;
    
    document.getElementById('selected-percentage').textContent = `${percentage}%`;
}

// Mettre à jour les top catégories par valeur
function updateTopCategories() {
    const categoryValues = {};
    
    allItems.forEach(item => {
        if (!item.category) return;
        
        let value = 0;
        if (item.status === 'Sold' && item.sold_price) {
            value = item.sold_price;
        } else if (item.status === 'Available' && item.asking_price) {
            value = item.asking_price;
        } else if (item.category === 'Actions' && item.current_price && item.stock_quantity) {
            value = item.current_price * item.stock_quantity;
        }
        
        if (!categoryValues[item.category]) {
            categoryValues[item.category] = 0;
        }
        categoryValues[item.category] += value;
    });
    
    // Trier par valeur décroissante
    const sortedCategories = Object.entries(categoryValues)
        .sort(([,a], [,b]) => b - a)
        .slice(0, 5);
    
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

// Exposer les fonctions globalement
window.toggleCategory = toggleCategory;
window.refreshAnalytics = refreshAnalytics; 