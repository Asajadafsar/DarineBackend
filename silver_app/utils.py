import uuid
import logging
import jdatetime
import requests

from decimal import Decimal
from datetime import timedelta

from django.utils import timezone

from .models import SilverPriceHistory


logger = logging.getLogger(__name__)

from decimal import Decimal, ROUND_DOWN

def decimal_3(value):
    return Decimal(value).quantize(
        Decimal("0.001"),
        rounding=ROUND_DOWN
    )
# =========================================================
# SILVER PRICE
# =========================================================
def get_live_silver_price():
    url = (
        "https://api.noghresea.ir/"
        "api/market/getSilverPrice"
    )

    try:
        response = requests.get(url, timeout=10)

        if response.status_code != 200:
            logger.error(f"Silver API Error: {response.status_code}")
            return None

        data = response.json()

        raw_price = Decimal(str(data['price']))

        if raw_price <= 0:
            return None

        price = raw_price * 1000

    except Exception as e:
        logger.error(f"Silver Price Error: {str(e)}")
        return None

    # offset
    try:
        from admin_panel.models import SilverPriceOffset
        offset = SilverPriceOffset.objects.filter(
            is_active=True
        ).first()
        if offset:
            price = price + offset.offset_amount
    except Exception:
        pass

    return price





# =========================================================
# SAVE SILVER PRICE HISTORY
# =========================================================

def save_silver_price_history():
    price = get_live_silver_price()

    if not price:
        return False

    last = SilverPriceHistory.objects.order_by("-created_at").first()

    # اصلاح باگ: اگر قیمت تکراری بود ولی بیشتر از ۱ ساعت گذشته بود، حتماً ثبت کن
    if last and last.price == price:
        if timezone.now() - last.created_at < timedelta(hours=1):
            return True

    SilverPriceHistory.objects.create(price=price)
    return True


from datetime import timedelta
from django.utils import timezone


def calculate_silver_price_changes(current_price):

    now = timezone.now()

    day = (
        SilverPriceHistory.objects.filter(
            created_at__lte=now - timedelta(hours=24)
        )
        .order_by("-created_at")
        .first()
    )

    week = (
        SilverPriceHistory.objects.filter(
            created_at__lte=now - timedelta(days=7)
        )
        .order_by("-created_at")
        .first()
    )

    month = (
        SilverPriceHistory.objects.filter(
            created_at__lte=now - timedelta(days=30)
        )
        .order_by("-created_at")
        .first()
    )

    def calc(old):

        if old is None or current_price == 0:
            return 0

        return round(
            (
                (current_price - float(old.price))
                / current_price
            ) * 100,
            2
        )

    return {
        "daily": calc(day),
        "weekly": calc(week),
        "monthly": calc(month),
    }




# =========================================================
# SILVER CHART DATA
# =========================================================

from datetime import timedelta

from django.utils import timezone
from django.db.models import Avg
from django.db.models.functions import (
    TruncMinute,
    TruncHour,
    TruncDate
)

from .models import SilverPriceHistory

def get_silver_chart_data(filter_type="24H"):

    now = timezone.now()

    if filter_type == "24H":
        start_date = now - timedelta(hours=24)
        trunc_fn = TruncMinute

    elif filter_type == "WEEKLY":
        start_date = now - timedelta(days=7)
        trunc_fn = TruncHour

    else:
        start_date = now - timedelta(days=30)
        trunc_fn = TruncDate

    queryset = (
        SilverPriceHistory.objects
        .filter(created_at__gte=start_date)
        .annotate(
            period=trunc_fn(
                "created_at",
                tzinfo=timezone.get_current_timezone()
            )
        )
        .values("period")
        .annotate(avg_price=Avg("price"))
        .order_by("period")
    )

    labels = []
    prices = []

    for item in queryset:

        if item["avg_price"] is None:
            continue

        local_dt = timezone.localtime(item["period"])

        labels.append(
            local_dt.isoformat(timespec="seconds")
        )

        prices.append(
            int(item["avg_price"])
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
                "change_amount": 0,
                "daily_change_percent": 0,
                "weekly_change_percent": 0,
                "monthly_change_percent": 0,
                "min_y": 0,
                "max_y": 0
            }
        }

    current_price = prices[-1]
    highest_price = max(prices)
    lowest_price = min(prices)
    first_price = prices[0]

    changes = calculate_silver_price_changes(current_price)

    change_amount = current_price - first_price

    change_percent = (
        round(
            ((current_price - first_price) / first_price) * 100,
            2
        )
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
            "prices": prices
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
            "max_y": highest_price + padding
        }
    }



def get_silver_bubble():

    try:

        from gold_app.utils import get_world_prices

        world = get_world_prices()

        if not world:
            return None

        market_price = get_live_silver_price()

        if not market_price:
            return None

        intrinsic = (
            world["silver_ounce"]
            * world["usdt"]
        ) / Decimal("31.1035")

        bubble_amount = market_price - intrinsic

        bubble_percent = round(
            (
                bubble_amount
                / intrinsic
            ) * 100,
            2
        )

        return {

            "market_price": int(market_price),

            "intrinsic_price": int(intrinsic),

            "bubble_amount": int(bubble_amount),

            "bubble_percent": float(bubble_percent),

            "is_positive": bubble_amount > 0

        }

    except Exception as e:

        logger.error(e)

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

        "weight": round(weight, 3),

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

        "weight": round(weight, 3),

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