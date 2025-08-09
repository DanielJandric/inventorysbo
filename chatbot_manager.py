import os
import json
from datetime import datetime
from types import SimpleNamespace

import requests


class ChatbotManager:
    def __init__(self, api_base_url="http://127.0.0.1:5000"):
        # Lazy import to avoid hard dependency at init time
        try:
            from ai_engine import get_ai_engine  # type: ignore
            self.ai_engine = get_ai_engine()
        except Exception:
            # Fallback: create a lightweight OpenAI client if possible
            self.ai_engine = None
            try:
                from openai import OpenAI  # type: ignore
                api_key = os.getenv("OPENAI_API_KEY")
                if api_key:
                    self.ai_engine = SimpleNamespace(openai_client=OpenAI(api_key=api_key))
            except Exception:
                self.ai_engine = None
        # Prefer explicit API_BASE_URL, then APP_URL (public Render URL), then provided default
        base = os.getenv("API_BASE_URL") or os.getenv("APP_URL") or api_base_url
        # Ensure scheme
        if not base.startswith("http://") and not base.startswith("https://"):
            base = "https://" + base
        self.api_base_url = base.rstrip('/')
        # Configurable HTTP timeout
        self.request_timeout = int(os.getenv("CHATBOT_API_TIMEOUT", "60"))

    def extract_item(self, user_input: str) -> dict:
        """Public method: extract and normalize item fields from natural language."""
        extracted = self._extract_item_data_with_ai(user_input) or {}
        normalized = self._normalize_item_payload(extracted)
        missing = [k for k in ("name", "category") if k not in normalized]
        return {"data": normalized, "missing": missing}

    def extract_items(self, user_input: str) -> dict:
        """Extract multiple items from a single natural language query.
        Returns: {"items": [payload, ...]} with normalized payloads.
        """
        raw = self._extract_items_data_with_ai(user_input) or {}
        items = raw.get("items") if isinstance(raw, dict) else None
        if not isinstance(items, list):
            # Fallback: try single extraction
            one = self._extract_item_data_with_ai(user_input) or {}
            items = [one] if one else []
        normalized_items = []
        for it in items:
            norm = self._normalize_item_payload(it or {})
            normalized_items.append(norm)
        return {"items": normalized_items}

    def create_from_payload(self, payload: dict) -> dict:
        """Public method: create an item from a given JSON payload."""
        normalized = self._normalize_item_payload(payload or {})
        if 'name' not in normalized or 'category' not in normalized:
            return {"success": False, "error": "Missing required fields: name and category."}
        return self._create_item_via_api(normalized)

    def parse_and_create_item(self, user_input: str) -> dict:
        """
        Parses user input to extract item details, confirms with the user,
        and creates the item via the API.
        """
        extracted_data = self._extract_item_data_with_ai(user_input)
        if not extracted_data:
            return {"success": False, "error": "Failed to extract item data from your request."}

        # Normalize keys and defaults
        normalized = self._normalize_item_payload(extracted_data)
        if 'name' not in normalized or 'category' not in normalized:
            return {"success": False, "error": "Missing required fields: name and category."}

        # Create the item by calling the local API
        return self._create_item_via_api(normalized)

    def _extract_item_data_with_ai(self, user_input: str) -> dict | None:
        """
        Uses the AI engine to convert natural language into a structured
        dictionary of item properties.
        """
        # Minimal schema the backend accepts (derived from app.py CollectionItem)
        allowed_keys = [
            "name", "category", "status", "construction_year", "condition", "description",
            "current_value", "sold_price", "acquisition_price", "for_sale", "sale_status",
            "sale_progress", "buyer_contact", "intermediary", "current_offer", "commission_rate",
            "last_action_date", "surface_m2", "rental_income_chf", "location",
            "stock_symbol", "stock_quantity", "stock_purchase_price", "stock_exchange",
            "stock_currency"
        ]

        prompt = f"""
        You are an assistant that extracts item data for a collection inventory.
        Return ONLY a valid JSON object containing any of these keys when present:
        {json.dumps(allowed_keys)}
        
        Rules:
        - Infer 'category' from text (e.g., "montre"->"Montres", "voiture"->"Voitures", "action"->"Actions").
        - Use numbers (not strings) for numeric fields (prices, quantities, years, commission_rate, surface_m2).
        - Use ISO-like strings for dates (YYYY-MM-DD) when given.
        - If a value is unknown, omit the key.
        - Default status is 'Available' (we may set it later if missing).
        - If the asset is a stock, include stock_symbol and stock_quantity when possible.
        
        User Request: "{user_input}"
        """

        try:
            if not self.ai_engine or not getattr(self.ai_engine, 'openai_client', None):
                raise ValueError("AI engine not configured.")

            response = self.ai_engine.openai_client.chat.completions.create(
                model=os.getenv("AI_MODEL", "gpt-4.1"),
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=0.2,
            )
            extracted_json = response.choices[0].message.content
            if extracted_json:
                return json.loads(extracted_json)
            return None
        except Exception:
            return None

    def _extract_items_data_with_ai(self, user_input: str) -> dict | None:
        """
        Uses AI to extract a list of items from the user's sentence.
        Returns a JSON object: {"items": [ {...}, {...} ]}
        Each item uses the same schema as _extract_item_data_with_ai.
        """
        allowed_keys = [
            "name", "category", "status", "construction_year", "condition", "description",
            "current_value", "sold_price", "acquisition_price", "for_sale", "sale_status",
            "sale_progress", "buyer_contact", "intermediary", "current_offer", "commission_rate",
            "last_action_date", "surface_m2", "rental_income_chf", "location",
            "stock_symbol", "stock_quantity", "stock_purchase_price", "stock_exchange",
            "stock_currency"
        ]

        prompt = f"""
        You are an assistant that extracts a LIST of items from a user's sentence about assets to add.
        Return ONLY a JSON object with an "items" array, where each item is a JSON object using any of these keys:
        {json.dumps(allowed_keys)}

        Rules:
        - Split the user's sentence into distinct items if it mentions quantities or conjunctions.
        - For plurals with a number (e.g., "trois voitures mercedes"), create that many items.
        - Infer 'category' from text (montre→Montres, voiture→Voitures, bateau→Bateaux, avion→Avions, action→Actions). Use your general knowledge for brands (e.g., Axopar → Bateaux, Mercedes → Voitures, Swatch → Montres, Sunseeker → Bateaux).
        - Infer 'condition' from wording: "neuf/neuve" → "Neuf"; "d'occasion/occasion/used" → "Bon".
        - If the text implies buying (e.g., "acheté/achete"), put the amount into "acquisition_price"; otherwise use "current_value".
        - Parse amounts like "20k", "30 kchf", "120kchf" into numbers (e.g., 20000, 30000, 120000). Currency always CHF.
        - If brand/model appears (e.g., Mercedes, Axopar), include it in the "name" if no explicit name is provided.
        - Use numeric types for numeric fields.
        - If information is missing, omit the key (we'll fill defaults later). Default status is 'Available'.

        User Request: "{user_input}"
        """

        try:
            if not self.ai_engine or not getattr(self.ai_engine, 'openai_client', None):
                raise ValueError("AI engine not configured.")

            response = self.ai_engine.openai_client.chat.completions.create(
                model=os.getenv("AI_MODEL", "gpt-4-turbo"),
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=0.2,
            )
            extracted_json = response.choices[0].message.content
            if extracted_json:
                return json.loads(extracted_json)
            return None
        except Exception:
            return None

    def _normalize_item_payload(self, data: dict) -> dict:
        """Normalize AI output keys to backend expectations and set defaults."""
        if not isinstance(data, dict):
            return {}
        normalized = dict(data)

        # Common synonyms mapping
        synonyms = {
            "purchase_price": "acquisition_price",
            "buy_price": "acquisition_price",
            "price": "current_value",
            "year": "construction_year",
            "area_m2": "surface_m2",
            "rent_income_chf": "rental_income_chf",
            "ticker": "stock_symbol",
            "symbol": "stock_symbol",
            "qty": "stock_quantity",
        }
        for k, v in list(normalized.items()):
            if k in synonyms and synonyms[k] not in normalized:
                normalized[synonyms[k]] = v

        # Default status
        if 'status' not in normalized or not normalized['status']:
            normalized['status'] = 'Available'

        # Default for_sale coercion
        if 'for_sale' in normalized and isinstance(normalized['for_sale'], str):
            normalized['for_sale'] = normalized['for_sale'].lower() in ("yes", "true", "1", "oui")

        # Ensure numeric fields are numbers when possible
        numeric_keys = [
            "current_value", "sold_price", "acquisition_price", "current_offer", "commission_rate",
            "surface_m2", "rental_income_chf", "stock_quantity", "stock_purchase_price", "construction_year"
        ]
        for nk in numeric_keys:
            if nk in normalized and isinstance(normalized[nk], str):
                try:
                    # allow floats and ints
                    normalized[nk] = float(str(normalized[nk]).replace(' ', '').replace(',', '.'))
                    if nk in ("stock_quantity", "construction_year"):
                        normalized[nk] = int(normalized[nk])
                except Exception:
                    pass

        return normalized

    def _create_item_via_api(self, item_data: dict) -> dict:
        url = f"{self.api_base_url}/api/items"
        headers = {"Content-Type": "application/json"}
        # Single retry on timeout
        for attempt in range(2):
            try:
                resp = requests.post(url, headers=headers, data=json.dumps(item_data), timeout=self.request_timeout)
                if resp.status_code >= 400:
                    return {"success": False, "status_code": resp.status_code, "error": resp.text}
                return {"success": True, "item": resp.json()}
            except (requests.exceptions.ReadTimeout, requests.exceptions.ConnectTimeout):
                if attempt == 0:
                    continue
                return {"success": False, "error": f"Timed out after {self.request_timeout}s"}
            except requests.exceptions.RequestException as e:
                return {"success": False, "error": str(e)}
        return {"success": False, "error": "Unknown error"}


if __name__ == '__main__':
    chatbot = ChatbotManager()
    user_text = "Ajoute une montre Patek Philippe Nautilus 5711, achetée 100000 CHF, état neuf."
    result = chatbot.parse_and_create_item(user_text)
    print(json.dumps(result, indent=2, ensure_ascii=False))
