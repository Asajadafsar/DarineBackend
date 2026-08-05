from decimal import Decimal

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from datetime import timedelta
import uuid

from darine_config import settings

from django.core.exceptions import ValidationError
from django.contrib.auth.models import User

import uuid

from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):

    ROLE_CHOICES = (
        ("customer", "خریدار"),
        ("agent", "نماینده فروش"),
        ("admin", "ادمین"),
    )

    AUTH_STATUS_CHOICES = (
        ("pending", "در انتظار"),
        ("verified", "تایید شده"),
        ("rejected", "رد شده"),
    )


    mobile = models.CharField(
        max_length=11,
        unique=True,
        verbose_name="شماره موبایل",
    )


    national_code = models.CharField(
        max_length=10,
        unique=True,
        null=True,
        blank=True,
        verbose_name="کد ملی",
    )


    birth_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="تاریخ تولد",
    )


    card_number = models.CharField(
        max_length=16,
        null=True,
        blank=True,
        verbose_name="شماره کارت",
    )


    shaba_number = models.CharField(
        max_length=26,
        null=True,
        blank=True,
        verbose_name="شماره شبا",
    )


    # =====================================
    # REFERRAL SYSTEM
    # =====================================

    referral_code = models.CharField(
        max_length=12,
        unique=True,
        null=True,
        blank=True,
        verbose_name="کد معرف اختصاصی",
    )


    referred_by = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="referrals",
        verbose_name="معرف",
    )


    # =====================================
    # USER INFO
    # =====================================

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default="customer",
        verbose_name="نقش کاربر",
    )


    auth_status = models.CharField(
        max_length=20,
        choices=AUTH_STATUS_CHOICES,
        default="pending",
        verbose_name="وضعیت تایید هویت",
    )


    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="تاریخ آخرین ویرایش",
    )


    USERNAME_FIELD = "mobile"

    REQUIRED_FIELDS = [
        "username",
    ]


    class Meta:
        verbose_name = "کاربر"
        verbose_name_plural = "کاربران"


    def generate_referral_code(self):

        return uuid.uuid4().hex[:8].upper()


    def save(self, *args, **kwargs):

        if not self.referral_code:
            self.referral_code = self.generate_referral_code()


        super().save(*args, **kwargs)


    def __str__(self):

        return (
            f"{self.mobile} - "
            f"{self.first_name} {self.last_name}"
        )
        
        

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
        User, on_delete=models.CASCADE, related_name="cards", verbose_name="کاربر"
    )

    card_number = models.CharField(
        max_length=16, null=True, blank=True, verbose_name="شماره کارت"
    )

    shaba_number = models.CharField(
        max_length=24, null=True, blank=True, verbose_name="شماره شبا"
    )

    bank_name = models.CharField(
        max_length=50, blank=True, null=True, verbose_name="نام بانک"
    )

    is_active = models.BooleanField(default=True, verbose_name="وضعیت فعال")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "اطلاعات بانکی"
        verbose_name_plural = "اطلاعات بانکی"

    def clean(self):

        if not self.card_number and not self.shaba_number:
            raise ValidationError("شماره کارت یا شماره شبا الزامی است.")

    def __str__(self):

        return self.card_number or self.shaba_number or f"BankInfo-{self.id}"


class CooperationRequest(models.Model):

    full_name = models.CharField(max_length=255)

    mobile = models.CharField(max_length=11)

    description = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)

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
        related_name="referral_earnings",
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="generated_referral_earnings",
    )

    source_type = models.CharField(max_length=10, choices=TYPE_CHOICES)

    transaction_amount = models.DecimalField(max_digits=20, decimal_places=0)

    commission_percent = models.DecimalField(max_digits=5, decimal_places=2)

    commission_amount = models.DecimalField(max_digits=20, decimal_places=0)

    marketer_percent = models.DecimalField(max_digits=5, decimal_places=2)

    profit = models.DecimalField(max_digits=20, decimal_places=0)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.referrer.mobile} -> {self.user.mobile}"


class ReferralSetting(models.Model):

    commission_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=20,
        verbose_name="درصد سود رفرال",
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        verbose_name = "تنظیمات رفرال"
        verbose_name_plural = "تنظیمات رفرال"

    def __str__(self):
        return f"{self.commission_percent}%"


from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError


class FeeSetting(models.Model):

    gold_buy_fee = models.DecimalField(
        max_digits=5,
        decimal_places=4,
        default=Decimal("0.01"),
        help_text="نرخ کارمزد خرید طلا (مثال: 0.01 = 1% ، 0.03 = 3%)"
    )

    gold_sell_fee = models.DecimalField(
        max_digits=5,
        decimal_places=4,
        default=Decimal("0.01"),
        help_text="نرخ کارمزد فروش طلا"
    )

    silver_buy_fee = models.DecimalField(
        max_digits=5,
        decimal_places=4,
        default=Decimal("0.01"),
        help_text="نرخ کارمزد خرید نقره"
    )

    silver_sell_fee = models.DecimalField(
        max_digits=5,
        decimal_places=4,
        default=Decimal("0.01"),
        help_text="نرخ کارمزد فروش نقره"
    )

    gold_referral_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=20
    )

    silver_referral_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=20
    )

    updated_at = models.DateTimeField(auto_now=True)
    






