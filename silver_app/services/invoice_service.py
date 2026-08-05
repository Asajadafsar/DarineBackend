# silver_app/services/invoice_service.py - نسخه نهایی (عین طلا)

from silver_app.models import SilverInvoice
import jdatetime
from datetime import datetime


class SilverInvoiceService:
    """سرویس مدیریت فاکتورهای نقره"""

    SHOP_NAME = 'فروشگاه دارینه'
    SHOP_NATIONAL_ID = '0371439477'
    SHOP_PHONE = '09191608771'
    SHOP_ADDRESS = 'قم، پاساژ شهر طلا، پلاک ۲۱'
    SHOP_PROVINCE = 'قم'

    @staticmethod
    def create_buy_invoice(transaction, request=None):
        """ایجاد فاکتور خرید نقره"""

        user = transaction.user

        buyer_name = user.get_full_name() or getattr(user, 'mobile', None) or 'کاربر'
        buyer_phone = getattr(user, 'mobile', None) or '---'
        buyer_national_id = getattr(user, 'national_code', None) or '---'
        buyer_address = getattr(user, 'address', None) or '---'
        buyer_province = getattr(user, 'province', None) or '---'

        invoice = SilverInvoice.objects.create(
            transaction=transaction,
            invoice_type='BUY',

            # خریدار (کاربر)
            buyer_name=buyer_name,
            buyer_phone=buyer_phone,
            buyer_national_id=buyer_national_id,
            buyer_address=buyer_address,
            buyer_province=buyer_province,

            # فروشنده (دارینه)
            seller_name=SilverInvoiceService.SHOP_NAME,
            seller_address=SilverInvoiceService.SHOP_ADDRESS,
            seller_province=SilverInvoiceService.SHOP_PROVINCE,

            # اطلاعات نقره
            silver_weight=transaction.amount_gr,
            silver_price_per_gram=transaction.price_per_gram,
            pure_silver_price=transaction.total_amount - transaction.commission_amount,
            fee_rate=transaction.commission_percent,
            fee_amount=transaction.commission_amount,
            total_amount=transaction.total_amount,
            tracking_code=transaction.tracking_code,
            status='CONFIRMED' if transaction.status == 'COMPLETED' else 'PENDING'
        )

        invoice.invoice_number = invoice.generate_invoice_number()
        invoice.save()

        return invoice

    @staticmethod
    def create_sell_invoice(transaction, request=None):
        """ایجاد فاکتور فروش نقره"""

        user = transaction.user

        seller_name = user.get_full_name() or getattr(user, 'mobile', None) or 'کاربر'
        seller_phone = getattr(user, 'mobile', None) or '---'
        seller_national_id = getattr(user, 'national_code', None) or '---'
        seller_address = getattr(user, 'address', None) or '---'
        seller_province = getattr(user, 'province', None) or '---'

        invoice = SilverInvoice.objects.create(
            transaction=transaction,
            invoice_type='SELL',

            # خریدار (دارینه)
            buyer_name=SilverInvoiceService.SHOP_NAME,
            buyer_phone=SilverInvoiceService.SHOP_PHONE,
            buyer_national_id=SilverInvoiceService.SHOP_NATIONAL_ID,
            buyer_address=SilverInvoiceService.SHOP_ADDRESS,
            buyer_province=SilverInvoiceService.SHOP_PROVINCE,

            # فروشنده (کاربر) - فقط فیلدهایی که در مدل وجود دارند
            seller_name=seller_name,
            seller_address=seller_address,
            seller_province=seller_province,

            # اطلاعات نقره
            silver_weight=transaction.amount_gr,
            silver_price_per_gram=transaction.price_per_gram,
            pure_silver_price=transaction.total_amount + transaction.commission_amount,
            fee_rate=transaction.commission_percent,
            fee_amount=transaction.commission_amount,
            total_amount=transaction.total_amount,
            tracking_code=transaction.tracking_code,
            status='CONFIRMED' if transaction.status == 'COMPLETED' else 'PENDING'
        )

        # ذخیره اطلاعات تماس فروشنده در description
        invoice.description = (
            f"SELLER_PHONE={seller_phone}\n"
            f"SELLER_NATIONAL_ID={seller_national_id}"
        )

        invoice.invoice_number = invoice.generate_invoice_number()
        invoice.save()

        return invoice

    @staticmethod
    def get_invoice_data(invoice):
        """دریافت اطلاعات فاکتور"""

        import jdatetime
        from django.utils import timezone

        local_time = timezone.localtime(invoice.created_at)
        jalali_date = jdatetime.datetime.fromgregorian(datetime=local_time)
        date_str = jalali_date.strftime('%Y/%m/%d')
        time_str = jalali_date.strftime('%H:%M')

        persian_digits = {
            '0': '۰', '1': '۱', '2': '۲', '3': '۳', '4': '۴',
            '5': '۵', '6': '۶', '7': '۷', '8': '۸', '9': '۹'
        }

        def to_persian_num(value):
            value = str(value)
            for e, p in persian_digits.items():
                value = value.replace(e, p)
            return value

        def format_price(price):
            if not price:
                return "۰"
            value = f"{int(price):,}"
            for e, p in persian_digits.items():
                value = value.replace(e, p)
            return f"{value} تومان"

        weight = f"{invoice.silver_weight:,.3f}" if invoice.silver_weight else "۰"
        for e, p in persian_digits.items():
            weight = weight.replace(e, p)

        # استخراج اطلاعات تماس فروشنده از description
        seller_phone = "---"
        seller_national_id = "---"

        if invoice.description:
            for line in invoice.description.split("\n"):
                if line.startswith("SELLER_PHONE="):
                    seller_phone = line.replace("SELLER_PHONE=", "")
                elif line.startswith("SELLER_NATIONAL_ID="):
                    seller_national_id = line.replace("SELLER_NATIONAL_ID=", "")

        data = {
            "invoice_number": invoice.invoice_number,
            "invoice_type": invoice.invoice_type,
            "invoice_type_display": "فاکتور خرید نقره" if invoice.invoice_type == "BUY" else "فاکتور فروش نقره",
            "invoice_date": f"{date_str}  {time_str}",
            "status": invoice.status,

            # ===== اطلاعات خریدار =====
            "buyer_name": invoice.buyer_name or "---",
            "buyer_address": invoice.buyer_address or "---",
            "buyer_province": invoice.buyer_province or "---",

            # ===== اطلاعات فروشنده =====
            "seller_name": invoice.seller_name or "---",
            "seller_address": invoice.seller_address or "---",
            "seller_province": invoice.seller_province or "---",

            # ===== اطلاعات تماس =====
            "buyer_phone": (
                invoice.buyer_phone
                if invoice.invoice_type == "BUY"
                else "---"
            ),

            "buyer_national_id": (
                invoice.buyer_national_id
                if invoice.invoice_type == "BUY"
                else "---"
            ),

            "seller_phone": (
                "---"
                if invoice.invoice_type == "BUY"
                else seller_phone
            ),

            "seller_national_id": (
                "---"
                if invoice.invoice_type == "BUY"
                else seller_national_id
            ),

            # ===== اطلاعات نقره =====
            "silver_weight": float(invoice.silver_weight or 0),
            "silver_weight_display": weight,
            "silver_price_per_gram": float(invoice.silver_price_per_gram or 0),
            "silver_price_per_gram_display": format_price(invoice.silver_price_per_gram),
            "pure_silver_price": float(invoice.pure_silver_price or 0),
            "pure_silver_price_display": format_price(invoice.pure_silver_price),
            "fee_rate": float(invoice.fee_rate or 0),
            "fee_amount": float(invoice.fee_amount or 0),
            "fee_amount_display": format_price(invoice.fee_amount),
            "total_amount": float(invoice.total_amount or 0),
            "total_amount_display": format_price(invoice.total_amount),
            "tracking_code": invoice.tracking_code,
            "description": invoice.description,
        }

        return data