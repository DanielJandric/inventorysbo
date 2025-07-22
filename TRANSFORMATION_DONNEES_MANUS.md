# 🔄 Transformation des Données API Manus → Frontend

## 📊 Flux de Données Complet

### 1. **API Manus Source** 
```
https://y0h0i3cqzyko.manus.space/api/report
```

**Format de réponse brut :**
```json
{
  "api_call_timestamp": "2025-07-22T12:00:00Z",
  "generation_time": "2.5s",
  "report": {
    "content": {
      "html": "<h1>Rapport de Marché...</h1>",
      "markdown": "# RAPPORT DE MARCHÉ QUOTIDIEN\n## 22 July 2025..."
    },
    "key_metrics": {
      "sp500": "+0.5%",
      "nasdaq": "+1.2%"
    },
    "summary": {
      "key_points": ["Marché haussier", "Tech en forme"]
    },
    "metadata": {
      "sections": ["Actions", "Obligations", "Crypto"]
    }
  }
}
```

### 2. **Transformation dans `manus_integration.py`**

#### A. **Fonction `get_market_report()`** (lignes 181-237)
```python
# Récupère les données brutes de l'API Manus
response = self.session.get(f"{self.base_url}/api/report", timeout=30)
data = response.json()

# Transforme en format standardisé
market_report = {
    'timestamp': datetime.now().isoformat(),
    'report_date': data.get('api_call_timestamp'),
    'generation_time': data.get('generation_time'),
    'source': 'Manus API',
    'status': 'complete',
    
    # Métriques de marché
    'market_metrics': report.get('key_metrics', {}),
    
    # Contenu - NOUVELLE STRUCTURE
    'content': {
        'html': report.get('content', {}).get('html', ''),
        'markdown': report.get('content', {}).get('markdown', '')
    },
    
    # Résumé
    'summary': report.get('summary', {}),
    
    # Sections
    'sections': report.get('metadata', {}).get('sections', [])
}
```

#### B. **Fonction `generate_market_briefing()`** (lignes 252-282)
```python
# Transforme le rapport en briefing pour le frontend
return {
    'status': 'success',
    'timestamp': datetime.now().isoformat(),
    'source': 'Manus API',
    'briefing': {
        'title': f"Briefing de Marché - {market_report.get('report_date')}",
        'summary': market_report.get('summary', {}).get('key_points', []),
        'metrics': market_report.get('market_metrics', {}),
        'content': market_report.get('content', {}).get('markdown', '')  # ← CONTENU MARKDOWN
    }
}
```

### 3. **Transformation dans `app.py`**

#### A. **Fonction `generate_market_briefing()`** (lignes 4781-4820)
```python
# Appelle l'API Manus via le wrapper
briefing = generate_market_briefing_manus()

if briefing.get('status') == 'success':
    # Extrait le contenu markdown pour le frontend
    briefing_content = briefing.get('briefing', {}).get('content', '')
    
    return {
        'status': 'success',
        'briefing': {
            'content': briefing_content,  # ← CONTENU MARKDOWN PUR
            'title': briefing.get('briefing', {}).get('title'),
            'summary': briefing.get('briefing', {}).get('summary', []),
            'metrics': briefing.get('briefing', {}).get('metrics', {})
        }
    }
```

#### B. **Route `/api/market-updates/trigger`** (lignes 4660-4740)
```python
# 1. Génère le briefing
briefing_result = generate_market_briefing()

# 2. Extrait le contenu markdown
briefing = briefing_result.get('briefing', {}).get('content', '')

# 3. Sauvegarde en base avec format frontend
update_data = {
    "content": briefing,  # ← CONTENU MARKDOWN PUR
    "date": datetime.now().strftime("%Y-%m-%d"),
    "time": datetime.now().strftime("%H:%M"),
    "created_at": datetime.now().isoformat(),
    "trigger_type": "manual"
}

# 4. Insère dans Supabase
response = supabase.table("market_updates").insert(update_data).execute()
```

#### C. **Route `/api/market-report/manus`** (lignes 4619-4659)
```python
# Récupère depuis la base de données (format frontend)
response = supabase.table("market_updates").select("*").order("created_at", desc=True).limit(1).execute()

if response.data:
    latest_report = response.data[0]
    return jsonify({
        "success": True,
        "report": {
            "date": latest_report.get("date", ""),
            "time": latest_report.get("time", ""),
            "content": latest_report.get("content", ""),  # ← CONTENU MARKDOWN PUR
            "created_at": latest_report.get("created_at", "")
        }
    })
```

### 4. **Affichage Frontend** (`templates/markets.html`)

#### A. **Appel API** (ligne 274)
```javascript
const response = await fetch('/api/market-report/manus');
const data = await response.json();

if (data.success) {
    displayMarketReport(data.report);  // ← data.report contient le format frontend
}
```

#### B. **Fonction d'affichage** (lignes 290-317)
```javascript
function displayMarketReport(report) {
    container.innerHTML = `
        <div class="glass-dark p-6 glowing-element">
            <div class="flex items-center justify-between mb-4">
                <div class="flex items-center gap-3">
                    <div>
                        <div class="text-lg font-semibold">Rapport du ${report.date}</div>
                        <div class="text-sm text-slate-400">Généré à ${report.time}</div>
                    </div>
                </div>
            </div>
            <div class="market-content prose prose-invert max-w-none">
                <div class="whitespace-pre-wrap text-slate-300 leading-relaxed">
                    ${report.content}  // ← CONTENU MARKDOWN AFFICHÉ
                </div>
            </div>
        </div>
    `;
}
```

## 🔄 **Résumé de la Transformation**

### **Format API Manus → Format Frontend**

| Étape | Format Source | Format Destination | Transformation |
|-------|---------------|-------------------|----------------|
| **1. API Manus** | `report.content.markdown` | `content` (string) | Extraction du contenu markdown |
| **2. Base de données** | `content` (string) | `content` (string) | Stockage direct |
| **3. Frontend** | `content` (string) | Affichage HTML | `whitespace-pre-wrap` |

### **Points Clés :**

1. **Contenu Markdown** : L'API Manus fournit le contenu en format Markdown, qui est préservé tout au long du processus
2. **Format Frontend** : Le frontend utilise `whitespace-pre-wrap` pour préserver les sauts de ligne et la mise en forme Markdown
3. **Base de données** : Le contenu est stocké tel quel en tant que texte brut
4. **Affichage** : Le Markdown est affiché comme du texte formaté avec les sauts de ligne préservés

### **Avantages de cette approche :**
- ✅ **Simplicité** : Pas de conversion HTML complexe
- ✅ **Performance** : Stockage et transmission efficaces
- ✅ **Flexibilité** : Le Markdown peut être facilement converti en HTML si nécessaire
- ✅ **Compatibilité** : Fonctionne avec tous les navigateurs 