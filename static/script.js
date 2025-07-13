let allItems = [];
let currentFilter = 'all';
let currentCategory = 'all';
let currentYear = 'all';
let currentCondition = 'all';
let currentSearch = '';
let currentViewMode = 'cards';

// Charger les données au démarrage
document.addEventListener('DOMContentLoaded', function() {
    loadItems();
});

async function loadItems() {
    try {
        const response = await fetch('/api/items');
        if (response.ok) {
            allItems = await response.json();
            updateStatistics();
            displayItems();
            updateFilterCounts();
        } else {
            const errorData = await response.json();
            showError(`Erreur lors du chargement des objets: ${errorData.error || response.statusText}`);
        }
    } catch (error) {
        console.error('Erreur:', error);
        showError('Erreur de connexion au serveur.');
    }
}

function updateStatistics() {
    const stats = calculateStats(allItems);
    document.getElementById('stat-total').textContent = stats.total;
    document.getElementById('stat-vendus').textContent = stats.vendus;
    document.getElementById('stat-disponibles').textContent = stats.disponibles;
    document.getElementById('stat-valeur-vente').textContent = formatPrice(stats.valeur_vente);
    document.getElementById('stat-valeur-dispo').textContent = formatPrice(stats.valeur_disponible);
    document.getElementById('stat-age-moyen').textContent = stats.age_moyen + ' ans';
}

function calculateStats(items) {
    const total = items.length;
    const vendus = items.filter(item => item.status === 'Sold').length;
    const disponibles = items.filter(item => item.status === 'Available').length;

    const valeur_vente = items
        .filter(item => item.status === 'Sold')
        .reduce((sum, item) => sum + (item.sold_price || 0), 0);

    const valeur_disponible = items
        .filter(item => item.status === 'Available')
        .reduce((sum, item) => sum + (item.asking_price || 0), 0);

    const currentYear = new Date().getFullYear();
    const years = items.filter(item => item.construction_year).map(item => item.construction_year);
    const age_moyen = years.length > 0 ? Math.round(years.reduce((sum, year) => sum + (currentYear - year), 0) / years.length) : 0;

    return { total, vendus, disponibles, valeur_vente, valeur_disponible, age_moyen };
}

function formatPrice(price) {
    if (!price) return 'N/A';
    return new Intl.NumberFormat('fr-CH', {
        style: 'currency',
        currency: 'CHF',
        minimumFractionDigits: 0,
        maximumFractionDigits: 0
    }).format(price);
}

function updateFilterCounts() {
    const all = allItems.length;
    const available = allItems.filter(item => item.status === 'Available').length;
    const sold = allItems.filter(item => item.status === 'Sold').length;

    document.getElementById('count-all').textContent = all;
    document.getElementById('count-available').textContent = available;
    document.getElementById('count-sold').textContent = sold;
}

function filterByStatus(status) {
    currentFilter = status;

    // Mettre à jour l'apparence des boutons
    document.querySelectorAll('.filter-btn').forEach(btn => {
        btn.classList.remove('ring-2', 'ring-yellow-400');
    });
    document.querySelector(`[data-status="${status}"]`).classList.add('ring-2', 'ring-yellow-400');

    displayItems();
}

function filterByCategory(category) {
    currentCategory = category;

    // Mettre à jour l'apparence des boutons
    document.querySelectorAll('.category-btn').forEach(btn => {
        btn.classList.remove('ring-2', 'ring-yellow-400');
    });
    document.querySelector(`[data-category="${category}"]`).classList.add('ring-2', 'ring-yellow-400');

    displayItems();
}

function filterByYear(yearRange) {
    currentYear = yearRange;

    // Mettre à jour l'apparence des boutons
    document.querySelectorAll('.year-btn').forEach(btn => {
        btn.classList.remove('ring-2', 'ring-yellow-400');
    });
    document.querySelector(`[data-year="${yearRange}"]`).classList.add('ring-2', 'ring-yellow-400');

    displayItems();
}

function filterByCondition(condition) {
    currentCondition = condition;

    // Mettre à jour l'apparence des boutons
    document.querySelectorAll('.condition-btn').forEach(btn => {
        btn.classList.remove('ring-2', 'ring-yellow-400');
    });
    document.querySelector(`[data-condition="${condition}"]`).classList.add('ring-2', 'ring-yellow-400');

    displayItems();
}

