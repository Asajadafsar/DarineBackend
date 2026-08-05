# gold_app/serializers.py

from rest_framework import serializers
from decimal import Decimal

from .utils import get_live_gold_price
from accounts.models import BankCard, ReferralEarning

from .models import (
    GoldInventory,
    GoldOrder,
    GoldTransaction,
    Invoice,
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


# class GoldTransactionSerializer(serializers.ModelSerializer):

#     type_display = serializers.CharField(source="get_type_display", read_only=True)

#     status_display = serializers.CharField(source="get_status_display", read_only=True)

#     final_price = serializers.SerializerMethodField()

#     class Meta:
#         model = GoldTransaction
#         fields = [
#             "id",
#             "type",
#             "type_display",
#             "status",
#             "status_display",
#             "amount_gr",
#             "price_per_gram",
#             "fee",
#             "total_amount",
#             "final_price",
#             "tracking_code",
#             "description",
#             "created_at",
#             "updated_at",
#         ]

#     def get_final_price(self, obj):

#         return int(obj.total_amount - obj.fee)

# gold_app/serializers.py - اصلاح GoldTransactionSerializer

from rest_framework import serializers
from decimal import Decimal
from .models import GoldTransaction


# gold_app/serializers.py - کامل

# gold_app/serializers.py - اصلاح GoldTransactionSerializer

from rest_framework import serializers
from decimal import Decimal
from datetime import datetime
import jdatetime
from .models import GoldTransaction, Invoice


class GoldTransactionSerializer(serializers.ModelSerializer):
    """
    سریالایزر تراکنش‌های طلا برای گزارشات
    """
    type_display = serializers.SerializerMethodField()
    status_display = serializers.SerializerMethodField()
    created_at_fa = serializers.SerializerMethodField()
    created_at_time = serializers.SerializerMethodField()
    
    shop_name = serializers.SerializerMethodField()
    customer_name = serializers.SerializerMethodField()
    customer_mobile = serializers.SerializerMethodField()
    customer_national_code = serializers.SerializerMethodField()
    gold_carat = serializers.SerializerMethodField()
    fee_toman = serializers.SerializerMethodField()
    price_per_gram = serializers.SerializerMethodField()
    weight_gr = serializers.SerializerMethodField()
    total_amount_display = serializers.SerializerMethodField()
    total_amount_toman = serializers.SerializerMethodField()
    fee_amount = serializers.SerializerMethodField()
    pure_gold_price = serializers.SerializerMethodField()
    
    # ✅ اضافه کردن invoice_id و invoice_number
    invoice_id = serializers.SerializerMethodField()
    invoice_number = serializers.SerializerMethodField()
    
    class Meta:
        model = GoldTransaction
        fields = [
            'id', 'tracking_code', 'type', 'type_display',
            'status', 'status_display',
            'amount_gr', 'weight_gr',
            'price_per_gram',
            'fee', 'fee_toman', 'fee_amount',
            'commission_percent', 'commission_amount',
            'total_amount', 'total_amount_display', 'total_amount_toman',
            'pure_gold_price',
            'shop_name',
            'customer_name',
            'customer_mobile',
            'customer_national_code',
            'gold_carat',
            'invoice_id',        # ✅ اضافه شد
            'invoice_number',    # ✅ اضافه شد
            'description',
            'created_at', 'created_at_fa', 'created_at_time',
            'updated_at'
        ]
        read_only_fields = ['id', 'tracking_code', 'created_at', 'updated_at']
    
    def get_type_display(self, obj):
        return dict(GoldTransaction.TYPE_CHOICES).get(obj.type, obj.type)
    
    def get_status_display(self, obj):
        return dict(GoldTransaction.STATUS_CHOICES).get(obj.status, obj.status)
    
    def get_created_at_fa(self, obj):
        if obj.created_at:
            shamsi = jdatetime.datetime.fromgregorian(datetime=obj.created_at)
            return shamsi.strftime("%Y/%m/%d")
        return None
    
    def get_created_at_time(self, obj):
        if obj.created_at:
            return obj.created_at.strftime("%H:%M")
        return None
    
    def get_shop_name(self, obj):
        return "دارینه"
    
    def get_customer_name(self, obj):
        if obj.user:
            return f"{obj.user.first_name} {obj.user.last_name}".strip() or obj.user.mobile
        return "کاربر ناشناس"
    
    def get_customer_mobile(self, obj):
        return obj.user.mobile if obj.user else None
    
    def get_customer_national_code(self, obj):
        return getattr(obj.user, 'national_code', None) if obj.user else None
    
    def get_gold_carat(self, obj):
        return 18
    
    def get_fee_toman(self, obj):
        return float(obj.fee or 0)
    
    def get_price_per_gram(self, obj):
        return float(obj.price_per_gram or 0)
    
    def get_weight_gr(self, obj):
        return float(obj.amount_gr or 0)
    
    def get_total_amount_display(self, obj):
        return f"{int(obj.total_amount or 0):,}"
    
    def get_total_amount_toman(self, obj):
        return float(obj.total_amount or 0)
    
    def get_fee_amount(self, obj):
        return float(obj.fee or 0)
    
    def get_pure_gold_price(self, obj):
        """محاسبه قیمت خالص طلا"""
        if obj.price_per_gram and obj.amount_gr:
            return float(obj.price_per_gram * obj.amount_gr)
        return 0
    
    def get_invoice_id(self, obj):
        """دریافت شناسه فاکتور مرتبط با تراکنش"""
        try:
            invoice = obj.invoices.first()
            return invoice.id if invoice else None
        except:
            return None
    
    def get_invoice_number(self, obj):
        """دریافت شماره فاکتور مرتبط با تراکنش"""
        try:
            invoice = obj.invoices.first()
            return invoice.invoice_number if invoice else None
        except:
            return None





# gold_app/serializers.py - InvoiceSerializer کامل

from rest_framework import serializers
from decimal import Decimal
from datetime import datetime
import jdatetime
from django.utils import timezone
from .models import GoldTransaction, Invoice


class InvoiceSerializer(serializers.ModelSerializer):
    """
    سریالایزر فاکتور - مطابق با ساختار فرانت‌اند
    """
    
    # =============================================
    # فیلدهای نمایشی
    # =============================================
    invoice_type_display = serializers.SerializerMethodField()
    status_display = serializers.SerializerMethodField()
    created_at_jalali = serializers.SerializerMethodField()
    created_at_time = serializers.SerializerMethodField()
    invoice_date_display = serializers.SerializerMethodField()
    
    # =============================================
    # فیلدهای خریدار
    # =============================================
    buyer_name = serializers.CharField()
    buyer_national_id = serializers.CharField()
    buyer_phone = serializers.CharField()
    buyer_address = serializers.CharField()
    
    # =============================================
    # فیلدهای فروشنده (فقط نام و آدرس)
    # =============================================
    seller_name = serializers.CharField()
    seller_address = serializers.CharField()
    
    # =============================================
    # فیلدهای طلا با فرمت
    # =============================================
    gold_weight = serializers.SerializerMethodField()
    gold_weight_display = serializers.SerializerMethodField()
    gold_carat = serializers.SerializerMethodField()
    gold_price_per_gram = serializers.SerializerMethodField()
    gold_price_per_gram_display = serializers.SerializerMethodField()
    pure_gold_price = serializers.SerializerMethodField()
    pure_gold_price_display = serializers.SerializerMethodField()
    fee_rate = serializers.SerializerMethodField()
    fee_amount = serializers.SerializerMethodField()
    fee_amount_display = serializers.SerializerMethodField()
    total_amount = serializers.SerializerMethodField()
    total_amount_display = serializers.SerializerMethodField()
    
    class Meta:
        model = Invoice
        fields = [
            # شناسه
            'id',
            'invoice_number',
            'invoice_type',
            'invoice_type_display',
            
            # تاریخ
            'invoice_date',
            'invoice_date_display',
            'created_at_jalali',
            'created_at_time',
            
            # وضعیت
            'status',
            'status_display',
            
            # خریدار (کامل)
            'buyer_name',
            'buyer_national_id',
            'buyer_phone',
            'buyer_address',
            
            # فروشنده (فقط نام و آدرس)
            'seller_name',
            'seller_address',
            
            # اطلاعات طلا
            'gold_weight',
            'gold_weight_display',
            'gold_carat',
            'gold_price_per_gram',
            'gold_price_per_gram_display',
            'pure_gold_price',
            'pure_gold_price_display',
            'fee_rate',
            'fee_amount',
            'fee_amount_display',
            'total_amount',
            'total_amount_display',
            
            # کد رهگیری و توضیحات
            'tracking_code',
            'description',
            'created_at'
        ]
        read_only_fields = [
            'id', 'invoice_number', 'created_at', 'invoice_date'
        ]
    
    # =============================================
    # متدهای نمایش وضعیت و نوع
    # =============================================
    
    def get_invoice_type_display(self, obj):
        """دریافت نمایش فارسی نوع فاکتور"""
        return obj.get_invoice_type_display()
    
    def get_status_display(self, obj):
        """دریافت نمایش فارسی وضعیت فاکتور"""
        return obj.get_status_display()
    
    # =============================================
    # متدهای نمایش تاریخ و زمان
    # =============================================
    
    def get_created_at_jalali(self, obj):
        """دریافت تاریخ شمسی"""
        if obj.created_at:
            local_time = timezone.localtime(obj.created_at)
            shamsi = jdatetime.datetime.fromgregorian(datetime=local_time)
            return shamsi.strftime('%Y/%m/%d')
        return None
    
    def get_created_at_time(self, obj):
        """دریافت ساعت"""
        if obj.created_at:
            local_time = timezone.localtime(obj.created_at)
            return local_time.strftime('%H:%M')
        return None
    
    def get_invoice_date_display(self, obj):
        """دریافت تاریخ و ساعت کامل برای نمایش"""
        if obj.created_at:
            local_time = timezone.localtime(obj.created_at)
            shamsi = jdatetime.datetime.fromgregorian(datetime=local_time)
            return shamsi.strftime('%Y/%m/%d %H:%M')
        return None
    
    # =============================================
    # متدهای نمایش وزن طلا
    # =============================================
    
    def get_gold_weight(self, obj):
        """دریافت وزن طلا به صورت عدد"""
        return float(obj.gold_weight) if obj.gold_weight else 0
    
    def get_gold_weight_display(self, obj):
        """
        نمایش وزن طلا با فرمت فارسی
        مثال: ۵٫۰۰۰
        """
        if obj.gold_weight:
            weight_str = f"{obj.gold_weight:,.3f}"
            persian_digits = {'0': '۰', '1': '۱', '2': '۲', '3': '۳', '4': '۴',
                            '5': '۵', '6': '۶', '7': '۷', '8': '۸', '9': '۹'}
            for eng, per in persian_digits.items():
                weight_str = weight_str.replace(eng, per)
            return weight_str
        return "۰"
    
    # =============================================
    # متدهای نمایش عیار طلا
    # =============================================
    
    def get_gold_carat(self, obj):
        """دریافت عیار طلا"""
        return obj.gold_carat or 18
    
    # =============================================
    # متدهای نمایش قیمت هر گرم طلا
    # =============================================
    
    def get_gold_price_per_gram(self, obj):
        """دریافت قیمت هر گرم طلا به صورت عدد"""
        return float(obj.gold_price_per_gram) if obj.gold_price_per_gram else 0
    
    def get_gold_price_per_gram_display(self, obj):
        """
        نمایش قیمت هر گرم طلا با فرمت تومان
        مثال: ۱۷,۲۱۷,۰۰۰ تومان
        """
        if obj.gold_price_per_gram:
            price_str = f"{int(obj.gold_price_per_gram):,}"
            persian_digits = {'0': '۰', '1': '۱', '2': '۲', '3': '۳', '4': '۴',
                            '5': '۵', '6': '۶', '7': '۷', '8': '۸', '9': '۹'}
            for eng, per in persian_digits.items():
                price_str = price_str.replace(eng, per)
            return f"{price_str} تومان"
        return "۰ تومان"
    
    # =============================================
    # متدهای نمایش قیمت خالص طلا
    # =============================================
    
    def get_pure_gold_price(self, obj):
        """دریافت قیمت خالص طلا به صورت عدد"""
        return float(obj.pure_gold_price) if obj.pure_gold_price else 0
    
    def get_pure_gold_price_display(self, obj):
        """
        نمایش قیمت خالص طلا با فرمت تومان
        مثال: ۸۶,۰۸۵,۰۰۰ تومان
        """
        if obj.pure_gold_price:
            price_str = f"{int(obj.pure_gold_price):,}"
            persian_digits = {'0': '۰', '1': '۱', '2': '۲', '3': '۳', '4': '۴',
                            '5': '۵', '6': '۶', '7': '۷', '8': '۸', '9': '۹'}
            for eng, per in persian_digits.items():
                price_str = price_str.replace(eng, per)
            return f"{price_str} تومان"
        return "۰ تومان"
    
    # =============================================
    # متدهای نمایش کارمزد
    # =============================================
    
    def get_fee_rate(self, obj):
        """دریافت درصد کارمزد"""
        return float(obj.fee_rate) if obj.fee_rate else 0
    
    def get_fee_amount(self, obj):
        """دریافت مبلغ کارمزد به صورت عدد"""
        return float(obj.fee_amount) if obj.fee_amount else 0
    
    def get_fee_amount_display(self, obj):
        """
        نمایش مبلغ کارمزد با فرمت تومان
        مثال: ۸۶۰,۸۵۰ تومان
        """
        if obj.fee_amount:
            fee_str = f"{int(obj.fee_amount):,}"
            persian_digits = {'0': '۰', '1': '۱', '2': '۲', '3': '۳', '4': '۴',
                            '5': '۵', '6': '۶', '7': '۷', '8': '۸', '9': '۹'}
            for eng, per in persian_digits.items():
                fee_str = fee_str.replace(eng, per)
            return f"{fee_str} تومان"
        return "۰ تومان"
    
    # =============================================
    # متدهای نمایش مبلغ کل
    # =============================================
    
    def get_total_amount(self, obj):
        """دریافت مبلغ کل به صورت عدد"""
        return float(obj.total_amount) if obj.total_amount else 0
    
    def get_total_amount_display(self, obj):
        """
        نمایش مبلغ کل با فرمت تومان
        مثال: ۸۶,۹۴۵,۸۵۰ تومان
        """
        if obj.total_amount:
            total_str = f"{int(obj.total_amount):,}"
            persian_digits = {'0': '۰', '1': '۱', '2': '۲', '3': '۳', '4': '۴',
                            '5': '۵', '6': '۶', '7': '۷', '8': '۸', '9': '۹'}
            for eng, per in persian_digits.items():
                total_str = total_str.replace(eng, per)
            return f"{total_str} تومان"
        return "۰ تومان"



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


# class OrderSerializer(serializers.ModelSerializer):

#     items = OrderItemSerializer(many=True, read_only=True)

#     payment_method_display = serializers.CharField(
#         source="get_payment_method_display", read_only=True
#     )

#     status_display = serializers.CharField(source="get_status_display", read_only=True)

#     delivery_type_display = serializers.CharField(
#         source="get_delivery_type_display", read_only=True
#     )

#     status_history = OrderStatusHistorySerializer(many=True, read_only=True)

#     class Meta:
#         model = Order
#         fields = [
#             "id",
#             "province",
#             "city",
#             "address",
#             "postal_code",
#             "plaque",
#             "unit",
#             "payment_method",
#             "payment_method_display",
#             "delivery_type",
#             "delivery_type_display",
#             "status",
#             "status_display",
#             "total_gold_amount",
#             "total_toman_amount",
#             "tracking_code",
#             "created_at",
#             "admin_note",
#             "items",
#             "status_history",
#         ]
# gold_app/serializers.py - اصلاح OrderSerializer

from rest_framework import serializers
from .models import Order, OrderItem


class OrderItemSerializer(serializers.ModelSerializer):
    """سریالایزر آیتم‌های سفارش"""
    
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_image = serializers.SerializerMethodField()
    
    class Meta:
        model = OrderItem
        fields = [
            'id',
            'product',
            'product_name',
            'product_image',
            'quantity',
            'price_at_time',
            'weight_at_time',
        ]
    
    def get_product_image(self, obj):
        if obj.product and obj.product.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.product.image.url)
            return obj.product.image.url
        return None


