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


def apply_referral_bonus(user, amount, source_type):

    if not user.referred_by:
        return

    referrer = user.referred_by

    settings_obj = FeeSetting.objects.first()

    if not settings_obj:
        settings_obj = FeeSetting.objects.create()

    # درصد سود
    if source_type == "GOLD":

        percent = settings_obj.gold_referral_percent

    else:

        percent = settings_obj.silver_referral_percent

    bonus = Decimal(str(amount)) * Decimal(str(percent)) / Decimal("100")

    ReferralEarning.objects.create(
        referrer=referrer, user=user, amount=bonus, source_type=source_type
    )

    # واریز به کیف پول
    if source_type == "GOLD":

        wallet, _ = Wallet.objects.get_or_create(user=referrer)

        wallet.balance += bonus
        wallet.save()

    else:

        wallet, _ = SilverWallet.objects.get_or_create(user=referrer)

        wallet.balance += bonus
        wallet.save()
