// script.js - Version complète avec toutes les corrections
// --- Variables globales ---
let allItems = [];
let currentMainFilter = 'all'; // Filtre principal simplifié (all, Available, ForSale, Sold)
let selectedCategories = new Set(); // Utilisation d'un Set pour les catégories sélectionnées
let currentSearch = '';
let currentViewMode = 'cards';
let conversationHistory = [];
let isTyping = false;
let cardObserver = null;
let stockPriceUpdateTimer = null;
let stockPriceUpdateErrors = {}; // Pour tracker les erreurs par symbole

// --- Notifications ---
function showNotification(message, isError = false) {
    const notification = document.createElement('div');
    notification.className = `fixed top-5 right-5 text-white px-6 py-3 rounded-xl shadow-lg transition-transform transform translate-x-full ${isError ? 'bg-red-600/80' : 'bg-green-600/80'} backdrop-blur-md border ${isError ? 'border-red-500' : 'border-green-500'} z-50`;
    notification.textContent = message;
    document.body.appendChild(notification);

    setTimeout(() => {
        notification.classList.remove('translate-x-full');
    }, 100);

    setTimeout(() => {
        notification.classList.add('translate-x-full');
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 300);
    }, 5000);
}

function showError(message) {
    showNotification(message, true);
}

function showSuccess(message) {
    showNotification(message, false);
}

// --- Initialisation sécurisée ---
document.addEventListener('DOMContentLoaded', function() {
    console.log('Application démarrée');
    
    try {
        // Vérifier que les éléments existent avant d'ajouter les listeners
        const itemForm = document.getElementById('item-form');
        if (itemForm) {
            itemForm.addEventListener('submit', handleFormSubmit);
        }

        const chatbotInput = document.getElementById('chatbot-input');
        if (chatbotInput) {
            chatbotInput.addEventListener('keypress', function(e) {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    handleChatSubmit(e);
                }
            });
        }

        const categorySelect = document.getElementById('item-category');
        if (categorySelect) {
            categorySelect.addEventListener('change', function() {
                toggleRealEstateFields();
                toggleStockFields();
            });
        }

        // Event listener pour le checkbox "En vente"
        const forSaleCheckbox = document.getElementById('item-for-sale');
        if (forSaleCheckbox) {
            forSaleCheckbox.addEventListener('change', toggleSaleProgressFields);
        }

        // Event listener pour le bouton de mise à jour manuelle du prix
        const updatePriceBtn = document.getElementById('update-current-price-btn');
        if (updatePriceBtn) {
            updatePriceBtn.addEventListener('click', updateCurrentPriceManually);
        }

        // Initialiser l'observer seulement si supporté
        if (window.IntersectionObserver) {
            initCardObserver();
        }

        // Charger les données
        loadItems();
        
        // Initialiser les filtres simplifiés
        filterByMainStatus('all');
        setViewMode('cards');

        // Ajouter les actions rapides du chatbot
        setTimeout(addQuickActions, 1000);
        
        // Démarrer la mise à jour automatique des prix (avec gestion d'erreur améliorée)
        startStockPriceUpdates();
        
        // Forcer la mise à jour des prix au refresh de la page
        window.addEventListener('beforeunload', function() {
            // Nettoyer le timer avant de quitter
            if (stockPriceUpdateTimer) {
                clearInterval(stockPriceUpdateTimer);
            }
        });
        
        // Mise à jour forcée au focus de la page (quand l'utilisateur revient sur l'onglet)
        window.addEventListener('focus', function() {
            console.log('Page refocusée - mise à jour des prix...');
            forceUpdateStockPrices();
        });
        
        // Détecter le refresh de la page et forcer la mise à jour
        let pageAccessedByReload = sessionStorage.getItem('pageAccessedByReload');
        if (pageAccessedByReload === null) {
            sessionStorage.setItem('pageAccessedByReload', 'true');
        } else {
            sessionStorage.removeItem('pageAccessedByReload');
            // C'est un refresh, forcer la mise à jour des prix
            console.log('Refresh détecté - mise à jour forcée des prix...');
            setTimeout(() => forceUpdateStockPrices(), 1000);
        }
        
    } catch (error) {
        console.error('Erreur lors de l\'initialisation:', error);
        showError('Erreur lors du chargement de l\'interface');
    }
});

function toggleRealEstateFields() {
    const categorySelect = document.getElementById('item-category');
    if (!categorySelect) return;
    
    const category = categorySelect.value;
    const isRealEstate = category === 'Appartements / maison';
    
    const surfaceField = document.getElementById('surface-field');
    const rentalField = document.getElementById('rental-income-field');
    
    if (surfaceField) {
        surfaceField.style.display = isRealEstate ? 'block' : 'none';
    }
    if (rentalField) {
        rentalField.style.display = isRealEstate ? 'block' : 'none';
    }
}

function toggleStockFields() {
    const categorySelect = document.getElementById('item-category');
    if (!categorySelect) return;
    
    const category = categorySelect.value;
    const isStock = category === 'Actions';
    
    const stockFields = document.getElementById('stock-fields');
    const currentPriceField = document.getElementById('current-price-field');
    
    if (stockFields) {
        stockFields.style.display = isStock ? 'block' : 'none';
    }
    if (currentPriceField) {
        currentPriceField.style.display = isStock ? 'block' : 'none';
    }
}

function toggleSaleProgressFields() {
    const forSaleCheckbox = document.getElementById('item-for-sale');
    const progressSection = document.getElementById('sale-progress-section');
    
    if (forSaleCheckbox && progressSection) {
        progressSection.style.display = forSaleCheckbox.checked ? 'block' : 'none';
    }
}

// --- Fonction pour mettre à jour manuellement le prix actuel ---
function updateCurrentPriceManually() {
    const currentPriceInput = document.getElementById('item-current-price');
    const askingPriceInput = document.getElementById('item-asking-price');
    const stockQuantityInput = document.getElementById('item-stock-quantity');
    
    if (!currentPriceInput || !askingPriceInput || !stockQuantityInput) return;
    
    const currentPrice = parseFloat(currentPriceInput.value);
    const quantity = parseInt(stockQuantityInput.value) || 1;
    
    if (currentPrice && quantity) {
        const totalValue = currentPrice * quantity;
        askingPriceInput.value = totalValue.toFixed(2);
        showSuccess(`Valeur totale mise à jour: ${formatPrice(totalValue)}`);
    }
}

// --- Chargement des données ---
async function loadItems() {
    displaySkeletonCards();
    try {
        const response = await fetch('/api/items');
        if (response.ok) {
            allItems = await response.json();
            console.log(`${allItems.length} objets chargés`);
            
            // S'assurer que currentMainFilter est initialisé
            if (!currentMainFilter) {
                currentMainFilter = 'all';
            }
            
            updateStatistics();
            updateStatusCounts();
            updateCategoryFilters();
            displayItems();
        } else {
            const err = await response.json();
            showError(`Erreur chargement: ${err.error || 'Erreur serveur'}`);
        }
    } catch (error) {
        console.error('Erreur:', error);
        showError('Impossible de se connecter au serveur.');
    }
}

