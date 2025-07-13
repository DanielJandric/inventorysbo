import os
import requests
import json
from flask import Flask, render_template_string, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Configuration Supabase - VRAIES DONNÉES
SUPABASE_URL = "https://meygeqsilwenitneamzt.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im1leWdlcXNpbHdlbml0bmVhbXp0Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTIyNDU2ODQsImV4cCI6MjA2NzgyMTY4NH0.xaxlxH2pY98Lc1HST7JyyAZ73JW_pgK8Lk3YhwTmJDk"

# Configuration OpenAI - À configurer via variable d'environnement
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', 'your_openai_api_key_here')

def get_supabase_headers():
    return {
        'apikey': SUPABASE_KEY,
        'Authorization': f'Bearer {SUPABASE_KEY}',
        'Content-Type': 'application/json'
    }

def get_items_from_supabase():
    """Récupérer les objets depuis Supabase - TABLE ITEMS"""
    try:
        response = requests.get(f"{SUPABASE_URL}/rest/v1/items", headers=get_supabase_headers())
        if response.status_code == 200:
            return response.json()
        else:
            return []
    except Exception as e:
        print(f"Erreur Supabase: {e}")
        return []

@app.route('/')
def index():
    return render_template_string('''
<!DOCTYPE html>
<html lang="fr" class="h-full">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>BONVIN - Collection Privée</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        /* Glassmorphisme */
        .glass {
            background: rgba(139, 69, 19, 0.15);
            backdrop-filter: blur(15px);
            border: 1px solid rgba(218, 165, 32, 0.2);
        }
        
        .glass-dark {
            background: rgba(101, 67, 33, 0.25);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(218, 165, 32, 0.3);
        }
        
        /* Couleurs glassmorphiques pour les statuts */
        .status-available {
            background: rgba(34, 197, 94, 0.2);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(34, 197, 94, 0.4);
            color: rgb(74, 222, 128);
        }
        
        .status-sold {
            background: rgba(234, 88, 12, 0.2);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(234, 88, 12, 0.4);
            color: rgb(251, 146, 60);
        }
        
        /* Gradient de fond marron/or inspiré de l'image BONVIN */
        body {
            background: linear-gradient(135deg, #3c2415 0%, #5d4037 25%, #8d6e63 50%, #a1887f 75%, #d7ccc8 100%);
            min-height: 100vh;
        }
        
        /* Cartes flottantes */
        .floating-card {
            box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.4);
            transition: all 0.3s ease;
        }
        
        .floating-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 35px 60px -12px rgba(0, 0, 0, 0.5);
        }
        
        /* Modal glassmorphique */
        .modal-backdrop {
            background: rgba(0, 0, 0, 0.7);
            backdrop-filter: blur(5px);
        }
        
        .modal-content {
            background: rgba(60, 36, 21, 0.9);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(218, 165, 32, 0.3);
        }
        
        /* Modal simple pour estimation IA */
        .estimation-modal {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.8);
            display: none;
            justify-content: center;
            align-items: center;
            z-index: 1000;
        }
        
        .estimation-content {
            background: white;
            padding: 30px;
            border-radius: 10px;
            max-width: 600px;
            width: 90%;
            max-height: 80vh;
            overflow-y: auto;
            color: black;
            font-family: Arial, sans-serif;
        }
    </style>
</head>
<body class="h-full text-white">
    <div class="min-h-screen p-4 md:p-8">
        <!-- En-tête avec image BONVIN -->
        <div class="text-center mb-12">
            <div class="flex justify-center mb-6">
                <img src="/static/bonvin-logo.png" alt="BONVIN" class="w-80 h-auto md:w-96">
            </div>
            <h1 class="text-5xl md:text-7xl font-bold bg-gradient-to-r from-yellow-400 to-yellow-600 bg-clip-text text-transparent mb-4">
                Collection Privée
            </h1>
        </div>

        <!-- Statistiques Dashboard -->
        <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 mb-8">
            <div class="glass rounded-xl p-4 text-center">
                <div class="text-sm text-gray-300 mb-1">TOTAL</div>
                <div id="stat-total" class="text-2xl font-bold text-yellow-400">-</div>
            </div>
            <div class="glass rounded-xl p-4 text-center">
                <div class="text-sm text-gray-300 mb-1">VENDUS</div>
                <div id="stat-vendus" class="text-2xl font-bold text-orange-400">-</div>
            </div>
            <div class="glass rounded-xl p-4 text-center">
                <div class="text-sm text-gray-300 mb-1">DISPONIBLE</div>
                <div id="stat-disponibles" class="text-2xl font-bold text-green-400">-</div>
            </div>
            <div class="glass rounded-xl p-4 text-center">
                <div class="text-sm text-gray-300 mb-1">VALEUR VENTE</div>
                <div id="stat-valeur-vente" class="text-2xl font-bold text-purple-400">-</div>
            </div>
            <div class="glass rounded-xl p-4 text-center">
                <div class="text-sm text-gray-300 mb-1">VALEUR DISPO</div>
                <div id="stat-valeur-dispo" class="text-2xl font-bold text-blue-400">-</div>
            </div>
            <div class="glass rounded-xl p-4 text-center">
                <div class="text-sm text-gray-300 mb-1">ÂGE MOYEN</div>
                <div id="stat-age-moyen" class="text-2xl font-bold text-pink-400">-</div>
            </div>
        </div>

        <!-- Filtres et Actions -->
        <div class="glass-dark rounded-2xl p-6 mb-8">
            <div class="flex flex-col lg:flex-row justify-between items-start lg:items-center gap-4 mb-6">
                <button onclick="openCreateModal()" class="status-available px-6 py-3 rounded-xl font-semibold hover:scale-105 transition-transform">
                    + Nouvel objet
                </button>
            </div>
            
            <!-- Mode d'affichage -->
            <div class="mb-6">
                <h3 class="text-lg font-semibold mb-3 text-yellow-400">Affichage</h3>
                <div class="flex gap-3">
                    <button onclick="setViewMode('cards')" class="view-btn glass px-4 py-2 rounded-lg hover:scale-105 transition-transform ring-2 ring-yellow-400" data-mode="cards">
                        Cartes
                    </button>
                    <button onclick="setViewMode('list')" class="view-btn glass px-4 py-2 rounded-lg hover:scale-105 transition-transform" data-mode="list">
                        Liste
                    </button>
                </div>
            </div>
            
            <!-- Barre de recherche -->
            <div class="mb-6">
                <h3 class="text-lg font-semibold mb-3 text-yellow-400">Recherche</h3>
                <div class="relative">
                    <input 
                        type="text" 
                        id="search-input" 
                        placeholder="Rechercher par nom, catégorie, description..." 
                        class="w-full glass rounded-xl px-4 py-3 pl-12 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-yellow-400 transition-all"
                        oninput="handleSearch()"
                    >
                    <svg class="absolute left-4 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path>
                    </svg>
                </div>
            </div>
            
            <!-- Filtres -->
            <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <!-- Filtres par catégorie -->
                <div>
                    <h3 class="text-lg font-semibold mb-3 text-yellow-400">Catégories</h3>
                    <div class="flex flex-wrap gap-2">
                        <button onclick="filterByCategory('all')" class="category-btn glass px-3 py-2 rounded-lg text-sm hover:scale-105 transition-transform ring-2 ring-yellow-400" data-category="all">
                            Toutes
                        </button>
                        <button onclick="filterByCategory('Voitures')" class="category-btn glass px-3 py-2 rounded-lg text-sm hover:scale-105 transition-transform" data-category="Voitures">
                            Voitures
                        </button>
                        <button onclick="filterByCategory('Bateaux')" class="category-btn glass px-3 py-2 rounded-lg text-sm hover:scale-105 transition-transform" data-category="Bateaux">
                            Bateaux
                        </button>
                        <button onclick="filterByCategory('Appartements / maison')" class="category-btn glass px-3 py-2 rounded-lg text-sm hover:scale-105 transition-transform" data-category="Appartements / maison">
                            Immobilier
                        </button>
                        <button onclick="filterByCategory('Be Capital')" class="category-btn glass px-3 py-2 rounded-lg text-sm hover:scale-105 transition-transform" data-category="Be Capital">
                            Be Capital
                        </button>
                        <button onclick="filterByCategory('Start ups')" class="category-btn glass px-3 py-2 rounded-lg text-sm hover:scale-105 transition-transform" data-category="Start ups">
                            Start-ups
                        </button>
                        <button onclick="filterByCategory('Avions')" class="category-btn glass px-3 py-2 rounded-lg text-sm hover:scale-105 transition-transform" data-category="Avions">
                            Avions
                        </button>
                        <button onclick="filterByCategory('Montres')" class="category-btn glass px-3 py-2 rounded-lg text-sm hover:scale-105 transition-transform" data-category="Montres">
                            Montres
                        </button>
                        <button onclick="filterByCategory('Art')" class="category-btn glass px-3 py-2 rounded-lg text-sm hover:scale-105 transition-transform" data-category="Art">
                            Art
                        </button>
                        <button onclick="filterByCategory('Bijoux')" class="category-btn glass px-3 py-2 rounded-lg text-sm hover:scale-105 transition-transform" data-category="Bijoux">
                            Bijoux
                        </button>
                        <button onclick="filterByCategory('Vins')" class="category-btn glass px-3 py-2 rounded-lg text-sm hover:scale-105 transition-transform" data-category="Vins">
                            Vins
                        </button>
                    </div>
                </div>
                
                <!-- Stat                <!-- Statut et État -->
                <div>
                    <h3 class="text-lg font-semibold mb-3 text-yellow-400">Filtres</h3>
                    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                        <!-- Catégories -->
                        <div>
                            <h4 class="text-sm font-medium text-gray-400 mb-3">Catégories</h4>
                            <div class="flex flex-wrap gap-2">
                                <button onclick="filterByCategory('all')" class="category-btn glass px-3 py-2 rounded-lg text-sm hover:scale-105 transition-transform ring-2 ring-yellow-400" data-category="all">
                                    Toutes
                                </button>
                                <button onclick="filterByCategory('Voitures')" class="category-btn glass px-3 py-2 rounded-lg text-sm hover:scale-105 transition-transform" data-category="Voitures">
                                    Voitures
                                </button>
                                <button onclick="filterByCategory('Bateaux')" class="category-btn glass px-3 py-2 rounded-lg text-sm hover:scale-105 transition-transform" data-category="Bateaux">
                                    Bateaux
                                </button>
                                <button onclick="filterByCategory('Appartements / maison')" class="category-btn glass px-3 py-2 rounded-lg text-sm hover:scale-105 transition-transform" data-category="Appartements / maison">
                                    Immobilier
                                </button>
                                <button onclick="filterByCategory('Be Capital')" class="category-btn glass px-3 py-2 rounded-lg text-sm hover:scale-105 transition-transform" data-category="Be Capital">
                                    Be Capital
                                </button>
                                <button onclick="filterByCategory('Start ups')" class="category-btn glass px-3 py-2 rounded-lg text-sm hover:scale-105 transition-transform" data-category="Start ups">
                                    Start-ups
                                </button>
                                <button onclick="filterByCategory('Avions')" class="category-btn glass px-3 py-2 rounded-lg text-sm hover:scale-105 transition-transform" data-category="Avions">
                                    Avions
                                </button>
                                <button onclick="filterByCategory('Montres')" class="category-btn glass px-3 py-2 rounded-lg text-sm hover:scale-105 transition-transform" data-category="Montres">
                                    Montres
                                </button>
                                <button onclick="filterByCategory('Art')" class="category-btn glass px-3 py-2 rounded-lg text-sm hover:scale-105 transition-transform" data-category="Art">
                                    Art
                                </button>
                                <button onclick="filterByCategory('Bijoux')" class="category-btn glass px-3 py-2 rounded-lg text-sm hover:scale-105 transition-transform" data-category="Bijoux">
                                    Bijoux
                                </button>
                                <button onclick="filterByCategory('Vins')" class="category-btn glass px-3 py-2 rounded-lg text-sm hover:scale-105 transition-transform" data-category="Vins">
                                    Vins
                                </button>
                            </div>
                        </div>
                        
                        <!-- Statut -->
                        <div>
                            <h4 class="text-sm font-medium text-gray-400 mb-3">Statut</h4>
                            <div class="flex flex-wrap gap-2">
                                <button onclick="filterByStatus('all')" class="filter-btn glass px-3 py-2 rounded-lg text-sm hover:scale-105 transition-transform ring-2 ring-yellow-400" data-status="all">
                                    Tous <span id="count-all" class="ml-1 text-yellow-400">-</span>
                                </button>
                                <button onclick="filterByStatus('Available')" class="filter-btn status-available px-3 py-2 rounded-lg text-sm hover:scale-105 transition-transform" data-status="Available">
                                    Disponible <span id="count-available" class="ml-1">-</span>
                                </button>
                                <button onclick="filterByStatus('Sold')" class="filter-btn status-sold px-3 py-2 rounded-lg text-sm hover:scale-105 transition-transform" data-status="Sold">
                                    Vendu <span id="count-sold" class="ml-1">-</span>
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Zone d'affichage des objets -->
        <div id="items-container" class="space-y-6">
            <div class="text-center text-gray-300 py-8">
                <div class="animate-spin w-8 h-8 border-4 border-yellow-400 border-t-transparent rounded-full mx-auto mb-4"></div>
                Chargement des objets...
            </div>
        </div>
    </div>

    <!-- Modal de création/modification glassmorphique -->
    <div id="item-modal" class="fixed inset-0 modal-backdrop hidden items-center justify-center z-50 p-4">
        <div class="modal-content rounded-3xl p-8 w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <div class="flex justify-between items-center mb-6">
                <h2 id="modal-title" class="text-3xl font-bold text-yellow-400">Nouvel Objet</h2>
                <button onclick="closeModal()" class="text-gray-400 hover:text-white text-3xl">&times;</button>
            </div>
            
            <form id="item-form" class="space-y-6">
                <input type="hidden" id="item-id">
                
                <!-- Nom -->
                <div>
                    <label class="block text-sm font-semibold text-gray-300 mb-2">Nom de l'objet</label>
                    <input type="text" id="item-name" class="w-full glass rounded-xl px-4 py-3 text-white placeholder-gray-400" placeholder="Ex: Lamborghini Urus SE" required>
                </div>
                
                <!-- Catégorie -->
                <div>
                    <label class="block text-sm font-semibold text-gray-300 mb-2">Catégorie</label>
                    <select id="item-category" class="w-full glass rounded-xl px-4 py-3 text-white" required>
                        <option value="">Sélectionner une catégorie</option>
                        <option value="Voitures">Voitures</option>
                        <option value="Bateaux">Bateaux</option>
                        <option value="Avions">Avions</option>
                        <option value="Appartements">Appartements</option>
                        <option value="Maisons">Maisons</option>
                        <option value="Be Capital">Be Capital</option>
                        <option value="Montres">Montres</option>
                        <option value="Bijoux">Bijoux</option>
                        <option value="Art">Art</option>
                        <option value="Vins">Vins</option>
                        <option value="Autres">Autres</option>
                    </select>
                </div>
                
                <!-- Statut -->
                <div>
                    <label class="block text-sm font-semibold text-gray-300 mb-2">Statut</label>
                    <select id="item-status" class="w-full glass rounded-xl px-4 py-3 text-white" required>
                        <option value="Available">Disponible</option>
                        <option value="Sold">Vendu</option>
                    </select>
                </div>
                
                <!-- Condition -->
                <div>
                    <label class="block text-sm font-semibold text-gray-300 mb-2">État</label>
                    <select id="item-condition" class="w-full glass rounded-xl px-4 py-3 text-white">
                        <option value="Excellent">Excellent</option>
                        <option value="Très bon">Très bon</option>
                        <option value="Bon">Bon</option>
                        <option value="Correct">Correct</option>
                    </select>
                </div>
                
                <!-- Année de construction -->
                <div>
                    <label class="block text-sm font-semibold text-gray-300 mb-2">Année de construction</label>
                    <input type="number" id="item-year" class="w-full glass rounded-xl px-4 py-3 text-white placeholder-gray-400" placeholder="Ex: 2023" min="1900" max="2030">
                </div>
                
                <!-- Prix d'acquisition -->
                <div>
                    <label class="block text-sm font-semibold text-gray-300 mb-2">Prix d'acquisition (CHF)</label>
                    <input type="number" id="item-acquisition-price" class="w-full glass rounded-xl px-4 py-3 text-white placeholder-gray-400" placeholder="Ex: 250000" min="0" step="0.01">
                </div>
                
                <!-- Prix demandé -->
                <div>
                    <label class="block text-sm font-semibold text-gray-300 mb-2">Prix demandé (CHF)</label>
                    <input type="number" id="item-asking-price" class="w-full glass rounded-xl px-4 py-3 text-white placeholder-gray-400" placeholder="Ex: 280000" min="0" step="0.01">
                </div>
                
                <!-- Prix de vente -->
                <div>
                    <label class="block text-sm font-semibold text-gray-300 mb-2">Prix de vente (CHF)</label>
                    <input type="number" id="item-sold-price" class="w-full glass rounded-xl px-4 py-3 text-white placeholder-gray-400" placeholder="Ex: 275000" min="0" step="0.01">
                </div>
                
                <!-- Description -->
                <div>
                    <label class="block text-sm font-semibold text-gray-300 mb-2">Description</label>
                    <textarea id="item-description" class="w-full glass rounded-xl px-4 py-3 text-white placeholder-gray-400 h-24" placeholder="Description détaillée de l'objet..."></textarea>
                </div>
                
                <!-- Boutons -->
                <div class="flex gap-4 pt-4">
                    <button type="submit" class="status-available px-8 py-3 rounded-xl font-semibold hover:scale-105 transition-transform flex-1">
                        Sauvegarder
                    </button>
                    <button type="button" onclick="closeModal()" class="glass px-8 py-3 rounded-xl font-semibold hover:scale-105 transition-transform">
                        Annuler
                    </button>
                </div>
            </form>
        </div>
    </div>

    <!-- Modal simple pour estimation IA -->
    <div id="estimation-modal" class="estimation-modal">
        <div class="estimation-content">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                <h2 style="margin: 0; color: #333; font-size: 24px;">Estimation IA</h2>
                <button onclick="closeEstimationModal()" style="background: none; border: none; font-size: 24px; cursor: pointer;">&times;</button>
            </div>
            <div id="estimation-content"></div>
        </div>
    </div>

    <script>
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
                    document.getElementById('items-container').innerHTML = '<div class="text-center text-red-400 py-8">Erreur lors du chargement des objets</div>';
                }
            } catch (error) {
                console.error('Erreur:', error);
                document.getElementById('items-container').innerHTML = '<div class="text-center text-red-400 py-8">Erreur de connexion</div>';
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
                    alert('Erreur lors de la suppression');
                }
            } catch (error) {
                console.error('Erreur:', error);
                alert('Erreur lors de la suppression');
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
                    showPriceModal(data);
                } else {
                    alert('Erreur lors de l\'estimation: ' + (data.error || 'Erreur inconnue'));
                }
            } catch (error) {
                console.error('Erreur:', error);
                alert('Erreur de connexion');
            } finally {
                // Restaurer le bouton
                setTimeout(() => {
                    button.textContent = originalText;
                    button.classList.remove('analyzing');
                    button.disabled = false;
                }, 500);
            }
        }on showEstimationModal(result) {
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
                    alert('Erreur lors de la sauvegarde');
                }
            } catch (error) {
                console.error('Erreur:', error);
                alert('Erreur lors de la sauvegarde');
            }
        });
    </script>
</body>
</html>
    ''')

