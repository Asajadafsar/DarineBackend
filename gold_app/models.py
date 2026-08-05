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
        ("COMPLETED", "انجام شده"),
        ("FAILED", "لغو شده"),
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
        
        
        
        


# ============================================
# gold_app/models.py - مدل کامل تضمین طلا
# ============================================

from django.db import models
from django.conf import settings
from django.utils import timezone
from decimal import Decimal

# gold_app/models.py - مدل کامل تضمین طلا با منطق صحیح

from django.db import models
from django.conf import settings
from django.utils import timezone
from decimal import Decimal


# class GoldGuaranteePlan(models.Model):
#     """
#     طرح‌های تضمین طلا - مدیریت در پنل ادمین
#     """
#     name = models.CharField(max_length=100, verbose_name="نام طرح")
#     duration_days = models.PositiveIntegerField(verbose_name="مدت تعهد (روز)")
#     service_fee_percent = models.DecimalField(
#         max_digits=5, 
#         decimal_places=2, 
#         verbose_name="کارمزد سرویس (%)"
#     )
#     is_active = models.BooleanField(default=True, verbose_name="فعال")
#     description = models.TextField(blank=True, null=True, verbose_name="توضیحات")
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)

#     class Meta:
#         verbose_name = "طرح تضمین طلا"
#         verbose_name_plural = "طرح‌های تضمین طلا"
#         ordering = ['duration_days']

#     def __str__(self):
#         return f"{self.name} - {self.duration_days} روز - {self.service_fee_percent}%"


# class GoldGuarantee(models.Model):
#     """
#     مدل اصلی تضمین طلا
    
#     منطق تضمین قیمت:
#     - کاربر طلا را بلوکه می‌کند (مقدار مشخصی طلا)
#     - قیمت تضمین شده (p1) = قیمت طلا در زمان شروع طرح
#     - در سررسید، قیمت طلا (p2) بررسی می‌شود
#     - اگر p2 < p1: کاربر سود می‌کند = (p1 - p2) × وزن طلا
#     - اگر p2 >= p1: کاربر سودی نمی‌کند
#     - در هر دو حالت، طلای بلوکه شده آزاد می‌شود
#     - کارمزد سرویس از کاربر دریافت می‌شود
#     """
    
#     STATUS_CHOICES = (
#         ('ACTIVE', 'فعال'),
#         ('EXPIRED', 'منقضی شده'),
#         ('CANCELLED', 'لغو شده'),
#         ('EXECUTED', 'اجرا شده'),
#     )

#     # =============================================
#     # روابط
#     # =============================================
#     user = models.ForeignKey(
#         settings.AUTH_USER_MODEL,
#         on_delete=models.CASCADE,
#         related_name='gold_guarantees',
#         verbose_name="کاربر"
#     )

#     plan = models.ForeignKey(
#         GoldGuaranteePlan,
#         on_delete=models.PROTECT,
#         related_name='guarantees',
#         verbose_name="طرح"
#     )

#     # =============================================
#     # اطلاعات اصلی
#     # =============================================
#     gold_weight = models.DecimalField(
#         max_digits=20, 
#         decimal_places=3,
#         verbose_name="مقدار طلای تضمین شده (گرم)"
#     )

#     guaranteed_price = models.DecimalField(
#         max_digits=20, 
#         decimal_places=0,
#         verbose_name="قیمت تضمین شده (قیمت شروع - p1)"
#     )

#     service_fee = models.DecimalField(
#         max_digits=20, 
#         decimal_places=0,
#         verbose_name="کارمزد سرویس (تومان)"
#     )

#     # =============================================
#     # تاریخ‌ها
#     # =============================================
#     start_date = models.DateTimeField(
#         auto_now_add=True, 
#         verbose_name="تاریخ شروع"
#     )

#     end_date = models.DateTimeField(
#         verbose_name="تاریخ سررسید"
#     )

#     # =============================================
#     # وضعیت
#     # =============================================
#     status = models.CharField(
#         max_length=20, 
#         choices=STATUS_CHOICES, 
#         default='ACTIVE',
#         verbose_name="وضعیت"
#     )

#     # =============================================
#     # تاریخ‌های وضعیت
#     # =============================================
#     cancelled_at = models.DateTimeField(
#         null=True, 
#         blank=True, 
#         verbose_name="تاریخ لغو"
#     )

#     executed_at = models.DateTimeField(
#         null=True, 
#         blank=True, 
#         verbose_name="تاریخ اجرا"
#     )

#     # =============================================
#     # اطلاعات اجرا
#     # =============================================
#     executed_price = models.DecimalField(
#         max_digits=20, 
#         decimal_places=0,
#         null=True, 
#         blank=True,
#         verbose_name="قیمت سررسید (قیمت پایان - p2)"
#     )

#     # =============================================
#     # محاسبات مالی
#     # =============================================
#     profit_loss = models.DecimalField(
#         max_digits=20, 
#         decimal_places=0,
#         default=0,
#         verbose_name="سود/زیان کاربر"
#     )

#     platform_profit = models.DecimalField(
#         max_digits=20, 
#         decimal_places=0,
#         default=0,
#         verbose_name="سود پلتفرم (کارمزد)"
#     )

#     user_payout = models.DecimalField(
#         max_digits=20, 
#         decimal_places=0,
#         default=0,
#         verbose_name="مبلغ پرداختی به کاربر"
#     )

#     # =============================================
#     # اطلاعات تکمیلی
#     # =============================================
#     tracking_code = models.CharField(
#         max_length=50,
#         unique=True,
#         editable=False,
#         null=True,
#         blank=True,
#         verbose_name="کد رهگیری"
#     )

#     transaction = models.ForeignKey(
#         'GoldTransaction',
#         on_delete=models.SET_NULL,
#         null=True,
#         blank=True,
#         related_name='guarantee',
#         verbose_name="تراکنش مرتبط"
#     )

#     description = models.TextField(
#         blank=True, 
#         null=True, 
#         verbose_name="توضیحات"
#     )

#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)

#     class Meta:
#         verbose_name = "تضمین طلا"
#         verbose_name_plural = "تضمین‌های طلا"
#         ordering = ['-created_at']

#     def __str__(self):
#         return f"{self.user.mobile} - {self.gold_weight}g - {self.get_status_display()}"

#     # =============================================
#     # متدهای کمکی
#     # =============================================

#     def generate_tracking_code(self):
#         """تولید کد رهگیری یکتا"""
#         import random
#         import string
#         prefix = "GTD"
#         date_str = timezone.now().strftime('%Y%m%d')
#         random_part = ''.join(random.choices(string.digits + string.ascii_uppercase, k=6))
#         return f"{prefix}-{date_str}-{random_part}"

#     def save(self, *args, **kwargs):
#         if not self.tracking_code:
#             self.tracking_code = self.generate_tracking_code()
#         super().save(*args, **kwargs)

