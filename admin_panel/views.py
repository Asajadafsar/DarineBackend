from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from accounts.models import User, UserFee
from silver_app.serializers import SilverTransactionSerializer
from .serializers import (
    AdminUserListSerializer,
    AdminUserDetailSerializer,
    AdminUserUpdateSerializer,
    GiftCardCreateUpdateSerializer,
    GiftCardOrderSerializer,
    GiftCardSerializer,
    GoldBankInfoSerializer,
    GoldTransactionSerializer,
    OrderSerializer,
    SilverBankInfoSerializer,
    SilverFinancialTransactionSerializer,
    SilverOrderSerializer,
    StatusUpdateSerializer
)
from rest_framework.parsers import MultiPartParser, FormParser
from silver_app.models import SilverBankInfo, SilverFinancialTransaction, SilverOrder, SilverProduct, SilverProductCategory, SilverTransaction
from .serializers import (
    SilverProductSerializer,
    SilverProductCreateUpdateSerializer,
    SilverProductCategorySerializer
)
from .serializers import FinancialTransactionSerializer
from gold_app.models import FinancialTransaction, GiftCard, GiftCardOrder, GoldBankInfo, GoldTransaction, Order, Product, ProductCategory
from .serializers import (
    ProductSerializer,
    ProductCreateUpdateSerializer,
    ProductCategorySerializer
)
from .permissions import IsAdminRole
from django.shortcuts import get_object_or_404
from decimal import Decimal
from rest_framework import serializers
from django.db.models import Sum
from rest_framework.views import APIView

from accounts.models import User

from gold_app.models import (
    Wallet,
    GoldInventory,
    Product,
    Order,
    FinancialTransaction,
)

from silver_app.models import (
    SilverWallet,
    SilverInventory,
    SilverProduct,
    SilverOrder,
    SilverFinancialTransaction,
)
from django.db import transaction
from .permissions import IsAdminRole




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
    

class AdminGiftCardListAPIView(APIView):

    permission_classes = [IsAdminRole]

    def get(self, request):

        status_filter = request.GET.get("status")

        cards = GiftCard.objects.all().order_by("-id")

        if status_filter:
            cards = cards.filter(status=status_filter)

        serializer = GiftCardSerializer(cards, many=True)

        return success_response(
            message="لیست گیفت کارت‌ها",
            data={
                "total_results": cards.count(),
                "results": serializer.data
            }
        )
    

class AdminGiftCardDetailAPIView(APIView):

    permission_classes = [IsAdminRole]

    def get(self, request, pk):

        card = get_object_or_404(GiftCard, pk=pk)

        serializer = GiftCardSerializer(card)

        return success_response(
            message="جزئیات گیفت کارت",
            data={
                "total_results": 1,
                "results": [serializer.data]
            }
        )
    

class AdminGiftCardCreateAPIView(APIView):

    permission_classes = [IsAdminRole]

    def post(self, request):

        serializer = GiftCardCreateUpdateSerializer(data=request.data)

        if serializer.is_valid():

            card = serializer.save(
                created_by=request.user,
                status="ACTIVE",
                is_used=False
            )

            return success_response(
                message="گیفت کارت ساخته شد",
                data={
                    "total_results": 1,
                    "results": [GiftCardSerializer(card).data]
                }
            )

        return error_response("خطا در ساخت گیفت کارت", data=serializer.errors)
    


class AdminGiftCardUpdateAPIView(APIView):

    permission_classes = [IsAdminRole]

    def put(self, request, pk):

        card = get_object_or_404(GiftCard, pk=pk)

        serializer = GiftCardCreateUpdateSerializer(
            instance=card,
            data=request.data,
            partial=True
        )

        if serializer.is_valid():

            card = serializer.save()

            return success_response(
                message="گیفت کارت ویرایش شد",
                data={
                    "total_results": 1,
                    "results": [GiftCardSerializer(card).data]
                }
            )

        return error_response("خطا در ویرایش", data=serializer.errors)
    

