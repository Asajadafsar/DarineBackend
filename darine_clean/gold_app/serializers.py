# gold_app/serializers.py

from rest_framework import serializers
from decimal import Decimal

from accounts.models import BankCard

from .models import (
    GoldInventory,
    GoldTransaction,
    Wallet,
    FinancialTransaction,
    Product,
    Cart,
    Order,
    OrderItem,
    GiftCard,
    GiftCardOrder,
    PriceAlert,
    ReferralEarning,
    GoldPriceHistory,
    PurchaseCredit,
    AutoSavingPlan
)


# =========================================================
# BASE RESPONSE SERIALIZER
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
            'id',
            'card_number',
            'bank_name',
            'is_active',
            'created_at'
        ]


# =========================================================
# WALLET & INVENTORY
# =========================================================

class WalletSerializer(serializers.ModelSerializer):

    available_balance = serializers.SerializerMethodField()

    class Meta:
        model = Wallet
        fields = [
            'balance',
            'blocked_balance',
            'available_balance',
            'updated_at'
        ]

    def get_available_balance(self, obj):

        return int(
            obj.balance - obj.blocked_balance
        )


class GoldInventorySerializer(serializers.ModelSerializer):

    available_balance = serializers.SerializerMethodField()

    class Meta:
        model = GoldInventory
        fields = [
            'balance',
            'blocked_balance',
            'available_balance',
            'updated_at'
        ]

    def get_available_balance(self, obj):

        return round(
            obj.balance - obj.blocked_balance,
            5
        )


# =========================================================
# GOLD TRANSACTION
# =========================================================

class GoldTransactionSerializer(serializers.ModelSerializer):

    type_display = serializers.CharField(
        source='get_type_display',
        read_only=True
    )

    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )

    final_price = serializers.SerializerMethodField()

    class Meta:
        model = GoldTransaction
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

    def get_final_price(self, obj):

        return int(
            obj.total_amount - obj.fee
        )


# =========================================================
# FINANCIAL TRANSACTION
# =========================================================

class FinancialTransactionSerializer(serializers.ModelSerializer):

    type_display = serializers.CharField(
        source='get_type_display',
        read_only=True
    )

    method_display = serializers.CharField(
        source='get_method_display',
        read_only=True
    )

    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )

    user_card_number = serializers.SerializerMethodField()

    class Meta:
        model = FinancialTransaction
        fields = [
            'id',
            'amount',
            'type',
            'type_display',
            'method',
            'method_display',
            'status',
            'status_display',
            'receipt_image',
            'user_card',
            'user_card_number',
            'admin_note',
            'tracking_code',
            'description',
            'created_at',
            'updated_at'
        ]

    def get_user_card_number(self, obj):

        if obj.user_card:
            return obj.user_card.card_number

        return None


# =========================================================
# PRODUCT
# =========================================================

class ProductSerializer(serializers.ModelSerializer):

    category_display = serializers.CharField(
        source='get_category_display',
        read_only=True
    )

    total_price = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            'id',
            'name',
            'category',
            'category_display',
            'weight',
            'total_weight_with_fees',
            'delivery_type',
            'buy_price',
            'sell_price',
            'inventory_count',
            'image',
            'description',
            'total_price',
            'is_active',
            'created_at'
        ]

    def get_total_price(self, obj):

        if obj.buy_price:
            return int(obj.buy_price)

        return 0


# =========================================================
# CART
# =========================================================

class CartSerializer(serializers.ModelSerializer):

    product_details = ProductSerializer(
        source='product',
        read_only=True
    )

    total_gold = serializers.SerializerMethodField()

    total_price = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = [
            'id',
            'product',
            'product_details',
            'quantity',
            'total_gold',
            'total_price',
            'created_at'
        ]

    def get_total_gold(self, obj):

        total = (
            obj.product.total_weight_with_fees
            * obj.quantity
        )

        return round(total, 5)

    def get_total_price(self, obj):

        if obj.product.buy_price:

            return int(
                obj.product.buy_price
                * obj.quantity
            )

        return 0


