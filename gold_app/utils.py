# gold_app/utils.py

import uuid
import logging
import requests
from decimal import Decimal, ROUND_DOWN
from datetime import timedelta

from django.utils import timezone

from .models import GoldPriceHistory

logger = logging.getLogger(__name__)


def round_gold(value):
    try:
        return float(
            Decimal(str(value)).quantize(Decimal("0.001"), rounding=ROUND_DOWN)
        )
    except:
        return 0


ABAN_URL = "https://api.abantether.com/api/v2/manager/coins"

SILVER_OUNCE_URL = (
    "https://datalens.tickr.ir/api/v1/ohlc/ohlc/candlestick/"
    "?symbol=xag&currency=USDT&timeframe=5m&limit=1"
)


def get_world_prices():

    try:

        response = requests.get(ABAN_URL, timeout=10)
        response.raise_for_status()

        coins = response.json()["data"]

        usdt = None
        gold_ounce = None

        for coin in coins:

            symbol = coin["symbol"].upper()

            if symbol == "USDT":

                buy = Decimal(str(coin["price_buy"]))
                sell = Decimal(str(coin["price_sell"]))

                usdt = (buy + sell) / 2

            elif symbol == "XAUT":

                gold_ounce = Decimal(str(coin["tether_price"]))

        silver_res = requests.get(SILVER_OUNCE_URL, timeout=10)

        silver_res.raise_for_status()

        silver_json = silver_res.json()

        silver_ounce = Decimal(str(silver_json["data"][0]["close"]))

        return {
            "usdt": usdt,
            "gold_ounce": gold_ounce,
            "silver_ounce": silver_ounce,
        }

    except Exception as e:

        logger.error(e)

        return None


# =========================================================
# GOLD PRICE
# =========================================================


def get_live_gold_price():
    url = "https://api.wallgold.ir/api/v1/" "price?side=buy&symbol=GLD_18C_750TMN"

    try:
        response = requests.get(url, timeout=10)

        if response.status_code != 200:
            logger.error(f"Gold API Error: {response.status_code}")
            return None

        data = response.json()

        if not data.get("success"):
            logger.error("Gold API success=False")
            return None

        price = Decimal(str(data["result"]["price"]))

    except Exception as e:
        logger.error(f"Gold Price Error: {str(e)}")
        return None

    # offset
    try:
        from admin_panel.models import GoldPriceOffset

        offset = GoldPriceOffset.objects.filter(is_active=True).first()
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


def calculate_gold_price_changes(current_price):

    now = timezone.now()

    day = (
        GoldPriceHistory.objects.filter(created_at__lte=now - timedelta(hours=24))
        .order_by("-created_at")
        .first()
    )

    week = (
        GoldPriceHistory.objects.filter(created_at__lte=now - timedelta(days=7))
        .order_by("-created_at")
        .first()
    )

    month = (
        GoldPriceHistory.objects.filter(created_at__lte=now - timedelta(days=30))
        .order_by("-created_at")
        .first()
    )

    def calc(old):

        if old is None or current_price == 0:
            return 0

        return round(((current_price - float(old.price)) / current_price) * 100, 2)

    return {
        "daily": calc(day),
        "weekly": calc(week),
        "monthly": calc(month),
    }


# =========================================================
# GOLD CHART DATA
# =========================================================


from django.db.models import Avg
from django.db.models.functions import TruncHour, TruncMinute, TruncDate

from django.db.models import Avg
from django.db.models.functions import TruncHour, TruncMinute, TruncDate
from datetime import timedelta
from django.utils import timezone

from datetime import timedelta, datetime

from django.utils import timezone
from django.db.models import Avg
from django.db.models.functions import TruncHour, TruncDate

from .models import GoldPriceHistory
from .utils import calculate_gold_price_changes