class AdminGiftCardDeleteAPIView(APIView):

    permission_classes = [IsAdminRole]

    def delete(self, request, pk):

        card = get_object_or_404(GiftCard, pk=pk)
        card.delete()

        return success_response(
            message="گیفت کارت حذف شد",
            data={"total_results": 0, "results": []}
        )
    


class AdminGiftCardChangeStatusAPIView(APIView):

    permission_classes = [IsAdminRole]

    def post(self, request, pk):

        card = get_object_or_404(GiftCard, pk=pk)

        new_status = request.data.get("status")

        if new_status not in ["ACTIVE", "USED", "EXPIRED"]:
            return error_response("status نامعتبر است")

        card.status = new_status

        if new_status == "USED":
            card.is_used = True

        card.save()

        return success_response(
            message="وضعیت تغییر کرد",
            data={
                "total_results": 1,
                "results": [GiftCardSerializer(card).data]
            }
        )
    


class AdminGiftCardOrderListAPIView(APIView):

    permission_classes = [IsAdminRole]

    def get(self, request):

        qs = GiftCardOrder.objects.all().order_by("-id")

        serializer = GiftCardOrderSerializer(qs, many=True)

        return success_response(
            message="لیست سفارش گیفت کارت",
            data={
                "total_results": qs.count(),
                "results": serializer.data
            }
        )



class AdminGiftCardOrderStatusAPIView(APIView):

    permission_classes = [IsAdminRole]

    def post(self, request, pk):

        order = get_object_or_404(GiftCardOrder, pk=pk)

        serializer = StatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        order.status = serializer.validated_data["status"]
        order.save()

        return success_response(
            message="وضعیت سفارش تغییر کرد",
            data={
                "total_results": 1,
                "results": GiftCardOrderSerializer(order).data
            }
        )




class AdminOrderListAPIView(APIView):

    permission_classes = [IsAdminRole]

    def get(self, request):

        qs = Order.objects.prefetch_related("items").all().order_by("-id")

        serializer = OrderSerializer(qs, many=True)

        return success_response(
            message="لیست سفارشات",
            data={
                "total_results": qs.count(),
                "results": serializer.data
            }
        )
    



class AdminOrderStatusAPIView(APIView):

    permission_classes = [IsAdminRole]

    def post(self, request, pk):

        order = get_object_or_404(Order, pk=pk)

        serializer = StatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        order.status = serializer.validated_data["status"]
        order.save()

        return success_response(
            message="وضعیت سفارش تغییر کرد",
            data={
                "total_results": 1,
                "results": OrderSerializer(order).data
            }
        )
    



class AdminFinancialListAPIView(APIView):

    permission_classes = [IsAdminRole]

    def get(self, request):

        qs = FinancialTransaction.objects.all().order_by("-id")

        serializer = FinancialTransactionSerializer(qs, many=True)

        return success_response(
            message="لیست تراکنش‌ها",
            data={
                "total_results": qs.count(),
                "results": serializer.data
            }
        )



class AdminFinancialStatusAPIView(APIView):

    permission_classes = [IsAdminRole]

    def post(self, request, pk):

        tx = get_object_or_404(FinancialTransaction, pk=pk)

        serializer = StatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        tx.status = serializer.validated_data["status"]
        tx.admin_note = serializer.validated_data.get("admin_note", "")
        tx.save()

        return success_response(
            message="وضعیت تراکنش تغییر کرد",
            data={
                "total_results": 1,
                "results": FinancialTransactionSerializer(tx).data
            }
        )
    

class AdminGoldTransactionListAPIView(APIView):

    permission_classes = [IsAdminRole]

    def get(self, request):

        qs = GoldTransaction.objects.all().order_by("-id")

        serializer = GoldTransactionSerializer(qs, many=True)

        return success_response(
            message="لیست معاملات طلا",
            data={
                "total_results": qs.count(),
                "results": serializer.data
            }
        )
    