function setViewMode(mode) {
    currentViewMode = mode;

    // Mettre à jour l'apparence des boutons
    document.querySelectorAll('.view-btn').forEach(btn => {
        btn.classList.remove('ring-2', 'ring-yellow-400');
    });
    document.querySelector(`[data-mode="${mode}"]`).classList.add('ring-2', 'ring-yellow-400');

    displayItems();
}

function handleSearch() {
    const searchInput = document.getElementById('search-input');
    currentSearch = searchInput.value;
    displayItems();
}

function displayItems() {
    const container = document.getElementById('items-container');
    let filteredItems = allItems;

    // Appliquer le filtre de statut
    if (currentFilter !== 'all') {
        filteredItems = filteredItems.filter(item => item.status === currentFilter);
    }

    // Appliquer le filtre de catégorie
    if (currentCategory !== 'all') {
        filteredItems = filteredItems.filter(item => item.category === currentCategory);
    }

    // Appliquer le filtre d'année
    if (currentYear !== 'all') {
        filteredItems = filteredItems.filter(item => {
            if (!item.construction_year) return false;
            const year = item.construction_year;
            switch (currentYear) {
                case '2020-2024': return year >= 2020 && year <= 2024;
                case '2010-2019': return year >= 2010 && year <= 2019;
                case '2000-2009': return year >= 2000 && year <= 2009;
                case '1990-1999': return year >= 1990 && year <= 1999;
                case 'before-1990': return year < 1990;
                default: return true;
            }
        });
    }

    // Appliquer le filtre d'état
    if (currentCondition !== 'all') {
        filteredItems = filteredItems.filter(item => item.condition === currentCondition);
    }

    // Appliquer la recherche
    if (currentSearch.trim() !== '') {
        const searchTerm = currentSearch.toLowerCase().trim();
        filteredItems = filteredItems.filter(item => {
            return (
                (item.name && item.name.toLowerCase().includes(searchTerm)) ||
                (item.category && item.category.toLowerCase().includes(searchTerm)) ||
                (item.description && item.description.toLowerCase().includes(searchTerm))
            );
        });
    }

    if (currentViewMode === 'cards') {
        displayItemsAsCards(container, filteredItems);
    } else {
        displayItemsAsList(container, filteredItems);
    }
}

function displayItemsAsCards(container, items) {
    if (items.length === 0) {
        container.innerHTML = '<div class="text-center text-gray-400 py-8">Aucun objet trouvé</div>';
        return;
    }

    container.innerHTML = `
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            ${items.map(item => `
                <div class="glass floating-card rounded-2xl p-6">
                    <div class="flex justify-between items-start mb-4">
                        <h3 class="text-xl font-bold text-white truncate">${item.name}</h3>
                        <span class="${item.status === 'Available' ? 'status-available' : 'status-sold'} px-3 py-1 rounded-full text-xs font-semibold">
                            ${item.status === 'Available' ? 'Disponible' : 'Vendu'}
                        </span>
                    </div>

                    <div class="space-y-2 text-sm text-gray-300 mb-4">
                        <div>Catégorie: ${item.category}</div>
                        ${item.construction_year ? `<div>Année: ${item.construction_year}</div>` : ''}
                        ${item.condition ? `<div>État: ${item.condition}</div>` : ''}
                        ${item.asking_price ? `<div>Prix: ${formatPrice(item.asking_price)}</div>` : ''}
                        ${item.sold_price ? `<div>Vendu: ${formatPrice(item.sold_price)}</div>` : ''}
                    </div>

                    <div class="flex gap-2">
                        <button onclick="getMarketPrice(${item.id})" class="glass px-3 py-2 rounded-lg text-xs hover:scale-105 transition-transform flex-1">
                            IA Prix
                        </button>
                        <button onclick="editItem(${item.id})" class="glass px-3 py-2 rounded-lg text-xs hover:scale-105 transition-transform">
                            Modifier
                        </button>
                        <button onclick="deleteItem(${item.id})" class="status-sold px-3 py-2 rounded-lg text-xs hover:scale-105 transition-transform">
                            Supprimer
                        </button>
                    </div>
                </div>
            `).join('')}
        </div>
    `;
}

