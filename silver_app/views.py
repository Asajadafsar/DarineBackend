# =========================================================
# SILVER APP VIEWS
# =========================================================

from datetime import datetime
from decimal import Decimal
from django.db import transaction
from django.db.models import Sum
from django.utils import timezone
from rest_framework.parsers import MultiPartParser, FormParser
from django.db import transaction
from decimal import Decimal

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from drf_spectacular.utils import extend_schema

from admin_panel.models import SilverAnnouncement, SilverBanner
from admin_panel.serializers import SilverAnnouncementSerializer, SilverBannerSerializer
from admin_panel.utils import create_admin_log

from .models import (
    SilverOrderStatusHistory,
    SilverWallet,
    SilverFinancialTransaction,
    SilverInventory
)

from .serializers import (
    SilverDepositSerializer,
    SilverWithdrawSerializer
)

from .utils import generate_tracking_code

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

from .views import success_response, error_response
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
# BUY SILVER API
# =========================================================

class BuySilverAPIView(APIView):

    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):

        try:

            silver_price = get_live_silver_price()

            if not silver_price:

                response = error_response(
                    message="خطا در دریافت قیمت نقره",
                    status_code=500
                )

                create_admin_log(
                    request=request,
                    user=request.user,
                    action_type="SYSTEM",
                    action="خطا در دریافت قیمت نقره",
                    model_name="SilverTransaction",
                    response_status=response.status_code,
                    success=False,
                    error_message="silver price unavailable"
                )

                return response


            serializer = BuySilverSerializer(
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
            total_toman = serializer.validated_data["total_toman"]
            weight = serializer.validated_data["final_weight"]


            wallet, _ = SilverWallet.objects.get_or_create(
                user=user
            )

            inventory, _ = SilverInventory.objects.get_or_create(
                user=user
            )


            old_balance = wallet.balance
            old_silver = inventory.balance


            payment_method = serializer.validated_data["payment_method"]


            if payment_method == "WALLET":


                if wallet.balance < total_toman:

                    response = error_response(
                        message="موجودی کافی نیست"
                    )


                    create_admin_log(
                        request=request,
                        user=user,
                        action_type="PAYMENT",
                        action="خرید نقره ناموفق - موجودی کم",
                        model_name="SilverTransaction",
                        response_status=response.status_code,
                        success=False,
                        description=f"amount={total_toman}"
                    )

                    return response



                wallet.balance -= total_toman

                wallet.save()



            elif payment_method == "GATEWAY":


                SilverFinancialTransaction.objects.create(

                    user=user,

                    amount=total_toman,

                    type="DEPOSIT",

                    method="ONLINE",

                    status="PENDING",

                    tracking_code=generate_tracking_code(
                        "SLV_PAY"
                    ),

                    description="پرداخت خرید نقره"

                )



            inventory.balance += weight

            inventory.save()



            tx = SilverTransaction.objects.create(

                user=user,

                type="BUY",

                status="PENDING",

                amount_gr=weight,

                price_per_gram=silver_price,

                fee=fee,

                total_amount=total_toman,

                tracking_code=generate_tracking_code(
                    "BUY_SLV"
                )
            )



            response = success_response(
                message="خرید نقره ثبت شد",
                status_code=201,
                data={
                    "transaction_id": tx.id
                }
            )


            create_admin_log(

                request=request,

                user=user,

                action_type="BUY_SILVER",

                action="خرید نقره",

                model_name="SilverTransaction",

                object_id=tx.id,

                tracking_code=tx.tracking_code,

                response_status=response.status_code,

                success=True,

                old_data={

                    "wallet_balance": str(old_balance),

                    "silver_balance": str(old_silver)

                },

                new_data={

                    "wallet_balance": str(wallet.balance),

                    "silver_balance": str(inventory.balance)

                },

                description=f"""

کاربر:
{user.mobile}


وزن خرید:
{weight}


قیمت گرم:
{silver_price}


مبلغ:
{total_toman}


روش پرداخت:
{payment_method}

"""

            )


            return response



        except Exception as e:


            response = error_response(
                message=str(e),
                status_code=500
            )


            create_admin_log(

                request=request,

                user=request.user,

                action_type="SYSTEM",

                action="خطای خرید نقره",

                model_name="SilverTransaction",

                response_status=response.status_code,

                success=False,

                error_message=str(e)

            )


            return response

# =========================================================
# SELL SILVER
# =========================================================


class SellSilverAPIView(APIView):

    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):

        try:

            silver_price = get_live_silver_price()

            if not silver_price:

                response = error_response(
                    message="خطا در دریافت قیمت نقره",
                    status_code=500
                )

                create_admin_log(
                    request=request,
                    user=request.user,
                    action_type="SYSTEM",
                    action="خطا در دریافت قیمت نقره برای فروش",
                    model_name="SilverTransaction",
                    response_status=response.status_code,
                    success=False,
                    error_message="silver price unavailable"
                )

                return response


            serializer = SellSilverSerializer(
                data=request.data,
                context={
                    "request": request,
                    "silver_price": silver_price
                }
            )


            serializer.is_valid(
                raise_exception=True
            )


            user = request.user


            fee = serializer.validated_data["fee"]

            fee_rate = serializer.validated_data["fee_rate"]

            final_amount = serializer.validated_data["final_amount"]

            final_weight = serializer.validated_data["final_weight"]



            inventory, _ = SilverInventory.objects.get_or_create(
                user=user
            )


            wallet, _ = SilverWallet.objects.get_or_create(
                user=user
            )


            # موجودی قبل از عملیات

            old_silver = inventory.balance

            old_wallet = wallet.balance



            if inventory.balance < final_weight:


                response = error_response(
                    message="موجودی نقره کافی نیست"
                )


                create_admin_log(
                    request=request,
                    user=user,
                    action_type="SELL_SILVER",
                    action="فروش نقره ناموفق - موجودی کم",
                    model_name="SilverTransaction",
                    response_status=response.status_code,
                    success=False,
                    description=f"""
موجودی:
{inventory.balance}

درخواست:
{final_weight}
"""
                )


                return response



            # کم کردن نقره

            inventory.balance -= final_weight

            inventory.save(
                update_fields=[
                    "balance"
                ]
            )



            # اضافه کردن تومان

            wallet.balance += final_amount

            wallet.save(
                update_fields=[
                    "balance"
                ]
            )



            tx = SilverTransaction.objects.create(

                user=user,

                type="SELL",

                status="COMPLETED",

                amount_gr=final_weight,

                price_per_gram=silver_price,

                fee=fee,

                total_amount=final_amount,

                tracking_code=generate_tracking_code(
                    "SELL_SLV"
                )
            )



            response = success_response(
                message="فروش نقره انجام شد",
                status_code=201,
                data={

                    "transaction_id": tx.id,

                    "tracking_code":
                        tx.tracking_code,

                    "silver_weight":
                        float(final_weight),

                    "fee":
                        float(fee),

                    "wallet_balance":
                        float(wallet.balance)

                }
            )



            create_admin_log(

                request=request,

                user=user,

                action_type="SELL_SILVER",

                action="فروش نقره",

                model_name="SilverTransaction",

                object_id=tx.id,

                tracking_code=tx.tracking_code,

                response_status=response.status_code,

                success=True,


                old_data={

                    "silver_balance":
                        str(old_silver),

                    "wallet_balance":
                        str(old_wallet)

                },


                new_data={

                    "silver_balance":
                        str(inventory.balance),

                    "wallet_balance":
                        str(wallet.balance)

                },


                description=f"""

کاربر:
{user.mobile}


نوع عملیات:
فروش نقره


وزن:
{final_weight}


قیمت گرم:
{silver_price}


کارمزد:
{fee}


درصد کارمزد:
{fee_rate}


مبلغ دریافتی:
{final_amount}


کد پیگیری:
{tx.tracking_code}

"""

            )



            return response



        except Exception as e:


            response = error_response(
                message=str(e),
                status_code=500
            )


            create_admin_log(

                request=request,

                user=request.user,

                action_type="SYSTEM",

                action="خطای سیستمی فروش نقره",

                model_name="SilverTransaction",

                response_status=response.status_code,

                success=False,

                error_message=str(e),

                description=str(e)

            )


            return response





