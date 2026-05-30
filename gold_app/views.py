# gold_app/views.py

from decimal import Decimal
from rest_framework.parsers import MultiPartParser, FormParser
from django.db import transaction
from django.db.models import Q, Sum
from django.utils import timezone

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import (
    IsAuthenticated,
    AllowAny
)
from rest_framework.response import Response

from drf_spectacular.utils import extend_schema

from accounts.models import BankCard, FeeSetting, ReferralEarning

from accounts.utils import apply_referral_bonus
from silver_app.models import (
    SilverInventory
)

from .models import (
    AutoSavingPlan,
    GiftCard,
    GiftCardOrder,
    GoldInventory,
    GoldOrder,
    GoldTransaction,
    UserAddress,
    Wallet,
    FinancialTransaction,
    Product,
    Order,
    OrderItem,
    PriceAlert
)

from .serializers import (
    AutoSavingPlanSerializer,
    GiftCardOrderSerializer,
    GiftCardSerializer,
    GoldOrderSerializer,
    PhysicalOrderSerializer,
    ProductSerializer,
    OrderSerializer,
    PriceAlertSerializer,
    FinancialTransactionSerializer,
    GoldTransactionSerializer,
    BuyGoldSerializer,
    ReferralEarningSerializer,
    SellGoldSerializer,
    DepositSerializer,
    UserAddressSerializer,
    WithdrawSerializer
    )

from .utils import (
    get_latest_price,
    get_live_gold_price,
    generate_tracking_code,
    get_gold_chart_data,
    filter_by_date,
    filter_by_status
)




# =========================================================
# SUCCESS RESPONSE
# =========================================================

def success_response(
    message="عملیات موفق بود",
    data=None,
    status_code=status.HTTP_200_OK
):

    return Response(
        {
            "success": True,
            "message": message,
            "data": data or {}
        },
        status=status_code
    )
# =========================================================
# ERROR RESPONSE
# =========================================================

def error_response(
    message="خطایی رخ داده است",
    status_code=status.HTTP_400_BAD_REQUEST,
    data=None
):

    response_data = data or {}

    final_message = message

    if isinstance(response_data, dict):

        # non field errors
        if "non_field_errors" in response_data:
            err = response_data["non_field_errors"]
            final_message = err[0] if isinstance(err, list) else err

        # message field
        elif "message" in response_data:
            err = response_data["message"]
            final_message = err[0] if isinstance(err, list) else err

        # first field error
        else:
            for v in response_data.values():
                if isinstance(v, list) and v:
                    final_message = v[0]
                    break
                elif isinstance(v, str):
                    final_message = v
                    break

    return Response(
        {
            "success": False,
            "message": str(final_message),
            "data": {}   # 👈 همیشه تمیز
        },
        status=status_code
    )

# =========================================================
# DASHBOARD
# =========================================================

class GoldDashboardAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        user = request.user

        inventory, _ = GoldInventory.objects.get_or_create(
            user=user
        )

        wallet, _ = Wallet.objects.get_or_create(
            user=user
        )

        gold_price = get_live_gold_price()

        gold_balance = Decimal(str(inventory.balance))
        toman_balance = Decimal(str(wallet.balance))

        gold_value = gold_balance * gold_price

        total_assets = gold_value + toman_balance

        return success_response(
            message='اطلاعات داشبورد دریافت شد',
            data={
                "gold_balance_gr": round(gold_balance, 5),
                "toman_balance": round(toman_balance),
                "gold_price": round(gold_price),
                "gold_value": round(gold_value),
                "total_assets": round(total_assets)
            }
        )


# =========================================================
# USER BALANCE
# =========================================================

class UserBalanceAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        inventory, _ = GoldInventory.objects.get_or_create(
            user=request.user
        )

        wallet, _ = Wallet.objects.get_or_create(
            user=request.user
        )

        gold_price = get_live_gold_price()

        total_assets = (
            inventory.balance * gold_price
        ) + wallet.balance

        return success_response(
            message='موجودی دریافت شد',
            data={
                "gold_balance_gr": inventory.balance,
                "toman_balance": wallet.balance,
                "current_gold_price": gold_price,
                "total_assets": round(total_assets)
            }
        )


# =========================================================
# GOLD CHART
# =========================================================

class GoldChartAPIView(APIView):

    permission_classes = [AllowAny]

    def get(self, request):

        filter_type = request.GET.get(
            'filter',
            '24H'
        )

        chart_data = get_gold_chart_data(
            filter_type
        )

        return success_response(
            message='اطلاعات نمودار دریافت شد',
            data=chart_data
        )


