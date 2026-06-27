# gold_app/views.py

from decimal import Decimal
import jdatetime
from rest_framework.parsers import MultiPartParser, FormParser
from django.db import transaction
from django.db.models import Q, Sum
from django.utils import timezone

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import (
    IsAuthenticated,
    AllowAny
)
from rest_framework.response import Response

from drf_spectacular.utils import extend_schema

from accounts.models import BankCard, FeeSetting, ReferralEarning

from accounts.utils import apply_referral_bonus
from admin_panel.models import GoldBanner
from admin_panel.serializers import GoldBannerSerializer
from admin_panel.utils import create_admin_log
from silver_app.models import (
    SilverInventory
)
from silver_app.utils import get_live_silver_price

from .models import (
    AutoSavingPlan,
    GiftCard,
    GiftCardOrder,
    GoldBankInfo,
    GoldInventory,
    GoldOrder,
    GoldTransaction,
    ProductCategory,
    UserAddress,
    Wallet,
    FinancialTransaction,
    Product,
    Order,
    OrderItem,
    PriceAlert
)

from .serializers import (
    AutoSavingPlanSerializer,
    GiftCardOrderSerializer,
    GiftCardSerializer,
    GoldOrderListSerializer,
    GoldOrderSerializer,
    PhysicalOrderSerializer,
    PriceQuerySerializer,
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
    WithdrawSerializer
    )

from .utils import (
    get_group_prices,
    get_latest_price,
    get_live_gold_price,
    generate_tracking_code,
    get_gold_chart_data,
    filter_by_date,
    filter_by_status,
    save_gold_price_history
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
        {
            "success": False,
            "message": str(final_message),
            "data": {}   # 👈 همیشه تمیز
        },
        status=status_code
    )




# =========================================================
# DASHBOARD
# =========================================================

class GoldDashboardAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        user = request.user

        inventory, _ = GoldInventory.objects.get_or_create(
            user=user
        )

        wallet, _ = Wallet.objects.get_or_create(
            user=user
        )

        gold_price = get_live_gold_price()

        gold_balance = Decimal(str(inventory.balance))
        toman_balance = Decimal(str(wallet.balance))

        gold_value = gold_balance * gold_price

        total_assets = gold_value + toman_balance

        return success_response(
            message='اطلاعات داشبورد دریافت شد',
            data={
                "gold_balance_gr": round(gold_balance, 5),
                "toman_balance": round(toman_balance),
                "gold_price": round(gold_price),
                "gold_value": round(gold_value),
                "total_assets": round(total_assets)
            }
        )


# =========================================================
# USER BALANCE
# =========================================================

class UserBalanceAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        inventory, _ = GoldInventory.objects.get_or_create(
            user=request.user
        )

        wallet, _ = Wallet.objects.get_or_create(
            user=request.user
        )

        gold_price = get_live_gold_price()

        total_assets = (
            inventory.balance * gold_price
        ) + wallet.balance

        return success_response(
            message='موجودی دریافت شد',
            data={
                "gold_balance_gr": inventory.balance,
                "toman_balance": wallet.balance,
                "current_gold_price": gold_price,
                "total_assets": round(total_assets)
            }
        )


# # =========================================================
# # GOLD CHART
# # =========================================================

# class GoldChartAPIView(APIView):

#     permission_classes = [AllowAny]

#     def get(self, request):

#         filter_type = request.GET.get(
#             'filter',
#             '24H'
#         )

#         chart_data = get_gold_chart_data(
#             filter_type
#         )

#         return success_response(
#             message='اطلاعات نمودار دریافت شد',
#             data=chart_data
#         )




# =========================================================
# BUY GOLD
# =========================================================

class BuyGoldAPIView(APIView):

    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):

        gold_price = get_live_gold_price()

        if not gold_price:
            return error_response(message="خطا در دریافت قیمت طلا")

        serializer = BuyGoldSerializer(
            data=request.data,
            context={
                "request": request,
                "gold_price": gold_price
            }
        )

        serializer.is_valid(raise_exception=True)

        user = request.user

        fee = serializer.validated_data["fee"]
        fee_rate = serializer.validated_data["fee_rate"]
        total_toman = serializer.validated_data["total_toman"]
        weight = serializer.validated_data["final_weight"]

        wallet, _ = Wallet.objects.get_or_create(user=user)
        inventory, _ = GoldInventory.objects.get_or_create(user=user)

        payment_method = request.data.get("payment_method")

        if payment_method == "WALLET":

            if wallet.balance < total_toman:
                return error_response(message="موجودی کافی نیست")

            wallet.balance -= total_toman
            wallet.save()

        elif payment_method == "GATEWAY":

            FinancialTransaction.objects.create(
                user=user,
                amount=total_toman,
                type="DEPOSIT",
                method="ONLINE",
                status="PENDING",
                tracking_code=generate_tracking_code("PAY"),
                description="خرید طلا ثبت شد و در انتظار تایید است"
            )

        inventory.balance += weight
        inventory.save()

        tx = GoldTransaction.objects.create(
            user=user,
            type="BUY",
            status="PENDING",
            amount_gr=weight,
            price_per_gram=gold_price,
            fee=fee,
            total_amount=total_toman,
            tracking_code=generate_tracking_code("BUY")
        )
        from admin_panel.utils import create_admin_log


        create_admin_log(
            admin=None,
            user=user,
            action_type="BUY_GOLD",
            action="خرید طلا",
            model_name="GoldTransaction",
            object_id=tx.id,
            description=f"""
        کاربر {user.mobile}
        خرید طلا
        وزن: {weight}
        مبلغ: {total_toman}
        """
        )

        return success_response(
            message="خرید طلا ثبت شد و در انتظار تایید است",
            data={
                "transaction_id": tx.id,
                "tracking_code": tx.tracking_code,
                "gold_weight": float(weight),
                "paid_amount": float(total_toman),
                "fee": float(fee),
                "fee_rate": float(fee_rate),
                "wallet_balance": float(wallet.balance)
            }
        )




