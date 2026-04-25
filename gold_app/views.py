from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from decimal import Decimal

from silver_app.models import SilverInventory, SilverTransaction
from .models import AdminBankInfo, FinancialTransaction, GoldInventory, GoldTransaction
from .utils import get_live_gold_price
from .models import GoldInventory, GoldTransaction, Wallet
from .utils import get_live_gold_price

class BuyGold(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        price_per_gram = get_live_gold_price()
        if not price_per_gram:
            return Response({"error": "خطا در دریافت قیمت لحظه‌ای طلا"}, status=500)

        # دریافت ورودی‌ها از فرانت‌ند
        toman_amount = request.data.get('toman')   # اگر کاربر مبلغ وارد کند
        weight_amount = request.data.get('weight') # اگر کاربر وزن (گرم) وارد کند

        fee_rate = Decimal('0.01') # کارمزد ۱ درصد

        # سناریو ۱: خرید بر اساس مبلغ (تومان)
        if toman_amount:
            total_toman = Decimal(str(toman_amount))
            # در این حالت، مبلغ پرداختی کاربر ثابت است (مثلاً ۱ میلیون)
            # کارمزد از این مبلغ کسر می‌شود و باقی‌مانده تبدیل به طلا می‌شود
            fee = total_toman * fee_rate
            net_amount = total_toman - fee
            weight = net_amount / price_per_gram

        # سناریو ۲: خرید بر اساس وزن (گرم)
        elif weight_amount:
            weight = Decimal(str(weight_amount))
            # در این حالت، وزن طلا ثابت است (مثلاً ۰.۵ گرم)
            # کارمزد به مبلغ طلا اضافه می‌شود و مبلغ نهایی پرداختی محاسبه می‌شود
            net_amount = weight * price_per_gram
            fee = net_amount * fee_rate
            total_toman = net_amount + fee
            
        else:
            return Response({"error": "لطفاً مبلغ یا وزن را برای خرید وارد کنید"}, status=400)

        # ثبت تراکنش در دیتابیس
        transaction = GoldTransaction.objects.create(
            user=request.user,
            type='BUY',
            amount_gr=weight,
            price_per_gram=price_per_gram,
            fee=fee,
            total_amount=total_toman,
            is_completed=True
        )

        # آپدیت موجودی کاربر
        inventory, _ = GoldInventory.objects.get_or_create(user=request.user)
        inventory.balance = Decimal(str(inventory.balance)) + Decimal(str(weight))
        inventory.save()

        return Response({
            "message": "خرید با موفقیت انجام شد",
            "details": {
                "weight_gr": round(weight, 5),
                "price_per_gram": price_per_gram,
                "fee_toman": round(fee),
                "total_paid_toman": round(total_toman)
            }
        }, status=status.HTTP_201_CREATED)
    

class GoldBalance(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # ۱. دریافت قیمت لحظه‌ای برای محاسبه ارزش روز
        price_per_gram = get_live_gold_price()
        if not price_per_gram:
            return Response({"error": "خطا در دریافت قیمت لحظه‌ای"}, status=500)

        # ۲. پیدا کردن موجودی کاربر (اگر رکورد نداشت، موجودی صفر برمی‌گردانیم)
        inventory, created = GoldInventory.objects.get_or_create(user=request.user)
        
        gold_balance = Decimal(str(inventory.balance))
        
        # ۳. محاسبه ارزش ریالی موجودی
        total_value_toman = gold_balance * price_per_gram

        return Response({
            "gold_balance_gr": round(gold_balance, 5), # موجودی به گرم
            "current_gold_price": price_per_gram,      # قیمت هر گرم (تومان)
            "total_value_toman": round(total_value_toman), # ارزش کل دارایی (تومان)
        }, status=status.HTTP_200_OK)
    


class SellGold(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        price_per_gram = get_live_gold_price()
        if not price_per_gram:
            return Response({"error": "خطا در دریافت قیمت لحظه‌ای طلا"}, status=500)

        toman_amount = request.data.get('toman')
        weight_amount = request.data.get('weight')
        fee_rate = Decimal('0.01') 

        inventory, _ = GoldInventory.objects.get_or_create(user=request.user)
        wallet, _ = Wallet.objects.get_or_create(user=request.user)

        # محاسبه وزن و مبلغ پرداختی به کاربر
        if toman_amount:
            total_toman_request = Decimal(str(toman_amount))
            weight_to_sell = total_toman_request / price_per_gram
            fee = total_toman_request * fee_rate
            final_payout = total_toman_request - fee
        elif weight_amount:
            weight_to_sell = Decimal(str(weight_amount))
            raw_toman = weight_to_sell * price_per_gram
            fee = raw_toman * fee_rate
            final_payout = raw_toman - fee
        else:
            return Response({"error": "لطفاً مبلغ یا وزن را وارد کنید"}, status=400)

        # بررسی موجودی طلا
        if inventory.balance < weight_to_sell:
            return Response({"error": "موجودی طلای شما کافی نیست"}, status=400)

        # ثبت تراکنش
        GoldTransaction.objects.create(
            user=request.user,
            type='SELL',
            amount_gr=weight_to_sell,
            price_per_gram=price_per_gram,
            fee=fee,
            total_amount=final_payout,
            is_completed=True
        )

        # عملیات انتقال وجه و کسر طلا
        inventory.balance = Decimal(str(inventory.balance)) - Decimal(str(weight_to_sell))
        inventory.save()
        
        wallet.balance = Decimal(str(wallet.balance)) + Decimal(str(final_payout))
        wallet.save()

        return Response({
            "message": "فروش با موفقیت انجام شد و مبلغ به کیف پول واریز شد",
            "details": {
                "sold_weight": round(weight_to_sell, 5),
                "payout_toman": round(final_payout),
                "wallet_balance": round(wallet.balance)
            }
        })
    

from silver_app.models import SilverInventory
from .utils import get_live_gold_price, get_live_silver_price

class UserAssets(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # دریافت قیمت‌های لحظه‌ای
        gold_price = get_live_gold_price()
        silver_price = get_live_silver_price()

        # دریافت موجودی‌ها (اگر رکورد نباشد، ساخته می‌شود)
        gold_inv, _ = GoldInventory.objects.get_or_create(user=request.user)
        silver_inv, _ = SilverInventory.objects.get_or_create(user=request.user)
        wallet, _ = Wallet.objects.get_or_create(user=request.user)

        # تبدیل مقادیر به Decimal برای محاسبات دقیق
        gold_weight = Decimal(str(gold_inv.balance))
        silver_weight = Decimal(str(silver_inv.balance))
        wallet_balance = Decimal(str(wallet.balance))

        # محاسبه ارزش ریالی هر دارایی
        gold_value = gold_weight * gold_price
        silver_value = silver_weight * silver_price
        
        # مجموع کل دارایی‌ها
        total_assets_value = gold_value + silver_value + wallet_balance

        return Response({
            "total_assets_value": round(total_assets_value), # جمع کل (ریال + طلا + نقره)
            "gold_balance_gr": round(gold_weight, 5),
            "silver_balance_gr": round(silver_weight, 5),
            "wallet_balance_toman": round(wallet_balance),
            "gold_value_toman": round(gold_value),     # ارزش طلای کاربر به تومان
            "silver_value_toman": round(silver_value), # ارزش نقره کاربر به تومان
            "live_gold_price": gold_price,
            "live_silver_price": silver_price
        })

from .utils import get_live_silver_price 

class DepositMoney(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """نمایش اطلاعات حساب جهت واریز کاربر"""
        bank_info = AdminBankInfo.get_active_info()
        return Response(bank_info)

    def post(self, request):
        """ثبت رسید واریز وجه"""
        amount = request.data.get('amount')
        receipt = request.FILES.get('receipt')

        if not amount or not receipt:
            return Response({"error": "مبلغ و تصویر رسید الزامی است"}, status=400)

        FinancialTransaction.objects.create(
            user=request.user,
            amount=Decimal(str(amount)),
            type='DEPOSIT',
            method='CARD',
            receipt_image=receipt,
            status='PENDING'
        )
        return Response({"message": "رسید با موفقیت ثبت شد. پس از تایید مدیریت، کیف پول شارژ می‌شود."}, status=201)

from decimal import Decimal, InvalidOperation

class WithdrawMoney(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """درخواست برداشت وجه یا تبدیل به نقره"""
        amount_raw = request.data.get('amount')
        target = request.data.get('target')  # 'bank' or 'silver'

        if not amount_raw or not target:
            return Response({"error": "مبلغ و مقصد (target) الزامی هستند"}, status=400)

        try:
            # تبدیل امن به Decimal برای جلوگیری از خطای نوع داده
            amount = Decimal(str(amount_raw))
        except InvalidOperation:
            return Response({"error": "مبلغ وارد شده معتبر نیست"}, status=400)

        if amount <= 0:
            return Response({"error": "مبلغ باید بیشتر از صفر باشد"}, status=400)

        # دریافت کیف پول ریالی
        wallet, _ = Wallet.objects.get_or_create(user=request.user)
        # اطمینان از Decimal بودن موجودی کیف پول
        current_wallet_balance = Decimal(str(wallet.balance))

        if current_wallet_balance < amount:
            return Response({"error": "موجودی کیف پول کافی نیست"}, status=400)

        # --- سناریو ۱: تبدیل مستقیم به نقره ---
        if target == 'silver':
            silver_price = get_live_silver_price()
            if not silver_price:
                return Response({"error": "خطا در دریافت قیمت لحظه‌ای نقره"}, status=500)
            
            # محاسبه وزن نقره (Decimal / Decimal)
            weight_to_add = amount / silver_price

            # کسر از کیف پول ریالی
            wallet.balance = current_wallet_balance - amount
            wallet.save()

            # اضافه به موجودی نقره
            silver_inv, _ = SilverInventory.objects.get_or_create(user=request.user)
            # تبدیل موجودی فعلی به Decimal قبل از جمع
            silver_inv.balance = Decimal(str(silver_inv.balance)) + weight_to_add
            silver_inv.save()

            # ثبت در تاریخچه نقره
            SilverTransaction.objects.create(
                user=request.user,
                amount_gr=weight_to_add,
                total_amount=amount,
                type='CONVERT'
            )
            return Response({
                "message": "مبلغ با موفقیت به موجودی نقره تبدیل شد",
                "added_weight": round(weight_to_add, 5),
                "new_wallet_balance": wallet.balance
            })

        # --- سناریو ۲: درخواست واریز به حساب بانکی ---
        elif target == 'bank':
            card_id = request.data.get('card_id')
            if not card_id:
                return Response({"error": "برای واریز نقدی انتخاب کارت الزامی است"}, status=400)

            # ثبت تراکنش مالی ریالی
            FinancialTransaction.objects.create(
                user=request.user,
                amount=amount,
                type='WITHDRAW',
                method='CARD',
                user_card_id=card_id,
                status='PENDING'
            )
            
            # کسر از کیف پول (پول بلوکه می‌شود تا ادمین واریز کند)
            wallet.balance = current_wallet_balance - amount
            wallet.save()

            return Response({
                "message": "درخواست واریز نقدی ثبت شد و در صف بررسی قرار گرفت.",
                "new_wallet_balance": wallet.balance
            })

        return Response({"error": "مقصد نامعتبر است"}, status=400)
    

