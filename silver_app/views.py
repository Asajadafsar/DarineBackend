# =========================================================
# SILVER APP VIEWS
# =========================================================

from datetime import datetime
from decimal import Decimal

from django.db import transaction
from django.db.models import Sum
from django.utils import timezone

import jdatetime
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

from drf_spectacular.utils import extend_schema

from accounts.models import BankCard, FeeSetting
from accounts.utils import apply_referral_bonus

# =========================
# SILVER MODELS
# =========================
from .models import (
    SilverBankInfo,
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

# =========================
# SILVER SERIALIZERS
# =========================
from .serializers import (
    SilverPhysicalOrderSerializer,
    SilverProductCategorySerializer,
    SilverWalletSerializer,
    SilverInventorySerializer,
    SilverTransactionSerializer,
    SilverFinancialTransactionSerializer,
    SilverProductSerializer,
    SilverOrderSerializer,
    SilverOrderItemSerializer,
    SilverPriceHistorySerializer,
    SilverReferralEarningSerializer,
    SilverRecentTransactionSerializer,
    SilverRecentDeliverySerializer,
    SilverDepositSerializer,
    BuySilverSerializer,
    SellSilverSerializer,
    SilverWithdrawSerializer,
    SilverUserBalanceSerializer,
    SilverChartSerializer,
    UserAddressSerializer
)

# =========================
# SILVER UTILS
# =========================
from .utils import (
    get_live_silver_price,
    generate_tracking_code,
    get_silver_chart_data,
    filter_by_date,
    filter_by_status,
    calculate_buy_silver,
    calculate_sell_silver
)


# =========================================================
# SUCCESS RESPONSE
# =========================================================

def success_response(
    message="عملیات موفق بود",
    data=None,
    status_code=status.HTTP_200_OK
):

    # فقط اگر None بود تصمیم بگیر
    if data is None:
        data = []

    return Response(
        {
            "success": True,
            "message": message,
            "data": data
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

        if "non_field_errors" in response_data:
            err = response_data["non_field_errors"]
            final_message = err[0] if isinstance(err, list) else err

        elif "message" in response_data:
            err = response_data["message"]
            final_message = err[0] if isinstance(err, list) else err

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
            "data": {}
        },
        status=status_code
    )


# =========================================================
# DASHBOARD
# =========================================================

class SilverDashboardAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        user = request.user

        wallet, _ = SilverWallet.objects.get_or_create(user=user)
        inventory, _ = SilverInventory.objects.get_or_create(user=user)

        silver_price = get_live_silver_price()

        silver_balance = Decimal(str(inventory.balance))
        toman_balance = Decimal(str(wallet.balance))

        silver_value = silver_balance * silver_price
        total_assets = silver_value + toman_balance

        return success_response(
            message="اطلاعات داشبورد دریافت شد",
            data={
                "silver_balance_gr": round(silver_balance, 5),
                "toman_balance": round(toman_balance),
                "silver_price": round(silver_price),
                "silver_value": round(silver_value),
                "total_assets": round(total_assets)
            }
        )


# =========================================================
# USER BALANCE
# =========================================================

class SilverUserBalanceAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        inventory, _ = SilverInventory.objects.get_or_create(user=request.user)
        wallet, _ = SilverWallet.objects.get_or_create(user=request.user)

        silver_price = get_live_silver_price()

        total_assets = (inventory.balance * silver_price) + wallet.balance

        return success_response(
            message="موجودی دریافت شد",
            data={
                "silver_balance_gr": inventory.balance,
                "toman_balance": wallet.balance,
                "current_silver_price": silver_price,
                "total_assets": round(total_assets)
            }
        )


# =========================================================
# SILVER CHART
# =========================================================

class SilverChartAPIView(APIView):

    permission_classes = [AllowAny]

    def get(self, request):

        filter_type = request.GET.get("filter", "24H")

        chart_data = get_silver_chart_data(filter_type)

        return success_response(
            message="اطلاعات نمودار دریافت شد",
            data=chart_data
        )
    


# =========================================================
# BUY SILVER
# =========================================================

class BuySilverAPIView(APIView):

    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):

        serializer = BuySilverSerializer(data=request.data)

        if not serializer.is_valid():
            return error_response(data=serializer.errors)

        user = request.user

        toman = serializer.validated_data.get("toman")
        weight_input = serializer.validated_data.get("weight")
        payment_method = serializer.validated_data.get("payment_method")

        silver_price = get_live_silver_price()

        if not silver_price:
            return error_response(
                message="خطا در دریافت قیمت نقره",
                status_code=500
            )

        # ======================
        # FEE
        # ======================
        fee_rate = Decimal("0.0099")

        # ======================
        # CALCULATION
        # ======================
        if toman:

            total_toman = Decimal(str(toman))
            fee = total_toman * fee_rate
            net = total_toman - fee

            weight = (net / silver_price).quantize(Decimal("0.0001"))

        else:

            weight = Decimal(str(weight_input)).quantize(Decimal("0.0001"))

            pure = weight * silver_price
            fee = pure * fee_rate
            total_toman = pure + fee

        # ======================
        # WALLET
        # ======================
        wallet, _ = SilverWallet.objects.get_or_create(user=user)

        if payment_method == "WALLET":

            if wallet.balance < total_toman:
                return error_response(message="موجودی کافی نیست")

            wallet.balance -= total_toman
            wallet.save()

        elif payment_method == "GATEWAY":

            SilverFinancialTransaction.objects.create(
                user=user,
                amount=total_toman,
                type="DEPOSIT",
                method="ONLINE",
                status="PENDING",
                tracking_code=generate_tracking_code("SLV_PAY"),
                description="پرداخت خرید نقره"
            )

        else:
            return error_response(message="روش پرداخت نامعتبر است")

        # ======================
        # INVENTORY
        # ======================
        inventory, _ = SilverInventory.objects.get_or_create(user=user)
        inventory.balance += weight
        inventory.save()

        # ======================
        # TRANSACTION
        # ======================
        tx = SilverTransaction.objects.create(
            user=user,
            type="BUY",
            status="PENDING",
            amount_gr=weight,
            price_per_gram=silver_price,
            fee=fee,
            total_amount=total_toman,
            tracking_code=generate_tracking_code("BUY_SLV")
        )

        return success_response(
            message="خرید  نقره ثبت شد و در انتظار تایید است",
            status_code=201,
            data={
                "transaction_id": tx.id,
                "tracking_code": tx.tracking_code,
                "silver_weight": float(weight),
                "paid_amount": float(total_toman),
                "wallet_balance": float(wallet.balance)
            }
        )
    


