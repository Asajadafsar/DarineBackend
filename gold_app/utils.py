# import requests
# from decimal import Decimal

# def get_live_gold_price():
#     """دریافت قیمت لحظه‌ای طلا از API وال‌گلد"""
#     url = "https://api.wallgold.ir/api/v1/price?side=buy&symbol=GLD_18C_750TMN"
#     try:
#         response = requests.get(url, timeout=10)
#         if response.status_code == 200:
#             data = response.json()
#             return Decimal(str(data['result']['price']))
#     except Exception as e:
#         print(f"Error fetching gold price: {e}")
#     return None

# def get_live_silver_price():
#     """دریافت قیمت لحظه‌ای نقره از API نقره‌سیء"""
#     url = "https://api.noghresea.ir/api/market/getSilverPrice"
#     try:
#         response = requests.get(url, timeout=10)
#         if response.status_code == 200:
#             data = response.json()
#             # توجه: اینجا فقط دیتای خام رو می‌گیریم، 
#             # اگر در طلاینه هم می‌خوای قیمت به تومان باشه، مثل فایل نقرینه ضرب در ۱۰۰۰ کن
#             return Decimal(str(data['price']))
#     except Exception as e:
#         print(f"Error fetching silver price: {e}")
#     return None


# gold_app/utils.py

import requests
import logging

from decimal import Decimal
from datetime import timedelta
from django.utils import timezone
from django.db.models import Avg

from .models import GoldPriceHistory


logger = logging.getLogger(__name__)


# =========================================================
# GOLD PRICE
# =========================================================

def get_live_gold_price():
    """
    دریافت قیمت لحظه‌ای طلای ۱۸ عیار
    """

    url = "https://api.wallgold.ir/api/v1/price?side=buy&symbol=GLD_18C_750TMN"

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

        if not data.get("success"):
            logger.error(
                "Gold API success=False"
            )
            return None

        price = Decimal(
            str(data["result"]["price"])
        )

        return price

    except Exception as e:

        logger.error(
            f"Error fetching gold price: {str(e)}"
        )

        return None


# =========================================================
# SILVER PRICE
# =========================================================

def get_live_silver_price():
    """
    دریافت قیمت لحظه‌ای نقره
    """

    url = "https://api.noghresea.ir/api/market/getSilverPrice"

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
            str(data["price"])
        )

        return price

    except Exception as e:

        logger.error(
            f"Error fetching silver price: {str(e)}"
        )

        return None


# =========================================================
# SAVE GOLD PRICE HISTORY
# =========================================================