class OrderSerializer(serializers.ModelSerializer):
    """
    سریالایزر سفارشات فیزیکی
    """
    
    status_display = serializers.SerializerMethodField()
    payment_method_display = serializers.SerializerMethodField()
    created_at_jalali = serializers.SerializerMethodField()
    created_at_time = serializers.SerializerMethodField()
    items = OrderItemSerializer(many=True, read_only=True)
    
    # ✅ استفاده از SerializerMethodField برای فیلدهای فاکتور
    physical_invoice_id = serializers.SerializerMethodField()
    physical_invoice_number = serializers.SerializerMethodField()
    physical_invoice_status = serializers.SerializerMethodField()
    physical_invoice_status_display = serializers.SerializerMethodField()
    
    class Meta:
        model = Order
        fields = [
            'id',
            'tracking_code',
            'status',
            'status_display',
            'payment_method',
            'payment_method_display',
            'total_gold_amount',
            'total_toman_amount',
            'province',
            'city',
            'address',
            'postal_code',
            'plaque',
            'unit',
            'description',
            'items',
            # ✅ فیلدهای جدید
            'physical_invoice_id',
            'physical_invoice_number',
            'physical_invoice_status',
            'physical_invoice_status_display',
            'created_at',
            'created_at_jalali',
            'created_at_time',
            'updated_at'
        ]
        read_only_fields = ['id', 'tracking_code', 'created_at', 'updated_at']
    
    def get_status_display(self, obj):
        return obj.get_status_display()
    
    def get_payment_method_display(self, obj):
        return obj.get_payment_method_display()
    
    def get_created_at_jalali(self, obj):
        if obj.created_at:
            import jdatetime
            from datetime import datetime
            shamsi = jdatetime.datetime.fromgregorian(datetime=obj.created_at)
            return shamsi.strftime("%Y/%m/%d")
        return None
    
    def get_created_at_time(self, obj):
        if obj.created_at:
            return obj.created_at.strftime("%H:%M")
        return None
    
    # =============================================
    # ✅ متدهای دریافت اطلاعات فاکتور فیزیکی
    # =============================================
    
    def get_physical_invoice_id(self, obj):
        """دریافت شناسه فاکتور سفارش فیزیکی"""
        try:
            invoice = obj.physical_invoices.first()
            return invoice.id if invoice else None
        except:
            return None
    
    def get_physical_invoice_number(self, obj):
        """دریافت شماره فاکتور سفارش فیزیکی"""
        try:
            invoice = obj.physical_invoices.first()
            return invoice.invoice_number if invoice else None
        except:
            return None
    
    def get_physical_invoice_status(self, obj):
        """دریافت وضعیت فاکتور سفارش فیزیکی"""
        try:
            invoice = obj.physical_invoices.first()
            return invoice.status if invoice else None
        except:
            return None
    
    def get_physical_invoice_status_display(self, obj):
        """دریافت نمایش فارسی وضعیت فاکتور سفارش فیزیکی"""
        try:
            invoice = obj.physical_invoices.first()
            return invoice.get_status_display() if invoice else None
        except:
            return None

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