// --- Fonction pour obtenir les items filtrés actuels ---
function getFilteredItems() {
    let filteredItems = allItems;
    
    // S'assurer que currentMainFilter a une valeur par défaut
    if (!currentMainFilter) {
        currentMainFilter = 'all';
    }
    
    // Appliquer le filtre de catégories si des catégories sont sélectionnées
    if (selectedCategories.size > 0) {
        filteredItems = filteredItems.filter(item => 
            item.category && selectedCategories.has(item.category)
        );
    }
    
    // Appliquer le filtre principal (status)
    if (currentMainFilter === 'Available') {
        filteredItems = filteredItems.filter(item => item.status === 'Available' && !item.for_sale);
    } else if (currentMainFilter === 'ForSale') {
        filteredItems = filteredItems.filter(item => item.status === 'Available' && item.for_sale === true);
    } else if (currentMainFilter === 'Sold') {
        filteredItems = filteredItems.filter(item => item.status === 'Sold');
    }
    // 'all' n'applique aucun filtre supplémentaire
    
    return filteredItems;
}

// --- Statistiques avec filtrage ---
function updateStatistics() {
    const filteredItems = getFilteredItems();
    const stats = calculateStats(filteredItems);
    
    const elements = {
        'stat-total': stats.total,
        'stat-vendus': stats.vendus,
        'stat-disponibles': stats.disponibles,
        'stat-valeur-vente': stats.valeur_vente,
        'stat-valeur-dispo': stats.valeur_disponible,
        'stat-age-moyen': stats.age_moyen
    };
    
    for (const [id, value] of Object.entries(elements)) {
        const element = document.getElementById(id);
        if (element) {
            if (id.includes('valeur')) {
                animateValue(element, 0, value, 2000, true);
            } else if (id === 'stat-age-moyen') {
                animateValue(element, 0, value, 1500, false, ' ans');
            } else {
                animateValue(element, 0, value);
            }
        }
    }
}

function calculateStats(items) {
    const total = items.length;
    const vendus = items.filter(item => item.status === 'Sold').length;
    const disponibles = items.filter(item => item.status === 'Available').length;
    const valeur_vente = items.filter(item => item.status === 'Sold').reduce((sum, item) => sum + (item.sold_price || 0), 0);
    const valeur_disponible = items.filter(item => item.status === 'Available').reduce((sum, item) => sum + (item.asking_price || 0), 0);
    const currentYear = new Date().getFullYear();
    const years = items.filter(item => item.construction_year).map(item => item.construction_year);
    const age_moyen = years.length > 0 ? Math.round(years.reduce((sum, year) => sum + (currentYear - year), 0) / years.length) : 0;
    return { total, vendus, disponibles, valeur_vente, valeur_disponible, age_moyen };
}

function animateValue(element, start, end, duration = 1500, isPrice = false, suffix = '') {
    if (!element || start === end) {
        if(element) element.textContent = isPrice ? formatPrice(end) : end + suffix;
        return;
    }
    let startTimestamp = null;
    const step = (timestamp) => {
        if (!startTimestamp) startTimestamp = timestamp;
        const progress = Math.min((timestamp - startTimestamp) / duration, 1);
        const currentValue = Math.floor(progress * (end - start) + start);
        element.textContent = isPrice ? formatPrice(currentValue) : currentValue + suffix;
        if (progress < 1) {
            window.requestAnimationFrame(step);
        }
    };
    window.requestAnimationFrame(step);
}

function formatPrice(price) {
    if (price === null || price === undefined) return 'N/A';
    return new Intl.NumberFormat('fr-CH', { 
        style: 'currency', 
        currency: 'CHF', 
        minimumFractionDigits: 0, 
        maximumFractionDigits: 0 
    }).format(price);
}

