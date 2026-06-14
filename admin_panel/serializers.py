from rest_framework import serializers
from decimal import Decimal
import uuid

from accounts.models import CooperationRequest, User, UserFee

from gold_app.models import (
    Product,
    ProductCategory,
    GoldBankInfo,
    GoldTransaction,
    FinancialTransaction,
    GiftCard,
    GiftCardOrder,
    Order,
    OrderItem
)

from silver_app.models import (
    SilverProduct,
    SilverProductCategory,
    SilverBankInfo,
    SilverFinancialTransaction,
    SilverOrder,
    SilverOrderItem,
    SilverTransaction
)
from django.conf import settings
from gold_app.utils import get_live_gold_price
from silver_app.utils import get_live_silver_price
from rest_framework import serializers






class BaseMessageSerializer(serializers.ModelSerializer):
    success_message = None
    error_messages = {}

    def get_success_message(self):
        return self.success_message or "عملیات موفق بود"

    def fail(self, field, msg):
        raise serializers.ValidationError({field: msg})
    

class BaseModelMessageSerializer(BaseMessageSerializer):

    def create(self, validated_data):
        obj = super().create(validated_data)
        self.instance = obj
        return obj

    def update(self, instance, validated_data):
        obj = super().update(instance, validated_data)
        self.instance = obj
        return obj

# =========================================================
# USER
# =========================================================

class AdminUserListSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        exclude = ["password"]


class AdminUserDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        exclude = ["password"]


class AdminUserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "username",
            "first_name",
            "last_name",
            "email",
            "mobile",
            "national_code",
            "birth_date",
            "card_number",
            "shaba_number",
            "referral_code",
            "role",
            "auth_status",
            "is_active",
            "referred_by",
        ]


# =========================================================
# USER FEE
# =========================================================

class UserFeeSerializer(serializers.ModelSerializer):
    user_mobile = serializers.CharField(source="user.mobile", read_only=True)

    class Meta:
        model = UserFee
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at", "user_mobile"]

class UserFeeUpdateSerializer(serializers.ModelSerializer):
    success_message = "کارمزدها با موفقیت آپدیت شد"
    class Meta:
        model = UserFee
        fields = [
            "gold_buy_fee",
            "gold_sell_fee",
            "silver_buy_fee",
            "silver_sell_fee",
        ]

    def validate(self, attrs):

        for field, value in attrs.items():

            if value is None:
                continue

            value = float(value)

            # 🔥 تبدیل درصد (2 → 0.02)
            if value > 1:
                value = value / 100

            if value < 0:
                raise serializers.ValidationError({
                    field: "کارمزد نمی‌تواند منفی باشد"
                })

            if value > 1:
                raise serializers.ValidationError({
                    field: "مقدار غیرمجاز است"
                })

            attrs[field] = value

        return attrs




# =========================================================
# PRODUCT (GOLD)
# =========================================================

class ProductCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductCategory
        fields = "__all__"






class ProductSerializer(serializers.ModelSerializer):

    image_url = serializers.SerializerMethodField()
    total_price = serializers.SerializerMethodField()
    profit_amount = serializers.SerializerMethodField()
    category_name = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = "__all__"

    def get_category_name(self, obj):
        return obj.category.name if obj.category else None

    def get_image_url(self, obj):

        if not obj.image:
            return None

        request = self.context.get("request")

        if request:
            return request.build_absolute_uri(
                obj.image.url
            )

        return obj.image.url

    def get_total_price(self, obj):

        price = get_live_gold_price()

        if price is None:
            return None

        price = Decimal(str(price))
        weight = Decimal(str(obj.weight))
        profit_percent = Decimal(str(obj.profit_percent or 0))

        base = weight * price
        profit = (base * profit_percent) / Decimal("100")

        return int(base + profit)

    def get_profit_amount(self, obj):

        price = get_live_gold_price()

        if price is None:
            return None

        price = Decimal(str(price))
        weight = Decimal(str(obj.weight))
        profit_percent = Decimal(str(obj.profit_percent or 0))

        base = weight * price
        profit = (base * profit_percent) / Decimal("100")

        return int(profit)

    def get_category_name(self, obj):
        return obj.category.name if obj.category else None
    
