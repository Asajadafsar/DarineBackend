from django.db import models
from django.conf import settings
from decimal import Decimal

class GoldInventory(models.Model):
    """موجودی طلای کاربر به گرم"""
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='gold_inventory')
    balance = models.DecimalField(max_digits=20, decimal_places=5, default=0.00000)

    def __str__(self):
        return f"{self.user.mobile} - {self.balance}g"

class GoldTransaction(models.Model):
    """تاریخچه خرید و فروش طلا"""
    TRANSACTION_TYPES = (
        ('BUY', 'خرید'),
        ('SELL', 'فروش'),
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    type = models.CharField(max_length=4, choices=TRANSACTION_TYPES)
    amount_gr = models.DecimalField(max_digits=20, decimal_places=5) # وزن به گرم
    price_per_gram = models.DecimalField(max_digits=20, decimal_places=0) # قیمت لحظه‌ای
    fee = models.DecimalField(max_digits=20, decimal_places=0) # مبلغ کارمزد
    total_amount = models.DecimalField(max_digits=20, decimal_places=0) # مبلغ کل (تومان)
    is_completed = models.BooleanField(default=False) # وضعیت پرداخت
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.mobile} - {self.type} - {self.amount_gr}g"
    

class Wallet(models.Model):
    """کیف پول ریالی کاربر"""
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='wallet')
    balance = models.DecimalField(max_digits=20, decimal_places=0, default=0) # موجودی به تومان

    def __str__(self):
        return f"{self.user.mobile} - {self.balance} Toman"
    


class AdminBankInfo(models.Model):
    """اطلاعات حساب مدیریت برای کارت به کارت"""
    card_number = models.CharField(max_length=16, verbose_name="شماره کارت")
    account_number = models.CharField(max_length=20, verbose_name="شماره حساب")
    shaba_number = models.CharField(max_length=26, verbose_name="شماره شبا")
    owner_name = models.CharField(max_length=100, verbose_name="بنام")
    is_active = models.BooleanField(default=True, verbose_name="فعال")

    class Meta:
        verbose_name = "اطلاعات حساب مدیریت"
        verbose_name_plural = "اطلاعات حساب مدیریت"

    def __str__(self):
        return f"{self.owner_name} - {self.card_number}"

    @staticmethod
    def get_active_info():
        """
        این متد چک می‌کند اگر ادمین رکوردی ثبت کرده بود آن را برگرداند،
        در غیر این صورت یک مقدار پیش‌فرض نمایش دهد تا اپلیکیشن کرش نکند.
        """
        info = AdminBankInfo.objects.filter(is_active=True).first()
        if info:
            return {
                "card_number": info.card_number,
                "shaba": info.shaba_number,
                "owner": info.owner_name,
                "account": info.account_number
            }
        # مقادیر دیفالت وقتی هنوز ادمین چیزی وارد نکرده
        return {
            "card_number": "0000000000000000",
            "shaba": "IR000000000000000000000000",
            "owner": "مدیریت سیستم",
            "account": "00000000"
        }

class FinancialTransaction(models.Model):
    """تراکنش‌های واریز و برداشت ریالی"""
    TYPE_CHOICES = (
        ('DEPOSIT', 'واریز'), 
        ('WITHDRAW', 'برداشت')
    )
    METHOD_CHOICES = (
        ('GATEWAY', 'درگاه بانکی'), 
        ('CARD', 'کارت به کارت')
    )
    STATUS_CHOICES = (
        ('PENDING', 'در انتظار بررسی'), 
        ('SUCCESS', 'موفق'), 
        ('REJECTED', 'رد شده')
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='financial_transactions'
    )
    amount = models.DecimalField(max_digits=20, decimal_places=0, verbose_name="مبلغ (تومان)")
    type = models.CharField(max_length=10, choices=TYPE_CHOICES, verbose_name="نوع تراکنش")
    method = models.CharField(max_length=10, choices=METHOD_CHOICES, verbose_name="روش پرداخت")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING', verbose_name="وضعیت")
    
    # فیلد مخصوص آپلود رسید برای کارت به کارت (واریز)
    receipt_image = models.ImageField(upload_to='receipts/%Y/%m/', null=True, blank=True, verbose_name="تصویر رسید")
    
    # فیلد انتخابی کارت کاربر برای واریز وجه توسط ادمین (برداشت)
    user_card = models.ForeignKey(
        'accounts.BankCard', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        verbose_name="کارت مقصد کاربر"
    )
    
    # فیلد توضیحات ادمین (مثلاً دلیل رد شدن تراکنش)
    admin_note = models.TextField(null=True, blank=True, verbose_name="توضیحات مدیریت")
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ایجاد")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="آخرین تغییر")

    class Meta:
        verbose_name = "تراکنش مالی"
        verbose_name_plural = "تراکنش‌های مالی"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.mobile} - {self.get_type_display()} - {self.amount} T"