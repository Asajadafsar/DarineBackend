# silver_app/views.py

from decimal import Decimal

from django.db import transaction
from django.db.models import Sum

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import (
    IsAuthenticated,
    AllowAny
)
from rest_framework.response import Response

from .models import (
    SilverInventory,
    SilverTransaction,
    SilverWallet,
    SilverProduct,
    SilverCart,
    SilverOrder,
    SilverOrderItem,
    SilverReferralEarning
)

from .serializers import (
    SilverProductSerializer,
    SilverCartSerializer,
    SilverOrderSerializer,
    SilverTransactionSerializer,
    SilverReferralEarningSerializer,
    BuySilverSerializer,
    SellSilverSerializer,
    DepositSilverSerializer,
    WithdrawSilverSerializer,
    CheckoutSilverSerializer
)

from .utils import (
    get_live_silver_price,
    generate_tracking_code,
    get_silver_chart_data
)


# =========================================================
# BASE RESPONSE
# =========================================================

def success_response(
    message="عملیات موفق بود",
    data=None,
    status_code=status.HTTP_200_OK
):

    if data is None:
        data = {}

    return Response({
        "success": True,
        "message": message,
        "data": data
    }, status=status_code)


def error_response(
    message="خطایی رخ داده است",
    status_code=status.HTTP_400_BAD_REQUEST,
    data=None
):

    if data is None:
        data = {}

    return Response({
        "success": False,
        "message": message,
        "data": data
    }, status=status_code)


# =========================================================
# USER BALANCE
# =========================================================

class SilverBalanceAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        inventory, _ = SilverInventory.objects.get_or_create(
            user=request.user
        )

        wallet, _ = SilverWallet.objects.get_or_create(
            user=request.user
        )

        silver_price = get_live_silver_price()

        total_assets = (
            inventory.balance * silver_price
        ) + wallet.balance

        return success_response(
            message='موجودی دریافت شد',
            data={
                "silver_balance_gr": inventory.balance,
                "toman_balance": wallet.balance,
                "current_silver_price": silver_price,
                "total_assets": round(total_assets)
            }
        )


# =========================================================
# SILVER CHART
# =========================================================

class SilverChartAPIView(APIView):

    permission_classes = [AllowAny]

    def get(self, request):

        filter_type = request.GET.get(
            'filter',
            '24H'
        )

        chart_data = get_silver_chart_data(
            filter_type
        )

        return success_response(
            message='اطلاعات نمودار دریافت شد',
            data=chart_data
        )




# =========================================================
# BUY SILVER
# =========================================================
class BuySilverAPIView(APIView):

    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):

        serializer = BuySilverSerializer(data=request.data)

        if not serializer.is_valid():
            return error_response(
                message="اطلاعات نامعتبر است",
                data=serializer.errors
            )

        user = request.user

        toman_amount = serializer.validated_data.get("toman")
        weight_amount = serializer.validated_data.get("weight")
        payment_method = serializer.validated_data.get("payment_method")

        silver_price = get_live_silver_price()
        fee_rate = Decimal("0.01")

        # =========================
        # CALCULATION
        # =========================
        if toman_amount:

            total_toman = Decimal(str(toman_amount))
            fee = total_toman * fee_rate
            net_amount = total_toman - fee
            weight = net_amount / silver_price

        else:

            weight = Decimal(str(weight_amount))
            pure_price = weight * silver_price
            fee = pure_price * fee_rate
            total_toman = pure_price + fee

        # =========================
        # WALLET
        # =========================
        wallet, _ = SilverWallet.objects.get_or_create(user=user)

        if payment_method == "WALLET":

            if wallet.balance < total_toman:
                return error_response(message="موجودی کیف پول کافی نیست")

            wallet.balance -= total_toman
            wallet.save()

        elif payment_method == "GATEWAY":
            # چون درگاه نداریم → فرض موفق
            pass

        else:
            return error_response(message="روش پرداخت نامعتبر است")

        # =========================
        # INVENTORY
        # =========================
        inventory, _ = SilverInventory.objects.get_or_create(user=user)
        inventory.balance += weight
        inventory.save()

        # =========================
        # TRANSACTION
        # =========================
        tx = SilverTransaction.objects.create(
            user=user,
            type="BUY",
            status="COMPLETED",
            amount_gr=weight,
            price_per_gram=silver_price,
            fee=fee,
            total_amount=total_toman,
            tracking_code=generate_tracking_code("SBUY")
        )

        return success_response(
            message="خرید نقره موفق بود",
            status_code=201,
            data={
                "transaction_id": tx.id,
                "tracking_code": tx.tracking_code,
                "silver_weight": float(round(weight, 5)),
                "paid_amount": float(round(total_toman)),
                "wallet_balance": float(round(wallet.balance, 2))
            }
        )


