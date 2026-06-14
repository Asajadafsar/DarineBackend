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
from django.db.models import Q
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser



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
            qs = qs.filter(
                mobile__icontains=mobile
            )

        if search:
            qs = qs.filter(
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search)
            )

        if national_code:
            qs = qs.filter(
                national_code__icontains=national_code
            )
        allowed_ordering = ["id", "-id", "created_at", "-created_at","first_name", "-first_name","last_name", "-last_name","mobile", "-mobile",]
        if ordering in allowed_ordering:
            
            qs = qs.order_by(ordering)
         
        return qs
    
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



class CooperationRequestAdminViewSet(AdminBaseViewSet):

    queryset = CooperationRequest.objects.all().order_by("-id")

    def get_queryset(self):

        qs = super().get_queryset()

        search = self.request.GET.get("search")
        mobile = self.request.GET.get("mobile")

        if search:
            qs = qs.filter(
                full_name__icontains=search
            )

        if mobile:
            qs = qs.filter(
                mobile__icontains=mobile
            )

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
            qs = qs.filter(
                name__icontains=search
            )

        if weight:
            qs = qs.filter(
                weight=weight
            )

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

    def get_queryset(self):

        qs = super().get_queryset()

        name = self.request.GET.get("name")
        ordering = self.request.GET.get("ordering")

        if name:
            qs = qs.filter(
                name__icontains=name
            )
        allowed_ordering = ["id", "-id", "created_at", "-created_at","name", "-name",]
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

    def get_queryset(self):

        qs = super().get_queryset()

        search = self.request.GET.get("search")
        weight = self.request.GET.get("weight")
        ordering = self.request.GET.get("ordering")

        if search:
            qs = qs.filter(
                name__icontains=search
            )

        if weight:
            qs = qs.filter(
                weight=weight
            )
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
        allowed_ordering = ["id", "-id", "created_at", "-created_at","first_name", "status", "-status","serial_number", "-serial_number",]
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

    def get_queryset(self):

        qs = super().get_queryset()

        search = self.request.GET.get("search")
        status = self.request.GET.get("status")
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

    def get_queryset(self):

        qs = super().get_queryset()

        search = self.request.GET.get("search")
        card_number = self.request.GET.get("card_number")
        iban = self.request.GET.get("iban")
        ordering = self.request.GET.get("ordering")

        if search:
            qs = qs.filter(
                full_name__icontains=search
            )

        if card_number:
            qs = qs.filter(
                card_number__icontains=card_number
            )

        if iban:
            qs = qs.filter(
                sheba__icontains=iban
            )
        allowed_ordering = ["id", "-id", "created_at", "-created_at","full_name", "-full_name","card_number", "-card_number",]
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
    




class SilverBankAdminViewSet(AdminBaseViewSet):

    queryset = SilverBankInfo.objects.all().order_by("-id")

    def get_queryset(self):

        qs = super().get_queryset()

        search = self.request.GET.get("search")
        card_number = self.request.GET.get("card_number")
        iban = self.request.GET.get("iban")
        ordering = self.request.GET.get("ordering")

        if search:
            qs = qs.filter(
                full_name__icontains=search
            )

        if card_number:
            qs = qs.filter(
                card_number__icontains=card_number
            )

        if iban:
            qs = qs.filter(
                sheba__icontains=iban
            )
        allowed_ordering = ["id", "-id", "created_at", "-created_at","full_name", "-full_name","card_number", "-card_number",]
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
        
        
        