# =========================================================
# SELL SILVER
# =========================================================

class SellSilverAPIView(APIView):

    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):

        silver_price = get_live_silver_price()

        serializer = SellSilverSerializer(
            data=request.data,
            context={
                "request": request,
                "silver_price": silver_price
            }
        )

        serializer.is_valid(raise_exception=True)

        user = request.user

        fee = serializer.validated_data["fee"]
        fee_rate = serializer.validated_data["fee_rate"]
        final_amount = serializer.validated_data["final_amount"]
        final_weight = serializer.validated_data["final_weight"]

        inventory, _ = SilverInventory.objects.get_or_create(user=user)
        wallet, _ = SilverWallet.objects.get_or_create(user=user)

        if inventory.balance < final_weight:
            return error_response(message="موجودی نقره کافی نیست")

        inventory.balance -= final_weight
        inventory.save()

        wallet.balance += final_amount
        wallet.save()

        tx = SilverTransaction.objects.create(
            user=user,
            type="SELL",
            status="COMPLETED",
            amount_gr=final_weight,
            price_per_gram=silver_price,
            fee=fee,
            total_amount=final_amount,
            tracking_code=generate_tracking_code("SELL_SLV")
        )

        return success_response(
            message="فروش نقره انجام شد",
            data={
                "transaction_id": tx.id,
                "tracking_code": tx.tracking_code,
                "silver_weight": float(final_weight),
                "fee": float(fee),
                "fee_rate": float(fee_rate),
                "wallet_balance": float(wallet.balance)
            }
        )
    


