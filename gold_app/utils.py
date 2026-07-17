# gold_app/utils.py

import uuid
import logging
import requests
from decimal import Decimal, ROUND_DOWN
from datetime import timedelta

from django.utils import timezone

from .models import GoldPriceHistory

logger = logging.getLogger(__name__)
# gold_app/utils.py - اضافه کردن به ابتدای فایل

from rest_framework.response import Response


def success_response(message="", data=None, status_code=200):
    return Response(
        {"success": True, "message": message, "data": data},
        status=status_code
    )


def error_response(message="اطلاعات نامعتبر است", errors=None, status_code=400):
    formatted_errors = []
    if errors:
        for field, msgs in errors.items():
            for msg in msgs:
                formatted_errors.append({"field": field, "message": msg})
        message = "، ".join([f"{item['message']}" for item in formatted_errors])
    
    return Response(
        {"success": False, "message": message, "errors": formatted_errors},
        status=status_code
    )

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


# def get_live_gold_price():
#     url = "https://api.wallgold.ir/api/v1/" "price?side=buy&symbol=GLD_18C_750TMN"

#     try:
#         response = requests.get(url, timeout=10)

#         if response.status_code != 200:
#             logger.error(f"Gold API Error: {response.status_code}")
#             return None

#         data = response.json()

#         if not data.get("success"):
#             logger.error("Gold API success=False")
#             return None

#         price = Decimal(str(data["result"]["price"]))

#     except Exception as e:
#         logger.error(f"Gold Price Error: {str(e)}")
#         return None

#     # offset
#     try:
#         from admin_panel.models import GoldPriceOffset

#         offset = GoldPriceOffset.objects.filter(is_active=True).first()
#         if offset:
#             price = price + offset.offset_amount
#     except Exception:
#         pass

#     return price


# gold_app/utils.py

from django.core.cache import cache

# gold_app/utils.py

# gold_app/utils.py

import time
import logging
import requests
import json
import os
from decimal import Decimal
from django.conf import settings

logger = logging.getLogger(__name__)


# =========================================================
# CACHE FILE PATH
# =========================================================

CACHE_DIR = os.path.join(settings.BASE_DIR, 'cache')
os.makedirs(CACHE_DIR, exist_ok=True)

GOLD_CACHE_FILE = os.path.join(CACHE_DIR, 'gold_price.json')
GOLD_CACHE_TIME_FILE = os.path.join(CACHE_DIR, 'gold_price_time.json')


# =========================================================
# READ/WRITE CACHE FUNCTIONS
# =========================================================

def read_cache(file_path):
    """خواندن از کش فایل"""
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"Cache read error: {e}")
    return None


def write_cache(file_path, data):
    """نوشتن در کش فایل"""
    try:
        with open(file_path, 'w') as f:
            json.dump(data, f)
    except Exception as e:
        logger.error(f"Cache write error: {e}")


# =========================================================
# GOLD PRICE WITH FILE CACHE (30 SECONDS)
# =========================================================

def get_live_gold_price():
    """
    دریافت قیمت لحظه‌ای طلا با کش ۳۰ ثانیه‌ای (ذخیره در فایل)
    هر ۳۰ ثانیه یک بار از API دریافت می‌شود
    """
    # ✅ خواندن از کش فایل
    cached_price = read_cache(GOLD_CACHE_FILE)
    cached_time = read_cache(GOLD_CACHE_TIME_FILE)
    
    now = time.time()
    
    # ✅ اگر کمتر از ۳۰ ثانیه گذشته، از کش برگردان
    if cached_time and cached_price:
        elapsed = now - cached_time
        if elapsed < 30:
            return Decimal(str(cached_price))
    
    # ✅ دریافت از API
    url = "https://api.wallgold.ir/api/v1/price?side=buy&symbol=GLD_18C_750TMN"

    try:
        response = requests.get(url, timeout=10)

        if response.status_code != 200:
            logger.error(f"Gold API Error: {response.status_code}")
            if cached_price is not None:
                return Decimal(str(cached_price))
            return None

        data = response.json()

        if not data.get("success"):
            logger.error("Gold API success=False")
            if cached_price is not None:
                return Decimal(str(cached_price))
            return None

        price = Decimal(str(data["result"]["price"]))

    except Exception as e:
        logger.error(f"Gold Price Error: {str(e)}")
        if cached_price is not None:
            return Decimal(str(cached_price))
        return None

    # ✅ اعمال آفست
    try:
        from admin_panel.models import GoldPriceOffset
        offset = GoldPriceOffset.objects.filter(is_active=True).first()
        if offset:
            price = price + offset.offset_amount
    except Exception:
        pass

    # ✅ ذخیره در کش فایل
    write_cache(GOLD_CACHE_FILE, float(price))
    write_cache(GOLD_CACHE_TIME_FILE, now)

    return price


