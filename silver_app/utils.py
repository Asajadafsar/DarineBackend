# silver_app/utils.py

import uuid
import logging
import requests
import time  # ✅ اضافه کردن این خط
from decimal import Decimal, ROUND_DOWN
from datetime import timedelta, datetime
from django.db import transaction
from django.utils import timezone
from django.db.models import Avg
from django.db.models.functions import TruncHour, TruncDate
from rest_framework.response import Response
from django.core.cache import cache

from .models import SilverPriceHistory

logger = logging.getLogger(__name__)


# =========================================================
# DECIMAL HELPERS
# =========================================================

def decimal_3(value):
    return Decimal(value).quantize(Decimal("0.001"), rounding=ROUND_DOWN)


# =========================================================
# RESPONSE HELPERS
# =========================================================

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


# =========================================================
# TRACKING CODE
# =========================================================

def generate_tracking_code(prefix="S"):
    return f"{prefix}-{uuid.uuid4().hex[:8].upper()}"


# =========================================================
# SILVER PRICE WITH CACHE (30 SECONDS)
# =========================================================
# silver_app/utils.py

import time
import logging
import requests
from decimal import Decimal
from django.core.cache import cache

logger = logging.getLogger(__name__)


# =========================================================
# SILVER PRICE WITH STABLE CACHE (30 SECONDS)
# =========================================================
# silver_app/utils.py

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

SILVER_CACHE_FILE = os.path.join(CACHE_DIR, 'silver_price.json')
SILVER_CACHE_TIME_FILE = os.path.join(CACHE_DIR, 'silver_price_time.json')


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
# SILVER PRICE WITH FILE CACHE (30 SECONDS)
# =========================================================

def get_live_silver_price():
    """
    دریافت قیمت لحظه‌ای نقره با کش ۳۰ ثانیه‌ای (ذخیره در فایل)
    هر ۳۰ ثانیه یک بار از API دریافت می‌شود
    """
    # ✅ خواندن از کش فایل
    cached_price = read_cache(SILVER_CACHE_FILE)
    cached_time = read_cache(SILVER_CACHE_TIME_FILE)
    
    now = time.time()
    
    # ✅ اگر کمتر از ۳۰ ثانیه گذشته، از کش برگردان
    if cached_time and cached_price:
        elapsed = now - cached_time
        if elapsed < 30:
            return Decimal(str(cached_price))
    
    # ✅ دریافت از API
    url = "https://api.noghresea.ir/api/market/getSilverPrice"

    try:
        response = requests.get(url, timeout=10)

        if response.status_code != 200:
            logger.error(f"Silver API Error: {response.status_code}")
            if cached_price is not None:
                return Decimal(str(cached_price))
            return None

        data = response.json()

        raw_price = Decimal(str(data["price"]))

        if raw_price <= 0:
            logger.error("Silver price <= 0")
            if cached_price is not None:
                return Decimal(str(cached_price))
            return None

        price = raw_price * 1000

    except Exception as e:
        logger.error(f"Silver Price Error: {str(e)}")
        if cached_price is not None:
            return Decimal(str(cached_price))
        return None

    # offset
    try:
        from admin_panel.models import SilverPriceOffset
        offset = SilverPriceOffset.objects.filter(is_active=True).first()
        if offset:
            price = price + offset.offset_amount
    except Exception:
        pass

    # ✅ ذخیره در کش فایل
    write_cache(SILVER_CACHE_FILE, float(price))
    write_cache(SILVER_CACHE_TIME_FILE, now)

    return price


def force_refresh_silver_price():
    """دریافت قیمت نقره بدون استفاده از کش"""
    for file_path in [SILVER_CACHE_FILE, SILVER_CACHE_TIME_FILE]:
        if os.path.exists(file_path):
            os.remove(file_path)
    return get_live_silver_price()

# =========================================================
# SAVE SILVER PRICE HISTORY
# =========================================================

def save_silver_price_history():
    price = get_live_silver_price()

    if not price:
        return False

    last = SilverPriceHistory.objects.order_by("-created_at").first()

    if last and last.price == price:
        if timezone.now() - last.created_at < timedelta(hours=1):
            return True

    SilverPriceHistory.objects.create(price=price)
    return True