# =========================================================
# DEPOSIT WALLET (SILVER)
# =========================================================

from rest_framework.parsers import MultiPartParser, FormParser
from django.db import transaction
from decimal import Decimal

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from drf_spectacular.utils import extend_schema

from .models import (
    SilverWallet,
    SilverFinancialTransaction,
    SilverInventory
)

from .serializers import (
    SilverDepositSerializer,
    SilverWithdrawSerializer
)

from .utils import generate_tracking_code

from .views import success_response, error_response


class DepositAPIView(APIView):

    permission_classes = [IsAuthenticated]

    parser_classes = [MultiPartParser, FormParser]

    @extend_schema(
        tags=['Silver Wallet'],
        request=SilverDepositSerializer,
        summary='واریز کیف پول نقره'
    )
    @transaction.atomic
    def post(self, request):

        try:

            serializer = SilverDepositSerializer(data=request.data)

            if not serializer.is_valid():
                return error_response(
                    message="اطلاعات نامعتبر است",
                    data=serializer.errors
                )

            user = request.user

            amount = serializer.validated_data.get("amount")
            method = serializer.validated_data.get("method")
            receipt = serializer.validated_data.get("receipt")

            wallet, _ = SilverWallet.objects.get_or_create(user=user)

            # =========================
            # RECEIPT METHOD
            # =========================
            if method == "RECEIPT":

                if not receipt:
                    return error_response(message="تصویر رسید الزامی است")

                tx = SilverFinancialTransaction.objects.create(
                    user=user,
                    amount=amount,
                    type="DEPOSIT",
                    method="CARD_TO_CARD",
                    status="PENDING",
                    receipt_image=receipt,
                    tracking_code=generate_tracking_code("SLV_DEP"),
                    description="واریز کارت به کارت نقره"
                )

                return success_response(
                    message="درخواست واریز ثبت شد",
                    status_code=201,
                    data={
                        "transaction_id": tx.id,
                        "tracking_code": tx.tracking_code,
                        "status": "PENDING"
                    }
                )

            # =========================
            # GATEWAY METHOD
            # =========================
            elif method == "GATEWAY":

                tx = SilverFinancialTransaction.objects.create(
                    user=user,
                    amount=amount,
                    type="DEPOSIT",
                    method="ONLINE",
                    status="COMPLETED",
                    tracking_code=generate_tracking_code("SLV_PAY"),
                    description="واریز آنلاین نقره"
                )

                wallet.balance += amount
                wallet.save()

                return success_response(
                    message="واریز با موفقیت انجام شد",
                    status_code=201,
                    data={
                        "transaction_id": tx.id,
                        "tracking_code": tx.tracking_code,
                        "wallet_balance": int(wallet.balance),
                        "status": "COMPLETED"
                    }
                )

            return error_response(message="روش واریز نامعتبر است")

        except Exception as e:
            return error_response(message=str(e), status_code=500)
        