# =========================================================
# BUY GOLD
# =========================================================

class BuyGoldAPIView(APIView):

    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):

        serializer = BuyGoldSerializer(data=request.data)

        if not serializer.is_valid():
            return error_response(data=serializer.errors)

        user = request.user

        toman = serializer.validated_data.get("toman")
        weight_input = serializer.validated_data.get("weight")
        payment_method = serializer.validated_data.get("payment_method")

        gold_price = get_live_gold_price()

        if not gold_price:
            return error_response(message="خطا در دریافت قیمت طلا", status_code=500)

        # ======================
        # FEE FROM SETTINGS
        # ======================
        fee_setting = FeeSetting.objects.first()
        fee_rate = fee_setting.gold_fee if fee_setting else Decimal("0.0099")

        # ======================
        # CALCULATION
        # ======================
        if toman:

            total_toman = Decimal(str(toman))
            fee = total_toman * fee_rate
            net = total_toman - fee

            weight = (net / gold_price).quantize(Decimal("0.0001"))

        else:

            weight = Decimal(str(weight_input)).quantize(Decimal("0.0001"))

            pure = weight * gold_price
            fee = pure * fee_rate
            total_toman = pure + fee

        # ======================
        # WALLET
        # ======================
        wallet, _ = Wallet.objects.get_or_create(user=user)

        if payment_method == "WALLET":

            if wallet.balance < total_toman:
                return error_response(message="موجودی کافی نیست")

            wallet.balance -= total_toman
            wallet.save()

        elif payment_method == "GATEWAY":

            FinancialTransaction.objects.create(
                user=user,
                amount=total_toman,
                type="DEPOSIT",
                method="ONLINE",
                status="COMPLETED",
                tracking_code=generate_tracking_code("PAY"),
                description="پرداخت خرید طلا"
            )

        else:
            return error_response(message="روش پرداخت نامعتبر است")

        # ======================
        # INVENTORY
        # ======================
        inventory, _ = GoldInventory.objects.get_or_create(user=user)
        inventory.balance += weight
        inventory.save()

        # ======================
        # TRANSACTION (PENDING)
        # ======================
        tx = GoldTransaction.objects.create(
            user=user,
            type="BUY",
            status="PENDING",
            amount_gr=weight,
            price_per_gram=gold_price,
            fee=fee,
            total_amount=total_toman,
            tracking_code=generate_tracking_code("BUY")
        )

        # ======================
        # REFERRAL BONUS
        # ======================
        apply_referral_bonus(user, total_toman, "GOLD")

        return success_response(
            message="خرید طلا ثبت شد و در انتظار تایید است",
            status_code=201,
            data={
                "transaction_id": tx.id,
                "tracking_code": tx.tracking_code,
                "gold_weight": float(weight),
                "paid_amount": float(total_toman),
                "wallet_balance": float(wallet.balance)
            }
        )




# =========================================================
# SELL GOLD
# =========================================================

class SellGoldAPIView(APIView):

    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):

        serializer = SellGoldSerializer(
            data=request.data
        )

        if not serializer.is_valid():

            return error_response(
                message='اطلاعات نامعتبر است',
                data=serializer.errors
            )

        user = request.user

        toman = serializer.validated_data.get(
            'toman'
        )

        weight = serializer.validated_data.get(
            'weight'
        )

        gold_price = get_live_gold_price()

        inventory, _ = GoldInventory.objects.get_or_create(
            user=user
        )

        wallet, _ = Wallet.objects.get_or_create(
            user=user
        )

        fee_rate = Decimal('0.99')

        if toman:

            toman = Decimal(str(toman))

            final_weight = (
                toman / gold_price
            )

            fee = toman * fee_rate

            final_amount = toman - fee

        else:

            final_weight = Decimal(str(weight))

            pure_price = (
                final_weight * gold_price
            )

            fee = pure_price * fee_rate

            final_amount = pure_price - fee

        if inventory.balance < final_weight:

            return error_response(
                message='موجودی طلا کافی نیست'
            )

        inventory.balance -= final_weight
        inventory.save()

        wallet.balance += final_amount
        wallet.save()

        transaction_obj = GoldTransaction.objects.create(
            user=user,
            type='SELL',
            status='COMPLETED',
            amount_gr=final_weight,
            price_per_gram=gold_price,
            fee=fee,
            total_amount=final_amount,
            tracking_code=generate_tracking_code(
                'SELL'
            )
        )

        return success_response(
            message='فروش طلا انجام شد',
            data={
                "transaction_id": transaction_obj.id,
                "tracking_code": transaction_obj.tracking_code,
                "wallet_balance": round(wallet.balance)
            }
        )