#     @property
#     def is_expired(self):
#         """بررسی انقضای طرح"""
#         return timezone.now() >= self.end_date

#     @property
#     def days_remaining(self):
#         """تعداد روزهای باقی‌مانده"""
#         if self.is_expired:
#             return 0
        
#         delta = self.end_date - timezone.now()
        
#         if delta.total_seconds() < 86400:
#             return 1
        
#         return delta.days

#     @property
#     def price_diff(self):
#         """تفاوت قیمت سررسید و قیمت تضمین"""
#         if self.executed_price is not None and self.guaranteed_price is not None:
#             return float(self.executed_price - self.guaranteed_price)
#         return 0

#     @property
#     def virtual_profit(self):
#         """
#         سود/زیان مجازی (فقط برای اطلاع کاربر)
#         اگر قیمت سررسید کمتر از قیمت تضمین باشد = سود
#         اگر قیمت سررسید بیشتر از قیمت تضمین باشد = ضرر (اما کاربر ضرر نمی‌کند)
#         """
#         if self.executed_price is not None and self.guaranteed_price is not None:
#             diff = self.guaranteed_price - self.executed_price
#             return float(diff * self.gold_weight)
#         return 0

#     # =============================================
#     # متدهای اصلی
#     # =============================================

#     def cancel(self):
#         """
#         لغو طرح تضمین
        
#         قوانین:
#         1. فقط طرح‌های فعال قابل لغو هستند
#         2. طلای بلوکه شده آزاد می‌شود
#         3. کارمزد سرویس برگشت داده نمی‌شود
#         """
#         if self.status != 'ACTIVE':
#             raise ValueError("فقط طرح‌های فعال قابل لغو هستند")
        
#         if self.is_expired:
#             raise ValueError("طرح منقضی شده است و قابل لغو نیست")

#         self.status = 'CANCELLED'
#         self.cancelled_at = timezone.now()
#         self.save()

#         from .models import GoldInventory
#         inventory, _ = GoldInventory.objects.get_or_create(user=self.user)
#         inventory.blocked_balance -= self.gold_weight
#         inventory.accessible_balance += self.gold_weight
#         inventory.save()

#         return {
#             'cancelled': True,
#             'message': 'طرح تضمین با موفقیت لغو شد. کارمزد سرویس قابل برگشت نیست.'
#         }

#     def execute(self, current_price):
#         """
#         اجرای طرح تضمین طلا در سررسید
        
#         منطق تضمین قیمت:
#         - اگر قیمت سررسید (p2) < قیمت تضمین (p1):
#             ✅ کاربر سود می‌کند = (p1 - p2) × وزن طلا
#             ✅ مبلغ سود به کیف پول کاربر واریز می‌شود
#             ✅ طلای بلوکه شده آزاد می‌شود
        
#         - اگر قیمت سررسید (p2) >= قیمت تضمین (p1):
#             ❌ کاربر سودی نمی‌کند
#             ✅ طلای بلوکه شده آزاد می‌شود
        
#         Args:
#             current_price: قیمت لحظه‌ای طلا در زمان اجرا (p2)
        
#         Returns:
#             dict: نتیجه اجرا
#         """
#         try:
#             # =============================================
#             # ۱. اعتبارسنجی
#             # =============================================
#             if self.status != 'ACTIVE':
#                 raise ValueError("فقط طرح‌های فعال قابل اجرا هستند")

#             if not self.is_expired:
#                 raise ValueError("طرح هنوز منقضی نشده است")

#             p1 = self.guaranteed_price
#             p2 = Decimal(str(current_price))

#             from .models import GoldInventory, Wallet, GoldTransaction
#             from .utils import generate_tracking_code
            
#             # =============================================
#             # ۲. آزادسازی طلا از بلوکه
#             # =============================================
#             inventory, _ = GoldInventory.objects.get_or_create(user=self.user)
#             inventory.blocked_balance -= self.gold_weight
#             inventory.accessible_balance += self.gold_weight
#             inventory.save()

#             # =============================================
#             # ۳. محاسبه سود کاربر و سود پلتفرم
#             # =============================================
#             if p2 < p1:
#                 # ✅ قیمت کاهش یافته - کاربر سود می‌کند
#                 price_diff = p1 - p2
#                 profit_amount = (price_diff * self.gold_weight).quantize(Decimal('1'))
                
#                 # واریز سود به کیف پول کاربر
#                 wallet, _ = Wallet.objects.get_or_create(user=self.user)
#                 wallet.accessible_toman += profit_amount
#                 wallet.save()
                
#                 self.user_payout = profit_amount
#                 self.profit_loss = profit_amount
#                 self.platform_profit = self.service_fee  # کارمزد = سود پلتفرم
#                 status_message = (
#                     f'قیمت کاهش یافته از {p1:,} به {p2:,} - '
#                     f'سود کاربر: {profit_amount:,} تومان'
#                 )
#             else:
#                 # ✅ قیمت افزایش یافته یا مساوی - کاربر سودی نمی‌کند
#                 self.user_payout = Decimal('0')
#                 self.profit_loss = Decimal('0')
#                 self.platform_profit = self.service_fee  # کارمزد = سود پلتفرم
#                 status_message = (
#                     f'قیمت افزایش یافته یا مساوی از {p1:,} به {p2:,} - '
#                     f'بدون سود برای کاربر'
#                 )

#             # =============================================
#             # ۴. به‌روزرسانی وضعیت
#             # =============================================
#             self.executed_at = timezone.now()
#             self.executed_price = p2
#             self.status = 'EXECUTED'
#             self.save()

#             # =============================================
#             # ۵. ثبت تراکنش
#             # =============================================
#             transaction = GoldTransaction.objects.create(
#                 user=self.user,
#                 type='SELL',
#                 status='COMPLETED',
#                 amount_gr=self.gold_weight,
#                 price_per_gram=p2,
#                 fee=0,
#                 commission_percent=0,
#                 commission_amount=0,
#                 total_amount=self.user_payout,
#                 tracking_code=generate_tracking_code('GUARANTEE'),
#                 description=f'اجرای تضمین طلا - شناسه: {self.id} - {status_message}'
#             )
#             self.transaction = transaction
#             self.save()

#             # =============================================
#             # ۶. پاسخ
#             # =============================================
#             return {
#                 'executed': True,
#                 'user_payout': float(self.user_payout),
#                 'platform_profit': float(self.platform_profit),
#                 'current_price': float(p2),
#                 'profit_loss': float(self.profit_loss),
#                 'message': f'✅ طرح تضمین با موفقیت اجرا شد. {status_message}'
#             }
            
#         except Exception as e:
#             print(f"❌ خطا در اجرای طرح تضمین: {e}")
#             import traceback
#             traceback.print_exc()
#             raise

