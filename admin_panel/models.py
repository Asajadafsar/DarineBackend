from django.db import models
from darine_config import settings

# admin_panel/models.py

from django.conf import settings


class AdminLog(models.Model):

    ACTION_TYPE = (
        ("AUTH", "Authentication"),
        ("USER", "User"),
        ("ADMIN", "Admin"),
        ("GOLD", "Gold"),
        ("SILVER", "Silver"),
        ("WALLET", "Wallet"),
        ("ORDER", "Order"),
        ("PAYMENT", "Payment"),
        ("PRICE", "Price"),
        ("PRODUCT", "Product"),
        ("GIFT_CARD", "Gift Card"),
        ("SETTING", "Setting"),
        ("SECURITY", "Security"),
        ("SERVER", "Server"),
        ("SYSTEM", "System"),
        ("OTHER", "Other"),
    )

    METHOD = (
        ("GET", "GET"),
        ("POST", "POST"),
        ("PUT", "PUT"),
        ("PATCH", "PATCH"),
        ("DELETE", "DELETE"),
    )

    LEVEL = (
        ("INFO", "Info"),
        ("WARNING", "Warning"),
        ("ERROR", "Error"),
        ("CRITICAL", "Critical"),
    )

    # ============================
    # USER
    # ============================

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="user_logs",
    )

    admin = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="admin_logs",
    )

    # ============================
    # ACTION
    # ============================

    action_type = models.CharField(max_length=30, choices=ACTION_TYPE, db_index=True)

    action = models.CharField(max_length=255, db_index=True)

    description = models.TextField(blank=True, null=True)

    level = models.CharField(max_length=20, choices=LEVEL, default="INFO")

    # ============================
    # MODEL
    # ============================

    app_name = models.CharField(max_length=100, blank=True, null=True)

    model_name = models.CharField(max_length=100, blank=True, null=True)

    object_id = models.CharField(max_length=100, blank=True, null=True)

    # ============================
    # REQUEST
    # ============================

    method = models.CharField(max_length=10, choices=METHOD, blank=True, null=True)

    endpoint = models.CharField(max_length=300, blank=True, null=True)

    request_data = models.JSONField(blank=True, null=True)

    response_data = models.JSONField(blank=True, null=True)

    response_status = models.PositiveIntegerField(blank=True, null=True)

    duration_ms = models.PositiveIntegerField(blank=True, null=True)

    # ============================
    # CLIENT
    # ============================

    ip_address = models.GenericIPAddressField(blank=True, null=True)

    forwarded_ip = models.GenericIPAddressField(blank=True, null=True)

    user_agent = models.TextField(blank=True, null=True)

    browser = models.CharField(max_length=150, blank=True, null=True)

    browser_version = models.CharField(max_length=100, blank=True, null=True)

    os = models.CharField(max_length=100, blank=True, null=True)

    device = models.CharField(max_length=100, blank=True, null=True)

    device_type = models.CharField(max_length=50, blank=True, null=True)

    # ============================
    # BEFORE / AFTER
    # ============================

    old_data = models.JSONField(blank=True, null=True)

    new_data = models.JSONField(blank=True, null=True)

    changed_fields = models.JSONField(blank=True, null=True)

    # ============================
    # SECURITY
    # ============================

    success = models.BooleanField(default=True)

    error_message = models.TextField(blank=True, null=True)

    # ============================
    # EXTRA
    # ============================

    tracking_code = models.CharField(
        max_length=150, blank=True, null=True, db_index=True
    )

    session_key = models.CharField(max_length=200, blank=True, null=True)

    extra = models.JSONField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]

        indexes = [
            models.Index(fields=["created_at"]),
            models.Index(fields=["action_type"]),
            models.Index(fields=["action"]),
            models.Index(fields=["user"]),
            models.Index(fields=["admin"]),
            models.Index(fields=["tracking_code"]),
            models.Index(fields=["response_status"]),
            models.Index(fields=["success"]),
        ]

    def __str__(self):

        if self.user:
            return f"{self.action} - {self.user.mobile}"

        if self.admin:
            return f"{self.action} - {self.admin.mobile}"

        return self.action





from django.db import models


class GoldBanner(models.Model):

    title = models.CharField(max_length=255, verbose_name="عنوان")

    image = models.ImageField(upload_to="gold/banners/", verbose_name="تصویر")

    link = models.URLField(blank=True, null=True, verbose_name="لینک")

    is_active = models.BooleanField(default=True, verbose_name="فعال")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "بنر طلا"
        verbose_name_plural = "بنرهای طلا"

    def __str__(self):
        return self.title


