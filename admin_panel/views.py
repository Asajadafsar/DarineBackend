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

from datetime import timedelta
import jdatetime

from rest_framework.views import APIView
from rest_framework.response import Response

from django.db.models import Sum

from gold_app.models import GoldTransaction
from silver_app.models import SilverTransaction
import psutil

from django.db.models import Sum
from django.utils import timezone

from rest_framework.viewsets import ViewSet

from accounts.models import User

from gold_app.models import (
    GoldTransaction,
    GoldInventory,
    Wallet,
    FinancialTransaction
)

from silver_app.models import (
    SilverTransaction,
    SilverInventory,
    SilverWallet,
    SilverFinancialTransaction
)

from .models import AdminLog
from .serializers import AdminLogSerializer
# admin_panel/views.py

from datetime import timedelta

import psutil

from django.db.models import Sum
from django.utils import timezone

from rest_framework.viewsets import ViewSet

from accounts.models import User

from gold_app.models import (
    GoldTransaction,
    GoldInventory
)

from silver_app.models import (
    SilverTransaction,
    SilverInventory,
    SilverWallet,
    SilverFinancialTransaction
)


from .models import AdminLog

from .serializers import (
    AdminAnalyticsSerializer
)

from .permissions import IsAdminRole



# =========================================================
# RESPONSE HELPERS
# =========================================================

from rest_framework.response import Response
from rest_framework import status


def success_response(message="OK", data=None):
    return Response({
        "success": True,
        "message": message,
        "data": data or {}
    }, status=status.HTTP_200_OK)


def error_response(message="error", data=None, code=400):
    return Response({
        "success": False,
        "message": message,
        "data": data or {}
    }, status=code)


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
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search)
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

        return success_response("لیست کاربران", {
            "total_results": len(results),
            "results": results
        })

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

        serializer = AdminUserUpdateSerializer(
            user,
            data=request.data,
            partial=True
        )
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
                    "silver_sell_fee"
                ]
                if request.data.get(key) is not None
            }

        if fee_data:
            fee_serializer = UserFeeUpdateSerializer(
                fee,
                data=fee_data,
                partial=True
            )
            fee_serializer.is_valid(raise_exception=True)
            fee_serializer.save()

        user.refresh_from_db()

        return success_response("آپدیت انجام شد", {
            "results": AdminUserDetailSerializer(user).data
        })

    # ======================
    # TOGGLE ACTIVE
    # ======================
    @action(detail=True, methods=["post"])
    def toggle_active(self, request, pk=None):
        user = get_object_or_404(User, pk=pk)
        user.is_active = not user.is_active
        user.save()

        return success_response("وضعیت تغییر کرد", {
            "is_active": user.is_active
        })

    # =========================================================
    # BULK UPDATE FEES
    # =========================================================
    @action(detail=False, methods=["post"], url_path="bulk-update-fees")
    def bulk_update_fees(self, request):
        user_ids = request.data.get("user_ids", [])
        
        if not user_ids or not isinstance(user_ids, list):
            return error_response("لطفاً لیست آیدی کاربران (user_ids) را به صورت آرایه ارسال کنید.")

        update_data = {}
        for key in ["gold_buy_fee", "gold_sell_fee", "silver_buy_fee", "silver_sell_fee"]:
            if request.data.get(key) is not None:
                update_data[key] = request.data.get(key)

        if not update_data:
            return error_response("هیچ کارمزدی جهت بروزرسانی ارسال نشده است.")

        with transaction.atomic():
            existing_user_ids = User.objects.filter(id__in=user_ids).values_list('id', flat=True)
            
            for u_id in existing_user_ids:
                UserFee.objects.get_or_create(user_id=u_id)

            updated_count = UserFee.objects.filter(user_id__in=existing_user_ids).update(**update_data)

        return success_response(
            f"کارمزد تعداد {updated_count} کاربر با موفقیت به صورت گروهی ویرایش شد.",
            {"updated_count": updated_count}
        )

