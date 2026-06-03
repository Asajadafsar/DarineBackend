# gold_app/models.py

from decimal import Decimal
from django.db import models
from django.conf import settings
from django.utils import timezone

from accounts.models import BankCard, User


# =========================================================
# WALLET
# =========================================================

class Wallet(models.Model):

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='wallet'
    )

    balance = models.DecimalField(
        max_digits=20,
        decimal_places=0,
        default=0
    )

    blocked_balance = models.DecimalField(
        max_digits=20,
        decimal_places=0,
        default=0
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):

        return f"{self.user.mobile}"


# =========================================================
# GOLD INVENTORY
# =========================================================

class GoldInventory(models.Model):

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='gold_inventory'
    )

    balance = models.DecimalField(
        max_digits=20,
        decimal_places=5,
        default=0
    )

    blocked_balance = models.DecimalField(
        max_digits=20,
        decimal_places=5,
        default=0
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):

        return self.user.mobile


# =========================================================
# GOLD TRANSACTION
# =========================================================

class GoldTransaction(models.Model):

    TYPE_CHOICES = (
        ('BUY', 'خرید'),
        ('SELL', 'فروش'),
    )

    STATUS_CHOICES = (
        ('PENDING', 'در انتظار'),
        ('COMPLETED', 'تکمیل شده'),
        ('FAILED', 'ناموفق'),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='COMPLETED'
    )

    amount_gr = models.DecimalField(
        max_digits=20,
        decimal_places=5
    )

    price_per_gram = models.DecimalField(
        max_digits=20,
        decimal_places=0
    )

    fee = models.DecimalField(
        max_digits=20,
        decimal_places=0,
        default=0
    )

    total_amount = models.DecimalField(
        max_digits=20,
        decimal_places=0
    )

    tracking_code = models.CharField(
        max_length=100,
        unique=True
    )

    description = models.TextField(
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )


# =========================================================
# FINANCIAL TRANSACTION
# =========================================================

class FinancialTransaction(models.Model):

    TYPE_CHOICES = (
        ('DEPOSIT', 'واریز'),
        ('WITHDRAW', 'برداشت'),
    )

    METHOD_CHOICES = (
        ('ONLINE', 'آنلاین'),
        ('CARD_TO_CARD', 'کارت به کارت'),
        ('BANK', 'بانکی'),
        ('SILVER', 'تبدیل به نقره'),
    )

    STATUS_CHOICES = (
        ('PENDING', 'در انتظار'),
        ('COMPLETED', 'تکمیل شده'),
        ('FAILED', 'ناموفق'),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    amount = models.DecimalField(
        max_digits=20,
        decimal_places=0
    )

    type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES
    )

    method = models.CharField(
        max_length=30,
        choices=METHOD_CHOICES
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING'
    )

    user_card = models.ForeignKey(
        BankCard,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    receipt_image = models.ImageField(
        upload_to='receipts/',
        null=True,
        blank=True
    )

    tracking_code = models.CharField(
        max_length=100,
        unique=True,
        null=True,
        blank=True
    )

    admin_note = models.TextField(
        blank=True,
        null=True
    )

    description = models.TextField(
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )


# =========================================================
# PRODUCT
# =========================================================



class ProductCategory(models.Model):

    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)

    def __str__(self):
        return self.name
    


class Product(models.Model):

    DELIVERY_CHOICES = (
        ('HOME', 'ارسال به منزل'),
        ('IN_PERSON', 'تحویل حضوری'),
    )

    category = models.ForeignKey(
        ProductCategory,
        on_delete=models.SET_NULL,
        null=True,
        related_name='products'
    )

    name = models.CharField(max_length=255)

    delivery_type = models.CharField(
        max_length=20,
        choices=DELIVERY_CHOICES,
        default='HOME'
    )

    weight = models.DecimalField(
        max_digits=20,
        decimal_places=5
    )

    total_weight_with_fees = models.DecimalField(
        max_digits=20,
        decimal_places=5,
        default=0
    )

    buy_price = models.DecimalField(
        max_digits=20,
        decimal_places=0,
        null=True,
        blank=True
    )

    sell_price = models.DecimalField(
        max_digits=20,
        decimal_places=0,
        null=True,
        blank=True
    )

    inventory_count = models.PositiveIntegerField(default=0)

    image = models.ImageField(
        upload_to='products/',
        null=True,
        blank=True
    )

    description = models.TextField(
        blank=True,
        null=True
    )

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name




