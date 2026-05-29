from rest_framework import serializers
from decimal import Decimal

from .models import (
    SilverInventory,
    SilverTransaction,
    SilverWallet,
    SilverFinancialTransaction,
    SilverProduct,
    SilverCart,
    SilverOrder,
    SilverOrderItem,
    SilverPriceAlert,
    SilverReferralEarning,
    SilverPriceHistory,
)

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
            "updated_at",
        ]

    def get_available_balance(self, obj):
        return obj.balance - obj.blocked_balance


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
            "updated_at",
        ]

    def get_available_balance(self, obj):
        return obj.balance - obj.blocked_balance


# =========================================================
# TRANSACTION
# =========================================================

class SilverTransactionSerializer(serializers.ModelSerializer):

    type_display = serializers.CharField(source="get_type_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = SilverTransaction
        fields = "__all__"


# =========================================================
# FINANCIAL TRANSACTION
# =========================================================

class SilverFinancialTransactionSerializer(serializers.ModelSerializer):

    class Meta:
        model = SilverFinancialTransaction
        fields = "__all__"


# =========================================================
# PRODUCT
# =========================================================

class SilverProductSerializer(serializers.ModelSerializer):

    class Meta:
        model = SilverProduct
        fields = "__all__"


# =========================================================
# CART
# =========================================================

class SilverCartSerializer(serializers.ModelSerializer):

    product_details = SilverProductSerializer(source="product", read_only=True)

    class Meta:
        model = SilverCart
        fields = "__all__"


# =========================================================
# ORDER ITEM
# =========================================================

class SilverOrderItemSerializer(serializers.ModelSerializer):

    class Meta:
        model = SilverOrderItem
        fields = "__all__"


# =========================================================
# ORDER
# =========================================================

class SilverOrderSerializer(serializers.ModelSerializer):

    items = SilverOrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = SilverOrder
        fields = "__all__"


# =========================================================
# PRICE ALERT
# =========================================================

class SilverPriceAlertSerializer(serializers.ModelSerializer):

    alert_type_display = serializers.CharField(
        source="get_alert_type_display",
        read_only=True
    )

    class Meta:
        model = SilverPriceAlert
        fields = [
            "id",
            "target_price",
            "alert_type",
            "alert_type_display",
            "is_active",
            "created_at",
        ]


# =========================================================
# REFERRAL
# =========================================================

class SilverReferralEarningSerializer(serializers.ModelSerializer):

    class Meta:
        model = SilverReferralEarning
        fields = "__all__"


# =========================================================
# PRICE HISTORY
# =========================================================

class SilverPriceHistorySerializer(serializers.ModelSerializer):

    class Meta:
        model = SilverPriceHistory
        fields = "__all__"


# =========================================================
# BUY SILVER
# =========================================================
class BuySilverSerializer(serializers.Serializer):
    toman = serializers.DecimalField(max_digits=20, decimal_places=2, required=False)
    weight = serializers.DecimalField(max_digits=20, decimal_places=6, required=False)
    payment_method = serializers.ChoiceField(
        choices=["WALLET", "GATEWAY"],
        required=True
    )

    def validate(self, attrs):
        if not attrs.get("toman") and not attrs.get("weight"):
            raise serializers.ValidationError("مبلغ یا وزن الزامی است")
        return attrs


# =========================================================
# SELL SILVER
# =========================================================
class SellSilverSerializer(serializers.Serializer):
    toman = serializers.DecimalField(max_digits=20, decimal_places=2, required=False)
    weight = serializers.DecimalField(max_digits=20, decimal_places=6, required=False)

    def validate(self, attrs):
        if not attrs.get("toman") and not attrs.get("weight"):
            raise serializers.ValidationError("مبلغ یا وزن الزامی است")
        return attrs
# =========================================================
# DEPOSIT / WITHDRAW
# =========================================================

class DepositSilverSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=20, decimal_places=0)


class WithdrawSilverSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=20, decimal_places=0)


# =========================================================
# CHECKOUT
# =========================================================

class CheckoutSilverSerializer(serializers.Serializer):
    confirm = serializers.BooleanField()


# =========================================================
# CHART
# =========================================================

class SilverChartSerializer(serializers.Serializer):
    price = serializers.DecimalField(max_digits=20, decimal_places=0)
    created_at = serializers.DateTimeField()