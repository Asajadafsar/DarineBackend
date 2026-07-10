# =========================================================
# SILVER APP VIEWS
# =========================================================

from datetime import datetime, timezone
from decimal import Decimal
from django.db import transaction
from django.db.models import F, Sum
from rest_framework.parsers import MultiPartParser, FormParser
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from drf_spectacular.utils import extend_schema

from admin_panel.models import SilverAnnouncement, SilverAnnouncementRead, SilverBanner
from admin_panel.serializers import SilverAnnouncementSerializer, SilverBannerSerializer
from admin_panel.utils import create_admin_log
from gold_app.models import GoldInventory, Wallet

from .models import (
    SilverOrderStatusHistory,
    SilverWallet,
    SilverFinancialTransaction,
    SilverInventory,
)

from .serializers import SilverDepositSerializer, SilverWithdrawSerializer

from .utils import generate_tracking_code

import jdatetime
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response


from accounts.models import BankCard

# =========================
# SILVER MODELS
# =========================
from .models import (
    SilverBankInfo,
    SilverTransaction,
    SilverProduct,
    SilverProductCategory,
    SilverOrder,
    SilverOrderItem,
    SilverReferralEarning,
    UserAddress,
)

# =========================
# SILVER SERIALIZERS
# =========================
from .serializers import (
    SilverPhysicalOrderSerializer,
    SilverProductCategorySerializer,
    SilverTransactionSerializer,
    SilverFinancialTransactionSerializer,
    SilverProductSerializer,
    SilverOrderSerializer,
    SilverReferralEarningSerializer,
    SilverRecentTransactionSerializer,
    BuySilverSerializer,
    SellSilverSerializer,
    UserAddressSerializer,
)

# =========================
# SILVER UTILS
# =========================
from .utils import get_live_silver_price, get_silver_chart_data

# =========================================================
# SUCCESS RESPONSE
# =========================================================


def success_response(
    message="عملیات موفق بود", data=None, status_code=status.HTTP_200_OK
):

    # فقط اگر None بود تصمیم بگیر
    if data is None:
        data = []

    return Response(
        {"success": True, "message": message, "data": data}, status=status_code
    )


# =========================================================
# ERROR RESPONSE
# =========================================================


def error_response(
    message="خطایی رخ داده است", status_code=status.HTTP_400_BAD_REQUEST, data=None
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
        {"success": False, "message": str(final_message), "data": {}},
        status=status_code,
    )


from .views import success_response, error_response

# =========================================================
# DASHBOARD
# =========================================================

# =========================================================
# DASHBOARD
# =========================================================


class SilverDashboardAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        user = request.user

        inventory, _ = SilverInventory.objects.get_or_create(user=user)

        wallet, _ = SilverWallet.objects.get_or_create(user=user)

        silver_price = get_live_silver_price() or Decimal("0")

        silver_balance = Decimal(str(inventory.accessible_balance))

        toman_balance = Decimal(str(wallet.accessible_toman))

        silver_value = silver_balance * silver_price

        total_assets = silver_value + toman_balance

        return success_response(
            message="اطلاعات داشبورد دریافت شد",
            data={
                "silver": {
                    "accessible_balance": silver_balance,
                    "blocked_balance": inventory.blocked_balance,
                    "total_balance": inventory.total_balance,
                },
                "wallet": {
                    "accessible_toman": wallet.accessible_toman,
                    "blocked_toman": wallet.blocked_toman,
                    "toman_total": wallet.toman_total,
                },
                "silver_price": round(silver_price),
                "silver_value": round(silver_value),
                "total_assets": round(total_assets),
            },
        )


# =========================================================
# USER BALANCE
# =========================================================


class SilverUserBalanceAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        inventory, _ = SilverInventory.objects.get_or_create(user=request.user)

        wallet, _ = SilverWallet.objects.get_or_create(user=request.user)

        silver_price = get_live_silver_price() or Decimal("0")

        total_assets = (
            inventory.accessible_balance * silver_price
        ) + wallet.accessible_toman

        return success_response(
            message="موجودی دریافت شد",
            data={
                "accessible_silver": inventory.accessible_balance,
                "blocked_silver": inventory.blocked_balance,
                "silver_total": inventory.total_balance,
                "accessible_toman": wallet.accessible_toman,
                "blocked_toman": wallet.blocked_toman,
                "toman_total": wallet.toman_total,
                "current_silver_price": int(silver_price),
                "total_assets": int(total_assets),
            },
        )



# =========================================================
# BUY SILVER
# =========================================================

from decimal import Decimal

from django.db import transaction
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from .models import SilverWallet, SilverInventory, SilverTransaction
from .serializers import BuySilverSerializer, SellSilverSerializer



class BuySilverCalculateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):

        silver_price = get_live_silver_price()

        if not silver_price:
            return error_response(
                message="خطا در دریافت قیمت نقره",
                status_code=500,
            )

        serializer = BuySilverSerializer(
            data=request.data,
            context={
                "request": request,
                "silver_price": silver_price,
            },
        )

        if not serializer.is_valid():
            return error_response(
                message="اطلاعات نامعتبر است.",
                data=serializer.errors,
            )

        wallet, _ = SilverWallet.objects.get_or_create(user=request.user)

        total_toman = serializer.validated_data["total_toman"]
        remaining_toman = wallet.accessible_toman - total_toman

        return success_response(
            message="محاسبه با موفقیت انجام شد.",
            data={
                "silver_price": float(serializer.validated_data["silver_price"]),
                "silver_weight": float(serializer.validated_data["final_weight"]),
                "pure_silver_price": float(serializer.validated_data["pure_silver_price"]),
                "fee_rate": float(serializer.validated_data["fee_rate"] * Decimal("100")),
                "fee": float(serializer.validated_data["fee"]),
                "total_toman": float(total_toman),
                "enough_balance": wallet.accessible_toman >= total_toman,
                "wallet": {
                    "accessible_toman": float(wallet.accessible_toman),
                    "blocked_toman": float(wallet.blocked_toman),
                    "remaining_toman": float(
                        max(Decimal("0"), remaining_toman)
                    ),
                },
            },
        )

class BuySilverAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):

        user = request.user

        silver_price = get_live_silver_price()

        if not silver_price:
            return error_response(message="خطا در دریافت قیمت نقره", status_code=500)

        serializer = BuySilverSerializer(
            data=request.data, context={"request": request, "silver_price": silver_price}
        )

        if not serializer.is_valid():
            return error_response(
                message="اطلاعات خرید نامعتبر است", data=serializer.errors
            )

        weight = serializer.validated_data["final_weight"]
        fee = serializer.validated_data["fee"]
        fee_rate = serializer.validated_data["fee_rate"]
        total_toman = serializer.validated_data["total_toman"]
        pure_silver_price = serializer.validated_data["pure_silver_price"]  # ✅ اضافه شد

        if weight <= Decimal("0"):
            return error_response(message="وزن نقره نامعتبر است")

        wallet, _ = SilverWallet.objects.select_for_update().get_or_create(user=user)
        inventory, _ = SilverInventory.objects.select_for_update().get_or_create(user=user)

        # ==========================
        # بررسی و بلوکه‌کردن موجودی نقدی
        # ==========================

        if wallet.accessible_toman < total_toman:
            return error_response(message="موجودی کیف پول کافی نیست")

        wallet.accessible_toman -= total_toman
        wallet.blocked_toman += total_toman
        wallet.save(update_fields=["accessible_toman", "blocked_toman", "updated_at"])

        # ==========================
        # تراکنش نقره - در انتظار تایید ادمین
        # ==========================

        tx = SilverTransaction.objects.create(
            user=user,
            type="BUY",
            status="PENDING",
            amount_gr=weight,
            price_per_gram=silver_price,
            fee=fee,
            commission_percent=(fee_rate * Decimal("100")),
            commission_amount=fee,
            total_amount=total_toman,
            tracking_code=generate_tracking_code("SBUY"),
        )

        create_admin_log(
            request=request,
            user=user,
            action_type="BUY_SILVER",
            action="درخواست خرید نقره (در انتظار تایید)",
            model_name="SilverTransaction",
            object_id=tx.id,
            tracking_code=tx.tracking_code,
            success=True,
            description=f"""
درخواست خرید نقره

کاربر: {user.mobile}
وزن: {weight} گرم
قیمت هر گرم: {silver_price}
قیمت خالص نقره: {pure_silver_price}
کارمزد: {fee}
مبلغ کل بلوکه‌شده: {total_toman}
موجودی بلوکه فعلی کیف پول: {wallet.blocked_toman}
""",
        )

        return success_response(
            message="درخواست خرید نقره ثبت شد و در انتظار تایید ادمین است",
            status_code=201,
            data={
                "transaction_id": tx.id,
                "tracking_code": tx.tracking_code,
                "status": tx.status,
                "silver_weight": float(weight),
                "pure_silver_price": float(pure_silver_price),  # ✅ اضافه شد
                "fee": float(fee),
                "fee_rate": float(fee_rate),
                "total_toman": float(total_toman),
                "accessible_toman": float(wallet.accessible_toman),
                "blocked_toman": float(wallet.blocked_toman),
            },
        )


class SellSilverCalculateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):

        silver_price = get_live_silver_price()

        if not silver_price:
            return error_response(
                message="خطا در دریافت قیمت نقره",
                status_code=500,
            )

        serializer = SellSilverSerializer(
            data=request.data,
            context={
                "request": request,
                "silver_price": silver_price,
            },
        )

        if not serializer.is_valid():
            return error_response(
                message="اطلاعات نامعتبر است.",
                data=serializer.errors,
            )

        inventory, _ = SilverInventory.objects.get_or_create(user=request.user)

        final_weight = serializer.validated_data["final_weight"]
        remaining_silver = inventory.accessible_balance - final_weight

        return success_response(
            message="محاسبه با موفقیت انجام شد.",
            data={
                "silver_price": float(serializer.validated_data["silver_price"]),
                "silver_weight": float(final_weight),
                "pure_silver_price": float(serializer.validated_data["pure_value"]),
                "fee_rate": float(serializer.validated_data["fee_rate"] * Decimal("100")),
                "fee": float(serializer.validated_data["fee"]),
                "final_amount": float(serializer.validated_data["final_amount"]),
                "enough_balance": inventory.accessible_balance >= final_weight,
                "inventory": {
                    "accessible_silver": float(inventory.accessible_balance),
                    "blocked_silver": float(inventory.blocked_balance),
                    "remaining_silver": float(
                        max(Decimal("0"), remaining_silver)
                    ),
                },
            },
        )
# =========================================================
# SELL SILVER
# =========================================================

class SellSilverAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):

        silver_price = get_live_silver_price()

        if not silver_price:
            return error_response(message="خطا در دریافت قیمت نقره", status_code=500)

        serializer = SellSilverSerializer(
            data=request.data, context={"request": request, "silver_price": silver_price}
        )

        if not serializer.is_valid():
            return error_response(message="اطلاعات نامعتبر است", data=serializer.errors)

        user = request.user
        final_weight = serializer.validated_data["final_weight"]
        final_amount = serializer.validated_data["final_amount"]
        fee = serializer.validated_data["fee"]
        fee_rate = serializer.validated_data["fee_rate"]
        pure_value = serializer.validated_data["pure_value"]  # ✅ اضافه شد

        if final_weight <= 0:
            return error_response(message="وزن فروش نامعتبر است")

        inventory, _ = SilverInventory.objects.select_for_update().get_or_create(user=user)
        wallet, _ = SilverWallet.objects.select_for_update().get_or_create(user=user)

        # ==========================
        # بررسی و بلوکه‌کردن موجودی نقره
        # ==========================

        if inventory.accessible_balance < final_weight:
            return error_response(message="موجودی نقره قابل معامله شما کافی نیست")

        inventory.accessible_balance -= final_weight
        inventory.blocked_balance += final_weight
        inventory.save(update_fields=["accessible_balance", "blocked_balance", "updated_at"])

        # ==========================
        # ثبت تراکنش به صورت PENDING (در انتظار تایید ادمین)
        # ==========================

        tx = SilverTransaction.objects.create(
            user=user,
            type="SELL",
            status="PENDING",
            amount_gr=final_weight,
            price_per_gram=silver_price,
            fee=fee,
            commission_percent=(fee_rate * Decimal("100")),
            commission_amount=fee,
            total_amount=final_amount,
            tracking_code=generate_tracking_code("SSELL"),
        )

        create_admin_log(
            request=request,
            user=user,
            action_type="SELL_SILVER",
            action="درخواست فروش نقره (در انتظار تایید)",
            model_name="SilverTransaction",
            object_id=tx.id,
            tracking_code=tx.tracking_code,
            success=True,
            description=f"""
درخواست فروش نقره

کاربر: {user.mobile}
وزن فروخته شده: {final_weight} گرم
ارزش خالص: {pure_value}
مبلغ خالص واریزی پس از کسر کارمزد: {final_amount} تومان
کارمزد کسر شده: {fee} تومان
موجودی نقره بلوکه شده فعلی: {inventory.blocked_balance} گرم
""",
        )

        return success_response(
            message="درخواست فروش نقره با موفقیت ثبت شد و در انتظار تایید ادمین است",
            status_code=201,
            data={
                "transaction_id": tx.id,
                "tracking_code": tx.tracking_code,
                "status": tx.status,
                "silver_weight": float(final_weight),
                "pure_silver_price": float(pure_value),  # ✅ اضافه شد
                "fee": float(fee),
                "fee_rate": float(fee_rate),
                "final_amount": float(final_amount),
                "accessible_silver": float(inventory.accessible_balance),
                "blocked_silver": float(inventory.blocked_balance),
            },
        )

# =========================================================
# DEPOSIT WALLET (SILVER)
# =========================================================


class DepositAPIView(APIView):

    permission_classes = [IsAuthenticated]

    parser_classes = [MultiPartParser, FormParser]

    ONLINE_LIMIT = 400_000_000

    @extend_schema(
        tags=["Silver Wallet"],
        request=SilverDepositSerializer,
        summary="واریز کیف پول نقره",
    )
    @transaction.atomic
    def post(self, request):

        try:

            serializer = SilverDepositSerializer(data=request.data)

            if not serializer.is_valid():

                response = error_response(
                    message="اطلاعات نامعتبر است", data=serializer.errors
                )

                create_admin_log(
                    request=request,
                    user=request.user,
                    action_type="PAYMENT",
                    action="خطا در اعتبارسنجی واریز نقره",
                    model_name="SilverFinancialTransaction",
                    response_status=response.status_code,
                    success=False,
                    description=str(serializer.errors),
                )

                return response

            user = request.user

            amount = serializer.validated_data["amount"]

            method = serializer.validated_data["method"]

            receipt = serializer.validated_data.get("receipt")

            description = serializer.validated_data.get("description", "")

            wallet, _ = SilverWallet.objects.get_or_create(user=user)

            # =====================================================
            # CARD TO CARD
            # =====================================================

            if method == "RECEIPT":

                tx = SilverFinancialTransaction.objects.create(
                    user=user,
                    amount=amount,
                    type="DEPOSIT",
                    method="CARD_TO_CARD",
                    status="PENDING",
                    receipt_image=receipt,
                    tracking_code=generate_tracking_code("SLV_DEP"),
                    description=description,
                )

                response = success_response(
                    message="درخواست واریز ثبت شد و پس از تایید ادمین به کیف پول اضافه خواهد شد.",
                    status_code=201,
                    data={
                        "transaction_id": tx.id,
                        "tracking_code": tx.tracking_code,
                        "status": tx.status,
                        "accessible_toman": wallet.accessible_toman,
                        "blocked_toman": wallet.blocked_toman,
                        "toman_total": wallet.toman_total,
                    },
                )

                create_admin_log(
                    request=request,
                    user=user,
                    action_type="PAYMENT",
                    action="ثبت درخواست واریز کارت به کارت نقره",
                    model_name="SilverFinancialTransaction",
                    object_id=tx.id,
                    tracking_code=tx.tracking_code,
                    response_status=response.status_code,
                    success=True,
                    description=f"""

کاربر:

{user.mobile}

نوع:

واریز کارت به کارت

مبلغ:

{amount:,}

وضعیت:

PENDING

""",
                )

                return response

            # =====================================================
            # ONLINE PAYMENT
            # =====================================================

            elif method == "GATEWAY":

                if amount > self.ONLINE_LIMIT:

                    response = error_response(
                        message="حداکثر مبلغ پرداخت آنلاین ۴۰۰,۰۰۰,۰۰۰ تومان است."
                    )

                    create_admin_log(
                        request=request,
                        user=user,
                        action_type="PAYMENT",
                        action="بیش از سقف مجاز پرداخت آنلاین",
                        model_name="SilverFinancialTransaction",
                        response_status=response.status_code,
                        success=False,
                        description=f"amount={amount}",
                    )

                    return response

                tx = SilverFinancialTransaction.objects.create(
                    user=user,
                    amount=amount,
                    type="DEPOSIT",
                    method="ONLINE",
                    status="COMPLETED",
                    tracking_code=generate_tracking_code("SLV_PAY"),
                    description=description,
                )

                wallet.accessible_toman += amount

                wallet.save(update_fields=["accessible_toman", "updated_at"])

                response = success_response(
                    message="واریز با موفقیت انجام شد.",
                    status_code=201,
                    data={
                        "transaction_id": tx.id,
                        "tracking_code": tx.tracking_code,
                        "status": tx.status,
                        "accessible_toman": wallet.accessible_toman,
                        "blocked_toman": wallet.blocked_toman,
                        "toman_total": wallet.toman_total,
                    },
                )

                create_admin_log(
                    request=request,
                    user=user,
                    action_type="PAYMENT",
                    action="واریز آنلاین کیف پول نقره",
                    model_name="SilverFinancialTransaction",
                    object_id=tx.id,
                    tracking_code=tx.tracking_code,
                    response_status=response.status_code,
                    success=True,
                    description=f"""

کاربر:

{user.mobile}

نوع:

واریز آنلاین

مبلغ:

{amount:,}

موجودی قابل استفاده:

{wallet.accessible_toman:,}

وضعیت:

COMPLETED

""",
                )

                return response

            response = error_response(message="روش واریز نامعتبر است")

            create_admin_log(
                request=request,
                user=user,
                action_type="PAYMENT",
                action="روش پرداخت نامعتبر",
                model_name="SilverFinancialTransaction",
                response_status=response.status_code,
                success=False,
                description=method,
            )

            return response

        except Exception as e:

            response = error_response(message=str(e), status_code=500)

            create_admin_log(
                request=request,
                user=request.user if request.user.is_authenticated else None,
                action_type="SYSTEM",
                action="خطا در واریز کیف پول نقره",
                model_name="SilverFinancialTransaction",
                response_status=response.status_code,
                success=False,
                error_message=str(e),
            )

            return response