def force_refresh_gold_price():
    """دریافت قیمت طلا بدون استفاده از کش"""
    # حذف فایل‌های کش
    for file_path in [GOLD_CACHE_FILE, GOLD_CACHE_TIME_FILE]:
        if os.path.exists(file_path):
            os.remove(file_path)
    return get_live_gold_price()


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





# gold_app/utils.py

from decimal import Decimal, ROUND_DOWN
from django.db import transaction
from .models import GoldOrder, GoldTransaction, Wallet, GoldInventory
from accounts.utils import create_referral_profit


# gold_app/utils.py

def check_and_execute_limit_orders():
    """
    تابعی که هر دقیقه اجرا میشه و سفارشات در انتظار رو چک میکنه
    ✅ سفارشات با قیمت رفرال ندارند
    """
    from .models import GoldOrder, GoldTransaction, Wallet, GoldInventory
    from decimal import Decimal, ROUND_DOWN
    
    pending_orders = GoldOrder.objects.filter(status='PENDING')
    
    if not pending_orders.exists():
        return 0
    
    executed_count = 0
    
    for order in pending_orders:
        current_price = get_live_gold_price()
        if not current_price:
            continue
        
        current_price = Decimal(str(current_price))
        
        should_execute = False
        
        if order.order_type == 'BUY':
            # ✅ خرید: قیمت فعلی <= قیمت هدف
            if current_price <= order.target_price:
                should_execute = True
        else:  # SELL
            # ✅ فروش: قیمت فعلی >= قیمت هدف
            if current_price >= order.target_price:
                should_execute = True
        
        if should_execute:
            try:
                with transaction.atomic():
                    _execute_order(order, current_price)
                    executed_count += 1
                    logger.info(f"✅ سفارش {order.id} خودکار اجرا شد - قیمت: {current_price}")
            except Exception as e:
                logger.error(f"❌ خطا در اجرای سفارش {order.id}: {e}")
    
    return executed_count