// --- FILTRES SIMPLIFIÉS (4 filtres uniquement) ---
function filterByMainStatus(status) {
    currentMainFilter = status;
    
    // Mettre à jour les boutons
    document.querySelectorAll('.main-filter-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    
    const activeButton = document.querySelector(`.main-filter-btn[data-main-status="${status}"]`);
    if (activeButton) {
        activeButton.classList.add('active');
    }
    
    // Mettre à jour les statistiques ET les compteurs
    updateStatistics();
    updateStatusCounts();
    displayItems();
}

function updateStatusCounts() {
    const filteredItems = getFilteredItems();
    
    const counts = {
        'count-all': filteredItems.length,
        'count-available': filteredItems.filter(item => item.status === 'Available' && !item.for_sale).length,
        'count-for-sale': filteredItems.filter(item => item.status === 'Available' && item.for_sale === true).length,
        'count-sold': filteredItems.filter(item => item.status === 'Sold').length
    };
    
    for (const [id, count] of Object.entries(counts)) {
        const element = document.getElementById(id);
        if (element) {
            element.textContent = count;
        }
    }
}

function updateCategoryFilters() {
    const categories = [...new Set(allItems.map(item => item.category).filter(cat => cat))].sort();
    const container = document.getElementById('category-filters');
    if (!container) return;
    
    // Ajouter un bouton "Effacer les filtres" si des catégories sont sélectionnées
    let html = '';
    if (selectedCategories.size > 0) {
        html += '<button onclick="clearCategoryFilters()" class="category-btn glass glowing-element px-3 py-2 rounded-lg text-sm transition-transform bg-red-500/20 border-red-400/30 text-red-300 hover:bg-red-500/30">Effacer filtres</button>';
    }
    
    // Ajouter les boutons de catégories
    categories.forEach(category => {
        const isSelected = selectedCategories.has(category);
        const selectedClass = isSelected ? 'ring-2 ring-cyan-400 bg-cyan-400/20' : '';
        html += `<button onclick="toggleCategory('${category}')" class="category-btn glass glowing-element px-3 py-2 rounded-lg text-sm transition-transform ${selectedClass}" data-category="${category}">${category}</button>`;
    });
    
    container.innerHTML = html;
}

function toggleCategory(category) {
    if (selectedCategories.has(category)) {
        selectedCategories.delete(category);
    } else {
        selectedCategories.add(category);
    }
    
    // Mettre à jour l'affichage des boutons
    updateCategoryFilters();
    
    // Mettre à jour les statistiques et les compteurs
    updateStatistics();
    updateStatusCounts();
    
    // Rafraîchir l'affichage
    displayItems();
}

function clearCategoryFilters() {
    selectedCategories.clear();
    updateCategoryFilters();
    updateStatistics();
    updateStatusCounts();
    displayItems();
}

function setViewMode(mode) {
    currentViewMode = mode;
    
    // Mettre à jour les boutons de vue
    document.querySelectorAll('.view-btn').forEach(btn => {
        btn.classList.remove('ring-2', 'ring-cyan-400');
    });
    
    const activeButton = document.getElementById(`view-btn-${mode}`);
    if (activeButton) {
        activeButton.classList.add('ring-2', 'ring-cyan-400');
    }
    
    displayItems();
}

function handleSearch() {
    const searchInput = document.getElementById('search-input');
    if (searchInput) {
        currentSearch = searchInput.value.toLowerCase().trim();
        displayItems();
    }
}

// --- Affichage avec logique simplifiée ---
function displayItems() {
    let filteredItems = getFilteredItems();
    
    // Filtrage principal simplifié
    if (currentMainFilter === 'Available') {
        filteredItems = filteredItems.filter(item => item.status === 'Available' && !item.for_sale);
    } else if (currentMainFilter === 'ForSale') {
        filteredItems = filteredItems.filter(item => item.status === 'Available' && item.for_sale === true);
    } else if (currentMainFilter === 'Sold') {
        filteredItems = filteredItems.filter(item => item.status === 'Sold');
    }
    // 'all' n'applique aucun filtre supplémentaire
    
    if (currentSearch) {
        filteredItems = filteredItems.filter(item => 
            (item.name && item.name.toLowerCase().includes(currentSearch)) ||
            (item.category && item.category.toLowerCase().includes(currentSearch)) ||
            (item.description && item.description.toLowerCase().includes(currentSearch)) ||
            (item.intermediary && item.intermediary.toLowerCase().includes(currentSearch)) ||
            (item.buyer_contact && item.buyer_contact.toLowerCase().includes(currentSearch)) ||
            (item.sale_progress && item.sale_progress.toLowerCase().includes(currentSearch))
        );
    }
    
    const container = document.getElementById('items-container');
    if (!container) return;
    
    container.innerHTML = '';

    if (currentViewMode === 'list') {
        displayItemsAsList(container, filteredItems);
    } else {
        displayItemsAsCards(container, filteredItems);
    }
    
    // Observer les nouvelles cartes
    if (cardObserver) {
        const cards = document.querySelectorAll('.floating-card');
        cards.forEach(card => {
            try {
                cardObserver.observe(card);
            } catch (error) {
                console.warn('Erreur observer:', error);
            }
        });
    }
}

// --- Gestion améliorée de la mise à jour des prix des actions ---
function startStockPriceUpdates() {
    // Mise à jour initiale immédiate
    updateStockPrices();
    
    // Puis toutes les 10 minutes (600000ms) pour éviter les rate limits
    if (stockPriceUpdateTimer) {
        clearInterval(stockPriceUpdateTimer);
    }
    stockPriceUpdateTimer = setInterval(updateStockPrices, 600000);
}

async function updateStockPrices(forceRefresh = false) {
    const stockItems = allItems.filter(item => item.category === 'Actions' && item.stock_symbol);
    
    if (stockItems.length === 0) return;
    
    console.log(`Mise à jour des prix pour ${stockItems.length} actions...${forceRefresh ? ' (refresh forcé)' : ''}`);
    
    for (const item of stockItems) {
        // Vérifier si on a déjà eu trop d'erreurs pour ce symbole (augmenté à 5)
        const errorCount = stockPriceUpdateErrors[item.stock_symbol] || 0;
        if (errorCount >= 5) {
            console.log(`Ignorer ${item.stock_symbol} - trop d'erreurs (${errorCount})`);
            continue;
        }
        
        try {
            const url = forceRefresh 
                ? `/api/stock-price/${item.stock_symbol}?force_refresh=true`
                : `/api/stock-price/${item.stock_symbol}`;
            const response = await fetch(url);
            
            if (response.status === 429) {
                // Rate limit atteint - retry intelligent
                console.warn(`Rate limit atteint pour ${item.stock_symbol}, retry dans 3 secondes...`);
                stockPriceUpdateErrors[item.stock_symbol] = (errorCount || 0) + 1;
                
                // Retry après 3 secondes au lieu de 5
                await new Promise(resolve => setTimeout(resolve, 3000));
                continue;
            }
            
            if (response.ok) {
                const data = await response.json();
                
                // Calculer la valeur totale
                const totalValue = data.price_chf * (item.stock_quantity || 1);
                
                // Mettre à jour l'objet en mémoire
                item.current_price = data.price_chf;
                item.asking_price = totalValue;
                item.last_price_update = data.last_update;
                
                // Réinitialiser le compteur d'erreur pour ce symbole
                delete stockPriceUpdateErrors[item.stock_symbol];
                
                // Mettre à jour l'affichage si l'objet est visible
                updateStockCardDisplay(item.id, data);
            } else {
                console.error(`Erreur ${response.status} pour ${item.stock_symbol}`);
                stockPriceUpdateErrors[item.stock_symbol] = (errorCount || 0) + 1;
            }
        } catch (error) {
            console.error(`Erreur mise à jour ${item.stock_symbol}:`, error);
            stockPriceUpdateErrors[item.stock_symbol] = (errorCount || 0) + 1;
        }
        
                        // Délai plus long pour éviter rate limiting Yahoo Finance
                const delay = item.stock_exchange && ['SWX', 'SIX', 'SWISS', 'CH'].includes(item.stock_exchange.toUpperCase()) ? 8000 : 3000;
                await new Promise(resolve => setTimeout(resolve, delay));
    }
    
    // Rafraîchir les statistiques si des prix ont été mis à jour
    updateStatistics();
}

// Fonction pour forcer la mise à jour immédiate des prix (ignore le cache)
async function forceUpdateStockPrices() {
    console.log('Mise à jour des prix (cache ignoré)...');
    showNotification('Mise à jour des prix en cours...', false);
    
    // Réinitialiser les erreurs pour permettre de nouveaux essais
    stockPriceUpdateErrors = {};
    
    // Lancer la mise à jour immédiatement avec force_refresh=true
    await updateStockPrices(true);
    
    showNotification('Prix mis à jour !', false);
}

// Fonction pour vider le cache côté serveur
async function clearStockPriceCache() {
    try {
        console.log('Vidage du cache des prix des actions...');
        showNotification('Vidage du cache en cours...', false);
        
        const response = await fetch('/api/stock-price/cache/clear', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        if (response.ok) {
            const result = await response.json();
            console.log('Cache vidé:', result);
            showNotification(`Cache vidé (${result.cache_size_before} entrées supprimées)`, false);
        } else {
            throw new Error(`Erreur ${response.status}`);
        }
    } catch (error) {
        console.error('Erreur lors du vidage du cache:', error);
        showNotification('Erreur lors du vidage du cache', true);
    }
}

// Fonction pour afficher le statut du cache
async function showCacheStatus() {
    try {
        const response = await fetch('/api/stock-price/cache/status');
        
        if (response.ok) {
            const status = await response.json();
            console.log('Statut du cache:', status);
            
            // Afficher dans une notification détaillée
            const message = `Cache: ${status.cache_size} entrées\nExpirées: ${status.expired_entries}\nDurée: ${Math.round(status.cache_duration/60)}min`;
            showNotification(message, false);
        } else {
            throw new Error(`Erreur ${response.status}`);
        }
    } catch (error) {
        console.error('Erreur lors de la récupération du statut du cache:', error);
        showNotification('Erreur lors de la récupération du statut', true);
    }
}

// Fonction pour mettre à jour l'affichage d'une carte action
function updateStockCardDisplay(itemId, stockData) {
    const card = document.querySelector(`[data-item-id="${itemId}"]`);
    if (!card) return;
    
    // Ajouter un indicateur de prix en temps réel
    const priceElement = card.querySelector('.stock-price-live');
    if (priceElement) {
        const changeClass = stockData.change_percent > 0 ? 'text-green-400' : 'text-red-400';
        const arrow = stockData.change_percent > 0 ? '↑' : '↓';
        
        // Formater les volumes
        const formatVolume = (volume) => {
            if (volume === 'N/A' || !volume) return 'N/A';
            if (volume > 1e9) return `${(volume/1e9).toFixed(2)}B`;
            if (volume > 1e6) return `${(volume/1e6).toFixed(2)}M`;
            if (volume > 1e3) return `${(volume/1e3).toFixed(2)}K`;
            return volume.toString();
        };
        
        // Formater les prix
        const formatPriceValue = (price) => {
            if (price === 'N/A' || !price) return 'N/A';
            return parseFloat(price).toFixed(2);
        };
        
        priceElement.innerHTML = `
            <div class="space-y-3">
                <!-- Prix principal -->
                <div class="flex items-center justify-between">
                    <div class="flex items-center gap-2">
                        <span class="text-lg font-bold">${formatPrice(stockData.price_chf)}</span>
                        <span class="text-xs text-slate-400 font-medium">${stockData.currency}</span>
                    </div>
                    <span class="${changeClass} text-sm font-semibold">
                        ${arrow} ${Math.abs(stockData.change_percent).toFixed(2)}%
                    </span>
                </div>
                
                <!-- Informations supplémentaires -->
                <div class="grid grid-cols-2 gap-2 text-xs">
                    <div class="glass-subtle p-2 rounded-lg">
                        <div class="text-cyan-300 font-medium">Volume</div>
                        <div class="text-slate-300">${formatVolume(stockData.volume)}</div>
                    </div>
                    <div class="glass-subtle p-2 rounded-lg">
                        <div class="text-cyan-300 font-medium">P/E Ratio</div>
                        <div class="text-slate-300">${stockData.pe_ratio !== 'N/A' ? parseFloat(stockData.pe_ratio).toFixed(1) : 'N/A'}</div>
                    </div>
                    <div class="glass-subtle p-2 rounded-lg">
                        <div class="text-cyan-300 font-medium">52W High</div>
                        <div class="text-slate-300">${formatPriceValue(stockData.fifty_two_week_high)}</div>
                    </div>
                    <div class="glass-subtle p-2 rounded-lg">
                        <div class="text-cyan-300 font-medium">52W Low</div>
                        <div class="text-slate-300">${formatPriceValue(stockData.fifty_two_week_low)}</div>
                    </div>
                </div>
                
                <!-- Source et timestamp -->
                <div class="text-xs text-slate-500 text-center">
                    ${stockData.source} • ${new Date(stockData.last_update).toLocaleTimeString()}
                </div>
            </div>
        `;
        
        // Retirer l'animation de chargement
        priceElement.classList.remove('animate-pulse');
    }
}

function displaySkeletonCards() {
    const container = document.getElementById('items-container');
    if (!container) return;
    
    const skeletonHTML = '<div class="skeleton-card glass"><div class="skeleton-line w-3/4 h-6 mb-4"></div><div class="skeleton-line w-1/2 h-4 mb-2"></div><div class="skeleton-line w-2/3 h-4"></div></div>';
    container.innerHTML = `<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-8">${skeletonHTML.repeat(8)}</div>`;
}

function displayItemsAsCards(container, items) {
    if (items.length === 0) {
        container.innerHTML = '<div class="text-center text-gray-400 py-8 col-span-full">Aucun objet trouvé.</div>';
        return;
    }
    
    const grid = document.createElement('div');
    grid.className = 'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-8';
    grid.innerHTML = items.map(createItemCardHTML).join('');
    container.appendChild(grid);
}

function displayItemsAsList(container, items) {
    if (items.length === 0) {
        container.innerHTML = '<div class="text-center text-gray-400 py-8">Aucun objet trouvé.</div>';
        return;
    }
    
    const tableHTML = `
        <div class="glass-dark glowing-element overflow-hidden">
            <div class="overflow-x-auto">
                <table class="w-full text-left">
                    <thead class="bg-black bg-opacity-20">
                        <tr>
                            <th class="p-4 font-semibold">Nom</th>
                            <th class="p-4 font-semibold hidden md:table-cell">Catégorie</th>
                            <th class="p-4 font-semibold">Statut</th>
                            <th class="p-4 font-semibold hidden lg:table-cell">Prix</th>
                            <th class="p-4 font-semibold text-right">Actions</th>
                        </tr>
                    </thead>
                    <tbody class="divide-y divide-cyan-900/20">
                        ${items.map(createItemListHTML).join('')}
                    </tbody>
                </table>
            </div>
        </div>
    `;
    container.innerHTML = tableHTML;
}

function createItemCardHTML(item) {
    const isForSale = item.status === 'Available' && item.for_sale === true;
    const isSold = item.status === 'Sold';
    
    let cardClass = isForSale ? 'card-for-sale' : isSold ? 'card-sold' : '';
    
    // Statut de progression de vente
    let saleStatusBadge = '';
    if (isForSale && item.sale_status && item.sale_status !== 'initial') {
        const statusLabels = {
            'presentation': 'Présentation',
            'intermediary': 'Intermédiaires',
            'inquiries': 'Demandes',
            'viewing': 'Visites',
            'negotiation': 'Négociation',
            'offer_received': 'Offre reçue',
            'offer_accepted': 'Offre acceptée',
            'paperwork': 'Formalités',
            'completed': 'Finalisé'
        };
        saleStatusBadge = `<span class="status-sale-progress px-2 py-1 rounded-full text-xs font-semibold mt-1">${statusLabels[item.sale_status] || item.sale_status}</span>`;
    }
    
    // Section prix pour les actions avec gestion d'erreur
    let stockPriceSection = '';
    if (item.category === 'Actions' && item.stock_symbol) {
        const hasError = stockPriceUpdateErrors[item.stock_symbol] >= 3;
        
        if (hasError && item.current_price) {
            // Si on a des erreurs mais un prix existant, l'afficher avec un avertissement
            stockPriceSection = `
                <div class="stock-price-live mt-3 p-2 bg-black/20 rounded-lg">
                    <div class="flex items-center gap-2">
                        <span class="text-lg font-bold">${formatPrice(item.current_price)}</span>
                        <span class="text-orange-400 text-xs">⚠️ Mise à jour indisponible</span>
                    </div>
                    <div class="text-xs text-gray-500">Dernier prix connu</div>
                </div>
            `;
        } else if (hasError) {
            // Si on a des erreurs et pas de prix
            stockPriceSection = `
                <div class="stock-price-live mt-3 p-2 bg-red-900/20 rounded-lg">
                    <div class="flex items-center gap-2">
                        <span class="text-sm text-red-400">❌ Prix indisponible</span>
                    </div>
                    <div class="text-xs text-gray-500">Mise à jour manuelle requise</div>
                </div>
            `;
        } else {
            // Cas normal - en attente ou avec prix
            stockPriceSection = `
                <div class="stock-price-live mt-3 p-3 bg-black/20 rounded-lg">
                    <div class="space-y-3">
                        <!-- Prix principal -->
                        <div class="flex items-center justify-between">
                            <div class="flex items-center gap-2">
                                <span class="text-lg font-bold animate-pulse">Chargement...</span>
                                <span class="text-xs text-slate-400 font-medium">--</span>
                            </div>
                            <span class="text-sm text-slate-400">--</span>
                        </div>
                        
                        <!-- Informations supplémentaires -->
                        <div class="grid grid-cols-2 gap-2 text-xs">
                            <div class="glass-subtle p-2 rounded-lg">
                                <div class="text-cyan-300 font-medium">Volume</div>
                                <div class="text-slate-300 animate-pulse">--</div>
                            </div>
                            <div class="glass-subtle p-2 rounded-lg">
                                <div class="text-cyan-300 font-medium">P/E Ratio</div>
                                <div class="text-slate-300 animate-pulse">--</div>
                            </div>
                            <div class="glass-subtle p-2 rounded-lg">
                                <div class="text-cyan-300 font-medium">52W High</div>
                                <div class="text-slate-300 animate-pulse">--</div>
                            </div>
                            <div class="glass-subtle p-2 rounded-lg">
                                <div class="text-cyan-300 font-medium">52W Low</div>
                                <div class="text-slate-300 animate-pulse">--</div>
                            </div>
                        </div>
                        
                        <!-- Source et timestamp -->
                        <div class="text-xs text-slate-500 text-center">
                            Chargement en cours...
                        </div>
                    </div>
                </div>
            `;
        }
        

    }
    
    return `
        <div class="glass floating-card glowing-element ${cardClass} p-6 flex flex-col justify-between" data-item-id="${item.id}" onclick="editItem(${item.id})">
            <div>
                <div class="flex justify-between items-start mb-4">
                    <h3 class="text-xl font-bold truncate pr-2">${item.name}</h3>
                    <div class="flex flex-col items-end gap-1 flex-shrink-0">
                        <span class="${item.status === 'Available' ? 'status-available' : 'status-sold'} px-3 py-1 rounded-full text-xs font-semibold whitespace-nowrap">
                            ${item.status === 'Available' ? 'Disponible' : 'Vendu'}
                        </span>
                        ${isForSale ? '<span class="status-for-sale px-2 py-1 rounded-full text-xs font-semibold">EN VENTE</span>' : ''}
                        ${saleStatusBadge}
                    </div>
                </div>
                <div class="space-y-2 text-sm mb-4 text-slate-400">
                    <div>Catégorie: ${item.category || 'N/A'}</div>
                    ${item.construction_year ? `<div>Année: ${item.construction_year}</div>` : ''}
                    ${item.condition ? `<div>État: ${item.condition}</div>` : ''}
                    ${item.status === 'Available' && item.asking_price ? `<div>Prix: ${formatPrice(item.asking_price)}</div>` : ''}
                    ${item.current_offer ? `<div>Offre: ${formatPrice(item.current_offer)}</div>` : ''}
                    ${item.status === 'Sold' && item.sold_price ? `<div>Vendu: ${formatPrice(item.sold_price)}</div>` : ''}
                    ${item.sale_progress ? `<div class="text-xs text-cyan-300">${item.sale_progress.substring(0, 50)}${item.sale_progress.length > 50 ? '...' : ''}</div>` : ''}
                    ${item.intermediary ? `<div class="text-xs text-purple-300">Agent: ${item.intermediary}</div>` : ''}
                    ${item.stock_symbol ? `<div class="text-xs text-blue-300">Symbole: ${item.stock_symbol} (${item.stock_quantity || '?'} actions)</div>` : ''}
                </div>
                
                ${stockPriceSection}
            </div>
            <div class="flex gap-2 mt-4">
                <button onclick="event.stopPropagation(); getMarketPrice(this, ${item.id})" class="glowing-element glass px-3 py-2 rounded-lg text-xs hover:scale-105 transition-transform flex-1">IA Prix</button>
                <button onclick="event.stopPropagation(); editItem(${item.id})" class="glowing-element glass px-3 py-2 rounded-lg text-xs hover:scale-105 transition-transform">Modifier</button>
                <button onclick="event.stopPropagation(); confirmDeleteItem(${item.id})" class="glowing-element status-sold px-3 py-2 rounded-lg text-xs hover:scale-105 transition-transform">Supprimer</button>
            </div>
        </div>
    `;
}

function createItemListHTML(item) {
    const isForSale = item.status === 'Available' && item.for_sale === true;
    
    let saleStatusBadge = '';
    if (isForSale && item.sale_status && item.sale_status !== 'initial') {
        const statusLabels = {
            'presentation': 'P',
            'intermediary': 'I',
            'inquiries': 'D',
            'viewing': 'V',
            'negotiation': 'N',
            'offer_received': 'O',
            'offer_accepted': 'A',
            'paperwork': 'F',
            'completed': 'C'
        };
        saleStatusBadge = `<span class="status-sale-progress px-2 py-1 rounded-full text-xs font-semibold ml-2">${statusLabels[item.sale_status] || item.sale_status}</span>`;
    }
    
    return `
        <tr class="hover:bg-black hover:bg-opacity-20 transition-colors cursor-pointer" onclick="editItem(${item.id})">
            <td class="p-4 font-semibold">
                ${item.name}
                ${isForSale ? '<span class="status-for-sale px-2 py-1 rounded-full text-xs font-semibold ml-2">EN VENTE</span>' : ''}
                ${saleStatusBadge}
            </td>
            <td class="p-4 hidden md:table-cell text-slate-400">${item.category || 'N/A'}</td>
            <td class="p-4">
                <span class="${item.status === 'Available' ? 'status-available' : 'status-sold'} px-3 py-1 rounded-full text-xs font-semibold">
                    ${item.status === 'Available' ? 'Disponible' : 'Vendu'}
                </span>
            </td>
            <td class="p-4 hidden lg:table-cell text-slate-400">
                ${formatPrice(item.status === 'Available' ? item.asking_price : item.sold_price)}
                ${item.current_offer ? `<br><small class="text-orange-300">Offre: ${formatPrice(item.current_offer)}</small>` : ''}
            </td>
            <td class="p-4">
                <div class="flex gap-2 justify-end">
                    <button onclick="event.stopPropagation(); getMarketPrice(this, ${item.id})" class="glowing-element glass p-2 rounded-lg text-xs hover:scale-105 transition-transform" title="Estimer le prix IA">
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"></path></svg>
                    </button>
                    <button onclick="event.stopPropagation(); editItem(${item.id})" class="glowing-element glass p-2 rounded-lg text-xs hover:scale-105 transition-transform" title="Modifier">
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z"></path></svg>
                    </button>
                    <button onclick="event.stopPropagation(); confirmDeleteItem(${item.id})" class="glowing-element status-sold p-2 rounded-lg text-xs hover:scale-105 transition-transform" title="Supprimer">
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path></svg>
                    </button>
                </div>
            </td>
        </tr>
    `;
}

// --- Lazy Loading pour les cartes ---
function initCardObserver() {
    if (!window.IntersectionObserver) {
        console.warn('IntersectionObserver non supporté');
        return;
    }
    
    try {
        cardObserver = new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('is-visible');
                    observer.unobserve(entry.target);
                }
            });
        }, {
            rootMargin: '0px',
            threshold: 0.1
        });
    } catch (error) {
        console.error('Erreur initialisation observer:', error);
        cardObserver = null;
    }
}