# =========================================================
# WITHDRAW SILVER WALLET → GOLD WALLET (TRANSFER BACK)
# =========================================================

class WithdrawAPIView(APIView):

    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):

        try:

            serializer = SilverWithdrawSerializer(
                data=request.data,
                context={"request": request}
            )

            # =====================================================
            # VALIDATION
            # =====================================================
            if not serializer.is_valid():

                response = error_response(
                    message="اطلاعات نامعتبر است",
                    data=serializer.errors
                )

                create_admin_log(
                    request=request,
                    admin=None,
                    user=request.user if request.user.is_authenticated else None,
                    action_type="PAYMENT",
                    action="خطا در برداشت نقره (بازگشت به طلا)",
                    model_name="SilverFinancialTransaction",
                    response_status=response.status_code,
                    success=False,
                    description=str(serializer.errors),
                )

                return response

            user = request.user
            amount = serializer.validated_data.get("amount")
            target = serializer.validated_data.get("target")

            # =====================================================
            # WALLET LOAD
            # =====================================================
            silver_wallet, _ = SilverWallet.objects.get_or_create(user=user)
            silver_wallet = SilverWallet.objects.select_for_update().get(pk=silver_wallet.pk)

            gold_wallet, _ = Wallet.objects.get_or_create(user=user)
            gold_wallet = Wallet.objects.select_for_update().get(pk=gold_wallet.pk)

            # =====================================================
            # CHECK BALANCE (SILVER WALLET)
            # =====================================================
            if silver_wallet.accessible_toman < amount:

                response = error_response(
                    message="موجودی نقره کافی نیست"
                )

                return response

            # =====================================================
            # ONLY TRANSFER MODE
            # =====================================================
            if target == "GOLD":

                # -----------------------------------------
                # کم کردن از نقره
                # -----------------------------------------
                silver_wallet.accessible_toman -= amount
                silver_wallet.save(update_fields=["accessible_toman"])

                # -----------------------------------------
                # اضافه کردن به طلا (تومان)
                # -----------------------------------------
                gold_wallet.accessible_toman += amount
                gold_wallet.save(update_fields=["accessible_toman"])

                # -----------------------------------------
                # ثبت تراکنش
                # -----------------------------------------
                tx = SilverFinancialTransaction.objects.create(
                    user=user,
                    amount=amount,
                    type="WITHDRAW",
                    method="BANK",
                    status="COMPLETED",
                    tracking_code=generate_tracking_code("SLV_TO_GOLD"),
                    admin_note="انتقال از نقره به کیف پول طلا",
                    description="برداشت از نقره و واریز به کیف پول طلا"
                )

                return success_response(
                    message="انتقال با موفقیت انجام شد",
                    data={
                        "transaction_id": tx.id,
                        "tracking_code": tx.tracking_code,
                        "silver_wallet": silver_wallet.accessible_toman,
                        "gold_wallet": gold_wallet.accessible_toman,
                    }
                )

            # =====================================================
            # INVALID TARGET
            # =====================================================
            return error_response(message="نوع عملیات نامعتبر است")

        except Exception as e:

            return error_response(message=str(e), status_code=500)
        
        

# =========================================================
# =========================================================
# PRODUCTS (SILVER)
# =========================================================


class SilverProductListAPIView(APIView):

    permission_classes = [AllowAny]

    def get(self, request):

        queryset = (
            SilverProduct.objects.filter(
                is_active=True,
                inventory_count__gt=0,
            )
            .select_related("category")
            .order_by("-created_at")
        )

        category = request.GET.get("category")
        delivery_type = request.GET.get("delivery_type")

        if category:
            queryset = queryset.filter(category__slug=category)

        if delivery_type:
            queryset = queryset.filter(delivery_type=delivery_type)

        serializer = SilverProductSerializer(queryset, many=True)

        return success_response(
            message="محصولات نقره دریافت شد",
            data=serializer.data,
        )
        
        
        

# =========================================================
# PHYSICAL ORDER (SILVER CHECKOUT)
# =========================================================


class SilverPhysicalOrderAPIView(APIView):

    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):

        serializer = SilverPhysicalOrderSerializer(data=request.data)

        if not serializer.is_valid():
            return error_response(data=serializer.errors)

        user = request.user

        products_data = serializer.validated_data["products"]

        wallet, _ = SilverWallet.objects.select_for_update().get_or_create(user=user)
        inventory, _ = SilverInventory.objects.select_for_update().get_or_create(
            user=user
        )

        total_silver = Decimal("0")
        total_toman = Decimal("0")

        order_items = []

        # =========================
        # VALIDATE PRODUCTS
        # =========================
        for item in products_data:

            product = SilverProduct.objects.filter(
                id=item["product_id"], is_active=True
            ).first()

            if not product:
                return error_response(message=f"محصول {item['product_id']} یافت نشد")

            quantity = int(item["quantity"])

            item_silver = product.total_weight_with_fees * quantity
            item_toman = product.buy_price * quantity

            total_silver += item_silver
            total_toman += item_toman

            order_items.append(
                {
                    "product": product,
                    "quantity": quantity,
                    "price_at_time": product.buy_price,
                    "weight_at_time": product.total_weight_with_fees,
                }
            )

        payment_method = serializer.validated_data["payment_method"]

        # =========================
        # PAYMENT → BLOCK ONLY (NO DEDUCT)
        # =========================

        if payment_method == "TOMAN":

            if wallet.accessible_toman < total_toman:
                return error_response(message="موجودی کیف پول کافی نیست")

            wallet.accessible_toman -= total_toman
            wallet.blocked_toman += total_toman

            wallet.save(
                update_fields=["accessible_toman", "blocked_toman", "updated_at"]
            )

        elif payment_method == "SILVER":

            if inventory.accessible_balance < total_silver:
                return error_response(message="موجودی نقره کافی نیست")

            inventory.accessible_balance -= total_silver
            inventory.blocked_balance += total_silver

            inventory.save(
                update_fields=["accessible_balance", "blocked_balance", "updated_at"]
            )

        else:
            return error_response(message="روش پرداخت نامعتبر است")

        # =========================
        # ADDRESS
        # =========================
        address_id = serializer.validated_data.get("address_id")

        if address_id:

            address = UserAddress.objects.filter(id=address_id, user=user).first()

            if not address:
                return error_response(message="آدرس یافت نشد")

        else:

            address = UserAddress.objects.create(
                user=user,
                province=serializer.validated_data["province"],
                city=serializer.validated_data["city"],
                address=serializer.validated_data["address"],
                postal_code=serializer.validated_data.get("postal_code"),
                plaque=serializer.validated_data.get("plaque"),
                unit=serializer.validated_data.get("unit"),
            )

        # =========================
        # CREATE ORDER (NO STOCK CHANGE)
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
            delivery_type=serializer.validated_data["delivery_type"],
            total_silver_amount=total_silver,
            total_toman_amount=total_toman,
            tracking_code=generate_tracking_code("SORD"),
            status="REQUESTED",
        )

        SilverOrderStatusHistory.objects.create(
            order=order, status="REQUESTED", description="سفارش ثبت شد"
        )

        for item in order_items:

            SilverOrderItem.objects.create(
                order=order,
                product=item["product"],
                quantity=item["quantity"],
                price_at_time=item["price_at_time"],
                weight_at_time=item["weight_at_time"],
            )

        return success_response(
            message="سفارش نقره ثبت شد",
            status_code=201,
            data={
                "order_id": order.id,
                "tracking_code": order.tracking_code,
                "status": order.status,
                "status_display": order.get_status_display(),
                "created_at": order.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                "total_silver": float(total_silver),
                "total_price": int(total_toman),
                "wallet": {
                    "accessible_toman": float(wallet.accessible_toman),
                    "blocked_toman": float(wallet.blocked_toman),
                    "toman_total": float(wallet.toman_total),
                },
                "inventory": {
                    "accessible_silver": float(inventory.accessible_balance),
                    "blocked_silver": float(inventory.blocked_balance),
                    "total_silver": float(inventory.total_balance),
                },
            },
        )


