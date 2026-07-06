from datetime import timedelta
from admin_panel.models import (
    GoldBalanceAdjustment,
    SilverBalanceAdjustment,
)
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


class UserAdminViewSet(AdminBaseViewSet):
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

        return success_response("جزئیات کاربر", data)

    # ======================
    # UPDATE (FULL FIX)
    # ======================
    def update(self, request, pk=None, *args, **kwargs):
        user = get_object_or_404(User, pk=pk)

        serializer = AdminUserUpdateSerializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

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

        user.refresh_from_db()

        return success_response(
            "آپدیت انجام شد", {"results": AdminUserDetailSerializer(user).data}
        )

    # ======================
    # TOGGLE ACTIVE
    # ======================
    @action(detail=True, methods=["post"])
    def toggle_active(self, request, pk=None):
        user = get_object_or_404(User, pk=pk)
        user.is_active = not user.is_active
        user.save()

        return success_response("وضعیت تغییر کرد", {"is_active": user.is_active})
        # =========================================================
   
   
# =========================================================
# USER TRANSACTIONS
# =========================================================
    @action(detail=True, methods=["get"], url_path="transactions")
    def transactions(self, request, pk=None):

        user = get_object_or_404(User, pk=pk)

        results = []

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

        for item in GoldBalanceAdjustment.objects.filter(user=user):

            results.append({
                "source": "GOLD_WALLET",
                "type": "ADMIN_ADJUSTMENT",
                "status": "COMPLETED",
                "amount": item.gold_amount,
                "toman_amount": item.wallet_amount,
                "payment_method": None,
                "delivery_type": None,
                "tracking_code": None,
                "description": item.admin_note or "افزایش موجودی توسط ادمین",
                "created_at": item.created_at,
            })

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
                "description": item.description or f"سفارش فیزیکی طلا ({item.get_delivery_type_display()})",
                "created_at": item.created_at,
            })

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

        for item in SilverBalanceAdjustment.objects.filter(user=user):

            results.append({
                "source": "SILVER_WALLET",
                "type": "ADMIN_ADJUSTMENT",
                "status": "COMPLETED",
                "amount": item.silver_amount,
                "toman_amount": item.wallet_amount,
                "payment_method": None,
                "delivery_type": None,
                "tracking_code": None,
                "description": item.admin_note or "افزایش موجودی توسط ادمین",
                "created_at": item.created_at,
            })

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
                "description": item.description or f"سفارش فیزیکی نقره ({item.get_delivery_type_display()})",
                "created_at": item.created_at,
            })

        results.sort(
            key=lambda x: x["created_at"],
            reverse=True,
        )

        serializer = UserTransactionSerializer(
            results,
            many=True,
        )

        return success_response(
            "لیست تراکنش‌های کاربر",
            {
                "total_results": len(serializer.data),
                "results": serializer.data,
            },
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

class OrderAdminViewSet(AdminBaseViewSet):

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
            "لیست سفارش‌ها",
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
            "جزئیات سفارش",
            data
        )

    # =====================================================
    # PATCH /orders/{id}/  (IMPORTANT FIX)
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
    # CORE BUSINESS LOGIC (SINGLE SOURCE OF TRUTH)
    # =====================================================
    def _change_status(self, request, pk):

        order = (
            Order.objects
            .select_for_update()
            .select_related("user")
            .prefetch_related("items__product")
            .get(pk=pk)
        )
        wallet = Wallet.objects.select_for_update().get(user=order.user)
        inventory = GoldInventory.objects.select_for_update().get(user=order.user)
        serializer = StatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        new_status = serializer.validated_data["status"]
        description = serializer.validated_data.get("description", "")

        old_status = order.status

        if old_status == new_status:
            return error_response("وضعیت تغییری نکرده است.")

        if old_status == "DELIVERED" and new_status == "CANCELLED":
            return error_response("امکان لغو سفارش تحویل داده شده وجود ندارد.")

        order.status = new_status
        order.save(update_fields=["status"])

        OrderStatusHistory.objects.create(
            order=order,
            status=new_status,
            description=description
        )

        wallet = order.user.wallet
        inventory = order.user.gold_inventory

        # =================================================
        # DELIVERED
        # =================================================
        if new_status == "DELIVERED":

            for item in order.items.all():

                product = item.product

                if product.inventory_count < item.quantity:
                    return error_response(
                        f"موجودی {product.title} کافی نیست."
                    )

                product.inventory_count = F("inventory_count") - item.quantity
                product.save(update_fields=["inventory_count"])

            if order.payment_method == "TOMAN":

                wallet.blocked_toman = max(
                    0,
                    wallet.blocked_toman - order.total_toman_amount
                )
                wallet.save(update_fields=["blocked_toman"])

            elif order.payment_method == "GOLD":

                inventory.blocked_balance = max(
                    0,
                    inventory.blocked_balance - order.total_gold_amount
                )
                inventory.save(update_fields=["blocked_balance"])

        # =================================================
        # CANCELLED
        # =================================================
        elif new_status == "CANCELLED":

            if order.payment_method == "TOMAN":

                wallet.accessible_toman += order.total_toman_amount
                wallet.blocked_toman = max(
                    0,
                    wallet.blocked_toman - order.total_toman_amount
                )

                wallet.save(update_fields=[
                    "accessible_toman",
                    "blocked_toman",
                ])

            elif order.payment_method == "GOLD":

                inventory.accessible_balance += order.total_gold_amount
                inventory.blocked_balance = max(
                    0,
                    inventory.blocked_balance - order.total_gold_amount
                )

                inventory.save(update_fields=[
                    "accessible_balance",
                    "blocked_balance",
                ])

        order.refresh_from_db()

        return success_response(
            "وضعیت سفارش با موفقیت تغییر کرد.",
            self.serializer_class(
                order,
                context={"request": request}
            ).data
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

    def list(self, request):

        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)

        if page is not None:

            serializer = self.get_serializer(page, many=True)

            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)

        return success_response(
            "لیست لاگ ها",
            {"total_results": queryset.count(), "results": serializer.data},
        )

    def retrieve(self, request, pk=None):

        obj = self.get_object()

        serializer = self.get_serializer(obj)

        return success_response("جزئیات لاگ", serializer.data)

    @action(detail=False, methods=["delete"], permission_classes=[IsAdminRole])
    def clear(self, request):

        deleted = AdminLog.objects.all().delete()

        return success_response("تمام لاگ‌ها حذف شدند.", {"deleted": deleted[0]})


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


