from rest_framework import serializers
from decimal import ROUND_DOWN, Decimal
from rest_framework import serializers
from decimal import Decimal
from accounts.models import BankCard, ReferralEarning

from .models import (
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
    SilverRecentTransaction,
    SilverRecentDelivery,
    UserAddress
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
        fields = [
            "id",
            "card_number",
            "bank_name",
            "is_active",
            "created_at"
        ]


# =========================================================
# WALLET
# =========================================================

class SilverWalletSerializer(serializers.ModelSerializer):

    available_balance = serializers.SerializerMethodField()

    class Meta:
        model = SilverWallet
        fields = [
            "balance",
            "blocked_balance",
            "available_balance",
            "updated_at"
        ]

    def get_available_balance(self, obj):
        return int(obj.balance - obj.blocked_balance)


# =========================================================
# INVENTORY
# =========================================================

class SilverInventorySerializer(serializers.ModelSerializer):

    available_balance = serializers.SerializerMethodField()

    class Meta:
        model = SilverInventory
        fields = [
            "balance",
            "blocked_balance",
            "available_balance",
            "updated_at"
        ]

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
            "created_at"
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
            "updated_at"
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




class SilverProductSerializer(serializers.ModelSerializer):

    category_name = serializers.CharField(
        source="category.name",
        read_only=True
    )

    image_url = serializers.SerializerMethodField()
    total_price = serializers.SerializerMethodField()

    class Meta:
        model = SilverProduct
        fields = [
            "id",
            "name",
            "category",
            "category_name",
            "delivery_type",
            "weight",
            "total_weight_with_fees",
            "buy_price",
            "sell_price",
            "total_price",
            "inventory_count",
            "image_url",   # 👈 مهم: image نه، image_url
            "description",
            "is_active",
            "created_at"
        ]

    # =========================
    # IMAGE FIX (قطعی)
    # =========================
    def get_image_url(self, obj):

        if not obj.image:
            return None

        request = self.context.get("request")

        # حالت استاندارد Django (بهترین حالت)
        if request:
            return request.build_absolute_uri(obj.image.url)

        # fallback (اگر request خراب بود)
        return f"https://api.darine.shop{obj.image.url}"

    # =========================
    # TOTAL PRICE
    # =========================
    def get_total_price(self, obj):

        if obj.buy_price and obj.total_weight_with_fees:
            return int(obj.buy_price * obj.total_weight_with_fees)

        if obj.buy_price:
            return int(obj.buy_price)

        return 0





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
            "weight_at_time"
        ]


# =========================================================
# ORDER (CHECKOUT)
# =========================================================

class SilverOrderSerializer(serializers.ModelSerializer):

    items = SilverOrderItemSerializer(many=True, read_only=True)

    payment_method_display = serializers.CharField(source="get_payment_method_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    delivery_type_display = serializers.CharField(source="get_delivery_type_display", read_only=True)

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
            "items"
        ]


# =========================================================
# PRICE HISTORY (CHART)
# =========================================================

class SilverPriceHistorySerializer(serializers.ModelSerializer):

    class Meta:
        model = SilverPriceHistory
        fields = [
            "id",
            "price",
            "created_at"
        ]


# =========================================================
# REFERRAL
# =========================================================

class SilverReferralEarningSerializer(serializers.ModelSerializer):

    class Meta:
        model = SilverReferralEarning
        fields = [
            "id",
            "amount",
            "source_type",
            "created_at"
        ]


# =========================================================
# RECENT TRANSACTIONS
# =========================================================

# class SilverRecentTransactionSerializer(serializers.Serializer):
#     id = serializers.IntegerField()
#     title = serializers.CharField()
#     amount = serializers.DecimalField(
#     max_digits=20,
#     decimal_places=0,
#     error_messages={
#         "required": "مبلغ الزامی است",
#         "invalid": "مبلغ نامعتبر است"
#     }
# )
#     status = serializers.CharField()
#     type = serializers.CharField()
#     created_at = serializers.DateTimeField()