def calculate_silver_price_changes(current_price):
    now = timezone.now()

    day = (
        SilverPriceHistory.objects.filter(created_at__lte=now - timedelta(hours=24))
        .order_by("-created_at")
        .first()
    )

    week = (
        SilverPriceHistory.objects.filter(created_at__lte=now - timedelta(days=7))
        .order_by("-created_at")
        .first()
    )

    month = (
        SilverPriceHistory.objects.filter(created_at__lte=now - timedelta(days=30))
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
# SILVER CHART DATA
# =========================================================

def get_silver_chart_data(filter_type="24H"):
    now = timezone.now()
    current_tz = timezone.get_current_timezone()

    if filter_type == "24H":
        start_date = now - timedelta(hours=24)
        trunc_fn = TruncHour
    elif filter_type == "WEEKLY":
        start_date = now - timedelta(days=7)
        trunc_fn = TruncDate
    elif filter_type == "MONTHLY":
        start_date = now - timedelta(days=30)
        trunc_fn = TruncDate
    else:
        start_date = now - timedelta(hours=24)
        trunc_fn = TruncHour

    queryset = (
        SilverPriceHistory.objects
        .filter(created_at__gte=start_date)
        .annotate(period=trunc_fn("created_at"))
        .values("period")
        .annotate(avg_price=Avg("price"))
        .order_by("period")
    )

    labels = []
    prices = []

    for item in queryset:
        if item["avg_price"] is None:
            continue

        period = item["period"]

        if isinstance(period, datetime):
            if timezone.is_naive(period):
                period = timezone.make_aware(period, current_tz)
            else:
                period = timezone.localtime(period)
        else:
            period = timezone.make_aware(
                datetime.combine(period, datetime.min.time()),
                current_tz,
            )

        labels.append(period.isoformat(timespec="seconds"))
        prices.append(int(item["avg_price"]))

    if not prices:
        return {
            "chart": {"labels": [], "prices": []},
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

    current_price = prices[-1]
    highest_price = max(prices)
    lowest_price = min(prices)
    first_price = prices[0]

    changes = calculate_silver_price_changes(current_price)

    change_amount = current_price - first_price
    change_percent = round(((current_price - first_price) / first_price) * 100, 2) if first_price else 0

    price_range = highest_price - lowest_price
    padding = int(price_range * 0.1) if price_range else int(highest_price * 0.01)

    return {
        "chart": {"labels": labels, "prices": prices},
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


def get_silver_bubble():
    try:
        from gold_app.utils import get_world_prices

        world = get_world_prices()

        if not world:
            return None

        market_price = get_live_silver_price()

        if not market_price:
            return None

        intrinsic = (world["silver_ounce"] * world["usdt"]) / Decimal("31.1035")

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
# FILTER HELPERS
# =========================================================

def filter_by_date(queryset, start_date=None, end_date=None):
    if start_date:
        queryset = queryset.filter(created_at__date__gte=start_date)
    if end_date:
        queryset = queryset.filter(created_at__date__lte=end_date)
    return queryset


def filter_by_status(queryset, status=None):
    if status:
        queryset = queryset.filter(status=status)
    return queryset


# =========================================================
# BUY SILVER CALC
# =========================================================

def calculate_buy_silver(toman_amount=None, weight_amount=None, fee_rate=Decimal("0.01")):
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
        "total_toman": round(total_toman),
    }


# =========================================================
# SELL SILVER CALC
# =========================================================

def calculate_sell_silver(toman_amount=None, weight_amount=None, fee_rate=Decimal("0.01")):
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


# =========================================================
# EXECUTE SILVER LIMIT ORDERS
# =========================================================

def check_and_execute_silver_limit_orders():
    """چک و اجرای خودکار سفارشات نقره"""
    from .models import SilverLimitOrder, SilverTransaction, SilverWallet, SilverInventory
    from accounts.utils import create_referral_profit
    
    pending_orders = SilverLimitOrder.objects.filter(status='PENDING')
    
    if not pending_orders.exists():
        return 0
    
    executed_count = 0
    
    for order in pending_orders:
        current_price = get_live_silver_price()
        if not current_price:
            continue
        
        should_execute = False
        
        if order.order_type == 'BUY':
            if current_price <= order.target_price:
                should_execute = True
        else:
            if current_price >= order.target_price:
                should_execute = True
        
        if should_execute:
            try:
                with transaction.atomic():
                    _execute_silver_order(order, current_price)
                    executed_count += 1
                    logger.info(f"✅ سفارش نقره {order.id} خودکار اجرا شد - قیمت: {current_price}")
            except Exception as e:
                logger.error(f"❌ خطا در اجرای سفارش نقره {order.id}: {e}")
    
    return executed_count


def _execute_silver_order(order, current_price):
    """اجرای خودکار یک سفارش نقره"""
    from .models import SilverLimitOrder, SilverTransaction, SilverWallet, SilverInventory
    from accounts.utils import create_referral_profit
    
    if order.order_type == 'BUY':
        wallet, _ = SilverWallet.objects.select_for_update().get_or_create(user=order.user)
        inventory, _ = SilverInventory.objects.select_for_update().get_or_create(user=order.user)

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

        SilverTransaction.objects.create(
            user=order.user,
            type='BUY',
            status='COMPLETED',
            amount_gr=weight,
            price_per_gram=current_price,
            fee=fee,
            commission_percent=fee_rate * 100,
            commission_amount=fee,
            total_amount=order.amount_toman,
            tracking_code=generate_tracking_code('SBUY'),
            description=f"✅ اجرای خودکار سفارش با قیمت نقره {order.target_price} - {order.description or ''}"
        )

        # ❌ بدون رفرال برای نقره

        order.status = 'EXECUTED'
        order.executed_price = current_price
        order.estimated_weight = weight
        order.save(update_fields=['status', 'executed_price', 'estimated_weight', 'updated_at'])

    else:  # SELL
        wallet, _ = SilverWallet.objects.select_for_update().get_or_create(user=order.user)
        inventory, _ = SilverInventory.objects.select_for_update().get_or_create(user=order.user)

        if inventory.blocked_balance < order.silver_weight:
            return

        inventory.blocked_balance -= order.silver_weight
        inventory.save(update_fields=['blocked_balance'])

        fee_rate = Decimal(str(order.fee_rate))
        pure_price = (current_price * order.silver_weight).quantize(Decimal("1"))
        fee = (pure_price * fee_rate).quantize(Decimal("1"))
        total_price = (pure_price - fee).quantize(Decimal("1"))

        wallet.accessible_toman += total_price
        wallet.save(update_fields=['accessible_toman'])

        SilverTransaction.objects.create(
            user=order.user,
            type='SELL',
            status='COMPLETED',
            amount_gr=order.silver_weight,
            price_per_gram=current_price,
            fee=fee,
            commission_percent=fee_rate * 100,
            commission_amount=fee,
            total_amount=total_price,
            tracking_code=generate_tracking_code('SSELL'),
            description=f"✅ اجرای خودکار سفارش با قیمت نقره {order.target_price} - {order.description or ''}"
        )

        # ❌ بدون رفرال برای نقره

        order.status = 'EXECUTED'
        order.executed_price = current_price
        order.save(update_fields=['status', 'executed_price', 'updated_at'])