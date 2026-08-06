from admin_panel.models import (
    GoldBalanceAdjustment,
    SilverBalanceAdjustment,
)
from datetime import timedelta
import psutil
from rest_framework.viewsets import ModelViewSet, ViewSet
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db.models import Sum
from django.db import transaction
from admin_panel.sms_service import send_admin_note_sms
from accounts.models import User, UserFee
from gold_app.models import *
from gold_app.utils import get_gold_bubble, get_gold_chart_data
from silver_app.models import *
from silver_app.utils import get_silver_bubble, get_silver_chart_data
from .serializers import *
from .permissions import IsAdminRole
from django.db.models import Q
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser
from rest_framework.decorators import action
import jdatetime
from decimal import Decimal
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action

from gold_app.models import GoldShortOrder, GoldShortOrderHistory, GoldInventory
from .serializers import (
    AdminGoldShortOrderListSerializer,
    AdminGoldShortOrderDetailSerializer,
    AdminGoldShortOrderUpdateSerializer,
    AdminGoldShortOrderHistorySerializer
)
from gold_app.utils import get_live_gold_price, success_response, error_response
from rest_framework.views import APIView
from rest_framework.response import Response


from gold_app.models import GoldTransaction
from silver_app.models import SilverTransaction
from django.shortcuts import get_object_or_404

from gold_app.models import FinancialTransaction, GoldTransaction
from silver_app.models import SilverFinancialTransaction, SilverTransaction
from django.utils import timezone


from gold_app.models import Wallet, FinancialTransaction

from silver_app.models import SilverWallet, SilverFinancialTransaction

from .models import AdminLog

# from .serializers import AdminLogSerializer
# admin_panel/views.py


# =========================================================
# RESPONSE HELPERS
# =========================================================

from rest_framework import status


def success_response(message="OK", data=None):
    return Response(
        {"success": True, "message": message, "data": data or {}},
        status=status.HTTP_200_OK,
    )


def error_response(message="error", data=None, code=400):
    return Response(
        {"success": False, "message": message, "data": data or {}}, status=code
    )


# =========================================================
# BASE VIEWSET (COMMON CONFIG)
# =========================================================


class AdminBaseViewSet(ModelViewSet):
    permission_classes = [IsAdminRole]


# =========================================================
# USERS
# =========================================================


# class UserAdminViewSet(AdminBaseViewSet):
#     queryset = User.objects.all().order_by("-id")
    
#     def get_queryset(self):
#         qs = super().get_queryset()

#         mobile = self.request.GET.get("mobile")
#         search = self.request.GET.get("search")
#         national_code = self.request.GET.get("national_code")
#         ordering = self.request.GET.get("ordering")

#         if mobile:
#             qs = qs.filter(mobile__icontains=mobile)

#         if search:
#             qs = qs.filter(
#                 Q(first_name__icontains=search) | Q(last_name__icontains=search)
#             )

#         if national_code:
#             qs = qs.filter(national_code__icontains=national_code)

#         ordering_map = {
#             "id": "id",
#             "-id": "-id",
#             "created_at": "date_joined",
#             "-created_at": "-date_joined",
#             "first_name": "first_name",
#             "-first_name": "-first_name",
#             "last_name": "last_name",
#             "-last_name": "-last_name",
#             "mobile": "mobile",
#             "-mobile": "-mobile",
#         }

#         if ordering in ordering_map:
#             qs = qs.order_by(ordering_map[ordering])

#         return qs

#     # ======================
#     # LIST
#     # ======================
#     def list(self, request):
#         users = self.get_queryset()
#         results = []

#         for user in users:
#             fee, _ = UserFee.objects.get_or_create(user=user)
#             data = AdminUserListSerializer(user).data
#             data["fees"] = UserFeeSerializer(fee).data
#             results.append(data)

#         return success_response(
#             "لیست کاربران", {"total_results": len(results), "results": results}
#         )

#     # ======================
#     # RETRIEVE
#     # ======================
#     def retrieve(self, request, pk=None):
#         user = get_object_or_404(User, pk=pk)
#         fee, _ = UserFee.objects.get_or_create(user=user)

#         data = AdminUserDetailSerializer(user).data
#         data["fees"] = UserFeeSerializer(fee).data

#         return success_response("جزئیات کاربر", data)

#     # ======================
#     # UPDATE (FULL FIX)
#     # ======================
#     def update(self, request, pk=None, *args, **kwargs):
#         user = get_object_or_404(User, pk=pk)

#         serializer = AdminUserUpdateSerializer(user, data=request.data, partial=True)
#         serializer.is_valid(raise_exception=True)
#         serializer.save()

#         fee, _ = UserFee.objects.get_or_create(user=user)
#         fee_data = request.data.get("fees")

#         if fee_data is None:
#             fee_data = {
#                 key: request.data.get(key)
#                 for key in [
#                     "gold_buy_fee",
#                     "gold_sell_fee",
#                     "silver_buy_fee",
#                     "silver_sell_fee",
#                 ]
#                 if request.data.get(key) is not None
#             }

#         if fee_data:
#             fee_serializer = UserFeeUpdateSerializer(fee, data=fee_data, partial=True)
#             fee_serializer.is_valid(raise_exception=True)
#             fee_serializer.save()

#         user.refresh_from_db()

#         return success_response(
#             "آپدیت انجام شد", {"results": AdminUserDetailSerializer(user).data}
#         )

#     # ======================
#     # TOGGLE ACTIVE
#     # ======================
#     @action(detail=True, methods=["post"])
#     def toggle_active(self, request, pk=None):
#         user = get_object_or_404(User, pk=pk)
#         user.is_active = not user.is_active
#         user.save()

#         return success_response("وضعیت تغییر کرد", {"is_active": user.is_active})
#         # =========================================================
    
    
    
#     @action(
#         detail=False,
#         methods=["post"],
#         url_path="bulk-update-fees",
#     )
#     def bulk_update_fees(self, request):

#         user_ids = request.data.get("user_ids", [])

#         if not user_ids:
#             return error_response(
#                 message="حداقل یک کاربر انتخاب کنید."
#             )

#         fee_data = {
#             key: request.data.get(key)
#             for key in [
#                 "gold_buy_fee",
#                 "gold_sell_fee",
#                 "silver_buy_fee",
#                 "silver_sell_fee",
#             ]
#             if request.data.get(key) is not None
#         }

#         if not fee_data:
#             return error_response(
#                 message="هیچ کارمزدی ارسال نشده است."
#             )

#         users = User.objects.filter(
#             id__in=user_ids,
#         )

#         if not users.exists():
#             return error_response(
#                 message="کاربری یافت نشد."
#             )

#         updated_users = 0

#         with transaction.atomic():

#             for user in users:

#                 fee, _ = UserFee.objects.get_or_create(
#                     user=user,
#                 )

#                 serializer = UserFeeUpdateSerializer(
#                     fee,
#                     data=fee_data,
#                     partial=True,
#                 )

#                 serializer.is_valid(
#                     raise_exception=True,
#                 )

#                 serializer.save()

#                 updated_users += 1

#         return success_response(
#             message="کارمزد کاربران با موفقیت بروزرسانی شد.",
#             data={
#                 "updated_users": updated_users,
#             },
#         )
   
#     @action(
#         detail=False,
#         methods=["post"],
#         url_path="bulk-update-referral",
#     )
#     def bulk_update_referral(self, request):
#         user_ids = request.data.get("user_ids", [])

#         if not user_ids:
#             return error_response(
#                 message="حداقل یک کاربر انتخاب کنید."
#             )

#         referral_percent = request.data.get("referral_percent")

#         if referral_percent is None:
#             return error_response(
#                 message="درصد سود رفرال ارسال نشده است."
#             )

#         try:
#             referral_percent = Decimal(str(referral_percent))
#         except Exception:
#             return error_response(
#                 message="درصد سود رفرال نامعتبر است."
#             )

#         if referral_percent < 0 or referral_percent > 100:
#             return error_response(
#                 message="درصد سود رفرال باید بین 0 تا 100 باشد."
#             )

#         users = User.objects.filter(id__in=user_ids)

#         if not users.exists():
#             return error_response(
#                 message="کاربری یافت نشد."
#             )

#         from accounts.models import FeeSetting

#         setting = FeeSetting.objects.first()

#         if not setting:
#             setting = FeeSetting.objects.create(
#                 gold_buy_fee=0.01,
#                 gold_sell_fee=0.01,
#                 silver_buy_fee=0.01,
#                 silver_sell_fee=0.01,
#                 gold_referral_percent=20,
#                 silver_referral_percent=20,
#             )

#         setting.gold_referral_percent = referral_percent
#         setting.silver_referral_percent = referral_percent
#         setting.save()

#         return success_response(
#             message="درصد سود رفرال کاربران با موفقیت بروزرسانی شد.",
#             data={
#                 "updated_users": users.count(),
#                 "referral_percent": float(referral_percent),
#             }
#         )
#     def update(self, request, pk=None, *args, **kwargs):
#         user = get_object_or_404(User, pk=pk)

#         # ✅ دریافت referral_percent از درخواست
#         referral_percent = request.data.get('referral_percent')

#         if referral_percent is not None:
#             from decimal import Decimal
#             setting = FeeSetting.objects.first()
#             if not setting:
#                 setting = FeeSetting.objects.create(
#                     gold_buy_fee=0.01,
#                     gold_sell_fee=0.01,
#                     silver_buy_fee=0.01,
#                     silver_sell_fee=0.01,
#                     gold_referral_percent=20,
#                     silver_referral_percent=20,
#                 )
#             setting.gold_referral_percent = Decimal(str(referral_percent))
#             setting.silver_referral_percent = Decimal(str(referral_percent))
#             setting.save()

#         serializer = AdminUserUpdateSerializer(user, data=request.data, partial=True)
#         serializer.is_valid(raise_exception=True)
#         serializer.save()

#         fee, _ = UserFee.objects.get_or_create(user=user)
#         fee_data = request.data.get("fees")

#         if fee_data is None:
#             fee_data = {
#                 key: request.data.get(key)
#                 for key in [
#                     "gold_buy_fee",
#                     "gold_sell_fee",
#                     "silver_buy_fee",
#                     "silver_sell_fee",
#                 ]
#                 if request.data.get(key) is not None
#             }

#         if fee_data:
#             fee_serializer = UserFeeUpdateSerializer(fee, data=fee_data, partial=True)
#             fee_serializer.is_valid(raise_exception=True)
#             fee_serializer.save()

#         user.refresh_from_db()

#         return success_response(
#             "آپدیت انجام شد",
#             {"results": AdminUserDetailSerializer(user).data}
#         )


#     @action(
#         detail=True,
#         methods=["get"],
#         url_path="transactions",
#     )
#     def transactions(self, request, pk=None):

#         user = get_object_or_404(
#             User,
#             pk=pk,
#         )

#         results = []

#         # =====================================================
#         # GOLD WALLET TRANSACTIONS
#         # =====================================================

#         for item in FinancialTransaction.objects.filter(
#             user=user,
#         ):

#             results.append(
#                 {
#                     "source": "GOLD_WALLET",
#                     "type": item.type,
#                     "status": item.status,
#                     "amount": None,
#                     "toman_amount": item.amount,
#                     "payment_method": None,
#                     "delivery_type": None,
#                     "tracking_code": item.tracking_code,
#                     "description": item.description,
#                     "created_at": item.created_at,
#                 }
#             )

#         # =====================================================
#         # GOLD ADMIN DEPOSIT
#         # =====================================================

#         for item in GoldBalanceAdjustment.objects.filter(
#             user=user,
#         ):

#             results.append(
#                 {
#                     "source": "GOLD_WALLET",
#                     "type": "ADMIN_ADJUSTMENT",
#                     "status": "COMPLETED",
#                     "amount": item.gold_amount,
#                     "toman_amount": item.wallet_amount,
#                     "payment_method": None,
#                     "delivery_type": None,
#                     "tracking_code": item.tracking_code,
#                     "description": item.admin_note
#                     or "افزایش موجودی توسط ادمین",
#                     "created_at": item.created_at,
#                 }
#             )

#         # =====================================================
#         # GOLD ADMIN WITHDRAW
#         # =====================================================

#         for item in GoldBalanceWithdrawal.objects.filter(
#             user=user,
#         ):

#             results.append(
#                 {
#                     "source": "GOLD_WALLET",
#                     "type": "ADMIN_WITHDRAWAL",
#                     "status": "COMPLETED",
#                     "amount": item.gold_amount,
#                     "toman_amount": item.wallet_amount,
#                     "payment_method": None,
#                     "delivery_type": None,
#                     "tracking_code": item.tracking_code,
#                     "description": item.admin_note
#                     or "برداشت موجودی توسط ادمین",
#                     "created_at": item.created_at,
#                 }
#             )

#         # =====================================================
#         # GOLD BUY / SELL
#         # =====================================================

#         for item in GoldTransaction.objects.filter(
#             user=user,
#         ):

#             results.append(
#                 {
#                     "source": "GOLD",
#                     "type": item.type,
#                     "status": item.status,
#                     "amount": item.amount_gr,
#                     "toman_amount": item.total_amount,
#                     "payment_method": None,
#                     "delivery_type": None,
#                     "tracking_code": item.tracking_code,
#                     "description": item.description,
#                     "created_at": item.created_at,
#                 }
#             )

#         # =====================================================
#         # GOLD LIMIT ORDERS (سفارش با قیمت طلا)
#         # =====================================================

#         for item in GoldOrder.objects.filter(
#             user=user,
#         ):

#             order_type_text = "خرید" if item.order_type == "BUY" else "فروش"

#             results.append(
#                 {
#                     "source": "GOLD_LIMIT_ORDER",
#                     "type": item.order_type,
#                     "status": item.status,
#                     "amount": item.estimated_weight,
#                     "toman_amount": item.amount_toman,
#                     "payment_method": None,
#                     "delivery_type": None,
#                     "tracking_code": f"LMT-{item.id:06d}",
#                     "description": (
#                         item.description
#                         or f"سفارش با قیمت طلا - {order_type_text} - قیمت هدف: {item.target_price:,}"
#                     ),
#                     "created_at": item.created_at,
#                 }
#             )

#         # =====================================================
#         # GOLD ORDERS (فیزیکی)
#         # =====================================================

#         for item in Order.objects.filter(
#             user=user,
#         ):

#             results.append(
#                 {
#                     "source": "GOLD_ORDER",
#                     "type": item.payment_method,
#                     "status": item.status,
#                     "amount": item.total_gold_amount,
#                     "toman_amount": item.total_toman_amount,
#                     "payment_method": item.payment_method,
#                     "delivery_type": item.delivery_type,
#                     "tracking_code": item.tracking_code,
#                     "description": (
#                         item.description
#                         or f"سفارش فیزیکی طلا ({item.get_delivery_type_display()})"
#                     ),
#                     "created_at": item.created_at,
#                 }
#             )

#         # =====================================================
#         # SILVER WALLET TRANSACTIONS
#         # =====================================================

#         for item in SilverFinancialTransaction.objects.filter(
#             user=user,
#         ):

#             results.append(
#                 {
#                     "source": "SILVER_WALLET",
#                     "type": item.type,
#                     "status": item.status,
#                     "amount": None,
#                     "toman_amount": item.amount,
#                     "payment_method": None,
#                     "delivery_type": None,
#                     "tracking_code": item.tracking_code,
#                     "description": item.description,
#                     "created_at": item.created_at,
#                 }
#             )

#         # =====================================================
#         # SILVER ADMIN DEPOSIT
#         # =====================================================

#         for item in SilverBalanceAdjustment.objects.filter(
#             user=user,
#         ):

#             results.append(
#                 {
#                     "source": "SILVER_WALLET",
#                     "type": "ADMIN_ADJUSTMENT",
#                     "status": "COMPLETED",
#                     "amount": item.silver_amount,
#                     "toman_amount": item.wallet_amount,
#                     "payment_method": None,
#                     "delivery_type": None,
#                     "tracking_code": item.tracking_code,
#                     "description": (
#                         item.admin_note
#                         or "افزایش موجودی توسط ادمین"
#                     ),
#                     "created_at": item.created_at,
#                 }
#             )

#         # =====================================================
#         # SILVER ADMIN WITHDRAW
#         # =====================================================

#         for item in SilverBalanceWithdrawal.objects.filter(
#             user=user,
#         ):

#             results.append(
#                 {
#                     "source": "SILVER_WALLET",
#                     "type": "ADMIN_WITHDRAWAL",
#                     "status": "COMPLETED",
#                     "amount": item.silver_amount,
#                     "toman_amount": item.wallet_amount,
#                     "payment_method": None,
#                     "delivery_type": None,
#                     "tracking_code": item.tracking_code,
#                     "description": (
#                         item.admin_note
#                         or "برداشت موجودی توسط ادمین"
#                     ),
#                     "created_at": item.created_at,
#                 }
#             )

#         # =====================================================
#         # SILVER BUY / SELL
#         # =====================================================

#         for item in SilverTransaction.objects.filter(
#             user=user,
#         ):

#             results.append(
#                 {
#                     "source": "SILVER",
#                     "type": item.type,
#                     "status": item.status,
#                     "amount": item.amount_gr,
#                     "toman_amount": item.total_amount,
#                     "payment_method": None,
#                     "delivery_type": None,
#                     "tracking_code": item.tracking_code,
#                     "description": item.description,
#                     "created_at": item.created_at,
#                 }
#             )

#         # =====================================================
#         # SILVER LIMIT ORDERS (سفارش با قیمت نقره)
#         # =====================================================

#         for item in SilverLimitOrder.objects.filter(
#             user=user,
#         ):

#             order_type_text = "خرید" if item.order_type == "BUY" else "فروش"

#             results.append(
#                 {
#                     "source": "SILVER_LIMIT_ORDER",
#                     "type": item.order_type,
#                     "status": item.status,
#                     "amount": item.silver_weight or item.estimated_weight,
#                     "toman_amount": item.amount_toman,
#                     "payment_method": None,
#                     "delivery_type": None,
#                     "tracking_code": f"SLV-{item.id:06d}",
#                     "description": (
#                         item.description
#                         or f"سفارش با قیمت نقره - {order_type_text} - قیمت هدف: {item.target_price:,}"
#                     ),
#                     "created_at": item.created_at,
#                 }
#             )

#         # =====================================================
#         # SILVER ORDERS (فیزیکی)
#         # =====================================================

#         for item in SilverOrder.objects.filter(
#             user=user,
#         ):

#             results.append(
#                 {
#                     "source": "SILVER_ORDER",
#                     "type": item.payment_method,
#                     "status": item.status,
#                     "amount": item.total_silver_amount,
#                     "toman_amount": item.total_toman_amount,
#                     "payment_method": item.payment_method,
#                     "delivery_type": item.delivery_type,
#                     "tracking_code": item.tracking_code,
#                     "description": (
#                         item.description
#                         or f"سفارش فیزیکی نقره ({item.get_delivery_type_display()})"
#                     ),
#                     "created_at": item.created_at,
#                 }
#             )

#         # =====================================================
#         # SORT BY CREATED_AT DESC
#         # =====================================================

#         results.sort(
#             key=lambda x: x["created_at"],
#             reverse=True,
#         )

#         # =====================================================
#         # TYPE / STATUS / PAYMENT / DELIVERY MAP
#         # =====================================================

#         TYPE_MAP = {

#             "BUY": "خرید",
#             "SELL": "فروش",
#             "DEPOSIT": "واریز",
#             "WITHDRAW": "برداشت",
#             "TRANSFER": "انتقال",
#             "TOMAN": "پرداخت تومانی",
#             "GOLD": "پرداخت با طلا",
#             "SILVER": "پرداخت با نقره",
#             "ADMIN_ADJUSTMENT": "افزایش موجودی توسط ادمین",
#             "ADMIN_WITHDRAWAL": "برداشت موجودی توسط ادمین",
#             "ONLINE": "پرداخت آنلاین",
#             "WALLET": "پرداخت از کیف پول",
#             "CARD_TO_CARD": "کارت به کارت",
#             "CASH": "پرداخت نقدی",
#         }

#         STATUS_MAP = {
#             "PENDING": "در انتظار",
#             "PROCESSING": "در حال پردازش",
#             "COMPLETED": "تکمیل شده",
#             "SUCCESS": "موفق",
#             "FAILED": "ناموفق",
#             "CANCELLED": "لغو شده",
#             "REQUESTED": "ثبت سفارش",
#             "PREPARING": "در حال آماده‌سازی",
#             "DELIVERING": "در حال ارسال",
#             "DELIVERED": "تحویل داده شد",
#             "EXECUTED": "اجرا شده",
#         }

#         DELIVERY_MAP = {
#             "POST": "پست",
#             "TIPAX": "تیپاکس",
#             "PICKUP": "تحویل حضوری",
#             "EXPRESS": "ارسال فوری",
#         }

#         for item in results:

#             item["type"] = TYPE_MAP.get(
#                 item["type"],
#                 item["type"],
#             )

#             item["status"] = STATUS_MAP.get(
#                 item["status"],
#                 item["status"],
#             )

#             if item["payment_method"]:

#                 item["payment_method"] = TYPE_MAP.get(
#                     item["payment_method"],
#                     item["payment_method"],
#                 )

#             if item["delivery_type"]:

#                 item["delivery_type"] = DELIVERY_MAP.get(
#                     item["delivery_type"],
#                     item["delivery_type"],
#                 )

#         serializer = UserTransactionSerializer(
#             results,
#             many=True,
#         )

#         return success_response(
#             "لیست تراکنش‌های کاربر",
#             {
#                 "total_results": len(serializer.data),
#                 "results": serializer.data,
#             },
#         )




#     def update(self, request, pk=None, *args, **kwargs):
#         user = get_object_or_404(User, pk=pk)

#         # ✅ دریافت referral_percent از درخواست
#         referral_percent = request.data.get('referral_percent')

#         # بروزرسانی اطلاعات کاربر
#         serializer = AdminUserUpdateSerializer(user, data=request.data, partial=True)
#         serializer.is_valid(raise_exception=True)
#         serializer.save()

#         # بروزرسانی کارمزدها
#         fee, _ = UserFee.objects.get_or_create(user=user)
#         fee_data = request.data.get("fees")

#         if fee_data is None:
#             fee_data = {
#                 key: request.data.get(key)
#                 for key in [
#                     "gold_buy_fee",
#                     "gold_sell_fee",
#                     "silver_buy_fee",
#                     "silver_sell_fee",
#                 ]
#                 if request.data.get(key) is not None
#             }

#         if fee_data:
#             fee_serializer = UserFeeUpdateSerializer(fee, data=fee_data, partial=True)
#             fee_serializer.is_valid(raise_exception=True)
#             fee_serializer.save()

#         # ✅ بروزرسانی درصد رفرال اختصاصی برای این کاربر
#         if referral_percent is not None:
#             try:
#                 referral_percent = Decimal(str(referral_percent))
#                 if 0 <= referral_percent <= 100:
#                     # ذخیره در Cache برای این کاربر خاص
#                     from django.core.cache import cache
#                     cache_key = f"user_referral_percent_{user.id}"
#                     cache.set(cache_key, float(referral_percent), timeout=60*60*24*30)  # 30 روز
#                 else:
#                     return error_response(
#                         message="درصد سود رفرال باید بین 0 تا 100 باشد."
#                     )
#             except Exception:
#                 return error_response(
#                     message="درصد سود رفرال نامعتبر است."
#                 )

#         user.refresh_from_db()

#         # دریافت دیتای نهایی با جزئیات کامل
#         data = AdminUserDetailSerializer(user).data
#         fee, _ = UserFee.objects.get_or_create(user=user)
#         data["fees"] = UserFeeSerializer(fee).data

#         # ✅ اضافه کردن referral_percent به خروجی
#         from django.core.cache import cache
#         cache_key = f"user_referral_percent_{user.id}"
#         cached_percent = cache.get(cache_key)
#         if cached_percent is not None:
#             data["referral_percent"] = float(cached_percent)
#         else:
#             # اگر در Cache نبود، از تنظیمات عمومی بگیر
#             from accounts.models import ReferralSetting
#             setting = ReferralSetting.objects.first()
#             data["referral_percent"] = float(setting.commission_percent) if setting else 20.0

#         return success_response(
#             "آپدیت انجام شد",
#             {"results": data}
#         )


# admin_panel/views.py - UserAdminViewSet کامل

from rest_framework.decorators import action
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.core.cache import cache
from decimal import Decimal
import logging

from admin_panel.serializers import (
    AdminUserListSerializer,
    AdminUserDetailSerializer,
    AdminUserUpdateSerializer,
    UserFeeSerializer,
    UserFeeUpdateSerializer,
    UserTransactionSerializer,
)
from accounts.models import User, UserFee, FeeSetting
from accounts.utils import success_response, error_response
from admin_panel.utils import create_admin_log
from gold_app.models import (
    GoldInvestment,
    GoldGuarantee,
    GoldTransaction,
    GoldOrder,
    Order,
    
)
from .models import (
    GoldBalanceAdjustment,
    GoldBalanceWithdrawal,
    SilverBalanceWithdrawal,
    GoldBalanceAdjustment,
    GoldBalanceWithdrawal,
    SilverBalanceAdjustment
)

from silver_app.models import (
    SilverTransaction,
    SilverLimitOrder,
    SilverOrder,
    SilverFinancialTransaction


)
from gold_app.models import FinancialTransaction

logger = logging.getLogger(__name__)


class UserAdminViewSet(AdminBaseViewSet):
    """
    مدیریت کاربران توسط ادمین
    """

    queryset = User.objects.all().order_by("-id")
    
    def get_queryset(self):
        qs = super().get_queryset()

        mobile = self.request.GET.get("mobile")
        search = self.request.GET.get("search")
        national_code = self.request.GET.get("national_code")
        ordering = self.request.GET.get("ordering")

        if mobile:
            qs = qs.filter(mobile__icontains=mobile)

        if search:
            qs = qs.filter(
                Q(first_name__icontains=search) | Q(last_name__icontains=search)
            )

        if national_code:
            qs = qs.filter(national_code__icontains=national_code)

        ordering_map = {
            "id": "id",
            "-id": "-id",
            "created_at": "date_joined",
            "-created_at": "-date_joined",
            "first_name": "first_name",
            "-first_name": "-first_name",
            "last_name": "last_name",
            "-last_name": "-last_name",
            "mobile": "mobile",
            "-mobile": "-mobile",
        }

        if ordering in ordering_map:
            qs = qs.order_by(ordering_map[ordering])

        return qs

    # ======================
    # LIST
    # ======================
    def list(self, request):
        users = self.get_queryset()
        results = []

        for user in users:
            fee, _ = UserFee.objects.get_or_create(user=user)
            data = AdminUserListSerializer(user).data
            data["fees"] = UserFeeSerializer(fee).data
            results.append(data)

        return success_response(
            "لیست کاربران", {"total_results": len(results), "results": results}
        )

    # ======================
    # RETRIEVE
    # ======================
    def retrieve(self, request, pk=None):
        user = get_object_or_404(User, pk=pk)
        fee, _ = UserFee.objects.get_or_create(user=user)

        data = AdminUserDetailSerializer(user).data
        data["fees"] = UserFeeSerializer(fee).data

        # دریافت درصد رفرال اختصاصی کاربر
        cache_key = f"user_referral_percent_{user.id}"
        cached_percent = cache.get(cache_key)
        if cached_percent is not None:
            data["referral_percent"] = float(cached_percent)
        else:
            from accounts.models import ReferralSetting
            setting = ReferralSetting.objects.first()
            data["referral_percent"] = float(setting.commission_percent) if setting else 20.0

        return success_response("جزئیات کاربر", data)

    # ======================
    # UPDATE
    # ======================
    def update(self, request, pk=None, *args, **kwargs):
        user = get_object_or_404(User, pk=pk)

        # دریافت referral_percent از درخواست
        referral_percent = request.data.get('referral_percent')

        # بروزرسانی اطلاعات کاربر
        serializer = AdminUserUpdateSerializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        # بروزرسانی کارمزدها
        fee, _ = UserFee.objects.get_or_create(user=user)
        fee_data = request.data.get("fees")

        if fee_data is None:
            fee_data = {
                key: request.data.get(key)
                for key in [
                    "gold_buy_fee",
                    "gold_sell_fee",
                    "silver_buy_fee",
                    "silver_sell_fee",
                ]
                if request.data.get(key) is not None
            }

        if fee_data:
            fee_serializer = UserFeeUpdateSerializer(fee, data=fee_data, partial=True)
            fee_serializer.is_valid(raise_exception=True)
            fee_serializer.save()

        # بروزرسانی درصد رفرال اختصاصی برای این کاربر
        if referral_percent is not None:
            try:
                referral_percent = Decimal(str(referral_percent))
                if 0 <= referral_percent <= 100:
                    cache_key = f"user_referral_percent_{user.id}"
                    cache.set(cache_key, float(referral_percent), timeout=60*60*24*30)
                else:
                    return error_response(
                        message="درصد سود رفرال باید بین 0 تا 100 باشد."
                    )
            except Exception:
                return error_response(
                    message="درصد سود رفرال نامعتبر است."
                )

        user.refresh_from_db()

        # دریافت دیتای نهایی با جزئیات کامل
        data = AdminUserDetailSerializer(user).data
        fee, _ = UserFee.objects.get_or_create(user=user)
        data["fees"] = UserFeeSerializer(fee).data

        # اضافه کردن referral_percent به خروجی
        cache_key = f"user_referral_percent_{user.id}"
        cached_percent = cache.get(cache_key)
        if cached_percent is not None:
            data["referral_percent"] = float(cached_percent)
        else:
            from accounts.models import ReferralSetting
            setting = ReferralSetting.objects.first()
            data["referral_percent"] = float(setting.commission_percent) if setting else 20.0

        return success_response(
            "آپدیت انجام شد",
            {"results": data}
        )

    # ======================
    # TOGGLE ACTIVE
    # ======================
    @action(detail=True, methods=["post"])
    def toggle_active(self, request, pk=None):
        user = get_object_or_404(User, pk=pk)
        user.is_active = not user.is_active
        user.save()

        create_admin_log(
            request=request,
            user=user,
            action_type="USER_TOGGLE_ACTIVE",
            action="تغییر وضعیت فعال/غیرفعال کاربر",
            model_name="User",
            object_id=user.id,
            success=True,
            description=f"""
تغییر وضعیت کاربر

کاربر: {user.mobile}
وضعیت جدید: {'فعال' if user.is_active else 'غیرفعال'}
"""
        )

        return success_response("وضعیت تغییر کرد", {"is_active": user.is_active})

    # ======================
    # BULK UPDATE FEES
    # ======================
    @action(
        detail=False,
        methods=["post"],
        url_path="bulk-update-fees",
    )
    def bulk_update_fees(self, request):

        user_ids = request.data.get("user_ids", [])

        if not user_ids:
            return error_response(
                message="حداقل یک کاربر انتخاب کنید."
            )

        fee_data = {
            key: request.data.get(key)
            for key in [
                "gold_buy_fee",
                "gold_sell_fee",
                "silver_buy_fee",
                "silver_sell_fee",
            ]
            if request.data.get(key) is not None
        }

        if not fee_data:
            return error_response(
                message="هیچ کارمزدی ارسال نشده است."
            )

        users = User.objects.filter(id__in=user_ids)

        if not users.exists():
            return error_response(
                message="کاربری یافت نشد."
            )

        updated_users = 0

        with transaction.atomic():
            for user in users:
                fee, _ = UserFee.objects.get_or_create(user=user)
                serializer = UserFeeUpdateSerializer(fee, data=fee_data, partial=True)
                serializer.is_valid(raise_exception=True)
                serializer.save()
                updated_users += 1

        return success_response(
            message="کارمزد کاربران با موفقیت بروزرسانی شد.",
            data={
                "updated_users": updated_users,
            },
        )

    # ======================
    # BULK UPDATE REFERRAL
    # ======================
    @action(
        detail=False,
        methods=["post"],
        url_path="bulk-update-referral",
    )
    def bulk_update_referral(self, request):
        user_ids = request.data.get("user_ids", [])

        if not user_ids:
            return error_response(
                message="حداقل یک کاربر انتخاب کنید."
            )

        referral_percent = request.data.get("referral_percent")

        if referral_percent is None:
            return error_response(
                message="درصد سود رفرال ارسال نشده است."
            )   

        try:
            referral_percent = Decimal(str(referral_percent))
        except Exception:
            return error_response(
                message="درصد سود رفرال نامعتبر است."
            )

        if referral_percent < 0 or referral_percent > 100:
            return error_response(
                message="درصد سود رفرال باید بین 0 تا 100 باشد."
            )

        users = User.objects.filter(id__in=user_ids)

        if not users.exists():
            return error_response(
                message="کاربری یافت نشد."
            )

        from accounts.models import FeeSetting

        setting = FeeSetting.objects.first()

        if not setting:
            setting = FeeSetting.objects.create(
                gold_buy_fee=0.01,
                gold_sell_fee=0.01,
                silver_buy_fee=0.01,
                silver_sell_fee=0.01,
                gold_referral_percent=20,
                silver_referral_percent=20,
            )

        setting.gold_referral_percent = referral_percent
        setting.silver_referral_percent = referral_percent
        setting.save()

        return success_response(
            message="درصد سود رفرال کاربران با موفقیت بروزرسانی شد.",
            data={
                "updated_users": users.count(),
                "referral_percent": float(referral_percent),
            }
        )

    # ======================
    # TRANSACTIONS (لیست تراکنش‌های کاربر)
    # ======================
    @action(
        detail=True,
        methods=["get"],
        url_path="transactions",
    )
    def transactions(self, request, pk=None):

        user = get_object_or_404(User, pk=pk)
        results = []

        # =====================================================
        # GOLD WALLET TRANSACTIONS
        # =====================================================
        for item in FinancialTransaction.objects.filter(user=user):
            results.append({
                "source": "GOLD_WALLET",
                "type": item.type,
                "status": item.status,
                "amount": None,
                "toman_amount": item.amount,
                "payment_method": None,
                "delivery_type": None,
                "tracking_code": item.tracking_code,
                "description": item.description,
                "created_at": item.created_at,
            })

        # =====================================================
        # GOLD ADMIN DEPOSIT
        # =====================================================
        for item in GoldBalanceAdjustment.objects.filter(user=user):
            results.append({
                "source": "GOLD_WALLET",
                "type": "ADMIN_ADJUSTMENT",
                "status": "COMPLETED",
                "amount": item.gold_amount,
                "toman_amount": item.wallet_amount,
                "payment_method": None,
                "delivery_type": None,
                "tracking_code": item.tracking_code,
                "description": item.admin_note or "افزایش موجودی توسط ادمین",
                "created_at": item.created_at,
            })

        # =====================================================
        # GOLD ADMIN WITHDRAW
        # =====================================================
        for item in GoldBalanceWithdrawal.objects.filter(user=user):
            results.append({
                "source": "GOLD_WALLET",
                "type": "ADMIN_WITHDRAWAL",
                "status": "COMPLETED",
                "amount": item.gold_amount,
                "toman_amount": item.wallet_amount,
                "payment_method": None,
                "delivery_type": None,
                "tracking_code": item.tracking_code,
                "description": item.admin_note or "برداشت موجودی توسط ادمین",
                "created_at": item.created_at,
            })

        # =====================================================
        # GOLD BUY / SELL
        # =====================================================
        for item in GoldTransaction.objects.filter(user=user):
            results.append({
                "source": "GOLD",
                "type": item.type,
                "status": item.status,
                "amount": item.amount_gr,
                "toman_amount": item.total_amount,
                "payment_method": None,
                "delivery_type": None,
                "tracking_code": item.tracking_code,
                "description": item.description,
                "created_at": item.created_at,
            })

        # =====================================================
        # GOLD INVESTMENTS (سرمایه‌گذاری طلا)
        # =====================================================
        for item in GoldInvestment.objects.filter(user=user):
            profit_amount = item.paid_profit or 0
            total_return = item.gold_weight + profit_amount
            
            results.append({
                "source": "GOLD_INVESTMENT",
                "type": "سرمایه‌گذاری",
                "status": item.status,
                "amount": item.gold_weight,
                "toman_amount": item.investment_price,
                "payment_method": None,
                "delivery_type": None,
                "tracking_code": item.tracking_code,
                "description": (
                    f"سرمایه‌گذاری در طرح {item.plan.name} - "
                    f"وزن: {item.gold_weight} گرم - "
                    f"سود: {item.expected_profit}% - "
                    f"بازگشت: {total_return} گرم"
                ),
                "created_at": item.created_at,
            })

        # =====================================================
        # GOLD INVESTMENT PROFIT COLLECT (برداشت سود سرمایه‌گذاری)
        # =====================================================
        for item in GoldInvestment.objects.filter(user=user, paid_profit__gt=0):
            results.append({
                "source": "GOLD_INVESTMENT",
                "type": "برداشت سود",
                "status": "COMPLETED",
                "amount": item.paid_profit,
                "toman_amount": None,
                "payment_method": None,
                "delivery_type": None,
                "tracking_code": f"PRF-{item.id:06d}",
                "description": (
                    f"برداشت سود سرمایه‌گذاری - طرح {item.plan.name} - "
                    f"سود: {item.paid_profit} گرم"
                ),
                "created_at": item.completed_at or item.updated_at,
            })

        # =====================================================
        # GOLD GUARANTEES (تضمین طلا)
        # =====================================================
        for item in GoldGuarantee.objects.filter(user=user):
            payout = item.user_payout or 0
            
            description = f"تضمین طلا - طرح {item.plan.name} - "
            
            if item.status == 'ACTIVE':
                description += f"فعال - باقی‌مانده: {item.days_remaining} روز"
            elif item.status == 'EXECUTED':
                if payout > 0:
                    description += f"اجرا شده - سود: {payout:,} تومان"
                else:
                    description += "اجرا شده - بدون سود"
            elif item.status == 'CANCELLED':
                description += "لغو شده"
            else:
                description += item.get_status_display()
            
            results.append({
                "source": "GOLD_GUARANTEE",
                "type": "تضمین قیمت",
                "status": item.status,
                "amount": item.gold_weight,
                "toman_amount": None,
                "payment_method": None,
                "delivery_type": None,
                "tracking_code": item.tracking_code,
                "description": description,
                "created_at": item.created_at,
            })

        # =====================================================
        # GOLD GUARANTEE PAYOUT (پرداخت سود تضمین)
        # =====================================================
        for item in GoldGuarantee.objects.filter(user=user, user_payout__gt=0):
            results.append({
                "source": "GOLD_GUARANTEE",
                "type": "پرداخت سود تضمین",
                "status": "COMPLETED",
                "amount": None,
                "toman_amount": item.user_payout,
                "payment_method": None,
                "delivery_type": None,
                "tracking_code": item.tracking_code,
                "description": (
                    f"پرداخت سود تضمین طلا - طرح {item.plan.name} - "
                    f"مبلغ: {item.user_payout:,} تومان"
                ),
                "created_at": item.executed_at or item.updated_at,
            })

        # =====================================================
        # GOLD LIMIT ORDERS (سفارش با قیمت طلا)
        # =====================================================
        for item in GoldOrder.objects.filter(user=user):
            order_type_text = "خرید" if item.order_type == "BUY" else "فروش"
            results.append({
                "source": "GOLD_LIMIT_ORDER",
                "type": item.order_type,
                "status": item.status,
                "amount": item.estimated_weight,
                "toman_amount": item.amount_toman,
                "payment_method": None,
                "delivery_type": None,
                "tracking_code": f"LMT-{item.id:06d}",
                "description": (
                    item.description
                    or f"سفارش با قیمت طلا - {order_type_text} - قیمت هدف: {item.target_price:,}"
                ),
                "created_at": item.created_at,
            })

        # =====================================================
        # GOLD ORDERS (فیزیکی)
        # =====================================================
        for item in Order.objects.filter(user=user):
            results.append({
                "source": "GOLD_ORDER",
                "type": item.payment_method,
                "status": item.status,
                "amount": item.total_gold_amount,
                "toman_amount": item.total_toman_amount,
                "payment_method": item.payment_method,
                "delivery_type": item.delivery_type,
                "tracking_code": item.tracking_code,
                "description": (
                    item.description
                    or f"سفارش فیزیکی طلا ({item.get_delivery_type_display()})"
                ),
                "created_at": item.created_at,
            })

        # =====================================================
        # SILVER WALLET TRANSACTIONS
        # =====================================================
        for item in SilverFinancialTransaction.objects.filter(user=user):
            results.append({
                "source": "SILVER_WALLET",
                "type": item.type,
                "status": item.status,
                "amount": None,
                "toman_amount": item.amount,
                "payment_method": None,
                "delivery_type": None,
                "tracking_code": item.tracking_code,
                "description": item.description,
                "created_at": item.created_at,
            })

        # =====================================================
        # SILVER ADMIN DEPOSIT
        # =====================================================
        for item in SilverBalanceAdjustment.objects.filter(user=user):
            results.append({
                "source": "SILVER_WALLET",
                "type": "ADMIN_ADJUSTMENT",
                "status": "COMPLETED",
                "amount": item.silver_amount,
                "toman_amount": item.wallet_amount,
                "payment_method": None,
                "delivery_type": None,
                "tracking_code": item.tracking_code,
                "description": item.admin_note or "افزایش موجودی توسط ادمین",
                "created_at": item.created_at,
            })

        # =====================================================
        # SILVER ADMIN WITHDRAW
        # =====================================================
        for item in SilverBalanceWithdrawal.objects.filter(user=user):
            results.append({
                "source": "SILVER_WALLET",
                "type": "ADMIN_WITHDRAWAL",
                "status": "COMPLETED",
                "amount": item.silver_amount,
                "toman_amount": item.wallet_amount,
                "payment_method": None,
                "delivery_type": None,
                "tracking_code": item.tracking_code,
                "description": item.admin_note or "برداشت موجودی توسط ادمین",
                "created_at": item.created_at,
            })

        # =====================================================
        # SILVER BUY / SELL
        # =====================================================
        for item in SilverTransaction.objects.filter(user=user):
            results.append({
                "source": "SILVER",
                "type": item.type,
                "status": item.status,
                "amount": item.amount_gr,
                "toman_amount": item.total_amount,
                "payment_method": None,
                "delivery_type": None,
                "tracking_code": item.tracking_code,
                "description": item.description,
                "created_at": item.created_at,
            })

        # =====================================================
        # SILVER LIMIT ORDERS (سفارش با قیمت نقره)
        # =====================================================
        for item in SilverLimitOrder.objects.filter(user=user):
            order_type_text = "خرید" if item.order_type == "BUY" else "فروش"
            results.append({
                "source": "SILVER_LIMIT_ORDER",
                "type": item.order_type,
                "status": item.status,
                "amount": item.silver_weight or item.estimated_weight,
                "toman_amount": item.amount_toman,
                "payment_method": None,
                "delivery_type": None,
                "tracking_code": f"SLV-{item.id:06d}",
                "description": (
                    item.description
                    or f"سفارش با قیمت نقره - {order_type_text} - قیمت هدف: {item.target_price:,}"
                ),
                "created_at": item.created_at,
            })

        # =====================================================
        # SILVER ORDERS (فیزیکی)
        # =====================================================
        for item in SilverOrder.objects.filter(user=user):
            results.append({
                "source": "SILVER_ORDER",
                "type": item.payment_method,
                "status": item.status,
                "amount": item.total_silver_amount,
                "toman_amount": item.total_toman_amount,
                "payment_method": item.payment_method,
                "delivery_type": item.delivery_type,
                "tracking_code": item.tracking_code,
                "description": (
                    item.description
                    or f"سفارش فیزیکی نقره ({item.get_delivery_type_display()})"
                ),
                "created_at": item.created_at,
            })

        # =====================================================
        # SORT BY CREATED_AT DESC
        # =====================================================
        results.sort(key=lambda x: x["created_at"], reverse=True)

        # =====================================================
        # TYPE / STATUS / PAYMENT / DELIVERY MAP
        # =====================================================
        TYPE_MAP = {
            "BUY": "خرید",
            "SELL": "فروش",
            "DEPOSIT": "واریز",
            "WITHDRAW": "برداشت",
            "TRANSFER": "انتقال",
            "TOMAN": "پرداخت تومانی",
            "GOLD": "پرداخت با طلا",
            "SILVER": "پرداخت با نقره",
            "ADMIN_ADJUSTMENT": "افزایش موجودی توسط ادمین",
            "ADMIN_WITHDRAWAL": "برداشت موجودی توسط ادمین",
            "ONLINE": "پرداخت آنلاین",
            "WALLET": "پرداخت از کیف پول",
            "CARD_TO_CARD": "کارت به کارت",
            "CASH": "پرداخت نقدی",
            "سرمایه‌گذاری": "سرمایه‌گذاری طلا",
            "تضمین قیمت": "تضمین طلا",
            "برداشت سود": "برداشت سود سرمایه‌گذاری",
            "پرداخت سود تضمین": "پرداخت سود تضمین طلا",
        }

        STATUS_MAP = {
            "PENDING": "در انتظار",
            "PROCESSING": "در حال پردازش",
            "COMPLETED": "تکمیل شده",
            "SUCCESS": "موفق",
            "FAILED": "ناموفق",
            "CANCELLED": "لغو شده",
            "REQUESTED": "ثبت سفارش",
            "PREPARING": "در حال آماده‌سازی",
            "DELIVERING": "در حال ارسال",
            "DELIVERED": "تحویل داده شد",
            "EXECUTED": "اجرا شده",
            "ACTIVE": "فعال",
            "EXPIRED": "منقضی شده",
        }

        DELIVERY_MAP = {
            "POST": "پست",
            "TIPAX": "تیپاکس",
            "PICKUP": "تحویل حضوری",
            "EXPRESS": "ارسال فوری",
        }

        for item in results:
            item["type"] = TYPE_MAP.get(item["type"], item["type"])
            item["status"] = STATUS_MAP.get(item["status"], item["status"])

            if item["payment_method"]:
                item["payment_method"] = TYPE_MAP.get(item["payment_method"], item["payment_method"])

            if item["delivery_type"]:
                item["delivery_type"] = DELIVERY_MAP.get(item["delivery_type"], item["delivery_type"])

        serializer = UserTransactionSerializer(results, many=True)

        return success_response(
            "لیست تراکنش‌های کاربر",
            {
                "total_results": len(serializer.data),
                "results": serializer.data,
            },
        )


class AdminGoldShortOrderViewSet(AdminBaseViewSet):
    """
    پنل ادمین - مدیریت سفارشات فروش تعهدی طلا
    """
    queryset = GoldShortOrder.objects.all().order_by("-created_at")
    
    def get_queryset(self):
        qs = super().get_queryset()

        # فیلترها
        status = self.request.GET.get("status")
        order_type = self.request.GET.get("order_type")
        user_mobile = self.request.GET.get("user_mobile")
        search = self.request.GET.get("search")
        start_date = self.request.GET.get("start_date")
        end_date = self.request.GET.get("end_date")
        ordering = self.request.GET.get("ordering")

        if status:
            qs = qs.filter(status=status)

        if order_type:
            qs = qs.filter(order_type=order_type)

        if user_mobile:
            qs = qs.filter(user__mobile__icontains=user_mobile)

        if search:
            qs = qs.filter(
                Q(user__mobile__icontains=search) |
                Q(user__first_name__icontains=search) |
                Q(user__last_name__icontains=search) |
                Q(description__icontains=search)
            )

        if start_date:
            qs = qs.filter(created_at__date__gte=start_date)

        if end_date:
            qs = qs.filter(created_at__date__lte=end_date)

        # مرتب‌سازی
        ordering_map = {
            "id": "id",
            "-id": "-id",
            "created_at": "created_at",
            "-created_at": "-created_at",
            "weight": "weight",
            "-weight": "-weight",
            "entry_price": "entry_price",
            "-entry_price": "-entry_price",
            "profit_loss": "profit_loss",
            "-profit_loss": "-profit_loss",
            "status": "status",
            "-status": "-status",
        }

        if ordering in ordering_map:
            qs = qs.order_by(ordering_map[ordering])

        return qs

    # ======================
    # LIST
    # ======================
    def list(self, request):
        orders = self.get_queryset()
        
        # صفحه‌بندی
        page = self.paginate_queryset(orders)
        if page is not None:
            serializer = AdminGoldShortOrderListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = AdminGoldShortOrderListSerializer(orders, many=True)
        return success_response(
            "لیست سفارشات فروش تعهدی",
            {
                "total_results": orders.count(),
                "results": serializer.data
            }
        )

    # ======================
    # RETRIEVE
    # ======================
    def retrieve(self, request, pk=None):
        order = get_object_or_404(GoldShortOrder, pk=pk)
        serializer = AdminGoldShortOrderDetailSerializer(order)
        return success_response("جزئیات سفارش فروش تعهدی", serializer.data)

    # ======================
    # UPDATE
    # ======================
    def update(self, request, pk=None):
        order = get_object_or_404(GoldShortOrder, pk=pk)
        
        serializer = AdminGoldShortOrderUpdateSerializer(
            order,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        # اگر وضعیت تغییر کرده، تاریخچه ثبت شود
        if 'status' in serializer.validated_data:
            GoldShortOrderHistory.objects.create(
                order=order,
                status=order.status,
                price=order.close_price or order.entry_price,
                profit_loss=order.profit_loss,
                description=f"تغییر وضعیت توسط ادمین: {order.get_status_display()}"
            )

        return success_response(
            "سفارش با موفقیت بروزرسانی شد",
            AdminGoldShortOrderDetailSerializer(order).data
        )

    # ======================
    # CLOSE ORDER
    # ======================
    @action(detail=True, methods=["post"])
    def close(self, request, pk=None):
        """
        بستن دستی سفارش توسط ادمین
        """
        order = get_object_or_404(GoldShortOrder, pk=pk)

        if order.status != 'ACTIVE':
            return error_response(
                message=f"سفارش در وضعیت {order.get_status_display()} قابل بستن نیست"
            )

        # قیمت بسته شدن (از درخواست یا قیمت فعلی)
        close_price = request.data.get("close_price")
        if close_price:
            close_price = Decimal(str(close_price))
        else:
            close_price = get_live_gold_price()
            if not close_price:
                return error_response("خطا در دریافت قیمت طلا", status_code=500)

        with transaction.atomic():
            # محاسبه سود/ضرر
            profit_loss = (order.entry_price - close_price) * order.weight * order.leverage
            profit_loss = profit_loss.quantize(Decimal("1"))

            # محاسبه کارمزد روزانه
            hours_active = (timezone.now() - order.created_at).total_seconds() / 3600
            daily_fee_rate = Decimal("0.0065")  # 0.65%
            daily_fee = (order.weight * order.entry_price * daily_fee_rate * Decimal(str(hours_active / 24))).quantize(Decimal("1"))
            total_fee = order.initial_fee + daily_fee

            # برگشت موجودی طلا
            inventory, _ = GoldInventory.objects.select_for_update().get_or_create(user=order.user)
            inventory.blocked_balance -= order.weight
            inventory.accessible_balance += order.weight
            inventory.save(update_fields=['accessible_balance', 'blocked_balance', 'updated_at'])

            # به‌روزرسانی سفارش
            order.status = 'CLOSED'
            order.close_price = close_price
            order.profit_loss = profit_loss
            order.daily_fee = daily_fee
            order.total_fee = total_fee
            order.closed_at = timezone.now()
            order.save(update_fields=['status', 'close_price', 'profit_loss', 'daily_fee', 'total_fee', 'closed_at', 'updated_at'])

            # ثبت تاریخچه
            GoldShortOrderHistory.objects.create(
                order=order,
                status='CLOSED',
                price=close_price,
                profit_loss=profit_loss,
                description=f'بسته شدن توسط ادمین - سود/ضرر: {profit_loss}'
            )

        return success_response(
            "سفارش با موفقیت بسته شد",
            {
                "order_id": order.id,
                "status": order.get_status_display(),
                "close_price": float(close_price),
                "profit_loss": float(profit_loss),
                "total_fee": float(total_fee),
            }
        )

    # ======================
    # LIQUIDATE ORDER
    # ======================
    @action(detail=True, methods=["post"])
    def liquidate(self, request, pk=None):
        """
        لیکوئید کردن سفارش توسط ادمین (سیستمی)
        """
        order = get_object_or_404(GoldShortOrder, pk=pk)

        if order.status != 'ACTIVE':
            return error_response(
                message=f"سفارش در وضعیت {order.get_status_display()} قابل لیکوئید نیست"
            )

        close_price = get_live_gold_price()
        if not close_price:
            return error_response("خطا در دریافت قیمت طلا", status_code=500)

        with transaction.atomic():
            # محاسبه ضرر
            profit_loss = (order.entry_price - close_price) * order.weight * order.leverage
            profit_loss = profit_loss.quantize(Decimal("1"))

            # برگشت موجودی طلا
            inventory, _ = GoldInventory.objects.select_for_update().get_or_create(user=order.user)
            inventory.blocked_balance -= order.weight
            inventory.accessible_balance += order.weight
            inventory.save(update_fields=['accessible_balance', 'blocked_balance', 'updated_at'])

            # به‌روزرسانی سفارش
            order.status = 'LIQUIDATED'
            order.close_price = close_price
            order.profit_loss = profit_loss
            order.closed_at = timezone.now()
            order.save(update_fields=['status', 'close_price', 'profit_loss', 'closed_at', 'updated_at'])

            # ثبت تاریخچه
            GoldShortOrderHistory.objects.create(
                order=order,
                status='LIQUIDATED',
                price=close_price,
                profit_loss=profit_loss,
                description=f'لیکوئید شد - ضرر: {profit_loss}'
            )

        return success_response(
            "سفارش لیکوئید شد",
            {
                "order_id": order.id,
                "status": order.get_status_display(),
                "close_price": float(close_price),
                "profit_loss": float(profit_loss),
            }
        )

    # ======================
    # CANCEL ORDER
    # ======================
    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        """
        لغو سفارش توسط ادمین
        """
        order = get_object_or_404(GoldShortOrder, pk=pk)

        if order.status != 'ACTIVE':
            return error_response(
                message=f"سفارش در وضعیت {order.get_status_display()} قابل لغو نیست"
            )

        with transaction.atomic():
            # برگشت موجودی طلا
            inventory, _ = GoldInventory.objects.select_for_update().get_or_create(user=order.user)
            inventory.blocked_balance -= order.weight
            inventory.accessible_balance += order.weight
            inventory.save(update_fields=['accessible_balance', 'blocked_balance', 'updated_at'])

            # به‌روزرسانی سفارش
            order.status = 'CANCELLED'
            order.closed_at = timezone.now()
            order.save(update_fields=['status', 'closed_at', 'updated_at'])

            # ثبت تاریخچه
            GoldShortOrderHistory.objects.create(
                order=order,
                status='CANCELLED',
                price=order.entry_price,
                description='لغو سفارش توسط ادمین'
            )

        return success_response(
            "سفارش با موفقیت لغو شد",
            {
                "order_id": order.id,
                "status": order.get_status_display(),
            }
        )

    # ======================
    # STATISTICS
    # ======================
    @action(detail=False, methods=["get"])
    def statistics(self, request):
        """
        آمار کلی سفارشات فروش تعهدی
        """
        total_orders = GoldShortOrder.objects.count()
        active_orders = GoldShortOrder.objects.filter(status='ACTIVE').count()
        closed_orders = GoldShortOrder.objects.filter(status='CLOSED').count()
        liquidated_orders = GoldShortOrder.objects.filter(status='LIQUIDATED').count()
        cancelled_orders = GoldShortOrder.objects.filter(status='CANCELLED').count()

        # مجموع سود/ضرر
        total_profit_loss = GoldShortOrder.objects.aggregate(
            total=Sum('profit_loss')
        )['total'] or Decimal("0")

        # کل وزن درگیر
        total_weight_active = GoldShortOrder.objects.filter(status='ACTIVE').aggregate(
            total=Sum('weight')
        )['total'] or Decimal("0")

        return success_response(
            "آمار سفارشات فروش تعهدی",
            {
                "total_orders": total_orders,
                "active_orders": active_orders,
                "closed_orders": closed_orders,
                "liquidated_orders": liquidated_orders,
                "cancelled_orders": cancelled_orders,
                "total_profit_loss": float(total_profit_loss),
                "total_weight_active": float(total_weight_active),
            }
        )



# =========================================================
# GOLD BALANCE ADJUSTMENT
# =========================================================
class GoldBalanceAdjustmentViewSet(AdminBaseViewSet):

    queryset = GoldBalanceAdjustment.objects.select_related(
        "user",
        "admin",
    ).order_by("-id")

    serializer_class = GoldBalanceAdjustmentSerializer

    # ======================
    # QUERYSET
    # ======================

    def get_queryset(self):

        qs = super().get_queryset()

        user_id = self.kwargs.get("user_id")

        if user_id:
            qs = qs.filter(user_id=user_id)

        return qs

    # ======================
    # LIST
    # ======================

    def list(self, request, user_id=None, *args, **kwargs):

        qs = self.get_queryset()

        serializer = self.get_serializer(
            qs,
            many=True,
        )

        return success_response(
            "لیست افزایش موجودی طلا",
            {
                "total_results": qs.count(),
                "results": serializer.data,
            },
        )

    # ======================
    # RETRIEVE
    # ======================

    def retrieve(self, request, user_id=None, pk=None, *args, **kwargs):

        obj = get_object_or_404(
            GoldBalanceAdjustment.objects.select_related(
                "user",
                "admin",
            ),
            pk=pk,
            user_id=user_id,
        )

        serializer = self.get_serializer(obj)

        return success_response(
            "جزئیات افزایش موجودی طلا",
            serializer.data,
        )

    # ======================
    # CREATE
    # ======================

    def create(self, request):

        serializer = self.get_serializer(data=request.data)

        serializer.is_valid(raise_exception=True)

        self.perform_create(serializer)

        return success_response(
            "افزایش موجودی طلا ثبت شد",
            self.get_serializer(serializer.instance).data,
        )

    @transaction.atomic
    def perform_create(self, serializer):

        user = serializer.validated_data["user"]

        wallet, _ = Wallet.objects.select_for_update().get_or_create(
            user=user
        )

        inventory, _ = GoldInventory.objects.select_for_update().get_or_create(
            user=user
        )

        wallet_amount = serializer.validated_data.get(
            "wallet_amount",
            0,
        )

        gold_amount = serializer.validated_data.get(
            "gold_amount",
            0,
        )

        wallet.accessible_toman += wallet_amount
        inventory.accessible_balance += gold_amount

        wallet.save(
            update_fields=["accessible_toman"]
        )

        inventory.save(
            update_fields=["accessible_balance"]
        )

        serializer.save(
            admin=request.user if False else self.request.user
        )

    # ======================
    # UPDATE
    # ======================

    def update(self, request, *args, **kwargs):

        partial = kwargs.pop(
            "partial",
            False,
        )

        obj = self.get_object()

        serializer = self.get_serializer(
            obj,
            data=request.data,
            partial=partial,
        )

        serializer.is_valid(
            raise_exception=True,
        )

        self.perform_update(serializer)

        return success_response(
            "افزایش موجودی طلا ویرایش شد",
            self.get_serializer(serializer.instance).data,
        )

    def partial_update(self, request, *args, **kwargs):

        kwargs["partial"] = True

        return self.update(
            request,
            *args,
            **kwargs,
        )

    @transaction.atomic
    def perform_update(self, serializer):

        instance = self.get_object()

        old_wallet = instance.wallet_amount
        old_gold = instance.gold_amount

        obj = serializer.save()

        wallet = Wallet.objects.select_for_update().get(
            user=obj.user
        )

        inventory = GoldInventory.objects.select_for_update().get(
            user=obj.user
        )

        wallet.accessible_toman += (
            obj.wallet_amount - old_wallet
        )

        inventory.accessible_balance += (
            obj.gold_amount - old_gold
        )

        wallet.save(
            update_fields=["accessible_toman"]
        )

        inventory.save(
            update_fields=["accessible_balance"]
        )

    # ======================
    # DELETE
    # ======================

    def destroy(self, request, *args, **kwargs):

        obj = self.get_object()

        self.perform_destroy(obj)

        return success_response(
            "افزایش موجودی طلا حذف شد"
        )

    @transaction.atomic
    def perform_destroy(self, instance):

        wallet = Wallet.objects.select_for_update().get(
            user=instance.user
        )

        inventory = GoldInventory.objects.select_for_update().get(
            user=instance.user
        )

        wallet.accessible_toman -= instance.wallet_amount

        inventory.accessible_balance -= instance.gold_amount

        wallet.save(
            update_fields=["accessible_toman"]
        )

        inventory.save(
            update_fields=["accessible_balance"]
        )

        instance.delete()





# =========================================================
# SILVER BALANCE ADJUSTMENT
# =========================================================
class SilverBalanceAdjustmentViewSet(AdminBaseViewSet):

    queryset = SilverBalanceAdjustment.objects.select_related(
        "user",
        "admin",
    ).order_by("-id")

    serializer_class = SilverBalanceAdjustmentSerializer

    # =====================================================
    # QUERYSET
    # =====================================================

    def get_queryset(self):

        qs = super().get_queryset()

        user_id = self.kwargs.get("user_id")

        if user_id:
            qs = qs.filter(user_id=user_id)

        return qs

    # =====================================================
    # LIST
    # =====================================================

    def list(self, request, user_id=None, *args, **kwargs):

        qs = self.get_queryset()

        serializer = self.get_serializer(
            qs,
            many=True,
        )

        return success_response(
            "لیست افزایش موجودی نقره",
            {
                "total_results": qs.count(),
                "results": serializer.data,
            },
        )

    # =====================================================
    # RETRIEVE
    # =====================================================

    def retrieve(self, request, user_id=None, pk=None, *args, **kwargs):

        obj = get_object_or_404(
            SilverBalanceAdjustment.objects.select_related(
                "user",
                "admin",
            ),
            pk=pk,
            user_id=user_id,
        )

        serializer = self.get_serializer(obj)

        return success_response(
            "جزئیات افزایش موجودی نقره",
            serializer.data,
        )

    # =====================================================
    # CREATE
    # =====================================================

    @transaction.atomic
    def create(self, request, *args, **kwargs):

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        obj = serializer.save(
            admin=request.user,
        )

        wallet, _ = SilverWallet.objects.select_for_update().get_or_create(
            user=obj.user,
        )

        inventory, _ = SilverInventory.objects.select_for_update().get_or_create(
            user=obj.user,
        )

        wallet.accessible_toman += obj.wallet_amount
        inventory.accessible_balance += obj.silver_amount

        wallet.save(update_fields=["accessible_toman"])
        inventory.save(update_fields=["accessible_balance"])

        return success_response(
            "افزایش موجودی نقره ثبت شد",
            self.get_serializer(obj).data,
        )

    # =====================================================
    # UPDATE
    # =====================================================

    @transaction.atomic
    def update(self, request, *args, **kwargs):

        partial = kwargs.pop("partial", False)

        obj = self.get_object()

        old_wallet = obj.wallet_amount
        old_silver = obj.silver_amount

        serializer = self.get_serializer(
            obj,
            data=request.data,
            partial=partial,
        )

        serializer.is_valid(raise_exception=True)

        obj = serializer.save()

        wallet = SilverWallet.objects.select_for_update().get(
            user=obj.user,
        )

        inventory = SilverInventory.objects.select_for_update().get(
            user=obj.user,
        )

        wallet.accessible_toman = (
            wallet.accessible_toman
            - old_wallet
            + obj.wallet_amount
        )

        inventory.accessible_balance = (
            inventory.accessible_balance
            - old_silver
            + obj.silver_amount
        )

        wallet.save(update_fields=["accessible_toman"])
        inventory.save(update_fields=["accessible_balance"])

        return success_response(
            "افزایش موجودی نقره ویرایش شد",
            self.get_serializer(obj).data,
        )

    # =====================================================
    # PATCH
    # =====================================================

    def partial_update(self, request, *args, **kwargs):

        kwargs["partial"] = True

        return self.update(
            request,
            *args,
            **kwargs,
        )

    # =====================================================
    # DELETE
    # =====================================================

    @transaction.atomic
    def destroy(self, request, *args, **kwargs):

        obj = self.get_object()

        wallet = SilverWallet.objects.select_for_update().get(
            user=obj.user,
        )

        inventory = SilverInventory.objects.select_for_update().get(
            user=obj.user,
        )

        wallet.accessible_toman -= obj.wallet_amount
        inventory.accessible_balance -= obj.silver_amount

        wallet.save(update_fields=["accessible_toman"])
        inventory.save(update_fields=["accessible_balance"])

        obj.delete()

        return success_response(
            "افزایش موجودی نقره حذف شد",
        )



# =========================================================
# GOLD BALANCE WITHDRAWAL
# =========================================================

class GoldBalanceWithdrawalViewSet(AdminBaseViewSet):

    queryset = GoldBalanceWithdrawal.objects.select_related(
        "user",
        "admin",
    ).order_by("-id")

    serializer_class = GoldBalanceWithdrawalSerializer

    # ======================
    # QUERYSET
    # ======================

    def get_queryset(self):

        qs = super().get_queryset()

        user_id = self.kwargs.get("user_id")

        if user_id:
            qs = qs.filter(user_id=user_id)

        return qs

    # ======================
    # LIST
    # ======================

    def list(self, request, user_id=None, *args, **kwargs):

        qs = self.get_queryset()

        serializer = self.get_serializer(
            qs,
            many=True,
        )

        return success_response(
            "لیست برداشت موجودی طلا",
            {
                "total_results": qs.count(),
                "results": serializer.data,
            },
        )

    # ======================
    # RETRIEVE
    # ======================

    def retrieve(self, request, user_id=None, pk=None, *args, **kwargs):

        obj = get_object_or_404(
            GoldBalanceWithdrawal.objects.select_related(
                "user",
                "admin",
            ),
            pk=pk,
            user_id=user_id,
        )

        serializer = self.get_serializer(obj)

        return success_response(
            "جزئیات برداشت موجودی طلا",
            serializer.data,
        )

    # ======================
    # CREATE
    # ======================

    def create(self, request):

        serializer = self.get_serializer(
            data=request.data,
        )

        serializer.is_valid(
            raise_exception=True,
        )

        response = self.perform_create(
            serializer,
        )

        if response is not None:
            return response

        return success_response(
            "برداشت موجودی طلا ثبت شد",
            self.get_serializer(
                serializer.instance,
            ).data,
        )
        
        

    @transaction.atomic
    def perform_create(self, serializer):

        user = serializer.validated_data["user"]

        wallet, _ = Wallet.objects.select_for_update().get_or_create(
            user=user,
        )

        inventory, _ = GoldInventory.objects.select_for_update().get_or_create(
            user=user,
        )

        wallet_amount = serializer.validated_data.get(
            "wallet_amount",
            0,
        )

        gold_amount = serializer.validated_data.get(
            "gold_amount",
            0,
        )

        if wallet.accessible_toman < wallet_amount:

            return error_response(
                message="موجودی تومان کاربر کافی نیست.",
            )

        if inventory.accessible_balance < gold_amount:

            return error_response(
                message="موجودی طلای کاربر کافی نیست.",
            )

        wallet.accessible_toman -= wallet_amount
        inventory.accessible_balance -= gold_amount

        wallet.save(
            update_fields=[
                "accessible_toman",
            ],
        )

        inventory.save(
            update_fields=[
                "accessible_balance",
            ],
        )

        serializer.save(
            admin=self.request.user,
        )

        return None
    
    
    # UPDATE
    # ======================

    def update(self, request, *args, **kwargs):

        partial = kwargs.pop(
            "partial",
            False,
        )

        instance = self.get_object()

        serializer = self.get_serializer(
            instance,
            data=request.data,
            partial=partial,
        )

        serializer.is_valid(
            raise_exception=True,
        )

        response = self.perform_update(
            serializer,
        )

        if response is not None:
            return response

        return success_response(
            "برداشت موجودی طلا ویرایش شد",
            self.get_serializer(
                serializer.instance,
            ).data,
        )
        

        
    def partial_update(self, request, *args, **kwargs):

        kwargs["partial"] = True

        return self.update(
            request,
            *args,
            **kwargs,
        )



    @transaction.atomic
    def perform_update(self, serializer):

        instance = self.get_object()

        wallet = Wallet.objects.select_for_update().get(
            user=instance.user
        )

        inventory = GoldInventory.objects.select_for_update().get(
            user=instance.user
        )

        # ==========================
        # برگرداندن برداشت قبلی
        # ==========================

        wallet.accessible_toman += instance.wallet_amount

        inventory.accessible_balance += instance.gold_amount

        # ==========================
        # مقادیر جدید
        # ==========================

        new_wallet_amount = serializer.validated_data.get(
            "wallet_amount",
            instance.wallet_amount,
        )

        new_gold_amount = serializer.validated_data.get(
            "gold_amount",
            instance.gold_amount,
        )

        # ==========================
        # بررسی موجودی
        # ==========================

        if wallet.accessible_toman < new_wallet_amount:

            return error_response(
                message="موجودی تومان کاربر کافی نیست.",
            )

        if inventory.accessible_balance < new_gold_amount:

            return error_response(
                message="موجودی طلای کاربر کافی نیست.",
            )

        # ==========================
        # اعمال برداشت جدید
        # ==========================

        wallet.accessible_toman -= new_wallet_amount

        inventory.accessible_balance -= new_gold_amount

        wallet.save(
            update_fields=[
                "accessible_toman",
            ]
        )

        inventory.save(
            update_fields=[
                "accessible_balance",
            ]
        )

        serializer.save()
        # ======================
    
    
    
    # DELETE
    # ======================

    def destroy(self, request, *args, **kwargs):

        obj = self.get_object()

        self.perform_destroy(obj)

        return success_response(
            "برداشت موجودی طلا حذف شد"
        )

    @transaction.atomic
    def perform_destroy(self, instance):

        wallet = Wallet.objects.select_for_update().get(
            user=instance.user
        )

        inventory = GoldInventory.objects.select_for_update().get(
            user=instance.user
        )

        # ==========================
        # برگشت موجودی
        # ==========================

        wallet.accessible_toman += instance.wallet_amount

        inventory.accessible_balance += instance.gold_amount

        wallet.save(
            update_fields=[
                "accessible_toman",
            ]
        )

        inventory.save(
            update_fields=[
                "accessible_balance",
            ]
        )

        instance.delete()



# =========================================================
# SILVER BALANCE WITHDRAWAL
# =========================================================

class SilverBalanceWithdrawalViewSet(AdminBaseViewSet):

    queryset = SilverBalanceWithdrawal.objects.select_related(
        "user",
        "admin",
    ).order_by("-id")

    serializer_class = SilverBalanceWithdrawalSerializer

    # ======================
    # QUERYSET
    # ======================

    def get_queryset(self):

        qs = super().get_queryset()

        user_id = self.kwargs.get("user_id")

        if user_id:
            qs = qs.filter(
                user_id=user_id,
            )

        return qs

    # ======================
    # LIST
    # ======================

    def list(self, request, user_id=None, *args, **kwargs):

        qs = self.get_queryset()

        serializer = self.get_serializer(
            qs,
            many=True,
        )

        return success_response(
            "لیست برداشت موجودی نقره",
            {
                "total_results": qs.count(),
                "results": serializer.data,
            },
        )

    # ======================
    # RETRIEVE
    # ======================

    def retrieve(self, request, user_id=None, pk=None, *args, **kwargs):

        obj = get_object_or_404(
            SilverBalanceWithdrawal.objects.select_related(
                "user",
                "admin",
            ),
            pk=pk,
            user_id=user_id,
        )

        serializer = self.get_serializer(
            obj,
        )

        return success_response(
            "جزئیات برداشت موجودی نقره",
            serializer.data,
        )

    # ======================
    # CREATE
    # ======================

    def create(self, request):

        serializer = self.get_serializer(
            data=request.data,
        )

        serializer.is_valid(
            raise_exception=True,
        )

        response = self.perform_create(
            serializer,
        )

        if response is not None:
            return response

        return success_response(
            "برداشت موجودی نقره ثبت شد",
            self.get_serializer(
                serializer.instance,
            ).data,
        )

    @transaction.atomic
    def perform_create(self, serializer):

        user = serializer.validated_data["user"]

        wallet, _ = SilverWallet.objects.select_for_update().get_or_create(
            user=user,
        )

        inventory, _ = SilverInventory.objects.select_for_update().get_or_create(
            user=user,
        )

        wallet_amount = serializer.validated_data.get(
            "wallet_amount",
            0,
        )

        silver_amount = serializer.validated_data.get(
            "silver_amount",
            0,
        )

        # ======================
        # CHECK BALANCE
        # ======================

        if wallet.accessible_toman < wallet_amount:

            return error_response(
                message="موجودی تومان کاربر کافی نیست.",
            )

        if inventory.accessible_balance < silver_amount:

            return error_response(
                message="موجودی نقره کاربر کافی نیست.",
            )

        # ======================
        # WITHDRAW
        # ======================

        wallet.accessible_toman -= wallet_amount
        inventory.accessible_balance -= silver_amount

        wallet.save(
            update_fields=[
                "accessible_toman",
            ],
        )

        inventory.save(
            update_fields=[
                "accessible_balance",
            ],
        )

        serializer.save(
            admin=self.request.user,
        )

        return None
        # ======================
    # UPDATE
    # ======================

    def update(self, request, *args, **kwargs):

        partial = kwargs.pop(
            "partial",
            False,
        )

        instance = self.get_object()

        serializer = self.get_serializer(
            instance,
            data=request.data,
            partial=partial,
        )

        serializer.is_valid(
            raise_exception=True,
        )

        response = self.perform_update(
            serializer,
        )

        if response is not None:
            return response

        return success_response(
            "برداشت موجودی نقره ویرایش شد",
            self.get_serializer(
                serializer.instance,
            ).data,
        )

    def partial_update(self, request, *args, **kwargs):

        kwargs["partial"] = True

        return self.update(
            request,
            *args,
            **kwargs,
        )

    @transaction.atomic
    def perform_update(self, serializer):

        instance = self.get_object()

        wallet = SilverWallet.objects.select_for_update().get(
            user=instance.user,
        )

        inventory = SilverInventory.objects.select_for_update().get(
            user=instance.user,
        )

        # ======================
        # برگرداندن برداشت قبلی
        # ======================

        wallet.accessible_toman += instance.wallet_amount
        inventory.accessible_balance += instance.silver_amount

        # ======================
        # مقادیر جدید
        # ======================

        new_wallet_amount = serializer.validated_data.get(
            "wallet_amount",
            instance.wallet_amount,
        )

        new_silver_amount = serializer.validated_data.get(
            "silver_amount",
            instance.silver_amount,
        )

        # ======================
        # بررسی موجودی
        # ======================

        if wallet.accessible_toman < new_wallet_amount:

            return error_response(
                message="موجودی تومان کاربر کافی نیست.",
            )

        if inventory.accessible_balance < new_silver_amount:

            return error_response(
                message="موجودی نقره کاربر کافی نیست.",
            )

        # ======================
        # اعمال برداشت جدید
        # ======================

        wallet.accessible_toman -= new_wallet_amount
        inventory.accessible_balance -= new_silver_amount

        wallet.save(
            update_fields=[
                "accessible_toman",
            ],
        )

        inventory.save(
            update_fields=[
                "accessible_balance",
            ],
        )

        serializer.save()

        return None
        # ======================
    # DELETE
    # ======================

    def destroy(self, request, *args, **kwargs):

        instance = self.get_object()

        self.perform_destroy(
            instance,
        )

        return success_response(
            "برداشت موجودی نقره حذف شد",
        )

    @transaction.atomic
    def perform_destroy(self, instance):

        wallet = SilverWallet.objects.select_for_update().get(
            user=instance.user,
        )

        inventory = SilverInventory.objects.select_for_update().get(
            user=instance.user,
        )

        # ======================
        # برگشت موجودی
        # ======================

        wallet.accessible_toman += instance.wallet_amount
        inventory.accessible_balance += instance.silver_amount

        wallet.save(
            update_fields=[
                "accessible_toman",
            ],
        )

        inventory.save(
            update_fields=[
                "accessible_balance",
            ],
        )

        instance.delete()



class CooperationRequestAdminViewSet(AdminBaseViewSet):

    queryset = CooperationRequest.objects.all().order_by("-id")

    def get_queryset(self):

        qs = super().get_queryset()

        search = self.request.GET.get("search")
        mobile = self.request.GET.get("mobile")
        ordering = self.request.GET.get("ordering")

        if search:
            qs = qs.filter(full_name__icontains=search)

        if mobile:
            qs = qs.filter(mobile__icontains=mobile)
        allowed_ordering = [
            "id",
            "-id",
            "created_at",
            "-created_at",
            "full_name",
            "full_name",
        ]
        if ordering in allowed_ordering:

            qs = qs.order_by(ordering)
        return qs

    queryset = CooperationRequest.objects.all().order_by("-id")

    # ======================
    # LIST
    # ======================
    def list(self, request):

        requests = self.get_queryset()

        results = []

        for item in requests:

            data = CooperationRequestListSerializer(item).data

            results.append(data)

        return success_response(
            "لیست درخواست‌های همکاری",
            {"total_results": len(results), "results": results},
        )

    # ======================
    # RETRIEVE
    # ======================
    def retrieve(self, request, pk=None):

        obj = get_object_or_404(CooperationRequest, pk=pk)

        data = CooperationRequestListSerializer(obj).data

        return success_response("جزئیات درخواست همکاری", data)


# =========================================================
# PRODUCT (GOLD)
# =========================================================


class ProductAdminViewSet(AdminBaseViewSet):

    queryset = Product.objects.all().order_by("-id")
    serializer_class = ProductSerializer

    def get_queryset(self):

        qs = super().get_queryset()

        search = self.request.GET.get("search")
        weight = self.request.GET.get("weight")
        ordering = self.request.GET.get("ordering")

        if search:
            qs = qs.filter(name__icontains=search)

        if weight:
            qs = qs.filter(weight=weight)

        allowed_ordering = [
            "id",
            "-id",
            "name",
            "-name",
            "weight",
            "-weight",
            "buy_price",
            "-buy_price",
            "sell_price",
            "-sell_price",
            "inventory_count",
            "-inventory_count",
            "created_at",
            "-created_at",
        ]

        # ❌ حذف فیلدهای محاسباتی که باعث 500 میشن
        # total_price
        # total_weight_with_fees

        if ordering in allowed_ordering:
            qs = qs.order_by(ordering)

        return qs

    def get_serializer_context(self):
        return {"request": self.request}

    queryset = Product.objects.all().order_by("-id")
    serializer_class = ProductSerializer

    def get_serializer_context(self):
        return {"request": self.request}

    # ======================
    # LIST
    # ======================
    def list(self, request):
        qs = self.get_queryset()

        ser = ProductSerializer(qs, many=True, context=self.get_serializer_context())

        return success_response(
            "لیست محصولات", {"total_results": qs.count(), "results": ser.data}
        )

    # ======================
    # RETRIEVE
    # ======================
    def retrieve(self, request, pk=None):
        obj = self.get_object()

        return success_response(
            "جزئیات محصول",
            ProductSerializer(obj, context=self.get_serializer_context()).data,
        )

    # ======================
    # CREATE (FIX مهم اینجاست)
    # ======================
    def create(self, request):
        ser = ProductCreateUpdateSerializer(
            data=request.data, context=self.get_serializer_context()
        )

        ser.is_valid(raise_exception=True)
        obj = ser.save()

        return success_response(
            "محصول ساخته شد",
            ProductSerializer(obj, context=self.get_serializer_context()).data,
        )

    # ======================
    # UPDATE
    # ======================
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        obj = self.get_object()

        ser = ProductCreateUpdateSerializer(
            obj,
            data=request.data,
            partial=partial,
            context=self.get_serializer_context(),
        )

        ser.is_valid(raise_exception=True)
        obj = ser.save()
        obj.refresh_from_db()

        return success_response(
            "محصول ویرایش شد",
            ProductSerializer(obj, context=self.get_serializer_context()).data,
        )

    def partial_update(self, request, *args, **kwargs):
        kwargs["partial"] = True
        return self.update(request, *args, **kwargs)

    # ======================
    # DELETE
    # ======================
    def destroy(self, request, *args, **kwargs):
        obj = self.get_object()
        obj.delete()

        return success_response("محصول حذف شد")


# =========================================================
# CATEGORY
# =========================================================


class CategoryAdminViewSet(AdminBaseViewSet):
    queryset = ProductCategory.objects.all().order_by("-id")
    serializer_class = ProductCategorySerializer

    def get_queryset(self):

        qs = super().get_queryset()

        search = self.request.GET.get("search")
        ordering = self.request.GET.get("ordering")

        if search:
            qs = qs.filter(name__icontains=search)

        allowed_ordering = [
            "id",
            "-id",
            "created_at",
            "-created_at",
            "name",
            "-name",
        ]

        if ordering in allowed_ordering:
            qs = qs.order_by(ordering)

        return qs

    queryset = ProductCategory.objects.all().order_by("-id")
    serializer_class = ProductCategorySerializer

    # ======================
    # LIST
    # ======================
    def list(self, request):
        qs = self.get_queryset()

        return success_response(
            "لیست دسته‌بندی‌ها",
            {
                "total_results": qs.count(),
                "results": self.serializer_class(qs, many=True).data,
            },
        )

    # ======================
    # RETRIEVE
    # ======================
    def retrieve(self, request, pk=None):
        obj = self.get_object()

        return success_response("جزئیات دسته‌بندی", self.serializer_class(obj).data)

    # ======================
    # CREATE
    # ======================
    def create(self, request):
        ser = self.serializer_class(data=request.data)
        ser.is_valid(raise_exception=True)
        obj = ser.save()

        return success_response("دسته‌بندی ساخته شد", self.serializer_class(obj).data)

    # ======================
    # UPDATE
    # ======================
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        obj = self.get_object()

        ser = self.serializer_class(obj, data=request.data, partial=partial)
        ser.is_valid(raise_exception=True)
        obj = ser.save()
        obj.refresh_from_db()

        return success_response("دسته‌بندی ویرایش شد", self.serializer_class(obj).data)

    def partial_update(self, request, *args, **kwargs):
        kwargs["partial"] = True
        return self.update(request, *args, **kwargs)

    # ======================
    # DELETE
    # ======================
    def destroy(self, request, *args, **kwargs):
        obj = self.get_object()
        obj.delete()

        return success_response("دسته‌بندی حذف شد")


# =========================================================
# SILVER PRODUCT
# =========================================================


class SilverProductAdminViewSet(AdminBaseViewSet):

    queryset = SilverProduct.objects.all().order_by("-id")
    serializer_class = SilverProductSerializer

    def get_queryset(self):

        qs = super().get_queryset()

        search = self.request.GET.get("search")
        weight = self.request.GET.get("weight")
        ordering = self.request.GET.get("ordering")

        if search:
            qs = qs.filter(name__icontains=search)

        if weight:
            qs = qs.filter(weight=weight)

        allowed_ordering = [
            "id",
            "-id",
            "name",
            "-name",
            "weight",
            "-weight",
            "buy_price",
            "-buy_price",
            "sell_price",
            "-sell_price",
            "inventory_count",
            "-inventory_count",
            "created_at",
            "-created_at",
        ]

        if ordering in allowed_ordering:
            qs = qs.order_by(ordering)

        return qs

    def get_serializer_context(self):
        return {"request": self.request}

    queryset = SilverProduct.objects.all().order_by("-id")
    serializer_class = SilverProductSerializer

    parser_classes = (
        MultiPartParser,
        FormParser,
    )

    def get_serializer_context(self):
        return {"request": self.request}

    # ======================
    # LIST
    # ======================
    def list(self, request):
        qs = self.get_queryset()

        ser = SilverProductSerializer(
            qs, many=True, context=self.get_serializer_context()
        )

        return success_response(
            "لیست محصولات نقره", {"total_results": qs.count(), "results": ser.data}
        )

    # ======================
    # RETRIEVE
    # ======================
    def retrieve(self, request, pk=None):
        obj = self.get_object()

        return success_response(
            "جزئیات محصول نقره",
            SilverProductSerializer(obj, context=self.get_serializer_context()).data,
        )

    # ======================
    # CREATE
    # ======================
    def create(self, request):

        ser = SilverProductCreateUpdateSerializer(
            data=request.data, context=self.get_serializer_context()
        )

        ser.is_valid(raise_exception=True)
        obj = ser.save()

        return success_response(
            "محصول نقره ساخته شد",
            SilverProductSerializer(obj, context=self.get_serializer_context()).data,
        )

    # ======================
    # UPDATE
    # ======================
    def update(self, request, *args, **kwargs):

        partial = kwargs.pop("partial", False)

        obj = self.get_object()

        ser = SilverProductCreateUpdateSerializer(
            obj,
            data=request.data,
            partial=partial,
            context=self.get_serializer_context(),
        )

        ser.is_valid(raise_exception=True)
        obj = ser.save()
        obj.refresh_from_db()

        return success_response(
            "محصول نقره ویرایش شد",
            SilverProductSerializer(obj, context=self.get_serializer_context()).data,
        )

    def partial_update(self, request, *args, **kwargs):
        kwargs["partial"] = True
        return self.update(request, *args, **kwargs)

    # ======================
    # DELETE
    # ======================
    def destroy(self, request, *args, **kwargs):

        obj = self.get_object()
        obj.delete()

        return success_response("محصول نقره حذف شد")


# =========================================================
# GIFT CARD
# =========================================================


class GiftCardAdminViewSet(AdminBaseViewSet):

    queryset = GiftCard.objects.all().order_by("-id")

    def get_queryset(self):

        qs = super().get_queryset()

        search = self.request.GET.get("search")
        status = self.request.GET.get("status")
        activated_by_name = self.request.GET.get("activated_by_name")
        serial_number = self.request.GET.get("serial_number")
        ordering = self.request.GET.get("ordering")

        if search:
            qs = qs.filter(created_by__mobile__icontains=search)

        if status:
            qs = qs.filter(status=status)

        if activated_by_name:
            qs = qs.filter(activated_by__mobile__icontains=activated_by_name)

        if serial_number:
            qs = qs.filter(serial_number__icontains=serial_number)
        allowed_ordering = [
            "id",
            "-id",
            "created_at",
            "-created_at",
            "weight",
            "-weight",
            "first_name",
            "status",
            "-status",
            "serial_number",
            "-serial_number",
        ]
        if ordering in allowed_ordering:

            qs = qs.order_by(ordering)
        return qs

    queryset = GiftCard.objects.all().order_by("-id")
    serializer_class = GiftCardSerializer

    # ======================
    # LIST
    # ======================
    def list(self, request):
        qs = self.get_queryset()

        return success_response(
            "لیست کارت‌ها",
            {
                "total_results": qs.count(),
                "results": GiftCardSerializer(qs, many=True).data,
            },
        )

    # ======================
    # RETRIEVE
    # ======================
    def retrieve(self, request, pk=None):
        obj = self.get_object()
        return success_response("جزئیات کارت", GiftCardSerializer(obj).data)

    # ======================
    # CREATE
    # ======================
    def create(self, request):
        ser = GiftCardCreateUpdateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)

        obj = ser.save(created_by=request.user, status="ACTIVE", is_used=False)

        return success_response("کارت ساخته شد", GiftCardSerializer(obj).data)

    # ======================
    # UPDATE
    # ======================
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        obj = self.get_object()

        ser = GiftCardCreateUpdateSerializer(obj, data=request.data, partial=partial)

        ser.is_valid(raise_exception=True)
        obj = ser.save()
        obj.refresh_from_db()

        return success_response("کارت ویرایش شد", GiftCardSerializer(obj).data)

    def partial_update(self, request, *args, **kwargs):
        kwargs["partial"] = True
        return self.update(request, *args, **kwargs)

    # ======================
    # DELETE
    # ======================
    def destroy(self, request, *args, **kwargs):
        obj = self.get_object()
        obj.delete()

        return success_response("کارت حذف شد")

    # ======================
    # CHANGE STATUS
    # ======================
    @action(detail=True, methods=["post"])
    def change_status(self, request, pk=None):
        obj = self.get_object()

        status_val = request.data.get("status")

        if status_val not in ["ACTIVE", "USED", "EXPIRED"]:
            return error_response("وضعیت نامعتبر است")

        obj.status = status_val

        if status_val == "USED":
            obj.is_used = True

        obj.save()
        obj.refresh_from_db()

        return success_response("وضعیت کارت تغییر کرد", GiftCardSerializer(obj).data)


# =========================================================
# ORDERS
# =========================================================

from rest_framework.decorators import action


from django.db import transaction
from django.db.models import F
from rest_framework.decorators import action


from django.db import transaction
from django.db.models import F
from rest_framework.decorators import action

# class OrderAdminViewSet(AdminBaseViewSet):

#     queryset = Order.objects.all().order_by("-id")
#     serializer_class = OrderSerializer

#     # =====================================================
#     # QUERYSET FILTER
#     # =====================================================
#     def get_queryset(self):

#         qs = super().get_queryset()

#         search = self.request.GET.get("search")
#         status = self.request.GET.get("status")
#         tracking_code = self.request.GET.get("tracking_code")
#         start_date = self.request.GET.get("start_date")
#         end_date = self.request.GET.get("end_date")
#         ordering = self.request.GET.get("ordering")

#         if search:
#             qs = qs.filter(user__mobile__icontains=search)

#         if status:
#             qs = qs.filter(status=status)

#         if tracking_code:
#             qs = qs.filter(tracking_code__icontains=tracking_code)

#         if start_date:
#             qs = qs.filter(created_at__date__gte=start_date)

#         if end_date:
#             qs = qs.filter(created_at__date__lte=end_date)

#         allowed_ordering = [
#             "id", "-id",
#             "created_at", "-created_at",
#             "status", "-status",
#         ]

#         if ordering in allowed_ordering:
#             qs = qs.order_by(ordering)

#         return qs

#     # =====================================================
#     # LIST
#     # =====================================================
#     def list(self, request):

#         qs = self.get_queryset()

#         return success_response(
#             "لیست سفارش‌ها",
#             {
#                 "total_results": qs.count(),
#                 "results": self.serializer_class(
#                     qs,
#                     many=True,
#                     context={"request": request}
#                 ).data
#             }
#         )

#     # =====================================================
#     # RETRIEVE
#     # =====================================================
#     def retrieve(self, request, pk=None):

#         obj = self.get_object()

#         data = self.serializer_class(
#             obj,
#             context={"request": request}
#         ).data

#         data["created_at"] = obj.created_at.strftime("%Y-%m-%d %H:%M:%S")

#         return success_response(
#             "جزئیات سفارش",
#             data
#         )

#     # =====================================================
#     # PATCH /orders/{id}/  (IMPORTANT FIX)
#     # =====================================================
#     @transaction.atomic
#     def partial_update(self, request, *args, **kwargs):

#         if "status" in request.data:
#             return self._change_status(request, kwargs["pk"])

#         return super().partial_update(request, *args, **kwargs)

#     # =====================================================
#     # PUT /orders/{id}/
#     # =====================================================
#     @transaction.atomic
#     def update(self, request, *args, **kwargs):

#         if "status" in request.data:
#             return self._change_status(request, kwargs["pk"])

#         return super().update(request, *args, **kwargs)

#     # =====================================================
#     # CHANGE STATUS ENDPOINT
#     # =====================================================
#     @action(detail=True, methods=["post"])
#     @transaction.atomic
#     def change_status(self, request, pk=None):
#         return self._change_status(request, pk)

#     # =====================================================
#     # CORE BUSINESS LOGIC (SINGLE SOURCE OF TRUTH)
#     # =====================================================
#     def _change_status(self, request, pk):

#         order = (
#             Order.objects
#             .select_for_update()
#             .select_related("user")
#             .prefetch_related("items__product")
#             .get(pk=pk)
#         )
#         wallet = Wallet.objects.select_for_update().get(user=order.user)
#         inventory = GoldInventory.objects.select_for_update().get(user=order.user)
#         serializer = StatusUpdateSerializer(data=request.data)
#         serializer.is_valid(raise_exception=True)

#         new_status = serializer.validated_data["status"]
#         description = serializer.validated_data.get("description", "")

#         old_status = order.status

#         if old_status == new_status:
#             return error_response("وضعیت تغییری نکرده است.")

#         if old_status == "DELIVERED" and new_status == "CANCELLED":
#             return error_response("امکان لغو سفارش تحویل داده شده وجود ندارد.")

#         order.status = new_status
#         order.save(update_fields=["status"])

#         OrderStatusHistory.objects.create(
#             order=order,
#             status=new_status,
#             description=description
#         )

#         wallet = order.user.wallet
#         inventory = order.user.gold_inventory

#         # =================================================
#         # DELIVERED
#         # =================================================
#         if new_status == "DELIVERED":

#             for item in order.items.all():

#                 product = item.product

#                 if product.inventory_count < item.quantity:
#                     return error_response(
#                         f"موجودی {product.title} کافی نیست."
#                     )

#                 product.inventory_count = F("inventory_count") - item.quantity
#                 product.save(update_fields=["inventory_count"])

#             if order.payment_method == "TOMAN":

#                 wallet.blocked_toman = max(
#                     0,
#                     wallet.blocked_toman - order.total_toman_amount
#                 )
#                 wallet.save(update_fields=["blocked_toman"])

#             elif order.payment_method == "GOLD":

#                 inventory.blocked_balance = max(
#                     0,
#                     inventory.blocked_balance - order.total_gold_amount
#                 )
#                 inventory.save(update_fields=["blocked_balance"])

#         # =================================================
#         # CANCELLED
#         # =================================================
#         elif new_status == "CANCELLED":

#             if order.payment_method == "TOMAN":

#                 wallet.accessible_toman += order.total_toman_amount
#                 wallet.blocked_toman = max(
#                     0,
#                     wallet.blocked_toman - order.total_toman_amount
#                 )

#                 wallet.save(update_fields=[
#                     "accessible_toman",
#                     "blocked_toman",
#                 ])

#             elif order.payment_method == "GOLD":

#                 inventory.accessible_balance += order.total_gold_amount
#                 inventory.blocked_balance = max(
#                     0,
#                     inventory.blocked_balance - order.total_gold_amount
#                 )

#                 inventory.save(update_fields=[
#                     "accessible_balance",
#                     "blocked_balance",
#                 ])

#         order.refresh_from_db()

#         return success_response(
#             "وضعیت سفارش با موفقیت تغییر کرد.",
#             self.serializer_class(
#                 order,
#                 context={"request": request}
#             ).data
#         )

# admin_panel/views.py - OrderAdminViewSet کامل

# admin_panel/views.py - OrderAdminViewSet اصلاح شده

from rest_framework.decorators import action
from django.db import transaction
from django.db.models import F, Q
from decimal import Decimal
import traceback

from admin_panel.serializers import StatusUpdateSerializer, OrderSerializer
from admin_panel.utils import create_admin_log
from accounts.utils import success_response, error_response
from gold_app.models import Order, OrderStatusHistory, OrderItem, Wallet, GoldInventory
from gold_app.services.physical_invoice_service import PhysicalOrderInvoiceService


class OrderAdminViewSet(AdminBaseViewSet):
    """
    مدیریت سفارشات فیزیکی توسط ادمین
    
    قابلیت‌ها:
    - لیست سفارشات با فیلترهای مختلف
    - مشاهده جزئیات سفارش
    - تغییر وضعیت سفارش 
    - امکان تغییر مستقیم از هر وضعیتی به DELIVERED (تحویل)
    - ایجاد خودکار فاکتور فقط برای سفارش‌های با پرداخت TOMAN (کیف پول)
    - لغو سفارش (CANCELLED) با برگشت مبلغ/طلا
    """

    queryset = Order.objects.all().order_by("-id")
    serializer_class = OrderSerializer

    # =====================================================
    # QUERYSET FILTER
    # =====================================================
    def get_queryset(self):
        qs = super().get_queryset()

        search = self.request.GET.get("search")
        status = self.request.GET.get("status")
        tracking_code = self.request.GET.get("tracking_code")
        payment_method = self.request.GET.get("payment_method")
        start_date = self.request.GET.get("start_date")
        end_date = self.request.GET.get("end_date")
        ordering = self.request.GET.get("ordering")

        if search:
            qs = qs.filter(
                Q(user__mobile__icontains=search) |
                Q(user__first_name__icontains=search) |
                Q(user__last_name__icontains=search) |
                Q(tracking_code__icontains=search)
            )

        if status:
            qs = qs.filter(status=status)

        if tracking_code:
            qs = qs.filter(tracking_code__icontains=tracking_code)

        if payment_method:
            qs = qs.filter(payment_method=payment_method)

        if start_date:
            qs = qs.filter(created_at__date__gte=start_date)

        if end_date:
            qs = qs.filter(created_at__date__lte=end_date)

        allowed_ordering = [
            "id", "-id",
            "created_at", "-created_at",
            "updated_at", "-updated_at",
            "status", "-status",
            "total_toman_amount", "-total_toman_amount",
            "total_gold_amount", "-total_gold_amount",
        ]

        if ordering in allowed_ordering:
            qs = qs.order_by(ordering)

        return qs

    # =====================================================
    # LIST
    # =====================================================
    def list(self, request):
        qs = self.get_queryset()

        results = []
        for order in qs:
            data = self.serializer_class(order, context={"request": request}).data
            
            # اضافه کردن اطلاعات فاکتور
            try:
                invoice = order.physical_invoices.first()
                if invoice:
                    data["physical_invoice_id"] = invoice.id
                    data["physical_invoice_number"] = invoice.invoice_number
                    data["physical_invoice_status"] = invoice.status
                    data["physical_invoice_status_display"] = invoice.get_status_display()
                else:
                    data["physical_invoice_id"] = None
                    data["physical_invoice_number"] = None
            except:
                data["physical_invoice_id"] = None
                data["physical_invoice_number"] = None
            
            results.append(data)

        return success_response(
            "لیست سفارش‌ها",
            {
                "total_results": qs.count(),
                "results": results
            }
        )

    # =====================================================
    # RETRIEVE
    # =====================================================
    def retrieve(self, request, pk=None):
        obj = self.get_object()

        data = self.serializer_class(obj, context={"request": request}).data

        # تاریخچه وضعیت‌ها
        status_history = obj.status_history.all().values(
            'status', 'description', 'created_at'
        )
        data["status_history"] = list(status_history)

        # اطلاعات فاکتور
        try:
            invoice = obj.physical_invoices.first()
            if invoice:
                data["physical_invoice_id"] = invoice.id
                data["physical_invoice_number"] = invoice.invoice_number
                data["physical_invoice_status"] = invoice.status
                data["physical_invoice_status_display"] = invoice.get_status_display()
                data["physical_invoice_date"] = invoice.invoice_date
                data["physical_invoice_total"] = invoice.total_amount
            else:
                data["physical_invoice_id"] = None
                data["physical_invoice_number"] = None
        except:
            data["physical_invoice_id"] = None
            data["physical_invoice_number"] = None

        return success_response(
            "جزئیات سفارش",
            data
        )

    # =====================================================
    # PATCH /orders/{id}/
    # =====================================================
    @transaction.atomic
    def partial_update(self, request, *args, **kwargs):
        if "status" in request.data:
            return self._change_status(request, kwargs["pk"])
        return super().partial_update(request, *args, **kwargs)

    # =====================================================
    # PUT /orders/{id}/
    # =====================================================
    @transaction.atomic
    def update(self, request, *args, **kwargs):
        if "status" in request.data:
            return self._change_status(request, kwargs["pk"])
        return super().update(request, *args, **kwargs)

    # =====================================================
    # CHANGE STATUS ENDPOINT
    # =====================================================
    @action(detail=True, methods=["post"])
    @transaction.atomic
    def change_status(self, request, pk=None):
        return self._change_status(request, pk)

    # =====================================================
    # CREATE INVOICE (برای سفارش‌های بدون فاکتور)
    # =====================================================
    @action(detail=True, methods=["post"])
    @transaction.atomic
    def create_invoice(self, request, pk=None):
        """
        ایجاد فاکتور برای سفارش تحویل شده (در صورت عدم وجود)
        فقط برای سفارش‌های با پرداخت TOMAN
        """
        try:
            order = (
                Order.objects
                .select_for_update()
                .select_related("user")
                .prefetch_related("items__product")
                .get(pk=pk)
            )
        except Order.DoesNotExist:
            return error_response("سفارش یافت نشد", status_code=404)

        # بررسی وضعیت سفارش
        if order.status != "DELIVERED":
            return error_response(
                f"فقط سفارش‌های تحویل شده قابلیت ایجاد فاکتور دارند. وضعیت فعلی: {order.get_status_display()}"
            )

        # ✅ فقط سفارش‌های با پرداخت TOMAN فاکتور دارند
        if order.payment_method != "TOMAN":
            return error_response(
                f"سفارش‌های با پرداخت {order.get_payment_method_display()} فاکتور ندارند. فقط سفارش‌های با پرداخت کیف پول فاکتور دارند."
            )

        # بررسی وجود فاکتور
        existing_invoice = order.physical_invoices.first()
        if existing_invoice:
            return success_response(
                "فاکتور قبلاً ایجاد شده است",
                {
                    "physical_invoice_id": existing_invoice.id,
                    "physical_invoice_number": existing_invoice.invoice_number,
                    "status": existing_invoice.status,
                    "status_display": existing_invoice.get_status_display()
                }
            )

        # ایجاد فاکتور
        try:
            invoice = PhysicalOrderInvoiceService.create_invoice(order, request)
            
            create_admin_log(
                request=request,
                user=order.user,
                action_type="PHYSICAL_INVOICE_CREATED",
                action="ایجاد فاکتور سفارش فیزیکی",
                model_name="PhysicalOrderInvoice",
                object_id=invoice.id,
                tracking_code=order.tracking_code,
                success=True,
                description=f"""
ایجاد فاکتور سفارش فیزیکی

کاربر: {order.user.mobile}
کد رهگیری: {order.tracking_code}
شماره فاکتور: {invoice.invoice_number}
مبلغ کل: {order.total_toman_amount:,} تومان
وزن طلا: {order.total_gold_amount} گرم
روش پرداخت: {order.get_payment_method_display()}
"""
            )

            return success_response(
                "فاکتور با موفقیت ایجاد شد",
                {
                    "physical_invoice_id": invoice.id,
                    "physical_invoice_number": invoice.invoice_number,
                    "status": invoice.status,
                    "status_display": invoice.get_status_display(),
                    "invoice_date": invoice.invoice_date
                }
            )

        except Exception as e:
            print(f"❌ خطا در ایجاد فاکتور: {e}")
            traceback.print_exc()
            return error_response(f"خطا در ایجاد فاکتور: {str(e)}", status_code=500)

    # =====================================================
    # CANCEL ORDER
    # =====================================================
    @action(detail=True, methods=["post"])
    @transaction.atomic
    def cancel_order(self, request, pk=None):
        """لغو سفارش با برگشت مبلغ/طلا به کاربر"""
        
        try:
            order = (
                Order.objects
                .select_for_update()
                .select_related("user")
                .prefetch_related("items__product")
                .get(pk=pk)
            )
        except Order.DoesNotExist:
            return error_response("سفارش یافت نشد", status_code=404)

        if order.status in ["DELIVERED", "CANCELLED"]:
            return error_response(
                f"سفارش در وضعیت {order.get_status_display()} قابل لغو نیست"
            )

        wallet, _ = Wallet.objects.select_for_update().get_or_create(user=order.user)
        inventory, _ = GoldInventory.objects.select_for_update().get_or_create(user=order.user)

        # برگشت مبلغ/طلا
        if order.payment_method == "TOMAN":
            wallet.accessible_toman += order.total_toman_amount
            wallet.blocked_toman = max(0, wallet.blocked_toman - order.total_toman_amount)
            wallet.save(update_fields=["accessible_toman", "blocked_toman"])
        elif order.payment_method == "GOLD":
            inventory.accessible_balance += order.total_gold_amount
            inventory.blocked_balance = max(0, inventory.blocked_balance - order.total_gold_amount)
            inventory.save(update_fields=["accessible_balance", "blocked_balance"])

        order.status = "CANCELLED"
        order.save(update_fields=["status"])

        OrderStatusHistory.objects.create(
            order=order,
            status="CANCELLED",
            description="لغو سفارش توسط ادمین"
        )

        # اگر فاکتوری وجود داشت، وضعیت آن را تغییر بده
        try:
            invoice = order.physical_invoices.first()
            if invoice:
                invoice.status = "REJECTED"
                invoice.save(update_fields=["status"])
        except:
            pass

        create_admin_log(
            request=request,
            user=order.user,
            action_type="ORDER_CANCELLED",
            action="لغو سفارش فیزیکی",
            model_name="Order",
            object_id=order.id,
            tracking_code=order.tracking_code,
            success=True,
            description=f"""
لغو سفارش فیزیکی

کاربر: {order.user.mobile}
کد رهگیری: {order.tracking_code}
مبلغ کل: {order.total_toman_amount:,} تومان
وزن طلا: {order.total_gold_amount} گرم
روش پرداخت: {order.get_payment_method_display()}
"""
        )

        return success_response(
            "سفارش با موفقیت لغو شد",
            {
                "order_id": order.id,
                "tracking_code": order.tracking_code,
                "status": order.status,
                "status_display": order.get_status_display()
            }
        )

    # =====================================================
    # CORE BUSINESS LOGIC - تغییر وضعیت
    # =====================================================
    def _change_status(self, request, pk):
        """هسته اصلی تغییر وضعیت سفارش"""

        try:
            order = (
                Order.objects
                .select_for_update()
                .select_related("user")
                .prefetch_related("items__product")
                .get(pk=pk)
            )
        except Order.DoesNotExist:
            return error_response("سفارش یافت نشد", status_code=404)

        # =============================================
        # اعتبارسنجی
        # =============================================
        serializer = StatusUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response("اطلاعات نامعتبر است", serializer.errors)

        new_status = serializer.validated_data["status"]
        description = serializer.validated_data.get("description", "")

        old_status = order.status

        if old_status == new_status:
            return error_response("وضعیت تغییری نکرده است.")

        # =============================================
        # ✅ اجازه تغییر مستقیم به DELIVERED از هر وضعیتی
        # =============================================
        ALLOWED_TRANSITIONS = {
            "REQUESTED": ["CONFIRMED", "DELIVERED", "CANCELLED"],
            "CONFIRMED": ["PROCESSING", "DELIVERED", "CANCELLED"],
            "PROCESSING": ["SHIPPED", "DELIVERED", "CANCELLED"],
            "SHIPPED": ["DELIVERED", "CANCELLED"],
            "DELIVERED": [],
            "CANCELLED": [],
        }

        if new_status not in ALLOWED_TRANSITIONS.get(old_status, []):
            return error_response(
                f"امکان تغییر وضعیت از {order.get_status_display()} به {dict(Order.STATUS_CHOICES).get(new_status, new_status)} وجود ندارد."
            )

        # =============================================
        # دریافت کیف پول و موجودی
        # =============================================
        wallet, _ = Wallet.objects.select_for_update().get_or_create(user=order.user)
        inventory, _ = GoldInventory.objects.select_for_update().get_or_create(user=order.user)

        invoice_id = None
        invoice_number = None

        # =============================================
        # DELIVERED - تحویل سفارش و ایجاد فاکتور
        # =============================================
        if new_status == "DELIVERED":

            # =============================================
            # ۱. اگر قبلاً DELIVERED نبود، عملیات تحویل را انجام بده
            # =============================================
            if old_status != "DELIVERED":
                
                # کاهش موجودی محصولات
                for item in order.items.all():
                    product = item.product
                    if product.inventory_count < item.quantity:
                        return error_response(
                            f"موجودی {product.title} کافی نیست. موجودی: {product.inventory_count} - نیاز: {item.quantity}"
                        )
                    product.inventory_count = F("inventory_count") - item.quantity
                    product.save(update_fields=["inventory_count"])

                # آزادسازی مبلغ بلوکه شده
                if order.payment_method == "TOMAN":
                    if wallet.blocked_toman < order.total_toman_amount:
                        return error_response("مغایرت در موجودی بلوکه‌شده تومانی کاربر.")
                    wallet.blocked_toman = max(0, wallet.blocked_toman - order.total_toman_amount)
                    wallet.save(update_fields=["blocked_toman"])

                elif order.payment_method == "GOLD":
                    if inventory.blocked_balance < order.total_gold_amount:
                        return error_response("مغایرت در موجودی بلوکه‌شده طلای کاربر.")
                    inventory.blocked_balance = max(0, inventory.blocked_balance - order.total_gold_amount)
                    inventory.save(update_fields=["blocked_balance"])

            # =============================================
            # ۲. ✅ ایجاد فاکتور (فقط برای پرداخت TOMAN)
            # =============================================
            if order.payment_method == "TOMAN":
                existing_invoice = order.physical_invoices.first()
                
                if existing_invoice:
                    invoice_id = existing_invoice.id
                    invoice_number = existing_invoice.invoice_number
                else:
                    try:
                        invoice = PhysicalOrderInvoiceService.create_invoice(order, request)
                        invoice_id = invoice.id
                        invoice_number = invoice.invoice_number

                        create_admin_log(
                            request=request,
                            user=order.user,
                            action_type="PHYSICAL_ORDER_DELIVERED",
                            action="تحویل سفارش فیزیکی و ایجاد فاکتور",
                            model_name="Order",
                            object_id=order.id,
                            tracking_code=order.tracking_code,
                            success=True,
                            description=f"""
تحویل سفارش فیزیکی

کاربر: {order.user.mobile}
کد رهگیری: {order.tracking_code}
مبلغ کل: {order.total_toman_amount:,} تومان
وزن طلا: {order.total_gold_amount} گرم
شماره فاکتور: {invoice.invoice_number}
روش پرداخت: {order.get_payment_method_display()}
آدرس: {order.address}
"""
                        )

                    except Exception as e:
                        print(f"❌ خطا در ایجاد فاکتور: {e}")
                        traceback.print_exc()
            else:
                # پرداخت با طلا - فاکتور صادر نمی‌شود
                create_admin_log(
                    request=request,
                    user=order.user,
                    action_type="PHYSICAL_ORDER_DELIVERED_GOLD",
                    action="تحویل سفارش فیزیکی (پرداخت با طلا - بدون فاکتور)",
                    model_name="Order",
                    object_id=order.id,
                    tracking_code=order.tracking_code,
                    success=True,
                    description=f"""
تحویل سفارش فیزیکی (پرداخت با طلا)

کاربر: {order.user.mobile}
کد رهگیری: {order.tracking_code}
مبلغ کل: {order.total_toman_amount:,} تومان
وزن طلا: {order.total_gold_amount} گرم
روش پرداخت: {order.get_payment_method_display()}
آدرس: {order.address}
توجه: این سفارش با طلا پرداخت شده است و فاکتور ندارد.
"""
                )

        # =============================================
        # CANCELLED - لغو سفارش
        # =============================================
        elif new_status == "CANCELLED":

            if order.payment_method == "TOMAN":
                wallet.accessible_toman += order.total_toman_amount
                wallet.blocked_toman = max(0, wallet.blocked_toman - order.total_toman_amount)
                wallet.save(update_fields=["accessible_toman", "blocked_toman"])

            elif order.payment_method == "GOLD":
                inventory.accessible_balance += order.total_gold_amount
                inventory.blocked_balance = max(0, inventory.blocked_balance - order.total_gold_amount)
                inventory.save(update_fields=["accessible_balance", "blocked_balance"])

            try:
                invoice = order.physical_invoices.first()
                if invoice:
                    invoice.status = "REJECTED"
                    invoice.save(update_fields=["status"])
            except:
                pass

            create_admin_log(
                request=request,
                user=order.user,
                action_type="ORDER_CANCELLED",
                action="لغو سفارش فیزیکی",
                model_name="Order",
                object_id=order.id,
                tracking_code=order.tracking_code,
                success=True,
                description=f"""
لغو سفارش فیزیکی

کاربر: {order.user.mobile}
کد رهگیری: {order.tracking_code}
مبلغ کل: {order.total_toman_amount:,} تومان
وزن طلا: {order.total_gold_amount} گرم
دلیل: {description or 'لغو توسط ادمین'}
"""
            )

        # =============================================
        # سایر وضعیت‌ها (CONFIRMED, PROCESSING, SHIPPED)
        # =============================================
        else:
            create_admin_log(
                request=request,
                user=order.user,
                action_type=f"ORDER_{new_status}",
                action=f"تغییر وضعیت سفارش به {dict(Order.STATUS_CHOICES).get(new_status, new_status)}",
                model_name="Order",
                object_id=order.id,
                tracking_code=order.tracking_code,
                success=True,
                description=f"""
تغییر وضعیت سفارش

کاربر: {order.user.mobile}
کد رهگیری: {order.tracking_code}
وضعیت جدید: {dict(Order.STATUS_CHOICES).get(new_status, new_status)}
توضیحات: {description or '---'}
"""
            )

        # =============================================
        # به‌روزرسانی وضعیت سفارش
        # =============================================
        order.status = new_status
        order.save(update_fields=["status"])

        OrderStatusHistory.objects.create(
            order=order,
            status=new_status,
            description=description or f"وضعیت به {dict(Order.STATUS_CHOICES).get(new_status, new_status)} تغییر یافت"
        )

        # =============================================
        # پاسخ
        # =============================================
        order.refresh_from_db()

        response_data = self.serializer_class(order, context={"request": request}).data

        # ✅ اضافه کردن اطلاعات فاکتور به پاسخ (فقط برای پرداخت TOMAN)
        if order.payment_method == "TOMAN":
            try:
                invoice = order.physical_invoices.first()
                if invoice:
                    response_data["physical_invoice_id"] = invoice.id
                    response_data["physical_invoice_number"] = invoice.invoice_number
                    response_data["physical_invoice_status"] = invoice.status
                    response_data["physical_invoice_status_display"] = invoice.get_status_display()
                else:
                    response_data["physical_invoice_id"] = invoice_id if invoice_id else None
                    response_data["physical_invoice_number"] = invoice_number if invoice_number else None
            except:
                response_data["physical_invoice_id"] = None
                response_data["physical_invoice_number"] = None
        else:
            # پرداخت با طلا - فاکتور وجود ندارد
            response_data["physical_invoice_id"] = None
            response_data["physical_invoice_number"] = None
            response_data["physical_invoice_note"] = "سفارش با طلا پرداخت شده است و فاکتور ندارد"

        # تاریخچه وضعیت‌ها
        status_history = order.status_history.all().values('status', 'description', 'created_at')
        response_data["status_history"] = list(status_history)

        return success_response(
            f"وضعیت سفارش با موفقیت به {order.get_status_display()} تغییر یافت.",
            response_data
        )

# SILVER ORDER
# =========================================================


from django.db import transaction
from django.db.models import F
from rest_framework.decorators import action


class SilverOrderAdminViewSet(AdminBaseViewSet):

    queryset = SilverOrder.objects.all().order_by("-id")
    serializer_class = SilverOrderSerializer

    # =====================================================
    # QUERYSET FILTER
    # =====================================================
    def get_queryset(self):

        qs = super().get_queryset()

        search = self.request.GET.get("search")
        status = self.request.GET.get("status")
        tracking_code = self.request.GET.get("tracking_code")
        start_date = self.request.GET.get("start_date")
        end_date = self.request.GET.get("end_date")
        ordering = self.request.GET.get("ordering")

        if search:
            qs = qs.filter(user__mobile__icontains=search)

        if status:
            qs = qs.filter(status=status)

        if tracking_code:
            qs = qs.filter(tracking_code__icontains=tracking_code)

        if start_date:
            qs = qs.filter(created_at__date__gte=start_date)

        if end_date:
            qs = qs.filter(created_at__date__lte=end_date)

        allowed_ordering = [
            "id", "-id",
            "created_at", "-created_at",
            "status", "-status",
            "total_silver_amount", "-total_silver_amount",
            "total_toman_amount", "-total_toman_amount",
        ]

        if ordering in allowed_ordering:
            qs = qs.order_by(ordering)
        else:
            qs = qs.order_by("-id")

        return qs

    # =====================================================
    # LIST
    # =====================================================
    def list(self, request):

        qs = self.get_queryset()

        return success_response(
            "لیست سفارشات نقره",
            {
                "total_results": qs.count(),
                "results": self.serializer_class(
                    qs,
                    many=True,
                    context={"request": request}
                ).data,
            }
        )

    # =====================================================
    # RETRIEVE
    # =====================================================
    def retrieve(self, request, pk=None):

        obj = self.get_object()

        data = self.serializer_class(
            obj,
            context={"request": request}
        ).data

        data["created_at"] = obj.created_at.strftime("%Y-%m-%d %H:%M:%S")

        return success_response(
            "جزئیات سفارش نقره",
            data
        )

    # =====================================================
    # PATCH /orders/{id}/  (REDIRECT TO BUSINESS LOGIC)
    # =====================================================
    @transaction.atomic
    def partial_update(self, request, *args, **kwargs):

        if "status" in request.data:
            return self._change_status(request, kwargs["pk"])

        return super().partial_update(request, *args, **kwargs)

    # =====================================================
    # PUT /orders/{id}/
    # =====================================================
    @transaction.atomic
    def update(self, request, *args, **kwargs):

        if "status" in request.data:
            return self._change_status(request, kwargs["pk"])

        return super().update(request, *args, **kwargs)

    # =====================================================
    # PUBLIC ENDPOINT
    # =====================================================
    @action(detail=True, methods=["post"])
    @transaction.atomic
    def change_status(self, request, pk=None):
        return self._change_status(request, pk)

    # =====================================================
    # CORE LOGIC (NEXT PART WILL BE FULL IMPLEMENTATION)
    # =====================================================
    def _change_status(self, request, pk):
        pass
    
        # =====================================================
    # CORE BUSINESS LOGIC
    # =====================================================
    def _change_status(self, request, pk):

        order = (
            SilverOrder.objects
            .select_for_update()
            .select_related("user")
            .prefetch_related("items__product")
            .get(pk=pk)
        )

        wallet = SilverWallet.objects.select_for_update().get(
            user=order.user
        )

        inventory = SilverInventory.objects.select_for_update().get(
            user=order.user
        )

        serializer = StatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        new_status = serializer.validated_data["status"]
        description = serializer.validated_data.get("description", "")

        old_status = order.status

        # =====================================================
        # وضعیت تغییری نکرده
        # =====================================================

        if old_status == new_status:
            return error_response(
                message="وضعیت تغییری نکرده است."
            )

        # =====================================================
        # جلوگیری از لغو بعد از تحویل
        # =====================================================

        if old_status == "DELIVERED" and new_status == "CANCELLED":
            return error_response(
                message="امکان لغو سفارش تحویل داده شده وجود ندارد."
            )

        # =====================================================
        # تغییر وضعیت
        # =====================================================

        order.status = new_status
        order.save(update_fields=["status"])

        SilverOrderStatusHistory.objects.create(
            order=order,
            status=new_status,
            description=description,
        )

        # =====================================================
        # DELIVERED
        # =====================================================

        if new_status == "DELIVERED":

            for item in order.items.all():

                product = item.product

                if product.inventory_count < item.quantity:
                    return error_response(
                        message=f"موجودی محصول {product.title} کافی نیست."
                    )

                product.inventory_count = (
                    F("inventory_count") - item.quantity
                )

                product.save(update_fields=["inventory_count"])

            # -----------------------------
            # پرداخت با کیف پول
            # -----------------------------

            if order.payment_method == "TOMAN":

                wallet.blocked_toman = max(
                    0,
                    wallet.blocked_toman - order.total_toman_amount
                )

                wallet.save(
                    update_fields=["blocked_toman"]
                )

            # -----------------------------
            # پرداخت با نقره
            # -----------------------------

            elif order.payment_method == "SILVER":

                inventory.blocked_balance = max(
                    0,
                    inventory.blocked_balance - order.total_silver_amount
                )

                inventory.save(
                    update_fields=["blocked_balance"]
                )

        # =====================================================
        # CANCELLED
        # =====================================================

        elif new_status == "CANCELLED":

            # -----------------------------
            # بازگشت پول
            # -----------------------------

            if order.payment_method == "TOMAN":

                wallet.accessible_toman += order.total_toman_amount

                wallet.blocked_toman = max(
                    0,
                    wallet.blocked_toman - order.total_toman_amount
                )

                wallet.save(
                    update_fields=[
                        "accessible_toman",
                        "blocked_toman",
                    ]
                )

            # -----------------------------
            # بازگشت نقره
            # -----------------------------

            elif order.payment_method == "SILVER":

                inventory.accessible_balance += (
                    order.total_silver_amount
                )

                inventory.blocked_balance = max(
                    0,
                    inventory.blocked_balance - order.total_silver_amount
                )

                inventory.save(
                    update_fields=[
                        "accessible_balance",
                        "blocked_balance",
                    ]
                )

        order.refresh_from_db()

        return success_response(
            "وضعیت سفارش نقره با موفقیت تغییر کرد.",
            self.serializer_class(
                order,
                context={"request": request}
            ).data,
        )
        
        
# =========================================================
# DASHBOARD
# =========================================================


class DashboardAdminViewSet(ViewSet):

    permission_classes = [IsAdminRole]

    def list(self, request):

        # =====================================================
        # Counts
        # =====================================================

        users = User.objects.count()

        gold_products = Product.objects.count()

        silver_products = SilverProduct.objects.count()

        products = gold_products + silver_products

        orders = Order.objects.count()

        silver_orders = SilverOrder.objects.count()

        # =====================================================
        # Gold Wallets
        # =====================================================

        gold_wallet = Wallet.objects.aggregate(
            accessible=Sum("accessible_toman"), blocked=Sum("blocked_toman")
        )

        # =====================================================
        # Silver Wallets
        # =====================================================

        silver_wallet = SilverWallet.objects.aggregate(
            accessible=Sum("accessible_toman"), blocked=Sum("blocked_toman")
        )

        # =====================================================
        # Wallet Balance
        # =====================================================

        wallet_balance = (
            (gold_wallet["accessible"] or 0)
            + (gold_wallet["blocked"] or 0)
            + (silver_wallet["accessible"] or 0)
            + (silver_wallet["blocked"] or 0)
        )

        # =====================================================
        # Response
        # =====================================================

        return success_response(
            message="داشبورد",
            data={
                "users": users,
                "products": products,
                "gold_products": gold_products,
                "silver_products": silver_products,
                "orders": orders,
                "silver_orders": silver_orders,
                "wallet_balance": round(wallet_balance),
            },
        )


class GoldBankAdminViewSet(AdminBaseViewSet):

    queryset = GoldBankInfo.objects.all().order_by("-id")
    serializer_class = GoldBankInfoSerializer
    create_update_serializer_class = GoldBankInfoCreateUpdateSerializer

    def get_queryset(self):
        qs = super().get_queryset()

        search = self.request.GET.get("search")
        card_number = self.request.GET.get("card_number")
        iban = self.request.GET.get("iban")
        ordering = self.request.GET.get("ordering")

        if search:
            qs = qs.filter(full_name__icontains=search)

        if card_number:
            qs = qs.filter(card_number__icontains=card_number)

        if iban:
            qs = qs.filter(sheba__icontains=iban)

        allowed_ordering = [
            "id",
            "-id",
            "created_at",
            "-created_at",
            "full_name",
            "-full_name",
            "card_number",
            "-card_number",
            "sheba",
            "-sheba",
            "is_active",
            "-is_active",
        ]

        if ordering in allowed_ordering:
            qs = qs.order_by(ordering)

        return qs

    queryset = GoldBankInfo.objects.all().order_by("-id")

    serializer_class = GoldBankInfoSerializer

    create_update_serializer_class = GoldBankInfoCreateUpdateSerializer

    # ======================
    # LIST
    # ======================
    def list(self, request):

        qs = self.get_queryset()

        return success_response(
            "لیست کارت‌های طلا",
            {
                "total_results": qs.count(),
                "results": self.serializer_class(qs, many=True).data,
            },
        )

    # ======================
    # RETRIEVE
    # ======================
    def retrieve(self, request, pk=None):

        obj = self.get_object()

        return success_response("جزئیات کارت طلا", self.serializer_class(obj).data)

    # ======================
    # CREATE
    # ======================
    def create(self, request):

        serializer = self.create_update_serializer_class(data=request.data)

        serializer.is_valid(raise_exception=True)

        obj = serializer.save()

        return success_response("کارت طلا ساخته شد", self.serializer_class(obj).data)

    # ======================
    # UPDATE
    # ======================
    def update(self, request, *args, **kwargs):

        partial = kwargs.pop("partial", False)

        obj = self.get_object()

        serializer = self.create_update_serializer_class(
            obj, data=request.data, partial=partial
        )

        serializer.is_valid(raise_exception=True)

        obj = serializer.save()

        obj.refresh_from_db()

        return success_response("کارت طلا ویرایش شد", self.serializer_class(obj).data)

    def partial_update(self, request, *args, **kwargs):

        kwargs["partial"] = True

        return self.update(request, *args, **kwargs)

    # ======================
    # TOGGLE
    # ======================
    @action(detail=True, methods=["post"])
    def toggle(self, request, pk=None):

        bank = self.get_object()

        GoldBankInfo.objects.exclude(pk=bank.pk).update(is_active=False)

        bank.is_active = True
        bank.save()

        return success_response("کارت طلا فعال شد", {"is_active": True})


# admin_panel/views.py


from rest_framework.viewsets import ViewSet

from accounts.models import User

# from .serializers import AdminLogSerializer
from .utils import create_admin_log

# اگر قبلا داری پاک نکن


class IsAdminRole(IsAuthenticated):
    def has_permission(self, request, view):

        return request.user.is_authenticated and request.user.role == "admin"


from rest_framework.viewsets import ViewSet

from accounts.models import User


from decimal import Decimal


from rest_framework.viewsets import ViewSet

from accounts.models import User

from .permissions import IsAdminRole

# =========================================================
# ADMIN ANALYTICS
# =========================================================


class AdminAnalyticsViewSet(ViewSet):

    permission_classes = [IsAdminRole]

    def list(self, request):

        now = timezone.now()

        today = now.date()
        week = now - timedelta(days=7)
        month = now - timedelta(days=30)

        # =====================================================
        # GOLD
        # =====================================================

        gold_buy = GoldTransaction.objects.filter(type="BUY").aggregate(
            total=Sum("total_amount")
        )["total"] or Decimal("0")

        gold_sell = GoldTransaction.objects.filter(type="SELL").aggregate(
            total=Sum("total_amount")
        )["total"] or Decimal("0")

        # =====================================================
        # SILVER
        # =====================================================

        silver_buy = SilverTransaction.objects.filter(type="BUY").aggregate(
            total=Sum("total_amount")
        )["total"] or Decimal("0")

        silver_sell = SilverTransaction.objects.filter(type="SELL").aggregate(
            total=Sum("total_amount")
        )["total"] or Decimal("0")

        total_buy = gold_buy + silver_buy
        total_sell = gold_sell + silver_sell
        difference = total_buy - total_sell

        # =====================================================
        # REPORTS
        # =====================================================

        daily = (
            GoldTransaction.objects.filter(created_at__date=today).count()
            + SilverTransaction.objects.filter(created_at__date=today).count()
        )

        weekly = (
            GoldTransaction.objects.filter(created_at__gte=week).count()
            + SilverTransaction.objects.filter(created_at__gte=week).count()
        )

        monthly = (
            GoldTransaction.objects.filter(created_at__gte=month).count()
            + SilverTransaction.objects.filter(created_at__gte=month).count()
        )

        # =====================================================
        # USERS
        # =====================================================

        users = User.objects.count()

        # =====================================================
        # GOLD WALLET
        # =====================================================

        gold_accessible = Wallet.objects.aggregate(total=Sum("accessible_toman"))[
            "total"
        ] or Decimal("0")

        gold_blocked = Wallet.objects.aggregate(total=Sum("blocked_toman"))[
            "total"
        ] or Decimal("0")

        gold_wallet = gold_accessible + gold_blocked

        # =====================================================
        # SILVER WALLET
        # =====================================================

        silver_accessible = SilverWallet.objects.aggregate(
            total=Sum("accessible_toman")
        )["total"] or Decimal("0")

        silver_blocked = SilverWallet.objects.aggregate(total=Sum("blocked_toman"))[
            "total"
        ] or Decimal("0")

        silver_wallet = silver_accessible + silver_blocked

        # =====================================================
        # SERVER STATUS
        # =====================================================

        vm = psutil.virtual_memory()
        disk = psutil.disk_usage("/")

        server = {
            "cpu": round(psutil.cpu_percent(interval=1), 1),
            "ram": {
                "total_gb": round(vm.total / 1024**3, 2),
                "used_gb": round(vm.used / 1024**3, 2),
                "free_gb": round(vm.available / 1024**3, 2),
                "percent": round(vm.percent, 1),
            },
            "disk": {
                "total_gb": round(disk.total / 1024**3, 2),
                "used_gb": round(disk.used / 1024**3, 2),
                "free_gb": round(disk.free / 1024**3, 2),
                "percent": round(disk.percent, 1),
            },
        }

        # =====================================================
        # RESPONSE
        # =====================================================

        return Response(
            {
                "success": True,
                "message": "داشبورد",
                "data": {
                    "users": users,
                    "gold": {
                        "buy": float(gold_buy),
                        "sell": float(gold_sell),
                    },
                    "silver": {
                        "buy": float(silver_buy),
                        "sell": float(silver_sell),
                    },
                    "total_buy": float(total_buy),
                    "total_sell": float(total_sell),
                    "difference": float(difference),
                    "reports": {
                        "daily": daily,
                        "weekly": weekly,
                        "monthly": monthly,
                    },
                    "wallets": {
                        "gold": float(gold_wallet),
                        "silver": float(silver_wallet),
                    },
                    "server": server,
                },
            }
        )


# =====================================================
# CREATE LOG API TEST
# =====================================================


class AdminLogCreateTestView(ViewSet):

    permission_classes = [IsAdminRole]

    def create(self, request):

        log = create_admin_log(
            admin=request.user,
            action_type=request.data.get("action_type", "ADMIN"),
            action=request.data.get("action", "test"),
            model_name=request.data.get("model_name", "system"),
            description=request.data.get("description"),
        )

        return Response({"message": "log created"})


# admin_panel/views/admin_log.py


from rest_framework.decorators import action

from admin_panel.models import AdminLog
from admin_panel.permissions import IsAdminRole

from admin_panel.views import success_response
from admin_panel.serializers import (
    AdminLogListSerializer,
    AdminLogDetailSerializer,
)
from .serializers import (
    AdminLogListSerializer,
    AdminLogDetailSerializer,
)


class AdminLogViewSet(AdminBaseViewSet):
    """
    مدیریت لاگ‌های سیستم برای ادمین با Pagination دستی
    """

    permission_classes = [IsAdminRole]
    queryset = AdminLog.objects.all()
    serializer_class = AdminLogListSerializer
    ordering = ["-created_at"]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return AdminLogDetailSerializer
        return AdminLogListSerializer

    def get_queryset(self):
        qs = super().get_queryset()

        # ==========================
        # SEARCH
        # ==========================
        search = self.request.GET.get("search")
        if search:
            qs = qs.filter(
                Q(action__icontains=search)
                | Q(description__icontains=search)
                | Q(user__mobile__icontains=search)
                | Q(admin__mobile__icontains=search)
                | Q(ip_address__icontains=search)
                | Q(endpoint__icontains=search)
                | Q(tracking_code__icontains=search)
            )

        # ==========================
        # FILTERS
        # ==========================
        action_type = self.request.GET.get("action_type")
        if action_type:
            qs = qs.filter(action_type=action_type)

        level = self.request.GET.get("level")
        if level:
            qs = qs.filter(level=level)

        success = self.request.GET.get("success")
        if success is not None:
            if success.lower() == "true":
                qs = qs.filter(success=True)
            elif success.lower() == "false":
                qs = qs.filter(success=False)

        method = self.request.GET.get("method")
        if method:
            qs = qs.filter(method=method.upper())

        status = self.request.GET.get("status")
        if status:
            qs = qs.filter(response_status=status)

        user = self.request.GET.get("user")
        if user:
            qs = qs.filter(user_id=user)

        admin = self.request.GET.get("admin")
        if admin:
            qs = qs.filter(admin_id=admin)

        start = self.request.GET.get("start_date")
        if start:
            qs = qs.filter(created_at__date__gte=start)

        end = self.request.GET.get("end_date")
        if end:
            qs = qs.filter(created_at__date__lte=end)

        return qs

    # =============================================
    # LIST با Pagination دستی
    # =============================================
    def list(self, request):
        queryset = self.filter_queryset(self.get_queryset())
        
        # =============================================
        # دریافت پارامترهای Pagination
        # =============================================
        try:
            page = int(request.GET.get("page", 1))
        except ValueError:
            page = 1
        
        try:
            page_size = int(request.GET.get("page_size", 10))
        except ValueError:
            page_size = 10
        
        # محدود کردن page_size به مقادیر مجاز
        allowed_page_sizes = [10, 25, 50, 100]
        if page_size not in allowed_page_sizes:
            page_size = 10
        
        # =============================================
        # محاسبه Offset و Limit
        # =============================================
        total_results = queryset.count()
        offset = (page - 1) * page_size
        total_pages = (total_results + page_size - 1) // page_size if page_size > 0 else 0
        
        # =============================================
        # گرفتن داده‌های صفحه مورد نظر
        # =============================================
        paginated_queryset = queryset[offset:offset + page_size]
        
        # =============================================
        # سریالایز کردن
        # =============================================
        serializer = self.get_serializer(paginated_queryset, many=True)
        
        # =============================================
        # ساخت پاسخ با متا
        # =============================================
        response_data = {
            "total_results": total_results,
            "total_pages": total_pages,
            "current_page": page,
            "page_size": page_size,
            "next": None,
            "previous": None,
            "results": serializer.data
        }
        
        # =============================================
        # ساخت لینک‌های next و previous
        # =============================================
        base_url = request.build_absolute_uri(request.path)
        query_params = request.GET.copy()
        
        # Next
        if page < total_pages:
            query_params['page'] = page + 1
            query_params['page_size'] = page_size
            response_data['next'] = f"{base_url}?{query_params.urlencode()}"
        
        # Previous
        if page > 1:
            query_params['page'] = page - 1
            query_params['page_size'] = page_size
            response_data['previous'] = f"{base_url}?{query_params.urlencode()}"
        
        return success_response(
            "لیست لاگ ها",
            response_data
        )

    # =============================================
    # RETRIEVE
    # =============================================
    def retrieve(self, request, pk=None):
        obj = self.get_object()
        serializer = self.get_serializer(obj)
        return success_response("جزئیات لاگ", serializer.data)

    # =============================================
    # CLEAR - حذف همه لاگ‌ها
    # =============================================
    @action(detail=False, methods=["delete"], permission_classes=[IsAdminRole])
    def clear(self, request):
        deleted = AdminLog.objects.all().delete()
        return success_response(
            "تمام لاگ‌ها حذف شدند.", 
            {"deleted": deleted[0]}
        )
class AdminLogViewSet(AdminBaseViewSet):
    """
    مدیریت لاگ‌های سیستم برای ادمین با Pagination دستی
    """

    permission_classes = [IsAdminRole]
    queryset = AdminLog.objects.all()
    serializer_class = AdminLogListSerializer
    ordering = ["-created_at"]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return AdminLogDetailSerializer
        return AdminLogListSerializer

    def get_queryset(self):
        qs = super().get_queryset()

        # ==========================
        # SEARCH
        # ==========================
        search = self.request.GET.get("search")
        if search:
            qs = qs.filter(
                Q(action__icontains=search)
                | Q(description__icontains=search)
                | Q(user__mobile__icontains=search)
                | Q(admin__mobile__icontains=search)
                | Q(ip_address__icontains=search)
                | Q(endpoint__icontains=search)
                | Q(tracking_code__icontains=search)
            )

        # ==========================
        # FILTERS
        # ==========================
        action_type = self.request.GET.get("action_type")
        if action_type:
            qs = qs.filter(action_type=action_type)

        level = self.request.GET.get("level")
        if level:
            qs = qs.filter(level=level)

        success = self.request.GET.get("success")
        if success is not None:
            if success.lower() == "true":
                qs = qs.filter(success=True)
            elif success.lower() == "false":
                qs = qs.filter(success=False)

        method = self.request.GET.get("method")
        if method:
            qs = qs.filter(method=method.upper())

        status = self.request.GET.get("status")
        if status:
            qs = qs.filter(response_status=status)

        user = self.request.GET.get("user")
        if user:
            qs = qs.filter(user_id=user)

        admin = self.request.GET.get("admin")
        if admin:
            qs = qs.filter(admin_id=admin)

        start = self.request.GET.get("start_date")
        if start:
            qs = qs.filter(created_at__date__gte=start)

        end = self.request.GET.get("end_date")
        if end:
            qs = qs.filter(created_at__date__lte=end)

        return qs

    # =============================================
    # LIST با Pagination دستی
    # =============================================
    def list(self, request):
        queryset = self.filter_queryset(self.get_queryset())
        
        # =============================================
        # دریافت پارامترهای Pagination
        # =============================================
        try:
            page = int(request.GET.get("page", 1))
        except ValueError:
            page = 1
        
        try:
            page_size = int(request.GET.get("page_size", 10))
        except ValueError:
            page_size = 10
        
        # محدود کردن page_size به مقادیر مجاز
        allowed_page_sizes = [10, 25, 50, 100]
        if page_size not in allowed_page_sizes:
            page_size = 10
        
        # =============================================
        # محاسبه Offset و Limit
        # =============================================
        total_results = queryset.count()
        offset = (page - 1) * page_size
        total_pages = (total_results + page_size - 1) // page_size if page_size > 0 else 0
        
        # =============================================
        # گرفتن داده‌های صفحه مورد نظر
        # =============================================
        paginated_queryset = queryset[offset:offset + page_size]
        
        # =============================================
        # سریالایز کردن
        # =============================================
        serializer = self.get_serializer(paginated_queryset, many=True)
        
        # =============================================
        # ساخت پاسخ با متا
        # =============================================
        response_data = {
            "total_results": total_results,
            "total_pages": total_pages,
            "current_page": page,
            "page_size": page_size,
            "next": None,
            "previous": None,
            "results": serializer.data
        }
        
        # =============================================
        # ساخت لینک‌های next و previous
        # =============================================
        base_url = request.build_absolute_uri(request.path)
        query_params = request.GET.copy()
        
        # Next
        if page < total_pages:
            query_params['page'] = page + 1
            query_params['page_size'] = page_size
            response_data['next'] = f"{base_url}?{query_params.urlencode()}"
        
        # Previous
        if page > 1:
            query_params['page'] = page - 1
            query_params['page_size'] = page_size
            response_data['previous'] = f"{base_url}?{query_params.urlencode()}"
        
        return success_response(
            "لیست لاگ ها",
            response_data
        )

    # =============================================
    # RETRIEVE
    # =============================================
    def retrieve(self, request, pk=None):
        obj = self.get_object()
        serializer = self.get_serializer(obj)
        return success_response("جزئیات لاگ", serializer.data)

    # =============================================
    # CLEAR - حذف همه لاگ‌ها
    # =============================================
    @action(detail=False, methods=["delete"], permission_classes=[IsAdminRole])
    def clear(self, request):
        deleted = AdminLog.objects.all().delete()
        return success_response(
            "تمام لاگ‌ها حذف شدند.", 
            {"deleted": deleted[0]}
        )

class AnalyticsChartAPIView(APIView):

    permission_classes = [IsAdminRole]

    def get(self, request):

        year = request.GET.get("year")
        month = request.GET.get("month")

        if not year:

            return error_response("سال الزامی است.")

        try:

            year = int(year)

        except ValueError:

            return error_response("سال نامعتبر است.")

        # =====================================
        # YEARLY CHART
        # =====================================

        if not month:

            month_names = [
                "فروردین",
                "اردیبهشت",
                "خرداد",
                "تیر",
                "مرداد",
                "شهریور",
                "مهر",
                "آبان",
                "آذر",
                "دی",
                "بهمن",
                "اسفند",
            ]

            result = []

            for m in range(1, 13):

                start_date = jdatetime.date(year, m, 1).togregorian()

                if m == 12:

                    end_date = jdatetime.date(year + 1, 1, 1).togregorian()

                else:

                    end_date = jdatetime.date(year, m + 1, 1).togregorian()

                gold_sales = (
                    GoldTransaction.objects.filter(
                        type="BUY",
                        created_at__date__gte=start_date,
                        created_at__date__lt=end_date,
                    ).aggregate(total=Sum("total_amount"))["total"]
                    or 0
                )

                silver_sales = (
                    SilverTransaction.objects.filter(
                        type="BUY",
                        created_at__date__gte=start_date,
                        created_at__date__lt=end_date,
                    ).aggregate(total=Sum("total_amount"))["total"]
                    or 0
                )

                result.append(
                    {
                        "month": month_names[m - 1],
                        "sales": float(gold_sales + silver_sales),
                    }
                )

            return success_response("نمودار فروش سالانه", result)

        # =====================================
        # MONTHLY CHART
        # =====================================

        try:

            month = int(month)

        except ValueError:

            return error_response("ماه نامعتبر است.")

        if month < 1 or month > 12:

            return error_response("ماه باید بین ۱ تا ۱۲ باشد.")

        result = []

        for day in range(1, 32):

            try:

                current_date = jdatetime.date(year, month, day).togregorian()

            except ValueError:
                break

            gold_sales = (
                GoldTransaction.objects.filter(
                    type="BUY", created_at__date=current_date
                ).aggregate(total=Sum("total_amount"))["total"]
                or 0
            )

            silver_sales = (
                SilverTransaction.objects.filter(
                    type="BUY", created_at__date=current_date
                ).aggregate(total=Sum("total_amount"))["total"]
                or 0
            )

            result.append({"day": day, "sales": float(gold_sales + silver_sales)})

        return success_response("نمودار فروش ماهانه", result)


class AnalyticsPurchaseChartAPIView(APIView):

    permission_classes = [IsAdminRole]

    def get(self, request):

        year = request.GET.get("year")
        month = request.GET.get("month")

        if not year:
            return error_response("سال الزامی است.")

        try:
            year = int(year)

        except ValueError:
            return error_response("سال نامعتبر است.")

        # =====================================
        # YEARLY CHART
        # =====================================

        if not month:

            month_names = [
                "فروردین",
                "اردیبهشت",
                "خرداد",
                "تیر",
                "مرداد",
                "شهریور",
                "مهر",
                "آبان",
                "آذر",
                "دی",
                "بهمن",
                "اسفند",
            ]

            result = []

            for m in range(1, 13):

                start_date = jdatetime.date(year, m, 1).togregorian()

                if m == 12:

                    end_date = jdatetime.date(year + 1, 1, 1).togregorian()

                else:

                    end_date = jdatetime.date(year, m + 1, 1).togregorian()

                gold_purchase = (
                    GoldTransaction.objects.filter(
                        type="SELL",
                        created_at__date__gte=start_date,
                        created_at__date__lt=end_date,
                    ).aggregate(total=Sum("total_amount"))["total"]
                    or 0
                )

                silver_purchase = (
                    SilverTransaction.objects.filter(
                        type="SELL",
                        created_at__date__gte=start_date,
                        created_at__date__lt=end_date,
                    ).aggregate(total=Sum("total_amount"))["total"]
                    or 0
                )

                result.append(
                    {
                        "month": month_names[m - 1],
                        "purchase": float(gold_purchase + silver_purchase),
                    }
                )

            return success_response("نمودار خرید سالانه", result)

        # =====================================
        # MONTHLY CHART
        # =====================================

        try:
            month = int(month)

        except ValueError:
            return error_response("ماه نامعتبر است.")

        if month < 1 or month > 12:

            return error_response("ماه باید بین ۱ تا ۱۲ باشد.")

        result = []

        for day in range(1, 32):

            try:

                current_date = jdatetime.date(year, month, day).togregorian()

            except ValueError:
                break

            gold_purchase = (
                GoldTransaction.objects.filter(
                    type="SELL", created_at__date=current_date
                ).aggregate(total=Sum("total_amount"))["total"]
                or 0
            )

            silver_purchase = (
                SilverTransaction.objects.filter(
                    type="SELL", created_at__date=current_date
                ).aggregate(total=Sum("total_amount"))["total"]
                or 0
            )

            result.append(
                {"day": day, "purchase": float(gold_purchase + silver_purchase)}
            )

        return success_response("نمودار خرید ماهانه", result)


# =========================================================
# GOLD BANNERS
# =========================================================


class GoldBannerAdminViewSet(AdminBaseViewSet):

    queryset = GoldBanner.objects.all().order_by("-id")
    serializer_class = GoldBannerSerializer

    parser_classes = (
        MultiPartParser,
        FormParser,
    )

    def get_serializer_context(self):
        return {"request": self.request}

    def get_queryset(self):

        qs = super().get_queryset()

        search = self.request.GET.get("search")
        is_active = self.request.GET.get("is_active")
        ordering = self.request.GET.get("ordering")

        if search:
            qs = qs.filter(title__icontains=search)

        if is_active is not None:
            qs = qs.filter(is_active=is_active.lower() == "true")

        allowed_ordering = [
            "id",
            "-id",
            "title",
            "-title",
            "created_at",
            "-created_at",
        ]

        if ordering in allowed_ordering:
            qs = qs.order_by(ordering)

        return qs

    # ======================
    # LIST
    # ======================

    def list(self, request):

        qs = self.get_queryset()

        serializer = self.serializer_class(
            qs, many=True, context=self.get_serializer_context()
        )

        return success_response(
            "لیست بنرهای طلا", {"total_results": qs.count(), "results": serializer.data}
        )

    # ======================
    # RETRIEVE
    # ======================

    def retrieve(self, request, pk=None):

        obj = self.get_object()

        return success_response(
            "جزئیات بنر",
            self.serializer_class(obj, context=self.get_serializer_context()).data,
        )

    # ======================
    # CREATE
    # ======================

    def create(self, request):

        serializer = self.serializer_class(
            data=request.data, context=self.get_serializer_context()
        )

        if not serializer.is_valid():

            first_error = next(iter(serializer.errors.values()))[0]

            return error_response(str(first_error))

        obj = serializer.save()

        return success_response(
            "بنر ایجاد شد",
            self.serializer_class(obj, context=self.get_serializer_context()).data,
        )

    # ======================
    # UPDATE
    # ======================

    def update(self, request, *args, **kwargs):

        partial = kwargs.pop("partial", False)

        obj = self.get_object()

        serializer = self.serializer_class(
            obj,
            data=request.data,
            partial=partial,
            context=self.get_serializer_context(),
        )

        if not serializer.is_valid():

            first_error = next(iter(serializer.errors.values()))[0]

            return error_response(str(first_error))

        obj = serializer.save()

        obj.refresh_from_db()

        return success_response(
            "بنر ویرایش شد",
            self.serializer_class(obj, context=self.get_serializer_context()).data,
        )

    # ======================
    # PATCH
    # ======================

    def partial_update(self, request, *args, **kwargs):

        kwargs["partial"] = True

        return self.update(request, *args, **kwargs)

    # ======================
    # DELETE
    # ======================

    def destroy(self, request, *args, **kwargs):

        obj = self.get_object()

        obj.delete()

        return success_response("بنر حذف شد")

    # ======================
    # TOGGLE ACTIVE
    # ======================

    @action(detail=True, methods=["post"])
    def toggle_active(self, request, pk=None):

        obj = self.get_object()

        obj.is_active = not obj.is_active

        obj.save()

        return success_response("وضعیت تغییر کرد", {"is_active": obj.is_active})


# =========================================================
# SILVER BANNERS
# =========================================================


class SilverBannerAdminViewSet(AdminBaseViewSet):

    queryset = SilverBanner.objects.all().order_by("-id")
    serializer_class = SilverBannerSerializer

    parser_classes = (
        MultiPartParser,
        FormParser,
    )

    def get_serializer_context(self):
        return {"request": self.request}

    def get_queryset(self):

        qs = super().get_queryset()

        search = self.request.GET.get("search")
        is_active = self.request.GET.get("is_active")
        ordering = self.request.GET.get("ordering")

        if search:
            qs = qs.filter(title__icontains=search)

        if is_active is not None:
            qs = qs.filter(is_active=is_active.lower() == "true")

        allowed_ordering = [
            "id",
            "-id",
            "title",
            "-title",
            "created_at",
            "-created_at",
        ]

        if ordering in allowed_ordering:
            qs = qs.order_by(ordering)

        return qs

    # ======================
    # LIST
    # ======================

    def list(self, request):

        qs = self.get_queryset()

        serializer = self.serializer_class(
            qs, many=True, context=self.get_serializer_context()
        )

        return success_response(
            "لیست بنرهای نقره",
            {"total_results": qs.count(), "results": serializer.data},
        )

    # ======================
    # RETRIEVE
    # ======================

    def retrieve(self, request, pk=None):

        obj = self.get_object()

        return success_response(
            "جزئیات بنر",
            self.serializer_class(obj, context=self.get_serializer_context()).data,
        )

    # ======================
    # CREATE
    # ======================

    def create(self, request):

        serializer = self.serializer_class(
            data=request.data, context=self.get_serializer_context()
        )

        if not serializer.is_valid():

            first_error = next(iter(serializer.errors.values()))[0]

            return error_response(str(first_error))

        obj = serializer.save()

        return success_response(
            "بنر ایجاد شد",
            self.serializer_class(obj, context=self.get_serializer_context()).data,
        )

    # ======================
    # UPDATE
    # ======================

    def update(self, request, *args, **kwargs):

        partial = kwargs.pop("partial", False)

        obj = self.get_object()

        serializer = self.serializer_class(
            obj,
            data=request.data,
            partial=partial,
            context=self.get_serializer_context(),
        )

        if not serializer.is_valid():

            first_error = next(iter(serializer.errors.values()))[0]

            return error_response(str(first_error))

        obj = serializer.save()

        obj.refresh_from_db()

        return success_response(
            "بنر ویرایش شد",
            self.serializer_class(obj, context=self.get_serializer_context()).data,
        )

    # ======================
    # PATCH
    # ======================

    def partial_update(self, request, *args, **kwargs):

        kwargs["partial"] = True

        return self.update(request, *args, **kwargs)

    # ======================
    # DELETE
    # ======================

    def destroy(self, request, *args, **kwargs):

        obj = self.get_object()

        obj.delete()

        return success_response("بنر حذف شد")

    # ======================
    # TOGGLE ACTIVE
    # ======================

    @action(detail=True, methods=["post"])
    def toggle_active(self, request, pk=None):

        obj = self.get_object()

        obj.is_active = not obj.is_active

        obj.save()

        return success_response("وضعیت تغییر کرد", {"is_active": obj.is_active})


class SilverBankAdminViewSet(AdminBaseViewSet):

    queryset = SilverBankInfo.objects.all().order_by("-id")
    serializer_class = SilverBankInfoSerializer
    create_update_serializer_class = SilverBankInfoCreateUpdateSerializer

    def get_queryset(self):
        qs = super().get_queryset()

        search = self.request.GET.get("search")
        card_number = self.request.GET.get("card_number")
        iban = self.request.GET.get("iban")
        ordering = self.request.GET.get("ordering")

        if search:
            qs = qs.filter(full_name__icontains=search)

        if card_number:
            qs = qs.filter(card_number__icontains=card_number)

        if iban:
            qs = qs.filter(sheba__icontains=iban)

        allowed_ordering = [
            "id",
            "-id",
            "created_at",
            "-created_at",
            "full_name",
            "-full_name",
            "card_number",
            "-card_number",
            "sheba",
            "-sheba",
            "is_active",
            "-is_active",
        ]

        if ordering in allowed_ordering:
            qs = qs.order_by(ordering)

        return qs

    queryset = SilverBankInfo.objects.all().order_by("-id")

    serializer_class = SilverBankInfoSerializer

    create_update_serializer_class = SilverBankInfoCreateUpdateSerializer

    # ======================
    # LIST
    # ======================
    def list(self, request):

        qs = self.get_queryset()

        return success_response(
            "لیست کارت‌های نقره",
            {
                "total_results": qs.count(),
                "results": self.serializer_class(qs, many=True).data,
            },
        )

    # ======================
    # RETRIEVE
    # ======================
    def retrieve(self, request, pk=None):

        obj = self.get_object()

        return success_response("جزئیات کارت نقره", self.serializer_class(obj).data)

    # ======================
    # CREATE
    # ======================
    def create(self, request):

        serializer = self.create_update_serializer_class(data=request.data)

        serializer.is_valid(raise_exception=True)

        obj = serializer.save()

        return success_response("کارت نقره ساخته شد", self.serializer_class(obj).data)

    # ======================
    # UPDATE
    # ======================
    def update(self, request, *args, **kwargs):

        partial = kwargs.pop("partial", False)

        obj = self.get_object()

        serializer = self.create_update_serializer_class(
            obj, data=request.data, partial=partial
        )

        serializer.is_valid(raise_exception=True)

        obj = serializer.save()

        obj.refresh_from_db()

        return success_response("کارت نقره ویرایش شد", self.serializer_class(obj).data)

    def partial_update(self, request, *args, **kwargs):

        kwargs["partial"] = True

        return self.update(request, *args, **kwargs)

    # ======================
    # TOGGLE
    # ======================
    @action(detail=True, methods=["post"])
    def toggle(self, request, pk=None):

        bank = self.get_object()

        SilverBankInfo.objects.exclude(pk=bank.pk).update(is_active=False)

        bank.is_active = True
        bank.save()

        return success_response("کارت نقره فعال شد", {"is_active": True})


# =========================================================
# GOLD ANNOUNCEMENTS
# =========================================================


class GoldAnnouncementAdminViewSet(AdminBaseViewSet):

    queryset = GoldAnnouncement.objects.all().order_by("-id")

    def get_queryset(self):

        qs = super().get_queryset()

        search = self.request.GET.get("search")
        ordering = self.request.GET.get("ordering")

        if search:
            qs = qs.filter(
                Q(title__icontains=search) | Q(description__icontains=search)
            )

        allowed_ordering = [
            "id",
            "-id",
            "created_at",
            "-created_at",
            "title",
            "-title",
        ]

        if ordering in allowed_ordering:
            qs = qs.order_by(ordering)

        return qs

    # ======================
    # LIST
    # ======================

    def list(self, request):

        announcements = self.get_queryset()

        results = []

        for item in announcements:
            results.append(GoldAnnouncementSerializer(item).data)

        return success_response(
            "لیست اطلاعیه‌های طلا", {"total_results": len(results), "results": results}
        )

    # ======================
    # RETRIEVE
    # ======================

    def retrieve(self, request, pk=None):

        obj = get_object_or_404(GoldAnnouncement, pk=pk)

        return success_response("جزئیات اطلاعیه", GoldAnnouncementSerializer(obj).data)

    # ======================
    # CREATE
    # ======================

    def create(self, request):

        serializer = GoldAnnouncementSerializer(data=request.data)

        serializer.is_valid(raise_exception=True)

        obj = serializer.save()

        return success_response(
            "اطلاعیه ایجاد شد", GoldAnnouncementSerializer(obj).data
        )

    # ======================
    # UPDATE
    # ======================

    def update(self, request, pk=None, *args, **kwargs):

        obj = get_object_or_404(GoldAnnouncement, pk=pk)

        serializer = GoldAnnouncementSerializer(obj, data=request.data, partial=True)

        serializer.is_valid(raise_exception=True)

        serializer.save()

        obj.refresh_from_db()

        return success_response(
            "اطلاعیه ویرایش شد", {"results": GoldAnnouncementSerializer(obj).data}
        )

    # ======================
    # DELETE
    # ======================

    def destroy(self, request, pk=None):

        obj = get_object_or_404(GoldAnnouncement, pk=pk)

        obj.delete()

        return success_response("اطلاعیه حذف شد")


# =========================================================
# SILVER ANNOUNCEMENTS
# =========================================================


class SilverAnnouncementAdminViewSet(AdminBaseViewSet):

    queryset = SilverAnnouncement.objects.all().order_by("-id")

    def get_queryset(self):

        qs = super().get_queryset()

        search = self.request.GET.get("search")
        ordering = self.request.GET.get("ordering")

        if search:
            qs = qs.filter(
                Q(title__icontains=search) | Q(description__icontains=search)
            )

        allowed_ordering = [
            "id",
            "-id",
            "created_at",
            "-created_at",
            "title",
            "-title",
        ]

        if ordering in allowed_ordering:
            qs = qs.order_by(ordering)

        return qs

    # ======================
    # LIST
    # ======================

    def list(self, request):

        announcements = self.get_queryset()

        results = []

        for item in announcements:
            results.append(SilverAnnouncementSerializer(item).data)

        return success_response(
            "لیست اطلاعیه‌های نقره", {"total_results": len(results), "results": results}
        )

    # ======================
    # RETRIEVE
    # ======================

    def retrieve(self, request, pk=None):

        obj = get_object_or_404(SilverAnnouncement, pk=pk)

        return success_response(
            "جزئیات اطلاعیه", SilverAnnouncementSerializer(obj).data
        )

    # ======================
    # CREATE
    # ======================

    def create(self, request):

        serializer = SilverAnnouncementSerializer(data=request.data)

        serializer.is_valid(raise_exception=True)

        obj = serializer.save()

        return success_response(
            "اطلاعیه ایجاد شد", SilverAnnouncementSerializer(obj).data
        )

    # ======================
    # UPDATE
    # ======================

    def update(self, request, pk=None, *args, **kwargs):

        obj = get_object_or_404(SilverAnnouncement, pk=pk)

        serializer = SilverAnnouncementSerializer(obj, data=request.data, partial=True)

        serializer.is_valid(raise_exception=True)

        serializer.save()

        obj.refresh_from_db()

        return success_response(
            "اطلاعیه ویرایش شد", {"results": SilverAnnouncementSerializer(obj).data}
        )

    # ======================
    # DELETE
    # ======================

    def destroy(self, request, pk=None):

        obj = get_object_or_404(SilverAnnouncement, pk=pk)

        obj.delete()

        return success_response("اطلاعیه حذف شد")


from rest_framework.views import APIView

# =========================================================
# BUY SELL ANALYTICS CHART
# =========================================================


class BuySellChartAPIView(APIView):

    permission_classes = [IsAdminRole]

    def get(self, request):

        year = request.GET.get("year")
        month = request.GET.get("month")

        if not year:

            return error_response("سال الزامی است.")

        try:

            year = int(year)

        except ValueError:

            return error_response("سال نامعتبر است.")

        # =====================================
        # YEARLY
        # =====================================

        if not month:

            months = [
                "فروردین",
                "اردیبهشت",
                "خرداد",
                "تیر",
                "مرداد",
                "شهریور",
                "مهر",
                "آبان",
                "آذر",
                "دی",
                "بهمن",
                "اسفند",
            ]

            result = []

            for m in range(1, 13):

                start = jdatetime.date(year, m, 1).togregorian()

                if m == 12:

                    end = jdatetime.date(year + 1, 1, 1).togregorian()

                else:

                    end = jdatetime.date(year, m + 1, 1).togregorian()

                # BUY = خرید کاربر از سیستم
                gold_buy = (
                    GoldTransaction.objects.filter(
                        type="BUY",
                        created_at__date__gte=start,
                        created_at__date__lt=end,
                    ).aggregate(total=Sum("total_amount"))["total"]
                    or 0
                )

                silver_buy = (
                    SilverTransaction.objects.filter(
                        type="BUY",
                        created_at__date__gte=start,
                        created_at__date__lt=end,
                    ).aggregate(total=Sum("total_amount"))["total"]
                    or 0
                )

                # SELL = فروش کاربر به سیستم
                gold_sell = (
                    GoldTransaction.objects.filter(
                        type="SELL",
                        created_at__date__gte=start,
                        created_at__date__lt=end,
                    ).aggregate(total=Sum("total_amount"))["total"]
                    or 0
                )

                silver_sell = (
                    SilverTransaction.objects.filter(
                        type="SELL",
                        created_at__date__gte=start,
                        created_at__date__lt=end,
                    ).aggregate(total=Sum("total_amount"))["total"]
                    or 0
                )

                result.append(
                    {
                        "month": months[m - 1],
                        "buy": float(gold_buy + silver_buy),
                        "sell": float(gold_sell + silver_sell),
                    }
                )

            return success_response("نمودار خرید و فروش ماهانه", result)

        # =====================================
        # DAILY
        # =====================================

        try:

            month = int(month)

        except ValueError:

            return error_response("ماه نامعتبر است.")

        if month < 1 or month > 12:

            return error_response("ماه نامعتبر است.")

        result = []

        for day in range(1, 32):

            try:

                date = jdatetime.date(year, month, day).togregorian()

            except ValueError:

                break

            gold_buy = (
                GoldTransaction.objects.filter(
                    type="BUY", created_at__date=date
                ).aggregate(total=Sum("total_amount"))["total"]
                or 0
            )

            silver_buy = (
                SilverTransaction.objects.filter(
                    type="BUY", created_at__date=date
                ).aggregate(total=Sum("total_amount"))["total"]
                or 0
            )

            gold_sell = (
                GoldTransaction.objects.filter(
                    type="SELL", created_at__date=date
                ).aggregate(total=Sum("total_amount"))["total"]
                or 0
            )

            silver_sell = (
                SilverTransaction.objects.filter(
                    type="SELL", created_at__date=date
                ).aggregate(total=Sum("total_amount"))["total"]
                or 0
            )

            result.append(
                {
                    "day": day,
                    "buy": float(gold_buy + silver_buy),
                    "sell": float(gold_sell + silver_sell),
                }
            )

        return success_response("نمودار خرید و فروش روزانه", result)


# # =========================================================
# # SILVER DEPOSIT
# # =========================================================

# class SilverDepositAdminViewSet(AdminBaseViewSet):

#     queryset = SilverFinancialTransaction.objects.filter(
#         type="DEPOSIT"
#     ).order_by("-id")

#     serializer_class = SilverFinancialTransactionSerializer

#     parser_classes = (
#         JSONParser,
#         MultiPartParser,
#         FormParser
#     )

#     def get_queryset(self):

#         qs = super().get_queryset()

#         search = self.request.GET.get("search")
#         status = self.request.GET.get("status")
#         tracking_code = self.request.GET.get("tracking_code")
#         user_id = self.request.GET.get("user_id")
#         method = self.request.GET.get("method")
#         start_date = self.request.GET.get("start_date")
#         end_date = self.request.GET.get("end_date")
#         ordering = self.request.GET.get("ordering")

#         if search:
#             qs = qs.filter(
#                 user__mobile__icontains=search
#             )

#         if status:
#             qs = qs.filter(
#                 status=status
#             )

#         if user_id:
#             qs = qs.filter(
#                 user_id=user_id
#             )

#         if method:
#             qs = qs.filter(
#                 method=method
#             )

#         if tracking_code:
#             qs = qs.filter(
#                 tracking_code__icontains=tracking_code
#             )

#         if start_date:
#             qs = qs.filter(
#                 created_at__date__gte=start_date
#             )

#         if end_date:
#             qs = qs.filter(
#                 created_at__date__lte=end_date
#             )

#         allowed_ordering = [

#             "id",
#             "-id",

#             "amount",
#             "-amount",

#             "status",
#             "-status",

#             "created_at",
#             "-created_at",

#             "updated_at",
#             "-updated_at"

#         ]

#         if ordering in allowed_ordering:
#             qs = qs.order_by(ordering)

#         return qs


#     def list(self, request):

#         qs = self.get_queryset()

#         serializer = SilverFinancialTransactionSerializer(
#             qs,
#             many=True,
#             context={
#                 "request": request
#             }
#         )

#         return success_response(

#             "لیست واریزهای نقره",

#             {

#                 "total_results": qs.count(),

#                 "results": serializer.data

#             }

#         )


#     def retrieve(self, request, pk=None):

#         obj = self.get_object()

#         serializer = SilverFinancialTransactionSerializer(
#             obj,
#             context={
#                 "request": request
#             }
#         )

#         return success_response(

#             "جزئیات واریز نقره",

#             serializer.data

#         )


#     @transaction.atomic
#     def partial_update(self, request, *args, **kwargs):

#         obj = self.get_object()

#         serializer = StatusUpdateSerializer(
#             data=request.data,
#             partial=True
#         )

#         serializer.is_valid(
#             raise_exception=True
#         )

#         new_status = serializer.validated_data.get(
#             "status"
#         )

#         admin_note = serializer.validated_data.get(
#             "admin_note",
#             ""
#         )

#         previous_status = obj.status

#         wallet, _ = SilverWallet.objects.get_or_create(
#             user=obj.user
#         )

#         # =====================================
#         # تایید واریز
#         # =====================================

#         if (
#             previous_status != "COMPLETED"
#             and
#             new_status == "COMPLETED"
#         ):

#             wallet.balance += obj.amount

#             wallet.save(
#                 update_fields=[
#                     "balance",
#                     "updated_at"
#                 ]
#             )

#         # =====================================
#         # ذخیره وضعیت
#         # =====================================

#         if new_status:
#             obj.status = new_status

#         if admin_note:
#             obj.admin_note = admin_note

#         obj.save()

#         # =====================================
#         # ارسال پیامک
#         # =====================================

#         sms_sent = None

#         if admin_note:

#             sms_sent = send_admin_note_sms(

#                 mobile=obj.user.mobile,

#                 note=admin_note

#             )

#         status_text = STATUS_FA.get(
#             new_status,
#             new_status
#         ) if new_status else "ویرایش شده"

#         message = f"وضعیت واریز نقره به {status_text} تغییر کرد"

#         if sms_sent is False:
#             message += " (ارسال پیامک ناموفق بود)"

#         # =====================================
#         # ثبت لاگ ادمین
#         # =====================================

#         create_admin_log(

#             request=request,

#             admin=request.user,

#             user=obj.user,

#             action_type="SILVER_DEPOSIT_UPDATE",

#             action="تغییر وضعیت واریز نقره",

#             model_name="SilverFinancialTransaction",

#             object_id=obj.id,

#             tracking_code=obj.tracking_code,

#             response_status=200,

#             description=f"""

# کد پیگیری:
# {obj.tracking_code}

# وضعیت قبلی:
# {previous_status}

# وضعیت جدید:
# {obj.status}

# مبلغ:
# {obj.amount:,}

# موجودی کیف پول:
# {wallet.balance:,}

# """

#         )

#         return success_response(

#             message,

#             {

#                 "transaction": SilverFinancialTransactionSerializer(
#                     obj
#                 ).data,

#                 "wallet": {

#                     "balance": wallet.balance,

#                     "blocked_balance": wallet.blocked_balance

#                 },

#                 "sms_sent": sms_sent

#             }

#         )


# # =========================================================
# # SILVER WITHDRAW (ADMIN)
# # =========================================================

# class SilverWithdrawAdminViewSet(AdminBaseViewSet):

#     queryset = SilverFinancialTransaction.objects.filter(type="WITHDRAW").order_by("-id")
#     serializer_class = SilverFinancialTransactionSerializer
#     parser_classes = (JSONParser, MultiPartParser, FormParser)

#     def get_queryset(self):
#         qs = super().get_queryset()
#         search = self.request.GET.get("search")
#         status = self.request.GET.get("status")
#         tracking_code = self.request.GET.get("tracking_code")
#         user_id = self.request.GET.get("user_id")
#         method = self.request.GET.get("method")
#         start_date = self.request.GET.get("start_date")
#         end_date = self.request.GET.get("end_date")
#         ordering = self.request.GET.get("ordering")

#         if search:
#             qs = qs.filter(user__mobile__icontains=search)
#         if status:
#             qs = qs.filter(status=status)
#         if user_id:
#             qs = qs.filter(user_id=user_id)
#         if method:
#             qs = qs.filter(method=method)
#         if tracking_code:
#             qs = qs.filter(tracking_code__icontains=tracking_code)
#         if start_date:
#             qs = qs.filter(created_at__date__gte=start_date)
#         if end_date:
#             qs = qs.filter(created_at__date__lte=end_date)

#         allowed_ordering = ["id", "-id", "amount", "-amount", "status", "-status", "created_at", "-created_at", "updated_at", "-updated_at"]
#         if ordering in allowed_ordering:
#             qs = qs.order_by(ordering)

#         return qs

#     def list(self, request):
#         qs = self.get_queryset()
#         ser = SilverFinancialTransactionSerializer(qs, many=True, context={"request": request})
#         return success_response("لیست برداشت‌های نقره", {"total_results": qs.count(), "results": ser.data})

#     def retrieve(self, request, pk=None):
#         obj = self.get_object()
#         return success_response("جزئیات برداشت نقره", SilverFinancialTransactionSerializer(obj, context={"request": request}).data)

#     @transaction.atomic
#     def partial_update(self, request, *args, **kwargs):
#         obj = self.get_object()

#         ser = StatusUpdateSerializer(data=request.data, partial=True)
#         ser.is_valid(raise_exception=True)

#         new_status = ser.validated_data.get("status")
#         admin_note = ser.validated_data.get("admin_note", "")

#         # =========================================================
#         # اعمال روی موجودی کیف‌پول
#         # فقط برای برداشت بانکی و فقط وقتی هنوز PENDING است
#         # (برداشت GOLD همان لحظه COMPLETED می‌شود و بلوکه ندارد)
#         # =========================================================

#         if new_status and obj.method == "BANK" and obj.status == "PENDING":

#             wallet = SilverWallet.objects.select_for_update().get(
#                 user=obj.user
#             )

#             if new_status == "COMPLETED":

#                 # -----------------------------------------
#                 # تایید شد: پول واقعاً از سیستم خارج شده
#                 # فقط از blocked_toman کسر می‌شود
#                 # -----------------------------------------

#                 wallet.blocked_toman -= obj.amount

#                 wallet.save(
#                     update_fields=[
#                         "blocked_toman",
#                     ]
#                 )

#             elif new_status == "FAILED":

#                 # -----------------------------------------
#                 # رد شد: پول به کاربر برمی‌گردد
#                 # از blocked_toman کم و به accessible_toman اضافه می‌شود
#                 # -----------------------------------------

#                 wallet.blocked_toman -= obj.amount
#                 wallet.accessible_toman += obj.amount

#                 wallet.save(
#                     update_fields=[
#                         "blocked_toman",
#                         "accessible_toman",
#                     ]
#                 )

#             create_admin_log(
#                 request=request,
#                 admin=getattr(request.user, "admin_profile", None),
#                 user=obj.user,
#                 action_type="PAYMENT",
#                 action="بروزرسانی وضعیت برداشت بانکی نقره",
#                 model_name="SilverFinancialTransaction",
#                 object_id=obj.id,
#                 tracking_code=obj.tracking_code,
#                 success=True,
#                 description=f"""
# کاربر:
# {obj.user.mobile}

# مبلغ:
# {obj.amount:,}

# وضعیت قبلی:
# PENDING

# وضعیت جدید:
# {new_status}

# موجودی قابل برداشت جدید:
# {wallet.accessible_toman:,}

# موجودی بلوکه جدید:
# {wallet.blocked_toman:,}
# """
#             )

#         if new_status:
#             obj.status = new_status
#         if admin_note:
#             obj.admin_note = admin_note
#         obj.save()

#         sms_sent = None
#         if admin_note:
#             sms_sent = send_admin_note_sms(
#                 mobile=obj.user.mobile,
#                 note=admin_note
#             )

#         status_text = STATUS_FA.get(new_status, new_status) if new_status else "ویرایش شده"
#         msg = f"وضعیت برداشت نقره به {status_text} تغییر کرد"
#         if sms_sent is False:
#             msg += " (ارسال پیامک ناموفق بود)"

#         return success_response(
#             msg,
#             {
#                 "transaction": SilverFinancialTransactionSerializer(obj).data,
#                 "sms_sent": sms_sent,
#             }
#         )


# # =========================================================
# # WITHDRAW (ADMIN) — طلا / کیف‌پول اصلی
# # =========================================================

# class WithdrawAdminViewSet(AdminBaseViewSet):

#     queryset = FinancialTransaction.objects.filter(type="WITHDRAW").order_by("-id")
#     serializer_class = FinancialTransactionSerializer
#     parser_classes = (MultiPartParser, FormParser)

#     def get_queryset(self):
#         qs = super().get_queryset()
#         search = self.request.GET.get("search")
#         status = self.request.GET.get("status")
#         tracking_code = self.request.GET.get("tracking_code")
#         user_id = self.request.GET.get("user_id")
#         method = self.request.GET.get("method")
#         start_date = self.request.GET.get("start_date")
#         end_date = self.request.GET.get("end_date")
#         ordering = self.request.GET.get("ordering")

#         if search:
#             qs = qs.filter(user__mobile__icontains=search)
#         if status:
#             qs = qs.filter(status=status)
#         if user_id:
#             qs = qs.filter(user_id=user_id)
#         if method:
#             qs = qs.filter(method=method)
#         if tracking_code:
#             qs = qs.filter(tracking_code__icontains=tracking_code)
#         if start_date:
#             qs = qs.filter(created_at__date__gte=start_date)
#         if end_date:
#             qs = qs.filter(created_at__date__lte=end_date)

#         allowed_ordering = ["id", "-id", "amount", "-amount", "status", "-status", "created_at", "-created_at", "updated_at", "-updated_at"]
#         if ordering in allowed_ordering:
#             qs = qs.order_by(ordering)

#         return qs

#     def list(self, request):
#         qs = self.get_queryset()
#         ser = FinancialTransactionSerializer(qs, many=True, context={"request": request})
#         return success_response("لیست برداشت‌ها", {"total_results": qs.count(), "results": ser.data})

#     def retrieve(self, request, pk=None):
#         obj = self.get_object()
#         return success_response("جزئیات برداشت", FinancialTransactionSerializer(obj, context={"request": request}).data)

#     @transaction.atomic
#     def partial_update(self, request, *args, **kwargs):
#         obj = self.get_object()

#         ser = StatusUpdateSerializer(data=request.data, partial=True)
#         ser.is_valid(raise_exception=True)

#         new_status = ser.validated_data.get("status")
#         admin_note = ser.validated_data.get("admin_note", "")

#         # =========================================================
#         # اعمال روی موجودی کیف‌پول
#         # فقط برای برداشت بانکی و فقط وقتی هنوز PENDING است
#         # (برداشت SILVER همان لحظه COMPLETED می‌شود و بلوکه ندارد)
#         # =========================================================

#         if new_status and obj.method == "BANK" and obj.status == "PENDING":

#             wallet = Wallet.objects.select_for_update().get(
#                 user=obj.user
#             )

#             if new_status == "COMPLETED":

#                 # -----------------------------------------
#                 # تایید شد: پول واقعاً از سیستم خارج شده
#                 # فقط از blocked_toman کسر می‌شود
#                 # -----------------------------------------

#                 wallet.blocked_toman -= obj.amount

#                 wallet.save(
#                     update_fields=[
#                         "blocked_toman",
#                     ]
#                 )

#             elif new_status == "FAILED":

#                 # -----------------------------------------
#                 # رد شد: پول به کاربر برمی‌گردد
#                 # از blocked_toman کم و به accessible_toman اضافه می‌شود
#                 # -----------------------------------------

#                 wallet.blocked_toman -= obj.amount
#                 wallet.accessible_toman += obj.amount

#                 wallet.save(
#                     update_fields=[
#                         "blocked_toman",
#                         "accessible_toman",
#                     ]
#                 )

#             create_admin_log(
#                 request=request,
#                 admin=getattr(request.user, "admin_profile", None),
#                 user=obj.user,
#                 action_type="WITHDRAW",
#                 action="بروزرسانی وضعیت برداشت بانکی",
#                 model_name="FinancialTransaction",
#                 object_id=obj.id,
#                 tracking_code=obj.tracking_code,
#                 success=True,
#                 description=f"""
# کاربر:
# {obj.user.mobile}

# مبلغ:
# {obj.amount:,}

# وضعیت قبلی:
# PENDING

# وضعیت جدید:
# {new_status}

# موجودی قابل برداشت جدید:
# {wallet.accessible_toman:,}

# موجودی بلوکه جدید:
# {wallet.blocked_toman:,}
# """
#             )

#         if new_status:
#             obj.status = new_status
#         if admin_note:
#             obj.admin_note = admin_note
#         obj.save()

#         sms_sent = None
#         if admin_note:
#             sms_sent = send_admin_note_sms(
#                 mobile=obj.user.mobile,
#                 note=admin_note
#             )

#         status_text = STATUS_FA.get(new_status, new_status) if new_status else "ویرایش شده"
#         msg = f"وضعیت برداشت به {status_text} تغییر کرد"
#         if sms_sent is False:
#             msg += " (ارسال پیامک ناموفق بود)"

#         return success_response(
#             msg,
#             {
#                 "transaction": FinancialTransactionSerializer(obj).data,
#                 "sms_sent": sms_sent,
#             }
#         )


from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser
from django.db import transaction
from .sms_service import send_admin_note_sms

STATUS_FA = {
    "PENDING": "در انتظار",
    "APPROVED": "تایید شده",
    "REJECTED": "رد شده",
    "DONE": "انجام شده",
    "CANCELED": "لغو شده",
    "COMPLETED": "موفق",
    "FAILED": "ناموفق",
}

# =========================================================
# DEPOSIT (MAIN / GOLD WALLET)
# =========================================================


class DepositAdminViewSet(AdminBaseViewSet):
    queryset = FinancialTransaction.objects.filter(type="DEPOSIT").order_by("-id")
    serializer_class = FinancialTransactionSerializer
    parser_classes = (MultiPartParser, FormParser)

    def get_queryset(self):
        qs = super().get_queryset()
        search = self.request.GET.get("search")
        status = self.request.GET.get("status")
        tracking_code = self.request.GET.get("tracking_code")
        user_id = self.request.GET.get("user_id")
        method = self.request.GET.get("method")
        start_date = self.request.GET.get("start_date")
        end_date = self.request.GET.get("end_date")
        ordering = self.request.GET.get("ordering")

        if search:
            qs = qs.filter(user__mobile__icontains=search)
        if status:
            qs = qs.filter(status=status)
        if user_id:
            qs = qs.filter(user_id=user_id)
        if method:
            qs = qs.filter(method=method)
        if tracking_code:
            qs = qs.filter(tracking_code__icontains=tracking_code)
        if start_date:
            qs = qs.filter(created_at__date__gte=start_date)
        if end_date:
            qs = qs.filter(created_at__date__lte=end_date)

        allowed_ordering = [
            "id",
            "-id",
            "amount",
            "-amount",
            "status",
            "-status",
            "created_at",
            "-created_at",
            "updated_at",
            "-updated_at",
        ]
        if ordering in allowed_ordering:
            qs = qs.order_by(ordering)
        return qs

    def list(self, request):
        qs = self.get_queryset()
        serializer = FinancialTransactionSerializer(
            qs, many=True, context={"request": request}
        )
        return success_response(
            "لیست واریزها", {"total_results": qs.count(), "results": serializer.data}
        )

    def retrieve(self, request, pk=None):
        obj = self.get_object()
        serializer = FinancialTransactionSerializer(obj, context={"request": request})
        return success_response("جزئیات واریز", serializer.data)

    @transaction.atomic
    def partial_update(self, request, *args, **kwargs):
        obj = FinancialTransaction.objects.select_for_update().get(pk=self.kwargs["pk"])
        serializer = StatusUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        new_status = serializer.validated_data.get("status")
        admin_note = serializer.validated_data.get("admin_note", "")
        previous_status = obj.status

        wallet, _ = Wallet.objects.select_for_update().get_or_create(user=obj.user)

        if new_status and new_status != previous_status:
            # 1. Transitioning into COMPLETED (Add to balance)
            if new_status == "COMPLETED":
                wallet.accessible_toman += obj.amount

            # 2. Transitioning OUT of COMPLETED into a failure state (Deduct what was previously given)
            elif previous_status == "COMPLETED" and new_status in [
                "FAILED",
                "REJECTED",
                "CANCELED",
            ]:
                wallet.accessible_toman -= obj.amount

            wallet.save(update_fields=["accessible_toman", "updated_at"])
            obj.status = new_status

        if admin_note:
            obj.admin_note = admin_note

        obj.save()

        sms_sent = (
            send_admin_note_sms(mobile=obj.user.mobile, note=admin_note)
            if admin_note
            else None
        )
        status_text = (
            STATUS_FA.get(new_status, new_status) if new_status else "ویرایش شده"
        )
        message = f"وضعیت واریز به {status_text} تغییر کرد"
        if sms_sent is False:
            message += " (ارسال پیامک ناموفق بود)"

        create_admin_log(
            request=request,
            admin=request.user,
            user=obj.user,
            action_type="DEPOSIT_UPDATE",
            action="تغییر وضعیت واریز",
            model_name="FinancialTransaction",
            object_id=obj.id,
            tracking_code=obj.tracking_code,
            response_status=200,
            description=f"کد پیگیری:\n{obj.tracking_code}\nوضعیت قبلی:\n{previous_status}\nوضعیت جدید:\n{obj.status}\nمبلغ:\n{obj.amount:,}\nموجودی:\n{wallet.accessible_toman:,}",
        )

        return success_response(
            message,
            {
                "transaction": FinancialTransactionSerializer(obj).data,
                "wallet": {
                    "accessible_toman": wallet.accessible_toman,
                    "blocked_toman": wallet.blocked_toman,
                    "toman_total": wallet.toman_total,
                },
                "sms_sent": sms_sent,
            },
        )


# =========================================================
# SILVER DEPOSIT
# =========================================================


class SilverDepositAdminViewSet(AdminBaseViewSet):
    queryset = SilverFinancialTransaction.objects.filter(type="DEPOSIT").order_by("-id")
    serializer_class = SilverFinancialTransactionSerializer
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    def get_queryset(self):
        qs = super().get_queryset()
        search = self.request.GET.get("search")
        status = self.request.GET.get("status")
        tracking_code = self.request.GET.get("tracking_code")
        user_id = self.request.GET.get("user_id")
        method = self.request.GET.get("method")
        start_date = self.request.GET.get("start_date")
        end_date = self.request.GET.get("end_date")
        ordering = self.request.GET.get("ordering")

        if search:
            qs = qs.filter(user__mobile__icontains=search)
        if status:
            qs = qs.filter(status=status)
        if user_id:
            qs = qs.filter(user_id=user_id)
        if method:
            qs = qs.filter(method=method)
        if tracking_code:
            qs = qs.filter(tracking_code__icontains=tracking_code)
        if start_date:
            qs = qs.filter(created_at__date__gte=start_date)
        if end_date:
            qs = qs.filter(created_at__date__lte=end_date)

        allowed_ordering = [
            "id",
            "-id",
            "amount",
            "-amount",
            "status",
            "-status",
            "created_at",
            "-created_at",
            "updated_at",
            "-updated_at",
        ]
        if ordering in allowed_ordering:
            qs = qs.order_by(ordering)
        return qs

    def list(self, request):
        qs = self.get_queryset()
        serializer = SilverFinancialTransactionSerializer(
            qs, many=True, context={"request": request}
        )
        return success_response(
            "لیست واریزهای نقره",
            {"total_results": qs.count(), "results": serializer.data},
        )

    def retrieve(self, request, pk=None):
        obj = self.get_object()
        serializer = SilverFinancialTransactionSerializer(
            obj, context={"request": request}
        )
        return success_response("جزئیات واریز نقره", serializer.data)

    @transaction.atomic
    def partial_update(self, request, *args, **kwargs):
        obj = SilverFinancialTransaction.objects.select_for_update().get(
            pk=self.kwargs["pk"]
        )
        serializer = StatusUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        new_status = serializer.validated_data.get("status")
        admin_note = serializer.validated_data.get("admin_note", "")
        previous_status = obj.status

        wallet, _ = SilverWallet.objects.select_for_update().get_or_create(
            user=obj.user
        )

        if new_status and new_status != previous_status:
            if new_status == "COMPLETED":
                wallet.balance += obj.amount
            elif previous_status == "COMPLETED" and new_status in [
                "FAILED",
                "REJECTED",
                "CANCELED",
            ]:
                wallet.balance -= obj.amount

            wallet.save(update_fields=["balance", "updated_at"])
            obj.status = new_status

        if admin_note:
            obj.admin_note = admin_note

        obj.save()

        sms_sent = (
            send_admin_note_sms(mobile=obj.user.mobile, note=admin_note)
            if admin_note
            else None
        )
        status_text = (
            STATUS_FA.get(new_status, new_status) if new_status else "ویرایش شده"
        )
        message = f"وضعیت واریز نقره به {status_text} تغییر کرد"
        if sms_sent is False:
            message += " (ارسال پیامک ناموفق بود)"

        create_admin_log(
            request=request,
            admin=request.user,
            user=obj.user,
            action_type="SILVER_DEPOSIT_UPDATE",
            action="تغییر وضعیت واریز نقره",
            model_name="SilverFinancialTransaction",
            object_id=obj.id,
            tracking_code=obj.tracking_code,
            response_status=200,
            description=f"کد پیگیری:\n{obj.tracking_code}\nوضعیت قبلی:\n{previous_status}\nوضعیت جدید:\n{obj.status}\nمبلغ:\n{obj.amount:,}\nموجودی:\n{wallet.balance:,}",
        )

        return success_response(
            message,
            {
                "transaction": SilverFinancialTransactionSerializer(obj).data,
                "wallet": {
                    "balance": wallet.balance,
                    "blocked_balance": wallet.blocked_balance,
                },
                "sms_sent": sms_sent,
            },
        )


# =========================================================
# SILVER WITHDRAW (ADMIN)
# =========================================================


class SilverWithdrawAdminViewSet(AdminBaseViewSet):
    queryset = SilverFinancialTransaction.objects.filter(type="WITHDRAW").order_by(
        "-id"
    )
    serializer_class = SilverFinancialTransactionSerializer
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    def get_queryset(self):
        qs = super().get_queryset()
        search = self.request.GET.get("search")
        status = self.request.GET.get("status")
        tracking_code = self.request.GET.get("tracking_code")
        user_id = self.request.GET.get("user_id")
        method = self.request.GET.get("method")
        start_date = self.request.GET.get("start_date")
        end_date = self.request.GET.get("end_date")
        ordering = self.request.GET.get("ordering")

        if search:
            qs = qs.filter(user__mobile__icontains=search)
        if status:
            qs = qs.filter(status=status)
        if user_id:
            qs = qs.filter(user_id=user_id)
        if method:
            qs = qs.filter(method=method)
        if tracking_code:
            qs = qs.filter(tracking_code__icontains=tracking_code)
        if start_date:
            qs = qs.filter(created_at__date__gte=start_date)
        if end_date:
            qs = qs.filter(created_at__date__lte=end_date)

        allowed_ordering = [
            "id",
            "-id",
            "amount",
            "-amount",
            "status",
            "-status",
            "created_at",
            "-created_at",
            "updated_at",
            "-updated_at",
        ]
        if ordering in allowed_ordering:
            qs = qs.order_by(ordering)
        return qs

    def list(self, request):
        qs = self.get_queryset()
        ser = SilverFinancialTransactionSerializer(
            qs, many=True, context={"request": request}
        )
        return success_response(
            "لیست برداشت‌های نقره", {"total_results": qs.count(), "results": ser.data}
        )

    def retrieve(self, request, pk=None):
        obj = self.get_object()
        return success_response(
            "جزئیات برداشت نقره",
            SilverFinancialTransactionSerializer(
                obj, context={"request": request}
            ).data,
        )

    @transaction.atomic
    def partial_update(self, request, *args, **kwargs):
        obj = SilverFinancialTransaction.objects.select_for_update().get(
            pk=self.kwargs["pk"]
        )
        ser = StatusUpdateSerializer(data=request.data, partial=True)
        ser.is_valid(raise_exception=True)

        new_status = ser.validated_data.get("status")
        admin_note = ser.validated_data.get("admin_note", "")
        previous_status = obj.status

        if new_status and new_status != previous_status and obj.method == "BANK":
            wallet = SilverWallet.objects.select_for_update().get(user=obj.user)

            # A: If coming from PENDING state
            if previous_status == "PENDING":
                if new_status == "COMPLETED":
                    wallet.blocked_toman -= obj.amount
                elif new_status in ["FAILED", "REJECTED", "CANCELED"]:
                    wallet.blocked_toman -= obj.amount
                    wallet.accessible_toman += obj.amount

            # B: Dynamic rollback if changed from COMPLETED to FAILED after the fact
            elif previous_status == "COMPLETED" and new_status in [
                "FAILED",
                "REJECTED",
                "CANCELED",
            ]:
                wallet.accessible_toman += obj.amount

            # C: If moving from FAILED back to COMPLETED
            elif (
                previous_status in ["FAILED", "REJECTED", "CANCELED"]
                and new_status == "COMPLETED"
            ):
                wallet.accessible_toman -= obj.amount

            wallet.save(update_fields=["blocked_toman", "accessible_toman"])
            obj.status = new_status

        if admin_note:
            obj.admin_note = admin_note
        obj.save()

        sms_sent = (
            send_admin_note_sms(mobile=obj.user.mobile, note=admin_note)
            if admin_note
            else None
        )
        status_text = (
            STATUS_FA.get(new_status, new_status) if new_status else "ویرایش شده"
        )
        msg = f"وضعیت برداشت نقره به {status_text} تغییر کرد"
        if sms_sent is False:
            msg += " (ارسال پیامک ناموفق بود)"

        return success_response(
            msg,
            {
                "transaction": SilverFinancialTransactionSerializer(obj).data,
                "sms_sent": sms_sent,
            },
        )


# =========================================================
# WITHDRAW (ADMIN) — MAIN / GOLD WALLET
# =========================================================


class WithdrawAdminViewSet(AdminBaseViewSet):
    queryset = FinancialTransaction.objects.filter(type="WITHDRAW").order_by("-id")
    serializer_class = FinancialTransactionSerializer
    parser_classes = (MultiPartParser, FormParser)

    def get_queryset(self):
        qs = super().get_queryset()
        search = self.request.GET.get("search")
        status = self.request.GET.get("status")
        tracking_code = self.request.GET.get("tracking_code")
        user_id = self.request.GET.get("user_id")
        method = self.request.GET.get("method")
        start_date = self.request.GET.get("start_date")
        end_date = self.request.GET.get("end_date")
        ordering = self.request.GET.get("ordering")

        if search:
            qs = qs.filter(user__mobile__icontains=search)
        if status:
            qs = qs.filter(status=status)
        if user_id:
            qs = qs.filter(user_id=user_id)
        if method:
            qs = qs.filter(method=method)
        if tracking_code:
            qs = qs.filter(tracking_code__icontains=tracking_code)
        if start_date:
            qs = qs.filter(created_at__date__gte=start_date)
        if end_date:
            qs = qs.filter(created_at__date__lte=end_date)

        allowed_ordering = [
            "id",
            "-id",
            "amount",
            "-amount",
            "status",
            "-status",
            "created_at",
            "-created_at",
            "updated_at",
            "-updated_at",
        ]
        if ordering in allowed_ordering:
            qs = qs.order_by(ordering)
        return qs

    def list(self, request):
        qs = self.get_queryset()
        ser = FinancialTransactionSerializer(
            qs, many=True, context={"request": request}
        )
        return success_response(
            "لیست برداشت‌ها", {"total_results": qs.count(), "results": ser.data}
        )

    def retrieve(self, request, pk=None):
        obj = self.get_object()
        return success_response(
            "جزئیات برداشت",
            FinancialTransactionSerializer(obj, context={"request": request}).data,
        )

    @transaction.atomic
    def partial_update(self, request, *args, **kwargs):
        obj = FinancialTransaction.objects.select_for_update().get(pk=self.kwargs["pk"])
        ser = StatusUpdateSerializer(data=request.data, partial=True)
        ser.is_valid(raise_exception=True)

        new_status = ser.validated_data.get("status")
        admin_note = ser.validated_data.get("admin_note", "")
        previous_status = obj.status

        if new_status and new_status != previous_status and obj.method == "BANK":
            wallet = Wallet.objects.select_for_update().get(user=obj.user)

            # A: Going from PENDING
            if previous_status == "PENDING":
                if new_status == "COMPLETED":
                    wallet.blocked_toman -= obj.amount
                elif new_status in ["FAILED", "REJECTED", "CANCELED"]:
                    wallet.blocked_toman -= obj.amount
                    wallet.accessible_toman += obj.amount

            # B: Moving from COMPLETED to FAILED (Return to balance)
            elif previous_status == "COMPLETED" and new_status in [
                "FAILED",
                "REJECTED",
                "CANCELED",
            ]:
                wallet.accessible_toman += obj.amount

            # C: Re-approving a previously failed/rejected transaction
            elif (
                previous_status in ["FAILED", "REJECTED", "CANCELED"]
                and new_status == "COMPLETED"
            ):
                wallet.accessible_toman -= obj.amount

            wallet.save(update_fields=["blocked_toman", "accessible_toman"])
            obj.status = new_status

        if admin_note:
            obj.admin_note = admin_note
        obj.save()

        sms_sent = (
            send_admin_note_sms(mobile=obj.user.mobile, note=admin_note)
            if admin_note
            else None
        )
        status_text = (
            STATUS_FA.get(new_status, new_status) if new_status else "ویرایش شده"
        )
        msg = f"وضعیت برداشت به {status_text} تغییر کرد"
        if sms_sent is False:
            msg += " (ارسال پیامک ناموفق بود)"

        return success_response(
            msg,
            {
                "transaction": FinancialTransactionSerializer(obj).data,
                "sms_sent": sms_sent,
            },
        )


# class GoldAdminViewSet(AdminBaseViewSet):
#     http_method_names = ["get"]
#     queryset = GoldPriceHistory.objects.none()
#     serializer_class = GoldLiveSerializer  # 👈 اضافه کن

#     # ----------------------
#     # LIST → ریدایرکت به live
#     # ----------------------
#     def list(self, request):
#         data = get_gold_bubble()

#         if data is None:
#             return error_response("دریافت قیمت لحظه‌ای طلا ناموفق بود", code=503)

#         return success_response(
#             "قیمت لحظه‌ای طلا", {"results": GoldLiveSerializer(data).data}
#         )

#     @action(detail=False, methods=["get"], url_path="live")
#     def live(self, request):
#         return self.list(request)

#     @action(detail=False, methods=["get"], url_path="chart")
#     def chart(self, request):
#         filter_type = request.GET.get("filter", "24H").upper()

#         if filter_type not in ["24H", "WEEKLY", "MONTHLY"]:
#             return error_response(
#                 "فیلتر نامعتبر است. مقادیر مجاز: 24H, WEEKLY, MONTHLY"
#             )

#         data = get_gold_chart_data(filter_type)

#         return success_response(
#             "چارت طلا", {"results": GoldChartDataSerializer(data).data}
#         )

# admin_panel/views.py - GoldAdminViewSet کامل

from rest_framework.decorators import action
from django.core.cache import cache
import requests
import logging
from datetime import datetime

from admin_panel.serializers import (
    GoldLiveSerializer,
    GoldChartDataSerializer,
    GoldPlatformPricesSerializer,
)
from gold_app.utils import get_gold_bubble, get_gold_chart_data
from accounts.utils import success_response, error_response
from gold_app.models import GoldPriceHistory

logger = logging.getLogger(__name__)


class GoldAdminViewSet(AdminBaseViewSet):
    """
    مدیریت قیمت طلا - نمایش قیمت لحظه‌ای و چارت
    """
    
    http_method_names = ["get"]
    queryset = GoldPriceHistory.objects.none()
    serializer_class = GoldLiveSerializer

    # =============================================
    # پلتفرم‌ها و API های آنها
    # =============================================
    
    PLATFORMS = {
        'KHANEH': {
            'name': 'خزانه زرین‌پین',
            'url': 'https://api-khazaneh.zarpin.com/v1/prc/prices/?v=2',
            'gold_code': 'GOLD_IRT',
        },
        'MILLI': {
            'name': 'میلی گلد',
            'url': 'https://milli.gold/api/v1/public/milli-price/external',
        },
        'TALASEA': {
            'name': 'طلاسی',
            'url': 'https://api.talasea.ir/api/market/getGoldPrice',
        },
        'WALLGOLD': {
            'name': 'وال گلد',
            'url': 'https://api.wallgold.ir/api/v1/price',
        },
        'HANZAEI': {
            'name': 'هنرایی گلد',
            'url': 'https://hamkarapi.hanzaeigold.com/api/v1/user/lastDataDashboard',
            'product_id': 60,
        },
    }

    CACHE_TIMEOUT = 240  # ۴ دقیقه

    # =============================================
    # متدهای دریافت قیمت از هر پلتفرم
    # =============================================

    def _fetch_khaneh(self):
        """دریافت قیمت از خزانه زرین‌پین"""
        try:
            response = requests.get(self.PLATFORMS['KHANEH']['url'], timeout=5)
            if response.status_code == 200:
                data = response.json()
                for item in data:
                    if item.get('code') == 'GOLD_IRT':
                        return {
                            'price': float(item.get('price', 0)),
                            'change_24h': float(item.get('price_change_24h', 0)),
                            'max_24h': float(item.get('max_24h_price', 0)),
                            'min_24h': float(item.get('min_24h_price', 0)),
                        }
            return None
        except Exception as e:
            logger.error(f"خطا در خزانه: {e}")
            return None

    def _fetch_milli(self):
        """دریافت قیمت از میلی گلد"""
        try:
            response = requests.get(self.PLATFORMS['MILLI']['url'], timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get('code') == 0:
                    price = data.get('data', {}).get('price18')
                    if price:
                        return {
                            'price': float(price) * 1000,
                            'change_24h': 0,
                            'max_24h': float(price) * 1000,
                            'min_24h': float(price) * 1000,
                        }
            return None
        except Exception as e:
            logger.error(f"خطا در میلی گلد: {e}")
            return None

    def _fetch_talasea(self):
        """دریافت قیمت از طلاسی"""
        try:
            response = requests.get(self.PLATFORMS['TALASEA']['url'], timeout=5)
            if response.status_code == 200:
                data = response.json()
                price = data.get('price')
                if price:
                    change = float(data.get('change24h', '0'))
                    return {
                        'price': float(price) * 1000,
                        'change_24h': change,
                        'max_24h': float(price) * 1000,
                        'min_24h': float(price) * 1000,
                    }
            return None
        except Exception as e:
            logger.error(f"خطا در طلاسی: {e}")
            return None

    def _fetch_wallgold(self):
        """دریافت قیمت از وال گلد"""
        try:
            response = requests.get(self.PLATFORMS['WALLGOLD']['url'], timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get('success') and data.get('result'):
                    price = data.get('result', {}).get('price')
                    if price:
                        return {
                            'price': float(price),
                            'change_24h': 0,
                            'max_24h': float(price),
                            'min_24h': float(price),
                        }
            return None
        except Exception as e:
            logger.error(f"خطا در وال گلد: {e}")
            return None

    def _fetch_hanzaei(self):
        """دریافت قیمت از هنرایی گلد"""
        try:
            response = requests.get(self.PLATFORMS['HANZAEI']['url'], timeout=5)
            if response.status_code == 200:
                data = response.json()
                products = data.get('data', {}).get('products', {}).get('gold', [])
                for item in products:
                    if item.get('product_id') == 60:
                        return {
                            'price': float(item.get('price_sell', 0)),
                            'change_24h': 0,
                            'max_24h': float(item.get('price_sell', 0)),
                            'min_24h': float(item.get('price_buy', 0)),
                        }
            return None
        except Exception as e:
            logger.error(f"خطا در هنرایی گلد: {e}")
            return None

    def _get_price_with_cache(self, platform_code):
        """دریافت قیمت با کش"""
        cache_key = f"gold_price_detail_{platform_code}"
        
        cached_price = cache.get(cache_key)
        if cached_price is not None:
            return cached_price
        
        fetch_methods = {
            'KHANEH': self._fetch_khaneh,
            'MILLI': self._fetch_milli,
            'TALASEA': self._fetch_talasea,
            'WALLGOLD': self._fetch_wallgold,
            'HANZAEI': self._fetch_hanzaei,
        }
        
        fetch_method = fetch_methods.get(platform_code)
        if not fetch_method:
            return None
        
        try:
            price_data = fetch_method()
            if price_data:
                cache.set(cache_key, price_data, self.CACHE_TIMEOUT)
            return price_data
        except Exception as e:
            logger.error(f"خطا در دریافت {platform_code}: {e}")
            return None

    def _get_all_platform_prices(self):
        """دریافت قیمت از همه پلتفرم‌ها"""
        result = []
        
        for platform_code, platform_info in self.PLATFORMS.items():
            price_data = self._get_price_with_cache(platform_code)
            
            item = {
                'platform_code': platform_code,
                'platform_name': platform_info['name'],
                'price': price_data['price'] if price_data else None,
                'change_24h': price_data.get('change_24h', 0) if price_data else None,
                'max_24h': price_data.get('max_24h', 0) if price_data else None,
                'min_24h': price_data.get('min_24h', 0) if price_data else None,
                'last_updated': datetime.now().isoformat() if price_data else None,
            }
            
            if price_data is None:
                item['error'] = 'دریافت قیمت ناموفق'
            
            result.append(item)
        
        return result

    # =============================================
    # LIST → قیمت لحظه‌ای + قیمت پلتفرم‌ها
    # =============================================

    def list(self, request):
        try:
            # دریافت قیمت اصلی (بابل)
            bubble_data = get_gold_bubble()
            
            if bubble_data is None:
                return error_response("دریافت قیمت لحظه‌ای طلا ناموفق بود", code=503)
            
            # دریافت قیمت‌های پلتفرم‌ها
            platform_prices = self._get_all_platform_prices()
            
            # ترکیب داده‌ها
            response_data = {
                "market_data": GoldLiveSerializer(bubble_data).data,
                "platform_prices": platform_prices,
                "last_updated": datetime.now().isoformat(),
            }
            
            return success_response(
                "قیمت لحظه‌ای طلا", 
                response_data
            )
            
        except Exception as e:
            logger.error(f"خطا در دریافت قیمت طلا: {e}")
            return error_response(f"خطا در دریافت قیمت طلا: {str(e)}")

    # =============================================
    # LIVE - قیمت لحظه‌ای
    # =============================================

    @action(detail=False, methods=["get"], url_path="live")
    def live(self, request):
        return self.list(request)

    # =============================================
    # CHART - چارت قیمت
    # =============================================

    @action(detail=False, methods=["get"], url_path="chart")
    def chart(self, request):
        filter_type = request.GET.get("filter", "24H").upper()

        if filter_type not in ["24H", "WEEKLY", "MONTHLY"]:
            return error_response(
                "فیلتر نامعتبر است. مقادیر مجاز: 24H, WEEKLY, MONTHLY"
            )

        data = get_gold_chart_data(filter_type)

        if data is None:
            return error_response("دریافت داده‌های چارت ناموفق بود", code=503)

        return success_response(
            "چارت طلا", {"results": GoldChartDataSerializer(data).data}
        )

    # =============================================
    # PLATFORMS - فقط قیمت پلتفرم‌ها
    # =============================================

    @action(detail=False, methods=["get"], url_path="platforms")
    def platforms(self, request):
        """دریافت قیمت‌های لحظه‌ای از همه پلتفرم‌ها"""
        try:
            platform_prices = self._get_all_platform_prices()
            
            return success_response(
                "قیمت پلتفرم‌های طلا",
                {
                    "platforms": platform_prices,
                    "last_updated": datetime.now().isoformat(),
                }
            )
        except Exception as e:
            logger.error(f"خطا در دریافت قیمت پلتفرم‌ها: {e}")
            return error_response(f"خطا در دریافت قیمت پلتفرم‌ها: {str(e)}")

    # =============================================
    # REFRESH - به‌روزرسانی کش
    # =============================================

    @action(detail=False, methods=["post"], url_path="refresh")
    def refresh(self, request):
        """به‌روزرسانی دستی قیمت‌ها"""
        try:
            # پاک کردن کش
            for platform_code in self.PLATFORMS.keys():
                cache.delete(f"gold_price_detail_{platform_code}")
            
            # دریافت مجدد
            platform_prices = self._get_all_platform_prices()
            
            return success_response(
                "قیمت‌ها با موفقیت به‌روزرسانی شدند",
                {
                    "platforms": platform_prices,
                    "last_updated": datetime.now().isoformat(),
                }
            )
        except Exception as e:
            logger.error(f"خطا در به‌روزرسانی: {e}")
            return error_response(f"خطا در به‌روزرسانی: {str(e)}")




# class SilverAdminViewSet(AdminBaseViewSet):
#     http_method_names = ["get"]
#     queryset = SilverPriceHistory.objects.none()
#     serializer_class = SilverLiveSerializer  # 👈 اضافه کن

#     # ----------------------
#     # LIST → ریدایرکت به live
#     # ----------------------
#     def list(self, request):
#         data = get_silver_bubble()

#         if data is None:
#             return error_response("دریافت قیمت لحظه‌ای نقره ناموفق بود", code=503)

#         return success_response(
#             "قیمت لحظه‌ای نقره", {"results": SilverLiveSerializer(data).data}
#         )

#     @action(detail=False, methods=["get"], url_path="live")
#     def live(self, request):
#         return self.list(request)

#     @action(detail=False, methods=["get"], url_path="chart")
#     def chart(self, request):
#         filter_type = request.GET.get("filter", "24H").upper()

#         if filter_type not in ["24H", "WEEKLY", "MONTHLY"]:
#             return error_response(
#                 "فیلتر نامعتبر است. مقادیر مجاز: 24H, WEEKLY, MONTHLY"
#             )

#         data = get_silver_chart_data(filter_type)

#         return success_response(
#             "چارت نقره", {"results": SilverChartDataSerializer(data).data}
#         )


# admin_panel/views.py - SilverAdminViewSet کامل

from rest_framework.decorators import action
from django.core.cache import cache
import requests
import logging
from datetime import datetime

from admin_panel.serializers import (
    SilverLiveSerializer,
    SilverChartDataSerializer,
    SilverPlatformPriceSerializer,
    SilverPlatformPricesSerializer,
)
from silver_app.utils import get_silver_bubble, get_silver_chart_data
from accounts.utils import success_response, error_response
from silver_app.models import SilverPriceHistory

logger = logging.getLogger(__name__)


class SilverAdminViewSet(AdminBaseViewSet):
    """
    مدیریت قیمت نقره - نمایش قیمت لحظه‌ای و چارت
    """
    
    http_method_names = ["get"]
    queryset = SilverPriceHistory.objects.none()
    serializer_class = SilverLiveSerializer

    # =============================================
    # پلتفرم‌ها و API های آنها
    # =============================================
    
    PLATFORMS = {
        'KHANEH': {
            'name': 'خزانه زرین‌پین',
            'code': 'KHANEH',
            'url': 'https://api-khazaneh.zarpin.com/v1/prc/prices/?v=2',
            'silver_code': 'SILVER_IRT',
        },
        'MILLI': {
            'name': 'میلی گلد',
            'code': 'MILLI',
            'url': 'https://milli.gold/api/v1/public/milli-price/external',
        },
        'TALASEA': {
            'name': 'طلاسی',
            'code': 'TALASEA',
            'url': 'https://api.talasea.ir/api/market/getGoldPrice',
        },
        'WALLGOLD': {
            'name': 'وال گلد',
            'code': 'WALLGOLD',
            'url': 'https://api.wallgold.ir/api/v1/price',
        },
        'HANZAEI': {
            'name': 'هنرایی گلد',
            'code': 'HANZAEI',
            'url': 'https://hamkarapi.hanzaeigold.com/api/v1/user/lastDataDashboard',
            'product_id': 61,  # product_id نقره در هنرایی گلد
        },
    }

    CACHE_TIMEOUT = 240  # ۴ دقیقه

    # =============================================
    # متدهای دریافت قیمت از هر پلتفرم
    # =============================================

    def _fetch_khaneh(self):
        """دریافت قیمت از خزانه زرین‌پین"""
        try:
            response = requests.get(self.PLATFORMS['KHANEH']['url'], timeout=5)
            if response.status_code == 200:
                data = response.json()
                for item in data:
                    if item.get('code') == 'SILVER_IRT':
                        return {
                            'price': float(item.get('price', 0)),
                            'change_24h': float(item.get('price_change_24h', 0)),
                            'max_24h': float(item.get('max_24h_price', 0)),
                            'min_24h': float(item.get('min_24h_price', 0)),
                        }
            return None
        except Exception as e:
            logger.error(f"خطا در خزانه (نقره): {e}")
            return None

    def _fetch_milli(self):
        """دریافت قیمت از میلی گلد - نقره ندارد، از طلا استفاده می‌کنیم و تبدیل می‌کنیم"""
        try:
            response = requests.get(self.PLATFORMS['MILLI']['url'], timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get('code') == 0:
                    price = data.get('data', {}).get('price18')
                    if price:
                        # نسبت طلا به نقره تقریباً ۱ به ۵۰ است
                        silver_price = (float(price) * 1000) / 50
                        return {
                            'price': silver_price,
                            'change_24h': 0,
                            'max_24h': silver_price,
                            'min_24h': silver_price,
                        }
            return None
        except Exception as e:
            logger.error(f"خطا در میلی گلد (نقره): {e}")
            return None

    def _fetch_talasea(self):
        """دریافت قیمت از طلاسی - نقره ندارد"""
        try:
            response = requests.get(self.PLATFORMS['TALASEA']['url'], timeout=5)
            if response.status_code == 200:
                data = response.json()
                # طلاسی فقط طلا دارد، برای نقره از طلا استفاده می‌کنیم
                price = data.get('price')
                if price:
                    silver_price = (float(price) * 1000) / 50
                    return {
                        'price': silver_price,
                        'change_24h': 0,
                        'max_24h': silver_price,
                        'min_24h': silver_price,
                    }
            return None
        except Exception as e:
            logger.error(f"خطا در طلاسی (نقره): {e}")
            return None

    def _fetch_wallgold(self):
        """دریافت قیمت از وال گلد"""
        try:
            response = requests.get(self.PLATFORMS['WALLGOLD']['url'], timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get('success') and data.get('result'):
                    price = data.get('result', {}).get('price')
                    if price:
                        return {
                            'price': float(price),
                            'change_24h': 0,
                            'max_24h': float(price),
                            'min_24h': float(price),
                        }
            return None
        except Exception as e:
            logger.error(f"خطا در وال گلد (نقره): {e}")
            return None

    def _fetch_hanzaei(self):
        """دریافت قیمت از هنرایی گلد - نقره"""
        try:
            response = requests.get(self.PLATFORMS['HANZAEI']['url'], timeout=5)
            if response.status_code == 200:
                data = response.json()
                products = data.get('data', {}).get('products', {}).get('gold', [])
                for item in products:
                    if item.get('product_id') == 61:  # product_id نقره
                        return {
                            'price': float(item.get('price_sell', 0)),
                            'change_24h': 0,
                            'max_24h': float(item.get('price_sell', 0)),
                            'min_24h': float(item.get('price_buy', 0)),
                        }
            return None
        except Exception as e:
            logger.error(f"خطا در هنرایی گلد (نقره): {e}")
            return None

    def _get_price_with_cache(self, platform_code):
        """دریافت قیمت با کش"""
        cache_key = f"silver_price_detail_{platform_code}"
        
        cached_price = cache.get(cache_key)
        if cached_price is not None:
            return cached_price
        
        fetch_methods = {
            'KHANEH': self._fetch_khaneh,
            'MILLI': self._fetch_milli,
            'TALASEA': self._fetch_talasea,
            'WALLGOLD': self._fetch_wallgold,
            'HANZAEI': self._fetch_hanzaei,
        }
        
        fetch_method = fetch_methods.get(platform_code)
        if not fetch_method:
            return None
        
        try:
            price_data = fetch_method()
            if price_data:
                cache.set(cache_key, price_data, self.CACHE_TIMEOUT)
            return price_data
        except Exception as e:
            logger.error(f"خطا در دریافت {platform_code} (نقره): {e}")
            return None

    def _get_all_platform_prices(self):
        """دریافت قیمت از همه پلتفرم‌ها"""
        result = []
        
        for platform_code, platform_info in self.PLATFORMS.items():
            price_data = self._get_price_with_cache(platform_code)
            
            item = {
                'platform_code': platform_code,
                'platform_name': platform_info['name'],
                'price': price_data['price'] if price_data else None,
                'change_24h': price_data.get('change_24h', 0) if price_data else None,
                'max_24h': price_data.get('max_24h', 0) if price_data else None,
                'min_24h': price_data.get('min_24h', 0) if price_data else None,
                'last_updated': datetime.now().isoformat() if price_data else None,
            }
            
            if price_data is None:
                item['error'] = 'دریافت قیمت ناموفق'
            
            result.append(item)
        
        return result

    # =============================================
    # LIST → قیمت لحظه‌ای + قیمت پلتفرم‌ها
    # =============================================

    def list(self, request):
        try:
            # دریافت قیمت اصلی (بابل) نقره
            bubble_data = get_silver_bubble()
            
            if bubble_data is None:
                return error_response("دریافت قیمت لحظه‌ای نقره ناموفق بود", code=503)
            
            # دریافت قیمت‌های پلتفرم‌ها
            platform_prices = self._get_all_platform_prices()
            
            # ترکیب داده‌ها
            response_data = {
                "market_data": SilverLiveSerializer(bubble_data).data,
                "platform_prices": platform_prices,
                "last_updated": datetime.now().isoformat(),
            }
            
            return success_response(
                "قیمت لحظه‌ای نقره", 
                response_data
            )
            
        except Exception as e:
            logger.error(f"خطا در دریافت قیمت نقره: {e}")
            return error_response(f"خطا در دریافت قیمت نقره: {str(e)}")

    # =============================================
    # LIVE - قیمت لحظه‌ای
    # =============================================

    @action(detail=False, methods=["get"], url_path="live")
    def live(self, request):
        return self.list(request)

    # =============================================
    # CHART - چارت قیمت
    # =============================================

    @action(detail=False, methods=["get"], url_path="chart")
    def chart(self, request):
        filter_type = request.GET.get("filter", "24H").upper()

        if filter_type not in ["24H", "WEEKLY", "MONTHLY"]:
            return error_response(
                "فیلتر نامعتبر است. مقادیر مجاز: 24H, WEEKLY, MONTHLY"
            )

        data = get_silver_chart_data(filter_type)

        if data is None:
            return error_response("دریافت داده‌های چارت نقره ناموفق بود", code=503)

        return success_response(
            "چارت نقره", {"results": SilverChartDataSerializer(data).data}
        )

    # =============================================
    # PLATFORMS - فقط قیمت پلتفرم‌ها
    # =============================================

    @action(detail=False, methods=["get"], url_path="platforms")
    def platforms(self, request):
        """دریافت قیمت‌های لحظه‌ای از همه پلتفرم‌ها"""
        try:
            platform_prices = self._get_all_platform_prices()
            
            return success_response(
                "قیمت پلتفرم‌های نقره",
                {
                    "platforms": platform_prices,
                    "last_updated": datetime.now().isoformat(),
                }
            )
        except Exception as e:
            logger.error(f"خطا در دریافت قیمت پلتفرم‌های نقره: {e}")
            return error_response(f"خطا در دریافت قیمت پلتفرم‌های نقره: {str(e)}")

    # =============================================
    # REFRESH - به‌روزرسانی کش
    # =============================================

    @action(detail=False, methods=["post"], url_path="refresh")
    def refresh(self, request):
        """به‌روزرسانی دستی قیمت‌ها"""
        try:
            # پاک کردن کش
            for platform_code in self.PLATFORMS.keys():
                cache.delete(f"silver_price_detail_{platform_code}")
            
            # دریافت مجدد
            platform_prices = self._get_all_platform_prices()
            
            return success_response(
                "قیمت‌های نقره با موفقیت به‌روزرسانی شدند",
                {
                    "platforms": platform_prices,
                    "last_updated": datetime.now().isoformat(),
                }
            )
        except Exception as e:
            logger.error(f"خطا در به‌روزرسانی قیمت نقره: {e}")
            return error_response(f"خطا در به‌روزرسانی قیمت نقره: {str(e)}")

# =========================================================


# =========================================================
# GOLD PRICE OFFSET
# =========================================================


class GoldPriceOffsetAdminViewSet(AdminBaseViewSet):

    queryset = GoldPriceOffset.objects.all().order_by("-id")
    serializer_class = GoldPriceOffsetSerializer
    http_method_names = ["get", "post", "patch", "delete"]

    # ======================
    # LIST
    # ======================
    def list(self, request):
        qs = self.get_queryset()
        return success_response(
            "لیست Offset های طلا",
            {
                "total_results": qs.count(),
                "results": self.serializer_class(
                    qs, many=True, context={"request": request}
                ).data,
            },
        )

    # ======================
    # RETRIEVE
    # ======================
    def retrieve(self, request, pk=None):
        obj = self.get_object()
        return success_response(
            "جزئیات Offset طلا",
            self.serializer_class(obj, context={"request": request}).data,
        )

    # ======================
    # CREATE
    # ======================
    def create(self, request):
        ser = self.serializer_class(data=request.data, context={"request": request})
        ser.is_valid(raise_exception=True)

        # گرفتن مقدار واقعی فرستاده شده؛ اگر نبود پیش‌فرض True
        is_active_val = request.data.get("is_active", True)
        if isinstance(is_active_val, str):
            is_active_val = is_active_val.lower() == "true"

        obj = ser.save(set_by=request.user, is_active=is_active_val)

        # برای اطمینان ملخی در صورتی که سریالایزر فیلد را نادیده گرفته باشد:
        if obj.is_active != is_active_val:
            obj.is_active = is_active_val
            obj.save()

        return success_response(
            "Offset طلا ثبت شد",
            self.serializer_class(obj, context={"request": request}).data,
        )

    # ======================
    # PATCH
    # ======================
    def partial_update(self, request, *args, **kwargs):
        obj = self.get_object()

        ser = self.serializer_class(
            obj, data=request.data, partial=True, context={"request": request}
        )
        ser.is_valid(raise_exception=True)
        obj = ser.save()

        # ⚡ راهکار اصلی: اگر فیلد در بدنه درخواست بود، مستقیماً روی مدل اوررایدش کن
        if "is_active" in request.data:
            val = request.data.get("is_active")
            # تبدیل حالت‌های استرینگ احتمالی مثل "false" به وضعیت بولین واقعی
            if isinstance(val, str):
                obj.is_active = val.lower() == "true"
            else:
                obj.is_active = bool(val)
            obj.save()

        obj.refresh_from_db()

        return success_response(
            "Offset طلا بروزرسانی شد",
            self.serializer_class(obj, context={"request": request}).data,
        )

    # ======================
    # DELETE
    # ======================
    def destroy(self, request, *args, **kwargs):
        obj = self.get_object()
        obj.delete()
        return success_response("Offset طلا حذف شد")



# =========================================================
# SILVER PRICE OFFSET
# =========================================================


class SilverPriceOffsetAdminViewSet(AdminBaseViewSet):

    queryset = SilverPriceOffset.objects.all().order_by("-id")
    serializer_class = SilverPriceOffsetSerializer
    http_method_names = ["get", "post", "patch", "delete"]

    # ======================
    # LIST
    # ======================
    def list(self, request):
        qs = self.get_queryset()
        return success_response(
            "لیست Offset های نقره",
            {
                "total_results": qs.count(),
                "results": self.serializer_class(
                    qs, many=True, context={"request": request}
                ).data,
            },
        )

    # ======================
    # RETRIEVE
    # ======================
    def retrieve(self, request, pk=None):
        obj = self.get_object()
        return success_response(
            "جزئیات Offset نقره",
            self.serializer_class(obj, context={"request": request}).data,
        )

    # ======================
    # CREATE
    # ======================
    def create(self, request):
        ser = self.serializer_class(data=request.data, context={"request": request})
        ser.is_valid(raise_exception=True)

        is_active_val = request.data.get("is_active", True)
        if isinstance(is_active_val, str):
            is_active_val = is_active_val.lower() == "true"

        obj = ser.save(set_by=request.user, is_active=is_active_val)

        if obj.is_active != is_active_val:
            obj.is_active = is_active_val
            obj.save()

        return success_response(
            "Offset نقره ثبت شد",
            self.serializer_class(obj, context={"request": request}).data,
        )

    # ======================
    # PATCH
    # ======================
    def partial_update(self, request, *args, **kwargs):
        obj = self.get_object()

        ser = self.serializer_class(
            obj, data=request.data, partial=True, context={"request": request}
        )
        ser.is_valid(raise_exception=True)
        obj = ser.save()

        # ⚡ راهکار اصلی: اگر فیلد در بدنه درخواست بود، مستقیماً روی مدل اوررایدش کن
        if "is_active" in request.data:
            val = request.data.get("is_active")
            if isinstance(val, str):
                obj.is_active = val.lower() == "true"
            else:
                obj.is_active = bool(val)
            obj.save()

        obj.refresh_from_db()

        return success_response(
            "Offset نقره بروزرسانی شد",
            self.serializer_class(obj, context={"request": request}).data,
        )

    # ======================
    # DELETE
    # ======================
    def destroy(self, request, *args, **kwargs):
        obj = self.get_object()
        obj.delete()
        return success_response("Offset نقره حذف شد")





from accounts.utils import create_referral_profit

 
# =========================================================
# VIEWSET
# =========================================================


# =========================================================
# GOLD TRANSACTION ADMIN VIEWSET
# =========================================================

from decimal import Decimal
from django.db import transaction
from django.contrib.auth import get_user_model
from rest_framework.decorators import action
import uuid

from accounts.utils import create_referral_profit
from gold_app.models import Wallet, GoldTransaction, GoldInventory

User = get_user_model()


# admin_panel/views.py

from decimal import Decimal
from django.db import transaction
from django.contrib.auth import get_user_model
from rest_framework.decorators import action
import uuid

from accounts.utils import create_referral_profit
from gold_app.models import Wallet, GoldTransaction, GoldInventory, GoldOrder
from gold_app.utils import get_live_gold_price, generate_tracking_code
from admin_panel.serializers import (
    GoldTransactionAdminSerializer,
    GoldOrderAdminSerializer,
    GoldTransactionStatusUpdateSerializer,
)

User = get_user_model()


# class GoldTransactionAdminViewSet(AdminBaseViewSet):
#     """
#     ویوست مدیریت تراکنش‌های طلا و سفارشات با قیمت طلا برای ادمین
#     """

#     queryset = GoldTransaction.objects.all().order_by("-id")
#     serializer_class = GoldTransactionAdminSerializer

#     # =====================================================
#     # QUERYSET FILTER
#     # =====================================================
#     def get_queryset(self):
#         qs = super().get_queryset()

#         search = self.request.GET.get("search")
#         status = self.request.GET.get("status")
#         type_ = self.request.GET.get("type")
#         tracking_code = self.request.GET.get("tracking_code")
#         start_date = self.request.GET.get("start_date")
#         end_date = self.request.GET.get("end_date")
#         ordering = self.request.GET.get("ordering")

#         if search:
#             qs = qs.filter(user__mobile__icontains=search)

#         if status:
#             qs = qs.filter(status=status)

#         if type_:
#             qs = qs.filter(type=type_)

#         if tracking_code:
#             qs = qs.filter(tracking_code__icontains=tracking_code)

#         if start_date:
#             qs = qs.filter(created_at__date__gte=start_date)

#         if end_date:
#             qs = qs.filter(created_at__date__lte=end_date)

#         allowed_ordering = [
#             "id", "-id",
#             "created_at", "-created_at",
#             "status", "-status",
#             "total_amount", "-total_amount",
#             "amount_gr", "-amount_gr",
#         ]

#         if ordering in allowed_ordering:
#             qs = qs.order_by(ordering)

#         return qs

#     # =====================================================
#     # LIST
#     # =====================================================
#     def list(self, request):
#         qs = self.get_queryset()
#         results = self.serializer_class(qs, many=True, context={"request": request}).data

#         # =====================================================
#         # ✅ اضافه کردن سفارشات با قیمت به لیست results
#         # =====================================================
#         limit_orders = GoldOrder.objects.filter(status="PENDING").order_by("-id")
#         limit_results = GoldOrderAdminSerializer(limit_orders, many=True).data

#         # ✅ ترکیب دو لیست در results
#         combined_results = results + limit_results

#         # ✅ مرتب‌سازی بر اساس created_at (جدیدترین اول)
#         combined_results.sort(key=lambda x: x.get("created_at", ""), reverse=True)

#         return success_response(
#             "لیست تراکنش‌های طلا و سفارشات با قیمت",
#             {
#                 "total_results": len(combined_results),
#                 "results": combined_results  # ✅ فرانت‌اند منتظر results هست
#             }
#         )

#     # =====================================================
#     # RETRIEVE
#     # =====================================================
#     def retrieve(self, request, pk=None):

#         try:
#             obj = GoldTransaction.objects.get(pk=pk)
#             data = self.serializer_class(obj, context={"request": request}).data
#             data["created_at"] = obj.created_at.strftime("%Y-%m-%d %H:%M:%S")
#             return success_response("جزئیات تراکنش طلا", data)
#         except GoldTransaction.DoesNotExist:
#             pass
#         try:
#             order = GoldOrder.objects.get(pk=pk)
#             data = GoldOrderAdminSerializer(order, context={"request": request}).data
#             data["created_at"] = order.created_at.strftime("%Y-%m-%d %H:%M:%S")
#             data["amount"] = data.get("amount_gr")
#             data["user"] = order.user.id
#             data["total_price"] = data.get("total_amount")
#             return success_response("جزئیات سفارش با قیمت طلا", data)
#         except GoldOrder.DoesNotExist:
#             pass
#         return error_response("تراکنش یا سفارش مورد نظر یافت نشد.")


#     # =====================================================
#     # PATCH
#     # =====================================================
#     @transaction.atomic
#     def partial_update(self, request, *args, **kwargs):
#         if "status" in request.data:
#             return self._change_status(request, kwargs["pk"])

#         return super().partial_update(request, *args, **kwargs)

#     # =====================================================
#     # UPDATE
#     # =====================================================
#     @transaction.atomic
#     def update(self, request, *args, **kwargs):
#         if "status" in request.data:
#             return self._change_status(request, kwargs["pk"])

#         return super().update(request, *args, **kwargs)

#     # =====================================================
#     # CHANGE STATUS
#     # =====================================================
#     @action(detail=True, methods=["post"])
#     @transaction.atomic
#     def change_status(self, request, pk=None):
#         return self._change_status(request, pk)

#     # =====================================================
#     # CORE BUSINESS LOGIC
#     # =====================================================
#     def _change_status(self, request, pk):
#         tx = (
#             GoldTransaction.objects
#             .select_for_update()
#             .select_related("user")
#             .get(pk=pk)
#         )

#         wallet, _ = Wallet.objects.select_for_update().get_or_create(user=tx.user)
#         inventory, _ = GoldInventory.objects.select_for_update().get_or_create(user=tx.user)

#         serializer = GoldTransactionStatusUpdateSerializer(data=request.data)
#         serializer.is_valid(raise_exception=True)

#         new_status = serializer.validated_data["status"]
#         description = serializer.validated_data.get("description", "")

#         old_status = tx.status

#         if old_status == new_status:
#             return error_response("وضعیت تغییری نکرده است.")

#         if old_status != "PENDING":
#             return error_response(
#                 f"تراکنشی که در وضعیت «{tx.get_status_display()}» است، قابل تغییر نیست."
#             )

#         if new_status not in ("COMPLETED", "FAILED"):
#             return error_response("وضعیت مقصد نامعتبر است.")

#         # =================================================
#         # BUY - COMPLETED
#         # =================================================
#         if tx.type == "BUY" and new_status == "COMPLETED":
#             if wallet.blocked_toman < tx.total_amount:
#                 return error_response("مغایرت در موجودی بلوکه‌شده تومانی کاربر.")

#             wallet.blocked_toman = max(0, wallet.blocked_toman - tx.total_amount)
#             wallet.save(update_fields=["blocked_toman"])

#             inventory.accessible_balance += tx.amount_gr
#             inventory.save(update_fields=["accessible_balance"])

#             try:
#                 from accounts.utils import create_referral_profit
#                 create_referral_profit(
#                     user=tx.user,
#                     source_type="GOLD",
#                     commission_amount=tx.commission_amount,
#                     transaction_amount=tx.total_amount,
#                 )
#             except Exception as e:
#                 print(f"❌ خطا در ایجاد پاداش معرفی: {e}")

#         # =================================================
#         # BUY - FAILED
#         # =================================================
#         elif tx.type == "BUY" and new_status == "FAILED":
#             wallet.accessible_toman += tx.total_amount
#             wallet.blocked_toman = max(0, wallet.blocked_toman - tx.total_amount)
#             wallet.save(update_fields=["accessible_toman", "blocked_toman"])

#         # =================================================
#         # SELL - COMPLETED
#         # =================================================
#         elif tx.type == "SELL" and new_status == "COMPLETED":
#             if inventory.blocked_balance < tx.amount_gr:
#                 return error_response("مغایرت در موجودی بلوکه‌شده طلای کاربر.")

#             inventory.blocked_balance = max(0, inventory.blocked_balance - tx.amount_gr)
#             inventory.save(update_fields=["blocked_balance"])

#             wallet.accessible_toman += tx.total_amount
#             wallet.save(update_fields=["accessible_toman"])
#             try:
#                 from accounts.utils import create_referral_profit
#                 create_referral_profit(
#                     user=tx.user,
#                     source_type="GOLD",
#                     commission_amount=tx.commission_amount,
#                     transaction_amount=tx.total_amount + tx.commission_amount
#                 )
#             except Exception as e:
#                 print(f"❌ خطا در ایجاد پاداش معرفی: {e}")

#         # =================================================
#         # SELL - FAILED
#         # =================================================
#         elif tx.type == "SELL" and new_status == "FAILED":
#             inventory.accessible_balance += tx.amount_gr
#             inventory.blocked_balance = max(0, inventory.blocked_balance - tx.amount_gr)
#             inventory.save(update_fields=["accessible_balance", "blocked_balance"])

#         # =================================================
#         # UPDATE TRANSACTION
#         # =================================================
#         tx.status = new_status
#         if description:
#             tx.description = f"{tx.description}\n{description}" if tx.description else description
#         tx.save(update_fields=["status", "description", "updated_at"])

#         create_admin_log(
#             request=request,
#             user=tx.user,
#             action_type=f"{tx.type}_GOLD_{new_status}",
#             action=f"تغییر وضعیت تراکنش طلا به {tx.get_status_display()}",
#             model_name="GoldTransaction",
#             object_id=tx.id,
#             tracking_code=tx.tracking_code,
#             success=True,
#             description=description or f"{tx.type} -> {new_status}",
#         )

#         tx.refresh_from_db()

#         return success_response(
#             "وضعیت تراکنش با موفقیت تغییر کرد.",
#             self.serializer_class(tx, context={"request": request}).data
#         )

#     # =====================================================
#     # ✅ CANCEL LIMIT ORDER (لغو سفارش با قیمت توسط ادمین)
#     # =====================================================
#     @action(detail=False, methods=["post"], url_path="limit-order/cancel")
#     @transaction.atomic
#     def cancel_limit_order(self, request):
#         order_id = request.data.get("order_id")
#         if not order_id:
#             return error_response("شناسه سفارش الزامی است.")

#         order = GoldOrder.objects.filter(id=order_id).first()
#         if not order:
#             return error_response("سفارش یافت نشد.")

#         if order.status != "PENDING":
#             return error_response("فقط سفارشات در وضعیت «در انتظار» قابل لغو هستند.")

#         if order.order_type == "BUY":
#             wallet, _ = Wallet.objects.select_for_update().get_or_create(user=order.user)
#             wallet.accessible_toman += order.amount_toman
#             wallet.blocked_toman -= order.amount_toman
#             wallet.save(update_fields=["accessible_toman", "blocked_toman"])
#         else:
#             inventory, _ = GoldInventory.objects.select_for_update().get_or_create(user=order.user)
#             inventory.accessible_balance += order.gold_weight
#             inventory.blocked_balance -= order.gold_weight
#             inventory.save(update_fields=["accessible_balance", "blocked_balance"])

#         order.status = "CANCELLED"
#         order.description = f"{order.description or ''}\nلغو شده توسط ادمین"
#         order.save(update_fields=["status", "description", "updated_at"])

#         create_admin_log(
#             request=request,
#             user=order.user,
#             action_type="GOLD_LIMIT_CANCEL",
#             action="لغو سفارش با قیمت طلا توسط ادمین",
#             model_name="GoldOrder",
#             object_id=order.id,
#             success=True,
#             description=f"""
# لغو سفارش با قیمت طلا توسط ادمین
# کاربر: {order.user.mobile}
# نوع سفارش: {order.get_order_type_display()}
# قیمت هدف: {order.target_price:,}
# وزن: {order.estimated_weight} گرم
# """,
#         )

#         return success_response(
#             "سفارش با موفقیت لغو شد.",
#             GoldOrderAdminSerializer(order, context={"request": request}).data
#         )

#     # =====================================================
#     # ✅ EXECUTE LIMIT ORDER (اجرای سفارش با قیمت توسط ادمین)
#     # =====================================================
#     @action(detail=False, methods=["post"], url_path="limit-order/execute")
#     @transaction.atomic
#     def execute_limit_order(self, request):
#         order_id = request.data.get("order_id")
#         if not order_id:
#             return error_response("شناسه سفارش الزامی است.")

#         order = GoldOrder.objects.filter(id=order_id).first()
#         if not order:
#             return error_response("سفارش یافت نشد.")

#         if order.status != "PENDING":
#             return error_response("فقط سفارشات در وضعیت «در انتظار» قابل اجرا هستند.")

#         current_price = get_live_gold_price()
#         if not current_price:
#             return error_response("خطا در دریافت قیمت لحظه‌ای طلا")

#         current_price = Decimal(str(current_price))

#         if order.order_type == "BUY" and current_price > order.target_price:
#             return error_response(
#                 f"قیمت فعلی ({current_price:,}) بیشتر از قیمت هدف ({order.target_price:,}) است. قابل اجرا نیست."
#             )
#         if order.order_type == "SELL" and current_price < order.target_price:
#             return error_response(
#                 f"قیمت فعلی ({current_price:,}) کمتر از قیمت هدف ({order.target_price:,}) است. قابل اجرا نیست."
#             )

#         if order.order_type == "BUY":
#             wallet, _ = Wallet.objects.select_for_update().get_or_create(user=order.user)
#             inventory, _ = GoldInventory.objects.select_for_update().get_or_create(user=order.user)

#             fee_rate = Decimal(str(order.fee_rate))
#             pure_price = (order.amount_toman / (Decimal("1") + fee_rate)).quantize(Decimal("1"))
#             fee = (order.amount_toman - pure_price).quantize(Decimal("1"))
#             weight = (pure_price / current_price).quantize(Decimal("0.001"), rounding=ROUND_DOWN)

#             if wallet.blocked_toman < order.amount_toman:
#                 return error_response("مغایرت در موجودی بلوکه شده")

#             wallet.blocked_toman -= order.amount_toman
#             wallet.save(update_fields=["blocked_toman"])

#             inventory.accessible_balance += weight
#             inventory.save(update_fields=["accessible_balance"])

#             GoldTransaction.objects.create(
#                 user=order.user,
#                 type="BUY",
#                 status="COMPLETED",
#                 amount_gr=weight,
#                 price_per_gram=current_price,
#                 fee=fee,
#                 commission_percent=fee_rate * 100,
#                 commission_amount=fee,
#                 total_amount=order.amount_toman,
#                 tracking_code=generate_tracking_code("BUY"),
#                 description=f"اجرای دستی توسط ادمین - قیمت هدف {order.target_price}"
#             )

#             try:
#                 create_referral_profit(
#                     user=order.user,
#                     source_type="GOLD",
#                     transaction_amount=order.amount_toman,
#                 )
#             except Exception as e:
#                 print(f"❌ خطا در ایجاد پاداش معرفی: {e}")

#         else:
#             wallet, _ = Wallet.objects.select_for_update().get_or_create(user=order.user)
#             inventory, _ = GoldInventory.objects.select_for_update().get_or_create(user=order.user)

#             fee_rate = Decimal(str(order.fee_rate))
#             pure_price = (current_price * order.gold_weight).quantize(Decimal("1"))
#             fee = (pure_price * fee_rate).quantize(Decimal("1"))
#             total_price = (pure_price - fee).quantize(Decimal("1"))

#             if inventory.blocked_balance < order.gold_weight:
#                 return error_response("مغایرت در موجودی بلوکه شده طلا")

#             inventory.blocked_balance -= order.gold_weight
#             inventory.save(update_fields=["blocked_balance"])

#             wallet.accessible_toman += total_price
#             wallet.save(update_fields=["accessible_toman"])

#             GoldTransaction.objects.create(
#                 user=order.user,
#                 type="SELL",
#                 status="COMPLETED",
#                 amount_gr=order.gold_weight,
#                 price_per_gram=current_price,
#                 fee=fee,
#                 commission_percent=fee_rate * 100,
#                 commission_amount=fee,
#                 total_amount=total_price,
#                 tracking_code=generate_tracking_code("SELL"),
#                 description=f"اجرای دستی توسط ادمین - قیمت هدف {order.target_price}"
#             )

#         order.status = "EXECUTED"
#         order.executed_price = current_price
#         order.save(update_fields=["status", "executed_price", "updated_at"])

#         create_admin_log(
#             request=request,
#             user=order.user,
#             action_type="GOLD_LIMIT_EXECUTE",
#             action="اجرای دستی سفارش با قیمت طلا توسط ادمین",
#             model_name="GoldOrder",
#             object_id=order.id,
#             success=True,
#             description=f"""
# اجرای دستی سفارش با قیمت طلا توسط ادمین
# کاربر: {order.user.mobile}
# نوع سفارش: {order.get_order_type_display()}
# قیمت هدف: {order.target_price:,}
# قیمت اجرا: {current_price:,}
# وزن: {order.estimated_weight} گرم
# """,
#         )

#         return success_response(
#             "سفارش با موفقیت اجرا شد.",
#             GoldOrderAdminSerializer(order, context={"request": request}).data
#         )
#     @action(detail=False, methods=["get"], url_path="limit-order/(?P<order_id>[^/.]+)")
#     def detail_limit_order(self, request, order_id):
#         order = GoldOrder.objects.filter(id=order_id).first()
#         if not order:
#             return error_response("سفارش یافت نشد.")
#         serializer = GoldOrderAdminSerializer(order, context={"request": request})
#         return success_response(
#             "جزئیات سفارش با قیمت طلا",
#             )

# admin_panel/views.py - GoldTransactionAdminViewSet کامل (نسخه‌ی امن در برابر None)

import traceback
from decimal import Decimal
from django.db import transaction
from django.contrib.auth import get_user_model
from rest_framework.decorators import action
import uuid

from accounts.utils import create_referral_profit
from gold_app.models import Wallet, GoldTransaction, GoldInventory
from gold_app.services.invoice_service import InvoiceService

User = get_user_model()


class GoldTransactionAdminViewSet(AdminBaseViewSet):
    """
    ویوست مدیریت تراکنش‌های طلا برای ادمین
    """

    queryset = GoldTransaction.objects.all().order_by("-id")
    serializer_class = GoldTransactionAdminSerializer

    # =====================================================
    # QUERYSET FILTER
    # =====================================================
    def get_queryset(self):
        qs = super().get_queryset()

        search = self.request.GET.get("search")
        status = self.request.GET.get("status")
        type_ = self.request.GET.get("type")
        tracking_code = self.request.GET.get("tracking_code")
        start_date = self.request.GET.get("start_date")
        end_date = self.request.GET.get("end_date")
        ordering = self.request.GET.get("ordering")

        if search:
            qs = qs.filter(user__mobile__icontains=search)

        if status:
            qs = qs.filter(status=status)

        if type_:
            qs = qs.filter(type=type_)

        if tracking_code:
            qs = qs.filter(tracking_code__icontains=tracking_code)

        if start_date:
            qs = qs.filter(created_at__date__gte=start_date)

        if end_date:
            qs = qs.filter(created_at__date__lte=end_date)

        allowed_ordering = [
            "id", "-id",
            "created_at", "-created_at",
            "status", "-status",
            "total_amount", "-total_amount",
            "amount_gr", "-amount_gr",
        ]

        if ordering in allowed_ordering:
            qs = qs.order_by(ordering)

        return qs

    # =====================================================
    # LIST
    # =====================================================
    def list(self, request):
        qs = self.get_queryset()

        return success_response(
            "لیست تراکنش‌های طلا",
            {
                "total_results": qs.count(),
                "results": self.serializer_class(
                    qs,
                    many=True,
                    context={"request": request}
                ).data
            }
        )

    # =====================================================
    # RETRIEVE
    # =====================================================
    def retrieve(self, request, pk=None):
        obj = self.get_object()

        data = self.serializer_class(
            obj,
            context={"request": request}
        ).data

        data["created_at"] = obj.created_at.strftime("%Y-%m-%d %H:%M:%S")

        return success_response(
            "جزئیات تراکنش طلا",
            data
        )

    # =====================================================
    # PATCH
    # =====================================================
    @transaction.atomic
    def partial_update(self, request, *args, **kwargs):
        if "status" in request.data:
            result = self._change_status(request, kwargs["pk"])
            # ✅ ایمنی: اگه به هر دلیلی None برگشت، خطای مشخص بده نه کرش خام
            if result is None:
                return error_response("خطای داخلی در تغییر وضعیت تراکنش رخ داد.", status_code=500)
            return result

        return super().partial_update(request, *args, **kwargs)

    # =====================================================
    # UPDATE
    # =====================================================
    @transaction.atomic
    def update(self, request, *args, **kwargs):
        if "status" in request.data:
            result = self._change_status(request, kwargs["pk"])
            if result is None:
                return error_response("خطای داخلی در تغییر وضعیت تراکنش رخ داد.", status_code=500)
            return result

        return super().update(request, *args, **kwargs)

    # =====================================================
    # CHANGE STATUS (action endpoint)
    # =====================================================
    @action(detail=True, methods=["post"])
    @transaction.atomic
    def change_status(self, request, pk=None):
        result = self._change_status(request, pk)
        if result is None:
            return error_response("خطای داخلی در تغییر وضعیت تراکنش رخ داد.", status_code=500)
        return result

    # =====================================================
    # CORE BUSINESS LOGIC
    # =====================================================
    def _change_status(self, request, pk):
        try:
            tx = (
                GoldTransaction.objects
                .select_for_update()
                .select_related("user")
                .get(pk=pk)
            )
        except GoldTransaction.DoesNotExist:
            return error_response("تراکنش یافت نشد", status_code=404)

        wallet, _ = Wallet.objects.select_for_update().get_or_create(user=tx.user)
        inventory, _ = GoldInventory.objects.select_for_update().get_or_create(user=tx.user)

        serializer = GoldTransactionStatusUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response("اطلاعات نامعتبر است", serializer.errors)

        new_status = serializer.validated_data["status"]
        description = serializer.validated_data.get("description", "")

        old_status = tx.status

        if old_status == new_status:
            return error_response("وضعیت تغییری نکرده است.")

        if old_status != "PENDING":
            return error_response(
                f"تراکنشی که در وضعیت «{tx.get_status_display()}» است، قابل تغییر نیست."
            )

        if new_status not in ("COMPLETED", "FAILED"):
            return error_response("وضعیت مقصد نامعتبر است.")

        # ✅ گارد جدید: اگه نوع تراکنش چیزی غیر از BUY/SELL بود، خطای مشخص بده
        if tx.type not in ("BUY", "SELL"):
            return error_response(f"نوع تراکنش «{tx.type}» پشتیبانی نمی‌شود.")

        invoice_obj = None

        try:
            # =================================================
            # BUY - COMPLETED ✅
            # =================================================
            if tx.type == "BUY" and new_status == "COMPLETED":
                if wallet.blocked_toman < tx.total_amount:
                    return error_response("مغایرت در موجودی بلوکه‌شده تومانی کاربر.")

                wallet.blocked_toman = max(0, wallet.blocked_toman - tx.total_amount)
                wallet.save(update_fields=["blocked_toman"])

                inventory.accessible_balance += tx.amount_gr
                inventory.save(update_fields=["accessible_balance"])

                try:
                    create_referral_profit(
                        user=tx.user,
                        source_type="GOLD",
                        transaction_amount=tx.total_amount,
                    )
                except Exception as e:
                    print(f"❌ خطا در ایجاد پاداش معرفی: {e}")

                tx.status = new_status
                if description:
                    tx.description = f"{tx.description}\n{description}" if tx.description else description
                tx.save(update_fields=["status", "description", "updated_at"])

                try:
                    invoice_obj = InvoiceService.create_buy_invoice(tx, request)
                    print(f"✅ فاکتور خرید ایجاد شد: {invoice_obj.invoice_number}")
                except Exception:
                    print("❌ خطا در ایجاد فاکتور خرید:")
                    traceback.print_exc()

            # =================================================
            # BUY - FAILED ❌
            # =================================================
            elif tx.type == "BUY" and new_status == "FAILED":
                wallet.accessible_toman += tx.total_amount
                wallet.blocked_toman = max(0, wallet.blocked_toman - tx.total_amount)
                wallet.save(update_fields=["accessible_toman", "blocked_toman"])

                tx.status = new_status
                if description:
                    tx.description = f"{tx.description}\n{description}" if tx.description else description
                tx.save(update_fields=["status", "description", "updated_at"])

            # =================================================
            # SELL - COMPLETED ✅
            # =================================================
            elif tx.type == "SELL" and new_status == "COMPLETED":
                if inventory.blocked_balance < tx.amount_gr:
                    return error_response("مغایرت در موجودی بلوکه‌شده طلای کاربر.")

                inventory.blocked_balance = max(0, inventory.blocked_balance - tx.amount_gr)
                inventory.save(update_fields=["blocked_balance"])

                wallet.accessible_toman += tx.total_amount
                wallet.save(update_fields=["accessible_toman"])

                try:
                    create_referral_profit(
                        user=tx.user,
                        source_type="GOLD",
                        transaction_amount=tx.total_amount,
                    )
                except Exception as e:
                    print(f"❌ خطا در ایجاد پاداش معرفی: {e}")

                tx.status = new_status
                if description:
                    tx.description = f"{tx.description}\n{description}" if tx.description else description
                tx.save(update_fields=["status", "description", "updated_at"])

                try:
                    invoice_obj = InvoiceService.create_sell_invoice(tx, request)
                    print(f"✅ فاکتور فروش ایجاد شد: {invoice_obj.invoice_number}")
                except Exception:
                    print("❌ خطا در ایجاد فاکتور فروش:")
                    traceback.print_exc()

            # =================================================
            # SELL - FAILED ❌
            # =================================================
            elif tx.type == "SELL" and new_status == "FAILED":
                inventory.accessible_balance += tx.amount_gr
                inventory.blocked_balance = max(0, inventory.blocked_balance - tx.amount_gr)
                inventory.save(update_fields=["accessible_balance", "blocked_balance"])

                tx.status = new_status
                if description:
                    tx.description = f"{tx.description}\n{description}" if tx.description else description
                tx.save(update_fields=["status", "description", "updated_at"])

        except Exception:
            # ✅ هر خطای غیرمنتظره‌ی دیگه هم اینجا گرفته می‌شه
            # و به‌جای برگردوندن None، خطای واضح برمی‌گرده
            print("❌ خطای غیرمنتظره در تغییر وضعیت تراکنش:")
            traceback.print_exc()
            return error_response("خطای داخلی در پردازش تراکنش رخ داد.", status_code=500)

        # =================================================
        # REGISTER ADMIN LOG
        # =================================================
        try:
            create_admin_log(
                request=request,
                user=tx.user,
                action_type=f"{tx.type}_GOLD_{new_status}",
                action=f"تغییر وضعیت تراکنش طلا به {tx.get_status_display()}",
                model_name="GoldTransaction",
                object_id=tx.id,
                tracking_code=tx.tracking_code,
                success=True,
                description=description or f"{tx.type} -> {new_status}",
            )
        except Exception:
            print("❌ خطا در ثبت لاگ ادمین:")
            traceback.print_exc()

        tx.refresh_from_db()

        response_data = self.serializer_class(tx, context={"request": request}).data

        if invoice_obj is None:
            invoice_obj = getattr(tx, "invoice", None)  # بسته به related_name مدل Invoice شما

        if invoice_obj:
            response_data["invoice_id"] = invoice_obj.id
            response_data["invoice_number"] = invoice_obj.invoice_number
        else:
            response_data["invoice_id"] = None
            response_data["invoice_number"] = None

        return success_response(
            "وضعیت تراکنش با موفقیت تغییر کرد.",
            response_data
        )



# =========================================================
# SILVER TRANSACTION ADMIN VIEWSET - بدون سفارش با قیمت ✅
# =========================================================

from decimal import Decimal
from django.db import transaction
from django.contrib.auth import get_user_model
from rest_framework.decorators import action
import uuid

from accounts.utils import create_referral_profit
from silver_app.models import SilverWallet, SilverTransaction, SilverInventory

User = get_user_model()


# class SilverTransactionAdminViewSet(AdminBaseViewSet):
#     """
#     ویوست مدیریت تراکنش‌های نقره برای ادمین
#     """

#     queryset = SilverTransaction.objects.all().order_by("-id")
#     serializer_class = SilverTransactionAdminSerializer

#     # =====================================================
#     # QUERYSET FILTER
#     # =====================================================
#     def get_queryset(self):
#         qs = super().get_queryset()

#         search = self.request.GET.get("search")
#         status = self.request.GET.get("status")
#         type_ = self.request.GET.get("type")
#         tracking_code = self.request.GET.get("tracking_code")
#         start_date = self.request.GET.get("start_date")
#         end_date = self.request.GET.get("end_date")
#         ordering = self.request.GET.get("ordering")

#         if search:
#             qs = qs.filter(user__mobile__icontains=search)

#         if status:
#             qs = qs.filter(status=status)

#         if type_:
#             qs = qs.filter(type=type_)

#         if tracking_code:
#             qs = qs.filter(tracking_code__icontains=tracking_code)

#         if start_date:
#             qs = qs.filter(created_at__date__gte=start_date)

#         if end_date:
#             qs = qs.filter(created_at__date__lte=end_date)

#         allowed_ordering = [
#             "id", "-id",
#             "created_at", "-created_at",
#             "status", "-status",
#             "total_amount", "-total_amount",
#             "amount_gr", "-amount_gr",
#         ]

#         if ordering in allowed_ordering:
#             qs = qs.order_by(ordering)

#         return qs

#     # =====================================================
#     # LIST
#     # =====================================================
#     def list(self, request):
#         qs = self.get_queryset()

#         return success_response(
#             "لیست تراکنش‌های نقره",
#             {
#                 "total_results": qs.count(),
#                 "results": self.serializer_class(
#                     qs,
#                     many=True,
#                     context={"request": request}
#                 ).data
#             }
#         )

#     # =====================================================
#     # RETRIEVE
#     # =====================================================
#     def retrieve(self, request, pk=None):
#         obj = self.get_object()

#         data = self.serializer_class(
#             obj,
#             context={"request": request}
#         ).data

#         data["created_at"] = obj.created_at.strftime("%Y-%m-%d %H:%M:%S")

#         return success_response(
#             "جزئیات تراکنش نقره",
#             data
#         )

#     # =====================================================
#     # PATCH
#     # =====================================================
#     @transaction.atomic
#     def partial_update(self, request, *args, **kwargs):
#         if "status" in request.data:
#             return self._change_status(request, kwargs["pk"])

#         return super().partial_update(request, *args, **kwargs)

#     # =====================================================
#     # UPDATE
#     # =====================================================
#     @transaction.atomic
#     def update(self, request, *args, **kwargs):
#         if "status" in request.data:
#             return self._change_status(request, kwargs["pk"])

#         return super().update(request, *args, **kwargs)

#     # =====================================================
#     # CHANGE STATUS
#     # =====================================================
#     @action(detail=True, methods=["post"])
#     @transaction.atomic
#     def change_status(self, request, pk=None):
#         return self._change_status(request, pk)

#     # =====================================================
#     # CORE BUSINESS LOGIC
#     # =====================================================
#     def _change_status(self, request, pk):
#         tx = (
#             SilverTransaction.objects
#             .select_for_update()
#             .select_related("user")
#             .get(pk=pk)
#         )

#         wallet, _ = SilverWallet.objects.select_for_update().get_or_create(user=tx.user)
#         inventory, _ = SilverInventory.objects.select_for_update().get_or_create(user=tx.user)

#         serializer = SilverTransactionStatusUpdateSerializer(data=request.data)
#         serializer.is_valid(raise_exception=True)

#         new_status = serializer.validated_data["status"]
#         description = serializer.validated_data.get("description", "")

#         old_status = tx.status

#         if old_status == new_status:
#             return error_response("وضعیت تغییری نکرده است.")

#         if old_status != "PENDING":
#             return error_response(
#                 f"تراکنشی که در وضعیت «{tx.get_status_display()}» است، قابل تغییر نیست."
#             )

#         if new_status not in ("COMPLETED", "FAILED"):
#             return error_response("وضعیت مقصد نامعتبر است.")

#         # =================================================
#         # BUY - COMPLETED
#         # =================================================
#         if tx.type == "BUY" and new_status == "COMPLETED":
#             if wallet.blocked_toman < tx.total_amount:
#                 return error_response("مغایرت در موجودی بلوکه‌شده تومانی کاربر.")

#             wallet.blocked_toman = max(0, wallet.blocked_toman - tx.total_amount)
#             wallet.save(update_fields=["blocked_toman"])

#             inventory.accessible_balance += tx.amount_gr
#             inventory.save(update_fields=["accessible_balance"])

#         # =================================================
#         # BUY - FAILED
#         # =================================================
#         elif tx.type == "BUY" and new_status == "FAILED":
#             wallet.accessible_toman += tx.total_amount
#             wallet.blocked_toman = max(0, wallet.blocked_toman - tx.total_amount)
#             wallet.save(update_fields=["accessible_toman", "blocked_toman"])

#         # =================================================
#         # SELL - COMPLETED
#         # =================================================
#         elif tx.type == "SELL" and new_status == "COMPLETED":
#             if inventory.blocked_balance < tx.amount_gr:
#                 return error_response("مغایرت در موجودی بلوکه‌شده نقره کاربر.")

#             inventory.blocked_balance = max(0, inventory.blocked_balance - tx.amount_gr)
#             inventory.save(update_fields=["blocked_balance"])

#             wallet.accessible_toman += tx.total_amount
#             wallet.save(update_fields=["accessible_toman"])

#         # =================================================
#         # SELL - FAILED
#         # =================================================
#         elif tx.type == "SELL" and new_status == "FAILED":
#             inventory.accessible_balance += tx.amount_gr
#             inventory.blocked_balance = max(0, inventory.blocked_balance - tx.amount_gr)
#             inventory.save(update_fields=["accessible_balance", "blocked_balance"])

#         # =================================================
#         # UPDATE TRANSACTION
#         # =================================================
#         tx.status = new_status
#         if description:
#             tx.description = f"{tx.description}\n{description}" if tx.description else description
#         tx.save(update_fields=["status", "description", "updated_at"])

#         create_admin_log(
#             request=request,
#             user=tx.user,
#             action_type=f"{tx.type}_SILVER_{new_status}",
#             action=f"تغییر وضعیت تراکنش نقره به {tx.get_status_display()}",
#             model_name="SilverTransaction",
#             object_id=tx.id,
#             tracking_code=tx.tracking_code,
#             success=True,
#             description=description or f"{tx.type} -> {new_status}",
#         )

#         tx.refresh_from_db()

#         return success_response(
#             "وضعیت تراکنش با موفقیت تغییر کرد.",
#             self.serializer_class(tx, context={"request": request}).data
#         )
        
        


# admin_panel/views.py - SilverTransactionAdminViewSet کامل (عین طلا)

import traceback
from decimal import Decimal
from django.db import transaction
from django.contrib.auth import get_user_model
from rest_framework.decorators import action

from accounts.utils import create_referral_profit, success_response, error_response
from silver_app.models import SilverWallet, SilverTransaction, SilverInventory
from silver_app.services.invoice_service import SilverInvoiceService
from admin_panel.serializers import SilverTransactionAdminSerializer, SilverTransactionStatusUpdateSerializer
from admin_panel.utils import create_admin_log

User = get_user_model()


class SilverTransactionAdminViewSet(AdminBaseViewSet):
    """
    ویوست مدیریت تراکنش‌های نقره برای ادمین
    """

    queryset = SilverTransaction.objects.all().order_by("-id")
    serializer_class = SilverTransactionAdminSerializer

    # =====================================================
    # QUERYSET FILTER
    # =====================================================
    def get_queryset(self):
        qs = super().get_queryset()

        search = self.request.GET.get("search")
        status = self.request.GET.get("status")
        type_ = self.request.GET.get("type")
        tracking_code = self.request.GET.get("tracking_code")
        start_date = self.request.GET.get("start_date")
        end_date = self.request.GET.get("end_date")
        ordering = self.request.GET.get("ordering")

        if search:
            qs = qs.filter(user__mobile__icontains=search)

        if status:
            qs = qs.filter(status=status)

        if type_:
            qs = qs.filter(type=type_)

        if tracking_code:
            qs = qs.filter(tracking_code__icontains=tracking_code)

        if start_date:
            qs = qs.filter(created_at__date__gte=start_date)

        if end_date:
            qs = qs.filter(created_at__date__lte=end_date)

        allowed_ordering = [
            "id", "-id",
            "created_at", "-created_at",
            "status", "-status",
            "total_amount", "-total_amount",
            "amount_gr", "-amount_gr",
        ]

        if ordering in allowed_ordering:
            qs = qs.order_by(ordering)

        return qs

    # =====================================================
    # LIST
    # =====================================================
    def list(self, request):
        qs = self.get_queryset()

        return success_response(
            "لیست تراکنش‌های نقره",
            {
                "total_results": qs.count(),
                "results": self.serializer_class(
                    qs,
                    many=True,
                    context={"request": request}
                ).data
            }
        )

    # =====================================================
    # RETRIEVE
    # =====================================================
    def retrieve(self, request, pk=None):
        obj = self.get_object()

        data = self.serializer_class(
            obj,
            context={"request": request}
        ).data

        data["created_at"] = obj.created_at.strftime("%Y-%m-%d %H:%M:%S")

        return success_response(
            "جزئیات تراکنش نقره",
            data
        )

    # =====================================================
    # PATCH
    # =====================================================
    @transaction.atomic
    def partial_update(self, request, *args, **kwargs):
        if "status" in request.data:
            result = self._change_status(request, kwargs["pk"])
            if result is None:
                return error_response("خطای داخلی در تغییر وضعیت تراکنش رخ داد.", status_code=500)
            return result

        return super().partial_update(request, *args, **kwargs)

    # =====================================================
    # UPDATE
    # =====================================================
    @transaction.atomic
    def update(self, request, *args, **kwargs):
        if "status" in request.data:
            result = self._change_status(request, kwargs["pk"])
            if result is None:
                return error_response("خطای داخلی در تغییر وضعیت تراکنش رخ داد.", status_code=500)
            return result

        return super().update(request, *args, **kwargs)

    # =====================================================
    # CHANGE STATUS (action endpoint)
    # =====================================================
    @action(detail=True, methods=["post"])
    @transaction.atomic
    def change_status(self, request, pk=None):
        result = self._change_status(request, pk)
        if result is None:
            return error_response("خطای داخلی در تغییر وضعیت تراکنش رخ داد.", status_code=500)
        return result

    # =====================================================
    # CORE BUSINESS LOGIC
    # =====================================================
    def _change_status(self, request, pk):
        try:
            tx = (
                SilverTransaction.objects
                .select_for_update()
                .select_related("user")
                .get(pk=pk)
            )
        except SilverTransaction.DoesNotExist:
            return error_response("تراکنش نقره یافت نشد", status_code=404)

        wallet, _ = SilverWallet.objects.select_for_update().get_or_create(user=tx.user)
        inventory, _ = SilverInventory.objects.select_for_update().get_or_create(user=tx.user)

        serializer = SilverTransactionStatusUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response("اطلاعات نامعتبر است", serializer.errors)

        new_status = serializer.validated_data["status"]
        description = serializer.validated_data.get("description", "")

        old_status = tx.status

        if old_status == new_status:
            return error_response("وضعیت تغییری نکرده است.")

        if old_status != "PENDING":
            return error_response(
                f"تراکنشی که در وضعیت «{tx.get_status_display()}» است، قابل تغییر نیست."
            )

        if new_status not in ("COMPLETED", "FAILED"):
            return error_response("وضعیت مقصد نامعتبر است.")

        if tx.type not in ("BUY", "SELL"):
            return error_response(f"نوع تراکنش «{tx.type}» پشتیبانی نمی‌شود.")

        invoice_obj = None

        try:
            # =================================================
            # BUY - COMPLETED ✅
            # =================================================
            if tx.type == "BUY" and new_status == "COMPLETED":
                if wallet.blocked_toman < tx.total_amount:
                    return error_response("مغایرت در موجودی بلوکه‌شده تومانی کاربر.")

                wallet.blocked_toman = max(0, wallet.blocked_toman - tx.total_amount)
                wallet.save(update_fields=["blocked_toman"])

                inventory.accessible_balance += tx.amount_gr
                inventory.save(update_fields=["accessible_balance"])

                tx.status = new_status
                if description:
                    tx.description = f"{tx.description}\n{description}" if tx.description else description
                tx.save(update_fields=["status", "description", "updated_at"])

                # ✅ رفرش کردن tx از دیتابیس
                tx.refresh_from_db()

                try:
                    invoice_obj = SilverInvoiceService.create_buy_invoice(tx, request)
                    if invoice_obj:
                        print(f"✅ فاکتور خرید نقره ایجاد شد: {invoice_obj.invoice_number}")
                except Exception:
                    print("❌ خطا در ایجاد فاکتور خرید نقره:")
                    traceback.print_exc()

            # =================================================
            # BUY - FAILED ❌
            # =================================================
            elif tx.type == "BUY" and new_status == "FAILED":
                wallet.accessible_toman += tx.total_amount
                wallet.blocked_toman = max(0, wallet.blocked_toman - tx.total_amount)
                wallet.save(update_fields=["accessible_toman", "blocked_toman"])

                tx.status = new_status
                if description:
                    tx.description = f"{tx.description}\n{description}" if tx.description else description
                tx.save(update_fields=["status", "description", "updated_at"])

            # =================================================
            # SELL - COMPLETED ✅
            # =================================================
            elif tx.type == "SELL" and new_status == "COMPLETED":
                if inventory.blocked_balance < tx.amount_gr:
                    return error_response("مغایرت در موجودی بلوکه‌شده نقره کاربر.")

                inventory.blocked_balance = max(0, inventory.blocked_balance - tx.amount_gr)
                inventory.save(update_fields=["blocked_balance"])

                wallet.accessible_toman += tx.total_amount
                wallet.save(update_fields=["accessible_toman"])

                tx.status = new_status
                if description:
                    tx.description = f"{tx.description}\n{description}" if tx.description else description
                tx.save(update_fields=["status", "description", "updated_at"])

                # ✅ رفرش کردن tx از دیتابیس
                tx.refresh_from_db()

                try:
                    invoice_obj = SilverInvoiceService.create_sell_invoice(tx, request)
                    if invoice_obj:
                        print(f"✅ فاکتور فروش نقره ایجاد شد: {invoice_obj.invoice_number}")
                except Exception:
                    print("❌ خطا در ایجاد فاکتور فروش نقره:")
                    traceback.print_exc()

            # =================================================
            # SELL - FAILED ❌
            # =================================================
            elif tx.type == "SELL" and new_status == "FAILED":
                inventory.accessible_balance += tx.amount_gr
                inventory.blocked_balance = max(0, inventory.blocked_balance - tx.amount_gr)
                inventory.save(update_fields=["accessible_balance", "blocked_balance"])

                tx.status = new_status
                if description:
                    tx.description = f"{tx.description}\n{description}" if tx.description else description
                tx.save(update_fields=["status", "description", "updated_at"])

        except Exception:
            print("❌ خطای غیرمنتظره در تغییر وضعیت تراکنش نقره:")
            traceback.print_exc()
            return error_response("خطای داخلی در پردازش تراکنش نقره رخ داد.", status_code=500)

        # =================================================
        # REGISTER ADMIN LOG
        # =================================================
        try:
            create_admin_log(
                request=request,
                user=tx.user,
                action_type=f"{tx.type}_SILVER_{new_status}",
                action=f"تغییر وضعیت تراکنش نقره به {tx.get_status_display()}",
                model_name="SilverTransaction",
                object_id=tx.id,
                tracking_code=tx.tracking_code,
                success=True,
                description=description or f"{tx.type} -> {new_status}",
            )
        except Exception:
            print("❌ خطا در ثبت لاگ ادمین:")
            traceback.print_exc()

        tx.refresh_from_db()

        response_data = self.serializer_class(tx, context={"request": request}).data

        if invoice_obj:
            response_data["invoice_id"] = invoice_obj.id
            response_data["invoice_number"] = invoice_obj.invoice_number
        else:
            response_data["invoice_id"] = None
            response_data["invoice_number"] = None

        return success_response(
            "وضعیت تراکنش با موفقیت تغییر کرد.",
            response_data
        )
# admin_panel/views.py

from silver_app.models import SilverLimitOrder
from admin_panel.serializers import SilverLimitOrderAdminSerializer
from silver_app.utils import get_live_silver_price, generate_tracking_code
# admin_panel/views.py

from gold_app.models import GoldOrder
from admin_panel.serializers import GoldLimitOrderAdminSerializer
from gold_app.utils import get_live_gold_price, generate_tracking_code


class GoldLimitOrderAdminViewSet(AdminBaseViewSet):
    """
    ویوست مدیریت سفارشات با قیمت طلا برای ادمین
    """

    queryset = GoldOrder.objects.all().order_by("-id")
    serializer_class = GoldLimitOrderAdminSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        search = self.request.GET.get("search")
        status = self.request.GET.get("status")
        type_ = self.request.GET.get("type")
        start_date = self.request.GET.get("start_date")
        end_date = self.request.GET.get("end_date")
        ordering = self.request.GET.get("ordering")

        if search:
            qs = qs.filter(user__mobile__icontains=search)
        if status:
            qs = qs.filter(status=status)
        if type_:
            qs = qs.filter(order_type=type_)
        if start_date:
            qs = qs.filter(created_at__date__gte=start_date)
        if end_date:
            qs = qs.filter(created_at__date__lte=end_date)

        allowed_ordering = [
            "id", "-id",
            "created_at", "-created_at",
            "status", "-status",
            "target_price", "-target_price",
            "estimated_weight", "-estimated_weight",
        ]
        if ordering in allowed_ordering:
            qs = qs.order_by(ordering)
        return qs

    def list(self, request):
        qs = self.get_queryset()
        return success_response(
            "لیست سفارشات با قیمت طلا",
            {
                "total_results": qs.count(),
                "results": self.serializer_class(qs, many=True, context={"request": request}).data
            }
        )

    def retrieve(self, request, pk=None):
        obj = self.get_object()
        data = self.serializer_class(obj, context={"request": request}).data
        data["created_at"] = obj.created_at.strftime("%Y-%m-%d %H:%M:%S")
        return success_response("جزئیات سفارش با قیمت طلا", data)

    @transaction.atomic
    def partial_update(self, request, *args, **kwargs):
        if "status" in request.data:
            return error_response("وضعیت سفارش از این طریق قابل تغییر نیست.")
        return super().partial_update(request, *args, **kwargs)

    @action(detail=True, methods=["post"])
    @transaction.atomic
    def cancel(self, request, pk=None):
        order = self.get_object()
        if order.status != "PENDING":
            return error_response("فقط سفارشات در وضعیت «در انتظار» قابل لغو هستند.")

        if order.order_type == "BUY":
            wallet, _ = Wallet.objects.select_for_update().get_or_create(user=order.user)
            wallet.accessible_toman += order.amount_toman
            wallet.blocked_toman -= order.amount_toman
            wallet.save(update_fields=["accessible_toman", "blocked_toman"])
        else:
            inventory, _ = GoldInventory.objects.select_for_update().get_or_create(user=order.user)
            inventory.accessible_balance += order.gold_weight
            inventory.blocked_balance -= order.gold_weight
            inventory.save(update_fields=["accessible_balance", "blocked_balance"])

        order.status = "FAILED"
        order.description = f"{order.description or ''}\nلغو شده توسط ادمین"
        order.save(update_fields=["status", "description", "updated_at"])

        return success_response(
            "سفارش با موفقیت لغو شد.",
            self.serializer_class(order, context={"request": request}).data
        )

    @action(detail=True, methods=["post"])
    @transaction.atomic
    def execute(self, request, pk=None):
        order = self.get_object()
        if order.status != "PENDING":
            return error_response("فقط سفارشات در وضعیت «در انتظار» قابل اجرا هستند.")

        current_price = get_live_gold_price()
        if not current_price:
            return error_response("خطا در دریافت قیمت لحظه‌ای طلا")

        current_price = Decimal(str(current_price))

        if order.order_type == "BUY" and current_price > order.target_price:
            return error_response(
                f"قیمت فعلی ({current_price:,}) بیشتر از قیمت هدف ({order.target_price:,}) است. قابل اجرا نیست."
            )
        if order.order_type == "SELL" and current_price < order.target_price:
            return error_response(
                f"قیمت فعلی ({current_price:,}) کمتر از قیمت هدف ({order.target_price:,}) است. قابل اجرا نیست."
            )

        if order.order_type == "BUY":
            wallet, _ = Wallet.objects.select_for_update().get_or_create(user=order.user)
            inventory, _ = GoldInventory.objects.select_for_update().get_or_create(user=order.user)

            fee_rate = Decimal(str(order.fee_rate))
            pure_price = (order.amount_toman / (Decimal("1") + fee_rate)).quantize(Decimal("1"))
            fee = (order.amount_toman - pure_price).quantize(Decimal("1"))
            weight = (pure_price / current_price).quantize(Decimal("0.001"), rounding=ROUND_DOWN)

            if wallet.blocked_toman < order.amount_toman:
                return error_response("مغایرت در موجودی بلوکه شده")

            wallet.blocked_toman -= order.amount_toman
            wallet.save(update_fields=["blocked_toman"])

            inventory.accessible_balance += weight
            inventory.save(update_fields=["accessible_balance"])

            GoldTransaction.objects.create(
                user=order.user,
                type="BUY",
                status="COMPLETED",
                amount_gr=weight,
                price_per_gram=current_price,
                fee=fee,
                commission_percent=fee_rate * 100,
                commission_amount=fee,
                total_amount=order.amount_toman,
                tracking_code=generate_tracking_code("BUY"),
                description=f"اجرای دستی توسط ادمین - قیمت هدف {order.target_price}"
            )

            try:
                from accounts.utils import create_referral_profit
                create_referral_profit(
                    user=order.user,
                    source_type="GOLD",
                    transaction_amount=order.amount_toman,
                )
            except Exception as e:
                print(f"❌ خطا در ایجاد پاداش معرفی: {e}")

        else:
            wallet, _ = Wallet.objects.select_for_update().get_or_create(user=order.user)
            inventory, _ = GoldInventory.objects.select_for_update().get_or_create(user=order.user)

            fee_rate = Decimal(str(order.fee_rate))
            pure_price = (current_price * order.gold_weight).quantize(Decimal("1"))
            fee = (pure_price * fee_rate).quantize(Decimal("1"))
            total_price = (pure_price - fee).quantize(Decimal("1"))

            if inventory.blocked_balance < order.gold_weight:
                return error_response("مغایرت در موجودی بلوکه شده طلا")

            inventory.blocked_balance -= order.gold_weight
            inventory.save(update_fields=["blocked_balance"])

            wallet.accessible_toman += total_price
            wallet.save(update_fields=["accessible_toman"])

            GoldTransaction.objects.create(
                user=order.user,
                type="SELL",
                status="COMPLETED",
                amount_gr=order.gold_weight,
                price_per_gram=current_price,
                fee=fee,
                commission_percent=fee_rate * 100,
                commission_amount=fee,
                total_amount=total_price,
                tracking_code=generate_tracking_code("SELL"),
                description=f"اجرای دستی توسط ادمین - قیمت هدف {order.target_price}"
            )

        order.status = "COMPLETED"
        order.executed_price = current_price
        order.save(update_fields=["status", "executed_price", "updated_at"])

        create_admin_log(
            request=request,
            user=order.user,
            action_type="GOLD_LIMIT_EXECUTE",
            action="اجرای دستی سفارش با قیمت طلا توسط ادمین",
            model_name="GoldOrder",
            object_id=order.id,
            success=True,
            description=f"""
اجرای دستی سفارش با قیمت طلا توسط ادمین
کاربر: {order.user.mobile}
نوع سفارش: {order.get_order_type_display()}
قیمت هدف: {order.target_price:,}
قیمت اجرا: {current_price:,}
وزن: {order.estimated_weight} گرم
""",
        )

        return success_response(
            "سفارش با موفقیت اجرا شد.",
            self.serializer_class(order, context={"request": request}).data
        )


class SilverLimitOrderAdminViewSet(AdminBaseViewSet):
    """
    ویوست مدیریت سفارشات با قیمت نقره برای ادمین
    """

    queryset = SilverLimitOrder.objects.all().order_by("-id")
    serializer_class = SilverLimitOrderAdminSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        search = self.request.GET.get("search")
        status = self.request.GET.get("status")
        type_ = self.request.GET.get("type")
        start_date = self.request.GET.get("start_date")
        end_date = self.request.GET.get("end_date")
        ordering = self.request.GET.get("ordering")

        if search:
            qs = qs.filter(user__mobile__icontains=search)
        if status:
            qs = qs.filter(status=status)
        if type_:
            qs = qs.filter(order_type=type_)
        if start_date:
            qs = qs.filter(created_at__date__gte=start_date)
        if end_date:
            qs = qs.filter(created_at__date__lte=end_date)

        allowed_ordering = [
            "id", "-id",
            "created_at", "-created_at",
            "status", "-status",
            "target_price", "-target_price",
            "estimated_weight", "-estimated_weight",
        ]
        if ordering in allowed_ordering:
            qs = qs.order_by(ordering)
        return qs

    def list(self, request):
        qs = self.get_queryset()
        return success_response(
            "لیست سفارشات با قیمت نقره",
            {
                "total_results": qs.count(),
                "results": self.serializer_class(qs, many=True, context={"request": request}).data
            }
        )

    def retrieve(self, request, pk=None):
        obj = self.get_object()
        data = self.serializer_class(obj, context={"request": request}).data
        data["created_at"] = obj.created_at.strftime("%Y-%m-%d %H:%M:%S")
        return success_response("جزئیات سفارش با قیمت نقره", data)

    @transaction.atomic
    def partial_update(self, request, *args, **kwargs):
        if "status" in request.data:
            return error_response("وضعیت سفارش از این طریق قابل تغییر نیست.")
        return super().partial_update(request, *args, **kwargs)

    @action(detail=True, methods=["post"])
    @transaction.atomic
    def cancel(self, request, pk=None):
        order = self.get_object()
        if order.status != "PENDING":
            return error_response("فقط سفارشات در وضعیت «در انتظار» قابل لغو هستند.")

        if order.order_type == "BUY":
            wallet, _ = SilverWallet.objects.select_for_update().get_or_create(user=order.user)
            wallet.accessible_toman += order.amount_toman
            wallet.blocked_toman -= order.amount_toman
            wallet.save(update_fields=["accessible_toman", "blocked_toman"])
        else:
            inventory, _ = SilverInventory.objects.select_for_update().get_or_create(user=order.user)
            inventory.accessible_balance += order.silver_weight
            inventory.blocked_balance -= order.silver_weight
            inventory.save(update_fields=["accessible_balance", "blocked_balance"])

        order.status = "FAILED"
        order.description = f"{order.description or ''}\nلغو شده توسط ادمین"
        order.save(update_fields=["status", "description", "updated_at"])

        return success_response(
            "سفارش با موفقیت لغو شد.",
            self.serializer_class(order, context={"request": request}).data
        )

    @action(detail=True, methods=["post"])
    @transaction.atomic
    def execute(self, request, pk=None):
        order = self.get_object()
        if order.status != "PENDING":
            return error_response("فقط سفارشات در وضعیت «در انتظار» قابل اجرا هستند.")

        current_price = get_live_silver_price()
        if not current_price:
            return error_response("خطا در دریافت قیمت لحظه‌ای نقره")

        current_price = Decimal(str(current_price))

        if order.order_type == "BUY" and current_price > order.target_price:
            return error_response(
                f"قیمت فعلی ({current_price:,}) بیشتر از قیمت هدف ({order.target_price:,}) است. قابل اجرا نیست."
            )
        if order.order_type == "SELL" and current_price < order.target_price:
            return error_response(
                f"قیمت فعلی ({current_price:,}) کمتر از قیمت هدف ({order.target_price:,}) است. قابل اجرا نیست."
            )

        if order.order_type == "BUY":
            wallet, _ = SilverWallet.objects.select_for_update().get_or_create(user=order.user)
            inventory, _ = SilverInventory.objects.select_for_update().get_or_create(user=order.user)

            fee_rate = Decimal(str(order.fee_rate))
            pure_price = (order.amount_toman / (Decimal("1") + fee_rate)).quantize(Decimal("1"))
            fee = (order.amount_toman - pure_price).quantize(Decimal("1"))
            weight = (pure_price / current_price).quantize(Decimal("0.001"), rounding=ROUND_DOWN)

            if wallet.blocked_toman < order.amount_toman:
                return error_response("مغایرت در موجودی بلوکه شده")

            wallet.blocked_toman -= order.amount_toman
            wallet.save(update_fields=["blocked_toman"])

            inventory.accessible_balance += weight
            inventory.save(update_fields=["accessible_balance"])

            SilverTransaction.objects.create(
                user=order.user,
                type="BUY",
                status="COMPLETED",
                amount_gr=weight,
                price_per_gram=current_price,
                fee=fee,
                commission_percent=fee_rate * 100,
                commission_amount=fee,
                total_amount=order.amount_toman,
                tracking_code=generate_tracking_code("BUY"),
                description=f"اجرای دستی توسط ادمین - قیمت هدف {order.target_price}"
            )

        else:
            wallet, _ = SilverWallet.objects.select_for_update().get_or_create(user=order.user)
            inventory, _ = SilverInventory.objects.select_for_update().get_or_create(user=order.user)

            fee_rate = Decimal(str(order.fee_rate))
            pure_price = (current_price * order.silver_weight).quantize(Decimal("1"))
            fee = (pure_price * fee_rate).quantize(Decimal("1"))
            total_price = (pure_price - fee).quantize(Decimal("1"))

            if inventory.blocked_balance < order.silver_weight:
                return error_response("مغایرت در موجودی بلوکه شده نقره")

            inventory.blocked_balance -= order.silver_weight
            inventory.save(update_fields=["blocked_balance"])

            wallet.accessible_toman += total_price
            wallet.save(update_fields=["accessible_toman"])

            SilverTransaction.objects.create(
                user=order.user,
                type="SELL",
                status="COMPLETED",
                amount_gr=order.silver_weight,
                price_per_gram=current_price,
                fee=fee,
                commission_percent=fee_rate * 100,
                commission_amount=fee,
                total_amount=total_price,
                tracking_code=generate_tracking_code("SELL"),
                description=f"اجرای دستی توسط ادمین - قیمت هدف {order.target_price}"
            )

        order.status = "COMPLETED"
        order.executed_price = current_price
        order.save(update_fields=["status", "executed_price", "updated_at"])

        create_admin_log(
            request=request,
            user=order.user,
            action_type="SILVER_LIMIT_EXECUTE",
            action="اجرای دستی سفارش با قیمت نقره توسط ادمین",
            model_name="SilverLimitOrder",
            object_id=order.id,
            success=True,
            description=f"""
اجرای دستی سفارش با قیمت نقره توسط ادمین
کاربر: {order.user.mobile}
نوع سفارش: {order.get_order_type_display()}
قیمت هدف: {order.target_price:,}
قیمت اجرا: {current_price:,}
وزن: {order.estimated_weight} گرم
""",
        )

        return success_response(
            "سفارش با موفقیت اجرا شد.",
            self.serializer_class(order, context={"request": request}).data
        )
        
        
# admin_panel/views.py - اضافه کردن ویوهای تیکت ادمین

from accounts.models import Ticket, TicketCategory, TicketMessage
from admin_panel.serializers import (
    TicketCategoryAdminSerializer,
    TicketAdminListSerializer,
    TicketAdminDetailSerializer,
    TicketStatusUpdateAdminSerializer,
    TicketMessageCreateAdminSerializer,
    TicketMessageAdminSerializer,
    TicketStatisticsAdminSerializer,
)
from accounts.utils import success_response, error_response
from admin_panel.utils import create_admin_log


# admin_panel/views.py - اصلاح TicketCategoryAdminViewSet

class TicketCategoryAdminViewSet(AdminBaseViewSet):
    """
    ویوست مدیریت دسته‌بندی‌های تیکت برای ادمین
    """

    queryset = TicketCategory.objects.all().order_by('name')
    serializer_class = TicketCategoryAdminSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        search = self.request.GET.get('search')
        is_active = self.request.GET.get('is_active')

        if search:
            qs = qs.filter(name__icontains=search)
        if is_active is not None:
            qs = qs.filter(is_active=is_active == 'true')

        return qs

    def list(self, request):
        qs = self.get_queryset()
        return success_response(
            "لیست دسته‌بندی‌های تیکت",
            {
                "total_results": qs.count(),
                "results": self.serializer_class(qs, many=True, context={"request": request}).data
            }
        )

    def create(self, request):
        # اگر slug ارسال نشده، از name تولید کن
        if 'slug' not in request.data or not request.data.get('slug'):
            name = request.data.get('name', '')
            if name:
                from django.utils.text import slugify
                request.data['slug'] = slugify(name)
        
        serializer = self.serializer_class(data=request.data)
        if not serializer.is_valid():
            return error_response("اطلاعات نامعتبر است", serializer.errors)

        category = serializer.save()

        create_admin_log(
            request=request,
            user=request.user,
            action_type="TICKET_CATEGORY_CREATED",
            action="ایجاد دسته‌بندی تیکت",
            model_name="TicketCategory",
            object_id=category.id,
            success=True,
            description=f"""
دسته‌بندی تیکت جدید ایجاد شد

نام: {category.name}
شناسه: {category.slug}
"""
        )

        return success_response(
            "دسته‌بندی با موفقیت ایجاد شد",
            self.serializer_class(category, context={"request": request}).data,
            status_code=201
        )

    def update(self, request, pk=None, partial=False):  # ✅ اضافه کردن partial
        """
        بروزرسانی کامل دسته‌بندی
        """
        category = self.get_object()
        serializer = self.serializer_class(category, data=request.data, partial=partial)
        
        if not serializer.is_valid():
            return error_response("اطلاعات نامعتبر است", serializer.errors)

        category = serializer.save()

        create_admin_log(
            request=request,
            user=request.user,
            action_type="TICKET_CATEGORY_UPDATED",
            action="بروزرسانی دسته‌بندی تیکت",
            model_name="TicketCategory",
            object_id=category.id,
            success=True,
            description=f"""
دسته‌بندی تیکت بروزرسانی شد

نام: {category.name}
شناسه: {category.slug}
"""
        )

        return success_response(
            "دسته‌بندی با موفقیت بروزرسانی شد",
            self.serializer_class(category, context={"request": request}).data
        )

    def partial_update(self, request, pk=None):  # ✅ اضافه کردن متد partial_update
        """
        بروزرسانی جزئی دسته‌بندی
        """
        return self.update(request, pk=pk, partial=True)

    def destroy(self, request, pk=None):
        category = self.get_object()
        
        # بررسی وجود تیکت‌های فعال
        if category.tickets.filter(status__in=['open', 'pending', 'answered', 'in_progress']).exists():
            return error_response(
                "این دسته‌بندی دارای تیکت‌های فعال است. ابتدا تیکت‌ها را منتقل یا ببندید.",
                status_code=400
            )
        
        category.delete()

        create_admin_log(
            request=request,
            user=request.user,
            action_type="TICKET_CATEGORY_DELETED",
            action="حذف دسته‌بندی تیکت",
            model_name="TicketCategory",
            object_id=category.id,
            success=True,
            description=f"""
دسته‌بندی تیکت حذف شد

نام: {category.name}
شناسه: {category.slug}
"""
        )

        return success_response("دسته‌بندی با موفقیت حذف شد")

class TicketAdminViewSet(AdminBaseViewSet):
    """
    ویوست مدیریت تیکت‌ها برای ادمین
    """

    queryset = Ticket.objects.all().order_by('-id')
    serializer_class = TicketAdminListSerializer

    def get_queryset(self):
        qs = super().get_queryset()

        search = self.request.GET.get('search')
        status = self.request.GET.get('status')
        priority = self.request.GET.get('priority')
        category = self.request.GET.get('category')
        tracking_code = self.request.GET.get('tracking_code')
        start_date = self.request.GET.get('start_date')
        end_date = self.request.GET.get('end_date')
        ordering = self.request.GET.get('ordering')
        has_unread = self.request.GET.get('has_unread')

        if search:
            qs = qs.filter(
                Q(title__icontains=search) |
                Q(tracking_code__icontains=search) |
                Q(user__mobile__icontains=search) |
                Q(user__first_name__icontains=search) |
                Q(user__last_name__icontains=search)
            )

        if status:
            qs = qs.filter(status=status)

        if priority:
            qs = qs.filter(priority=priority)

        if category:
            qs = qs.filter(category_id=category)

        if tracking_code:
            qs = qs.filter(tracking_code__icontains=tracking_code)

        if start_date:
            qs = qs.filter(created_at__date__gte=start_date)

        if end_date:
            qs = qs.filter(created_at__date__lte=end_date)

        if has_unread == 'true':
            qs = qs.filter(messages__is_admin=False, messages__is_read=False).distinct()

        allowed_ordering = [
            'id', '-id',
            'created_at', '-created_at',
            'updated_at', '-updated_at',
            'last_activity_at', '-last_activity_at',
            'status', '-status',
            'priority', '-priority'
        ]
        if ordering in allowed_ordering:
            qs = qs.order_by(ordering)

        return qs

    def list(self, request):
        qs = self.get_queryset()
        return success_response(
            "لیست تیکت‌ها",
            {
                "total_results": qs.count(),
                "results": TicketAdminListSerializer(
                    qs,
                    many=True,
                    context={"request": request}
                ).data
            }
        )

    def retrieve(self, request, pk=None):
        obj = self.get_object()

        # علامت‌گذاری پیام‌های کاربر به عنوان خوانده شده
        TicketMessage.objects.filter(
            ticket=obj,
            is_admin=False,
            is_read=False
        ).update(is_read=True, read_at=timezone.now())

        data = TicketAdminDetailSerializer(
            obj,
            context={"request": request}
        ).data

        return success_response("جزئیات تیکت", data)

    @transaction.atomic
    def partial_update(self, request, *args, **kwargs):
        if "status" in request.data:
            return self._change_status(request, kwargs["pk"])
        return super().partial_update(request, *args, **kwargs)

    @action(detail=True, methods=["post"])
    @transaction.atomic
    def change_status(self, request, pk=None):
        return self._change_status(request, pk)

    def _change_status(self, request, pk):
        ticket = self.get_object()

        serializer = TicketStatusUpdateAdminSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response("اطلاعات نامعتبر است", serializer.errors)

        new_status = serializer.validated_data["status"]
        description = serializer.validated_data.get("description", "")

        old_status = ticket.status

        if old_status == new_status:
            return error_response("وضعیت تغییری نکرده است.")

        # اگر تیکت بسته یا حل شده باشد، قابل تغییر نیست
        if old_status in ['closed', 'resolved']:
            return error_response(
                f"تیکتی که در وضعیت «{ticket.get_status_display()}» است، قابل تغییر نیست."
            )

        # =================================================
        # تغییر وضعیت
        # =================================================
        ticket.status = new_status
        
        if new_status == 'resolved':
            ticket.resolved_at = timezone.now()
        
        if new_status == 'closed':
            ticket.closed_at = timezone.now()
            ticket.closed_by = request.user

        if description:
            ticket.description = f"{ticket.description}\n\nتغییر وضعیت توسط ادمین:\n{description}" if ticket.description else description

        ticket.save()

        # ثبت لاگ
        create_admin_log(
            request=request,
            user=ticket.user,
            action_type="TICKET_STATUS_CHANGED",
            action=f"تغییر وضعیت تیکت به {ticket.get_status_display()}",
            model_name="Ticket",
            object_id=ticket.id,
            tracking_code=ticket.tracking_code,
            success=True,
            description=f"""
تغییر وضعیت تیکت توسط ادمین

کد رهگیری: {ticket.tracking_code}
عنوان: {ticket.title}
کاربر: {ticket.user.mobile}
وضعیت قبلی: {ticket.get_status_display()}
وضعیت جدید: {ticket.get_status_display()}
توضیحات: {description or 'بدون توضیحات'}
"""
        )

        return success_response(
            "وضعیت تیکت با موفقیت تغییر کرد.",
            TicketAdminDetailSerializer(ticket, context={"request": request}).data
        )

    @action(detail=True, methods=["post"])
    @transaction.atomic
    def assign_to_me(self, request, pk=None):
        """اختصاص تیکت به ادمین فعلی"""
        ticket = self.get_object()

        if ticket.status in ['closed', 'resolved']:
            return error_response("تیکت بسته یا حل شده است.")

        ticket.status = 'in_progress'
        ticket.save()

        create_admin_log(
            request=request,
            action_type="TICKET_ASSIGNED",
            action="اختصاص تیکت به ادمین",
            model_name="Ticket",
            object_id=ticket.id,
            tracking_code=ticket.tracking_code,
            success=True,
            description=f"""
تیکت به ادمین اختصاص داده شد

کد رهگیری: {ticket.tracking_code}
عنوان: {ticket.title}
کاربر: {ticket.user.mobile}
ادمین: {request.user.mobile}
"""
        )

        return success_response(
            "تیکت با موفقیت به شما اختصاص داده شد.",
            TicketAdminDetailSerializer(ticket, context={"request": request}).data
        )


class TicketMessageAdminViewSet(AdminBaseViewSet):
    """
    ویوست مدیریت پیام‌های تیکت برای ادمین
    """

    queryset = TicketMessage.objects.all().order_by('created_at')
    serializer_class = TicketMessageAdminSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        ticket_id = self.request.GET.get('ticket')
        if ticket_id:
            qs = qs.filter(ticket_id=ticket_id)
        return qs

    def list(self, request):
        qs = self.get_queryset()
        return success_response(
            "لیست پیام‌های تیکت",
            {
                "total_results": qs.count(),
                "results": self.serializer_class(qs, many=True, context={"request": request}).data
            }
        )

    @transaction.atomic
    def create(self, request):
        """ارسال پیام جدید توسط ادمین"""
        ticket_id = request.data.get('ticket')
        if not ticket_id:
            return error_response("شناسه تیکت الزامی است")

        try:
            ticket = Ticket.objects.get(id=ticket_id)
        except Ticket.DoesNotExist:
            return error_response("تیکت یافت نشد", status_code=404)

        if ticket.status in ['closed', 'resolved']:
            return error_response("تیکت بسته یا حل شده است. نمی‌توان پیام ارسال کرد.")

        serializer = TicketMessageCreateAdminSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response("اطلاعات نامعتبر است", serializer.errors)

        message = TicketMessage.objects.create(
            ticket=ticket,
            user=request.user,
            message=serializer.validated_data['message'],
            attachment=serializer.validated_data.get('attachment'),
            is_admin=True
        )

        # اگر تیکت در وضعیت pending یا open بود، به answered تغییر کن
        if ticket.status in ['pending', 'open']:
            ticket.status = 'answered'
            ticket.save()

        create_admin_log(
            request=request,
            action_type="TICKET_ADMIN_MESSAGE",
            action="ارسال پیام توسط ادمین در تیکت",
            model_name="TicketMessage",
            object_id=message.id,
            tracking_code=ticket.tracking_code,
            success=True,
            description=f"""
پیام جدید توسط ادمین ارسال شد

کد رهگیری: {ticket.tracking_code}
عنوان: {ticket.title}
کاربر: {ticket.user.mobile}
ادمین: {request.user.mobile}
"""
        )

        return success_response(
            "پیام با موفقیت ارسال شد",
            TicketMessageAdminSerializer(message, context={"request": request}).data,
            status_code=201
        )


class TicketStatisticsAdminView(APIView):
    """
    دریافت آمار تیکت‌ها برای داشبورد ادمین
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        status_counts = {}
        total = Ticket.objects.count()

        for status, label in Ticket.STATUS_CHOICES:
            status_counts[status] = Ticket.objects.filter(status=status).count()

        # تعداد پیام‌های خوانده نشده برای ادمین
        unread_admin = TicketMessage.objects.filter(
            is_admin=False,
            is_read=False
        ).count()

        data = {
            'total': total,
            'open': status_counts.get('open', 0),
            'pending': status_counts.get('pending', 0),
            'answered': status_counts.get('answered', 0),
            'in_progress': status_counts.get('in_progress', 0),
            'resolved': status_counts.get('resolved', 0),
            'closed': status_counts.get('closed', 0),
            'unread_admin': unread_admin,
        }

        return success_response("آمار تیکت‌ها", data)
    
    
# admin_panel/views.py - اضافه کردن ویوهای تضمین طلا

from gold_app.models import GoldGuarantee, GoldGuaranteePlan, GoldInventory, Wallet
from admin_panel.serializers import (
    GoldGuaranteePlanAdminSerializer,
    GoldGuaranteeAdminListSerializer,
    GoldGuaranteeAdminDetailSerializer,
    GoldGuaranteeStatusUpdateAdminSerializer,
    GoldGuaranteeStatisticsAdminSerializer,
)
from gold_app.utils import get_live_gold_price
from accounts.utils import success_response, error_response
from admin_panel.utils import create_admin_log


# admin_panel/views.py - اصلاح GoldGuaranteePlanAdminViewSet

class GoldGuaranteePlanAdminViewSet(AdminBaseViewSet):
    """
    ویوست مدیریت طرح‌های تضمین طلا برای ادمین
    """

    queryset = GoldGuaranteePlan.objects.all().order_by('duration_days')
    serializer_class = GoldGuaranteePlanAdminSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        search = self.request.GET.get('search')
        is_active = self.request.GET.get('is_active')

        if search:
            qs = qs.filter(name__icontains=search)
        if is_active is not None:
            qs = qs.filter(is_active=is_active == 'true')

        return qs

    def list(self, request):
        qs = self.get_queryset()
        return success_response(
            "لیست طرح‌های تضمین طلا",
            {
                "total_results": qs.count(),
                "results": self.serializer_class(qs, many=True, context={"request": request}).data
            }
        )

    def create(self, request):
        serializer = self.serializer_class(data=request.data)
        if not serializer.is_valid():
            return error_response("اطلاعات نامعتبر است", serializer.errors)

        plan = serializer.save()

        create_admin_log(
            request=request,
            user=request.user,
            action_type="GUARANTEE_PLAN_CREATED",
            action="ایجاد طرح تضمین طلا",
            model_name="GoldGuaranteePlan",
            object_id=plan.id,
            success=True,
            description=f"""
طرح تضمین طلا جدید ایجاد شد

نام: {plan.name}
مدت: {plan.duration_days} روز
کارمزد: {plan.service_fee_percent}%
"""
        )

        return success_response(
            "طرح تضمین با موفقیت ایجاد شد",
            self.serializer_class(plan, context={"request": request}).data,
            status_code=201
        )

    # ✅ اصلاح: اضافه کردن پارامتر partial
    def update(self, request, pk=None, partial=False):
        plan = self.get_object()
        serializer = self.serializer_class(plan, data=request.data, partial=partial)
        if not serializer.is_valid():
            return error_response("اطلاعات نامعتبر است", serializer.errors)

        serializer.save()

        create_admin_log(
            request=request,
            user=request.user,
            action_type="GUARANTEE_PLAN_UPDATED",
            action="بروزرسانی طرح تضمین طلا",
            model_name="GoldGuaranteePlan",
            object_id=plan.id,
            success=True,
            description=f"""
طرح تضمین طلا بروزرسانی شد

نام: {plan.name}
مدت: {plan.duration_days} روز
کارمزد: {plan.service_fee_percent}%
"""
        )

        return success_response(
            "طرح تضمین با موفقیت بروزرسانی شد",
            self.serializer_class(plan, context={"request": request}).data
        )

    # ✅ اضافه کردن متد partial_update برای پشتیبانی از PATCH
    def partial_update(self, request, pk=None):
        """به‌روزرسانی جزئی طرح تضمین طلا (PATCH)"""
        return self.update(request, pk, partial=True)

    def destroy(self, request, pk=None):
        plan = self.get_object()
        
        # بررسی وجود تضمین‌های فعال
        if plan.guarantees.filter(status='ACTIVE').exists():
            return error_response(
                "این طرح دارای تضمین‌های فعال است. ابتدا آن‌ها را مدیریت کنید.",
                status_code=400
            )
        
        plan.delete()

        create_admin_log(
            request=request,
            user=request.user,
            action_type="GUARANTEE_PLAN_DELETED",
            action="حذف طرح تضمین طلا",
            model_name="GoldGuaranteePlan",
            object_id=plan.id,
            success=True,
            description=f"""
طرح تضمین طلا حذف شد

نام: {plan.name}
"""
        )

        return success_response("طرح تضمین با موفقیت حذف شد")
    
    
class GoldGuaranteeAdminViewSet(AdminBaseViewSet):
    """
    ویوست مدیریت تضمین‌های طلا برای ادمین
    """

    queryset = GoldGuarantee.objects.all().order_by('-id')
    serializer_class = GoldGuaranteeAdminListSerializer

    def get_queryset(self):
        qs = super().get_queryset()

        search = self.request.GET.get('search')
        status = self.request.GET.get('status')
        plan = self.request.GET.get('plan')
        user_id = self.request.GET.get('user_id')
        start_date = self.request.GET.get('start_date')
        end_date = self.request.GET.get('end_date')
        ordering = self.request.GET.get('ordering')

        if search:
            qs = qs.filter(
                Q(user__mobile__icontains=search) |
                Q(user__first_name__icontains=search) |
                Q(user__last_name__icontains=search) |
                Q(plan__name__icontains=search)
            )

        if status:
            qs = qs.filter(status=status)

        if plan:
            qs = qs.filter(plan_id=plan)

        if user_id:
            qs = qs.filter(user_id=user_id)

        if start_date:
            qs = qs.filter(created_at__date__gte=start_date)

        if end_date:
            qs = qs.filter(created_at__date__lte=end_date)

        allowed_ordering = [
            'id', '-id',
            'created_at', '-created_at',
            'end_date', '-end_date',
            'status', '-status',
            'gold_weight', '-gold_weight',
            'service_fee', '-service_fee'
        ]
        if ordering in allowed_ordering:
            qs = qs.order_by(ordering)

        return qs

    def list(self, request):
        qs = self.get_queryset()
        return success_response(
            "لیست تضمین‌های طلا",
            {
                "total_results": qs.count(),
                "results": GoldGuaranteeAdminListSerializer(
                    qs,
                    many=True,
                    context={"request": request}
                ).data
            }
        )

    def retrieve(self, request, pk=None):
        obj = self.get_object()
        data = GoldGuaranteeAdminDetailSerializer(
            obj,
            context={"request": request}
        ).data
        return success_response("جزئیات تضمین طلا", data)

    @transaction.atomic
    def partial_update(self, request, *args, **kwargs):
        if "status" in request.data:
            return self._change_status(request, kwargs["pk"])
        return super().partial_update(request, *args, **kwargs)

    @action(detail=True, methods=["post"])
    @transaction.atomic
    def change_status(self, request, pk=None):
        return self._change_status(request, pk)

    def _change_status(self, request, pk):
        guarantee = self.get_object()

        serializer = GoldGuaranteeStatusUpdateAdminSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response("اطلاعات نامعتبر است", serializer.errors)

        new_status = serializer.validated_data["status"]
        description = serializer.validated_data.get("description", "")

        old_status = guarantee.status

        if old_status == new_status:
            return error_response("وضعیت تغییری نکرده است.")

        # فقط طرح‌های فعال قابل تغییر هستند
        if old_status != 'ACTIVE':
            return error_response(
                f"تضمینی که در وضعیت «{guarantee.get_status_display()}» است، قابل تغییر نیست."
            )

        # =================================================
        # تغییر وضعیت به CANCELLED
        # =================================================
        if new_status == 'CANCELLED':
            guarantee.status = 'CANCELLED'
            guarantee.cancelled_at = timezone.now()
            guarantee.save()

            # برگرداندن طلای بلوکه شده
            inventory, _ = GoldInventory.objects.select_for_update().get_or_create(user=guarantee.user)
            inventory.blocked_balance -= guarantee.gold_weight
            inventory.accessible_balance += guarantee.gold_weight
            inventory.save()

            # کارمزد برگشت داده نمی‌شود

        # =================================================
        # تغییر وضعیت به EXPIRED (منقضی شده توسط ادمین)
        # =================================================
        elif new_status == 'EXPIRED':
            guarantee.status = 'EXPIRED'
            guarantee.save()

            # برگرداندن طلای بلوکه شده
            inventory, _ = GoldInventory.objects.select_for_update().get_or_create(user=guarantee.user)
            inventory.blocked_balance -= guarantee.gold_weight
            inventory.accessible_balance += guarantee.gold_weight
            inventory.save()

        if description:
            guarantee.description = f"{guarantee.description}\n\nتغییر وضعیت توسط ادمین:\n{description}" if guarantee.description else description
            guarantee.save()

        # ثبت لاگ
        create_admin_log(
            request=request,
            user=guarantee.user,
            action_type="GUARANTEE_STATUS_CHANGED",
            action=f"تغییر وضعیت تضمین طلا به {guarantee.get_status_display()}",
            model_name="GoldGuarantee",
            object_id=guarantee.id,
            success=True,
            description=f"""
تغییر وضعیت تضمین طلا توسط ادمین

کاربر: {guarantee.user.mobile}
وزن طلا: {guarantee.gold_weight} گرم
وضعیت قبلی: {old_status}
وضعیت جدید: {new_status}
توضیحات: {description or 'بدون توضیحات'}
"""
        )

        return success_response(
            "وضعیت تضمین با موفقیت تغییر کرد.",
            GoldGuaranteeAdminDetailSerializer(guarantee, context={"request": request}).data
        )

    @action(detail=True, methods=["post"])
    @transaction.atomic
    def force_expire(self, request, pk=None):
        """
        انقضای اجباری تضمین (برای موارد خاص)
        """
        guarantee = self.get_object()

        if guarantee.status != 'ACTIVE':
            return error_response("فقط تضمین‌های فعال قابل انقضای اجباری هستند.")

        guarantee.status = 'EXPIRED'
        guarantee.save()

        # برگرداندن طلای بلوکه شده
        inventory, _ = GoldInventory.objects.select_for_update().get_or_create(user=guarantee.user)
        inventory.blocked_balance -= guarantee.gold_weight
        inventory.accessible_balance += guarantee.gold_weight
        inventory.save()

        create_admin_log(
            request=request,
            user=guarantee.user,
            action_type="GUARANTEE_FORCE_EXPIRE",
            action="انقضای اجباری تضمین طلا",
            model_name="GoldGuarantee",
            object_id=guarantee.id,
            success=True,
            description=f"""
انقضای اجباری تضمین طلا توسط ادمین

کاربر: {guarantee.user.mobile}
وزن طلا: {guarantee.gold_weight} گرم
قیمت تضمین: {guarantee.guaranteed_price:,}
کارمزد پرداخت شده: {guarantee.service_fee:,}
"""
        )

        return success_response(
            "تضمین با موفقیت منقضی شد.",
            GoldGuaranteeAdminDetailSerializer(guarantee, context={"request": request}).data
        )

# admin_panel/views.py - اصلاح GoldGuaranteeStatisticsAdminView

class GoldGuaranteeStatisticsAdminView(APIView):
    """
    دریافت آمار تضمین‌های طلا برای داشبورد ادمین
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        status_counts = {}
        total = GoldGuarantee.objects.count()

        for status, label in GoldGuarantee.STATUS_CHOICES:
            status_counts[status] = GoldGuarantee.objects.filter(status=status).count()

        # مجموع وزن طلای تضمین شده
        total_gold_weight = GoldGuarantee.objects.filter(status='ACTIVE').aggregate(
            total=models.Sum('gold_weight')
        )['total'] or 0

        # مجموع کارمزدهای دریافت شده
        total_service_fee = GoldGuarantee.objects.aggregate(
            total=models.Sum('service_fee')
        )['total'] or 0

        # مجموع سود/ضررهای اجرا شده
        total_profit_loss = GoldGuarantee.objects.filter(status='EXECUTED').aggregate(
            total=models.Sum('profit_loss')
        )['total'] or 0

        # ✅ مجموع سود پلتفرم
        total_platform_profit = GoldGuarantee.objects.filter(status='EXECUTED').aggregate(
            total=models.Sum('platform_profit')
        )['total'] or 0

        # ✅ مجموع مبلغ پرداختی به کاربران
        total_user_payout = GoldGuarantee.objects.filter(status='EXECUTED').aggregate(
            total=models.Sum('user_payout')
        )['total'] or 0

        # تعداد طرح‌های فعال
        plans_count = GoldGuaranteePlan.objects.filter(is_active=True).count()

        data = {
            'total': total,
            'active': status_counts.get('ACTIVE', 0),
            'expired': status_counts.get('EXPIRED', 0),
            'cancelled': status_counts.get('CANCELLED', 0),
            'executed': status_counts.get('EXECUTED', 0),
            'total_gold_weight': float(total_gold_weight),
            'total_service_fee': float(total_service_fee),
            'total_profit_loss': float(total_profit_loss),
            'total_platform_profit': float(total_platform_profit),      # ✅ اضافه شد
            'total_user_payout': float(total_user_payout),              # ✅ اضافه شد
            'plans_count': plans_count,
        }

        return success_response("آمار تضمین‌های طلا", data)
    


# admin_panel/views.py - اضافه کردن ویوهای سرمایه‌گذاری


# admin_panel/views.py - اصلاح GoldInvestmentPlanAdminViewSet

from rest_framework.decorators import action
from django.db import transaction
from django.utils import timezone
from django.db import models
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q

from gold_app.models import GoldInvestment, GoldInvestmentPlan, GoldInventory
from admin_panel.serializers import (
    GoldInvestmentPlanAdminSerializer,
    GoldInvestmentAdminListSerializer,
    GoldInvestmentAdminDetailSerializer,
    GoldInvestmentStatusUpdateAdminSerializer,
    GoldInvestmentStatisticsAdminSerializer,
)
from accounts.utils import success_response, error_response
from admin_panel.utils import create_admin_log


# admin_panel/views.py - اصلاح GoldInvestmentPlanAdminViewSet

# admin_panel/views.py - اصلاح GoldInvestmentPlanAdminViewSet

class GoldInvestmentPlanAdminViewSet(AdminBaseViewSet):
    """
    ویوست مدیریت طرح‌های سرمایه‌گذاری طلا برای ادمین
    """

    queryset = GoldInvestmentPlan.objects.all().order_by('duration_days')
    serializer_class = GoldInvestmentPlanAdminSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        search = self.request.GET.get('search')
        is_active = self.request.GET.get('is_active')

        if search:
            qs = qs.filter(name__icontains=search)
        if is_active is not None:
            qs = qs.filter(is_active=is_active == 'true')

        return qs

    def list(self, request):
        qs = self.get_queryset()
        return success_response(
            "لیست طرح‌های سرمایه‌گذاری طلا",
            {
                "total_results": qs.count(),
                "results": self.serializer_class(qs, many=True, context={"request": request}).data
            }
        )

    def create(self, request):
        serializer = self.serializer_class(data=request.data)
        if not serializer.is_valid():
            return error_response("اطلاعات نامعتبر است", serializer.errors)

        plan = serializer.save()

        create_admin_log(
            request=request,
            user=request.user,
            action_type="INVESTMENT_PLAN_CREATED",
            action="ایجاد طرح سرمایه‌گذاری طلا",
            model_name="GoldInvestmentPlan",
            object_id=plan.id,
            success=True,
            description=f"""
طرح سرمایه‌گذاری طلا جدید ایجاد شد

نام: {plan.name}
مدت: {plan.duration_days} روز
سود کل: {plan.total_profit_percent}%
"""
        )

        return success_response(
            "طرح سرمایه‌گذاری با موفقیت ایجاد شد",
            self.serializer_class(plan, context={"request": request}).data,
            status_code=201
        )

    def update(self, request, pk=None, partial=False):
        plan = self.get_object()
        serializer = self.serializer_class(plan, data=request.data, partial=partial)
        if not serializer.is_valid():
            return error_response("اطلاعات نامعتبر است", serializer.errors)

        serializer.save()

        create_admin_log(
            request=request,
            user=request.user,
            action_type="INVESTMENT_PLAN_UPDATED",
            action="بروزرسانی طرح سرمایه‌گذاری طلا",
            model_name="GoldInvestmentPlan",
            object_id=plan.id,
            success=True,
            description=f"""
طرح سرمایه‌گذاری طلا بروزرسانی شد

نام: {plan.name}
مدت: {plan.duration_days} روز
سود کل: {plan.total_profit_percent}%
"""
        )

        return success_response(
            "طرح سرمایه‌گذاری با موفقیت بروزرسانی شد",
            self.serializer_class(plan, context={"request": request}).data
        )

    def partial_update(self, request, pk=None):
        """به‌روزرسانی جزئی طرح سرمایه‌گذاری طلا (PATCH)"""
        return self.update(request, pk, partial=True)

    def destroy(self, request, pk=None):
        plan = self.get_object()
        
        if plan.investments.filter(status='ACTIVE').exists():
            return error_response(
                "این طرح دارای سرمایه‌گذاری‌های فعال است. ابتدا آن‌ها را مدیریت کنید.",
                status_code=400
            )
        
        plan.delete()

        create_admin_log(
            request=request,
            user=request.user,
            action_type="INVESTMENT_PLAN_DELETED",
            action="حذف طرح سرمایه‌گذاری طلا",
            model_name="GoldInvestmentPlan",
            object_id=plan.id,
            success=True,
            description=f"""
طرح سرمایه‌گذاری طلا حذف شد

نام: {plan.name}
"""
        )

        return success_response("طرح سرمایه‌گذاری با موفقیت حذف شد")

class GoldInvestmentAdminViewSet(AdminBaseViewSet):
    """
    ویوست مدیریت سرمایه‌گذاری‌های طلا برای ادمین
    """

    queryset = GoldInvestment.objects.all().order_by('-id')
    serializer_class = GoldInvestmentAdminListSerializer

    def get_queryset(self):
        qs = super().get_queryset()

        search = self.request.GET.get('search')
        status = self.request.GET.get('status')
        plan = self.request.GET.get('plan')
        user_id = self.request.GET.get('user_id')
        start_date = self.request.GET.get('start_date')
        end_date = self.request.GET.get('end_date')
        ordering = self.request.GET.get('ordering')

        if search:
            qs = qs.filter(
                Q(user__mobile__icontains=search) |
                Q(user__first_name__icontains=search) |
                Q(user__last_name__icontains=search) |
                Q(plan__name__icontains=search)
            )

        if status:
            qs = qs.filter(status=status)

        if plan:
            qs = qs.filter(plan_id=plan)

        if user_id:
            qs = qs.filter(user_id=user_id)

        if start_date:
            qs = qs.filter(created_at__date__gte=start_date)

        if end_date:
            qs = qs.filter(created_at__date__lte=end_date)

        allowed_ordering = [
            'id', '-id',
            'created_at', '-created_at',
            'start_date', '-start_date',
            'end_date', '-end_date',
            'status', '-status',
            'gold_weight', '-gold_weight',
            'investment_price', '-investment_price'
        ]
        if ordering in allowed_ordering:
            qs = qs.order_by(ordering)

        return qs

    def list(self, request):
        qs = self.get_queryset()
        return success_response(
            "لیست سرمایه‌گذاری‌های طلا",
            {
                "total_results": qs.count(),
                "results": GoldInvestmentAdminListSerializer(
                    qs,
                    many=True,
                    context={"request": request}
                ).data
            }
        )

    def retrieve(self, request, pk=None):
        obj = self.get_object()
        data = GoldInvestmentAdminDetailSerializer(
            obj,
            context={"request": request}
        ).data
        return success_response("جزئیات سرمایه‌گذاری طلا", data)

    @transaction.atomic
    def partial_update(self, request, *args, **kwargs):
        if "status" in request.data:
            return self._change_status(request, kwargs["pk"])
        return super().partial_update(request, *args, **kwargs)

    @action(detail=True, methods=["post"])
    @transaction.atomic
    def change_status(self, request, pk=None):
        return self._change_status(request, pk)

    def _change_status(self, request, pk):
        investment = self.get_object()

        serializer = GoldInvestmentStatusUpdateAdminSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response("اطلاعات نامعتبر است", serializer.errors)

        new_status = serializer.validated_data["status"]
        description = serializer.validated_data.get("description", "")

        old_status = investment.status

        if old_status == new_status:
            return error_response("وضعیت تغییری نکرده است.")

        # فقط سرمایه‌گذاری‌های فعال قابل تغییر هستند
        if old_status != 'ACTIVE':
            return error_response(
                f"سرمایه‌گذاری که در وضعیت «{investment.get_status_display()}» است، قابل تغییر نیست."
            )

        # =================================================
        # تغییر وضعیت به COMPLETED (تکمیل شده)
        # =================================================
        if new_status == 'COMPLETED':
            # محاسبه سود باقی‌مانده
            remaining_profit = investment.total_expected_profit - investment.paid_profit

            # واریز سود باقی‌مانده
            if remaining_profit > 0:
                inventory, _ = GoldInventory.objects.select_for_update().get_or_create(user=investment.user)
                inventory.accessible_balance += remaining_profit
                inventory.save()
                investment.paid_profit = investment.total_expected_profit

            # آزادسازی طلای بلوکه شده
            inventory, _ = GoldInventory.objects.select_for_update().get_or_create(user=investment.user)
            inventory.blocked_balance -= investment.gold_weight
            inventory.accessible_balance += investment.gold_weight
            inventory.save()

            investment.status = 'COMPLETED'
            investment.completed_at = timezone.now()

        # =================================================
        # تغییر وضعیت به CANCELLED (لغو شده توسط ادمین)
        # =================================================
        elif new_status == 'CANCELLED':
            # محاسبه سود انصراف
            cancel_profit = investment.cancellation_profit_amount

            investment.status = 'CANCELLED'
            investment.cancelled_at = timezone.now()
            investment.cancellation_profit = cancel_profit

            # برگرداندن طلای بلوکه شده
            inventory, _ = GoldInventory.objects.select_for_update().get_or_create(user=investment.user)
            inventory.blocked_balance -= investment.gold_weight
            inventory.accessible_balance += investment.gold_weight
            inventory.save()

            # اضافه کردن سود انصراف
            if cancel_profit > 0:
                inventory.accessible_balance += cancel_profit
                inventory.save()

        if description:
            investment.description = f"{investment.description}\n\nتغییر وضعیت توسط ادمین:\n{description}" if investment.description else description

        investment.save()

        # ثبت لاگ
        create_admin_log(
            request=request,
            user=investment.user,
            action_type="INVESTMENT_STATUS_CHANGED",
            action=f"تغییر وضعیت سرمایه‌گذاری طلا به {investment.get_status_display()}",
            model_name="GoldInvestment",
            object_id=investment.id,
            success=True,
            description=f"""
تغییر وضعیت سرمایه‌گذاری طلا توسط ادمین

کاربر: {investment.user.mobile}
وزن طلا: {investment.gold_weight} گرم
طرح: {investment.plan.name}
وضعیت قبلی: {old_status}
وضعیت جدید: {new_status}
توضیحات: {description or 'بدون توضیحات'}
"""
        )

        return success_response(
            "وضعیت سرمایه‌گذاری با موفقیت تغییر کرد.",
            GoldInvestmentAdminDetailSerializer(investment, context={"request": request}).data
        )

    @action(detail=True, methods=["post"])
    @transaction.atomic
    def force_complete(self, request, pk=None):
        """
        تکمیل اجباری سرمایه‌گذاری (برای موارد خاص)
        """
        investment = self.get_object()

        if investment.status != 'ACTIVE':
            return error_response("فقط سرمایه‌گذاری‌های فعال قابل تکمیل هستند.")

        # محاسبه سود باقی‌مانده
        remaining_profit = investment.total_expected_profit - investment.paid_profit

        # واریز سود باقی‌مانده
        if remaining_profit > 0:
            inventory, _ = GoldInventory.objects.select_for_update().get_or_create(user=investment.user)
            inventory.accessible_balance += remaining_profit
            inventory.save()
            investment.paid_profit = investment.total_expected_profit

        # آزادسازی طلای بلوکه شده
        inventory, _ = GoldInventory.objects.select_for_update().get_or_create(user=investment.user)
        inventory.blocked_balance -= investment.gold_weight
        inventory.accessible_balance += investment.gold_weight
        inventory.save()

        investment.status = 'COMPLETED'
        investment.completed_at = timezone.now()
        investment.save()

        create_admin_log(
            request=request,
            user=investment.user,
            action_type="INVESTMENT_FORCE_COMPLETE",
            action="تکمیل اجباری سرمایه‌گذاری طلا",
            model_name="GoldInvestment",
            object_id=investment.id,
            success=True,
            description=f"""
تکمیل اجباری سرمایه‌گذاری طلا توسط ادمین

کاربر: {investment.user.mobile}
وزن طلا: {investment.gold_weight} گرم
طرح: {investment.plan.name}
سود پرداخت شده: {investment.paid_profit} گرم
"""
        )

        return success_response(
            "سرمایه‌گذاری با موفقیت تکمیل شد.",
            GoldInvestmentAdminDetailSerializer(investment, context={"request": request}).data
        )


class GoldInvestmentStatisticsAdminView(APIView):
    """
    دریافت آمار سرمایه‌گذاری‌های طلا برای داشبورد ادمین
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        status_counts = {}
        total = GoldInvestment.objects.count()

        for status, label in GoldInvestment.STATUS_CHOICES:
            status_counts[status] = GoldInvestment.objects.filter(status=status).count()

        # مجموع طلای سرمایه‌گذاری شده
        total_invested = GoldInvestment.objects.aggregate(
            total=models.Sum('gold_weight')
        )['total'] or 0

        # مجموع سود پرداخت شده
        total_paid = GoldInvestment.objects.aggregate(
            total=models.Sum('paid_profit')
        )['total'] or 0

        # مجموع سود مورد انتظار
        total_expected = GoldInvestment.objects.filter(status='ACTIVE').aggregate(
            total=models.Sum('expected_profit')
        )['total'] or 0

        # مجموع سود انصراف
        total_cancel = GoldInvestment.objects.filter(status='CANCELLED').aggregate(
            total=models.Sum('cancellation_profit')
        )['total'] or 0

        # تعداد طرح‌ها
        plans_count = GoldInvestmentPlan.objects.count()
        active_plans_count = GoldInvestmentPlan.objects.filter(is_active=True).count()

        data = {
            'total': total,
            'active': status_counts.get('ACTIVE', 0),
            'completed': status_counts.get('COMPLETED', 0),
            'cancelled': status_counts.get('CANCELLED', 0),
            'total_invested_gold': float(total_invested),
            'total_paid_profit': float(total_paid),
            'total_expected_profit': float(total_expected),
            'total_cancellation_profit': float(total_cancel),
            'plans_count': plans_count,
            'active_plans_count': active_plans_count,
        }

        return success_response("آمار سرمایه‌گذاری‌های طلا", data)
    
    
    
    
# admin_panel/views.py - اضافه کردن VersionControlAdminViewSet

from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from django.views.decorators.cache import never_cache
from django.utils.decorators import method_decorator

from gold_app.models import AppVersion
from admin_panel.serializers import AppVersionSerializer
from accounts.utils import success_response, error_response
from admin_panel.utils import create_admin_log


class VersionControlAdminViewSet(ModelViewSet):
    """
    مدیریت نسخه اپلیکیشن برای ادمین
    """
    
    queryset = AppVersion.objects.all().order_by('-version_code')
    serializer_class = AppVersionSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "post", "patch", "delete"]

    # =============================================
    # LIST
    # =============================================
    
    def list(self, request):
        qs = self.get_queryset()
        return success_response(
            "لیست نسخه‌های اپلیکیشن",
            {
                "total_results": qs.count(),
                "results": self.serializer_class(qs, many=True, context={"request": request}).data
            }
        )

    # =============================================
    # RETRIEVE
    # =============================================
    
    def retrieve(self, request, pk=None):
        obj = self.get_object()
        return success_response(
            "جزئیات نسخه اپلیکیشن",
            self.serializer_class(obj, context={"request": request}).data
        )

    # =============================================
    # CREATE
    # =============================================
    
    def create(self, request):
        serializer = self.serializer_class(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        
        obj = serializer.save()
        
        # ثبت لاگ
        create_admin_log(
            request=request,
            user=request.user,
            action_type="APP_VERSION_CREATED",
            action="ایجاد نسخه جدید اپلیکیشن",
            model_name="AppVersion",
            object_id=obj.id,
            success=True,
            description=f"""
نسخه جدید اپلیکیشن ایجاد شد

نام نسخه: {obj.version_name}
کد نسخه: {obj.version_code}
حداقل نسخه مورد نیاز: {obj.min_required_version_code}
بروزرسانی اجباری: {obj.is_force_update}
"""
        )
        
        return success_response(
            "نسخه اپلیکیشن با موفقیت ایجاد شد",
            self.serializer_class(obj, context={"request": request}).data,
            status_code=201
        )

    # =============================================
    # UPDATE
    # =============================================
    
    def update(self, request, pk=None, partial=False):
        obj = self.get_object()
        serializer = self.serializer_class(obj, data=request.data, partial=partial, context={"request": request})
        serializer.is_valid(raise_exception=True)
        
        obj = serializer.save()
        
        create_admin_log(
            request=request,
            user=request.user,
            action_type="APP_VERSION_UPDATED",
            action="بروزرسانی نسخه اپلیکیشن",
            model_name="AppVersion",
            object_id=obj.id,
            success=True,
            description=f"""
نسخه اپلیکیشن بروزرسانی شد

نام نسخه: {obj.version_name}
کد نسخه: {obj.version_code}
حداقل نسخه مورد نیاز: {obj.min_required_version_code}
بروزرسانی اجباری: {obj.is_force_update}
"""
        )
        
        return success_response(
            "نسخه اپلیکیشن با موفقیت بروزرسانی شد",
            self.serializer_class(obj, context={"request": request}).data
        )

    # =============================================
    # PARTIAL UPDATE
    # =============================================
    
    def partial_update(self, request, pk=None):
        return self.update(request, pk, partial=True)

    # =============================================
    # DELETE
    # =============================================
    
    def destroy(self, request, pk=None):
        obj = self.get_object()
        
        # جلوگیری از حذف نسخه فعال
        if obj.is_active:
            return error_response("نسخه فعال قابل حذف نیست. ابتدا آن را غیرفعال کنید.", status_code=400)
        
        obj.delete()
        
        create_admin_log(
            request=request,
            user=request.user,
            action_type="APP_VERSION_DELETED",
            action="حذف نسخه اپلیکیشن",
            model_name="AppVersion",
            object_id=obj.id,
            success=True,
            description=f"""
نسخه اپلیکیشن حذف شد

نام نسخه: {obj.version_name}
کد نسخه: {obj.version_code}
"""
        )
        
        return success_response("نسخه اپلیکیشن با موفقیت حذف شد")

    # =============================================
    # SET ACTIVE - فعال کردن یک نسخه
    # =============================================
    
    @action(detail=True, methods=["post"])
    def set_active(self, request, pk=None):
        """فعال کردن یک نسخه و غیرفعال کردن سایر نسخه‌ها"""
        obj = self.get_object()
        
        # غیرفعال کردن همه نسخه‌ها
        AppVersion.objects.all().update(is_active=False)
        
        # فعال کردن نسخه انتخاب شده
        obj.is_active = True
        obj.save()
        
        create_admin_log(
            request=request,
            user=request.user,
            action_type="APP_VERSION_SET_ACTIVE",
            action="فعال کردن نسخه اپلیکیشن",
            model_name="AppVersion",
            object_id=obj.id,
            success=True,
            description=f"""
نسخه اپلیکیشن فعال شد

نام نسخه: {obj.version_name}
کد نسخه: {obj.version_code}
"""
        )
        
        return success_response(
            "نسخه با موفقیت فعال شد",
            self.serializer_class(obj, context={"request": request}).data
        )