class SilverRecentTransactionSerializer(serializers.Serializer):

    id = serializers.IntegerField()

    title = serializers.CharField()

    amount = serializers.DecimalField(
        max_digits=20,
        decimal_places=0
    )

    status = serializers.CharField()

    type = serializers.CharField()

    method = serializers.CharField(
        required=False,
        allow_null=True
    )

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

    METHOD_CHOICES = (
        ("RECEIPT", "رسید"),
        ("GATEWAY", "درگاه")
    )

    amount = serializers.DecimalField(
        max_digits=20,
        decimal_places=0,
        error_messages={
            "required": "مبلغ الزامی است",
            "invalid": "مبلغ نامعتبر است"
        }
    )

    method = serializers.ChoiceField(
        choices=METHOD_CHOICES
    )

    receipt = serializers.ImageField(
        required=False
    )

    description = serializers.CharField(
        required=False,
        allow_blank=True
    )

    def validate(self, attrs):

        method = attrs.get("method")
        receipt = attrs.get("receipt")

        if method == "RECEIPT" and not receipt:
            raise serializers.ValidationError({
                "receipt": "تصویر رسید الزامی است"
            })

        return attrs

# =========================================================
# BUY SILVER
# =========================================================



class BuySilverSerializer(serializers.Serializer):

    payment_method = serializers.ChoiceField(
        choices=[
            ("WALLET", "کیف پول"),
            ("GATEWAY", "درگاه")
        ]
    )

    toman = serializers.DecimalField(
        max_digits=20,
        decimal_places=2,
        required=False,
        allow_null=True
    )

    # 👇 مهم: validation سخت رو برمی‌داریم
    weight = serializers.DecimalField(
        max_digits=30,
        decimal_places=18,   # 👈 اجازه عدد خام فرانت
        required=False,
        allow_null=True
    )

    def validate(self, attrs):

        if not attrs.get("toman") and not attrs.get("weight"):
            raise serializers.ValidationError({
                "message": "مبلغ یا وزن الزامی است"
            })

        request = self.context.get("request")
        user = request.user
        silver_price = self.context.get("silver_price")

        user_fee = getattr(user, "fee", None)
        fee_rate = user_fee.silver_buy_fee if user_fee else Decimal("0.0099")

        attrs["fee_rate"] = fee_rate

        # ======================
        # CALCULATION
        # ======================

        if attrs.get("toman"):

            total_toman = Decimal(str(attrs["toman"]))
            fee = total_toman * fee_rate
            net = total_toman - fee

            weight = net / silver_price

        else:

            # 👇 اینجا trim واقعی انجام میشه
            weight = Decimal(str(attrs["weight"])).quantize(
                Decimal("0.00000001"),
                rounding=ROUND_DOWN
            )

            pure = weight * silver_price
            fee = pure * fee_rate
            total_toman = pure + fee

        attrs["fee"] = fee.quantize(Decimal("0.01"), rounding=ROUND_DOWN)
        attrs["total_toman"] = total_toman.quantize(Decimal("0.01"), rounding=ROUND_DOWN)
        attrs["final_weight"] = weight.quantize(Decimal("0.00000001"), rounding=ROUND_DOWN)

        return attrs
    

# =========================================================
# SELL SILVER
# =========================================================

class SellSilverSerializer(serializers.Serializer):

    toman = serializers.DecimalField(
        max_digits=20,
        decimal_places=2,
        required=False,
        allow_null=True
    )

    weight = serializers.DecimalField(
        max_digits=20,
        decimal_places=8,
        required=False,
        allow_null=True
    )

    fee = None
    fee_rate = None
    final_amount = None
    final_weight = None

    def validate(self, attrs):

        if not attrs.get("toman") and not attrs.get("weight"):
            raise serializers.ValidationError({
                "message": "مبلغ یا وزن الزامی است"
            })

        request = self.context.get("request")
        user = request.user

        silver_price = self.context.get("silver_price")

        # ======================
        # USER FEE
        # ======================
        user_fee = getattr(user, "fee", None)
        fee_rate = user_fee.silver_sell_fee if user_fee else Decimal("0.0099")

        attrs["fee_rate"] = fee_rate

        # ======================
        # CALCULATION
        # ======================
        if attrs.get("toman"):

            toman = Decimal(str(attrs["toman"]))

            final_weight = toman / silver_price
            fee = toman * fee_rate
            final_amount = toman - fee

        else:

            final_weight = Decimal(str(attrs["weight"]))

            pure = final_weight * silver_price
            fee = pure * fee_rate
            final_amount = pure - fee

        attrs["fee"] = fee
        attrs["final_amount"] = final_amount
        attrs["final_weight"] = final_weight

        return attrs
    


