# silver_app/models.py

from django.db import models
from django.conf import settings


# =========================================================
# WALLET
# =========================================================

class SilverWallet(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='silver_wallet'
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

    updated_at = models.DateTimeField(auto_now=True)
# =========================================================
# INVENTORY
# =========================================================
class SilverInventory(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='silver_inventory'
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

    updated_at = models.DateTimeField(auto_now=True)



# =========================================================
# PRICE HISTORY
# =========================================================

class SilverPriceHistory(models.Model):

    price = models.DecimalField(
        max_digits=20,
        decimal_places=0
    )

    created_at = models.DateTimeField(auto_now_add=True)


# =========================================================
# TRANSACTION
# =========================================================

class SilverTransaction(models.Model):

    TYPE_CHOICES = (
        ('BUY', 'خرید'),
        ('SELL', 'فروش'),
    )

    STATUS_CHOICES = (
        ('PENDING', 'در انتظار'),
        ('COMPLETED', 'تکمیل شده'),
        ('FAILED', 'ناموفق'),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    type = models.CharField(max_length=20, choices=TYPE_CHOICES)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='COMPLETED'
    )

    amount_gr = models.DecimalField(max_digits=20, decimal_places=5)

    price_per_gram = models.DecimalField(max_digits=20, decimal_places=0)

    fee = models.DecimalField(max_digits=20, decimal_places=0, default=0)

    total_amount = models.DecimalField(max_digits=20, decimal_places=0)

    tracking_code = models.CharField(max_length=100, unique=True)

    description = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)


# =========================================================
# FINANCIAL TRANSACTION
# =========================================================

class SilverFinancialTransaction(models.Model):

    TYPE_CHOICES = (
        ('DEPOSIT', 'واریز'),
        ('WITHDRAW', 'برداشت'),
    )

    METHOD_CHOICES = (
        ('ONLINE', 'آنلاین'),
        ('CARD_TO_CARD', 'کارت به کارت'),
        ('BANK', 'بانکی'),
        ('GOLD', 'تبدیل به طلا'),
    )

    STATUS_CHOICES = (
        ('PENDING', 'در انتظار'),
        ('COMPLETED', 'تکمیل شده'),
        ('FAILED', 'ناموفق'),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    amount = models.DecimalField(max_digits=20, decimal_places=0)

    type = models.CharField(max_length=20, choices=TYPE_CHOICES)

    method = models.CharField(max_length=30, choices=METHOD_CHOICES)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING'
    )

    tracking_code = models.CharField(
        max_length=100,
        unique=True,
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)


# =========================================================
# PRODUCT
# =========================================================

class SilverProduct(models.Model):

    name = models.CharField(max_length=255)

    weight = models.DecimalField(max_digits=20, decimal_places=5)

    price = models.DecimalField(max_digits=20, decimal_places=0)

    inventory_count = models.PositiveIntegerField(default=0)

    is_active = models.BooleanField(default=True)

    image = models.ImageField(upload_to='silver/products/', null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


# =========================================================
# CART
# =========================================================

class SilverCart(models.Model):

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    product = models.ForeignKey(SilverProduct, on_delete=models.CASCADE)

    quantity = models.PositiveIntegerField(default=1)

    created_at = models.DateTimeField(auto_now_add=True)


# =========================================================
# ORDER
# =========================================================

class SilverOrder(models.Model):

    STATUS_CHOICES = (
        ('PENDING', 'در انتظار'),
        ('PROCESSING', 'در حال پردازش'),
        ('SHIPPED', 'ارسال شده'),
        ('COMPLETED', 'تکمیل شده'),
        ('CANCELLED', 'لغو شده'),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    total_silver_amount = models.DecimalField(max_digits=20, decimal_places=5)

    total_toman_amount = models.DecimalField(max_digits=20, decimal_places=0)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING'
    )

    tracking_code = models.CharField(max_length=100, unique=True)

    created_at = models.DateTimeField(auto_now_add=True)


# =========================================================
# ORDER ITEM
# =========================================================

class SilverOrderItem(models.Model):

    order = models.ForeignKey(
        SilverOrder,
        on_delete=models.CASCADE,
        related_name='items'
    )

    product = models.ForeignKey(SilverProduct, on_delete=models.CASCADE)

    quantity = models.PositiveIntegerField()

    price_at_time = models.DecimalField(max_digits=20, decimal_places=0)

    weight_at_time = models.DecimalField(max_digits=20, decimal_places=5)


# =========================================================
# PRICE ALERT
# =========================================================

class SilverPriceAlert(models.Model):

    ALERT_CHOICES = (
        ('ABOVE', 'بالاتر'),
        ('BELOW', 'پایین‌تر'),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    target_price = models.DecimalField(max_digits=20, decimal_places=5)

    alert_type = models.CharField(max_length=20, choices=ALERT_CHOICES)

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)


# =========================================================
# REFERRAL
# =========================================================

class SilverReferralEarning(models.Model):

    referrer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='silver_referral_earnings'
    )

    referred_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    amount = models.DecimalField(max_digits=20, decimal_places=0)

    created_at = models.DateTimeField(auto_now_add=True)