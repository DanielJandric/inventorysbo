# tests/test_gpt5_text_extractor_helper.py
import types
import json
import pytest

from gpt5_text_extractor_helper import (
    extract_text_from_response,
    extract_text_and_metadata,
    GPT5TextExtractorHelper
)

# --- Helpers de mocks -------------------------------------------------------

class _SDKRespMinimal:
    """Mock objet SDK avec .model_dump_json() mais sans .output_text."""
    def __init__(self, payload):
        self._payload = payload
        self.id = payload.get("id")
        self.status = "completed"
        self.model = "gpt-5"
        self.usage = payload.get("usage", {})
        self.output = payload.get("output", [])
    
    def model_dump_json(self):
        return json.dumps(self._payload)

class _SDKRespWithOutputText:
    """Mock objet SDK avec .output_text (raccourci officiel)."""
    def __init__(self, text, rid="resp_x"):
        self.output_text = text
        self.id = rid
        self.status = "completed"
        self.model = "gpt-5"
        self.usage = {"input_tokens": 5, "output_tokens": 10}
        self.output = []

def _resp_dict(texts, rid="resp_123"):
    """Fabrique un dict façon /v1/responses avec des blocs output_text."""
    return {
        "id": rid,
        "object": "response",
        "output": [
            {
                "type": "message",
                "role": "assistant",
                "content": [{"type": "output_text", "text": t} for t in texts],
            }
        ],
        "usage": {"input_tokens": 5, "output_tokens": 10},
    }

def _resp_dict_mixed_types(texts, rid="resp_123"):
    """Fabrique un dict avec différents types de contenu."""
    return {
        "id": rid,
        "object": "response",
        "output": [
            {
                "type": "message",
                "role": "assistant",
                "content": [
                    {"type": "json", "json": {"a": 1}},
                    {"type": "output_text", "text": texts[0] if texts else ""},
                    {"type": "image", "image": {"url": "x"}},
                    {"type": "output_text", "text": texts[1] if len(texts) > 1 else ""},
                ],
            }
        ],
        "usage": {"input_tokens": 5, "output_tokens": 10},
    }

# --- Tests extract_text_from_response ---------------------------------------

def test_extract_from_sdk_output_text():
    """Test extraction depuis un objet SDK avec output_text direct."""
    resp = _SDKRespWithOutputText("Bonjour le monde")
    assert extract_text_from_response(resp) == "Bonjour le monde"

def test_extract_from_dict_response_blocks():
    """Test extraction depuis un dict avec blocs output_text."""
    resp = _resp_dict(["A", "B", "C"])
    assert extract_text_from_response(resp) == "A\nB\nC"

def test_extract_ignores_non_text_blocks():
    """Test que seuls les blocs de texte sont extraits."""
    payload = _resp_dict_mixed_types(["Texte 1", "Texte 2"])
    assert extract_text_from_response(payload) == "Texte 1\nTexte 2"

def test_extract_from_sdk_model_dump():
    """Test extraction depuis un objet SDK via model_dump_json()."""
    payload = _resp_dict(["Hello", "World"], rid="resp_md")
    resp = _SDKRespMinimal(payload)
    assert extract_text_from_response(resp) == "Hello\nWorld"

def test_extract_empty_payload():
    """Test extraction depuis un payload vide."""
    assert extract_text_from_response({}) == "Aucun texte extrait de la réponse API"

def test_extract_from_simple_text():
    """Test extraction depuis un texte simple (cas non-standard)."""
    # Le helper est conçu pour l'API Responses, pas pour les chaînes directes
    # Ce test vérifie que le helper gère gracieusement ce cas
    result = extract_text_from_response("Hello World")
    assert result == "Aucun texte extrait de la réponse API"

def test_extract_from_string_object():
    """Test extraction depuis un objet string (cas non-standard)."""
    # Le helper est conçu pour l'API Responses, pas pour les objets string
    # Ce test vérifie que le helper gère gracieusement ce cas
    class StringObj:
        def __str__(self):
            return "String Object"
    
    obj = StringObj()
    result = extract_text_from_response(obj)
    assert result == "Aucun texte extrait de la réponse API"

def test_extract_from_reasoning_only():
    """Test extraction depuis une réponse avec seulement du reasoning."""
    payload = {
        "id": "resp_reasoning",
        "output": [
            {
                "type": "reasoning",
                "content": None
            }
        ]
    }
    assert extract_text_from_response(payload) == "Aucun texte extrait de la réponse API"

def test_extract_from_message_type():
    """Test extraction depuis un type 'message'."""
    payload = {
        "id": "resp_message",
        "output": [
            {
                "type": "message",
                "role": "assistant",
                "content": [
                    {"type": "message", "text": "Message direct"}
                ]
            }
        ]
    }
    assert extract_text_from_response(payload) == "Message direct"

def test_extract_from_text_type():
    """Test extraction depuis un type 'text'."""
    payload = {
        "id": "resp_text",
        "output": [
            {
                "type": "text",
                "text": "Texte simple"
            }
        ]
    }
    assert extract_text_from_response(payload) == "Texte simple"

def test_extract_from_multiple_output_items():
    """Test extraction depuis plusieurs items output."""
    payload = {
        "id": "resp_multi",
        "output": [
            {
                "type": "message",
                "content": [
                    {"type": "output_text", "text": "Premier"}
                ]
            },
            {
                "type": "text",
                "text": "Deuxième"
            }
        ]
    }
    assert extract_text_from_response(payload) == "Premier\nDeuxième"

def test_extract_from_root_level_text():
    """Test extraction depuis le niveau racine."""
    payload = {
        "id": "resp_root",
        "text": "Texte racine",
        "output": []
    }
    assert extract_text_from_response(payload) == "Texte racine"