class CooperationRequestAdminViewSet(AdminBaseViewSet):

    queryset = CooperationRequest.objects.all().order_by("-id")

    def get_queryset(self):

        qs = super().get_queryset()

        search = self.request.GET.get("search")
        mobile = self.request.GET.get("mobile")
        ordering = self.request.GET.get("ordering")

        if search:
            qs = qs.filter(
                full_name__icontains=search
            )

        if mobile:
            qs = qs.filter(
                mobile__icontains=mobile
            )
        allowed_ordering = ["id", "-id", "created_at", "-created_at","full_name","full_name",]
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
            {
                "total_results": len(results),
                "results": results
            }
        )

    # ======================
    # RETRIEVE
    # ======================
    def retrieve(self, request, pk=None):

        obj = get_object_or_404(CooperationRequest, pk=pk)

        data = CooperationRequestListSerializer(obj).data

        return success_response(
            "جزئیات درخواست همکاری",
            data
        )




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
            "id", "-id",
            "name", "-name",
            "weight", "-weight",
            "buy_price", "-buy_price",
            "sell_price", "-sell_price",
            "inventory_count", "-inventory_count",
            "created_at", "-created_at",
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

        ser = ProductSerializer(
            qs,
            many=True,
            context=self.get_serializer_context()
        )

        return success_response(
            "لیست محصولات",
            {
                "total_results": qs.count(),
                "results": ser.data
            }
        )

    # ======================
    # RETRIEVE
    # ======================
    def retrieve(self, request, pk=None):
        obj = self.get_object()

        return success_response(
            "جزئیات محصول",
            ProductSerializer(obj, context=self.get_serializer_context()).data
        )

    # ======================
    # CREATE (FIX مهم اینجاست)
    # ======================
    def create(self, request):
        ser = ProductCreateUpdateSerializer(
            data=request.data,
            context=self.get_serializer_context()
        )

        ser.is_valid(raise_exception=True)
        obj = ser.save()

        return success_response(
            "محصول ساخته شد",
            ProductSerializer(obj, context=self.get_serializer_context()).data
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
            context=self.get_serializer_context()
        )

        ser.is_valid(raise_exception=True)
        obj = ser.save()
        obj.refresh_from_db()

        return success_response(
            "محصول ویرایش شد",
            ProductSerializer(obj, context=self.get_serializer_context()).data
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
            "id", "-id",
            "created_at", "-created_at",
            "name", "-name",
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
                "results": self.serializer_class(qs, many=True).data
            }
        )

    # ======================
    # RETRIEVE
    # ======================
    def retrieve(self, request, pk=None):
        obj = self.get_object()

        return success_response(
            "جزئیات دسته‌بندی",
            self.serializer_class(obj).data
        )

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

        return success_response(
            "دسته‌بندی ویرایش شد",
            self.serializer_class(obj).data
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
            "id", "-id",
            "name", "-name",
            "weight", "-weight",
            "buy_price", "-buy_price",
            "sell_price", "-sell_price",
            "inventory_count", "-inventory_count",
            "created_at", "-created_at",
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
            qs,
            many=True,
            context=self.get_serializer_context()
        )

        return success_response(
            "لیست محصولات نقره",
            {
                "total_results": qs.count(),
                "results": ser.data
            }
        )

    # ======================
    # RETRIEVE
    # ======================
    def retrieve(self, request, pk=None):
        obj = self.get_object()

        return success_response(
            "جزئیات محصول نقره",
            SilverProductSerializer(
                obj,
                context=self.get_serializer_context()
            ).data
        )

    # ======================
    # CREATE
    # ======================
    def create(self, request):

        ser = SilverProductCreateUpdateSerializer(
            data=request.data,
            context=self.get_serializer_context()
        )

        ser.is_valid(raise_exception=True)
        obj = ser.save()

        return success_response(
            "محصول نقره ساخته شد",
            SilverProductSerializer(
                obj,
                context=self.get_serializer_context()
            ).data
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
            context=self.get_serializer_context()
        )

        ser.is_valid(raise_exception=True)
        obj = ser.save()
        obj.refresh_from_db()

        return success_response(
            "محصول نقره ویرایش شد",
            SilverProductSerializer(
                obj,
                context=self.get_serializer_context()
            ).data
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

        return success_response(
            "محصول نقره حذف شد"
        )
    

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
            qs = qs.filter(
                created_by__mobile__icontains=search
            )

        if status:
            qs = qs.filter(
                status=status
            )

        if activated_by_name:
            qs = qs.filter(
                activated_by__mobile__icontains=activated_by_name
            )

        if serial_number:
            qs = qs.filter(
                serial_number__icontains=serial_number
            )
        allowed_ordering = ["id", "-id", "created_at", "-created_at","weight","-weight","first_name", "status", "-status","serial_number", "-serial_number",]
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
                "results": GiftCardSerializer(qs, many=True).data
            }
        )

    # ======================
    # RETRIEVE
    # ======================
    def retrieve(self, request, pk=None):
        obj = self.get_object()
        return success_response(
            "جزئیات کارت",
            GiftCardSerializer(obj).data
        )

    # ======================
    # CREATE
    # ======================
    def create(self, request):
        ser = GiftCardCreateUpdateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)

        obj = ser.save(
            created_by=request.user,
            status="ACTIVE",
            is_used=False
        )

        return success_response(
            "کارت ساخته شد",
            GiftCardSerializer(obj).data
        )

    # ======================
    # UPDATE
    # ======================
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        obj = self.get_object()

        ser = GiftCardCreateUpdateSerializer(
            obj,
            data=request.data,
            partial=partial
        )

        ser.is_valid(raise_exception=True)
        obj = ser.save()
        obj.refresh_from_db()

        return success_response(
            "کارت ویرایش شد",
            GiftCardSerializer(obj).data
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

        return success_response(
            "وضعیت کارت تغییر کرد",
            GiftCardSerializer(obj).data
        )

# =========================================================
# ORDERS
# =========================================================

class OrderAdminViewSet(AdminBaseViewSet):

    queryset = Order.objects.all().order_by("-id")

    def get_queryset(self):

        qs = super().get_queryset()

        search = self.request.GET.get("search")
        status = self.request.GET.get("status")
        tracking_code = self.request.GET.get("tracking_code")
        start_date = self.request.GET.get("start_date")
        end_date = self.request.GET.get("end_date")
        ordering = self.request.GET.get("ordering")

        if search:
            qs = qs.filter(
                user__mobile__icontains=search
            )

        if status:
            qs = qs.filter(
                status=status
            )
        if tracking_code:
            qs = qs.filter(
                tracking_code__icontains=tracking_code
            )
        if start_date:
            qs = qs.filter(
                created_at__date__gte=start_date
            )

        if end_date:
            qs = qs.filter(
                created_at__date__lte=end_date
            )
        allowed_ordering = ["id", "-id", "created_at", "-created_at","status", "-status",]
        if ordering in allowed_ordering:
            
            qs = qs.order_by(ordering)
        return qs
    queryset = Order.objects.all().order_by("-id")
    serializer_class = OrderSerializer

    # ======================
    # LIST
    # ======================
    def list(self, request):
        qs = self.get_queryset()

        return success_response(
            "لیست سفارش‌ها",
            {
                "total_results": qs.count(),
                "results": self.serializer_class(qs, many=True).data
            }
        )

    # ======================
    # RETRIEVE
    # ======================
    def retrieve(self, request, pk=None):
        obj = self.get_object()

        return success_response(
            "جزئیات سفارش",
            self.serializer_class(obj).data
        )

    # ======================
    # CHANGE STATUS
    # ======================
    @action(detail=True, methods=["post"])
    def change_status(self, request, pk=None):
        obj = self.get_object()

        ser = StatusUpdateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)

        obj.status = ser.validated_data["status"]
        obj.save()
        obj.refresh_from_db()

        return success_response(
            "وضعیت سفارش تغییر کرد",
            self.serializer_class(obj).data
        )
    

# =========================================================
# SILVER ORDER
# =========================================================
class SilverOrderAdminViewSet(AdminBaseViewSet):

    queryset = SilverOrder.objects.all().order_by("-id")
    serializer_class = SilverOrderSerializer

    # ======================
    # GET QUERYSET
    # ======================
    def get_queryset(self):

        qs = SilverOrder.objects.all()

        search = self.request.GET.get("search")
        status = self.request.GET.get("status")
        tracking_code = self.request.GET.get("tracking_code")
        start_date = self.request.GET.get("start_date")
        end_date = self.request.GET.get("end_date")
        ordering = self.request.GET.get("ordering")

        # search user mobile
        if search:
            qs = qs.filter(user__mobile__icontains=search)

        # status filter
        if status:
            qs = qs.filter(status=status)

        # tracking code
        if tracking_code:
            qs = qs.filter(tracking_code__icontains=tracking_code)

        # date filters
        if start_date:
            qs = qs.filter(created_at__date__gte=start_date)

        if end_date:
            qs = qs.filter(created_at__date__lte=end_date)

        # ordering whitelist
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

    # ======================
    # LIST
    # ======================
    def list(self, request):

        qs = self.get_queryset()

        ser = self.serializer_class(
            qs,
            many=True,
            context={"request": request}
        )

        return success_response(
            "لیست سفارشات نقره",
            {
                "total_results": qs.count(),
                "results": ser.data
            }
        )

    # ======================
    # RETRIEVE
    # ======================
    def retrieve(self, request, pk=None):

        obj = self.get_object()

        return success_response(
            "جزئیات سفارش نقره",
            self.serializer_class(
                obj,
                context={"request": request}
            ).data
        )

    # ======================
    # CHANGE STATUS
    # ======================
    @action(detail=True, methods=["post"])
    def change_status(self, request, pk=None):

        obj = self.get_object()

        ser = StatusUpdateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)

        obj.status = ser.validated_data["status"]
        obj.save()

        return success_response(
            "وضعیت سفارش نقره تغییر کرد",
            self.serializer_class(obj).data
        )
        
        