class WithdrawAPIView(APIView):

    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):

        serializer = SilverWithdrawSerializer(
            data=request.data,
            context={"request": request}
        )

        if not serializer.is_valid():
            return error_response(
                message="اطلاعات نامعتبر است",
                data=serializer.errors
            )

        user = request.user

        amount = serializer.validated_data.get("amount")
        target = serializer.validated_data.get("target")
        card_id = serializer.validated_data.get("card_id")

        wallet, _ = SilverWallet.objects.get_or_create(user=user)

        if wallet.balance < amount:
            return error_response(message="موجودی کافی نیست")

        # =========================
        # BANK WITHDRAW
        # =========================
        if target == "BANK":

            if not card_id:
                return error_response(message="کارت بانکی الزامی است")

            card = BankCard.objects.filter(id=card_id, user=user).first()

            if not card:
                return error_response(message="کارت یافت نشد")

            wallet.balance -= amount
            wallet.save()

            tx = SilverFinancialTransaction.objects.create(
                user=user,
                amount=amount,
                type="WITHDRAW",
                method="BANK",
                status="PENDING",
                user_card=card,
                tracking_code=generate_tracking_code("SLV_WDB"),
                admin_note="در انتظار تسویه بانکی",
                description=f"برداشت بانکی - کارت {card.card_number}"
            )

            return success_response(
                message="درخواست برداشت ثبت شد",
                data={
                    "transaction_id": tx.id,
                    "tracking_code": tx.tracking_code,
                    "status": tx.status,
                    "wallet_balance": int(wallet.balance),
                    "card_number": card.card_number
                }
            )

        # =========================
        # CONVERT TO SILVER
        # =========================
        elif target == "SILVER":

            silver_price = Decimal("1")  # همون مدل خودت (placeholder)

            silver_inventory, _ = SilverInventory.objects.get_or_create(user=user)

            silver_weight = amount / silver_price

            wallet.balance -= amount
            wallet.save()

            silver_inventory.balance += silver_weight
            silver_inventory.save()

            tx = SilverFinancialTransaction.objects.create(
                user=user,
                amount=amount,
                type="WITHDRAW",
                method="BANK",
                status="COMPLETED",
                tracking_code=generate_tracking_code("SLV_CONVERT"),
                admin_note="تبدیل ریال به نقره",
                description="تبدیل کیف پول به نقره"
            )

            return success_response(
                message="تبدیل به نقره انجام شد",
                data={
                    "transaction_id": tx.id,
                    "tracking_code": tx.tracking_code,
                    "silver_weight": round(silver_weight, 5),
                    "wallet_balance": int(wallet.balance)
                }
            )

        return error_response(message="نوع برداشت نامعتبر است")
    



# =========================================================
# PRODUCTS (SILVER)
# =========================================================

class SilverProductListAPIView(APIView):

    permission_classes = [AllowAny]

    def get(self, request):

        queryset = SilverProduct.objects.filter(
            is_active=True
        ).select_related("category").order_by("-created_at")

        category = request.GET.get("category")
        delivery_type = request.GET.get("delivery_type")

        if category:
            queryset = queryset.filter(category__slug=category)

        if delivery_type:
            queryset = queryset.filter(delivery_type=delivery_type)

        serializer = SilverProductSerializer(queryset, many=True)

        return success_response(
            message="محصولات نقره دریافت شد",
            data=serializer.data
        )


# =========================================================
# PHYSICAL ORDER (SILVER CHECKOUT)
# =========================================================
# =========================================================
# PHYSICAL ORDER (SILVER CHECKOUT)
# =========================================================