class GoldAdminViewSet(AdminBaseViewSet):
    http_method_names = ["get"]
    queryset = GoldPriceHistory.objects.none()
    serializer_class = GoldLiveSerializer  # 👈 اضافه کن

    # ----------------------
    # LIST → ریدایرکت به live
    # ----------------------
    def list(self, request):
        data = get_gold_bubble()

        if data is None:
            return error_response("دریافت قیمت لحظه‌ای طلا ناموفق بود", code=503)

        return success_response(
            "قیمت لحظه‌ای طلا", {"results": GoldLiveSerializer(data).data}
        )

    @action(detail=False, methods=["get"], url_path="live")
    def live(self, request):
        return self.list(request)

    @action(detail=False, methods=["get"], url_path="chart")
    def chart(self, request):
        filter_type = request.GET.get("filter", "24H").upper()

        if filter_type not in ["24H", "WEEKLY", "MONTHLY"]:
            return error_response(
                "فیلتر نامعتبر است. مقادیر مجاز: 24H, WEEKLY, MONTHLY"
            )

        data = get_gold_chart_data(filter_type)

        return success_response(
            "چارت طلا", {"results": GoldChartDataSerializer(data).data}
        )


class SilverAdminViewSet(AdminBaseViewSet):
    http_method_names = ["get"]
    queryset = SilverPriceHistory.objects.none()
    serializer_class = SilverLiveSerializer  # 👈 اضافه کن

    # ----------------------
    # LIST → ریدایرکت به live
    # ----------------------
    def list(self, request):
        data = get_silver_bubble()

        if data is None:
            return error_response("دریافت قیمت لحظه‌ای نقره ناموفق بود", code=503)

        return success_response(
            "قیمت لحظه‌ای نقره", {"results": SilverLiveSerializer(data).data}
        )

    @action(detail=False, methods=["get"], url_path="live")
    def live(self, request):
        return self.list(request)

    @action(detail=False, methods=["get"], url_path="chart")
    def chart(self, request):
        filter_type = request.GET.get("filter", "24H").upper()

        if filter_type not in ["24H", "WEEKLY", "MONTHLY"]:
            return error_response(
                "فیلتر نامعتبر است. مقادیر مجاز: 24H, WEEKLY, MONTHLY"
            )

        data = get_silver_chart_data(filter_type)

        return success_response(
            "چارت نقره", {"results": SilverChartDataSerializer(data).data}
        )


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