class ProductCreateUpdateSerializer(serializers.ModelSerializer):

    class Meta:
        model = Product
        fields = "__all__"

    def validate(self, attrs):

        instance = self.instance

        weight = attrs.get("weight", getattr(instance, "weight", None))
        profit_percent = attrs.get(
            "profit_percent",
            getattr(instance, "profit_percent", 0)
        )

        if weight is None:
            raise serializers.ValidationError({
                "weight": "وزن الزامی است"
            })

        price_data = get_live_gold_price()

        if price_data is None:
            raise serializers.ValidationError({
                "price": "قیمت طلا دریافت نشد"
            })

        # ✅ SAFE conversion
        price = Decimal(str(price_data))
        weight = Decimal(str(weight))
        profit_percent = Decimal(str(profit_percent))

        base_price = weight * price
        profit_amount = (base_price * profit_percent) / Decimal("100")
        total_price = base_price + profit_amount

        attrs["buy_price"] = int(base_price)
        attrs["sell_price"] = int(total_price)
        attrs["total_weight_with_fees"] = weight

        return attrs




# =========================================================
# PRODUCT (SILVER)
# =========================================================

class SilverProductCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = SilverProductCategory
        fields = "__all__"


class SilverProductSerializer(serializers.ModelSerializer):

    image_url = serializers.SerializerMethodField()
    total_price = serializers.SerializerMethodField()
    profit_amount = serializers.SerializerMethodField()
    category_name = serializers.SerializerMethodField()

    class Meta:
        model = SilverProduct
        fields = "__all__"

    def get_category_name(self, obj):
        return obj.category.name if obj.category else None

    def get_image_url(self, obj):
        request = self.context.get("request")

        if obj.image:
            url = obj.image.url
            return request.build_absolute_uri(url) if request else url

        return None

    def get_total_price(self, obj):

        price = get_live_silver_price()

        if price is None:
            return None

        price = Decimal(str(price))
        weight = Decimal(str(obj.weight))
        profit_percent = Decimal(str(obj.profit_percent or 0))

        base = weight * price
        profit = (base * profit_percent) / Decimal("100")

        return int(base + profit)

    def get_profit_amount(self, obj):

        price = get_live_silver_price()

        if price is None:
            return None

        price = Decimal(str(price))
        weight = Decimal(str(obj.weight))
        profit_percent = Decimal(str(obj.profit_percent or 0))

        base = weight * price

        return int((base * profit_percent) / Decimal("100"))

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["category_name"] = self.get_category_name(instance)
        return data

class SilverProductCreateUpdateSerializer(serializers.ModelSerializer):

    class Meta:
        model = SilverProduct
        fields = "__all__"

    def validate(self, attrs):

        instance = self.instance

        weight = attrs.get("weight", getattr(instance, "weight", None))
        profit_percent = attrs.get(
            "profit_percent",
            getattr(instance, "profit_percent", 0)
        )

        if weight is None:
            raise serializers.ValidationError({
                "weight": "وزن الزامی است"
            })

        price = get_live_silver_price()

        if not price:
            raise serializers.ValidationError({
                "price": "قیمت نقره دریافت نشد"
            })

        price = Decimal(str(price))
        weight = Decimal(str(weight))
        profit_percent = Decimal(str(profit_percent))

        # ======================
        # BASE PRICE
        # ======================
        base_price = weight * price

        # ======================
        # PROFIT
        # ======================
        profit_amount = (base_price * profit_percent) / Decimal("100")

        # ======================
        # FINAL PRICE (TOTAL)
        # ======================
        total_price = base_price + profit_amount

        # ======================
        # SAVE ONLY DB FIELDS
        # ======================
        attrs["buy_price"] = int(base_price)
        attrs["sell_price"] = int(total_price)
        attrs["total_weight_with_fees"] = weight

        return attrs






