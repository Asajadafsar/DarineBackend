from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from accounts.models import User, UserFee
from .serializers import (
    AdminUserListSerializer,
    AdminUserDetailSerializer,
    AdminUserUpdateSerializer
)
from rest_framework.parsers import MultiPartParser, FormParser
from silver_app.models import SilverProduct, SilverProductCategory
from .serializers import (
    SilverProductSerializer,
    SilverProductCreateUpdateSerializer,
    SilverProductCategorySerializer
)

from gold_app.models import Product, ProductCategory
from .serializers import (
    ProductSerializer,
    ProductCreateUpdateSerializer,
    ProductCategorySerializer
)
from .permissions import IsAdminRole
from django.shortcuts import get_object_or_404
from decimal import Decimal
from rest_framework import serializers





# =========================================================
# RESPONSE BASE
# =========================================================

def success_response(message="OK", data=None, status_code=200):

    if data is None:
        data = {
            "total_results": 0,
            "results": []
        }

    return Response(
        {
            "success": True,
            "message": message,
            "data": data
        },
        status=status_code
    )


def error_response(message="error", data=None, status_code=400):

    if data is None:
        data = {
            "total_results": 0,
            "results": []
        }

    return Response(
        {
            "success": False,
            "message": message,
            "data": data
        },
        status=status_code
    )


# =========================================================
# helper: attach fee
# =========================================================

def attach_fee(user):
    fee, _ = UserFee.objects.get_or_create(user=user)
    return {
        "gold_buy_fee": fee.gold_buy_fee,
        "gold_sell_fee": fee.gold_sell_fee,
        "silver_buy_fee": fee.silver_buy_fee,
        "silver_sell_fee": fee.silver_sell_fee,
    }



# =========================================================
# 1. USERS LIST
# =========================================================

class AdminUserListAPIView(APIView):

    permission_classes = [IsAdminRole]

    def get(self, request):

        users = User.objects.all().order_by("-id")

        results = []

        for user in users:

            user_data = AdminUserListSerializer(user).data
            user_data["fees"] = attach_fee(user)

            results.append(user_data)

        return success_response(
            message="لیست کاربران",
            results=results
        )


# =========================================================
# 2. USER DETAIL
# =========================================================

class AdminUserDetailAPIView(APIView):

    permission_classes = [IsAdminRole]

    def get(self, request, user_id):

        user = User.objects.filter(id=user_id).first()

        if not user:
            return error_response("کاربر یافت نشد")

        data = AdminUserDetailSerializer(user).data
        data["fees"] = attach_fee(user)

        return success_response(
            message="جزئیات کاربر",
            results=data
        )


# =========================================================
# 3. USER UPDATE (including fees)
# =========================================================

class AdminUserUpdateAPIView(APIView):

    permission_classes = [IsAdminRole]

    def put(self, request, user_id):

        user = User.objects.filter(id=user_id).first()

        if not user:
            return error_response("کاربر یافت نشد")

        serializer = AdminUserUpdateSerializer(
            user,
            data=request.data,
            partial=True
        )

        if serializer.is_valid():

            serializer.save()

            # =========================
            # UPDATE FEES IF EXISTS
            # =========================
            fee_data = request.data.get("fees")

            if fee_data:

                fee_obj, _ = UserFee.objects.get_or_create(user=user)

                fee_obj.gold_buy_fee = fee_data.get("gold_buy_fee", fee_obj.gold_buy_fee)
                fee_obj.gold_sell_fee = fee_data.get("gold_sell_fee", fee_obj.gold_sell_fee)
                fee_obj.silver_buy_fee = fee_data.get("silver_buy_fee", fee_obj.silver_buy_fee)
                fee_obj.silver_sell_fee = fee_data.get("silver_sell_fee", fee_obj.silver_sell_fee)

                fee_obj.save()

            data = AdminUserDetailSerializer(user).data
            data["fees"] = attach_fee(user)

            return success_response(
                message="کاربر ویرایش شد",
                results=data
            )

        return error_response("خطا در ویرایش", data=serializer.errors)


# =========================================================
# 4. DELETE USER
# =========================================================

