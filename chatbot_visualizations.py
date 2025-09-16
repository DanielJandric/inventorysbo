"""
Module de visualisation et d'export pour le chatbot BONVIN
Génère des graphiques, rapports et exports de données
"""

import json
import base64
import io
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import matplotlib
matplotlib.use('Agg')  # Backend non-interactif
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
import numpy as np

# Configuration des styles
sns.set_theme(style="darkgrid")
plt.rcParams['figure.facecolor'] = '#1a1a2e'
plt.rcParams['axes.facecolor'] = '#16213e'
plt.rcParams['text.color'] = '#ffffff'
plt.rcParams['axes.labelcolor'] = '#ffffff'
plt.rcParams['xtick.color'] = '#ffffff'
plt.rcParams['ytick.color'] = '#ffffff'

class ChatbotVisualizer:
    """
    Générateur de visualisations pour le chatbot
    """
    
    def __init__(self):
        self.color_palette = {
            'primary': '#22d3ee',
            'secondary': '#818cf8',
            'accent': '#f472b6',
            'success': '#10b981',
            'warning': '#f59e0b',
            'danger': '#ef4444',
            'dark': '#1a1a2e',
            'light': '#f3f4f6'
        }
    
    def generate_portfolio_chart(self, items: List[Dict]) -> str:
        """
        Génère un graphique en camembert du portefeuille
        Retourne une image en base64
        """
        # Préparer les données
        categories = {}
        for item in items:
            cat = item.get('category', 'Autre')
            value = item.get('current_value', 0)
            categories[cat] = categories.get(cat, 0) + value
        
        if not categories:
            return ""
        
        # Créer le graphique
        fig, ax = plt.subplots(figsize=(10, 8), facecolor=self.color_palette['dark'])
        ax.set_facecolor(self.color_palette['dark'])
        
        # Données pour le camembert
        labels = list(categories.keys())
        values = list(categories.values())
        colors_list = plt.cm.Set3(np.linspace(0, 1, len(labels)))
        
        # Créer le camembert avec explosion
        explode = [0.05] * len(labels)  # Légère séparation
        wedges, texts, autotexts = ax.pie(
            values, 
            labels=labels, 
            autopct='%1.1f%%',
            startangle=90,
            colors=colors_list,
            explode=explode,
            textprops={'color': 'white', 'fontsize': 10}
        )
        
        # Améliorer l'apparence
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_weight('bold')
        
        ax.set_title('Répartition du Portefeuille par Catégorie', 
                     color='white', fontsize=14, fontweight='bold', pad=20)
        
        # Ajouter une légende avec valeurs
        legend_labels = [f'{label}: {value:,.0f} CHF' for label, value in zip(labels, values)]
        ax.legend(legend_labels, loc='best', facecolor=self.color_palette['dark'], 
                 edgecolor='white', labelcolor='white')
        
        # Convertir en base64
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', facecolor=self.color_palette['dark'], 
                   edgecolor='none', bbox_inches='tight')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode()
        plt.close()
        
        return f"data:image/png;base64,{image_base64}"
    
    def generate_performance_chart(self, performance_data: List[Dict]) -> str:
        """
        Génère un graphique de performance temporelle
        """
        if not performance_data:
            return ""
        
        # Créer le graphique
        fig, ax = plt.subplots(figsize=(12, 6), facecolor=self.color_palette['dark'])
        ax.set_facecolor(self.color_palette['dark'])
        
        # Préparer les données
        dates = [item.get('date', '') for item in performance_data]
        values = [item.get('value', 0) for item in performance_data]
        
        # Tracer la ligne
        ax.plot(dates, values, color=self.color_palette['primary'], linewidth=2.5, marker='o')
        
        # Remplir sous la courbe
        ax.fill_between(range(len(dates)), values, alpha=0.3, color=self.color_palette['primary'])
        
        # Formatter
        ax.set_title('Évolution de la Valeur du Portefeuille', 
                    color='white', fontsize=14, fontweight='bold')
        ax.set_xlabel('Date', color='white', fontsize=12)
        ax.set_ylabel('Valeur (CHF)', color='white', fontsize=12)
        ax.grid(True, alpha=0.3, color='white')
        
        # Rotation des labels de date
        plt.xticks(rotation=45, ha='right')
        
        # Ajouter des annotations pour min/max
        if values:
            max_idx = values.index(max(values))
            min_idx = values.index(min(values))
            
            ax.annotate(f'Max: {values[max_idx]:,.0f} CHF',
                       xy=(max_idx, values[max_idx]),
                       xytext=(10, 10), textcoords='offset points',
                       color=self.color_palette['success'],
                       fontweight='bold',
                       arrowprops=dict(arrowstyle='->', color=self.color_palette['success']))
            
            ax.annotate(f'Min: {values[min_idx]:,.0f} CHF',
                       xy=(min_idx, values[min_idx]),
                       xytext=(10, -20), textcoords='offset points',
                       color=self.color_palette['danger'],
                       fontweight='bold',
                       arrowprops=dict(arrowstyle='->', color=self.color_palette['danger']))
        
        # Convertir en base64
        buffer = io.BytesIO()
        plt.tight_layout()
        plt.savefig(buffer, format='png', facecolor=self.color_palette['dark'], 
                   edgecolor='none', bbox_inches='tight')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode()
        plt.close()
        
        return f"data:image/png;base64,{image_base64}"
    
    def generate_heatmap(self, correlation_data: Dict) -> str:
        """
        Génère une heatmap de corrélation
        """
        if not correlation_data:
            return ""
        
        # Créer le graphique
        fig, ax = plt.subplots(figsize=(10, 8), facecolor=self.color_palette['dark'])
        
        # Convertir en DataFrame
        df = pd.DataFrame(correlation_data)
        
        # Créer la heatmap
        sns.heatmap(df, annot=True, fmt='.2f', cmap='coolwarm', center=0,
                   square=True, linewidths=1, cbar_kws={"shrink": 0.8},
                   ax=ax)
        
        ax.set_title('Matrice de Corrélation des Actifs', 
                    color='white', fontsize=14, fontweight='bold')
        
        # Convertir en base64
        buffer = io.BytesIO()
        plt.tight_layout()
        plt.savefig(buffer, format='png', facecolor=self.color_palette['dark'], 
                   edgecolor='none', bbox_inches='tight')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode()
        plt.close()
        
        return f"data:image/png;base64,{image_base64}"
    
    def generate_comparison_chart(self, data1: List, data2: List, labels: List[str]) -> str:
        """
        Génère un graphique de comparaison (barres groupées)
        """
        fig, ax = plt.subplots(figsize=(12, 6), facecolor=self.color_palette['dark'])
        ax.set_facecolor(self.color_palette['dark'])
        
        x = np.arange(len(labels))
        width = 0.35
        
        bars1 = ax.bar(x - width/2, data1, width, label='Actuel', 
                      color=self.color_palette['primary'])
        bars2 = ax.bar(x + width/2, data2, width, label='Objectif', 
                      color=self.color_palette['accent'])
        
        ax.set_xlabel('Catégories', color='white', fontsize=12)
        ax.set_ylabel('Valeur (CHF)', color='white', fontsize=12)
        ax.set_title('Comparaison Actuel vs Objectif', color='white', 
                    fontsize=14, fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels(labels, rotation=45, ha='right')
        ax.legend(facecolor=self.color_palette['dark'], edgecolor='white', 
                 labelcolor='white')
        
        # Ajouter les valeurs sur les barres
        for bars in [bars1, bars2]:
            for bar in bars:
                height = bar.get_height()
                ax.annotate(f'{height:,.0f}',
                           xy=(bar.get_x() + bar.get_width() / 2, height),
                           xytext=(0, 3),
                           textcoords="offset points",
                           ha='center', va='bottom',
                           color='white', fontsize=9)
        
        ax.grid(True, alpha=0.3, axis='y', color='white')
        
        # Convertir en base64
        buffer = io.BytesIO()
        plt.tight_layout()
        plt.savefig(buffer, format='png', facecolor=self.color_palette['dark'], 
                   edgecolor='none', bbox_inches='tight')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode()
        plt.close()
        
        return f"data:image/png;base64,{image_base64}"


class ReportGenerator:
    """
    Générateur de rapports PDF professionnels
    """
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Configure les styles personnalisés"""
        # Style pour le titre principal
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Title'],
            fontSize=24,
            textColor=colors.HexColor('#1a1a2e'),
            spaceAfter=30,
            alignment=TA_CENTER
        ))
        
        # Style pour les sous-titres
        self.styles.add(ParagraphStyle(
            name='CustomHeading',
            parent=self.styles['Heading1'],
            fontSize=16,
            textColor=colors.HexColor('#22d3ee'),
            spaceAfter=12,
            spaceBefore=12
        ))
        
        # Style pour le texte normal
        self.styles.add(ParagraphStyle(
            name='CustomBody',
            parent=self.styles['BodyText'],
            fontSize=11,
            textColor=colors.HexColor('#333333'),
            spaceAfter=6
        ))
        
        # Style pour les chiffres importants
        self.styles.add(ParagraphStyle(
            name='CustomNumber',
            parent=self.styles['BodyText'],
            fontSize=14,
            textColor=colors.HexColor('#10b981'),
            alignment=TA_RIGHT,
            fontName='Helvetica-Bold'
        ))
    
    def generate_portfolio_report(self, data: Dict, filename: str = None) -> bytes:
        """
        Génère un rapport PDF complet du portefeuille
        """
        # Créer le buffer
        buffer = io.BytesIO()
        
        # Créer le document
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18,
        )
        
        # Container pour les éléments
        elements = []
        
        # Page de titre
        elements.append(Paragraph("RAPPORT DE PATRIMOINE", self.styles['CustomTitle']))
        elements.append(Paragraph(f"Collection BONVIN", self.styles['Heading2']))
        elements.append(Paragraph(f"Généré le {datetime.now().strftime('%d/%m/%Y')}", 
                                 self.styles['Normal']))
        elements.append(Spacer(1, 12))
        
        # Ligne de séparation
        elements.append(Table([['']], colWidths=[450], 
                            style=TableStyle([('LINEBELOW', (0, 0), (-1, -1), 1, 
                                             colors.HexColor('#22d3ee'))])))
        elements.append(Spacer(1, 12))
        
        # Résumé exécutif
        elements.append(Paragraph("RÉSUMÉ EXÉCUTIF", self.styles['CustomHeading']))
        
        summary_data = [
            ['Valeur Totale:', f"{data.get('total_value', 0):,.0f} CHF"],
            ['Nombre d\'Actifs:', f"{data.get('total_items', 0)}"],
            ['Performance YTD:', f"{data.get('ytd_performance', 0):.1f}%"],
            ['Plus-value Latente:', f"{data.get('unrealized_gains', 0):,.0f} CHF"],
        ]
        
        summary_table = Table(summary_data, colWidths=[200, 250])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f3f4f6')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#333333')),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        elements.append(summary_table)
        elements.append(Spacer(1, 20))
        
        # Répartition par catégorie
        elements.append(Paragraph("RÉPARTITION PAR CATÉGORIE", self.styles['CustomHeading']))
        
        categories = data.get('categories', {})
        if categories:
            cat_data = [['Catégorie', 'Valeur (CHF)', 'Pourcentage']]
            total = sum(categories.values())
            for cat, value in sorted(categories.items(), key=lambda x: x[1], reverse=True):
                percentage = (value / total * 100) if total > 0 else 0
                cat_data.append([cat, f"{value:,.0f}", f"{percentage:.1f}%"])
            
            cat_table = Table(cat_data, colWidths=[150, 150, 150])
            cat_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#22d3ee')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ]))
            elements.append(cat_table)
        
        elements.append(PageBreak())
        
        # Top 10 des actifs
        elements.append(Paragraph("TOP 10 DES ACTIFS", self.styles['CustomHeading']))
        
        top_items = data.get('top_items', [])[:10]
        if top_items:
            top_data = [['Rang', 'Nom', 'Catégorie', 'Valeur (CHF)']]
            for i, item in enumerate(top_items, 1):
                top_data.append([
                    str(i),
                    item.get('name', 'N/A')[:30],
                    item.get('category', 'N/A'),
                    f"{item.get('current_value', 0):,.0f}"
                ])
            
            top_table = Table(top_data, colWidths=[40, 200, 100, 110])
            top_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#818cf8')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('ALIGN', (1, 1), (1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ]))
            elements.append(top_table)
        
        elements.append(Spacer(1, 20))
        
        # Recommandations
        elements.append(Paragraph("RECOMMANDATIONS STRATÉGIQUES", self.styles['CustomHeading']))
        
        recommendations = data.get('recommendations', [
            "Diversifier le portefeuille pour réduire le risque de concentration",
            "Considérer la vente des actifs avec les plus-values les plus importantes",
            "Réévaluer les actifs n'ayant pas été mis à jour depuis plus de 6 mois",
            "Explorer les opportunités d'investissement dans les secteurs sous-représentés"
        ])
        
        for rec in recommendations[:4]:
            elements.append(Paragraph(f"• {rec}", self.styles['CustomBody']))
        
        elements.append(Spacer(1, 20))
        
        # Note de bas de page
        elements.append(Paragraph(
            "Ce rapport a été généré automatiquement par l'Assistant IA BONVIN. "
            "Les données et analyses sont basées sur les informations disponibles "
            f"au {datetime.now().strftime('%d/%m/%Y à %H:%M')}.",
            self.styles['Normal']
        ))
        
        # Construire le PDF
        doc.build(elements)
        
        # Retourner le contenu
        buffer.seek(0)
        return buffer.getvalue()
    
    def generate_excel_export(self, items: List[Dict]) -> bytes:
        """
        Génère un export Excel avec plusieurs onglets
        """
        buffer = io.BytesIO()
        
        # Créer un writer Excel
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            # Onglet principal - Inventaire
            df_inventory = pd.DataFrame(items)
            df_inventory.to_excel(writer, sheet_name='Inventaire', index=False)
            
            # Onglet statistiques par catégorie
            if items:
                categories = {}
                for item in items:
                    cat = item.get('category', 'Autre')
                    if cat not in categories:
                        categories[cat] = {
                            'count': 0,
                            'total_value': 0,
                            'avg_value': 0
                        }
                    categories[cat]['count'] += 1
                    categories[cat]['total_value'] += item.get('current_value', 0)
                
                for cat in categories:
                    if categories[cat]['count'] > 0:
                        categories[cat]['avg_value'] = categories[cat]['total_value'] / categories[cat]['count']
                
                df_stats = pd.DataFrame.from_dict(categories, orient='index')
                df_stats.to_excel(writer, sheet_name='Statistiques')
            
            # Onglet performance (si disponible)
            perf_data = []
            for item in items:
                if item.get('acquisition_price') and item.get('current_value'):
                    perf = {
                        'Nom': item.get('name', 'N/A'),
                        'Catégorie': item.get('category', 'N/A'),
                        'Prix Acquisition': item.get('acquisition_price', 0),
                        'Valeur Actuelle': item.get('current_value', 0),
                        'Plus-value': item.get('current_value', 0) - item.get('acquisition_price', 0),
                        'ROI %': ((item.get('current_value', 0) / item.get('acquisition_price', 1) - 1) * 100)
                    }
                    perf_data.append(perf)
            
            if perf_data:
                df_perf = pd.DataFrame(perf_data)
                df_perf.to_excel(writer, sheet_name='Performance', index=False)
            
            # Formater les cellules
            workbook = writer.book
            
            # Format pour les montants
            money_format = workbook.add_format({
                'num_format': '#,##0 CHF',
                'align': 'right'
            })
            
            # Format pour les pourcentages
            percent_format = workbook.add_format({
                'num_format': '0.0%',
                'align': 'right'
            })
            
            # Format pour les en-têtes
            header_format = workbook.add_format({
                'bold': True,
                'bg_color': '#22d3ee',
                'font_color': 'white',
                'align': 'center'
            })
        
        buffer.seek(0)
        return buffer.getvalue()


# Instance globale
visualizer = ChatbotVisualizer()
report_generator = ReportGenerator()