def _execute_order(order, current_price):
    """
    اجرای یک سفارش با قیمت
    ❌ بدون رفرال
    """
    from .models import GoldTransaction, Wallet, GoldInventory
    from decimal import Decimal, ROUND_DOWN
    
    if order.order_type == 'BUY':
        wallet, _ = Wallet.objects.select_for_update().get_or_create(user=order.user)
        inventory, _ = GoldInventory.objects.select_for_update().get_or_create(user=order.user)

        fee_rate = Decimal(str(order.fee_rate))
        pure_price = (order.amount_toman / (Decimal("1") + fee_rate)).quantize(Decimal("1"))
        fee = (order.amount_toman - pure_price).quantize(Decimal("1"))
        weight = (pure_price / current_price).quantize(Decimal("0.001"), rounding=ROUND_DOWN)

        if wallet.blocked_toman < order.amount_toman:
            logger.error(f"❌ موجودی بلوکه شده برای سفارش {order.id} کافی نیست")
            return

        wallet.blocked_toman -= order.amount_toman
        wallet.save(update_fields=['blocked_toman'])

        inventory.accessible_balance += weight
        inventory.save(update_fields=['accessible_balance'])

        GoldTransaction.objects.create(
            user=order.user,
            type='BUY',
            status='COMPLETED',
            amount_gr=weight,
            price_per_gram=current_price,
            fee=fee,
            commission_percent=fee_rate * 100,
            commission_amount=fee,
            total_amount=order.amount_toman,
            tracking_code=generate_tracking_code('BUY'),
            description=f"✅ اجرای خودکار سفارش با قیمت {order.target_price} - {order.description or ''}"
        )

        # ❌ بدون رفرال برای سفارش با قیمت

        order.status = 'EXECUTED'
        order.executed_price = current_price
        order.estimated_weight = weight
        order.save(update_fields=['status', 'executed_price', 'estimated_weight', 'updated_at'])

    else:  # SELL
        wallet, _ = Wallet.objects.select_for_update().get_or_create(user=order.user)
        inventory, _ = GoldInventory.objects.select_for_update().get_or_create(user=order.user)

        if inventory.blocked_balance < order.gold_weight:
            logger.error(f"❌ موجودی بلوکه شده طلا برای سفارش {order.id} کافی نیست")
            return

        inventory.blocked_balance -= order.gold_weight
        inventory.save(update_fields=['blocked_balance'])

        fee_rate = Decimal(str(order.fee_rate))
        pure_price = (current_price * order.gold_weight).quantize(Decimal("1"))
        fee = (pure_price * fee_rate).quantize(Decimal("1"))
        total_price = (pure_price - fee).quantize(Decimal("1"))

        wallet.accessible_toman += total_price
        wallet.save(update_fields=['accessible_toman'])

        GoldTransaction.objects.create(
            user=order.user,
            type='SELL',
            status='COMPLETED',
            amount_gr=order.gold_weight,
            price_per_gram=current_price,
            fee=fee,
            commission_percent=fee_rate * 100,
            commission_amount=fee,
            total_amount=total_price,
            tracking_code=generate_tracking_code('SELL'),
            description=f"✅ اجرای خودکار سفارش با قیمت {order.target_price} - {order.description or ''}"
        )

        # ❌ بدون رفرال برای سفارش با قیمت

        order.status = 'EXECUTED'
        order.executed_price = current_price
        order.save(update_fields=['status', 'executed_price', 'updated_at'])
        
        

# def _execute_order(order, current_price):
#     """
#     اجرای یک سفارش
#     """
#     if order.order_type == 'BUY':
#         wallet, _ = Wallet.objects.select_for_update().get_or_create(user=order.user)
#         inventory, _ = GoldInventory.objects.select_for_update().get_or_create(user=order.user)

#         fee_rate = Decimal(str(order.fee_rate))
#         pure_price = (order.amount_toman / (Decimal("1") + fee_rate)).quantize(Decimal("1"))
#         fee = (order.amount_toman - pure_price).quantize(Decimal("1"))
#         weight = (pure_price / current_price).quantize(Decimal("0.001"), rounding=ROUND_DOWN)

#         wallet.blocked_toman -= order.amount_toman
#         wallet.save(update_fields=['blocked_toman'])

#         inventory.accessible_balance += weight
#         inventory.save(update_fields=['accessible_balance'])

#         GoldTransaction.objects.create(
#             user=order.user,
#             type='BUY',
#             status='COMPLETED',
#             amount_gr=weight,
#             price_per_gram=current_price,
#             fee=fee,
#             commission_percent=fee_rate * 100,
#             commission_amount=fee,
#             total_amount=order.amount_toman,
#             tracking_code=generate_tracking_code('BUY'),
#             description=f"اجرای خودکار سفارش با قیمت {order.target_price} - {order.description or ''}"
#         )

#         create_referral_profit(
#             user=order.user,
#             source_type='GOLD',
#             transaction_amount=order.amount_toman
#         )

#         order.status = 'EXECUTED'
#         order.executed_price = current_price
#         order.estimated_weight = weight
#         order.save(update_fields=['status', 'executed_price', 'estimated_weight', 'updated_at'])

#     else:  # SELL
#         wallet, _ = Wallet.objects.select_for_update().get_or_create(user=order.user)
#         inventory, _ = GoldInventory.objects.select_for_update().get_or_create(user=order.user)

#         inventory.blocked_balance -= order.gold_weight
#         inventory.save(update_fields=['blocked_balance'])