from rest_framework import serializers
from gold_app.models import GoldBankInfo


class GoldBankInfoSerializer(serializers.ModelSerializer):

    class Meta:
        model = GoldBankInfo
        fields = "__all__"


class GoldBankInfoCreateUpdateSerializer(serializers.ModelSerializer):

    success_message = "کارت بانکی با موفقیت ثبت/ویرایش شد"

    class Meta:
        model = GoldBankInfo
        fields = "__all__"

    # =========================
    # REMOVE DRF UNIQUE VALIDATOR
    # =========================
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # جلوگیری از خطای انگلیسی unique
        self.fields['card_number'].validators = []
        self.fields['sheba'].validators = []

    # =========================
    # CARD NUMBER VALIDATION
    # =========================
    def validate_card_number(self, value):

        value = value.replace(" ", "").replace("-", "")

        if not value.isdigit():
            raise serializers.ValidationError("شماره کارت نامعتبر است")

        if len(value) != 16:
            raise serializers.ValidationError("شماره کارت باید 16 رقم باشد")

        qs = GoldBankInfo.objects.filter(card_number=value)

        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)

        if qs.exists():
            raise serializers.ValidationError("این شماره کارت قبلاً ثبت شده است")

        return value

    # =========================
    # SHEBA VALIDATION
    # =========================
    def validate_sheba(self, value):

        value = value.strip().upper()

        if not value.startswith("IR"):
            raise serializers.ValidationError("شماره شبا باید با IR شروع شود")

        if len(value) != 26:
            raise serializers.ValidationError("شماره شبا باید 26 کاراکتر باشد")

        if not value[2:].isdigit():
            raise serializers.ValidationError("فرمت شماره شبا نامعتبر است")

        qs = GoldBankInfo.objects.filter(sheba=value)

        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)

        if qs.exists():
            raise serializers.ValidationError("این شماره شبا قبلاً ثبت شده است")

        return value
    

from rest_framework import serializers
from silver_app.models import SilverBankInfo


class SilverBankInfoSerializer(serializers.ModelSerializer):

    class Meta:
        model = SilverBankInfo
        fields = "__all__"


class SilverBankInfoCreateUpdateSerializer(serializers.ModelSerializer):

    success_message = "کارت بانکی با موفقیت ثبت/ویرایش شد"

    class Meta:
        model = SilverBankInfo
        fields = "__all__"

    # =========================
    # REMOVE DRF UNIQUE VALIDATOR
    # =========================
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['card_number'].validators = []
        self.fields['sheba'].validators = []

    # =========================
    # CARD NUMBER VALIDATION
    # =========================
    def validate_card_number(self, value):

        value = value.replace(" ", "").replace("-", "")

        if not value.isdigit():
            raise serializers.ValidationError("شماره کارت نامعتبر است")

        if len(value) != 16:
            raise serializers.ValidationError("شماره کارت باید 16 رقم باشد")

        qs = SilverBankInfo.objects.filter(card_number=value)

        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)

        if qs.exists():
            raise serializers.ValidationError("این شماره کارت قبلاً ثبت شده است")

        return value

    # =========================
    # SHEBA VALIDATION
    # =========================
    def validate_sheba(self, value):

        value = value.strip().upper()

        if not value.startswith("IR"):
            raise serializers.ValidationError("شماره شبا باید با IR شروع شود")

        if len(value) != 26:
            raise serializers.ValidationError("شماره شبا باید 26 کاراکتر باشد")

        if not value[2:].isdigit():
            raise serializers.ValidationError("فرمت شماره شبا نامعتبر است")

        qs = SilverBankInfo.objects.filter(sheba=value)

        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)

        if qs.exists():
            raise serializers.ValidationError("این شماره شبا قبلاً ثبت شده است")

        return value












# ORDERS
# =========================================================

