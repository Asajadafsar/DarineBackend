from django.db import models
from accounts.models import User
from darine_config import settings


class AdminLog(models.Model):

    ACTION_TYPES = (

        ("BUY_GOLD", "خرید طلا"),
        ("SELL_GOLD", "فروش طلا"),

        ("BUY_SILVER", "خرید نقره"),
        ("SELL_SILVER", "فروش نقره"),

        ("DEPOSIT", "واریز"),
        ("WITHDRAW", "برداشت"),

        ("USER_REGISTER", "ثبت نام کاربر"),
        ("USER_VERIFY", "احراز هویت"),

        ("ORDER", "سفارش"),

        ("ADMIN", "فعالیت ادمین"),
    )


    admin = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="admin_action_logs"
    )


    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="user_action_logs"
    )


    action_type = models.CharField(
        max_length=50,
        choices=ACTION_TYPES
    )


    action = models.CharField(
        max_length=255
    )


    model_name = models.CharField(
        max_length=255,
        null=True,
        blank=True
    )


    object_id = models.PositiveBigIntegerField(
        null=True,
        blank=True
    )


    description = models.TextField(
        null=True,
        blank=True
    )


    created_at = models.DateTimeField(
        auto_now_add=True
    )


    class Meta:

        ordering = [
            "-created_at"
        ]


    def __str__(self):

        return self.action
    
    
    
from django.db import models


class GoldBanner(models.Model):

    title = models.CharField(
        max_length=255,
        verbose_name="عنوان"
    )

    image = models.ImageField(
        upload_to="gold/banners/",
        verbose_name="تصویر"
    )

    link = models.URLField(
        blank=True,
        null=True,
        verbose_name="لینک"
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name="فعال"
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        verbose_name = "بنر طلا"
        verbose_name_plural = "بنرهای طلا"

    def __str__(self):
        return self.title


class SilverBanner(models.Model):

    title = models.CharField(
        max_length=255,
        verbose_name="عنوان"
    )

    image = models.ImageField(
        upload_to="silver/banners/",
        verbose_name="تصویر"
    )

    link = models.URLField(
        blank=True,
        null=True,
        verbose_name="لینک"
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name="فعال"
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        verbose_name = "بنر نقره"
        verbose_name_plural = "بنرهای نقره"

    def __str__(self):
        return self.title
    
    
# =========================================================
# MANUAL PRICE
# =========================================================
# =========================================================
# GOLD PRICE OFFSET
# =========================================================

class GoldPriceOffset(models.Model):

    offset_amount = models.DecimalField(
        max_digits=20,
        decimal_places=0,
        default=0
    )
    # مثبت = اضافه، منفی = کم میکنه

    is_active = models.BooleanField(
        default=True
    )

    set_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        if self.is_active:
            GoldPriceOffset.objects.exclude(
                pk=self.pk
            ).update(is_active=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"طلا offset: {self.offset_amount}"


# =========================================================
# SILVER PRICE OFFSET
# =========================================================

class SilverPriceOffset(models.Model):

    offset_amount = models.DecimalField(
        max_digits=20,
        decimal_places=0,
        default=0
    )

    is_active = models.BooleanField(
        default=True
    )

    set_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        if self.is_active:
            SilverPriceOffset.objects.exclude(
                pk=self.pk
            ).update(is_active=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"نقره offset: {self.offset_amount}"