# =========================================================
# DEPOSIT WALLET
# =========================================================

from rest_framework.parsers import MultiPartParser, FormParser


class DepositAPIView(APIView):

    permission_classes = [IsAuthenticated]

    parser_classes = [
        MultiPartParser,
        FormParser
    ]

    @extend_schema(
        tags=['Wallet'],
        request=DepositSerializer,
        summary='واریز کیف پول'
    )
    @transaction.atomic
    def post(self, request):

        try:

            serializer = DepositSerializer(
                data=request.data
            )

            if not serializer.is_valid():

                return error_response(
                    message='اطلاعات نامعتبر است',
                    data=serializer.errors
                )

            user = request.user

            amount = serializer.validated_data.get(
                'amount'
            )

            method = serializer.validated_data.get(
                'method'
            )

            receipt = serializer.validated_data.get(
                'receipt'
            )

            wallet, _ = Wallet.objects.get_or_create(
                user=user
            )

            # =====================================
            # RECEIPT METHOD
            # =====================================

            if method == 'RECEIPT':

                if not receipt:

                    return error_response(
                        message='تصویر رسید الزامی است'
                    )

                transaction_obj = FinancialTransaction.objects.create(
                    user=user,
                    amount=amount,
                    type='DEPOSIT',
                    method='CARD_TO_CARD',
                    status='PENDING',
                    receipt_image=receipt,
                    tracking_code=generate_tracking_code(
                        'DEP'
                    ),
                    description='واریز کارت به کارت'
                )

                return success_response(
                    message='درخواست واریز ثبت شد و در انتظار تایید است',
                    status_code=201,
                    data={
                        "transaction_id": transaction_obj.id,
                        "tracking_code": transaction_obj.tracking_code,
                        "status": "PENDING"
                    }
                )

            # =====================================
            # GATEWAY METHOD
            # =====================================

            elif method == 'GATEWAY':

                transaction_obj = FinancialTransaction.objects.create(
                    user=user,
                    amount=amount,
                    type='DEPOSIT',
                    method='ONLINE',
                    status='COMPLETED',
                    tracking_code=generate_tracking_code(
                        'PAY'
                    ),
                    description='واریز با درگاه پرداخت'
                )

                wallet.balance += amount
                wallet.save()

                return success_response(
                    message='واریز با موفقیت انجام شد',
                    status_code=201,
                    data={
                        "transaction_id": transaction_obj.id,
                        "tracking_code": transaction_obj.tracking_code,
                        "wallet_balance": round(wallet.balance),
                        "status": "COMPLETED"
                    }
                )

            return error_response(
                message='روش واریز نامعتبر است'
            )

        except Exception as e:

            return error_response(
                message=str(e),
                status_code=500
            )
# =========================================================
# WITHDRAW
# =========================================================

class WithdrawAPIView(APIView):

    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):

        serializer = WithdrawSerializer(
            data=request.data,
            context={'request': request}
        )

        if not serializer.is_valid():

            return error_response(
                message='اطلاعات نامعتبر است',
                data=serializer.errors
            )

        user = request.user

        amount = serializer.validated_data.get(
            'amount'
        )

        target = serializer.validated_data.get(
            'target'
        )

        wallet, _ = Wallet.objects.get_or_create(
            user=user
        )

        if wallet.balance < amount:

            return error_response(
                message='موجودی کیف پول کافی نیست'
            )

        # =====================================================
        # BANK WITHDRAW
        # =====================================================

        if target == 'BANK':

            card = serializer.validated_data.get(
                'card'
            )

            wallet.balance -= amount
            wallet.save()

            transaction_obj = FinancialTransaction.objects.create(
                user=user,
                amount=amount,
                type='WITHDRAW',
                method='BANK',
                status='PENDING',
                user_card=card,
                tracking_code=generate_tracking_code(
                    'WDB'
                ),
                admin_note='در انتظار تسویه بانکی',
                description=f'''
برداشت بانکی
کارت: {card.card_number}
بانک: {card.bank_name}
'''
            )

            return success_response(
                message='درخواست برداشت ثبت شد',
                data={
                    "transaction_id": transaction_obj.id,
                    "tracking_code": transaction_obj.tracking_code,
                    "status": transaction_obj.status,
                    "wallet_balance": round(wallet.balance),
                    "card_number": card.card_number
                }
            )

        # =====================================================
        # CONVERT TO SILVER
        # =====================================================

        elif target == 'SILVER':

            silver_price = Decimal('1')

            silver_inventory, _ = SilverInventory.objects.get_or_create(
                user=user
            )

            silver_weight = amount / silver_price

            wallet.balance -= amount
            wallet.save()

            silver_inventory.balance += silver_weight
            silver_inventory.save()

            transaction_obj = FinancialTransaction.objects.create(
                user=user,
                amount=amount,
                type='CONVERT',
                method='SILVER',
                status='COMPLETED',
                tracking_code=generate_tracking_code(
                    'SLV'
                ),
                admin_note='تبدیل ریال به نقره',
                description='تبدیل موجودی کیف پول به نقره'
            )

            return success_response(
                message='تبدیل به نقره انجام شد',
                data={
                    "transaction_id": transaction_obj.id,
                    "tracking_code": transaction_obj.tracking_code,
                    "silver_weight": round(silver_weight, 5),
                    "wallet_balance": round(wallet.balance)
                }
            )

        return error_response(
            message='نوع برداشت نامعتبر است'
        )