// --- Modals ---
function openCreateModal() {
    const modal = document.getElementById('item-modal');
    const form = document.getElementById('item-form');
    const title = document.getElementById('modal-title');
    const itemId = document.getElementById('item-id');
    
    if (title) title.textContent = 'Nouvel Objet';
    if (form) form.reset();
    if (itemId) itemId.value = '';
    
    toggleRealEstateFields();
    toggleStockFields();
    toggleSaleProgressFields();
    
    if (modal) {
        modal.classList.remove('hidden');
        modal.classList.add('flex');
    }
}

function editItem(id) {
    const item = allItems.find(i => i.id === id);
    if (!item) return;
    
    const title = document.getElementById('modal-title');
    if (title) title.textContent = 'Modifier l\'Objet';
    
    // Remplir le formulaire avec les champs existants
    Object.keys(item).forEach(key => {
        const element = document.getElementById(`item-${key.replace(/_/g, '-')}`);
        if (element) {
            if (element.type === 'checkbox') {
                element.checked = item[key];
            } else {
                element.value = item[key] || '';
            }
        }
    });

    // Remplir les champs spécifiques aux actions
    if (item.category === 'Actions') {
        const stockSymbol = document.getElementById('item-stock-symbol');
        if (stockSymbol) stockSymbol.value = item.stock_symbol || '';
        
        const stockQuantity = document.getElementById('item-stock-quantity');
        if (stockQuantity) stockQuantity.value = item.stock_quantity || '';
        
        const stockPurchasePrice = document.getElementById('item-stock-purchase-price');
        if (stockPurchasePrice) stockPurchasePrice.value = item.stock_purchase_price || '';
        
        const stockExchange = document.getElementById('item-stock-exchange');
        if (stockExchange) stockExchange.value = item.stock_exchange || '';
        
        const currentPrice = document.getElementById('item-current-price');
        if (currentPrice) currentPrice.value = item.current_price || '';
    }

    // Remplir les champs de suivi des ventes
    const saleStatus = document.getElementById('item-sale-status');
    if (saleStatus) saleStatus.value = item.sale_status || 'initial';
    
    const lastActionDate = document.getElementById('item-last-action-date');
    if (lastActionDate && item.last_action_date) {
        lastActionDate.value = item.last_action_date.split('T')[0];
    }
    
    const saleProgress = document.getElementById('item-sale-progress');
    if (saleProgress) saleProgress.value = item.sale_progress || '';
    
    const buyerContact = document.getElementById('item-buyer-contact');
    if (buyerContact) buyerContact.value = item.buyer_contact || '';
    
    const intermediary = document.getElementById('item-intermediary');
    if (intermediary) intermediary.value = item.intermediary || '';
    
    const currentOffer = document.getElementById('item-current-offer');
    if (currentOffer) currentOffer.value = item.current_offer || '';
    
    const commissionRate = document.getElementById('item-commission-rate');
    if (commissionRate) commissionRate.value = item.commission_rate || '';
    
    const itemId = document.getElementById('item-id');
    if (itemId) itemId.value = item.id;
    
    toggleRealEstateFields();
    toggleStockFields();
    toggleSaleProgressFields();
    
    const modal = document.getElementById('item-modal');
    if (modal) {
        modal.classList.remove('hidden');
        modal.classList.add('flex');
    }
}