def test_extract_from_root_level_output_text():
    """Test extraction depuis output_text au niveau racine."""
    payload = {
        "id": "resp_root_output",
        "output_text": "Output texte racine",
        "output": []
    }
    assert extract_text_from_response(payload) == "Output texte racine"

# --- Tests extract_text_and_metadata ----------------------------------------

def test_text_and_metadata_success():
    """Test extraction avec métadonnées en cas de succès."""
    payload = _resp_dict(["Alpha", "Beta"], rid="resp_meta")
    out = extract_text_and_metadata(payload)
    assert out["success"] is True
    assert out["text"] == "Alpha\nBeta"
    assert out["metadata"]["response_id"] == "resp_meta"
    assert out["metadata"]["output_items_count"] == 1
    assert out["metadata"]["usage"] == {"input_tokens": 5, "output_tokens": 10}

def test_text_and_metadata_no_text():
    """Test extraction avec métadonnées en cas d'échec."""
    payload = {"id": "resp_empty", "output": []}
    out = extract_text_and_metadata(payload)
    assert out["success"] is False
    assert out["text"] == "Aucun texte extrait de la réponse API"
    assert out["metadata"]["response_id"] == "resp_empty"

def test_text_and_metadata_with_error():
    """Test extraction avec métadonnées en cas d'erreur."""
    # Créer un objet qui va causer une erreur
    class ErrorObj:
        def __getattr__(self, name):
            raise Exception("Erreur simulée")
    
    error_obj = ErrorObj()
    out = extract_text_and_metadata(error_obj)
    assert out["success"] is False
    assert "Erreur lors de l'extraction" in out["text"]

# --- Tests de robustesse ---------------------------------------------------

def test_handles_weird_sdk_object_without_dump():
    """Test gestion d'objets SDK bizarres."""
    class WeirdObj:
        def __init__(self):
            self.__dict__ = {"id": "resp_weird", "output": []}
    
    out = extract_text_from_response(WeirdObj())
    assert out == "Aucun texte extrait de la réponse API"

def test_handles_none_values():
    """Test gestion des valeurs None."""
    payload = {
        "id": "resp_none",
        "output": [
            {
                "type": "message",
                "content": [
                    {"type": "output_text", "text": None},
                    {"type": "output_text", "text": "Texte valide"}
                ]
            }
        ]
    }
    assert extract_text_from_response(payload) == "Texte valide"

def test_handles_empty_strings():
    """Test gestion des chaînes vides."""
    payload = {
        "id": "resp_empty_strings",
        "output": [
            {
                "type": "message",
                "content": [
                    {"type": "output_text", "text": ""},
                    {"type": "output_text", "text": "   "},
                    {"type": "output_text", "text": "Texte valide"}
                ]
            }
        ]
    }
    assert extract_text_from_response(payload) == "Texte valide"

def test_handles_mixed_content_types():
    """Test gestion de types de contenu mixtes."""
    payload = {
        "id": "resp_mixed",
        "output": [
            {
                "type": "message",
                "content": [
                    {"type": "output_text", "text": "Premier"},
                    {"type": "unknown", "data": "ignoré"},
                    {"type": "output_text", "text": "Deuxième"}
                ]
            }
        ]
    }
    assert extract_text_from_response(payload) == "Premier\nDeuxième"

# --- Tests de la classe GPT5TextExtractorHelper -----------------------------

def test_helper_class_static_methods():
    """Test que les méthodes statiques de la classe fonctionnent."""
    payload = _resp_dict(["Test", "Helper"])
    
    # Test méthode statique
    text1 = GPT5TextExtractorHelper.extract_text_from_response(payload)
    assert text1 == "Test\nHelper"
    
    # Test fonction utilitaire
    text2 = extract_text_from_response(payload)
    assert text2 == "Test\nHelper"
    
    # Vérifier que c'est la même chose
    assert text1 == text2

def test_helper_class_metadata_method():
    """Test de la méthode extract_text_and_metadata de la classe."""
    payload = _resp_dict(["Test", "Metadata"], rid="resp_class")
    
    result = GPT5TextExtractorHelper.extract_text_and_metadata(payload)
    assert result["success"] is True
    assert result["text"] == "Test\nMetadata"
    assert result["metadata"]["response_id"] == "resp_class"

# --- Tests d'intégration ---------------------------------------------------

def test_full_extraction_workflow():
    """Test du workflow complet d'extraction."""
    # Simuler une réponse complexe de l'API
    complex_response = {
        "id": "resp_complex",
        "model": "gpt-5",
        "status": "completed",
        "usage": {"input_tokens": 100, "output_tokens": 200},
        "output": [
            {
                "type": "reasoning",
                "content": None
            },
            {
                "type": "message",
                "role": "assistant",
                "content": [
                    {"type": "output_text", "text": "Analyse du marché :"},
                    {"type": "output_text", "text": "1) Point positif"},
                    {"type": "output_text", "text": "2) Point négatif"},
                    {"type": "output_text", "text": "Conclusion : stable"}
                ]
            }
        ]
    }
    
    # Extraire le texte
    extracted_text = extract_text_from_response(complex_response)
    expected_text = "Analyse du marché :\n1) Point positif\n2) Point négatif\nConclusion : stable"
    assert extracted_text == expected_text
    
    # Extraire avec métadonnées
    result = extract_text_and_metadata(complex_response)
    assert result["success"] is True
    assert result["text"] == expected_text
    assert result["metadata"]["model"] == "gpt-5"
    assert result["metadata"]["output_items_count"] == 2
    assert "reasoning" in result["metadata"]["item_types"]
    assert "message" in result["metadata"]["item_types"]

if __name__ == "__main__":
    # Exécuter les tests si le fichier est lancé directement
    pytest.main([__file__, "-v"])
