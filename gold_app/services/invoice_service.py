# gold_app/services/invoice_service.py

from gold_app.models import GoldTransaction, Invoice
import jdatetime
from datetime import datetime


class InvoiceService:
    """سرویس مدیریت فاکتورها"""

    SHOP_NAME = 'فروشگاه دارینه'
    SHOP_NATIONAL_ID = '0371439477'
    SHOP_PHONE = '09191608771'
    SHOP_ADDRESS = 'قم، پاساژ شهر طلا، پلاک ۲۱'
    SHOP_PROVINCE = 'قم'

    @staticmethod
    def create_buy_invoice(transaction: GoldTransaction, request=None):
        """ایجاد فاکتور خرید"""

        user = transaction.user

        buyer_name = user.get_full_name() or getattr(user, 'mobile', None) or 'کاربر'
        buyer_phone = getattr(user, 'mobile', None) or '---'
        buyer_national_id = getattr(user, 'national_code', None) or '---'
        buyer_address = getattr(user, 'address', None) or '---'
        buyer_province = getattr(user, 'province', None) or '---'

        invoice = Invoice.objects.create(
            transaction=transaction,
            invoice_type='BUY',

            # خریدار
            buyer_name=buyer_name,
            buyer_phone=buyer_phone,
            buyer_national_id=buyer_national_id,
            buyer_address=buyer_address,
            buyer_province=buyer_province,

            # فروشنده
            seller_name=InvoiceService.SHOP_NAME,
            seller_address=InvoiceService.SHOP_ADDRESS,
            seller_province=InvoiceService.SHOP_PROVINCE,

            gold_weight=transaction.amount_gr,
            gold_carat=18,
            gold_price_per_gram=transaction.price_per_gram,
            pure_gold_price=transaction.total_amount - transaction.commission_amount,
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
    def create_sell_invoice(transaction: GoldTransaction, request=None):
        """ایجاد فاکتور فروش"""

        user = transaction.user

        seller_name = user.get_full_name() or getattr(user, 'mobile', None) or 'کاربر'
        seller_phone = getattr(user, 'mobile', None) or '---'
        seller_national_id = getattr(user, 'national_code', None) or '---'
        seller_address = getattr(user, 'address', None) or '---'
        seller_province = getattr(user, 'province', None) or '---'

        invoice = Invoice.objects.create(
            transaction=transaction,
            invoice_type='SELL',

            # خریدار (دارینه)
            buyer_name=InvoiceService.SHOP_NAME,
            buyer_phone=InvoiceService.SHOP_PHONE,
            buyer_national_id=InvoiceService.SHOP_NATIONAL_ID,
            buyer_address=InvoiceService.SHOP_ADDRESS,
            buyer_province=InvoiceService.SHOP_PROVINCE,

            # فروشنده (کاربر)
            seller_name=seller_name,
            seller_address=seller_address,
            seller_province=seller_province,

            gold_weight=transaction.amount_gr,
            gold_carat=18,
            gold_price_per_gram=transaction.price_per_gram,
            pure_gold_price=transaction.total_amount + transaction.commission_amount,
            fee_rate=transaction.commission_percent,
            fee_amount=transaction.commission_amount,
            total_amount=transaction.total_amount,
            tracking_code=transaction.tracking_code,
            status='CONFIRMED' if transaction.status == 'COMPLETED' else 'PENDING'
        )

        # چون مدل Invoice این دو فیلد را ندارد،
        # اطلاعات کاربر را داخل description ذخیره می‌کنیم.
        invoice.description = (
            f"SELLER_PHONE={seller_phone}\n"
            f"SELLER_NATIONAL_ID={seller_national_id}"
        )

        invoice.invoice_number = invoice.generate_invoice_number()
        invoice.save()

        return invoice

    @staticmethod
    def get_invoice_data(invoice: Invoice):
        """دریافت اطلاعات فاکتور"""

        jalali_date = jdatetime.datetime.fromgregorian(datetime=invoice.created_at)
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

        weight = f"{invoice.gold_weight:,.3f}" if invoice.gold_weight else "۰"

        for e, p in persian_digits.items():
            weight = weight.replace(e, p)

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
            "invoice_type_display": "فاکتور خرید" if invoice.invoice_type == "BUY" else "فاکتور فروش",
            "invoice_date": f"{date_str} {time_str}",
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

            # ===== اطلاعات طلا =====
            "gold_weight": float(invoice.gold_weight or 0),
            "gold_weight_display": weight,
            "gold_carat": invoice.gold_carat,
            "gold_price_per_gram": float(invoice.gold_price_per_gram or 0),
            "gold_price_per_gram_display": format_price(invoice.gold_price_per_gram),
            "pure_gold_price": float(invoice.pure_gold_price or 0),
            "pure_gold_price_display": format_price(invoice.pure_gold_price),
            "fee_rate": float(invoice.fee_rate or 0),
            "fee_amount": float(invoice.fee_amount or 0),
            "fee_amount_display": format_price(invoice.fee_amount),
            "total_amount": float(invoice.total_amount or 0),
            "total_amount_display": format_price(invoice.total_amount),
            "tracking_code": invoice.tracking_code,
            "description": invoice.description,
        }

        return data