function closeModal() {
    const modal = document.getElementById('item-modal');
    if (modal) {
        modal.classList.add('hidden');
        modal.classList.remove('flex');
    }
}

function closeEstimationModal() {
    const modal = document.getElementById('estimation-modal');
    if (modal) {
        modal.classList.add('hidden');
        modal.classList.remove('flex');
    }
}

async function handleFormSubmit(e) {
    e.preventDefault();
    
    const itemId = document.getElementById('item-id');
    const isEditing = itemId && !!itemId.value;
    
    const data = {
        // Champs existants
        name: document.getElementById('item-name')?.value || '',
        category: document.getElementById('item-category')?.value || '',
        status: document.getElementById('item-status')?.value || 'Available',
        condition: document.getElementById('item-condition')?.value || '',
        construction_year: parseInt(document.getElementById('item-year')?.value) || null,
        surface_m2: parseFloat(document.getElementById('item-surface')?.value) || null,
        rental_income_chf: parseFloat(document.getElementById('item-rental-income')?.value) || null,
        acquisition_price: parseFloat(document.getElementById('item-acquisition-price')?.value) || null,
        asking_price: parseFloat(document.getElementById('item-asking-price')?.value) || null,
        sold_price: parseFloat(document.getElementById('item-sold-price')?.value) || null,
        description: document.getElementById('item-description')?.value?.trim() || null,
        for_sale: document.getElementById('item-for-sale')?.checked || false,
        
        // Champs spécifiques aux actions
        stock_symbol: document.getElementById('item-stock-symbol')?.value?.trim() || null,
        stock_quantity: parseInt(document.getElementById('item-stock-quantity')?.value) || null,
        stock_purchase_price: parseFloat(document.getElementById('item-stock-purchase-price')?.value) || null,
        stock_exchange: document.getElementById('item-stock-exchange')?.value || null,
        current_price: parseFloat(document.getElementById('item-current-price')?.value) || null,

        // Champs de suivi des ventes
        sale_status: document.getElementById('item-sale-status')?.value || 'initial',
        sale_progress: document.getElementById('item-sale-progress')?.value?.trim() || null,
        buyer_contact: document.getElementById('item-buyer-contact')?.value?.trim() || null,
        intermediary: document.getElementById('item-intermediary')?.value?.trim() || null,
        current_offer: parseFloat(document.getElementById('item-current-offer')?.value) || null,
        commission_rate: parseFloat(document.getElementById('item-commission-rate')?.value) || null,
        last_action_date: document.getElementById('item-last-action-date')?.value || null
    };
    
    // Si l'objet n'est pas en vente, réinitialiser les champs de suivi
    if (!data.for_sale) {
        data.sale_status = 'initial';
        data.sale_progress = null;
        data.buyer_contact = null;
        data.intermediary = null;
        data.current_offer = null;
        data.commission_rate = null;
        data.last_action_date = null;
    }
    
    try {
        const url = isEditing ? `/api/items/${itemId.value}` : '/api/items';
        const method = isEditing ? 'PUT' : 'POST';
        
        const response = await fetch(url, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        
        if (response.ok) {
            closeModal();
            await loadItems();
            showSuccess(`Objet ${isEditing ? 'modifié' : 'créé'} avec succès`);
        } else {
            const err = await response.json();
            showError(`Erreur: ${err.error || 'Sauvegarde impossible'}`);
        }
    } catch (error) {
        console.error('Erreur:', error);
        showError('Erreur de connexion serveur.');
    }
}

function confirmDeleteItem(id) {
    if (confirm('Êtes-vous sûr de vouloir supprimer cet objet ? Cette action est irréversible.')) {
        deleteItem(id);
    }
}

async function deleteItem(id) {
    try {
        const response = await fetch(`/api/items/${id}`, { method: 'DELETE' });
        if (response.ok) {
            await loadItems();
            showSuccess('Objet supprimé');
        } else {
            const err = await response.json();
            showError(`Erreur: ${err.error || 'Suppression impossible'}`);
        }
    } catch (error) {
        console.error('Erreur:', error);
        showError('Erreur de connexion serveur.');
    }
}

// --- Estimation IA ---
async function getMarketPrice(button, id) {
    if (!button) return;
    
    const originalHTML = button.innerHTML;
    button.innerHTML = '<svg class="animate-spin h-4 w-4 mx-auto" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>';
    button.disabled = true;
    
    try {
        const response = await fetch(`/api/market-price/${id}`);
        const data = await response.json();
        
        if (response.ok) {
            showEstimationModal(data, id);
        } else {
            showError(data.error || 'Erreur lors de l\'estimation');
        }
    } catch (error) {
        console.error('Erreur:', error);
        showError('Erreur de connexion pour l\'estimation.');
    } finally {
        button.innerHTML = originalHTML;
        button.disabled = false;
    }
}

function showEstimationModal(data, itemId) {
    const item = allItems.find(i => i.id === itemId);
    if (!item) return;
    
    const { estimated_price, reasoning, comparable_items, confidence_score, market_analysis } = data;
    
    let comparablesHTML = '';
    
    // Vérifier si on a des objets comparables valides
    if (comparable_items && comparable_items.length > 0) {
        const validComparables = comparable_items.filter(comp => comp && comp.name);
        
        if (validComparables.length > 0) {
            comparablesHTML = `
                <div class="glass-subtle p-6 rounded-2xl">
                    <h3 class="text-lg font-semibold mb-4">Objets comparables</h3>
                    <div class="space-y-3">
                        ${validComparables.map(comp => {
                            const price = comp.reference_price || comp.price || comp.prix || 0;
                            const name = comp.name || 'Objet comparable';
                            const source = comp.source || comp.comparison_reason || 'Marché';
                            const year = comp.year || comp.année || '';
                            
                            return `
                                <div class="flex justify-between items-center p-3 bg-slate-800/50 rounded-xl">
                                    <div>
                                        <div class="font-medium">${name}${year ? ` (${year})` : ''}</div>
                                        <div class="text-sm text-slate-500">${source}</div>
                                    </div>
                                    <div class="font-bold text-cyan-400">${formatPrice(price)}</div>
                                </div>
                            `;
                        }).join('')}
                    </div>
                </div>`;
        }
    }
    
    const confidenceColor = confidence_score > 0.7 ? 'text-green-400' : confidence_score > 0.4 ? 'text-yellow-400' : 'text-orange-400';
    
    const contentBody = document.getElementById('estimation-content-body');
    if (contentBody) {
        contentBody.innerHTML = `
            <div class="space-y-6">
                <div class="text-center p-8 glass-subtle rounded-2xl">
                    <h3 class="text-2xl font-bold mb-4">${item.name}</h3>
                    <div class="text-3xl font-bold text-cyan-400 mb-2">${formatPrice(estimated_price)}</div>
                    <div class="${confidenceColor} text-sm">Confiance: ${Math.round(confidence_score * 100)}%</div>
                </div>
                <div class="glass-subtle p-6 rounded-2xl">
                    <h3 class="text-lg font-semibold mb-4">Analyse de l'IA</h3>
                    <p class="text-slate-400 whitespace-pre-wrap">${reasoning}</p>
                </div>
                ${comparablesHTML}
            </div>`;
    }
    
    const modal = document.getElementById('estimation-modal');
    if (modal) {
        modal.classList.remove('hidden');
        modal.classList.add('flex');
    }
}

// ==========================================
// CHATBOT INTELLIGENT AVEC STREAMING AMÉLIORÉ
// ==========================================

// Fonction pour smooth scroll
function smoothScrollToBottom(element, duration = 300) {
    const start = element.scrollTop;
    const end = element.scrollHeight - element.clientHeight;
    const distance = end - start;
    const startTime = performance.now();
    
    function scrollAnimation(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        
        // Easing function pour un scroll plus naturel
        const easeInOutQuad = progress < 0.5 
            ? 2 * progress * progress 
            : 1 - Math.pow(-2 * progress + 2, 2) / 2;
        
        element.scrollTop = start + distance * easeInOutQuad;
        
        if (progress < 1) {
            requestAnimationFrame(scrollAnimation);
        }
    }
    
    requestAnimationFrame(scrollAnimation);
}

// Fonction pour le streaming du texte
function streamText(element, text, onComplete, speed = 10) {
    let index = 0;
    const messagesContainer = document.getElementById('chatbot-messages');
    
    // Nettoyer le texte pour un affichage optimal
    const cleanedText = text
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        .replace(/`(.*?)`/g, '<code style="background: rgba(255,255,255,0.1); padding: 2px 4px; border-radius: 3px;">$1</code>')
        .replace(/\n/g, '<br>');
    
    element.innerHTML = '';
    
    function addChar() {
        if (index < cleanedText.length) {
            // Ajouter les caractères par groupes pour les balises HTML
            if (cleanedText[index] === '<') {
                const closeIndex = cleanedText.indexOf('>', index);
                if (closeIndex !== -1) {
                    element.innerHTML += cleanedText.substring(index, closeIndex + 1);
                    index = closeIndex + 1;
                } else {
                    element.innerHTML += cleanedText[index];
                    index++;
                }
            } else {
                element.innerHTML += cleanedText[index];
                index++;
            }
            
            // Scroll progressif
            if (messagesContainer && index % 10 === 0) {
                messagesContainer.scrollTop = messagesContainer.scrollHeight;
            }
            
            setTimeout(addChar, speed);
        } else {
            // Scroll final smooth
            if (messagesContainer) {
                smoothScrollToBottom(messagesContainer);
            }
            if (onComplete) onComplete();
        }
    }
    
    addChar();
}

function toggleChatbot() {
    const chatWindow = document.getElementById('chatbot-window');
    if (!chatWindow) return;
    
    chatWindow.classList.toggle('is-open');

    if (chatWindow.classList.contains('is-open')) {
        const input = document.getElementById('chatbot-input');
        if (input) input.focus();
        
        // Message de bienvenue simple si première ouverture
        const messages = document.getElementById('chatbot-messages');
        if (messages && messages.children.length === 1) {
            addWelcomeMessage();
        }
    }
}

async function handleChatSubmit(event) {
    event.preventDefault();
    if (isTyping) return;
    
    const input = document.getElementById('chatbot-input');
    if (!input) return;
    
    const message = input.value.trim();
    if (!message) return;
    
    addChatMessage(message, 'user');
    conversationHistory.push({ role: 'user', content: message });
    input.value = '';
    isTyping = true;
    
    const typingIndicator = addTypingIndicator();
    
    try {
        const response = await fetch('/api/chatbot', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message: message,
                history: conversationHistory.slice(-10)
            })
        });
        
        if (typingIndicator && typingIndicator.parentNode) {
            typingIndicator.remove();
        }
        
        const data = await response.json();
        
        if (response.ok && data.reply) {
            // Utiliser le streaming pour la réponse
            addChatMessage(data.reply, 'bot', true);
            conversationHistory.push({ role: 'assistant', content: data.reply });
            
            // Suggestions intelligentes après certaines réponses
            setTimeout(() => {
                addSmartSuggestions(data.reply, message);
            }, 1500);
        } else {
            addChatMessage(data.error || 'Désolé, une erreur s\'est produite.', 'bot');
        }
    } catch (error) {
        console.error('Erreur chatbot:', error);
        if (typingIndicator && typingIndicator.parentNode) {
            typingIndicator.remove();
        }
        addChatMessage('Erreur de connexion. L\'assistant utilise le mode de base.', 'bot');
    } finally {
        isTyping = false;
        if(conversationHistory.length > 20) {
            conversationHistory = conversationHistory.slice(-20);
        }
    }
}