# =========================================================
# ORDER ITEM
# =========================================================

class OrderItemSerializer(serializers.ModelSerializer):

    product_name = serializers.CharField(
        source='product.name',
        read_only=True
    )

    product_image = serializers.ImageField(
        source='product.image',
        read_only=True
    )

    class Meta:
        model = OrderItem
        fields = [
            'id',
            'product',
            'product_name',
            'product_image',
            'quantity',
            'price_at_time',
            'weight_at_time'
        ]


# =========================================================
# ORDER
# =========================================================

class OrderSerializer(serializers.ModelSerializer):

    items = OrderItemSerializer(
        many=True,
        read_only=True
    )

    payment_method_display = serializers.CharField(
        source='get_payment_method_display',
        read_only=True
    )

    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )

    delivery_type_display = serializers.CharField(
        source='get_delivery_type_display',
        read_only=True
    )

    class Meta:
        model = Order
        fields = [
            'id',
            'address',
            'province',
            'city',
            'postal_code',
            'plaque',
            'unit',
            'payment_method',
            'payment_method_display',
            'delivery_type',
            'delivery_type_display',
            'status',
            'status_display',
            'total_gold_amount',
            'total_toman_amount',
            'tracking_code',
            'description',
            'created_at',
            'updated_at',
            'items'
        ]


# =========================================================
# GIFT CARD
# =========================================================

class GiftCardSerializer(serializers.ModelSerializer):

    class Meta:
        model = GiftCard
        fields = [
            'id',
            'serial_number',
            'weight',
            'is_used',
            'activated_by',
            'created_at'
        ]


# =========================================================
# GIFT CARD ORDER
# =========================================================

class GiftCardOrderSerializer(serializers.ModelSerializer):

    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )

    class Meta:
        model = GiftCardOrder
        fields = [
            'id',
            'weight_per_card',
            'quantity',
            'total_price',
            'province',
            'city',
            'address',
            'postal_code',
            'plaque',
            'unit',
            'status',
            'status_display',
            'tracking_code',
            'created_at',
            'updated_at'
        ]

        read_only_fields = [
            'user',
            'total_price',
            'status',
            'tracking_code'
        ]


# =========================================================
# PRICE ALERT
# =========================================================

class PriceAlertSerializer(serializers.ModelSerializer):

    alert_type_display = serializers.CharField(
        source='get_alert_type_display',
        read_only=True
    )

    class Meta:
        model = PriceAlert
        fields = [
            'id',
            'target_price',
            'alert_type',
            'alert_type_display',
            'is_active',
            'created_at'
        ]


# =========================================================
# REFERRAL EARNING
# =========================================================

class ReferralEarningSerializer(serializers.ModelSerializer):

    referred_user_mobile = serializers.CharField(
        source='referred_user.mobile',
        read_only=True
    )

    class Meta:
        model = ReferralEarning
        fields = [
            'id',
            'referred_user_mobile',
            'amount',
            'transaction_date'
        ]


# =========================================================
# GOLD PRICE HISTORY
# =========================================================

class GoldPriceHistorySerializer(serializers.ModelSerializer):

    class Meta:
        model = GoldPriceHistory
        fields = [
            'id',
            'price',
            'created_at'
        ]


# =========================================================
# PURCHASE CREDIT
# =========================================================

class PurchaseCreditSerializer(serializers.ModelSerializer):

    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )

    class Meta:
        model = PurchaseCredit
        fields = [
            'id',
            'amount',
            'used_amount',
            'remaining_amount',
            'status',
            'status_display',
            'expire_at',
            'created_at'
        ]

# =========================================================
# AUTO SAVING PLAN
# =========================================================

