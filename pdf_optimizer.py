"""
Module d'optimisation pour la génération de PDFs professionnels
Optimisé pour réduire la consommation mémoire et améliorer la qualité
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional
from flask import Response, jsonify

logger = logging.getLogger(__name__)

def get_optimized_pdf_css() -> str:
    """Retourne un CSS optimisé pour PDFs noir et blanc avec styles professionnels"""
    return '''
    @page {
        size: A4;
        margin: 0.75in;
        @top-center {
            content: "BONVIN - Collection Privée";
            font-size: 9pt;
            font-family: Arial, sans-serif;
            color: #333;
        }
        @bottom-center {
            content: "Page " counter(page) " sur " counter(pages);
            font-size: 9pt;
            font-family: Arial, sans-serif;
            color: #333;
        }
    }
    
    /* Reset et base */
    * {
        box-sizing: border-box;
    }
    
    body {
        font-family: Arial, sans-serif;
        font-size: 10pt;
        line-height: 1.4;
        color: #000;
        margin: 0;
        padding: 0;
        background: white;
    }
    
    /* En-têtes */
    .header {
        text-align: center;
        margin-bottom: 2em;
        padding-bottom: 1em;
        border-bottom: 2px solid #000;
    }
    
    .header h1 {
        font-size: 18pt;
        font-weight: bold;
        margin: 0 0 0.5em 0;
        color: #000;
    }
    
    .header .subtitle {
        font-size: 12pt;
        color: #333;
        margin: 0;
    }
    
    .header .date {
        font-size: 10pt;
        color: #666;
        margin-top: 0.5em;
    }
    
    /* Sections */
    .section {
        margin-bottom: 2em;
        page-break-inside: avoid;
    }
    
    .section-title {
        font-size: 14pt;
        font-weight: bold;
        margin-bottom: 1em;
        color: #000;
        border-bottom: 1px solid #333;
        padding-bottom: 0.5em;
        text-transform: uppercase;
        letter-spacing: 0.5pt;
    }
    
    /* Items */
    .item {
        margin-bottom: 1em;
        padding: 0.75em;
        border: 1px solid #ccc;
        border-radius: 3px;
        background: #fafafa;
        page-break-inside: avoid;
    }
    
    .item-name {
        font-weight: bold;
        font-size: 11pt;
        color: #000;
        margin-bottom: 0.5em;
    }
    
    .item-details {
        color: #333;
        font-size: 9pt;
        line-height: 1.3;
    }
    
    .item-details strong {
        color: #000;
    }
    
    /* Prix et valeurs */
    .price {
        font-weight: bold;
        font-size: 11pt;
        color: #000;
        background: #f0f0f0;
        padding: 0.25em 0.5em;
        border-radius: 2px;
        display: inline-block;
    }
    
    .value-highlight {
        font-weight: bold;
        color: #000;
        background: #e8e8e8;
        padding: 0.2em 0.4em;
        border-radius: 2px;
    }
    
    /* Statuts avec styles distinctifs */
    .status-available { 
        color: #000; 
        font-weight: bold;
        background: #e8f5e8;
        padding: 0.2em 0.4em;
        border-radius: 2px;
        border: 1px solid #ccc;
    }
    .status-for-sale { 
        color: #000; 
        font-weight: bold;
        background: #fff3cd;
        padding: 0.2em 0.4em;
        border-radius: 2px;
        border: 1px solid #ccc;
    }
    .status-sold { 
        color: #000; 
        font-weight: bold;
        background: #f8d7da;
        padding: 0.2em 0.4em;
        border-radius: 2px;
        border: 1px solid #ccc;
    }
    
    /* Tableaux optimisés */
    table {
        width: 100%;
        border-collapse: collapse;
        margin-bottom: 1em;
        font-size: 9pt;
        page-break-inside: avoid;
    }
    
    th {
        background-color: #333;
        color: white;
        font-weight: bold;
        padding: 0.5em;
        text-align: left;
        border: 1px solid #000;
        font-size: 9pt;
    }
    
    td {
        border: 1px solid #ccc;
        padding: 0.4em;
        text-align: left;
        vertical-align: top;
    }
    
    tr:nth-child(even) {
        background-color: #f9f9f9;
    }
    
    /* Résumés et statistiques */
    .summary-box {
        border: 2px solid #333;
        padding: 1em;
        margin: 1em 0;
        background: #f8f8f8;
        page-break-inside: avoid;
    }
    
    .summary-title {
        font-size: 12pt;
        font-weight: bold;
        color: #000;
        margin-bottom: 0.5em;
        border-bottom: 1px solid #333;
        padding-bottom: 0.25em;
    }
    
    .summary-item {
        margin-bottom: 0.5em;
        display: flex;
        justify-content: space-between;
    }
    
    .summary-label {
        font-weight: bold;
        color: #333;
    }
    
    .summary-value {
        font-weight: bold;
        color: #000;
    }
    
    /* Grilles et layouts */
    .grid-2 {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 1em;
        margin-bottom: 1em;
    }
    
    .grid-3 {
        display: grid;
        grid-template-columns: 1fr 1fr 1fr;
        gap: 1em;
        margin-bottom: 1em;
    }
    
    /* Utilitaires */
    .text-center { text-align: center; }
    .text-right { text-align: right; }
    .text-bold { font-weight: bold; }
    .text-small { font-size: 8pt; }
    .text-large { font-size: 12pt; }
    
    .mb-1 { margin-bottom: 0.5em; }
    .mb-2 { margin-bottom: 1em; }
    .mb-3 { margin-bottom: 1.5em; }
    
    .mt-1 { margin-top: 0.5em; }
    .mt-2 { margin-top: 1em; }
    .mt-3 { margin-top: 1.5em; }
    
    /* Saut de page contrôlé */
    .page-break { page-break-before: always; }
    .no-break { page-break-inside: avoid; }
    
    /* Notes et commentaires */
    .note {
        font-size: 8pt;
        color: #666;
        font-style: italic;
        border-left: 2px solid #ccc;
        padding-left: 0.5em;
        margin: 0.5em 0;
    }
    
    /* Codes et références */
    .code {
        font-family: 'Courier New', monospace;
        background: #f0f0f0;
        padding: 0.2em 0.4em;
        border-radius: 2px;
        font-size: 8pt;
    }
    '''

def generate_optimized_pdf(html_content: str, filename: str, custom_css: Optional[str] = None) -> Response:
    """
    Génère un PDF optimisé avec gestion d'erreur mémoire
    
    Args:
        html_content: Contenu HTML à convertir
        filename: Nom du fichier PDF
        custom_css: CSS personnalisé (optionnel)
    
    Returns:
        Response Flask avec le PDF ou une erreur
    """
    try:
        from weasyprint import HTML, CSS
        from weasyprint.text.fonts import FontConfiguration
        
        # Configuration des polices
        font_config = FontConfiguration()
        
        # Utiliser le CSS optimisé par défaut ou le CSS personnalisé
        css_string = custom_css if custom_css else get_optimized_pdf_css()
        
        # Créer le PDF avec optimisations mémoire
        html_doc = HTML(string=html_content)
        css_doc = CSS(string=css_string, font_config=font_config)
        
        # Options pour réduire la consommation mémoire
        pdf = html_doc.write_pdf(
            stylesheets=[css_doc], 
            font_config=font_config,
            optimize_images=True,
            jpeg_quality=85
        )
        
        # Retourner le PDF
        response = Response(pdf, mimetype='application/pdf')
        response.headers['Content-Disposition'] = f'attachment; filename={filename}'
        
        return response
        
    except MemoryError:
        logger.error("❌ Erreur mémoire lors de la génération PDF")
        return jsonify({
            "error": "Erreur mémoire. Le rapport est trop volumineux. Essayez de filtrer les données."
        }), 500
    except ImportError:
        logger.error("❌ WeasyPrint non installé")
        return jsonify({
            "error": "WeasyPrint non installé. Installez avec: pip install weasyprint"
        }), 500
    except Exception as e:
        logger.error(f"❌ Erreur génération PDF: {e}")
        return jsonify({
            "error": f"Erreur lors de la génération PDF: {str(e)}"
        }), 500

def format_price_for_pdf(price: float) -> str:
    """Formate un prix pour l'affichage dans le PDF"""
    if not price or price == 0:
        return '0 CHF'
    try:
        return f"{price:,.0f} CHF"
    except:
        return '0 CHF'