def get_gold_chart_data(filter_type="24H"):

    now = timezone.now()
    current_tz = timezone.get_current_timezone()

    # =====================================================
    # TIME FRAME + GROUPING STRATEGY
    # =====================================================

    if filter_type == "24H":
        start_date = now - timedelta(hours=24)
        trunc_fn = TruncHour
        is_hourly = True

    elif filter_type == "WEEKLY":
        start_date = now - timedelta(days=7)
        trunc_fn = TruncHour   # 👈 اصلاح مهم

        is_hourly = True

    elif filter_type == "MONTHLY":
        start_date = now - timedelta(days=30)
        trunc_fn = TruncDate
        is_hourly = False

    else:
        start_date = now - timedelta(hours=24)
        trunc_fn = TruncHour
        is_hourly = True

    # =====================================================
    # QUERY
    # =====================================================

    queryset = (
        GoldPriceHistory.objects
        .filter(created_at__gte=start_date)
        .annotate(period=trunc_fn("created_at"))
        .values("period")
        .annotate(avg_price=Avg("price"))
        .order_by("period")
    )

    labels = []
    prices = []

    # =====================================================
    # FORMAT PERIOD (FIX TIMEZONE BUG)
    # =====================================================

    for item in queryset:

        if item["avg_price"] is None:
            continue

        period = item["period"]

        # -----------------------------
        # FIX: date vs datetime handling
        # -----------------------------
        if isinstance(period, datetime):

            if timezone.is_naive(period):
                period = timezone.make_aware(period, current_tz)
            else:
                period = timezone.localtime(period)

        else:
            # date -> datetime
            period = datetime.combine(period, datetime.min.time())
            period = timezone.make_aware(period, current_tz)

        # =================================================
        # LABEL FORMAT
        # =================================================

        if is_hourly:
            labels.append(period.isoformat(timespec="seconds"))
        else:
            labels.append(period.strftime("%Y-%m-%d"))

        prices.append(int(item["avg_price"]))

    # =====================================================
    # EMPTY SAFE RESPONSE
    # =====================================================

    if not prices:
        return {
            "chart": {
                "labels": [],
                "prices": [],
            },
            "stats": {
                "current_price": 0,
                "highest_price": 0,
                "lowest_price": 0,
                "change_amount": 0,
                "change_percent": 0,
                "daily_change_percent": 0,
                "weekly_change_percent": 0,
                "monthly_change_percent": 0,
                "min_y": 0,
                "max_y": 0,
            },
        }

    # =====================================================
    # STATS
    # =====================================================

    current_price = prices[-1]
    highest_price = max(prices)
    lowest_price = min(prices)
    first_price = prices[0]

    changes = calculate_gold_price_changes(current_price)

    change_amount = current_price - first_price

    change_percent = (
        round(((current_price - first_price) / first_price) * 100, 2)
        if first_price else 0
    )

    price_range = highest_price - lowest_price
    padding = (
        int(price_range * 0.1)
        if price_range
        else int(highest_price * 0.01)
    )

    return {
        "chart": {
            "labels": labels,
            "prices": prices,
        },
        "stats": {
            "current_price": current_price,
            "highest_price": highest_price,
            "lowest_price": lowest_price,
            "change_amount": change_amount,
            "change_percent": change_percent,
            "daily_change_percent": changes["daily"],
            "weekly_change_percent": changes["weekly"],
            "monthly_change_percent": changes["monthly"],
            "min_y": max(0, lowest_price - padding),
            "max_y": highest_price + padding,
        },
    }

def get_gold_bubble():

    try:

        world = get_world_prices()

        if not world:
            return None

        market_price = get_live_gold_price()

        if not market_price:
            return None

        intrinsic = (world["gold_ounce"] * world["usdt"] * Decimal("0.750")) / Decimal(
            "31.1035"
        )

        bubble_amount = market_price - intrinsic

        bubble_percent = round((bubble_amount / intrinsic) * 100, 2)

        return {
            "market_price": int(market_price),
            "intrinsic_price": int(intrinsic),
            "bubble_amount": int(bubble_amount),
            "bubble_percent": float(bubble_percent),
            "is_positive": bubble_amount > 0,
        }

    except Exception as e:

        logger.error(e)

        return None


# =========================================================
# FILTER DATE
# =========================================================


def filter_by_date(queryset, start_date=None, end_date=None):

    if start_date:

        queryset = queryset.filter(created_at__date__gte=start_date)

    if end_date:

        queryset = queryset.filter(created_at__date__lte=end_date)

    return queryset


# =========================================================
# FILTER STATUS
# =========================================================


def filter_by_status(queryset, status=None):

    if status:

        queryset = queryset.filter(status=status)

    return queryset


# =========================================================
# TRACKING CODE
# =========================================================


def generate_tracking_code(prefix="GLD"):

    random_part = str(uuid.uuid4()).split("-")[0]

    return f"{prefix}-" f"{random_part.upper()}"


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
            "total_toman": round(total_toman),
        }

    weight = Decimal(str(weight_amount))
    base = weight * price
    fee = base * fee_rate
    total = base + fee

    return {
        "price_per_gram": int(price),
        "weight": round_gold(weight),
        "fee": round(fee),
        "total_toman": round(total),
    }


# =========================================================
# SELL GOLD CALC
# =========================================================


def calculate_sell_gold(
    toman_amount=None, weight_amount=None, fee_rate=Decimal("0.01")
):

    price_per_gram = get_live_gold_price()

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
        "price_per_gram": int(price_per_gram),
        "weight": round_gold(weight),
        "fee": round(fee),
        "final_amount": round(final_amount),
    }


# =========================================================
# MONEY FORMAT
# =========================================================


def format_money(amount):

    try:

        return "{:,}".format(int(amount))

    except Exception:

        return "0"


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
