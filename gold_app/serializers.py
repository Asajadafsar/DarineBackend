# gold_app/serializers.py

from rest_framework import serializers
from decimal import Decimal

from .utils import get_live_gold_price
from accounts.models import BankCard, ReferralEarning

from .models import (
    GoldInventory,
    GoldOrder,
    GoldTransaction,
    OrderStatusHistory,
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
    AutoSavingPlan,
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
        fields = ["id", "card_number", "bank_name", "is_active", "created_at"]


# =========================================================
# WALLET & INVENTORY
# =========================================================


class WalletSerializer(serializers.ModelSerializer):

    available_balance = serializers.SerializerMethodField()

    class Meta:
        model = Wallet
        fields = ["balance", "blocked_balance", "available_balance", "updated_at"]

    def get_available_balance(self, obj):

        return int(obj.balance - obj.blocked_balance)


class GoldInventorySerializer(serializers.ModelSerializer):

    available_balance = serializers.SerializerMethodField()

    class Meta:
        model = GoldInventory
        fields = ["balance", "blocked_balance", "available_balance", "updated_at"]

    def get_available_balance(self, obj):

        return round(obj.balance - obj.blocked_balance, 5)


# =========================================================
# GOLD TRANSACTION
# =========================================================


class GoldTransactionSerializer(serializers.ModelSerializer):

    type_display = serializers.CharField(source="get_type_display", read_only=True)

    status_display = serializers.CharField(source="get_status_display", read_only=True)

    final_price = serializers.SerializerMethodField()

    class Meta:
        model = GoldTransaction
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
            "description",
            "created_at",
            "updated_at",
        ]

    def get_final_price(self, obj):

        return int(obj.total_amount - obj.fee)


# =========================================================
# FINANCIAL TRANSACTION
# =========================================================


class FinancialTransactionSerializer(serializers.ModelSerializer):

    type_display = serializers.CharField(source="get_type_display", read_only=True)
    method_display = serializers.CharField(source="get_method_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    user_card_number = serializers.SerializerMethodField()
    receipt_image_url = serializers.SerializerMethodField()

    class Meta:
        model = FinancialTransaction
        fields = [
            "id",
            "amount",
            "type",
            "type_display",
            "method",
            "method_display",
            "status",
            "status_display",
            "receipt_image",  # optional (raw)
            "receipt_image_url",  # 👈 NEW FIX
            "user_card",
            "user_card_number",
            "admin_note",
            "tracking_code",
            "description",
            "created_at",
            "updated_at",
        ]

    def get_user_card_number(self, obj):
        if obj.user_card:
            return obj.user_card.card_number
        return None

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


class ProductSerializer(serializers.ModelSerializer):

    category_name = serializers.CharField(source="category.name", read_only=True)

    image_url = serializers.SerializerMethodField()

    # مقدار وزنی هر محصول با اجرت
    product_weight_with_fee = serializers.SerializerMethodField()

    # قیمت نهایی نمایش به کاربر
    total_price = serializers.SerializerMethodField()

    class Meta:
        model = Product
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
            "image",
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

        return obj.image.url

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
            live_price = get_live_gold_price()
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


class OrderStatusHistorySerializer(serializers.ModelSerializer):

    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = OrderStatusHistory
        fields = [
            "status",
            "status_display",
            "description",
            "created_at",
        ]


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
            "weight_at_time",
        ]


# =========================================================
# ORDER
# =========================================================

# =========================================================
# ORDER
# =========================================================


class OrderSerializer(serializers.ModelSerializer):

    items = OrderItemSerializer(many=True, read_only=True)

    payment_method_display = serializers.CharField(
        source="get_payment_method_display", read_only=True
    )

    status_display = serializers.CharField(source="get_status_display", read_only=True)

    delivery_type_display = serializers.CharField(
        source="get_delivery_type_display", read_only=True
    )

    status_history = OrderStatusHistorySerializer(many=True, read_only=True)

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
            "admin_note",
            "items",
            "status_history",
        ]


# =========================================================
# GIFT CARD
# =========================================================