# =========================================================
# DASHBOARD
# =========================================================

# class DashboardAdminViewSet(ViewSet):

#     permission_classes = [IsAdminRole]

#     def list(self, request):

#         users_count = User.objects.count()

#         verified_users = User.objects.filter(
#             auth_status="verified"
#         ).count()

#         pending_users = User.objects.filter(
#             auth_status="pending"
#         ).count()

#         gold_products = Product.objects.count()

#         silver_products = SilverProduct.objects.count()

#         gold_orders = Order.objects.count()

#         silver_orders = SilverOrder.objects.count()

#         pending_orders = (
#             Order.objects.filter(status="PENDING").count()
#             +
#             SilverOrder.objects.filter(status="PENDING").count()
#         )

#         gold_transactions = GoldTransaction.objects.count()

#         silver_transactions = SilverTransaction.objects.count()

#         total_wallet_balance = (
#             Wallet.objects.aggregate(
#                 total=Sum("balance")
#             )["total"]
#             or 0
#         )

#         total_silver_wallet_balance = (
#             SilverWallet.objects.aggregate(
#                 total=Sum("balance")
#             )["total"]
#             or 0
#         )

#         total_gold_inventory = (
#             GoldInventory.objects.aggregate(
#                 total=Sum("balance")
#             )["total"]
#             or 0
#         )

#         total_silver_inventory = (
#             SilverInventory.objects.aggregate(
#                 total=Sum("balance")
#             )["total"]
#             or 0
#         )

#         total_deposit_amount = (
#             FinancialTransaction.objects.filter(
#                 type="DEPOSIT",
#                 status="COMPLETED"
#             ).aggregate(
#                 total=Sum("amount")
#             )["total"]
#             or 0
#         )

#         pending_withdraw_amount = (
#             FinancialTransaction.objects.filter(
#                 type="WITHDRAW",
#                 status="PENDING"
#             ).aggregate(
#                 total=Sum("amount")
#             )["total"]
#             or 0
#         )

#         recent_users = list(
#             User.objects.order_by("-id")[:10]
#             .values(
#                 "id",
#                 "first_name",
#                 "last_name",
#                 "mobile"
#             )
#         )

#         recent_orders = list(
#             Order.objects.order_by("-id")[:10]
#             .values(
#                 "id",
#                 "tracking_code",
#                 "status"
#             )
#         )

#         return success_response(

#             message="داشبورد",

#             data={

#                 "users_count": users_count,

#                 "verified_users": verified_users,

#                 "pending_users": pending_users,

#                 "gold_products": gold_products,

#                 "silver_products": silver_products,

#                 "gold_orders": gold_orders,

#                 "silver_orders": silver_orders,

#                 "pending_orders": pending_orders,

#                 "gold_transactions": gold_transactions,

#                 "silver_transactions": silver_transactions,

#                 "total_wallet_balance": total_wallet_balance,

#                 "total_silver_wallet_balance": total_silver_wallet_balance,

#                 "total_gold_inventory": total_gold_inventory,

#                 "total_silver_inventory": total_silver_inventory,

#                 "total_deposit_amount": total_deposit_amount,

#                 "pending_withdraw_amount": pending_withdraw_amount,

#                 "recent_users": recent_users,

#                 "recent_orders": recent_orders,
#             }
#         )



from django.db.models import Sum
from rest_framework.viewsets import ViewSet

# =========================================================
# DASHBOARD
# =========================================================

class DashboardAdminViewSet(ViewSet):

    permission_classes = [IsAdminRole]

    def list(self, request):

        users = User.objects.count()

        gold_products = Product.objects.count()

        silver_products = SilverProduct.objects.count()

        products = (
            gold_products +
            silver_products
        )

        orders = Order.objects.count()

        silver_orders = SilverOrder.objects.count()

        wallet_balance = (
            (
                Wallet.objects.aggregate(
                    total=Sum("balance")
                )["total"]
                or 0
            )
            +
            (
                SilverWallet.objects.aggregate(
                    total=Sum("balance")
                )["total"]
                or 0
            )
        )

        return success_response(

            message="داشبورد",

            data={

                "users": users,

                "products": products,

                "gold_products": gold_products,

                "silver_products": silver_products,

                "orders": orders,

                "silver_orders": silver_orders,

                "wallet_balance": float(wallet_balance),
            }
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
            "id", "-id",
            "created_at", "-created_at",
            "full_name", "-full_name",
            "card_number", "-card_number",
            "sheba", "-sheba",
            "is_active", "-is_active",
        ]

        if ordering in allowed_ordering:
            qs = qs.order_by(ordering)

        return qs
    queryset = GoldBankInfo.objects.all().order_by("-id")

    serializer_class = GoldBankInfoSerializer

    create_update_serializer_class = (
        GoldBankInfoCreateUpdateSerializer
    )

    # ======================
    # LIST
    # ======================
    def list(self, request):

        qs = self.get_queryset()

        return success_response(
            "لیست کارت‌های طلا",
            {
                "total_results": qs.count(),
                "results": self.serializer_class(
                    qs,
                    many=True
                ).data
            }
        )

    # ======================
    # RETRIEVE
    # ======================
    def retrieve(self, request, pk=None):

        obj = self.get_object()

        return success_response(
            "جزئیات کارت طلا",
            self.serializer_class(obj).data
        )

    # ======================
    # CREATE
    # ======================
    def create(self, request):

        serializer = (
            self.create_update_serializer_class(
                data=request.data
            )
        )

        serializer.is_valid(
            raise_exception=True
        )

        obj = serializer.save()

        return success_response(
            "کارت طلا ساخته شد",
            self.serializer_class(obj).data
        )

    # ======================
    # UPDATE
    # ======================
    def update(
        self,
        request,
        *args,
        **kwargs
    ):

        partial = kwargs.pop(
            "partial",
            False
        )

        obj = self.get_object()

        serializer = (
            self.create_update_serializer_class(
                obj,
                data=request.data,
                partial=partial
            )
        )

        serializer.is_valid(
            raise_exception=True
        )

        obj = serializer.save()

        obj.refresh_from_db()

        return success_response(
            "کارت طلا ویرایش شد",
            self.serializer_class(obj).data
        )

    def partial_update(
        self,
        request,
        *args,
        **kwargs
    ):

        kwargs["partial"] = True

        return self.update(
            request,
            *args,
            **kwargs
        )

    # ======================
    # TOGGLE
    # ======================
    @action(
        detail=True,
        methods=["post"]
    )
    def toggle(
        self,
        request,
        pk=None
    ):

        bank = self.get_object()

        GoldBankInfo.objects.exclude(
            pk=bank.pk
        ).update(
            is_active=False
        )

        bank.is_active = True
        bank.save()

        return success_response(
            "کارت طلا فعال شد",
            {
                "is_active": True
            }
        )
    

