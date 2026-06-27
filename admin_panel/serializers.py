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
from .models import AdminLog, GoldPriceOffset,SilverPriceOffset

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


from rest_framework import serializers

from .models import AdminLog


from rest_framework import serializers

from admin_panel.models import GoldBanner
from admin_panel.models import SilverBanner





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
    created_at = serializers.DateTimeField(
        source="date_joined",
        read_only=True
    )
    class Meta:
        model = User
        exclude = ["password"]


class AdminUserDetailSerializer(serializers.ModelSerializer):
    created_at = serializers.DateTimeField(
        source="date_joined",
        read_only=True
    )
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

        return int(
            Decimal(str(obj.total_weight_with_fees))
            *
            Decimal(str(price))
        )

    def get_profit_amount(self, obj):

        try:

            return float(
                Decimal(str(obj.total_weight_with_fees))
                -
                Decimal(str(obj.weight))
            )

        except Exception:
            return 0

    def to_representation(self, instance):

        data = super().to_representation(instance)

        data["category_name"] = self.get_category_name(instance)

        return data

    
from decimal import Decimal
from rest_framework import serializers

class ProductCreateUpdateSerializer(serializers.ModelSerializer):

    class Meta:
        model = Product
        fields = "__all__"
        read_only_fields = (
            "total_weight_with_fees",
            "buy_price",
            "sell_price",
        )

    def validate(self, attrs):

        instance = self.instance

        weight = attrs.get(
            "weight",
            getattr(instance, "weight", None)
        )

        inventory_count = attrs.get(
            "inventory_count",
            getattr(instance, "inventory_count", 1)
        )

        fee_percent = attrs.get(
            "profit_percent",
            getattr(instance, "profit_percent", 0)
        )

        if weight is None:
            raise serializers.ValidationError({
                "weight": "وزن الزامی است"
            })

        gold_price = get_live_gold_price()

        if gold_price is None:
            raise serializers.ValidationError({
                "price": "قیمت طلا دریافت نشد"
            })

        weight = Decimal(str(weight))
        inventory_count = Decimal(str(inventory_count))
        fee_percent = Decimal(str(fee_percent))
        gold_price = Decimal(str(gold_price))

        # مقدار وزنی هر محصول
        product_weight_with_fee = (
            weight *
            (
                Decimal("1")
                +
                (fee_percent / Decimal("100"))
            )
        )

        # مقدار وزنی کل موجودی
        total_weight_with_fees = (
            inventory_count *
            product_weight_with_fee
        )

        # قیمت خرید کل موجودی
        buy_price = (
            inventory_count *
            weight *
            gold_price
        )

        # قیمت فروش کل موجودی
        sell_price = (
            total_weight_with_fees *
            gold_price
        )

        attrs["total_weight_with_fees"] = total_weight_with_fees
        attrs["buy_price"] = int(buy_price)
        attrs["sell_price"] = int(sell_price)

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

        if not obj.image:
            return None

        request = self.context.get("request")

        if request:
            return request.build_absolute_uri(
                obj.image.url
            )

        return obj.image.url

    def get_total_price(self, obj):

        price = get_live_silver_price()

        if price is None:
            return None

        return int(
            Decimal(str(obj.total_weight_with_fees))
            *
            Decimal(str(price))
        )

    def get_profit_amount(self, obj):

        try:

            return float(
                Decimal(str(obj.total_weight_with_fees))
                -
                Decimal(str(obj.weight))
            )

        except Exception:
            return 0

    def to_representation(self, instance):

        data = super().to_representation(instance)

        data["category_name"] = self.get_category_name(instance)

        return data


from decimal import Decimal
from rest_framework import serializers

