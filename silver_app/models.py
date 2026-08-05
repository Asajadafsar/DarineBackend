# silver_app/models.py

from django.db import models
from django.conf import settings

from accounts.models import BankCard

# =========================================================
# SILVER WALLET
# =========================================================


class SilverWallet(models.Model):

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="silver_wallet"
    )

    # ===========================
    # TOMAN
    # ===========================

    accessible_toman = models.DecimalField(max_digits=20, decimal_places=0, default=0)

    blocked_toman = models.DecimalField(max_digits=20, decimal_places=0, default=0)

    updated_at = models.DateTimeField(auto_now=True)

    @property
    def toman_total(self):
        return self.accessible_toman + self.blocked_toman

    def __str__(self):
        return self.user.mobile


# =========================================================
# SILVER INVENTORY
# =========================================================


class SilverInventory(models.Model):

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="silver_inventory",
    )

    accessible_balance = models.DecimalField(max_digits=20, decimal_places=3, default=0)

    blocked_balance = models.DecimalField(max_digits=20, decimal_places=3, default=0)

    updated_at = models.DateTimeField(auto_now=True)

    @property
    def total_balance(self):
        return self.accessible_balance + self.blocked_balance

    def __str__(self):
        return self.user.mobile


# =========================================================
# SILVER TRANSACTION
# =========================================================


class SilverTransaction(models.Model):

    TYPE_CHOICES = (
        ("BUY", "خرید"),
        ("SELL", "فروش"),
    )

    STATUS_CHOICES = (
        ("PENDING", "در انتظار"),
        ("COMPLETED", "تکمیل شده"),
        ("FAILED", "ناموفق"),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    type = models.CharField(max_length=20, choices=TYPE_CHOICES)

    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="COMPLETED"
    )

    amount_gr = models.DecimalField(max_digits=20, decimal_places=3)

    price_per_gram = models.DecimalField(max_digits=20, decimal_places=0)

    # مبلغ کارمزد
    fee = models.DecimalField(max_digits=20, decimal_places=0, default=0)

    # درصد کارمزد همان لحظه
    commission_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    # مبلغ کارمزد همان لحظه
    commission_amount = models.DecimalField(max_digits=20, decimal_places=0, default=0)

    # درصد سود معرف همان لحظه
    marketer_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    # مبلغ سود معرف همان لحظه
    profit = models.DecimalField(max_digits=20, decimal_places=0, default=0)

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
        ("DEPOSIT", "واریز"),
        ("WITHDRAW", "برداشت"),
    )

    METHOD_CHOICES = (
        ("ONLINE", "آنلاین"),
        ("CARD_TO_CARD", "کارت به کارت"),
        ("BANK", "بانکی"),
    )

    STATUS_CHOICES = (
        ("PENDING", "در انتظار"),
        ("COMPLETED", "تکمیل شده"),
        ("FAILED", "ناموفق"),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    amount = models.DecimalField(max_digits=20, decimal_places=0)

    type = models.CharField(max_length=20, choices=TYPE_CHOICES)

    method = models.CharField(max_length=30, choices=METHOD_CHOICES)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="PENDING")

    user_card = models.ForeignKey(
        BankCard, on_delete=models.SET_NULL, null=True, blank=True
    )

    receipt_image = models.ImageField(
        upload_to="silver_receipts/", null=True, blank=True
    )

    tracking_code = models.CharField(max_length=100, unique=True, null=True, blank=True)

    admin_note = models.TextField(blank=True, null=True)

    description = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)


# =========================================================
# PRODUCT CATEGORY
# =========================================================


class SilverProductCategory(models.Model):

    name = models.CharField(max_length=100)

    slug = models.SlugField(unique=True)

    def __str__(self):
        return self.name


# =========================================================
# PRODUCT
# =========================================================


class SilverProduct(models.Model):

    DELIVERY_CHOICES = (
        ("HOME", "ارسال به منزل"),
        ("IN_PERSON", "تحویل حضوری"),
    )

    category = models.ForeignKey(
        SilverProductCategory,
        on_delete=models.SET_NULL,
        null=True,
        related_name="products",
    )

    name = models.CharField(max_length=255)

    delivery_type = models.CharField(
        max_length=20, choices=DELIVERY_CHOICES, default="HOME"
    )

    weight = models.DecimalField(max_digits=20, decimal_places=3)

    total_weight_with_fees = models.DecimalField(
        max_digits=20, decimal_places=3, default=0
    )

    buy_price = models.DecimalField(
        max_digits=20, decimal_places=0, null=True, blank=True
    )

    sell_price = models.DecimalField(
        max_digits=20, decimal_places=0, null=True, blank=True
    )

    inventory_count = models.PositiveIntegerField(default=0)

    image = models.ImageField(upload_to="silver_products/", null=True, blank=True)

    description = models.TextField(blank=True, null=True)

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    profit_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    def __str__(self):
        return self.name


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

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    province = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    address = models.TextField()
    postal_code = models.CharField(max_length=20, blank=True, null=True)
    plaque = models.CharField(max_length=20, blank=True, null=True)
    unit = models.CharField(max_length=20, blank=True, null=True)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_CHOICES)
    delivery_type = models.CharField(max_length=20, choices=DELIVERY_CHOICES)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="REQUESTED"
    )

    total_silver_amount = models.DecimalField(max_digits=20, decimal_places=3)
    total_toman_amount = models.DecimalField(max_digits=20, decimal_places=0)
    tracking_code = models.CharField(max_length=100, unique=True)
    admin_note = models.TextField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.tracking_code