# =========================================================
# SELL GOLD
# =========================================================

class SellGoldAPIView(APIView):

    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):

        gold_price = get_live_gold_price()

        serializer = SellGoldSerializer(
            data=request.data,
            context={
                "request": request,
                "gold_price": gold_price
            }
        )

        serializer.is_valid(raise_exception=True)

        user = request.user

        fee = serializer.validated_data["fee"]
        fee_rate = serializer.validated_data["fee_rate"]
        final_amount = serializer.validated_data["final_amount"]
        final_weight = serializer.validated_data["final_weight"]

        inventory, _ = GoldInventory.objects.get_or_create(user=user)
        wallet, _ = Wallet.objects.get_or_create(user=user)

        if inventory.balance < final_weight:
            return error_response(message="موجودی طلا کافی نیست")

        inventory.balance -= final_weight
        inventory.save()

        wallet.balance += final_amount
        wallet.save()

        tx = GoldTransaction.objects.create(
            user=user,
            type="SELL",
            status="COMPLETED",
            amount_gr=final_weight,
            price_per_gram=gold_price,
            fee=fee,
            total_amount=final_amount,
            tracking_code=generate_tracking_code("SELL")
        )
        create_admin_log(
            admin=None,
            user=user,
            action_type="SELL_GOLD",
            action="فروش طلا",
            model_name="GoldTransaction",
            object_id=tx.id,
            description=f"""
        کاربر {user.mobile}
        فروش طلا
        وزن: {final_weight}
        مبلغ: {final_amount}
        """
        )
        return success_response(
            message="فروش طلا انجام شد",
            data={
                "transaction_id": tx.id,
                "tracking_code": tx.tracking_code,
                "gold_weight": float(final_weight),
                "fee": float(fee),
                "fee_rate": float(fee_rate),
                "wallet_balance": float(wallet.balance)
            }
        )


# =========================================================
# DEPOSIT WALLET
# =========================================================




from rest_framework.parsers import MultiPartParser, FormParser




