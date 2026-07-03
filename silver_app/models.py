# silver_app/models.py

from django.db import models
from django.conf import settings

from accounts.models import BankCard


# =========================================================
# SILVER WALLET
# =========================================================

class SilverWallet(models.Model):

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="silver_wallet"
    )

    # ===========================
    # TOMAN
    # ===========================

    accessible_toman = models.DecimalField(
        max_digits=20,
        decimal_places=0,
        default=0
    )

    blocked_toman = models.DecimalField(
        max_digits=20,
        decimal_places=0,
        default=0
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    @property
    def toman_total(self):
        return (
            self.accessible_toman +
            self.blocked_toman
        )

    def __str__(self):
        return self.user.mobile

# =========================================================
# SILVER INVENTORY
# =========================================================

class SilverInventory(models.Model):

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="silver_inventory"
    )

    accessible_balance = models.DecimalField(
        max_digits=20,
        decimal_places=3,
        default=0
    )

    blocked_balance = models.DecimalField(
        max_digits=20,
        decimal_places=3,
        default=0
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    @property
    def total_balance(self):
        return (
            self.accessible_balance +
            self.blocked_balance
        )

    def __str__(self):
        return self.user.mobile
# =========================================================
# SILVER TRANSACTION
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
        decimal_places=3
    )

    price_per_gram = models.DecimalField(
        max_digits=20,
        decimal_places=0
    )

    # مبلغ کارمزد
    fee = models.DecimalField(
        max_digits=20,
        decimal_places=0,
        default=0
    )

    # درصد کارمزد همان لحظه
    commission_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0
    )

    # مبلغ کارمزد همان لحظه
    commission_amount = models.DecimalField(
        max_digits=20,
        decimal_places=0,
        default=0
    )

    # درصد سود معرف همان لحظه
    marketer_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0
    )

    # مبلغ سود معرف همان لحظه
    profit = models.DecimalField(
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

class SilverFinancialTransaction(models.Model):

    TYPE_CHOICES = (
        ('DEPOSIT', 'واریز'),
        ('WITHDRAW', 'برداشت'),
    )

    METHOD_CHOICES = (
        ('ONLINE', 'آنلاین'),
        ('CARD_TO_CARD', 'کارت به کارت'),
        ('BANK', 'بانکی'),
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
        upload_to='silver_receipts/',
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
# PRODUCT CATEGORY
# =========================================================

class SilverProductCategory(models.Model):

    name = models.CharField(max_length=100)

    slug = models.SlugField(
        unique=True
    )

    def __str__(self):
        return self.name


# =========================================================
# PRODUCT
# =========================================================

class SilverProduct(models.Model):

    DELIVERY_CHOICES = (
        ('HOME', 'ارسال به منزل'),
        ('IN_PERSON', 'تحویل حضوری'),
    )

    category = models.ForeignKey(
        SilverProductCategory,
        on_delete=models.SET_NULL,
        null=True,
        related_name='products'
    )

    name = models.CharField(
        max_length=255
    )

    delivery_type = models.CharField(
        max_length=20,
        choices=DELIVERY_CHOICES,
        default='HOME'
    )

    weight = models.DecimalField(
        max_digits=20,
        decimal_places=3
    )

    total_weight_with_fees = models.DecimalField(
        max_digits=20,
        decimal_places=3,
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

    inventory_count = models.PositiveIntegerField(
        default=0
    )

    image = models.ImageField(
        upload_to='silver_products/',
        null=True,
        blank=True
    )

    description = models.TextField(
        blank=True,
        null=True
    )

    is_active = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )
    profit_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)  
    def __str__(self):
        return self.name


# =========================================================
# ORDER
# =========================================================

# =========================================================
# ORDER
# =========================================================

class SilverOrder(models.Model):

    PAYMENT_CHOICES = (
        ("SILVER", "نقره"),
        ("TOMAN", "کیف پول"),
    )

    DELIVERY_CHOICES = (
        ("HOME", "ارسال"),
        ("IN_PERSON", "حضوری"),
    )

    STATUS_CHOICES = (
        ("REQUESTED", "درخواست سفارش"),
        ("PREPARING", "در حال آماده‌سازی"),
        ("DELIVERING", "در حال تحویل"),
        ("DELIVERED", "تحویل داده شد"),
        ("CANCELLED", "لغو شده"),
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
        default="REQUESTED"
    )

    total_silver_amount = models.DecimalField(
        max_digits=20,
        decimal_places=3
    )

    total_toman_amount = models.DecimalField(
        max_digits=20,
        decimal_places=0
    )

    tracking_code = models.CharField(
        max_length=100,
        unique=True
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

    def __str__(self):
        return self.tracking_code
# =========================================================
# ORDER ITEM
# =========================================================

class SilverOrderItem(models.Model):

    order = models.ForeignKey(
        SilverOrder,
        on_delete=models.CASCADE,
        related_name='items'
    )

    product = models.ForeignKey(
        SilverProduct,
        on_delete=models.CASCADE
    )

    quantity = models.PositiveIntegerField()

    price_at_time = models.DecimalField(
        max_digits=20,
        decimal_places=0
    )

    weight_at_time = models.DecimalField(
        max_digits=20,
        decimal_places=3
    )

# =========================================================
# ORDER STATUS HISTORY
# =========================================================

class SilverOrderStatusHistory(models.Model):

    STATUS_CHOICES = (
        ("REQUESTED", "درخواست سفارش"),
        ("PREPARING", "در حال آماده‌سازی"),
        ("DELIVERING", "در حال تحویل"),
        ("DELIVERED", "تحویل داده شد"),
        ("CANCELLED", "لغو شده"),
    )

    order = models.ForeignKey(
        SilverOrder,
        on_delete=models.CASCADE,
        related_name="status_history"
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES
    )

    description = models.TextField(
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        ordering = ["created_at"]
        verbose_name = "مرحله سفارش نقره"
        verbose_name_plural = "مراحل سفارش نقره"

    def __str__(self):
        return (
            f"{self.order.tracking_code} - "
            f"{self.get_status_display()}"
        )
# =========================================================
# RECENT TRANSACTION
# =========================================================

class SilverRecentTransaction(models.Model):

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    title = models.CharField(
        max_length=255
    )

    amount = models.DecimalField(
        max_digits=20,
        decimal_places=0
    )

    status = models.CharField(
        max_length=50
    )

    type = models.CharField(
        max_length=50
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )


# =========================================================
# RECENT DELIVERY
# =========================================================

class SilverRecentDelivery(models.Model):

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    delivery_type = models.CharField(
        max_length=50
    )

    status = models.CharField(
        max_length=50
    )

    total_amount = models.DecimalField(
        max_digits=20,
        decimal_places=0
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )


# =========================================================
# REFERRAL EARNING
# =========================================================

class SilverReferralEarning(models.Model):

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    amount = models.DecimalField(
        max_digits=20,
        decimal_places=0
    )

    source_type = models.CharField(
        max_length=50
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )


# =========================================================
# SILVER PRICE HISTORY
# =========================================================

class SilverPriceHistory(models.Model):

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



class SilverBankInfo(models.Model):

    card_number = models.CharField(
        max_length=16,
        unique=True
    )

    full_name = models.CharField(
        max_length=255
    )

    sheba = models.CharField(
        max_length=26,
        unique=True
    )

    is_active = models.BooleanField(
        default=False
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def save(self, *args, **kwargs):

        if self.is_active:

            SilverBankInfo.objects.exclude(
                pk=self.pk
            ).update(
                is_active=False
            )

        super().save(*args, **kwargs)


class UserAddress(models.Model):

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='silver_addresses'
    )

    province = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    address = models.TextField()

    postal_code = models.CharField(max_length=20, null=True, blank=True)
    plaque = models.CharField(max_length=20, null=True, blank=True)
    unit = models.CharField(max_length=20, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)