class SilverOrderItem(models.Model):
    order = models.ForeignKey(
        SilverOrder, on_delete=models.CASCADE, related_name="items"
    )
    product = models.ForeignKey(SilverProduct, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price_at_time = models.DecimalField(max_digits=20, decimal_places=0)
    weight_at_time = models.DecimalField(max_digits=20, decimal_places=3)


class SilverOrderStatusHistory(models.Model):
    STATUS_CHOICES = (
        ("REQUESTED", "درخواست سفارش"),
        ("PREPARING", "در حال آماده‌سازی"),
        ("DELIVERING", "در حال تحویل"),
        ("DELIVERED", "تحویل داده شد"),
        ("CANCELLED", "لغو شده"),
    )
    order = models.ForeignKey(
        SilverOrder, on_delete=models.CASCADE, related_name="status_history"
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
        verbose_name = "مرحله سفارش نقره"
        verbose_name_plural = "مراحل سفارش نقره"

    def __str__(self):
        return f"{self.order.tracking_code} - {self.get_status_display()}"


# =========================================================
# RECENT TRANSACTION
# =========================================================


class SilverRecentTransaction(models.Model):

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    title = models.CharField(max_length=255)

    amount = models.DecimalField(max_digits=20, decimal_places=0)

    status = models.CharField(max_length=50)

    type = models.CharField(max_length=50)

    created_at = models.DateTimeField(auto_now_add=True)


# =========================================================
# RECENT DELIVERY
# =========================================================


class SilverRecentDelivery(models.Model):

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    delivery_type = models.CharField(max_length=50)

    status = models.CharField(max_length=50)

    total_amount = models.DecimalField(max_digits=20, decimal_places=0)

    created_at = models.DateTimeField(auto_now_add=True)


# =========================================================
# REFERRAL EARNING
# =========================================================


class SilverReferralEarning(models.Model):

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    amount = models.DecimalField(max_digits=20, decimal_places=0)

    source_type = models.CharField(max_length=50)

    created_at = models.DateTimeField(auto_now_add=True)


# =========================================================
# SILVER PRICE HISTORY
# =========================================================


class SilverPriceHistory(models.Model):

    price = models.DecimalField(max_digits=20, decimal_places=0)

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["created_at"]


class SilverBankInfo(models.Model):

    card_number = models.CharField(max_length=16, unique=True)

    full_name = models.CharField(max_length=255)

    sheba = models.CharField(max_length=26, unique=True)

    is_active = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):

        if self.is_active:

            SilverBankInfo.objects.exclude(pk=self.pk).update(is_active=False)

        super().save(*args, **kwargs)


class UserAddress(models.Model):

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="silver_addresses",
    )

    province = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    address = models.TextField()

    postal_code = models.CharField(max_length=20, null=True, blank=True)
    plaque = models.CharField(max_length=20, null=True, blank=True)
    unit = models.CharField(max_length=20, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)


# silver_app/models.py (اضافه کنید)

# silver_app/models.py (اضافه کنید)