class GiftCardSerializer(serializers.ModelSerializer):

    class Meta:
        model = GiftCard
        fields = [
            "id",
            "serial_number",
            "weight",
            "is_used",
            "activated_by",
            "created_at",
        ]


# =========================================================
# PRICE ALERT SERIALIZER
# =========================================================

from rest_framework import serializers

from .models import (
    PriceAlertLog,
)


class PriceAlertSerializer(serializers.ModelSerializer):

    target_price = serializers.DecimalField(max_digits=20, decimal_places=3)

    alert_type = serializers.ChoiceField(choices=PriceAlert.ALERT_CHOICES)

    max_notifications = serializers.IntegerField(
        min_value=1,
        max_value=1000,
        error_messages={
            "required": "تعداد دفعات ارسال الزامی است.",
            "min_value": "حداقل تعداد ۱ است.",
            "max_value": "حداکثر تعداد ۱۰۰۰ است.",
        },
    )

    remaining_notifications = serializers.SerializerMethodField()

    class Meta:
        model = PriceAlert
        fields = [
            "id",
            "target_price",
            "alert_type",
            "max_notifications",
            "sent_notifications",
            "remaining_notifications",
            "status",
            "is_active",
            "triggered",
            "last_triggered_price",
            "last_triggered_at",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "sent_notifications",
            "remaining_notifications",
            "status",
            "triggered",
            "is_active",
            "last_triggered_price",
            "last_triggered_at",
            "created_at",
            "updated_at",
        ]

    def get_remaining_notifications(self, obj):
        return max(obj.max_notifications - obj.sent_notifications, 0)

    def validate_target_price(self, value):

        if value <= 0:
            raise serializers.ValidationError("قیمت هدف باید بزرگتر از صفر باشد.")

        return value

    def validate_max_notifications(self, value):

        if value < 1:
            raise serializers.ValidationError("تعداد دفعات باید حداقل ۱ باشد.")

        return value


# =========================================================
# PRICE ALERT LOG SERIALIZER
# =========================================================


class PriceAlertLogSerializer(serializers.ModelSerializer):

    class Meta:
        model = PriceAlertLog
        fields = [
            "id",
            "price",
            "sms_cost",
            "sms_status",
            "sms_response",
            "created_at",
        ]


# =========================================================
# GIFT CARD ORDER SERIALIZER
# =========================================================


class GiftCardOrderSerializer(serializers.ModelSerializer):

    address_id = serializers.IntegerField(required=False)

    province = serializers.CharField(required=False)

    city = serializers.CharField(required=False)

    address = serializers.CharField(required=False)

    postal_code = serializers.CharField(required=False, allow_blank=True)

    plaque = serializers.CharField(required=False, allow_blank=True)

    unit = serializers.CharField(required=False, allow_blank=True)

    class Meta:

        model = GiftCardOrder

        fields = [
            "address_id",
            "weight_per_card",
            "quantity",
            "province",
            "city",
            "address",
            "postal_code",
            "plaque",
            "unit",
        ]

    def validate(self, attrs):

        address_id = attrs.get("address_id")

        # =====================================
        # IF NO ADDRESS ID
        # REQUIRE ADDRESS FIELDS
        # =====================================

        if not address_id:

            required_fields = ["province", "city", "address"]

            for field in required_fields:

                if not attrs.get(field):

                    raise serializers.ValidationError({field: "این فیلد اجباری است"})

        return attrs


# =========================================================
# REFERRAL EARNING
# =========================================================


class ReferralEarningSerializer(serializers.ModelSerializer):

    user_mobile = serializers.CharField(source="user.mobile", read_only=True)

    class Meta:
        model = ReferralEarning
        fields = ["id", "user_mobile", "amount", "source_type", "created_at"]


# =========================================================
# GOLD PRICE HISTORY
# =========================================================


class GoldPriceHistorySerializer(serializers.ModelSerializer):

    class Meta:
        model = GoldPriceHistory
        fields = ["id", "price", "created_at"]


# =========================================================
# PURCHASE CREDIT
# =========================================================


class PurchaseCreditSerializer(serializers.ModelSerializer):

    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = PurchaseCredit
        fields = [
            "id",
            "amount",
            "used_amount",
            "remaining_amount",
            "status",
            "status_display",
            "expire_at",
            "created_at",
        ]