#     def get_status_display(self):
#         """دریافت نمایش فارسی وضعیت"""
#         return dict(self.STATUS_CHOICES).get(self.status, self.status)

#     def get_info(self):
#         """
#         دریافت اطلاعات کامل طرح برای نمایش در فرانت‌اند
#         """
#         return {
#             'id': self.id,
#             'tracking_code': self.tracking_code,
#             'plan_name': self.plan.name,
#             'plan_duration': self.plan.duration_days,
#             'gold_weight': float(self.gold_weight),
#             'guaranteed_price': float(self.guaranteed_price),
#             'executed_price': float(self.executed_price) if self.executed_price else None,
#             'service_fee': float(self.service_fee),
#             'service_fee_percent': float(self.plan.service_fee_percent),
#             'start_date': self.start_date,
#             'end_date': self.end_date,
#             'status': self.status,
#             'status_display': self.get_status_display(),
#             'is_expired': self.is_expired,
#             'days_remaining': self.days_remaining,
#             'user_payout': float(self.user_payout),
#             'platform_profit': float(self.platform_profit),
#             'profit_loss': float(self.profit_loss),
#             'virtual_profit': self.virtual_profit,
#             'price_diff': self.price_diff,
#             'executed_at': self.executed_at,
#             'cancelled_at': self.cancelled_at,
#             'description': self.description,
#             'created_at': self.created_at,
#             'updated_at': self.updated_at,
#         }


# gold_app/models.py - مدل کامل GoldGuarantee

from django.db import models
from django.conf import settings
from django.utils import timezone
from decimal import Decimal


class GoldGuaranteePlan(models.Model):
    """
    طرح‌های تضمین طلا - مدیریت در پنل ادمین
    """
    name = models.CharField(max_length=100, verbose_name="نام طرح")
    duration_days = models.PositiveIntegerField(verbose_name="مدت تعهد (روز)")
    service_fee_percent = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        verbose_name="کارمزد سرویس (%)"
    )
    is_active = models.BooleanField(default=True, verbose_name="فعال")
    description = models.TextField(blank=True, null=True, verbose_name="توضیحات")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "طرح تضمین طلا"
        verbose_name_plural = "طرح‌های تضمین طلا"
        ordering = ['duration_days']

    def __str__(self):
        return f"{self.name} - {self.duration_days} روز - {self.service_fee_percent}%"


