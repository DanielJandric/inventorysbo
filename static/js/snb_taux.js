/**
 * SNB Taux - Frontend Controller
 * Gère les charts (Chart.js), interactions et API calls
 */

(function () {
    const state = {
        currentModel: null,
        charts: {
            probs: null,
            path: null
        },
        loading: false
    };

    const els = {};

    // === HELPERS ===

    function cacheElements() {
        els.loadingSection = document.getElementById('loading-section');
        els.errorSection = document.getElementById('error-section');
        els.errorMessage = document.getElementById('error-message');
        els.mainContent = document.getElementById('main-content');
        
        // Metadata
        els.modelDate = document.getElementById('model-date');
        els.modelVersion = document.getElementById('model-version');
        
        // KPIs
        els.kpiCpi = document.getElementById('kpi-cpi');
        els.kpiKof = document.getElementById('kpi-kof');
        els.kpiOutputGap = document.getElementById('kpi-output-gap');
        els.kpiIstar = document.getElementById('kpi-istar');
        
        // Charts
        els.chartProbs = document.getElementById('chart-probs');
        els.chartPath = document.getElementById('chart-path');
        els.probsLegend = document.getElementById('probs-legend');
        
        // Scenario form
        els.scenarioForm = document.getElementById('scenario-form');
        
        // Narrative
        els.narrativeSection = document.getElementById('narrative-section');
        els.narrativeHeadline = document.getElementById('narrative-headline');
        els.narrativeBullets = document.getElementById('narrative-bullets');
        els.narrativeRisks = document.getElementById('narrative-risks');
        els.narrativeSteps = document.getElementById('narrative-steps');
        els.narrativeOneliner = document.getElementById('narrative-oneliner');
    }

    function bindEvents() {
        if (els.scenarioForm) {
            els.scenarioForm.addEventListener('submit', handleScenarioSubmit);
        }
    }

    function setLoading(loading) {
        state.loading = loading;
        if (loading) {
            els.loadingSection?.classList.remove('hidden');
            els.errorSection?.classList.add('hidden');
            els.mainContent?.classList.add('hidden');
        } else {
            els.loadingSection?.classList.add('hidden');
        }
    }

    function showError(message) {
        if (els.errorMessage) {
            els.errorMessage.textContent = message;
        }
        els.errorSection?.classList.remove('hidden');
        els.mainContent?.classList.add('hidden');
        els.loadingSection?.classList.add('hidden');
    }

    function showMainContent() {
        els.mainContent?.classList.remove('hidden');
        els.errorSection?.classList.add('hidden');
        els.loadingSection?.classList.add('hidden');
    }

    function formatPercent(value, decimals = 2) {
        if (value == null) return '—';
        return `${(value * 100).toFixed(decimals)}%`;
    }

    function formatNumber(value, decimals = 2) {
        if (value == null) return '—';
        return Number(value).toFixed(decimals);
    }

    // === API CALLS ===

    async function fetchLatestModel() {
        const response = await fetch('/api/snb/model/latest');
        const data = await response.json();
        if (!response.ok || !data.success) {
            throw new Error(data.error || 'Failed to fetch model');
        }
        return data.result;
    }

    async function runScenario(overrides) {
        const response = await fetch('/api/snb/model/run', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ overrides })
        });
        const data = await response.json();
        if (!response.ok || !data.success) {
            throw new Error(data.error || 'Failed to run scenario');
        }
        return data.result;
    }

    async function fetchExplanation(model) {
        const response = await fetch('/api/snb/explain', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ model, tone: 'concise', lang: 'fr-CH' })
        });
        const data = await response.json();
        if (!response.ok || !data.success) {
            throw new Error(data.error || 'Failed to fetch explanation');
        }
        return data.explanation;
    }

    // === RENDER FUNCTIONS ===

    function renderMetadata(model) {
        if (els.modelDate) {
            els.modelDate.textContent = model.as_of || '—';
        }
        if (els.modelVersion) {
            els.modelVersion.textContent = model.version || '—';
        }
    }

    function renderKPIs(model) {
        if (els.kpiCpi) {
            els.kpiCpi.textContent = `${formatNumber(model.inputs.cpi_yoy_pct, 2)} %`;
        }
        if (els.kpiKof) {
            els.kpiKof.textContent = formatNumber(model.inputs.kof_barometer, 1);
        }
        if (els.kpiOutputGap) {
            els.kpiOutputGap.textContent = `${formatNumber(model.output_gap_pct, 2)} %`;
        }
        if (els.kpiIstar) {
            els.kpiIstar.textContent = `${formatNumber(model.i_star_next_pct, 2)} %`;
        }
    }

    function renderProbsChart(probs) {
        if (!els.chartProbs) return;

        const ctx = els.chartProbs.getContext('2d');

        // Destroy existing chart
        if (state.charts.probs) {
            state.charts.probs.destroy();
        }

        state.charts.probs = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: ['Baisse', 'Maintien', 'Hausse'],
                datasets: [{
                    label: 'Probabilités',
                    data: [probs.cut, probs.hold, probs.hike],
                    backgroundColor: [
                        'rgba(248, 113, 113, 0.6)',
                        'rgba(34, 197, 94, 0.6)',
                        'rgba(96, 165, 250, 0.6)'
                    ],
                    borderColor: [
                        'rgba(248, 113, 113, 1)',
                        'rgba(34, 197, 94, 1)',
                        'rgba(96, 165, 250, 1)'
                    ],
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 1,
                        ticks: {
                            callback: (value) => `${(value * 100).toFixed(0)}%`,
                            color: '#88a0a8'
                        },
                        grid: {
                            color: 'rgba(0, 200, 220, 0.1)'
                        }
                    },
                    x: {
                        ticks: {
                            color: '#88a0a8'
                        },
                        grid: {
                            display: false
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        callbacks: {
                            label: (context) => `${(context.parsed.y * 100).toFixed(1)}%`
                        }
                    }
                }
            }
        });

        // Legend custom
        if (els.probsLegend) {
            els.probsLegend.innerHTML = `
                <div class="prob-bar bg-green-500/20 border border-green-500/40 text-green-300">
                    Maintien: ${formatPercent(probs.hold, 1)}
                </div>
                <div class="prob-bar bg-red-500/20 border border-red-500/40 text-red-300">
                    Baisse: ${formatPercent(probs.cut, 1)}
                </div>
                <div class="prob-bar bg-blue-500/20 border border-blue-500/40 text-blue-300">
                    Hausse: ${formatPercent(probs.hike, 1)}
                </div>
            `;
        }
    }

    function renderPathChart(path) {
        if (!els.chartPath) return;

        const ctx = els.chartPath.getContext('2d');

        // Destroy existing chart
        if (state.charts.path) {
            state.charts.path.destroy();
        }

        const labels = path.map(p => `M+${p.month_ahead}`);
        const ruleData = path.map(p => p.rule);
        const marketData = path.map(p => p.market);
        const fusedData = path.map(p => p.fused);

        state.charts.path = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'Règle (modèle)',
                        data: ruleData,
                        borderColor: 'rgba(251, 191, 36, 1)',
                        backgroundColor: 'rgba(251, 191, 36, 0.1)',
                        borderWidth: 2,
                        pointRadius: 0,
                        tension: 0.3
                    },
                    {
                        label: 'Marché (OIS/Fut.)',
                        data: marketData,
                        borderColor: 'rgba(96, 165, 250, 1)',
                        backgroundColor: 'rgba(96, 165, 250, 0.1)',
                        borderWidth: 2,
                        pointRadius: 0,
                        tension: 0.3
                    },
                    {
                        label: 'Fusion (Kalman)',
                        data: fusedData,
                        borderColor: 'rgba(34, 211, 238, 1)',
                        backgroundColor: 'rgba(34, 211, 238, 0.1)',
                        borderWidth: 3,
                        pointRadius: 0,
                        tension: 0.3
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: (value) => `${value.toFixed(2)}%`,
                            color: '#88a0a8'
                        },
                        grid: {
                            color: 'rgba(0, 200, 220, 0.1)'
                        }
                    },
                    x: {
                        ticks: {
                            color: '#88a0a8',
                            maxRotation: 45,
                            minRotation: 45
                        },
                        grid: {
                            display: false
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: true,
                        position: 'top',
                        labels: {
                            color: '#88a0a8',
                            font: {
                                size: 12
                            }
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: (context) => `${context.dataset.label}: ${context.parsed.y.toFixed(3)}%`
                        }
                    }
                }
            }
        });
    }

    function renderNarrative(explanation) {
        if (!explanation) {
            els.narrativeSection?.classList.add('hidden');
            return;
        }

        els.narrativeSection?.classList.remove('hidden');

        if (els.narrativeHeadline) {
            els.narrativeHeadline.textContent = explanation.headline || '—';
        }

        if (els.narrativeBullets) {
            const bullets = explanation.bullets || [];
            els.narrativeBullets.innerHTML = bullets.map(b => `<li>${b}</li>`).join('');
        }

        if (els.narrativeRisks) {
            const risks = explanation.risks || [];
            els.narrativeRisks.innerHTML = risks.map(r => `<span class="risk-tag">${r}</span>`).join('');
        }

        if (els.narrativeSteps) {
            const steps = explanation.next_steps || [];
            els.narrativeSteps.innerHTML = steps.map(s => `<li>${s}</li>`).join('');
        }

        if (els.narrativeOneliner) {
            els.narrativeOneliner.textContent = explanation.one_liner || '—';
        }
    }

    function renderModel(model) {
        state.currentModel = model;
        renderMetadata(model);
        renderKPIs(model);
        renderProbsChart(model.probs);
        renderPathChart(model.path);
    }

    // === EVENT HANDLERS ===

    async function handleScenarioSubmit(event) {
        event.preventDefault();
        if (state.loading) return;

        try {
            setLoading(true);

            const formData = new FormData(els.scenarioForm);
            const overrides = {};

            for (const [key, value] of formData.entries()) {
                if (value.trim() !== '') {
                    overrides[key] = parseFloat(value);
                }
            }

            // Run scenario
            const model = await runScenario(overrides);
            renderModel(model);
            showMainContent();

            // Fetch explanation
            try {
                const explanation = await fetchExplanation(model);
                renderNarrative(explanation);
            } catch (err) {
                console.error('Failed to fetch explanation:', err);
                // Non-blocking
            }

        } catch (error) {
            console.error('Scenario error:', error);
            showError(error.message || 'Erreur lors du calcul du scénario');
        } finally {
            setLoading(false);
        }
    }

    async function loadLatestModel() {
        try {
            setLoading(true);

            const model = await fetchLatestModel();
            renderModel(model);
            showMainContent();

            // Fetch explanation (non-blocking)
            try {
                const explanation = await fetchExplanation(model);
                renderNarrative(explanation);
            } catch (err) {
                console.error('Failed to fetch explanation:', err);
            }

        } catch (error) {
            console.error('Load error:', error);
            showError(error.message || 'Erreur lors du chargement du modèle. Vérifiez que des données ont été ingérées.');
        } finally {
            setLoading(false);
        }
    }

    // === COLLECTION TRIGGERS ===

    async function triggerCollection(mode) {
        const statusDiv = document.getElementById('collection-status');
        const messageDiv = document.getElementById('collection-message');
        
        if (!statusDiv || !messageDiv) return;
        
        try {
            // Afficher le statut
            statusDiv.classList.remove('hidden');
            statusDiv.querySelector('.p-3').className = 'p-3 rounded-lg border border-blue-500/40 bg-blue-500/10';
            messageDiv.innerHTML = `
                <div class="flex items-center gap-2">
                    <div class="loading-spinner" style="width: 1rem; height: 1rem; border-width: 2px;"></div>
                    <span class="text-blue-300">Collecte ${mode} en cours... (peut prendre jusqu'à 2 minutes)</span>
                </div>
            `;
            
            // Appeler l'API
            const response = await fetch('/api/snb/trigger/collect', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ mode })
            });
            
            const data = await response.json();
            
            if (response.ok && data.success) {
                // Succès
                statusDiv.querySelector('.p-3').className = 'p-3 rounded-lg border border-green-500/40 bg-green-500/10';
                messageDiv.innerHTML = `
                    <div class="text-green-300">
                        <div class="font-semibold mb-1">✅ ${data.message}</div>
                        <div class="text-xs opacity-80">Le modèle a été recalculé automatiquement</div>
                    </div>
                `;
                
                // Recharger le modèle après 2 secondes
                setTimeout(() => {
                    loadLatestModel();
                }, 2000);
                
                // Masquer après 10 secondes
                setTimeout(() => {
                    statusDiv.classList.add('hidden');
                }, 10000);
                
            } else {
                // Erreur
                statusDiv.querySelector('.p-3').className = 'p-3 rounded-lg border border-red-500/40 bg-red-500/10';
                messageDiv.innerHTML = `
                    <div class="text-red-300">
                        <div class="font-semibold mb-1">❌ Erreur de collecte</div>
                        <div class="text-xs opacity-80">${data.error || 'Erreur inconnue'}</div>
                    </div>
                `;
            }
            
        } catch (error) {
            console.error('Collection error:', error);
            statusDiv.querySelector('.p-3').className = 'p-3 rounded-lg border border-red-500/40 bg-red-500/10';
            messageDiv.innerHTML = `
                <div class="text-red-300">
                    <div class="font-semibold mb-1">❌ Erreur réseau</div>
                    <div class="text-xs opacity-80">${error.message}</div>
                </div>
            `;
        }
    }

    // === PUBLIC API ===

    window.SNBTaux = {
        init() {
            cacheElements();
            bindEvents();
            loadLatestModel();
        },
        loadLatestModel,
        triggerCollection,
        state
    };
})();