class SilverBanner(models.Model):

    title = models.CharField(max_length=255, verbose_name="عنوان")

    image = models.ImageField(upload_to="silver/banners/", verbose_name="تصویر")

    link = models.URLField(blank=True, null=True, verbose_name="لینک")

    is_active = models.BooleanField(default=True, verbose_name="فعال")

    created_at = models.DateTimeField(auto_now_add=True)

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

    offset_amount = models.DecimalField(max_digits=20, decimal_places=0, default=0)
    # مثبت = اضافه، منفی = کم میکنه

    is_active = models.BooleanField(default=True)

    set_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        if self.is_active:
            GoldPriceOffset.objects.exclude(pk=self.pk).update(is_active=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"طلا offset: {self.offset_amount}"


# =========================================================
# SILVER PRICE OFFSET
# =========================================================


class SilverPriceOffset(models.Model):

    offset_amount = models.DecimalField(max_digits=20, decimal_places=0, default=0)

    is_active = models.BooleanField(default=True)

    set_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        if self.is_active:
            SilverPriceOffset.objects.exclude(pk=self.pk).update(is_active=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"نقره offset: {self.offset_amount}"


# =========================================================
# GOLD ANNOUNCEMENT
# =========================================================


class GoldAnnouncement(models.Model):

    title = models.CharField(max_length=255, verbose_name="عنوان")

    description = models.TextField(verbose_name="توضیحات")

    link = models.URLField(blank=True, null=True, verbose_name="لینک")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "اطلاعیه طلا"
        verbose_name_plural = "اطلاعیه‌های طلا"

    def __str__(self):
        return self.title

class GoldAnnouncementRead(models.Model):

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    announcement = models.ForeignKey(
        GoldAnnouncement,
        on_delete=models.CASCADE
    )

    is_read = models.BooleanField(default=False)

    read_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "announcement")
        
        

# =========================================================
# SILVER ANNOUNCEMENT
# =========================================================


class SilverAnnouncement(models.Model):

    title = models.CharField(max_length=255, verbose_name="عنوان")

    description = models.TextField(verbose_name="توضیحات")

    link = models.URLField(blank=True, null=True, verbose_name="لینک")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "اطلاعیه نقره"
        verbose_name_plural = "اطلاعیه‌های نقره"

    def __str__(self):
        return self.title


class SilverAnnouncementRead(models.Model):

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    announcement = models.ForeignKey(
        SilverAnnouncement,
        on_delete=models.CASCADE
    )

    is_read = models.BooleanField(default=False)

    read_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "announcement")
        
        







# =========================================================
# GOLD BALANCE ADJUSTMENT
# =========================================================

class GoldBalanceAdjustment(models.Model):

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="gold_balance_adjustments",
    )

    admin = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_gold_balance_adjustments",
    )

    wallet_amount = models.DecimalField(
        max_digits=20,
        decimal_places=0,
        default=0,
    )

    gold_amount = models.DecimalField(
        max_digits=20,
        decimal_places=3,
        default=0,
    )

    admin_note = models.TextField(
        blank=True,
        null=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["-id"]
        verbose_name = "افزایش موجودی طلا"
        verbose_name_plural = "افزایش موجودی طلا"

    def __str__(self):
        return f"{self.user.mobile} - {self.id}"
    
    
    
    
    
    
    
    
    
# =========================================================
# SILVER BALANCE ADJUSTMENT
# =========================================================

class SilverBalanceAdjustment(models.Model):

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="silver_balance_adjustments",
    )

    admin = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_silver_balance_adjustments",
    )

    wallet_amount = models.DecimalField(
        max_digits=20,
        decimal_places=0,
        default=0,
    )

    silver_amount = models.DecimalField(
        max_digits=20,
        decimal_places=3,
        default=0,
    )

    admin_note = models.TextField(
        blank=True,
        null=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["-id"]
        verbose_name = "افزایش موجودی نقره"
        verbose_name_plural = "افزایش موجودی نقره"

    def __str__(self):
        return f"{self.user.mobile} - {self.id}"
    
    
    
    
# =========================================================
# GOLD BALANCE WITHDRAWAL
# =========================================================

class GoldBalanceWithdrawal(models.Model):

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="gold_balance_withdrawals",
    )

    admin = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_gold_balance_withdrawals",
    )

    wallet_amount = models.DecimalField(
        max_digits=20,
        decimal_places=0,
        default=0,
    )

    gold_amount = models.DecimalField(
        max_digits=20,
        decimal_places=3,
        default=0,
    )

    admin_note = models.TextField(
        blank=True,
        null=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["-id"]
        verbose_name = "برداشت موجودی طلا"
        verbose_name_plural = "برداشت موجودی طلا"

    def __str__(self):
        return f"{self.user.mobile} - {self.id}"
    
    
# =========================================================
# SILVER BALANCE WITHDRAWAL
# =========================================================

class SilverBalanceWithdrawal(models.Model):

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="silver_balance_withdrawals",
    )

    admin = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_silver_balance_withdrawals",
    )

    wallet_amount = models.DecimalField(
        max_digits=20,
        decimal_places=0,
        default=0,
    )

    silver_amount = models.DecimalField(
        max_digits=20,
        decimal_places=3,
        default=0,
    )

    admin_note = models.TextField(
        blank=True,
        null=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["-id"]
        verbose_name = "برداشت موجودی نقره"
        verbose_name_plural = "برداشت موجودی نقره"

    def __str__(self):
        return f"{self.user.mobile} - {self.id}"




