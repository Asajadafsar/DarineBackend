from rest_framework.viewsets import ModelViewSet, ViewSet
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db.models import Sum
from django.db import transaction

from accounts.models import User, UserFee
from gold_app.models import *
from silver_app.models import *
from .serializers import *
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

        # ----------------------
        # USER UPDATE
        # ----------------------
        serializer = AdminUserUpdateSerializer(
            user,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        # ----------------------
        # FEES UPDATE (FIXED FLEXIBLE INPUT)
        # ----------------------

        fee, _ = UserFee.objects.get_or_create(user=user)

        # 1) nested mode
        fee_data = request.data.get("fees")

        # 2) flat mode fallback
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

        # فقط اگر چیزی برای آپدیت وجود داشت
        if fee_data:
            fee_serializer = UserFeeUpdateSerializer(
                fee,
                data=fee_data,
                partial=True
            )
            fee_serializer.is_valid(raise_exception=True)
            fee_serializer.save()

        # ----------------------
        # FORCE SYNC
        # ----------------------
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
# PRODUCT (GOLD)
# =========================================================

class ProductAdminViewSet(AdminBaseViewSet):
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

        ser = SilverProductSerializer(
            obj,
            context=self.get_serializer_context()
        )

        return success_response(
            "جزئیات محصول نقره",
            ser.data
        )

    # ======================
    # CREATE (FIX مهم)
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
            SilverProductSerializer(obj, context=self.get_serializer_context()).data
        )

    # ======================
    # UPDATE
    # ======================
    def update(self, request, *args, **kwargs):

        obj = self.get_object()

        ser = SilverProductCreateUpdateSerializer(
            obj,
            data=request.data,
            partial=kwargs.pop("partial", False),
            context=self.get_serializer_context()
        )

        ser.is_valid(raise_exception=True)
        obj = ser.save()

        return success_response(
            "محصول نقره ویرایش شد",
            SilverProductSerializer(obj, context=self.get_serializer_context()).data
        )

    def partial_update(self, request, *args, **kwargs):
        kwargs["partial"] = True
        return self.update(request, *args, **kwargs)
    



# =========================================================
# GIFT CARD
# =========================================================

class GiftCardAdminViewSet(AdminBaseViewSet):
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
    # LIST
    # ======================
    def list(self, request):
        qs = self.get_queryset()

        return success_response(
            "لیست سفارشات نقره",
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
            "جزئیات سفارش نقره",
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
            "وضعیت سفارش نقره تغییر کرد",
            self.serializer_class(obj).data
        )

# =========================================================
# DASHBOARD
# =========================================================

class DashboardAdminViewSet(ViewSet):
    permission_classes = [IsAdminRole]

    def list(self, request):

        return success_response("داشبورد", {
            "users": User.objects.count(),
            "products": Product.objects.count(),
            "silver_products": SilverProduct.objects.count(),
            "orders": Order.objects.count(),
            "silver_orders": SilverOrder.objects.count(),
            "wallet_balance": Wallet.objects.aggregate(total=Sum("balance"))["total"] or 0,
        })


class GoldBankAdminViewSet(AdminBaseViewSet):
    queryset = GoldBankInfo.objects.all().order_by("-id")
    serializer_class = GoldBankInfoSerializer

    # ======================
    # LIST
    # ======================
    def list(self, request):
        qs = self.get_queryset()

        return success_response(
            "لیست کارت‌های طلا",
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
            "جزئیات کارت طلا",
            self.serializer_class(obj).data
        )

    # ======================
    # CREATE
    # ======================
    def create(self, request):
        ser = self.serializer_class(data=request.data)
        ser.is_valid(raise_exception=True)
        obj = ser.save()

        return success_response("کارت طلا ساخته شد", self.serializer_class(obj).data)

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
            "کارت طلا ویرایش شد",
            self.serializer_class(obj).data
        )

    def partial_update(self, request, *args, **kwargs):
        kwargs["partial"] = True
        return self.update(request, *args, **kwargs)

    # ======================
    # TOGGLE
    # ======================
    @action(detail=True, methods=["post"])
    def toggle(self, request, pk=None):
        bank = self.get_object()

        GoldBankInfo.objects.exclude(pk=pk).update(is_active=False)
        bank.is_active = True
        bank.save()

        return success_response(
            "کارت طلا فعال شد",
            {"is_active": bank.is_active}
        )
    

    
class SilverBankAdminViewSet(AdminBaseViewSet):
    queryset = SilverBankInfo.objects.all().order_by("-id")
    serializer_class = SilverBankInfoSerializer

    # ======================
    # LIST
    # ======================
    def list(self, request):
        qs = self.get_queryset()

        return success_response(
            "لیست کارت‌های نقره",
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
            "جزئیات کارت نقره",
            self.serializer_class(obj).data
        )

    # ======================
    # CREATE
    # ======================
    def create(self, request):
        ser = self.serializer_class(data=request.data)
        ser.is_valid(raise_exception=True)
        obj = ser.save()

        return success_response("کارت نقره ساخته شد", self.serializer_class(obj).data)

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
            "کارت نقره ویرایش شد",
            self.serializer_class(obj).data
        )

    def partial_update(self, request, *args, **kwargs):
        kwargs["partial"] = True
        return self.update(request, *args, **kwargs)

    # ======================
    # TOGGLE
    # ======================
    @action(detail=True, methods=["post"])
    def toggle(self, request, pk=None):
        bank = self.get_object()

        SilverBankInfo.objects.exclude(pk=pk).update(is_active=False)
        bank.is_active = True
        bank.save()

        return success_response(
            "کارت نقره فعال شد",
            {"is_active": bank.is_active}
        )