class AdminUserDeleteAPIView(APIView):

    permission_classes = [IsAdminRole]

    def delete(self, request, user_id):

        user = User.objects.filter(id=user_id).first()

        if not user:
            return error_response("کاربر یافت نشد")

        user.delete()

        return success_response(
            message="کاربر حذف شد",
            results=[]
        )


# =========================================================
# 5. TOGGLE ACTIVE
# =========================================================

class AdminUserToggleActiveAPIView(APIView):

    permission_classes = [IsAdminRole]

    def post(self, request, user_id):

        user = User.objects.filter(id=user_id).first()

        if not user:
            return error_response("کاربر یافت نشد")

        user.is_active = not user.is_active
        user.save()

        return success_response(
            message="وضعیت کاربر تغییر کرد",
            results={"is_active": user.is_active}
        )
    

# =========================================================
# PRODUCT LIST
# =========================================================

class AdminProductListAPIView(APIView):

    permission_classes = [IsAdminRole]

    def get(self, request):

        products = Product.objects.all().order_by("-id")

        serializer = ProductSerializer(products, many=True)

        return success_response(
            message="لیست محصولات",
            data={
                "total_results": products.count(),
                "results": serializer.data
            }
        )


# =========================================================
# PRODUCT DETAIL (products/1/)
# =========================================================

class AdminProductDetailAPIView(APIView):

    permission_classes = [IsAdminRole]

    def get(self, request, pk):

        product = get_object_or_404(Product, pk=pk)

        serializer = ProductSerializer(product)

        return success_response(
            message="جزئیات محصول",
            data={
                "total_results": 1,
                "results": [serializer.data]
            }
        )


# =========================================================
# PRODUCT CREATE
# =========================================================

class AdminProductCreateAPIView(APIView):

    permission_classes = [IsAdminRole]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):

        serializer = ProductCreateUpdateSerializer(data=request.data)

        if serializer.is_valid():

            product = serializer.save()

            return success_response(
                message="محصول ساخته شد",
                data={
                    "total_results": 1,
                    "results": [ProductSerializer(product).data]
                }
            )

        return error_response("خطا در ساخت محصول", data=serializer.errors)

# =========================================================
# PRODUCT UPDATE (FIXED)
# =========================================================

class AdminProductUpdateAPIView(APIView):

    permission_classes = [IsAdminRole]
    parser_classes = [MultiPartParser, FormParser]

    def put(self, request, pk):

        product = get_object_or_404(Product, pk=pk)

        serializer = ProductCreateUpdateSerializer(
            instance=product,
            data=request.data,
            partial=True,
            context={"request": request}
        )

        try:

            if serializer.is_valid(raise_exception=True):

                product = serializer.save()

                return success_response(
                    message="محصول ویرایش شد",
                    results={
                        "total_results": 1,
                        "results": ProductSerializer(product).data
                    }
                )

        except Exception as e:

            return error_response(
                message="خطا در ویرایش محصول",
                data={"error": str(e)}
            )
        

# =========================================================
# PRODUCT DELETE
# =========================================================

class AdminProductDeleteAPIView(APIView):

    permission_classes = [IsAdminRole]

    def delete(self, request, pk):

        product = get_object_or_404(Product, pk=pk)
        product.delete()

        return success_response(
            message="محصول حذف شد",
            data={"total_results": 0, "results": []}
        )
    
# =========================================================
# CATEGORY LIST
# =========================================================

class AdminCategoryListAPIView(APIView):

    permission_classes = [IsAdminRole]

    def get(self, request):

        cats = ProductCategory.objects.all()

        serializer = ProductCategorySerializer(cats, many=True)

        return success_response(
            message="لیست دسته‌بندی‌ها",
            data={
                "total_results": cats.count(),
                "results": serializer.data
            }
        )


# =========================================================
# CATEGORY CREATE
# =========================================================

class AdminCategoryCreateAPIView(APIView):

    permission_classes = [IsAdminRole]

    def post(self, request):

        serializer = ProductCategorySerializer(data=request.data)

        if serializer.is_valid():

            cat = serializer.save()

            return success_response(
                message="دسته‌بندی ساخته شد",
                data={
                    "total_results": 1,
                    "results": [serializer.data]
                }
            )

        return error_response("خطا در ساخت دسته‌بندی", data=serializer.errors)


