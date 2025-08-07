#!/usr/bin/env python3
"""
Scraper avancé pour les annonces d'immeubles de rendement sur ImmoScout24,
basé sur le code fourni par l'utilisateur.
"""

import os
import asyncio
import logging
from typing import List, Dict, Optional
from scrapingbee import ScrapingBeeClient # Synchrone par défaut, nous allons l'adapter.
import aiohttp # Pour des appels asynchrones
from bs4 import BeautifulSoup

from real_estate_db import RealEstateListing, get_real_estate_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ImmoScout24Scraper:
    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("La clé API ScrapingBee est requise.")
        self.api_key = api_key
        self.base_url = "https://www.immoscout24.ch/fr/immeuble-habitation/acheter/pays-suisse" # Recherche sur toute la suisse

    async def _send_scrapingbee_request(self, url: str, params: Dict) -> Optional[str]:
        """Envoie une requête asynchrone à ScrapingBee."""
        scraping_bee_url = "https://app.scrapingbee.com/api/v1/"
        
        # Les paramètres de base sont fusionnés avec les paramètres spécifiques
        base_params = {'api_key': self.api_key, 'url': url}
        final_params = {**base_params, **params}

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(scraping_bee_url, params=final_params, timeout=180) as response:
                    if response.status == 200:
                        return await response.text()
                    else:
                        response_text = await response.text()
                        logger.error(f"❌ Erreur ScrapingBee: {response.status}")
                        logger.error(f"URL: {url}")
                        logger.error(f"Réponse: {response_text}")
                        return None
        except Exception as e:
            logger.error(f"❌ Exception lors de l'appel à ScrapingBee pour {url}: {e}")
            return None

    async def scrape_page(self, page_num: int = 1) -> Optional[str]:
        """Scrape une page de résultats spécifique."""
        url = f"{self.base_url}?pn={page_num}"
        logger.info(f"Scraping de la page de résultats {page_num}: {url}")

        params = {
            'render_js': 'true',
            'premium_proxy': 'true',
            'country_code': 'ch',
            'wait': '5000',
            'wait_for': 'article[data-test="result-item"]',
            'js_scenario': '{"instructions":[{"wait":2000},{"click":"#onetrust-accept-btn-handler","optional":true},{"wait":1000},{"wait_for":"article[data-test=\\"result-item\\"]"},{"scroll":"bottom"},{"wait":2000}]}'
        }
        return await self._send_scrapingbee_request(url, params)

    def _parse_listing_summary(self, article_soup: BeautifulSoup) -> Optional[Dict]:
        """Extrait les données sommaires d'une annonce depuis la page de résultats."""
        try:
            title_elem = article_soup.find('h3', {'data-test': 'result-item-title'})
            price_elem = article_soup.find('span', {'data-test': 'result-item-price'})
            address_elem = article_soup.find('span', {'data-test': 'result-item-address'})
            link_elem = article_soup.find('a', {'data-test': 'result-item-link'})

            url = f"https://www.immoscout24.ch{link_elem['href']}" if link_elem and link_elem.get('href') else None
            if not url:
                return None
            
            price_text = price_elem.text.strip() if price_elem else "0"
            price = int("".join(filter(str.isdigit, price_text))) if "sur demande" not in price_text.lower() else 0

            # Filtrage initial par prix
            if price < 2000000:
                logger.info(f"Annonce ignorée (prix < 2M): {title_elem.text.strip() if title_elem else 'Sans titre'}")
                return None

            return {
                'source_url': url,
                'title': title_elem.text.strip() if title_elem else 'Titre non trouvé',
                'location': address_elem.text.strip() if address_elem else 'Lieu non trouvé',
                'price': price
            }
        except Exception as e:
            logger.error(f"Erreur lors du parsing d'une annonce sommaire: {e}")
            return None
    
    async def scrape_and_save_all(self, max_pages: int = 5):
        """
        Orchestre le scraping de plusieurs pages, le traitement et la sauvegarde en BDD.
        """
        db = get_real_estate_db()
        
        for page_num in range(1, max_pages + 1):
            html_content = await self.scrape_page(page_num)
            if not html_content:
                logger.error(f"Impossible de récupérer le contenu de la page {page_num}. Arrêt.")
                break

            soup = BeautifulSoup(html_content, 'html.parser')
            articles = soup.find_all('article', {'data-test': 'result-item'})

            if not articles:
                logger.info(f"Aucune annonce trouvée sur la page {page_num}, fin du scraping.")
                break
            
            logger.info(f"Trouvé {len(articles)} annonces sur la page {page_num}.")

            for article in articles:
                listing_summary = self._parse_listing_summary(article)
                if not listing_summary:
                    continue

                # Vérifier si l'annonce existe déjà avant de continuer
                if db.get_listing_by_url(listing_summary['source_url']):
                    logger.info(f"Annonce déjà en base : {listing_summary['source_url']}")
                    continue

                # Ici, on pourrait enrichir avec l'IA ou un scraping de détail, mais pour l'instant on sauvegarde les infos de base
                logger.info(f"Nouvelle annonce trouvée : {listing_summary['title']}")
                
                # Utiliser l'IA pour valider et enrichir
                listing_details = await self._extract_data_with_llm(listing_summary['source_url'])
                if not listing_details or not listing_details.get('is_yield_property'):
                    logger.info(f"Annonce ignorée par l'IA: {listing_summary['source_url']}")
                    continue
                
                # Fusionner les données et sauvegarder
                final_listing_data = {**listing_summary, **listing_details}
                listing = RealEstateListing(**final_listing_data)
                db.save_listing(listing)

                await asyncio.sleep(1) # Petite pause entre chaque annonce
            
            await asyncio.sleep(3) # Pause entre les pages

    async def _extract_data_with_llm(self, url: str) -> Optional[Dict]:
        """Scrape la page de détail et utilise l'IA pour extraire les données."""
        logger.info(f"Extraction par IA pour {url}")
        
        params = {'render_js': 'true', 'wait': '3000'}
        html_content = await self._send_scrapingbee_request(url, params)
        if not html_content:
            return None
            
        from openai import OpenAI
        client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        prompt_template = """
Analyse le code HTML d'une annonce ImmoScout24. Extrait les informations suivantes en JSON:
- is_yield_property: booléen, `true` si c'est un "immeuble de rendement", "locatif", ou "maison plurifamiliale".
- image_url: L'URL de l'image principale.
- description_summary: Résumé de la description.
- rental_income_yearly: Revenu locatif annuel (nombre entier).
- number_of_apartments: Nombre d'appartements (nombre entier).

HTML:
{html_data}
"""
        prompt = prompt_template.format(html_data=html_content[:15000])
        
        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )
            # Ajout d'un import json manquant
            import json
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            logger.error(f"Erreur d'extraction IA pour {url}: {e}")
            return None


# Point d'entrée pour le background worker
async def run_real_estate_scraper():
    logger.info("Lancement du scraper immobilier depuis le worker...")
    api_key = os.getenv("SCRAPINGBEE_API_KEY")
    if not api_key:
        logger.error("La variable d'environnement SCRAPINGBEE_API_KEY est manquante.")
        return
    
    scraper = ImmoScout24Scraper(api_key=api_key)
    await scraper.scrape_and_save_all(max_pages=5)
    logger.info("Scraping immobilier terminé.")

if __name__ == "__main__":
    # Pour des tests manuels
    asyncio.run(run_real_estate_scraper())
