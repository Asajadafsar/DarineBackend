    # gold_app/models.py

from django.db import models
from django.conf import settings

from accounts.models import BankCard, User


    # =========================================================
    # WALLET
    # =========================================================

    # =========================================================
    # WALLET
    # =========================================================

    # =========================================================
    # WALLET
    # =========================================================

class Wallet(models.Model):

        user = models.OneToOneField(
            settings.AUTH_USER_MODEL,
            on_delete=models.CASCADE,
            related_name="wallet"
        )

        # ==========================
        # TOMAN
        # ==========================

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
    # GOLD INVENTORY
    # =========================================================




from django.db import models
from django.conf import settings

class GoldInventory(models.Model):

        user = models.OneToOneField(
            settings.AUTH_USER_MODEL,
            on_delete=models.CASCADE,
            related_name="gold_inventory"
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
        ('REJECTED', 'ناموفق'),
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
    profit_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)  
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name




# =========================================================
# ORDERS
# =========================================================

class Order(models.Model):
    PAYMENT_CHOICES = (
        ("GOLD", "طلا"),
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

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    province = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    address = models.TextField()
    postal_code = models.CharField(max_length=20, blank=True, null=True)
    plaque = models.CharField(max_length=20, blank=True, null=True)
    unit = models.CharField(max_length=20, blank=True, null=True)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_CHOICES)
    delivery_type = models.CharField(max_length=20, choices=DELIVERY_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="REQUESTED")
    
    total_gold_amount = models.DecimalField(max_digits=20, decimal_places=3)
    total_toman_amount = models.DecimalField(max_digits=20, decimal_places=0)
    tracking_code = models.CharField(max_length=100, unique=True)
    admin_note = models.TextField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.tracking_code
    
    
    
# =========================================================
# STATUS HISTORIES
# =========================================================

class OrderStatusHistory(models.Model):
    STATUS_CHOICES = (
        ("REQUESTED", "درخواست سفارش"),
        ("PREPARING", "در حال آماده‌سازی"),
        ("DELIVERING", "در حال تحویل"),
        ("DELIVERED", "تحویل داده شد"),
        ("CANCELLED", "لغو شده"),
    )
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="status_history")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
        verbose_name = "مرحله سفارش طلا"
        verbose_name_plural = "مراحل سفارش طلا"

    def __str__(self):
        return f"{self.order.tracking_code} - {self.get_status_display()}"

# =========================================================
# ORDER ITEMS
# =========================================================

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price_at_time = models.DecimalField(max_digits=20, decimal_places=0)
    weight_at_time = models.DecimalField(max_digits=20, decimal_places=3)
    
    

# =========================================================
# PRICE ALERT
# =========================================================

class PriceAlert(models.Model):

    ALERT_CHOICES = (
        ("ABOVE", "بالاتر"),
        ("BELOW", "پایین‌تر"),
    )

    STATUS_CHOICES = (
        ("ACTIVE", "فعال"),
        ("PAUSED", "متوقف"),
        ("FINISHED", "اتمام"),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    target_price = models.DecimalField(
        max_digits=20,
        decimal_places=3
    )

    alert_type = models.CharField(
        max_length=20,
        choices=ALERT_CHOICES
    )
    triggered = models.BooleanField(default=False)

    # تعداد دفعاتی که کاربر میخواهد پیامک بگیرد
    max_notifications = models.PositiveIntegerField(default=1)

    # تعداد دفعات ارسال شده
    sent_notifications = models.PositiveIntegerField(default=0)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="ACTIVE"
    )

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    last_triggered_price = models.DecimalField(
        max_digits=20,
        decimal_places=3,
        null=True,
        blank=True
    )

    last_triggered_at = models.DateTimeField(
        null=True,
        blank=True
    )



class PriceAlertLog(models.Model):

    STATUS = (
        ("SUCCESS","موفق"),
        ("FAILED","ناموفق"),
        ("INSUFFICIENT_BALANCE","عدم موجودی"),
    )

    alert = models.ForeignKey(
        PriceAlert,
        on_delete=models.CASCADE,
        related_name="logs"
    )

    price = models.DecimalField(
        max_digits=20,
        decimal_places=3
    )

    sms_cost = models.DecimalField(
        max_digits=10,
        decimal_places=0,
        default=900
    )

    sms_status = models.CharField(
        max_length=30,
        choices=STATUS
    )

    sms_response = models.TextField(
        blank=True
    )

    created_at=models.DateTimeField(
        auto_now_add=True
    )





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
        decimal_places=3
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
        decimal_places=3
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

            GoldBankInfo.objects.exclude(
                pk=self.pk
            ).update(
                is_active=False
            )

        super().save(*args, **kwargs)