class GoldGuarantee(models.Model):
    """
    مدل اصلی تضمین طلا
    
    منطق تضمین قیمت:
    - کاربر طلا را بلوکه می‌کند (مقدار مشخصی طلا)
    - قیمت تضمین شده (p1) = قیمت طلا در زمان شروع طرح
    - در سررسید، قیمت طلا (p2) بررسی می‌شود
    - اگر p2 < p1: کاربر سود می‌کند = (p1 - p2) × وزن طلا
    - اگر p2 >= p1: کاربر سودی نمی‌کند
    - در هر دو حالت، طلای بلوکه شده آزاد می‌شود
    - کارمزد سرویس از کاربر دریافت می‌شود
    """
    
    STATUS_CHOICES = (
        ('ACTIVE', 'فعال'),
        ('EXPIRED', 'منقضی شده'),
        ('CANCELLED', 'لغو شده'),
        ('EXECUTED', 'اجرا شده'),
    )

    # =============================================
    # روابط
    # =============================================
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='gold_guarantees',
        verbose_name="کاربر"
    )

    plan = models.ForeignKey(
        GoldGuaranteePlan,
        on_delete=models.PROTECT,
        related_name='guarantees',
        verbose_name="طرح"
    )

    # =============================================
    # اطلاعات اصلی
    # =============================================
    gold_weight = models.DecimalField(
        max_digits=20, 
        decimal_places=3,
        verbose_name="مقدار طلای تضمین شده (گرم)"
    )

    guaranteed_price = models.DecimalField(
        max_digits=20, 
        decimal_places=0,
        verbose_name="قیمت تضمین شده (قیمت شروع - p1)"
    )

    service_fee = models.DecimalField(
        max_digits=20, 
        decimal_places=0,
        verbose_name="کارمزد سرویس (تومان)"
    )

    # =============================================
    # تاریخ‌ها
    # =============================================
    start_date = models.DateTimeField(
        auto_now_add=True, 
        verbose_name="تاریخ شروع"
    )

    end_date = models.DateTimeField(
        verbose_name="تاریخ سررسید"
    )

    # =============================================
    # وضعیت
    # =============================================
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='ACTIVE',
        verbose_name="وضعیت"
    )

    # =============================================
    # تاریخ‌های وضعیت
    # =============================================
    cancelled_at = models.DateTimeField(
        null=True, 
        blank=True, 
        verbose_name="تاریخ لغو"
    )

    executed_at = models.DateTimeField(
        null=True, 
        blank=True, 
        verbose_name="تاریخ اجرا"
    )

    # =============================================
    # اطلاعات اجرا
    # =============================================
    executed_price = models.DecimalField(
        max_digits=20, 
        decimal_places=0,
        null=True, 
        blank=True,
        verbose_name="قیمت سررسید (قیمت پایان - p2)"
    )

    # =============================================
    # محاسبات مالی
    # =============================================
    profit_loss = models.DecimalField(
        max_digits=20, 
        decimal_places=0,
        default=0,
        verbose_name="سود/زیان کاربر"
    )

    platform_profit = models.DecimalField(
        max_digits=20, 
        decimal_places=0,
        default=0,
        verbose_name="سود پلتفرم (کارمزد)"
    )

    user_payout = models.DecimalField(
        max_digits=20, 
        decimal_places=0,
        default=0,
        verbose_name="مبلغ پرداختی به کاربر"
    )

    # =============================================
    # اطلاعات تکمیلی
    # =============================================
    tracking_code = models.CharField(
        max_length=50,
        unique=True,
        editable=False,
        null=True,
        blank=True,
        verbose_name="کد رهگیری"
    )

    transaction = models.ForeignKey(
        'GoldTransaction',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='guarantee',
        verbose_name="تراکنش مرتبط"
    )

    description = models.TextField(
        blank=True, 
        null=True, 
        verbose_name="توضیحات"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "تضمین طلا"
        verbose_name_plural = "تضمین‌های طلا"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.mobile} - {self.gold_weight}g - {self.get_status_display()}"

    # =============================================
    # متدهای کمکی
    # =============================================

    def generate_tracking_code(self):
        """تولید کد رهگیری یکتا"""
        import random
        import string
        prefix = "GTD"
        date_str = timezone.now().strftime('%Y%m%d')
        random_part = ''.join(random.choices(string.digits + string.ascii_uppercase, k=6))
        return f"{prefix}-{date_str}-{random_part}"

    def save(self, *args, **kwargs):
        if not self.tracking_code:
            self.tracking_code = self.generate_tracking_code()
        super().save(*args, **kwargs)

    @property
    def is_expired(self):
        """بررسی انقضای طرح"""
        return timezone.now() >= self.end_date

    @property
    def days_remaining(self):
        """تعداد روزهای باقی‌مانده"""
        if self.is_expired:
            return 0
        
        delta = self.end_date - timezone.now()
        
        if delta.total_seconds() < 86400:
            return 1
        
        return delta.days

    @property
    def price_diff(self):
        """تفاوت قیمت سررسید و قیمت تضمین"""
        if self.executed_price is not None and self.guaranteed_price is not None:
            return float(self.executed_price - self.guaranteed_price)
        return 0

    @property
    def virtual_profit(self):
        """
        سود/زیان مجازی (فقط برای اطلاع کاربر)
        اگر قیمت سررسید کمتر از قیمت تضمین باشد = سود
        اگر قیمت سررسید بیشتر از قیمت تضمین باشد = ضرر (اما کاربر ضرر نمی‌کند)
        """
        if self.executed_price is not None and self.guaranteed_price is not None:
            diff = self.guaranteed_price - self.executed_price
            return float(diff * self.gold_weight)
        return 0

    @property
    def platform_profit_with_sign(self):
        """
        سود پلتفرم با علامت مثبت/منفی
        """
        profit = self.platform_profit or 0
        if profit > 0:
            return f"+{int(profit):,}"
        elif profit < 0:
            return f"{int(profit):,}"
        return "۰"

    @property
    def platform_profit_color(self):
        """
        رنگ سود پلتفرم:
        - سبز: سود > 0
        - قرمز: سود < 0
        - خاکستری: سود = 0
        """
        profit = self.platform_profit or 0
        if profit > 0:
            return "success"
        elif profit < 0:
            return "danger"
        return "secondary"

    @property
    def platform_profit_sign(self):
        """
        علامت سود پلتفرم برای نمایش
        """
        profit = self.platform_profit or 0
        if profit > 0:
            return "positive"
        elif profit < 0:
            return "negative"
        return "zero"

    # =============================================
    # متدهای اصلی
    # =============================================

    def cancel(self):
        """
        لغو طرح تضمین
        
        قوانین:
        1. فقط طرح‌های فعال قابل لغو هستند
        2. طلای بلوکه شده آزاد می‌شود
        3. کارمزد سرویس برگشت داده نمی‌شود
        """
        if self.status != 'ACTIVE':
            raise ValueError("فقط طرح‌های فعال قابل لغو هستند")
        
        if self.is_expired:
            raise ValueError("طرح منقضی شده است و قابل لغو نیست")

        self.status = 'CANCELLED'
        self.cancelled_at = timezone.now()
        self.save()

        from .models import GoldInventory
        inventory, _ = GoldInventory.objects.get_or_create(user=self.user)
        inventory.blocked_balance -= self.gold_weight
        inventory.accessible_balance += self.gold_weight
        inventory.save()

        return {
            'cancelled': True,
            'message': 'طرح تضمین با موفقیت لغو شد. کارمزد سرویس قابل برگشت نیست.'
        }

    def execute(self, current_price):
        """
        اجرای طرح تضمین طلا در سررسید
        
        منطق تضمین قیمت:
        - اگر قیمت سررسید (p2) < قیمت تضمین (p1):
            ✅ کاربر سود می‌کند = (p1 - p2) × وزن طلا
            ✅ مبلغ سود به کیف پول کاربر واریز می‌شود
            ✅ طلای بلوکه شده آزاد می‌شود
        
        - اگر قیمت سررسید (p2) >= قیمت تضمین (p1):
            ❌ کاربر سودی نمی‌کند
            ✅ طلای بلوکه شده آزاد می‌شود
        
        Args:
            current_price: قیمت لحظه‌ای طلا در زمان اجرا (p2)
        
        Returns:
            dict: نتیجه اجرا
        """
        try:
            # =============================================
            # ۱. اعتبارسنجی
            # =============================================
            if self.status != 'ACTIVE':
                raise ValueError("فقط طرح‌های فعال قابل اجرا هستند")

            if not self.is_expired:
                raise ValueError("طرح هنوز منقضی نشده است")

            p1 = self.guaranteed_price
            p2 = Decimal(str(current_price))

            from .models import GoldInventory, Wallet, GoldTransaction
            from .utils import generate_tracking_code
            
            # =============================================
            # ۲. آزادسازی طلا از بلوکه
            # =============================================
            inventory, _ = GoldInventory.objects.get_or_create(user=self.user)
            inventory.blocked_balance -= self.gold_weight
            inventory.accessible_balance += self.gold_weight
            inventory.save()

            # =============================================
            # ۳. محاسبه سود کاربر و سود پلتفرم
            # =============================================
            if p2 < p1:
                # ✅ قیمت کاهش یافته - کاربر سود می‌کند
                price_diff = p1 - p2
                profit_amount = (price_diff * self.gold_weight).quantize(Decimal('1'))
                
                # واریز سود به کیف پول کاربر
                wallet, _ = Wallet.objects.get_or_create(user=self.user)
                wallet.accessible_toman += profit_amount
                wallet.save()
                
                self.user_payout = profit_amount
                self.profit_loss = profit_amount
                # ✅ سود پلتفرم = کارمزد - مبلغ پرداختی به کاربر
                self.platform_profit = self.service_fee - profit_amount
                status_message = (
                    f'قیمت کاهش یافته از {p1:,} به {p2:,} - '
                    f'سود کاربر: {profit_amount:,} تومان - '
                    f'سود پلتفرم: {self.platform_profit:,} تومان'
                )
            else:
                # ✅ قیمت افزایش یافته یا مساوی - کاربر سودی نمی‌کند
                self.user_payout = Decimal('0')
                self.profit_loss = Decimal('0')
                # ✅ سود پلتفرم = کارمزد (چون به کاربر سودی پرداخت نشده)
                self.platform_profit = self.service_fee
                status_message = (
                    f'قیمت افزایش یافته یا مساوی از {p1:,} به {p2:,} - '
                    f'بدون سود برای کاربر - '
                    f'سود پلتفرم: {self.platform_profit:,} تومان'
                )

            # =============================================
            # ۴. به‌روزرسانی وضعیت
            # =============================================
            self.executed_at = timezone.now()
            self.executed_price = p2
            self.status = 'EXECUTED'
            self.save()

            # =============================================
            # ۵. ثبت تراکنش
            # =============================================
            transaction = GoldTransaction.objects.create(
                user=self.user,
                type='SELL',
                status='COMPLETED',
                amount_gr=self.gold_weight,
                price_per_gram=p2,
                fee=0,
                commission_percent=0,
                commission_amount=0,
                total_amount=self.user_payout,
                tracking_code=generate_tracking_code('GUARANTEE'),
                description=f'اجرای تضمین طلا - شناسه: {self.id} - {status_message}'
            )
            self.transaction = transaction
            self.save()

            # =============================================
            # ۶. پاسخ
            # =============================================
            return {
                'executed': True,
                'user_payout': float(self.user_payout),
                'platform_profit': float(self.platform_profit),
                'current_price': float(p2),
                'profit_loss': float(self.profit_loss),
                'message': f'✅ طرح تضمین با موفقیت اجرا شد. {status_message}'
            }
            
        except Exception as e:
            print(f"❌ خطا در اجرای طرح تضمین: {e}")
            import traceback
            traceback.print_exc()
            raise

    def get_status_display(self):
        """دریافت نمایش فارسی وضعیت"""
        return dict(self.STATUS_CHOICES).get(self.status, self.status)

    def get_info(self):
        """
        دریافت اطلاعات کامل طرح برای نمایش در فرانت‌اند
        """
        return {
            'id': self.id,
            'tracking_code': self.tracking_code,
            'plan_name': self.plan.name,
            'plan_duration': self.plan.duration_days,
            'gold_weight': float(self.gold_weight),
            'guaranteed_price': float(self.guaranteed_price),
            'executed_price': float(self.executed_price) if self.executed_price else None,
            'service_fee': float(self.service_fee),
            'service_fee_percent': float(self.plan.service_fee_percent),
            'start_date': self.start_date,
            'end_date': self.end_date,
            'status': self.status,
            'status_display': self.get_status_display(),
            'is_expired': self.is_expired,
            'days_remaining': self.days_remaining,
            'user_payout': float(self.user_payout),
            'platform_profit': float(self.platform_profit),
            'platform_profit_display': self.platform_profit_with_sign,
            'platform_profit_color': self.platform_profit_color,
            'platform_profit_sign': self.platform_profit_sign,
            'profit_loss': float(self.profit_loss),
            'virtual_profit': self.virtual_profit,
            'price_diff': self.price_diff,
            'executed_at': self.executed_at,
            'cancelled_at': self.cancelled_at,
            'description': self.description,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
        }