def create_summary_box(title: str, items: Dict[str, Any]) -> str:
    """Crée une boîte de résumé pour le PDF"""
    html = f'''
    <div class="summary-box">
        <div class="summary-title">{title}</div>
    '''
    
    for label, value in items.items():
        html += f'''
        <div class="summary-item">
            <span class="summary-label">{label}:</span>
            <span class="summary-value">{value}</span>
        </div>
        '''
    
    html += '</div>'
    return html

def create_item_card_html(item: Dict[str, Any]) -> str:
    """Crée le HTML pour une carte d'item optimisée pour PDF"""
    status_class = f"status-{item.get('status', 'available').lower().replace(' ', '-')}"
    
    html = f'''
    <div class="item">
        <div class="item-name">{item.get('name', 'Sans nom')}</div>
        <div class="item-details">
            <strong>Catégorie:</strong> {item.get('category', 'N/A')}<br>
            <strong>Statut:</strong> <span class="{status_class}">{item.get('status', 'N/A')}</span><br>
    '''
    
    if item.get('acquisition_price'):
        html += f'<strong>Prix d\'acquisition:</strong> <span class="price">{format_price_for_pdf(item["acquisition_price"])}</span><br>'
    
    if item.get('asking_price'):
        html += f'<strong>Prix de vente:</strong> <span class="price">{format_price_for_pdf(item["asking_price"])}</span><br>'
    
    if item.get('current_price') and item.get('stock_quantity'):
        total_value = item['current_price'] * item['stock_quantity']
        html += f'<strong>Valeur actuelle:</strong> <span class="value-highlight">{format_price_for_pdf(total_value)}</span><br>'
    
    if item.get('description'):
        html += f'<strong>Description:</strong> {item["description"]}<br>'
    
    html += '</div></div>'
    return html 