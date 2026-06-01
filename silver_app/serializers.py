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

    method_display = serializers.CharField(source="get_method_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    user_card_number = serializers.SerializerMethodField()

    class Meta:
        model = SilverFinancialTransaction
        fields = [
            "id",
            "amount",
            "type",
            "method",
            "method_display",
            "status",
            "status_display",
            "user_card",
            "user_card_number",
            "receipt_image",
            "tracking_code",
            "created_at"
        ]

    def get_user_card_number(self, obj):
        return obj.user_card.card_number if obj.user_card else None


# =========================================================
# PRODUCT
# =========================================================

class SilverProductSerializer(serializers.ModelSerializer):

    category_name = serializers.CharField(source="category.name", read_only=True)

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
            "inventory_count",
            "image",
            "description",
            "is_active",
            "created_at"
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

class SilverRecentTransactionSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    title = serializers.CharField()
    amount = serializers.DecimalField(
    max_digits=20,
    decimal_places=0,
    error_messages={
        "required": "مبلغ الزامی است",
        "invalid": "مبلغ نامعتبر است"
    }
)
    status = serializers.CharField()
    type = serializers.CharField()
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
    method = serializers.ChoiceField(choices=METHOD_CHOICES)
    receipt = serializers.ImageField(required=False)


# =========================================================
# BUY SILVER
# =========================================================

class BuySilverSerializer(serializers.Serializer):

    payment_method = serializers.ChoiceField(
        choices=[
            ("WALLET", "کیف پول"),
            ("GATEWAY", "درگاه")
        ],
        error_messages={
            "required": "روش پرداخت الزامی است",
            "invalid_choice": "روش پرداخت نامعتبر است"
        }
    )

    toman = serializers.DecimalField(
        max_digits=20,
        decimal_places=2,
        required=False,
        allow_null=True,
        error_messages={
            "invalid": "مبلغ نامعتبر است"
        }
    )

    weight = serializers.DecimalField(
        max_digits=20,
        decimal_places=8,
        required=False,
        allow_null=True,
        error_messages={
            "invalid": "وزن نامعتبر است"
        }
    )

    def validate(self, attrs):
        if not attrs.get("toman") and not attrs.get("weight"):
            raise serializers.ValidationError({
                "non_field_errors": ["مبلغ یا وزن الزامی است"]
            })
        return attrs


# =========================================================
# SELL SILVER
# =========================================================

class SellSilverSerializer(serializers.Serializer):

    toman = serializers.DecimalField(
        max_digits=20,
        decimal_places=2,
        required=False,
        allow_null=True,
        error_messages={
            "invalid": "مبلغ نامعتبر است"
        }
    )

    weight = serializers.DecimalField(
        max_digits=20,
        decimal_places=8,
        required=False,
        allow_null=True,
        error_messages={
            "invalid": "وزن نامعتبر است"
        }
    )

    def validate(self, attrs):
        if not attrs.get("toman") and not attrs.get("weight"):
            raise serializers.ValidationError({
                "non_field_errors": ["مبلغ یا وزن الزامی است"]
            })
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
# CHART
# =========================================================

class SilverChartSerializer(serializers.Serializer):

    labels = serializers.ListField(child=serializers.CharField())
    prices = serializers.ListField(child=serializers.DecimalField(max_digits=20, decimal_places=0))
    highest_price = serializers.DecimalField(max_digits=20, decimal_places=0)
    lowest_price = serializers.DecimalField(max_digits=20, decimal_places=0)
    change_percent = serializers.DecimalField(max_digits=10, decimal_places=2)
    filter_type = serializers.CharField()




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

    product_id = serializers.IntegerField(
        error_messages={
            "required": "شناسه محصول الزامی است",
            "invalid": "شناسه محصول نامعتبر است"
        }
    )

    quantity = serializers.IntegerField(
        min_value=1,
        error_messages={
            "required": "تعداد الزامی است",
            "invalid": "تعداد نامعتبر است",
            "min_value": "حداقل تعداد 1 است"
        }
    )

    payment_method = serializers.ChoiceField(
        choices=[
            ('TOMAN', 'کیف پول'),
            ('SILVER', 'نقره')
        ],
        error_messages={
            "required": "روش پرداخت الزامی است",
            "invalid_choice": "روش پرداخت نامعتبر است"
        }
    )

    delivery_type = serializers.ChoiceField(
        choices=[
            ('HOME', 'ارسال'),
            ('IN_PERSON', 'حضوری')
        ],
        error_messages={
            "required": "نوع ارسال الزامی است",
            "invalid_choice": "نوع ارسال نامعتبر است"
        }
    )

    # =========================
    # ADDRESS
    # =========================
    address_id = serializers.IntegerField(
        required=False,
        allow_null=True,
        error_messages={
            "invalid": "شناسه آدرس نامعتبر است"
        }
    )

    province = serializers.CharField(required=False, allow_blank=True)
    city = serializers.CharField(required=False, allow_blank=True)
    address = serializers.CharField(required=False, allow_blank=True)

    postal_code = serializers.CharField(required=False, allow_blank=True)
    plaque = serializers.CharField(required=False, allow_blank=True)
    unit = serializers.CharField(required=False, allow_blank=True)

    def validate(self, data):

        address_id = data.get("address_id")
        province = data.get("province")
        city = data.get("city")
        address = data.get("address")

        # =========================
        # ADDRESS CONFLICT
        # =========================
        if address_id and any([province, city, address]):
            raise serializers.ValidationError({
                "non_field_errors": ["یا آدرس قبلی یا آدرس جدید، نه هر دو"]
            })

        # =========================
        # NEW ADDRESS REQUIRED
        # =========================
        if not address_id:
            if not (province and city and address):
                raise serializers.ValidationError({
                    "non_field_errors": ["province, city, address الزامی است"]
                })

        return data