class DepositAdminViewSet(AdminBaseViewSet):

    queryset = FinancialTransaction.objects.filter(type="DEPOSIT").order_by("-id")
    serializer_class = FinancialTransactionSerializer
    parser_classes = (MultiPartParser, FormParser)

    # ======================
    # QUERYSET (FILTER + SEARCH + SORT)
    # ======================
    def get_queryset(self):

        qs = super().get_queryset()

        search = self.request.GET.get("search")
        status = self.request.GET.get("status")
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

        if start_date:
            qs = qs.filter(created_at__date__gte=start_date)

        if end_date:
            qs = qs.filter(created_at__date__lte=end_date)

        allowed_ordering = [
            "id", "-id",
            "amount", "-amount",
            "status", "-status",
            "created_at", "-created_at",
            "updated_at", "-updated_at",
        ]

        if ordering in allowed_ordering:
            qs = qs.order_by(ordering)

        return qs

    # ======================
    # LIST
    # ======================
    def list(self, request):

        qs = self.get_queryset()

        ser = FinancialTransactionSerializer(
            qs,
            many=True,
            context={"request": request}
        )

        return success_response(
            "لیست واریزها",
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
            "جزئیات واریز",
            FinancialTransactionSerializer(
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

        if ser.validated_data.get("admin_note"):
            obj.admin_note = ser.validated_data["admin_note"]

        obj.save()

        return success_response(
            "وضعیت واریز تغییر کرد",
            FinancialTransactionSerializer(obj).data
        )
        
        
class WithdrawAdminViewSet(AdminBaseViewSet):

    queryset = FinancialTransaction.objects.filter(type="WITHDRAW").order_by("-id")
    serializer_class = FinancialTransactionSerializer
    parser_classes = (MultiPartParser, FormParser)

    def get_queryset(self):

        qs = super().get_queryset()

        search = self.request.GET.get("search")
        status = self.request.GET.get("status")
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

        if start_date:
            qs = qs.filter(created_at__date__gte=start_date)

        if end_date:
            qs = qs.filter(created_at__date__lte=end_date)

        allowed_ordering = [
            "id", "-id",
            "amount", "-amount",
            "status", "-status",
            "created_at", "-created_at",
            "updated_at", "-updated_at",
        ]

        if ordering in allowed_ordering:
            qs = qs.order_by(ordering)

        return qs

    # ======================
    # LIST
    # ======================
    def list(self, request):

        qs = self.get_queryset()

        ser = FinancialTransactionSerializer(
            qs,
            many=True,
            context={"request": request}
        )

        return success_response(
            "لیست برداشت‌ها",
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
            "جزئیات برداشت",
            FinancialTransactionSerializer(
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

        if ser.validated_data.get("admin_note"):
            obj.admin_note = ser.validated_data["admin_note"]

        obj.save()

        return success_response(
            "وضعیت برداشت تغییر کرد",
            FinancialTransactionSerializer(obj).data
        )
        
        
        
class SilverDepositAdminViewSet(AdminBaseViewSet):

    queryset = SilverFinancialTransaction.objects.filter(type="DEPOSIT").order_by("-id")
    serializer_class = SilverFinancialTransactionSerializer
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    def get_queryset(self):

        qs = super().get_queryset()

        search = self.request.GET.get("search")
        status = self.request.GET.get("status")
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

        if start_date:
            qs = qs.filter(created_at__date__gte=start_date)

        if end_date:
            qs = qs.filter(created_at__date__lte=end_date)

        allowed_ordering = [
            "id", "-id",
            "amount", "-amount",
            "status", "-status",
            "created_at", "-created_at",
            "updated_at", "-updated_at",
        ]

        if ordering in allowed_ordering:
            qs = qs.order_by(ordering)

        return qs

    # ======================
    # LIST
    # ======================
    def list(self, request):

        qs = self.get_queryset()

        ser = SilverFinancialTransactionSerializer(
            qs,
            many=True,
            context={"request": request}
        )

        return success_response(
            "لیست واریزهای نقره",
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
            "جزئیات واریز نقره",
            SilverFinancialTransactionSerializer(
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

        if ser.validated_data.get("admin_note"):
            obj.admin_note = ser.validated_data["admin_note"]

        obj.save()

        return success_response(
            "وضعیت واریز نقره تغییر کرد",
            SilverFinancialTransactionSerializer(obj).data
        )
        
        
class SilverWithdrawAdminViewSet(AdminBaseViewSet):

    queryset = SilverFinancialTransaction.objects.filter(type="WITHDRAW").order_by("-id")
    serializer_class = SilverFinancialTransactionSerializer
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    def get_queryset(self):

        qs = super().get_queryset()

        search = self.request.GET.get("search")
        status = self.request.GET.get("status")
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

        if start_date:
            qs = qs.filter(created_at__date__gte=start_date)

        if end_date:
            qs = qs.filter(created_at__date__lte=end_date)

        allowed_ordering = [
            "id", "-id",
            "amount", "-amount",
            "status", "-status",
            "created_at", "-created_at",
            "updated_at", "-updated_at",
        ]

        if ordering in allowed_ordering:
            qs = qs.order_by(ordering)

        return qs

    # ======================
    # LIST
    # ======================
    def list(self, request):

        qs = self.get_queryset()

        ser = SilverFinancialTransactionSerializer(
            qs,
            many=True,
            context={"request": request}
        )

        return success_response(
            "لیست برداشت‌های نقره",
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
            "جزئیات برداشت نقره",
            SilverFinancialTransactionSerializer(
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

        if ser.validated_data.get("admin_note"):
            obj.admin_note = ser.validated_data["admin_note"]

        obj.save()

        return success_response(
            "وضعیت برداشت نقره تغییر کرد",
            SilverFinancialTransactionSerializer(obj).data
        )