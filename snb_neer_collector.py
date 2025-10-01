"""
Collecteur NEER (Nominal Effective Exchange Rate) depuis data.snb.ch

API officielle BNS gratuite et publique
Source: https://data.snb.ch/en/topics/ziredev#!/cube/devkum
"""

import requests
import pandas as pd
import json
from datetime import datetime, date, timedelta
from typing import Dict, Any, Optional
import io


def collect_neer_from_snb_api() -> Dict[str, Any]:
    """
    Collecte le NEER depuis l'API data.snb.ch
    
    Calcule la variation sur 3 mois (nécessaire pour le modèle BNS)
    
    Returns:
        dict avec neer_value (index actuel) et neer_change_3m_pct (variation 3M en %)
    """
    
    # URL de l'API SNB pour le NEER
    # Cube: devkum (Taux de change effectifs nominaux et réels)
    # D0 = NEER nominal (base 1999 = 100)
    api_url = "https://data.snb.ch/api/cube/devkum/data/csv/en"
    
    try:
        print("📊 Collecte NEER depuis data.snb.ch...")
        
        # Télécharger le CSV
        response = requests.get(api_url, timeout=30)
        response.raise_for_status()
        
        # Parser le CSV (essayer différents séparateurs)
        try:
            df = pd.read_csv(io.StringIO(response.text), sep=';', on_bad_lines='skip')
        except Exception:
            try:
                df = pd.read_csv(io.StringIO(response.text), sep=',', on_bad_lines='skip')
            except Exception:
                df = pd.read_csv(io.StringIO(response.text), sep='\t', on_bad_lines='skip')
        
        # Filtrer pour NEER nominal (D0) et valeurs mensuelles
        # Les colonnes SNB sont typiquement: Date, D0 (NEER nominal), D1 (NEER réel)
        
        # Nettoyer les noms de colonnes
        df.columns = df.columns.str.strip()
        
        # Debug: afficher les colonnes disponibles
        print(f"   Colonnes CSV SNB: {list(df.columns)[:10]}")
        
        # Chercher la colonne de date (plusieurs formats possibles)
        date_col = None
        for col in ['Date', 'date', 'TIME_PERIOD', 'Period', 'Periode', df.columns[0]]:
            if col in df.columns:
                date_col = col
                break
        
        if not date_col:
            raise ValueError(f"Colonne Date non trouvée. Colonnes: {list(df.columns)}")
        
        # Convertir la date
        df['Date'] = pd.to_datetime(df[date_col], errors='coerce')
        
        # Trouver la colonne de valeur NEER
        value_col = None
        for col in ['Value', 'D0', 'value', 'Wert']:
            if col in df.columns:
                value_col = col
                break
        
        if not value_col:
            raise ValueError("Colonne Value non trouvée dans le CSV SNB")
        
        # Convertir en numérique
        df[value_col] = pd.to_numeric(df[value_col], errors='coerce')
        
        # Trier par date descendante
        df = df.sort_values('Date', ascending=False).dropna(subset=['Date', value_col])
        
        if len(df) < 4:
            raise ValueError("Pas assez de données NEER (min 4 mois requis)")
        
        # Récupérer valeur actuelle (dernier mois)
        current_value = df.iloc[0][value_col]
        current_date = df.iloc[0]['Date']
        
        # Récupérer valeur il y a 3 mois
        # Chercher la date la plus proche de -3 mois
        target_date = current_date - pd.Timedelta(days=90)
        
        # Trouver la ligne la plus proche
        df['date_diff'] = abs(df['Date'] - target_date)
        closest_idx = df['date_diff'].idxmin()
        value_3m_ago = df.loc[closest_idx, value_col]
        
        # Calculer variation sur 3 mois (%)
        neer_change_3m_pct = ((current_value - value_3m_ago) / value_3m_ago) * 100
        
        print(f"✅ NEER collecté:")
        print(f"   Actuel: {current_value:.2f} (au {current_date.strftime('%Y-%m-%d')})")
        print(f"   Il y a 3M: {value_3m_ago:.2f}")
        print(f"   Variation 3M: {neer_change_3m_pct:+.2f}%")
        
        return {
            "neer_value": float(current_value),
            "neer_change_3m_pct": float(neer_change_3m_pct),
            "as_of": current_date.strftime('%Y-%m-%d'),
            "source_url": "https://data.snb.ch",
            "idempotency_key": f"neer-{current_date.strftime('%Y-%m')}"
        }
    
    except Exception as e:
        print(f"❌ Erreur collecte NEER: {e}")
        import traceback
        traceback.print_exc()
        
        # Fallback: valeur par défaut (neutre)
        print("⚠️  Utilisation valeur NEER par défaut (0.0%)")
        return {
            "neer_value": 100.0,
            "neer_change_3m_pct": 0.0,
            "as_of": date.today().isoformat(),
            "source_url": "Fallback (default)",
            "idempotency_key": f"neer-{date.today().strftime('%Y-%m')}-fallback"
        }


if __name__ == "__main__":
    # Test
    result = collect_neer_from_snb_api()
    print(f"\n🧪 Test NEER:")
    print(json.dumps(result, indent=2))