class SilverLimitOrder(models.Model):
    """
    مدل سفارش با قیمت برای نقره (Limit Order)
    خرید در قیمت پایین‌تر - فروش در قیمت بالاتر
    """
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
        related_name='silver_limit_orders'
    )
    order_type = models.CharField(max_length=10, choices=ORDER_TYPE)
    target_price = models.DecimalField(max_digits=20, decimal_places=0)
    amount_toman = models.DecimalField(max_digits=20, decimal_places=0, null=True, blank=True)
    silver_weight = models.DecimalField(max_digits=20, decimal_places=3, null=True, blank=True)
    estimated_weight = models.DecimalField(max_digits=20, decimal_places=3)
    fee_rate = models.DecimalField(max_digits=5, decimal_places=4, default=0.0099)
    status = models.CharField(max_length=20, default="PENDING", choices=STATUS)
    executed_price = models.DecimalField(max_digits=20, decimal_places=0, null=True, blank=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'سفارش با قیمت نقره'
        verbose_name_plural = 'سفارش‌های با قیمت نقره'

    def __str__(self):
        return f"{self.get_order_type_display()} - {self.user.mobile} - {self.target_price}"
    
    
    
    
# silver_app/models.py

from django.db import models
from django.contrib.auth import get_user_model
from decimal import Decimal

User = get_user_model()


# class SilverInvoice(models.Model):
#     """مدل فاکتور نقره"""
    
#     INVOICE_TYPES = (
#         ('BUY', 'فاکتور خرید نقره'),
#         ('SELL', 'فاکتور فروش نقره'),
#     )
    
#     INVOICE_STATUS = (
#         ('PENDING', 'در انتظار تایید'),
#         ('CONFIRMED', 'تایید شده'),
#         ('CANCELLED', 'لغو شده'),
#     )
    
#     # ارتباط با تراکنش
#     transaction = models.OneToOneField(
#         'SilverTransaction',
#         on_delete=models.CASCADE,
#         related_name='silver_invoice',
#         null=True,
#         blank=True
#     )
    
#     # اطلاعات فاکتور
#     invoice_number = models.CharField(max_length=50, unique=True)
#     invoice_type = models.CharField(max_length=10, choices=INVOICE_TYPES)
#     invoice_date = models.DateTimeField(auto_now_add=True)
#     status = models.CharField(max_length=20, choices=INVOICE_STATUS, default='PENDING')
    
#     # اطلاعات خریدار
#     buyer_name = models.CharField(max_length=200, blank=True, null=True)
#     buyer_national_id = models.CharField(max_length=20, blank=True, null=True)
#     buyer_phone = models.CharField(max_length=20, blank=True, null=True)
#     buyer_address = models.TextField(blank=True, null=True)
    
#     # اطلاعات فروشنده (دارینه)
#     seller_name = models.CharField(max_length=200, default='فروشگاه دارینه')
#     seller_national_id = models.CharField(max_length=20, default='0371439477')
#     seller_phone = models.CharField(max_length=20, default='09191608771')
#     seller_address = models.TextField(default='قم، پاساژ شهر طلا، پلاک ۲۱')
    
#     # اطلاعات نقره
#     silver_weight = models.DecimalField(max_digits=20, decimal_places=3)
#     silver_price_per_gram = models.DecimalField(max_digits=20, decimal_places=0)
#     pure_silver_price = models.DecimalField(max_digits=20, decimal_places=0)  # قیمت خالص نقره
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
#         db_table = 'silver_invoice'
    
#     def __str__(self):
#         return f"{self.invoice_number} - {self.get_invoice_type_display()}"
    
#     def generate_invoice_number(self):
#         """تولید شماره فاکتور"""
#         import jdatetime
        
#         now = jdatetime.datetime.now()
#         date_str = now.strftime('%Y%m%d')
        
#         last_invoice = SilverInvoice.objects.filter(
#             invoice_number__startswith=f"{self.invoice_type}-{date_str}"
#         ).order_by('-invoice_number').first()
        
#         if last_invoice:
#             last_num = int(last_invoice.invoice_number.split('-')[-1])
#             new_num = last_num + 1
#         else:
#             new_num = 1
            
#         return f"{self.invoice_type}-{date_str}-{new_num:04d}"
    
#     def get_invoice_type_display(self):
#         return dict(self.INVOICE_TYPES).get(self.invoice_type, self.invoice_type)
    
#     def get_status_display(self):
#         return dict(self.INVOICE_STATUS).get(self.status, self.status)

# silver_app/models.py - مدل SilverInvoice کامل

from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class SilverInvoice(models.Model):
    """مدل فاکتور خرید/فروش نقره"""
    
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
        'SilverTransaction',
        on_delete=models.CASCADE,
        related_name='silver_invoices',
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
    
    # ========== اطلاعات نقره ==========
    silver_weight = models.DecimalField(
        max_digits=20, decimal_places=3,
        verbose_name="وزن نقره (گرم)"
    )
    silver_price_per_gram = models.DecimalField(
        max_digits=20, decimal_places=0,
        verbose_name="قیمت هر گرم نقره"
    )
    pure_silver_price = models.DecimalField(
        max_digits=20, decimal_places=0,
        verbose_name="قیمت خالص نقره"
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
        verbose_name = "فاکتور نقره"
        verbose_name_plural = "فاکتورهای نقره"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.invoice_number} - {self.get_invoice_type_display()}"
    
    def generate_invoice_number(self):
        """تولید شماره فاکتور"""
        import jdatetime
        now = jdatetime.datetime.now()
        prefix = 'SINV'  # Silver Invoice
        date_part = now.strftime('%Y%m%d')
        
        last_invoice = SilverInvoice.objects.filter(
            invoice_number__startswith=f'{prefix}-{date_part}'
        ).order_by('-id').first()
        
        if last_invoice:
            last_num = int(last_invoice.invoice_number.split('-')[-1])
            new_num = last_num + 1
        else:
            new_num = 1
        
        return f"{prefix}-{date_part}-{new_num:04d}"
    
    def get_invoice_type_display(self):
        return dict(self.INVOICE_TYPE_CHOICES).get(self.invoice_type, self.invoice_type)
    
    def get_status_display(self):
        return dict(self.STATUS_CHOICES).get(self.status, self.status)