class SilverPhysicalOrderAPIView(APIView):

    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):

        serializer = SilverPhysicalOrderSerializer(
            data=request.data
        )

        if not serializer.is_valid():
            return error_response(
                data=serializer.errors
            )

        user = request.user

        products_data = serializer.validated_data[
            "products"
        ]

        wallet, _ = SilverWallet.objects.get_or_create(
            user=user
        )

        inventory, _ = SilverInventory.objects.get_or_create(
            user=user
        )

        total_silver = 0
        total_toman = 0
        order_items = []

        # =========================
        # PROCESS PRODUCTS
        # =========================

        for item in products_data:

            product = SilverProduct.objects.filter(
                id=item["product_id"],
                is_active=True
            ).first()

            if not product:

                return error_response(
                    message=f"محصول {item['product_id']} یافت نشد"
                )

            quantity = item["quantity"]

            if product.inventory_count < quantity:

                return error_response(
                    message=f"موجودی {product.name} کافی نیست"
                )

            item_silver = (
                product.total_weight_with_fees * quantity
            )

            item_toman = (
                product.buy_price * quantity
            )

            total_silver += item_silver
            total_toman += item_toman

            order_items.append({

                "product": product,

                "quantity": quantity,

                "price_at_time": product.buy_price,

                "weight_at_time": product.total_weight_with_fees
            })

        payment_method = serializer.validated_data[
            "payment_method"
        ]

        # =========================
        # PAYMENT
        # =========================

        if payment_method == "TOMAN":

            if wallet.balance < total_toman:

                return error_response(
                    message="موجودی کیف پول کافی نیست"
                )

            wallet.balance -= total_toman

            wallet.save(
                update_fields=["balance"]
            )

        elif payment_method == "SILVER":

            if inventory.balance < total_silver:

                return error_response(
                    message="موجودی نقره کافی نیست"
                )

            inventory.balance -= total_silver

            inventory.save(
                update_fields=["balance"]
            )

        else:

            return error_response(
                message="روش پرداخت نامعتبر است"
            )

        # =========================
        # ADDRESS
        # =========================

        address_id = serializer.validated_data.get(
            "address_id"
        )

        if address_id:

            address = UserAddress.objects.filter(
                id=address_id,
                user=user
            ).first()

            if not address:

                return error_response(
                    message="آدرس یافت نشد"
                )

        else:

            address = UserAddress.objects.create(

                user=user,

                province=serializer.validated_data[
                    "province"
                ],

                city=serializer.validated_data[
                    "city"
                ],

                address=serializer.validated_data[
                    "address"
                ],

                postal_code=serializer.validated_data.get(
                    "postal_code"
                ),

                plaque=serializer.validated_data.get(
                    "plaque"
                ),

                unit=serializer.validated_data.get(
                    "unit"
                ),
            )

        # =========================
        # ORDER CREATE
        # =========================

        order = SilverOrder.objects.create(

            user=user,

            province=address.province,

            city=address.city,

            address=address.address,

            postal_code=address.postal_code,

            plaque=address.plaque,

            unit=address.unit,

            payment_method=payment_method,

            delivery_type=serializer.validated_data[
                "delivery_type"
            ],

            total_silver_amount=total_silver,

            total_toman_amount=total_toman,

            tracking_code=generate_tracking_code(
                "SORD"
            ),

            status="PENDING"
        )

        # =========================
        # ORDER ITEMS
        # =========================

        for item in order_items:

            product = item["product"]

            SilverOrderItem.objects.create(

                order=order,

                product=product,

                quantity=item["quantity"],

                price_at_time=item["price_at_time"],

                weight_at_time=item["weight_at_time"]
            )

            product.inventory_count -= item[
                "quantity"
            ]

            product.save(
                update_fields=["inventory_count"]
            )

        return success_response(

            message="سفارش نقره ثبت شد",

            status_code=201,

            data={

                "order_id": order.id,

                "tracking_code": order.tracking_code,

                "total_silver": float(total_silver),

                "total_price": int(total_toman)
            }
        )

# =========================================================
# SILVER PRODUCT CATEGORIES
# =========================================================

class SilverProductCategoryListAPIView(APIView):

    permission_classes = [AllowAny]

    def get(self, request):

        queryset = SilverProductCategory.objects.all().order_by("name")

        serializer = SilverProductCategorySerializer(
            queryset,
            many=True
        )

        return success_response(
            message="دسته بندی محصولات نقره دریافت شد",
            data=serializer.data
        )




# =========================================================
# USER ADDRESS LIST
# =========================================================

class SilverUserAddressListAPIView(APIView):

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

class SilverUserAddressCreateAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request):

        serializer = UserAddressSerializer(data=request.data)

        if not serializer.is_valid():
            return error_response(data=serializer.errors)

        address = UserAddress.objects.create(
            user=request.user,
            province=serializer.validated_data["province"],
            city=serializer.validated_data["city"],
            address=serializer.validated_data["address"],
            postal_code=serializer.validated_data.get("postal_code"),
            plaque=serializer.validated_data.get("plaque"),
            unit=serializer.validated_data.get("unit"),
        )

        return success_response(
            message="آدرس ثبت شد",
            status_code=201,
            data={
                "address_id": address.id
            }
        )