function addChatMessage(message, sender, useStreaming = false) {
    const messagesContainer = document.getElementById('chatbot-messages');
    if (!messagesContainer) return;
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `chat-message ${sender}`;
    
    // Position de départ pour l'animation
    messageDiv.style.opacity = '0';
    messageDiv.style.transform = 'translateY(10px)';
    
    messagesContainer.appendChild(messageDiv);
    
    // Scroll au début du nouveau message
    setTimeout(() => {
        messageDiv.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }, 100);
    
    // Animation d'apparition
    setTimeout(() => {
        messageDiv.style.transition = 'all 0.3s ease';
        messageDiv.style.opacity = '1';
        messageDiv.style.transform = 'translateY(0)';
    }, 50);
    
    // Streaming ou affichage direct
    if (sender === 'bot' && useStreaming) {
        setTimeout(() => {
            streamText(messageDiv, message, () => {
                // Callback après streaming complet
                const messagesContainer = document.getElementById('chatbot-messages');
                if (messagesContainer) {
                    smoothScrollToBottom(messagesContainer);
                }
            });
        }, 300);
    } else {
        // Affichage direct pour les messages utilisateur
        let formattedMessage = message
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/`(.*?)`/g, '<code style="background: rgba(255,255,255,0.1); padding: 2px 4px; border-radius: 3px;">$1</code>')
            .replace(/\n/g, '<br>');
        
        messageDiv.innerHTML = formattedMessage;
        smoothScrollToBottom(messagesContainer);
    }
}