class SilverOrderNoAddressAPIView(APIView):

    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):

        serializer = SilverPhysicalOrderSerializer(data=request.data)

        if not serializer.is_valid():
            return error_response(data=serializer.errors)

        user = request.user

        products_data = serializer.validated_data["products"]
        payment_method = serializer.validated_data["payment_method"]

        if payment_method not in ["TOMAN", "SILVER"]:
            return error_response(message="روش پرداخت نامعتبر است")

        wallet, _ = SilverWallet.objects.select_for_update().get_or_create(user=user)
        inventory, _ = SilverInventory.objects.select_for_update().get_or_create(user=user)

        total_silver = Decimal("0")
        total_toman = Decimal("0")

        order_items = []
        locked_products = {}

        # =========================
        # VALIDATE PRODUCTS (با قفل روی موجودی محصول برای جلوگیری از race condition)
        # =========================
        for item in products_data:

            product = (
                SilverProduct.objects.select_for_update()
                .filter(id=item["product_id"], is_active=True)
                .first()
            )

            if not product:
                return error_response(
                    message=f"محصول {item['product_id']} یافت نشد"
                )

            quantity = int(item["quantity"])

            # -----------------------------------------
            # اگر یک محصول چند بار در لیست ارسال شده باشد،
            # موجودی تجمعی چک شود نه فقط تک‌تک
            # -----------------------------------------
            already_requested = locked_products.get(product.id, 0)
            total_requested = already_requested + quantity

            if product.inventory_count < total_requested:
                return error_response(
                    message=f"موجودی {product.name} کافی نیست"
                )

            locked_products[product.id] = total_requested

            item_silver = product.total_weight_with_fees * quantity
            item_toman = product.buy_price * quantity

            total_silver += item_silver
            total_toman += item_toman

            order_items.append({
                "product": product,
                "quantity": quantity,
                "price_at_time": product.buy_price,
                "weight_at_time": product.total_weight_with_fees,
            })

        # =========================
        # PAYMENT → BLOCK ONLY
        # =========================

        if payment_method == "TOMAN":

            if wallet.accessible_toman < total_toman:
                return error_response(message="موجودی کیف پول کافی نیست")

            wallet.accessible_toman -= total_toman
            wallet.blocked_toman += total_toman

            wallet.save(update_fields=[
                "accessible_toman",
                "blocked_toman",
                "updated_at"
            ])

        elif payment_method == "SILVER":

            if inventory.accessible_balance < total_silver:
                return error_response(message="موجودی نقره کافی نیست")

            inventory.accessible_balance -= total_silver
            inventory.blocked_balance += total_silver

            inventory.save(update_fields=[
                "accessible_balance",
                "blocked_balance",
                "updated_at"
            ])

        # =========================
        # DECREASE PRODUCT INVENTORY
        # =========================

        # for product_id, requested_qty in locked_products.items():
        #     SilverProduct.objects.filter(id=product_id).update(
        #         inventory_count=F("inventory_count") - requested_qty
        #     )

        # =========================
        # CREATE ORDER (NO ADDRESS)
        # =========================

        order = SilverOrder.objects.create(
            user=user,
            province="",   # حذف آدرس → خالی
            city="",
            address="",
            postal_code=None,
            plaque=None,
            unit=None,
            payment_method=payment_method,
            total_silver_amount=total_silver,
            total_toman_amount=total_toman,
            tracking_code=generate_tracking_code("SORD"),
            status="REQUESTED",
        )

        SilverOrderStatusHistory.objects.create(
            order=order,
            status="REQUESTED",
            description="سفارش ثبت شد"
        )

        for item in order_items:

            SilverOrderItem.objects.create(
                order=order,
                product=item["product"],
                quantity=item["quantity"],
                price_at_time=item["price_at_time"],
                weight_at_time=item["weight_at_time"],
            )

        # =========================
        # LOG
        # =========================

        create_admin_log(
            request=request,
            admin=None,
            user=user,
            action_type="ORDER",
            action="ثبت سفارش فیزیکی نقره",
            model_name="SilverOrder",
            tracking_code=order.tracking_code,
            object_id=order.id,
            description=f"""
کاربر: {user.mobile}

روش پرداخت:
{payment_method}

مبلغ تومانی:
{total_toman:,}

وزن نقره:
{total_silver}

موجودی قابل برداشت تومان:
{wallet.accessible_toman:,}

موجودی قابل برداشت نقره:
{inventory.accessible_balance}
""",
        )

        return success_response(
            message="سفارش نقره  آدرس ثبت شد",
            status_code=201,
            data={
                "order_id": order.id,
                "tracking_code": order.tracking_code,
                "status": order.status,
                "status_display": order.get_status_display(),
                "created_at": order.created_at.strftime("%Y-%m-%d %H:%M:%S"),

                "total_silver": float(total_silver),
                "total_price": int(total_toman),

                "wallet": {
                    "accessible_toman": float(wallet.accessible_toman),
                    "blocked_toman": float(wallet.blocked_toman),
                    "toman_total": float(wallet.toman_total),
                },

                "inventory": {
                    "accessible_silver": float(inventory.accessible_balance),
                    "blocked_silver": float(inventory.blocked_balance),
                    "total_silver": float(inventory.total_balance),
                },
            },
        )

from django.db.models import Sum

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from accounts.models import ReferralEarning, ReferralSetting
from accounts.utils import success_response

class SilverReferralInfoAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        earnings = ReferralEarning.objects.filter(
            referrer=request.user,
            source_type="SILVER",
        )

        total_profit = earnings.aggregate(
            total=Sum("profit")
        )["total"] or 0

        total_transactions = earnings.aggregate(
            total=Sum("transaction_amount")
        )["total"] or 0

        # ✅ دریافت یا ایجاد تنظیمات رفرال
        setting, _ = ReferralSetting.objects.get_or_create(
            defaults={'commission_percent': 20}
        )

        return success_response(
            message="اطلاعات رفرال نقره",
            data={
                "referral_code": request.user.referral_code,
                "referral_percent": float(setting.commission_percent),
                "total_silver_sales": float(total_transactions),
                "total_earnings": float(total_profit),
                "referrals_count": earnings.count(),
                "wallet_type": "SILVER",
            }
        )
# =========================================================
# SILVER PRODUCT CATEGORIES
# =========================================================


class SilverProductCategoryListAPIView(APIView):

    permission_classes = [AllowAny]

    def get(self, request):

        queryset = SilverProductCategory.objects.all().order_by("name")

        serializer = SilverProductCategorySerializer(queryset, many=True)

        return success_response(
            message="دسته بندی محصولات نقره دریافت شد", data=serializer.data
        )