# =========================================================
# PRODUCTS
# =========================================================

class ProductListAPIView(APIView):

    permission_classes = [AllowAny]

    def get(self, request):

        queryset = Product.objects.filter(
            is_active=True
        ).select_related('category').order_by('-created_at')

        category = request.GET.get("category")
        delivery_type = request.GET.get("delivery_type")

        if category:
            queryset = queryset.filter(category__slug=category)

        if delivery_type:
            queryset = queryset.filter(delivery_type=delivery_type)

        serializer = ProductSerializer(queryset, many=True)

        return success_response(
            message="محصولات دریافت شد",
            data=serializer.data
        )
# =========================================================




class PhysicalOrderAPIView(APIView):

    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):

        serializer = PhysicalOrderSerializer(data=request.data)

        if not serializer.is_valid():
            return error_response(data=serializer.errors)

        user = request.user

        # =========================
        # PRODUCT CHECK
        # =========================
        try:
            product = Product.objects.get(
                id=serializer.validated_data["product_id"],
                is_active=True
            )
        except Product.DoesNotExist:
            return error_response(message="محصول یافت نشد")

        quantity = serializer.validated_data["quantity"]

        if product.inventory_count < quantity:
            return error_response(message="موجودی کافی نیست")

        # =========================
        # CALCULATION
        # =========================
        total_gold = product.total_weight_with_fees * quantity
        total_toman = product.buy_price * quantity

        payment_method = serializer.validated_data["payment_method"]

        wallet, _ = Wallet.objects.get_or_create(user=user)
        inventory, _ = GoldInventory.objects.get_or_create(user=user)

        # =========================
        # PAYMENT
        # =========================
        if payment_method == "TOMAN":

            if wallet.balance < total_toman:
                return error_response(message="موجودی کیف پول کافی نیست")

            wallet.balance -= total_toman
            wallet.save()

        else:

            if inventory.balance < total_gold:
                return error_response(message="موجودی طلا کافی نیست")

            inventory.balance -= total_gold
            inventory.save()

        # =========================
        # ADDRESS HANDLING (FIXED)
        # =========================
        address = None

        address_id = serializer.validated_data.get("address_id")

        if address_id:

            address = UserAddress.objects.filter(
                id=address_id,
                user=user
            ).first()

            if not address:
                return error_response(
                    message="آدرس یافت نشد",
                    data={
                        "address_id": address_id,
                        "user_id": user.id
                    }
                )

        # =========================
        # SET ADDRESS DATA
        # =========================
        if address:

            province = address.province
            city = address.city
            full_address = address.address
            postal_code = address.postal_code
            plaque = address.plaque
            unit = address.unit

        else:

            province = serializer.validated_data["province"]
            city = serializer.validated_data["city"]
            full_address = serializer.validated_data["address"]
            postal_code = serializer.validated_data.get("postal_code")
            plaque = serializer.validated_data.get("plaque")
            unit = serializer.validated_data.get("unit")

            # =========================
            # AUTO SAVE NEW ADDRESS
            # =========================
            address = UserAddress.objects.create(
                user=user,
                province=province,
                city=city,
                address=full_address,
                postal_code=postal_code,
                plaque=plaque,
                unit=unit,
            )

        # =========================
        # CREATE ORDER
        # =========================
        order = Order.objects.create(
            user=user,
            province=province,
            city=city,
            address=full_address,
            postal_code=postal_code,
            plaque=plaque,
            unit=unit,
            payment_method=payment_method,
            delivery_type=serializer.validated_data["delivery_type"],
            total_gold_amount=total_gold,
            total_toman_amount=total_toman,
            tracking_code=generate_tracking_code("ORD"),
            status="PENDING"
        )

        OrderItem.objects.create(
            order=order,
            product=product,
            quantity=quantity,
            price_at_time=product.buy_price,
            weight_at_time=product.total_weight_with_fees
        )

        product.inventory_count -= quantity
        product.save()

        return success_response(
            message="سفارش با موفقیت ثبت شد",
            status_code=201,
            data={
                "order_id": order.id,
                "tracking_code": order.tracking_code,
                "total_price": int(total_toman),
                "total_gold": float(total_gold)
            }
        )
    

class UserAddressListAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        addresses = UserAddress.objects.filter(
            user=request.user
        ).order_by("-created_at")

        serializer = UserAddressSerializer(addresses, many=True)

        return success_response(
            message="لیست آدرس‌ها دریافت شد",
            data=serializer.data
        )



# =========================================================
# ORDER HISTORY
# =========================================================

class OrderHistoryAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        queryset = Order.objects.filter(
            user=request.user
        ).order_by('-created_at')

        serializer = OrderSerializer(
            queryset,
            many=True
        )

        return success_response(
            message='سفارشات دریافت شد',
            data=serializer.data
        )


# =========================================================
# PRICE ALERT
# =========================================================

class PriceAlertAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        queryset = PriceAlert.objects.filter(
            user=request.user
        ).order_by('-created_at')

        serializer = PriceAlertSerializer(
            queryset,
            many=True
        )

        return success_response(
            message='هشدارها دریافت شد',
            data=serializer.data
        )

    def post(self, request):

        serializer = PriceAlertSerializer(
            data=request.data
        )

        if not serializer.is_valid():

            return error_response(
                message='اطلاعات نامعتبر است',
                data=serializer.errors
            )

        serializer.save(
            user=request.user
        )

        return success_response(
            message='هشدار ثبت شد',
            data=serializer.data,
            status_code=201
        )


# =========================================================
# DELETE PRICE ALERT
# =========================================================

class DeletePriceAlertAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):

        try:

            alert = PriceAlert.objects.get(
                id=pk,
                user=request.user
            )

        except PriceAlert.DoesNotExist:

            return error_response(
                message='هشدار یافت نشد',
                status_code=404
            )

        alert.delete()

        return success_response(
            message='هشدار حذف شد'
        )


# =========================================================
# REPORTS
# =========================================================

class ReportsAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        report_type = request.GET.get(
            'type'
        )

        status_filter = request.GET.get(
            'status'
        )

        start_date = request.GET.get(
            'start_date'
        )

        end_date = request.GET.get(
            'end_date'
        )

        # =====================================================
        # GOLD REPORT
        # =====================================================

        if report_type == 'gold':

            queryset = GoldTransaction.objects.filter(
                user=request.user
            ).order_by('-created_at')

            if status_filter:

                queryset = queryset.filter(
                    status=status_filter
                )

            if start_date:

                queryset = queryset.filter(
                    created_at__date__gte=start_date
                )

            if end_date:

                queryset = queryset.filter(
                    created_at__date__lte=end_date
                )

            serializer = GoldTransactionSerializer(
                queryset,
                many=True
            )

            return success_response(
                message='گزارش معاملات طلا',
                data=serializer.data
            )

        # =====================================================
        # DEPOSIT REPORT
        # =====================================================

        elif report_type == 'deposit':

            queryset = FinancialTransaction.objects.filter(
                user=request.user,
                type='DEPOSIT'
            ).order_by('-created_at')

            if status_filter:

                queryset = queryset.filter(
                    status=status_filter
                )

            if start_date:

                queryset = queryset.filter(
                    created_at__date__gte=start_date
                )

            if end_date:

                queryset = queryset.filter(
                    created_at__date__lte=end_date
                )

            serializer = FinancialTransactionSerializer(
                queryset,
                many=True
            )

            return success_response(
                message='گزارش واریزها',
                data=serializer.data
            )

        # =====================================================
        # WITHDRAW REPORT
        # =====================================================

        elif report_type == 'withdraw':

            queryset = FinancialTransaction.objects.filter(
                user=request.user,
                type='WITHDRAW'
            ).order_by('-created_at')

            if status_filter:

                queryset = queryset.filter(
                    status=status_filter
                )

            if start_date:

                queryset = queryset.filter(
                    created_at__date__gte=start_date
                )

            if end_date:

                queryset = queryset.filter(
                    created_at__date__lte=end_date
                )

            serializer = FinancialTransactionSerializer(
                queryset,
                many=True
            )

            return success_response(
                message='گزارش برداشت‌ها',
                data=serializer.data
            )

        # =====================================================
        # ORDERS REPORT
        # =====================================================

        elif report_type == 'orders':

            queryset = Order.objects.filter(
                user=request.user
            ).order_by('-created_at')

            if status_filter:

                queryset = queryset.filter(
                    status=status_filter
                )

            if start_date:

                queryset = queryset.filter(
                    created_at__date__gte=start_date
                )

            if end_date:

                queryset = queryset.filter(
                    created_at__date__lte=end_date
                )

            serializer = OrderSerializer(
                queryset,
                many=True
            )

            return success_response(
                message='گزارش سفارشات',
                data=serializer.data
            )

        return error_response(
            message='نوع گزارش نامعتبر است'
        )