from rest_framework import serializers
from rest_framework import serializers

# =========================================================
# BUY GOLD SERIALIZER (FIXED)
# =========================================================

from decimal import Decimal, ROUND_DOWN

from rest_framework import serializers


# =========================================================
# BUY GOLD SERIALIZER (FIXED)
# =========================================================

from decimal import Decimal, ROUND_DOWN

from rest_framework import serializers

from decimal import Decimal, ROUND_DOWN
from rest_framework import serializers
from accounts.models import FeeSetting, UserFee  # نام اپلیکیشن خود را جایگزین کنید

from decimal import Decimal, ROUND_DOWN

from rest_framework import serializers

from accounts.models import FeeSetting
from decimal import Decimal, ROUND_DOWN
from rest_framework import serializers
from accounts.models import FeeSetting

from decimal import Decimal, ROUND_DOWN
from rest_framework import serializers
from accounts.models import FeeSetting


from accounts.models import FeeSetting
from rest_framework import serializers
from decimal import Decimal, ROUND_DOWN


class BuyGoldSerializer(serializers.Serializer):
    """
    خرید طلا
    
    اگر weight ارسال شود:
        قیمت خالص = قیمت طلا × وزن
        کارمزد = قیمت خالص × نرخ کارمزد
        مبلغ کل = قیمت خالص + کارمزد
    
    اگر toman ارسال شود (مبلغ کل شامل کارمزد):
        قیمت خالص = مبلغ کل ÷ (۱ + نرخ کارمزد)
        کارمزد = مبلغ کل - قیمت خالص
        وزن = قیمت خالص ÷ قیمت طلا
        مبلغ کل = مبلغ وارد شده (همون toman)  ✅ اینجا مهمه
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

        # دریافت قیمت طلا از context
        gold_price = Decimal(str(self.context["gold_price"]))
        if gold_price <= 0:
            raise serializers.ValidationError(
                {"non_field_errors": ["قیمت طلا نامعتبر است."]}
            )

        # دریافت نرخ کارمزد
        user = self.context["request"].user
        user_fee = getattr(user, "fee", None)

        if user_fee:
            fee_rate = user_fee.gold_buy_fee
        else:
            setting = FeeSetting.objects.last()
            fee_rate = setting.gold_buy_fee if setting else Decimal("0.01")

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
            pure_gold_price = (gold_price * final_weight).quantize(Decimal("1"))
            fee = (pure_gold_price * fee_rate).quantize(Decimal("1"))
            total_toman = (pure_gold_price + fee).quantize(Decimal("1"))

        # ===========================
        # خرید بر اساس مبلغ کل (کارمزد از مبلغ کم میشه)  ✅ درسته
        # ===========================
        else:
            toman = Decimal(str(toman)).quantize(Decimal("1"))
            if toman <= 0:
                raise serializers.ValidationError(
                    {"toman": ["مبلغ وارد شده باید بزرگتر از صفر باشد."]}
                )

            # ✅ قیمت خالص = مبلغ کل ÷ (۱ + نرخ کارمزد)
            pure_gold_price = (toman / (Decimal("1") + fee_rate)).quantize(Decimal("1"))
            
            # ✅ کارمزد = مبلغ کل - قیمت خالص
            fee = (toman - pure_gold_price).quantize(Decimal("1"))
            
            # ✅ وزن = قیمت خالص ÷ قیمت هر گرم
            final_weight = (pure_gold_price / gold_price).quantize(
                Decimal("0.001"),
                rounding=ROUND_DOWN,
            )

            if final_weight <= 0:
                raise serializers.ValidationError(
                    {"non_field_errors": ["مبلغ وارد شده برای خرید حتی یک هزارم گرم طلا کافی نیست."]}
                )

            # ✅ مبلغ کل = همون مبلغ ورودی (۱۰ میلیون)
            total_toman = toman  # ← اینجا مهمه! همون ۱۰ میلیون میمونه

        # ذخیره در attrs
        attrs["fee_rate"] = fee_rate
        attrs["fee"] = fee
        attrs["gold_price"] = gold_price
        attrs["pure_gold_price"] = pure_gold_price
        attrs["total_toman"] = total_toman  # ✅ اینجا ۱۰ میلیون هست
        attrs["final_weight"] = final_weight

        return attrs


from decimal import Decimal, ROUND_DOWN

from rest_framework import serializers

from decimal import Decimal, ROUND_DOWN, ROUND_HALF_UP
from rest_framework import serializers
from accounts.models import FeeSetting
# =========================================================
# SELL GOLD SERIALIZER - نسخه نهایی ✅
# =========================================================

from decimal import Decimal, ROUND_DOWN, ROUND_UP
from rest_framework import serializers


# =========================================================
# SELL GOLD SERIALIZER - اصلاح شده برای فروش مثل خرید ✅
# =========================================================

from decimal import Decimal, ROUND_DOWN, ROUND_UP
from rest_framework import serializers

# =========================================================
# SELL GOLD SERIALIZER - ورودی وزن ✅
# =========================================================

from decimal import Decimal, ROUND_DOWN
from rest_framework import serializers


class SellGoldSerializer(serializers.Serializer):
    """
    فروش طلا - ورودی وزن (گرم)
    
    weight = وزن طلا برای فروش (مثلاً 0.555 گرم)
    """
    
    weight = serializers.DecimalField(
        max_digits=20, 
        decimal_places=3, 
        required=True,
        error_messages={
            'required': 'وارد کردن وزن برای فروش الزامی است',
            'blank': 'وزن نمی‌تواند خالی باشد',
            'null': 'وزن نمی‌تواند خالی باشد',
            'min_value': 'وزن باید بزرگتر از صفر باشد',
        }
    )

    def validate(self, attrs):
        weight = attrs.get("weight")

        # ===========================
        # اعتبارسنجی وزن
        # ===========================
        if weight is None:
            raise serializers.ValidationError(
                {"weight": ["وارد کردن وزن برای فروش الزامی است."]}
            )

        weight = Decimal(str(weight)).quantize(Decimal("0.001"), rounding=ROUND_DOWN)
        if weight <= 0:
            raise serializers.ValidationError(
                {"weight": ["وزن وارد شده باید بزرگتر از صفر باشد."]}
            )

        attrs["weight"] = weight

        # ===========================
        # دریافت قیمت طلا
        # ===========================
        gold_price = Decimal(str(self.context["gold_price"]))
        if gold_price <= 0:
            raise serializers.ValidationError(
                {"non_field_errors": ["قیمت طلا نامعتبر است."]}
            )

        # ===========================
        # دریافت نرخ کارمزد
        # ===========================
        user = self.context["request"].user
        user_fee = getattr(user, "fee", None)

        if user_fee:
            fee_rate = user_fee.gold_sell_fee
        else:
            setting = FeeSetting.objects.last()
            fee_rate = setting.gold_sell_fee if setting else Decimal("0.01")

        fee_rate = Decimal(str(fee_rate))
        if fee_rate < 0:
            raise serializers.ValidationError(
                {"non_field_errors": ["کارمزد نامعتبر است."]}
            )

        # ===========================
        # محاسبات فروش با وزن ورودی ✅
        # ===========================
        final_weight = weight  # ✅ وزن تغییری نمیکند
        
        # ارزش خالص = وزن × قیمت
        pure_value = (gold_price * final_weight).quantize(Decimal("1"))
        
        # کارمزد = ارزش خالص × نرخ کارمزد
        fee = (pure_value * fee_rate).quantize(Decimal("1"))
        
        # مبلغ نهایی = ارزش خالص - کارمزد
        final_amount = (pure_value - fee).quantize(Decimal("1"))

        if final_amount < 0:
            raise serializers.ValidationError(
                {"non_field_errors": ["کارمزد بیشتر از ارزش طلا است."]}
            )

        # ===========================
        # ذخیره در attrs
        # ===========================
        attrs["fee_rate"] = fee_rate
        attrs["fee"] = fee
        attrs["gold_price"] = gold_price
        attrs["pure_value"] = pure_value
        attrs["final_amount"] = final_amount
        attrs["final_weight"] = final_weight

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

# gold_app/serializers.py - اضافه کردن PhysicalOrderInvoiceSerializer

from gold_app.models import PhysicalOrderInvoice

# gold_app/serializers.py - اصلاح PhysicalOrderInvoiceSerializer

from gold_app.models import PhysicalOrderInvoice


class PhysicalOrderInvoiceSerializer(serializers.ModelSerializer):
    """
    سریالایزر فاکتور سفارش فیزیکی
    """
    
    status_display = serializers.SerializerMethodField()
    invoice_type_display = serializers.SerializerMethodField()
    payment_method_display = serializers.SerializerMethodField()
    created_at_jalali = serializers.SerializerMethodField()
    created_at_time = serializers.SerializerMethodField()
    
    gold_weight_display = serializers.SerializerMethodField()
    total_amount_display = serializers.SerializerMethodField()
    pure_gold_price_display = serializers.SerializerMethodField()
    
    class Meta:
        model = PhysicalOrderInvoice
        fields = [
            'id',
            'invoice_number',
            'invoice_type',
            'invoice_type_display',
            'status',
            'status_display',
            'invoice_date',
            'created_at_jalali',
            'created_at_time',
            
            # اطلاعات خریدار (بدون شماره ملی و تلفن)
            'buyer_name',
            # 'buyer_national_id',  # ❌ حذف شد
            # 'buyer_phone',        # ❌ حذف شد
            'buyer_address',
            'buyer_province',
            'buyer_city',
            'buyer_postal_code',
            
            # اطلاعات فروشنده
            'seller_name',
            # 'seller_national_id',  # ❌ حذف شد
            # 'seller_phone',        # ❌ حذف شد
            'seller_address',
            'seller_province',
            
            # اطلاعات سفارش
            'order_tracking_code',
            'payment_method',
            'payment_method_display',
            
            # اطلاعات طلا
            'gold_weight',
            'gold_weight_display',
            'gold_carat',
            'gold_price_per_gram',
            'pure_gold_price',
            'pure_gold_price_display',
            
            # اطلاعات مالی
            'shipping_fee',
            'tax_amount',
            'discount_amount',
            'total_amount',
            'total_amount_display',
            
            # محصولات
            'products_summary',
            
            # تکمیلی
            'description',
            'created_at',
            'updated_at'
        ]
        read_only_fields = [
            'id', 'invoice_number', 'created_at', 'updated_at', 'invoice_date'
        ]
    
    def get_status_display(self, obj):
        return obj.get_status_display()
    
    def get_invoice_type_display(self, obj):
        return obj.get_invoice_type_display()
    
    def get_payment_method_display(self, obj):
        return obj.get_payment_method_display()
    
    def get_created_at_jalali(self, obj):
        if obj.created_at:
            import jdatetime
            from django.utils import timezone
            local_time = timezone.localtime(obj.created_at)
            shamsi = jdatetime.datetime.fromgregorian(datetime=local_time)
            return shamsi.strftime('%Y/%m/%d')
        return None
    
    def get_created_at_time(self, obj):
        if obj.created_at:
            from django.utils import timezone
            local_time = timezone.localtime(obj.created_at)
            return local_time.strftime('%H:%M')
        return None
    
    def get_gold_weight_display(self, obj):
        if obj.gold_weight:
            return f"{obj.gold_weight:,.3f}"
        return "۰"
    
    def get_total_amount_display(self, obj):
        if obj.total_amount:
            return f"{int(obj.total_amount):,} تومان"
        return "۰ تومان"
    
    def get_pure_gold_price_display(self, obj):
        if obj.pure_gold_price:
            return f"{int(obj.pure_gold_price):,} تومان"
        return "۰ تومان"
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




# gold_app/serializers.py

from rest_framework import serializers
from decimal import Decimal, ROUND_DOWN
from .models import GoldOrder
from accounts.models import FeeSetting, UserFee

# gold_app/serializers.py

from rest_framework import serializers
from decimal import Decimal, ROUND_DOWN
from .models import GoldOrder, Wallet, GoldInventory
from accounts.models import FeeSetting, UserFee

from rest_framework import serializers
from decimal import Decimal, ROUND_DOWN
from .models import GoldOrder, Wallet, GoldInventory
from accounts.models import FeeSetting, UserFee


# class GoldLimitOrderCreateSerializer(serializers.Serializer):
#     """
#     سریالایزر ایجاد سفارش با قیمت برای طلا

