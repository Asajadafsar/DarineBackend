from decimal import Decimal

from rest_framework.response import Response


def success_response(message="", data=None, status_code=200):
    return Response(
        {"success": True, "message": message, "data": data}, status=status_code
    )


def error_response(message="اطلاعات نامعتبر است", errors=None, status_code=400):

    formatted_errors = []

    if errors:

        for field, msgs in errors.items():

            for msg in msgs:

                formatted_errors.append({"field": field, "message": msg})

        # ساخت message کلی از همه خطاها
        message = "، ".join([f"{item['message']}" for item in formatted_errors])

    return Response(
        {"success": False, "message": message, "errors": formatted_errors},
        status=status_code,
    )


from .models import FeeSetting, ReferralEarning


from accounts.models import ReferralEarning, FeeSetting

from gold_app.models import Wallet
from silver_app.models import SilverWallet



from decimal import Decimal

from django.db import transaction

from accounts.models import ReferralSetting, ReferralEarning

from gold_app.models import Wallet
from silver_app.models import SilverWallet



# accounts/utils.py

def get_user_referral_percent(user):
    """
    دریافت درصد رفرال کاربر
    اگر کاربر تنظیمات اختصاصی دارد، از آن استفاده کن
    در غیر این صورت از تنظیمات عمومی استفاده کن
    """
    from accounts.models import UserFee, FeeSetting, ReferralSetting
    
    # چک کردن اینکه آیا کاربر تنظیمات اختصاصی در UserFee دارد؟
    # از آنجایی که UserFee فیلد referral_percent ندارد، 
    # از یک روش جایگزین استفاده میکنیم: 
    # اگر کاربر در ReferralEarning به عنوان referrer ثبت شده باشد،
    # آخرین درصدی که برای او ثبت شده را میگیریم
    
    latest_earning = ReferralEarning.objects.filter(
        referrer=user
    ).order_by('-created_at').first()
    
    if latest_earning:
        # اگر سودی برای این کاربر ثبت شده، از همان درصد استفاده کن
        return latest_earning.commission_percent
    
    # در غیر این صورت از تنظیمات عمومی استفاده کن
    setting = ReferralSetting.objects.first()
    if setting:
        return setting.commission_percent
    
    return Decimal("20")  # مقدار پیش‌فرض



# accounts/utils.py

@transaction.atomic
def create_referral_profit(
    user,
    source_type,
    transaction_amount,
    commission_amount,
):
    """
    ایجاد سود رفرال بر اساس کارمزد معامله
    سود رفرال = درصد رفرال × کارمزد معامله
    """
    
    # فقط برای طلا
    if source_type != "GOLD":
        return None
    
    # اگر معرف ندارد
    if not user.referred_by:
        return None
    
    referrer = user.referred_by
    
    # ✅ دریافت درصد رفرال از آخرین سود ثبت شده برای این کاربر
    # یا از تنظیمات عمومی
    percent = get_user_referral_percent(referrer)
    
    # محاسبه سود از کارمزد
    profit = (
        Decimal(commission_amount) * percent / Decimal("100")
    ).quantize(Decimal("1"))
    
    # اگر سود صفر بود، ثبت نشود
    if profit <= 0:
        return None
    
    # ثبت تاریخچه سود رفرال
    earning = ReferralEarning.objects.create(
        referrer=referrer,
        user=user,
        source_type=source_type,
        transaction_amount=transaction_amount,
        commission_amount=commission_amount,
        commission_percent=percent,  # ✅ درصد فعلی ذخیره میشه
        marketer_percent=percent,
        profit=profit,
    )
    
    # واریز به کیف پول طلای معرف
    wallet, _ = Wallet.objects.get_or_create(
        user=referrer
    )
    wallet.accessible_toman += profit
    wallet.save()
    
    return earning