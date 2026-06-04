# gold_app/serializers.py

from rest_framework import serializers
from decimal import Decimal

from accounts.models import BankCard, ReferralEarning

from .models import (
    GoldInventory,
    GoldOrder,
    GoldTransaction,
    ProductCategory,
    UserAddress,
    Wallet,
    FinancialTransaction,
    Product,
    Order,
    OrderItem,
    GiftCard,
    GiftCardOrder,
    PriceAlert,
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

    category_name = serializers.CharField(
        source="category.name",
        read_only=True
    )

    total_price = serializers.SerializerMethodField()

    class Meta:
        model = Product
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
            "image",
            "description",
            "is_active",
            "created_at"
        ]

    def get_total_price(self, obj):

        if obj.buy_price and obj.total_weight_with_fees:
            return int(obj.buy_price * obj.total_weight_with_fees)

        if obj.buy_price:
            return int(obj.buy_price)

        return 0





# =========================================================
# ORDER ITEM
# =========================================================

class OrderItemSerializer(serializers.ModelSerializer):

    product_name = serializers.CharField(source="product.name", read_only=True)
    product_image = serializers.ImageField(source="product.image", read_only=True)

    class Meta:
        model = OrderItem
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
# ORDER
# =========================================================

class OrderSerializer(serializers.ModelSerializer):

    items = OrderItemSerializer(many=True, read_only=True)

    payment_method_display = serializers.CharField(
        source="get_payment_method_display",
        read_only=True
    )

    status_display = serializers.CharField(
        source="get_status_display",
        read_only=True
    )

    delivery_type_display = serializers.CharField(
        source="get_delivery_type_display",
        read_only=True
    )

    class Meta:
        model = Order
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
            "total_gold_amount",
            "total_toman_amount",
            "tracking_code",
            "created_at",
            "items"
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
# PRICE ALERT SERIALIZER
# =========================================================

class PriceAlertSerializer(serializers.ModelSerializer):

    target_price = serializers.DecimalField(
        max_digits=20,
        decimal_places=5
    )

    alert_type = serializers.ChoiceField(
        choices=[
            ('ABOVE', 'بالاتر'),
            ('BELOW', 'پایین‌تر'),
        ]
    )

    class Meta:
        model = PriceAlert
        fields = [
            'id',
            'target_price',
            'alert_type',
            'is_active',
            'created_at'
        ]

        read_only_fields = [
            'id',
            'created_at'
        ]



# =========================================================
# GIFT CARD ORDER SERIALIZER
# =========================================================

class GiftCardOrderSerializer(serializers.ModelSerializer):

    address_id = serializers.IntegerField(
        required=False
    )

    province = serializers.CharField(
        required=False
    )

    city = serializers.CharField(
        required=False
    )

    address = serializers.CharField(
        required=False
    )

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

    class Meta:

        model = GiftCardOrder

        fields = [

            'address_id',

            'weight_per_card',

            'quantity',

            'province',

            'city',

            'address',

            'postal_code',

            'plaque',

            'unit'
        ]

    def validate(self, attrs):

        address_id = attrs.get(
            'address_id'
        )

        # =====================================
        # IF NO ADDRESS ID
        # REQUIRE ADDRESS FIELDS
        # =====================================

        if not address_id:

            required_fields = [
                'province',
                'city',
                'address'
            ]

            for field in required_fields:

                if not attrs.get(field):

                    raise serializers.ValidationError({
                        field: 'این فیلد اجباری است'
                    })

        return attrs


# =========================================================
# REFERRAL EARNING
# =========================================================