# admin_panel/views.py

import psutil

from datetime import timedelta

from django.db.models import Sum, Q
from django.utils import timezone

from rest_framework.viewsets import ViewSet

from accounts.models import User

from gold_app.models import (
    GoldTransaction,
    Wallet
)

from silver_app.models import (
    SilverTransaction,
    SilverWallet
)

from .models import AdminLog
from .serializers import AdminLogSerializer
from .utils import create_admin_log


from rest_framework.permissions import IsAuthenticated


# اگر قبلا داری پاک نکن
from rest_framework.response import Response


class IsAdminRole(IsAuthenticated):
    def has_permission(self, request, view):

        return (
            request.user.is_authenticated
            and request.user.role == "admin"
        )



# =====================================================
# DASHBOARD + ANALYTICS
# =====================================================

class AdminAnalyticsViewSet(ViewSet):

    permission_classes = [IsAdminRole]

    def list(self, request):

        now = timezone.now()

        today = now.date()
        week = now - timedelta(days=7)
        month = now - timedelta(days=30)

        # -----------------
        # GOLD
        # -----------------

        gold_buy = (
            GoldTransaction.objects
            .filter(type="BUY")
            .aggregate(total=Sum("total_amount"))["total"]
            or 0
        )

        gold_sell = (
            GoldTransaction.objects
            .filter(type="SELL")
            .aggregate(total=Sum("total_amount"))["total"]
            or 0
        )

        # -----------------
        # SILVER
        # -----------------

        silver_buy = (
            SilverTransaction.objects
            .filter(type="BUY")
            .aggregate(total=Sum("total_amount"))["total"]
            or 0
        )

        silver_sell = (
            SilverTransaction.objects
            .filter(type="SELL")
            .aggregate(total=Sum("total_amount"))["total"]
            or 0
        )

        total_buy = gold_buy + silver_buy
        total_sell = gold_sell + silver_sell

        difference = total_buy - total_sell

        # -----------------
        # REPORTS
        # -----------------

        daily = (
            GoldTransaction.objects.filter(
                created_at__date=today
            ).count()
            +
            SilverTransaction.objects.filter(
                created_at__date=today
            ).count()
        )

        weekly = (
            GoldTransaction.objects.filter(
                created_at__gte=week
            ).count()
            +
            SilverTransaction.objects.filter(
                created_at__gte=week
            ).count()
        )

        monthly = (
            GoldTransaction.objects.filter(
                created_at__gte=month
            ).count()
            +
            SilverTransaction.objects.filter(
                created_at__gte=month
            ).count()
        )

        # -----------------
        # USERS
        # -----------------

        users = User.objects.count()

        # -----------------
        # WALLETS
        # -----------------

        gold_wallet = (
            Wallet.objects.aggregate(
                total=Sum("balance")
            )["total"]
            or 0
        )

        silver_wallet = (
            SilverWallet.objects.aggregate(
                total=Sum("balance")
            )["total"]
            or 0
        )

        # -----------------
        # SERVER STATUS
        # -----------------

        server = {
            "cpu": psutil.cpu_percent(),
            "ram": psutil.virtual_memory().percent,
            "disk": psutil.disk_usage("/").percent,
        }

        return Response({

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
            }
        })

# # =====================================================
# # ADMIN LOG
# # =====================================================


# class AdminLogViewSet(ViewSet):

#     permission_classes=[IsAdminRole]


#     def list(self,request):


#         qs = AdminLog.objects.all()



#         search=request.GET.get("search")

#         action=request.GET.get("action_type")



#         if search:

#             qs=qs.filter(

#                 Q(action__icontains=search)
#                 |
#                 Q(description__icontains=search)

#             )



#         if action:

#             qs=qs.filter(
#                 action_type=action
#             )



#         serializer=AdminLogSerializer(
#             qs,
#             many=True
#         )


#         return Response({

#             "count":qs.count(),

#             "results":serializer.data
#         })




#     def retrieve(self,request,pk=None):


#         obj=AdminLog.objects.get(
#             id=pk
#         )


#         return Response(
#             AdminLogSerializer(obj).data
#         )



# =====================================================
# CREATE LOG API TEST
# =====================================================


class AdminLogCreateTestView(ViewSet):


    permission_classes=[IsAdminRole]


    def create(self,request):


        log=create_admin_log(

            admin=request.user,

            action_type=request.data.get(
                "action_type",
                "ADMIN"
            ),

            action=request.data.get(
                "action",
                "test"
            ),

            model_name=request.data.get(
                "model_name",
                "system"
            ),

            description=request.data.get(
                "description"
            )

        )


        return Response({

            "message":
            "log created"

        })
        
 

class AdminLogViewSet(AdminBaseViewSet):


    queryset = AdminLog.objects.all()


    serializer_class = AdminLogSerializer



    def get_queryset(self):

        qs = super().get_queryset()



        search = self.request.GET.get(
            "search"
        )


        action_type = self.request.GET.get(
            "action_type"
        )


        start = self.request.GET.get(
            "start_date"
        )


        end = self.request.GET.get(
            "end_date"
        )



        if search:

            qs = qs.filter(

                Q(action__icontains=search)

                |

                Q(description__icontains=search)

                |

                Q(user__mobile__icontains=search)

                |

                Q(admin__mobile__icontains=search)

            )



        if action_type:

            qs = qs.filter(
                action_type=action_type
            )



        if start:

            qs = qs.filter(
                created_at__date__gte=start
            )


        if end:

            qs = qs.filter(
                created_at__date__lte=end
            )


        return qs




    def list(
        self,
        request
    ):


        qs = self.get_queryset()



        return success_response(

            "لاگ ها",

            {

                "total_results":
                    qs.count(),


                "results":
                    self.serializer_class(
                        qs,
                        many=True
                    ).data
            }
        )




    def retrieve(
        self,
        request,
        pk=None
    ):


        obj = self.get_object()



        return success_response(

            "جزئیات لاگ",

            self.serializer_class(
                obj
            ).data
        )






