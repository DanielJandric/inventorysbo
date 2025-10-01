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
        // Pas de formulaire scénario, tout se fait dans Settings
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
        // Ajouter cache-busting pour éviter cache navigateur
        const response = await fetch('/api/snb/model/latest?t=' + Date.now(), {
            cache: 'no-store',
            headers: {
                'Cache-Control': 'no-cache, no-store, must-revalidate',
                'Pragma': 'no-cache'
            }
        });
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
        // Lancer la tâche GPT-5 en background
        const response = await fetch('/api/snb/explain', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ model, tone: 'concise', lang: 'fr-CH' })
        });
        const data = await response.json();
        
        if (response.status === 202 && data.task_id) {
            // Tâche lancée, polling du résultat
            return await pollExplainTask(data.task_id);
        } else if (data.success && data.explanation) {
            // Résultat immédiat (fallback)
            return data.explanation;
        } else {
            throw new Error(data.error || 'Failed to fetch explanation');
        }
    }

    async function pollExplainTask(taskId) {
        console.log('🔍 Polling GPT-5 task:', taskId);
        const maxAttempts = 40; // 40 x 2s = 80s max
        let attempts = 0;
        
        while (attempts < maxAttempts) {
            try {
                const response = await fetch(`/api/snb/explain/status/${taskId}`);
                const data = await response.json();
                console.log(`📊 Poll attempt ${attempts + 1}:`, data.state, data.meta);
                
                if (data.state === 'SUCCESS') {
                    console.log('✅ GPT-5 SUCCESS, explanation:', data.explanation ? 'présent' : 'MANQUANT');
                    if (data.explanation) {
                        return data.explanation;
                    } else {
                        console.error('❌ SUCCESS mais pas d\'explanation dans la réponse!');
                        throw new Error('Explanation missing in success response');
                    }
                }
                
                if (data.state === 'FAILURE') {
                    console.error('❌ GPT-5 FAILURE:', data.error);
                    throw new Error(data.error || 'GPT-5 task failed');
                }
                
                // PROGRESS ou PENDING: attendre et réessayer
                attempts++;
                await new Promise(resolve => setTimeout(resolve, 2000));
                
            } catch (error) {
                console.error('Polling error:', error);
                attempts++;
                if (attempts >= maxAttempts) {
                    throw error;
                }
                await new Promise(resolve => setTimeout(resolve, 2000));
            }
        }
        
        console.error('❌ Timeout après', maxAttempts, 'tentatives');
        throw new Error('Timeout: GPT-5 prend trop de temps');
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
        console.log('🎨 renderNarrative appelé avec:', explanation);
        
        if (!explanation) {
            console.warn('⚠️ Explanation est null/undefined, section cachée');
            els.narrativeSection?.classList.add('hidden');
            return;
        }

        console.log('✅ Affichage du narratif...');
        els.narrativeSection?.classList.remove('hidden');

        if (els.narrativeHeadline) {
            const headline = explanation.headline || '—';
            console.log('  Headline:', headline.substring(0, 50) + '...');
            els.narrativeHeadline.textContent = headline;
        }

        if (els.narrativeBullets) {
            const bullets = explanation.bullets || [];
            console.log('  Bullets:', bullets.length, 'points');
            els.narrativeBullets.innerHTML = bullets.map(b => `<li>${b}</li>`).join('');
        }

        if (els.narrativeRisks) {
            const risks = explanation.risks || [];
            console.log('  Risks:', risks.length, 'risques');
            els.narrativeRisks.innerHTML = risks.map(r => `<span class="risk-tag">${r}</span>`).join('');
        }

        if (els.narrativeSteps) {
            const steps = explanation.next_steps || [];
            console.log('  Next steps:', steps.length, 'actions');
            els.narrativeSteps.innerHTML = steps.map(s => `<li>${s}</li>`).join('');
        }

        if (els.narrativeOneliner) {
            const oneliner = explanation.one_liner || '—';
            console.log('  One-liner:', oneliner.substring(0, 50) + '...');
            els.narrativeOneliner.textContent = oneliner;
        }
        
        console.log('✅ Narratif affiché avec succès');
    }

    function renderModel(model) {
        state.currentModel = model;
        renderMetadata(model);
        renderKPIs(model);
        renderProbsChart(model.probs);
        renderPathChart(model.path);
    }

    // === EVENT HANDLERS ===

    // Fonction handleScenarioSubmit retirée - scénarios gérés dans Settings

    async function loadLatestModel() {
        try {
            setLoading(true);

            const model = await fetchLatestModel();
            renderModel(model);
            showMainContent();

            // Fetch explanation avec retry automatique
            try {
                const explanation = await fetchExplanation(model);
                if (explanation) {
                    renderNarrative(explanation);
                } else {
                    // Retry après 3 secondes si pas de résultat
                    console.log('Narratif vide, retry dans 3s...');
                    setTimeout(async () => {
                        try {
                            const retryExplanation = await fetchExplanation(model);
                            if (retryExplanation) {
                                renderNarrative(retryExplanation);
                            }
                        } catch (retryErr) {
                            console.error('Retry failed:', retryErr);
                        }
                    }, 3000);
                }
            } catch (err) {
                console.error('Failed to fetch explanation:', err);
                // Afficher une section avec message d'erreur au lieu de cacher
                if (els.narrativeSection) {
                    els.narrativeSection.classList.remove('hidden');
                    if (els.narrativeHeadline) {
                        els.narrativeHeadline.textContent = 'Analyse en cours de génération...';
                    }
                    if (els.narrativeBullets) {
                        els.narrativeBullets.innerHTML = '<li class="text-gray-400">Le narratif GPT-5 est en cours de génération. Rafraîchissez la page dans quelques secondes.</li>';
                    }
                }
            }

        } catch (error) {
            console.error('Load error:', error);
            showError(error.message || 'Erreur lors du chargement du modèle. Vérifiez que des données ont été ingérées.');
        } finally {
            setLoading(false);
        }
    }

    // Fonctions de collecte retirées - tout géré dans Settings maintenant

    // === PUBLIC API ===

    window.SNBTaux = {
        init() {
            cacheElements();
            bindEvents();
            loadLatestModel();
        },
        loadLatestModel,
        state
    };
})();

