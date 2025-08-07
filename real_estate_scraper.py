#!/usr/bin/env python3
"""
Scraper pour les annonces immobilières suisses, spécialisé dans les immeubles de rendement.
"""

import os
import asyncio
import logging
import json
from typing import List, Dict, Optional
from scrapingbee_scraper import ScrapingBeeScraper
from real_estate_db import RealEstateListing, get_real_estate_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RealEstateScraper:
    def __init__(self):
        self.scraper = ScrapingBeeScraper()
        self.db = get_real_estate_db()

    async def find_and_scrape_listings(self):
        """
        Orchestre la recherche d'annonces sur les portails suisses et les sauvegarde.
        """
        logger.info("🏠 Lancement du scraping d'annonces immobilières...")
        # Pour commencer, nous allons cibler un site. On pourra en ajouter d'autres plus tard.
        # ImmoScout24 est un bon point de départ.
        search_url = "https://www.immoscout24.ch/fr/recherche/acheter/type-immeuble-de-rapport/pays-suisse"
        
        try:
            # Étape 1: Scraper la page de recherche pour trouver les URLs des annonces individuelles
            listing_urls = await self._scrape_search_page(search_url)
            
            if not listing_urls:
                logger.warning("Aucune annonce trouvée sur la page de recherche.")
                return

            logger.info(f"Trouvé {len(listing_urls)} annonces potentielles. Début du scraping individuel...")

            # Étape 2: Scraper chaque annonce individuellement
            for url in listing_urls:
                await self._scrape_and_process_listing(url, "immoscout24.ch")

        except Exception as e:
            logger.error(f"Erreur majeure lors du scraping immobilier: {e}")

    async def _scrape_search_page(self, url: str) -> List[str]:
        """Scrape une page de résultats pour en extraire les URLs des annonces."""
        html_content = await self.scraper._scrape_page(url)
        if not html_content:
            return []
        
        # Utiliser l'IA pour extraire les URLs des annonces de manière fiable
        from openai import OpenAI
        client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

        prompt = f"""
        Extrait toutes les URLs des annonces individuelles de ce code HTML.
        Ne retourne QUE les URLs pointant vers des annonces, pas les liens de navigation ou de publicité.
        Les URLs doivent être complètes (commençant par https://).
        
        HTML:
        {html_content[:8000]}
        
        Réponds uniquement avec un objet JSON contenant une clé "urls" avec la liste des URLs.
        Exemple de réponse: {{"urls": ["https://.../annonce1", "https://.../annonce2"]}}
        """
        
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )
            data = json.loads(response.choices[0].message.content)
            return data.get("urls", [])
        except Exception as e:
            logger.error(f"Erreur d'extraction d'URL par IA: {e}")
            return []

    async def _scrape_and_process_listing(self, url: str, source_site: str):
        """Scrape une annonce, l'analyse avec l'IA et la sauvegarde en BDD."""
        logger.info(f"Scraping de l'annonce : {url}")
        
        # Vérifier si l'annonce existe déjà pour éviter un scraping inutile
        if self.db.supabase.table('real_estate_listings').select('id').eq('source_url', url).execute().data:
            logger.info(f"Annonce déjà en base de données. Saut.")
            return

        html_content = await self.scraper._scrape_page(url)
        if not html_content:
            logger.warning(f"Impossible de scraper le contenu de {url}")
            return

        # Utiliser l'IA pour extraire les informations structurées
        listing_data = await self._extract_data_with_llm(html_content)

        if not listing_data:
            logger.warning(f"Impossible d'extraire les données de {url} via l'IA.")
            return

        # Créer l'objet et le sauvegarder
        listing = RealEstateListing(
            source_url=url,
            source_site=source_site,
            **listing_data
        )
        self.db.save_listing(listing)

    async def _extract_data_with_llm(self, html_content: str) -> Optional[Dict]:
        """Utilise GPT-4o pour extraire les données structurées d'une annonce."""
        from openai import OpenAI
        client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        prompt = f"""
        Analyse le code HTML suivant d'une annonce immobilière suisse pour un immeuble de rendement.
        Extrait les informations suivantes et retourne-les dans un format JSON.
        - title: Le titre principal de l'annonce.
        - location: La localité (ville ou village).
        - price: Le prix de vente en CHF (nombre entier, sans séparateurs). Si non trouvé, laisse null.
        - rental_income_yearly: Le revenu locatif annuel en CHF (nombre entier). Si non trouvé, laisse null.
        - number_of_apartments: Le nombre d'appartements dans l'immeuble (nombre entier).
        - image_url: L'URL de l'image principale de l'annonce (doit être une URL complète .jpg, .png, etc.).
        - description_summary: Un bref résumé de la description.

        HTML:
        {html_content[:12000]}
        """
        
        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            logger.error(f"Erreur d'extraction de données par l'IA: {e}")
            return None

async def main():
    """Fonction principale pour tester le scraper."""
    scraper = RealEstateScraper()
    await scraper.find_and_scrape_listings()

if __name__ == "__main__":
    asyncio.run(main())