class AdminGoldTransactionStatusAPIView(APIView):

    permission_classes = [IsAdminRole]

    def post(self, request, pk):

        tx = get_object_or_404(GoldTransaction, pk=pk)

        serializer = StatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        tx.status = serializer.validated_data["status"]
        tx.save()

        return success_response(
            message="وضعیت معامله تغییر کرد",
            data={
                "total_results": 1,
                "results": GoldTransactionSerializer(tx).data
            }
        )
    


class AdminSilverOrderListAPIView(APIView):

    permission_classes = [IsAdminRole]

    def get(self, request):

        qs = SilverOrder.objects.prefetch_related("items").all().order_by("-id")

        serializer = SilverOrderSerializer(qs, many=True)

        return success_response(
            message="لیست سفارشات نقره",
            data={
                "total_results": qs.count(),
                "results": serializer.data
            }
        )
    

class AdminSilverOrderStatusAPIView(APIView):

    permission_classes = [IsAdminRole]

    def post(self, request, pk):

        order = get_object_or_404(SilverOrder, pk=pk)

        serializer = StatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        order.status = serializer.validated_data["status"]
        order.save()

        return success_response(
            message="وضعیت سفارش تغییر کرد",
            data={
                "total_results": 1,
                "results": SilverOrderSerializer(order).data
            }
        )
    


class AdminSilverFinancialListAPIView(APIView):

    permission_classes = [IsAdminRole]

    def get(self, request):

        qs = SilverFinancialTransaction.objects.all().order_by("-id")

        serializer = SilverFinancialTransactionSerializer(qs, many=True)

        return success_response(
            message="لیست تراکنش‌های نقره",
            data={
                "total_results": qs.count(),
                "results": serializer.data
            }
        )
    

class AdminSilverFinancialStatusAPIView(APIView):

    permission_classes = [IsAdminRole]

    def post(self, request, pk):

        tx = get_object_or_404(SilverFinancialTransaction, pk=pk)

        serializer = StatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        tx.status = serializer.validated_data["status"]
        tx.admin_note = serializer.validated_data.get("admin_note", "")
        tx.save()

        return success_response(
            message="وضعیت تراکنش نقره تغییر کرد",
            data={
                "total_results": 1,
                "results": SilverFinancialTransactionSerializer(tx).data
            }
        )
    

class AdminSilverFinancialStatusAPIView(APIView):

    permission_classes = [IsAdminRole]

    def post(self, request, pk):

        tx = get_object_or_404(SilverFinancialTransaction, pk=pk)

        serializer = StatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        tx.status = serializer.validated_data["status"]
        tx.admin_note = serializer.validated_data.get("admin_note", "")
        tx.save()

        return success_response(
            message="وضعیت تراکنش نقره تغییر کرد",
            data={
                "total_results": 1,
                "results": SilverFinancialTransactionSerializer(tx).data
            }
        )
    

class AdminSilverTransactionListAPIView(APIView):

    permission_classes = [IsAdminRole]

    def get(self, request):

        qs = SilverTransaction.objects.all().order_by("-id")

        serializer = SilverTransactionSerializer(qs, many=True)

        return success_response(
            message="لیست معاملات نقره",
            data={
                "total_results": qs.count(),
                "results": serializer.data
            }
        )
    

class AdminSilverTransactionStatusAPIView(APIView):

    permission_classes = [IsAdminRole]

    def post(self, request, pk):

        tx = get_object_or_404(SilverTransaction, pk=pk)

        serializer = StatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        tx.status = serializer.validated_data["status"]
        tx.save()

        return success_response(
            message="وضعیت معامله تغییر کرد",
            data={
                "total_results": 1,
                "results": SilverTransactionSerializer(tx).data
            }
        )