#     خرید (BUY) - amount_toman ارسال می‌شود (مبلغ کل شامل کارمزد):
#         قیمت خالص = مبلغ کل ÷ (۱ + نرخ کارمزد)
#         کارمزد = مبلغ کل - قیمت خالص
#         وزن = قیمت خالص ÷ قیمت هدف
#         مبلغ کل = همان amount_toman ورودی

#     فروش (SELL) - gold_weight ارسال می‌شود:
#         قیمت خالص = قیمت هدف × وزن
#         کارمزد = قیمت خالص × نرخ کارمزد
#         مبلغ نهایی = قیمت خالص - کارمزد
#     """
#     order_type = serializers.ChoiceField(
#         choices=[('BUY', 'خرید'), ('SELL', 'فروش')],
#         required=True,
#         error_messages={
#             'required': 'نوع سفارش الزامی است',
#             'blank': 'نوع سفارش نمی‌تواند خالی باشد',
#             'invalid_choice': 'نوع سفارش نامعتبر است',
#         }
#     )
#     target_price = serializers.DecimalField(
#         max_digits=20,
#         decimal_places=0,
#         required=True,
#         min_value=Decimal("1"),
#         error_messages={
#             'required': 'قیمت مد نظر الزامی است',
#             'blank': 'قیمت مد نظر نمی‌تواند خالی باشد',
#             'min_value': 'قیمت مد نظر باید بزرگتر از صفر باشد',
#             'invalid': 'قیمت مد نظر نامعتبر است',
#         }
#     )
#     amount_toman = serializers.DecimalField(
#         max_digits=20,
#         decimal_places=0,
#         required=False,
#         allow_null=True,
#         error_messages={
#             'invalid': 'مبلغ به تومان نامعتبر است',
#         }
#     )
#     gold_weight = serializers.DecimalField(
#         max_digits=20,
#         decimal_places=3,
#         required=False,
#         allow_null=True,
#         error_messages={
#             'invalid': 'وزن طلا نامعتبر است',
#             'max_digits': 'وزن طلا بیش از حد بزرگ است',
#             'max_decimal_places': 'وزن طلا باید دقیقاً ۳ رقم اعشار داشته باشد',
#         }
#     )

#     def validate_gold_weight(self, value):
#         """
#         ✅ اعتبارسنجی دقیق وزن طلا - ۳ رقم اعشار
#         """
#         if value is None:
#             return value

