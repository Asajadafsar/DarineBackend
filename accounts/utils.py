from decimal import Decimal

from rest_framework.response import Response

def success_response(message="", data=None, status_code=200):
    return Response({
        "success": True,
        "message": message,
        "data": data
    }, status=status_code)


def error_response(message="", errors=None, status_code=400):
    return Response({
        "success": False,
        "message": message,
        "errors": errors
    }, status=status_code)

from .models import FeeSetting, ReferralEarning


def apply_referral_bonus(user, amount, source_type):

    if not user.referred_by:
        return

    referrer = user.referred_by

    fee_setting = FeeSetting.objects.first()

    if source_type == "GOLD":
        percent = Decimal("0.01")  # یا از setting بخون
    else:
        percent = Decimal("0.008")

    bonus = amount * percent

    ReferralEarning.objects.create(
        referrer=referrer,
        user=user,
        amount=int(bonus),
        source_type=source_type
    )