# =========================================================
# CATEGORY DELETE
# =========================================================

class AdminCategoryDeleteAPIView(APIView):

    permission_classes = [IsAdminRole]

    def delete(self, request, pk):

        cat = get_object_or_404(ProductCategory, pk=pk)
        cat.delete()

        return success_response(
            message="دسته‌بندی حذف شد",
            data={"total_results": 0, "results": []}
        )
    


class AdminSilverProductListAPIView(APIView):

    permission_classes = [IsAdminRole]

    def get(self, request):

        products = SilverProduct.objects.all().order_by("-id")

        serializer = SilverProductSerializer(products, many=True)

        return success_response(
            message="لیست محصولات نقره",
            data={
                "total_results": products.count(),
                "results": serializer.data
            }
        )
    


class AdminSilverProductDetailAPIView(APIView):

    permission_classes = [IsAdminRole]

    def get(self, request, pk):

        product = get_object_or_404(SilverProduct, pk=pk)

        serializer = SilverProductSerializer(product)

        return success_response(
            message="جزئیات محصول نقره",
            data={
                "total_results": 1,
                "results": [serializer.data]
            }
        )
    


class AdminSilverProductCreateAPIView(APIView):

    permission_classes = [IsAdminRole]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):

        serializer = SilverProductCreateUpdateSerializer(data=request.data)

        if serializer.is_valid():

            product = serializer.save()

            return success_response(
                message="محصول نقره ساخته شد",
                data={
                    "total_results": 1,
                    "results": [SilverProductSerializer(product).data]
                }
            )

        return error_response(
            "خطا در ساخت محصول",
            data=serializer.errors
        )
    


class AdminSilverProductUpdateAPIView(APIView):

    permission_classes = [IsAdminRole]
    parser_classes = [MultiPartParser, FormParser]

    def put(self, request, pk):

        product = get_object_or_404(SilverProduct, pk=pk)

        serializer = SilverProductCreateUpdateSerializer(
            instance=product,
            data=request.data,
            partial=True
        )

        try:
            serializer.is_valid(raise_exception=True)

            product = serializer.save()

            return success_response(
                message="محصول نقره ویرایش شد",
                data={
                    "total_results": 1,
                    "results": [SilverProductSerializer(product).data]
                }
            )

        except Exception as e:

            return error_response(
                "خطا در ویرایش محصول",
                data={"error": str(e)}
            )
        


class AdminSilverProductDeleteAPIView(APIView):

    permission_classes = [IsAdminRole]

    def delete(self, request, pk):

        product = get_object_or_404(SilverProduct, pk=pk)
        product.delete()

        return success_response(
            message="محصول حذف شد",
            data={"total_results": 0, "results": []}
        )
    


class AdminSilverCategoryListAPIView(APIView):

    permission_classes = [IsAdminRole]

    def get(self, request):

        cats = SilverProductCategory.objects.all()

        serializer = SilverProductCategorySerializer(cats, many=True)

        return success_response(
            message="لیست دسته‌بندی نقره",
            data={
                "total_results": cats.count(),
                "results": serializer.data
            }
        )




class AdminSilverCategoryCreateAPIView(APIView):

    permission_classes = [IsAdminRole]

    def post(self, request):

        serializer = SilverProductCategorySerializer(data=request.data)

        if serializer.is_valid():

            cat = serializer.save()

            return success_response(
                message="دسته‌بندی نقره ساخته شد",
                data={
                    "total_results": 1,
                    "results": [serializer.data]
                }
            )

        return error_response(
            "خطا در ساخت دسته‌بندی",
            data=serializer.errors
        )
    


class AdminSilverCategoryDeleteAPIView(APIView):

    permission_classes = [IsAdminRole]

    def delete(self, request, pk):

        cat = get_object_or_404(SilverProductCategory, pk=pk)
        cat.delete()

        return success_response(
            message="دسته‌بندی حذف شد",
            data={"total_results": 0, "results": []}
        )
    