# =========================================================
# RECENT TRANSACTIONS
# =========================================================

class RecentTransactionsAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        queryset = FinancialTransaction.objects.filter(
            user=request.user
        ).order_by('-created_at')[:10]

        serializer = FinancialTransactionSerializer(
            queryset,
            many=True
        )

        return success_response(
            message='تراکنش ها دریافت شد',
            data=serializer.data
        )


# =========================================================
# RECENT DELIVERIES
# =========================================================

class RecentDeliveriesAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        queryset = Order.objects.filter(
            user=request.user
        ).order_by('-created_at')[:10]

        serializer = OrderSerializer(
            queryset,
            many=True
        )

        return success_response(
            message='تحویل ها دریافت شد',
            data=serializer.data
        )


# =========================================================
# REFERRAL DASHBOARD
# =========================================================

class ReferralDashboardAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        user = request.user

        total_invited = user.subscribers.count()

        total_earned = ReferralEarning.objects.filter(
            referrer=user
        ).aggregate(
            total=Sum('amount')
        )['total'] or 0

        recent_earnings = ReferralEarning.objects.filter(
            referrer=user
        ).order_by('-transaction_date')[:10]

        serializer = ReferralEarningSerializer(
            recent_earnings,
            many=True
        )

        referral_link = (
            f"https://gold.darine.shop/register?"
            f"ref={user.referral_code}"
        )

        return success_response(
            message='اطلاعات دعوت دوستان دریافت شد',
            data={
                "referral_code": user.referral_code,
                "referral_link": referral_link,
                "total_invited": total_invited,
                "total_earned": int(total_earned),
                "recent_earnings": serializer.data
            }
        )
    


# =========================================================
# AUTO SAVING PLAN
# =========================================================

from datetime import timedelta
from django.utils import timezone


class AutoSavingPlanAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        plans = AutoSavingPlan.objects.filter(
            user=request.user
        ).order_by('-created_at')

        serializer = AutoSavingPlanSerializer(
            plans,
            many=True
        )

        return success_response(
            message='پلن های پس انداز دریافت شد',
            data=serializer.data
        )

    def post(self, request):

        saving_type = request.data.get('type')
        amount = request.data.get('amount')

        if not saving_type:

            return error_response(
                message='نوع پلن الزامی است'
            )

        if not amount:

            return error_response(
                message='مبلغ الزامی است'
            )

        # =====================================
        # PERIOD DAYS
        # =====================================

        if saving_type == 'DAILY':

            period_days = 1

        elif saving_type == 'WEEKLY':

            period_days = 7

        elif saving_type == 'MONTHLY':

            period_days = 30

        else:

            return error_response(
                message='نوع پلن نامعتبر است'
            )

        # =====================================
        # CREATE PLAN
        # =====================================

        plan = AutoSavingPlan.objects.create(
            user=request.user,
            type=saving_type,
            amount=amount,
            period_days=period_days,
            next_execute_at=timezone.now() + timedelta(days=period_days),
            status='ACTIVE'
        )

        serializer = AutoSavingPlanSerializer(
            plan
        )

        return success_response(
            message='پلن پس انداز ایجاد شد',
            data=serializer.data,
            status_code=201
        )

    def delete(self, request):

        plan_id = request.data.get(
            'plan_id'
        )

        try:

            plan = AutoSavingPlan.objects.get(
                id=plan_id,
                user=request.user
            )

        except AutoSavingPlan.DoesNotExist:

            return error_response(
                message='پلن یافت نشد'
            )

        plan.delete()

        return success_response(
            message='پلن حذف شد'
        )