class DepositAPIView(APIView):

    permission_classes = [IsAuthenticated]

    parser_classes = [
        MultiPartParser,
        FormParser
    ]

    @extend_schema(
        tags=['Wallet'],
        request=DepositSerializer,
        summary='واریز کیف پول'
    )
    @transaction.atomic
    def post(self, request):

        try:

            serializer = DepositSerializer(
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

            method = serializer.validated_data.get(
                'method'
            )

            receipt = serializer.validated_data.get(
                'receipt'
            )

            description = serializer.validated_data.get(
                'description',
                ''
            )

            wallet, _ = Wallet.objects.get_or_create(
                user=user
            )

            # =====================================
            # RECEIPT METHOD
            # =====================================

            if method == 'RECEIPT':

                transaction_obj = FinancialTransaction.objects.create(
                    user=user,
                    amount=amount,
                    type='DEPOSIT',
                    method='CARD_TO_CARD',
                    status='PENDING',
                    receipt_image=receipt,
                    tracking_code=generate_tracking_code(
                        'DEP'
                    ),
                    description=description
                )

                return success_response(
                    message='درخواست واریز ثبت شد و در انتظار تایید است',
                    status_code=201,
                    data={
                        "transaction_id": transaction_obj.id,
                        "tracking_code": transaction_obj.tracking_code,
                        "status": "PENDING"
                    }
                )

            # =====================================
            # GATEWAY METHOD
            # =====================================

            elif method == 'GATEWAY':

                transaction_obj = FinancialTransaction.objects.create(
                    user=user,
                    amount=amount,
                    type='DEPOSIT',
                    method='ONLINE',
                    status='PENDING',
                    tracking_code=generate_tracking_code(
                        'PAY'
                    ),
                    description=description
                )

                wallet.balance += amount
                wallet.save()

                return success_response(
                    message='درخواست واریز با موفقیت ثبت و در انتظار تایید است',
                    status_code=201,
                    data={
                        "transaction_id": transaction_obj.id,
                        "tracking_code": transaction_obj.tracking_code,
                        "wallet_balance": round(wallet.balance),
                        "status": "COMPLETED"
                    }
                )

            return error_response(
                message='روش واریز نامعتبر است'
            )

        except Exception as e:

            return error_response(
                message=str(e),
                status_code=500
            )

# =========================================================
# WITHDRAW
# =========================================================

# class WithdrawAPIView(APIView):

#     permission_classes = [IsAuthenticated]

#     @transaction.atomic
#     def post(self, request):

#         serializer = WithdrawSerializer(
#             data=request.data,
#             context={'request': request}
#         )

#         if not serializer.is_valid():

#             return error_response(
#                 message='اطلاعات نامعتبر است',
#                 data=serializer.errors
#             )

#         user = request.user

#         amount = serializer.validated_data.get(
#             'amount'
#         )

#         target = serializer.validated_data.get(
#             'target'
#         )

#         wallet, _ = Wallet.objects.get_or_create(
#             user=user
#         )

#         if wallet.balance < amount:

#             return error_response(
#                 message='موجودی کیف پول کافی نیست'
#             )

#         # =====================================================
#         # BANK WITHDRAW
#         # =====================================================

#         if target == 'BANK':

#             card = serializer.validated_data.get(
#                 'card'
#             )

#             wallet.balance -= amount
#             wallet.save()

#             transaction_obj = FinancialTransaction.objects.create(
#                 user=user,
#                 amount=amount,
#                 type='WITHDRAW',
#                 method='BANK',
#                 status='PENDING',
#                 user_card=card,
#                 tracking_code=generate_tracking_code(
#                     'WDB'
#                 ),
#                 admin_note='در انتظار تسویه بانکی',
#                 description=f'''
# برداشت بانکی
# کارت: {card.card_number}
# بانک: {card.bank_name}
# '''
#             )

#             return success_response(
#                 message='درخواست برداشت ثبت شد',
#                 data={
#                     "transaction_id": transaction_obj.id,
#                     "tracking_code": transaction_obj.tracking_code,
#                     "status": transaction_obj.status,
#                     "wallet_balance": round(wallet.balance),
#                     "card_number": card.card_number
#                 }
#             )

#         # =====================================================
#         # CONVERT TO SILVER
#         # =====================================================

#         elif target == 'SILVER':

#             silver_price = Decimal('1')

#             silver_inventory, _ = SilverInventory.objects.get_or_create(
#                 user=user
#             )

#             silver_weight = amount / silver_price

#             wallet.balance -= amount
#             wallet.save()

#             silver_inventory.balance += silver_weight
#             silver_inventory.save()

#             transaction_obj = FinancialTransaction.objects.create(
#                 user=user,
#                 amount=amount,
#                 type='CONVERT',
#                 method='SILVER',
#                 status='PENDING',
#                 tracking_code=generate_tracking_code(
#                     'SLV'
#                 ),
#                 admin_note='تبدیل ریال به نقره',
#                 description='تبدیل موجودی کیف پول به نقره'
#             )

#             return success_response(
#                 message='درخواست تبدیل به نقره انجام شد ',
#                 data={
#                     "transaction_id": transaction_obj.id,
#                     "tracking_code": transaction_obj.tracking_code,
#                     "silver_weight": round(silver_weight, 5),
#                     "wallet_balance": round(wallet.balance)
#                 }
#             )

#         return error_response(
#             message='نوع برداشت نامعتبر است'
#         )



# =========================================================
# WITHDRAW
# =========================================================

class WithdrawAPIView(APIView):

    permission_classes = [IsAuthenticated]


    @transaction.atomic
    def post(self, request):

        serializer = WithdrawSerializer(
            data=request.data,
            context={
                "request": request
            }
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


        target = serializer.validated_data.get(
            'target'
        )


        wallet, _ = Wallet.objects.get_or_create(
            user=user
        )


        if wallet.balance < amount:

            return error_response(
                message='موجودی کیف پول کافی نیست'
            )



        # =====================================================
        # BANK WITHDRAW
        # =====================================================

        if target == 'BANK':


            card = serializer.validated_data.get(
                'card'
            )


            wallet.balance -= amount

            wallet.save(
                update_fields=[
                    "balance"
                ]
            )


            transaction_obj = FinancialTransaction.objects.create(

                user=user,

                amount=amount,

                type='WITHDRAW',

                method='BANK',

                status='PENDING',

                user_card=card,

                tracking_code=generate_tracking_code(
                    'WDB'
                ),

                admin_note='در انتظار تسویه بانکی',

                description=f'''
برداشت بانکی

کارت:
{card.card_number}

بانک:
{card.bank_name}
'''
            )


            return success_response(

                message='درخواست برداشت ثبت شد',

                data={

                    "transaction_id":
                        transaction_obj.id,

                    "tracking_code":
                        transaction_obj.tracking_code,

                    "status":
                        transaction_obj.status,

                    "wallet_balance":
                        round(wallet.balance),

                    "card_number":
                        card.card_number
                }
            )




        # =====================================================
        # CONVERT TO SILVER
        # =====================================================

        elif target == 'SILVER':


            silver_price = Decimal(
                '1'
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



            transaction_obj = FinancialTransaction.objects.create(

                user=user,

                amount=amount,


                # FIXED
                # قبلا CONVERT بود و گزارش نمی‌گرفت
                type='WITHDRAW',


                method='SILVER',

                status='COMPLETED',


                tracking_code=generate_tracking_code(
                    'SLV'
                ),


                admin_note='تبدیل کیف پول به نقره',


                description='تبدیل موجودی کیف پول به نقره'

            )



            return success_response(

                message='تبدیل به نقره انجام شد',

                data={

                    "transaction_id":
                        transaction_obj.id,


                    "tracking_code":
                        transaction_obj.tracking_code,


                    "silver_weight":
                        round(
                            silver_weight,
                            5
                        ),


                    "wallet_balance":
                        round(
                            wallet.balance
                        )

                }
            )




        return error_response(

            message='نوع برداشت نامعتبر است'

        )
# =========================================================
# PRODUCTS
# =========================================================

class ProductListAPIView(APIView):

    permission_classes = [AllowAny]

    def get(self, request):

        queryset = Product.objects.filter(
            is_active=True
        ).select_related(
            "category"
        ).order_by(
            "-created_at"
        )

        category = request.GET.get("category")
        delivery_type = request.GET.get("delivery_type")

        if category:
            queryset = queryset.filter(
                category__slug=category
            )

        if delivery_type:
            queryset = queryset.filter(
                delivery_type=delivery_type
            )

        serializer = ProductSerializer(
            queryset,
            many=True,
            context={"request": request}
        )

        return success_response(
            message="محصولات دریافت شد",
            data=serializer.data
        )

# =========================================================
# PHYSICAL ORDER (GOLD CHECKOUT)
# =========================================================

class PhysicalOrderAPIView(APIView):

    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):

        serializer = PhysicalOrderSerializer(data=request.data)

        if not serializer.is_valid():
            return error_response(data=serializer.errors)

        user = request.user

        products_data = serializer.validated_data["products"]

        wallet, _ = Wallet.objects.get_or_create(user=user)
        inventory, _ = GoldInventory.objects.get_or_create(user=user)

        total_gold = 0
        total_toman = 0
        order_items = []

        # =========================
        # PROCESS PRODUCTS
        # =========================
        for item in products_data:

            product = Product.objects.filter(
                id=item["product_id"],
                is_active=True
            ).first()

            if not product:
                return error_response(message=f"محصول {item['product_id']} یافت نشد")

            quantity = item["quantity"]

            if product.inventory_count < quantity:
                return error_response(message=f"موجودی {product.name} کافی نیست")

            item_gold = product.total_weight_with_fees * quantity
            item_toman = product.buy_price * quantity

            total_gold += item_gold
            total_toman += item_toman

            order_items.append({
                "product": product,
                "quantity": quantity,
                "price_at_time": product.buy_price,
                "weight_at_time": product.total_weight_with_fees
            })

        payment_method = serializer.validated_data["payment_method"]

        # =========================
        # PAYMENT
        # =========================
        if payment_method == "TOMAN":

            if wallet.balance < total_toman:
                return error_response(message="موجودی کیف پول کافی نیست")

            wallet.balance -= total_toman
            wallet.save(update_fields=["balance"])

        elif payment_method == "GOLD":

            if inventory.balance < total_gold:
                return error_response(message="موجودی طلا کافی نیست")

            inventory.balance -= total_gold
            inventory.save(update_fields=["balance"])

        else:
            return error_response(message="روش پرداخت نامعتبر است")

        # =========================
        # ADDRESS
        # =========================
        address_id = serializer.validated_data.get("address_id")

        if address_id:
            address = UserAddress.objects.filter(id=address_id, user=user).first()
            if not address:
                return error_response(message="آدرس یافت نشد")
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

        # =========================
        # ORDER CREATE
        # =========================
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
            status="PENDING"
        )

        # =========================
        # ORDER ITEMS
        # =========================
        for item in order_items:

            product = item["product"]

            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=item["quantity"],
                price_at_time=item["price_at_time"],
                weight_at_time=item["weight_at_time"]
            )

            product.inventory_count -= item["quantity"]
            product.save(update_fields=["inventory_count"])

        return success_response(
            message="سفارش طلا ثبت شد",
            status_code=201,
            data={
                "order_id": order.id,
                "tracking_code": order.tracking_code,
                "total_gold": float(total_gold),
                "total_price": int(total_toman)
            }
        )


