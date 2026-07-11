from rest_framework import serializers
from decimal import ROUND_DOWN, Decimal
from accounts.models import BankCard
from .utils import get_live_silver_price
from .models import (
    SilverOrderStatusHistory,
    SilverWallet,
    SilverInventory,
    SilverTransaction,
    SilverFinancialTransaction,
    SilverProduct,
    SilverProductCategory,
    SilverOrder,
    SilverOrderItem,
    SilverPriceHistory,
    SilverReferralEarning,
    UserAddress,
)

# =========================================================
# BASE RESPONSE
# =========================================================


class MessageResponseSerializer(serializers.Serializer):
    message = serializers.CharField()


# =========================================================
# BANK CARD
# =========================================================


class BankCardSerializer(serializers.ModelSerializer):

    class Meta:
        model = BankCard
        fields = ["id", "card_number", "bank_name", "is_active", "created_at"]


# =========================================================
# WALLET
# =========================================================


class SilverWalletSerializer(serializers.ModelSerializer):

    available_balance = serializers.SerializerMethodField()

    class Meta:
        model = SilverWallet
        fields = ["balance", "blocked_balance", "available_balance", "updated_at"]

    def get_available_balance(self, obj):
        return int(obj.balance - obj.blocked_balance)


# =========================================================
# INVENTORY
# =========================================================


class SilverInventorySerializer(serializers.ModelSerializer):

    available_balance = serializers.SerializerMethodField()

    class Meta:
        model = SilverInventory
        fields = ["balance", "blocked_balance", "available_balance", "updated_at"]

    def get_available_balance(self, obj):
        return round(obj.balance - obj.blocked_balance, 5)


# =========================================================
# TRANSACTION (BUY / SELL SILVER)
# =========================================================


