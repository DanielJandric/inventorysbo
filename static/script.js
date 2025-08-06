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
let stockPriceUpdateErrors = {}; // Pour tracker les erreurs par symbole

// --- Notifications ---
function showNotification(message, isError = false) {
    // Notifications désactivées pour éviter les popups dérangeants
    // console.log(`Notification ${isError ? 'erreur' : 'succès'}: ${message}`);
}

function showError(message) {
    showNotification(message, true);
}

function showSuccess(message) {
    showNotification(message, false);
}

// --- Initialisation sécurisée ---
document.addEventListener('DOMContentLoaded', async function() {
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
        await loadItems();
        
        // Forcer la mise à jour des prix des actions au démarrage
        await forceUpdateStockPrices();
        
        // Initialiser les filtres simplifiés
        filterByMainStatus('all');
        setViewMode('cards');

        // Ajouter les actions rapides du chatbot
        setTimeout(addQuickActions, 1000);
        
        // Écouter les événements de refresh/visibility change
        document.addEventListener('visibilitychange', async function() {
            if (!document.hidden) {
                console.log('Page redevenue visible - mise à jour des prix...');
                await forceUpdateStockPrices();
            }
        });
        
        // Écouter les événements de focus (retour sur l'onglet)
        window.addEventListener('focus', async function() {
            console.log('Onglet refocusé - mise à jour des prix...');
            await forceUpdateStockPrices();
        });
        
        // Charger automatiquement les données boursières au démarrage
        setTimeout(() => {
            loadStockPricesOnStartup();
        }, 2000);
        
        console.log('Chargement automatique des données boursières activé');
        
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
    const stockMetricsField = document.getElementById('stock-metrics-field');
    
    if (stockFields) {
        stockFields.style.display = isStock ? 'block' : 'none';
    }
    if (currentPriceField) {
        currentPriceField.style.display = isStock ? 'block' : 'none';
    }
    if (stockMetricsField) {
        stockMetricsField.style.display = isStock ? 'block' : 'none';
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
            const currentValueInput = document.getElementById('item-current-value');
    const stockQuantityInput = document.getElementById('item-stock-quantity');
    
    if (!currentPriceInput || !currentValueInput || !stockQuantityInput) return;
    
    const currentPrice = parseFloat(currentPriceInput.value);
    const quantity = parseInt(stockQuantityInput.value) || 1;
    
    if (currentPrice && quantity) {
        const totalValue = currentPrice * quantity;
        currentValueInput.value = totalValue.toFixed(2);
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
    } else if (currentMainFilter === 'all') {
        // Pour 'all', exclure les items vendus par défaut (ils sont dans l'onglet Vendu)
        filteredItems = filteredItems.filter(item => item.status !== 'Sold');
    }
    
    return filteredItems;
}

// --- Statistiques avec filtrage ---
function updateStatistics() {
    const filteredItems = getFilteredItems();
    const stats = calculateStats(filteredItems);
    
    const elements = {
        'stat-total': stats.total,
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
    
    // Calculer la valeur disponible en incluant les actions
    const valeur_disponible = items.filter(item => item.status === 'Available').reduce((sum, item) => {
        if (item.category === 'Actions' && item.current_price && item.stock_quantity) {
            // Pour les actions : prix actuel × quantité
            const actionValue = item.current_price * item.stock_quantity;
            console.log(`Action ${item.name}: ${item.current_price} × ${item.stock_quantity} = ${actionValue}`);
            return sum + actionValue;
        } else if (item.current_value) {
            // Pour les autres objets : valeur actuelle
            return sum + item.current_value;
        }
        return sum;
    }, 0);
    
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
    if (price === null || price === undefined || isNaN(price)) return 'N/A';
    return new Intl.NumberFormat('fr-CH', {
        style: 'currency',
        currency: 'CHF',
        minimumFractionDigits: 0,
        maximumFractionDigits: 0
    }).format(price);
}

function formatPriceInCurrency(price, currency = 'CHF') {
    if (price === null || price === undefined) return 'N/A';
    return new Intl.NumberFormat('fr-CH', { 
        style: 'currency', 
        currency: currency, 
        minimumFractionDigits: 2, 
        maximumFractionDigits: 2 
    }).format(price);
}

function formatVolume(volume) {
    if (volume === 'N/A' || !volume) return 'N/A';
    if (volume > 1e9) return `${(volume/1e9).toFixed(2)}B`;
    if (volume > 1e6) return `${(volume/1e6).toFixed(2)}M`;
    if (volume > 1e3) return `${(volume/1e3).toFixed(2)}K`;
    return volume.toString();
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
        'count-for-sale': filteredItems.filter(item => item.status === 'Available' && item.for_sale === true).length
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
    
    // Tri par statut d'abord (disponibles avant vendus), puis par catégorie
    filteredItems.sort((a, b) => {
        // 1. Tri par statut : Available avant Sold
        const statusA = a.status === 'Available' ? 0 : 1;
        const statusB = b.status === 'Available' ? 0 : 1;
        
        if (statusA !== statusB) {
            return statusA - statusB;
        }
        
        // 2. Si même statut, trier par priorité de catégorie
        const categoryPriority = {
            'Actions': 1,
            'Voitures': 2,
            'Bateaux': 3,
            'Avions': 4
        };
        
        const priorityA = categoryPriority[a.category] || 5;
        const priorityB = categoryPriority[b.category] || 5;
        
        if (priorityA !== priorityB) {
            return priorityA - priorityB;
        }
        
        // 3. Si même catégorie, trier par nom
        return (a.name || '').localeCompare(b.name || '');
    });
    
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
// Fonction startStockPriceUpdates() supprimée - plus de mises à jour automatiques

async function updateStockPrices(forceRefresh = false) {
    const stockItems = allItems.filter(item => item.category === 'Actions' && item.stock_symbol);
    
    if (stockItems.length === 0) return;
    
    console.log(`Mise à jour manuelle des prix pour ${stockItems.length} actions...${forceRefresh ? ' (refresh forcé)' : ''}`);
    
    for (const item of stockItems) {
        // Vérifier si on a déjà eu trop d'erreurs pour ce symbole
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
                // Rate limit atteint
                console.warn(`Rate limit atteint pour ${item.stock_symbol}`);
                stockPriceUpdateErrors[item.stock_symbol] = (errorCount || 0) + 1;
                continue;
            }
            
            if (response.ok) {
                const data = await response.json();
                
                // Calculer la valeur totale
                const totalValue = data.price * (item.stock_quantity || 1);
                
                // Mettre à jour l'objet en mémoire
                item.current_price = data.price;
                item.current_value = totalValue; // Mettre à jour current_value pour l'agrégation
                item.last_price_update = data.last_update;
                
                console.log(`✅ ${item.stock_symbol} mis à jour: ${data.price} ${data.currency} × ${item.stock_quantity} = ${totalValue} ${data.currency}`);
                
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
        
        // Délai minimal entre les requêtes pour éviter les rate limits
        await new Promise(resolve => setTimeout(resolve, 1000));
    }
    
    // Rafraîchir les statistiques si des prix ont été mis à jour
    updateStatistics();
}

// Fonction pour forcer la mise à jour immédiate des prix (ignore le cache)
async function forceUpdateStockPrices() {
    console.log('Mise à jour des prix (cache ignoré)...');
    
    // Réinitialiser les erreurs pour permettre de nouveaux essais
    stockPriceUpdateErrors = {};
    
    // Lancer la mise à jour immédiatement avec force_refresh=true
    await updateStockPrices(true);
    
    // Mettre à jour les statistiques après la mise à jour des prix
    updateStatistics();
}

async function updateSingleStockPrice(symbol, itemId) {
    try {
        console.log(`🔄 Début mise à jour ${symbol} (ID: ${itemId})`);
        
        const response = await fetch(`/api/stock-price/${symbol}?force_refresh=true`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        if (response.ok) {
            const data = await response.json();
            console.log(`✅ Données reçues pour ${symbol}:`, data);
            
            // Mettre à jour l'affichage de la carte
            console.log(`🔄 Appel updateStockCardDisplay pour ${itemId}`);
            updateStockCardDisplay(itemId, data);
        } else {
            const error = await response.json();
            console.error(`❌ Erreur API pour ${symbol}:`, error);
            showError(`Erreur ${symbol}: ${error.error || 'Erreur serveur'}`);
        }
    } catch (error) {
        console.error('Erreur:', error);
        showError(`Impossible de mettre à jour ${symbol}`);
    }
}

// Fonction pour ouvrir la modal de sélection de véhicule
function openVehicleSelectModal() {
    // Filtrer seulement les véhicules (Voitures, Bateaux, Avions, etc.) - pas les Actions
    const vehicleCategories = ['Voitures', 'Bateaux', 'Avions', 'Véhicules', 'Motos', 'Camions'];
    const vehicles = allItems.filter(item => 
        vehicleCategories.includes(item.category) && 
        item.status === 'Available'
    );
    
    if (vehicles.length === 0) {
        showError('Aucun véhicule disponible pour la mise à jour');
        return;
    }
    
    // Remplir la liste déroulante
    const select = document.getElementById('vehicle-select');
    select.innerHTML = '<option value="">Sélectionnez un véhicule...</option>';
    
    vehicles.forEach(vehicle => {
        const option = document.createElement('option');
        option.value = vehicle.id;
        option.textContent = `${vehicle.name} (${vehicle.category})`;
        select.appendChild(option);
    });
    
    // Afficher la modal
    document.getElementById('vehicle-select-modal').classList.remove('hidden');
    
    // Écouter les changements de sélection
    select.addEventListener('change', function() {
        const selectedId = this.value;
        const vehicleDetails = document.getElementById('vehicle-details');
        const vehicleInfo = document.getElementById('vehicle-info');
        const confirmBtn = document.getElementById('confirm-ai-btn');
        
        if (selectedId) {
            const vehicle = vehicles.find(v => v.id == selectedId);
            if (vehicle) {
                // Afficher les détails du véhicule
                vehicleInfo.innerHTML = `
                    <div><strong>Nom:</strong> ${vehicle.name}</div>
                    <div><strong>Catégorie:</strong> ${vehicle.category}</div>
                    <div><strong>Année:</strong> ${vehicle.construction_year || 'N/A'}</div>
                    <div><strong>État:</strong> ${vehicle.condition || 'N/A'}</div>
                    <div><strong>Prix actuel:</strong> ${vehicle.current_value ? formatPrice(vehicle.current_value) : 'Non défini'}</div>
                    <div><strong>Prix d'acquisition:</strong> ${vehicle.acquisition_price ? formatPrice(vehicle.acquisition_price) : 'Non défini'}</div>
                    ${vehicle.description ? `<div><strong>Description:</strong> ${vehicle.description.substring(0, 100)}...</div>` : ''}
                `;
                vehicleDetails.classList.remove('hidden');
                confirmBtn.disabled = false;
            }
        } else {
            vehicleDetails.classList.add('hidden');
            confirmBtn.disabled = true;
        }
    });
}

// Fonction pour fermer la modal de sélection
function closeVehicleSelectModal() {
    document.getElementById('vehicle-select-modal').classList.add('hidden');
    document.getElementById('vehicle-select').value = '';
    document.getElementById('vehicle-details').classList.add('hidden');
    document.getElementById('confirm-ai-btn').disabled = true;
}

// Fonction pour confirmer la mise à jour IA
async function confirmAiUpdate() {
    const selectedId = document.getElementById('vehicle-select').value;
    if (!selectedId) return;
    
    // Filtrer seulement les véhicules (Voitures, Bateaux, Avions, etc.) - pas les Actions
    const vehicleCategories = ['Voitures', 'Bateaux', 'Avions', 'Véhicules', 'Motos', 'Camions'];
    const vehicles = allItems.filter(item => 
        vehicleCategories.includes(item.category) && 
        item.status === 'Available'
    );
    const selectedVehicle = vehicles.find(v => v.id == selectedId);
    
    if (!selectedVehicle) {
        showError('Véhicule non trouvé');
        return;
    }
    
    // Confirmation finale
    if (!confirm(`Mettre à jour le prix de "${selectedVehicle.name}" via l'IA ?\n\nCette opération va:\n- Analyser le marché actuel\n- Calculer une nouvelle estimation\n- Mettre à jour la base de données\n\nContinuer ?`)) {
        return;
    }
    
    // Fermer la modal
    closeVehicleSelectModal();
    
    try {
        showNotification('Analyse IA en cours...', false);
        
        const response = await fetch(`/api/ai-update-price/${selectedVehicle.id}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const result = await response.json();
        
        if (response.ok) {
            showSuccess(`✅ ${result.message}\n\nNouveau prix: ${formatPrice(result.updated_price)}`);
            
            // Recharger les données pour afficher les changements
            await loadItems();
            
            // Afficher les détails de l'estimation IA
            if (result.ai_estimation) {
                const details = result.ai_estimation;
                const confidence = Math.round(details.confidence_score * 100);
                const reasoning = details.reasoning ? details.reasoning.substring(0, 200) + '...' : 'Aucun détail';
                
                console.log('📊 Estimation IA:', {
                    prix: result.updated_price,
                    confiance: confidence + '%',
                    raisonnement: reasoning,
                    tendance: details.market_trend
                });
            }
        } else {
            showError(`Erreur: ${result.error}`);
        }
        
    } catch (error) {
        console.error('Erreur mise à jour IA:', error);
        showError('Erreur lors de la mise à jour IA');
    }
}

// Fonction pour mettre à jour le prix d'un véhicule via IA (ancienne version - maintenant redirige vers la modal)
async function aiUpdateVehiclePrice() {
    openVehicleSelectModal();
}

// Fonction pour mettre à jour tous les véhicules via IA
async function aiUpdateAllVehicles() {
    // Filtrer seulement les véhicules (Voitures, Bateaux, Avions, etc.) - pas les Actions
    const vehicleCategories = ['Voitures', 'Bateaux', 'Avions', 'Véhicules', 'Motos', 'Camions'];
    const vehicles = allItems.filter(item => 
        vehicleCategories.includes(item.category) && 
        item.status === 'Available'
    );
    
    if (vehicles.length === 0) {
        showError('Aucun véhicule disponible pour la mise à jour');
        return;
    }
    
    // Confirmation importante
    const confirmMessage = `Mettre à jour TOUS les véhicules via l'IA ?\n\nCette opération va:\n- Analyser ${vehicles.length} véhicules\n- Calculer de nouvelles estimations pour chacun\n- Mettre à jour la base de données\n- Prendre plusieurs minutes\n\nÊtes-vous sûr de vouloir continuer ?`;
    
    if (!confirm(confirmMessage)) {
        return;
    }
    
    try {
        showNotification(`Mise à jour IA en cours pour ${vehicles.length} véhicules...`, false);
        
        const response = await fetch('/api/ai-update-all-vehicles', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const result = await response.json();
        
        if (response.ok) {
            const successRate = Math.round((result.updated / result.total_vehicles) * 100);
            showSuccess(`✅ Mise à jour terminée!\n\n${result.updated}/${result.total_vehicles} véhicules mis à jour (${successRate}%)\n${result.errors} erreurs`);
            
            // Recharger les données
            await loadItems();
            
            // Afficher les détails dans la console
            console.log('📊 Résultats mise à jour IA:', result);
            
            // Afficher les erreurs s'il y en a
            if (result.errors > 0) {
                const errors = result.details.filter(d => d.status === 'error');
                console.warn('❌ Erreurs lors de la mise à jour:', errors);
            }
            
        } else {
            showError(`Erreur: ${result.error}`);
        }
        
    } catch (error) {
        console.error('Erreur mise à jour IA en masse:', error);
        showError('Erreur lors de la mise à jour IA en masse');
    }
}

// Fonction pour corriger les catégories 'Véhicules' en 'Voitures'
async function fixVehicleCategories() {
    // Confirmation importante
    if (!confirm(`Corriger les catégories 'Véhicules' en 'Voitures' ?\n\nCette opération va:\n- Rechercher tous les objets avec la catégorie 'Véhicules'\n- Les renommer en 'Voitures'\n- Corriger les erreurs de base de données\n\nContinuer ?`)) {
        return;
    }
    
    try {
        showNotification('Correction des catégories en cours...', false);
        
        const response = await fetch('/api/fix-vehicle-categories', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const result = await response.json();
        
        if (response.ok) {
            if (result.fixed > 0) {
                showSuccess(`✅ ${result.message}\n\n${result.fixed} objets corrigés sur ${result.total_found} trouvés`);
                
                // Recharger les données pour afficher les changements
                await loadItems();
                
                // Afficher les erreurs s'il y en a
                if (result.errors && result.errors.length > 0) {
                    console.warn('❌ Erreurs lors de la correction:', result.errors);
                }
            } else {
                // Afficher les informations de diagnostic
                let diagnosticMessage = `ℹ️ ${result.message}`;
                
                if (result.categories_with_count) {
                    diagnosticMessage += `\n\n📊 Diagnostic:\n`;
                    diagnosticMessage += `• Total objets: ${result.total_items || 'N/A'}\n`;
                    diagnosticMessage += `• Objets sans catégorie: ${result.items_without_category || 0}\n`;
                    diagnosticMessage += `• Catégories trouvées: ${result.all_categories ? result.all_categories.join(', ') : 'Aucune'}\n\n`;
                    
                    if (result.categories_with_count) {
                        diagnosticMessage += `📋 Répartition:\n`;
                        Object.entries(result.categories_with_count).forEach(([cat, count]) => {
                            diagnosticMessage += `• ${cat}: ${count} objet(s)\n`;
                        });
                    }
                }
                
                showSuccess(diagnosticMessage);
            }
            
            console.log('📊 Résultats correction catégories:', result);
            
        } else {
            let errorMessage = `Erreur: ${result.error}`;
            
            // Ajouter des détails supplémentaires si disponibles
            if (result.status_code) {
                errorMessage += `\nCode HTTP: ${result.status_code}`;
            }
            if (result.response_text) {
                errorMessage += `\nRéponse: ${result.response_text}`;
            }
            if (result.parse_error) {
                errorMessage += `\nErreur parsing: ${result.parse_error}`;
            }
            if (result.response_preview) {
                errorMessage += `\nAperçu: ${result.response_preview}`;
            }
            
            showError(errorMessage);
        }
        
    } catch (error) {
        console.error('Erreur correction catégories:', error);
        showError('Erreur lors de la correction des catégories');
    }
}

// Fonction pour générer le PDF
async function generatePDF() {
    try {
        console.log('📄 Génération du PDF...');
        showNotification('Génération du PDF en cours...', false);
        
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
            showNotification('PDF généré avec succès !', false);
        } else {
            const error = await response.json();
            console.error('❌ Erreur génération PDF:', error);
            showNotification('Erreur lors de la génération du PDF: ' + (error.error || 'Erreur inconnue'), true);
        }
        
    } catch (error) {
        console.error('❌ Erreur:', error);
        showNotification('Erreur lors de la génération du PDF', true);
    }
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
    console.log(`🔄 Mise à jour carte action ${itemId}:`, stockData);
    
    // Mettre à jour les données dans allItems
    const itemIndex = allItems.findIndex(item => item.id == itemId);
    if (itemIndex !== -1) {
        const item = allItems[itemIndex];
        
        // Mettre à jour les données de l'action
        item.current_price = stockData.price;
        item.current_value = stockData.price * (item.stock_quantity || 1);
        item.last_price_update = stockData.last_update;
        
        // Mettre à jour les métriques boursières
        item.stock_volume = stockData.volume;
        item.stock_pe_ratio = stockData.pe_ratio;
        item.stock_52_week_high = stockData.fifty_two_week_high;
        item.stock_52_week_low = stockData.fifty_two_week_low;
        item.stock_change = stockData.change;
        item.stock_change_percent = stockData.change_percent;
        
        console.log(`✅ Données mises à jour pour ${item.name}: prix=${stockData.price}, valeur=${item.current_value}`);
        
        // Recalculer les statistiques
        updateStatistics();
    } else {
        console.warn(`⚠️ Item non trouvé dans allItems pour l'ID ${itemId}`);
    }
    
    const card = document.querySelector(`[data-item-id="${itemId}"]`);
    if (!card) {
        console.warn(`⚠️ Carte non trouvée pour l'ID ${itemId}`);
        return;
    }
    
    // Ajouter un indicateur de prix en temps réel
    const priceElement = card.querySelector('.stock-price-live');
    if (!priceElement) {
        console.warn(`⚠️ Élément .stock-price-live non trouvé dans la carte ${itemId}`);
        return;
    }
    
    console.log(`✅ Éléments trouvés pour la carte ${itemId}`);
    
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
    
    // Formater les prix dans la monnaie d'origine
    const formatPriceValue = (price) => {
        if (price === 'N/A' || !price) return 'N/A';
        return formatPriceInCurrency(parseFloat(price), stockData.currency);
    };
    
    // Formater la variation dans la monnaie d'origine
    const formatChange = (change) => {
        if (change === 'N/A' || !change) return 'N/A';
        const value = parseFloat(change);
        const formattedValue = formatPriceInCurrency(Math.abs(value), stockData.currency);
        return value > 0 ? `+${formattedValue}` : `-${formattedValue}`;
    };
    
    priceElement.innerHTML = `
        <div class="space-y-3">
            <!-- Prix principal -->
            <div class="flex items-center justify-between">
                <div class="flex items-center gap-2">
                    <span class="text-lg font-bold text-amber-200">${formatPriceInCurrency(stockData.price, stockData.currency)}</span>
                </div>
                <div class="text-right">
                    <div class="${changeClass} text-sm font-semibold">
                        ${arrow} ${Math.abs(stockData.change_percent).toFixed(2)}%
                    </div>
                    <div class="${changeClass} text-xs">
                        ${formatChange(stockData.change)}
                    </div>
                </div>
            </div>
            
            <!-- Informations détaillées -->
            <div class="space-y-2 text-xs">
                <div class="flex justify-between">
                    <span class="text-amber-300/80 font-medium">Volume:</span>
                    <span class="text-amber-200/90">${formatVolume(stockData.volume)}</span>
                </div>
                <div class="flex justify-between">
                    <span class="text-amber-300/80 font-medium">P/E Ratio:</span>
                    <span class="text-amber-200/90">${stockData.pe_ratio !== 'N/A' ? parseFloat(stockData.pe_ratio).toFixed(1) : 'N/A'}</span>
                </div>
                <div class="flex justify-between">
                    <span class="text-amber-300/80 font-medium">52W High:</span>
                    <span class="text-amber-200/90">${formatPriceValue(stockData.fifty_two_week_high)}</span>
                </div>
                <div class="flex justify-between">
                    <span class="text-amber-300/80 font-medium">52W Low:</span>
                    <span class="text-amber-200/90">${formatPriceValue(stockData.fifty_two_week_low)}</span>
                </div>
            </div>
            
            <!-- Dernière mise à jour -->
            <div class="text-xs text-amber-300/60 text-center pt-1 border-t border-amber-300/20">
                API Manus • ${new Date(stockData.last_update).toLocaleString('fr-FR')}
            </div>
        </div>
    `;
    
    // Retirer l'animation de chargement
    priceElement.classList.remove('animate-pulse');
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
    
    // Grouper les items par statut et catégorie
    const groups = {
        available: {
            Actions: [],
            Voitures: [],
            Bateaux: [],
            Avions: [],
            Autres: []
        },
        sold: {
            Actions: [],
            Voitures: [],
            Bateaux: [],
            Avions: [],
            Autres: []
        }
    };
    
    // Trier les items dans les groupes
    items.forEach(item => {
        const status = item.status === 'Available' ? 'available' : 'sold';
        const category = item.category;
        
        if (groups[status][category]) {
            groups[status][category].push(item);
        } else {
            groups[status].Autres.push(item);
        }
    });
    
    // Créer le HTML avec les sections
    let html = '';
    
    // Section des objets disponibles
    const availableItems = [
        ...groups.available.Actions,
        ...groups.available.Voitures,
        ...groups.available.Bateaux,
        ...groups.available.Avions,
        ...groups.available.Autres
    ];
    
    if (availableItems.length > 0) {
        html += '<div class="mb-8">';
        html += '<h2 class="text-2xl font-bold text-cyan-400 mb-6 border-b border-cyan-500/30 pb-2">Objets Disponibles</h2>';
        html += '<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-8">';
        html += availableItems.map(createItemCardHTML).join('');
        html += '</div>';
        html += '</div>';
    }
    
    // Section des objets vendus
    const soldItems = [
        ...groups.sold.Actions,
        ...groups.sold.Voitures,
        ...groups.sold.Bateaux,
        ...groups.sold.Avions,
        ...groups.sold.Autres
    ];
    
    if (soldItems.length > 0) {
        html += '<div class="mt-12">';
        html += '<h2 class="text-2xl font-bold text-gray-400 mb-6 border-b border-gray-500/30 pb-2">Objets Vendus</h2>';
        html += '<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-8">';
        html += soldItems.map(createItemCardHTML).join('');
        html += '</div>';
        html += '</div>';
    }
    
    container.innerHTML = html;
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
    const isStock = item.category === 'Actions';
    
    let cardClass = isForSale ? 'card-for-sale' : isSold ? 'card-sold' : '';
    if (isStock) {
        cardClass = cardClass ? `${cardClass} card-stock` : 'card-stock';
    }
    
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
            const currency = item.stock_currency || 'USD';
            stockPriceSection = `
                <div class="stock-price-live mt-3 p-2 bg-black/20 rounded-lg">
                    <div class="flex items-center gap-2">
                        <span class="text-lg font-bold">${formatPriceInCurrency(item.current_price, currency)}</span>
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
        } else if (item.current_price && item.stock_change_percent !== undefined) {
            // Si on a des données réelles, les afficher
            const changeClass = item.stock_change_percent > 0 ? 'text-green-400' : 'text-red-400';
            const arrow = item.stock_change_percent > 0 ? '↑' : '↓';
            
            // Utiliser la devise originale de l'action
            const currency = item.stock_currency || 'USD';
            
            stockPriceSection = `
                <div class="stock-price-live mt-3 p-3 bg-black/20 rounded-lg">
                    <div class="space-y-3">
                        <!-- Prix principal -->
                        <div class="flex items-center justify-between">
                            <div class="flex items-center gap-2">
                                <span class="text-lg font-bold text-amber-200">${formatPriceInCurrency(item.current_price, currency)}</span>
                            </div>
                            <div class="text-right">
                                <div class="${changeClass} text-sm font-semibold">
                                    ${arrow} ${Math.abs(item.stock_change_percent || 0).toFixed(2)}%
                                </div>
                                <div class="${changeClass} text-xs">
                                    ${item.stock_change ? (item.stock_change > 0 ? '+' : '') + formatPriceInCurrency(item.stock_change, currency) : '--'}
                                </div>
                            </div>
                        </div>
                        
                        <!-- Informations détaillées -->
                        <div class="space-y-2 text-xs">
                            <div class="flex justify-between">
                                <span class="text-amber-300/80 font-medium">Volume:</span>
                                <span class="text-amber-200/90">${item.stock_volume ? formatVolume(item.stock_volume) : 'N/A'}</span>
                            </div>
                            <div class="flex justify-between">
                                <span class="text-amber-300/80 font-medium">P/E Ratio:</span>
                                <span class="text-amber-200/90">${item.stock_pe_ratio ? parseFloat(item.stock_pe_ratio).toFixed(1) : 'N/A'}</span>
                            </div>
                            <div class="flex justify-between">
                                <span class="text-amber-300/80 font-medium">52W High:</span>
                                <span class="text-amber-200/90">${item.stock_52_week_high ? formatPriceInCurrency(item.stock_52_week_high, currency) : 'N/A'}</span>
                            </div>
                            <div class="flex justify-between">
                                <span class="text-amber-300/80 font-medium">52W Low:</span>
                                <span class="text-amber-200/90">${item.stock_52_week_low ? formatPriceInCurrency(item.stock_52_week_low, currency) : 'N/A'}</span>
                            </div>
                        </div>
                        
                        <!-- Dernière mise à jour -->
                        <div class="text-xs text-amber-300/60 text-center pt-1 border-t border-amber-300/20">
                            API Manus • ${item.last_price_update ? new Date(item.last_price_update).toLocaleString('fr-FR') : 'Jamais'}
                        </div>
                    </div>
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
                                <span class="text-lg font-bold text-amber-200 animate-pulse">Chargement...</span>
                                <span class="text-xs text-amber-300/70 font-medium">--</span>
                            </div>
                            <span class="text-sm text-amber-300/60">--</span>
                        </div>
                        
                        <!-- Informations supplémentaires sans tableaux -->
                        <div class="space-y-2 text-xs">
                            <div class="flex justify-between">
                                <span class="text-amber-300/80 font-medium">Volume:</span>
                                <span class="text-amber-200/90 animate-pulse">--</span>
                            </div>
                            <div class="flex justify-between">
                                <span class="text-amber-300/80 font-medium">P/E Ratio:</span>
                                <span class="text-amber-200/90 animate-pulse">--</span>
                            </div>
                            <div class="flex justify-between">
                                <span class="text-amber-300/80 font-medium">52W High:</span>
                                <span class="text-amber-200/90 animate-pulse">--</span>
                            </div>
                            <div class="flex justify-between">
                                <span class="text-amber-300/80 font-medium">52W Low:</span>
                                <span class="text-amber-200/90 animate-pulse">--</span>
                            </div>
                        </div>
                        
                        <!-- Dernière mise à jour -->
                        <div class="text-xs text-amber-300/60 text-center pt-1 border-t border-amber-300/20">
                            Dernière mise à jour: ${item.last_price_update ? new Date(item.last_price_update).toLocaleString('fr-FR') : 'Jamais'}
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
                    ${item.status === 'Available' && item.current_value ? `<div>Votre Total: ${formatPrice(item.current_value)}</div>` : ''}
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
                ${formatPrice(item.status === 'Available' ? item.current_value : item.sold_price)}
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
    
    // Réinitialiser explicitement le champ location
    const locationField = document.getElementById('item-location');
    if (locationField) locationField.value = '';
    
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
    
    const form = document.getElementById('item-form');
    if (form) {
        // Marquer qu'il n'y a pas de changements non sauvegardés au début
        form.dataset.hasUnsavedChanges = 'false';
        
        // Supprimer les anciens event listeners
        const inputs = form.querySelectorAll('input, select, textarea');
        inputs.forEach(input => {
            input.removeEventListener('input', markFormChanged);
            input.removeEventListener('change', markFormChanged);
            input.addEventListener('input', markFormChanged);
            input.addEventListener('change', markFormChanged);
        });
    }
    
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
        
        const stockCurrency = document.getElementById('item-stock-currency');
        if (stockCurrency) stockCurrency.value = item.stock_currency || 'CHF';
        
        const stockExchange = document.getElementById('item-stock-exchange');
        if (stockExchange) stockExchange.value = item.stock_exchange || '';
        
        const currentPrice = document.getElementById('item-current-price');
        if (currentPrice) currentPrice.value = item.current_price || '';
        
        // Métriques boursières
        const stockVolume = document.getElementById('item-stock-volume');
        if (stockVolume) stockVolume.value = item.stock_volume || '';
        
        const stockAverageVolume = document.getElementById('item-stock-average-volume');
        if (stockAverageVolume) stockAverageVolume.value = item.stock_average_volume || '';
        
        const stockPeRatio = document.getElementById('item-stock-pe-ratio');
        if (stockPeRatio) stockPeRatio.value = item.stock_pe_ratio || '';
        
        const stock52WeekHigh = document.getElementById('item-stock-52-week-high');
        if (stock52WeekHigh) stock52WeekHigh.value = item.stock_52_week_high || '';
        
        const stock52WeekLow = document.getElementById('item-stock-52-week-low');
        if (stock52WeekLow) stock52WeekLow.value = item.stock_52_week_low || '';
        
        const stockChange = document.getElementById('item-stock-change');
        if (stockChange) stockChange.value = item.stock_change || '';
        
        const stockChangePercent = document.getElementById('item-stock-change-percent');
        if (stockChangePercent) stockChangePercent.value = item.stock_change_percent || '';
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

async function closeModal() {
    const modal = document.getElementById('item-modal');
    const form = document.getElementById('item-form');
    
    // Vérifier si le formulaire a des données non sauvegardées
    if (form && form.dataset.hasUnsavedChanges === 'true') {
        const shouldSave = confirm('Vous avez des modifications non sauvegardées. Voulez-vous les sauvegarder avant de fermer ?');
        
        if (shouldSave) {
            // Sauvegarder les données
            try {
                await handleFormSubmit(new Event('submit'));
                showSuccess('Données sauvegardées avec succès');
            } catch (error) {
                console.error('Erreur lors de la sauvegarde:', error);
                showError('Erreur lors de la sauvegarde');
                return; // Ne pas fermer le modal si la sauvegarde échoue
            }
        }
    }
    
    if (modal) {
        modal.classList.add('hidden');
        modal.classList.remove('flex');
    }
    
    // Nettoyer le formulaire quand on ferme le modal
    if (form) {
        form.reset();
        form.dataset.hasUnsavedChanges = 'false';
    }
    
    // Réinitialiser explicitement le champ location
    const locationField = document.getElementById('item-location');
    if (locationField) locationField.value = '';
}

function markFormChanged() {
    const form = document.getElementById('item-form');
    if (form) {
        form.dataset.hasUnsavedChanges = 'true';
    }
}

function closeEstimationModal() {
    const modal = document.getElementById('estimation-modal');
    if (modal) {
        modal.classList.add('hidden');
        modal.classList.remove('flex');
    }
}

// --- Fonctions pour l'import CSV ---
function openImportModal() {
    const modal = document.getElementById('import-modal');
    if (modal) {
        modal.classList.remove('hidden');
        
        // Ajouter l'event listener pour le formulaire
        const importForm = document.getElementById('import-form');
        if (importForm) {
            importForm.addEventListener('submit', handleImportSubmit);
        }
    }
}

function closeImportModal() {
    const modal = document.getElementById('import-modal');
    if (modal) {
        modal.classList.add('hidden');
        
        // Réinitialiser le formulaire
        const importForm = document.getElementById('import-form');
        if (importForm) {
            importForm.reset();
        }
    }
}

async function handleImportSubmit(e) {
    e.preventDefault();
    
    const fileInput = document.getElementById('csv-file');
    if (!fileInput || !fileInput.files[0]) {
        showError('Veuillez sélectionner un fichier CSV');
        return;
    }
    
    const file = fileInput.files[0];
    if (!file.name.endsWith('.csv')) {
        showError('Le fichier doit être au format CSV');
        return;
    }
    
    // Confirmation finale
    if (!confirm('Êtes-vous sûr de vouloir supprimer toutes les voitures existantes (catégorie "Véhicules") et les remplacer par les données du CSV ? Cette action est irréversible !')) {
        return;
    }
    
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        // Afficher un indicateur de chargement
        const submitBtn = e.target.querySelector('button[type="submit"]');
        const originalText = submitBtn.textContent;
        submitBtn.textContent = 'Import en cours...';
        submitBtn.disabled = true;
        
        const response = await fetch('/api/import-csv', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (response.ok) {
            showSuccess(`Import réussi ! ${result.imported_count} voitures importées`);
            closeImportModal();
            
            // Recharger les données
            await loadItems();
        } else {
            showError(`Erreur lors de l'import: ${result.error}`);
        }
        
    } catch (error) {
        console.error('Erreur import:', error);
        showError('Erreur lors de l\'import du fichier');
    } finally {
        // Restaurer le bouton
        const submitBtn = e.target.querySelector('button[type="submit"]');
        submitBtn.textContent = originalText;
        submitBtn.disabled = false;
    }
}

// --- Fonctions pour le rollback CSV ---
function openRollbackModal() {
    const modal = document.getElementById('rollback-modal');
    if (modal) {
        modal.classList.remove('hidden');
        
        // Ajouter l'event listener pour le formulaire
        const rollbackForm = document.getElementById('rollback-form');
        if (rollbackForm) {
            rollbackForm.addEventListener('submit', handleRollbackSubmit);
        }
    }
}

function closeRollbackModal() {
    const modal = document.getElementById('rollback-modal');
    if (modal) {
        modal.classList.add('hidden');
        
        // Réinitialiser le formulaire
        const rollbackForm = document.getElementById('rollback-form');
        if (rollbackForm) {
            rollbackForm.reset();
        }
    }
}

async function handleRollbackSubmit(e) {
    e.preventDefault();
    
    const fileInput = document.getElementById('rollback-csv-file');
    if (!fileInput || !fileInput.files[0]) {
        showError('Veuillez sélectionner un fichier CSV de sauvegarde');
        return;
    }
    
    const file = fileInput.files[0];
    if (!file.name.endsWith('.csv')) {
        showError('Le fichier doit être au format CSV');
        return;
    }
    
    // Confirmation finale TRÈS importante
    if (!confirm('⚠️ ATTENTION : Cette action va supprimer TOUTES les données existantes et les remplacer par votre CSV de sauvegarde. Êtes-vous ABSOLUMENT sûr ?')) {
        return;
    }
    
    // Double confirmation
    if (!confirm('Dernière chance : Êtes-vous vraiment sûr de vouloir supprimer TOUTES les données actuelles ?')) {
        return;
    }
    
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        // Afficher un indicateur de chargement
        const submitBtn = e.target.querySelector('button[type="submit"]');
        const originalText = submitBtn.textContent;
        submitBtn.textContent = 'Rollback en cours...';
        submitBtn.disabled = true;
        
        const response = await fetch('/api/rollback-csv', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (response.ok) {
            showSuccess(`Rollback réussi ! ${result.restored_count} objets restaurés`);
            closeRollbackModal();
            
            // Recharger les données
            await loadItems();
        } else {
            showError(`Erreur lors du rollback: ${result.error}`);
        }
        
    } catch (error) {
        console.error('Erreur rollback:', error);
        showError('Erreur lors du rollback');
    } finally {
        // Restaurer le bouton
        const submitBtn = e.target.querySelector('button[type="submit"]');
        submitBtn.textContent = originalText;
        submitBtn.disabled = false;
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
        current_value: parseFloat(document.getElementById('item-current-value')?.value) || null,
        sold_price: parseFloat(document.getElementById('item-sold-price')?.value) || null,
        description: document.getElementById('item-description')?.value?.trim() || null,
        location: document.getElementById('item-location')?.value || null,
        for_sale: document.getElementById('item-for-sale')?.checked || false,
        
        // Champs spécifiques aux actions
        stock_symbol: document.getElementById('item-stock-symbol')?.value?.trim() || null,
        stock_quantity: parseInt(document.getElementById('item-stock-quantity')?.value) || null,
        stock_purchase_price: parseFloat(document.getElementById('item-stock-purchase-price')?.value) || null,
        stock_exchange: document.getElementById('item-stock-exchange')?.value || null,
        stock_currency: document.getElementById('item-stock-currency')?.value || 'CHF',
        current_price: parseFloat(document.getElementById('item-current-price')?.value) || null,
        
        // Métriques boursières
        stock_volume: parseInt(document.getElementById('item-stock-volume')?.value) || null,
        stock_average_volume: parseInt(document.getElementById('item-stock-average-volume')?.value) || null,
        stock_pe_ratio: parseFloat(document.getElementById('item-stock-pe-ratio')?.value) || null,
        stock_52_week_high: parseFloat(document.getElementById('item-stock-52-week-high')?.value) || null,
        stock_52_week_low: parseFloat(document.getElementById('item-stock-52-week-low')?.value) || null,
        stock_change: parseFloat(document.getElementById('item-stock-change')?.value) || null,
        stock_change_percent: parseFloat(document.getElementById('item-stock-change-percent')?.value) || null,

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
            // Marquer que les changements ont été sauvegardés
            const form = document.getElementById('item-form');
            if (form) {
                form.dataset.hasUnsavedChanges = 'false';
            }
            
            // Recharger les données AVANT de fermer le modal
            await loadItems();
            showSuccess(`Objet ${isEditing ? 'modifié' : 'créé'} avec succès`);
            
            // Fermer le modal APRÈS avoir rechargé les données
            closeModal();
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

// Fonction pour mettre à jour le prix avec l'estimation IA
async function updatePriceWithAI(itemId, estimatedPrice) {
    try {
        showNotification('Mise à jour du prix en cours...', false);
        
        const response = await fetch(`/api/ai-update-price/${itemId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const result = await response.json();
        
        if (response.ok) {
            showSuccess(`✅ Prix mis à jour avec succès!\n\nNouveau prix: ${formatPrice(result.updated_price)}`);
            
            // Fermer le modal d'estimation
            closeEstimationModal();
            
            // Recharger les données pour afficher les changements
            await loadItems();
            
        } else {
            showError(`Erreur: ${result.error}`);
        }
        
    } catch (error) {
        console.error('Erreur mise à jour prix IA:', error);
        showError('Erreur lors de la mise à jour du prix');
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
                <div class="text-center p-6 glass-subtle rounded-2xl">
                    <h3 class="text-lg font-semibold mb-4">Mise à jour du prix</h3>
                    <p class="text-slate-400 mb-4">Voulez-vous mettre à jour le prix actuel de cet objet avec l'estimation de l'IA ?</p>
                    <div class="flex justify-center gap-4">
                        <button onclick="updatePriceWithAI(${itemId}, ${estimated_price})" class="glass glowing-element px-6 py-3 rounded-xl font-medium transition-all duration-300 hover:scale-105 border border-green-500/30 text-green-400 hover:text-green-300 hover:border-green-400/50">
                            <span class="flex items-center gap-2">
                                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
                                </svg>
                                Mettre à jour le prix
                            </span>
                        </button>
                        <button onclick="closeEstimationModal()" class="glass glowing-element px-6 py-3 rounded-xl font-medium transition-all duration-300 hover:scale-105 border border-red-500/30 text-red-400 hover:text-red-300 hover:border-red-400/50">
                            <span class="flex items-center gap-2">
                                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                                </svg>
                                Annuler
                            </span>
                        </button>
                    </div>
                </div>
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
    const chatButton = document.getElementById('chatbot-button');
    if (!chatWindow) return;
    
    chatWindow.classList.toggle('is-open');

    if (chatWindow.classList.contains('is-open')) {
        // Cacher le bouton chat quand le chat est ouvert
        if (chatButton) {
            chatButton.classList.add('chat-hidden');
        }
        
        const input = document.getElementById('chatbot-input');
        if (input) input.focus();
        
        // Message de bienvenue simple si première ouverture
        const messages = document.getElementById('chatbot-messages');
        if (messages && messages.children.length === 1) {
            addWelcomeMessage();
        }
    } else {
        // Montrer le bouton chat quand le chat est fermé
        if (chatButton) {
            chatButton.classList.remove('chat-hidden');
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

// Fonction pour charger les données boursières au démarrage
async function loadStockPricesOnStartup() {
    console.log('Chargement des données boursières au démarrage...');
    
    const stockItems = allItems.filter(item => item.category === 'Actions' && item.stock_symbol);
    
    if (stockItems.length === 0) {
        console.log('Aucune action trouvée pour le chargement initial');
        return;
    }
    
    console.log(`Chargement des données pour ${stockItems.length} actions...`);
    
    for (const item of stockItems) {
        try {
            const response = await fetch(`/api/stock-price/${item.stock_symbol}`);
            
            if (response.ok) {
                const data = await response.json();
                
                // Calculer la valeur totale
                const totalValue = data.price_chf * (item.stock_quantity || 1);
                
                // Mettre à jour l'objet en mémoire
                item.current_price = data.price_chf;
                item.current_value = totalValue; // Mettre à jour current_value pour l'agrégation
                item.last_price_update = data.last_update;
                
                console.log(`✅ ${item.stock_symbol} chargé: ${data.price_chf} CHF × ${item.stock_quantity} = ${totalValue} CHF`);
                
                // Mettre à jour l'affichage de la carte
                updateStockCardDisplay(item.id, data);
                
                console.log(`${item.stock_symbol}: ${formatPrice(data.price_chf)} CHF`);
            } else {
                console.warn(`Impossible de charger ${item.stock_symbol}: ${response.status}`);
            }
        } catch (error) {
            console.error(`Erreur chargement ${item.stock_symbol}:`, error);
        }
        
        // Délai minimal entre les requêtes
        await new Promise(resolve => setTimeout(resolve, 500));
    }
    
    console.log('Chargement des données boursières terminé');
    
    // Rafraîchir les statistiques
    updateStatistics();
}

// Nettoyer les timers au déchargement
window.addEventListener('beforeunload', function() {
    if (stockPriceUpdateTimer) {
        clearInterval(stockPriceUpdateTimer);
    }
});
