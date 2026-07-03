from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from gold_app.models import (
    GoldPriceHistory,
    PriceAlert,
    PriceAlertLog,
    Wallet,
)

from gold_app.sms_service import send_price_alert_sms


SMS_PRICE = Decimal("400")


def get_current_gold_price():
    """
    دریافت آخرین قیمت طلا
    """

    gold_price = (
        GoldPriceHistory.objects
        .order_by("-created_at")
        .first()
    )

    if not gold_price:
        return None

    return gold_price.price



def is_alert_triggered(alert, current_price):
    """
    بررسی رسیدن قیمت به تارگت
    """

    if current_price == alert.target_price:

        if alert.triggered:
            return False

        return True


    if alert.triggered:

        alert.triggered = False
        alert.save(
            update_fields=[
                "triggered"
            ]
        )

    return False




@transaction.atomic
def process_price_alert(alert, current_price):

    """
    اجرای ارسال آلارم
    """

    alert = (
        PriceAlert.objects
        .select_for_update()
        .get(pk=alert.pk)
    )


    wallet = (
        Wallet.objects
        .select_for_update()
        .get(user=alert.user)
    )


    # تعداد آلارم کامل شده
    if alert.sent_notifications >= alert.max_notifications:

        alert.status = "FINISHED"
        alert.is_active = False

        alert.save(
            update_fields=[
                "status",
                "is_active"
            ]
        )

        return



    # اگر رزرو پول تمام شده
    if wallet.blocked_balance < SMS_PRICE:

        PriceAlertLog.objects.create(
            alert=alert,
            price=current_price,
            sms_cost=SMS_PRICE,
            sms_status="FAILED",
            sms_response="Blocked balance finished"
        )

        return



    # ارسال پیامک
    sms_success = send_price_alert_sms(
        alert.user.mobile,
        current_price
    )



    if not sms_success:


        PriceAlertLog.objects.create(
            alert=alert,
            price=current_price,
            sms_cost=SMS_PRICE,
            sms_status="FAILED",
            sms_response="SMS provider error"
        )

        return




    # آزاد کردن هزینه یک پیام
    wallet.blocked_balance -= SMS_PRICE


    if wallet.blocked_balance < 0:
        wallet.blocked_balance = 0


    wallet.save(
        update_fields=[
            "blocked_balance"
        ]
    )



    # ثبت تاریخچه
    PriceAlertLog.objects.create(
        alert=alert,
        price=current_price,
        sms_cost=SMS_PRICE,
        sms_status="SUCCESS",
        sms_response="SMS sent successfully"
    )



    # بروزرسانی آلارم

    alert.sent_notifications += 1

    alert.last_triggered_price = current_price

    alert.last_triggered_at = timezone.now()

    alert.triggered = True



    # کامل شده
    if (
        alert.sent_notifications
        >=
        alert.max_notifications
    ):

        alert.status = "FINISHED"

        alert.is_active = False



    alert.save(
        update_fields=[
            "sent_notifications",
            "last_triggered_price",
            "last_triggered_at",
            "triggered",
            "status",
            "is_active",
        ]
    )




def run_price_alert_worker():

    """
    اجرا توسط cron / celery
    """

    current_price = get_current_gold_price()


    if current_price is None:
        return



    alerts = (
        PriceAlert.objects
        .select_related("user")
        .filter(
            is_active=True,
            status="ACTIVE"
        )
    )



    for alert in alerts:

        try:

            if is_alert_triggered(
                alert,
                current_price
            ):

                process_price_alert(
                    alert,
                    current_price
                )


        except Exception as exc:


            PriceAlertLog.objects.create(
                alert=alert,
                price=current_price,
                sms_cost=0,
                sms_status="FAILED",
                sms_response=str(exc)
            )