# gold_app/views.py

from decimal import Decimal
import jdatetime
from rest_framework.parsers import MultiPartParser, FormParser
from django.db import transaction
from django.db.models import Q, Sum
from django.utils import timezone

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema
from accounts.models import ReferralEarning
from admin_panel.models import GoldAnnouncement, GoldAnnouncementRead, GoldBanner
from admin_panel.serializers import GoldAnnouncementSerializer, GoldBannerSerializer
from admin_panel.utils import create_admin_log
from silver_app.models import SilverFinancialTransaction, SilverInventory, SilverTransaction, SilverWallet
from silver_app.serializers import SilverFinancialTransactionSerializer
from silver_app.utils import decimal_3, get_live_silver_price
from .models import (
    AutoSavingPlan,
    GiftCard,
    GiftCardOrder,
    GoldBankInfo,
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
    PriceAlert,
)
from .utils import get_live_gold_price, get_gold_chart_data, get_gold_bubble
from .serializers import (
    AutoSavingPlanSerializer,
    GiftCardOrderSerializer,
    GiftCardSerializer,
    GoldOrderListSerializer,
    GoldOrderSerializer,
    PhysicalOrderSerializer,
    ProductCategorySerializer,
    ProductSerializer,
    OrderSerializer,
    PriceAlertSerializer,
    FinancialTransactionSerializer,
    GoldTransactionSerializer,
    BuyGoldSerializer,
    RecentTransactionSerializer,
    ReferralEarningSerializer,
    SellGoldSerializer,
    DepositSerializer,
    UserAddressSerializer,
    WithdrawSerializer,
)
from .utils import get_group_prices, get_latest_price, generate_tracking_code
from datetime import datetime
from datetime import timedelta

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
        {"success": False, "message": str(final_message), "data": {}},  # 👈 همیشه تمیز
        status=status_code,
    )


# =========================================================
# DASHBOARD
# =========================================================


class GoldDashboardAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        user = request.user

        inventory, _ = GoldInventory.objects.get_or_create(user=user)

        wallet, _ = Wallet.objects.get_or_create(user=user)

        gold_price = get_live_gold_price() or Decimal("0")

        gold_balance = Decimal(str(inventory.accessible_balance))

        toman_balance = Decimal(str(wallet.accessible_toman))

        gold_value = gold_balance * gold_price

        total_assets = gold_value + toman_balance

        return success_response(
            message="اطلاعات داشبورد دریافت شد",
            data={
                "gold": {
                    "accessible_balance": gold_balance,
                    "blocked_balance": inventory.blocked_balance,
                    "total_balance": inventory.total_balance,
                },
                "wallet": {
                    "accessible_toman": wallet.accessible_toman,
                    "blocked_toman": wallet.blocked_toman,
                    "toman_total": wallet.toman_total,
                },
                "gold_price": round(gold_price),
                "gold_value": round(gold_value),
                "total_assets": round(total_assets),
            },
        )


# =========================================================
# USER BALANCE
# =========================================================


class UserBalanceAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        inventory, _ = GoldInventory.objects.get_or_create(user=request.user)

        wallet, _ = Wallet.objects.get_or_create(user=request.user)

        gold_price = get_live_gold_price() or Decimal("0")

        gold_asset_value = inventory.accessible_balance * gold_price

        total_assets = gold_asset_value + wallet.accessible_toman

        return success_response(
            message="موجودی دریافت شد",
            data={
                "gold": {
                    "accessible_balance": inventory.accessible_balance,
                    "blocked_balance": inventory.blocked_balance,
                    "total_balance": inventory.total_balance,
                },
                "wallet": {
                    "accessible_toman": wallet.accessible_toman,
                    "blocked_toman": wallet.blocked_toman,
                    "toman_total": wallet.toman_total,
                },
                "current_gold_price": round(gold_price),
                "gold_asset_value": round(gold_asset_value),
                "total_assets": round(total_assets),
            },
        )


# =========================================================
# BUY GOLD
# =========================================================


class BuyGoldAPIView(APIView):

    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):

        user = request.user

        gold_price = get_live_gold_price()

        if not gold_price:

            return error_response(message="خطا در دریافت قیمت طلا", status_code=500)

        serializer = BuyGoldSerializer(
            data=request.data, context={"request": request, "gold_price": gold_price}
        )

        if not serializer.is_valid():

            return error_response(
                message="اطلاعات خرید نامعتبر است", data=serializer.errors
            )

        weight = serializer.validated_data["final_weight"]

        fee = serializer.validated_data["fee"]

        fee_rate = serializer.validated_data["fee_rate"]

        total_toman = serializer.validated_data["total_toman"]

        payment_method = serializer.validated_data["payment_method"]

        if weight <= Decimal("0"):

            return error_response(message="وزن طلا نامعتبر است")

        wallet, _ = Wallet.objects.get_or_create(user=user)

        inventory, _ = GoldInventory.objects.get_or_create(user=user)

        # ==========================
        # پرداخت
        # ==========================

        if payment_method == "WALLET":

            if wallet.balance < total_toman:

                return error_response(message="موجودی کیف پول کافی نیست")

            wallet.balance -= total_toman

            wallet.save(update_fields=["balance"])

        elif payment_method == "GATEWAY":

            FinancialTransaction.objects.create(
                user=user,
                amount=total_toman,
                type="DEPOSIT",
                method="ONLINE",
                status="PENDING",
                tracking_code=generate_tracking_code("PAY"),
                description="پرداخت خرید طلا",
            )

        else:

            return error_response(message="روش پرداخت اشتباه است")

        # ==========================
        # افزایش موجودی طلا
        # ==========================

        inventory.balance = inventory.balance + weight

        if inventory.balance < 0:

            inventory.balance = Decimal("0")

        inventory.save(update_fields=["balance"])

        # ==========================
        # تراکنش طلا
        # ==========================

        tx = GoldTransaction.objects.create(
            user=user,
            type="BUY",
            status="PENDING",
            amount_gr=weight,
            price_per_gram=gold_price,
            fee=fee,
            total_amount=total_toman,
            tracking_code=generate_tracking_code("BUY"),
        )

        create_admin_log(
            request=request,
            user=user,
            action_type="BUY_GOLD",
            action="خرید طلا",
            model_name="GoldTransaction",
            object_id=tx.id,
            tracking_code=tx.tracking_code,
            success=True,
            description=f"""
خرید طلا

کاربر:
{user.mobile}

وزن:
{weight} گرم

قیمت:
{gold_price}

کارمزد:
{fee}

مبلغ:
{total_toman}

موجودی جدید:
{inventory.balance}
""",
        )

        return success_response(
            message="خرید طلا با موفقیت ثبت شد",
            status_code=201,
            data={
                "transaction_id": tx.id,
                "tracking_code": tx.tracking_code,
                "gold_weight": float(weight),
                "fee": float(fee),
                "fee_rate": float(fee_rate),
                "wallet_balance": float(wallet.balance),
                "gold_balance": float(inventory.balance),
            },
        )


# =========================================================
# SELL GOLD
# =========================================================