class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)

    class Meta:
        model = OrderItem
        fields = "__all__"


class OrderSerializer(serializers.ModelSerializer):
    user_mobile = serializers.CharField(source="user.mobile", read_only=True)
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = "__all__"


class SilverOrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)

    class Meta:
        model = SilverOrderItem
        fields = "__all__"


class SilverOrderSerializer(serializers.ModelSerializer):
    items = SilverOrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = SilverOrder
        fields = "__all__"


# =========================================================
# TRANSACTIONS
# =========================================================

class FinancialTransactionSerializer(serializers.ModelSerializer):
    user_mobile = serializers.CharField(source="user.mobile", read_only=True)

    class Meta:
        model = FinancialTransaction
        fields = "__all__"


class SilverFinancialTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = SilverFinancialTransaction
        fields = "__all__"


class GoldTransactionSerializer(serializers.ModelSerializer):
    user_mobile = serializers.CharField(source="user.mobile", read_only=True)

    class Meta:
        model = GoldTransaction
        fields = "__all__"


class SilverTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = SilverTransaction
        fields = "__all__"


# =========================================================
# GIFT CARD
# =========================================================

class GiftCardSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source="created_by.mobile", read_only=True)
    activated_by_name = serializers.CharField(source="activated_by.mobile", read_only=True)

    class Meta:
        model = GiftCard
        fields = "__all__"


class GiftCardCreateUpdateSerializer(serializers.ModelSerializer):
    success_message = " گیفت کارت با موفقیت ثبت/ویرایش شد"
    class Meta:
        model = GiftCard
        fields = "__all__"
        extra_kwargs = {
            "created_by": {"read_only": True},
            "activated_by": {"read_only": True},
        }

    def validate(self, attrs):
        if not attrs.get("serial_number"):
            attrs["serial_number"] = str(uuid.uuid4()).split("-")[0].upper()

        return attrs


# =========================================================
# STATUS UPDATE
# =========================================================

class StatusUpdateSerializer(serializers.Serializer):
    status = serializers.CharField(required=True)
    admin_note = serializers.CharField(required=False, allow_blank=True)


# =========================================================
# DASHBOARD
# =========================================================

class AdminDashboardSerializer(serializers.Serializer):
    users_count = serializers.IntegerField()
    verified_users = serializers.IntegerField()
    pending_users = serializers.IntegerField()

    gold_products = serializers.IntegerField()
    silver_products = serializers.IntegerField()

    gold_orders = serializers.IntegerField()
    silver_orders = serializers.IntegerField()

    pending_orders = serializers.IntegerField()

    gold_transactions = serializers.IntegerField()
    silver_transactions = serializers.IntegerField()

    total_wallet_balance = serializers.DecimalField(max_digits=30, decimal_places=0)
    total_silver_wallet_balance = serializers.DecimalField(max_digits=30, decimal_places=0)

    total_gold_inventory = serializers.DecimalField(max_digits=30, decimal_places=5)
    total_silver_inventory = serializers.DecimalField(max_digits=30, decimal_places=5)

    total_deposit_amount = serializers.DecimalField(max_digits=30, decimal_places=0)
    pending_withdraw_amount = serializers.DecimalField(max_digits=30, decimal_places=0)

    recent_users = serializers.ListField()
    recent_orders = serializers.ListField()


class CooperationRequestListSerializer(serializers.ModelSerializer):

    class Meta:
        model = CooperationRequest
        fields = "__all__"
        
        
        
        
class FinancialTransactionSerializer(serializers.ModelSerializer):

    user_mobile = serializers.CharField(source="user.mobile", read_only=True)
    receipt_url = serializers.SerializerMethodField()

    class Meta:
        model = FinancialTransaction
        fields = "__all__"

    def get_receipt_url(self, obj):

        if not obj.receipt_image:
            return None

        request = self.context.get("request")

        if request:
            return request.build_absolute_uri(obj.receipt_image.url)

        return obj.receipt_image.url
    
    
    