class AutoSavingPlanSerializer(serializers.ModelSerializer):

    type_display = serializers.CharField(
        source='get_type_display',
        read_only=True
    )

    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )

    class Meta:

        model = AutoSavingPlan

        fields = [
            'id',
            'type',
            'type_display',
            'amount',
            'period_days',
            'next_execute_at',
            'status',
            'status_display',
            'created_at'
        ]

        read_only_fields = [
            'period_days',
            'next_execute_at',
            'status',
            'created_at'
        ]

# =========================================================
# FILTER SERIALIZERS
# =========================================================

class ReportFilterSerializer(serializers.Serializer):

    status = serializers.CharField(
        required=False
    )

    start_date = serializers.DateField(
        required=False
    )

    end_date = serializers.DateField(
        required=False
    )


class TradeFilterSerializer(ReportFilterSerializer):

    type = serializers.ChoiceField(
        choices=[
            'BUY',
            'SELL'
        ],
        required=False
    )


class FinancialFilterSerializer(
    ReportFilterSerializer
):

    method = serializers.CharField(
        required=False
    )

    type = serializers.CharField(
        required=False
    )


class GiftCardFilterSerializer(
    ReportFilterSerializer
):

    mode = serializers.CharField(
        required=False
    )


class PhysicalOrderFilterSerializer(
    ReportFilterSerializer
):

    delivery_type = serializers.CharField(
        required=False
    )


class AutoSavingFilterSerializer(
    ReportFilterSerializer
):

    type = serializers.CharField(
        required=False
    )


# =========================================================
# DASHBOARD SERIALIZERS
# =========================================================

class UserBalanceSerializer(
    serializers.Serializer
):

    gold_balance_gr = serializers.DecimalField(
        max_digits=20,
        decimal_places=5
    )

    toman_balance = serializers.DecimalField(
        max_digits=20,
        decimal_places=0
    )

    current_gold_price = serializers.DecimalField(
        max_digits=20,
        decimal_places=0
    )

    total_assets = serializers.DecimalField(
        max_digits=20,
        decimal_places=0
    )


class GoldChartSerializer(
    serializers.Serializer
):

    labels = serializers.ListField(
        child=serializers.CharField()
    )

    prices = serializers.ListField(
        child=serializers.DecimalField(
            max_digits=20,
            decimal_places=0
        )
    )

    highest_price = serializers.DecimalField(
        max_digits=20,
        decimal_places=0
    )

    lowest_price = serializers.DecimalField(
        max_digits=20,
        decimal_places=0
    )

    change_percent = serializers.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    filter_type = serializers.CharField()


# =========================================================
# RECENT TRANSACTION SERIALIZER
# =========================================================

class RecentTransactionSerializer(
    serializers.Serializer
):

    id = serializers.IntegerField()

    title = serializers.CharField()

    amount = serializers.DecimalField(
        max_digits=20,
        decimal_places=0
    )

    status = serializers.CharField()

    created_at = serializers.DateTimeField()

    type = serializers.CharField()


# =========================================================
# RECENT DELIVERY SERIALIZER
# =========================================================

class RecentDeliverySerializer(
    serializers.Serializer
):

    id = serializers.IntegerField()

    delivery_type = serializers.CharField()

    status = serializers.CharField()

    total_amount = serializers.DecimalField(
        max_digits=20,
        decimal_places=0
    )

    created_at = serializers.DateTimeField()


# =========================================================
# DEPOSIT SERIALIZER
# =========================================================

class DepositSerializer(serializers.Serializer):

    METHOD_CHOICES = (
        ('RECEIPT', 'رسید بانکی'),
        ('GATEWAY', 'درگاه پرداخت'),
    )

    amount = serializers.DecimalField(
        max_digits=20,
        decimal_places=0
    )

    method = serializers.ChoiceField(
        choices=METHOD_CHOICES
    )

    receipt = serializers.ImageField(
        required=False
    )

    def validate(self, attrs):

        method = attrs.get('method')
        receipt = attrs.get('receipt')

        if method == 'RECEIPT' and not receipt:

            raise serializers.ValidationError({
                "receipt": "تصویر رسید الزامی است"
            })

        return attrs


