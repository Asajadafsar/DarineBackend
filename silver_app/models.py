from decimal import Decimal

from django.db import models
from django.conf import settings

class SilverInventory(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='silver_inventory')
    # مقدار default را داخل کوتیشن بگذار تا به عنوان رشته به Decimal تبدیل شود
    balance = models.DecimalField(max_digits=20, decimal_places=5, default=Decimal('0.00000'))

    def __str__(self):
        return f"{self.user.mobile} - {self.balance}g Silver"

class SilverTransaction(models.Model):
    TYPE_CHOICES = (
        ('BUY', 'خرید'), 
        ('SELL', 'فروش'), 
        ('CONVERT', 'تبدیل از ریال')
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    amount_gr = models.DecimalField(max_digits=20, decimal_places=5)
    total_amount = models.DecimalField(max_digits=20, decimal_places=0)
    # فیلد زیر را حتما اضافه کنید:
    type = models.CharField(max_length=10, choices=TYPE_CHOICES, default='BUY') 
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.mobile} - {self.type} - {self.amount_gr}g"
    