class SilverTransactionSerializer(serializers.ModelSerializer):

    type_display = serializers.CharField(source="get_type_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    final_price = serializers.SerializerMethodField()

    class Meta:
        model = SilverTransaction
        fields = [
            "id",
            "type",
            "type_display",
            "status",
            "status_display",
            "amount_gr",
            "price_per_gram",
            "fee",
            "total_amount",
            "final_price",
            "tracking_code",
            "created_at",
        ]

    def get_final_price(self, obj):
        return int(obj.total_amount - obj.fee)


# =========================================================
# FINANCIAL (DEPOSIT / WITHDRAW)
# =========================================================


class SilverFinancialTransactionSerializer(serializers.ModelSerializer):

    type_display = serializers.CharField(source="get_type_display", read_only=True)
    method_display = serializers.CharField(source="get_method_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    user_card_number = serializers.SerializerMethodField()
    receipt_image_url = serializers.SerializerMethodField()

    class Meta:
        model = SilverFinancialTransaction
        fields = [
            "id",
            "amount",
            "type",
            "type_display",
            "method",
            "method_display",
            "status",
            "status_display",
            # raw + full url (مثل Gold)
            "receipt_image",
            "receipt_image_url",
            "user_card",
            "user_card_number",
            "tracking_code",
            "admin_note",
            "description",
            "created_at",
            "updated_at",
        ]

    def get_user_card_number(self, obj):
        return obj.user_card.card_number if obj.user_card else None

    def get_receipt_image_url(self, obj):

        if not obj.receipt_image:
            return None

        request = self.context.get("request")

        if request:
            return request.build_absolute_uri(obj.receipt_image.url)

        return f"https://api.darine.shop{obj.receipt_image.url}"


# =========================================================
# PRODUCT
# =========================================================


from rest_framework import serializers


class SilverProductSerializer(serializers.ModelSerializer):

    category_name = serializers.CharField(source="category.name", read_only=True)

    image_url = serializers.SerializerMethodField()

    # مقدار وزنی هر محصول با اجرت
    product_weight_with_fee = serializers.SerializerMethodField()

    # قیمت نهایی نمایش به کاربر
    total_price = serializers.SerializerMethodField()

    class Meta:
        model = SilverProduct
        fields = [
            "id",
            "name",
            "category",
            "category_name",
            "delivery_type",
            # وزن خالص
            "weight",
            # مقدار وزنی
            "product_weight_with_fee",
            # قیمت نهایی
            "sell_price",
            "total_price",
            "inventory_count",
            "image_url",
            "description",
            "is_active",
            "created_at",
        ]

    def get_image_url(self, obj):

        if not obj.image:
            return None

        request = self.context.get("request")

        if request:
            return request.build_absolute_uri(obj.image.url)

        return f"https://api.darine.shop{obj.image.url}"

    def get_product_weight_with_fee(self, obj):

        try:

            return float(
                Decimal(str(obj.weight))
                * (Decimal("1") + (Decimal(str(obj.profit_percent)) / Decimal("100")))
            )

        except Exception:
            return 0

    def get_total_price(self, obj):
        try:
            live_price = get_live_silver_price()
            if not live_price:
                return int(obj.sell_price or 0)
            total_price = Decimal(str(obj.total_weight_with_fees)) * Decimal(
                str(live_price)
            )
            return int(total_price)
        except Exception:
            return int(obj.sell_price or 0)


# =========================================================
# ORDER STATUS HISTORY
# =========================================================


class SilverOrderStatusHistorySerializer(serializers.ModelSerializer):

    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = SilverOrderStatusHistory
        fields = [
            "status",
            "status_display",
            "description",
            "created_at",
        ]


# =========================================================
# ORDER ITEM
# =========================================================


class SilverOrderItemSerializer(serializers.ModelSerializer):

    product_name = serializers.CharField(source="product.name", read_only=True)
    product_image = serializers.ImageField(source="product.image", read_only=True)

    class Meta:
        model = SilverOrderItem
        fields = [
            "id",
            "product",
            "product_name",
            "product_image",
            "quantity",
            "price_at_time",
            "weight_at_time",
        ]


# =========================================================
# ORDER (CHECKOUT)
# =========================================================


class SilverOrderSerializer(serializers.ModelSerializer):

    items = SilverOrderItemSerializer(many=True, read_only=True)

    payment_method_display = serializers.CharField(
        source="get_payment_method_display", read_only=True
    )

    status_display = serializers.CharField(source="get_status_display", read_only=True)

    delivery_type_display = serializers.CharField(
        source="get_delivery_type_display", read_only=True
    )

    status_history = SilverOrderStatusHistorySerializer(many=True, read_only=True)

    class Meta:
        model = SilverOrder
        fields = [
            "id",
            "province",
            "city",
            "address",
            "postal_code",
            "plaque",
            "unit",
            "payment_method",
            "payment_method_display",
            "delivery_type",
            "delivery_type_display",
            "status",
            "status_display",
            "total_silver_amount",
            "total_toman_amount",
            "tracking_code",
            "created_at",
            "admin_note",
            "items",
            "status_history",
        ]


# =========================================================
# PRICE HISTORY (CHART)
# =========================================================


class SilverPriceHistorySerializer(serializers.ModelSerializer):

    class Meta:
        model = SilverPriceHistory
        fields = ["id", "price", "created_at"]


# =========================================================
# REFERRAL
# =========================================================


class SilverReferralEarningSerializer(serializers.ModelSerializer):

    class Meta:
        model = SilverReferralEarning
        fields = ["id", "amount", "source_type", "created_at"]


class SilverRecentTransactionSerializer(serializers.Serializer):

    id = serializers.IntegerField()

    title = serializers.CharField()

    amount = serializers.DecimalField(max_digits=20, decimal_places=0)

    status = serializers.CharField()

    type = serializers.CharField()

    method = serializers.CharField(required=False, allow_null=True)

    created_at = serializers.DateTimeField()


# =========================================================
# RECENT DELIVERIES
# =========================================================


class SilverRecentDeliverySerializer(serializers.Serializer):
    id = serializers.IntegerField()
    delivery_type = serializers.CharField()
    status = serializers.CharField()
    total_amount = serializers.DecimalField(max_digits=20, decimal_places=0)
    created_at = serializers.DateTimeField()


# =========================================================
# DEPOSIT
# =========================================================

# =========================================================
# DEPOSIT
# =========================================================


class SilverDepositSerializer(serializers.Serializer):

    METHOD_CHOICES = (("RECEIPT", "رسید"), ("GATEWAY", "درگاه"))

    amount = serializers.DecimalField(
        max_digits=20,
        decimal_places=0,
        error_messages={"required": "مبلغ الزامی است", "invalid": "مبلغ نامعتبر است"},
    )

    method = serializers.ChoiceField(choices=METHOD_CHOICES)

    receipt = serializers.ImageField(required=False)

    description = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):

        method = attrs.get("method")
        receipt = attrs.get("receipt")

        if method == "RECEIPT" and not receipt:
            raise serializers.ValidationError({"receipt": "تصویر رسید الزامی است"})

        return attrs


# =========================================================
# BUY SILVER SERIALIZER
# =========================================================

from decimal import Decimal, ROUND_DOWN

from rest_framework import serializers

from accounts.models import FeeSetting, UserFee  # نام اپلیکیشن خود را جایگزین کنید


# =========================================================
# BUY SILVER SERIALIZER (FIXED - DIRECT FEE CALCULATION)
# =========================================================

from decimal import Decimal, ROUND_DOWN

from rest_framework import serializers

from accounts.models import FeeSetting

from decimal import Decimal, ROUND_DOWN
from rest_framework import serializers
from accounts.models import FeeSetting




from decimal import Decimal, ROUND_DOWN
from rest_framework import serializers
from accounts.models import FeeSetting

from decimal import Decimal, ROUND_DOWN
from rest_framework import serializers
from accounts.models import FeeSetting


class BuySilverSerializer(serializers.Serializer):
    """
    خرید نقره
    
    اگر weight ارسال شود:
        قیمت خالص = قیمت نقره × وزن
        کارمزد = قیمت خالص × نرخ کارمزد
        مبلغ کل = قیمت خالص + کارمزد
    
    اگر toman ارسال شود (مبلغ کل شامل کارمزد):
        قیمت خالص = مبلغ کل ÷ (۱ + نرخ کارمزد)
        کارمزد = مبلغ کل - قیمت خالص
        وزن = قیمت خالص ÷ قیمت نقره
        مبلغ کل = مبلغ وارد شده (همون toman)
    """
    
    payment_method = serializers.ChoiceField(
        choices=[("WALLET", "کیف پول")],
        required=True
    )
    toman = serializers.DecimalField(
        max_digits=25,
        decimal_places=2,
        required=False,
        allow_null=True,
    )
    weight = serializers.DecimalField(
        max_digits=20,
        decimal_places=3,
        required=False,
        allow_null=True,
    )

    def validate(self, attrs):
        toman = attrs.get("toman")
        weight = attrs.get("weight")

        # اعتبارسنجی: حداقل یکی باید وارد شده باشد
        if toman is None and weight is None:
            raise serializers.ValidationError(
                {"non_field_errors": ["وارد کردن مبلغ یا وزن الزامی است."]}
            )

        # اگر هر دو ارسال شدند، وزن ملاک است
        if toman is not None and weight is not None:
            weight = Decimal(str(weight)).quantize(Decimal("0.001"), rounding=ROUND_DOWN)
            if weight <= 0:
                raise serializers.ValidationError(
                    {"weight": ["وزن وارد شده باید بزرگتر از صفر باشد."]}
                )
            toman = None
            attrs["toman"] = None

        # دریافت قیمت نقره از context
        silver_price = Decimal(str(self.context["silver_price"]))
        if silver_price <= 0:
            raise serializers.ValidationError(
                {"non_field_errors": ["قیمت نقره نامعتبر است."]}
            )

        # دریافت نرخ کارمزد
        user = self.context["request"].user
        user_fee = getattr(user, "fee", None)

        if user_fee:
            fee_rate = user_fee.silver_buy_fee
        else:
            setting = FeeSetting.objects.last()
            fee_rate = setting.silver_buy_fee if setting else Decimal("0.01")

        fee_rate = Decimal(str(fee_rate))
        if fee_rate < 0:
            raise serializers.ValidationError(
                {"non_field_errors": ["کارمزد نامعتبر است."]}
            )

        # ===========================
        # خرید بر اساس وزن
        # ===========================
        if weight is not None:
            final_weight = weight
            pure_silver_price = (silver_price * final_weight).quantize(Decimal("1"))
            fee = (pure_silver_price * fee_rate).quantize(Decimal("1"))
            total_toman = (pure_silver_price + fee).quantize(Decimal("1"))

        # ===========================
        # خرید بر اساس مبلغ کل (کارمزد از مبلغ کم میشه)
        # ===========================
        else:
            toman = Decimal(str(toman)).quantize(Decimal("1"))
            if toman <= 0:
                raise serializers.ValidationError(
                    {"toman": ["مبلغ وارد شده باید بزرگتر از صفر باشد."]}
                )

            # ✅ قیمت خالص = مبلغ کل ÷ (۱ + نرخ کارمزد)
            pure_silver_price = (toman / (Decimal("1") + fee_rate)).quantize(Decimal("1"))
            
            # ✅ کارمزد = مبلغ کل - قیمت خالص
            fee = (toman - pure_silver_price).quantize(Decimal("1"))
            
            # ✅ وزن = قیمت خالص ÷ قیمت هر گرم نقره
            final_weight = (pure_silver_price / silver_price).quantize(
                Decimal("0.001"),
                rounding=ROUND_DOWN,
            )

            if final_weight <= 0:
                raise serializers.ValidationError(
                    {"non_field_errors": ["مبلغ وارد شده برای خرید حتی یک هزارم گرم نقره کافی نیست."]}
                )

            # ✅ مبلغ کل = همون مبلغ ورودی
            total_toman = toman

        # ذخیره در attrs
        attrs["fee_rate"] = fee_rate
        attrs["fee"] = fee
        attrs["silver_price"] = silver_price
        attrs["pure_silver_price"] = pure_silver_price
        attrs["total_toman"] = total_toman
        attrs["final_weight"] = final_weight

        return attrs
    
    

from decimal import Decimal, ROUND_DOWN
from rest_framework import serializers
from accounts.models import FeeSetting

# =========================================================
# silver_app/serializers.py - سریالایزر جدید ✅
# =========================================================

from decimal import Decimal, ROUND_DOWN, ROUND_UP
from rest_framework import serializers

# =========================================================
# SELL SILVER SERIALIZER - اصلاح شده (کسر کارمزد) ✅
# =========================================================

from decimal import Decimal, ROUND_DOWN, ROUND_UP
from rest_framework import serializers
from accounts.models import FeeSetting


class SellSilverSerializer(serializers.Serializer):
    """
    فروش نقره (کارمزد از مبلغ کاربر کسر میشود)
    
    اگر toman ارسال شود (مبلغی که کاربر دریافت میکند):
        کاربر ۱۰,۰۰۰,۰۰۰ وارد میکند
        کارمزد = ۱۰,۰۰۰,۰۰۰ × ۱٪ = ۱۰۰,۰۰۰
        ارزش خالص = ۱۰,۰۰۰,۰۰۰ + ۱۰۰,۰۰۰ = ۱۰,۱۰۰,۰۰۰
        وزن = ۱۰,۱۰۰,۰۰۰ ÷ قیمت نقره
        total_toman = ۱۰,۰۰۰,۰۰۰ (همون مبلغ دریافتی کاربر)
    """
    
    payment_method = serializers.ChoiceField(
        choices=[("WALLET", "کیف پول")],
        required=True
    )
    toman = serializers.DecimalField(
        max_digits=25, 
        decimal_places=2, 
        required=False, 
        allow_null=True
    )
    weight = serializers.DecimalField(
        max_digits=20, 
        decimal_places=3, 
        required=False, 
        allow_null=True
    )

    def validate(self, attrs):
        toman = attrs.get("toman")
        weight = attrs.get("weight")

        # ===========================
        # اعتبارسنجی
        # ===========================
        if toman is None and weight is None:
            raise serializers.ValidationError(
                {"non_field_errors": ["وارد کردن مبلغ یا وزن برای فروش الزامی است."]}
            )

        if toman is not None and weight is not None:
            weight = Decimal(str(weight)).quantize(Decimal("0.001"), rounding=ROUND_DOWN)
            if weight <= 0:
                raise serializers.ValidationError(
                    {"weight": ["وزن وارد شده باید بزرگتر از صفر باشد."]}
                )
            toman = None
            attrs["toman"] = None

        # ===========================
        # دریافت قیمت نقره
        # ===========================
        silver_price = Decimal(str(self.context["silver_price"]))
        if silver_price <= 0:
            raise serializers.ValidationError(
                {"non_field_errors": ["قیمت نقره نامعتبر است."]}
            )

        # ===========================
        # دریافت نرخ کارمزد
        # ===========================
        user = self.context["request"].user
        user_fee = getattr(user, "fee", None)

        if user_fee:
            fee_rate = user_fee.silver_sell_fee
        else:
            setting = FeeSetting.objects.last()
            fee_rate = setting.silver_sell_fee if setting else Decimal("0.01")

        fee_rate = Decimal(str(fee_rate))
        if fee_rate < 0:
            raise serializers.ValidationError(
                {"non_field_errors": ["کارمزد نامعتبر است."]}
            )

        # ===========================
        # فروش بر اساس وزن
        # ===========================
        if weight is not None:
            final_weight = weight
            # ارزش خالص نقره
            pure_value = (silver_price * final_weight).quantize(Decimal("1"))
            # کارمزد = ارزش خالص × نرخ کارمزد
            fee = (pure_value * fee_rate).quantize(Decimal("1"))
            # مبلغ نهایی که کاربر دریافت میکنه = ارزش خالص - کارمزد
            total_toman = (pure_value - fee).quantize(Decimal("1"))
            
            if total_toman < 0:
                raise serializers.ValidationError(
                    {"non_field_errors": ["کارمزد بیشتر از ارزش نقره است."]}
                )

        # ===========================
        # فروش بر اساس مبلغ (کاربر مبلغ دریافتی رو وارد میکنه) ✅
        # ===========================
        else:
            # ✅ مبلغی که کاربر دریافت میکنه (مثلاً ۱۰,۰۰۰,۰۰۰)
            total_toman = Decimal(str(toman)).quantize(Decimal("1"))
            if total_toman <= 0:
                raise serializers.ValidationError(
                    {"toman": ["مبلغ وارد شده باید بزرگتر از صفر باشد."]}
                )

            # ✅ کارمزد = مبلغ دریافتی × نرخ کارمزد
            fee = (total_toman * fee_rate).quantize(Decimal("1"))
            
            # ✅ ارزش خالص = مبلغ دریافتی + کارمزد
            pure_value = (total_toman + fee).quantize(Decimal("1"))
            
            # ✅ وزن = ارزش خالص ÷ قیمت هر گرم
            final_weight = (pure_value / silver_price).quantize(
                Decimal("0.001"),
                rounding=ROUND_DOWN,
            )

            if final_weight <= 0:
                raise serializers.ValidationError(
                    {"non_field_errors": ["مبلغ وارد شده برای فروش حتی یک هزارم گرم نقره کافی نیست."]}
                )

        # ===========================
        # ✅ ذخیره در attrs
        # ===========================
        attrs["fee_rate"] = fee_rate
        attrs["fee"] = fee  # کارمزد کسر شده
        attrs["silver_price"] = silver_price
        attrs["pure_value"] = pure_value  # ارزش خالص نقره (قبل از کسر کارمزد)
        attrs["pure_silver_price"] = pure_value  # کلید کمکی
        attrs["total_toman"] = total_toman  # ✅ مبلغ دریافتی کاربر (۱۰,۰۰۰,۰۰۰)
        attrs["final_weight"] = final_weight

        return attrs





# =========================================================
# WITHDRAW (SILVER)
# =========================================================


class SilverWithdrawSerializer(serializers.Serializer):

    TARGET_CHOICES = (
        ("BANK", "بانک"),
        ("GOLD", "تبدیل به طلا"),
    )

    amount = serializers.DecimalField(
        max_digits=20,
        decimal_places=0,
        error_messages={"required": "مبلغ الزامی است", "invalid": "مبلغ نامعتبر است"},
    )

    target = serializers.ChoiceField(
        choices=TARGET_CHOICES,
        error_messages={
            "required": "نوع برداشت الزامی است",
            "invalid_choice": "نوع برداشت نامعتبر است",
        },
    )

    card_id = serializers.IntegerField(
        required=False,
        allow_null=True,
        error_messages={"invalid": "شناسه کارت نامعتبر است"},
    )


# =========================================================
# USER BALANCE (DASHBOARD)
# =========================================================


class SilverBubbleSerializer(serializers.Serializer):
    silver_price = serializers.IntegerField()
    intrinsic_price = serializers.IntegerField()
    bubble_percent = serializers.FloatField()
    is_positive = serializers.BooleanField()


class SilverChartStatsSerializer(serializers.Serializer):
    current_price = serializers.IntegerField()
    highest_price = serializers.IntegerField()
    lowest_price = serializers.IntegerField()
    change_amount = serializers.IntegerField()
    change_percent = serializers.FloatField()
    min_y = serializers.IntegerField()
    max_y = serializers.IntegerField()


class SilverChartDataSerializer(serializers.Serializer):
    labels = serializers.ListField(child=serializers.CharField())
    prices = serializers.ListField(child=serializers.IntegerField())


class SilverChartSerializer(serializers.Serializer):
    chart = SilverChartDataSerializer()
    stats = SilverChartStatsSerializer()
    bubble = SilverBubbleSerializer()


from rest_framework import serializers
import re

from rest_framework import serializers


class UserAddressSerializer(serializers.ModelSerializer):

    class Meta:
        model = UserAddress
        fields = ["id", "province", "city", "address", "plaque", "unit", "postal_code"]
        read_only_fields = ["id"]

    def validate(self, attrs):

        required_fields = [
            "province",
            "city",
            "address",
            "plaque",
            "unit",
            "postal_code",
        ]

        # =========================
        # بررسی اجباری بودن
        # =========================
        for field in required_fields:
            value = attrs.get(field)

            if value is None or str(value).strip() == "":
                raise serializers.ValidationError({field: "این فیلد اجباری است"})

        # =========================
        # بررسی کد پستی
        # =========================
        postal_code = str(attrs.get("postal_code"))

        if not re.fullmatch(r"\d{10}", postal_code):
            raise serializers.ValidationError(
                {"postal_code": "کد پستی باید دقیقاً ۱۰ رقم عددی باشد"}
            )

        return attrs



# =========================================================
# SILVER CHECKOUT (NO ADDRESS)
# =========================================================

class SilverPhysicalOrderSerializer(serializers.Serializer):

    products = serializers.ListField(
        child=serializers.DictField(),
        allow_empty=False
    )

    payment_method = serializers.ChoiceField(
        choices=[
            ("TOMAN", "کیف پول"),
            ("SILVER", "نقره"),
        ]
    )

    def validate(self, data):

        products = data.get("products")

        if not products:
            raise serializers.ValidationError(
                {"non_field_errors": ["سبد خرید خالی است"]}
            )

        for item in products:

            if "product_id" not in item:
                raise serializers.ValidationError(
                    {"non_field_errors": ["product_id الزامی است"]}
                )

            if "quantity" not in item:
                raise serializers.ValidationError(
                    {"non_field_errors": ["quantity الزامی است"]}
                )

            if int(item["quantity"]) < 1:
                raise serializers.ValidationError(
                    {"non_field_errors": ["quantity نامعتبر است"]}
                )

        return data






class SilverProductCategorySerializer(serializers.ModelSerializer):

    class Meta:
        model = SilverProductCategory
        fields = [
            "id",
            "name",
            "slug",
        ]




# silver_app/serializers.py

from rest_framework import serializers
from decimal import Decimal, ROUND_DOWN
from .models import SilverLimitOrder, SilverWallet, SilverInventory
from accounts.models import FeeSetting, UserFee


class SilverLimitOrderCreateSerializer(serializers.Serializer):
    """
    سریالایزر ایجاد سفارش با قیمت برای نقره
    """
    order_type = serializers.ChoiceField(
        choices=[('BUY', 'خرید'), ('SELL', 'فروش')],
        required=True,
        error_messages={
            'required': 'نوع سفارش الزامی است',
            'blank': 'نوع سفارش نمی‌تواند خالی باشد',
        }
    )
    target_price = serializers.DecimalField(
        max_digits=20,
        decimal_places=0,
        required=True,
        min_value=Decimal("1"),
        error_messages={
            'required': 'قیمت مد نظر الزامی است',
            'blank': 'قیمت مد نظر نمی‌تواند خالی باشد',
            'min_value': 'قیمت مد نظر باید بزرگتر از صفر باشد',
        }
    )
    amount_toman = serializers.DecimalField(
        max_digits=20,
        decimal_places=0,
        required=False,
        allow_null=True,
        error_messages={
            'invalid': 'مبلغ به تومان نامعتبر است',
        }
    )
    silver_weight = serializers.DecimalField(
        max_digits=20,
        decimal_places=3,
        required=False,
        allow_null=True,
        error_messages={
            'invalid': 'وزن نقره نامعتبر است',
        }
    )

    def validate(self, attrs):
        user = self.context['request'].user
        order_type = attrs.get('order_type')
        target_price = attrs.get('target_price')
        amount_toman = attrs.get('amount_toman')
        silver_weight = attrs.get('silver_weight')

        # دریافت نرخ کارمزد
        user_fee = getattr(user, 'fee', None)
        if user_fee:
            fee_rate = user_fee.silver_buy_fee if order_type == 'BUY' else user_fee.silver_sell_fee
        else:
            setting = FeeSetting.objects.last()
            fee_rate = setting.silver_buy_fee if order_type == 'BUY' else setting.silver_sell_fee
            fee_rate = fee_rate if fee_rate else Decimal("0.0099")

        fee_rate = Decimal(str(fee_rate))

        # =============================================
        # خرید نقره
        # =============================================
        if order_type == 'BUY':
            if not amount_toman:
                raise serializers.ValidationError({'amount_toman': 'مبلغ به تومان الزامی است'})
            
            toman = amount_toman
            total_price = toman.quantize(Decimal("1"))
            estimated_weight = (total_price / (target_price * (Decimal("1") + fee_rate))).quantize(
                Decimal("0.001"), rounding=ROUND_DOWN
            )
            estimated_weight = max(estimated_weight, Decimal("0.001"))
            
            pure_price = (target_price * estimated_weight).quantize(Decimal("1"))
            fee = (pure_price * fee_rate).quantize(Decimal("1"))
            
            wallet, _ = SilverWallet.objects.get_or_create(user=user)
            if wallet.accessible_toman < total_price:
                raise serializers.ValidationError({'amount_toman': 'موجودی کیف پول نقره کافی نیست'})
            
            attrs['estimated_weight'] = estimated_weight
            attrs['fee'] = fee
            attrs['fee_rate'] = fee_rate
            attrs['pure_price'] = pure_price

        # =============================================
        # فروش نقره
        # =============================================
        else:  # SELL
            if not silver_weight:
                raise serializers.ValidationError({'silver_weight': 'وزن نقره الزامی است'})
            
            weight = silver_weight
            pure_price = (target_price * weight).quantize(Decimal("1"))
            fee = (pure_price * fee_rate).quantize(Decimal("1"))
            total_price = (pure_price - fee).quantize(Decimal("1"))
            estimated_weight = weight
            
            if total_price <= 0:
                raise serializers.ValidationError({'silver_weight': 'وزن وارد شده برای فروش کافی نیست'})
            
            inventory, _ = SilverInventory.objects.get_or_create(user=user)
            if inventory.accessible_balance < weight:
                raise serializers.ValidationError({'silver_weight': 'موجودی نقره شما کافی نیست'})
            
            attrs['estimated_weight'] = estimated_weight
            attrs['fee'] = fee
            attrs['fee_rate'] = fee_rate
            attrs['pure_price'] = pure_price
            attrs['total_price'] = total_price

        return attrs

# =========================================================
# SILVER ORDER LIST SERIALIZER
# =========================================================
class SilverOrderListSerializer(serializers.ModelSerializer):
    """
    سریالایزر لیست سفارشات با قیمت نقره
    """
    type = serializers.CharField(source='order_type', read_only=True)
    type_display = serializers.CharField(source='get_order_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    amount_gr = serializers.CharField(source='silver_weight', read_only=True)
    price_per_gram = serializers.CharField(source='target_price', read_only=True)
    final_price = serializers.CharField(source='executed_price', read_only=True)
    total_amount = serializers.CharField(source='amount_toman', read_only=True)
    
    # محاسبه کارمزد (اگر در مدل نیست)
    fee = serializers.SerializerMethodField()
    tracking_code = serializers.SerializerMethodField()

    class Meta:
        model = SilverLimitOrder
        fields = [
            'id',
            'type',
            'type_display',
            'status',
            'status_display',
            'amount_gr',
            'price_per_gram',
            'fee',
            'total_amount',
            'final_price',
            'tracking_code',
            'description',
            'created_at',
            'updated_at'
        ]

    def get_fee(self, obj):
        """محاسبه کارمزد بر اساس مبلغ و نرخ کارمزد"""
        if obj.amount_toman and obj.fee_rate:
            return (obj.amount_toman * obj.fee_rate).quantize(Decimal("1"))
        return Decimal("0")

    def get_tracking_code(self, obj):
        """ساخت کد رهگیری برای سفارشات نقره"""
        return f"SILVER-{obj.id:06d}"