#         value = Decimal(str(value))
#         decimal_places = abs(value.as_tuple().exponent)

#         if decimal_places != 3:
#             raise serializers.ValidationError(
#                 f'وزن طلا باید دقیقاً ۳ رقم اعشار داشته باشد (مثلاً {value:.3f})'
#             )

#         if value <= 0:
#             raise serializers.ValidationError(
#                 'وزن طلا باید بزرگتر از صفر باشد'
#             )

#         return value

#     def validate(self, attrs):
#         user = self.context['request'].user
#         order_type = attrs.get('order_type')
#         target_price = attrs.get('target_price')
#         amount_toman = attrs.get('amount_toman')
#         gold_weight = attrs.get('gold_weight')

#         # دریافت قیمت لحظه‌ای طلا
#         from .utils import get_live_gold_price
#         current_price = get_live_gold_price()

#         if not current_price:
#             raise serializers.ValidationError({
#                 'non_field_errors': ['خطا در دریافت قیمت لحظه‌ای طلا']
#             })

#         current_price = Decimal(str(current_price))

#         # =============================================
#         # اعتبارسنجی قیمت هدف
#         # خرید: قیمت هدف باید کمتر یا مساوی قیمت لحظه‌ای باشد
#         # فروش: قیمت هدف باید بیشتر یا مساوی قیمت لحظه‌ای باشد
#         # =============================================
#         if order_type == 'BUY':
#             if target_price > current_price:
#                 raise serializers.ValidationError({
#                     'target_price': [
#                         f'قیمت هدف خرید ({target_price:,}) باید کمتر یا مساوی قیمت لحظه‌ای ({current_price:,}) باشد'
#                     ]
#                 })
#         else:  # SELL
#             if target_price < current_price:
#                 raise serializers.ValidationError({
#                     'target_price': [
#                         f'قیمت هدف فروش ({target_price:,}) باید بیشتر یا مساوی قیمت لحظه‌ای ({current_price:,}) باشد'
#                     ]
#                 })

#         # دریافت نرخ کارمزد
#         user_fee = getattr(user, 'fee', None)
#         if user_fee:
#             fee_rate = user_fee.gold_buy_fee if order_type == 'BUY' else user_fee.gold_sell_fee
#         else:
#             from admin_panel.models import FeeSetting
#             setting = FeeSetting.objects.last()
#             fee_rate = setting.gold_buy_fee if order_type == 'BUY' else setting.gold_sell_fee
#             fee_rate = fee_rate if fee_rate else Decimal("0.01")

#         fee_rate = Decimal(str(fee_rate))
#         if fee_rate < 0:
#             raise serializers.ValidationError({
#                 'non_field_errors': ['کارمزد نامعتبر است.']
#             })

#         # =============================================
#         # خرید - دقیقاً مطابق فرمول BuyGoldSerializer
#         # =============================================
#         if order_type == 'BUY':
#             if not amount_toman:
#                 raise serializers.ValidationError({
#                     'amount_toman': ['مبلغ به تومان برای خرید الزامی است']
#                 })

#             toman = Decimal(str(amount_toman)).quantize(Decimal("1"))
#             if toman <= 0:
#                 raise serializers.ValidationError({
#                     'amount_toman': ['مبلغ وارد شده باید بزرگتر از صفر باشد.']
#                 })

#             # ✅ قیمت خالص = مبلغ کل ÷ (۱ + نرخ کارمزد)
#             pure_price = (toman / (Decimal("1") + fee_rate)).quantize(Decimal("1"))

#             # ✅ کارمزد = مبلغ کل - قیمت خالص
#             fee = (toman - pure_price).quantize(Decimal("1"))

#             # ✅ وزن = قیمت خالص ÷ قیمت هدف
#             estimated_weight = (pure_price / target_price).quantize(
#                 Decimal("0.001"), rounding=ROUND_DOWN
#             )

#             if estimated_weight <= 0:
#                 raise serializers.ValidationError({
#                     'amount_toman': ['مبلغ وارد شده برای خرید حتی یک هزارم گرم طلا کافی نیست.']
#                 })

#             # ✅ مبلغ کل = همان مبلغ ورودی (بدون تغییر)
#             total_price = toman

#             # ✅ بررسی موجودی کیف پول
#             wallet, _ = Wallet.objects.get_or_create(user=user)
#             if wallet.accessible_toman < total_price:
#                 raise serializers.ValidationError({
#                     'amount_toman': [
#                         f'موجودی کیف پول شما ({wallet.accessible_toman:,}) برای خرید کافی نیست. مبلغ مورد نیاز: {total_price:,}'
#                     ]
#                 })

#             attrs['estimated_weight'] = estimated_weight
#             attrs['fee'] = fee
#             attrs['fee_rate'] = fee_rate
#             attrs['pure_price'] = pure_price
#             attrs['amount_toman'] = total_price

#         # =============================================
#         # فروش - دقیقاً مطابق فرمول SellGoldSerializer
#         # =============================================
#         else:  # SELL
#             if not gold_weight:
#                 raise serializers.ValidationError({
#                     'gold_weight': ['وزن طلا برای فروش الزامی است']
#                 })

#             weight = Decimal(str(gold_weight)).quantize(Decimal("0.001"), rounding=ROUND_DOWN)
#             if weight <= 0:
#                 raise serializers.ValidationError({
#                     'gold_weight': ['وزن وارد شده باید بزرگتر از صفر باشد.']
#                 })

#             # ✅ ارزش خالص = وزن × قیمت هدف
#             pure_price = (target_price * weight).quantize(Decimal("1"))

#             # ✅ کارمزد = ارزش خالص × نرخ کارمزد
#             fee = (pure_price * fee_rate).quantize(Decimal("1"))

#             # ✅ مبلغ نهایی = ارزش خالص - کارمزد
#             total_price = (pure_price - fee).quantize(Decimal("1"))

#             estimated_weight = weight

#             if total_price < 0:
#                 raise serializers.ValidationError({
#                     'non_field_errors': ['کارمزد بیشتر از ارزش طلا است.']
#                 })

#             # ✅ بررسی موجودی طلا
#             inventory, _ = GoldInventory.objects.get_or_create(user=user)
#             if inventory.accessible_balance < weight:
#                 raise serializers.ValidationError({
#                     'gold_weight': [
#                         f'موجودی طلای شما ({inventory.accessible_balance:,}) گرم برای فروش کافی نیست. وزن مورد نیاز: {weight:,} گرم'
#                     ]
#                 })

#             attrs['estimated_weight'] = estimated_weight
#             attrs['fee'] = fee
#             attrs['fee_rate'] = fee_rate
#             attrs['pure_price'] = pure_price
#             attrs['total_price'] = total_price
#             # ✅ amount_toman = ارزش خالص (pure_price)، چون get_fee/get_final_price در
#             # GoldOrderListSerializer دقیقاً با همین فرض (total*fee_rate و total-fee) کار می‌کنند
#             attrs['amount_toman'] = pure_price

#         attrs['current_price'] = current_price

#         return attrs

# gold_app/serializers.py

class GoldLimitOrderCreateSerializer(serializers.Serializer):
    order_type = serializers.ChoiceField(choices=[('BUY', 'خرید'), ('SELL', 'فروش')])
    target_price = serializers.DecimalField(max_digits=20, decimal_places=0)
    amount_toman = serializers.DecimalField(max_digits=20, decimal_places=0, required=False)
    gold_weight = serializers.DecimalField(max_digits=20, decimal_places=3, required=False)
    fee_rate = serializers.DecimalField(max_digits=10, decimal_places=4, default=Decimal("0.01"))
    description = serializers.CharField(required=False, allow_blank=True)
    
    def validate(self, data):
        order_type = data.get('order_type')
        target_price = data.get('target_price')
        fee_rate = data.get('fee_rate', Decimal("0.01"))
        
        # ✅ دریافت current_price از context
        current_price = self.context.get('current_price')
        if not current_price:
            raise serializers.ValidationError("قیمت لحظه‌ای دریافت نشد")
        
        # ✅ ذخیره current_price در data
        data['current_price'] = current_price
        
        if order_type == 'BUY':
            amount_toman = data.get('amount_toman')
            if not amount_toman:
                raise serializers.ValidationError({"amount_toman": "مبلغ خرید الزامی است"})
            
            if target_price > current_price:
                raise serializers.ValidationError(
                    f"قیمت هدف خرید ({target_price:,}) باید کمتر یا مساوی قیمت لحظه‌ای ({current_price:,}) باشد"
                )
            
            # محاسبه وزن تخمینی
            pure_price = (amount_toman / (Decimal("1") + fee_rate)).quantize(Decimal("1"))
            estimated_weight = (pure_price / target_price).quantize(Decimal("0.001"), rounding=ROUND_DOWN)
            data['estimated_weight'] = max(estimated_weight, Decimal("0.001"))
            
        else:  # SELL
            gold_weight = data.get('gold_weight')
            if not gold_weight:
                raise serializers.ValidationError({"gold_weight": "وزن فروش الزامی است"})
            
            if target_price < current_price:
                raise serializers.ValidationError(
                    f"قیمت هدف فروش ({target_price:,}) باید بیشتر یا مساوی قیمت لحظه‌ای ({current_price:,}) باشد"
                )
            
            # محاسبه مبلغ
            pure_price = (current_price * gold_weight).quantize(Decimal("1"))
            data['amount_toman'] = pure_price
            data['estimated_weight'] = gold_weight
        
        return data