class AnalyticsChartAPIView(APIView):

    permission_classes = [IsAdminRole]

    def get(self, request):

        year = request.GET.get("year")
        month = request.GET.get("month")

        if not year:

            return error_response(
                "سال الزامی است."
            )

        try:

            year = int(year)

        except ValueError:

            return error_response(
                "سال نامعتبر است."
            )

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

                start_date = (
                    jdatetime.date(
                        year,
                        m,
                        1
                    ).togregorian()
                )

                if m == 12:

                    end_date = (
                        jdatetime.date(
                            year + 1,
                            1,
                            1
                        ).togregorian()
                    )

                else:

                    end_date = (
                        jdatetime.date(
                            year,
                            m + 1,
                            1
                        ).togregorian()
                    )

                gold_sales = (
                    GoldTransaction.objects.filter(
                        type="BUY",
                        created_at__date__gte=start_date,
                        created_at__date__lt=end_date
                    ).aggregate(
                        total=Sum("total_amount")
                    )["total"] or 0
                )

                silver_sales = (
                    SilverTransaction.objects.filter(
                        type="BUY",
                        created_at__date__gte=start_date,
                        created_at__date__lt=end_date
                    ).aggregate(
                        total=Sum("total_amount")
                    )["total"] or 0
                )

                result.append({
                    "month": month_names[m - 1],
                    "sales": float(
                        gold_sales + silver_sales
                    )
                })

            return success_response(
                "نمودار فروش سالانه",
                result
            )

        # =====================================
        # MONTHLY CHART
        # =====================================

        try:

            month = int(month)

        except ValueError:

            return error_response(
                "ماه نامعتبر است."
            )

        if month < 1 or month > 12:

            return error_response(
                "ماه باید بین ۱ تا ۱۲ باشد."
            )

        result = []

        for day in range(1, 32):

            try:

                current_date = (
                    jdatetime.date(
                        year,
                        month,
                        day
                    ).togregorian()
                )

            except ValueError:
                break

            gold_sales = (
                GoldTransaction.objects.filter(
                    type="BUY",
                    created_at__date=current_date
                ).aggregate(
                    total=Sum("total_amount")
                )["total"] or 0
            )

            silver_sales = (
                SilverTransaction.objects.filter(
                    type="BUY",
                    created_at__date=current_date
                ).aggregate(
                    total=Sum("total_amount")
                )["total"] or 0
            )

            result.append({
                "day": day,
                "sales": float(
                    gold_sales + silver_sales
                )
            })

        return success_response(
            "نمودار فروش ماهانه",
            result
        )