class SilverProductCreateUpdateSerializer(serializers.ModelSerializer):

    class Meta:
        model = SilverProduct
        fields = "__all__"
        read_only_fields = (
            "total_weight_with_fees",
            "buy_price",
            "sell_price",
        )

    def validate(self, attrs):

        instance = self.instance

        weight = attrs.get(
            "weight",
            getattr(instance, "weight", None)
        )

        inventory_count = attrs.get(
            "inventory_count",
            getattr(instance, "inventory_count", 1)
        )

        fee_percent = attrs.get(
            "profit_percent",
            getattr(instance, "profit_percent", 0)
        )

        if weight is None:
            raise serializers.ValidationError({
                "weight": "وزن الزامی است"
            })

        silver_price = get_live_silver_price()

        if silver_price is None:
            raise serializers.ValidationError({
                "price": "قیمت نقره دریافت نشد"
            })

        weight = Decimal(str(weight))
        inventory_count = Decimal(str(inventory_count))
        fee_percent = Decimal(str(fee_percent))
        silver_price = Decimal(str(silver_price))

        # مقدار وزنی هر محصول
        product_weight_with_fee = (
            weight *
            (
                Decimal("1")
                +
                (fee_percent / Decimal("100"))
            )
        )

        # مقدار وزنی کل موجودی
        total_weight_with_fees = (
            inventory_count *
            product_weight_with_fee
        )

        # قیمت خرید کل موجودی
        buy_price = (
            inventory_count *
            weight *
            silver_price
        )

        # قیمت فروش کل موجودی
        sell_price = (
            total_weight_with_fees *
            silver_price
        )

        attrs["total_weight_with_fees"] = total_weight_with_fees
        attrs["buy_price"] = int(buy_price)
        attrs["sell_price"] = int(sell_price)

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

    user_mobile = serializers.CharField(
        source="user.mobile",
        read_only=True
    )

    items = SilverOrderItemSerializer(
        many=True,
        read_only=True
    )

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

    type_display = serializers.CharField(
        source="get_type_display",
        read_only=True
    )

    method_display = serializers.CharField(
        source="get_method_display",
        read_only=True
    )

    status_display = serializers.CharField(
        source="get_status_display",
        read_only=True
    )

    user_mobile = serializers.CharField(
        source="user.mobile",
        read_only=True
    )

    user_card_number = serializers.SerializerMethodField()

    receipt_image_url = serializers.SerializerMethodField()

    class Meta:
        model = SilverFinancialTransaction
        fields = [
            "id",

            "user",
            "user_mobile",

            "amount",

            "type",
            "type_display",

            "method",
            "method_display",

            "status",
            "status_display",

            "receipt_image",
            "receipt_image_url",

            "user_card",
            "user_card_number",

            "tracking_code",

            # 👇 اینا مهمن
            "description",
            "admin_note",

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
            return request.build_absolute_uri(
                obj.receipt_image.url
            )

        return f"https://api.darine.shop{obj.receipt_image.url}"


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





# =========================================================
# GOLD BANNER
# =========================================================

class GoldBannerSerializer(serializers.ModelSerializer):

    image_url = serializers.SerializerMethodField()

    link = serializers.URLField(
        required=False,
        allow_null=True,
        allow_blank=True,
        error_messages={
            "invalid": "لینک وارد شده معتبر نیست.",
            "blank": "لینک نمی‌تواند خالی باشد."
        }
    )

    class Meta:
        model = GoldBanner
        fields = [
            "id",
            "image",
            "image_url",
            "title",
            "link",
            "is_active",
            "created_at"
        ]

    def validate_link(self, value):

        if value and not value.startswith(
            ("http://", "https://")
        ):
            raise serializers.ValidationError(
                "لینک باید با http:// یا https:// شروع شود."
            )

        return value

    def get_image_url(self, obj):

        request = self.context.get("request")

        if not obj.image:
            return None

        return request.build_absolute_uri(
            obj.image.url
        )



# =========================================================
# SILVER BANNER
# =========================================================

class SilverBannerSerializer(serializers.ModelSerializer):

    image_url = serializers.SerializerMethodField()

    link = serializers.URLField(
        required=False,
        allow_null=True,
        allow_blank=True,
        error_messages={
            "invalid": "لینک وارد شده معتبر نیست.",
            "blank": "لینک نمی‌تواند خالی باشد."
        }
    )

    class Meta:
        model = SilverBanner
        fields = [
            "id",
            "image",
            "image_url",
            "title",
            "link",
            "is_active",
            "created_at",
        ]

    def validate_link(self, value):

        if value and not value.startswith(
            ("http://", "https://")
        ):
            raise serializers.ValidationError(
                "لینک باید با http:// یا https:// شروع شود."
            )

        return value

    def get_image_url(self, obj):

        request = self.context.get("request")

        if not obj.image:
            return None

        return request.build_absolute_uri(
            obj.image.url
        )

class AdminLogSerializer(serializers.ModelSerializer):


    admin_mobile = serializers.CharField(
        source="admin.mobile",
        read_only=True
    )


    user_mobile = serializers.CharField(
        source="user.mobile",
        read_only=True
    )


    action_type_display = serializers.CharField(
        source="get_action_type_display",
        read_only=True
    )


    class Meta:

        model = AdminLog

        fields = [

            "id",

            "admin",
            "admin_mobile",

            "user",
            "user_mobile",

            "action_type",
            "action_type_display",

            "model_name",
            "object_id",

            "action",
            "description",

            "created_at"
        ]



class AdminAnalyticsSerializer(serializers.Serializer):


    users_count = serializers.IntegerField()


    verified_users = serializers.IntegerField()


    pending_users = serializers.IntegerField()


    gold_buy_total = serializers.DecimalField(
        max_digits=30,
        decimal_places=0
    )


    gold_sell_total = serializers.DecimalField(
        max_digits=30,
        decimal_places=0
    )


    silver_buy_total = serializers.DecimalField(
        max_digits=30,
        decimal_places=0
    )


    silver_sell_total = serializers.DecimalField(
        max_digits=30,
        decimal_places=0
    )


    total_buy = serializers.DecimalField(
        max_digits=30,
        decimal_places=0
    )


    total_sell = serializers.DecimalField(
        max_digits=30,
        decimal_places=0
    )


    difference = serializers.DecimalField(
        max_digits=30,
        decimal_places=0
    )


    daily_transactions = serializers.IntegerField()


    weekly_transactions = serializers.IntegerField()


    monthly_transactions = serializers.IntegerField()


    server = serializers.JSONField()



class CooperationRequestListSerializer(serializers.ModelSerializer):

    class Meta:
        model = CooperationRequest
        fields = "__all__"
        
        


class GoldLiveSerializer(serializers.Serializer):
    buy_price = serializers.IntegerField()
    sell_price = serializers.IntegerField()
    bubble_amount = serializers.IntegerField()
    bubble_percent = serializers.FloatField()
    is_positive = serializers.BooleanField()


class GoldChartSerializer(serializers.Serializer):
    labels = serializers.ListField(child=serializers.CharField())
    prices = serializers.ListField(child=serializers.IntegerField())


class GoldStatsSerializer(serializers.Serializer):
    current_price = serializers.IntegerField()
    highest_price = serializers.IntegerField()
    lowest_price = serializers.IntegerField()
    change_amount = serializers.IntegerField()
    change_percent = serializers.FloatField()
    min_y = serializers.IntegerField()
    max_y = serializers.IntegerField()


class GoldChartDataSerializer(serializers.Serializer):
    chart = GoldChartSerializer()
    stats = GoldStatsSerializer()


# ---

class SilverLiveSerializer(serializers.Serializer):
    silver_price = serializers.IntegerField()      
    intrinsic_price = serializers.IntegerField()
    bubble_percent = serializers.FloatField()
    is_positive = serializers.BooleanField()


class SilverChartSerializer(serializers.Serializer):
    labels = serializers.ListField(child=serializers.CharField())
    prices = serializers.ListField(child=serializers.IntegerField())


class SilverStatsSerializer(serializers.Serializer):
    current_price = serializers.IntegerField()
    highest_price = serializers.IntegerField()
    lowest_price = serializers.IntegerField()
    change_amount = serializers.IntegerField()
    change_percent = serializers.FloatField()
    min_y = serializers.IntegerField()
    max_y = serializers.IntegerField()


class SilverChartDataSerializer(serializers.Serializer):
    chart = SilverChartSerializer()
    stats = SilverStatsSerializer()
       
        
class FinancialTransactionSerializer(serializers.ModelSerializer):

    type_display = serializers.CharField(
        source="get_type_display",
        read_only=True
    )

    method_display = serializers.CharField(
        source="get_method_display",
        read_only=True
    )

    status_display = serializers.CharField(
        source="get_status_display",
        read_only=True
    )

    user_mobile = serializers.CharField(
        source="user.mobile",
        read_only=True
    )

    user_card_number = serializers.SerializerMethodField()

    receipt_image_url = serializers.SerializerMethodField()

    class Meta:
        model = FinancialTransaction
        fields = [
            "id",

            "user",
            "user_mobile",

            "amount",

            "type",
            "type_display",

            "method",
            "method_display",

            "status",
            "status_display",

            "receipt_image",
            "receipt_image_url",

            "user_card",
            "user_card_number",

            "tracking_code",

            # 👇 اینا مهمن
            "description",
            "admin_note",

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
            return request.build_absolute_uri(
                obj.receipt_image.url
            )

        return f"https://api.darine.shop{obj.receipt_image.url}"
    
    
    

# =========================================================
# GOLD PRICE OFFSET
# =========================================================

class GoldPriceOffsetSerializer(serializers.ModelSerializer):
    set_by_mobile = serializers.CharField(
        source="set_by.mobile",
        read_only=True
    )

    class Meta:
        model = GoldPriceOffset
        fields = [
            "id",
            "offset_amount",
            "is_active",
            "set_by_mobile",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "is_active",
            "set_by_mobile",
            "created_at",
            "updated_at",
        ]


# =========================================================
# SILVER PRICE OFFSET
# =========================================================

class SilverPriceOffsetSerializer(serializers.ModelSerializer):
    set_by_mobile = serializers.CharField(
        source="set_by.mobile",
        read_only=True
    )

    class Meta:
        model = SilverPriceOffset
        fields = [
            "id",
            "offset_amount",
            "is_active",
            "set_by_mobile",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "is_active",
            "set_by_mobile",
            "created_at",
            "updated_at",
        ]