#         fee_rate = Decimal(str(order.fee_rate))
#         pure_price = (current_price * order.gold_weight).quantize(Decimal("1"))
#         fee = (pure_price * fee_rate).quantize(Decimal("1"))
#         total_price = (pure_price - fee).quantize(Decimal("1"))

#         wallet.accessible_toman += total_price
#         wallet.save(update_fields=['accessible_toman'])

#         GoldTransaction.objects.create(
#             user=order.user,
#             type='SELL',
#             status='COMPLETED',
#             amount_gr=order.gold_weight,
#             price_per_gram=current_price,
#             fee=fee,
#             commission_percent=fee_rate * 100,
#             commission_amount=fee,
#             total_amount=total_price,
#             tracking_code=generate_tracking_code('SELL'),
#             description=f"اجرای خودکار سفارش با قیمت {order.target_price} - {order.description or ''}"
#         )

#         order.status = 'EXECUTED'
#         order.executed_price = current_price
#         order.save(update_fields=['status', 'executed_price', 'updated_at'])

# gold_app/utils.py

def _execute_order(order, current_price):
    """اجرای یک سفارش با قیمت"""
    if order.order_type == 'BUY':
        wallet, _ = Wallet.objects.select_for_update().get_or_create(user=order.user)
        inventory, _ = GoldInventory.objects.select_for_update().get_or_create(user=order.user)

        fee_rate = Decimal(str(order.fee_rate))
        pure_price = (order.amount_toman / (Decimal("1") + fee_rate)).quantize(Decimal("1"))
        fee = (order.amount_toman - pure_price).quantize(Decimal("1"))
        weight = (pure_price / current_price).quantize(Decimal("0.001"), rounding=ROUND_DOWN)

        if wallet.blocked_toman < order.amount_toman:
            return

        wallet.blocked_toman -= order.amount_toman
        wallet.save(update_fields=['blocked_toman'])

        inventory.accessible_balance += weight
        inventory.save(update_fields=['accessible_balance'])

        GoldTransaction.objects.create(
            user=order.user,
            type='BUY',
            status='COMPLETED',
            amount_gr=weight,
            price_per_gram=current_price,
            fee=fee,
            commission_percent=fee_rate * 100,
            commission_amount=fee,
            total_amount=order.amount_toman,
            tracking_code=generate_tracking_code('BUY'),
            description=f"اجرای خودکار سفارش با قیمت {order.target_price} - {order.description or ''}"
        )

        # ✅ فقط این بخش اضافه شده (commission_amount)
        try:
            create_referral_profit(
                user=order.user,
                source_type='GOLD',
                transaction_amount=order.amount_toman,
                commission_amount=fee,  # ✅ اضافه شده
            )
        except Exception as e:
            logger.error(f"❌ خطا در ایجاد پاداش معرفی: {e}")

        order.status = 'EXECUTED'
        order.executed_price = current_price
        order.estimated_weight = weight
        order.save(update_fields=['status', 'executed_price', 'estimated_weight', 'updated_at'])

    else:  # SELL
        wallet, _ = Wallet.objects.select_for_update().get_or_create(user=order.user)
        inventory, _ = GoldInventory.objects.select_for_update().get_or_create(user=order.user)

        if inventory.blocked_balance < order.gold_weight:
            return

        inventory.blocked_balance -= order.gold_weight
        inventory.save(update_fields=['blocked_balance'])

        fee_rate = Decimal(str(order.fee_rate))
        pure_price = (current_price * order.gold_weight).quantize(Decimal("1"))
        fee = (pure_price * fee_rate).quantize(Decimal("1"))
        total_price = (pure_price - fee).quantize(Decimal("1"))

        wallet.accessible_toman += total_price
        wallet.save(update_fields=['accessible_toman'])

        GoldTransaction.objects.create(
            user=order.user,
            type='SELL',
            status='COMPLETED',
            amount_gr=order.gold_weight,
            price_per_gram=current_price,
            fee=fee,
            commission_percent=fee_rate * 100,
            commission_amount=fee,
            total_amount=total_price,
            tracking_code=generate_tracking_code('SELL'),
            description=f"اجرای خودکار سفارش با قیمت {order.target_price} - {order.description or ''}"
        )

        # ✅ فقط این بخش اضافه شده (commission_amount)
        try:
            create_referral_profit(
                user=order.user,
                source_type='GOLD',
                transaction_amount=pure_price,
                commission_amount=fee,  # ✅ اضافه شده
            )
        except Exception as e:
            logger.error(f"❌ خطا در ایجاد پاداش معرفی: {e}")

        order.status = 'EXECUTED'
        order.executed_price = current_price
        order.save(update_fields=['status', 'executed_price', 'updated_at'])