# gold_app/models.py

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

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='gold_orders'
    )

    order_type = models.CharField(max_length=10, choices=ORDER_TYPE)

    target_price = models.DecimalField(max_digits=20, decimal_places=0)

    amount_toman = models.DecimalField(max_digits=20, decimal_places=0, null=True, blank=True)

    gold_weight = models.DecimalField(max_digits=20, decimal_places=3, null=True, blank=True)

    estimated_weight = models.DecimalField(max_digits=20, decimal_places=3)

    fee_rate = models.DecimalField(max_digits=5, decimal_places=4, default=0.0099)

    status = models.CharField(max_length=20, default="PENDING", choices=STATUS)

    executed_price = models.DecimalField(max_digits=20, decimal_places=0, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    
    updated_at = models.DateTimeField(auto_now=True)
    
    description = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_order_type_display()} - {self.user.mobile} - {self.target_price}"
    
    
    
# gold_app/models.py

class GoldShortOrder(models.Model):
    """
    مدل فروش تعهدی طلا (Short Selling)
    """
    STATUS_CHOICES = (
        ('PENDING', 'در انتظار'),
        ('ACTIVE', 'فعال'),
        ('CLOSED', 'بسته شده'),
        ('LIQUIDATED', 'لیکوئید شده'),
        ('CANCELLED', 'لغو شده'),
    )
    
    ORDER_TYPE_CHOICES = (
        ('MARKET', 'قیمت بازار'),
        ('LIMIT', 'قیمت هدف'),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='gold_short_orders'
    )
    
    # نوع سفارش (بازار یا هدف)
    order_type = models.CharField(max_length=10, choices=ORDER_TYPE_CHOICES)
    
    # وزن طلا (گرم)
    weight = models.DecimalField(max_digits=20, decimal_places=3)
    
    # ضریب (1x تا 5x)
    leverage = models.PositiveSmallIntegerField(default=1, verbose_name='ضریب')
    
    # قیمت ورود (قیمتی که سفارش در آن اجرا شده)
    entry_price = models.DecimalField(max_digits=20, decimal_places=0, verbose_name='قیمت ورود')
    
    # قیمت هدف (برای سفارش LIMIT)
    target_price = models.DecimalField(max_digits=20, decimal_places=0, null=True, blank=True, verbose_name='قیمت هدف')
    
    # حد سود (اختیاری)
    take_profit = models.DecimalField(max_digits=20, decimal_places=0, null=True, blank=True, verbose_name='حد سود')
    
    # حد ضرر (اختیاری)
    stop_loss = models.DecimalField(max_digits=20, decimal_places=0, null=True, blank=True, verbose_name='حد ضرر')
    
    # قیمت بسته شدن
    close_price = models.DecimalField(max_digits=20, decimal_places=0, null=True, blank=True, verbose_name='قیمت بسته شدن')
    
    # سود/ضرر نهایی
    profit_loss = models.DecimalField(max_digits=20, decimal_places=0, default=0, verbose_name='سود/ضرر')
    
    # کارمزد اولیه (1%)
    initial_fee = models.DecimalField(max_digits=20, decimal_places=0, default=0, verbose_name='کارمزد اولیه')
    
    # کارمزد روزانه (0.65% در روز)
    daily_fee = models.DecimalField(max_digits=20, decimal_places=0, default=0, verbose_name='کارمزد روزانه')
    
    # کل کارمزد
    total_fee = models.DecimalField(max_digits=20, decimal_places=0, default=0, verbose_name='کل کارمزد')
    
    # وضعیت
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    
    # توضیحات
    description = models.TextField(blank=True, null=True)
    
    # تاریخ‌ها
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    closed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'فروش تعهدی طلا'
        verbose_name_plural = 'فروش‌های تعهدی طلا'

    def __str__(self):
        return f"Short - {self.user.mobile} - {self.weight}g - {self.entry_price}"


# =========================================================
# SHORT ORDER HISTORY (تاریخچه تغییرات)
# =========================================================

class GoldShortOrderHistory(models.Model):
    """
    تاریخچه تغییرات سفارش فروش تعهدی
    """
    order = models.ForeignKey(GoldShortOrder, on_delete=models.CASCADE, related_name='history')
    status = models.CharField(max_length=20, choices=GoldShortOrder.STATUS_CHOICES)
    price = models.DecimalField(max_digits=20, decimal_places=0)
    profit_loss = models.DecimalField(max_digits=20, decimal_places=0, default=0)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']