@app.route('/api/items', methods=['GET'])
def get_items():
    """Récupérer tous les objets depuis Supabase"""
    try:
        items = get_items_from_supabase()
        return jsonify(items)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/items', methods=['POST'])
def create_item():
    """Créer un nouvel objet dans Supabase"""
    try:
        data = request.json
        response = requests.post(
            f"{SUPABASE_URL}/rest/v1/items",
            headers=get_supabase_headers(),
            json=data
        )
        
        if response.status_code in [200, 201]:
            return jsonify({"success": True})
        else:
            return jsonify({"error": "Erreur lors de la création"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/items/<int:item_id>', methods=['PUT'])
def update_item(item_id):
    """Modifier un objet existant dans Supabase"""
    try:
        data = request.json
        response = requests.patch(
            f"{SUPABASE_URL}/rest/v1/items?id=eq.{item_id}",
            headers=get_supabase_headers(),
            json=data
        )
        
        if response.status_code == 204:
            return jsonify({"success": True})
        else:
            return jsonify({"error": "Erreur lors de la modification"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/items/<int:item_id>', methods=['DELETE'])
def delete_item(item_id):
    """Supprimer un objet de Supabase"""
    try:
        response = requests.delete(
            f"{SUPABASE_URL}/rest/v1/items?id=eq.{item_id}",
            headers=get_supabase_headers()
        )
        
        if response.status_code == 204:
            return jsonify({"success": True})
        else:
            return jsonify({"error": "Erreur lors de la suppression"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/market-price/<int:item_id>')
def get_market_price(item_id):
    """Obtenir une estimation de prix via OpenAI GPT-4o"""
    try:
        # Récupérer l'objet depuis Supabase
        items = get_items_from_supabase()
        item = next((i for i in items if i['id'] == item_id), None)
        
        if not item:
            return jsonify({"error": "Objet non trouvé"}), 404
        
        # Prompt optimisé qui analyse d'abord le titre
        prompt = f"""ESTIMATION DE PRIX - MARCHÉ SUISSE

OBJET À ANALYSER:
Titre: "{item.get('name', 'objet')}"

DONNÉES COMPLÉMENTAIRES (si disponibles):
- Catégorie: {item.get('category', 'non spécifiée')}
- Année: {item.get('construction_year', 'non spécifiée')}
- État: {item.get('condition', 'non spécifié')}

INSTRUCTIONS:
1. COMMENCE TOUJOURS par analyser le titre pour identifier l'objet
2. Le titre seul doit suffire pour une première estimation
3. Utilise les données complémentaires pour affiner SI elles sont utiles
4. L'absence d'informations complémentaires ne doit PAS empêcher l'estimation
5. Donne un prix réaliste pour le marché suisse en CHF

Réponds UNIQUEMENT en JSON valide:
{{
    "price": [prix en CHF basé principalement sur le titre],
    "confidence": [0-100, selon la qualité des infos du titre],
    "analysis": "Ton raisonnement depuis le titre, puis affinements",
    "market_factors": "Facteurs de marché",
    "comparable_sales": "Exemples similaires"
}}"""
        
        # Appel à l'API OpenAI
        openai_response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "gpt-4o",
                "messages": [
                    {"role": "system", "content": "Tu es un expert en évaluation. Réponds uniquement en JSON valide."},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 300,
                "temperature": 0.1
            }
        )
        
        if openai_response.status_code == 200:
            openai_data = openai_response.json()
            content = openai_data['choices'][0]['message']['content'].strip()
            
            # Nettoyer le contenu pour extraire le JSON
            if content.startswith('```json'):
                content = content[7:]
            if content.startswith('```'):
                content = content[3:]
            if content.endswith('```'):
                content = content[:-3]
            content = content.strip()
            
            # Parser la réponse JSON
            try:
                price_data = json.loads(content)
                
                # Validation des prix pour éviter les aberrations
                estimated_price = price_data.get("price", 0)
                if estimated_price > 50000000 or estimated_price < 0:  # Prix aberrant
                    return jsonify({
                        "price": 0,
                        "confidence": 0,
                        "analysis": "Données pas disponibles - estimation aberrante détectée",
                        "market_factors": "Données pas disponibles",
                        "comparable_sales": "Données pas disponibles",
                        "success": True
                    })
                
                price_data["price"] = estimated_price
                price_data['success'] = True
                return jsonify(price_data)
            except json.JSONDecodeError as e:
                print(f"Erreur JSON: {e}")
                print(f"Contenu reçu: {content}")
                # Fallback honnête : données pas disponibles
                return jsonify({
                    "price": 0,
                    "confidence": 0,
                    "analysis": "Données pas disponibles pour cette estimation. L'IA n'a pas pu fournir une évaluation fiable pour cet objet.",
                    "market_factors": "Données pas disponibles",
                    "comparable_sales": "Données pas disponibles",
                    "success": True
                })
        else:
            return jsonify({"error": "Erreur OpenAI"}), 500
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/static/<path:filename>')
def static_files(filename):
    """Servir les fichiers statiques"""
    return app.send_static_file(filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