# =========================================================
# GOLD INVESTMENT
# =========================================================

# gold_app/models.py - مدل‌های کامل سرمایه‌گذاری

from django.db import models
from django.conf import settings
from django.utils import timezone
from decimal import Decimal


# =========================================================
# GOLD INVESTMENT PLAN
# =========================================================

class GoldInvestmentPlan(models.Model):
    """
    طرح‌های سرمایه‌گذاری طلا - مدیریت در پنل ادمین
    """
    name = models.CharField(max_length=100, verbose_name="نام طرح")
    
    # مدت به روز
    duration_days = models.PositiveIntegerField(
        verbose_name="مدت سرمایه‌گذاری (روز)",
        help_text="تعداد روزهای سرمایه‌گذاری (مثلاً 30، 90، 180، 365)"
    )
    
    # سود کل (درصد) - ادمین مستقیماً وارد می‌کند
    total_profit_percent = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        verbose_name="سود کل (%)",
        help_text="مثلاً 30 برای ۳۰٪ سود در کل دوره",
        default=0
    )
    
    is_active = models.BooleanField(default=True, verbose_name="فعال")
    description = models.TextField(blank=True, null=True, verbose_name="توضیحات")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "طرح سرمایه‌گذاری طلا"
        verbose_name_plural = "طرح‌های سرمایه‌گذاری طلا"
        ordering = ['duration_days']

    def __str__(self):
        return f"{self.name} - {self.duration_days} روز - {self.total_profit_percent}% سود"


# =========================================================
# GOLD INVESTMENT
# =========================================================