class SellGoldAPIView(APIView):

    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):

        gold_price = get_live_gold_price()

        if not gold_price:

            return error_response(message="خطا در دریافت قیمت طلا")

        serializer = SellGoldSerializer(
            data=request.data, context={"request": request, "gold_price": gold_price}
        )

        if not serializer.is_valid():

            return error_response(message="اطلاعات نامعتبر است", data=serializer.errors)

        user = request.user

        final_weight = serializer.validated_data["final_weight"]

        final_amount = serializer.validated_data["final_amount"]

        fee = serializer.validated_data["fee"]

        fee_rate = serializer.validated_data["fee_rate"]

        if final_weight <= 0:

            return error_response(message="وزن فروش نامعتبر است")

        inventory, _ = GoldInventory.objects.get_or_create(user=user)

        wallet, _ = Wallet.objects.get_or_create(user=user)

        if inventory.balance < final_weight:

            return error_response(message="موجودی طلای کافی نیست")

        inventory.balance -= final_weight

        if inventory.balance < 0:

            inventory.balance = Decimal("0")

        inventory.save(update_fields=["balance"])

        wallet.balance += final_amount

        wallet.save(update_fields=["balance"])

        tx = GoldTransaction.objects.create(
            user=user,
            type="SELL",
            status="COMPLETED",
            amount_gr=abs(final_weight),
            price_per_gram=gold_price,
            fee=fee,
            total_amount=final_amount,
            tracking_code=generate_tracking_code("SELL"),
        )

        create_admin_log(
            request=request,
            user=user,
            action_type="SELL_GOLD",
            action="فروش طلا",
            model_name="GoldTransaction",
            object_id=tx.id,
            tracking_code=tx.tracking_code,
            success=True,
            description=f"""
فروش طلا

کاربر:
{user.mobile}

وزن:
{final_weight}

مبلغ:
{final_amount}

موجودی باقی مانده:
{inventory.balance}
""",
        )

        return success_response(
            message="فروش طلا انجام شد",
            data={
                "transaction_id": tx.id,
                "tracking_code": tx.tracking_code,
                "gold_weight": float(final_weight),
                "wallet_balance": float(wallet.balance),
                "fee": float(fee),
                "fee_rate": float(fee_rate),
            },
        )


# =========================================================
# DEPOSIT WALLET
# =========================================================


class DepositAPIView(APIView):

    permission_classes = [IsAuthenticated]

    parser_classes = [MultiPartParser, FormParser]

    ONLINE_LIMIT = 400_000_000

    @extend_schema(tags=["Wallet"], request=DepositSerializer, summary="واریز کیف پول")
    @transaction.atomic
    def post(self, request):

        try:

            serializer = DepositSerializer(data=request.data)

            if not serializer.is_valid():

                response = error_response(
                    message="اطلاعات نامعتبر است", data=serializer.errors
                )

                create_admin_log(
                    request=request,
                    admin=None,
                    user=request.user,
                    action_type="DEPOSIT_ERROR",
                    action="خطا در اعتبارسنجی واریز",
                    model_name="FinancialTransaction",
                    description=str(serializer.errors),
                    response_status=response.status_code,
                )

                return response

            user = request.user

            amount = serializer.validated_data["amount"]

            method = serializer.validated_data["method"]

            receipt = serializer.validated_data.get("receipt")

            description = serializer.validated_data.get("description", "")

            wallet, _ = Wallet.objects.get_or_create(user=user)

            # =====================================================
            # CARD TO CARD
            # =====================================================

            if method == "RECEIPT":

                transaction_obj = FinancialTransaction.objects.create(
                    user=user,
                    amount=amount,
                    type="DEPOSIT",
                    method="CARD_TO_CARD",
                    status="PENDING",
                    receipt_image=receipt,
                    tracking_code=generate_tracking_code("DEP"),
                    description=description,
                )

                response = success_response(
                    message="درخواست واریز ثبت شد و پس از تایید ادمین به کیف پول اضافه خواهد شد.",
                    status_code=201,
                    data={
                        "transaction_id": transaction_obj.id,
                        "tracking_code": transaction_obj.tracking_code,
                        "status": transaction_obj.status,
                        "accessible_toman": wallet.accessible_toman,
                        "blocked_toman": wallet.blocked_toman,
                        "toman_total": wallet.toman_total,
                    },
                )

                create_admin_log(
                    request=request,
                    admin=None,
                    user=user,
                    action_type="DEPOSIT",
                    action="ثبت درخواست واریز کارت به کارت",
                    model_name="FinancialTransaction",
                    object_id=transaction_obj.id,
                    tracking_code=transaction_obj.tracking_code,
                    response_status=response.status_code,
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
                        admin=None,
                        user=user,
                        action_type="DEPOSIT_ERROR",
                        action="بیش از سقف مجاز پرداخت آنلاین",
                        model_name="FinancialTransaction",
                        description=f"amount={amount}",
                        response_status=response.status_code,
                    )

                    return response

                transaction_obj = FinancialTransaction.objects.create(
                    user=user,
                    amount=amount,
                    type="DEPOSIT",
                    method="ONLINE",
                    status="COMPLETED",
                    tracking_code=generate_tracking_code("PAY"),
                    description=description,
                )

                wallet.accessible_toman += amount

                wallet.save(update_fields=["accessible_toman", "updated_at"])

                response = success_response(
                    message="واریز با موفقیت انجام شد.",
                    status_code=201,
                    data={
                        "transaction_id": transaction_obj.id,
                        "tracking_code": transaction_obj.tracking_code,
                        "status": transaction_obj.status,
                        "accessible_toman": wallet.accessible_toman,
                        "blocked_toman": wallet.blocked_toman,
                        "toman_total": wallet.toman_total,
                    },
                )

                create_admin_log(
                    request=request,
                    admin=None,
                    user=user,
                    action_type="DEPOSIT",
                    action="واریز آنلاین کیف پول",
                    model_name="FinancialTransaction",
                    object_id=transaction_obj.id,
                    tracking_code=transaction_obj.tracking_code,
                    response_status=response.status_code,
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
                admin=None,
                user=user,
                action_type="DEPOSIT_ERROR",
                action="روش پرداخت نامعتبر",
                model_name="FinancialTransaction",
                response_status=response.status_code,
                description=method,
            )

            return response

        except Exception as e:

            response = error_response(message=str(e), status_code=500)

            create_admin_log(
                request=request,
                admin=None,
                user=request.user if request.user.is_authenticated else None,
                action_type="DEPOSIT_ERROR",
                action="خطا در واریز کیف پول",
                model_name="FinancialTransaction",
                description=str(e),
                response_status=response.status_code,
            )

            return response


# =========================================================
# WITHDRAW
# =========================================================