class AnalyticsPurchaseChartAPIView(APIView):

    permission_classes = [IsAdminRole]

    def get(self, request):

        year = request.GET.get("year")
        month = request.GET.get("month")

        if not year:
            return error_response(
                "سال الزامی است."
            )

        try:
            year = int(year)

        except ValueError:
            return error_response(
                "سال نامعتبر است."
            )

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

                start_date = (
                    jdatetime.date(
                        year,
                        m,
                        1
                    ).togregorian()
                )

                if m == 12:

                    end_date = (
                        jdatetime.date(
                            year + 1,
                            1,
                            1
                        ).togregorian()
                    )

                else:

                    end_date = (
                        jdatetime.date(
                            year,
                            m + 1,
                            1
                        ).togregorian()
                    )

                gold_purchase = (
                    GoldTransaction.objects.filter(
                        type="SELL",
                        created_at__date__gte=start_date,
                        created_at__date__lt=end_date
                    ).aggregate(
                        total=Sum("total_amount")
                    )["total"] or 0
                )

                silver_purchase = (
                    SilverTransaction.objects.filter(
                        type="SELL",
                        created_at__date__gte=start_date,
                        created_at__date__lt=end_date
                    ).aggregate(
                        total=Sum("total_amount")
                    )["total"] or 0
                )

                result.append({
                    "month": month_names[m - 1],
                    "purchase": float(
                        gold_purchase + silver_purchase
                    )
                })

            return success_response(
                "نمودار خرید سالانه",
                result
            )

        # =====================================
        # MONTHLY CHART
        # =====================================

        try:
            month = int(month)

        except ValueError:
            return error_response(
                "ماه نامعتبر است."
            )

        if month < 1 or month > 12:

            return error_response(
                "ماه باید بین ۱ تا ۱۲ باشد."
            )

        result = []

        for day in range(1, 32):

            try:

                current_date = (
                    jdatetime.date(
                        year,
                        month,
                        day
                    ).togregorian()
                )

            except ValueError:
                break

            gold_purchase = (
                GoldTransaction.objects.filter(
                    type="SELL",
                    created_at__date=current_date
                ).aggregate(
                    total=Sum("total_amount")
                )["total"] or 0
            )

            silver_purchase = (
                SilverTransaction.objects.filter(
                    type="SELL",
                    created_at__date=current_date
                ).aggregate(
                    total=Sum("total_amount")
                )["total"] or 0
            )

            result.append({
                "day": day,
                "purchase": float(
                    gold_purchase + silver_purchase
                )
            })

        return success_response(
            "نمودار خرید ماهانه",
            result
        )





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
        return {
            "request": self.request
        }

    def get_queryset(self):

        qs = super().get_queryset()

        search = self.request.GET.get("search")
        is_active = self.request.GET.get("is_active")
        ordering = self.request.GET.get("ordering")

        if search:
            qs = qs.filter(
                title__icontains=search
            )

        if is_active is not None:
            qs = qs.filter(
                is_active=is_active.lower() == "true"
            )

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
            qs,
            many=True,
            context=self.get_serializer_context()
        )

        return success_response(
            "لیست بنرهای طلا",
            {
                "total_results": qs.count(),
                "results": serializer.data
            }
        )

    # ======================
    # RETRIEVE
    # ======================

    def retrieve(self, request, pk=None):

        obj = self.get_object()

        return success_response(
            "جزئیات بنر",
            self.serializer_class(
                obj,
                context=self.get_serializer_context()
            ).data
        )

    # ======================
    # CREATE
    # ======================

    def create(self, request):

        serializer = self.serializer_class(
            data=request.data,
            context=self.get_serializer_context()
        )

        if not serializer.is_valid():

            first_error = next(
                iter(serializer.errors.values())
            )[0]

            return error_response(
                str(first_error)
            )

        obj = serializer.save()

        return success_response(
            "بنر ایجاد شد",
            self.serializer_class(
                obj,
                context=self.get_serializer_context()
            ).data
        )

    # ======================
    # UPDATE
    # ======================

    def update(self, request, *args, **kwargs):

        partial = kwargs.pop(
            "partial",
            False
        )

        obj = self.get_object()

        serializer = self.serializer_class(
            obj,
            data=request.data,
            partial=partial,
            context=self.get_serializer_context()
        )

        if not serializer.is_valid():

            first_error = next(
                iter(serializer.errors.values())
            )[0]

            return error_response(
                str(first_error)
            )

        obj = serializer.save()

        obj.refresh_from_db()

        return success_response(
            "بنر ویرایش شد",
            self.serializer_class(
                obj,
                context=self.get_serializer_context()
            ).data
        )

    # ======================
    # PATCH
    # ======================

    def partial_update(
        self,
        request,
        *args,
        **kwargs
    ):

        kwargs["partial"] = True

        return self.update(
            request,
            *args,
            **kwargs
        )

    # ======================
    # DELETE
    # ======================

    def destroy(
        self,
        request,
        *args,
        **kwargs
    ):

        obj = self.get_object()

        obj.delete()

        return success_response(
            "بنر حذف شد"
        )

    # ======================
    # TOGGLE ACTIVE
    # ======================

    @action(
        detail=True,
        methods=["post"]
    )
    def toggle_active(
        self,
        request,
        pk=None
    ):

        obj = self.get_object()

        obj.is_active = not obj.is_active

        obj.save()

        return success_response(
            "وضعیت تغییر کرد",
            {
                "is_active": obj.is_active
            }
        )



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
        return {
            "request": self.request
        }

    def get_queryset(self):

        qs = super().get_queryset()

        search = self.request.GET.get("search")
        is_active = self.request.GET.get("is_active")
        ordering = self.request.GET.get("ordering")

        if search:
            qs = qs.filter(
                title__icontains=search
            )

        if is_active is not None:
            qs = qs.filter(
                is_active=is_active.lower() == "true"
            )

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
            qs,
            many=True,
            context=self.get_serializer_context()
        )

        return success_response(
            "لیست بنرهای نقره",
            {
                "total_results": qs.count(),
                "results": serializer.data
            }
        )


    # ======================
    # RETRIEVE
    # ======================

    def retrieve(self, request, pk=None):

        obj = self.get_object()

        return success_response(
            "جزئیات بنر",
            self.serializer_class(
                obj,
                context=self.get_serializer_context()
            ).data
        )


    # ======================
    # CREATE
    # ======================

    def create(self, request):

        serializer = self.serializer_class(
            data=request.data,
            context=self.get_serializer_context()
        )

        if not serializer.is_valid():

            first_error = next(
                iter(serializer.errors.values())
            )[0]

            return error_response(
                str(first_error)
            )

        obj = serializer.save()


        return success_response(
            "بنر ایجاد شد",
            self.serializer_class(
                obj,
                context=self.get_serializer_context()
            ).data
        )


    # ======================
    # UPDATE
    # ======================

    def update(self, request, *args, **kwargs):

        partial = kwargs.pop(
            "partial",
            False
        )

        obj = self.get_object()


        serializer = self.serializer_class(
            obj,
            data=request.data,
            partial=partial,
            context=self.get_serializer_context()
        )


        if not serializer.is_valid():

            first_error = next(
                iter(serializer.errors.values())
            )[0]

            return error_response(
                str(first_error)
            )


        obj = serializer.save()

        obj.refresh_from_db()


        return success_response(
            "بنر ویرایش شد",
            self.serializer_class(
                obj,
                context=self.get_serializer_context()
            ).data
        )


    # ======================
    # PATCH
    # ======================

    def partial_update(
        self,
        request,
        *args,
        **kwargs
    ):

        kwargs["partial"] = True

        return self.update(
            request,
            *args,
            **kwargs
        )


    # ======================
    # DELETE
    # ======================

    def destroy(
        self,
        request,
        *args,
        **kwargs
    ):

        obj = self.get_object()

        obj.delete()


        return success_response(
            "بنر حذف شد"
        )


    # ======================
    # TOGGLE ACTIVE
    # ======================

    @action(
        detail=True,
        methods=["post"]
    )
    def toggle_active(
        self,
        request,
        pk=None
    ):

        obj = self.get_object()

        obj.is_active = not obj.is_active

        obj.save()


        return success_response(
            "وضعیت تغییر کرد",
            {
                "is_active": obj.is_active
            }
        )




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
            "id", "-id",
            "created_at", "-created_at",
            "full_name", "-full_name",
            "card_number", "-card_number",
            "sheba", "-sheba",
            "is_active", "-is_active",
        ]

        if ordering in allowed_ordering:
            qs = qs.order_by(ordering)

        return qs
    queryset = SilverBankInfo.objects.all().order_by("-id")

    serializer_class = SilverBankInfoSerializer

    create_update_serializer_class = (
        SilverBankInfoCreateUpdateSerializer
    )

    # ======================
    # LIST
    # ======================
    def list(self, request):

        qs = self.get_queryset()

        return success_response(
            "لیست کارت‌های نقره",
            {
                "total_results": qs.count(),
                "results": self.serializer_class(
                    qs,
                    many=True
                ).data
            }
        )

    # ======================
    # RETRIEVE
    # ======================
    def retrieve(self, request, pk=None):

        obj = self.get_object()

        return success_response(
            "جزئیات کارت نقره",
            self.serializer_class(obj).data
        )

    # ======================
    # CREATE
    # ======================
    def create(self, request):

        serializer = (
            self.create_update_serializer_class(
                data=request.data
            )
        )

        serializer.is_valid(
            raise_exception=True
        )

        obj = serializer.save()

        return success_response(
            "کارت نقره ساخته شد",
            self.serializer_class(obj).data
        )

    # ======================
    # UPDATE
    # ======================
    def update(
        self,
        request,
        *args,
        **kwargs
    ):

        partial = kwargs.pop(
            "partial",
            False
        )

        obj = self.get_object()

        serializer = (
            self.create_update_serializer_class(
                obj,
                data=request.data,
                partial=partial
            )
        )

        serializer.is_valid(
            raise_exception=True
        )

        obj = serializer.save()

        obj.refresh_from_db()

        return success_response(
            "کارت نقره ویرایش شد",
            self.serializer_class(obj).data
        )

    def partial_update(
        self,
        request,
        *args,
        **kwargs
    ):

        kwargs["partial"] = True

        return self.update(
            request,
            *args,
            **kwargs
        )

    # ======================
    # TOGGLE
    # ======================
    @action(
        detail=True,
        methods=["post"]
    )
    def toggle(
        self,
        request,
        pk=None
    ):

        bank = self.get_object()

        SilverBankInfo.objects.exclude(
            pk=bank.pk
        ).update(
            is_active=False
        )

        bank.is_active = True
        bank.save()

        return success_response(
            "کارت نقره فعال شد",
            {
                "is_active": True
            }
        )
        



from django.db.models import Sum
from rest_framework.views import APIView

import jdatetime

from gold_app.models import GoldTransaction
from silver_app.models import SilverTransaction