# =========================================================
# GIFT CARD ORDER
# =========================================================

class GiftCardOrderAPIView(APIView):

    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):

        serializer = GiftCardOrderSerializer(
            data=request.data
        )

        if not serializer.is_valid():

            return error_response(
                message='اطلاعات نامعتبر است',
                data=serializer.errors
            )

        user = request.user

        wallet, _ = Wallet.objects.get_or_create(
            user=user
        )

        gold_price = get_live_gold_price()

        if not gold_price:

            return error_response(
                message='خطا در دریافت قیمت طلا'
            )

        weight_per_card = Decimal(
            str(
                serializer.validated_data[
                    'weight_per_card'
                ]
            )
        )

        quantity = serializer.validated_data[
            'quantity'
        ]

        total_weight = (
            weight_per_card * quantity
        )

        total_price = (
            total_weight * gold_price
        )

        if wallet.balance < total_price:

            return error_response(
                message='موجودی کیف پول کافی نیست'
            )

        # =====================================
        # ADDRESS
        # =====================================

        address_id = request.data.get(
            'address_id'
        )

        province = None
        city = None
        address = None
        postal_code = None
        plaque = None
        unit = None

        # =====================================
        # USE OLD ADDRESS
        # =====================================

        if address_id:

            old_order = Order.objects.filter(
                id=address_id,
                user=user
            ).first()

            old_gift = GiftCardOrder.objects.filter(
                id=address_id,
                user=user
            ).first()

            source = old_order or old_gift

            if not source:

                return error_response(
                    message='آدرس یافت نشد'
                )

            province = source.province
            city = source.city
            address = source.address
            postal_code = source.postal_code
            plaque = source.plaque
            unit = source.unit

        # =====================================
        # NEW ADDRESS
        # =====================================

        else:

            province = serializer.validated_data[
                'province'
            ]

            city = serializer.validated_data[
                'city'
            ]

            address = serializer.validated_data[
                'address'
            ]

            postal_code = serializer.validated_data.get(
                'postal_code'
            )

            plaque = serializer.validated_data.get(
                'plaque'
            )

            unit = serializer.validated_data.get(
                'unit'
            )

        # =====================================
        # WALLET
        # =====================================

        wallet.balance -= total_price
        wallet.save()

        # =====================================
        # CREATE ORDER
        # =====================================

        order = GiftCardOrder.objects.create(

            user=user,

            weight_per_card=weight_per_card,

            quantity=quantity,

            total_price=total_price,

            province=province,

            city=city,

            address=address,

            postal_code=postal_code,

            plaque=plaque,

            unit=unit,

            status='PENDING',

            tracking_code=generate_tracking_code(
                'GFT'
            )
        )

        # =====================================
        # CREATE CARDS
        # =====================================

        created_cards = []

        for i in range(quantity):

            serial = generate_tracking_code(
                'CARD'
            )

            card = GiftCard.objects.create(

                serial_number=serial,

                weight=weight_per_card,

                created_by=user,

                status='ACTIVE',

                is_used=False
            )

            created_cards.append({

                "serial_number": card.serial_number,

                "weight": card.weight
            })

        return success_response(

            message='سفارش کارت هدیه ثبت شد',

            status_code=201,

            data={

                "order_id": order.id,

                "tracking_code": order.tracking_code,

                "total_price": total_price,

                "cards": created_cards
            }
        )

class GiftCardOrderListAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        queryset = GiftCardOrder.objects.filter(
            user=request.user
        ).order_by('-created_at')

        serializer = GiftCardOrderSerializer(
            queryset,
            many=True
        )

        return success_response(
            message='لیست سفارشات کارت هدیه',
            data=serializer.data
        )
    

# =========================================================
# REDEEM GIFT CARD
# =========================================================