class ProductCategoryListAPIView(APIView):

    permission_classes = [AllowAny]

    def get(self, request):

        queryset = ProductCategory.objects.all().order_by("name")

        serializer = ProductCategorySerializer(
            queryset,
            many=True
        )

        return success_response(
            message="دسته بندی محصولات دریافت شد",
            data=serializer.data
        )


# =========================================================
# PRODUCT DETAIL
# =========================================================

class ProductDetailAPIView(APIView):

    permission_classes = [AllowAny]

    def get(self, request, product_id):

        product = Product.objects.filter(
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

        serializer = ProductSerializer(
            product,
            context={"request": request}
        )

        return success_response(
            message="اطلاعات محصول دریافت شد",
            data=serializer.data
        )


class UserAddressListAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        addresses = UserAddress.objects.filter(
            user=request.user
        ).order_by("-created_at")

        serializer = UserAddressSerializer(addresses, many=True)

        return success_response(
            message="لیست آدرس‌ها دریافت شد",
            data=serializer.data
        )

class UserAddressCreateAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request):

        serializer = UserAddressSerializer(data=request.data)

        if not serializer.is_valid():
            return error_response(data=serializer.errors)

        address = UserAddress.objects.create(
            user=request.user,
            province=serializer.validated_data["province"],
            city=serializer.validated_data["city"],
            address=serializer.validated_data["address"],
            postal_code=serializer.validated_data.get("postal_code"),
            plaque=serializer.validated_data.get("plaque"),
            unit=serializer.validated_data.get("unit"),
        )

        return success_response(
            message="آدرس ثبت شد",
            status_code=201,
            data={
                "address_id": address.id
            }
        )




# =========================================================
# ORDER HISTORY
# =========================================================

class OrderHistoryAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        queryset = Order.objects.filter(
            user=request.user
        ).order_by('-created_at')

        serializer = OrderSerializer(
            queryset,
            many=True
        )

        return success_response(
            message='سفارشات دریافت شد',
            data=serializer.data
        )


# =========================================================
# PRICE ALERT
# =========================================================

class PriceAlertAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        queryset = PriceAlert.objects.filter(
            user=request.user
        )

        # ==========================================
        # STATUS FILTER
        # active / inactive / completed
        # ==========================================

        status_filter = request.query_params.get(
            "status"
        )

        if status_filter:

            if status_filter == "ACTIVE":

                queryset = queryset.filter(
                    is_active=True
                )

            elif status_filter == "INACTIVE":

                queryset = queryset.filter(
                    is_active=False
                )

            elif status_filter == "COMPLETED":

                queryset = queryset.filter(
                    is_triggered=True
                )

        # ==========================================
        # DATE FILTER
        # 1405/03/13
        # 2026-06-03
        # ==========================================

        start_date = request.query_params.get(
            "start_date"
        )

        end_date = request.query_params.get(
            "end_date"
        )

        try:

            if start_date:

                if "/" in start_date:

                    y, m, d = map(
                        int,
                        start_date.split("/")
                    )

                    start_date = (
                        jdatetime.date(
                            y,
                            m,
                            d
                        ).togregorian()
                    )

                else:

                    start_date = datetime.strptime(
                        start_date,
                        "%Y-%m-%d"
                    ).date()

                queryset = queryset.filter(
                    created_at__date__gte=start_date
                )

            if end_date:

                if "/" in end_date:

                    y, m, d = map(
                        int,
                        end_date.split("/")
                    )

                    end_date = (
                        jdatetime.date(
                            y,
                            m,
                            d
                        ).togregorian()
                    )

                else:

                    end_date = datetime.strptime(
                        end_date,
                        "%Y-%m-%d"
                    ).date()

                queryset = queryset.filter(
                    created_at__date__lte=end_date
                )

        except Exception:

            return error_response(
                "فرمت تاریخ اشتباه است (1405/03/13 یا 2026-06-03)"
            )

        queryset = queryset.order_by(
            "-created_at"
        )

        serializer = PriceAlertSerializer(
            queryset,
            many=True
        )

        return success_response(
            message="هشدارها دریافت شد",
            data=serializer.data
        )

    def post(self, request):

        serializer = PriceAlertSerializer(
            data=request.data
        )

        if not serializer.is_valid():

            return error_response(
                message="اطلاعات نامعتبر است",
                data=serializer.errors
            )

        serializer.save(
            user=request.user
        )

        return success_response(
            message="هشدار ثبت شد",
            data=serializer.data,
            status_code=201
        )



# =========================================================
# DELETE PRICE ALERT
# =========================================================

class DeletePriceAlertAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):

        try:

            alert = PriceAlert.objects.get(
                id=pk,
                user=request.user
            )

        except PriceAlert.DoesNotExist:

            return error_response(
                message='هشدار یافت نشد',
                status_code=404
            )

        alert.delete()

        return success_response(
            message='هشدار حذف شد'
        )




# =========================================================
# REPORTS
# =========================================================

class ReportsAPIView(APIView):

    permission_classes = [IsAuthenticated]


    def parse_date(self, value):

        if not value:
            return None

        try:

            if "/" in value:

                y, m, d = map(int, value.split("/"))

                return jdatetime.date(
                    y, m, d
                ).togregorian()


            return datetime.strptime(
                value,
                "%Y-%m-%d"
            ).date()


        except Exception:
            return None



    def get(self, request):

        report_type = request.GET.get("type")
        status_filter = request.GET.get("status")
        method_filter = request.GET.get("method")


        start_date = self.parse_date(
            request.GET.get("start_date")
        )

        end_date = self.parse_date(
            request.GET.get("end_date")
        )



        # =====================================================
        # FINANCIAL (DEPOSIT / WITHDRAW)
        # =====================================================

        if report_type in [
            "deposit",
            "withdraw"
        ]:


            transaction_type = (
                "DEPOSIT"
                if report_type == "deposit"
                else "WITHDRAW"
            )


            queryset = FinancialTransaction.objects.filter(
                user=request.user,
                type=transaction_type
            )


            # method
            if method_filter:

                queryset = queryset.filter(
                    method__iexact=method_filter
                )


            # status
            if status_filter:

                queryset = queryset.filter(
                    status__iexact=status_filter
                )


            # date
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
            )


            serializer = FinancialTransactionSerializer(
                queryset,
                many=True
            )


            return success_response(
                message=(
                    "گزارش واریزها"
                    if report_type == "deposit"
                    else "گزارش برداشت‌ها"
                ),
                data=serializer.data
            )



        # =====================================================
        # GOLD
        # =====================================================

        if report_type == "gold":


            queryset = GoldTransaction.objects.filter(
                user=request.user
            )


            if method_filter:

                queryset = queryset.filter(
                    type__iexact=method_filter
                )


            if status_filter:

                queryset = queryset.filter(
                    status__iexact=status_filter
                )


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
            )


            serializer = GoldTransactionSerializer(
                queryset,
                many=True
            )


            return success_response(
                message="گزارش معاملات طلا",
                data=serializer.data
            )



        # =====================================================
        # ORDERS
        # =====================================================

        if report_type == "orders":


            queryset = Order.objects.filter(
                user=request.user
            )


            if method_filter:

                queryset = queryset.filter(
                    payment_method__iexact=method_filter
                )


            if status_filter:

                queryset = queryset.filter(
                    status__iexact=status_filter
                )


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
            )


            serializer = OrderSerializer(
                queryset,
                many=True
            )


            return success_response(
                message="گزارش سفارشات",
                data=serializer.data
            )



        return error_response(
            message="نوع گزارش نامعتبر است"
        )



# =========================================================
# RECENT TRANSACTIONS
# =========================================================

from datetime import datetime

class RecentTransactionsAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        queryset = FinancialTransaction.objects.filter(
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
        # DATE FILTER
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

                elif item.method == "SILVER":
                    title = "واریز از نقرینه"

                else:
                    title = "واریز"

            else:

                if item.method == "SILVER":
                    title = "برداشت به نقرینه"

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

        serializer = RecentTransactionSerializer(
            data,
            many=True
        )

        return success_response(
            message="تراکنش ها دریافت شد",
            data=serializer.data
        )
    


# =========================================================
# RECENT DELIVERIES
# =========================================================

class RecentDeliveriesAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        queryset = Order.objects.filter(
            user=request.user
        ).order_by('-created_at')[:10]

        serializer = OrderSerializer(
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

class ReferralDashboardAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        user = request.user

        total_invited = user.subscribers.count()

        total_earned = ReferralEarning.objects.filter(
            referrer=user,
            source_type="GOLD"
        ).aggregate(
            total=Sum("amount")
        )["total"] or 0

        recent_earnings = ReferralEarning.objects.filter(
            referrer=user,
            source_type="GOLD"
        ).order_by(
            "-created_at"
        )[:10]

        serializer = ReferralEarningSerializer(
            recent_earnings,
            many=True
        )

        return success_response(
            message="اطلاعات دعوت دوستان دریافت شد",
            data={
                "referral_code": user.referral_code,
                "referral_link":
                    f"https://gold.darine.shop/register?ref={user.referral_code}",
                "total_invited": total_invited,
                "total_earned": int(total_earned),
                "recent_earnings": serializer.data
            }
        )
    

# =========================================================
# AUTO SAVING PLAN
# =========================================================

from datetime import datetime, timedelta
from django.utils import timezone


class AutoSavingPlanAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        plans = AutoSavingPlan.objects.filter(
            user=request.user
        ).order_by('-created_at')

        serializer = AutoSavingPlanSerializer(
            plans,
            many=True
        )

        return success_response(
            message='پلن های پس انداز دریافت شد',
            data=serializer.data
        )

    def post(self, request):

        saving_type = request.data.get('type')
        amount = request.data.get('amount')

        if not saving_type:

            return error_response(
                message='نوع پلن الزامی است'
            )

        if not amount:

            return error_response(
                message='مبلغ الزامی است'
            )

        # =====================================
        # PERIOD DAYS
        # =====================================

        if saving_type == 'DAILY':

            period_days = 1

        elif saving_type == 'WEEKLY':

            period_days = 7

        elif saving_type == 'MONTHLY':

            period_days = 30

        else:

            return error_response(
                message='نوع پلن نامعتبر است'
            )

        # =====================================
        # CREATE PLAN
        # =====================================

        plan = AutoSavingPlan.objects.create(
            user=request.user,
            type=saving_type,
            amount=amount,
            period_days=period_days,
            next_execute_at=timezone.now() + timedelta(days=period_days),
            status='ACTIVE'
        )

        serializer = AutoSavingPlanSerializer(
            plan
        )

        return success_response(
            message='پلن پس انداز ایجاد شد',
            data=serializer.data,
            status_code=201
        )

    def delete(self, request):

        plan_id = request.data.get(
            'plan_id'
        )

        try:

            plan = AutoSavingPlan.objects.get(
                id=plan_id,
                user=request.user
            )

        except AutoSavingPlan.DoesNotExist:

            return error_response(
                message='پلن یافت نشد'
            )

        plan.delete()

        return success_response(
            message='پلن حذف شد'
        )

# =========================================================
# GIFT CARD ORDER
# =========================================================

class GiftCardOrderAPIView(APIView):

    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):

        serializer = GiftCardOrderSerializer(data=request.data)

        if not serializer.is_valid():
            return error_response(
                message="اطلاعات نامعتبر است",
                data=serializer.errors
            )

        user = request.user

        # =========================
        # WALLET
        # =========================
        wallet, _ = Wallet.objects.get_or_create(user=user)

        gold_price = get_live_gold_price()

        if not gold_price:
            return error_response(message="خطا در دریافت قیمت طلا")

        weight_per_card = Decimal(serializer.validated_data["weight_per_card"])
        quantity = serializer.validated_data["quantity"]

        total_weight = weight_per_card * quantity
        total_price = total_weight * Decimal(gold_price)

        if wallet.balance < total_price:
            return error_response(message="موجودی کیف پول کافی نیست")

        # =========================
        # ADDRESS HANDLING (FIXED)
        # =========================

        address_id = serializer.validated_data.get("address_id")

        province = None
        city = None
        address = None
        postal_code = None
        plaque = None
        unit = None

        # ---- use saved address
        if address_id:

            saved_address = UserAddress.objects.filter(
                id=address_id,
                user=user
            ).first()

            if not saved_address:
                return error_response(message="آدرس یافت نشد")

            province = saved_address.province
            city = saved_address.city
            address = saved_address.address
            postal_code = saved_address.postal_code
            plaque = saved_address.plaque
            unit = saved_address.unit

        # ---- new address
        else:

            province = serializer.validated_data.get("province")
            city = serializer.validated_data.get("city")
            address = serializer.validated_data.get("address")

            if not province or not city or not address:
                return error_response(
                    message="اطلاعات آدرس ناقص است"
                )

            postal_code = serializer.validated_data.get("postal_code")
            plaque = serializer.validated_data.get("plaque")
            unit = serializer.validated_data.get("unit")

            # ذخیره آدرس برای استفاده بعدی
            UserAddress.objects.create(
                user=user,
                province=province,
                city=city,
                address=address,
                postal_code=postal_code,
                plaque=plaque,
                unit=unit
            )

        # =========================
        # WALLET DECREASE
        # =========================
        wallet.balance -= total_price
        wallet.save(update_fields=["balance"])

        # =========================
        # CREATE ORDER
        # =========================
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
            tracking_code=generate_tracking_code("GFT")
        )

        # =========================
        # CREATE CARDS
        # =========================
        cards = []

        for _ in range(quantity):

            card = GiftCard.objects.create(
                serial_number=generate_tracking_code("CARD"),
                weight=weight_per_card,
                created_by=user,
                status="ACTIVE",
                is_used=False
            )

            cards.append({
                "serial_number": card.serial_number,
                "weight": float(card.weight)
            })

        return success_response(
            message="سفارش کارت هدیه ثبت شد",
            status_code=201,
            data={
                "order_id": order.id,
                "tracking_code": order.tracking_code,
                "total_price": float(total_price),
                "cards": cards
            }
        )
    

class GiftCardOrderListAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        queryset = GiftCardOrder.objects.filter(
            user=request.user
        ).order_by('-created_at')

        serializer = GiftCardOrderSerializer(
            queryset,
            many=True
        )

        return success_response(
            message='لیست سفارشات کارت هدیه',
            data=serializer.data
        )
    

# =========================================================
# REDEEM GIFT CARD
# =========================================================

class RedeemGiftCardAPIView(APIView):

    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):

        serial = request.data.get(
            'serial_number'
        )

        if not serial:

            return error_response(
                message='کد کارت الزامی است'
            )

        try:

            card = GiftCard.objects.get(
                serial_number=serial,
                status='ACTIVE',
                is_used=False
            )

        except GiftCard.DoesNotExist:

            return error_response(
                message='کارت هدیه نامعتبر است'
            )

        inventory, _ = GoldInventory.objects.get_or_create(
            user=request.user
        )

        inventory.balance += card.weight
        inventory.save()

        card.is_used = True
        card.status = 'USED'
        card.activated_by = request.user
        card.used_at = timezone.now()
        card.save()

        return success_response(

            message='کارت هدیه فعال شد',

            data={

                "weight_added": card.weight,

                "new_balance": inventory.balance
            }
        )


# =========================================================
# GIFT CARD LIST
# =========================================================

class GiftCardListAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        queryset = GiftCard.objects.filter(

            Q(created_by=request.user)
            |
            Q(activated_by=request.user)

        )

        # =====================================
        # STATUS FILTER
        # ACTIVE | INACTIVE
        # =====================================

        status = request.query_params.get(
            "status"
        )

        if status:

            status = status.upper()

            if status == "ACTIVE":

                queryset = queryset.filter(
                    status="ACTIVE"
                )

            elif status == "INACTIVE":

                queryset = queryset.exclude(
                    status="ACTIVE"
                )

        # =====================================
        # DATE FILTER
        # =====================================

        start_date = request.query_params.get(
            "start_date"
        )

        end_date = request.query_params.get(
            "end_date"
        )

        try:

            if start_date:

                if "/" in start_date:

                    y, m, d = map(
                        int,
                        start_date.split("/")
                    )

                    start_date = (
                        jdatetime.date(
                            y,
                            m,
                            d
                        ).togregorian()
                    )

                else:

                    start_date = datetime.strptime(
                        start_date,
                        "%Y-%m-%d"
                    ).date()

                queryset = queryset.filter(
                    created_at__date__gte=start_date
                )

            if end_date:

                if "/" in end_date:

                    y, m, d = map(
                        int,
                        end_date.split("/")
                    )

                    end_date = (
                        jdatetime.date(
                            y,
                            m,
                            d
                        ).togregorian()
                    )

                else:

                    end_date = datetime.strptime(
                        end_date,
                        "%Y-%m-%d"
                    ).date()

                queryset = queryset.filter(
                    created_at__date__lte=end_date
                )

        except Exception:

            return error_response(
                message="فرمت تاریخ اشتباه است (1405/03/13 یا 2026-06-03)"
            )

        queryset = queryset.order_by(
            "-created_at"
        )

        serializer = GiftCardSerializer(
            queryset,
            many=True
        )

        return success_response(
            message="لیست کارت هدیه",
            data=serializer.data
        )

    
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

        orders = Order.objects.filter(
            user=request.user
        ).order_by('-created_at')

        for item in orders:

            data.append({

                "id": item.id,

                "type": "PRODUCT_ORDER",

                "province": item.province,

                "city": item.city,

                "address": item.address,

                "postal_code": item.postal_code,

                "plaque": item.plaque,

                "unit": item.unit
            })

        # =====================================
        # GIFT CARD ORDERS
        # =====================================

        gifts = GiftCardOrder.objects.filter(
            user=request.user
        ).order_by('-created_at')

        for item in gifts:

            data.append({

                "id": item.id,

                "type": "GIFT_CARD_ORDER",

                "province": item.province,

                "city": item.city,

                "address": item.address,

                "postal_code": item.postal_code,

                "plaque": item.plaque,

                "unit": item.unit
            })

        return success_response(
            message='آدرس‌ها دریافت شد',
            data=data
        )



class GoldLimitOrderCreateAPIView(APIView):

    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):

        serializer = GoldOrderSerializer(
            data=request.data
        )

        if not serializer.is_valid():

            return error_response(
                message="اطلاعات نامعتبر است",
                data=serializer.errors
            )

        user = request.user

        order_type = serializer.validated_data["order_type"]

        target_price = Decimal(
            serializer.validated_data["target_price"]
        )

        amount_toman = serializer.validated_data.get(
            "amount_toman"
        )

        gold_weight = serializer.validated_data.get(
            "gold_weight"
        )

        fee_rate = Decimal("0.0099")

        if order_type == "BUY":

            amount_toman = Decimal(amount_toman)

            fee = amount_toman * fee_rate

            net_amount = amount_toman - fee

            estimated_weight = (
                net_amount / target_price
            )

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
            status="PENDING"
        )

        return success_response(
            message="سفارش با موفقیت ثبت شد",
            status_code=201,
            data={
                "order_id": order.id,
                "status": order.status,
            }
        )


class GoldLimitOrderListAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        orders = GoldOrder.objects.filter(
            user=request.user
        ).order_by("-created_at")

        serializer = GoldOrderListSerializer(
            orders,
            many=True
        )

        return success_response(
            message="لیست سفارشات",
            data=serializer.data
        )




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
            }
        )