# =========================================================
# AUTO SAVING PLAN
# =========================================================


class AutoSavingPlanSerializer(serializers.ModelSerializer):

    type_display = serializers.CharField(source="get_type_display", read_only=True)

    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:

        model = AutoSavingPlan

        fields = [
            "id",
            "type",
            "type_display",
            "amount",
            "period_days",
            "next_execute_at",
            "status",
            "status_display",
            "created_at",
        ]

        read_only_fields = ["period_days", "next_execute_at", "status", "created_at"]


# =========================================================
# FILTER SERIALIZERS
# =========================================================


class ReportFilterSerializer(serializers.Serializer):

    status = serializers.CharField(required=False)

    start_date = serializers.DateField(required=False)

    end_date = serializers.DateField(required=False)


class TradeFilterSerializer(ReportFilterSerializer):

    type = serializers.ChoiceField(choices=["BUY", "SELL"], required=False)


class FinancialFilterSerializer(ReportFilterSerializer):

    method = serializers.CharField(required=False)

    type = serializers.CharField(required=False)


class GiftCardFilterSerializer(ReportFilterSerializer):

    mode = serializers.CharField(required=False)


class PhysicalOrderFilterSerializer(ReportFilterSerializer):

    delivery_type = serializers.CharField(required=False)


class AutoSavingFilterSerializer(ReportFilterSerializer):

    type = serializers.CharField(required=False)


# =========================================================
# DASHBOARD SERIALIZERS
# =========================================================


class UserBalanceSerializer(serializers.Serializer):

    gold_balance_gr = serializers.DecimalField(max_digits=20, decimal_places=5)

    toman_balance = serializers.DecimalField(max_digits=20, decimal_places=0)

    current_gold_price = serializers.DecimalField(max_digits=20, decimal_places=0)

    total_assets = serializers.DecimalField(max_digits=20, decimal_places=0)


# =========================================================
# RECENT TRANSACTION SERIALIZER
# =========================================================


class RecentTransactionSerializer(serializers.Serializer):

    id = serializers.IntegerField()

    title = serializers.CharField()

    amount = serializers.DecimalField(max_digits=20, decimal_places=0)

    status = serializers.CharField()

    created_at = serializers.DateTimeField()

    type = serializers.CharField()


# =========================================================
# RECENT DELIVERY SERIALIZER
# =========================================================


class RecentDeliverySerializer(serializers.Serializer):

    id = serializers.IntegerField()

    delivery_type = serializers.CharField()

    status = serializers.CharField()

    total_amount = serializers.DecimalField(max_digits=20, decimal_places=0)

    created_at = serializers.DateTimeField()


# =========================================================
# DEPOSIT SERIALIZER
# =========================================================


class DepositSerializer(serializers.Serializer):

    METHOD_CHOICES = (
        ("RECEIPT", "رسید بانکی"),
        ("GATEWAY", "درگاه پرداخت"),
    )

    amount = serializers.DecimalField(max_digits=20, decimal_places=0)

    method = serializers.ChoiceField(choices=METHOD_CHOICES)

    receipt = serializers.ImageField(required=False)

    description = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):

        method = attrs.get("method")
        receipt = attrs.get("receipt")

        if method == "RECEIPT" and not receipt:

            raise serializers.ValidationError({"receipt": "تصویر رسید الزامی است"})

        return attrs


from rest_framework import serializers

# =========================================================
# BUY GOLD SERIALIZER FIX
# =========================================================

from rest_framework import serializers
from rest_framework import serializers