class WithdrawAPIView(APIView):

    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):

        serializer = WithdrawSerializer(data=request.data, context={"request": request})

        if not serializer.is_valid():

            return error_response(message="اطلاعات نامعتبر است", data=serializer.errors)

        user = request.user

        amount = serializer.validated_data["amount"]

        target = serializer.validated_data["target"]

        wallet, _ = Wallet.objects.get_or_create(user=user)

        # =====================================================
        # CHECK BALANCE
        # =====================================================

        if wallet.accessible_toman < amount:

            create_admin_log(
                request=request,
                admin=None,
                user=user,
                action_type="WITHDRAW_FAILED",
                action="برداشت ناموفق",
                model_name="FinancialTransaction",
                description=f"""
کاربر: {user.mobile}

علت:
موجودی قابل برداشت کافی نیست

مبلغ درخواستی:
{amount:,}

موجودی قابل برداشت:
{wallet.accessible_toman:,}
""",
            )

            return error_response(message="موجودی قابل برداشت کافی نیست")

        # =====================================================
        # BANK WITHDRAW
        # =====================================================

        if target == "BANK":

            card = serializer.validated_data["card"]

            # -----------------------------------------
            # Move money to blocked balance
            # -----------------------------------------

            wallet.accessible_toman -= amount
            wallet.blocked_toman += amount

            wallet.save(
                update_fields=[
                    "accessible_toman",
                    "blocked_toman",
                ]
            )

            transaction_obj = FinancialTransaction.objects.create(
                user=user,
                amount=amount,
                type="WITHDRAW",
                method="BANK",
                status="PENDING",
                user_card=card,
                tracking_code=generate_tracking_code("WDB"),
                admin_note="در انتظار تسویه بانکی",
                description=f"""
برداشت بانکی

کارت:
{card.card_number}

بانک:
{card.bank_name}
""",
            )

            create_admin_log(
                request=request,
                admin=None,
                user=user,
                action_type="WITHDRAW",
                action="درخواست برداشت بانکی",
                model_name="FinancialTransaction",
                tracking_code=transaction_obj.tracking_code,
                object_id=transaction_obj.id,
                description=f"""
کاربر: {user.mobile}

نوع عملیات:
برداشت بانکی

مبلغ:
{amount:,}

شماره کارت:
{card.card_number}

بانک:
{card.bank_name}

موجودی قابل برداشت:
{wallet.accessible_toman:,}

موجودی بلوکه:
{wallet.blocked_toman:,}

وضعیت:
PENDING
""",
            )

            return success_response(
                message="درخواست برداشت با موفقیت ثبت شد",
                data={
                    "transaction_id": transaction_obj.id,
                    "tracking_code": transaction_obj.tracking_code,
                    "status": transaction_obj.status,
                    "accessible_toman": round(wallet.accessible_toman),
                    "blocked_toman": round(wallet.blocked_toman),
                    "card_number": card.card_number,
                },
            )


        # =====================================================
        # CONVERT / TRANSFER TO SILVER PANEL (FIXED)
        # =====================================================
        # =====================================================
        # TRANSFER FROM GOLD WALLET TO SILVER WALLET
        # =====================================================

        elif target == "SILVER":

            silver_price = get_live_silver_price()

            if not silver_price:
                return error_response(
                    message="قیمت نقره دریافت نشد"
                )

            # گرفتن کیف پول‌ها
            wallet = Wallet.objects.select_for_update().get(user=user)
            silver_wallet, _ = SilverWallet.objects.select_for_update().get_or_create(user=user)

            # =========================================
            # چک موجودی تومان در کیف پول طلا
            # =========================================
            if wallet.accessible_toman < amount:
                return error_response(
                    message="موجودی کافی نیست"
                )

            # =========================================
            # کم کردن از کیف پول طلا
            # =========================================
            wallet.accessible_toman = wallet.accessible_toman - amount
            wallet.save(update_fields=["accessible_toman"])

            # =========================================
            # اضافه کردن به کیف پول نقره (TOMAN BALANCE)
            # =========================================
            silver_wallet.accessible_toman = silver_wallet.accessible_toman + amount
            silver_wallet.save(update_fields=["accessible_toman"])

            # =========================================
            # فقط ثبت لاگ نقره (بدون تغییر inventory)
            # =========================================
            silver_weight = decimal_3(amount / silver_price)

            SilverTransaction.objects.create(
                user=user,
                type="BUY",
                status="COMPLETED",
                amount_gr=silver_weight,
                price_per_gram=silver_price,
                total_amount=amount,
                tracking_code=generate_tracking_code("SLV"),
                description="انتقال تومان از کیف پول طلا به کیف پول نقره"
            )

            transaction_obj = SilverFinancialTransaction.objects.create(
                user=user,
                amount=amount,
                type="TRANSFER",
                method="BANK",
                status="COMPLETED",
                tracking_code=generate_tracking_code("TRS"),
                admin_note="انتقال داخلی از طلا به نقره",
                description="انتقال موفق به کیف پول نقره"
            )

            return success_response(
                message="انتقال با موفقیت انجام شد",
                data={
                    "from_wallet": wallet.accessible_toman,
                    "to_silver_wallet": silver_wallet.accessible_toman,
                    "silver_equivalent": float(silver_weight),
                }
            )


        # =====================================================
        # INVALID TARGET
        # =====================================================

        create_admin_log(
            request=request,
            admin=None,
            user=user,
            action_type="WITHDRAW_FAILED",
            action="برداشت نامعتبر",
            model_name="FinancialTransaction",
            description=f"""
کاربر: {user.mobile}

target نامعتبر:
{target}
""",
        )

        return error_response(message="نوع برداشت نامعتبر است")


# =========================================================
# PRODUCTS
# =========================================================


class ProductListAPIView(APIView):

    permission_classes = [AllowAny]

    def get(self, request):

        queryset = (
            Product.objects.filter(is_active=True)
            .select_related("category")
            .order_by("-created_at")
        )

        category = request.GET.get("category")
        delivery_type = request.GET.get("delivery_type")

        if category:
            queryset = queryset.filter(category__slug=category)

        if delivery_type:
            queryset = queryset.filter(delivery_type=delivery_type)

        serializer = ProductSerializer(
            queryset, many=True, context={"request": request}
        )

        return success_response(message="محصولات دریافت شد", data=serializer.data)


from django.db import transaction
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated


class PhysicalOrderAPIView(APIView):

    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):

        serializer = PhysicalOrderSerializer(data=request.data)

        if not serializer.is_valid():
            return error_response(
                message="خطا در داده‌های ارسالی", data=serializer.errors
            )

        user = request.user

        products_data = serializer.validated_data["products"]

        wallet, _ = Wallet.objects.select_for_update().get_or_create(user=user)
        inventory, _ = GoldInventory.objects.select_for_update().get_or_create(
            user=user
        )

        total_gold = Decimal("0")
        total_toman = Decimal("0")

        order_items = []

        # =====================================================
        # VALIDATE PRODUCTS
        # =====================================================
        for item in products_data:

            product = Product.objects.filter(
                id=item["product_id"], is_active=True
            ).first()

            if not product:
                return error_response(message=f"محصول {item['product_id']} یافت نشد")

            quantity = int(item["quantity"])

            if product.inventory_count < quantity:
                return error_response(message=f"موجودی {product.name} کافی نیست")

            item_gold = product.total_weight_with_fees * quantity
            item_toman = product.buy_price * quantity

            total_gold += item_gold
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

        # =====================================================
        # PAYMENT HANDLING
        # =====================================================

        if payment_method == "TOMAN":

            if wallet.accessible_toman < total_toman:
                return error_response(message="موجودی کیف پول کافی نیست")

            # ❗ بهتر: به blocked منتقل شود (نه حذف مستقیم)
            wallet.accessible_toman -= total_toman
            wallet.blocked_toman += total_toman

            wallet.save(
                update_fields=["accessible_toman", "blocked_toman", "updated_at"]
            )

        elif payment_method == "GOLD":

            if inventory.accessible_balance < total_gold:
                return error_response(message="موجودی طلا کافی نیست")

            inventory.accessible_balance -= total_gold
            inventory.blocked_balance += total_gold

            inventory.save(
                update_fields=["accessible_balance", "blocked_balance", "updated_at"]
            )

        else:
            return error_response(message="روش پرداخت نامعتبر است")

        # =====================================================
        # ADDRESS (FIXED + REQUIRED HANDLING)
        # =====================================================

        address_id = serializer.validated_data.get("address_id")

        if address_id:

            address = UserAddress.objects.filter(id=address_id, user=user).first()

            if not address:
                return error_response(message="آدرس انتخابی یافت نشد")

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

        # =====================================================
        # CREATE ORDER
        # =====================================================

        order = Order.objects.create(
            user=user,
            province=address.province,
            city=address.city,
            address=address.address,
            postal_code=address.postal_code,
            plaque=address.plaque,
            unit=address.unit,
            payment_method=payment_method,
            delivery_type=serializer.validated_data["delivery_type"],
            total_gold_amount=total_gold,
            total_toman_amount=total_toman,
            tracking_code=generate_tracking_code("ORD"),
            status="REQUESTED",
        )

        OrderStatusHistory.objects.create(
            order=order, status="REQUESTED", description="سفارش ثبت شد"
        )

        # =====================================================
        # ORDER ITEMS + STOCK
        # =====================================================

        for item in order_items:

            product = item["product"]

            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=item["quantity"],
                price_at_time=item["price_at_time"],
                weight_at_time=item["weight_at_time"],
            )

        # =====================================================
        # RESPONSE (WITH DATE FIX)
        # =====================================================

        return success_response(
            message="سفارش با موفقیت ثبت شد",
            status_code=201,
            data={
                "order_id": order.id,
                "tracking_code": order.tracking_code,
                "status": order.status,
                "status_display": order.get_status_display(),
                # ⏱ تاریخ و ساعت اضافه شد
                "created_at": order.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                "total_gold": float(total_gold),
                "total_price": int(total_toman),
                "wallet": {
                    "accessible_toman": float(wallet.accessible_toman),
                    "blocked_toman": float(wallet.blocked_toman),
                    "toman_total": float(wallet.toman_total),
                },
                "gold_inventory": {
                    "accessible_balance": float(inventory.accessible_balance),
                    "blocked_balance": float(inventory.blocked_balance),
                    "total_balance": float(inventory.total_balance),
                },
            },
        )