function addSmartSuggestions(botReply, userMessage) {
    const suggestions = getSmartSuggestions(botReply, userMessage);
    
    if (suggestions.length > 0) {
        setTimeout(() => {
            addSuggestionButtons(suggestions);
        }, 500);
    }
}

function getSmartSuggestions(botReply, userMessage) {
    const suggestions = [];
    
    // Suggestions basées sur la réponse du bot et le suivi des ventes
    if (botReply.includes('vente') || botReply.includes('offre') || botReply.includes('négociation')) {
        suggestions.push('Où en sont mes ventes ?');
        suggestions.push('Statistiques complètes');
    }
    
    if (botReply.includes('IA a trouvé') || botReply.includes('Correspondances intelligentes') || botReply.includes('Identifiés par l\'IA')) {
        suggestions.push('Mes SUV en vente');
        suggestions.push('Combien j\'ai de montres automatiques');
    }
    
    if (botReply.includes('performance') || botReply.includes('ventes')) {
        suggestions.push('Quels objets dois-je mettre en vente ?');
        suggestions.push('Analyse ma rentabilité par catégorie');
    }
    
    // Suggestions générales si aucune spécifique
    if (suggestions.length === 0) {
        const generalSuggestions = [
            'Où en sont mes ventes ?',
            'Comment va ma collection ?',
            'Combien j\'ai de voitures 4 places',
            'Mes objets en négociation'
        ];
        suggestions.push(generalSuggestions[Math.floor(Math.random() * generalSuggestions.length)]);
    }
    
    return suggestions.slice(0, 2);
}

