import requests
from decimal import Decimal

def get_live_silver_price():
    url = "https://api.noghresea.ir/api/market/getSilverPrice"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            # تبدیل به تومان برای محاسبات نقرینه
            price = Decimal(str(data['price']))
            return price * 1000  
    except Exception as e:
        print(f"Error fetching silver price: {e}")
    return None