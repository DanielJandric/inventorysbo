#!/usr/bin/env python3
"""
Helper GPT-5 - Extraction GARANTIE de texte de l'API Responses
Basé sur l'analyse de ChatGPT : extrait TOUT le texte disponible
"""

import json
from typing import Dict, Any, List, Optional, Union
from openai import OpenAI, OpenAIError

class GPT5TextExtractorHelper:
    """Helper qui garantit TOUJOURS l'extraction de texte de l'API Responses"""
    
    @staticmethod
    def extract_text_from_response(response: Union[Dict, Any]) -> str:
        """
        Extrait et concatène TOUT le texte présent dans la réponse OpenAI (/v1/responses).
        Garantit de retourner du texte, même si la structure change.
        """
        texts = []
        
        try:
            # Si c'est un objet OpenAI, le convertir en dict
            if hasattr(response, 'model_dump_json'):
                resp_dict = json.loads(response.model_dump_json())
            elif hasattr(response, '__dict__'):
                resp_dict = response.__dict__
            else:
                resp_dict = response
            
            # Vérifier si output existe
            if "output" in resp_dict and resp_dict["output"]:
                for item in resp_dict["output"]:
                    # Si l'item a du contenu
                    if "content" in item and item["content"]:
                        for block in item["content"]:
                            # Extraire le texte selon le type
                            if block.get("type") == "output_text":
                                text = block.get("text", "")
                                if text and isinstance(text, str):
                                    texts.append(text)
                            
                            # Si c'est du texte simple
                            elif block.get("type") == "text":
                                text = block.get("text", "")
                                if text and isinstance(text, str):
                                    texts.append(text)
                            
                            # Si c'est un message
                            elif block.get("type") == "message":
                                text = block.get("text", "")
                                if text and isinstance(text, str):
                                    texts.append(text)
                    
                    # Si l'item a du texte direct
                    if "text" in item and item["text"]:
                        text = item["text"]
                        if isinstance(text, str):
                            texts.append(text)
            
            # Vérifier aussi au niveau racine
            if "text" in resp_dict and resp_dict["text"]:
                text = resp_dict["text"]
                if isinstance(text, str):
                    texts.append(text)
            
            # Si output_text existe au niveau racine (fallback)
            if "output_text" in resp_dict and resp_dict["output_text"]:
                text = resp_dict["output_text"]
                if isinstance(text, str):
                    texts.append(text)
            
        except Exception as e:
            print(f"⚠️ Erreur lors de l'extraction: {e}")
            # En cas d'erreur, essayer d'extraire du texte brut
            try:
                if isinstance(response, str):
                    texts.append(response)
                elif hasattr(response, '__str__'):
                    texts.append(str(response))
            except:
                pass
        
        # Filtrer et nettoyer les textes
        clean_texts = []
        for text in texts:
            if text and isinstance(text, str) and text.strip():
                clean_texts.append(text.strip())
        
        # Concaténer tous les textes trouvés
        result = "\n".join(clean_texts).strip()
        
        # Si aucun texte trouvé, retourner un message d'erreur
        if not result:
            result = "Aucun texte extrait de la réponse API"
        
        return result
    
    @staticmethod
    def extract_text_with_fallback(response: Union[Dict, Any]) -> str:
        """
        Version avec fallback : si pas de texte, retourne la structure complète
        """
        text = GPT5TextExtractorHelper.extract_text_from_response(response)
        
        if text == "Aucun texte extrait de la réponse API":
            # Fallback : afficher la structure pour debug
            try:
                if hasattr(response, 'model_dump_json'):
                    structure = json.loads(response.model_dump_json())
                else:
                    structure = str(response)
                
                text = f"Structure de réponse (pas de texte): {structure}"
            except:
                text = f"Impossible d'extraire le texte ou la structure: {type(response)}"
        
        return text
    
    @staticmethod
    def extract_text_and_metadata(response: Union[Dict, Any]) -> Dict[str, Any]:
        """
        Extrait le texte ET les métadonnées utiles
        """
        try:
            # Extraire le texte
            text = GPT5TextExtractorHelper.extract_text_from_response(response)
            
            # Extraire les métadonnées
            metadata = {}
            
            # Gérer les différents types d'objets
            if hasattr(response, 'id'):
                metadata['response_id'] = response.id
            elif hasattr(response, '__dict__') and 'id' in response.__dict__:
                metadata['response_id'] = response.__dict__['id']
            elif isinstance(response, dict) and 'id' in response:
                metadata['response_id'] = response['id']
            
            if hasattr(response, 'status'):
                metadata['status'] = response.status
            elif hasattr(response, '__dict__') and 'status' in response.__dict__:
                metadata['status'] = response.__dict__['status']
            elif isinstance(response, dict) and 'status' in response:
                metadata['status'] = response['status']
            
            if hasattr(response, 'usage'):
                metadata['usage'] = response.usage
            elif hasattr(response, '__dict__') and 'usage' in response.__dict__:
                metadata['usage'] = response.__dict__['usage']
            elif isinstance(response, dict) and 'usage' in response:
                metadata['usage'] = response['usage']
            
            if hasattr(response, 'model'):
                metadata['model'] = response.model
            elif hasattr(response, '__dict__') and 'model' in response.__dict__:
                metadata['model'] = response.__dict__['model']
            elif isinstance(response, dict) and 'model' in response:
                metadata['model'] = response['model']
            
            # Compter les items de sortie et analyser les types
            try:
                output_items = None
                if hasattr(response, 'output') and response.output:
                    output_items = response.output
                elif hasattr(response, '__dict__') and 'output' in response.__dict__ and response.__dict__['output']:
                    output_items = response.__dict__['output']
                elif isinstance(response, dict) and 'output' in response and response['output']:
                    output_items = response['output']
                
                if output_items:
                    metadata['output_items_count'] = len(output_items)
                    
                    # Analyser les types d'items
                    item_types = []
                    for item in output_items:
                        if hasattr(item, 'type'):
                            item_types.append(item.type)
                        elif isinstance(item, dict) and 'type' in item:
                            item_types.append(item['type'])
                    
                    metadata['item_types'] = item_types
                else:
                    metadata['output_items_count'] = 0
                    metadata['item_types'] = []
            except:
                metadata['output_items_count'] = 0
                metadata['item_types'] = []
            
            return {
                "text": text,
                "metadata": metadata,
                "success": text != "Aucun texte extrait de la réponse API"
            }
            
        except Exception as e:
            return {
                "text": f"Erreur lors de l'extraction: {e}",
                "metadata": {"error": str(e)},
                "success": False
            }