# =========================================================
# BUY GOLD
# =========================================================

class BuyGoldSerializer(serializers.Serializer):

    payment_method = serializers.ChoiceField(
        choices=[
            ('WALLET', 'کیف پول'),
            ('GATEWAY', 'درگاه پرداخت')
        ]
    )

    toman = serializers.DecimalField(
        max_digits=20,
        decimal_places=0,
        required=False
    )

    weight = serializers.DecimalField(
        max_digits=20,
        decimal_places=5,
        required=False
    )

    def validate(self, attrs):

        toman = attrs.get('toman')
        weight = attrs.get('weight')

        if not toman and not weight:

            raise serializers.ValidationError({
                "message": "مبلغ یا وزن الزامی است"
            })

        return attrs

# =========================================================
# SELL GOLD
# =========================================================

class SellGoldSerializer(serializers.Serializer):

    toman = serializers.DecimalField(
        max_digits=20,
        decimal_places=0,
        required=False
    )

    weight = serializers.DecimalField(
        max_digits=20,
        decimal_places=5,
        required=False
    )

    def validate(self, attrs):

        toman = attrs.get('toman')

        weight = attrs.get('weight')

        if not toman and not weight:

            raise serializers.ValidationError({
                "message": "مبلغ یا وزن الزامی است"
            })

        return attrs





# =========================================================
# WITHDRAW
# =========================================================

class WithdrawSerializer(serializers.Serializer):

    TARGET_CHOICES = (
        ('BANK', 'برداشت بانکی'),
        ('SILVER', 'تبدیل به نقره'),
    )

    amount = serializers.DecimalField(
        max_digits=20,
        decimal_places=0
    )

    target = serializers.ChoiceField(
        choices=TARGET_CHOICES
    )

    card_id = serializers.IntegerField(
        required=False
    )

    def validate(self, attrs):

        request = self.context.get('request')

        target = attrs.get('target')

        card_id = attrs.get('card_id')

        if target == 'BANK':

            if not card_id:

                raise serializers.ValidationError({
                    "card_id": "کارت بانکی الزامی است"
                })

            try:

                card = BankCard.objects.get(
                    id=card_id,
                    user=request.user,
                    is_active=True
                )

            except BankCard.DoesNotExist:

                raise serializers.ValidationError({
                    "card_id": "کارت بانکی معتبر نیست"
                })

            attrs['card'] = card

        return attrs


# =========================================================
# CHECKOUT
# =========================================================

class CheckoutSerializer(serializers.Serializer):

    payment_method = serializers.ChoiceField(
        choices=[
            ('GOLD', 'طلا'),
            ('TOMAN', 'موجودی')
        ]
    )

    delivery_type = serializers.ChoiceField(
        choices=[
            ('HOME', 'ارسال به منزل'),
            ('IN_PERSON', 'تحویل حضوری')
        ]
    )

    province = serializers.CharField()

    city = serializers.CharField()

    address = serializers.CharField()

    postal_code = serializers.CharField(
        required=False,
        allow_blank=True
    )

    plaque = serializers.CharField(
        required=False,
        allow_blank=True
    )

    unit = serializers.CharField(
        required=False,
        allow_blank=True
    )


# =========================================================
# GIFT CARD REDEEM
# =========================================================

class RedeemGiftCardSerializer(
    serializers.Serializer
):

    serial_number = serializers.CharField()


# =========================================================
# CHART FILTER
# =========================================================

class GoldChartFilterSerializer(
    serializers.Serializer
):

    filter = serializers.ChoiceField(
        choices=[
            '24H',
            'WEEKLY',
            'MONTHLY'
        ]
    )