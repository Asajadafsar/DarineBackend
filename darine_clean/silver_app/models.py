from django.db import models
from django.conf import settings
from decimal import Decimal




class SilverInventory(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='silver_inventory')
    balance = models.DecimalField(max_digits=20, decimal_places=5, default=Decimal('0.00000'))
    total_spent_toman = models.DecimalField(max_digits=20, decimal_places=0, default=0) 
    total_withdrawn_gr = models.DecimalField(max_digits=20, decimal_places=5, default=0)

    def __str__(self):
        return f"{self.user.mobile} - {self.balance}g"

class SilverTransaction(models.Model):
    TYPE_CHOICES = (
        ('BUY', 'خرید نقره'),
        ('SELL', 'فروش نقره'),
        ('CONVERT', 'تبدیل از ریال'),
    )
    STATUS_CHOICES = (
        ('DONE', 'انجام شده'),
        ('PENDING', 'در انتظار'),
        ('FAILED', 'ناموفق'),
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    amount_gr = models.DecimalField(max_digits=20, decimal_places=5, default=0)
    amount_toman = models.DecimalField(max_digits=20, decimal_places=0) # مبلغ کل تراکنش به تومان
    type = models.CharField(max_length=15, choices=TYPE_CHOICES)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='DONE')
    created_at = models.DateTimeField(auto_now_add=True)

class BankCard(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='silver_cards')
    bank_name = models.CharField(max_length=50)
    card_number = models.CharField(max_length=16)
    iban = models.CharField(max_length=26, blank=True, null=True)

    def __str__(self):
        return f"{self.user.mobile} - {self.bank_name}"
    



class SilverProduct(models.Model):
    title = models.CharField(max_length=255, verbose_name="نام محصول")
    weight_gr = models.DecimalField(max_digits=10, decimal_places=3, verbose_name="وزن خالص (گرم)")
    total_weight_with_packaging = models.DecimalField(max_digits=10, decimal_places=3, verbose_name="وزن با صرب و بسته‌بندی")
    description = models.TextField(blank=True, verbose_name="توضیحات")
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title


class PhysicalDeliveryOrder(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'در انتظار بررسی'),
        ('PREPARING', 'در حال آماده‌سازی'),
        ('SHIPPED', 'ارسال شده'),
        ('DELIVERED', 'تحویل شده'),
        ('CANCELLED', 'لغو شده'),
    ]
    PAYMENT_METHODS = [
        ('SILVER', 'پرداخت با نقره'),
        ('TOMAN', 'پرداخت مستقیم تومانی'),
    ]
    DELIVERY_METHODS = [
        ('COURIER', 'تحویل درب منزل'),
        ('IN_PERSON', 'تحویل حضوری در دفتر'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    product = models.ForeignKey(SilverProduct, on_delete=models.PROTECT)
    
    # وزن و قیمت در لحظه سفارش (برای ثبت در فاکتور)
    weight_at_time_of_order = models.DecimalField(max_digits=10, decimal_places=3)
    total_price_toman = models.DecimalField(max_digits=20, decimal_places=0, default=0)
    
    # روش پرداخت و تحویل
    payment_method = models.CharField(max_length=10, choices=PAYMENT_METHODS, default='SILVER')
    delivery_method = models.CharField(max_length=15, choices=DELIVERY_METHODS, default='IN_PERSON')
    
    # اطلاعات ارسال (می‌توانند خالی باشند اگر تحویل حضوری بود)
    address = models.TextField(blank=True, null=True, verbose_name="آدرس ارسال")
    postal_code = models.CharField(max_length=10, blank=True, null=True, verbose_name="کد پستی")
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"سفارش {self.id} - {self.user} - {self.product.title}"