class ReferralEarningSerializer(serializers.ModelSerializer):

    user_mobile = serializers.CharField(
        source="user.mobile",
        read_only=True
    )

    class Meta:
        model = ReferralEarning
        fields = [
            "id",
            "user_mobile",
            "amount",
            "source_type",
            "created_at"
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

from rest_framework import serializers
from decimal import Decimal

class BuyGoldSerializer(serializers.Serializer):

    payment_method = serializers.ChoiceField(
        choices=[
            ('WALLET', 'کیف پول'),
            ('GATEWAY', 'درگاه پرداخت')
        ]
    )

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

    # =========================
    # CALCULATED FIELDS
    # =========================
    fee = None
    fee_rate = None
    total_toman = None
    final_weight = None

    def validate(self, attrs):

        toman = attrs.get('toman')
        weight = attrs.get('weight')

        if not toman and not weight:
            raise serializers.ValidationError({
                "message": "مبلغ یا وزن الزامی است"
            })

        request = self.context.get("request")
        user = request.user

        # =========================
        # FEE FROM USER SETTINGS
        # =========================
        user_fee = getattr(user, "fee", None)
        fee_rate = user_fee.gold_buy_fee if user_fee else Decimal("0.0099")

        attrs["fee_rate"] = fee_rate

        gold_price = self.context.get("gold_price")

        # =========================
        # CALCULATION
        # =========================
        if toman:

            total_toman = Decimal(str(toman))
            fee = total_toman * fee_rate
            net = total_toman - fee

            weight = net / gold_price

        else:

            weight = Decimal(str(weight))
            pure = weight * gold_price

            fee = pure * fee_rate
            total_toman = pure + fee

        attrs["fee"] = fee
        attrs["total_toman"] = total_toman
        attrs["final_weight"] = weight

        return attrs
    


# =========================================================
# SELL GOLD
# =========================================================

class SellGoldSerializer(serializers.Serializer):

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

        if not attrs.get('toman') and not attrs.get('weight'):
            raise serializers.ValidationError({
                "message": "مبلغ یا وزن الزامی است"
            })

        request = self.context.get("request")
        user = request.user

        user_fee = getattr(user, "fee", None)
        fee_rate = user_fee.gold_sell_fee if user_fee else Decimal("0.0099")

        attrs["fee_rate"] = fee_rate

        gold_price = self.context.get("gold_price")

        if attrs.get("toman"):

            toman = Decimal(str(attrs["toman"]))

            final_weight = toman / gold_price
            fee = toman * fee_rate
            final_amount = toman - fee

        else:

            final_weight = Decimal(str(attrs["weight"]))

            pure = final_weight * gold_price
            fee = pure * fee_rate
            final_amount = pure - fee

        attrs["fee"] = fee
        attrs["final_amount"] = final_amount
        attrs["final_weight"] = final_weight

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
class PhysicalOrderSerializer(serializers.Serializer):

    products = serializers.ListField(
        child=serializers.DictField(),
        allow_empty=False
    )

    payment_method = serializers.ChoiceField(
        choices=[
            ('TOMAN', 'کیف پول'),
            ('GOLD', 'طلا')
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






class GoldOrderSerializer(serializers.Serializer):

    order_type = serializers.ChoiceField(
        choices=["BUY", "SELL"]
    )

    target_price = serializers.DecimalField(
        max_digits=20,
        decimal_places=0
    )

    amount_toman = serializers.DecimalField(
        max_digits=20,
        decimal_places=0,
        required=False
    )

    gold_weight = serializers.DecimalField(
        max_digits=20,
        decimal_places=5,
        required=False
    )

    def validate(self, data):

        order_type = data["order_type"]

        if order_type == "BUY":

            if not data.get("amount_toman"):
                raise serializers.ValidationError(
                    "مبلغ تومان الزامی است"
                )

        elif order_type == "SELL":

            if not data.get("gold_weight"):
                raise serializers.ValidationError(
                    "وزن طلا الزامی است"
                )

        return data


class GoldOrderListSerializer(serializers.ModelSerializer):

    class Meta:
        model = GoldOrder

        fields = (
            "id",
            "order_type",
            "target_price",
            "amount_toman",
            "gold_weight",
            "estimated_weight",
            "status",
            "created_at",
        )



class PriceQuerySerializer(serializers.Serializer):
    key = serializers.CharField()

    

class ProductCategorySerializer(serializers.ModelSerializer):

    class Meta:
        model = ProductCategory
        fields = [
            "id",
            "name",
            "slug",
        ]