# =========================================================
# BUY SELL ANALYTICS CHART
# =========================================================

class BuySellChartAPIView(APIView):

    permission_classes = [IsAdminRole]


    def get(self, request):

        year = request.GET.get("year")
        month = request.GET.get("month")


        if not year:

            return error_response(
                "سال الزامی است."
            )


        try:

            year = int(year)

        except ValueError:

            return error_response(
                "سال نامعتبر است."
            )


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


            for m in range(1,13):


                start = jdatetime.date(
                    year,
                    m,
                    1
                ).togregorian()



                if m == 12:

                    end = jdatetime.date(
                        year + 1,
                        1,
                        1
                    ).togregorian()

                else:

                    end = jdatetime.date(
                        year,
                        m + 1,
                        1
                    ).togregorian()



                # BUY = خرید کاربر از سیستم
                gold_buy = GoldTransaction.objects.filter(
                    type="BUY",
                    created_at__date__gte=start,
                    created_at__date__lt=end
                ).aggregate(
                    total=Sum("total_amount")
                )["total"] or 0



                silver_buy = SilverTransaction.objects.filter(
                    type="BUY",
                    created_at__date__gte=start,
                    created_at__date__lt=end
                ).aggregate(
                    total=Sum("total_amount")
                )["total"] or 0



                # SELL = فروش کاربر به سیستم
                gold_sell = GoldTransaction.objects.filter(
                    type="SELL",
                    created_at__date__gte=start,
                    created_at__date__lt=end
                ).aggregate(
                    total=Sum("total_amount")
                )["total"] or 0



                silver_sell = SilverTransaction.objects.filter(
                    type="SELL",
                    created_at__date__gte=start,
                    created_at__date__lt=end
                ).aggregate(
                    total=Sum("total_amount")
                )["total"] or 0



                result.append({

                    "month": months[m-1],

                    "buy": float(
                        gold_buy + silver_buy
                    ),

                    "sell": float(
                        gold_sell + silver_sell
                    )
                })



            return success_response(
                "نمودار خرید و فروش ماهانه",
                result
            )



        # =====================================
        # DAILY
        # =====================================


        try:

            month = int(month)

        except ValueError:

            return error_response(
                "ماه نامعتبر است."
            )



        if month < 1 or month > 12:

            return error_response(
                "ماه نامعتبر است."
            )



        result = []



        for day in range(1,32):


            try:

                date = jdatetime.date(
                    year,
                    month,
                    day
                ).togregorian()


            except ValueError:

                break




            gold_buy = GoldTransaction.objects.filter(
                type="BUY",
                created_at__date=date
            ).aggregate(
                total=Sum("total_amount")
            )["total"] or 0



            silver_buy = SilverTransaction.objects.filter(
                type="BUY",
                created_at__date=date
            ).aggregate(
                total=Sum("total_amount")
            )["total"] or 0



            gold_sell = GoldTransaction.objects.filter(
                type="SELL",
                created_at__date=date
            ).aggregate(
                total=Sum("total_amount")
            )["total"] or 0



            silver_sell = SilverTransaction.objects.filter(
                type="SELL",
                created_at__date=date
            ).aggregate(
                total=Sum("total_amount")
            )["total"] or 0



            result.append({

                "day": day,

                "buy": float(
                    gold_buy + silver_buy
                ),

                "sell": float(
                    gold_sell + silver_sell
                )

            })



        return success_response(
            "نمودار خرید و فروش روزانه",
            result
        )

from rest_framework.decorators import action
from rest_framework import status
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser
from .sms_service import send_admin_note_sms

STATUS_FA = {
    "PENDING": "در انتظار",
    "APPROVED": "تایید شده",
    "REJECTED": "رد شده",
    "DONE": "انجام شده",
    "CANCELED": "لغو شده",
}


# =========================================================
# DEPOSIT
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

        allowed_ordering = ["id", "-id", "amount", "-amount", "status", "-status", "created_at", "-created_at", "updated_at", "-updated_at"]
        if ordering in allowed_ordering:
            qs = qs.order_by(ordering)

        return qs

    def list(self, request):
        qs = self.get_queryset()
        ser = FinancialTransactionSerializer(qs, many=True, context={"request": request})
        return success_response("لیست واریزها", {"total_results": qs.count(), "results": ser.data})

    def retrieve(self, request, pk=None):
        obj = self.get_object()
        return success_response("جزئیات واریز", FinancialTransactionSerializer(obj, context={"request": request}).data)

    def partial_update(self, request, *args, **kwargs):
        obj = self.get_object()

        ser = StatusUpdateSerializer(data=request.data, partial=True)
        ser.is_valid(raise_exception=True)

        new_status = ser.validated_data.get("status")
        admin_note = ser.validated_data.get("admin_note", "")

        if new_status:
            obj.status = new_status
        if admin_note:
            obj.admin_note = admin_note
        obj.save()

        sms_sent = None
        if admin_note:
            sms_sent = send_admin_note_sms(
                mobile=obj.user.mobile,
                note=admin_note
            )

        status_text = STATUS_FA.get(new_status, new_status) if new_status else "ویرایش شده"
        msg = f"وضعیت واریز به {status_text} تغییر کرد"
        if sms_sent is False:
            msg += " (ارسال پیامک ناموفق بود)"

        return success_response(
            msg,
            {
                "transaction": FinancialTransactionSerializer(obj).data,
                "sms_sent": sms_sent,
            }
        )


