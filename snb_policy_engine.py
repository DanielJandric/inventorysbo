"""
SNB Policy Engine - Modèle de prévision des taux d'intérêt BNS
Adapté pour l'architecture Flask existante

Architecture:
- Nowcast inflation (3M, 6M, 12M)
- Règle de Taylor augmentée (avec NEER)
- Fusion Kalman (règle + marché)
- Probabilités décision (cut/hold/hike)
"""

import numpy as np
import math
from typing import Dict, List, Optional, Tuple, Any
from datetime import date, datetime
from dataclasses import dataclass, asdict

# === CONSTANTES ===
TARGET_INFLATION = 1.0  # %
LOWER_BOUND = 0.0       # Effective lower bound
DEFAULT_KAPPA = 0.25    # Vitesse convergence Kalman
DEFAULT_Q = 0.003       # Variance processus
DEFAULT_R = 0.006       # Variance observation

# === MODÈLES DE DONNÉES ===
@dataclass
class OISPoint:
    """Point de la courbe OIS"""
    tenor_months: int
    rate_pct: float


@dataclass
class ModelInputs:
    """Inputs pour le modèle"""
    policy_rate_now_pct: float
    cpi_yoy_pct: float
    kof_barometer: float
    neer_change_3m_pct: float
    snb_forecast: Dict[str, float]  # {"2025": 0.2, "2026": 0.5, ...}


@dataclass
class NowcastResult:
    """Résultat du nowcast inflation"""
    pi_3m: float
    pi_6m: float
    pi_12m: float


@dataclass
class PathPoint:
    """Point du chemin de taux"""
    month_ahead: int
    rule: float      # Règle de Taylor
    market: float    # OIS/Futures
    fused: float     # Fusion Kalman
    var: float       # Variance Kalman


@dataclass
class DecisionProbs:
    """Probabilités de décision"""
    cut: float
    hold: float
    hike: float


@dataclass
class ModelOutput:
    """Output complet du modèle"""
    as_of: str
    inputs: Dict[str, Any]
    nowcast: Dict[str, float]
    output_gap_pct: float
    i_star_next_pct: float
    probs: Dict[str, float]
    path: List[Dict[str, Any]]
    version: str


# === FONCTIONS CORE DU MODÈLE ===

def nowcast_inflation(cpi_yoy: float, snb_forecast: Dict[str, float]) -> NowcastResult:
    """
    Nowcast de l'inflation à différents horizons
    
    Args:
        cpi_yoy: Inflation YoY actuelle (%)
        snb_forecast: Prévisions BNS {"2025": 0.2, "2026": 0.5, ...}
    
    Returns:
        NowcastResult avec pi_3m, pi_6m, pi_12m
    """
    # Moyenne des 2 dernières années de prévisions BNS
    years = sorted([int(y) for y in snb_forecast.keys()])[-2:] if snb_forecast else []
    mid = np.mean([snb_forecast[str(y)] for y in years]) if years else TARGET_INFLATION
    
    # Pondération progressive CPI actuel → forecast BNS
    pi_3m = 0.7 * cpi_yoy + 0.3 * mid
    pi_6m = 0.5 * cpi_yoy + 0.5 * mid
    pi_12m = 0.3 * cpi_yoy + 0.7 * mid
    
    return NowcastResult(pi_3m=pi_3m, pi_6m=pi_6m, pi_12m=pi_12m)


def output_gap_from_kof(kof_value: float) -> float:
    """
    Estime l'output gap à partir du baromètre KOF
    
    Args:
        kof_value: Valeur du baromètre KOF (typiquement 90-110)
    
    Returns:
        Output gap estimé (%)
    """
    # KOF = 100 → output gap neutre
    # Sensibilité: 0.5 (à calibrer selon données historiques)
    return 0.5 * (kof_value - 100.0)


def taylor_augmented(
    pi_exp: float,
    ygap: float,
    d_neer: float,
    beta_pi: float = 1.5,
    beta_y: float = 0.5,
    beta_fx: float = 0.05,
    alpha: float = 0.0
) -> float:
    """
    Règle de Taylor augmentée avec réaction au taux de change
    
    Args:
        pi_exp: Inflation anticipée (%)
        ygap: Output gap (%)
        d_neer: Variation NEER 3 mois (%)
        beta_pi: Coefficient inflation (défaut: 1.5)
        beta_y: Coefficient output gap (défaut: 0.5)
        beta_fx: Coefficient NEER (défaut: 0.05)
        alpha: Taux neutre (défaut: 0.0)
    
    Returns:
        Taux directeur optimal selon la règle (%)
    """
    i_star = alpha + beta_pi * (pi_exp - TARGET_INFLATION) + beta_y * ygap + beta_fx * d_neer
    return max(LOWER_BOUND, i_star)