# =========================================================
# DEPOSIT WALLET (SILVER)
# =========================================================

class DepositAPIView(APIView):

    permission_classes = [IsAuthenticated]

    parser_classes = [
        MultiPartParser,
        FormParser
    ]

    ONLINE_LIMIT = 400_000_000

    @extend_schema(
        tags=["Silver Wallet"],
        request=SilverDepositSerializer,
        summary="واریز کیف پول نقره"
    )
    @transaction.atomic
    def post(self, request):

        try:

            serializer = SilverDepositSerializer(
                data=request.data
            )

            if not serializer.is_valid():

                response = error_response(
                    message="اطلاعات نامعتبر است",
                    data=serializer.errors
                )

                create_admin_log(
                    request=request,
                    user=request.user,
                    action_type="PAYMENT",
                    action="خطا در اعتبارسنجی واریز نقره",
                    model_name="SilverFinancialTransaction",
                    response_status=response.status_code,
                    success=False,
                    description=str(serializer.errors)
                )

                return response

            user = request.user

            amount = serializer.validated_data["amount"]

            method = serializer.validated_data["method"]

            receipt = serializer.validated_data.get(
                "receipt"
            )

            description = serializer.validated_data.get(
                "description",
                ""
            )

            wallet, _ = SilverWallet.objects.get_or_create(
                user=user
            )

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

                    tracking_code=generate_tracking_code(
                        "SLV_DEP"
                    ),

                    description=description

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

                        "toman_total": wallet.toman_total

                    }

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