class BuyGoldSerializer(serializers.Serializer):

    payment_method = serializers.ChoiceField(
        choices=[("WALLET", "کیف پول"), ("GATEWAY", "درگاه")]
    )

    toman = serializers.DecimalField(
        max_digits=25, decimal_places=2, required=False, allow_null=True
    )

    weight = serializers.DecimalField(
        max_digits=20, decimal_places=3, required=False, allow_null=True
    )

    def validate(self, attrs):

        toman = attrs.get("toman")
        weight = attrs.get("weight")

        if toman is None and weight is None:
            raise serializers.ValidationError("مبلغ یا وزن الزامی است")

        gold_price = Decimal(str(self.context["gold_price"]))

        user = self.context["request"].user

        user_fee = getattr(user, "fee", None)

        fee_rate = user_fee.gold_buy_fee if user_fee else Decimal("0.0099")

        if toman is not None:

            toman = Decimal(str(toman))

            if toman <= 0:
                raise serializers.ValidationError("مبلغ نامعتبر است")

            fee = toman * fee_rate

            pure = toman - fee

            final_weight = pure / gold_price

            total_toman = toman

        else:

            weight = Decimal(str(weight))

            if weight <= 0:
                raise serializers.ValidationError("وزن نامعتبر است")

            pure = weight * gold_price

            fee = pure * fee_rate

            total_toman = pure + fee

            final_weight = weight

        attrs["fee"] = fee
        attrs["fee_rate"] = fee_rate
        attrs["total_toman"] = total_toman

        # مهم
        attrs["final_weight"] = final_weight.quantize(Decimal("0.001"))

        return attrs


# =========================================================
# SELL GOLD
# =========================================================


class SellGoldSerializer(serializers.Serializer):

    toman = serializers.DecimalField(
        max_digits=20, decimal_places=2, required=False, allow_null=True
    )

    weight = serializers.DecimalField(
        max_digits=20, decimal_places=4, required=False, allow_null=True
    )

    fee = None
    fee_rate = None
    final_amount = None
    final_weight = None

    def validate(self, attrs):

        toman = attrs.get("toman")
        weight = attrs.get("weight")

        if toman is None and weight is None:
            raise serializers.ValidationError("مبلغ یا وزن الزامی است")

        if toman is not None and Decimal(toman) <= 0:
            raise serializers.ValidationError("مبلغ نامعتبر است")

        if weight is not None and Decimal(weight) <= 0:
            raise serializers.ValidationError("وزن طلا نامعتبر است")

        request = self.context.get("request")
        user = request.user

        user_fee = getattr(user, "fee", None)

        fee_rate = user_fee.gold_sell_fee if user_fee else Decimal("0.0099")

        gold_price = Decimal(str(self.context.get("gold_price")))

        attrs["fee_rate"] = fee_rate

        if toman is not None:

            toman = Decimal(toman)

            final_weight = toman / gold_price

            fee = toman * fee_rate

            final_amount = toman - fee

        else:

            final_weight = Decimal(weight)

            pure = final_weight * gold_price

            fee = pure * fee_rate

            final_amount = pure - fee

        attrs["fee"] = fee
        attrs["final_weight"] = final_weight
        attrs["final_amount"] = final_amount

        return attrs


# =========================================================
# WITHDRAW
# =========================================================


class WithdrawSerializer(serializers.Serializer):

    TARGET_CHOICES = (
        ("BANK", "برداشت بانکی"),
        ("SILVER", "تبدیل به نقره"),
    )

    amount = serializers.DecimalField(max_digits=20, decimal_places=0)

    target = serializers.ChoiceField(choices=TARGET_CHOICES)

    card_id = serializers.IntegerField(required=False)

    def validate(self, attrs):

        request = self.context.get("request")

        target = attrs.get("target")

        card_id = attrs.get("card_id")

        if target == "BANK":

            if not card_id:

                raise serializers.ValidationError({"card_id": "کارت بانکی الزامی است"})

            try:

                card = BankCard.objects.get(
                    id=card_id, user=request.user, is_active=True
                )

            except BankCard.DoesNotExist:

                raise serializers.ValidationError({"card_id": "کارت بانکی معتبر نیست"})

            attrs["card"] = card

        return attrs


# =========================================================
# CHECKOUT
# =========================================================
# =========================================================
# CHECKOUT (NO ADDRESS)
# =========================================================

