"""
Module de visualisations pour les marchés financiers
Génère des graphiques techniques, indicateurs et rapports de marché
"""

import io
import base64
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import Rectangle
import seaborn as sns
import pandas as pd
import numpy as np

# Configuration du style pour les marchés
plt.style.use('dark_background')
sns.set_palette("husl")


class MarketsVisualizer:
    """
    Générateur de visualisations pour les analyses de marché
    """
    
    def __init__(self):
        self.colors = {
            'bullish': '#00ff41',  # Vert vif
            'bearish': '#ff0051',  # Rouge vif
            'neutral': '#ffaa00',  # Orange
            'background': '#0a0e27',
            'grid': '#1a1e3a',
            'text': '#ffffff'
        }
        
        # Style pour les graphiques financiers
        self.chart_style = {
            'figure.facecolor': self.colors['background'],
            'axes.facecolor': self.colors['background'],
            'axes.edgecolor': self.colors['grid'],
            'axes.labelcolor': self.colors['text'],
            'text.color': self.colors['text'],
            'xtick.color': self.colors['text'],
            'ytick.color': self.colors['text'],
            'grid.color': self.colors['grid'],
            'grid.alpha': 0.3
        }
    
    def generate_price_chart(self, data: Dict) -> str:
        """
        Génère un graphique de prix avec volume
        """
        plt.rcParams.update(self.chart_style)
        
        # Préparer les données
        dates = pd.date_range(end=datetime.now(), periods=100, freq='D')
        prices = np.random.randn(100).cumsum() + 100
        volumes = np.random.randint(1000000, 5000000, 100)
        
        # Créer la figure avec 2 subplots
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), 
                                       gridspec_kw={'height_ratios': [3, 1]})
        
        # Graphique de prix principal
        ax1.plot(dates, prices, color=self.colors['bullish'], linewidth=2)
        ax1.fill_between(dates, prices, alpha=0.3, color=self.colors['bullish'])
        
        # Moyennes mobiles
        sma20 = pd.Series(prices).rolling(20).mean()
        sma50 = pd.Series(prices).rolling(50).mean()
        ax1.plot(dates, sma20, color='#00aaff', linewidth=1, alpha=0.7, label='SMA 20')
        ax1.plot(dates, sma50, color='#ff00ff', linewidth=1, alpha=0.7, label='SMA 50')
        
        # Bollinger Bands
        std = pd.Series(prices).rolling(20).std()
        upper_band = sma20 + (std * 2)
        lower_band = sma20 - (std * 2)
        ax1.fill_between(dates, upper_band, lower_band, alpha=0.1, color='white')
        
        ax1.set_title('📈 Graphique de Prix avec Indicateurs Techniques', 
                     fontsize=14, fontweight='bold', pad=20)
        ax1.set_ylabel('Prix', fontsize=12)
        ax1.legend(loc='upper left')
        ax1.grid(True, alpha=0.3)
        
        # Graphique de volume
        colors = [self.colors['bullish'] if prices[i] > prices[i-1] else self.colors['bearish'] 
                 for i in range(1, len(prices))]
        colors = [self.colors['neutral']] + colors
        
        ax2.bar(dates, volumes, color=colors, alpha=0.7)
        ax2.set_ylabel('Volume', fontsize=12)
        ax2.set_xlabel('Date', fontsize=12)
        ax2.grid(True, alpha=0.3)
        
        # Formater les dates
        ax1.xaxis.set_major_formatter(mdates.DateFormatter('%d/%m'))
        ax2.xaxis.set_major_formatter(mdates.DateFormatter('%d/%m'))
        plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45)
        plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45)
        
        # Ajuster le layout
        plt.tight_layout()
        
        # Convertir en base64
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', facecolor=self.colors['background'], 
                   edgecolor='none', bbox_inches='tight', dpi=100)
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode()
        plt.close()
        
        return f"data:image/png;base64,{image_base64}"
    
    def generate_candlestick_chart(self, ohlc_data: List[Dict]) -> str:
        """
        Génère un graphique en chandeliers japonais
        """
        plt.rcParams.update(self.chart_style)
        
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # Données simulées si non fournies
        if not ohlc_data:
            dates = pd.date_range(end=datetime.now(), periods=50, freq='D')
            ohlc_data = []
            price = 100
            for date in dates:
                open_price = price
                close_price = price + np.random.randn() * 2
                high = max(open_price, close_price) + abs(np.random.randn())
                low = min(open_price, close_price) - abs(np.random.randn())
                ohlc_data.append({
                    'date': date,
                    'open': open_price,
                    'high': high,
                    'low': low,
                    'close': close_price
                })
                price = close_price
        
        # Dessiner les chandeliers
        for i, candle in enumerate(ohlc_data):
            color = self.colors['bullish'] if candle['close'] > candle['open'] else self.colors['bearish']
            
            # Ligne haute-basse
            ax.plot([i, i], [candle['low'], candle['high']], 
                   color=color, linewidth=1, alpha=0.8)
            
            # Corps du chandelier
            height = abs(candle['close'] - candle['open'])
            bottom = min(candle['close'], candle['open'])
            rect = Rectangle((i - 0.3, bottom), 0.6, height, 
                           facecolor=color, edgecolor=color, alpha=0.8)
            ax.add_patch(rect)
        
        # Ajouter des niveaux de support/résistance
        resistance = max([c['high'] for c in ohlc_data])
        support = min([c['low'] for c in ohlc_data])
        
        ax.axhline(y=resistance, color=self.colors['bearish'], 
                  linestyle='--', alpha=0.5, label=f'Résistance: {resistance:.2f}')
        ax.axhline(y=support, color=self.colors['bullish'], 
                  linestyle='--', alpha=0.5, label=f'Support: {support:.2f}')
        
        ax.set_title('🕯️ Graphique en Chandeliers Japonais', 
                    fontsize=14, fontweight='bold', pad=20)
        ax.set_xlabel('Période', fontsize=12)
        ax.set_ylabel('Prix', fontsize=12)
        ax.legend(loc='upper left')
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        # Convertir en base64
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', facecolor=self.colors['background'], 
                   edgecolor='none', bbox_inches='tight', dpi=100)
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode()
        plt.close()
        
        return f"data:image/png;base64,{image_base64}"
    
    def generate_technical_indicators_chart(self, data: Dict) -> str:
        """
        Génère un graphique multi-indicateurs techniques
        """
        plt.rcParams.update(self.chart_style)
        
        fig, axes = plt.subplots(4, 1, figsize=(12, 10), 
                                gridspec_kw={'height_ratios': [3, 1, 1, 1]})
        
        # Données
        periods = 100
        dates = pd.date_range(end=datetime.now(), periods=periods, freq='D')
        prices = np.random.randn(periods).cumsum() + 100
        
        # Prix principal
        axes[0].plot(dates, prices, color=self.colors['bullish'], linewidth=2)
        axes[0].set_title('📊 Analyse Technique Complète', 
                         fontsize=14, fontweight='bold', pad=20)
        axes[0].set_ylabel('Prix', fontsize=12)
        axes[0].grid(True, alpha=0.3)
        
        # RSI
        rsi = 50 + np.random.randn(periods).cumsum()
        rsi = np.clip(rsi, 0, 100)
        axes[1].plot(dates, rsi, color='#00aaff', linewidth=1.5)
        axes[1].axhline(y=70, color=self.colors['bearish'], linestyle='--', alpha=0.5)
        axes[1].axhline(y=30, color=self.colors['bullish'], linestyle='--', alpha=0.5)
        axes[1].fill_between(dates, 30, 70, alpha=0.1, color='white')
        axes[1].set_ylabel('RSI', fontsize=12)
        axes[1].set_ylim(0, 100)
        axes[1].grid(True, alpha=0.3)
        
        # MACD
        macd = np.random.randn(periods).cumsum()
        signal = pd.Series(macd).rolling(9).mean()
        histogram = macd - signal
        
        axes[2].plot(dates, macd, color='#00ff41', linewidth=1.5, label='MACD')
        axes[2].plot(dates, signal, color='#ff0051', linewidth=1.5, label='Signal')
        axes[2].bar(dates, histogram, color='#ffaa00', alpha=0.5, label='Histogram')
        axes[2].axhline(y=0, color='white', linestyle='-', alpha=0.3)
        axes[2].set_ylabel('MACD', fontsize=12)
        axes[2].legend(loc='upper left', fontsize=8)
        axes[2].grid(True, alpha=0.3)
        
        # Stochastique
        stoch_k = 50 + np.random.randn(periods).cumsum()
        stoch_k = np.clip(stoch_k, 0, 100)
        stoch_d = pd.Series(stoch_k).rolling(3).mean()
        
        axes[3].plot(dates, stoch_k, color='#ff00ff', linewidth=1.5, label='%K')
        axes[3].plot(dates, stoch_d, color='#00ffff', linewidth=1.5, label='%D')
        axes[3].axhline(y=80, color=self.colors['bearish'], linestyle='--', alpha=0.5)
        axes[3].axhline(y=20, color=self.colors['bullish'], linestyle='--', alpha=0.5)
        axes[3].set_ylabel('Stoch', fontsize=12)
        axes[3].set_xlabel('Date', fontsize=12)
        axes[3].set_ylim(0, 100)
        axes[3].legend(loc='upper left', fontsize=8)
        axes[3].grid(True, alpha=0.3)
        
        # Formater les dates
        for ax in axes:
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%d/%m'))
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
        
        plt.tight_layout()
        
        # Convertir en base64
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', facecolor=self.colors['background'], 
                   edgecolor='none', bbox_inches='tight', dpi=100)
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode()
        plt.close()
        
        return f"data:image/png;base64,{image_base64}"
    
    def generate_market_heatmap(self, correlations: Dict) -> str:
        """
        Génère une heatmap des corrélations de marché
        """
        plt.rcParams.update(self.chart_style)
        
        # Données de corrélation simulées
        assets = ['S&P 500', 'NASDAQ', 'EUR/USD', 'Gold', 'Oil', 'Bitcoin', 
                 'Bonds', 'VIX', 'Dollar Index', 'Silver']
        
        if not correlations:
            # Générer des corrélations simulées
            n = len(assets)
            corr_matrix = np.random.randn(n, n)
            corr_matrix = (corr_matrix + corr_matrix.T) / 2
            np.fill_diagonal(corr_matrix, 1)
            corr_matrix = np.clip(corr_matrix, -1, 1)
        else:
            corr_matrix = correlations
        
        fig, ax = plt.subplots(figsize=(10, 8))
        
        # Créer la heatmap
        im = ax.imshow(corr_matrix, cmap='RdBu_r', aspect='auto', vmin=-1, vmax=1)
        
        # Ajouter les labels
        ax.set_xticks(np.arange(len(assets)))
        ax.set_yticks(np.arange(len(assets)))
        ax.set_xticklabels(assets, rotation=45, ha='right')
        ax.set_yticklabels(assets)
        
        # Ajouter les valeurs dans les cellules
        for i in range(len(assets)):
            for j in range(len(assets)):
                value = corr_matrix[i, j] if isinstance(corr_matrix, np.ndarray) else corr_matrix[i][j]
                color = 'white' if abs(value) > 0.5 else 'black'
                text = ax.text(j, i, f'{value:.2f}', ha='center', va='center', 
                             color=color, fontsize=9)
        
        # Titre et colorbar
        ax.set_title('🌡️ Matrice de Corrélation des Marchés', 
                    fontsize=14, fontweight='bold', pad=20)
        
        cbar = plt.colorbar(im, ax=ax)
        cbar.set_label('Corrélation', rotation=270, labelpad=20)
        
        plt.tight_layout()
        
        # Convertir en base64
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', facecolor=self.colors['background'], 
                   edgecolor='none', bbox_inches='tight', dpi=100)
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode()
        plt.close()
        
        return f"data:image/png;base64,{image_base64}"
    
    def generate_risk_gauge(self, risk_level: float) -> str:
        """
        Génère une jauge de risque visuelle
        """
        plt.rcParams.update(self.chart_style)
        
        fig, ax = plt.subplots(figsize=(8, 4), subplot_kw=dict(projection='polar'))
        
        # Configuration de la jauge
        theta = np.linspace(np.pi, 0, 100)
        r = np.ones_like(theta)
        
        # Zones de risque
        zones = [
            (0, 20, self.colors['bullish'], 'Très Bas'),
            (20, 40, '#00ff88', 'Bas'),
            (40, 60, self.colors['neutral'], 'Modéré'),
            (60, 80, '#ff8800', 'Élevé'),
            (80, 100, self.colors['bearish'], 'Très Élevé')
        ]
        
        # Dessiner les zones
        for start, end, color, label in zones:
            theta_zone = np.linspace(np.pi - np.pi * start/100, 
                                    np.pi - np.pi * end/100, 50)
            ax.fill_between(theta_zone, 0.8, 1.0, color=color, alpha=0.6)
        
        # Aiguille
        risk_angle = np.pi - (np.pi * risk_level / 100)
        ax.plot([risk_angle, risk_angle], [0, 0.9], 'white', linewidth=3)
        ax.scatter([risk_angle], [0.9], color='white', s=100, zorder=5)
        
        # Configuration des axes
        ax.set_theta_direction(-1)
        ax.set_theta_offset(np.pi/2)
        ax.set_ylim(0, 1)
        ax.set_yticklabels([])
        ax.set_xticks([])
        ax.grid(False)
        ax.set_facecolor(self.colors['background'])
        
        # Titre avec niveau de risque
        risk_text = next((z[3] for z in zones if z[0] <= risk_level <= z[1]), 'Modéré')
        ax.text(0, -0.3, f'Niveau de Risque: {risk_level:.0f}% - {risk_text}', 
               transform=ax.transAxes, ha='center', fontsize=14, 
               fontweight='bold', color='white')
        
        # Convertir en base64
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', facecolor=self.colors['background'], 
                   edgecolor='none', bbox_inches='tight', dpi=100)
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode()
        plt.close()
        
        return f"data:image/png;base64,{image_base64}"
    
    def generate_sentiment_meter(self, sentiment_data: Dict) -> str:
        """
        Génère un indicateur de sentiment de marché
        """
        plt.rcParams.update(self.chart_style)
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
        
        # Gauge de sentiment Fear & Greed
        sentiment_value = sentiment_data.get('value', 50)
        
        # Créer un demi-cercle pour la gauge
        theta = np.linspace(np.pi, 0, 100)
        colors_gradient = []
        for i in range(100):
            if i < 20:
                colors_gradient.append(self.colors['bearish'])
            elif i < 40:
                colors_gradient.append('#ff8800')
            elif i < 60:
                colors_gradient.append(self.colors['neutral'])
            elif i < 80:
                colors_gradient.append('#88ff00')
            else:
                colors_gradient.append(self.colors['bullish'])
        
        # Dessiner l'arc coloré
        for i in range(len(theta)-1):
            ax1.fill_between([theta[i], theta[i+1]], 0, 1, 
                           color=colors_gradient[i], alpha=0.8)
        
        # Aiguille
        angle = np.pi - (np.pi * sentiment_value / 100)
        ax1.arrow(0, 0, 0.8*np.cos(angle), 0.8*np.sin(angle), 
                 head_width=0.05, head_length=0.05, fc='white', ec='white')
        
        ax1.set_xlim(-1.1, 1.1)
        ax1.set_ylim(-0.1, 1.1)
        ax1.set_aspect('equal')
        ax1.axis('off')
        
        # Labels
        ax1.text(-0.9, -0.05, 'Fear', fontsize=10, color=self.colors['bearish'])
        ax1.text(0.7, -0.05, 'Greed', fontsize=10, color=self.colors['bullish'])
        ax1.text(0, -0.05, f'{sentiment_value}', fontsize=20, ha='center', 
                fontweight='bold', color='white')
        
        sentiment_text = 'Extreme Fear' if sentiment_value < 20 else \
                        'Fear' if sentiment_value < 40 else \
                        'Neutral' if sentiment_value < 60 else \
                        'Greed' if sentiment_value < 80 else 'Extreme Greed'
        
        ax1.set_title(f'Fear & Greed Index: {sentiment_text}', 
                     fontsize=12, fontweight='bold', color='white')
        
        # Barres de composants du sentiment
        components = sentiment_data.get('components', {
            'Momentum': 65,
            'Volume': 45,
            'Volatility': 30,
            'Options': 55,
            'Social': 70
        })
        
        bars = ax2.barh(list(components.keys()), list(components.values()), 
                       color=[self.colors['bullish'] if v > 50 else self.colors['bearish'] 
                             for v in components.values()])
        
        ax2.set_xlim(0, 100)
        ax2.set_xlabel('Score', fontsize=10)
        ax2.set_title('Composants du Sentiment', fontsize=12, fontweight='bold')
        ax2.grid(True, alpha=0.3, axis='x')
        
        # Ajouter les valeurs sur les barres
        for bar, value in zip(bars, components.values()):
            ax2.text(value + 2, bar.get_y() + bar.get_height()/2, 
                    f'{value}', va='center', fontsize=9)
        
        plt.tight_layout()
        
        # Convertir en base64
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', facecolor=self.colors['background'], 
                   edgecolor='none', bbox_inches='tight', dpi=100)
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode()
        plt.close()
        
        return f"data:image/png;base64,{image_base64}"
    
    def generate_market_overview_dashboard(self, market_data: Dict) -> str:
        """
        Génère un dashboard complet de vue d'ensemble du marché
        """
        plt.rcParams.update(self.chart_style)
        
        fig = plt.figure(figsize=(15, 10))
        gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)
        
        # Indices majeurs (top row)
        ax1 = fig.add_subplot(gs[0, :])
        indices = market_data.get('indices', {
            'S&P 500': {'value': 4500, 'change': 1.2},
            'NASDAQ': {'value': 14000, 'change': -0.5},
            'DOW': {'value': 35000, 'change': 0.8},
            'EUR/USD': {'value': 1.08, 'change': -0.3},
            'Gold': {'value': 2000, 'change': 1.5}
        })
        
        x_pos = np.arange(len(indices))
        changes = [v['change'] for v in indices.values()]
        colors_bars = [self.colors['bullish'] if c > 0 else self.colors['bearish'] 
                      for c in changes]
        
        bars = ax1.bar(x_pos, changes, color=colors_bars, alpha=0.8)
        ax1.set_xticks(x_pos)
        ax1.set_xticklabels(indices.keys())
        ax1.set_ylabel('Variation %')
        ax1.set_title('📊 Indices Majeurs - Performance du Jour', 
                     fontsize=14, fontweight='bold')
        ax1.axhline(y=0, color='white', linestyle='-', alpha=0.3)
        ax1.grid(True, alpha=0.3, axis='y')
        
        # Ajouter les valeurs
        for bar, (name, data) in zip(bars, indices.items()):
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height,
                    f'{data["change"]:+.1f}%\n{data["value"]:,.0f}',
                    ha='center', va='bottom' if height > 0 else 'top',
                    fontsize=9, color='white')
        
        # Secteurs (middle left)
        ax2 = fig.add_subplot(gs[1, 0])
        sectors = market_data.get('sectors', {
            'Tech': 2.1, 'Finance': -0.8, 'Energy': 1.5,
            'Healthcare': 0.3, 'Consumer': -0.2
        })
        
        y_pos = np.arange(len(sectors))
        values = list(sectors.values())
        colors_sectors = [self.colors['bullish'] if v > 0 else self.colors['bearish'] 
                         for v in values]
        
        ax2.barh(y_pos, values, color=colors_sectors, alpha=0.8)
        ax2.set_yticks(y_pos)
        ax2.set_yticklabels(sectors.keys(), fontsize=9)
        ax2.set_xlabel('Performance %', fontsize=9)
        ax2.set_title('🏢 Secteurs', fontsize=12, fontweight='bold')
        ax2.grid(True, alpha=0.3, axis='x')
        
        # Top movers (middle center)
        ax3 = fig.add_subplot(gs[1, 1])
        movers = market_data.get('movers', {
            'TSLA': 5.2, 'AAPL': 3.1, 'NVDA': -2.8,
            'MSFT': 1.5, 'AMZN': -1.2
        })
        
        sorted_movers = sorted(movers.items(), key=lambda x: x[1], reverse=True)
        names = [m[0] for m in sorted_movers]
        values = [m[1] for m in sorted_movers]
        colors_movers = [self.colors['bullish'] if v > 0 else self.colors['bearish'] 
                        for v in values]
        
        ax3.barh(range(len(names)), values, color=colors_movers, alpha=0.8)
        ax3.set_yticks(range(len(names)))
        ax3.set_yticklabels(names, fontsize=9)
        ax3.set_xlabel('Variation %', fontsize=9)
        ax3.set_title('🚀 Top Movers', fontsize=12, fontweight='bold')
        ax3.grid(True, alpha=0.3, axis='x')
        
        # Volatilité (middle right)
        ax4 = fig.add_subplot(gs[1, 2])
        vix_history = market_data.get('vix_history', np.random.randn(30).cumsum() + 20)
        ax4.plot(vix_history, color=self.colors['neutral'], linewidth=2)
        ax4.fill_between(range(len(vix_history)), vix_history, alpha=0.3, 
                        color=self.colors['neutral'])
        ax4.axhline(y=20, color=self.colors['bullish'], linestyle='--', 
                   alpha=0.5, label='Normal')
        ax4.axhline(y=30, color=self.colors['bearish'], linestyle='--', 
                   alpha=0.5, label='Élevé')
        ax4.set_title(f'😰 VIX: {vix_history[-1]:.1f}', fontsize=12, fontweight='bold')
        ax4.set_ylabel('VIX', fontsize=9)
        ax4.legend(loc='upper left', fontsize=8)
        ax4.grid(True, alpha=0.3)
        
        # Calendrier économique (bottom)
        ax5 = fig.add_subplot(gs[2, :])
        events = market_data.get('events', [
            'Fed Meeting - Mercredi 14:00',
            'CPI Data - Jeudi 08:30',
            'Earnings: AAPL, MSFT - Vendredi',
            'ECB Decision - Jeudi 13:45'
        ])
        
        ax5.axis('off')
        ax5.set_title('📅 Événements à Venir', fontsize=12, fontweight='bold', 
                     loc='left', pad=20)
        
        for i, event in enumerate(events[:4]):
            ax5.text(0.25 * (i % 4), 0.5 - 0.3 * (i // 4), 
                    f'• {event}', fontsize=10, color='white',
                    transform=ax5.transAxes)
        
        # Titre général
        fig.suptitle('🌍 Dashboard des Marchés Financiers', 
                    fontsize=16, fontweight='bold', y=0.98)
        
        plt.tight_layout()
        
        # Convertir en base64
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', facecolor=self.colors['background'], 
                   edgecolor='none', bbox_inches='tight', dpi=100)
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode()
        plt.close()
        
        return f"data:image/png;base64,{image_base64}"


# Instance globale
markets_visualizer = MarketsVisualizer()