# gold_app/utils.py

from decimal import Decimal, ROUND_DOWN
from django.db import transaction
from .models import GoldOrder, GoldTransaction, Wallet, GoldInventory
from accounts.utils import create_referral_profit


# def check_and_execute_limit_orders():
#     """
#     تابعی که هر دقیقه اجرا میشه و سفارشات در انتظار رو چک میکنه
#     """
#     pending_orders = GoldOrder.objects.filter(status='PENDING')
    
#     if not pending_orders.exists():
#         return 0
    
#     executed_count = 0
    
#     for order in pending_orders:
#         current_price = get_live_gold_price()
#         if not current_price:
#             continue
        
#         should_execute = False
        
#         if order.order_type == 'BUY':
#             # ✅ خرید: قیمت فعلی <= قیمت هدف
#             if current_price <= order.target_price:
#                 should_execute = True
#         else:  # SELL
#             # ✅ فروش: قیمت فعلی >= قیمت هدف
#             if current_price >= order.target_price:
#                 should_execute = True
        
#         if should_execute:
#             try:
#                 with transaction.atomic():
#                     _execute_order(order, current_price)
#                     executed_count += 1
#                     logger.info(f"✅ سفارش {order.id} خودکار اجرا شد - قیمت: {current_price}")
#             except Exception as e:
#                 logger.error(f"❌ خطا در اجرای سفارش {order.id}: {e}")
    
#     return executed_count

# gold_app/utils.py

# def check_and_execute_limit_orders():
#     """
#     تابعی که هر دقیقه اجرا میشه و سفارشات در انتظار رو چک میکنه
#     """
#     pending_orders = GoldOrder.objects.filter(status='PENDING')
    
#     if not pending_orders.exists():
#         return 0
    
#     executed_count = 0
    
#     for order in pending_orders:
#         current_price = get_live_gold_price()
#         if not current_price:
#             continue
        
#         should_execute = False
        
#         if order.order_type == 'BUY':
#             if current_price <= order.target_price:
#                 should_execute = True
#         else:  # SELL
#             if current_price >= order.target_price:
#                 should_execute = True
        
#         if should_execute:
#             try:
#                 with transaction.atomic():
#                     _execute_order(order, current_price)
#                     executed_count += 1
#                     logger.info(f"✅ سفارش {order.id} خودکار اجرا شد - قیمت: {current_price}")  # ✅ اضافه شده
#             except Exception as e:
#                 logger.error(f"❌ خطا در اجرای سفارش {order.id}: {e}")  # ✅ اضافه شده
    
#     return executed_count




