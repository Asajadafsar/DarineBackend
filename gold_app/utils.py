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
    url = (
        "https://api.wallgold.ir/api/v1/"
        "price?side=buy&symbol=GLD_18C_750TMN"
    )

    try:
        response = requests.get(url, timeout=10)

        if response.status_code != 200:
            logger.error(f"Gold API Error: {response.status_code}")
            return None

        data = response.json()

        if not data.get('success'):
            logger.error("Gold API success=False")
            return None

        return Decimal(str(data['result']['price']))

    except Exception as e:
        logger.error(f"Gold Price Error: {str(e)}")
        return None


# =========================================================
# SAVE HISTORY
# =========================================================

def save_gold_price_history():
    price = get_live_gold_price()

    if price is None:
        return False

    last = GoldPriceHistory.objects.order_by("-created_at").first()

    if last and last.price == price:
        return True

    GoldPriceHistory.objects.create(price=price)
    return True


# =========================================================
# GOLD CHART DATA
# =========================================================

from django.db.models import Avg
from django.db.models.functions import TruncHour, TruncDate

from datetime import timedelta
from django.utils import timezone


def get_gold_chart_data(filter_type='24H'):

    now = timezone.now()

    if filter_type == "24H":
        start_date = now - timedelta(hours=24)

    elif filter_type == "WEEKLY":
        start_date = now - timedelta(days=7)

    else:
        start_date = now - timedelta(days=30)

    queryset = GoldPriceHistory.objects.filter(
        created_at__gte=start_date
    ).order_by("created_at")

    labels = []
    prices = []

    for item in queryset:

        prices.append(int(item.price))

        if filter_type == "24H":

            labels.append(
                item.created_at.strftime(
                    "%H:%M:%S"
                )
            )

        else:

            labels.append(
                item.created_at.strftime(
                    "%m/%d %H:%M"
                )
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
# BUY CALC (SAFE - NO UNPACK)
# =========================================================

def calculate_buy_gold(toman_amount=None, weight_amount=None, fee_rate=Decimal("0.01")):
    price = get_live_gold_price()

    if price is None:
        return None

    price = Decimal(price)

    if toman_amount is not None:

        total_toman = Decimal(str(toman_amount))
        fee = total_toman * fee_rate
        net = total_toman - fee
        weight = net / price

        return {
            "price_per_gram": price,
            "weight": float(weight),
            "fee": float(fee),
            "total_toman": float(total_toman)
        }

    weight = Decimal(str(weight_amount))
    base = weight * price
    fee = base * fee_rate
    total = base + fee

    return {
        "price_per_gram": price,
        "weight": float(weight),
        "fee": float(fee),
        "total_toman": float(total)
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

# 👇 گروه‌بندی جدید
PRICE_GROUPS = {
    "gold": ["gerami", "rob", "ons", "nim", "geram18", "geram24"],
    "coin": ["sekeb", "sekee"],
    "parsian": [],  # اگر API اضافه شد اینجا پر کن
}


def clean_number(value):
    if value is None:
        return 0

    value = re.sub(r"<.*?>", "", str(value))
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

        return {
            "type": key,
            "currentRate": clean_number(last[1]),
            "minPriceDay": clean_number(last[3]),
            "maxPriceDay": clean_number(last[2]),
            "dayChange": clean_number(last[4]),
            "percentChange": clean_percent(last[5]),
            "weeklyChart": rows[:7],
        }

    except Exception as e:
        logger.error(f"Price error: {str(e)}")
        return None


def get_group_prices(group_name: str):

    keys = PRICE_GROUPS.get(group_name)

    if keys is None:
        return None

    result = []

    for key in keys:
        data = get_latest_price(key)
        if data:
            result.append(data)

    return result