import os
import requests
from dotenv import load_dotenv

load_dotenv()

RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY_SEEKING_ALPHA")
RAPIDAPI_HOST = "seeking-alpha.p.rapidapi.com"

def logout():
    """
    Logs out from the Seeking Alpha API.
    """
    url = f"https://{RAPIDAPI_HOST}/accounts/logout"
    headers = {
        "x-rapidapi-host": RAPIDAPI_HOST,
        "x-rapidapi-key": RAPIDAPI_KEY
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise an exception for bad status codes
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return None

def get_movers(region: str = "US"):
    """
    Get market movers from the Seeking Alpha API.
    """
    url = f"https://{RAPIDAPI_HOST}/market/get-movers"
    headers = {
        "x-rapidapi-host": RAPIDAPI_HOST,
        "x-rapidapi-key": RAPIDAPI_KEY
    }
    params = {"region": region}
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return None

def get_stock_statistics(symbol: str):
    """
    Get statistics for a stock from the Seeking Alpha API.
    """
    url = f"https://{RAPIDAPI_HOST}/stock/get-statistics"
    headers = {
        "x-rapidapi-host": RAPIDAPI_HOST,
        "x-rapidapi-key": RAPIDAPI_KEY
    }
    params = {"symbol": symbol}
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return None

def get_news():
    """
    Get news from the Seeking Alpha API.
    """
    url = f"https://{RAPIDAPI_HOST}/news/list"
    headers = {
        "x-rapidapi-host": RAPIDAPI_HOST,
        "x-rapidapi-key": RAPIDAPI_KEY
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return None

def get_market_summary(region: str = "US"):
    """
    Get market summary from the Seeking Alpha API.
    """
    url = f"https://{RAPIDAPI_HOST}/market/get-summary"
    headers = {
        "x-rapidapi-host": RAPIDAPI_HOST,
        "x-rapidapi-key": RAPIDAPI_KEY
    }
    params = {"region": region}
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return None

def get_price_chart(id: str, interval: str = "d1"):
    """Get price chart/ticks for an instrument to draw sparklines."""
    url = f"https://{RAPIDAPI_HOST}/market/get-price-chart"
    headers = {
        "x-rapidapi-host": RAPIDAPI_HOST,
        "x-rapidapi-key": RAPIDAPI_KEY
    }
    params = {"id": id, "interval": interval}
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return None





if __name__ == '__main__':
    # Example usage:
    logout_response = logout()
    if logout_response:
        print("Logout successful:", logout_response)
    else:
        print("Logout failed.")