class GoldOrderListSerializer(serializers.ModelSerializer):
    """
    سریالایزر لیست سفارشات با قیمت طلا با خروجی مورد نظر
    """
    type = serializers.CharField(source='order_type', read_only=True)
    type_display = serializers.CharField(source='get_order_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    amount_gr = serializers.DecimalField(source='estimated_weight', max_digits=20, decimal_places=3, read_only=True)
    price_per_gram = serializers.DecimalField(source='target_price', max_digits=20, decimal_places=0, read_only=True)
    
    # ✅ total_amount با متد محاسبه میشه
    total_amount = serializers.SerializerMethodField()
    
    fee = serializers.SerializerMethodField()
    final_price = serializers.SerializerMethodField()
    tracking_code = serializers.SerializerMethodField()

    class Meta:
        model = GoldOrder
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
            'updated_at',
        ]

    def get_total_amount(self, obj):
        """
        محاسبه مبلغ کل:
        - خرید: amount_toman
        - فروش: gold_weight × target_price
        """
        from decimal import Decimal
        
        if obj.order_type == 'BUY':
            return float(obj.amount_toman or 0)
        else:  # SELL
            weight = obj.gold_weight or Decimal("0")
            price = obj.target_price or Decimal("0")
            total = weight * price
            return int(total)

    def get_fee(self, obj):
        from decimal import Decimal
        total = Decimal(str(self.get_total_amount(obj)))
        fee_rate = obj.fee_rate or Decimal("0.01")
        fee = (total * fee_rate).quantize(Decimal("1"))
        return int(fee)

    def get_final_price(self, obj):
        from decimal import Decimal
        total = Decimal(str(self.get_total_amount(obj)))
        fee_rate = obj.fee_rate or Decimal("0.01")
        fee = (total * fee_rate).quantize(Decimal("1"))
        final = total - fee
        return int(final)

    def get_tracking_code(self, obj):
        return f"LMT-{obj.id:06d}"
# gold_app/serializers.py

from rest_framework import serializers
from .models import GoldOrder



from decimal import Decimal
from rest_framework import serializers
from .models import GoldShortOrder, GoldShortOrderHistory
from accounts.models import FeeSetting, UserFee


class GoldShortOrderCreateSerializer(serializers.Serializer):
    """
    سریالایزر ایجاد سفارش فروش تعهدی
    """
    order_type = serializers.ChoiceField(
        choices=[('MARKET', 'قیمت بازار'), ('LIMIT', 'قیمت هدف')],
        required=True
    )
    weight = serializers.DecimalField(
        max_digits=20,
        decimal_places=3,
        required=True,
        min_value=Decimal("0.001")
    )
    leverage = serializers.IntegerField(
        required=True,
        min_value=1,
        max_value=5
    )
    target_price = serializers.DecimalField(
        max_digits=20,
        decimal_places=0,
        required=False,
        allow_null=True
    )
    take_profit = serializers.DecimalField(
        max_digits=20,
        decimal_places=0,
        required=False,
        allow_null=True
    )
    stop_loss = serializers.DecimalField(
        max_digits=20,
        decimal_places=0,
        required=False,
        allow_null=True
    )

    def validate(self, attrs):
        user = self.context['request'].user
        order_type = attrs.get('order_type')
        weight = attrs.get('weight')
        leverage = attrs.get('leverage')
        target_price = attrs.get('target_price')
        take_profit = attrs.get('take_profit')
        stop_loss = attrs.get('stop_loss')

        # دریافت قیمت لحظه‌ای طلا
        from .utils import get_live_gold_price
        current_price = get_live_gold_price()
        
        if not current_price:
            raise serializers.ValidationError({'non_field_errors': 'خطا در دریافت قیمت طلا'})

        current_price = Decimal(str(current_price))

        # =============================================
        # اعتبارسنجی قیمت هدف (برای سفارش LIMIT)
        # =============================================
        if order_type == 'LIMIT':
            if not target_price:
                raise serializers.ValidationError({'target_price': 'قیمت هدف الزامی است'})
            
            target_price = Decimal(str(target_price))
            
            # قیمت هدف باید کمتر از قیمت فعلی باشد (فروش تعهدی)
            if target_price >= current_price:
                raise serializers.ValidationError({
                    'target_price': f'قیمت هدف باید کمتر از قیمت فعلی ({current_price}) باشد'
                })
            
            entry_price = target_price
        else:
            entry_price = current_price

        # =============================================
        # اعتبارسنجی حد سود و حد ضرر
        # =============================================
        if take_profit:
            take_profit = Decimal(str(take_profit))
            # حد سود باید کمتر از قیمت ورود باشد (فروش تعهدی)
            if take_profit >= entry_price:
                raise serializers.ValidationError({
                    'take_profit': f'حد سود باید کمتر از قیمت ورود ({entry_price}) باشد'
                })

        if stop_loss:
            stop_loss = Decimal(str(stop_loss))
            # حد ضرر باید بیشتر از قیمت ورود باشد (فروش تعهدی)
            if stop_loss <= entry_price:
                raise serializers.ValidationError({
                    'stop_loss': f'حد ضرر باید بیشتر از قیمت ورود ({entry_price}) باشد'
                })

        # =============================================
        # بررسی موجودی طلا
        # =============================================
        from .models import GoldInventory
        inventory, _ = GoldInventory.objects.get_or_create(user=user)
        
        # برای فروش تعهدی نیاز به موجودی طلا داریم
        if inventory.accessible_balance < weight:
            raise serializers.ValidationError({
                'weight': f'موجودی طلای شما ({inventory.accessible_balance} گرم) کافی نیست'
            })

        # =============================================
        # محاسبه مبلغ کل و کارمزد
        # =============================================
        # مبلغ کل = وزن × قیمت ورود × (1 - کارمزد)
        fee_rate = Decimal("0.01")  # 1%
        
        # قیمت خالص
        pure_price = (weight * entry_price).quantize(Decimal("1"))
        
        # کارمزد اولیه (1%)
        initial_fee = (pure_price * fee_rate).quantize(Decimal("1"))
        
        # مبلغ کل = قیمت خالص - کارمزد
        total_price = (pure_price - initial_fee).quantize(Decimal("1"))

        # ذخیره در attrs
        attrs['entry_price'] = entry_price
        attrs['fee_rate'] = fee_rate
        attrs['initial_fee'] = initial_fee
        attrs['total_price'] = total_price
        attrs['pure_price'] = pure_price

        return attrs