class LatestPriceAPIView(APIView):

    permission_classes = [AllowAny]

    def get(self, request):

        key = request.GET.get("key")

        if not key:
            return error_response(message="key الزامی است")

        price = get_latest_price(key)

        if not price:
            return error_response(message="قیمت یافت نشد")

        return success_response(
            message="آخرین قیمت دریافت شد",
            data=price
        )
    
# =========================================================
# GOLD CHART API
# =========================================================

from .utils import get_live_gold_price, get_gold_chart_data, get_gold_bubble

class GoldChartAPIView(APIView):

    permission_classes = [AllowAny]

    def get(self, request):
        
        
        filter_type = request.GET.get('filter', '24H').upper()

        if filter_type not in ['24H', 'WEEKLY', 'MONTHLY']:
            return error_response(
                message="فیلتر نامعتبر است. مقادیر مجاز: 24H, WEEKLY, MONTHLY"
            )

        data = get_gold_chart_data(filter_type)

        live_price = get_live_gold_price()
        if live_price:
            data["stats"]["current_price"] = int(live_price)

        bubble = get_gold_bubble()
        data["bubble"] = bubble if bubble else {
            "buy_price": 0,
            "sell_price": 0,
            "bubble_amount": 0,
            "bubble_percent": 0,
            "is_positive": False,
        }

        return success_response(
            message="داده‌های نمودار طلا",
            data=data
        )
# gold_app/views.py




class GoldBannerListAPIView(APIView):

    permission_classes = [AllowAny]

    def get(self, request):

        banners = GoldBanner.objects.filter(
            is_active=True
        ).order_by("-id")

        serializer = GoldBannerSerializer(
            banners,
            many=True,
            context={"request": request}
        )

        return success_response(
            "بنرهای طلا",
            serializer.data
        )




class GoldPriceAPIView(APIView):

    permission_classes = [AllowAny]

    def get(self, request):

        data = get_group_prices("gold")

        if not data:
            return error_response(message="قیمت طلا یافت نشد")

        return success_response(
            message="قیمت لحظه‌ای طلا",
            data=data
        )
    

class CoinPriceAPIView(APIView):

    permission_classes = [AllowAny]

    def get(self, request):

        data = get_group_prices("coin")

        if not data:
            return error_response(message="قیمت سکه یافت نشد")

        return success_response(
            message="قیمت لحظه‌ای سکه",
            data=data
        )
    

class ParsianPriceAPIView(APIView):

    permission_classes = [AllowAny]

    def get(self, request):

        data = get_group_prices("parsian")

        if not data:
            return error_response(message="قیمت پارسیان یافت نشد")

        return success_response(
            message="قیمت لحظه‌ای پارسیان",
            data=data
        )
    

class AssetValueAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        user = request.user

        wallet = Wallet.objects.filter(
            user=user
        ).first()

        gold_inventory = GoldInventory.objects.filter(
            user=user
        ).first()

        silver_inventory = SilverInventory.objects.filter(
            user=user
        ).first()

        wallet_balance = (
            wallet.balance
            if wallet
            else Decimal("0")
        )

        gold_balance = (
            gold_inventory.balance
            if gold_inventory
            else Decimal("0")
        )

        silver_balance = (
            silver_inventory.balance
            if silver_inventory
            else Decimal("0")
        )

        gold_price = (
            get_live_gold_price()
            or Decimal("0")
        )

        silver_price = (
            get_live_silver_price()
            or Decimal("0")
        )

        gold_asset_value = (
            gold_balance * gold_price
        )

        silver_asset_value = (
            silver_balance * silver_price
        )

        total_asset_value = (
            wallet_balance +
            gold_asset_value +
            silver_asset_value
        )

        return Response({

            "total_asset_value": round(
                total_asset_value
            ),

            "gold_balance": gold_balance,

            "silver_balance": silver_balance,

            "wallet_balance": round(
                wallet_balance
            ),

            "gold_asset_value": round(
                gold_asset_value
            ),

            "silver_asset_value": round(
                silver_asset_value
            ),

            "gold_price": round(
                gold_price
            ),

            "silver_price": round(
                silver_price
            )

        })
    


class GoldStatisticsAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        user = request.user

        gold_price = (
            get_live_gold_price()
            or Decimal("0")
        )

        wallet = Wallet.objects.filter(
            user=user
        ).first()

        inventory = GoldInventory.objects.filter(
            user=user
        ).first()

        wallet_balance = (
            wallet.balance
            if wallet else Decimal("0")
        )

        gold_balance = (
            inventory.balance
            if inventory else Decimal("0")
        )

        total_assets = (
            wallet_balance +
            (gold_balance * gold_price)
        )

        withdrawn_gold = (
            FinancialTransaction.objects.filter(
                user=user,
                type="WITHDRAW",
                status="COMPLETED"
            ).aggregate(
                total=Sum("amount")
            )["total"]
            or 0
        )

        purchased_giftcards = (
            GiftCardOrder.objects.filter(
                user=user
            ).aggregate(
                total=Sum("total_price")
            )["total"]
            or 0
        )

        pending_toman = (
            FinancialTransaction.objects.filter(
                user=user,
                status="PENDING"
            ).aggregate(
                total=Sum("amount")
            )["total"]
            or 0
        )

        pending_gold = (
            inventory.blocked_balance
            if inventory else Decimal("0")
        )

        return Response({

            "total_assets": int(total_assets),

            "profit": 0,

            "withdrawn_gold": pending_gold,

            "purchased_giftcards": int(
                purchased_giftcards
            ),

            "received_giftcards": 0,

            "pending_toman": int(
                pending_toman
            ),

            "pending_gold": pending_gold

        })