# =========================================================
# ORDER HISTORY
# =========================================================

class SilverOrderHistoryAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        queryset = SilverOrder.objects.filter(
            user=request.user
        ).order_by("-created_at")

        serializer = SilverOrderSerializer(queryset, many=True)

        return success_response(
            message="سفارشات نقره دریافت شد",
            data=serializer.data
        )
    



# =========================================================
# SILVER REPORTS
# =========================================================

# =========================================================
# SILVER REPORTS (FIXED - SAME STRUCTURE AS GOLD)
# =========================================================

class SilverReportsAPIView(APIView):

    permission_classes = [IsAuthenticated]

    # ==========================================
    # DATE PARSER
    # ==========================================
    def parse_date(self, value):

        if not value:
            return None

        try:
            if "/" in value:
                y, m, d = map(int, value.split("/"))
                return jdatetime.date(y, m, d).togregorian()

            return datetime.strptime(value, "%Y-%m-%d").date()

        except Exception:
            return None

    # ==========================================
    def get(self, request):

        report_type = request.GET.get("type")
        status_filter = request.GET.get("status")
        method_filter = request.GET.get("method")

        start_date = self.parse_date(request.GET.get("start_date"))
        end_date = self.parse_date(request.GET.get("end_date"))

        # =====================================================
        # SILVER TRANSACTIONS (BUY / SELL)
        # =====================================================
        if report_type == "silver":

            queryset = SilverTransaction.objects.filter(
                user=request.user
            ).order_by("-created_at")

            if method_filter:
                queryset = queryset.filter(type=method_filter.upper())

            if status_filter:
                queryset = queryset.filter(status=status_filter)

            if start_date:
                queryset = queryset.filter(created_at__date__gte=start_date)

            if end_date:
                queryset = queryset.filter(created_at__date__lte=end_date)

            serializer = SilverTransactionSerializer(queryset, many=True)

            return success_response(
                message="گزارش معاملات نقره",
                data=serializer.data
            )

        # =====================================================
        # DEPOSIT
        # =====================================================
        elif report_type == "deposit":

            queryset = SilverFinancialTransaction.objects.filter(
                user=request.user,
                type="DEPOSIT"
            ).order_by("-created_at")

            if method_filter:
                queryset = queryset.filter(method=method_filter.upper())

            if status_filter:
                queryset = queryset.filter(status=status_filter)

            if start_date:
                queryset = queryset.filter(created_at__date__gte=start_date)

            if end_date:
                queryset = queryset.filter(created_at__date__lte=end_date)

            serializer = SilverFinancialTransactionSerializer(queryset, many=True)

            return success_response(
                message="گزارش واریزهای نقره",
                data=serializer.data
            )

        # =====================================================
        # WITHDRAW
        # =====================================================
        elif report_type == "withdraw":

            queryset = SilverFinancialTransaction.objects.filter(
                user=request.user,
                type="WITHDRAW"
            ).order_by("-created_at")

            if method_filter:
                queryset = queryset.filter(method=method_filter.upper())

            if status_filter:
                queryset = queryset.filter(status=status_filter)

            if start_date:
                queryset = queryset.filter(created_at__date__gte=start_date)

            if end_date:
                queryset = queryset.filter(created_at__date__lte=end_date)

            serializer = SilverFinancialTransactionSerializer(queryset, many=True)

            return success_response(
                message="گزارش برداشت‌های نقره",
                data=serializer.data
            )

        # =====================================================
        # ORDERS
        # =====================================================
        elif report_type == "orders":

            queryset = SilverOrder.objects.filter(
                user=request.user
            ).order_by("-created_at")

            if method_filter:
                queryset = queryset.filter(payment_method=method_filter.upper())

            if status_filter:
                queryset = queryset.filter(status=status_filter)

            if start_date:
                queryset = queryset.filter(created_at__date__gte=start_date)

            if end_date:
                queryset = queryset.filter(created_at__date__lte=start_date)

            serializer = SilverOrderSerializer(queryset, many=True)

            return success_response(
                message="گزارش سفارشات نقره",
                data=serializer.data
            )

        return error_response(
            message="نوع گزارش نامعتبر است"
        )

