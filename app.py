<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>BONVIN Collection - Gestion d'Inventaire</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-color: #0A232A;
            --glass-bg: rgba(10, 50, 60, 0.25);
            --glass-border: rgba(0, 200, 220, 0.2);
            --glass-glow: rgba(0, 220, 255, 0.15);
            --text-primary: #e0e6e7;
            --text-secondary: #88a0a8;
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background-color: var(--bg-color);
            color: var(--text-primary);
            min-height: 100vh;
            overflow-x: hidden;
            background-image: 
                radial-gradient(circle at 15% 25%, rgba(0, 220, 255, 0.2), transparent 40%),
                radial-gradient(circle at 85% 75%, rgba(10, 50, 60, 0.3), transparent 40%);
        }

        /* Glassmorphism Components */
        .glass {
            background: var(--glass-bg);
            backdrop-filter: blur(15px);
            -webkit-backdrop-filter: blur(15px);
            border: 1px solid var(--glass-border);
            border-radius: 1.5rem;
            box-shadow: 0 25px 50px -12px rgba(0,0,0,0.5);
        }

        .glass-dark {
            background: rgba(10, 40, 50, 0.4);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border: 1px solid var(--glass-border);
            border-radius: 1.5rem;
        }

        .glass-subtle {
            background: rgba(10, 35, 45, 0.3);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border: 1px solid var(--glass-border);
            border-radius: 1.5rem;
        }

        /* Glowing Effects */
        .glowing-element {
            position: relative;
            transition: all 0.3s ease;
        }

        .glowing-element:hover {
            transform: translateY(-2px);
            box-shadow: 0 0 30px var(--glass-glow);
        }

        .glowing-element:hover::before {
            opacity: 1;
        }

        .glowing-element::before {
            content: '';
            position: absolute;
            inset: -2px;
            border-radius: inherit;
            background: linear-gradient(45deg, transparent, var(--glass-glow), transparent);
            opacity: 0;
            transition: opacity 0.3s;
            z-index: -1;
            filter: blur(5px);
        }

        /* Custom Scrollbar */
        ::-webkit-scrollbar {
            width: 10px;
            height: 10px;
        }

        ::-webkit-scrollbar-track {
            background: rgba(10, 50, 60, 0.3);
            border-radius: 10px;
        }

        ::-webkit-scrollbar-thumb {
            background: rgba(0, 200, 220, 0.3);
            border-radius: 10px;
            border: 1px solid rgba(0, 200, 220, 0.1);
        }

        ::-webkit-scrollbar-thumb:hover {
            background: rgba(0, 200, 220, 0.5);
        }

        /* Form Inputs */
        .form-input {
            background: rgba(10, 30, 40, 0.5);
            border: 1px solid rgba(0, 200, 220, 0.2);
            border-radius: 0.75rem;
            padding: 0.75rem 1rem;
            color: var(--text-primary);
            transition: all 0.3s;
            width: 100%;
        }

        .form-input:focus {
            outline: none;
            border-color: rgba(0, 200, 220, 0.5);
            box-shadow: 0 0 0 3px rgba(0, 200, 220, 0.1);
            background: rgba(10, 30, 40, 0.7);
        }

        .form-input::placeholder {
            color: var(--text-secondary);
        }

        /* Status Badges */
        .status-available {
            background: rgba(22, 163, 74, 0.2);
            border: 1px solid rgba(22, 163, 74, 0.4);
            color: #4ade80;
        }

        .status-sold {
            background: rgba(234, 88, 12, 0.2);
            border: 1px solid rgba(234, 88, 12, 0.4);
            color: #fb923c;
        }

        .status-for-sale {
            background: rgba(220, 38, 38, 0.15);
            border: 1px solid rgba(220, 38, 38, 0.3);
            color: #f87171;
            animation: pulse-sale 2s ease-in-out infinite;
        }

        .status-sale-progress {
            background: rgba(59, 130, 246, 0.2);
            border: 1px solid rgba(59, 130, 246, 0.4);
            color: #60a5fa;
        }

        @keyframes pulse-sale {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.6; }
        }

        /* Floating Animation */
        @keyframes float {
            0%, 100% { transform: translateY(0px); }
            50% { transform: translateY(-10px); }
        }

        .floating-card {
            animation: float 4s ease-in-out infinite;
            animation-delay: calc(var(--float-delay, 0) * 0.1s);
        }

        /* Statistics Grid */
        .stat-card {
            background: linear-gradient(135deg, rgba(10, 50, 60, 0.3), rgba(10, 40, 50, 0.2));
            border: 1px solid rgba(0, 200, 220, 0.2);
            backdrop-filter: blur(10px);
            transition: all 0.3s;
        }

        .stat-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 40px rgba(0, 200, 220, 0.2);
            border-color: rgba(0, 200, 220, 0.4);
        }

        /* Skeleton Loading */
        .skeleton-card {
            animation: skeleton-loading 1s linear infinite alternate;
        }

        @keyframes skeleton-loading {
            0% {
                background-color: rgba(10, 50, 60, 0.3);
            }
            100% {
                background-color: rgba(10, 50, 60, 0.5);
            }
        }

        .skeleton-line {
            height: 1rem;
            background: linear-gradient(90deg, rgba(10, 50, 60, 0.3) 25%, rgba(0, 200, 220, 0.1) 50%, rgba(10, 50, 60, 0.3) 75%);
            background-size: 200% 100%;
            animation: loading 1.5s ease-in-out infinite;
            border-radius: 0.5rem;
        }

        @keyframes loading {
            0% { background-position: 200% 0; }
            100% { background-position: -200% 0; }
        }

        /* Modal Animation */
        .modal-content {
            animation: modalSlideIn 0.3s ease-out;
        }

        @keyframes modalSlideIn {
            from {
                opacity: 0;
                transform: translateY(-50px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        /* Card Hover Effects */
        .card-for-sale {
            border: 1px solid rgba(220, 38, 38, 0.3);
            background: linear-gradient(135deg, rgba(220, 38, 38, 0.05), rgba(10, 50, 60, 0.25));
        }

        .card-sold {
            opacity: 0.8;
            background: linear-gradient(135deg, rgba(234, 88, 12, 0.1), rgba(10, 50, 60, 0.25));
        }

        /* Lazy Loading */
        .floating-card {
            opacity: 0;
            transform: translateY(20px);
            transition: opacity 0.6s ease-out, transform 0.6s ease-out;
        }

        .floating-card.is-visible {
            opacity: 1;
            transform: translateY(0);
        }

        /* Filters */
        .main-filter-btn {
            transition: all 0.3s;
            position: relative;
            overflow: hidden;
        }

        .main-filter-btn.active {
            background: rgba(0, 200, 220, 0.2);
            border-color: rgba(0, 200, 220, 0.5);
            color: #00dcff;
        }

        .main-filter-btn:hover {
            transform: translateY(-2px);
        }

        /* Logo Animation */
        @keyframes logo-glow {
            0%, 100% { filter: brightness(1) drop-shadow(0 0 10px rgba(0, 220, 255, 0.5)); }
            50% { filter: brightness(1.2) drop-shadow(0 0 20px rgba(0, 220, 255, 0.8)); }
        }

        .logo {
            animation: logo-glow 3s ease-in-out infinite;
        }

        /* Category Badges */
        .category-btn {
            background: rgba(10, 40, 50, 0.3);
            border: 1px solid rgba(0, 200, 220, 0.2);
            color: var(--text-primary);
            transition: all 0.3s;
        }

        .category-btn:hover {
            background: rgba(0, 200, 220, 0.2);
            border-color: rgba(0, 200, 220, 0.5);
            transform: translateY(-2px);
        }

        /* View Buttons */
        .view-btn {
            background: rgba(10, 30, 40, 0.5);
            border: 1px solid rgba(0, 200, 220, 0.2);
            transition: all 0.3s;
        }

        .view-btn:hover {
            background: rgba(0, 200, 220, 0.2);
            transform: scale(1.05);
        }

        /* Price Highlight */
        .price-tag {
            background: linear-gradient(135deg, rgba(0, 200, 220, 0.2), rgba(0, 150, 180, 0.1));
            border: 1px solid rgba(0, 200, 220, 0.3);
            font-weight: 600;
        }

        /* Chatbot Styles */
        #chatbot-window {
            position: fixed;
            bottom: 20px;
            right: 20px;
            width: 380px;
            height: 600px;
            max-height: 80vh;
            z-index: 1000;
            transition: all 0.3s ease;
            opacity: 0;
            transform: translateY(100px) scale(0.9);
            pointer-events: none;
        }

        #chatbot-window.is-open {
            opacity: 1;
            transform: translateY(0) scale(1);
            pointer-events: all;
        }

        .chat-message {
            margin: 10px 0;
            padding: 12px 16px;
            border-radius: 18px;
            max-width: 80%;
            animation: messageSlide 0.3s ease-out;
            word-wrap: break-word;
        }

        @keyframes messageSlide {
            from {
                opacity: 0;
                transform: translateX(-20px);
            }
            to {
                opacity: 1;
                transform: translateX(0);
            }
        }

        .chat-message.user {
            background: linear-gradient(135deg, #0ea5e9, #0284c7);
            color: white;
            margin-left: auto;
            margin-right: 10px;
        }

        .chat-message.bot {
            background: rgba(10, 40, 50, 0.6);
            border: 1px solid rgba(0, 200, 220, 0.2);
            margin-left: 10px;
            margin-right: auto;
        }

        .quick-btn {
            background: rgba(0, 200, 220, 0.1);
            border: 1px solid rgba(0, 200, 220, 0.3);
            color: #22d3ee;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 12px;
            transition: all 0.2s;
        }

        .quick-btn:hover {
            background: rgba(0, 200, 220, 0.2);
            transform: scale(1.05);
        }

        #chatbot-toggle {
            position: fixed;
            bottom: 20px;
            right: 20px;
            width: 60px;
            height: 60px;
            background: linear-gradient(135deg, #0ea5e9, #0284c7);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            box-shadow: 0 4px 20px rgba(14, 165, 233, 0.4);
            transition: all 0.3s;
            z-index: 999;
        }

        #chatbot-toggle:hover {
            transform: scale(1.1);
            box-shadow: 0 6px 30px rgba(14, 165, 233, 0.6);
        }

        /* Responsive Design */
        @media (max-width: 768px) {
            #chatbot-window {
                width: calc(100vw - 40px);
                height: calc(100vh - 100px);
                bottom: 10px;
                right: 10px;
            }
            
            .floating-card {
                animation: none;
            }
        }
    </style>
