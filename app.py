import os
import requests
import json
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

# Configuration Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Configuration OpenAI
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

def get_supabase_headers():
    return {
        'apikey': SUPABASE_KEY,
        'Authorization': f'Bearer {SUPABASE_KEY}',
        'Content-Type': 'application/json'
    }

def get_items_from_supabase():
    """Récupérer les objets depuis Supabase - TABLE ITEMS"""
    try:
        response = requests.get(f"{SUPABASE_URL}/rest/v1/items", headers=get_supabase_headers())
        if response.status_code == 200:
            return response.json()
        else:
            return []
    except Exception as e:
        print(f"Erreur Supabase: {e}")
        return []

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/items', methods=['GET'])
def get_items():
    """Récupérer tous les objets depuis Supabase"""
    try:
        items = get_items_from_supabase()
        return jsonify(items)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/items', methods=['POST'])
def create_item():
    """Créer un nouvel objet dans Supabase"""
    try:
        data = request.json
        response = requests.post(
            f"{SUPABASE_URL}/rest/v1/items",
            headers=get_supabase_headers(),
            json=data
        )
        
        if response.status_code in [200, 201]:
            return jsonify({"success": True})
        else:
            return jsonify({"error": "Erreur lors de la création"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/items/<int:item_id>', methods=['PUT'])
def update_item(item_id):
    """Modifier un objet existant dans Supabase"""
    try:
        data = request.json
        response = requests.patch(
            f"{SUPABASE_URL}/rest/v1/items?id=eq.{item_id}",
            headers=get_supabase_headers(),
            json=data
        )
        
        if response.status_code == 204:
            return jsonify({"success": True})
        else:
            return jsonify({"error": "Erreur lors de la modification"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/items/<int:item_id>', methods=['DELETE'])
def delete_item(item_id):
    """Supprimer un objet de Supabase"""
    try:
        response = requests.delete(
            f"{SUPABASE_URL}/rest/v1/items?id=eq.{item_id}",
            headers=get_supabase_headers()
        )
        
        if response.status_code == 204:
            return jsonify({"success": True})
        else:
            return jsonify({"error": "Erreur lors de la suppression"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/market-price/<int:item_id>')
def get_market_price(item_id):
    """Obtenir une estimation de prix via OpenAI GPT-4o"""
    try:
        # Récupérer l'objet depuis Supabase
        items = get_items_from_supabase()
        item = next((i for i in items if i['id'] == item_id), None)
        
        if not item:
            return jsonify({"error": "Objet non trouvé"}), 404
        
        # Prompt optimisé qui analyse d'abord le titre
        prompt = f"""ESTIMATION DE PRIX - MARCHÉ SUISSE

OBJET À ANALYSER:
Titre: "{item.get('name', 'objet')}"

DONNÉES COMPLÉMENTAIRES (si disponibles):
- Catégorie: {item.get('category', 'non spécifiée')}
- Année: {item.get('construction_year', 'non spécifiée')}
- État: {item.get('condition', 'non spécifié')}

INSTRUCTIONS:
1. COMMENCE TOUJOURS par analyser le titre pour identifier l'objet
2. Le titre seul doit suffire pour une première estimation
3. Utilise les données complémentaires pour affiner SI elles sont utiles
4. L'absence d'informations complémentaires ne doit PAS empêcher l'estimation
5. Donne un prix réaliste pour le marché suisse en CHF

Réponds UNIQUEMENT en JSON valide:
{{
    "price": [prix en CHF basé principalement sur le titre],
    "confidence": [0-100, selon la qualité des infos du titre],
    "analysis": "Ton raisonnement depuis le titre, puis affinements",
    "market_factors": "Facteurs de marché",
    "comparable_sales": "Exemples similaires"
}}"""
        
        # Appel à l'API OpenAI
        openai_response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "gpt-4o",
                "messages": [
                    {"role": "system", "content": "Tu es un expert en évaluation. Réponds uniquement en JSON valide."},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 300,
                "temperature": 0.1
            }
        )
        
        if openai_response.status_code == 200:
            openai_data = openai_response.json()
            content = openai_data['choices'][0]['message']['content'].strip()
            
            # Nettoyer le contenu pour extraire le JSON
            if content.startswith('```json'):
                content = content[7:]
            if content.startswith('```'):
                content = content[3:]
            if content.endswith('```'):
                content = content[:-3]
            content = content.strip()
            
            # Parser la réponse JSON
            try:
                price_data = json.loads(content)
                
                # Validation des prix pour éviter les aberrations
                estimated_price = price_data.get("price", 0)
                if estimated_price > 50000000 or estimated_price < 0:  # Prix aberrant
                    return jsonify({
                        "price": 0,
                        "confidence": 0,
                        "analysis": "Données pas disponibles - estimation aberrante détectée",
                        "market_factors": "Données pas disponibles",
                        "comparable_sales": "Données pas disponibles",
                        "success": True
                    })
                
                price_data["price"] = estimated_price
                price_data['success'] = True
                return jsonify(price_data)
            except json.JSONDecodeError as e:
                print(f"Erreur JSON: {e}")
                print(f"Contenu reçu: {content}")
                # Fallback honnête : données pas disponibles
                return jsonify({
                    "price": 0,
                    "confidence": 0,
                    "analysis": "Données pas disponibles pour cette estimation. L'IA n'a pas pu fournir une évaluation fiable pour cet objet.",
                    "market_factors": "Données pas disponibles",
                    "comparable_sales": "Données pas disponibles",
                    "success": True
                })
        else:
            return jsonify({"error": "Erreur OpenAI"}), 500
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/static/<path:filename>')
def static_files(filename):
    """Servir les fichiers statiques"""
    return app.send_static_file(filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