# =========================================================
# ORDER
# =========================================================

class Order(models.Model):

    PAYMENT_CHOICES = (
        ('GOLD', 'طلا'),
        ('TOMAN', 'کیف پول'),
    )

    DELIVERY_CHOICES = (
        ('HOME', 'ارسال'),
        ('IN_PERSON', 'حضوری'),
    )

    STATUS_CHOICES = (
        ('PENDING', 'در انتظار'),
        ('PROCESSING', 'در حال پردازش'),
        ('SHIPPED', 'ارسال شده'),
        ('COMPLETED', 'تکمیل شده'),
        ('CANCELLED', 'لغو شده'),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    province = models.CharField(
        max_length=100
    )

    city = models.CharField(
        max_length=100
    )

    address = models.TextField()

    postal_code = models.CharField(
        max_length=20,
        blank=True,
        null=True
    )

    plaque = models.CharField(
        max_length=20,
        blank=True,
        null=True
    )

    unit = models.CharField(
        max_length=20,
        blank=True,
        null=True
    )

    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_CHOICES
    )

    delivery_type = models.CharField(
        max_length=20,
        choices=DELIVERY_CHOICES
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING'
    )

    total_gold_amount = models.DecimalField(
        max_digits=20,
        decimal_places=5
    )

    total_toman_amount = models.DecimalField(
        max_digits=20,
        decimal_places=0
    )

    tracking_code = models.CharField(
        max_length=100,
        unique=True
    )

    description = models.TextField(
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )


# =========================================================
# ORDER ITEM
# =========================================================

class OrderItem(models.Model):

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items'
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE
    )

    quantity = models.PositiveIntegerField()

    price_at_time = models.DecimalField(
        max_digits=20,
        decimal_places=0
    )

    weight_at_time = models.DecimalField(
        max_digits=20,
        decimal_places=5
    )


# =========================================================
# PRICE ALERT
# =========================================================

class PriceAlert(models.Model):

    ALERT_CHOICES = (
        ('ABOVE', 'بالاتر'),
        ('BELOW', 'پایین‌تر'),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    target_price = models.DecimalField(
        max_digits=20,
        decimal_places=5
    )

    alert_type = models.CharField(
        max_length=20,
        choices=ALERT_CHOICES
    )

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)


# # =========================================================
# # REFERRAL EARNING
# # =========================================================

# class ReferralEarning(models.Model):

#     referrer = models.ForeignKey(
#         settings.AUTH_USER_MODEL,
#         on_delete=models.CASCADE,
#         related_name='silver_referral_earnings'
#     )

#     referred_user = models.ForeignKey(
#         settings.AUTH_USER_MODEL,
#         on_delete=models.CASCADE,
#         related_name='earned_from_me'
#     )

#     amount = models.DecimalField(
#         max_digits=20,
#         decimal_places=0
#     )

#     transaction_date = models.DateTimeField(
#         auto_now_add=True
#     )


# =========================================================
# GIFT CARD
# =========================================================

class GiftCard(models.Model):

    STATUS_CHOICES = (
        ('ACTIVE', 'ACTIVE'),
        ('USED', 'USED'),
        ('EXPIRED', 'EXPIRED'),
    )

    serial_number = models.CharField(
        max_length=100,
        unique=True
    )

    weight = models.DecimalField(
        max_digits=12,
        decimal_places=5
    )

    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='created_gift_cards'
    )

    activated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='activated_gift_cards'
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='ACTIVE'
    )

    is_used = models.BooleanField(
        default=False
    )

    used_at = models.DateTimeField(
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):

        return self.serial_number

# =========================================================
# GIFT CARD ORDER
# =========================================================