def save_gold_price_history():
    """
    ذخیره قیمت لحظه‌ای طلا داخل دیتابیس
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
    """
    دیتا برای نمودار قیمت طلا

    filter_type:
    - 24H
    - WEEKLY
    - MONTHLY
    """

    now = timezone.now()

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

    prices = [
        int(item.price)
        for item in queryset
    ]

    if not prices:

        current_price = get_live_gold_price()

        if current_price:

            return {
                "labels": ["الان"],
                "prices": [int(current_price)],
                "highest_price": int(current_price),
                "lowest_price": int(current_price),
                "change_percent": Decimal('0.00'),
                "filter_type": filter_type
            }

        return {
            "labels": [],
            "prices": [],
            "highest_price": 0,
            "lowest_price": 0,
            "change_percent": Decimal('0.00'),
            "filter_type": filter_type
        }

    highest_price = max(prices)
    lowest_price = min(prices)

    first_price = Decimal(str(prices[0]))
    last_price = Decimal(str(prices[-1]))

    if first_price == 0:

        change_percent = Decimal('0.00')

    else:

        change_percent = (
            (last_price - first_price)
            / first_price
        ) * Decimal('100')

    return {
        "labels": labels,
        "prices": prices,
        "highest_price": highest_price,
        "lowest_price": lowest_price,
        "change_percent": round(change_percent, 2),
        "filter_type": filter_type
    }


# =========================================================
# FILTER QUERYSET BY DATE
# =========================================================

def filter_by_date(
    queryset,
    start_date=None,
    end_date=None
):
    """
    فیلتر بازه زمانی
    """

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
# FILTER QUERYSET BY STATUS
# =========================================================

def filter_by_status(
    queryset,
    status=None
):
    """
    فیلتر وضعیت
    """

    if status:
        queryset = queryset.filter(
            status=status
        )

    return queryset


# =========================================================
# GENERATE TRACKING CODE
# =========================================================

def generate_tracking_code(prefix='GLD'):
    """
    تولید کد رهگیری یکتا
    """

    import uuid

    random_part = str(uuid.uuid4()).split('-')[0]

    return f"{prefix}-{random_part.upper()}"


# =========================================================
# CALCULATE BUY GOLD
# =========================================================

def calculate_buy_gold(
    toman_amount=None,
    weight_amount=None,
    fee_rate=Decimal('0.01')
):
    """
    محاسبات خرید طلا
    """

    price_per_gram = get_live_gold_price()

    if not price_per_gram:
        return None

    if toman_amount:

        total_toman = Decimal(
            str(toman_amount)
        )

        fee = total_toman * fee_rate

        net_amount = total_toman - fee

        weight = (
            net_amount / price_per_gram
        )

    else:

        weight = Decimal(
            str(weight_amount)
        )

        net_amount = (
            weight * price_per_gram
        )

        fee = net_amount * fee_rate

        total_toman = net_amount + fee

    return {
        "price_per_gram": price_per_gram,
        "weight": round(weight, 5),
        "fee": round(fee),
        "total_toman": round(total_toman)
    }


# =========================================================
# CALCULATE SELL GOLD
# =========================================================

def calculate_sell_gold(
    toman_amount=None,
    weight_amount=None,
    fee_rate=Decimal('0.01')
):
    """
    محاسبات فروش طلا
    """

    price_per_gram = get_live_gold_price()

    if not price_per_gram:
        return None

    if toman_amount:

        total_toman = Decimal(
            str(toman_amount)
        )

        weight = (
            total_toman / price_per_gram
        )

        fee = total_toman * fee_rate

        final_amount = (
            total_toman - fee
        )

    else:

        weight = Decimal(
            str(weight_amount)
        )

        raw_price = (
            weight * price_per_gram
        )

        fee = raw_price * fee_rate

        final_amount = (
            raw_price - fee
        )

    return {
        "price_per_gram": price_per_gram,
        "weight": round(weight, 5),
        "fee": round(fee),
        "final_amount": round(final_amount)
    }


# =========================================================
# USER TOTAL ASSETS
# =========================================================

def calculate_user_total_assets(
    gold_balance,
    toman_balance,
    gold_price
):
    """
    محاسبه مجموع دارایی کاربر
    """

    gold_value = (
        Decimal(str(gold_balance))
        * Decimal(str(gold_price))
    )

    total_assets = (
        gold_value
        + Decimal(str(toman_balance))
    )

    return {
        "gold_value": round(gold_value),
        "total_assets": round(total_assets)
    }


# =========================================================
# PRICE CHANGE PERCENT
# =========================================================

def calculate_price_change_percent(
    old_price,
    new_price
):
    """
    محاسبه درصد تغییر قیمت
    """

    old_price = Decimal(str(old_price))
    new_price = Decimal(str(new_price))

    if old_price == 0:
        return Decimal('0.00')

    percent = (
        (new_price - old_price)
        / old_price
    ) * Decimal('100')

    return round(percent, 2)


# =========================================================
# FORMAT MONEY
# =========================================================

def format_money(amount):
    """
    فرمت مبلغ
    """

    try:
        return "{:,}".format(
            int(amount)
        )

    except Exception:
        return "0"


# =========================================================
# GET DASHBOARD DATA
# =========================================================

def get_dashboard_statistics(user):

    from .models import (
        GoldInventory,
        Wallet,
        GoldTransaction,
        FinancialTransaction
    )

    gold_inventory, _ = GoldInventory.objects.get_or_create(
        user=user
    )

    wallet, _ = Wallet.objects.get_or_create(
        user=user
    )

    current_price = get_live_gold_price()

    gold_balance = Decimal(
        str(gold_inventory.balance)
    )

    toman_balance = Decimal(
        str(wallet.balance)
    )

    total_gold_value = (
        gold_balance * current_price
    )

    total_assets = (
        total_gold_value + toman_balance
    )

    total_buy = GoldTransaction.objects.filter(
        user=user,
        type='BUY',
        status='COMPLETED'
    ).count()

    total_sell = GoldTransaction.objects.filter(
        user=user,
        type='SELL',
        status='COMPLETED'
    ).count()

    total_deposit = FinancialTransaction.objects.filter(
        user=user,
        type='DEPOSIT',
        status='COMPLETED'
    ).count()

    total_withdraw = FinancialTransaction.objects.filter(
        user=user,
        type='WITHDRAW',
        status='COMPLETED'
    ).count()

    return {
        "gold_balance": round(gold_balance, 5),
        "toman_balance": round(toman_balance),
        "gold_price": current_price,
        "gold_value": round(total_gold_value),
        "total_assets": round(total_assets),
        "total_buy_transactions": total_buy,
        "total_sell_transactions": total_sell,
        "total_deposit_transactions": total_deposit,
        "total_withdraw_transactions": total_withdraw
    }


# =========================================================
# RECENT GOLD TRANSACTIONS
# =========================================================

def get_recent_gold_transactions(user, limit=10):

    from .models import GoldTransaction

    queryset = GoldTransaction.objects.filter(
        user=user
    ).order_by('-created_at')[:limit]

    return queryset


# =========================================================
# RECENT FINANCIAL TRANSACTIONS
# =========================================================

def get_recent_financial_transactions(
    user,
    limit=10
):

    from .models import FinancialTransaction

    queryset = FinancialTransaction.objects.filter(
        user=user
    ).order_by('-created_at')[:limit]

    return queryset


# =========================================================
# GET PRICE STATISTICS
# =========================================================

def get_price_statistics(days=30):

    start_date = timezone.now() - timedelta(
        days=days
    )

    queryset = GoldPriceHistory.objects.filter(
        created_at__gte=start_date
    )

    if not queryset.exists():

        current_price = get_live_gold_price()

        return {
            "average_price": current_price or 0,
            "highest_price": current_price or 0,
            "lowest_price": current_price or 0
        }

    prices = [
        item.price
        for item in queryset
    ]

    average_price = sum(prices) / len(prices)

    return {
        "average_price": round(average_price),
        "highest_price": max(prices),
        "lowest_price": min(prices)
    }