class AdminDashboardAPIView(APIView):

    permission_classes = [IsAdminRole]

    def get(self, request):

        users_count = User.objects.count()

        verified_users = User.objects.filter(
            auth_status="verified"
        ).count()

        pending_users = User.objects.filter(
            auth_status="pending"
        ).count()

        gold_products = Product.objects.count()

        silver_products = SilverProduct.objects.count()

        gold_orders = Order.objects.count()

        silver_orders = SilverOrder.objects.count()

        pending_orders = (
            Order.objects.filter(status="PENDING").count()
            +
            SilverOrder.objects.filter(status="PENDING").count()
        )

        gold_transactions = FinancialTransaction.objects.count()

        silver_transactions = SilverFinancialTransaction.objects.count()

        total_wallet_balance = (
            Wallet.objects.aggregate(
                total=Sum("balance")
            )["total"] or 0
        )

        total_silver_wallet_balance = (
            SilverWallet.objects.aggregate(
                total=Sum("balance")
            )["total"] or 0
        )

        total_gold_inventory = (
            GoldInventory.objects.aggregate(
                total=Sum("balance")
            )["total"] or 0
        )

        total_silver_inventory = (
            SilverInventory.objects.aggregate(
                total=Sum("balance")
            )["total"] or 0
        )

        total_deposit_amount = (
            FinancialTransaction.objects.filter(
                type="DEPOSIT",
                status="COMPLETED"
            ).aggregate(
                total=Sum("amount")
            )["total"] or 0
        )

        pending_withdraw_amount = (
            FinancialTransaction.objects.filter(
                type="WITHDRAW",
                status="PENDING"
            ).aggregate(
                total=Sum("amount")
            )["total"] or 0
        )

        recent_users = list(
            User.objects.order_by("-id")
            .values(
                "id",
                "mobile",
                "first_name",
                "last_name",
                "auth_status"
            )[:10]
        )

        recent_orders = []

        gold_recent = Order.objects.order_by("-id")[:5]

        for order in gold_recent:

            recent_orders.append({
                "id": order.id,
                "type": "gold",
                "user": order.user.mobile,
                "status": order.status,
                "amount": str(order.total_toman_amount),
                "created_at": order.created_at
            })

        silver_recent = SilverOrder.objects.order_by("-id")[:5]

        for order in silver_recent:

            recent_orders.append({
                "id": order.id,
                "type": "silver",
                "user": order.user.mobile,
                "status": order.status,
                "amount": str(order.total_toman_amount),
                "created_at": order.created_at
            })

        return success_response(
            message="اطلاعات داشبورد",
            data={
                "users_count": users_count,
                "verified_users": verified_users,
                "pending_users": pending_users,

                "gold_products": gold_products,
                "silver_products": silver_products,

                "gold_orders": gold_orders,
                "silver_orders": silver_orders,

                "pending_orders": pending_orders,

                "gold_transactions": gold_transactions,
                "silver_transactions": silver_transactions,

                "total_wallet_balance": total_wallet_balance,
                "total_silver_wallet_balance": total_silver_wallet_balance,

                "total_gold_inventory": total_gold_inventory,
                "total_silver_inventory": total_silver_inventory,

                "total_deposit_amount": total_deposit_amount,
                "pending_withdraw_amount": pending_withdraw_amount,

                "recent_users": recent_users,
                "recent_orders": recent_orders
            }
        )
    


class AdminGoldBankDetailAPIView(APIView):

    permission_classes = [IsAdminRole]

    def get(self, request, pk):

        bank = get_object_or_404(
            GoldBankInfo,
            pk=pk
        )

        return success_response(
            message="جزئیات کارت",
            data={
                "total_results": 1,
                "results": [
                    GoldBankInfoSerializer(bank).data
                ]
            }
        )
    

class AdminGoldBankCreateAPIView(APIView):

    permission_classes = [IsAdminRole]

    def post(self, request):

        serializer = GoldBankInfoSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        bank = serializer.save()

        return success_response(
            message="کارت ثبت شد",
            data={
                "total_results": 1,
                "results": [
                    GoldBankInfoSerializer(bank).data
                ]
            }
        )
    

class AdminGoldBankUpdateAPIView(APIView):

    permission_classes = [IsAdminRole]

    def put(self, request, pk):

        bank = get_object_or_404(
            GoldBankInfo,
            pk=pk
        )

        serializer = GoldBankInfoSerializer(
            bank,
            data=request.data,
            partial=True
        )

        serializer.is_valid(
            raise_exception=True
        )

        bank = serializer.save()

        return success_response(
            message="کارت ویرایش شد",
            data={
                "total_results": 1,
                "results": [
                    GoldBankInfoSerializer(bank).data
                ]
            }
        )
    