</head>
<body>
    <!-- Header -->
    <header class="glass sticky top-0 z-40 border-b border-cyan-900/20">
        <div class="container mx-auto px-4 py-4">
            <div class="flex items-center justify-between">
                <div class="flex items-center gap-4">
                    <img src="/static/bonvin-logo.png" alt="BONVIN" class="h-10 w-auto logo">
                    <div>
                        <h1 class="text-2xl font-bold tracking-wider">BONVIN</h1>
                        <p class="text-sm text-slate-400">Collection Privée</p>
                    </div>
                </div>
                <button onclick="openCreateModal()" class="glowing-element glass px-6 py-2 rounded-xl text-sm font-medium hover:scale-105 transition-transform flex items-center gap-2">
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"></path>
                    </svg>
                    Nouvel Objet
                </button>
            </div>
        </div>
    </header>

    <!-- Statistics Dashboard -->
    <section class="container mx-auto px-4 py-8">
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-6">
            <div class="stat-card glass p-6 rounded-2xl">
                <h3 class="text-sm text-slate-400 mb-2">Total Objets</h3>
                <p class="text-3xl font-bold" id="stat-total">0</p>
            </div>
            <div class="stat-card glass p-6 rounded-2xl">
                <h3 class="text-sm text-slate-400 mb-2">Vendus</h3>
                <p class="text-3xl font-bold text-orange-400" id="stat-vendus">0</p>
            </div>
            <div class="stat-card glass p-6 rounded-2xl">
                <h3 class="text-sm text-slate-400 mb-2">Disponibles</h3>
                <p class="text-3xl font-bold text-green-400" id="stat-disponibles">0</p>
            </div>
            <div class="stat-card glass p-6 rounded-2xl">
                <h3 class="text-sm text-slate-400 mb-2">Valeur Ventes</h3>
                <p class="text-2xl font-bold text-cyan-400" id="stat-valeur-vente">CHF 0</p>
            </div>
            <div class="stat-card glass p-6 rounded-2xl">
                <h3 class="text-sm text-slate-400 mb-2">Valeur Stock</h3>
                <p class="text-2xl font-bold text-blue-400" id="stat-valeur-dispo">CHF 0</p>
            </div>
            <div class="stat-card glass p-6 rounded-2xl">
                <h3 class="text-sm text-slate-400 mb-2">Âge Moyen</h3>
                <p class="text-3xl font-bold text-purple-400" id="stat-age-moyen">0 ans</p>
            </div>
        </div>
    </section>

    <!-- Filters Section -->
    <section class="container mx-auto px-4 py-4">
        <div class="glass-dark p-6 rounded-2xl space-y-4">
            <!-- Main Status Filters -->
            <div class="flex flex-wrap gap-3">
                <button onclick="filterByMainStatus('all')" class="main-filter-btn glass glowing-element px-4 py-2 rounded-lg font-medium transition-all active" data-main-status="all">
                    Tous (<span id="count-all">0</span>)
                </button>
                <button onclick="filterByMainStatus('Available')" class="main-filter-btn glass glowing-element px-4 py-2 rounded-lg font-medium transition-all" data-main-status="Available">
                    Disponibles (<span id="count-available">0</span>)
                </button>
                <button onclick="filterByMainStatus('ForSale')" class="main-filter-btn glass glowing-element px-4 py-2 rounded-lg font-medium transition-all text-red-400" data-main-status="ForSale">
                    🔥 En Vente (<span id="count-for-sale">0</span>)
                </button>
                <button onclick="filterByMainStatus('Sold')" class="main-filter-btn glass glowing-element px-4 py-2 rounded-lg font-medium transition-all" data-main-status="Sold">
                    Vendus (<span id="count-sold">0</span>)
                </button>
            </div>

            <!-- Category Filters -->
            <div class="flex flex-wrap gap-2" id="category-filters">
                <!-- Dynamically populated -->
            </div>

            <!-- Search and View Options -->
            <div class="flex flex-col md:flex-row gap-4 items-center">
                <div class="relative flex-1">
                    <input type="text" id="search-input" placeholder="Rechercher..." class="form-input w-full pl-10" onkeyup="handleSearch()">
                    <svg class="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-slate-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path>
                    </svg>
                </div>
                <div class="flex gap-2">
                    <button id="view-btn-cards" onclick="setViewMode('cards')" class="view-btn glowing-element p-2 rounded-lg">
                        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z"></path>
                        </svg>
                    </button>
                    <button id="view-btn-list" onclick="setViewMode('list')" class="view-btn glowing-element p-2 rounded-lg">
                        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 10h16M4 14h16M4 18h16"></path>
                        </svg>
                    </button>
                </div>
            </div>
        </div>
    </section>

    <!-- Items Container -->
    <main class="container mx-auto px-4 py-8">
        <div id="items-container">
            <!-- Items will be dynamically loaded here -->
        </div>
    </main>

    <!-- Create/Edit Modal -->
    <div id="item-modal" class="fixed inset-0 bg-black bg-opacity-50 hidden items-center justify-center z-50 p-4">
        <div class="glass modal-content max-w-2xl w-full max-h-[90vh] overflow-hidden">
            <div class="p-6 border-b border-cyan-900/20">
                <h2 class="text-2xl font-bold" id="modal-title">Nouvel Objet</h2>
            </div>
            <form id="item-form" class="p-6 overflow-y-auto max-h-[calc(90vh-200px)]">
                <input type="hidden" id="item-id">
                
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                        <label class="block text-sm font-medium mb-2">Nom *</label>
                        <input type="text" id="item-name" class="form-input" required>
                    </div>
                    <div>
                        <label class="block text-sm font-medium mb-2">Catégorie</label>
                        <select id="item-category" class="form-input">
                            <option value="">Sélectionner...</option>
                            <option value="Voitures">Voitures</option>
                            <option value="Bateaux">Bateaux</option>
                            <option value="Appartements / maison">Appartements / maison</option>
                            <option value="Be Capital">Be Capital</option>
                            <option value="Start-ups">Start-ups</option>
                            <option value="Avions">Avions</option>
                            <option value="Montres">Montres</option>
                            <option value="Art">Art</option>
                            <option value="Bijoux">Bijoux</option>
                            <option value="Vins">Vins</option>
                            <option value="Actions">Actions</option>
                        </select>
                    </div>
                    <div>
                        <label class="block text-sm font-medium mb-2">Année de construction</label>
                        <input type="number" id="item-year" class="form-input" min="1900" max="2030">
                    </div>
                    <div>
                        <label class="block text-sm font-medium mb-2">État</label>
                        <select id="item-condition" class="form-input">
                            <option value="">Sélectionner...</option>
                            <option value="Neuf">Neuf</option>
                            <option value="Excellent">Excellent</option>
                            <option value="Bon">Bon</option>
                            <option value="Moyen">Moyen</option>
                            <option value="À rénover">À rénover</option>
                        </select>
                    </div>
                    <div id="surface-field" style="display: none;">
                        <label class="block text-sm font-medium mb-2">Surface (m²)</label>
                        <input type="number" id="item-surface" class="form-input" step="0.01">
                    </div>
                    <div id="rental-income-field" style="display: none;">
                        <label class="block text-sm font-medium mb-2">Revenus locatifs (CHF/mois)</label>
                        <input type="number" id="item-rental-income" class="form-input" step="0.01">
                    </div>
                </div>

                <!-- Champs spécifiques aux actions -->
                <div id="stock-fields" style="display: none;" class="mt-4 p-4 bg-blue-900/20 rounded-lg border border-blue-500/30">
                    <h3 class="text-lg font-semibold mb-3 text-blue-400">Informations boursières</h3>
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                            <label class="block text-sm font-medium mb-2">Symbole boursier *</label>
                            <input type="text" id="item-stock-symbol" class="form-input" placeholder="Ex: AAPL, NESN.SW">
                        </div>
                        <div>
                            <label class="block text-sm font-medium mb-2">Quantité d'actions</label>
                            <input type="number" id="item-stock-quantity" class="form-input" min="1" value="1">
                        </div>
                        <div>
                            <label class="block text-sm font-medium mb-2">Prix d'achat unitaire (CHF)</label>
                            <input type="number" id="item-stock-purchase-price" class="form-input" step="0.01">
                        </div>
                        <div>
                            <label class="block text-sm font-medium mb-2">Bourse</label>
                            <select id="item-stock-exchange" class="form-input">
                                <option value="">Sélectionner...</option>
                                <option value="SIX">SIX Swiss Exchange</option>
                                <option value="NYSE">NYSE</option>
                                <option value="NASDAQ">NASDAQ</option>
                                <option value="EURONEXT">Euronext</option>
                                <option value="LSE">London Stock Exchange</option>
                                <option value="XETRA">XETRA</option>
                                <option value="TSE">Tokyo Stock Exchange</option>
                            </select>
                        </div>
                    </div>
                </div>

                <!-- Champ prix actuel manuel pour les actions -->
                <div id="current-price-field" style="display: none;" class="mt-4 p-4 bg-cyan-900/20 rounded-lg border border-cyan-500/30">
                    <h3 class="text-lg font-semibold mb-3 text-cyan-400">Prix actuel (optionnel)</h3>
                    <div class="grid grid-cols-1 md:grid-cols-3 gap-4 items-end">
                        <div>
                            <label class="block text-sm font-medium mb-2">Prix actuel (CHF/action)</label>
                            <input type="number" id="item-current-price" class="form-input" step="0.01" placeholder="Prix manuel si mise à jour auto échoue">
                        </div>
                        <div>
                            <button type="button" id="update-current-price-btn" class="glowing-element glass px-4 py-2 rounded-lg text-sm hover:scale-105 transition-transform w-full">
                                Calculer la valeur totale
                            </button>
                        </div>
                        <div class="text-sm text-gray-400">
                            Utilisez ce champ si la mise à jour automatique échoue
                        </div>
                    </div>
                </div>

                <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
                    <div>
                        <label class="block text-sm font-medium mb-2">Prix d'acquisition (CHF)</label>
                        <input type="number" id="item-acquisition-price" class="form-input" step="0.01">
                    </div>
                    <div>
                        <label class="block text-sm font-medium mb-2">Prix demandé (CHF)</label>
                        <input type="number" id="item-asking-price" class="form-input" step="0.01">
                    </div>
                    <div>
                        <label class="block text-sm font-medium mb-2">Prix de vente (CHF)</label>
                        <input type="number" id="item-sold-price" class="form-input" step="0.01">
                    </div>
                    <div>
                        <label class="block text-sm font-medium mb-2">Statut</label>
                        <select id="item-status" class="form-input">
                            <option value="Available">Disponible</option>
                            <option value="Sold">Vendu</option>
                        </select>
                    </div>
                </div>

                <div class="mt-4">
                    <label class="flex items-center gap-3 cursor-pointer">
                        <input type="checkbox" id="item-for-sale" class="w-5 h-5 rounded border-cyan-500/50 bg-slate-800/50 text-red-500 focus:ring-red-500 focus:ring-offset-0">
                        <span class="font-medium text-red-400">🔥 Mettre en vente</span>
                    </label>
                </div>

                <!-- Section suivi des ventes -->
                <div id="sale-progress-section" style="display: none;" class="mt-4 p-4 bg-red-900/20 rounded-lg border border-red-500/30">
                    <h3 class="text-lg font-semibold mb-3 text-red-400">Suivi de la vente</h3>
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                            <label class="block text-sm font-medium mb-2">Statut de vente</label>
                            <select id="item-sale-status" class="form-input">
                                <option value="initial">Mise en vente initiale</option>
                                <option value="presentation">Préparation présentation</option>
                                <option value="intermediary">Choix intermédiaires</option>
                                <option value="inquiries">Premières demandes</option>
                                <option value="viewing">Visites programmées</option>
                                <option value="negotiation">En négociation</option>
                                <option value="offer_received">Offre reçue</option>
                                <option value="offer_accepted">Offre acceptée</option>
                                <option value="paperwork">Formalités en cours</option>
                                <option value="completed">Vente finalisée</option>
                            </select>
                        </div>
                        <div>
                            <label class="block text-sm font-medium mb-2">Date dernière action</label>
                            <input type="date" id="item-last-action-date" class="form-input">
                        </div>
                        <div class="md:col-span-2">
                            <label class="block text-sm font-medium mb-2">Détails du progrès</label>
                            <textarea id="item-sale-progress" class="form-input" rows="2" placeholder="Notes sur l'avancement de la vente..."></textarea>
                        </div>
                        <div>
                            <label class="block text-sm font-medium mb-2">Contact acheteur</label>
                            <input type="text" id="item-buyer-contact" class="form-input" placeholder="Nom, téléphone, email...">
                        </div>
                        <div>
                            <label class="block text-sm font-medium mb-2">Intermédiaire/Agent</label>
                            <input type="text" id="item-intermediary" class="form-input" placeholder="Nom de l'agence ou agent...">
                        </div>
                        <div>
                            <label class="block text-sm font-medium mb-2">Offre actuelle (CHF)</label>
                            <input type="number" id="item-current-offer" class="form-input" step="0.01">
                        </div>
                        <div>
                            <label class="block text-sm font-medium mb-2">Commission (%)</label>
                            <input type="number" id="item-commission-rate" class="form-input" step="0.01" min="0" max="100">
                        </div>
                    </div>
                </div>

                <div class="mt-4">
                    <label class="block text-sm font-medium mb-2">Description</label>
                    <textarea id="item-description" class="form-input" rows="3"></textarea>
                </div>

                <div class="flex justify-end gap-3 mt-6">
                    <button type="button" onclick="closeModal()" class="glass px-6 py-2 rounded-lg hover:bg-slate-700/50 transition-colors">
                        Annuler
                    </button>
                    <button type="submit" class="glowing-element glass px-6 py-2 rounded-lg bg-cyan-500/20 hover:bg-cyan-500/30 transition-colors">
                        Sauvegarder
                    </button>
                </div>
            </form>
        </div>
    </div>

    <!-- Estimation Modal -->
    <div id="estimation-modal" class="fixed inset-0 bg-black bg-opacity-50 hidden items-center justify-center z-50 p-4">
        <div class="glass modal-content max-w-2xl w-full max-h-[90vh] overflow-hidden">
            <div class="p-6 border-b border-cyan-900/20 flex justify-between items-center">
                <h2 class="text-2xl font-bold">Estimation de Marché par IA</h2>
                <button onclick="closeEstimationModal()" class="text-slate-400 hover:text-white transition-colors">
                    <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                    </svg>
                </button>
            </div>
            <div class="p-6 overflow-y-auto max-h-[calc(90vh-120px)]" id="estimation-content-body">
                <!-- Content will be injected here -->
            </div>
        </div>
    </div>

    <!-- Chatbot -->
    <div id="chatbot-toggle" onclick="toggleChatbot()">
        <svg class="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"></path>
        </svg>
    </div>

    <div id="chatbot-window" class="glass">
        <div id="chatbot-header" class="p-4 border-b border-cyan-900/20 flex justify-between items-center">
            <div>
                <h3 class="font-semibold">Assistant BONVIN</h3>
                <p class="text-xs text-slate-400">IA avec recherche intelligente</p>
            </div>
            <button onclick="toggleChatbot()" class="text-slate-400 hover:text-white transition-colors">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                </svg>
            </button>
        </div>
        
        <div id="chatbot-messages" class="flex-1 overflow-y-auto p-4" style="height: calc(100% - 140px);">
            <div class="text-center text-sm text-slate-500 py-8">
                <div class="mb-4">
                    <svg class="w-16 h-16 mx-auto text-cyan-500/50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"></path>
                    </svg>
                </div>
                Prêt à analyser votre collection avec l'IA
            </div>
        </div>
        
        <form id="chatbot-form" onsubmit="handleChatSubmit(event)" class="p-4 border-t border-cyan-900/20">
            <div class="flex gap-2">
                <input type="text" id="chatbot-input" placeholder="Posez votre question..." class="form-input flex-1" autocomplete="off">
                <button type="submit" class="glowing-element glass px-4 py-2 rounded-lg hover:scale-105 transition-transform">
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"></path>
                    </svg>
                </button>
            </div>
        </form>
    </div>

    <script src="/static/script.js"></script>
</body>
</html>