# =========================================================
# USER ADDRESS LIST
# =========================================================


class SilverUserAddressListAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        addresses = UserAddress.objects.filter(user=request.user).order_by(
            "-created_at"
        )

        serializer = UserAddressSerializer(addresses, many=True)

        return success_response(message="لیست آدرس‌ها دریافت شد", data=serializer.data)


# =========================================================
# USER ADDRESS CREATE
# =========================================================


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

        addresses = UserAddress.objects.filter(user=request.user).order_by(
            "-created_at"
        )

        return success_response(
            message="آدرس ثبت شد",
            status_code=201,
            data=UserAddressSerializer(address).data,
        )


class SilverUserAddressAPIView(APIView):

    permission_classes = [IsAuthenticated]

    # =====================================
    # GET single address
    # =====================================
    def get(self, request, address_id):

        address = UserAddress.objects.filter(id=address_id, user=request.user).first()

        if not address:
            return error_response(message="آدرس یافت نشد")

        return success_response(
            message="جزئیات آدرس", data=UserAddressSerializer(address).data
        )

    # =====================================
    # UPDATE address
    # =====================================
    def patch(self, request, address_id):

        address = UserAddress.objects.filter(id=address_id, user=request.user).first()

        if not address:
            return error_response(message="آدرس یافت نشد")

        serializer = UserAddressSerializer(address, data=request.data, partial=True)

        serializer.is_valid(raise_exception=True)
        serializer.save()

        return success_response(message="آدرس ویرایش شد", data=serializer.data)

    # =====================================
    # DELETE address
    # =====================================
    def delete(self, request, address_id):

        address = UserAddress.objects.filter(id=address_id, user=request.user).first()

        if not address:
            return error_response(message="آدرس یافت نشد")

        address.delete()

        return success_response(message="آدرس حذف شد", data={"deleted_id": address_id})


class SilverProductDetailAPIView(APIView):

    permission_classes = [AllowAny]

    def get(self, request, product_id):

        product = (
            SilverProduct.objects.filter(id=product_id, is_active=True)
            .select_related("category")
            .first()
        )

        if not product:
            return error_response(message="محصول یافت نشد", status_code=404)

        serializer = SilverProductSerializer(product, context={"request": request})

        return success_response(message="اطلاعات محصول دریافت شد", data=serializer.data)


# =========================================================
# ORDER HISTORY
# =========================================================


class SilverOrderHistoryAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        queryset = SilverOrder.objects.filter(user=request.user).order_by("-created_at")

        serializer = SilverOrderSerializer(queryset, many=True)

        return success_response(message="سفارشات نقره دریافت شد", data=serializer.data)


from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404


class SilverOrderDetailAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request, order_id):

        order = get_object_or_404(
            SilverOrder.objects.select_related("user").prefetch_related(
                "items", "status_history"
            ),
            id=order_id,
            user=request.user,
        )

        serializer = SilverOrderSerializer(order)

        return success_response(message="جزئیات سفارش نقره", data=serializer.data)


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

        except (ValueError, TypeError):
            return False

    # ==========================================
    # GET
    # ==========================================
    def get(self, request):

        report_type = request.GET.get("type")
        status_filter = request.GET.get("status")
        method_filter = request.GET.get("method")

        start_date_raw = request.GET.get("start_date")
        end_date_raw = request.GET.get("end_date")

        start_date = self.parse_date(start_date_raw)
        end_date = self.parse_date(end_date_raw)

        # ==========================================
        # VALIDATIONS
        # ==========================================
        allowed_types = ["silver", "deposit", "withdraw", "orders"]

        if not report_type:
            return error_response(message="نوع گزارش الزامی است")

        if report_type not in allowed_types:
            return error_response(message="نوع گزارش نامعتبر است")

        if start_date_raw and start_date is False:
            return error_response(message="فرمت تاریخ شروع نامعتبر است")

        if end_date_raw and end_date is False:
            return error_response(message="فرمت تاریخ پایان نامعتبر است")

        if start_date and end_date and start_date > end_date:
            return error_response(message="تاریخ شروع نمی‌تواند بزرگ‌تر باشد")

        # ==========================================
        # SILVER TRANSACTIONS (BUY / SELL)
        # ==========================================
        if report_type == "silver":

            queryset = SilverTransaction.objects.filter(user=request.user)

            if method_filter:
                queryset = queryset.filter(type=method_filter.upper())

            if status_filter:
                queryset = queryset.filter(status=status_filter)

            if start_date:
                queryset = queryset.filter(created_at__date__gte=start_date)

            if end_date:
                queryset = queryset.filter(created_at__date__lte=end_date)

            queryset = queryset.order_by("-created_at")

            serializer = SilverTransactionSerializer(
                queryset, many=True, context={"request": request}
            )

            return success_response(
                message="گزارش معاملات نقره دریافت شد", data=serializer.data
            )

        # ==========================================
        # DEPOSIT (واریز مستقیم + تبدیل طلا -> نقره)
        # ==========================================
        if report_type == "deposit":

            # -----------------------------------------
            # واریزهای مستقیم (type=DEPOSIT)
            # -----------------------------------------
            queryset = SilverFinancialTransaction.objects.filter(
                user=request.user, type="DEPOSIT"
            )

            if method_filter:
                queryset = queryset.filter(method=method_filter.upper())

            if status_filter:
                queryset = queryset.filter(status=status_filter)

            if start_date:
                queryset = queryset.filter(created_at__date__gte=start_date)

            if end_date:
                queryset = queryset.filter(created_at__date__lte=end_date)

            queryset = queryset.order_by("-created_at")[:50]

            serializer = SilverFinancialTransactionSerializer(
                queryset, many=True, context={"request": request}
            )

            combined_data = list(serializer.data)

            # -----------------------------------------
            # تبدیل از طلا به نقره (type=TRANSFER)
            # این‌ها هم از دید کاربر «واریز» به کیف پول نقره هستند
            # -----------------------------------------
            transfer_queryset = SilverFinancialTransaction.objects.filter(
                user=request.user, type="TRANSFER"
            )

            if status_filter:
                transfer_queryset = transfer_queryset.filter(status=status_filter)

            if start_date:
                transfer_queryset = transfer_queryset.filter(created_at__date__gte=start_date)

            if end_date:
                transfer_queryset = transfer_queryset.filter(created_at__date__lte=end_date)

            transfer_queryset = transfer_queryset.order_by("-created_at")[:50]

            transfer_serializer = SilverFinancialTransactionSerializer(
                transfer_queryset, many=True, context={"request": request}
            )

            transfer_data = list(transfer_serializer.data)

            for item in transfer_data:
                item["type"] = "DEPOSIT"
                item["type_display"] = "واریز"
                item["method"] = "GOLD_CONVERT"
                item["method_display"] = "تبدیل از طلا"

            # -----------------------------------------
            # فیلتر method روی نتیجه‌ی نهایی (چون method واقعی
            # در دیتابیس برای این رکوردها BANK است نه GOLD_CONVERT)
            # -----------------------------------------
            if method_filter and method_filter.upper() != "GOLD_CONVERT":
                transfer_data = []
            elif method_filter and method_filter.upper() == "GOLD_CONVERT":
                pass  # نگه‌داشتن همه، چون همه از این نوع‌اند
            # اگر method_filter خالی باشد، همه نمایش داده می‌شوند

            combined_data.extend(transfer_data)

            combined_data.sort(key=lambda item: item.get("created_at") or "", reverse=True)

            return success_response(
                message="گزارش واریزهای نقره دریافت شد", data=combined_data
            )

        # ==========================================
        # WITHDRAW (برداشت مستقیم + انتقال نقره -> طلا)
        # ==========================================
        if report_type == "withdraw":

            queryset = SilverFinancialTransaction.objects.filter(
                user=request.user, type="WITHDRAW"
            )

            if method_filter and method_filter.upper() != "GOLD_CONVERT":
                queryset = queryset.filter(method=method_filter.upper())

            if status_filter:
                queryset = queryset.filter(status=status_filter)

            if start_date:
                queryset = queryset.filter(created_at__date__gte=start_date)

            if end_date:
                queryset = queryset.filter(created_at__date__lte=end_date)

            queryset = queryset.order_by("-created_at")[:50]

            serializer = SilverFinancialTransactionSerializer(
                queryset, many=True, context={"request": request}
            )

            combined_data = list(serializer.data)

            # -----------------------------------------
            # این رکوردها همان تراکنش‌های انتقال نقره -> طلا هستند
            # (در WithdrawAPIView نقره با tracking_code شروع‌شونده با
            # "SLV_TO_GOLD" و method=BANK ساخته می‌شوند)
            # برچسب دقیق‌تر برای نمایش در گزارش قرار می‌دهیم
            # -----------------------------------------
            for item in combined_data:
                if str(item.get("tracking_code", "")).startswith("SLV_TO_GOLD"):
                    item["method"] = "GOLD_CONVERT"
                    item["method_display"] = "تبدیل به طلا"

            # -----------------------------------------
            # اگر method_filter=GOLD_CONVERT بود، فقط همین‌ها را نگه دار
            # -----------------------------------------
            if method_filter and method_filter.upper() == "GOLD_CONVERT":
                combined_data = [
                    item for item in combined_data
                    if item.get("method") == "GOLD_CONVERT"
                ]

            combined_data.sort(key=lambda item: item.get("created_at") or "", reverse=True)

            return success_response(
                message="گزارش برداشت‌های نقره دریافت شد", data=combined_data
            )

        # ==========================================
        # ORDERS
        # ==========================================
        if report_type == "orders":

            queryset = SilverOrder.objects.filter(user=request.user)

            if method_filter:
                queryset = queryset.filter(payment_method=method_filter.upper())

            if status_filter:
                queryset = queryset.filter(status=status_filter)

            if start_date:
                queryset = queryset.filter(created_at__date__gte=start_date)

            if end_date:
                queryset = queryset.filter(created_at__date__lte=end_date)

            queryset = queryset.order_by("-created_at")

            serializer = SilverOrderSerializer(
                queryset, many=True, context={"request": request}
            )

            return success_response(
                message="گزارش سفارشات نقره دریافت شد", data=serializer.data
            )

        return error_response(message="نوع گزارش نامعتبر است")
