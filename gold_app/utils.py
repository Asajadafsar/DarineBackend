# gold_app/utils.py

import uuid
import logging
import requests

from decimal import Decimal
from datetime import timedelta

from django.utils import timezone

from .models import GoldPriceHistory


logger = logging.getLogger(__name__)


# =========================================================
# GOLD PRICE
# =========================================================

def get_live_gold_price():

    """
    دریافت قیمت لحظه‌ای طلا
    """

    url = (
        "https://api.wallgold.ir/api/v1/"
        "price?side=buy&symbol=GLD_18C_750TMN"
    )

    try:

        response = requests.get(
            url,
            timeout=10
        )

        if response.status_code != 200:

            logger.error(
                f"Gold API Error: {response.status_code}"
            )

            return None

        data = response.json()

        if not data.get('success'):

            logger.error(
                "Gold API success=False"
            )

            return None

        price = Decimal(
            str(
                data['result']['price']
            )
        )

        return price

    except Exception as e:

        logger.error(
            f"Gold Price Error: {str(e)}"
        )

        return None


# =========================================================
# SILVER PRICE
# =========================================================

def get_live_silver_price():

    """
    دریافت قیمت نقره
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

        return price

    except Exception as e:

        logger.error(
            f"Silver Price Error: {str(e)}"
        )

        return None


# =========================================================
# SAVE GOLD PRICE HISTORY
# =========================================================

def save_gold_price_history():

    """
    ذخیره قیمت لحظه‌ای طلا
    """

    price = get_live_gold_price()

    if not price:
        return False

    GoldPriceHistory.objects.create(
        price=price
    )

    return True


# =========================================================
# GOLD CHART DATA
# =========================================================

def get_gold_chart_data(filter_type='24H'):

    from django.utils import timezone
    from datetime import timedelta

    now = timezone.now()

    # =========================================
    # FILTER
    # =========================================

    if filter_type == '24H':

        start_date = now - timedelta(hours=24)

        queryset = GoldPriceHistory.objects.filter(
            created_at__gte=start_date
        ).order_by('created_at')

        labels = [
            item.created_at.strftime('%H:%M')
            for item in queryset
        ]

    elif filter_type == 'WEEKLY':

        start_date = now - timedelta(days=7)

        queryset = GoldPriceHistory.objects.filter(
            created_at__gte=start_date
        ).order_by('created_at')

        labels = [
            item.created_at.strftime('%m/%d')
            for item in queryset
        ]

    else:

        start_date = now - timedelta(days=30)

        queryset = GoldPriceHistory.objects.filter(
            created_at__gte=start_date
        ).order_by('created_at')

        labels = [
            item.created_at.strftime('%m/%d')
            for item in queryset
        ]

    # =========================================
    # PRICES
    # =========================================

    prices = [
        int(item.price)
        for item in queryset
    ]

    # =========================================
    # EMPTY DATA
    # =========================================

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
                "change_percent": 0
            }
        }

    # =========================================
    # STATS
    # =========================================

    current_price = prices[-1]

    highest_price = max(prices)

    lowest_price = min(prices)

    first_price = prices[0]

    change_percent = round(
        (
            (current_price - first_price)
            / first_price
        ) * 100,
        2
    )

    # =========================================
    # RESPONSE
    # =========================================

    return {

        "chart": {

            "labels": labels,

            "prices": prices
        },

        "stats": {

            "current_price": current_price,

            "highest_price": highest_price,

            "lowest_price": lowest_price,

            "change_percent": change_percent
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
    prefix='GLD'
):

    random_part = str(
        uuid.uuid4()
    ).split('-')[0]

    return (
        f"{prefix}-"
        f"{random_part.upper()}"
    )


# =========================================================
# BUY GOLD CALC
# =========================================================

def calculate_buy_gold(
    toman_amount=None,
    weight_amount=None,
    fee_rate=Decimal('0.01')
):

    price_per_gram = (
        get_live_gold_price()
    )

    if not price_per_gram:
        return None

    if toman_amount:

        total_toman = Decimal(
            str(toman_amount)
        )

        fee = (
            total_toman * fee_rate
        )

        net_amount = (
            total_toman - fee
        )

        weight = (
            net_amount / price_per_gram
        )

    else:

        weight = Decimal(
            str(weight_amount)
        )

        pure_price = (
            weight * price_per_gram
        )

        fee = (
            pure_price * fee_rate
        )

        total_toman = (
            pure_price + fee
        )

    return {

        "price_per_gram": price_per_gram,

        "weight": round(
            weight,
            5
        ),

        "fee": round(fee),

        "total_toman": round(
            total_toman
        )
    }


# =========================================================
# SELL GOLD CALC
# =========================================================

def calculate_sell_gold(
    toman_amount=None,
    weight_amount=None,
    fee_rate=Decimal('0.01')
):

    price_per_gram = (
        get_live_gold_price()
    )

    if not price_per_gram:
        return None

    if toman_amount:

        total_toman = Decimal(
            str(toman_amount)
        )

        weight = (
            total_toman / price_per_gram
        )

        fee = (
            total_toman * fee_rate
        )

        final_amount = (
            total_toman - fee
        )

    else:

        weight = Decimal(
            str(weight_amount)
        )

        pure_price = (
            weight * price_per_gram
        )

        fee = (
            pure_price * fee_rate
        )

        final_amount = (
            pure_price - fee
        )

    return {

        "price_per_gram": price_per_gram,

        "weight": round(
            weight,
            5
        ),

        "fee": round(fee),

        "final_amount": round(
            final_amount
        )
    }


# =========================================================
# MONEY FORMAT
# =========================================================

def format_money(amount):

    try:

        return "{:,}".format(
            int(amount)
        )

    except Exception:

        return "0"
    











#GET API LIST
import requests
import logging
import re

logger = logging.getLogger(__name__)

PRICE_URLS = {
    "gerami": "https://prices.wallgold.ir/indicator/summary-table-data/gerami",
    "rob": "https://prices.wallgold.ir/indicator/summary-table-data/rob",
    "ons": "https://prices.wallgold.ir/indicator/summary-table-data/ons",
    "nim": "https://prices.wallgold.ir/indicator/summary-table-data/nim",
    "sekeb": "https://prices.wallgold.ir/indicator/summary-table-data/sekeb",
    "sekee": "https://prices.wallgold.ir/indicator/summary-table-data/sekee",
    "geram18": "https://prices.wallgold.ir/indicator/summary-table-data/geram18",
    "geram24": "https://prices.wallgold.ir/indicator/summary-table-data/geram24",
}


def clean_number(value):
    """حذف کاما و تبدیل به عدد"""
    if value is None:
        return 0

    value = re.sub(r"<.*?>", "", str(value))  # حذف span
    value = value.replace(",", "").strip()

    try:
        return float(value)
    except:
        return 0


def clean_percent(value):
    value = re.sub(r"<.*?>", "", str(value))
    value = value.replace("%", "").strip()
    try:
        return float(value)
    except:
        return 0


def get_latest_price(key: str):

    url = PRICE_URLS.get(key)
    if not url:
        return None

    try:
        res = requests.get(url, timeout=10)

        if res.status_code != 200:
            logger.error(f"Price API error: {res.status_code}")
            return None

        data = res.json()
        rows = data.get("data")

        if not rows:
            return None

        last = rows[0]

        buy = clean_number(last[0])
        sell = clean_number(last[1])
        high = clean_number(last[2])
        low = clean_number(last[3])
        change = clean_number(last[4])
        percent = clean_percent(last[5])

        return {
            "typeGold": key,
            "currentRate": sell,
            "minPriceDay": low,
            "maxPriceDay": high,
            "dayChange": change,
            "monthChange": percent,
            "weeklyChart": rows[:7],  # یا اگر خواستی جدا حرفه‌ای می‌کنیم
        }

    except Exception as e:
        logger.error(f"Price error: {str(e)}")
        return None