function addSuggestionButtons(suggestions) {
    const messagesContainer = document.getElementById('chatbot-messages');
    if (!messagesContainer) return;
    
    const suggestionDiv = document.createElement('div');
    suggestionDiv.className = 'chat-suggestions';
    suggestionDiv.style.cssText = `
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        margin: 10px 0;
        padding: 0 10px;
        opacity: 0;
        transform: translateY(10px);
        transition: all 0.3s ease;
    `;
    
    suggestions.forEach(suggestion => {
        const button = document.createElement('button');
        button.textContent = suggestion;
        button.style.cssText = `
            background: rgba(34, 211, 238, 0.1);
            border: 1px solid rgba(34, 211, 238, 0.3);
            color: #22d3ee;
            padding: 6px 12px;
            border-radius: 15px;
            font-size: 12px;
            cursor: pointer;
            transition: all 0.2s;
        `;
        
        button.addEventListener('mouseenter', () => {
            button.style.background = 'rgba(34, 211, 238, 0.2)';
            button.style.transform = 'scale(1.05)';
        });
        
        button.addEventListener('mouseleave', () => {
            button.style.background = 'rgba(34, 211, 238, 0.1)';
            button.style.transform = 'scale(1)';
        });
        
        button.addEventListener('click', () => {
            const input = document.getElementById('chatbot-input');
            if (input) {
                input.value = suggestion;
                input.focus();
                suggestionDiv.remove();
            }
        });
        
        suggestionDiv.appendChild(button);
    });
    
    messagesContainer.appendChild(suggestionDiv);
    
    // Animation d'apparition
    setTimeout(() => {
        suggestionDiv.style.opacity = '1';
        suggestionDiv.style.transform = 'translateY(0)';
    }, 50);
    
    smoothScrollToBottom(messagesContainer);
    
    // Auto-suppression après 30 secondes
    setTimeout(() => {
        if (suggestionDiv.parentNode) {
            suggestionDiv.style.opacity = '0';
            setTimeout(() => suggestionDiv.remove(), 300);
        }
    }, 30000);
}

function addTypingIndicator() {
    const messagesContainer = document.getElementById('chatbot-messages');
    if (!messagesContainer) return null;
    
    const typingDiv = document.createElement('div');
    typingDiv.className = 'chat-message bot typing-indicator';
    typingDiv.style.opacity = '0';
    typingDiv.style.transform = 'translateY(10px)';
    typingDiv.innerHTML = `
        <div style="display: flex; align-items: center; gap: 8px;">
            <div class="typing-dots" style="display: flex; gap: 4px;">
                <div style="width: 8px; height: 8px; background: currentColor; border-radius: 50%; animation: typingPulse 1.4s infinite ease-in-out;"></div>
                <div style="width: 8px; height: 8px; background: currentColor; border-radius: 50%; animation: typingPulse 1.4s infinite ease-in-out 0.2s;"></div>
                <div style="width: 8px; height: 8px; background: currentColor; border-radius: 50%; animation: typingPulse 1.4s infinite ease-in-out 0.4s;"></div>
            </div>
            <span style="font-size: 12px; opacity: 0.7;">Assistant analyse avec IA...</span>
        </div>
    `;
    
    // Ajouter l'animation CSS si pas déjà présente
    if (!document.getElementById('typing-animation-style')) {
        const style = document.createElement('style');
        style.id = 'typing-animation-style';
        style.textContent = `
            @keyframes typingPulse {
                0%, 60%, 100% { opacity: 0.3; transform: scale(0.8); }
                30% { opacity: 1; transform: scale(1); }
            }
        `;
        document.head.appendChild(style);
    }
    
    messagesContainer.appendChild(typingDiv);
    
    // Animation d'apparition et scroll
    setTimeout(() => {
        typingDiv.style.transition = 'all 0.3s ease';
        typingDiv.style.opacity = '1';
        typingDiv.style.transform = 'translateY(0)';
        typingDiv.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }, 50);
    
    return typingDiv;
}

// Actions rapides prédéfinies
function addQuickActions() {
    const chatWindow = document.getElementById('chatbot-window');
    if (!chatWindow) return;
    
    const quickActionsHTML = `
        <div class="quick-actions" style="padding: 10px; border-bottom: 1px solid var(--glass-border); display: flex; flex-wrap: wrap; gap: 5px;">
            <button onclick="askQuickQuestion('Où en sont mes ventes ?')" class="quick-btn">Ventes</button>
            <button onclick="askQuickQuestion('Statistiques complètes')" class="quick-btn">Stats</button>
            <button onclick="askQuickQuestion('Combien j\\'ai de voitures 4 places')" class="quick-btn">IA</button>
        </div>
    `;
    
    const header = chatWindow.querySelector('#chatbot-header');
    if (header && !chatWindow.querySelector('.quick-actions')) {
        header.insertAdjacentHTML('afterend', quickActionsHTML);
    }
}

function askQuickQuestion(question) {
    const input = document.getElementById('chatbot-input');
    if (input) {
        input.value = question;
        handleChatSubmit(new Event('submit'));
    }
}

// Raccourcis clavier intelligents
document.addEventListener('keydown', function(e) {
    // Ctrl/Cmd + K pour ouvrir le chat
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        const chatWindow = document.getElementById('chatbot-window');
        if (chatWindow && !chatWindow.classList.contains('is-open')) {
            toggleChatbot();
        }
    }
    
    // Échap pour fermer le chat et modaux
    if (e.key === 'Escape') {
        const chatWindow = document.getElementById('chatbot-window');
        if (chatWindow && chatWindow.classList.contains('is-open')) {
            toggleChatbot();
        }
        
        const itemModal = document.getElementById('item-modal');
        if (itemModal && !itemModal.classList.contains('hidden')) {
            closeModal();
        }
        
        const estimationModal = document.getElementById('estimation-modal');
        if (estimationModal && !estimationModal.classList.contains('hidden')) {
            closeEstimationModal();
        }
    }
});

// Nettoyer les timers au déchargement
window.addEventListener('beforeunload', function() {
    if (stockPriceUpdateTimer) {
        clearInterval(stockPriceUpdateTimer);
    }
});