# =========================================================
# RECENT TRANSACTIONS (SILVER)
# =========================================================


class SilverRecentTransactionsAPIView(APIView):

    permission_classes = [IsAuthenticated]

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

    def get(self, request):

        queryset = SilverFinancialTransaction.objects.filter(user=request.user)

        transaction_type = request.GET.get("type")
        status_filter = request.GET.get("status")

        start_date = self.parse_date(request.GET.get("start_date"))

        end_date = self.parse_date(request.GET.get("end_date"))

        # =====================
        # TYPE
        # =====================

        if transaction_type:
            queryset = queryset.filter(type__iexact=transaction_type)

        # =====================
        # STATUS
        # =====================

        if status_filter:
            queryset = queryset.filter(status__iexact=status_filter)

        # =====================
        # DATE
        # =====================

        if start_date:
            queryset = queryset.filter(created_at__date__gte=start_date)

        if end_date:
            queryset = queryset.filter(created_at__date__lte=end_date)

        queryset = queryset.order_by("-created_at")[:50]

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

                if item.method == "GOLD":
                    title = "برداشت به طلا"

                elif item.method == "BANK":
                    title = "برداشت"

                else:
                    title = "برداشت"

            data.append(
                {
                    "id": item.id,
                    "title": title,
                    "amount": item.amount,
                    "status": item.status,
                    "type": item.type,
                    "method": item.method,
                    "created_at": item.created_at,
                }
            )

        serializer = SilverRecentTransactionSerializer(data, many=True)

        return success_response(message="تراکنش ها دریافت شد", data=serializer.data)


# =========================================================
# RECENT DELIVERIES (SILVER)
# =========================================================


class SilverRecentDeliveriesAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        queryset = SilverOrder.objects.filter(user=request.user).order_by(
            "-created_at"
        )[:10]

        serializer = SilverOrderSerializer(queryset, many=True)

        return success_response(message="تحویل ها دریافت شد", data=serializer.data)


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
            },
        )


# =========================================================
# REFERRAL DASHBOARD (SILVER)
# =========================================================


class SilverReferralDashboardAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        user = request.user

        total_invited = user.subscribers.count()

        total_earned = (
            SilverReferralEarning.objects.filter(user=user).aggregate(
                total=Sum("amount")
            )["total"]
            or 0
        )

        recent_earnings = SilverReferralEarning.objects.filter(user=user).order_by(
            "-created_at"
        )[:10]

        serializer = SilverReferralEarningSerializer(recent_earnings, many=True)

        return success_response(
            message="اطلاعات دعوت دوستان دریافت شد",
            data={
                "referral_code": getattr(user, "referral_code", None),
                "referral_link": f"https://silver.darine.shop/register?ref={getattr(user, 'referral_code', '')}",
                "total_invited": total_invited,
                "total_earned": int(total_earned),
                "recent_earnings": serializer.data,
            },
        )


from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

# =========================================================
# SILVER ASSET VALUE
# =========================================================


class SilverAssetValueAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        user = request.user

        wallet = (
            SilverWallet.objects.only(
                "accessible_toman",
                "blocked_toman",
            )
            .filter(user=user)
            .first()
        )

        inventory = (
            SilverInventory.objects.only(
                "accessible_balance",
                "blocked_balance",
            )
            .filter(user=user)
            .first()
        )

        # =====================================================
        # Wallet
        # =====================================================

        wallet_balance = wallet.accessible_toman if wallet else Decimal("0")

        # =====================================================
        # Silver
        # =====================================================

        silver_balance = (
            (inventory.accessible_balance + inventory.blocked_balance)
            if inventory
            else Decimal("0")
        )

        # =====================================================
        # Prices
        # =====================================================

        silver_price = get_live_silver_price() or Decimal("0")

        # =====================================================
        # Asset Values
        # =====================================================

        silver_asset_value = silver_balance * silver_price

        # این Endpoint فقط برای نقره است
        gold_balance = Decimal("0")
        gold_price = Decimal("0")
        gold_asset_value = Decimal("0")

        total_asset_value = wallet_balance + silver_asset_value

        # =====================================================
        # Response
        # =====================================================

        return Response(
            {
                "total_asset_value": round(total_asset_value),
                "gold_balance": float(gold_balance),
                "silver_balance": float(silver_balance),
                "wallet_balance": round(wallet_balance),
                "gold_asset_value": float(gold_asset_value),
                "silver_asset_value": round(silver_asset_value),
                "gold_price": float(gold_price),
                "silver_price": round(silver_price),
            }
        )


from .utils import get_silver_bubble


class SilverChartAPIView(APIView):

    permission_classes = [AllowAny]

    def get(self, request):

        filter_type = request.GET.get("filter", "24H").upper()

        if filter_type not in ["24H", "WEEKLY", "MONTHLY"]:
            return error_response(message="فیلتر نامعتبر است.")

        data = get_silver_chart_data(filter_type)

        # قیمت لحظه‌ای
        live_price = get_live_silver_price()
        if live_price:
            data["stats"]["current_price"] = int(live_price)

        # حباب
        bubble = get_silver_bubble()
        data["bubble"] = (
            bubble
            if bubble
            else {
                "silver_price": 0,
                "intrinsic_price": 0,
                "bubble_percent": 0,
                "is_positive": False,
            }
        )

        return success_response(message="داده‌های نمودار نقره", data=data)


# =========================================================
# SILVER ANNOUNCEMENTS
# =========================================================
class SilverAnnouncementAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        user = request.user

        announcements = SilverAnnouncement.objects.all().order_by("-created_at")

        read_ids = set(
            SilverAnnouncementRead.objects.filter(
                user=user,
                is_read=True
            ).values_list("announcement_id", flat=True)
        )

        notif_list = []
        unread_count = 0

        for ann in announcements:

            is_read = ann.id in read_ids

            if not is_read:
                unread_count += 1

            notif_list.append({
                "id": ann.id,
                "title": ann.title,
                "description": ann.description,
                "link": ann.link,
                "created_at": ann.created_at.isoformat(),
                "is_read": is_read
            })

        return success_response(
            message="اطلاعیه‌های نقره",
            data={
                "notifList": notif_list,
                "unread_count": unread_count
            }
        )
        
        
        

class SilverAnnouncementMarkReadAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request, pk):

        obj, created = SilverAnnouncementRead.objects.get_or_create(
            user=request.user,
            announcement_id=pk,
            defaults={
                "is_read": True,
                "read_at": timezone.now()
            }
        )

        if not created:
            obj.is_read = True
            obj.read_at = timezone.now()
            obj.save(update_fields=["is_read", "read_at"])

        return success_response(message="اعلان نقره خوانده شد")
    
    
    
    
class SilverAnnouncementMarkAllReadAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request):

        user = request.user
        now = timezone.now()

        announcements = SilverAnnouncement.objects.all().values_list("id", flat=True)

        existing = SilverAnnouncementRead.objects.filter(user=user)

        existing_map = {x.announcement_id: x for x in existing}

        to_create = []
        to_update = []

        for ann_id in announcements:

            if ann_id in existing_map:

                obj = existing_map[ann_id]

                if not obj.is_read:
                    obj.is_read = True
                    obj.read_at = now
                    to_update.append(obj)

            else:
                to_create.append(
                    SilverAnnouncementRead(
                        user=user,
                        announcement_id=ann_id,
                        is_read=True,
                        read_at=now
                    )
                )

        if to_create:
            SilverAnnouncementRead.objects.bulk_create(to_create)

        if to_update:
            SilverAnnouncementRead.objects.bulk_update(
                to_update,
                ["is_read", "read_at"]
            )

        return success_response(message="همه اعلان‌های نقره خوانده شد")
    
    

class SilverBannerListAPIView(APIView):

    permission_classes = [AllowAny]

    def get(self, request):

        banners = SilverBanner.objects.filter(is_active=True).order_by("-id")

        serializer = SilverBannerSerializer(
            banners, many=True, context={"request": request}
        )

        return success_response("بنرهای نقره", serializer.data)


# =========================================================
# SILVER STATISTICS
# =========================================================


class SilverStatisticsAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        user = request.user

        wallet = (
            SilverWallet.objects.only(
                "accessible_toman",
                "blocked_toman",
            )
            .filter(user=user)
            .first()
        )

        inventory = (
            SilverInventory.objects.only(
                "accessible_balance",
                "blocked_balance",
            )
            .filter(user=user)
            .first()
        )

        silver_price = get_live_silver_price() or Decimal("0")

        # =====================================================
        # Wallet
        # =====================================================

        accessible_toman = wallet.accessible_toman if wallet else Decimal("0")

        blocked_toman = wallet.blocked_toman if wallet else Decimal("0")

        wallet_balance = accessible_toman + blocked_toman

        # =====================================================
        # Silver
        # =====================================================

        accessible_silver = inventory.accessible_balance if inventory else Decimal("0")

        blocked_silver = inventory.blocked_balance if inventory else Decimal("0")

        silver_balance = accessible_silver + blocked_silver

        silver_asset_value = silver_balance * silver_price

        # =====================================================
        # Total Assets
        # =====================================================

        total_assets = wallet_balance + silver_asset_value

        # =====================================================
        # Statistics
        # =====================================================

        withdrawn_silver = SilverFinancialTransaction.objects.filter(
            user=user, type="WITHDRAW", status="COMPLETED"
        ).aggregate(total=Sum("amount"))["total"] or Decimal("0")

        return Response(
            {
                "total_assets": round(total_assets),
                "profit": 0,
                "wallet_balance": round(wallet_balance),
                "blocked_wallet_balance": round(blocked_toman),
                "silver_balance": silver_balance,
                "blocked_silver_balance": blocked_silver,
                "silver_price": round(silver_price),
                "silver_asset_value": round(silver_asset_value),
                "withdrawn_silver": round(withdrawn_silver),
                "purchased_giftcards": 0,
                "received_giftcards": 0,
                "pending_toman": round(blocked_toman),
                "pending_silver": blocked_silver,
            }
        )




# silver_app/views.py

from decimal import Decimal, ROUND_DOWN
from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from datetime import datetime

from .models import SilverLimitOrder, SilverTransaction, SilverWallet, SilverInventory
from .serializers import (
    SilverLimitOrderCreateSerializer,
    SilverOrderListSerializer,
)
from .utils import get_live_silver_price, generate_tracking_code, success_response, error_response
from accounts.utils import create_referral_profit


class SilverLimitOrderCreateAPIView(APIView):
    """ایجاد سفارش با قیمت برای نقره"""
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        user = request.user

        serializer = SilverLimitOrderCreateSerializer(
            data=request.data,
            context={'request': request}
        )

        if not serializer.is_valid():
            return error_response(
                message="اطلاعات سفارش نامعتبر است",
                data=serializer.errors
            )

        validated_data = serializer.validated_data
        order_type = validated_data['order_type']
        target_price = validated_data['target_price']
        estimated_weight = validated_data['estimated_weight']
        fee_rate = validated_data['fee_rate']
        amount_toman = validated_data.get('amount_toman')
        silver_weight = validated_data.get('silver_weight')

        if order_type == 'BUY':
            wallet, _ = SilverWallet.objects.select_for_update().get_or_create(user=user)

            if wallet.accessible_toman < amount_toman:
                return error_response("موجودی کیف پول نقره کافی نیست")

            wallet.accessible_toman -= amount_toman
            wallet.blocked_toman += amount_toman
            wallet.save(update_fields=['accessible_toman', 'blocked_toman'])

        else:
            inventory, _ = SilverInventory.objects.select_for_update().get_or_create(user=user)

            if inventory.accessible_balance < silver_weight:
                return error_response("موجودی نقره شما کافی نیست")

            inventory.accessible_balance -= silver_weight
            inventory.blocked_balance += silver_weight
            inventory.save(update_fields=['accessible_balance', 'blocked_balance'])

        order = SilverLimitOrder.objects.create(
            user=user,
            order_type=order_type,
            target_price=target_price,
            amount_toman=amount_toman,
            silver_weight=silver_weight,
            estimated_weight=estimated_weight,
            fee_rate=fee_rate,
            description=request.data.get('description', ''),
        )

        return success_response(
            message="سفارش با قیمت نقره با موفقیت ثبت شد",
            status_code=201,
            data=SilverOrderListSerializer(order).data
        )


