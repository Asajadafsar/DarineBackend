from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from django.db.models import Sum
from decimal import Decimal, InvalidOperation
from .models import SilverInventory, SilverTransaction, BankCard
from .utils import get_live_silver_price
from gold_app.models import Wallet, FinancialTransaction, ReferralEarning, AdminBankInfo
from django.db import transaction
from accounts.models import BankCard as AccountsBankCard
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Sum
from .models import SilverTransaction
from decimal import Decimal
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
from decimal import Decimal
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
from decimal import Decimal
from .models import SilverProduct, PhysicalDeliveryOrder, SilverInventory
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import SilverTransaction, PhysicalDeliveryOrder




#کلاس خرید
class BuySilver(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        user = request.user
        # نرخ لحظه‌ای نقره را از تابع خودت می‌گیرد
        price = get_live_silver_price() 
        
        toman = request.data.get('toman')
        weight = request.data.get('weight')
        method = request.data.get('method')  # 'WALLET', 'GATEWAY', 'DIRECT_CARD'
        receipt = request.FILES.get('receipt')

        # ۱. محاسبه مقادیر (وزن یا مبلغ)
        if toman:
            total_toman = Decimal(str(toman))
            weight = total_toman / price
        elif weight:
            weight = Decimal(str(weight))
            total_toman = weight * price
        else:
            return Response({"error": "مبلغ یا وزن را وارد کنید"}, status=400)

        # ۲. متغیر کمکی برای واریز سود رفرال در انتهای متد
        is_purchase_finalized = False

        # ۳. سناریو اول: خرید مستقیم (درگاه یا فیش)
        if method in ['GATEWAY', 'DIRECT_CARD']:
            if method == 'DIRECT_CARD' and not receipt:
                return Response({"error": "برای واریز کارت به کارت، تصویر فیش الزامی است"}, status=400)

            # ثبت تراکنش مالی
            FinancialTransaction.objects.create(
                user=user,
                amount=total_toman,
                type='DEPOSIT',
                method='GATEWAY' if method == 'GATEWAY' else 'CARD',
                status='SUCCESS' if method == 'GATEWAY' else 'PENDING',
                receipt_image=receipt if method == 'DIRECT_CARD' else None,
                admin_note=f"خرید مستقیم {weight:.2f} گرم نقره"
            )

            # ثبت تراکنش نقره
            SilverTransaction.objects.create(
                user=user,
                type='BUY',
                amount_gr=weight,
                amount_toman=total_toman,
                status='DONE' if method == 'GATEWAY' else 'PENDING'
            )

            if method == 'GATEWAY':
                inv, _ = SilverInventory.objects.get_or_create(user=user)
                inv.balance += weight
                inv.save()
                is_purchase_finalized = True # خرید قطعی شد
                response_data = {"message": "خرید با درگاه موفق بود و نقره واریز شد", "weight": weight}
            else:
                return Response({"message": "فیش ثبت شد و پس از تایید مدیریت، نقره واریز و سود معرف محاسبه می‌شود"})

        # ۴. سناریو دوم: خرید از کیف پول (WALLET)
        elif method == 'WALLET':
            wallet, _ = Wallet.objects.get_or_create(user=user)
            if wallet.balance < total_toman:
                return Response({"error": "موجودی کیف پول کافی نیست"}, status=400)

            wallet.balance -= total_toman
            wallet.save()

            inv, _ = SilverInventory.objects.get_or_create(user=user)
            inv.balance += weight
            inv.save()

            SilverTransaction.objects.create(
                user=user, type='BUY', amount_gr=weight, amount_toman=total_toman, status='DONE'
            )
            is_purchase_finalized = True # خرید قطعی شد
            response_data = {"message": "خرید از کیف پول انجام شد", "weight": weight}
        
        else:
            return Response({"error": "روش پرداخت نامعتبر است"}, status=400)

        # ۵. منطق واریز سود رفرال (فقط برای خریدهای قطعی شده)
        if is_purchase_finalized and user.referred_by:
            referrer = user.referred_by
            
            # محاسبه سود: فرض می‌کنیم ۱ درصد مبلغ خرید کارمزد پلتفرم است
            # و شما ۲۰ درصد از آن ۱ درصد را به معرف می‌دهید
            platform_fee = total_toman * Decimal('0.01') 
            referral_commission = platform_fee * Decimal('0.20')

            if referral_commission > 0:
                # الف) ثبت تراکنش سود در لیست معاملات نقره/مالی معرف
                SilverTransaction.objects.create(
                    user=referrer,
                    type='REFERRAL_REWARD',
                    amount_gr=0,
                    amount_toman=referral_commission,
                    status='DONE'
                )
                # ب) اضافه کردن مبلغ به کیف پول ریالی معرف
                ref_wallet, _ = Wallet.objects.get_or_create(user=referrer)
                ref_wallet.balance += referral_commission
                ref_wallet.save()

        return Response(response_data)





# --- کلاس فروش ---
class SellSilver(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        user = request.user
        price = get_live_silver_price()
        
        if not price:
            return Response({"error": "خطا در دریافت قیمت لحظه‌ای"}, status=500)

        toman_input = request.data.get('toman')
        weight_input = request.data.get('weight')
        
        inventory, _ = SilverInventory.objects.get_or_create(user=user)

        # ۱. منطق محاسباتی هوشمند
        try:
            if toman_input:
                # کاربر می‌گوید: ۱۰۰ هزار تومان نقره بفروش
                total_toman_to_receive = Decimal(str(toman_input))
                # برای اینکه کاربر خالص ۱۰۰ ت بگیرد، باید معادل (۱۰۰ ت + کارمزد) نقره کسر شود
                # یا ساده‌تر: ۱۰۰ تومانی که می‌فروشد، قبل از کسر کارمزد چقدر بوده؟
                # Gross_Amount - (Gross_Amount * 0.01) = Net_Toman
                raw_toman_value = total_toman_to_receive / Decimal('0.99')
                weight_to_deduct = raw_toman_value / price
                fee = raw_toman_value * Decimal('0.01')
                final_payout = total_toman_to_receive
            elif weight_input:
                # کاربر می‌گوید: ۰.۵ گرم نقره بفروش
                weight_to_deduct = Decimal(str(weight_input))
                raw_toman_value = weight_to_deduct * price
                fee = raw_toman_value * Decimal('0.01')
                final_payout = raw_toman_value - fee
            else:
                return Response({"error": "لطفاً مبلغ یا وزن برای فروش را وارد کنید"}, status=400)
        except (InvalidOperation, ValueError):
            return Response({"error": "مقادیر وارد شده معتبر نیستند"}, status=400)

        # ۲. بررسی موجودی نقره کاربر
        if inventory.balance < weight_to_deduct:
            return Response({
                "error": "موجودی نقره کافی نیست",
                "required_gr": round(weight_to_deduct, 5),
                "your_balance": round(inventory.balance, 5)
            }, status=400)

        # ۳. کسر نقره و واریز تومان به کیف پول
        inventory.balance -= weight_to_deduct
        inventory.save()

        wallet, _ = Wallet.objects.get_or_create(user=user)
        wallet.balance += final_payout
        wallet.save()

        # ۴. ثبت تراکنش
        SilverTransaction.objects.create(
            user=user,
            type='SELL',
            amount_gr=weight_to_deduct,
            amount_toman=final_payout,
            status='DONE'
        )

        return Response({
            "message": "فروش با موفقیت انجام شد",
            "details": {
                "deducted_weight_gr": round(weight_to_deduct, 5),
                "payout_toman": round(final_payout),
                "fee_toman": round(fee),
                "new_silver_balance": round(inventory.balance, 5),
                "new_wallet_balance": round(wallet.balance)
            }
        }, status=status.HTTP_200_OK)





# --- داشبورد (تحلیلی) ---
class SilverDashboardAPI(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        price = get_live_silver_price()
        inv, _ = SilverInventory.objects.get_or_create(user=request.user)
        wallet, _ = Wallet.objects.get_or_create(user=request.user)
        return Response({
            "assets": {"total": round((inv.balance * price) + wallet.balance), "silver": round(inv.balance, 5), "toman": round(wallet.balance)},
            "price_info": {"current": price, "change": 9.56, "highest": 493000, "lowest": 391920}
        })





# --- کیف پول (عملیاتی) ---
class SilverWalletAPI(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        price = get_live_silver_price()
        inv, _ = SilverInventory.objects.get_or_create(user=request.user)
        wallet, _ = Wallet.objects.get_or_create(user=request.user)
        return Response({
            "wallet_header": {"total": round((inv.balance * price) + wallet.balance), "silver": round(inv.balance, 5), "toman": round(wallet.balance)},
            "summary": {"profit": round((inv.balance * price) - inv.total_spent_toman), "pending_toman": 0, "pending_silver": 0}
        })




# --- دیپوزیت و کارت ---
class SilverDeposit(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        FinancialTransaction.objects.create(user=request.user, amount=request.data['amount'], type='DEPOSIT', status='PENDING')
        return Response({"message": "در انتظار تایید"})




class BankCardAPI(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        return Response([{"id": c.id, "bank": c.bank_name, "card": c.card_number} for c in BankCard.objects.filter(user=request.user)])
    def post(self, request):
        BankCard.objects.create(user=request.user, bank_name=request.data['bank_name'], card_number=request.data['card_number'])
        return Response({"message": "ثبت شد"})



# --- بخش واریز (تومان) ---
class DepositMoney(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """دریافت اطلاعات حساب مدیریت برای واریز مستقیم"""
        bank_info = AdminBankInfo.get_active_info()
        return Response({
            "direct_deposit_info": bank_info,
            "methods": ["GATEWAY", "DIRECT_CARD_TO_CARD"]
        })

    def post(self, request):
        """ثبت واریز (چه درگاه، چه فیش)"""
        method = request.data.get('method') # 'GATEWAY' یا 'CARD'
        amount = request.data.get('amount')
        receipt = request.FILES.get('receipt')

        if not amount:
            return Response({"error": "مبلغ الزامی است"}, status=400)

        if method == 'CARD' and not receipt:
            return Response({"error": "برای واریز مستقیم، تصویر رسید الزامی است"}, status=400)

        transaction = FinancialTransaction.objects.create(
            user=request.user,
            amount=Decimal(str(amount)),
            type='DEPOSIT',
            method=method,
            status='PENDING' if method == 'CARD' else 'SUCCESS', # درگاه مستقیم موفق می‌شود
            receipt_image=receipt if method == 'CARD' else None
        )

        # اگر درگاه بود، موجودی کیف پول بلافاصله زیاد شود
        if method == 'GATEWAY':
            wallet, _ = Wallet.objects.get_or_create(user=request.user)
            wallet.balance += Decimal(str(amount))
            wallet.save()

        return Response({
            "message": "درخواست واریز ثبت شد",
            "transaction_id": transaction.id,
            "status": transaction.status
        })



#برداشت
class WithdrawMoney(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic  # استفاده از دکوریتور برای امنیت کل متد
    def post(self, request):
        """درخواست برداشت وجه یا انتقال به طلاینه"""
        amount_type = request.data.get('amount_type')
        card_id = request.data.get('card_id')
        destination = request.data.get('destination') # 'BANK_ACCOUNT' یا 'TALAYINEH'

        wallet, _ = Wallet.objects.get_or_create(user=request.user)

        # ۱. تعیین مبلغ
        try:
            if amount_type == 'TOTAL':
                amount = Decimal(str(wallet.balance))
            else:
                amount = Decimal(str(request.data.get('amount', 0)))
        except (InvalidOperation, ValueError, TypeError):
            return Response({"error": "مبلغ وارد شده معتبر نیست"}, status=400)

        # ۲. بررسی موجودی
        if amount <= 0:
            return Response({"error": "مبلغ باید بیشتر از صفر باشد"}, status=400)
        
        if wallet.balance < amount:
            return Response({"error": "موجودی کافی نیست"}, status=400)

        # ۳. کسر وجه از کیف پول (در هر دو حالت کسر می‌شود تا موجودی نقرینه صفر شود)
        wallet.balance -= amount
        wallet.save()

        # ۴. منطق ثبت تراکنش بر اساس مقصد
        if destination == 'TALAYINEH':
            # ثبت تراکنش انتقال داخلی
            FinancialTransaction.objects.create(
                user=request.user,
                amount=amount,
                type='TRANSFER', 
                method='INTERNAL',
                status='SUCCESS', # انتقال داخلی آنی تایید می‌شود
                admin_note=f"انتقال داخلی به بخش طلاینه"
            )
            
            # نکته: اگر می‌خواهی این پول در داشبورد طلا دیده شود، 
            # باید در آنجا تراکنش‌های TRANSFER موفق را با balance فعلی جمع کنی.
            
            return Response({
                "message": f"مبلغ {amount:,} تومان از نقرینه کسر و به طلاینه منتقل شد",
                "remaining_balance": round(wallet.balance)
            }, status=status.HTTP_200_OK)

        else:
            # حالت برداشت به حساب بانکی
            if not card_id:
                return Response({"error": "انتخاب کارت بانکی الزامی است"}, status=400)
            
            try:
                user_card_obj = AccountsBankCard.objects.get(id=card_id, user=request.user)
            except AccountsBankCard.DoesNotExist:
                return Response({"error": "کارت انتخاب شده یافت نشد"}, status=400)

            FinancialTransaction.objects.create(
                user=request.user,
                amount=amount,
                type='WITHDRAW',
                method='CARD',
                status='PENDING',
                user_card=user_card_obj,
                admin_note=f"برداشت به حساب بانکی"
            )

            return Response({
                "message": f"درخواست برداشت مبلغ {amount:,} تومان ثبت شد",
                "remaining_balance": round(wallet.balance)
            }, status=status.HTTP_201_CREATED)
        





# ایمپورت مدل‌های خود اپلیکیشن سیلور
from .models import SilverProduct, PhysicalDeliveryOrder, SilverInventory

# ایمپورت مدل کیف پول از اپلیکیشن اصلی (نام اپلیکیشن را چک کن)
try:
    from gold_app.models import Wallet # اگر نام اپلیکیشن طلا چیزی مثل 'gold' است، اصلاح کن
except ImportError:
    # اگر هنوز مدل والت رو نداری یا جای دیگه‌ست، برای اینکه کد کرش نکنه:
    Wallet = None

class SilverProductListView(APIView):
    def get(self, request):
        products = SilverProduct.objects.filter(is_active=True)
        current_silver_price = Decimal('471589') 

        product_list = []
        for p in products:
            product_list.append({
                "id": p.id,
                "title": p.title,
                "pure_weight_gr": p.weight_gr,
                "total_weight_gr": p.total_weight_with_packaging,
                "price_toman": round(p.total_weight_with_packaging * current_silver_price),
            })
        
        inventory, _ = SilverInventory.objects.get_or_create(user=request.user)
        
        # هندل کردن نمایش موجودی تومان اگر مدل والت در دسترس بود
        toman_balance = 0
        if Wallet:
            wallet, _ = Wallet.objects.get_or_create(user=request.user)
            toman_balance = wallet.balance

        return Response({
            "products": product_list,
            "user_assets": {
                "silver_balance": inventory.balance,
                "toman_balance": toman_balance
            }
        })









class SubmitPhysicalDelivery(APIView):
    def post(self, request):
        product_id = request.data.get('product_id')
        payment_method = request.data.get('payment_method')   # 'SILVER' یا 'TOMAN'
        delivery_method = request.data.get('delivery_method') # 'COURIER' یا 'IN_PERSON'
        address = request.data.get('address')
        postal_code = request.data.get('postal_code')
        
        # قیمت لحظه‌ای نقره (می‌توانید از تابع get_live_price استفاده کنید)
        current_silver_price = Decimal('471589') 

        try:
            with transaction.atomic():
                # ۱. پیدا کردن محصول
                product = SilverProduct.objects.get(id=product_id)
                weight_needed = product.total_weight_with_packaging
                price_needed = round(weight_needed * current_silver_price)

                # ۲. هندل کردن روش‌های پرداخت
                if payment_method == 'SILVER':
                    # کسر از موجودی نقره
                    inventory, _ = SilverInventory.objects.select_for_update().get_or_create(user=request.user)
                    if inventory.balance < weight_needed:
                        return Response({"error": "موجودی نقره شما برای این محصول کافی نیست"}, status=400)
                    
                    inventory.balance -= weight_needed
                    inventory.total_withdrawn_gr += weight_needed
                    inventory.save()
                    msg = "سفارش با کسر از موجودی نقره ثبت شد."

                elif payment_method == 'TOMAN':
                    # در این حالت فقط سفارش ثبت می‌شود تا بعداً تسویه شود
                    msg = "سفارش با روش پرداخت تومانی ثبت شد. منتظر تماس کارشناسان باشید."
                
                else:
                    return Response({"error": "روش پرداخت انتخاب شده معتبر نیست"}, status=400)

                # ۳. بررسی متد تحویل
                if delivery_method == 'COURIER' and not address:
                    return Response({"error": "آدرس برای ارسال پستی الزامی است"}, status=400)

                # ۴. ایجاد رکورد سفارش در دیتابیس
                order = PhysicalDeliveryOrder.objects.create(
                    user=request.user,
                    product=product,
                    weight_at_time_of_order=weight_needed,
                    total_price_toman=price_needed,
                    payment_method=payment_method,
                    delivery_method=delivery_method,
                    address=address if delivery_method == 'COURIER' else "تحویل حضوری در دفتر",
                    postal_code=postal_code if delivery_method == 'COURIER' else None,
                    status='PENDING'
                )

                return Response({
                    "message": msg,
                    "order_id": order.id,
                    "final_price_toman": price_needed,
                    "product_title": product.title
                }, status=status.HTTP_201_CREATED)

        except SilverProduct.DoesNotExist:
            return Response({"error": "محصول مورد نظر یافت نشد"}, status=404)
        except Exception as e:
            return Response({"error": f"خطای غیرمنتظره: {str(e)}"}, status=500)




class UserReportsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        report_type = request.query_params.get('type')
        data = []

        try:
            # ۱. معاملات (trades)
            if report_type == 'trades':
                query = SilverTransaction.objects.filter(user=user).order_by('-created_at')
                data = [{
                    "id": t.id,
                    "type": t.type,
                    "amount_gr": str(t.amount_gr),
                    "amount_toman": str(t.amount_toman),
                    "status": t.status,
                    "date": t.created_at.strftime('%Y-%m-%d %H:%M') if t.created_at else None
                } for t in query]

            # ۲. مالی (financial)
            elif report_type == 'financial':
                query = SilverTransaction.objects.filter(user=user).order_by('-created_at')
                data = [{
                    "id": t.id,
                    "type": "واریز/برداشت",
                    "amount_toman": str(t.amount_toman),
                    "status": t.status,
                    "date": t.created_at.strftime('%Y-%m-%d %H:%M') if t.created_at else None
                } for t in query]

            # ۳. تحویل فیزیکی (اصلاح شده)
            elif report_type == 'physical':
                query = PhysicalDeliveryOrder.objects.filter(user=user).select_related('product').order_by('-created_at')
                data = [{
                    "id": o.id,
                    "product": o.product.title if o.product else "محصول حذف شده",
                    "weight": str(o.weight_at_time_of_order),
                    "price": str(o.total_price_toman),
                    "payment": o.payment_method,
                    "delivery": o.delivery_method,
                    "status": o.status,
                    "address": o.address or "تحویل حضوری",
                    "date": o.created_at.strftime('%Y-%m-%d %H:%M') if o.created_at else None
                } for o in query] # <--- اینجا اصلاح شد (for o in query)

            else:
                return Response({"error": "Type is invalid"}, status=400)

            return Response({
                "status": "success",
                "type": report_type,
                "results": data
            })

        except Exception as e:
            # نمایش دقیق خطا در کنسول برای دیباگ
            print(f"Error in Reports: {str(e)}")
            return Response({"error": "Internal Server Error", "detail": str(e)}, status=500)
        







class ReferralDashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        
        # ۱. تعداد افراد دعوت شده (زیرمجموعه‌ها)
        subscribers_count = user.subscribers.count()
        
        # ۲. محاسبه مجموع سود دریافتی از رفرال
        # نکته: در مدل سیلور، تراکنش‌هایی با تایپ REFERRAL_REWARD را جمع می‌زنیم
        total_earned = SilverTransaction.objects.filter(
            user=user, 
            type='REFERRAL_REWARD',
            status='DONE'
        ).aggregate(total=Sum('amount_toman'))['total'] or 0

        # ۳. لیست موبایل‌های افراد دعوت شده (برای شفافیت بیشتر)
        subscribers_list = user.subscribers.values_list('mobile', flat=True)

        return Response({
            "referral_code": user.referral_code,
            "statistics": {
                "total_subscribers": subscribers_count,
                "total_earnings_toman": int(total_earned),
                "commission_percentage": "20%",
            },
            "subscribers": subscribers_list,
            "message": "با دعوت از دوستان، 20% از کارمزد معاملات آن‌ها به حساب شما واریز می‌شود."
        })

