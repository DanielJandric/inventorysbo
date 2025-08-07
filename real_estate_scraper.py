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

    async def find_and_scrape_listings(self, num_pages_to_scrape: int = 3):
        """
        Orchestre la recherche d'annonces sur les portails suisses, gère la pagination et sauvegarde les résultats.
        """
        logger.info(f"🏠 Lancement du scraping d'annonces sur {num_pages_to_scrape} pages...")
        base_search_url = "https://www.immoscout24.ch/fr/immeuble-habitation/acheter/pays-suisse"
        all_listing_urls = set()

        # Étape 1: Parcourir les pages de résultats pour collecter les URLs
        for page_num in range(1, num_pages_to_scrape + 1):
            logger.info(f"--- Scraping de la page de résultats n°{page_num} ---")
            search_url = f"{base_search_url}?pn={page_num}"
            listing_urls_on_page = await self._scrape_search_page(search_url)
            
            if not listing_urls_on_page:
                logger.warning(f"Aucune annonce trouvée sur la page {page_num}. Arrêt de la pagination.")
                break
            
            new_urls = set(listing_urls_on_page) - all_listing_urls
            if not new_urls:
                logger.info(f"Aucune nouvelle annonce trouvée sur la page {page_num}. Arrêt de la pagination.")
                break
                
            all_listing_urls.update(new_urls)
            logger.info(f"{len(new_urls)} nouvelles annonces ajoutées. Total: {len(all_listing_urls)}.")
            await asyncio.sleep(2) # Politesse envers le serveur

        if not all_listing_urls:
            logger.error("Aucune annonce n'a été trouvée sur l'ensemble des pages parcourues.")
            return

        # Étape 2: Scraper chaque annonce individuellement
        logger.info(f"Scraping des pages de recherche terminé. {len(all_listing_urls)} URLs uniques trouvées. Début du traitement individuel.")
        tasks = [self._scrape_and_process_listing(url, "immoscout24.ch") for url in all_listing_urls]
        await asyncio.gather(*tasks)
        logger.info("✅ Scraping immobilier terminé.")

    async def _scrape_search_page(self, url: str) -> List[str]:
        """Scrape une page de résultats pour en extraire les URLs des annonces avec BeautifulSoup."""
        logger.info(f"Scraping de la page de recherche: {url}")
        params = {
            'render_js': 'true',
            'wait': '7000', # Attendre 7 secondes pour être sûr que tout est chargé
        }
        html_content = await self.scraper._scrape_with_params(url, params)
        if not html_content:
            logger.warning("Le scraping de la page de recherche n'a retourné aucun contenu.")
            return []
        
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')
            # Ce sélecteur est très spécifique à ImmoScout24 et donc plus robuste
            links = soup.find_all('a', attrs={'data-testid': 'result-list-item-link'})
            found_urls = set()

            for link in links:
                href = link.get('href')
                if href and href.startswith('/fr/'):
                    full_url = f"https://www.immoscout24.ch{href}"
                    found_urls.add(full_url)
            
            if not found_urls:
                logger.warning("Aucune annonce trouvée sur la page avec le sélecteur 'data-testid'. Le HTML sera sauvegardé pour débogage.")
                with open("debug_real_estate_search_page.html", "w", encoding="utf-8") as f:
                    f.write(soup.prettify())
                logger.info("Contenu HTML de la page sauvegardé dans 'debug_real_estate_search_page.html'.")
            
            logger.info(f"{len(found_urls)} URLs trouvées sur la page.")
            return list(found_urls)

        except Exception as e:
            logger.error(f"Erreur lors du parsing HTML avec BeautifulSoup: {e}")
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

        # Étape de validation et filtrage
        is_yield_property = listing_data.get('is_yield_property', False)
        price = listing_data.get('price')

        if not is_yield_property:
            logger.info(f"Annonce {url} ignorée : n'est pas un immeuble de rendement.")
            return
        
        if price is None or price < 2000000:
            logger.info(f"Annonce {url} ignorée : prix ({price} CHF) inférieur à 2'000'000 CHF.")
            return

        logger.info(f"✅ Annonce validée : {listing_data.get('title')} à {price} CHF.")

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
        
        prompt = f\"\"\"
        Analyse le code HTML suivant d'une annonce immobilière suisse pour un immeuble de rendement.
        Extrait les informations suivantes et retourne-les dans un format JSON.
        - is_yield_property: Un booléen (`true` ou `false`). Mettre `true` si l'annonce est clairement un "immeuble de rendement", "immeuble locatif", ou "maison plurifamiliale". Mettre `false` s'il s'agit d'une simple maison ou d'un seul appartement.
        - title: Le titre principal de l'annonce.
        - location: La localité (ville ou village).
        - price: Le prix de vente en CHF (nombre entier, sans séparateurs). Si non trouvé, laisse null.
        - rental_income_yearly: Le revenu locatif annuel en CHF (nombre entier). Si non trouvé, laisse null.
        - number_of_apartments: Le nombre d'appartements dans l'immeuble (nombre entier).
        - image_url: L'URL de l'image principale de l'annonce (doit être une URL complète .jpg, .png, etc.).
        - description_summary: Un bref résumé de la description.

        HTML:
        {html_content[:12000]}
        \"\"\"
        
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