class GoldInvestment(models.Model):
    """
    مدل اصلی سرمایه‌گذاری طلا
    """
    STATUS_CHOICES = (
        ('ACTIVE', 'فعال'),
        ('COMPLETED', 'تکمیل شده'),
        ('CANCELLED', 'لغو شده'),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='gold_investments'
    )

    plan = models.ForeignKey(
        GoldInvestmentPlan,
        on_delete=models.PROTECT,
        related_name='investments'
    )

    # مقدار طلای سرمایه‌گذاری شده (گرم)
    gold_weight = models.DecimalField(
        max_digits=20, 
        decimal_places=3,
        verbose_name="مقدار طلای سرمایه‌گذاری شده"
    )

    # قیمت طلا در زمان سرمایه‌گذاری
    investment_price = models.DecimalField(
        max_digits=20, 
        decimal_places=0,
        verbose_name="قیمت سرمایه‌گذاری"
    )

    # تاریخ شروع
    start_date = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ شروع")

    # تاریخ پایان
    end_date = models.DateTimeField(verbose_name="تاریخ پایان")

    # سود کل مورد انتظار (گرم)
    expected_profit = models.DecimalField(
        max_digits=20, 
        decimal_places=3,
        default=0,
        verbose_name="سود کل مورد انتظار"
    )

    # سود پرداخت شده تا الان (گرم)
    paid_profit = models.DecimalField(
        max_digits=20, 
        decimal_places=3,
        default=0,
        verbose_name="سود پرداخت شده"
    )

    # سود پرداخت شده به تومان (برای نمایش)
    paid_profit_toman = models.DecimalField(
        max_digits=20, 
        decimal_places=0,
        default=0,
        verbose_name="سود پرداخت شده (تومان)"
    )

    # سود انصراف (در صورت لغو قبل از موعد)
    cancellation_profit = models.DecimalField(
        max_digits=20, 
        decimal_places=3,
        default=0,
        verbose_name="سود انصراف"
    )

    # وضعیت
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='ACTIVE',
        verbose_name="وضعیت"
    )

    # تاریخ لغو
    cancelled_at = models.DateTimeField(null=True, blank=True, verbose_name="تاریخ لغو")

    # تاریخ تکمیل
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name="تاریخ تکمیل")

    # آخرین تاریخ پرداخت سود
    last_profit_paid_at = models.DateTimeField(null=True, blank=True, verbose_name="آخرین پرداخت سود")

    # کد رهگیری
    tracking_code = models.CharField(
        max_length=50,
        unique=True,
        editable=False,
        null=True,
        blank=True,
        verbose_name="کد رهگیری"
    )

    description = models.TextField(blank=True, null=True, verbose_name="توضیحات")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "سرمایه‌گذاری طلا"
        verbose_name_plural = "سرمایه‌گذاری‌های طلا"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.mobile} - {self.gold_weight}g - {self.get_status_display()}"

    def generate_tracking_code(self):
        """تولید کد رهگیری یکتا"""
        import random
        import string
        prefix = "INV"
        date_str = timezone.now().strftime('%Y%m%d')
        random_part = ''.join(random.choices(string.digits + string.ascii_uppercase, k=6))
        return f"{prefix}-{date_str}-{random_part}"

    def save(self, *args, **kwargs):
        if not self.tracking_code:
            self.tracking_code = self.generate_tracking_code()
        super().save(*args, **kwargs)

    @property
    def is_completed(self):
        """بررسی تکمیل دوره"""
        return timezone.now() >= self.end_date

    @property
    def days_passed(self):
        """تعداد روزهای گذشته از شروع"""
        delta = timezone.now() - self.start_date
        return max(0, delta.days)

    @property
    def total_days(self):
        """تعداد کل روزهای طرح"""
        return self.plan.duration_days

    @property
    def remaining_days(self):
        """تعداد روزهای باقی‌مانده"""
        return max(0, self.total_days - self.days_passed)

    @property
    def total_expected_profit(self):
        """سود کل مورد انتظار (گرم)"""
        return (self.gold_weight * self.plan.total_profit_percent / 100).quantize(Decimal('0.001'))

    @property
    def total_return_amount(self):
        """مبلغ کل بازگشتی در پایان دوره (گرم)"""
        return self.gold_weight + self.total_expected_profit

    @property
    def cancellation_profit_amount(self):
        """
        سود انصراف - در صورت لغو قبل از موعد
        ✅ فقط در صورت تکمیل دوره، سود کامل تعلق می‌گیرد
        """
        # اگر طرح کامل نشده، سودی تعلق نمی‌گیرد
        if not self.is_completed:
            return Decimal('0')
        return self.total_expected_profit

    def calculate_profit(self):
        """محاسبه و پرداخت سود - فقط در پایان دوره"""
        from .models import GoldInventory, GoldTransaction
        from .utils import generate_tracking_code
        
        if self.status != 'ACTIVE':
            return

        # فقط اگر دوره کامل شده باشد
        if not self.is_completed:
            return

        # پرداخت کل سود یکجا
        total_profit = self.total_expected_profit
        
        if total_profit <= 0:
            return

        inventory, _ = GoldInventory.objects.get_or_create(user=self.user)
        inventory.accessible_balance += total_profit
        inventory.save()

        self.paid_profit = total_profit
        self.last_profit_paid_at = timezone.now()
        self.save()

        GoldTransaction.objects.create(
            user=self.user,
            type='BUY',
            status='COMPLETED',
            amount_gr=total_profit,
            price_per_gram=self.investment_price,
            fee=0,
            commission_percent=0,
            commission_amount=0,
            total_amount=0,
            tracking_code=generate_tracking_code('INVESTMENT'),
            description=f'سود سرمایه‌گذاری طلا - طرح {self.plan.name}'
        )

    def cancel(self):
        """لغو سرمایه‌گذاری"""
        from .models import GoldInventory
        
        if self.status != 'ACTIVE':
            raise ValueError("فقط سرمایه‌گذاری‌های فعال قابل لغو هستند")

        # محاسبه سود انصراف (در صورت تکمیل دوره)
        cancel_profit = self.cancellation_profit_amount
        
        self.status = 'CANCELLED'
        self.cancelled_at = timezone.now()
        self.cancellation_profit = cancel_profit
        self.save()

        # برگرداندن طلای بلوکه شده
        inventory, _ = GoldInventory.objects.get_or_create(user=self.user)
        inventory.blocked_balance -= self.gold_weight
        inventory.accessible_balance += self.gold_weight
        inventory.save()

        # اگر سود انصراف وجود دارد، اضافه کن
        if cancel_profit > 0:
            inventory.accessible_balance += cancel_profit
            inventory.save()

        return {
            'cancelled': True,
            'cancel_profit': cancel_profit,
            'message': f'سرمایه‌گذاری لغو شد. سود انصراف: {cancel_profit} گرم'
        }

    def complete(self):
        """تکمیل سرمایه‌گذاری در پایان دوره"""
        from .models import GoldInventory
        
        if self.status != 'ACTIVE':
            return

        if not self.is_completed:
            return

        # پرداخت سود کل
        self.calculate_profit()

        # آزادسازی طلای بلوکه شده
        inventory, _ = GoldInventory.objects.get_or_create(user=self.user)
        inventory.blocked_balance -= self.gold_weight
        inventory.accessible_balance += self.gold_weight
        inventory.save()

        self.status = 'COMPLETED'
        self.completed_at = timezone.now()
        self.save()

    def get_status_display(self):
        """دریافت نمایش فارسی وضعیت"""
        return dict(self.STATUS_CHOICES).get(self.status, self.status)  
# gold_app/models.py
# gold_app/models.py

# class Invoice(models.Model):
#     """مدل فاکتور"""
#     INVOICE_TYPES = (
#         ('BUY', 'فاکتور خرید'),
#         ('SELL', 'فاکتور فروش'),
#     )
    
#     INVOICE_STATUS = (
#         ('PENDING', 'در انتظار تایید'),
#         ('CONFIRMED', 'تایید شده'),
#         ('CANCELLED', 'لغو شده'),
#     )
    
#     # ارتباط با تراکنش
#     transaction = models.OneToOneField(
#         GoldTransaction,
#         on_delete=models.CASCADE,
#         related_name='invoice',
#         null=True,
#         blank=True
#     )
    
#     # اطلاعات فاکتور
#     invoice_number = models.CharField(max_length=50, unique=True)
#     invoice_type = models.CharField(max_length=10, choices=INVOICE_TYPES)
#     invoice_date = models.DateTimeField(auto_now_add=True)
#     status = models.CharField(max_length=20, choices=INVOICE_STATUS, default='PENDING')
    
#     # اطلاعات خریدار/فروشنده
#     buyer_name = models.CharField(max_length=200, blank=True, null=True)
#     buyer_national_id = models.CharField(max_length=20, blank=True, null=True)
#     buyer_phone = models.CharField(max_length=20, blank=True, null=True)
#     buyer_address = models.TextField(blank=True, null=True)
    
#     # اطلاعات فروشنده (✅ با مشخصات جدید)
#     seller_name = models.CharField(max_length=200, default='فروشگاه دارینه')
#     seller_national_id = models.CharField(max_length=20, default='0371439477')
#     seller_phone = models.CharField(max_length=20, default='09191608771')
#     seller_address = models.TextField(default='قم، پاساژ شهر طلا، پلاک ۲۱')
    
#     # اطلاعات طلا
#     gold_weight = models.DecimalField(max_digits=20, decimal_places=3)
#     gold_carat = models.IntegerField(default=18)
#     gold_price_per_gram = models.DecimalField(max_digits=20, decimal_places=0)
#     pure_gold_price = models.DecimalField(max_digits=20, decimal_places=0)
#     fee_rate = models.DecimalField(max_digits=5, decimal_places=2)
#     fee_amount = models.DecimalField(max_digits=20, decimal_places=0)
#     total_amount = models.DecimalField(max_digits=20, decimal_places=0)
    