class PhysicalOrderSerializer(serializers.Serializer):

    products = serializers.ListField(
        child=serializers.DictField(),
        allow_empty=False
    )

    payment_method = serializers.ChoiceField(
        choices=[
            ("TOMAN", "کیف پول"),
            ("GOLD", "طلا"),
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




from rest_framework import serializers


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

        extra_kwargs = {
            "province": {
                "required": True,
                "error_messages": {"required": "استان اجباری است"},
            },
            "city": {
                "required": True,
                "error_messages": {"required": "شهر اجباری است"},
            },
            "address": {
                "required": True,
                "error_messages": {"required": "آدرس اجباری است"},
            },
            "postal_code": {
                "required": True,
                "error_messages": {"required": "کد پستی اجباری است"},
            },
            "plaque": {
                "required": True,
                "error_messages": {"required": "پلاک اجباری است"},
            },
            "unit": {
                "required": True,
                "error_messages": {"required": "واحد اجباری است"},
            },
        }

    # =========================
    # VALIDATION
    # =========================

    def validate_postal_code(self, value):

        if not str(value).isdigit():
            raise serializers.ValidationError("کد پستی فقط باید عدد باشد")

        if len(str(value)) != 10:
            raise serializers.ValidationError("کد پستی باید دقیقاً ۱۰ رقم باشد")

        return value


# =========================================================
# GIFT CARD REDEEM
# =========================================================


class RedeemGiftCardSerializer(serializers.Serializer):

    serial_number = serializers.CharField()


# =========================================================
# CHART FILTER
# =========================================================


class GoldChartFilterSerializer(serializers.Serializer):

    filter = serializers.ChoiceField(choices=["24H", "WEEKLY", "MONTHLY"])


# =========================================================
# GOLD CHART
# =========================================================


class GoldChartSerializer(serializers.Serializer):

    FILTER_CHOICES = ["24H", "WEEKLY", "MONTHLY"]

    filter_type = serializers.ChoiceField(choices=FILTER_CHOICES, default="24H")


class GoldBubbleSerializer(serializers.Serializer):
    buy_price = serializers.IntegerField()
    sell_price = serializers.IntegerField()
    bubble_amount = serializers.IntegerField()
    bubble_percent = serializers.FloatField()
    is_positive = serializers.BooleanField()


class GoldChartStatsSerializer(serializers.Serializer):
    current_price = serializers.IntegerField()
    highest_price = serializers.IntegerField()
    lowest_price = serializers.IntegerField()
    change_amount = serializers.IntegerField()
    change_percent = serializers.FloatField()
    min_y = serializers.IntegerField()
    max_y = serializers.IntegerField()


class GoldChartDataSerializer(serializers.Serializer):
    labels = serializers.ListField(child=serializers.CharField())
    prices = serializers.ListField(child=serializers.IntegerField())


class GoldChartSerializer(serializers.Serializer):
    chart = GoldChartDataSerializer()
    stats = GoldChartStatsSerializer()
    bubble = GoldBubbleSerializer()


class GoldOrderSerializer(serializers.Serializer):

    order_type = serializers.ChoiceField(choices=["BUY", "SELL"])

    target_price = serializers.DecimalField(max_digits=20, decimal_places=0)

    amount_toman = serializers.DecimalField(
        max_digits=20, decimal_places=0, required=False
    )

    gold_weight = serializers.DecimalField(
        max_digits=20, decimal_places=5, required=False
    )

    def validate(self, data):

        order_type = data["order_type"]

        if order_type == "BUY":

            if not data.get("amount_toman"):
                raise serializers.ValidationError("مبلغ تومان الزامی است")

        elif order_type == "SELL":

            if not data.get("gold_weight"):
                raise serializers.ValidationError("وزن طلا الزامی است")

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


class AssetValueSerializer(serializers.Serializer):

    total_asset_value = serializers.DecimalField(max_digits=25, decimal_places=0)

    gold_balance = serializers.DecimalField(max_digits=20, decimal_places=5)

    silver_balance = serializers.DecimalField(max_digits=20, decimal_places=5)

    wallet_balance = serializers.DecimalField(max_digits=20, decimal_places=0)

    gold_asset_value = serializers.DecimalField(max_digits=25, decimal_places=0)

    silver_asset_value = serializers.DecimalField(max_digits=25, decimal_places=0)

    gold_price = serializers.DecimalField(max_digits=20, decimal_places=0)

    silver_price = serializers.DecimalField(max_digits=20, decimal_places=0)