class PhysicalOrderNoAddressAPIView(APIView):

    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):

        serializer = PhysicalOrderSerializer(data=request.data)

        if not serializer.is_valid():
            return error_response(
                message="خطا در داده‌های ارسالی",
                data=serializer.errors
            )

        user = request.user

        products_data = serializer.validated_data["products"]
        payment_method = serializer.validated_data["payment_method"]

        if payment_method not in ["TOMAN", "GOLD"]:
            return error_response(message="روش پرداخت نامعتبر است")

        wallet, _ = Wallet.objects.select_for_update().get_or_create(user=user)
        inventory, _ = GoldInventory.objects.select_for_update().get_or_create(user=user)

        total_gold = Decimal("0")
        total_toman = Decimal("0")

        order_items = []
        locked_products = {}

        # =====================================================
        # VALIDATE PRODUCTS (با قفل روی موجودی محصول برای جلوگیری از race condition)
        # =====================================================

        for item in products_data:

            product = (
                Product.objects.select_for_update()
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

            item_gold = product.total_weight_with_fees * quantity
            item_toman = product.buy_price * quantity

            total_gold += item_gold
            total_toman += item_toman

            order_items.append({
                "product": product,
                "quantity": quantity,
                "price_at_time": product.buy_price,
                "weight_at_time": product.total_weight_with_fees,
            })

        # =====================================================
        # PAYMENT HANDLING
        # =====================================================

        if payment_method == "TOMAN":

            if wallet.accessible_toman < total_toman:
                return error_response(message="موجودی کیف پول کافی نیست")

            wallet.accessible_toman -= total_toman
            wallet.blocked_toman += total_toman

            wallet.save(update_fields=["accessible_toman", "blocked_toman"])

        elif payment_method == "GOLD":

            if inventory.accessible_balance < total_gold:
                return error_response(message="موجودی طلا کافی نیست")

            inventory.accessible_balance -= total_gold
            inventory.blocked_balance += total_gold

            inventory.save(update_fields=["accessible_balance", "blocked_balance"])

        # =====================================================
        # DECREASE PRODUCT INVENTORY
        # =====================================================

        # for product_id, requested_qty in locked_products.items():
        #     Product.objects.filter(id=product_id).update(
        #         inventory_count=F("inventory_count") - requested_qty
        #     )

        # =====================================================
        # CREATE ORDER (NO ADDRESS)
        # =====================================================

        order = Order.objects.create(
            user=user,
            province="",
            city="",
            address="",
            postal_code="",
            plaque="",
            unit="",
            payment_method=payment_method,
            total_gold_amount=total_gold,
            total_toman_amount=total_toman,
            tracking_code=generate_tracking_code("ORD"),
            status="REQUESTED",
        )

        OrderStatusHistory.objects.create(
            order=order,
            status="REQUESTED",
            description="سفارش ثبت شد"
        )

        # =====================================================
        # ORDER ITEMS
        # =====================================================

        for item in order_items:

            OrderItem.objects.create(
                order=order,
                product=item["product"],
                quantity=item["quantity"],
                price_at_time=item["price_at_time"],
                weight_at_time=item["weight_at_time"],
            )

        # =====================================================
        # LOG
        # =====================================================

        create_admin_log(
            request=request,
            admin=None,
            user=user,
            action_type="ORDER",
            action="ثبت سفارش فیزیکی",
            model_name="Order",
            tracking_code=order.tracking_code,
            object_id=order.id,
            description=f"""
کاربر: {user.mobile}

روش پرداخت:
{payment_method}

مبلغ تومانی:
{total_toman:,}

وزن طلا:
{total_gold}

موجودی قابل برداشت تومان:
{wallet.accessible_toman:,}

موجودی قابل برداشت طلا:
{inventory.accessible_balance}
""",
        )

        # =====================================================
        # RESPONSE
        # =====================================================

        return success_response(
            message="سفارش با موفقیت ثبت شد",
            status_code=201,
            data={
                "order_id": order.id,
                "tracking_code": order.tracking_code,
                "status": order.status,
                "status_display": order.get_status_display(),
                "created_at": order.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                "total_gold": float(total_gold),
                "total_price": int(total_toman),
                "wallet": {
                    "accessible_toman": float(wallet.accessible_toman),
                    "blocked_toman": float(wallet.blocked_toman),
                },
                "gold_inventory": {
                    "accessible_balance": float(inventory.accessible_balance),
                    "blocked_balance": float(inventory.blocked_balance),
                },
            },
        )


class ProductCategoryListAPIView(APIView):

    permission_classes = [AllowAny]

    def get(self, request):

        queryset = ProductCategory.objects.all().order_by("name")

        serializer = ProductCategorySerializer(queryset, many=True)

        return success_response(
            message="دسته بندی محصولات دریافت شد", data=serializer.data
        )


# =========================================================
# PRODUCT DETAIL
# =========================================================


class ProductDetailAPIView(APIView):

    permission_classes = [AllowAny]

    def get(self, request, product_id):

        product = (
            Product.objects.filter(id=product_id, is_active=True)
            .select_related("category")
            .first()
        )

        if not product:
            return error_response(message="محصول یافت نشد", status_code=404)

        serializer = ProductSerializer(product, context={"request": request})

        return success_response(message="اطلاعات محصول دریافت شد", data=serializer.data)


# =========================================================
# USER ADDRESS LIST
# ========================================================
class UserAddressListAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        addresses = UserAddress.objects.filter(user=request.user).order_by(
            "-created_at"
        )

        serializer = UserAddressSerializer(addresses, many=True)

        return success_response(message="لیست آدرس‌ها دریافت شد", data=serializer.data)


class UserAddressCreateAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request):

        serializer = UserAddressSerializer(data=request.data)

        if not serializer.is_valid():

            return error_response(
                message="خطا در اطلاعات وارد شده", data=serializer.errors
            )

        address = serializer.save(user=request.user)

        return success_response(
            message="آدرس با موفقیت ثبت شد",
            status_code=201,
            data=UserAddressSerializer(address).data,
        )


class UserAddressAPIView(APIView):

    permission_classes = [IsAuthenticated]

    # =========================
    # GET single
    # =========================
    def get(self, request, address_id):

        address = UserAddress.objects.filter(id=address_id, user=request.user).first()

        if not address:
            return error_response("آدرس یافت نشد")

        return success_response(
            message="جزئیات آدرس", data=UserAddressSerializer(address).data
        )

    # =========================
    # UPDATE
    # =========================
    def patch(self, request, address_id):

        address = UserAddress.objects.filter(id=address_id, user=request.user).first()

        if not address:
            return error_response("آدرس یافت نشد")

        serializer = UserAddressSerializer(address, data=request.data, partial=True)

        serializer.is_valid(raise_exception=True)
        serializer.save()

        return success_response(message="آدرس ویرایش شد", data=serializer.data)

    # =========================
    # DELETE
    # =========================
    def delete(self, request, address_id):

        address = UserAddress.objects.filter(id=address_id, user=request.user).first()

        if not address:
            return error_response("آدرس یافت نشد")

        address.delete()

        return success_response(message="آدرس حذف شد", data={"deleted_id": address_id})


# =========================================================
# ORDER HISTORY
# =========================================================


class OrderHistoryAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        queryset = Order.objects.filter(user=request.user).order_by("-created_at")

        serializer = OrderSerializer(queryset, many=True)

        return success_response(message="سفارشات دریافت شد", data=serializer.data)


class OrderDetailAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request, pk):

        order = Order.objects.filter(id=pk, user=request.user).first()

        if not order:
            return error_response(message="سفارش یافت نشد")

        serializer = OrderSerializer(order, context={"request": request})

        return success_response(message="جزئیات سفارش دریافت شد", data=serializer.data)


# =========================================================
# PRICE ALERT
# =========================================================

from django.shortcuts import get_object_or_404
from django.db import transaction
from django.db.models import F

from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from gold_app.models import Wallet
from .models import PriceAlertLog
from .serializers import (
    PriceAlertLogSerializer,
)

SMS_PRICE = Decimal("400")


# =========================================================
# PRICE ALERT
# =========================================================


class PriceAlertAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        queryset = PriceAlert.objects.filter(user=request.user)

        status_filter = request.query_params.get("status")

        if status_filter == "ACTIVE":

            queryset = queryset.filter(
                is_active=True, sent_notifications__lt=F("max_notifications")
            )

        elif status_filter == "INACTIVE":

            queryset = queryset.filter(is_active=False)

        elif status_filter == "COMPLETED":

            queryset = queryset.filter(sent_notifications=F("max_notifications"))

        queryset = queryset.order_by("-created_at")

        serializer = PriceAlertSerializer(queryset, many=True)

        return success_response("لیست هشدارهای قیمت", serializer.data)

    @transaction.atomic
    def post(self, request):

        serializer = PriceAlertSerializer(data=request.data)

        serializer.is_valid(raise_exception=True)

        max_notifications = serializer.validated_data["max_notifications"]

        total_cost = SMS_PRICE * Decimal(max_notifications)

        wallet, _ = Wallet.objects.select_for_update().get_or_create(user=request.user)

        # ==========================================
        # بررسی موجودی قابل استفاده
        # ==========================================

        if wallet.accessible_toman < total_cost:

            return error_response(
                f"برای ثبت این هشدار حداقل {int(total_cost):,} تومان موجودی لازم است."
            )

        # ==========================================
        # انتقال مبلغ از موجودی قابل استفاده به بلوکه
        # ==========================================

        wallet.accessible_toman -= total_cost

        wallet.blocked_toman += total_cost

        wallet.save(update_fields=["accessible_toman", "blocked_toman", "updated_at"])

        # ==========================================
        # ایجاد هشدار
        # ==========================================

        alert = serializer.save(user=request.user)

        return success_response(
            "هشدار با موفقیت ثبت شد",
            {
                "alert": PriceAlertSerializer(alert).data,
                "sms_price": int(SMS_PRICE),
                "alarm_count": max_notifications,
                "total_price": int(total_cost),
                "wallet": {
                    "accessible_toman": int(wallet.accessible_toman),
                    "blocked_toman": int(wallet.blocked_toman),
                    "toman_total": int(wallet.toman_total),
                },
            },
        )


# =========================================================
# DELETE PRICE ALERT (CANCEL)
# =========================================================


class DeletePriceAlertAPIView(APIView):

    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def delete(self, request, pk):

        alert = get_object_or_404(PriceAlert, id=pk, user=request.user)

        if alert.status == "FINISHED":

            return error_response("این هشدار قبلاً تکمیل شده است.")

        wallet = Wallet.objects.select_for_update().get(user=request.user)

        remaining_count = alert.max_notifications - alert.sent_notifications

        refund_amount = Decimal(remaining_count) * SMS_PRICE

        if refund_amount > 0:

            wallet.blocked_toman -= refund_amount

            if wallet.blocked_toman < 0:
                wallet.blocked_toman = Decimal("0")

            wallet.accessible_toman += refund_amount

            wallet.save(
                update_fields=[
                    "accessible_toman",
                    "blocked_toman",
                    "updated_at",
                ]
            )

        alert.status = "CANCELLED"
        alert.is_active = False

        alert.save(
            update_fields=[
                "status",
                "is_active",
            ]
        )

        return success_response(
            "هشدار لغو شد و مبلغ باقی‌مانده بازگردانده شد",
            {
                "alert_id": alert.id,
                "sent_count": alert.sent_notifications,
                "remaining_count": remaining_count,
                "refund_amount": int(refund_amount),
                "wallet": {
                    "accessible_toman": int(wallet.accessible_toman),
                    "blocked_toman": int(wallet.blocked_toman),
                    "toman_total": int(wallet.toman_total),
                },
            },
        )


# =========================================================
# ENABLE / DISABLE ALERT
# =========================================================


class TogglePriceAlertAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request, pk):

        alert = get_object_or_404(PriceAlert, id=pk, user=request.user)

        alert.is_active = not alert.is_active
        alert.save(update_fields=["is_active"])

        return success_response(
            "وضعیت هشدار تغییر کرد", {"id": alert.id, "is_active": alert.is_active}
        )


# =========================================================
# ALERT LOGS
# =========================================================


class PriceAlertLogAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        logs = PriceAlertLog.objects.filter(alert__user=request.user).order_by(
            "-created_at"
        )

        serializer = PriceAlertLogSerializer(logs, many=True)

        return success_response("سوابق ارسال هشدار", serializer.data)


# =========================================================
# REPORT
# =========================================================


class PriceAlertReportAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        alerts = PriceAlert.objects.filter(user=request.user)

        logs = PriceAlertLog.objects.filter(alert__user=request.user)

        data = {
            "alerts": {
                "total": alerts.count(),
                "active": alerts.filter(
                    is_active=True, sent_notifications__lt=F("max_notifications")
                ).count(),
                "inactive": alerts.filter(is_active=False).count(),
                "completed": alerts.filter(
                    sent_notifications=F("max_notifications")
                ).count(),
            },
            "notifications": {
                "total": logs.count(),
                "success": logs.filter(sms_status="SUCCESS").count(),
                "failed": logs.filter(sms_status="FAILED").count(),
                "insufficient_balance": logs.filter(
                    sms_status="INSUFFICIENT_BALANCE"
                ).count(),
            },
            "logs": PriceAlertLogSerializer(
                logs.order_by("-created_at"), many=True
            ).data,
        }

        return success_response("گزارش هشدارهای قیمت", data)






# =========================================================
# REPORTS (GOLD)
# =========================================================