#     # اطلاعات اضافی
#     tracking_code = models.CharField(max_length=100)
#     description = models.TextField(blank=True, null=True)
    
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)
    
#     class Meta:
#         ordering = ['-created_at']
    
#     def __str__(self):
#         return f"{self.invoice_number} - {self.get_invoice_type_display()}"
    
#     def generate_invoice_number(self):
#         """تولید شماره فاکتور"""
#         from datetime import datetime
#         import jdatetime
        
#         now = jdatetime.datetime.now()
#         date_str = now.strftime('%Y%m%d')
        
#         last_invoice = Invoice.objects.filter(
#             invoice_number__startswith=f"{self.invoice_type}-{date_str}"
#         ).order_by('-invoice_number').first()
        
#         if last_invoice:
#             last_num = int(last_invoice.invoice_number.split('-')[-1])
#             new_num = last_num + 1
#         else:
#             new_num = 1
            
#         return f"{self.invoice_type}-{date_str}-{new_num:04d}"


# gold_app/models.py - اضافه کردن مدل Invoice

class Invoice(models.Model):
    """مدل فاکتور خرید/فروش طلا"""
    
    INVOICE_TYPE_CHOICES = (
        ('BUY', 'خرید'),
        ('SELL', 'فروش'),
    )
    
    STATUS_CHOICES = (
        ('PENDING', 'در انتظار'),
        ('CONFIRMED', 'تایید شده'),
        ('REJECTED', 'رد شده'),
    )
    
    # ارتباط با تراکنش
    transaction = models.ForeignKey(
        GoldTransaction,
        on_delete=models.CASCADE,
        related_name='invoices',
        verbose_name="تراکنش"
    )
    
    # شماره فاکتور
    invoice_number = models.CharField(
        max_length=50,
        unique=True,
        editable=False,
        verbose_name="شماره فاکتور"
    )
    
    # نوع فاکتور
    invoice_type = models.CharField(
        max_length=10,
        choices=INVOICE_TYPE_CHOICES,
        verbose_name="نوع فاکتور"
    )
    
    # تاریخ فاکتور
    invoice_date = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ فاکتور")
    
    # وضعیت
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING',
        verbose_name="وضعیت"
    )
    
    # ========== اطلاعات خریدار ==========
    buyer_name = models.CharField(max_length=200, blank=True, null=True, verbose_name="نام خریدار")
    buyer_national_id = models.CharField(max_length=20, blank=True, null=True, verbose_name="کد ملی خریدار")
    buyer_phone = models.CharField(max_length=20, blank=True, null=True, verbose_name="تلفن خریدار")
    buyer_address = models.TextField(blank=True, null=True, verbose_name="آدرس خریدار")
    buyer_province = models.CharField(max_length=100, blank=True, null=True, verbose_name="استان خریدار")
    
    # ========== اطلاعات فروشنده ==========
    seller_name = models.CharField(max_length=200, blank=True, null=True, verbose_name="نام فروشنده")
    # seller_national_id = models.CharField(max_length=20, blank=True, null=True, verbose_name="کد ملی فروشنده")
    # seller_phone = models.CharField(max_length=20, blank=True, null=True, verbose_name="تلفن فروشنده")
    seller_address = models.TextField(blank=True, null=True, verbose_name="آدرس فروشنده")
    seller_province = models.CharField(max_length=100, blank=True, null=True, verbose_name="استان فروشنده")
    
    # ========== اطلاعات طلا ==========
    gold_weight = models.DecimalField(
        max_digits=20, decimal_places=3,
        verbose_name="وزن طلا (گرم)"
    )
    gold_carat = models.PositiveSmallIntegerField(default=18, verbose_name="عیار طلا")
    gold_price_per_gram = models.DecimalField(
        max_digits=20, decimal_places=0,
        verbose_name="قیمت هر گرم طلا"
    )
    pure_gold_price = models.DecimalField(
        max_digits=20, decimal_places=0,
        verbose_name="قیمت خالص طلا"
    )
    fee_rate = models.DecimalField(
        max_digits=5, decimal_places=2,
        default=0,
        verbose_name="درصد کارمزد"
    )
    fee_amount = models.DecimalField(
        max_digits=20, decimal_places=0,
        default=0,
        verbose_name="مبلغ کارمزد"
    )
    total_amount = models.DecimalField(
        max_digits=20, decimal_places=0,
        verbose_name="مبلغ کل"
    )
    
    # کد رهگیری
    tracking_code = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="کد رهگیری"
    )
    
    description = models.TextField(blank=True, null=True, verbose_name="توضیحات")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "فاکتور"
        verbose_name_plural = "فاکتورها"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.invoice_number} - {self.get_invoice_type_display()}"
    
    def generate_invoice_number(self):
        """تولید شماره فاکتور"""
        import jdatetime
        now = jdatetime.datetime.now()
        prefix = 'INV'
        date_part = now.strftime('%Y%m%d')
        
        # پیدا کردن آخرین فاکتور امروز
        last_invoice = Invoice.objects.filter(
            invoice_number__startswith=f'{prefix}-{date_part}'
        ).order_by('-id').first()
        
        if last_invoice:
            # استخراج شماره آخر
            last_num = int(last_invoice.invoice_number.split('-')[-1])
            new_num = last_num + 1
        else:
            new_num = 1
        
        return f"{prefix}-{date_part}-{new_num:04d}"
    
    
    
# gold_app/models.py - اضافه کردن مدل PhysicalOrderInvoice