def _execute_order(order, current_price):
    """اجرای یک سفارش با قیمت"""
    if order.order_type == 'BUY':
        wallet, _ = Wallet.objects.select_for_update().get_or_create(user=order.user)
        inventory, _ = GoldInventory.objects.select_for_update().get_or_create(user=order.user)

        fee_rate = Decimal(str(order.fee_rate))
        pure_price = (order.amount_toman / (Decimal("1") + fee_rate)).quantize(Decimal("1"))
        fee = (order.amount_toman - pure_price).quantize(Decimal("1"))
        weight = (pure_price / current_price).quantize(Decimal("0.001"), rounding=ROUND_DOWN)

        if wallet.blocked_toman < order.amount_toman:
            return

        wallet.blocked_toman -= order.amount_toman
        wallet.save(update_fields=['blocked_toman'])

        inventory.accessible_balance += weight
        inventory.save(update_fields=['accessible_balance'])

        GoldTransaction.objects.create(
            user=order.user,
            type='BUY',
            status='COMPLETED',
            amount_gr=weight,
            price_per_gram=current_price,
            fee=fee,
            commission_percent=fee_rate * 100,
            commission_amount=fee,
            total_amount=order.amount_toman,
            tracking_code=generate_tracking_code('BUY'),
            description=f"اجرای خودکار سفارش با قیمت {order.target_price} - {order.description or ''}"
        )

        # ✅ ایجاد سود رفرال
        try:
            create_referral_profit(
                user=order.user,
                source_type='GOLD',
                transaction_amount=order.amount_toman
            )
        except Exception as e:
            print(f"❌ خطا در ایجاد پاداش معرفی: {e}")

        order.status = 'EXECUTED'
        order.executed_price = current_price
        order.estimated_weight = weight
        order.save(update_fields=['status', 'executed_price', 'estimated_weight', 'updated_at'])

    else:  # SELL
        wallet, _ = Wallet.objects.select_for_update().get_or_create(user=order.user)
        inventory, _ = GoldInventory.objects.select_for_update().get_or_create(user=order.user)

        if inventory.blocked_balance < order.gold_weight:
            return

        inventory.blocked_balance -= order.gold_weight
        inventory.save(update_fields=['blocked_balance'])

        fee_rate = Decimal(str(order.fee_rate))
        pure_price = (current_price * order.gold_weight).quantize(Decimal("1"))
        fee = (pure_price * fee_rate).quantize(Decimal("1"))
        total_price = (pure_price - fee).quantize(Decimal("1"))

        wallet.accessible_toman += total_price
        wallet.save(update_fields=['accessible_toman'])

        GoldTransaction.objects.create(
            user=order.user,
            type='SELL',
            status='COMPLETED',
            amount_gr=order.gold_weight,
            price_per_gram=current_price,
            fee=fee,
            commission_percent=fee_rate * 100,
            commission_amount=fee,
            total_amount=total_price,
            tracking_code=generate_tracking_code('SELL'),
            description=f"اجرای خودکار سفارش با قیمت {order.target_price} - {order.description or ''}"
        )

        order.status = 'EXECUTED'
        order.executed_price = current_price
        order.save(update_fields=['status', 'executed_price', 'updated_at'])








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






# gold_app/utils.py - فقط بخش فروش تعهدی

from decimal import Decimal, ROUND_DOWN
from django.db import transaction
from django.utils import timezone
from .models import GoldShortOrder, GoldShortOrderHistory, GoldInventory, GoldTransaction
import logging

logger = logging.getLogger(__name__)


# =========================================================
# CHECK SHORT ORDERS (اجرای خودکار حد سود/حد ضرر)
# =========================================================

def check_short_orders():
    """
    چک کردن سفارشات فروش تعهدی برای حد سود/حد ضرر
    هر دقیقه توسط cron اجرا میشود
    """
    from .utils import get_live_gold_price, generate_tracking_code
    
    active_orders = GoldShortOrder.objects.filter(status='ACTIVE')
    
    if not active_orders.exists():
        return 0
    
    current_price = get_live_gold_price()
    
    if not current_price:
        return 0
    
    current_price = Decimal(str(current_price))
    processed_count = 0
    
    for order in active_orders:
        # محاسبه سود/ضرر فعلی
        profit_loss = (order.entry_price - current_price) * order.weight * order.leverage
        profit_loss = profit_loss.quantize(Decimal("1"))
        
        # =============================================
        # بررسی حد سود (Take Profit)
        # =============================================
        if order.take_profit:
            take_profit_amount = Decimal(str(order.take_profit))
            if profit_loss >= take_profit_amount:
                try:
                    with transaction.atomic():
                        close_short_order(order, current_price, 'TAKE_PROFIT')
                        processed_count += 1
                        logger.info(f"✅ سفارش {order.id} با حد سود بسته شد - سود: {profit_loss}")
                except Exception as e:
                    logger.error(f"❌ خطا در بستن سفارش {order.id}: {e}")
                continue
        
        # =============================================
        # بررسی حد ضرر (Stop Loss)
        # =============================================
        if order.stop_loss:
            stop_loss_amount = Decimal(str(order.stop_loss))
            if profit_loss <= -stop_loss_amount:
                try:
                    with transaction.atomic():
                        close_short_order(order, current_price, 'STOP_LOSS')
                        processed_count += 1
                        logger.info(f"✅ سفارش {order.id} با حد ضرر بسته شد - ضرر: {profit_loss}")
                except Exception as e:
                    logger.error(f"❌ خطا در بستن سفارش {order.id}: {e}")
                continue
        
        # =============================================
        # بررسی لیکوئید (Liquidation)
        # اگر ضرر به 100% سرمایه رسید
        # =============================================
        initial_value = order.entry_price * order.weight
        if profit_loss <= -initial_value:
            try:
                with transaction.atomic():
                    liquidate_short_order(order, current_price)
                    processed_count += 1
                    logger.info(f"✅ سفارش {order.id} لیکوئید شد - ضرر: {profit_loss}")
            except Exception as e:
                logger.error(f"❌ خطا در لیکوئید سفارش {order.id}: {e}")
    
    return processed_count