class UserFee(models.Model):

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="fee"
    )

    gold_buy_fee = models.DecimalField(
        max_digits=5,
        decimal_places=4,
        default=Decimal("0.01")
    )

    gold_sell_fee = models.DecimalField(
        max_digits=5,
        decimal_places=4,
        default=Decimal("0.01")
    )

    silver_buy_fee = models.DecimalField(
        max_digits=5,
        decimal_places=4,
        default=Decimal("0.01")
    )

    silver_sell_fee = models.DecimalField(
        max_digits=5,
        decimal_places=4,
        default=Decimal("0.01")
    )

    updated_at = models.DateTimeField(auto_now=True)
    
    
    
    
    
    
    
# accounts/models.py - مدل‌های تیکت کامل

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.core.validators import FileExtensionValidator
import uuid
from datetime import timedelta



class TicketCategory(models.Model):
    """دسته‌بندی تیکت‌ها"""
    name = models.CharField(max_length=100, verbose_name="نام دسته‌بندی")
    slug = models.SlugField(max_length=100, unique=True, verbose_name="شناسه")
    description = models.TextField(blank=True, null=True, verbose_name="توضیحات")
    is_active = models.BooleanField(default=True, verbose_name="فعال")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "دسته‌بندی تیکت"
        verbose_name_plural = "دسته‌بندی‌های تیکت"
        ordering = ['name']

    def __str__(self):
        return self.name


def ticket_attachment_path(instance, filename):
    """مسیر ذخیره فایل ضمیمه تیکت"""
    return f'tickets/attachments/{instance.tracking_code}/{filename}'


def ticket_message_attachment_path(instance, filename):
    """مسیر ذخیره فایل ضمیمه پیام"""
    return f'tickets/messages/{instance.ticket.tracking_code}/{filename}'


class Ticket(models.Model):
    """مدل اصلی تیکت"""
    
    # وضعیت‌های تیکت
    STATUS_CHOICES = (
        ('open', 'باز'),
        ('in_progress', 'در حال بررسی'),
        ('pending', 'در انتظار پاسخ کاربر'),  # کاربر پیام داده، منتظر پاسخ ادمین
        ('answered', 'پاسخ داده شده'),        # ادمین پاسخ داده، منتظر بازخورد کاربر
        ('resolved', 'حل شده'),
        ('closed', 'بسته شده'),
    )
    
    # اولویت‌های تیکت
    PRIORITY_CHOICES = (
        ('low', 'کم'),
        ('medium', 'متوسط'),
        ('high', 'بالا'),
        ('urgent', 'فوری'),
    )
    
    # کد رهگیری یکتا
    tracking_code = models.CharField(
        max_length=20, 
        unique=True, 
        editable=False,
        verbose_name="کد رهگیری"
    )
    
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='tickets',
        verbose_name="کاربر"
    )
    category = models.ForeignKey(
        TicketCategory,
        on_delete=models.SET_NULL,
        null=True,
        related_name='tickets',
        verbose_name="دسته‌بندی"
    )
    title = models.CharField(max_length=200, verbose_name="عنوان")
    description = models.TextField(verbose_name="توضیحات")
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='open',
        verbose_name="وضعیت"
    )
    priority = models.CharField(
        max_length=20,
        choices=PRIORITY_CHOICES,
        default='medium',
        verbose_name="اولویت"
    )
    
    # فایل ضمیمه (با اعتبارسنجی)
    attachment = models.FileField(
        upload_to=ticket_attachment_path,
        blank=True,
        null=True,
        validators=[
            FileExtensionValidator(
                allowed_extensions=['jpg', 'jpeg', 'png', 'gif', 'bmp', 'svg', 
                                   'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx',
                                   'zip', 'rar', '7z', 'txt', 'csv', 'json', 'xml']
            )
        ],
        verbose_name="فایل ضمیمه"
    )
    
    # زمان‌ها
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ایجاد")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاریخ بروزرسانی")
    resolved_at = models.DateTimeField(blank=True, null=True, verbose_name="تاریخ حل")
    closed_at = models.DateTimeField(blank=True, null=True, verbose_name="تاریخ بسته شدن")
    last_activity_at = models.DateTimeField(auto_now=True, verbose_name="آخرین فعالیت")
    
    # کاربری که تیکت را بسته است
    closed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='closed_tickets',
        verbose_name="بسته شده توسط"
    )
    
    # تعداد پیام‌های خوانده نشده
    unread_count = models.IntegerField(default=0, verbose_name="پیام‌های خوانده نشده")
    
    # آیا اتومات حل شده است؟
    auto_resolved = models.BooleanField(default=False, verbose_name="حل شده خودکار")

    class Meta:
        verbose_name = "تیکت"
        verbose_name_plural = "تیکت‌ها"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.tracking_code} - {self.title} - {self.user.mobile}"

    def save(self, *args, **kwargs):
        # تولید کد رهگیری در صورت نبودن
        if not self.tracking_code:
            self.tracking_code = self.generate_tracking_code()
        
        # اگر وضعیت به resolved تغییر کرد، زمان حل را ثبت کن
        if self.status == 'resolved' and not self.resolved_at:
            self.resolved_at = timezone.now()
        
        # اگر وضعیت به closed تغییر کرد، زمان بسته شدن را ثبت کن
        if self.status == 'closed' and not self.closed_at:
            self.closed_at = timezone.now()
        
        super().save(*args, **kwargs)

    def generate_tracking_code(self):
        """تولید کد رهگیری یکتا"""
        # فرمت: TKT-YYYYMMDD-XXXXX
        prefix = f"TKT-{timezone.now().strftime('%Y%m%d')}"
        random_part = str(uuid.uuid4().hex[:6].upper())
        return f"{prefix}-{random_part}"

    def update_status_based_on_last_message(self):
        """بروزرسانی وضعیت تیکت بر اساس آخرین پیام"""
        last_message = self.messages.last()
        
        if not last_message:
            return
        
        # اگر آخرین پیام توسط کاربر باشد → در انتظار پاسخ
        if not last_message.is_admin:
            if self.status not in ['closed', 'resolved']:
                self.status = 'pending'
                self.save()
        else:
            # اگر آخرین پیام توسط ادمین باشد → پاسخ داده شده
            if self.status not in ['closed', 'resolved']:
                self.status = 'answered'
                self.save()
        
        # بروزرسانی زمان آخرین فعالیت
        self.last_activity_at = timezone.now()
        self.save(update_fields=['last_activity_at'])

    def check_and_auto_resolve(self):
        """بررسی و حل خودکار تیکت در صورت عدم فعالیت"""
        if self.status != 'answered':
            return False
        
        # اگر تیکت در وضعیت پاسخ داده شده باشد و ۲ روز از آخرین فعالیت گذشته باشد
        two_days_ago = timezone.now() - timedelta(days=2)
        
        if self.last_activity_at <= two_days_ago:
            self.status = 'resolved'
            self.resolved_at = timezone.now()
            self.auto_resolved = True
            self.save()
            return True
        
        return False

    def can_user_edit(self, user):
        """بررسی اینکه کاربر می‌تواند این تیکت را ویرایش کند"""
        return self.user == user and self.status in ['open', 'pending']

    def can_user_close(self, user):
        """بررسی اینکه کاربر می‌تواند این تیکت را ببندد"""
        return self.user == user and self.status not in ['closed', 'resolved']

    def get_last_message_user_type(self):
        """نوع کاربر ارسال‌کننده آخرین پیام"""
        last_message = self.messages.last()
        if last_message:
            return 'admin' if last_message.is_admin else 'user'
        return None