# =========================================================
# SELL SILVER
# =========================================================

class SellSilverAPIView(APIView):

    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):

        serializer = SellSilverSerializer(
            data=request.data
        )

        if not serializer.is_valid():

            return error_response(
                message='اطلاعات نامعتبر است',
                data=serializer.errors
            )

        user = request.user

        toman = serializer.validated_data.get(
            'toman'
        )

        weight = serializer.validated_data.get(
            'weight'
        )

        silver_price = get_live_silver_price()

        inventory, _ = SilverInventory.objects.get_or_create(
            user=user
        )

        wallet, _ = SilverWallet.objects.get_or_create(
            user=user
        )

        fee_rate = Decimal('0.01')

        if toman:

            toman = Decimal(str(toman))

            final_weight = (
                toman / silver_price
            )

            fee = toman * fee_rate

            final_amount = toman - fee

        else:

            final_weight = Decimal(str(weight))

            pure_price = (
                final_weight * silver_price
            )

            fee = pure_price * fee_rate

            final_amount = pure_price - fee

        if inventory.balance < final_weight:

            return error_response(
                message='موجودی نقره کافی نیست'
            )

        inventory.balance -= final_weight
        inventory.save()

        wallet.balance += final_amount
        wallet.save()

        transaction_obj = SilverTransaction.objects.create(
            user=user,
            type='SELL',
            status='COMPLETED',
            amount_gr=final_weight,
            price_per_gram=silver_price,
            fee=fee,
            total_amount=final_amount,
            tracking_code=generate_tracking_code(
                'SSELL'
            )
        )

        return success_response(
            message='فروش نقره انجام شد',
            data={
                "transaction_id": transaction_obj.id,
                "tracking_code": transaction_obj.tracking_code,
                "wallet_balance": round(wallet.balance)
            }
        )


# =========================================================
# DEPOSIT WALLET
# =========================================================

class DepositSilverAPIView(APIView):

    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):

        serializer = DepositSilverSerializer(
            data=request.data
        )

        if not serializer.is_valid():

            return error_response(
                message='اطلاعات نامعتبر است',
                data=serializer.errors
            )

        user = request.user

        amount = serializer.validated_data.get(
            'amount'
        )

        wallet, _ = SilverWallet.objects.get_or_create(
            user=user
        )

        wallet.balance += amount
        wallet.save()

        return success_response(
            message='واریز با موفقیت انجام شد',
            status_code=201,
            data={
                "wallet_balance": round(wallet.balance)
            }
        )


# =========================================================
# WITHDRAW
# =========================================================

class WithdrawSilverAPIView(APIView):

    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):

        serializer = WithdrawSilverSerializer(
            data=request.data
        )

        if not serializer.is_valid():

            return error_response(
                message='اطلاعات نامعتبر است',
                data=serializer.errors
            )

        user = request.user

        amount = serializer.validated_data.get(
            'amount'
        )

        wallet, _ = SilverWallet.objects.get_or_create(
            user=user
        )

        if wallet.balance < amount:

            return error_response(
                message='موجودی کیف پول کافی نیست'
            )

        wallet.balance -= amount
        wallet.save()

        return success_response(
            message='برداشت انجام شد',
            data={
                "wallet_balance": round(wallet.balance)
            }
        )