# =========================================================
# GOLD SHORT ORDER LIST SERIALIZER
# =========================================================
class GoldShortOrderListSerializer(serializers.ModelSerializer):
    """
    سریالایزر لیست سفارشات فروش تعهدی
    """
    order_type_display = serializers.CharField(source='get_order_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    leverage_display = serializers.SerializerMethodField()
    profit_loss_display = serializers.SerializerMethodField()

    class Meta:
        model = GoldShortOrder
        fields = [
            'id',
            'order_type',
            'order_type_display',
            'status',
            'status_display',
            'weight',
            'leverage',
            'leverage_display',
            'entry_price',
            'target_price',
            'take_profit',
            'stop_loss',
            'close_price',
            'profit_loss',
            'profit_loss_display',
            'initial_fee',
            'daily_fee',
            'total_fee',
            'description',
            'created_at',
            'updated_at',
            'closed_at'
        ]

    def get_leverage_display(self, obj):
        return f"{obj.leverage}x"

    def get_profit_loss_display(self, obj):
        if obj.profit_loss > 0:
            return f"+{obj.profit_loss}"
        return str(obj.profit_loss)



class GoldShortOrderHistorySerializer(serializers.ModelSerializer):
    """
    سریالایزر تاریخچه سفارش فروش تعهدی
    """
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = GoldShortOrderHistory
        fields = '__all__'
        
        
        
# gold_app/serializers.py - اضافه کردن سریالایزرهای تضمین طلا

from rest_framework import serializers
from django.utils import timezone
from decimal import Decimal
from .models import GoldGuarantee, GoldGuaranteePlan, GoldInventory, Wallet


class GoldGuaranteePlanSerializer(serializers.ModelSerializer):
    """سریالایزر طرح‌های تضمین طلا"""
    
    class Meta:
        model = GoldGuaranteePlan
        fields = [
            'id', 'name', 'duration_days', 'service_fee_percent',
            'is_active', 'description', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class GoldGuaranteeCreateSerializer(serializers.Serializer):
    """سریالایزر ایجاد تضمین طلا"""
    
    plan_id = serializers.IntegerField(required=True)
    gold_weight = serializers.DecimalField(max_digits=20, decimal_places=3, required=True)
    
    def validate_plan_id(self, value):
        try:
            plan = GoldGuaranteePlan.objects.get(id=value, is_active=True)
            return plan
        except GoldGuaranteePlan.DoesNotExist:
            raise serializers.ValidationError("طرح انتخاب شده نامعتبر یا غیرفعال است")
    
    def validate_gold_weight(self, value):
        if value <= 0:
            raise serializers.ValidationError("مقدار طلا باید بیشتر از صفر باشد")
        return value
    
    def validate(self, attrs):
        user = self.context.get('request').user
        plan = attrs.get('plan_id')
        gold_weight = attrs.get('gold_weight')
        
        # بررسی موجودی طلای در دسترس
        inventory, _ = GoldInventory.objects.get_or_create(user=user)
        if inventory.accessible_balance < gold_weight:
            raise serializers.ValidationError(
                {"gold_weight": f"موجودی طلای در دسترس شما ({inventory.accessible_balance} گرم) کافی نیست"}
            )
        
        # محاسبه کارمزد سرویس
        from gold_app.utils import get_live_gold_price
        gold_price = get_live_gold_price()
        if not gold_price:
            raise serializers.ValidationError("خطا در دریافت قیمت طلا")
        
        service_fee = (gold_weight * gold_price * (plan.service_fee_percent / Decimal('100'))).quantize(Decimal('1'))
        
        # بررسی موجودی کیف پول
        wallet, _ = Wallet.objects.get_or_create(user=user)
        if wallet.accessible_toman < service_fee:
            raise serializers.ValidationError(
                {"service_fee": f"موجودی کیف پول شما برای پرداخت کارمزد ({service_fee:,} تومان) کافی نیست"}
            )
        
        # ذخیره در context برای استفاده در create
        self.context['gold_price'] = gold_price
        self.context['service_fee'] = service_fee
        
        return attrs




# gold_app/serializers.py - سریالایزر لیست تضمین‌ها برای کاربر

class GoldGuaranteeListSerializer(serializers.ModelSerializer):
    """
    سریالایزر لیست تضمین‌های طلا برای کاربر
    """
    plan_name = serializers.CharField(source='plan.name', read_only=True)
    status_display = serializers.SerializerMethodField()
    end_date_shamsi = serializers.SerializerMethodField()
    days_remaining = serializers.SerializerMethodField()
    user_payout_display = serializers.SerializerMethodField()
    
    class Meta:
        model = GoldGuarantee
        fields = [
            'id',
            'plan', 
            'plan_name',
            'gold_weight',
            'guaranteed_price',
            'service_fee',
            'start_date',
            'end_date',
            'end_date_shamsi',
            'status',
            'status_display',
            'days_remaining',
            'is_expired',
            'user_payout',
            'user_payout_display',
            'description',
            'created_at',
            'updated_at'
        ]
    
    def get_status_display(self, obj):
        return obj.get_status_display()
    
    def get_end_date_shamsi(self, obj):
        import jdatetime
        if obj.end_date:
            shamsi = jdatetime.date.fromgregorian(date=obj.end_date)
            return shamsi.strftime("%Y/%m/%d")
        return None
    
    def get_days_remaining(self, obj):
        return obj.days_remaining
    
    def get_user_payout_display(self, obj):
        if obj.user_payout:
            return f"{int(obj.user_payout):,} تومان"
        return "۰ تومان"
# gold_app/serializers.py - سریالایزر جزئیات تضمین طلا برای کاربر

from rest_framework import serializers
from gold_app.models import GoldGuarantee
# gold_app/serializers.py - سریالایزر کامل GoldGuaranteeDetailSerializer

from rest_framework import serializers
from gold_app.models import GoldGuarantee
from django.utils import timezone

# ============================================
# gold_app/serializers.py - اصلاح شده
# ============================================

# gold_app/serializers.py - اصلاح GoldGuaranteeDetailSerializer

class GoldGuaranteeDetailSerializer(serializers.ModelSerializer):
    """
    سریالایزر جزئیات تضمین طلا برای کاربر
    """
    
    # فیلدهای طرح
    plan_name = serializers.CharField(source='plan.name', read_only=True)
    plan_duration_days = serializers.IntegerField(source='plan.duration_days', read_only=True)
    service_fee_percent = serializers.DecimalField(
        source='plan.service_fee_percent', 
        read_only=True, 
        max_digits=5, 
        decimal_places=2
    )
    
    # فیلدهای نمایشی
    status_display = serializers.SerializerMethodField()
    days_remaining = serializers.SerializerMethodField()
    start_date_shamsi = serializers.SerializerMethodField()
    end_date_shamsi = serializers.SerializerMethodField()
    
    # فیلدهای قابلیت‌ها
    can_cancel = serializers.SerializerMethodField()
    can_execute = serializers.SerializerMethodField()
    
    class Meta:
        model = GoldGuarantee
        fields = [
            'id',
            'tracking_code',
            'plan', 
            'plan_name', 
            'plan_duration_days',
            'service_fee_percent',
            'gold_weight',
            'guaranteed_price',
            'executed_price',
            'service_fee',
            'start_date',
            'start_date_shamsi',
            'end_date',
            'end_date_shamsi',
            'status',
            'status_display',
            'days_remaining',
            'is_expired',
            'cancelled_at',
            'executed_at',
            'user_payout',
            'profit_loss',
            'platform_profit',
            'can_cancel',
            'can_execute',
            'description',
            'created_at',
            'updated_at'
        ]
        # ✅ اصلاح: استفاده از لیست به جای '__all__'
        read_only_fields = [
            'id', 
            'tracking_code',
            'plan',
            'created_at', 
            'updated_at',
            'start_date',
            'end_date'
        ]
    
    def get_status_display(self, obj):
        return obj.get_status_display()
    
    def get_days_remaining(self, obj):
        if obj.is_expired:
            return 0
        delta = obj.end_date - timezone.now()
        if delta.total_seconds() < 86400:
            return 1
        return delta.days
    
    def get_start_date_shamsi(self, obj):
        if obj.start_date:
            import jdatetime
            from django.utils import timezone
            local_time = timezone.localtime(obj.start_date)
            shamsi = jdatetime.datetime.fromgregorian(datetime=local_time)
            return shamsi.strftime("%Y/%m/%d %H:%M")
        return None
    
    def get_end_date_shamsi(self, obj):
        if obj.end_date:
            import jdatetime
            from django.utils import timezone
            local_time = timezone.localtime(obj.end_date)
            shamsi = jdatetime.datetime.fromgregorian(datetime=local_time)
            return shamsi.strftime("%Y/%m/%d %H:%M")
        return None
    
    def get_can_cancel(self, obj):
        return obj.status == 'ACTIVE' and not obj.is_expired
    
    def get_can_execute(self, obj):
        return obj.status == 'ACTIVE' and obj.is_expired

# gold_app/serializers.py - اضافه کردن سریالایزرهای سرمایه‌گذاری

from rest_framework import serializers
from django.utils import timezone
from decimal import Decimal
from .models import GoldInvestment, GoldInvestmentPlan, GoldInventory

# gold_app/serializers.py - اصلاح GoldInvestmentPlanSerializer

# gold_app/serializers.py - سریالایزرهای سرمایه‌گذاری

from rest_framework import serializers
from .models import GoldInvestment, GoldInvestmentPlan, GoldInventory


class GoldInvestmentPlanSerializer(serializers.ModelSerializer):
    """سریالایزر طرح‌های سرمایه‌گذاری برای کاربر"""
    
    duration_display = serializers.SerializerMethodField()
    
    class Meta:
        model = GoldInvestmentPlan
        fields = [
            'id', 'name', 
            'duration_days', 'duration_display',
            'total_profit_percent',
            'is_active', 'description'
        ]
    
    def get_duration_display(self, obj):
        days = obj.duration_days
        if days == 1:
            return "۱ روز"
        elif days < 30:
            return f"{days} روز"
        elif days == 30:
            return "۱ ماه"
        elif days % 30 == 0:
            return f"{days // 30} ماه"
        else:
            return f"{days} روز"


class GoldInvestmentPreviewSerializer(serializers.Serializer):
    """سریالایزر پیش‌نمایش سرمایه‌گذاری"""
    
    plan_id = serializers.IntegerField(required=True)
    gold_weight = serializers.DecimalField(max_digits=20, decimal_places=3, required=True)
    
    def validate_plan_id(self, value):
        try:
            plan = GoldInvestmentPlan.objects.get(id=value, is_active=True)
            return plan
        except GoldInvestmentPlan.DoesNotExist:
            raise serializers.ValidationError("طرح انتخاب شده نامعتبر یا غیرفعال است")
    
    def validate_gold_weight(self, value):
        if value <= 0:
            raise serializers.ValidationError("مقدار طلا باید بیشتر از صفر باشد")
        return value
    
    def validate(self, attrs):
        user = self.context.get('request').user
        gold_weight = attrs.get('gold_weight')
        
        inventory, _ = GoldInventory.objects.get_or_create(user=user)
        if inventory.accessible_balance < gold_weight:
            raise serializers.ValidationError(
                {"gold_weight": f"موجودی طلای در دسترس شما ({inventory.accessible_balance} گرم) کافی نیست"}
            )
        
        return attrs


class GoldInvestmentCreateSerializer(serializers.Serializer):
    """سریالایزر ایجاد سرمایه‌گذاری"""
    
    plan_id = serializers.IntegerField(required=True)
    gold_weight = serializers.DecimalField(max_digits=20, decimal_places=3, required=True)
    
    def validate_plan_id(self, value):
        try:
            plan = GoldInvestmentPlan.objects.get(id=value, is_active=True)
            return plan
        except GoldInvestmentPlan.DoesNotExist:
            raise serializers.ValidationError("طرح انتخاب شده نامعتبر یا غیرفعال است")
    
    def validate_gold_weight(self, value):
        if value <= 0:
            raise serializers.ValidationError("مقدار طلا باید بیشتر از صفر باشد")
        return value
    
    def validate(self, attrs):
        user = self.context.get('request').user
        gold_weight = attrs.get('gold_weight')
        
        inventory, _ = GoldInventory.objects.get_or_create(user=user)
        if inventory.accessible_balance < gold_weight:
            raise serializers.ValidationError(
                {"gold_weight": f"موجودی طلای در دسترس شما ({inventory.accessible_balance} گرم) کافی نیست"}
            )
        
        return attrs


class GoldInvestmentListSerializer(serializers.ModelSerializer):
    """سریالایزر لیست سرمایه‌گذاری‌ها برای کاربر"""
    
    plan_name = serializers.CharField(source='plan.name', read_only=True)
    plan_duration_days = serializers.IntegerField(source='plan.duration_days', read_only=True)
    status_display = serializers.SerializerMethodField()
    end_date_shamsi = serializers.SerializerMethodField()
    total_expected_profit = serializers.SerializerMethodField()
    total_return = serializers.SerializerMethodField()
    can_cancel = serializers.SerializerMethodField()
    days_passed = serializers.SerializerMethodField()
    remaining_days = serializers.SerializerMethodField()
    
    class Meta:
        model = GoldInvestment
        fields = [
            'id', 'plan', 'plan_name', 'plan_duration_days',
            'gold_weight', 'investment_price',
            'start_date', 'end_date', 'end_date_shamsi',
            'status', 'status_display',
            'total_expected_profit', 'paid_profit',
            'total_return', 'days_passed', 'remaining_days',
            'cancellation_profit', 'can_cancel'
        ]
    
    def get_status_display(self, obj):
        return obj.get_status_display()
    
    def get_end_date_shamsi(self, obj):
        import jdatetime
        if obj.end_date:
            shamsi = jdatetime.date.fromgregorian(date=obj.end_date)
            return shamsi.strftime("%Y/%m/%d")
        return None
    
    def get_total_expected_profit(self, obj):
        return float(obj.total_expected_profit)
    
    def get_total_return(self, obj):
        return float(obj.total_return_amount)
    
    def get_can_cancel(self, obj):
        return obj.status == 'ACTIVE'
    
    def get_days_passed(self, obj):
        return obj.days_passed
    
    def get_remaining_days(self, obj):
        return obj.remaining_days


class GoldInvestmentDetailSerializer(serializers.ModelSerializer):
    """سریالایزر جزئیات سرمایه‌گذاری برای کاربر"""
    
    plan_name = serializers.CharField(source='plan.name', read_only=True)
    plan_duration_days = serializers.IntegerField(source='plan.duration_days', read_only=True)
    total_profit_percent = serializers.DecimalField(source='plan.total_profit_percent', read_only=True, max_digits=10, decimal_places=2)
    status_display = serializers.SerializerMethodField()
    end_date_shamsi = serializers.SerializerMethodField()
    total_expected_profit = serializers.SerializerMethodField()
    total_return = serializers.SerializerMethodField()
    can_cancel = serializers.SerializerMethodField()
    days_passed = serializers.SerializerMethodField()
    remaining_days = serializers.SerializerMethodField()
    
    class Meta:
        model = GoldInvestment
        fields = [
            'id', 'plan', 'plan_name', 'plan_duration_days',
            'total_profit_percent',
            'gold_weight', 'investment_price',
            'start_date', 'end_date', 'end_date_shamsi',
            'status', 'status_display',
            'total_expected_profit', 'paid_profit',
            'total_return', 'days_passed', 'remaining_days',
            'cancellation_profit', 'can_cancel', 'is_completed',
            'description', 'created_at', 'updated_at'
        ]
    
    def get_status_display(self, obj):
        return obj.get_status_display()
    
    def get_end_date_shamsi(self, obj):
        import jdatetime
        if obj.end_date:
            shamsi = jdatetime.date.fromgregorian(date=obj.end_date)
            return shamsi.strftime("%Y/%m/%d")
        return None
    
    def get_total_expected_profit(self, obj):
        return float(obj.total_expected_profit)
    
    def get_total_return(self, obj):
        return float(obj.total_return_amount)
    
    def get_can_cancel(self, obj):
        return obj.status == 'ACTIVE'
    
    def get_days_passed(self, obj):
        return obj.days_passed
    
    def get_remaining_days(self, obj):
        return obj.remaining_days
# gold_app/serializers.py
# gold_app/serializers.py - اصلاح InvoiceSerializer

class InvoiceSerializer(serializers.ModelSerializer):
    """سریالایزر فاکتور"""
    
    invoice_type_display = serializers.SerializerMethodField()
    status_display = serializers.SerializerMethodField()
    created_at_jalali = serializers.SerializerMethodField()
    
    class Meta:
        model = Invoice
        fields = [
            'id', 'invoice_number', 'invoice_type', 'invoice_type_display',
            'invoice_date', 'status', 'status_display', 'created_at_jalali',
            'buyer_name', 'buyer_national_id', 'buyer_phone', 'buyer_address',
            'seller_name', 'seller_address',  # ✅ فقط نام و آدرس
            'gold_weight', 'gold_carat', 'gold_price_per_gram',
            'pure_gold_price', 'fee_rate', 'fee_amount', 'total_amount',
            'tracking_code', 'description',
        ]
    
    def get_invoice_type_display(self, obj):
        return obj.get_invoice_type_display()
    
    def get_status_display(self, obj):
        return obj.get_status_display()
    
    def get_created_at_jalali(self, obj):
        import jdatetime
        from django.utils import timezone
        if obj.created_at:
            local_time = timezone.localtime(obj.created_at)
            shamsi = jdatetime.datetime.fromgregorian(datetime=local_time)
            return shamsi.strftime('%Y/%m/%d %H:%M')
        return None
    
    
    
# gold_app/serializers.py - اضافه کردن AppVersionSerializer

from rest_framework import serializers
from .models import AppVersion


class AppVersionSerializer(serializers.ModelSerializer):
    """سریالایزر نسخه اپلیکیشن"""
    
    class Meta:
        model = AppVersion
        fields = [
            'id',
            'version_code',
            'version_name',
            'min_required_version_code',
            'update_message',
            'release_notes',
            'store_url',
            'is_active',
            'is_force_update',
            'release_date',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'release_date', 'created_at', 'updated_at']