# =========================================================
# WITHDRAW
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

        allowed_ordering = ["id", "-id", "amount", "-amount", "status", "-status", "created_at", "-created_at", "updated_at", "-updated_at"]
        if ordering in allowed_ordering:
            qs = qs.order_by(ordering)

        return qs

    def list(self, request):
        qs = self.get_queryset()
        ser = FinancialTransactionSerializer(qs, many=True, context={"request": request})
        return success_response("لیست برداشت‌ها", {"total_results": qs.count(), "results": ser.data})

    def retrieve(self, request, pk=None):
        obj = self.get_object()
        return success_response("جزئیات برداشت", FinancialTransactionSerializer(obj, context={"request": request}).data)

    def partial_update(self, request, *args, **kwargs):
        obj = self.get_object()

        ser = StatusUpdateSerializer(data=request.data, partial=True)
        ser.is_valid(raise_exception=True)

        new_status = ser.validated_data.get("status")
        admin_note = ser.validated_data.get("admin_note", "")

        if new_status:
            obj.status = new_status
        if admin_note:
            obj.admin_note = admin_note
        obj.save()

        sms_sent = None
        if admin_note:
            sms_sent = send_admin_note_sms(
                mobile=obj.user.mobile,
                note=admin_note
            )

        status_text = STATUS_FA.get(new_status, new_status) if new_status else "ویرایش شده"
        msg = f"وضعیت برداشت به {status_text} تغییر کرد"
        if sms_sent is False:
            msg += " (ارسال پیامک ناموفق بود)"

        return success_response(
            msg,
            {
                "transaction": FinancialTransactionSerializer(obj).data,
                "sms_sent": sms_sent,
            }
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

        allowed_ordering = ["id", "-id", "amount", "-amount", "status", "-status", "created_at", "-created_at", "updated_at", "-updated_at"]
        if ordering in allowed_ordering:
            qs = qs.order_by(ordering)

        return qs

    def list(self, request):
        qs = self.get_queryset()
        ser = SilverFinancialTransactionSerializer(qs, many=True, context={"request": request})
        return success_response("لیست واریزهای نقره", {"total_results": qs.count(), "results": ser.data})

    def retrieve(self, request, pk=None):
        obj = self.get_object()
        return success_response("جزئیات واریز نقره", SilverFinancialTransactionSerializer(obj, context={"request": request}).data)

    def partial_update(self, request, *args, **kwargs):
        obj = self.get_object()

        ser = StatusUpdateSerializer(data=request.data, partial=True)
        ser.is_valid(raise_exception=True)

        new_status = ser.validated_data.get("status")
        admin_note = ser.validated_data.get("admin_note", "")

        if new_status:
            obj.status = new_status
        if admin_note:
            obj.admin_note = admin_note
        obj.save()

        sms_sent = None
        if admin_note:
            sms_sent = send_admin_note_sms(
                mobile=obj.user.mobile,
                note=admin_note
            )

        status_text = STATUS_FA.get(new_status, new_status) if new_status else "ویرایش شده"
        msg = f"وضعیت واریز نقره به {status_text} تغییر کرد"
        if sms_sent is False:
            msg += " (ارسال پیامک ناموفق بود)"

        return success_response(
            msg,
            {
                "transaction": SilverFinancialTransactionSerializer(obj).data,
                "sms_sent": sms_sent,
            }
        )


# =========================================================
# SILVER WITHDRAW
# =========================================================

class SilverWithdrawAdminViewSet(AdminBaseViewSet):

    queryset = SilverFinancialTransaction.objects.filter(type="WITHDRAW").order_by("-id")
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

        allowed_ordering = ["id", "-id", "amount", "-amount", "status", "-status", "created_at", "-created_at", "updated_at", "-updated_at"]
        if ordering in allowed_ordering:
            qs = qs.order_by(ordering)

        return qs

    def list(self, request):
        qs = self.get_queryset()
        ser = SilverFinancialTransactionSerializer(qs, many=True, context={"request": request})
        return success_response("لیست برداشت‌های نقره", {"total_results": qs.count(), "results": ser.data})

    def retrieve(self, request, pk=None):
        obj = self.get_object()
        return success_response("جزئیات برداشت نقره", SilverFinancialTransactionSerializer(obj, context={"request": request}).data)

    def partial_update(self, request, *args, **kwargs):
        obj = self.get_object()

        ser = StatusUpdateSerializer(data=request.data, partial=True)
        ser.is_valid(raise_exception=True)

        new_status = ser.validated_data.get("status")
        admin_note = ser.validated_data.get("admin_note", "")

        if new_status:
            obj.status = new_status
        if admin_note:
            obj.admin_note = admin_note
        obj.save()

        sms_sent = None
        if admin_note:
            sms_sent = send_admin_note_sms(
                mobile=obj.user.mobile,
                note=admin_note
            )

        status_text = STATUS_FA.get(new_status, new_status) if new_status else "ویرایش شده"
        msg = f"وضعیت برداشت نقره به {status_text} تغییر کرد"
        if sms_sent is False:
            msg += " (ارسال پیامک ناموفق بود)"

        return success_response(
            msg,
            {
                "transaction": SilverFinancialTransactionSerializer(obj).data,
                "sms_sent": sms_sent,
            }
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
            return error_response(
                "دریافت قیمت لحظه‌ای طلا ناموفق بود",
                code=503
            )

        return success_response(
            "قیمت لحظه‌ای طلا",
            {"results": GoldLiveSerializer(data).data}
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
            "چارت طلا",
            {"results": GoldChartDataSerializer(data).data}
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
            return error_response(
                "دریافت قیمت لحظه‌ای نقره ناموفق بود",
                code=503
            )

        return success_response(
            "قیمت لحظه‌ای نقره",
            {"results": SilverLiveSerializer(data).data}
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
            "چارت نقره",
            {"results": SilverChartDataSerializer(data).data}
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
                "results": self.serializer_class(qs, many=True, context={"request": request}).data
            }
        )

    # ======================
    # RETRIEVE
    # ======================
    def retrieve(self, request, pk=None):
        obj = self.get_object()
        return success_response(
            "جزئیات Offset طلا",
            self.serializer_class(obj, context={"request": request}).data
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

        obj = ser.save(
            set_by=request.user,
            is_active=is_active_val
        )
        
        # برای اطمینان ملخی در صورتی که سریالایزر فیلد را نادیده گرفته باشد:
        if obj.is_active != is_active_val:
            obj.is_active = is_active_val
            obj.save()

        return success_response(
            "Offset طلا ثبت شد",
            self.serializer_class(obj, context={"request": request}).data
        )

    # ======================
    # PATCH
    # ======================
    def partial_update(self, request, *args, **kwargs):
        obj = self.get_object()

        ser = self.serializer_class(
            obj,
            data=request.data,
            partial=True,
            context={"request": request}
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
            self.serializer_class(obj, context={"request": request}).data
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
                "results": self.serializer_class(qs, many=True, context={"request": request}).data
            }
        )

    # ======================
    # RETRIEVE
    # ======================
    def retrieve(self, request, pk=None):
        obj = self.get_object()
        return success_response(
            "جزئیات Offset نقره",
            self.serializer_class(obj, context={"request": request}).data
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

        obj = ser.save(
            set_by=request.user,
            is_active=is_active_val
        )

        if obj.is_active != is_active_val:
            obj.is_active = is_active_val
            obj.save()

        return success_response(
            "Offset نقره ثبت شد",
            self.serializer_class(obj, context={"request": request}).data
        )

    # ======================
    # PATCH
    # ======================
    def partial_update(self, request, *args, **kwargs):
        obj = self.get_object()

        ser = self.serializer_class(
            obj,
            data=request.data,
            partial=True,
            context={"request": request}
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
            self.serializer_class(obj, context={"request": request}).data
        )

    # ======================
    # DELETE
    # ======================
    def destroy(self, request, *args, **kwargs):
        obj = self.get_object()
        obj.delete()
        return success_response("Offset نقره حذف شد")