class RedeemGiftCardAPIView(APIView):

    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):

        serial = request.data.get(
            'serial_number'
        )

        if not serial:

            return error_response(
                message='کد کارت الزامی است'
            )

        try:

            card = GiftCard.objects.get(
                serial_number=serial,
                status='ACTIVE',
                is_used=False
            )

        except GiftCard.DoesNotExist:

            return error_response(
                message='کارت هدیه نامعتبر است'
            )

        inventory, _ = GoldInventory.objects.get_or_create(
            user=request.user
        )

        inventory.balance += card.weight
        inventory.save()

        card.is_used = True
        card.status = 'USED'
        card.activated_by = request.user
        card.used_at = timezone.now()
        card.save()

        return success_response(

            message='کارت هدیه فعال شد',

            data={

                "weight_added": card.weight,

                "new_balance": inventory.balance
            }
        )


# =========================================================
# GIFT CARD LIST
# =========================================================

class GiftCardListAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        queryset = GiftCard.objects.filter(

            Q(created_by=request.user)
            |
            Q(activated_by=request.user)

        ).order_by('-created_at')

        serializer = GiftCardSerializer(
            queryset,
            many=True
        )

        return success_response(
            message='لیست کارت هدیه',
            data=serializer.data
        )

# =========================================================
# USER ADDRESSES
# =========================================================

class UserAddressesAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        data = []

        # =====================================
        # PRODUCT ORDERS
        # =====================================

        orders = Order.objects.filter(
            user=request.user
        ).order_by('-created_at')

        for item in orders:

            data.append({

                "id": item.id,

                "type": "PRODUCT_ORDER",

                "province": item.province,

                "city": item.city,

                "address": item.address,

                "postal_code": item.postal_code,

                "plaque": item.plaque,

                "unit": item.unit
            })

        # =====================================
        # GIFT CARD ORDERS
        # =====================================

        gifts = GiftCardOrder.objects.filter(
            user=request.user
        ).order_by('-created_at')

        for item in gifts:

            data.append({

                "id": item.id,

                "type": "GIFT_CARD_ORDER",

                "province": item.province,

                "city": item.city,

                "address": item.address,

                "postal_code": item.postal_code,

                "plaque": item.plaque,

                "unit": item.unit
            })

        return success_response(
            message='آدرس‌ها دریافت شد',
            data=data
        )


class GoldOrderAPIView(APIView):

    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):

        serializer = GoldOrderSerializer(data=request.data)

        if not serializer.is_valid():
            return error_response(
                message="اطلاعات نامعتبر است",
                data=serializer.errors
            )

        user = request.user

        order_type = serializer.validated_data["order_type"]
        target_price = Decimal(serializer.validated_data["target_price"])

        amount_toman = serializer.validated_data.get("amount_toman")
        gold_weight = serializer.validated_data.get("gold_weight")

        fee_rate = Decimal("0.0099")  # 0.99%

        # ==============================
        # BUY ORDER (خرید در قیمت پایین)
        # ==============================
        if order_type == "BUY":

            if amount_toman:

                amount_toman = Decimal(amount_toman)

                fee = amount_toman * fee_rate
                net_amount = amount_toman - fee

                estimated_weight = net_amount / target_price

            else:

                estimated_weight = Decimal(gold_weight)

        # ==============================
        # SELL ORDER (فروش در قیمت بالا)
        # ==============================
        else:

            if gold_weight:

                estimated_weight = Decimal(gold_weight)
                gross_amount = estimated_weight * target_price

                fee = gross_amount * fee_rate
                net_amount = gross_amount - fee

            else:

                amount_toman = Decimal(amount_toman)

                fee = amount_toman * fee_rate
                net_amount = amount_toman - fee

                estimated_weight = amount_toman / target_price

        # ==============================
        # CREATE ORDER (PENDING)
        # ==============================
        order = GoldOrder.objects.create(
            user=user,
            order_type=order_type,
            target_price=target_price,
            amount_toman=amount_toman if amount_toman else None,
            gold_weight=gold_weight if gold_weight else None,
            estimated_weight=estimated_weight,
            status="PENDING"
        )

        return success_response(
            message="سفارش با موفقیت ثبت شد (در انتظار اجرا)",
            status_code=201,
            data={
                "order_id": order.id,
                "type": order_type,
                "target_price": str(target_price),
                "estimated_weight": str(round(estimated_weight, 4))
            }
        )
    

class LatestPriceAPIView(APIView):

    permission_classes = [AllowAny]

    def get(self, request):

        key = request.GET.get("key")

        if not key:
            return error_response(message="key الزامی است")

        price = get_latest_price(key)

        if not price:
            return error_response(message="قیمت یافت نشد")

        return success_response(
            message="آخرین قیمت دریافت شد",
            data=price
        )
    