# =========================================================
# WITHDRAW
# =========================================================

class SilverWithdrawSerializer(serializers.Serializer):

    TARGET_CHOICES = (
        ("BANK", "بانک"),
        ("SILVER", "تبدیل به نقره"),
    )

    amount = serializers.DecimalField(
        max_digits=20,
        decimal_places=0,
        error_messages={
            "required": "مبلغ الزامی است",
            "invalid": "مبلغ نامعتبر است"
        }
    )

    target = serializers.ChoiceField(
        choices=TARGET_CHOICES,
        error_messages={
            "required": "نوع برداشت الزامی است",
            "invalid_choice": "نوع برداشت نامعتبر است"
        }
    )

    card_id = serializers.IntegerField(
        required=False,
        allow_null=True,
        error_messages={
            "invalid": "شناسه کارت نامعتبر است"
        }
    )

# =========================================================
# USER BALANCE (DASHBOARD)
# =========================================================

class SilverUserBalanceSerializer(serializers.Serializer):

    silver_balance_gr = serializers.DecimalField(max_digits=20, decimal_places=5)
    toman_balance = serializers.DecimalField(max_digits=20, decimal_places=0)
    current_silver_price = serializers.DecimalField(max_digits=20, decimal_places=0)
    total_assets = serializers.DecimalField(max_digits=20, decimal_places=0)


# =========================================================
# # CHART
# # =========================================================

# class SilverChartSerializer(serializers.Serializer):

#     labels = serializers.ListField(child=serializers.CharField())
#     prices = serializers.ListField(child=serializers.DecimalField(max_digits=20, decimal_places=0))
#     highest_price = serializers.DecimalField(max_digits=20, decimal_places=0)
#     lowest_price = serializers.DecimalField(max_digits=20, decimal_places=0)
#     change_percent = serializers.DecimalField(max_digits=10, decimal_places=2)
#     filter_type = serializers.CharField()


# silver_app/serializers.py

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

class UserAddressSerializer(serializers.ModelSerializer):

    class Meta:
        model = UserAddress
        fields = [
            "id",
            "province",
            "city",
            "address",
            "postal_code",
            "plaque",
            "unit",
            "created_at",
        ]


class SilverPhysicalOrderSerializer(serializers.Serializer):

    products = serializers.ListField(
        child=serializers.DictField(),
        allow_empty=False
    )

    payment_method = serializers.ChoiceField(
        choices=[
            ('TOMAN', 'کیف پول'),
            ('SILVER', 'نقره')
        ]
    )

    delivery_type = serializers.ChoiceField(
        choices=[
            ('HOME', 'ارسال'),
            ('IN_PERSON', 'حضوری')
        ]
    )

    # =========================
    # ADDRESS
    # =========================
    address_id = serializers.IntegerField(required=False, allow_null=True)

    province = serializers.CharField(required=False, allow_blank=True)
    city = serializers.CharField(required=False, allow_blank=True)
    address = serializers.CharField(required=False, allow_blank=True)

    postal_code = serializers.CharField(required=False, allow_blank=True)
    plaque = serializers.CharField(required=False, allow_blank=True)
    unit = serializers.CharField(required=False, allow_blank=True)

    def validate(self, data):

        products = data.get("products")

        if not products:
            raise serializers.ValidationError({
                "non_field_errors": ["سبد خرید خالی است"]
            })

        # validate each product item
        for item in products:

            if "product_id" not in item:
                raise serializers.ValidationError({
                    "non_field_errors": ["product_id الزامی است"]
                })

            if "quantity" not in item or int(item["quantity"]) < 1:
                raise serializers.ValidationError({
                    "non_field_errors": ["quantity نامعتبر است"]
                })

        address_id = data.get("address_id")
        province = data.get("province")
        city = data.get("city")
        address = data.get("address")

        # address logic
        if address_id and any([province, city, address]):
            raise serializers.ValidationError({
                "non_field_errors": ["یا آدرس قبلی یا جدید، نه هر دو"]
            })

        if not address_id:
            if not (province and city and address):
                raise serializers.ValidationError({
                    "non_field_errors": ["province, city, address الزامی است"]
                })

        return data
    

class SilverProductCategorySerializer(serializers.ModelSerializer):

    class Meta:
        model = SilverProductCategory
        fields = [
            "id",
            "name",
            "slug",
        ]