class TicketMessage(models.Model):
    """پیام‌های تیکت"""
    
    ticket = models.ForeignKey(
        Ticket,
        on_delete=models.CASCADE,
        related_name='messages',
        verbose_name="تیکت"
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='ticket_messages',
        verbose_name="فرستنده"
    )
    message = models.TextField(verbose_name="متن پیام")
    
    # فایل ضمیمه برای پیام (با اعتبارسنجی)
    attachment = models.FileField(
        upload_to=ticket_message_attachment_path,
        blank=True,
        null=True,
        validators=[
            FileExtensionValidator(
                allowed_extensions=['jpg', 'jpeg', 'png', 'gif', 'bmp', 'svg',
                                   'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx',
                                   'zip', 'rar', '7z', 'txt', 'csv', 'json', 'xml']
            )
        ],
        verbose_name="فایل ضمیمه"
    )
    
    # مشخص می‌کند که پیام توسط کاربر است یا ادمین
    is_admin = models.BooleanField(default=False, verbose_name="پیام ادمین")
    
    # خوانده شده
    is_read = models.BooleanField(default=False, verbose_name="خوانده شده")
    read_at = models.DateTimeField(blank=True, null=True, verbose_name="زمان خواندن")
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ارسال")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاریخ بروزرسانی")

    class Meta:
        verbose_name = "پیام تیکت"
        verbose_name_plural = "پیام‌های تیکت"
        ordering = ['created_at']

    def __str__(self):
        return f"{self.ticket.tracking_code} - {self.user.mobile} - {self.created_at}"

    def mark_as_read(self):
        """علامت‌گذاری پیام به عنوان خوانده شده"""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save()

    def save(self, *args, **kwargs):
        # اعتبارسنجی حجم فایل (حداکثر ۱۰ مگابایت)
        if self.attachment:
            if self.attachment.size > 10 * 1024 * 1024:
                raise ValidationError("حجم فایل نباید بیشتر از ۱۰ مگابایت باشد")
        
        super().save(*args, **kwargs)
        
        # بروزرسانی وضعیت تیکت بر اساس آخرین پیام
        self.ticket.update_status_based_on_last_message()