class GiftCardOrder(models.Model):

    STATUS_CHOICES = (
        ('PENDING', 'در انتظار'),
        ('COMPLETED', 'تکمیل شده'),
        ('CANCELLED', 'لغو شده'),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    weight_per_card = models.DecimalField(
        max_digits=20,
        decimal_places=5
    )

    quantity = models.PositiveIntegerField()

    total_price = models.DecimalField(
        max_digits=20,
        decimal_places=0
    )

    province = models.CharField(
        max_length=100
    )

    city = models.CharField(
        max_length=100
    )

    address = models.TextField()

    postal_code = models.CharField(
        max_length=20,
        blank=True,
        null=True
    )

    plaque = models.CharField(
        max_length=20,
        blank=True,
        null=True
    )

    unit = models.CharField(
        max_length=20,
        blank=True,
        null=True
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING'
    )

    tracking_code = models.CharField(
        max_length=100,
        unique=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )


# =========================================================
# GOLD PRICE HISTORY
# =========================================================

class GoldPriceHistory(models.Model):

    price = models.DecimalField(
        max_digits=20,
        decimal_places=0
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True
    )

    class Meta:
        ordering = ["created_at"]


# =========================================================
# PURCHASE CREDIT
# =========================================================

class PurchaseCredit(models.Model):

    STATUS_CHOICES = (
        ('ACTIVE', 'فعال'),
        ('USED', 'استفاده شده'),
        ('EXPIRED', 'منقضی شده'),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    amount = models.DecimalField(
        max_digits=20,
        decimal_places=0
    )

    used_amount = models.DecimalField(
        max_digits=20,
        decimal_places=0,
        default=0
    )

    remaining_amount = models.DecimalField(
        max_digits=20,
        decimal_places=0,
        default=0
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='ACTIVE'
    )

    expire_at = models.DateTimeField()

    created_at = models.DateTimeField(
        auto_now_add=True
    )


# =========================================================
# AUTO SAVING PLAN
# =========================================================

class AutoSavingPlan(models.Model):

    TYPE_CHOICES = (
        ('DAILY', 'روزانه'),
        ('WEEKLY', 'هفتگی'),
        ('MONTHLY', 'ماهانه'),
    )

    STATUS_CHOICES = (
        ('ACTIVE', 'فعال'),
        ('PAUSED', 'متوقف'),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='saving_plans'
    )

    plan_type = models.CharField(   # 👈 مهم: هیچوقت دوباره "type" نذار
        max_length=20,
        choices=TYPE_CHOICES
    )

    amount = models.DecimalField(max_digits=20, decimal_places=0)
    period_days = models.PositiveIntegerField()
    next_execute_at = models.DateTimeField()

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE')

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} - {self.plan_type}"





class UserAddress(models.Model):

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='gold_addresses'
    )
    province = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    address = models.TextField()

    postal_code = models.CharField(max_length=20, null=True, blank=True)
    plaque = models.CharField(max_length=20, null=True, blank=True)
    unit = models.CharField(max_length=20, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

class GoldBankInfo(models.Model):

    card_number = models.CharField(max_length=30)
    full_name = models.CharField(max_length=255)
    sheba = models.CharField(max_length=34)

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"GOLD - {self.card_number}"


class GoldOrder(models.Model):

    ORDER_TYPE = (
        ("BUY", "خرید"),
        ("SELL", "فروش"),
    )

    STATUS = (
        ("PENDING", "در انتظار"),
        ("EXECUTED", "انجام شده"),
        ("CANCELLED", "لغو شده"),
    )
    fee_rate = models.DecimalField(
    max_digits=5,
    decimal_places=4,
    default=0.0099
)

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    order_type = models.CharField(max_length=10, choices=ORDER_TYPE)

    target_price = models.DecimalField(max_digits=20, decimal_places=0)

    amount_toman = models.DecimalField(max_digits=20, decimal_places=0, null=True, blank=True)

    gold_weight = models.DecimalField(max_digits=20, decimal_places=5, null=True, blank=True)

    estimated_weight = models.DecimalField(max_digits=20, decimal_places=5)

    status = models.CharField(max_length=20, default="PENDING", choices=STATUS)

    executed_price = models.DecimalField(max_digits=20, decimal_places=0, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)