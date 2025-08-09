from flask import Blueprint, request, jsonify
from typing import Optional
from datetime import datetime

metrics_bp = Blueprint('metrics', __name__)

# --- Helpers ---

def _normalize_category_label(raw: Optional[str]) -> Optional[str]:
    if not raw:
        return raw
    mapping = {
        'voiture': 'Voitures', 'voitures': 'Voitures', 'vehicules': 'Voitures', 'véhicules': 'Voitures',
        'montre': 'Montres', 'montres': 'Montres',
        'avion': 'Avions', 'avions': 'Avions',
        'bateau': 'Bateaux', 'bateaux': 'Bateaux',
        'action': 'Actions', 'actions': 'Actions',
    }
    key = raw.strip().lower()
    return mapping.get(key, raw)


def _item_value(it) -> float:
    try:
        # For stocks, compute value as quantity * current_price
        if getattr(it, 'category', None) == 'Actions' and getattr(it, 'current_price', None) and getattr(it, 'stock_quantity', None):
            return float(it.current_price) * float(it.stock_quantity)
        # Otherwise, use current_value
        return float(getattr(it, 'current_value', 0) or 0)
    except Exception:
        return 0.0


def _compute_counts(items_list, category: Optional[str], mode: str = 'available') -> dict:
    if category:
        category = _normalize_category_label(category)
        items_cat = [i for i in items_list if i.category == category]
    else:
        items_cat = items_list
    total = len(items_cat)
    sold = sum(1 for i in items_cat if (getattr(i, 'status', '') or '') == 'Sold')
    available = total - sold
    if mode == 'total':
        return {"category": category, "total": total, "sold": sold, "available": available}
    return {"category": category, "available": available, "sold": sold, "total": total}


def _compute_values(items_list, category: Optional[str], mode: str = 'available') -> dict:
    if category:
        category = _normalize_category_label(category)
        items_cat = [i for i in items_list if i.category == category]
    else:
        items_cat = items_list
    def is_available(it) -> bool:
        return (getattr(it, 'status', '') or '') != 'Sold'
    selected = items_cat if mode == 'total' else [i for i in items_cat if is_available(i)]
    total_value = 0.0
    for it in selected:
        total_value += _item_value(it)
    return {"category": category, "mode": mode, "value": round(total_value, 2)}


@metrics_bp.route('/metrics/counts', methods=['GET'])
def api_metrics_counts():
    try:
        # Deferred import to avoid circular dependency
        from app import AdvancedDataManager
        category = request.args.get('category')
        mode = (request.args.get('mode') or 'available').lower()
        items_list = AdvancedDataManager.fetch_all_items()
        if category:
            res = _compute_counts(items_list, category, mode)
        else:
            cats = sorted({i.category for i in items_list})
            res = {c: _compute_counts(items_list, c, mode) for c in cats}
        return jsonify({"success": True, "result": res})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@metrics_bp.route('/metrics/values', methods=['GET'])
def api_metrics_values():
    try:
        from app import AdvancedDataManager
        category = request.args.get('category')
        mode = (request.args.get('mode') or 'available').lower()
        items_list = AdvancedDataManager.fetch_all_items()
        if category:
            res = _compute_values(items_list, category, mode)
        else:
            cats = sorted({i.category for i in items_list})
            res = {c: _compute_values(items_list, c, mode) for c in cats}
        return jsonify({"success": True, "result": res})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@metrics_bp.route('/knowledge/pack', methods=['GET'])
def api_knowledge_pack():
    try:
        from app import AdvancedDataManager
        items_list = AdvancedDataManager.fetch_all_items()
        cats = sorted({i.category for i in items_list})
        pack = {
            "generated_at": datetime.now().isoformat(),
            "categories": {}
        }
        for c in cats:
            counts = _compute_counts(items_list, c, 'total')
            val_av = _compute_values(items_list, c, 'available')
            val_tot = _compute_values(items_list, c, 'total')
            top_items = [i for i in items_list if i.category == c and (getattr(i, 'status', '') or '') != 'Sold']
            top_items.sort(key=_item_value, reverse=True)
            pack["categories"][c] = {
                "counts": counts,
                "value_available": val_av,
                "value_total": val_tot,
                "top_items": [{"id": i.id, "name": i.name, "value": _item_value(i)} for i in top_items[:5]]
            }
        return jsonify({"success": True, "pack": pack})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
