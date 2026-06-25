# gold_app/utils.py

import uuid
import logging
import requests
from decimal import Decimal, ROUND_DOWN
from decimal import Decimal
from datetime import timedelta

from django.utils import timezone

from .models import GoldPriceHistory


logger = logging.getLogger(__name__)

def round_gold(value):
    try:
        return float(
            Decimal(str(value)).quantize(
                Decimal("0.001"),
                rounding=ROUND_DOWN
            )
        )
    except:
        return 0
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

        price = Decimal(str(data['result']['price']))

    except Exception as e:
        logger.error(f"Gold Price Error: {str(e)}")
        return None

    # offset
    try:
        from admin_panel.models import GoldPriceOffset
        offset = GoldPriceOffset.objects.filter(
            is_active=True
        ).first()
        if offset:
            price = price + offset.offset_amount
    except Exception:
        pass

    return price
# =========================================================
# SAVE HISTORY
# =========================================================

def save_gold_price_history():
    price = get_live_gold_price()

    if price is None:
        return False

    last = GoldPriceHistory.objects.order_by("-created_at").first()

    # اگر قیمت تکراری بود و کمتر از 1 ساعت از ثبت قبلی گذشته بود، ثبت نکن
    if last and last.price == price:
        if timezone.now() - last.created_at < timedelta(hours=1):
            return True

    GoldPriceHistory.objects.create(price=price)
    return True
# =========================================================
# GOLD CHART DATA
# =========================================================


from django.db.models import Avg
from django.db.models.functions import TruncHour, TruncMinute, TruncDate

def get_gold_chart_data(filter_type='24H'):

    now = timezone.now()

    if filter_type == "24H":
        start_date = now - timedelta(hours=24)
        trunc_fn = TruncMinute
        label_format = "%H:%M"

    elif filter_type == "WEEKLY":
        start_date = now - timedelta(days=7)
        trunc_fn = TruncHour
        label_format = "%m/%d %H:%M"

    else:
        start_date = now - timedelta(days=30)
        trunc_fn = TruncDate
        label_format = "%m/%d"

    queryset = (
        GoldPriceHistory.objects
        .filter(created_at__gte=start_date)
        .annotate(period=trunc_fn('created_at', tzinfo=timezone.get_current_timezone()))
        .values('period')
        .annotate(avg_price=Avg('price'))
        .order_by('period')
    )

    labels = []
    prices = []

    for item in queryset:
        if item['avg_price'] is None:
            continue
        prices.append(int(item['avg_price']))
        labels.append(item['period'].strftime(label_format))

    if not prices:
        return {
            "chart": {"labels": [], "prices": []},
            "stats": {
                "current_price": 0,
                "highest_price": 0,
                "lowest_price": 0,
                "change_percent": 0,
                "change_amount": 0,
                "min_y": 0,
                "max_y": 0
            }
        }

    current_price = prices[-1]
    highest_price = max(prices)
    lowest_price = min(prices)
    first_price = prices[0]

    change_amount = current_price - first_price
    change_percent = round(
        ((current_price - first_price) / first_price) * 100, 2
    ) if first_price else 0

    price_range = highest_price - lowest_price
    padding = int(price_range * 0.1) if price_range else int(highest_price * 0.01)

    return {
        "chart": {
            "labels": labels,
            "prices": prices
        },
        "stats": {
            "current_price": current_price,
            "highest_price": highest_price,
            "lowest_price": lowest_price,
            "change_amount": change_amount,      # مقدار تغییر به تومان
            "change_percent": change_percent,     # درصد تغییر
            "min_y": max(0, lowest_price - padding),
            "max_y": highest_price + padding
        }
    }



def get_gold_bubble():
    try:
        # buy از get_live_gold_price میگیریم (چک manual میکنه)
        buy_price = get_live_gold_price()

        if not buy_price:
            return None

        # sell رو از API میگیریم
        sell_url = "https://api.wallgold.ir/api/v1/price?side=sell&symbol=GLD_18C_750TMN"
        sell_res = requests.get(sell_url, timeout=10)
        sell_data = sell_res.json()

        if not sell_data.get('success'):
            return None

        sell_price = Decimal(str(sell_data['result']['price']))

        bubble_amount = buy_price - sell_price
        bubble_percent = round(
            (bubble_amount / sell_price) * 100, 2
        )

        return {
            "buy_price": int(buy_price),
            "sell_price": int(sell_price),
            "bubble_amount": int(bubble_amount),
            "bubble_percent": float(bubble_percent),
            "is_positive": bubble_percent > 0,
        }

    except Exception as e:
        logger.error(f"Gold Bubble Error: {str(e)}")
        return None
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
            "price_per_gram": int(price),
            "weight": round_gold(weight),
            "fee": round(fee),
            "total_toman": round(total_toman)
        }

    weight = Decimal(str(weight_amount))
    base = weight * price
    fee = base * fee_rate
    total = base + fee

    return {
        "price_per_gram":  int(price),
        "weight": round_gold(weight),
        "fee": round(fee),
        "total_toman":  round(total)
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
    "price_per_gram": int(price_per_gram),
    "weight": round_gold(weight),
    "fee": round(fee),
    "final_amount": round(final_amount)
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