"""

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

                        description=f"amount={amount}"

                    )

                    return response

                tx = SilverFinancialTransaction.objects.create(

                    user=user,

                    amount=amount,

                    type="DEPOSIT",

                    method="ONLINE",

                    status="COMPLETED",

                    tracking_code=generate_tracking_code(
                        "SLV_PAY"
                    ),

                    description=description

                )

                wallet.accessible_toman += amount

                wallet.save(

                    update_fields=[

                        "accessible_toman",

                        "updated_at"

                    ]

                )

                response = success_response(

                    message="واریز با موفقیت انجام شد.",

                    status_code=201,

                    data={

                        "transaction_id": tx.id,

                        "tracking_code": tx.tracking_code,

                        "status": tx.status,

                        "accessible_toman": wallet.accessible_toman,

                        "blocked_toman": wallet.blocked_toman,

                        "toman_total": wallet.toman_total

                    }

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

"""

                )

                return response

            response = error_response(
                message="روش واریز نامعتبر است"
            )

            create_admin_log(

                request=request,

                user=user,

                action_type="PAYMENT",

                action="روش پرداخت نامعتبر",

                model_name="SilverFinancialTransaction",

                response_status=response.status_code,

                success=False,

                description=method

            )

            return response

        except Exception as e:

            response = error_response(

                message=str(e),

                status_code=500

            )

            create_admin_log(

                request=request,

                user=request.user if request.user.is_authenticated else None,

                action_type="SYSTEM",

                action="خطا در واریز کیف پول نقره",

                model_name="SilverFinancialTransaction",

                response_status=response.status_code,

                success=False,

                error_message=str(e)

            )

            return response


# =========================================================
# WITHDRAW WALLET (SILVER)
# =========================================================

