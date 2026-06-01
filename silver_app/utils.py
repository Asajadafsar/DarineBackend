import uuid
import logging
import requests

from decimal import Decimal
from datetime import timedelta

from django.utils import timezone

from .models import SilverPriceHistory


logger = logging.getLogger(__name__)


# =========================================================
# SILVER PRICE
# =========================================================

def get_live_silver_price():
    """
    دریافت قیمت لحظه‌ای نقره
    """

    url = (
        "https://api.noghresea.ir/"
        "api/market/getSilverPrice"
    )

    try:

        response = requests.get(
            url,
            timeout=10
        )

        if response.status_code != 200:

            logger.error(
                f"Silver API Error: {response.status_code}"
            )

            return None

        data = response.json()

        price = Decimal(
            str(
                data['price']
            )
        )

        if price <= 0:

            logger.error("Invalid Silver Price")

            return None

        return price

    except Exception as e:

        logger.error(
            f"Silver Price Error: {str(e)}"
        )

        return None


# =========================================================
# SAVE SILVER PRICE HISTORY
# =========================================================

def save_silver_price_history():

    price = get_live_silver_price()

    if not price:
        return False

    last = SilverPriceHistory.objects.order_by(
        "-created_at"
    ).first()

    if last and last.price == price:
        return True

    SilverPriceHistory.objects.create(
        price=price
    )

    return True


# =========================================================
# SILVER CHART DATA
# =========================================================

def get_silver_chart_data(filter_type='24H'):

    now = timezone.now()

    if filter_type == "24H":
        start_date = now - timedelta(hours=24)

    elif filter_type == "WEEKLY":
        start_date = now - timedelta(days=7)

    else:
        start_date = now - timedelta(days=30)

    queryset = SilverPriceHistory.objects.filter(
        created_at__gte=start_date
    ).order_by("created_at")

    labels = []
    prices = []

    for item in queryset:

        prices.append(int(item.price))

        if filter_type == "24H":

            labels.append(
                item.created_at.strftime("%H:%M:%S")
            )

        else:

            labels.append(
                item.created_at.strftime("%m/%d %H:%M")
            )

    if not prices:

        return {
            "chart": {
                "labels": [],
                "prices": []
            },
            "stats": {
                "current_price": 0,
                "highest_price": 0,
                "lowest_price": 0,
                "change_percent": 0,
                "min_y": 0,
                "max_y": 0
            }
        }

    current_price = prices[-1]
    highest_price = max(prices)
    lowest_price = min(prices)
    first_price = prices[0]

    change_percent = round(
        ((current_price - first_price) / first_price) * 100,
        2
    )

    return {

        "chart": {
            "labels": labels,
            "prices": prices
        },

        "stats": {

            "current_price": current_price,
            "highest_price": highest_price,
            "lowest_price": lowest_price,
            "change_percent": change_percent,
            "min_y": lowest_price,
            "max_y": highest_price
        }
    }


# =========================================================
# FILTER DATE
# =========================================================

def filter_by_date(
    queryset,
    start_date=None,
    end_date=None
):

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
# FILTER STATUS
# =========================================================

def filter_by_status(
    queryset,
    status=None
):

    if status:

        queryset = queryset.filter(
            status=status
        )

    return queryset


# =========================================================
# TRACKING CODE
# =========================================================

def generate_tracking_code(
    prefix='SLV'
):

    random_part = str(
        uuid.uuid4()
    ).split('-')[0]

    return (
        f"{prefix}-"
        f"{random_part.upper()}"
    )


# =========================================================
# BUY SILVER CALC
# =========================================================

def calculate_buy_silver(
    toman_amount=None,
    weight_amount=None,
    fee_rate=Decimal('0.01')
):

    price_per_gram = get_live_silver_price()

    if not price_per_gram:
        return None

    if toman_amount:

        total_toman = Decimal(str(toman_amount))

        fee = total_toman * fee_rate

        net_amount = total_toman - fee

        weight = net_amount / price_per_gram

    else:

        weight = Decimal(str(weight_amount))

        pure_price = weight * price_per_gram

        fee = pure_price * fee_rate

        total_toman = pure_price + fee

    return {

        "price_per_gram": price_per_gram,

        "weight": round(weight, 5),

        "fee": round(fee),

        "total_toman": round(total_toman)
    }


# =========================================================
# SELL SILVER CALC
# =========================================================

def calculate_sell_silver(
    toman_amount=None,
    weight_amount=None,
    fee_rate=Decimal('0.01')
):

    price_per_gram = get_live_silver_price()

    if not price_per_gram:
        return None

    if toman_amount:

        total_toman = Decimal(str(toman_amount))

        weight = total_toman / price_per_gram

        fee = total_toman * fee_rate

        final_amount = total_toman - fee

    else:

        weight = Decimal(str(weight_amount))

        pure_price = weight * price_per_gram

        fee = pure_price * fee_rate

        final_amount = pure_price - fee

    return {

        "price_per_gram": price_per_gram,

        "weight": round(weight, 5),

        "fee": round(fee),

        "final_amount": round(final_amount)
    }


# =========================================================
# MONEY FORMAT
# =========================================================

def format_money(amount):

    try:
        return "{:,}".format(int(amount))

    except Exception:
        return "0"