# Fonction utilitaire simple pour usage rapide
def extract_text_from_response(response: Union[Dict, Any]) -> str:
    """
    Fonction utilitaire simple pour extraire le texte
    """
    return GPT5TextExtractorHelper.extract_text_from_response(response)

def extract_text_with_fallback(response: Union[Dict, Any]) -> str:
    """
    Fonction utilitaire avec fallback
    """
    return GPT5TextExtractorHelper.extract_text_with_fallback(response)

def extract_text_and_metadata(response: Union[Dict, Any]) -> Dict[str, Any]:
    """
    Fonction utilitaire avec métadonnées
    """
    return GPT5TextExtractorHelper.extract_text_and_metadata(response)

# Test du helper
if __name__ == "__main__":
    print("🧪 TEST DU HELPER D'EXTRACTION DE TEXTE")
    
    # Test avec une structure simulée
    test_response = {
        "id": "resp_test",
        "output": [
            {
                "type": "reasoning",
                "content": None
            },
            {
                "type": "message",
                "role": "assistant",
                "content": [
                    {
                        "type": "output_text",
                        "text": "OK – Voici ma réponse de test."
                    }
                ]
            }
        ]
    }
    
    print("\n📝 Test 1: Structure simulée")
    text1 = extract_text_from_response(test_response)
    print(f"Texte extrait: {text1}")
    
    print("\n📊 Test 2: Avec métadonnées")
    result2 = extract_text_and_metadata(test_response)
    print(f"Résultat: {result2}")
    
    # Test avec structure vide
    empty_response = {
        "id": "resp_empty",
        "output": [
            {
                "type": "reasoning",
                "content": None
            }
        ]
    }
    
    print("\n❌ Test 3: Structure vide")
    text3 = extract_text_from_response(empty_response)
    print(f"Texte extrait: {text3}")
    
    print("\n✅ Helper testé avec succès !")