function displayItemsAsList(container, items) {
    if (items.length === 0) {
        container.innerHTML = '<div class="text-center text-gray-400 py-8">Aucun objet trouvé</div>';
        return;
    }

    container.innerHTML = `
        <div class="glass-dark rounded-2xl overflow-hidden">
            <div class="overflow-x-auto">
                <table class="w-full">
                    <thead class="bg-black bg-opacity-30">
                        <tr class="text-left">
                            <th class="px-6 py-4 text-yellow-400 font-semibold">Nom</th>
                            <th class="px-6 py-4 text-yellow-400 font-semibold hidden md:table-cell">Catégorie</th>
                            <th class="px-6 py-4 text-yellow-400 font-semibold">Statut</th>
                            <th class="px-6 py-4 text-yellow-400 font-semibold hidden lg:table-cell">Prix</th>
                            <th class="px-6 py-4 text-yellow-400 font-semibold">Actions</th>
                        </tr>
                    </thead>
                    <tbody class="divide-y divide-gray-700">
                        ${items.map(item => `
                            <tr class="hover:bg-white hover:bg-opacity-5 transition-colors">
                                <td class="px-6 py-4">
                                    <div class="font-semibold text-white">${item.name}</div>
                                    <div class="text-sm text-gray-400 md:hidden">${item.category}</div>
                                    ${item.construction_year ? `<div class="text-xs text-gray-500">${item.construction_year}</div>` : ''}
                                </td>
                                <td class="px-6 py-4 text-gray-300 hidden md:table-cell">${item.category}</td>
                                <td class="px-6 py-4">
                                    <span class="${item.status === 'Available' ? 'status-available' : 'status-sold'} px-3 py-1 rounded-full text-xs font-semibold">
                                        ${item.status === 'Available' ? 'Disponible' : 'Vendu'}
                                    </span>
                                </td>
                                <td class="px-6 py-4 text-gray-300 hidden lg:table-cell">
                                    ${item.asking_price ? formatPrice(item.asking_price) : ''}
                                    ${item.sold_price ? formatPrice(item.sold_price) : ''}
                                </td>
                                <td class="px-6 py-4">
                                    <div class="flex gap-2">
                                        <button onclick="getMarketPrice(${item.id})" class="glass px-3 py-1 rounded text-xs hover:scale-105 transition-transform">
                                            IA
                                        </button>
                                        <button onclick="editItem(${item.id})" class="glass px-3 py-1 rounded text-xs hover:scale-105 transition-transform">
                                            Modifier
                                        </button>
                                        <button onclick="deleteItem(${item.id})" class="status-sold px-3 py-1 rounded text-xs hover:scale-105 transition-transform">
                                            Supprimer
                                        </button>
                                    </div>
                                </td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        </div>
    `;
}

// Fonctions CRUD
function openCreateModal() {
    document.getElementById('modal-title').textContent = 'Nouvel Objet';
    document.getElementById('item-form').reset();
    document.getElementById('item-id').value = '';
    document.getElementById('item-modal').classList.remove('hidden');
    document.getElementById('item-modal').classList.add('flex');
}

function editItem(id) {
    const item = allItems.find(i => i.id === id);
    if (!item) return;

    document.getElementById('modal-title').textContent = 'Modifier l\\'Objet';
    document.getElementById('item-id').value = item.id;
    document.getElementById('item-name').value = item.name || '';
    document.getElementById('item-category').value = item.category || '';
    document.getElementById('item-status').value = item.status || 'Available';
    document.getElementById('item-condition').value = item.condition || '';
    document.getElementById('item-year').value = item.construction_year || '';
    document.getElementById('item-acquisition-price').value = item.acquisition_price || '';
    document.getElementById('item-asking-price').value = item.asking_price || '';
    document.getElementById('item-sold-price').value = item.sold_price || '';
    document.getElementById('item-description').value = item.description || '';

    document.getElementById('item-modal').classList.remove('hidden');
    document.getElementById('item-modal').classList.add('flex');
}

function closeModal() {
    document.getElementById('item-modal').classList.add('hidden');
    document.getElementById('item-modal').classList.remove('flex');
}

async function deleteItem(id) {
    if (!confirm('Êtes-vous sûr de vouloir supprimer cet objet ?')) return;

    try {
        const response = await fetch(`/api/items/${id}`, {
            method: 'DELETE'
        });

        if (response.ok) {
            await loadItems();
        } else {
            const errorData = await response.json();
            showError(`Erreur lors de la suppression: ${errorData.error || response.statusText}`);
        }
    } catch (error) {
        console.error('Erreur:', error);
        showError('Erreur de connexion au serveur.');
    }
}

async function getMarketPrice(itemId) {
    const button = event.target;
    const originalText = button.textContent;

    // Animation du bouton
    button.textContent = 'Analyze';
    button.classList.add('analyzing');
    button.disabled = true;

    try {
        const response = await fetch(`/api/market-price/${itemId}`);
        const data = await response.json();

        if (data.success) {
            showEstimationModal(data);
        } else {
            showError('Erreur lors de l\'estimation: ' + (data.error || 'Erreur inconnue'));
        }
    } catch (error) {
        console.error('Erreur:', error);
        showError('Erreur de connexion au serveur.');
    } finally {
        // Restaurer le bouton
        setTimeout(() => {
            button.textContent = originalText;
            button.classList.remove('analyzing');
            button.disabled = false;
        }, 500);
    }
}

function showEstimationModal(result) {
    const content = `
        <div style="margin-bottom: 25px;">
            <h3 style="color: #2563eb; font-size: 20px; margin-bottom: 10px;">Prix Estimé</h3>
            <div style="font-size: 32px; font-weight: bold; color: #059669;">${formatPrice(result.price || result.estimated_price)}</div>
        </div>

        <div style="margin-bottom: 25px;">
            <h3 style="color: #2563eb; font-size: 16px; margin-bottom: 10px;">Niveau de Confiance</h3>
            <div style="font-size: 18px; font-weight: bold; color: #dc2626;">${result.confidence}%</div>
        </div>

        ${result.analysis ? `
        <div style="margin-bottom: 25px;">
            <h3 style="color: #2563eb; font-size: 16px; margin-bottom: 10px;">Analyse Détaillée</h3>
            <div style="line-height: 1.6; color: #374151; background: #f9fafb; padding: 15px; border-radius: 8px; border-left: 4px solid #2563eb;">${result.analysis}</div>
        </div>
        ` : ''}

        ${result.market_factors ? `
        <div style="margin-bottom: 25px;">
            <h3 style="color: #2563eb; font-size: 16px; margin-bottom: 10px;">Facteurs de Marché</h3>
            <div style="line-height: 1.6; color: #374151;">${result.market_factors}</div>
        </div>
        ` : ''}

        ${result.comparable_sales ? `
        <div style="margin-bottom: 25px;">
            <h3 style="color: #2563eb; font-size: 16px; margin-bottom: 10px;">Ventes Comparables</h3>
            <div style="line-height: 1.6; color: #374151;">${result.comparable_sales}</div>
        </div>
        ` : ''}

        <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #e5e7eb; color: #6b7280; font-size: 14px;">
            Estimation générée par IA • Marché Suisse (CHF) • ${new Date().toLocaleDateString('fr-CH')}
        </div>
    `;

    document.getElementById('estimation-content').innerHTML = content;
    document.getElementById('estimation-modal').style.display = 'flex';
}

function closeEstimationModal() {
    document.getElementById('estimation-modal').style.display = 'none';
}

function showError(message) {
    const container = document.getElementById('items-container');
    container.innerHTML = `<div class="text-center text-red-400 py-8">${message}</div>`;
}

// Gestion du formulaire
document.getElementById('item-form').addEventListener('submit', async function(e) {
    e.preventDefault();

    const formData = {
        name: document.getElementById('item-name').value,
        category: document.getElementById('item-category').value,
        status: document.getElementById('item-status').value,
        condition: document.getElementById('item-condition').value,
        construction_year: parseInt(document.getElementById('item-year').value) || null,
        acquisition_price: parseFloat(document.getElementById('item-acquisition-price').value) || null,
        asking_price: parseFloat(document.getElementById('item-asking-price').value) || null,
        sold_price: parseFloat(document.getElementById('item-sold-price').value) || null,
        description: document.getElementById('item-description').value || null
    };

    const itemId = document.getElementById('item-id').value;
    const isEdit = itemId !== '';

    try {
        const response = await fetch(isEdit ? `/api/items/${itemId}` : '/api/items', {
            method: isEdit ? 'PUT' : 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });

        if (response.ok) {
            closeModal();
            await loadItems();
        } else {
            const errorData = await response.json();
            showError(`Erreur lors de la sauvegarde: ${errorData.error || response.statusText}`);
        }
    } catch (error) {
        console.error('Erreur:', error);
        showError('Erreur de connexion au serveur.');
    }
});