# =========================================================
# CLOSE SHORT ORDER (بستن خودکار سفارش)
# =========================================================

def close_short_order(order, current_price, reason):
    """
    بستن خودکار سفارش فروش تعهدی
    reason: 'TAKE_PROFIT' یا 'STOP_LOSS'
    """
    from .utils import generate_tracking_code
    
    # محاسبه سود/ضرر
    profit_loss = (order.entry_price - current_price) * order.weight * order.leverage
    profit_loss = profit_loss.quantize(Decimal("1"))
    
    # کارمزد روزانه (0.65% در روز)
    hours_active = (timezone.now() - order.created_at).total_seconds() / 3600
    daily_fee_rate = Decimal("0.0065")  # 0.65%
    daily_fee = (order.weight * order.entry_price * daily_fee_rate * Decimal(str(hours_active / 24))).quantize(Decimal("1"))
    total_fee = order.initial_fee + daily_fee
    
    # برگشت موجودی طلا
    inventory, _ = GoldInventory.objects.select_for_update().get_or_create(user=order.user)
    
    if inventory.blocked_balance < order.weight:
        return False
    
    inventory.blocked_balance -= order.weight
    inventory.accessible_balance += order.weight
    inventory.save(update_fields=['accessible_balance', 'blocked_balance', 'updated_at'])
    
    # به‌روزرسانی سفارش
    order.status = 'CLOSED'
    order.close_price = current_price
    order.profit_loss = profit_loss
    order.daily_fee = daily_fee
    order.total_fee = total_fee
    order.closed_at = timezone.now()
    
    reason_text = "حد سود" if reason == 'TAKE_PROFIT' else "حد ضرر"
    order.description = f"{order.description or ''}\nبسته شده خودکار - {reason_text}"
    order.save(update_fields=['status', 'close_price', 'profit_loss', 'daily_fee', 'total_fee', 'closed_at', 'description', 'updated_at'])
    
    # ثبت تاریخچه
    GoldShortOrderHistory.objects.create(
        order=order,
        status='CLOSED',
        price=current_price,
        profit_loss=profit_loss,
        description=f'بسته شده خودکار - {reason_text} - سود/ضرر: {profit_loss}'
    )
    
    # ایجاد تراکنش
    GoldTransaction.objects.create(
        user=order.user,
        type='SELL',
        status='COMPLETED',
        amount_gr=order.weight,
        price_per_gram=current_price,
        fee=total_fee,
        commission_percent=Decimal("1"),
        commission_amount=total_fee,
        total_amount=order.weight * current_price,
        tracking_code=generate_tracking_code('SHORT-CLOSE'),
        description=f'بسته شدن خودکار فروش تعهدی - {reason_text} - سود/ضرر: {profit_loss}'
    )
    
    return True


# =========================================================
# LIQUIDATE SHORT ORDER (لیکوئید کردن خودکار)
# =========================================================

