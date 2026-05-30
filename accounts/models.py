from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from datetime import timedelta
import uuid

from darine_config import settings



class User(AbstractUser):
    ROLE_CHOICES = (
        ('customer', 'خریدار'),
        ('agent', 'نماینده فروش'),
        ('admin', 'ادمین'),
    )

    AUTH_STATUS_CHOICES = (
        ('pending', 'در انتظار'),
        ('verified', 'تایید شده'),
        ('rejected', 'رد شده'),
    )
    TYPE_CHOICES = (
    ('BUY', 'خرید نقره'),
    ('SELL', 'فروش نقره'),
    ('CONVERT', 'تبدیل از ریال'),
    ('REFERRAL_REWARD', 'پاداش معرفی دوستان'), # اضافه شود
)
    

    
    mobile = models.CharField(max_length=11, unique=True, verbose_name="شماره موبایل")
    national_code = models.CharField(max_length=10, unique=True, null=True, blank=True, verbose_name="کد ملی")
    birth_date = models.DateField(null=True, blank=True, verbose_name="تاریخ تولد")
    card_number = models.CharField(max_length=16, null=True, blank=True, verbose_name="شماره کارت")
    shaba_number = models.CharField(max_length=26, null=True, blank=True, verbose_name="شماره شبا")
    
    # سیستم معرف
    referred_by = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='subscribers', verbose_name="معرف")
    referral_code = models.CharField(max_length=10, unique=True, null=True, blank=True, verbose_name="کد معرف اختصاصی")

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='customer', verbose_name="نقش کاربر")
    auth_status = models.CharField(max_length=20, choices=AUTH_STATUS_CHOICES, default='pending', verbose_name="وضعیت تایید هویت")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاریخ آخرین ویرایش")

    USERNAME_FIELD = 'mobile'
    REQUIRED_FIELDS = ['username']

    class Meta:
        verbose_name = "کاربر"
        verbose_name_plural = "کاربران"

    def save(self, *args, **kwargs):
        if not self.referral_code:
            self.referral_code = str(uuid.uuid4()).split('-')[0][:8] # تولید کد معرف خودکار
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.mobile} - {self.first_name} {self.last_name}"


class OTPRequest(models.Model):
    mobile = models.CharField(max_length=11, verbose_name="شماره موبایل")
    code = models.CharField(max_length=6, verbose_name="کد تایید")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="زمان ایجاد")
    is_used = models.BooleanField(default=False, verbose_name="استفاده شده")
    def is_expired(self):
        # زمان حال به وقت سرور
        now = timezone.now()
        # کدی که ۲ دقیقه از زمان ایجادش گذشته باشد منقضی است
        return now > self.created_at + timedelta(minutes=2)

    class Meta:
        verbose_name = "درخواست کد تایید"
        verbose_name_plural = "درخواست‌های کد تایید"

    def is_expired(self):
        return timezone.now() > self.created_at + timedelta(minutes=2)
    

def is_expired(self):
    # استفاده از timezone.now خود جنگو که با تنظیمات settings.py هماهنگ است
    now = timezone.now()
    # افزایش زمان انقضا به 10 دقیقه برای تست راحت‌تر
    expire_time = self.created_at + timedelta(minutes=10)
    return now > expire_time


class BankCard(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cards', verbose_name="کاربر")
    card_number = models.CharField(max_length=16, verbose_name="شماره کارت")
    bank_name = models.CharField(max_length=50, blank=True, null=True, verbose_name="نام بانک")
    is_active = models.BooleanField(default=True, verbose_name="وضعیت فعال")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "کارت بانکی"
        verbose_name_plural = "کارت‌های بانکی"

    def __str__(self):
        return f"{self.user.mobile} - {self.card_number}"
    


class CooperationRequest(models.Model):

    organization_name = models.CharField(max_length=255)

    full_name = models.CharField(max_length=255)

    email = models.EmailField()

    mobile = models.CharField(max_length=20)

    description = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    is_reviewed = models.BooleanField(default=False)

    def __str__(self):
        return self.full_name
    



class ReferralEarning(models.Model):

    TYPE_CHOICES = (
        ("GOLD", "طلا"),
        ("SILVER", "نقره"),
    )

    referrer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="referral_earnings"
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="referrals"
    )

    amount = models.DecimalField(max_digits=20, decimal_places=0)

    source_type = models.CharField(max_length=10, choices=TYPE_CHOICES)

    created_at = models.DateTimeField(auto_now_add=True)



class FeeSetting(models.Model):

    # کارمزد معاملات
    gold_fee = models.DecimalField(
        max_digits=5,
        decimal_places=4,
        default=0.0099
    )

    silver_fee = models.DecimalField(
        max_digits=5,
        decimal_places=4,
        default=0.01
    )

    # درصد سود معرف
    gold_referral_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=20.00
    )

    silver_referral_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=10.00
    )

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "Fee Settings"