import os
import requests
from datetime import datetime, timedelta
import json

class NewsAPIManager:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv("NEWS_API_AI_KEY")
        if not self.api_key:
            raise ValueError("NewsAPI.ai API key not found. Please set the NEWS_API_AI_KEY environment variable.")
        self.base_url = "http://eventregistry.org/api/v1/article/getArticles"

    def get_real_estate_news(self):
        """
        Fetches real estate news articles from newsapi.ai based on a predefined query.
        """
        keywords = [
            "immobilier", "real estate", "immobilien", "taux d'intérêt", "interest rates",
            "zinssätze", "hypothèque", "mortgage", "PSP Swiss Property", "Swiss Prime Site",
            "Allreal", "Mobimo", "Investis Group", "fonds immobilier", "real estate fund",
            "immobilienfonds", "prix immobilier", "housing prices", "immobilienpreise",
            "logements vacants", "vacancy rate", "leerstand",
            "Suisse", "Switzerland"  # Add explicit location keywords
        ]

        request_params = {
            "action": "getArticles",
            "keyword": keywords,
            "keywordOper": "or",
            "lang": ["fra", "eng", "deu", "ita"],
            "dateStart": (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'),
            "dateEnd": datetime.now().strftime('%Y-%m-%d'),
            "dataType": ["news", "pr"],
            "articlesPage": 1,
            "articlesCount": 50,  # Increased to 50 to get a richer selection
            "articlesSortBy": "rel",
            "articlesSortByAsc": False,
            "articleBodyLen": -1,
            "isDuplicateFilter": "skipDuplicates",
            "resultType": "articles",
            "includeArticleTitle": True,
            "includeArticleBody": True,
            "includeArticleConcepts": True,
            "includeArticleSentiment": True,
            "apiKey": self.api_key
        }

        try:
            # Log the prepared request URL for debugging
            prepared_request = requests.Request('GET', self.base_url, params=request_params).prepare()
            print(f"DEBUG: Requesting URL: {prepared_request.url}")

            response = requests.get(self.base_url, params=request_params)
            response.raise_for_status()  # Raises an exception for bad status codes (4xx or 5xx)
            data = response.json()

            if 'articles' in data and 'results' in data['articles']:
                return data['articles']['results']
            else:
                # Log or handle cases where the structure is not as expected
                print(f"Warning: Unexpected API response structure from NewsAPI.ai: {data}")
                return []

        except requests.exceptions.RequestException as e:
            print(f"Error fetching news from NewsAPI.ai: {e}")
            return None
        except Exception as e:
            print(f"An unexpected error occurred in NewsAPIManager: {e}")
            return None


if __name__ == '__main__':
    # This allows for direct testing of the manager
    # Make sure to have a .env file with NEWS_API_AI_KEY="YOUR_KEY" in the root
    # or have the environment variable set.
    from dotenv import load_dotenv

    load_dotenv()

    manager = NewsAPIManager()
    articles = manager.get_real_estate_news()

    if articles:
        print(f"Successfully fetched {len(articles)} articles.")
        for i, article in enumerate(articles[:3]):  # Print first 3 articles for preview
            print(f"\n--- Article {i + 1} ---")
            print(f"Title: {article.get('title')}")
            print(f"Source: {article.get('source', {}).get('title')}")
            print(f"Date: {article.get('date')}")
            print(f"URL: {article.get('url')}")
            print(f"Body Preview: {article.get('body', '')[:200]}...")
    elif articles == []:
        print("API call successful, but no articles were returned.")
    else:
        print("Failed to fetch articles.")