def interp_monthly(ois_points: List[OISPoint], months: int = 24) -> np.ndarray:
    """
    Interpolation linéaire de la courbe OIS sur base mensuelle
    
    Args:
        ois_points: Liste de points OIS
        months: Nombre de mois à interpoler (défaut: 24)
    
    Returns:
        Array numpy avec les taux mensuels interpolés
    """
    x = np.array([p.tenor_months for p in ois_points], dtype=float)
    y = np.array([p.rate_pct for p in ois_points], dtype=float)
    xi = np.arange(1, months + 1, dtype=float)
    yi = np.interp(xi, x, y, left=y[0], right=y[-1])
    return yi


def kalman_fuse(
    rule_path: np.ndarray,
    market_path: np.ndarray,
    kappa: float = DEFAULT_KAPPA,
    q: float = DEFAULT_Q,
    r: float = DEFAULT_R
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Fusion Kalman entre règle de Taylor et anticipations de marché
    
    Args:
        rule_path: Chemin règle de Taylor (24 mois)
        market_path: Chemin marché OIS/Futures (24 mois)
        kappa: Vitesse de convergence (0-1)
        q: Variance du processus
        r: Variance de l'observation
    
    Returns:
        Tuple (fused_path, variance_path)
    """
    n = len(rule_path)
    x = rule_path[0]  # État initial = règle mois 1
    P = 0.05          # Variance initiale
    
    fused = np.zeros(n)
    var = np.zeros(n)
    
    for t in range(n):
        # Prédiction
        if t > 0:
            x_pred = x + kappa * (rule_path[t - 1] - x)
        else:
            x_pred = x
        P_pred = P + q
        
        # Mise à jour (observation = marché)
        z = market_path[t]
        K = P_pred / (P_pred + r)  # Gain de Kalman
        x = x_pred + K * (z - x_pred)
        P = (1 - K) * P_pred
        
        fused[t] = x
        var[t] = P
    
    return fused, var


def decision_probs(i_now: float, i_star_next: float) -> DecisionProbs:
    """
    Calcule les probabilités de décision (baisse/maintien/hausse)
    
    Utilise des sigmoïdes pour modéliser les probabilités de changement
    
    Args:
        i_now: Taux directeur actuel (%)
        i_star_next: Taux optimal selon règle (%)
    
    Returns:
        DecisionProbs avec cut, hold, hike
    """
    diff = i_star_next - i_now
    scale = 0.05  # Sensibilité de la sigmoid
    
    # Prob hausse: sigmoid si diff > 0.125 (12.5 bps)
    p_hike = 1 / (1 + math.exp(-(diff - 0.125) / scale))
    
    # Prob baisse: sigmoid si diff < -0.125
    p_cut = 1 / (1 + math.exp(-(-diff - 0.125) / scale))
    
    # Prob maintien: reste
    p_hold = max(0.0, 1 - (p_hike + p_cut))
    
    # Normalisation
    total = p_hike + p_cut + p_hold
    if total > 0:
        return DecisionProbs(
            cut=p_cut / total,
            hold=p_hold / total,
            hike=p_hike / total
        )
    else:
        return DecisionProbs(cut=0.0, hold=1.0, hike=0.0)


# === FONCTION PRINCIPALE ===

def run_model(
    cpi_yoy: float,
    kof: float,
    snb_forecast: Dict[str, float],
    ois_points: List[OISPoint],
    policy_rate_now: float = 0.0,
    neer_change_3m: float = 0.0,
    as_of_date: Optional[date] = None,
    months: int = 24
) -> ModelOutput:
    """
    Exécute le modèle complet BNS
    
    Args:
        cpi_yoy: Inflation YoY (%)
        kof: Baromètre KOF
        snb_forecast: Prévisions BNS {"2025": 0.2, ...}
        ois_points: Points de la courbe OIS
        policy_rate_now: Taux directeur actuel (%, défaut: 0.0)
        neer_change_3m: Variation NEER 3 mois (%, défaut: 0.0)
        as_of_date: Date de référence (défaut: aujourd'hui)
        months: Horizon de projection (défaut: 24)
    
    Returns:
        ModelOutput complet avec tous les résultats
    """
    if as_of_date is None:
        as_of_date = date.today()
    
    # 1. Nowcast inflation
    nowc = nowcast_inflation(cpi_yoy, snb_forecast)
    
    # 2. Output gap
    ygap = output_gap_from_kof(kof)
    
    # 3. Règle de Taylor (utilise pi_12m)
    i_star = taylor_augmented(nowc.pi_12m, ygap, neer_change_3m)
    
    # 4. Chemins de taux
    # Règle: transition sigmoïde de i_now vers i_star
    t = np.arange(months)
    trans = 1.0 / (1.0 + np.exp(-(t - 6) / 2.5))  # Transition progressive sur 6-9 mois
    rule_path = policy_rate_now + (i_star - policy_rate_now) * trans
    
    # Marché: interpolation OIS
    market_path = interp_monthly(ois_points, months=months)
    
    # Fusion Kalman
    fused, var = kalman_fuse(rule_path, market_path)
    
    # 5. Assemblage path
    path = [
        PathPoint(
            month_ahead=int(m + 1),
            rule=float(rule_path[m]),
            market=float(market_path[m]),
            fused=float(fused[m]),
            var=float(var[m])
        )
        for m in range(months)
    ]
    
    # 6. Probabilités de décision
    probs = decision_probs(policy_rate_now, i_star)
    
    # 7. Output final
    return ModelOutput(
        as_of=as_of_date.isoformat(),
        inputs={
            "policy_rate_now_pct": policy_rate_now,
            "cpi_yoy_pct": cpi_yoy,
            "kof_barometer": kof,
            "neer_change_3m_pct": neer_change_3m,
            "snb_forecast": snb_forecast
        },
        nowcast={
            "pi_3m": nowc.pi_3m,
            "pi_6m": nowc.pi_6m,
            "pi_12m": nowc.pi_12m
        },
        output_gap_pct=ygap,
        i_star_next_pct=i_star,
        probs={
            "cut": probs.cut,
            "hold": probs.hold,
            "hike": probs.hike
        },
        path=[
            {
                "month_ahead": p.month_ahead,
                "rule": p.rule,
                "market": p.market,
                "fused": p.fused,
                "var": p.var
            }
            for p in path
        ],
        version="bns-model-2025.09"
    )


def model_output_to_dict(output: ModelOutput) -> Dict[str, Any]:
    """Convertit ModelOutput en dict pour JSON"""
    return {
        "as_of": output.as_of,
        "inputs": output.inputs,
        "nowcast": output.nowcast,
        "output_gap_pct": output.output_gap_pct,
        "i_star_next_pct": output.i_star_next_pct,
        "probs": output.probs,
        "path": output.path,
        "version": output.version
    }


# === HELPERS POUR SUPABASE ===

def parse_ois_points_from_db(ois_data: Dict[str, Any]) -> List[OISPoint]:
    """
    Parse les points OIS depuis le format Supabase
    
    Args:
        ois_data: Row de snb_ois_data (avec field 'points' JSONB)
    
    Returns:
        Liste de OISPoint
    """
    points_json = ois_data.get("points", [])
    if isinstance(points_json, str):
        import json
        points_json = json.loads(points_json)
    
    return [
        OISPoint(tenor_months=p["tenor_months"], rate_pct=p["rate_pct"])
        for p in points_json
    ]


if __name__ == "__main__":
    # Test rapide
    print("🧪 Test du modèle SNB Policy Engine")
    
    # Données de test
    test_ois = [
        OISPoint(tenor_months=3, rate_pct=0.00),
        OISPoint(tenor_months=6, rate_pct=0.01),
        OISPoint(tenor_months=12, rate_pct=0.10),
        OISPoint(tenor_months=24, rate_pct=0.20),
    ]
    
    test_forecast = {"2025": 0.2, "2026": 0.5, "2027": 0.7}
    
    result = run_model(
        cpi_yoy=0.2,
        kof=97.4,
        snb_forecast=test_forecast,
        ois_points=test_ois,
        policy_rate_now=0.0,
        neer_change_3m=0.0
    )
    
    print(f"✅ Output gap: {result.output_gap_pct:.2f}%")
    print(f"✅ i* next: {result.i_star_next_pct:.2f}%")
    print(f"✅ Probs: cut={result.probs['cut']:.1%}, hold={result.probs['hold']:.1%}, hike={result.probs['hike']:.1%}")
    print(f"✅ Path (M+1): rule={result.path[0]['rule']:.3f}, market={result.path[0]['market']:.3f}, fused={result.path[0]['fused']:.3f}")

