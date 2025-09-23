/* Trading page client-side controller */
(function () {
    const state = {
        items: [],
        filtered: [],
        stats: {},
        filters: {
            symbol: '',
            direction: '',
            status: '',
            tag: '',
            dateStart: '',
            dateEnd: ''
        },
        currentPage: 1,
        pageSize: 15,
        loading: false
    };

    const els = {};

    const numberFields = [
        'entry_price', 'stop_loss', 'take_profit', 'exit_price', 'size',
        'strike', 'multiplier', 'iv', 'delta', 'gamma', 'theta', 'vega'
    ];

    const optionFields = [
        'option_type', 'expiration', 'strike', 'contract_symbol', 'multiplier',
        'iv', 'delta', 'gamma', 'theta', 'vega'
    ];

    function onReady(fn) {
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', fn);
        } else {
            fn();
        }
    }

    function cacheElements() {
        els.form = document.getElementById('trade-form');
        els.tableBody = document.getElementById('trades-body');
        els.tableEmpty = document.getElementById('table-empty');
        els.pagination = document.getElementById('pagination');
        els.midSummary = document.getElementById('mid-summary');
        els.stats = document.getElementById('stats');
        els.livePrice = document.getElementById('live-price');
        els.refreshBtn = document.getElementById('refresh-btn');
        els.exportCsvBtn = document.getElementById('export-csv');
        els.clearFiltersBtn = document.getElementById('clear-filters');
        els.assetType = document.getElementById('asset-type');
        els.optionsBlock = document.getElementById('options-block');
        els.optionType = document.getElementById('option-type');
        els.expSelect = document.getElementById('exp-select');
        els.chainStatus = document.getElementById('chain-status');
        els.symbolInput = document.getElementById('symbol-input');
        els.entryPriceInput = document.querySelector('input[name="entry_price"]');
        els.strikeInput = document.getElementById('strike-input');
        els.contractInput = document.getElementById('contract-input');
        els.multiplierInput = document.getElementById('multiplier-input');
        els.ivInput = document.getElementById('iv-input');
        els.deltaInput = document.getElementById('delta-input');
        els.gammaInput = document.getElementById('gamma-input');
        els.thetaInput = document.getElementById('theta-input');
        els.vegaInput = document.getElementById('vega-input');
        els.toastContainer = document.getElementById('toast-container');

        els.filters = {
            symbol: document.getElementById('filter-symbol'),
            direction: document.getElementById('filter-direction'),
            status: document.getElementById('filter-status'),
            tag: document.getElementById('filter-tag'),
            dateStart: document.getElementById('filter-date-start'),
            dateEnd: document.getElementById('filter-date-end')
        };

        els.buttons = {
            price: document.getElementById('btn-price'),
            expirations: document.getElementById('btn-exp'),
            chain: document.getElementById('btn-chain')
        };
    }

    function bindEvents() {
        if (!els.form) {
            console.warn('[Trading] Éléments introuvables.');
            return;
        }

        els.form.addEventListener('submit', handleFormSubmit);
        els.tableBody.addEventListener('click', handleTableAction);
        els.refreshBtn?.addEventListener('click', () => loadTrades(true));
        els.exportCsvBtn?.addEventListener('click', exportCsv);
        els.clearFiltersBtn?.addEventListener('click', clearFilters);
        els.assetType?.addEventListener('change', handleAssetTypeChange);
        els.buttons.price?.addEventListener('click', handleFetchPrice);
        els.buttons.expirations?.addEventListener('click', handleFetchExpirations);
        els.buttons.chain?.addEventListener('click', handleFetchChain);
        els.pagination?.addEventListener('click', handlePaginationClick);

        Object.entries(els.filters).forEach(([key, element]) => {
            if (!element) {
                return;
            }
            const eventName = element.tagName === 'SELECT' ? 'change' : 'input';
            element.addEventListener(eventName, (event) => {
                state.filters[key] = (event.target.value || '').trim();
                applyFilters();
            });
        });
    }

    function handleAssetTypeChange(event) {
        const isOption = (event.target.value || '') === 'option';
        if (els.optionsBlock) {
            els.optionsBlock.style.display = isOption ? '' : 'none';
        }
    }

    function setLoading(loading) {
        state.loading = loading;
        if (loading && els.tableBody) {
            els.tableBody.innerHTML = '<tr><td colspan="16" class="text-center py-4 text-cyan-200/70">Chargement…</td></tr>';
        }
        if (els.refreshBtn) {
            els.refreshBtn.disabled = loading;
        }
        const submitBtn = els.form?.querySelector('button[type="submit"]');
        if (submitBtn) {
            submitBtn.disabled = loading;
        }
    }

    async function loadTrades(showToast = false) {
        try {
            setLoading(true);
            const response = await fetch('/api/trades');
            if (!response.ok) {
                throw new Error('Impossible de récupérer les trades.');
            }
            const payload = await response.json();
            if (!payload.success) {
                throw new Error(payload.error || 'Erreur inconnue.');
            }
            state.items = Array.isArray(payload.items) ? payload.items : [];
            state.stats = payload.stats || {};
            state.currentPage = 1;
            applyFilters(false);
            renderStats();
            renderMidSummary();
            if (showToast) {
                notify('Journal mis à jour.', 'success');
            }
        } catch (error) {
            console.error(error);
            notify(error.message || 'Erreur de chargement.', 'error');
            if (els.tableBody) {
                els.tableBody.innerHTML = '<tr><td colspan="16" class="text-center py-4 text-red-400">Erreur de chargement</td></tr>';
            }
            state.items = [];
            state.filtered = [];
            renderStats();
            renderMidSummary();
        } finally {
            setLoading(false);
        }
    }

    function applyFilters(resetPage = true) {
        const { symbol, direction, status, tag, dateStart, dateEnd } = state.filters;
        const symbolLower = symbol.toLowerCase();
        const tagLower = tag.toLowerCase();
        const startDate = dateStart ? new Date(dateStart) : null;
        const endDate = dateEnd ? new Date(dateEnd) : null;

        state.filtered = state.items.filter((trade) => {
            if (symbolLower && !(trade.symbol || '').toLowerCase().includes(symbolLower)) {
                return false;
            }
            if (direction && String(trade.direction || '').toUpperCase() !== direction) {
                return false;
            }
            const normalizedStatus = String(trade.status || 'OPEN').toUpperCase();
            if (status && normalizedStatus !== status) {
                return false;
            }
            if (tagLower) {
                const tagsText = String(trade.tags || '').toLowerCase();
                if (!tagsText.includes(tagLower)) {
                    return false;
                }
            }
            if (startDate || endDate) {
                const entryDate = trade.entry_date ? new Date(trade.entry_date) : null;
                if (entryDate) {
                    if (startDate && entryDate < startDate) {
                        return false;
                    }
                    if (endDate) {
                        const endDateAdjusted = new Date(endDate);
                        endDateAdjusted.setHours(23, 59, 59, 999);
                        if (entryDate > endDateAdjusted) {
                            return false;
                        }
                    }
                }
            }
            return true;
        });

        if (resetPage) {
            state.currentPage = 1;
        }

        renderTable();
        renderEmptyState();
        renderPagination();
        renderStats();
        renderMidSummary();
    }

    function renderEmptyState() {
        if (!els.tableEmpty) {
            return;
        }
        if (!state.filtered.length && !state.loading) {
            els.tableEmpty.classList.remove('hidden');
        } else {
            els.tableEmpty.classList.add('hidden');
        }
    }

    function renderTable() {
        if (!els.tableBody) {
            return;
        }
        if (!state.filtered.length) {
            els.tableBody.innerHTML = state.loading ? '' : '';
            return;
        }
        const start = (state.currentPage - 1) * state.pageSize;
        const end = start + state.pageSize;
        const pageItems = state.filtered.slice(start, end);
        const rows = pageItems.map(createRow).join('');
        els.tableBody.innerHTML = rows;
    }

    function createRow(trade) {
        const rMultiple = trade.r_multiple == null ? '' : formatNumber(trade.r_multiple, 2);
        const pnl = trade.pnl == null ? '' : formatNumber(trade.pnl, 2);
        const pnlClass = Number(trade.pnl || 0) >= 0 ? 'pnl-pos' : 'pnl-neg';
        const status = (trade.status || 'OPEN').toUpperCase();
        return `
            <tr>
                <td>${safe(trade.id)}</td>
                <td><strong>${safe(trade.symbol)}</strong></td>
                <td>${safe(trade.direction)}</td>
                <td>${safe(trade.strategy)}</td>
                <td>${formatDate(trade.entry_date)}</td>
                <td>${formatNumber(trade.entry_price)}</td>
                <td>${formatNumber(trade.stop_loss)}</td>
                <td>${formatNumber(trade.take_profit)}</td>
                <td>${formatNumber(trade.size)}</td>
                <td>${formatDate(trade.exit_date)}</td>
                <td>${formatNumber(trade.exit_price)}</td>
                <td>${renderBadge(status)}</td>
                <td class="${pnlClass}">${pnl}</td>
                <td>${rMultiple}</td>
                <td>${safe(trade.tags)}</td>
                <td>
                    <div class="flex gap-2">
                        <button class="btn glass" data-action="close" data-id="${trade.id}">${status === 'CLOSED' ? 'Réouvrir' : 'Clôturer'}</button>
                        <button class="btn glass" data-action="delete" data-id="${trade.id}">Supprimer</button>
                    </div>
                </td>
            </tr>
        `;
    }

    function renderBadge(status) {
        const normalized = (status || '').toUpperCase();
        const cls = normalized === 'CLOSED' ? 'badge badge-closed' : 'badge badge-open';
        return `<span class="${cls}">${normalized}</span>`;
    }

    function renderPagination() {
        if (!els.pagination) {
            return;
        }
        const totalPages = Math.max(1, Math.ceil(state.filtered.length / state.pageSize));
        if (totalPages <= 1) {
            els.pagination.innerHTML = '';
            els.pagination.classList.add('hidden');
            return;
        }
        els.pagination.classList.remove('hidden');
        let html = '';
        for (let page = 1; page <= totalPages; page += 1) {
            const active = page === state.currentPage ? 'active' : '';
            html += `<button data-page="${page}" class="page-btn ${active}">${page}</button>`;
        }
        els.pagination.innerHTML = html;
    }

    function handlePaginationClick(event) {
        const button = event.target.closest('button[data-page]');
        if (!button) {
            return;
        }
        const page = Number(button.dataset.page);
        if (!Number.isFinite(page) || page === state.currentPage) {
            return;
        }
        state.currentPage = page;
        renderTable();
        renderPagination();
    }

    function renderStats() {
        if (!els.stats) {
            return;
        }
        const stats = state.stats || {};
        const items = [
            { key: 'Total', value: stats.total_trades ?? state.items.length },
            { key: 'Trades ouverts', value: state.items.filter((t) => (t.status || 'OPEN').toUpperCase() !== 'CLOSED').length },
            { key: 'Hit Rate', value: formatPercent(stats.hit_rate) },
            { key: 'Wins', value: stats.wins ?? 0 },
            { key: 'Losses', value: stats.losses ?? 0 },
            { key: 'Avg R', value: formatNumber(stats.avg_r, 2) },
            { key: 'Total PnL', value: formatNumber(stats.total_pnl, 2) },
            { key: 'Best R', value: stats.best_r == null ? '-' : formatNumber(stats.best_r, 2) },
            { key: 'Worst R', value: stats.worst_r == null ? '-' : formatNumber(stats.worst_r, 2) }
        ];
        els.stats.innerHTML = items.map((item) => `
            <div class="glass-dark p-3 rounded-xl">
                <div class="text-sm text-cyan-200/70">${item.key}</div>
                <div class="text-xl font-bold">${item.value}</div>
            </div>
        `).join('');
    }

    function renderMidSummary() {
        if (!els.midSummary) {
            return;
        }
        if (!state.items.length) {
            els.midSummary.classList.add('hidden');
            els.midSummary.textContent = '';
            return;
        }
        const stats = state.stats || {};
        const openTrades = state.items.filter((t) => (t.status || 'OPEN').toUpperCase() !== 'CLOSED').length;
        const closedTrades = (stats.total_trades ?? state.items.length) - openTrades;
        const hitRate = formatPercent(stats.hit_rate);
        const pnl = formatNumber(stats.total_pnl, 2);
        const pnlLabel = Number(stats.total_pnl || 0) >= 0 ? 'PnL total' : 'PnL total';
        els.midSummary.innerHTML = `
            <span class="font-semibold text-cyan-100">${openTrades}</span> trades ouverts ·
            ${closedTrades} clôturés · Hit rate <span class="font-semibold text-cyan-100">${hitRate}</span> ·
            ${pnlLabel} <span class="font-semibold ${Number(stats.total_pnl || 0) >= 0 ? 'text-green-300' : 'text-red-300'}">${pnl}</span>
        `;
        els.midSummary.classList.remove('hidden');
    }

    async function handleFormSubmit(event) {
        event.preventDefault();
        if (state.loading) {
            return;
        }
        try {
            const payload = serializeForm(els.form);
            const response = await fetch('/api/trades', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            const data = await response.json();
            if (!response.ok || !data.success) {
                throw new Error(data.error || 'Impossible de sauvegarder le trade.');
            }
            els.form.reset();
            handleAssetTypeChange({ target: els.assetType });
            notify('Trade enregistré.', 'success');
            await loadTrades();
        } catch (error) {
            notify(error.message || 'Erreur lors de la sauvegarde.', 'error');
        }
    }

    function serializeForm(form) {
        const formData = new FormData(form);
        const data = {};
        formData.forEach((value, key) => {
            if (typeof value === 'string') {
                data[key] = value.trim();
            } else {
                data[key] = value;
            }
        });

        const assetType = data.asset_type || '';
        const isOption = assetType === 'option';
        data.is_option = isOption ? 1 : 0;

        numberFields.forEach((field) => {
            if (!(field in data)) {
                return;
            }
            if (data[field] === '') {
                data[field] = null;
            } else {
                const numeric = Number(data[field]);
                data[field] = Number.isFinite(numeric) ? numeric : null;
            }
        });

        if (!isOption) {
            optionFields.forEach((field) => {
                data[field] = null;
            });
        }

        return data;
    }

    function handleTableAction(event) {
        const button = event.target.closest('button[data-action]');
        if (!button) {
            return;
        }
        const tradeId = button.dataset.id;
        if (!tradeId) {
            return;
        }
        const action = button.dataset.action;
        if (action === 'delete') {
            deleteTrade(tradeId);
        } else if (action === 'close') {
            toggleTrade(tradeId, button.textContent || '');
        }
    }

    async function deleteTrade(tradeId) {
        if (!confirm('Supprimer ce trade ?')) {
            return;
        }
        try {
            const response = await fetch(`/api/trades/${tradeId}`, { method: 'DELETE' });
            const data = await response.json();
            if (!response.ok || !data.success) {
                throw new Error(data.error || 'Suppression impossible.');
            }
            notify('Trade supprimé.', 'success');
            await loadTrades();
        } catch (error) {
            notify(error.message || 'Erreur lors de la suppression.', 'error');
        }
    }

    async function toggleTrade(tradeId, label) {
        const isClosing = label.toLowerCase().includes('clôturer');
        if (isClosing) {
            const exitPrice = prompt('Prix de sortie ?');
            if (exitPrice === null) {
                return;
            }
            const payload = {
                exit_price: exitPrice === '' ? null : Number(exitPrice),
                exit_date: new Date().toISOString()
            };
            try {
                const response = await fetch(`/api/trades/${tradeId}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                const data = await response.json();
                if (!response.ok || !data.success) {
                    throw new Error(data.error || 'Mise à jour impossible.');
                }
                notify('Trade clôturé.', 'success');
                await loadTrades();
            } catch (error) {
                notify(error.message || 'Erreur lors de la mise à jour.', 'error');
            }
        } else {
            try {
                const response = await fetch(`/api/trades/${tradeId}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ exit_price: null, exit_date: null, status: 'OPEN' })
                });
                const data = await response.json();
                if (!response.ok || !data.success) {
                    throw new Error(data.error || 'Réouverture impossible.');
                }
                notify('Trade réouvert.', 'success');
                await loadTrades();
            } catch (error) {
                notify(error.message || 'Erreur lors de la mise à jour.', 'error');
            }
        }
    }

    async function handleFetchPrice() {
        const symbol = (els.symbolInput?.value || '').trim();
        if (!symbol) {
            notify('Veuillez saisir un symbole.', 'warning');
            return;
        }
        if (els.livePrice) {
            els.livePrice.textContent = 'Chargement…';
        }
        try {
            const response = await fetch(`/api/price?symbol=${encodeURIComponent(symbol)}`);
            const data = await response.json();
            if (!response.ok || !data.success) {
                throw new Error(data.error || 'Prix indisponible.');
            }
            const price = data.data && data.data.price != null ? Number(data.data.price) : null;
            const currency = data.data && data.data.currency ? data.data.currency : '';
            if (els.livePrice) {
                els.livePrice.textContent = price != null ? `Prix: ${formatNumber(price)} ${currency}` : 'Indisponible';
            }
            if (price != null && els.entryPriceInput && !els.entryPriceInput.value) {
                els.entryPriceInput.value = price;
            }
        } catch (error) {
            if (els.livePrice) {
                els.livePrice.textContent = error.message || 'Erreur';
            }
            notify(error.message || 'Erreur prix.', 'error');
        }
    }

    async function handleFetchExpirations() {
        const symbol = (els.symbolInput?.value || '').trim();
        if (!symbol || !els.expSelect || !els.chainStatus) {
            return;
        }
        els.expSelect.innerHTML = '';
        els.chainStatus.textContent = 'Chargement expirations…';
        try {
            const response = await fetch(`/api/options/expirations?symbol=${encodeURIComponent(symbol)}`);
            const data = await response.json();
            if (!response.ok || !data.success) {
                throw new Error(data.error || 'Échéances indisponibles.');
            }
            const expirations = Array.isArray(data.expirations) ? data.expirations : [];
            expirations.forEach((exp) => {
                const option = document.createElement('option');
                option.value = exp;
                option.textContent = exp;
                els.expSelect.appendChild(option);
            });
            els.chainStatus.textContent = `${expirations.length} échéances`;
        } catch (error) {
            els.chainStatus.textContent = error.message || 'Erreur';
            notify(error.message || 'Erreur expirations.', 'error');
        }
    }

    async function handleFetchChain() {
        const symbol = (els.symbolInput?.value || '').trim();
        const expiration = (els.expSelect?.value || '').trim();
        if (!symbol || !expiration || !els.chainStatus) {
            if (els.chainStatus) {
                els.chainStatus.textContent = 'Symbol/expiration requis';
            }
            return;
        }
        els.chainStatus.textContent = 'Chargement chaîne…';
        try {
            const response = await fetch(`/api/options/chain?symbol=${encodeURIComponent(symbol)}&expiration=${encodeURIComponent(expiration)}`);
            const data = await response.json();
            if (!response.ok || !data.success) {
                throw new Error(data.error || 'Chaîne indisponible.');
            }
            const calls = Array.isArray(data.calls) ? data.calls : [];
            const puts = Array.isArray(data.puts) ? data.puts : [];
            const collection = (els.optionType?.value || 'CALL') === 'CALL' ? calls : puts;
            const spot = els.entryPriceInput && els.entryPriceInput.value ? Number(els.entryPriceInput.value) : NaN;
            let best = null;
            let bestDiff = Number.POSITIVE_INFINITY;
            collection.forEach((contract) => {
                const strike = Number(contract.strike);
                if (!Number.isFinite(strike)) {
                    return;
                }
                const diff = Number.isFinite(spot) ? Math.abs(strike - spot) : Math.abs(strike);
                if (diff < bestDiff) {
                    bestDiff = diff;
                    best = contract;
                }
            });
            if (best) {
                if (els.strikeInput) {
                    els.strikeInput.value = best.strike ?? '';
                }
                if (els.contractInput) {
                    els.contractInput.value = best.contractSymbol ?? '';
                }
                if (els.multiplierInput) {
                    els.multiplierInput.value = best.contractSize ?? best.multiplier ?? 100;
                }
                if (els.ivInput) {
                    els.ivInput.value = best.impliedVolatility ?? '';
                }
                if (els.deltaInput) {
                    els.deltaInput.value = best.delta ?? '';
                }
                if (els.gammaInput) {
                    els.gammaInput.value = best.gamma ?? '';
                }
                if (els.thetaInput) {
                    els.thetaInput.value = best.theta ?? '';
                }
                if (els.vegaInput) {
                    els.vegaInput.value = best.vega ?? '';
                }
                const premium = best.lastPrice ?? best.bid ?? null;
                if (premium != null && els.entryPriceInput && !els.entryPriceInput.value) {
                    els.entryPriceInput.value = premium;
                }
            }
            els.chainStatus.textContent = `Chaîne chargée (${collection.length} contrats)`;
        } catch (error) {
            els.chainStatus.textContent = error.message || 'Erreur';
            notify(error.message || 'Erreur chaîne.', 'error');
        }
    }

    function clearFilters() {
        Object.entries(els.filters).forEach(([key, element]) => {
            if (!element) {
                return;
            }
            element.value = '';
            state.filters[key] = '';
        });
        applyFilters();
    }

    function exportCsv() {
        const rows = state.filtered.length ? state.filtered : state.items;
        if (!rows.length) {
            notify('Aucune donnée à exporter.', 'warning');
            return;
        }
        const headers = [
            'id', 'symbol', 'direction', 'strategy', 'entry_date', 'entry_price', 'stop_loss',
            'take_profit', 'size', 'exit_date', 'exit_price', 'status', 'pnl', 'r_multiple', 'tags'
        ];
        const csvLines = [headers.join(';')];
        rows.forEach((trade) => {
            const values = headers.map((key) => {
                const value = trade[key];
                if (value == null) {
                    return '';
                }
                if (typeof value === 'number') {
                    return formatNumber(value);
                }
                return String(value).replace(/;/g, ',');
            });
            csvLines.push(values.join(';'));
        });
        const blob = new Blob([csvLines.join('\n')], { type: 'text/csv;charset=utf-8;' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `trading_journal_${new Date().toISOString().slice(0, 10)}.csv`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
        notify('Export CSV généré.', 'success');
    }

    function notify(message, type = 'info') {
        if (!els.toastContainer) {
            return;
        }
        els.toastContainer.classList.remove('hidden');
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.textContent = message;
        toast.addEventListener('click', () => toast.remove());
        els.toastContainer.appendChild(toast);
        setTimeout(() => {
            toast.classList.add('toast-hide');
            setTimeout(() => {
                toast.remove();
                if (!els.toastContainer.hasChildNodes()) {
                    els.toastContainer.classList.add('hidden');
                }
            }, 150);
        }, 4000);
    }

    function formatNumber(value, decimals = 2) {
        if (value === null || value === undefined || value === '') {
            return '';
        }
        const number = Number(value);
        if (!Number.isFinite(number)) {
            return '';
        }
        return number.toFixed(decimals);
    }

    function formatPercent(value) {
        if (value === null || value === undefined || value === '') {
            return '0%';
        }
        const number = Number(value);
        if (!Number.isFinite(number)) {
            return '0%';
        }
        return `${(number * 100).toFixed(1)}%`;
    }

    function formatDate(value) {
        if (!value) {
            return '';
        }
        const date = new Date(value);
        if (Number.isNaN(date.getTime())) {
            return value;
        }
        return date.toLocaleString('fr-CH', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    }

    function safe(value) {
        if (value === null || value === undefined) {
            return '';
        }
        return String(value);
    }

    window.TradingPage = {
        init() {
            cacheElements();
            if (!els.form || !els.tableBody) {
                console.warn('[Trading] Éléments requis manquants.');
                return;
            }
            bindEvents();
            handleAssetTypeChange({ target: els.assetType || { value: '' } });
            loadTrades();
        }
    };
})();