# =========================================================
# RECENT TRANSACTIONS (SILVER)
# =========================================================

class SilverRecentTransactionsAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        queryset = SilverFinancialTransaction.objects.filter(
            user=request.user
        )

        transaction_type = request.GET.get("type")
        status = request.GET.get("status")
        start_date = request.GET.get("start_date")
        end_date = request.GET.get("end_date")

        # =====================
        # TYPE
        # =====================

        if transaction_type:
            queryset = queryset.filter(
                type=transaction_type
            )

        # =====================
        # STATUS
        # =====================

        if status:
            queryset = queryset.filter(
                status=status
            )

        # =====================
        # DATE
        # =====================

        if start_date:
            queryset = queryset.filter(
                created_at__date__gte=start_date
            )

        if end_date:
            queryset = queryset.filter(
                created_at__date__lte=end_date
            )

        queryset = queryset.order_by(
            "-created_at"
        )[:50]

        data = []

        for item in queryset:

            if item.type == "DEPOSIT":

                if item.method == "ONLINE":
                    title = "واریز مستقیم"

                elif item.method == "BANK":
                    title = "واریز"

                else:
                    title = "واریز"

            else:

                if item.method == "BANK":
                    title = "برداشت"

                else:
                    title = "برداشت"

            data.append({
                "id": item.id,
                "title": title,
                "amount": item.amount,
                "status": item.status,
                "type": item.type,
                "method": item.method,
                "created_at": item.created_at,
            })

        serializer = SilverRecentTransactionSerializer(
            data,
            many=True
        )

        return success_response(
            message="تراکنش ها دریافت شد",
            data=serializer.data
        )
    

# =========================================================
# RECENT DELIVERIES (SILVER)
# =========================================================

class SilverRecentDeliveriesAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        queryset = SilverOrder.objects.filter(
            user=request.user
        ).order_by('-created_at')[:10]

        serializer = SilverOrderSerializer(
            queryset,
            many=True
        )

        return success_response(
            message='تحویل ها دریافت شد',
            data=serializer.data
        )

class SilverDepositInfoAPIView(APIView):

    permission_classes = [AllowAny]

    def get(self, request):

        bank = SilverBankInfo.objects.filter(is_active=True).first()

        if not bank:
            return error_response(message="اطلاعات بانکی نقره ثبت نشده")

        return success_response(
            message="اطلاعات واریز نقره",
            data={
                "card_number": bank.card_number,
                "full_name": bank.full_name,
                "sheba": bank.sheba,
            }
        )
    


# =========================================================
# REFERRAL DASHBOARD (SILVER)
# =========================================================

class SilverReferralDashboardAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        user = request.user

        total_invited = user.subscribers.count()

        total_earned = SilverReferralEarning.objects.filter(
            user=user
        ).aggregate(
            total=Sum("amount")
        )["total"] or 0

        recent_earnings = SilverReferralEarning.objects.filter(
            user=user
        ).order_by("-created_at")[:10]

        serializer = SilverReferralEarningSerializer(
            recent_earnings,
            many=True
        )

        return success_response(
            message="اطلاعات دعوت دوستان دریافت شد",
            data={
                "referral_code": getattr(user, "referral_code", None),
                "referral_link": f"https://silver.darine.shop/register?ref={getattr(user, 'referral_code', '')}",
                "total_invited": total_invited,
                "total_earned": int(total_earned),
                "recent_earnings": serializer.data
            }
        )