class ReportsAPIView(APIView):

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

        # -----------------------------------------
        # نرمال‌سازی ورودی‌ها (رفع باگ حساس بودن به بزرگی/کوچکی حروف)
        # -----------------------------------------

        report_type = (request.GET.get("type") or "").strip().lower()
        status_filter = request.GET.get("status")
        method_filter = request.GET.get("method")

        start_date = self.parse_date(request.GET.get("start_date"))

        end_date = self.parse_date(request.GET.get("end_date"))

        # =====================================================
        # FINANCIAL (DEPOSIT / WITHDRAW)
        # =====================================================
        if report_type in ["deposit", "withdraw"]:

            transaction_type = "DEPOSIT" if report_type == "deposit" else "WITHDRAW"

            queryset = FinancialTransaction.objects.filter(
                user=request.user, type=transaction_type
            )

            # method
            if method_filter:

                queryset = queryset.filter(method__iexact=method_filter)

            # status
            if status_filter:

                queryset = queryset.filter(status__iexact=status_filter)

            # date
            if start_date:

                queryset = queryset.filter(created_at__date__gte=start_date)

            if end_date:

                queryset = queryset.filter(created_at__date__lte=end_date)

            queryset = queryset.order_by("-created_at")

            serializer = FinancialTransactionSerializer(
                queryset, many=True, context={"request": request}
            )

            combined_data = list(serializer.data)

            # =====================================================
            # اضافه کردن انتقال (طلا -> نقره) به گزارش برداشت
            # =====================================================

            if report_type == "withdraw":

                silver_queryset = SilverFinancialTransaction.objects.filter(
                    user=request.user, type="TRANSFER"
                )

                if status_filter:

                    silver_queryset = silver_queryset.filter(status__iexact=status_filter)

                if start_date:

                    silver_queryset = silver_queryset.filter(created_at__date__gte=start_date)

                if end_date:

                    silver_queryset = silver_queryset.filter(created_at__date__lte=end_date)

                silver_queryset = silver_queryset.order_by("-created_at")

                silver_serializer = SilverFinancialTransactionSerializer(
                    silver_queryset, many=True, context={"request": request}
                )

                silver_data = list(silver_serializer.data)

                # -----------------------------------------
                # این تراکنش‌ها در واقع "برداشت به روش تبدیل به نقره" هستند
                # -----------------------------------------

                for item in silver_data:
                    item["type"] = "WITHDRAW"
                    item["type_display"] = "برداشت"
                    item["method"] = "SILVER"
                    item["method_display"] = "تبدیل به نقره"

                combined_data.extend(silver_data)

            # =====================================================
            # اضافه کردن انتقال (نقره -> طلا) به گزارش واریز طلا
            # =====================================================

            if report_type == "deposit":

                silver_to_gold_queryset = SilverFinancialTransaction.objects.filter(
                    user=request.user,
                    type="WITHDRAW",
                    tracking_code__startswith="SLV_TO_GOLD",
                )

                if status_filter:

                    silver_to_gold_queryset = silver_to_gold_queryset.filter(
                        status__iexact=status_filter
                    )

                if start_date:

                    silver_to_gold_queryset = silver_to_gold_queryset.filter(
                        created_at__date__gte=start_date
                    )

                if end_date:

                    silver_to_gold_queryset = silver_to_gold_queryset.filter(
                        created_at__date__lte=end_date
                    )

                silver_to_gold_queryset = silver_to_gold_queryset.order_by("-created_at")

                silver_to_gold_serializer = SilverFinancialTransactionSerializer(
                    silver_to_gold_queryset, many=True, context={"request": request}
                )

                silver_to_gold_data = list(silver_to_gold_serializer.data)

                # -----------------------------------------
                # این تراکنش‌ها در واقع "واریز به روش تبدیل از نقره" هستند
                # -----------------------------------------

                for item in silver_to_gold_data:
                    item["type"] = "DEPOSIT"
                    item["type_display"] = "واریز"
                    item["method"] = "SILVER"
                    item["method_display"] = "تبدیل از نقره"

                combined_data.extend(silver_to_gold_data)

            # -----------------------------------------
            # فیلتر method روی نتیجه‌ی نهایی (چون method واقعی
            # این رکوردها در دیتابیس BANK است نه SILVER)
            # -----------------------------------------

            if method_filter and method_filter.upper() == "SILVER":

                combined_data = [
                    item for item in combined_data
                    if item.get("method") == "SILVER"
                ]

            # -----------------------------------------
            # مرتب‌سازی نهایی بر اساس تاریخ (جدیدترین اول)
            # -----------------------------------------

            combined_data.sort(key=lambda item: item.get("created_at") or "", reverse=True)

            return success_response(
                message=(
                    "گزارش واریزها" if report_type == "deposit" else "گزارش برداشت‌ها"
                ),
                data=combined_data,
            )

        # =====================================================
        # GOLD
        # =====================================================

        if report_type == "gold":

            queryset = GoldTransaction.objects.filter(user=request.user)

            if method_filter:

                queryset = queryset.filter(type__iexact=method_filter)

            if status_filter:

                queryset = queryset.filter(status__iexact=status_filter)

            if start_date:

                queryset = queryset.filter(created_at__date__gte=start_date)

            if end_date:

                queryset = queryset.filter(created_at__date__lte=end_date)

            queryset = queryset.order_by("-created_at")

            serializer = GoldTransactionSerializer(
                queryset, many=True, context={"request": request}
            )

            return success_response(message="گزارش معاملات طلا", data=serializer.data)

        # =====================================================
        # ORDERS
        # =====================================================

        if report_type == "orders":

            queryset = Order.objects.filter(user=request.user)

            if method_filter:

                queryset = queryset.filter(payment_method__iexact=method_filter)

            if status_filter:

                queryset = queryset.filter(status__iexact=status_filter)

            if start_date:

                queryset = queryset.filter(created_at__date__gte=start_date)

            if end_date:

                queryset = queryset.filter(created_at__date__lte=end_date)

            queryset = queryset.order_by("-created_at")

            serializer = OrderSerializer(
                queryset, many=True, context={"request": request}
            )

            return success_response(message="گزارش سفارشات", data=serializer.data)

        return error_response(message="نوع گزارش نامعتبر است")




# =========================================================
# RECENT TRANSACTIONS (GOLD)
# =========================================================


class RecentTransactionsAPIView(APIView):

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

        queryset = FinancialTransaction.objects.filter(user=request.user)

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
        # DATE FILTER
        # (باگ قبلی: تاریخ خام و پارس‌نشده فیلتر می‌شد و
        # با فرمت جلالی کرش می‌کرد یا نتیجه‌ی خالی می‌داد)
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

                elif item.method == "SILVER":
                    title = "واریز از نقرینه"

                else:
                    title = "واریز"

            else:

                if item.method == "SILVER":
                    title = "برداشت به نقرینه"

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

        serializer = RecentTransactionSerializer(data, many=True)

        return success_response(message="تراکنش ها دریافت شد", data=serializer.data)


# =========================================================
# RECENT DELIVERIES
# =========================================================


class RecentDeliveriesAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        queryset = Order.objects.filter(user=request.user).order_by("-created_at")[:10]

        serializer = OrderSerializer(queryset, many=True)

        return success_response(message="تحویل ها دریافت شد", data=serializer.data)


# =========================================================
# REFERRAL DASHBOARD
# =========================================================


class ReferralDashboardAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        user = request.user

        total_invited = user.subscribers.count()

        total_earned = (
            ReferralEarning.objects.filter(referrer=user, source_type="GOLD").aggregate(
                total=Sum("amount")
            )["total"]
            or 0
        )

        recent_earnings = ReferralEarning.objects.filter(
            referrer=user, source_type="GOLD"
        ).order_by("-created_at")[:10]

        serializer = ReferralEarningSerializer(recent_earnings, many=True)

        return success_response(
            message="اطلاعات دعوت دوستان دریافت شد",
            data={
                "referral_code": user.referral_code,
                "referral_link": f"https://gold.darine.shop/register?ref={user.referral_code}",
                "total_invited": total_invited,
                "total_earned": int(total_earned),
                "recent_earnings": serializer.data,
            },
        )


# =========================================================
# AUTO SAVING PLAN
# =========================================================


class AutoSavingPlanAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        plans = AutoSavingPlan.objects.filter(user=request.user).order_by("-created_at")

        serializer = AutoSavingPlanSerializer(plans, many=True)

        return success_response(
            message="پلن های پس انداز دریافت شد", data=serializer.data
        )

    def post(self, request):

        saving_type = request.data.get("type")
        amount = request.data.get("amount")

        if not saving_type:

            return error_response(message="نوع پلن الزامی است")

        if not amount:

            return error_response(message="مبلغ الزامی است")

        # =====================================
        # PERIOD DAYS
        # =====================================

        if saving_type == "DAILY":

            period_days = 1

        elif saving_type == "WEEKLY":

            period_days = 7

        elif saving_type == "MONTHLY":

            period_days = 30

        else:

            return error_response(message="نوع پلن نامعتبر است")

        # =====================================
        # CREATE PLAN
        # =====================================

        plan = AutoSavingPlan.objects.create(
            user=request.user,
            type=saving_type,
            amount=amount,
            period_days=period_days,
            next_execute_at=timezone.now() + timedelta(days=period_days),
            status="ACTIVE",
        )

        serializer = AutoSavingPlanSerializer(plan)

        return success_response(
            message="پلن پس انداز ایجاد شد", data=serializer.data, status_code=201
        )

    def delete(self, request):

        plan_id = request.data.get("plan_id")

        try:

            plan = AutoSavingPlan.objects.get(id=plan_id, user=request.user)

        except AutoSavingPlan.DoesNotExist:

            return error_response(message="پلن یافت نشد")

        plan.delete()

        return success_response(message="پلن حذف شد")


# =========================================================
# GIFT CARD ORDER
# =========================================================