class WithdrawAPIView(APIView):

    permission_classes = [IsAuthenticated]


    @transaction.atomic
    def post(self, request):

        try:

            serializer = SilverWithdrawSerializer(
                data=request.data,
                context={
                    "request": request
                }
            )


            # =========================
            # VALIDATION
            # =========================

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
                    action="خطا در اعتبارسنجی برداشت نقره",
                    model_name="SilverFinancialTransaction",
                    response_status=response.status_code,
                    success=False,
                    description=str(serializer.errors)
                )


                return response



            user = request.user


            amount = serializer.validated_data.get(
                "amount"
            )


            target = serializer.validated_data.get(
                "target"
            )


            card_id = serializer.validated_data.get(
                "card_id"
            )


            wallet, _ = SilverWallet.objects.get_or_create(
                user=user
            )



            # =========================
            # CHECK BALANCE
            # =========================

            if wallet.balance < amount:


                response = error_response(
                    message="موجودی کافی نیست"
                )


                create_admin_log(
                    request=request,
                    admin=None,
                    user=user,
                    action_type="PAYMENT",
                    action="برداشت ناموفق نقره",
                    model_name="SilverFinancialTransaction",
                    response_status=response.status_code,
                    success=False,
                    description=f"""
کاربر:
{user.mobile}

علت:
موجودی کافی نیست

مبلغ درخواست:
{amount:,}

موجودی:
{wallet.balance:,}
"""
                )


                return response



            # =========================
            # BANK WITHDRAW
            # =========================

            if target == "BANK":


                if not card_id:


                    response = error_response(
                        message="کارت بانکی الزامی است"
                    )


                    create_admin_log(
                        request=request,
                        admin=None,
                        user=user,
                        action_type="PAYMENT",
                        action="برداشت بانکی بدون کارت",
                        model_name="SilverFinancialTransaction",
                        response_status=response.status_code,
                        success=False,
                        description="card_id ارسال نشده"
                    )


                    return response



                card = BankCard.objects.filter(
                    id=card_id,
                    user=user
                ).first()



                if not card:


                    response = error_response(
                        message="کارت یافت نشد"
                    )


                    create_admin_log(
                        request=request,
                        admin=None,
                        user=user,
                        action_type="SECURITY",
                        action="کارت بانکی نامعتبر",
                        model_name="SilverFinancialTransaction",
                        response_status=response.status_code,
                        success=False,
                        description=f"""
user:
{user.mobile}

card_id:
{card_id}
"""
                    )


                    return response



                wallet.balance -= amount


                wallet.save(
                    update_fields=[
                        "balance"
                    ]
                )



                tx = SilverFinancialTransaction.objects.create(
                    user=user,
                    amount=amount,
                    type="WITHDRAW",
                    method="BANK",
                    status="PENDING",
                    user_card=card,
                    tracking_code=generate_tracking_code(
                        "SLV_WDB"
                    ),
                    admin_note="در انتظار تسویه بانکی",
                    description=f"""
برداشت بانکی

کارت:
{card.card_number}

بانک:
{card.bank_name}
"""
                )


                response = success_response(
                    message="درخواست برداشت ثبت شد و در انتظار تایید است",
                    data={
                        "transaction_id": tx.id,
                        "tracking_code": tx.tracking_code,
                        "status": tx.status,
                        "wallet_balance": int(wallet.balance),
                        "card_number": card.card_number
                    }
                )
                create_admin_log(
                    request=request,
                    admin=None,
                    user=user,
                    action_type="PAYMENT",
                    action="درخواست برداشت بانکی نقره",
                    model_name="SilverFinancialTransaction",
                    object_id=tx.id,
                    tracking_code=tx.tracking_code,
                    response_status=response.status_code,
                    success=True,
                    description=f"""
کاربر:
{user.mobile}

نوع عملیات:
برداشت بانکی نقره

مبلغ:
{amount:,}

کارت:
{card.card_number}

بانک:
{card.bank_name}

موجودی جدید کیف پول:
{wallet.balance:,}

وضعیت:
PENDING
"""
                )


                return response



            # =========================
            # CONVERT TO SILVER
            # =========================

            elif target == "SILVER":


                silver_price = Decimal(
                    "1"
                )


                silver_inventory, _ = SilverInventory.objects.get_or_create(
                    user=user
                )


                silver_weight = (
                    amount / silver_price
                )



                wallet.balance -= amount


                wallet.save(
                    update_fields=[
                        "balance"
                    ]
                )



                silver_inventory.balance += silver_weight


                silver_inventory.save(
                    update_fields=[
                        "balance"
                    ]
                )



                tx = SilverFinancialTransaction.objects.create(
                    user=user,
                    amount=amount,
                    type="WITHDRAW",
                    method="SILVER",
                    status="COMPLETED",
                    tracking_code=generate_tracking_code(
                        "SLV_CONVERT"
                    ),
                    admin_note="تبدیل کیف پول به نقره",
                    description="تبدیل موجودی کیف پول به نقره"
                )



                response = success_response(
                    message="تبدیل به نقره انجام شد",
                    data={
                        "transaction_id": tx.id,
                        "tracking_code": tx.tracking_code,
                        "silver_weight": round(
                            silver_weight,
                            5
                        ),
                        "wallet_balance": int(wallet.balance)
                    }
                )



                create_admin_log(
                    request=request,
                    admin=None,
                    user=user,
                    action_type="SILVER",
                    action="تبدیل کیف پول به نقره",
                    model_name="SilverFinancialTransaction",
                    object_id=tx.id,
                    tracking_code=tx.tracking_code,
                    response_status=response.status_code,
                    success=True,
                    description=f"""
کاربر:
{user.mobile}

نوع عملیات:
تبدیل موجودی کیف پول به نقره

مبلغ:
{amount:,}

وزن نقره:
{silver_weight:.5f}

موجودی جدید:
{wallet.balance:,}

وضعیت:
COMPLETED
"""
                )


                return response



            # =========================
            # INVALID TARGET
            # =========================


            response = error_response(
                message="نوع برداشت نامعتبر است"
            )


            create_admin_log(
                request=request,
                admin=None,
                user=user,
                action_type="PAYMENT",
                action="نوع برداشت نامعتبر",
                model_name="SilverFinancialTransaction",
                response_status=response.status_code,
                success=False,
                description=f"""
کاربر:
{user.mobile}

target:
{target}
"""
            )


            return response



        # =========================
        # EXCEPTION
        # =========================


        except Exception as e:


            response = error_response(
                message=str(e),
                status_code=500
            )


            create_admin_log(
                request=request,
                admin=None,
                user=request.user if request.user.is_authenticated else None,
                action_type="SYSTEM",
                action="خطا در برداشت کیف پول نقره",
                model_name="SilverFinancialTransaction",
                response_status=response.status_code,
                success=False,
                error_message=str(e),
                description=str(e)
            )


            return response


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

        products_data = serializer.validated_data["products"]

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
                "weight_at_time": product.total_weight_with_fees,
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

            status="REQUESTED"
        )

        # =========================
        # FIRST ORDER STATUS
        # =========================

        SilverOrderStatusHistory.objects.create(
            order=order,
            status="REQUESTED",
            description="سفارش توسط کاربر ثبت شد."
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

            product.inventory_count -= item["quantity"]

            product.save(
                update_fields=["inventory_count"]
            )

        return success_response(

            message="سفارش نقره ثبت شد",

            status_code=201,

            data={

                "order_id": order.id,

                "tracking_code": order.tracking_code,

                "status": order.status,

                "status_display": order.get_status_display(),

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



        serializer = UserAddressSerializer(
            addresses,
            many=True
        )

        return success_response(
            message="لیست آدرس‌ها دریافت شد",
            data=serializer.data
        )


# =========================================================
# USER ADDRESS CREATE
# =========================================================

class SilverUserAddressCreateAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request):



        serializer = UserAddressSerializer(data=request.data)

        if not serializer.is_valid():

            print("SERIALIZER ERRORS:", serializer.errors)

            return error_response(
                data=serializer.errors
            )

        address = UserAddress.objects.create(
            user=request.user,
            province=serializer.validated_data["province"],
            city=serializer.validated_data["city"],
            address=serializer.validated_data["address"],
            postal_code=serializer.validated_data.get("postal_code"),
            plaque=serializer.validated_data.get("plaque"),
            unit=serializer.validated_data.get("unit"),
        )

        print("CREATED ADDRESS ID:", address.id)

        addresses = UserAddress.objects.filter(
            user=request.user
        ).order_by("-created_at")

        print("ADDRESS COUNT AFTER CREATE:", addresses.count())
        print("ADDRESSES AFTER CREATE:", list(addresses.values()))
        print("==========================================\n")

        return success_response(
            message="آدرس ثبت شد",
            status_code=201,
            data=UserAddressSerializer(address).data
        )
        
        

class SilverProductDetailAPIView(APIView):

    permission_classes = [AllowAny]

    def get(self, request, product_id):

        product = SilverProduct.objects.filter(
            id=product_id,
            is_active=True
        ).select_related(
            "category"
        ).first()

        if not product:
            return error_response(
                message="محصول یافت نشد",
                status_code=404
            )

        serializer = SilverProductSerializer(
            product,
            context={"request": request}
        )

        return success_response(
            message="اطلاعات محصول دریافت شد",
            data=serializer.data
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

            queryset = SilverTransaction.objects.filter(
                user=request.user
            )

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
                queryset,
                many=True,
                context={"request": request}
            )

            return success_response(
                message="گزارش معاملات نقره دریافت شد",
                data=serializer.data
            )

        # ==========================================
        # DEPOSIT
        # ==========================================
        if report_type == "deposit":

            queryset = SilverFinancialTransaction.objects.filter(
                user=request.user,
                type="DEPOSIT"
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
                queryset,
                many=True,
                context={"request": request}
            )

            return success_response(
                message="گزارش واریزهای نقره دریافت شد",
                data=serializer.data
            )

        # ==========================================
        # WITHDRAW
        # ==========================================
        if report_type == "withdraw":

            queryset = SilverFinancialTransaction.objects.filter(
                user=request.user,
                type="WITHDRAW"
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
                queryset,
                many=True,
                context={"request": request}
            )

            return success_response(
                message="گزارش برداشت‌های نقره دریافت شد",
                data=serializer.data
            )

        # ==========================================
        # ORDERS
        # ==========================================
        if report_type == "orders":

            queryset = SilverOrder.objects.filter(
                user=request.user
            )

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
                queryset,
                many=True,
                context={"request": request}
            )

            return success_response(
                message="گزارش سفارشات نقره دریافت شد",
                data=serializer.data
            )

        return error_response(message="نوع گزارش نامعتبر است")
    

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
    


# =========================================================
# SILVER ASSET VALUE
# =========================================================

class SilverAssetValueAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        user = request.user

        wallet = SilverWallet.objects.filter(
            user=user
        ).first()

        inventory = SilverInventory.objects.filter(
            user=user
        ).first()

        accessible_toman = (
            wallet.accessible_toman
            if wallet
            else Decimal("0")
        )

        blocked_toman = (
            wallet.blocked_toman
            if wallet
            else Decimal("0")
        )

        toman_total = (
            wallet.toman_total
            if wallet
            else Decimal("0")
        )

        accessible_silver = (
            inventory.accessible_balance
            if inventory
            else Decimal("0")
        )

        blocked_silver = (
            inventory.blocked_balance
            if inventory
            else Decimal("0")
        )

        silver_total = (
            inventory.total_balance
            if inventory
            else Decimal("0")
        )

        silver_price = (
            get_live_silver_price()
            or Decimal("0")
        )

        silver_asset_value = (
            accessible_silver * silver_price
        )

        total_asset_value = (
            toman_total +
            silver_asset_value
        )

        return Response({

            "total_asset_value": round(
                total_asset_value
            ),

            "wallet": {

                "accessible_toman": round(
                    accessible_toman
                ),

                "blocked_toman": round(
                    blocked_toman
                ),

                "toman_total": round(
                    toman_total
                )

            },

            "silver": {

                "accessible_silver": accessible_silver,

                "blocked_silver": blocked_silver,

                "silver_total": silver_total,

                "asset_value": round(
                    silver_asset_value
                ),

                "price": round(
                    silver_price
                )

            }

        })

# silver_app/views.py

from .utils import get_live_silver_price, get_silver_chart_data, get_silver_bubble

class SilverChartAPIView(APIView):

    permission_classes = [AllowAny]

    def get(self, request):

        filter_type = request.GET.get('filter', '24H').upper()

        if filter_type not in ['24H', 'WEEKLY', 'MONTHLY']:
            return error_response(
                message="فیلتر نامعتبر است."
            )

        data = get_silver_chart_data(filter_type)

        # قیمت لحظه‌ای
        live_price = get_live_silver_price()
        if live_price:
            data["stats"]["current_price"] = int(live_price)

        # حباب
        bubble = get_silver_bubble()
        data["bubble"] = bubble if bubble else {
            "silver_price": 0,
            "intrinsic_price": 0,
            "bubble_percent": 0,
            "is_positive": False,
        }

        return success_response(
            message="داده‌های نمودار نقره",
            data=data
        )



# =========================================================
# SILVER ANNOUNCEMENTS
# =========================================================

class SilverAnnouncementAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        announcements = SilverAnnouncement.objects.all().order_by("-created_at")

        serializer = SilverAnnouncementSerializer(
            announcements,
            many=True,
            context={
                "request": request
            }
        )

        return success_response(
            message="اطلاعیه‌های نقره",
            data=serializer.data
        )


class SilverBannerListAPIView(APIView):

    permission_classes = [AllowAny]

    def get(self, request):

        banners = SilverBanner.objects.filter(
            is_active=True
        ).order_by("-id")

        serializer = SilverBannerSerializer(
            banners,
            many=True,
            context={"request": request}
        )

        return success_response(
            "بنرهای نقره",
            serializer.data
        )




class SilverStatisticsAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        user = request.user

        silver_price = (
            get_live_silver_price()
            or Decimal("0")
        )

        wallet = SilverWallet.objects.filter(
            user=user
        ).first()

        inventory = SilverInventory.objects.filter(
            user=user
        ).first()

        wallet_balance = (
            wallet.balance
            if wallet
            else Decimal("0")
        )

        silver_balance = (
            inventory.balance
            if inventory
            else Decimal("0")
        )

        total_assets = (
            wallet_balance +
            (silver_balance * silver_price)
        )

        pending_toman = (
            SilverFinancialTransaction.objects.filter(
                user=user,
                status="PENDING"
            ).aggregate(
                total=Sum("amount")
            )["total"]
            or Decimal("0")
        )

        pending_silver = (
            inventory.blocked_balance
            if inventory
            else Decimal("0")
        )

        withdrawn_silver = (
            SilverFinancialTransaction.objects.filter(
                user=user,
                type="WITHDRAW",
                status="COMPLETED"
            ).aggregate(
                total=Sum("amount")
            )["total"]
            or Decimal("0")
        )

        return Response({

            "total_assets": int(
                total_assets
            ),

            "profit": 0,

            "withdrawn_silver": str(
                withdrawn_silver
            ),

            "purchased_giftcards": 0,

            "received_giftcards": 0,

            "pending_toman": int(
                pending_toman
            ),

            "pending_silver": str(
                pending_silver
            )

        })