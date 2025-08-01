import requests
from decimal import Decimal

def get_current_price(coin_id):
    """
    Fetch current price for a given coin_id (e.g., 'bitcoin', 'ethereum') from CoinGecko.
    Returns Decimal price or raises exception if failed.
    """
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd"

    try:
        response = requests.get(url)
        data = response.json()
        price = data[coin_id]['usd']
        return Decimal(str(price))
    except Exception as e:
        raise Exception(f"Failed to fetch price for {coin_id}: {e}")