class GiftCardOrderAPIView(APIView):

    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):

        serializer = GiftCardOrderSerializer(data=request.data)

        if not serializer.is_valid():

            return error_response(message="اطلاعات نامعتبر است", data=serializer.errors)

        user = request.user

        # =====================================
        # WALLET
        # =====================================

        wallet, _ = Wallet.objects.get_or_create(user=user)

        gold_price = get_live_gold_price()

        if not gold_price:

            return error_response(message="خطا در دریافت قیمت طلا")

        weight_per_card = Decimal(serializer.validated_data["weight_per_card"])

        quantity = serializer.validated_data["quantity"]

        total_weight = weight_per_card * quantity

        total_price = total_weight * Decimal(gold_price)

        if wallet.accessible_toman < total_price:

            return error_response(message="موجودی کیف پول کافی نیست")

        # =====================================
        # ADDRESS
        # =====================================

        address_id = serializer.validated_data.get("address_id")

        province = None
        city = None
        address = None
        postal_code = None
        plaque = None
        unit = None

        # استفاده از آدرس ذخیره شده

        if address_id:

            saved_address = UserAddress.objects.filter(id=address_id, user=user).first()

            if not saved_address:

                return error_response(message="آدرس یافت نشد")

            province = saved_address.province
            city = saved_address.city
            address = saved_address.address
            postal_code = saved_address.postal_code
            plaque = saved_address.plaque
            unit = saved_address.unit

        # ثبت آدرس جدید

        else:

            province = serializer.validated_data.get("province")

            city = serializer.validated_data.get("city")

            address = serializer.validated_data.get("address")

            if not province or not city or not address:

                return error_response(message="اطلاعات آدرس ناقص است")

            postal_code = serializer.validated_data.get("postal_code")

            plaque = serializer.validated_data.get("plaque")

            unit = serializer.validated_data.get("unit")

            UserAddress.objects.create(
                user=user,
                province=province,
                city=city,
                address=address,
                postal_code=postal_code,
                plaque=plaque,
                unit=unit,
            )

        # =====================================
        # DECREASE WALLET
        # =====================================

        wallet.accessible_toman -= total_price

        wallet.save(update_fields=["accessible_toman", "updated_at"])

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
            status="PENDING",
            tracking_code=generate_tracking_code("GFT"),
        )

        # =====================================
        # CREATE GIFT CARDS
        # =====================================

        cards = []

        for _ in range(quantity):

            card = GiftCard.objects.create(
                serial_number=generate_tracking_code("CARD"),
                weight=weight_per_card,
                created_by=user,
                status="ACTIVE",
                is_used=False,
            )

            cards.append(
                {"serial_number": card.serial_number, "weight": float(card.weight)}
            )

        return success_response(
            message="سفارش کارت هدیه ثبت شد",
            status_code=201,
            data={
                "order_id": order.id,
                "tracking_code": order.tracking_code,
                "total_price": int(total_price),
                "wallet": {
                    "accessible_toman": int(wallet.accessible_toman),
                    "blocked_toman": int(wallet.blocked_toman),
                    "toman_total": int(wallet.toman_total),
                },
                "cards": cards,
            },
        )


# =========================================================
# GIFT CARD ORDERS
# =========================================================


class GiftCardOrderListAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        queryset = GiftCardOrder.objects.filter(user=request.user).order_by(
            "-created_at"
        )

        serializer = GiftCardOrderSerializer(queryset, many=True)

        return success_response(message="لیست سفارشات کارت هدیه", data=serializer.data)


# =========================================================
# REDEEM GIFT CARD
# =========================================================


class RedeemGiftCardAPIView(APIView):

    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):

        serial = request.data.get("serial_number")

        if not serial:

            return error_response(message="کد کارت الزامی است")

        try:

            card = GiftCard.objects.get(
                serial_number=serial, status="ACTIVE", is_used=False
            )

        except GiftCard.DoesNotExist:

            return error_response(message="کارت هدیه نامعتبر است")

        inventory, _ = GoldInventory.objects.get_or_create(user=request.user)

        inventory.balance += card.weight
        inventory.save()

        card.is_used = True
        card.status = "USED"
        card.activated_by = request.user
        card.used_at = timezone.now()
        card.save()

        return success_response(
            message="کارت هدیه فعال شد",
            data={"weight_added": card.weight, "new_balance": inventory.balance},
        )


# =========================================================
# GIFT CARD LIST
# =========================================================


class GiftCardListAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        queryset = GiftCard.objects.filter(
            Q(created_by=request.user) | Q(activated_by=request.user)
        )

        # =====================================
        # STATUS FILTER
        # ACTIVE | INACTIVE
        # =====================================

        status = request.query_params.get("status")

        if status:

            status = status.upper()

            if status == "ACTIVE":

                queryset = queryset.filter(status="ACTIVE")

            elif status == "INACTIVE":

                queryset = queryset.exclude(status="ACTIVE")

        # =====================================
        # DATE FILTER
        # =====================================

        start_date = request.query_params.get("start_date")

        end_date = request.query_params.get("end_date")

        try:

            if start_date:

                if "/" in start_date:

                    y, m, d = map(int, start_date.split("/"))

                    start_date = jdatetime.date(y, m, d).togregorian()

                else:

                    start_date = datetime.strptime(start_date, "%Y-%m-%d").date()

                queryset = queryset.filter(created_at__date__gte=start_date)

            if end_date:

                if "/" in end_date:

                    y, m, d = map(int, end_date.split("/"))

                    end_date = jdatetime.date(y, m, d).togregorian()

                else:

                    end_date = datetime.strptime(end_date, "%Y-%m-%d").date()

                queryset = queryset.filter(created_at__date__lte=end_date)

        except Exception:

            return error_response(
                message="فرمت تاریخ اشتباه است (1405/03/13 یا 2026-06-03)"
            )

        queryset = queryset.order_by("-created_at")

        serializer = GiftCardSerializer(queryset, many=True)

        return success_response(message="لیست کارت هدیه", data=serializer.data)


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

        orders = Order.objects.filter(user=request.user).order_by("-created_at")

        for item in orders:

            data.append(
                {
                    "id": item.id,
                    "type": "PRODUCT_ORDER",
                    "province": item.province,
                    "city": item.city,
                    "address": item.address,
                    "postal_code": item.postal_code,
                    "plaque": item.plaque,
                    "unit": item.unit,
                }
            )

        # =====================================
        # GIFT CARD ORDERS
        # =====================================

        gifts = GiftCardOrder.objects.filter(user=request.user).order_by("-created_at")

        for item in gifts:

            data.append(
                {
                    "id": item.id,
                    "type": "GIFT_CARD_ORDER",
                    "province": item.province,
                    "city": item.city,
                    "address": item.address,
                    "postal_code": item.postal_code,
                    "plaque": item.plaque,
                    "unit": item.unit,
                }
            )

        return success_response(message="آدرس‌ها دریافت شد", data=data)


# =========================================================
# CREATE GOLD LIMIT ORDER
# =========================================================


class GoldLimitOrderCreateAPIView(APIView):

    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):

        serializer = GoldOrderSerializer(data=request.data)

        if not serializer.is_valid():

            return error_response(message="اطلاعات نامعتبر است", data=serializer.errors)

        user = request.user

        order_type = serializer.validated_data["order_type"]

        target_price = Decimal(serializer.validated_data["target_price"])

        amount_toman = serializer.validated_data.get("amount_toman")

        gold_weight = serializer.validated_data.get("gold_weight")

        fee_rate = Decimal("0.0099")

        if order_type == "BUY":

            amount_toman = Decimal(amount_toman)

            fee = amount_toman * fee_rate

            net_amount = amount_toman - fee

            estimated_weight = net_amount / target_price

        else:

            gold_weight = Decimal(gold_weight)

            estimated_weight = gold_weight

        order = GoldOrder.objects.create(
            user=user,
            order_type=order_type,
            target_price=target_price,
            amount_toman=amount_toman,
            gold_weight=gold_weight,
            estimated_weight=estimated_weight,
            status="PENDING",
        )

        return success_response(
            message="سفارش با موفقیت ثبت شد",
            status_code=201,
            data={
                "order_id": order.id,
                "status": order.status,
            },
        )


# =========================================================
# GOLD LIMIT ORDER LIST
# =========================================================


class GoldLimitOrderListAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        orders = GoldOrder.objects.filter(user=request.user).order_by("-created_at")

        serializer = GoldOrderListSerializer(orders, many=True)

        return success_response(message="لیست سفارشات", data=serializer.data)


# =========================================================
# GOLD DEPOSIT INFORMATION
# =========================================================


class GoldDepositInfoAPIView(APIView):

    permission_classes = [AllowAny]

    def get(self, request):

        bank = GoldBankInfo.objects.filter(is_active=True).first()

        if not bank:
            return error_response(message="اطلاعات بانکی طلا ثبت نشده")

        return success_response(
            message="اطلاعات واریز طلا",
            data={
                "card_number": bank.card_number,
                "full_name": bank.full_name,
                "sheba": bank.sheba,
            },
        )