class PhysicalOrderInvoice(models.Model):
    """
    مدل فاکتور سفارشات فیزیکی (مستقل از فاکتور آب شده)
    """
    
    INVOICE_TYPE_CHOICES = (
        ('BUY', 'خرید'),
        ('SELL', 'فروش'),
    )
    
    STATUS_CHOICES = (
        ('PENDING', 'در انتظار'),
        ('CONFIRMED', 'تایید شده'),
        ('REJECTED', 'رد شده'),
    )
    
    # =============================================
    # ارتباط با سفارش
    # =============================================
    order = models.ForeignKey(
        'Order',
        on_delete=models.CASCADE,
        related_name='physical_invoices',
        verbose_name="سفارش فیزیکی"
    )
    
    # =============================================
    # اطلاعات پایه فاکتور
    # =============================================
    invoice_number = models.CharField(
        max_length=50,
        unique=True,
        editable=False,
        verbose_name="شماره فاکتور"
    )
    
    invoice_type = models.CharField(
        max_length=10,
        choices=INVOICE_TYPE_CHOICES,
        default='BUY',
        verbose_name="نوع فاکتور"
    )
    
    invoice_date = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ فاکتور")
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING',
        verbose_name="وضعیت"
    )
    
    # =============================================
    # اطلاعات خریدار (کاربر)
    # =============================================
    buyer_name = models.CharField(max_length=200, blank=True, null=True, verbose_name="نام خریدار")
    buyer_national_id = models.CharField(max_length=20, blank=True, null=True, verbose_name="کد ملی خریدار")
    buyer_phone = models.CharField(max_length=20, blank=True, null=True, verbose_name="تلفن خریدار")
    buyer_address = models.TextField(blank=True, null=True, verbose_name="آدرس خریدار")
    buyer_province = models.CharField(max_length=100, blank=True, null=True, verbose_name="استان خریدار")
    buyer_city = models.CharField(max_length=100, blank=True, null=True, verbose_name="شهر خریدار")
    buyer_postal_code = models.CharField(max_length=20, blank=True, null=True, verbose_name="کد پستی خریدار")
    
    # =============================================
    # اطلاعات فروشنده (دارینه)
    # =============================================
    seller_name = models.CharField(max_length=200, default='فروشگاه دارینه', verbose_name="نام فروشنده")
    seller_national_id = models.CharField(max_length=20, default='0371439477', verbose_name="کد ملی فروشنده")
    seller_phone = models.CharField(max_length=20, default='09191608771', verbose_name="تلفن فروشنده")
    seller_address = models.TextField(default='قم، پاساژ شهر طلا، پلاک ۲۱', verbose_name="آدرس فروشنده")
    seller_province = models.CharField(max_length=100, default='قم', verbose_name="استان فروشنده")
    
    # =============================================
    # اطلاعات سفارش
    # =============================================
    order_tracking_code = models.CharField(
        max_length=50,
        verbose_name="کد رهگیری سفارش"
    )
    
    payment_method = models.CharField(
        max_length=20,
        choices=[('TOMAN', 'کیف پول'), ('GOLD', 'طلا')],
        verbose_name="روش پرداخت"
    )
    
    # =============================================
    # اطلاعات طلا
    # =============================================
    gold_weight = models.DecimalField(
        max_digits=20, 
        decimal_places=3,
        verbose_name="وزن طلا (گرم)"
    )
    
    gold_carat = models.PositiveSmallIntegerField(
        default=18, 
        verbose_name="عیار طلا"
    )
    
    gold_price_per_gram = models.DecimalField(
        max_digits=20, 
        decimal_places=0,
        verbose_name="قیمت هر گرم طلا"
    )
    
    pure_gold_price = models.DecimalField(
        max_digits=20, 
        decimal_places=0,
        verbose_name="قیمت خالص طلا"
    )
    
    # =============================================
    # اطلاعات مالی
    # =============================================
    shipping_fee = models.DecimalField(
        max_digits=20, 
        decimal_places=0,
        default=0,
        verbose_name="هزینه ارسال"
    )
    
    tax_amount = models.DecimalField(
        max_digits=20, 
        decimal_places=0,
        default=0,
        verbose_name="مالیات"
    )
    
    discount_amount = models.DecimalField(
        max_digits=20, 
        decimal_places=0,
        default=0,
        verbose_name="تخفیف"
    )
    
    total_amount = models.DecimalField(
        max_digits=20, 
        decimal_places=0,
        verbose_name="مبلغ کل"
    )
    
    # =============================================
    # اطلاعات محصولات
    # =============================================
    products_summary = models.JSONField(
        default=list,
        verbose_name="خلاصه محصولات",
        help_text="لیست محصولات با نام، تعداد، قیمت و وزن"
    )
    
    # =============================================
    # اطلاعات تکمیلی
    # =============================================
    description = models.TextField(blank=True, null=True, verbose_name="توضیحات")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "فاکتور سفارش فیزیکی"
        verbose_name_plural = "فاکتورهای سفارش فیزیکی"
        ordering = ['-created_at']
        db_table = 'gold_app_physical_order_invoice'
    
    def __str__(self):
        return f"{self.invoice_number} - {self.order_tracking_code}"
    
    def generate_invoice_number(self):
        """تولید شماره فاکتور منحصر به فرد"""
        import jdatetime
        now = jdatetime.datetime.now()
        prefix = 'POI'  # Physical Order Invoice
        date_part = now.strftime('%Y%m%d')
        
        # پیدا کردن آخرین فاکتور امروز
        last_invoice = PhysicalOrderInvoice.objects.filter(
            invoice_number__startswith=f'{prefix}-{date_part}'
        ).order_by('-id').first()
        
        if last_invoice:
            last_num = int(last_invoice.invoice_number.split('-')[-1])
            new_num = last_num + 1
        else:
            new_num = 1
        
        return f"{prefix}-{date_part}-{new_num:04d}"
    
    def save(self, *args, **kwargs):
        if not self.invoice_number:
            self.invoice_number = self.generate_invoice_number()
        super().save(*args, **kwargs)
    
    @property
    def status_display(self):
        """نمایش فارسی وضعیت"""
        return dict(self.STATUS_CHOICES).get(self.status, self.status)
    
    @property
    def invoice_type_display(self):
        """نمایش فارسی نوع فاکتور"""
        return dict(self.INVOICE_TYPE_CHOICES).get(self.invoice_type, self.invoice_type)
    
    @property
    def payment_method_display(self):
        """نمایش فارسی روش پرداخت"""
        return dict(self.PAYMENT_METHOD_CHOICES).get(self.payment_method, self.payment_method)
    
    
    
# gold_app/models.py - اضافه کردن مدل AppVersion

from django.db import models
from django.conf import settings


class AppVersion(models.Model):
    """
    مدل مدیریت نسخه اپلیکیشن
    """
    
    version_code = models.PositiveIntegerField(
        default=1,
        verbose_name="شماره نسخه (کد)"
    )
    
    version_name = models.CharField(
        max_length=50,
        default="1.0.0",
        verbose_name="نام نسخه"
    )
    
    min_required_version_code = models.PositiveIntegerField(
        default=1,
        verbose_name="حداقل نسخه مورد نیاز"
    )
    
    update_message = models.TextField(
        blank=True,
        null=True,
        verbose_name="پیام بروزرسانی"
    )
    
    release_notes = models.TextField(
        blank=True,
        null=True,
        verbose_name="توضیحات نسخه"
    )
    
    store_url = models.CharField(
        max_length=255,
        default="bazaar://details?id=shop.darine.gold",
        verbose_name="آدرس مارکت"
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name="فعال"
    )
    
    is_force_update = models.BooleanField(
        default=False,
        verbose_name="بروزرسانی اجباری"
    )
    
    release_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name="تاریخ انتشار"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "نسخه اپلیکیشن"
        verbose_name_plural = "نسخه‌های اپلیکیشن"
        ordering = ['-version_code']
    
    def __str__(self):
        return f"v{self.version_name} (code: {self.version_code})"