def liquidate_short_order(order, current_price):
    """
    لیکوئید کردن خودکار سفارش فروش تعهدی
    """
    from .utils import generate_tracking_code
    
    # محاسبه ضرر
    profit_loss = (order.entry_price - current_price) * order.weight * order.leverage
    profit_loss = profit_loss.quantize(Decimal("1"))
    
    # کارمزد روزانه (0.65% در روز)
    hours_active = (timezone.now() - order.created_at).total_seconds() / 3600
    daily_fee_rate = Decimal("0.0065")
    daily_fee = (order.weight * order.entry_price * daily_fee_rate * Decimal(str(hours_active / 24))).quantize(Decimal("1"))
    total_fee = order.initial_fee + daily_fee
    
    # برگشت موجودی طلا
    inventory, _ = GoldInventory.objects.select_for_update().get_or_create(user=order.user)
    
    if inventory.blocked_balance < order.weight:
        return False
    
    inventory.blocked_balance -= order.weight
    inventory.accessible_balance += order.weight
    inventory.save(update_fields=['accessible_balance', 'blocked_balance', 'updated_at'])
    
    # به‌روزرسانی سفارش
    order.status = 'LIQUIDATED'
    order.close_price = current_price
    order.profit_loss = profit_loss
    order.daily_fee = daily_fee
    order.total_fee = total_fee
    order.closed_at = timezone.now()
    order.description = f"{order.description or ''}\nلیکوئید شده - ضرر: {profit_loss}"
    order.save(update_fields=['status', 'close_price', 'profit_loss', 'daily_fee', 'total_fee', 'closed_at', 'description', 'updated_at'])
    
    # ثبت تاریخچه
    GoldShortOrderHistory.objects.create(
        order=order,
        status='LIQUIDATED',
        price=current_price,
        profit_loss=profit_loss,
        description=f'لیکوئید شد - ضرر: {profit_loss}'
    )
    
    # ایجاد تراکنش
    GoldTransaction.objects.create(
        user=order.user,
        type='SELL',
        status='FAILED',
        amount_gr=order.weight,
        price_per_gram=current_price,
        fee=total_fee,
        commission_percent=Decimal("1"),
        commission_amount=total_fee,
        total_amount=0,
        tracking_code=generate_tracking_code('SHORT-LIQ'),
        description=f'لیکوئید شدن فروش تعهدی - ضرر: {profit_loss}'
    )
    
    return True


# =========================================================
# CALCULATE SHORT PROFIT/LOSS (محاسبه سود/ضرر لحظه‌ای)
# =========================================================

def calculate_short_profit_loss(order, current_price=None):
    """
    محاسبه سود/ضرر لحظه‌ای یک سفارش فروش تعهدی
    """
    if not current_price:
        from .utils import get_live_gold_price
        current_price = get_live_gold_price()
        
        if not current_price:
            return None
    
    current_price = Decimal(str(current_price))
    
    # سود/ضرر = (قیمت ورود - قیمت فعلی) × وزن × ضریب
    profit_loss = (order.entry_price - current_price) * order.weight * order.leverage
    profit_loss = profit_loss.quantize(Decimal("1"))
    
    # درصد سود/ضرر
    initial_value = order.entry_price * order.weight
    profit_percent = (profit_loss / initial_value * 100).quantize(Decimal("0.01")) if initial_value > 0 else Decimal("0")
    
    return {
        'current_price': current_price,
        'profit_loss': profit_loss,
        'profit_percent': profit_percent,
        'entry_price': order.entry_price,
        'weight': order.weight,
        'leverage': order.leverage,
    }


# =========================================================
# CHECK SHORT LIQUIDATION (بررسی لیکوئید)
# =========================================================

def check_short_liquidation(order, current_price=None):
    """
    بررسی اینکه آیا سفارش باید لیکوئید شود یا نه
    """
    if not current_price:
        from .utils import get_live_gold_price
        current_price = get_live_gold_price()
        
        if not current_price:
            return False, None
    
    current_price = Decimal(str(current_price))
    
    # محاسبه سود/ضرر
    profit_loss = (order.entry_price - current_price) * order.weight * order.leverage
    profit_loss = profit_loss.quantize(Decimal("1"))
    
    # ارزش اولیه
    initial_value = order.entry_price * order.weight
    
    # اگر ضرر به 100% سرمایه رسید، لیکوئید
    if profit_loss <= -initial_value:
        return True, profit_loss
    
    return False, profit_loss