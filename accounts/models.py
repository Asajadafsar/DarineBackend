from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from datetime import timedelta
import uuid

from darine_config import settings

from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User



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

    class Meta:
        verbose_name = "درخواست کد تایید"
        verbose_name_plural = "درخواست‌های کد تایید"

    def is_expired(self):
        return timezone.now() > self.created_at + timedelta(minutes=10)

    def __str__(self):
        return f"{self.mobile} - {self.code}"
    

def is_expired(self):
    # استفاده از timezone.now خود جنگو که با تنظیمات settings.py هماهنگ است
    now = timezone.now()
    # افزایش زمان انقضا به 10 دقیقه برای تست راحت‌تر
    expire_time = self.created_at + timedelta(minutes=10)
    return now > expire_time


# models.py



class BankCard(models.Model):

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="cards",
        verbose_name="کاربر"
    )

    card_number = models.CharField(
        max_length=16,
        null=True,
        blank=True,
        verbose_name="شماره کارت"
    )

    shaba_number = models.CharField(
        max_length=24,
        null=True,
        blank=True,
        verbose_name="شماره شبا"
    )

    bank_name = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name="نام بانک"
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name="وضعیت فعال"
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )


    class Meta:
        verbose_name = "اطلاعات بانکی"
        verbose_name_plural = "اطلاعات بانکی"


    def clean(self):

        if not self.card_number and not self.shaba_number:
            raise ValidationError(
                "شماره کارت یا شماره شبا الزامی است."
            )


    def __str__(self):

        return (
            self.card_number
            or self.shaba_number
            or f"BankInfo-{self.id}"
        )



class CooperationRequest(models.Model):

    full_name = models.CharField(
        max_length=255
    )

    mobile = models.CharField(
        max_length=11
    )

    description = models.TextField()

    created_at = models.DateTimeField(
        auto_now_add=True
    )

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
        related_name="generated_referral_earnings"
    )

    source_type = models.CharField(
        max_length=10,
        choices=TYPE_CHOICES
    )

    transaction_amount = models.DecimalField(
        max_digits=20,
        decimal_places=0
    )

    commission_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2
    )

    commission_amount = models.DecimalField(
        max_digits=20,
        decimal_places=0
    )

    marketer_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2
    )

    profit = models.DecimalField(
        max_digits=20,
        decimal_places=0
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"{self.referrer.mobile} -> {self.user.mobile}"


from django.db import models


class FeeSetting(models.Model):

    # =========================
    # DEFAULT BUY/SELL FEES
    # =========================

    gold_buy_fee = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=1.00,
        help_text="درصد کارمزد خرید طلا"
    )

    gold_sell_fee = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=1.00,
        help_text="درصد کارمزد فروش طلا"
    )

    silver_buy_fee = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=1.00,
        help_text="درصد کارمزد خرید نقره"
    )

    silver_sell_fee = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=1.00,
        help_text="درصد کارمزد فروش نقره"
    )

    # =========================
    # REFERRAL PERCENT
    # =========================

    gold_referral_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=20.00,
        help_text="درصد سود معرف از کارمزد طلا"
    )

    silver_referral_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=20.00,
        help_text="درصد سود معرف از کارمزد نقره"
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return "Fee Settings"
    
    
class UserFee(models.Model):

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="fee"
    )

    gold_buy_fee = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=1.00
    )

    gold_sell_fee = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=1.00
    )

    silver_buy_fee = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=1.00
    )

    silver_sell_fee = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=1.00
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return self.user.mobile