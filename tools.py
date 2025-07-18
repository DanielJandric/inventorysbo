# tools.py

import logging

logger = logging.getLogger(__name__)

class ToolBox:
    """
    Contient tous les outils que l'agent IA peut décider d'utiliser.
    Chaque outil est une fonction Python qui effectue une tâche spécifique,
    comme récupérer des données de la collection.
    """

    def __init__(self, data_manager):
        """
        Initialise la boîte à outils avec un accès au gestionnaire de données.
        """
        self.data_manager = data_manager
        # Connaissance du domaine, centralisée ici
        self.domain_knowledge = {
            'voitures': {
                'marques': {
                    'italiennes': ['ferrari', 'lamborghini', 'maserati', 'alfa romeo', 'pagani'],
                    'allemandes': ['porsche', 'bmw', 'mercedes', 'audi', 'vw', 'volkswagen'],
                    'anglaises': ['rolls', 'bentley', 'aston martin', 'mclaren', 'jaguar'],
                    'françaises': ['bugatti', 'peugeot', 'citroën', 'renault']
                },
                'attributs': {
                    '2 places': ['gt3', 'gt ranks', 'dakar', 'targa', 'turbo s', 'essenza', 'revuelto', 'aventador', 'diablo', 'evo', 'spider'],
                    'suv': ['macan', 'urus', 'purosangue', 'cayenne', 'g-class'],
                    '4 places': ['taycan', 'panamera', 'rs6', 'm5']
                }
            }
        }

    def fetch_collection_items(self, filters: dict) -> list:
        """
        Outil pour rechercher et filtrer des objets dans la collection.
        :param filters: Un dictionnaire de filtres à appliquer.
                        Exemple: {"category": "Voitures", "brand_origin": "allemandes", "for_sale": True}
        :return: Une liste d'objets (dictionnaires) correspondant aux filtres.
        """
        logger.info(f"Outil 'fetch_collection_items' appelé avec les filtres : {filters}")
        all_items = self.data_manager.fetch_all_items()
        
        filtered_items = all_items

        # Filtre par catégorie
        if 'category' in filters:
            filtered_items = [item for item in filtered_items if item.category == filters['category']]
        
        # Filtre par origine de marque
        if 'brand_origin' in filters:
            origin = filters['brand_origin']
            brands_to_check = self.domain_knowledge.get('voitures', {}).get('marques', {}).get(origin, [])
            if brands_to_check:
                filtered_items = [item for item in filtered_items if any(brand in item.name.lower() for brand in brands_to_check)]
        
        # Filtre par attribut (ex: 2 places)
        if 'attribute' in filters:
            attribute = filters['attribute']
            keywords_to_check = self.domain_knowledge.get('voitures', {}).get('attributs', {}).get(attribute, [])
            if keywords_to_check:
                filtered_items = [item for item in filtered_items if any(keyword in item.name.lower() for keyword in keywords_to_check)]

        # Filtre par statut "en vente"
        if filters.get('for_sale') is True:
            filtered_items = [item for item in filtered_items if item.for_sale is True]

        logger.info(f"{len(filtered_items)} objets trouvés après filtrage.")
        # Retourne une version concise pour limiter la taille du contexte
        return [item.to_dict() for item in filtered_items]

    def get_available_tools(self):
        """Retourne une description des outils disponibles pour l'IA."""
        return [
            {
                "name": "fetch_collection_items",
                "description": "Recherche et filtre des objets dans la collection privée. A utiliser pour répondre à des questions sur le nombre, la liste, ou les détails d'objets spécifiques (voitures, montres, etc.).",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "category": {"type": "string", "description": "La catégorie d'objet à rechercher (ex: 'Voitures', 'Montres')."},
                        "brand_origin": {"type": "string", "description": "Le pays d'origine de la marque pour les voitures (ex: 'italiennes', 'allemandes')."},
                        "attribute": {"type": "string", "description": "Une caractéristique spécifique de l'objet (ex: '2 places', 'suv')."},
                        "for_sale": {"type": "boolean", "description": "Mettre à True pour ne chercher que les objets en vente."}
                    }
                }
            }
            # ... on pourrait ajouter d'autres outils ici
        ]