class AdminGoldBankDeleteAPIView(APIView):

    permission_classes = [IsAdminRole]

    def delete(self, request, pk):

        bank = get_object_or_404(
            GoldBankInfo,
            pk=pk
        )

        bank.delete()

        return success_response(
            message="کارت حذف شد"
        )
    

class AdminGoldBankToggleAPIView(APIView):

    permission_classes = [IsAdminRole]

    @transaction.atomic
    def post(self, request, pk):

        bank = get_object_or_404(GoldBankInfo, pk=pk)

        # فقط یک کارت فعال باشه
        GoldBankInfo.objects.exclude(pk=pk).update(is_active=False)

        bank.is_active = True
        bank.save(update_fields=["is_active"])

        return success_response(
            message="کارت فعال شد",
            data={
                "results": GoldBankInfoSerializer(bank).data
            }
        )
    


class AdminSilverBankListAPIView(APIView):

    permission_classes = [IsAdminRole]

    def get(self, request):

        qs = SilverBankInfo.objects.all().order_by("-id")

        serializer = SilverBankInfoSerializer(
            qs,
            many=True
        )

        return success_response(
            message="لیست کارت های نقره",
            data={
                "total_results": qs.count(),
                "results": serializer.data
            }
        )
    

class AdminSilverBankDetailAPIView(APIView):

    permission_classes = [IsAdminRole]

    def get(self, request, pk):

        bank = get_object_or_404(
            SilverBankInfo,
            pk=pk
        )

        return success_response(
            message="جزئیات کارت",
            data={
                "total_results": 1,
                "results": [
                    SilverBankInfoSerializer(bank).data
                ]
            }
        )
    

class AdminSilverBankCreateAPIView(APIView):

    permission_classes = [IsAdminRole]

    def post(self, request):

        serializer = SilverBankInfoSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        bank = serializer.save()

        return success_response(
            message="کارت ثبت شد",
            data={
                "total_results": 1,
                "results": [
                    SilverBankInfoSerializer(bank).data
                ]
            }
        )
    

class AdminSilverBankUpdateAPIView(APIView):

    permission_classes = [IsAdminRole]

    def put(self, request, pk):

        bank = get_object_or_404(
            SilverBankInfo,
            pk=pk
        )

        serializer = SilverBankInfoSerializer(
            bank,
            data=request.data,
            partial=True
        )

        serializer.is_valid(
            raise_exception=True
        )

        bank = serializer.save()

        return success_response(
            message="کارت ویرایش شد",
            data={
                "total_results": 1,
                "results": [
                    SilverBankInfoSerializer(bank).data
                ]
            }
        )
    

class AdminSilverBankDeleteAPIView(APIView):

    permission_classes = [IsAdminRole]

    def delete(self, request, pk):

        bank = get_object_or_404(
            SilverBankInfo,
            pk=pk
        )

        bank.delete()

        return success_response(
            message="کارت حذف شد"
        )
    

class AdminSilverBankToggleAPIView(APIView):

    permission_classes = [IsAdminRole]

    def post(self, request, pk):

        bank = get_object_or_404(
            SilverBankInfo,
            pk=pk
        )

        SilverBankInfo.objects.update(
            is_active=False
        )

        bank.is_active = True
        bank.save()

        return success_response(
            message="کارت فعال شد",
            data={
                "total_results": 1,
                "results": [
                    SilverBankInfoSerializer(bank).data
                ]
            }
        )
    


class AdminGoldBankListAPIView(APIView):

    permission_classes = [IsAdminRole]

    def get(self, request):

        qs = GoldBankInfo.objects.all().order_by("-id")

        serializer = GoldBankInfoSerializer(
            qs,
            many=True
        )

        return success_response(
            message="لیست کارت های طلا",
            data={
                "total_results": qs.count(),
                "results": serializer.data
            }
        )