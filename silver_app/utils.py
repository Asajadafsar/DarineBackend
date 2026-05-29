# silver_app/utils.py

import random
import string
import requests

from decimal import Decimal, InvalidOperation
from django.core.cache import cache

from silver_app.models import SilverPriceHistory


# =========================================================
# LIVE SILVER PRICE
# =========================================================

def get_live_silver_price():

    cache_key = "silver_price"

    cached = cache.get(cache_key)

    if cached is not None:
        return cached

    url = "https://api.noghresea.ir/api/market/getSilverPrice"

    try:

        res = requests.get(url, timeout=5)

        if res.status_code != 200:
            return get_fallback_price()

        data = res.json()

        if "price" not in data:
            return get_fallback_price()

        try:
            price = Decimal(str(data["price"])) * Decimal("1000")

        except (InvalidOperation, TypeError):
            return get_fallback_price()

        cache.set(cache_key, price, timeout=60)

        return price

    except requests.RequestException:
        return get_fallback_price()


# =========================================================
# FALLBACK PRICE
# =========================================================

def get_fallback_price():

    try:

        last = SilverPriceHistory.objects.order_by(
            "-created_at"
        ).first()

        if last:
            return Decimal(str(last.price))

    except Exception:
        pass

    return Decimal("0")


# =========================================================
# GENERATE TRACKING CODE
# =========================================================

def generate_tracking_code(prefix="SLV"):

    random_part = ''.join(
        random.choices(
            string.ascii_uppercase + string.digits,
            k=10
        )
    )

    return f"{prefix}-{random_part}"


# =========================================================
# SILVER CHART DATA
# =========================================================

def get_silver_chart_data(filter_type='24H'):

    queryset = SilverPriceHistory.objects.order_by(
        '-created_at'
    )

    if filter_type == '24H':
        queryset = queryset[:24]

    elif filter_type == '7D':
        queryset = queryset[:7]

    elif filter_type == '30D':
        queryset = queryset[:30]

    elif filter_type == '1Y':
        queryset = queryset[:365]

    queryset = reversed(queryset)

    data = []

    for item in queryset:

        data.append({
            "price": item.price,
            "created_at": item.created_at
        })

    return data


# =========================================================
# FILTER BY DATE
# =========================================================

def filter_by_date(queryset, start_date=None, end_date=None):

    if start_date:
        queryset = queryset.filter(
            created_at__date__gte=start_date
        )

    if end_date:
        queryset = queryset.filter(
            created_at__date__lte=end_date
        )

    return queryset


# =========================================================
# FILTER BY STATUS
# =========================================================

def filter_by_status(queryset, status_value=None):

    if status_value:
        queryset = queryset.filter(
            status=status_value
        )

    return queryset