class SilverLimitOrderListAPIView(APIView):
    """لیست سفارشات با قیمت نقره"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        order_type = request.GET.get('order_type')
        status = request.GET.get('status')
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        search = request.GET.get('search')

        orders = SilverLimitOrder.objects.filter(user=user)

        if order_type:
            orders = orders.filter(order_type=order_type)

        if status:
            orders = orders.filter(status=status)

        if start_date:
            try:
                start = datetime.strptime(start_date, '%Y-%m-%d')
                orders = orders.filter(created_at__date__gte=start)
            except ValueError:
                pass

        if end_date:
            try:
                end = datetime.strptime(end_date, '%Y-%m-%d')
                orders = orders.filter(created_at__date__lte=end)
            except ValueError:
                pass

        if search:
            orders = orders.filter(description__icontains=search)

        orders = orders.order_by('-created_at')

        serializer = SilverOrderListSerializer(orders, many=True)

        return success_response(
            message="لیست سفارشات با قیمت نقره",
            data={
                "total_results": orders.count(),
                "results": serializer.data
            }
        )


class SilverLimitOrderDetailAPIView(APIView):
    """جزئیات سفارش با قیمت نقره"""
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        user = request.user
        order = get_object_or_404(SilverLimitOrder, pk=pk, user=user)
        serializer = SilverOrderListSerializer(order)
        return success_response(
            message="جزئیات سفارش با قیمت نقره",
            data=serializer.data
        )


class SilverLimitOrderCancelAPIView(APIView):
    """لغو سفارش با قیمت نقره"""
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, pk):
        user = request.user
        order = get_object_or_404(SilverLimitOrder, pk=pk, user=user)

        if order.status != 'PENDING':
            return error_response(
                message=f"سفارش در وضعیت {order.get_status_display()} قابل لغو نیست"
            )

        if order.order_type == 'BUY':
            wallet, _ = SilverWallet.objects.select_for_update().get_or_create(user=user)
            wallet.accessible_toman += order.amount_toman
            wallet.blocked_toman -= order.amount_toman
            wallet.save(update_fields=['accessible_toman', 'blocked_toman'])

        else:
            inventory, _ = SilverInventory.objects.select_for_update().get_or_create(user=user)
            inventory.accessible_balance += order.silver_weight
            inventory.blocked_balance -= order.silver_weight
            inventory.save(update_fields=['accessible_balance', 'blocked_balance'])

        order.status = 'CANCELLED'
        order.description = f"{order.description or ''}\nلغو شده توسط کاربر"
        order.save(update_fields=['status', 'description', 'updated_at'])

        return success_response(
            message="سفارش با موفقیت لغو شد",
            data={
                "order_id": order.id,
                "status": order.get_status_display(),
            }
        )


class SilverLimitOrderExecuteAPIView(APIView):
    """اجرای خودکار سفارش با قیمت نقره"""
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, pk):
        user = request.user
        order = get_object_or_404(SilverLimitOrder, pk=pk, user=user)

        if order.status != 'PENDING':
            return error_response(
                message=f"سفارش در وضعیت {order.get_status_display()} قابل اجرا نیست"
            )

        current_price = get_live_silver_price()
        if not current_price:
            return error_response(message="خطا در دریافت قیمت نقره", status_code=500)

        # بررسی شرط قیمت
        if order.order_type == 'BUY':
            if current_price > order.target_price:
                return error_response(
                    message=f"قیمت فعلی ({current_price}) بیشتر از قیمت مد نظر ({order.target_price}) است"
                )
        else:
            if current_price < order.target_price:
                return error_response(
                    message=f"قیمت فعلی ({current_price}) کمتر از قیمت مد نظر ({order.target_price}) است"
                )

        if order.order_type == 'BUY':
            wallet, _ = SilverWallet.objects.select_for_update().get_or_create(user=user)
            inventory, _ = SilverInventory.objects.select_for_update().get_or_create(user=user)

            if wallet.blocked_toman < order.amount_toman:
                return error_response("مغایرت در موجودی بلوکه شده")

            wallet.blocked_toman -= order.amount_toman
            wallet.save(update_fields=['blocked_toman'])

            fee_rate = Decimal(str(order.fee_rate))
            pure_price = (order.amount_toman / (Decimal("1") + fee_rate)).quantize(Decimal("1"))
            fee = (order.amount_toman - pure_price).quantize(Decimal("1"))
            weight = (pure_price / current_price).quantize(Decimal("0.001"), rounding=ROUND_DOWN)

            inventory.accessible_balance += weight
            inventory.save(update_fields=['accessible_balance'])

            SilverTransaction.objects.create(
                user=user,
                type='BUY',
                status='COMPLETED',
                amount_gr=weight,
                price_per_gram=current_price,
                fee=fee,
                commission_percent=fee_rate * 100,
                commission_amount=fee,
                total_amount=order.amount_toman,
                tracking_code=generate_tracking_code('SBUY'),
                description=f"اجرای خودکار سفارش با قیمت نقره {order.target_price} - {order.description or ''}"
            )

            create_referral_profit(
                user=user,
                source_type='SILVER',
                transaction_amount=order.amount_toman
            )

            order.status = 'EXECUTED'
            order.executed_price = current_price
            order.estimated_weight = weight
            order.save(update_fields=['status', 'executed_price', 'estimated_weight', 'updated_at'])

        else:  # SELL
            wallet, _ = SilverWallet.objects.select_for_update().get_or_create(user=user)
            inventory, _ = SilverInventory.objects.select_for_update().get_or_create(user=user)

            if inventory.blocked_balance < order.silver_weight:
                return error_response("مغایرت در موجودی بلوکه شده نقره")

            inventory.blocked_balance -= order.silver_weight
            inventory.save(update_fields=['blocked_balance'])

            fee_rate = Decimal(str(order.fee_rate))
            pure_price = (current_price * order.silver_weight).quantize(Decimal("1"))
            fee = (pure_price * fee_rate).quantize(Decimal("1"))
            total_price = (pure_price - fee).quantize(Decimal("1"))

            wallet.accessible_toman += total_price
            wallet.save(update_fields=['accessible_toman'])

            SilverTransaction.objects.create(
                user=user,
                type='SELL',
                status='COMPLETED',
                amount_gr=order.silver_weight,
                price_per_gram=current_price,
                fee=fee,
                commission_percent=fee_rate * 100,
                commission_amount=fee,
                total_amount=total_price,
                tracking_code=generate_tracking_code('SSELL'),
                description=f"اجرای خودکار سفارش با قیمت نقره {order.target_price} - {order.description or ''}"
            )

            order.status = 'EXECUTED'
            order.executed_price = current_price
            order.save(update_fields=['status', 'executed_price', 'updated_at'])

        return success_response(
            message="سفارش با قیمت نقره با موفقیت اجرا شد",
            data={
                "order_id": order.id,
                "status": order.get_status_display(),
                "executed_price": float(current_price),
                "estimated_weight": float(order.estimated_weight) if order.estimated_weight else None,
                "amount_toman": float(order.amount_toman) if order.amount_toman else None,
                "silver_weight": float(order.silver_weight) if order.silver_weight else None,
            }
        )


class SilverLimitOrderUpdateAPIView(APIView):
    """ویرایش سفارش با قیمت نقره"""
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def put(self, request, pk):
        user = request.user
        order = get_object_or_404(SilverLimitOrder, pk=pk, user=user)

        if order.status != 'PENDING':
            return error_response(
                message=f"سفارش در وضعیت {order.get_status_display()} قابل ویرایش نیست"
            )

        new_amount_toman = request.data.get('amount_toman')
        new_silver_weight = request.data.get('silver_weight')
        new_target_price = request.data.get('target_price')

        if not new_amount_toman and not new_silver_weight and not new_target_price:
            return error_response(
                message="حداقل یکی از فیلدهای amount_toman، silver_weight یا target_price را وارد کنید"
            )

        if order.order_type == 'BUY':
            if new_amount_toman:
                new_amount_toman = Decimal(str(new_amount_toman)).quantize(Decimal("1"))
                wallet, _ = SilverWallet.objects.select_for_update().get_or_create(user=user)
                
                diff = new_amount_toman - order.amount_toman
                
                if diff > 0:
                    if wallet.accessible_toman < diff:
                        return error_response("موجودی کیف پول نقره برای افزایش مبلغ کافی نیست")
                    wallet.accessible_toman -= diff
                    wallet.blocked_toman += diff
                    wallet.save(update_fields=['accessible_toman', 'blocked_toman'])
                elif diff < 0:
                    diff_abs = abs(diff)
                    if wallet.blocked_toman < diff_abs:
                        return error_response("مغایرت در موجودی بلوکه شده")
                    wallet.blocked_toman -= diff_abs
                    wallet.accessible_toman += diff_abs
                    wallet.save(update_fields=['accessible_toman', 'blocked_toman'])
                
                order.amount_toman = new_amount_toman
                
            if new_target_price:
                new_target_price = Decimal(str(new_target_price)).quantize(Decimal("1"))
                if new_target_price <= 0:
                    return error_response("قیمت مد نظر باید بزرگتر از صفر باشد")
                order.target_price = new_target_price
            
            fee_rate = Decimal(str(order.fee_rate))
            pure_price = (order.amount_toman / (Decimal("1") + fee_rate)).quantize(Decimal("1"))
            estimated_weight = (pure_price / order.target_price).quantize(Decimal("0.001"), rounding=ROUND_DOWN)
            order.estimated_weight = max(estimated_weight, Decimal("0.001"))

        else:  # SELL
            if new_silver_weight:
                new_silver_weight = Decimal(str(new_silver_weight)).quantize(Decimal("0.001"))
                inventory, _ = SilverInventory.objects.select_for_update().get_or_create(user=user)
                
                diff = new_silver_weight - order.silver_weight
                
                if diff > 0:
                    if inventory.accessible_balance < diff:
                        return error_response("موجودی نقره برای افزایش وزن کافی نیست")
                    inventory.accessible_balance -= diff
                    inventory.blocked_balance += diff
                    inventory.save(update_fields=['accessible_balance', 'blocked_balance'])
                elif diff < 0:
                    diff_abs = abs(diff)
                    if inventory.blocked_balance < diff_abs:
                        return error_response("مغایرت در موجودی بلوکه شده نقره")
                    inventory.blocked_balance -= diff_abs
                    inventory.accessible_balance += diff_abs
                    inventory.save(update_fields=['accessible_balance', 'blocked_balance'])
                
                order.silver_weight = new_silver_weight
                order.estimated_weight = new_silver_weight
                
            if new_target_price:
                new_target_price = Decimal(str(new_target_price)).quantize(Decimal("1"))
                if new_target_price <= 0:
                    return error_response("قیمت مد نظر باید بزرگتر از صفر باشد")
                order.target_price = new_target_price

        order.save(update_fields=[
            'amount_toman', 'silver_weight', 'target_price',
            'estimated_weight', 'description', 'updated_at'
        ])

        return success_response(
            message="سفارش با موفقیت ویرایش شد",
            data=SilverOrderListSerializer(order).data
        )