# =========================================================
# PRODUCTS
# =========================================================

class SilverProductListAPIView(APIView):

    permission_classes = [AllowAny]

    def get(self, request):

        queryset = SilverProduct.objects.filter(
            is_active=True
        ).order_by('-created_at')

        serializer = SilverProductSerializer(
            queryset,
            many=True
        )

        return success_response(
            message='محصولات دریافت شد',
            data=serializer.data
        )


# =========================================================
# CHECKOUT
# =========================================================

class SilverCheckoutAPIView(APIView):

    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):

        serializer = CheckoutSilverSerializer(
            data=request.data
        )

        if not serializer.is_valid():

            return error_response(
                message='اطلاعات نامعتبر است',
                data=serializer.errors
            )

        user = request.user

        cart_items = SilverCart.objects.filter(
            user=user
        ).select_related('product')

        if not cart_items.exists():

            return error_response(
                message='سبد خرید خالی است'
            )

        wallet, _ = SilverWallet.objects.get_or_create(
            user=user
        )

        total_toman = Decimal('0')
        total_silver = Decimal('0')

        for item in cart_items:

            product = item.product

            if product.inventory_count < item.quantity:

                return error_response(
                    message=f'موجودی {product.name} کافی نیست'
                )

            total_silver += (
                product.weight * item.quantity
            )

            total_toman += (
                product.price * item.quantity
            )

        if wallet.balance < total_toman:

            return error_response(
                message='موجودی کیف پول کافی نیست'
            )

        wallet.balance -= total_toman
        wallet.save()

        order = SilverOrder.objects.create(
            user=user,
            total_silver_amount=total_silver,
            total_toman_amount=total_toman,
            tracking_code=generate_tracking_code(
                'SORD'
            ),
            status='PENDING'
        )

        for item in cart_items:

            product = item.product

            SilverOrderItem.objects.create(
                order=order,
                product=product,
                quantity=item.quantity,
                price_at_time=product.price,
                weight_at_time=product.weight
            )

            product.inventory_count -= item.quantity
            product.save()

        cart_items.delete()

        return success_response(
            message='سفارش ثبت شد',
            status_code=201,
            data={
                "order_id": order.id,
                "tracking_code": order.tracking_code,
                "total_price": int(total_toman),
                "total_silver": round(total_silver, 5)
            }
        )


# =========================================================
# CART
# =========================================================

class SilverCartAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        queryset = SilverCart.objects.filter(
            user=request.user
        ).select_related('product')

        serializer = SilverCartSerializer(
            queryset,
            many=True
        )

        total_price = sum([
            item.product.price * item.quantity
            for item in queryset
        ])

        total_silver = sum([
            item.product.weight * item.quantity
            for item in queryset
        ])

        return success_response(
            message='سبد خرید دریافت شد',
            data={
                "items": serializer.data,
                "total_price": int(total_price),
                "total_silver": round(total_silver, 5),
                "count": queryset.count()
            }
        )

    def post(self, request):

        product_id = request.data.get(
            'product_id'
        )

        quantity = int(
            request.data.get(
                'quantity',
                1
            )
        )

        try:

            product = SilverProduct.objects.get(
                id=product_id,
                is_active=True
            )

        except SilverProduct.DoesNotExist:

            return error_response(
                message='محصول یافت نشد',
                status_code=404
            )

        if product.inventory_count < quantity:

            return error_response(
                message='موجودی محصول کافی نیست'
            )

        cart_item, created = SilverCart.objects.get_or_create(
            user=request.user,
            product=product
        )

        if created:

            cart_item.quantity = quantity

        else:

            final_quantity = (
                cart_item.quantity + quantity
            )

            if final_quantity > product.inventory_count:

                return error_response(
                    message='موجودی کافی نیست'
                )

            cart_item.quantity = final_quantity

        cart_item.save()

        return success_response(
            message='محصول به سبد خرید اضافه شد',
            data={
                "cart_item_id": cart_item.id,
                "quantity": cart_item.quantity
            }
        )

    def put(self, request):

        item_id = request.data.get(
            'item_id'
        )

        quantity = int(
            request.data.get(
                'quantity',
                1
            )
        )

        try:

            cart_item = SilverCart.objects.get(
                id=item_id,
                user=request.user
            )

        except SilverCart.DoesNotExist:

            return error_response(
                message='آیتم یافت نشد'
            )

        if quantity < 1:

            cart_item.delete()

            return success_response(
                message='آیتم حذف شد'
            )

        if quantity > cart_item.product.inventory_count:

            return error_response(
                message='موجودی محصول کافی نیست'
            )

        cart_item.quantity = quantity
        cart_item.save()

        return success_response(
            message='سبد خرید بروزرسانی شد'
        )

    def delete(self, request):

        item_id = request.data.get(
            'item_id'
        )

        deleted = SilverCart.objects.filter(
            id=item_id,
            user=request.user
        ).delete()

        if not deleted[0]:

            return error_response(
                message='آیتم یافت نشد'
            )

        return success_response(
            message='آیتم حذف شد'
        )


# =========================================================
# ORDER HISTORY
# =========================================================

class SilverOrderHistoryAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        queryset = SilverOrder.objects.filter(
            user=request.user
        ).order_by('-created_at')

        serializer = SilverOrderSerializer(
            queryset,
            many=True
        )

        return success_response(
            message='سفارشات دریافت شد',
            data=serializer.data
        )


# =========================================================
# REPORTS
# =========================================================

class SilverReportsAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        report_type = request.GET.get(
            'type'
        )

        if report_type == 'silver':

            queryset = SilverTransaction.objects.filter(
                user=request.user
            ).order_by('-created_at')

            serializer = SilverTransactionSerializer(
                queryset,
                many=True
            )

            return success_response(
                message='گزارش معاملات نقره',
                data=serializer.data
            )

        elif report_type == 'orders':

            queryset = SilverOrder.objects.filter(
                user=request.user
            ).order_by('-created_at')

            serializer = SilverOrderSerializer(
                queryset,
                many=True
            )

            return success_response(
                message='گزارش سفارشات',
                data=serializer.data
            )

        return error_response(
            message='نوع گزارش نامعتبر است'
        )


# =========================================================
# RECENT TRANSACTIONS
# =========================================================

class SilverRecentTransactionsAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        queryset = SilverTransaction.objects.filter(
            user=request.user
        ).order_by('-created_at')[:10]

        serializer = SilverTransactionSerializer(
            queryset,
            many=True
        )

        return success_response(
            message='تراکنش ها دریافت شد',
            data=serializer.data
        )


# =========================================================
# RECENT DELIVERIES
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
    


# =========================================================
# REFERRAL DASHBOARD
# =========================================================

class SilverReferralDashboardAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        user = request.user

        total_invited = user.subscribers.count()

        total_earned = SilverReferralEarning.objects.filter(
            referrer=user
        ).aggregate(
            total=Sum('amount')
        )['total'] or 0

        recent_earnings = SilverReferralEarning.objects.filter(
            referrer=user
        ).order_by('-created_at')[:10]

        serializer = SilverReferralEarningSerializer(
            recent_earnings,
            many=True
        )

        referral_link = (
            f"https://silver.darine.shop/register?"
            f"ref={user.referral_code}"
        )

        return success_response(
            message='اطلاعات دعوت دوستان دریافت شد',
            data={
                "referral_code": user.referral_code,
                "referral_link": referral_link,
                "total_invited": total_invited,
                "total_earned": int(total_earned),
                "recent_earnings": serializer.data
            }
        )