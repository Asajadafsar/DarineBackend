# gold_app/services/physical_invoice_service.py - سرویس جدید

from decimal import Decimal
from django.utils import timezone
from gold_app.models import PhysicalOrderInvoice


class PhysicalOrderInvoiceService:
    """سرویس مدیریت فاکتورهای سفارش فیزیکی"""
    
    SHOP_NAME = 'فروشگاه دارینه'
    SHOP_NATIONAL_ID = '0371439477'
    SHOP_PHONE = '09191608771'
    SHOP_ADDRESS = 'قم، پاساژ شهر طلا، پلاک ۲۱'
    SHOP_PROVINCE = 'قم'
    
    @classmethod
    def create_invoice(cls, order, request=None):
        """
        ایجاد فاکتور برای سفارش فیزیکی تحویل شده
        
        Args:
            order: مدل Order
            request: درخواست (اختیاری)
        
        Returns:
            PhysicalOrderInvoice: فاکتور ایجاد شده
        """
        
        user = order.user
        
        # =============================================
        # اطلاعات خریدار (کاربر)
        # =============================================
        buyer_name = user.get_full_name() or user.mobile or 'کاربر'
        buyer_phone = user.mobile or '---'
        buyer_national_id = getattr(user, 'national_code', None) or '---'
        buyer_address = order.address or getattr(user, 'address', None) or '---'
        buyer_province = order.province or getattr(user, 'province', None) or '---'
        buyer_city = order.city or getattr(user, 'city', None) or '---'
        buyer_postal_code = order.postal_code or getattr(user, 'postal_code', None) or '---'
        
        # =============================================
        # محاسبه قیمت هر گرم طلا
        # =============================================
        if order.total_gold_amount and order.total_gold_amount > 0:
            price_per_gram = (order.total_toman_amount / order.total_gold_amount).quantize(Decimal('1'))
        else:
            price_per_gram = Decimal('0')
        
        # =============================================
        # ساخت خلاصه محصولات
        # =============================================
        products_summary = []
        for item in order.items.all():
            products_summary.append({
                'product_id': item.product.id,
                'product_name': item.product.title,
                'product_code': item.product.code,
                'quantity': int(item.quantity),
                'price_at_time': float(item.price_at_time),
                'weight_at_time': float(item.weight_at_time),
                'total_weight': float(item.weight_at_time * item.quantity),
                'total_price': float(item.price_at_time * item.quantity),
            })
        
        # =============================================
        # ایجاد فاکتور
        # =============================================
        invoice = PhysicalOrderInvoice.objects.create(
            order=order,
            invoice_type='BUY',
            status='CONFIRMED',
            
            # خریدار
            buyer_name=buyer_name,
            buyer_phone=buyer_phone,
            buyer_national_id=buyer_national_id,
            buyer_address=buyer_address,
            buyer_province=buyer_province,
            buyer_city=buyer_city,
            buyer_postal_code=buyer_postal_code,
            
            # فروشنده
            seller_name=cls.SHOP_NAME,
            seller_national_id=cls.SHOP_NATIONAL_ID,
            seller_phone=cls.SHOP_PHONE,
            seller_address=cls.SHOP_ADDRESS,
            seller_province=cls.SHOP_PROVINCE,
            
            # اطلاعات سفارش
            order_tracking_code=order.tracking_code,
            payment_method=order.payment_method,
            
            # اطلاعات طلا
            gold_weight=order.total_gold_amount,
            gold_carat=18,
            gold_price_per_gram=price_per_gram,
            pure_gold_price=order.total_toman_amount,
            
            # اطلاعات مالی
            shipping_fee=Decimal('0'),
            tax_amount=Decimal('0'),
            discount_amount=Decimal('0'),
            total_amount=order.total_toman_amount,
            
            # محصولات
            products_summary=products_summary,
            
            # توضیحات
            description=f"سفارش فیزیکی - شناسه: {order.id}"
        )
        
        # تولید شماره فاکتور
        invoice.invoice_number = invoice.generate_invoice_number()
        invoice.save()
        
        return invoice
    
    @classmethod
    def get_invoice_data(cls, invoice):
        """دریافت اطلاعات فاکتور برای نمایش"""
        
        import jdatetime
        from django.utils import timezone
        
        local_time = timezone.localtime(invoice.created_at)
        shamsi = jdatetime.datetime.fromgregorian(datetime=local_time)
        
        return {
            'id': invoice.id,
            'invoice_number': invoice.invoice_number,
            'invoice_type': invoice.invoice_type,
            'invoice_type_display': invoice.invoice_type_display,
            'status': invoice.status,
            'status_display': invoice.status_display,
            'invoice_date': shamsi.strftime('%Y/%m/%d %H:%M'),
            
            # خریدار
            'buyer_name': invoice.buyer_name,
            'buyer_national_id': invoice.buyer_national_id,
            'buyer_phone': invoice.buyer_phone,
            'buyer_address': invoice.buyer_address,
            'buyer_province': invoice.buyer_province,
            'buyer_city': invoice.buyer_city,
            'buyer_postal_code': invoice.buyer_postal_code,
            
            # فروشنده
            'seller_name': invoice.seller_name,
            'seller_national_id': invoice.seller_national_id,
            'seller_phone': invoice.seller_phone,
            'seller_address': invoice.seller_address,
            'seller_province': invoice.seller_province,
            
            # سفارش
            'order_tracking_code': invoice.order_tracking_code,
            'payment_method': invoice.payment_method,
            'payment_method_display': invoice.payment_method_display,
            
            # طلا
            'gold_weight': float(invoice.gold_weight),
            'gold_weight_display': f"{invoice.gold_weight:,.3f}",
            'gold_carat': invoice.gold_carat,
            'gold_price_per_gram': float(invoice.gold_price_per_gram),
            'pure_gold_price': float(invoice.pure_gold_price),
            'pure_gold_price_display': f"{int(invoice.pure_gold_price):,} تومان",
            
            # مالی
            'shipping_fee': float(invoice.shipping_fee),
            'tax_amount': float(invoice.tax_amount),
            'discount_amount': float(invoice.discount_amount),
            'total_amount': float(invoice.total_amount),
            'total_amount_display': f"{int(invoice.total_amount):,} تومان",
            
            # محصولات
            'products': invoice.products_summary,
            
            # تکمیلی
            'description': invoice.description,
        }