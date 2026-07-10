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



@transaction.atomic
def create_referral_profit(
    user,
    source_type,
    transaction_amount,
):

    # اگر معرف ندارد
    if not user.referred_by:
        return None


    # درصد فعلی رفرال
    setting = ReferralSetting.objects.first()

    if not setting:
        return None


    percent = setting.commission_percent


    # محاسبه سود
    profit = (
        Decimal(transaction_amount)
        *
        percent
        /
        Decimal("100")
    )


    # ثبت تاریخچه سود رفرال
    earning = ReferralEarning.objects.create(

        referrer=user.referred_by,

        user=user,

        source_type=source_type,

        transaction_amount=transaction_amount,

        commission_percent=percent,

        commission_amount=profit,

        marketer_percent=percent,

        profit=profit,
    )


    # =====================================
    # واریز به کیف پول معرف
    # =====================================


    if source_type == "GOLD":

        wallet, _ = Wallet.objects.get_or_create(
            user=user.referred_by
        )

        wallet.accessible_toman += profit

        wallet.save()


    elif source_type == "SILVER":

        wallet, _ = SilverWallet.objects.get_or_create(
            user=user.referred_by
        )

        wallet.accessible_toman += profit

        wallet.save()


    return earning