# =========================================================
# GOLD ANNOUNCEMENTS
# =========================================================
class GoldAnnouncementAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        user = request.user

        announcements = GoldAnnouncement.objects.all().order_by("-created_at")

        read_ids = set(
            GoldAnnouncementRead.objects.filter(
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
            message="اطلاعیه‌های طلا",
            data={
                "notifList": notif_list,
                "unread_count": unread_count
            }
        )
        
        

class GoldAnnouncementMarkReadAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request, pk):

        obj, created = GoldAnnouncementRead.objects.get_or_create(
            user=request.user,
            announcement_id=pk,
            defaults={"is_read": True, "read_at": timezone.now()}
        )

        if not created:
            obj.is_read = True
            obj.read_at = timezone.now()
            obj.save(update_fields=["is_read", "read_at"])

        return success_response(message="خوانده شد")
    
    
class GoldAnnouncementMarkAllReadAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request):

        user = request.user

        now = timezone.now()

        announcements = GoldAnnouncement.objects.all().values_list("id", flat=True)

        existing = GoldAnnouncementRead.objects.filter(
            user=user
        )

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
                    GoldAnnouncementRead(
                        user=user,
                        announcement_id=ann_id,
                        is_read=True,
                        read_at=now
                    )
                )

        if to_create:
            GoldAnnouncementRead.objects.bulk_create(to_create)

        if to_update:
            GoldAnnouncementRead.objects.bulk_update(
                to_update,
                ["is_read", "read_at"]
            )

        return success_response(
            message="همه اعلان‌ها خوانده شد"
        )


# =========================================================
# LATEST PRICE
# =========================================================


class LatestPriceAPIView(APIView):

    permission_classes = [AllowAny]

    def get(self, request):

        key = request.GET.get("key")

        if not key:
            return error_response(message="key الزامی است")

        price = get_latest_price(key)

        if not price:
            return error_response(message="قیمت یافت نشد")

        return success_response(message="آخرین قیمت دریافت شد", data=price)


# =========================================================
# GOLD CHART API
# =========================================================


class GoldChartAPIView(APIView):

    permission_classes = [AllowAny]

    def get(self, request):

        filter_type = request.GET.get("filter", "24H").upper()

        if filter_type not in ["24H", "WEEKLY", "MONTHLY"]:
            return error_response(
                message="فیلتر نامعتبر است. مقادیر مجاز: 24H, WEEKLY, MONTHLY"
            )

        data = get_gold_chart_data(filter_type)

        live_price = get_live_gold_price()
        if live_price:
            data["stats"]["current_price"] = int(live_price)

        bubble = get_gold_bubble()
        data["bubble"] = (
            bubble
            if bubble
            else {
                "buy_price": 0,
                "sell_price": 0,
                "bubble_amount": 0,
                "bubble_percent": 0,
                "is_positive": False,
            }
        )

        return success_response(message="داده‌های نمودار طلا", data=data)


# =========================================================
# GOLD BANNERS
# =========================================================


class GoldBannerListAPIView(APIView):

    permission_classes = [AllowAny]

    def get(self, request):

        banners = GoldBanner.objects.filter(is_active=True).order_by("-id")

        serializer = GoldBannerSerializer(
            banners, many=True, context={"request": request}
        )

        return success_response("بنرهای طلا", serializer.data)


# =========================================================
# GOLD PRICE
# =========================================================


class GoldPriceAPIView(APIView):

    permission_classes = [AllowAny]

    def get(self, request):

        data = get_group_prices("gold")

        if not data:
            return error_response(message="قیمت طلا یافت نشد")

        return success_response(message="قیمت لحظه‌ای طلا", data=data)


# =========================================================
# COIN PRICE
# =========================================================


class CoinPriceAPIView(APIView):

    permission_classes = [AllowAny]

    def get(self, request):

        data = get_group_prices("coin")

        if not data:
            return error_response(message="قیمت سکه یافت نشد")

        return success_response(message="قیمت لحظه‌ای سکه", data=data)


# =========================================================
# PARSIAN PRICE
# =========================================================


class ParsianPriceAPIView(APIView):

    permission_classes = [AllowAny]

    def get(self, request):

        data = get_group_prices("parsian")

        if not data:
            return error_response(message="قیمت پارسیان یافت نشد")

        return success_response(message="قیمت لحظه‌ای پارسیان", data=data)


# =========================================================
# ASSET VALUE
# =========================================================

from decimal import Decimal

from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from gold_app.models import GoldInventory

from gold_app.utils import get_live_gold_price
from decimal import Decimal

# =========================================================
# ASSET VALUE
# =========================================================


class AssetValueAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        user = request.user

        wallet = (
            Wallet.objects.only(
                "accessible_toman",
                "blocked_toman",
            )
            .filter(user=user)
            .first()
        )

        gold_inventory = (
            GoldInventory.objects.only(
                "accessible_balance",
                "blocked_balance",
            )
            .filter(user=user)
            .first()
        )

        silver_inventory = (
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
        # Gold
        # =====================================================

        gold_balance = (
            (gold_inventory.accessible_balance + gold_inventory.blocked_balance)
            if gold_inventory
            else Decimal("0")
        )

        # =====================================================
        # Silver
        # =====================================================

        silver_balance = (
            (silver_inventory.accessible_balance + silver_inventory.blocked_balance)
            if silver_inventory
            else Decimal("0")
        )

        # =====================================================
        # Prices
        # =====================================================

        gold_price = get_live_gold_price() or Decimal("0")

        silver_price = get_live_silver_price() or Decimal("0")

        # =====================================================
        # Asset Values
        # =====================================================

        gold_asset_value = gold_balance * gold_price

        silver_asset_value = silver_balance * silver_price

        total_asset_value = wallet_balance + gold_asset_value + silver_asset_value

        return Response(
            {
                "total_asset_value": round(total_asset_value),
                "gold_balance": gold_balance,
                "silver_balance": silver_balance,
                "wallet_balance": round(wallet_balance),
                "gold_asset_value": round(gold_asset_value),
                "silver_asset_value": round(silver_asset_value),
                "gold_price": round(gold_price),
                "silver_price": round(silver_price),
            }
        )


# =========================================================
# GOLD STATISTICS
# =========================================================


class GoldStatisticsAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        user = request.user

        wallet = (
            Wallet.objects.only(
                "accessible_toman",
                "blocked_toman",
            )
            .filter(user=user)
            .first()
        )

        inventory = (
            GoldInventory.objects.only(
                "accessible_balance",
                "blocked_balance",
            )
            .filter(user=user)
            .first()
        )

        gold_price = get_live_gold_price() or Decimal("0")

        # =====================================================
        # Wallet
        # =====================================================

        accessible_toman = wallet.accessible_toman if wallet else Decimal("0")

        blocked_toman = wallet.blocked_toman if wallet else Decimal("0")

        wallet_balance = accessible_toman + blocked_toman

        # =====================================================
        # Gold
        # =====================================================

        accessible_gold = inventory.accessible_balance if inventory else Decimal("0")

        blocked_gold = inventory.blocked_balance if inventory else Decimal("0")

        gold_balance = accessible_gold + blocked_gold

        gold_asset_value = gold_balance * gold_price

        # =====================================================
        # Total Assets
        # =====================================================

        total_assets = wallet_balance + gold_asset_value

        # =====================================================
        # Statistics
        # =====================================================

        withdrawn_gold = FinancialTransaction.objects.filter(
            user=user, type="WITHDRAW", status="COMPLETED"
        ).aggregate(total=Sum("amount"))["total"] or Decimal("0")

        purchased_giftcards = GiftCardOrder.objects.filter(user=user).aggregate(
            total=Sum("total_price")
        )["total"] or Decimal("0")

        return Response(
            {
                "total_assets": round(total_assets),
                "profit": 0,
                "wallet_balance": round(wallet_balance),
                "blocked_wallet_balance": round(blocked_toman),
                "gold_balance": gold_balance,
                "blocked_gold_balance": blocked_gold,
                "gold_price": round(gold_price),
                "gold_asset_value": round(gold_asset_value),
                "withdrawn_gold": round(withdrawn_gold),
                "purchased_giftcards": round(purchased_giftcards),
                "received_giftcards": 0,
                "pending_toman": round(blocked_toman),
                "pending_gold": blocked_gold,
            }
        )
