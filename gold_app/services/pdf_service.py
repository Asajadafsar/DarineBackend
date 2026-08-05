# gold_app/services/pdf_service.py - اصلاح نهایی

import io
import os
import requests
import logging
from django.http import HttpResponse
from django.conf import settings
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_RIGHT, TA_CENTER
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import arabic_reshaper
from bidi.algorithm import get_display

logger = logging.getLogger(__name__)


class InvoicePDFService:
    """سرویس تولید PDF فاکتور با دیزاین لاکچری طلایی/سرمه‌ای"""

    FONT_REGULAR_URLS = [
        "https://raw.githubusercontent.com/rastikerdar/vazirmatn/master/fonts/ttf/Vazirmatn-Regular.ttf",
        "https://cdn.jsdelivr.net/gh/rastikerdar/vazirmatn@master/fonts/ttf/Vazirmatn-Regular.ttf",
    ]
    FONT_BOLD_URLS = [
        "https://raw.githubusercontent.com/rastikerdar/vazirmatn/master/fonts/ttf/Vazirmatn-Bold.ttf",
        "https://cdn.jsdelivr.net/gh/rastikerdar/vazirmatn@master/fonts/ttf/Vazirmatn-Bold.ttf",
    ]

    FONT_DIR = os.path.join(settings.BASE_DIR, 'static', 'fonts')
    FONT_REGULAR_FILENAME = 'Vazirmatn-Regular.ttf'
    FONT_BOLD_FILENAME = 'Vazirmatn-Bold.ttf'
    FONT_REGULAR_PATH = os.path.join(FONT_DIR, FONT_REGULAR_FILENAME)
    FONT_BOLD_PATH = os.path.join(FONT_DIR, FONT_BOLD_FILENAME)

    # ==================================================================
    # پالت رنگ لاکچری طلایی/سرمه‌ای
    # ==================================================================
    GOLD = colors.HexColor('#C9A227')
    GOLD_LIGHT = colors.HexColor('#E7C766')
    GOLD_PALE = colors.HexColor('#F6EBC7')
    INK = colors.HexColor('#12121C')
    NAVY = colors.HexColor('#20203A')
    CREAM = colors.HexColor('#FDF9EF')
    GRAY = colors.HexColor('#8B8B99')
    LINE_GRAY = colors.HexColor('#E7E2D6')
    WATERMARK = colors.HexColor('#F4F0E4')
    WHITE = colors.HexColor('#FFFFFF')
    RIBBON_SHADOW = colors.HexColor('#8A7328')
    HEADER_SUBTEXT = colors.HexColor('#D8D6E8')
    TRACK_SUBTEXT = colors.HexColor('#B9B7CC')

    PAGE_MARGIN = 9 * mm
    CONTENT_PAD = 11 * mm

    # ------------------------------------------------------------------
    # فونت
    # ------------------------------------------------------------------
    @classmethod
    def _ensure_font_dir(cls):
        if not os.path.exists(cls.FONT_DIR):
            os.makedirs(cls.FONT_DIR, exist_ok=True)

    @classmethod
    def _download_one(cls, path, urls):
        if os.path.exists(path):
            return True
        cls._ensure_font_dir()
        for url in urls:
            try:
                resp = requests.get(url, timeout=30)
                if resp.status_code == 200 and resp.content:
                    with open(path, 'wb') as f:
                        f.write(resp.content)
                    return True
            except Exception:
                continue
        return False

    @classmethod
    def _register_fonts(cls):
        reg_name, bold_name = 'Helvetica', 'Helvetica-Bold'
        try:
            if cls._download_one(cls.FONT_REGULAR_PATH, cls.FONT_REGULAR_URLS):
                pdfmetrics.registerFont(TTFont('PersianFont', cls.FONT_REGULAR_PATH))
                reg_name = 'PersianFont'
        except Exception:
            logger.exception("خطا در ثبت فونت فارسی regular")

        try:
            if cls._download_one(cls.FONT_BOLD_PATH, cls.FONT_BOLD_URLS):
                pdfmetrics.registerFont(TTFont('PersianFontBold', cls.FONT_BOLD_PATH))
                bold_name = 'PersianFontBold'
            elif reg_name == 'PersianFont':
                bold_name = 'PersianFont'
        except Exception:
            logger.exception("خطا در ثبت فونت فارسی bold")
            bold_name = reg_name

        return reg_name, bold_name

    @staticmethod
    def fix_persian_text(text):
        if not text:
            return ''
        try:
            reshaped_text = arabic_reshaper.reshape(str(text))
            return get_display(reshaped_text)
        except Exception:
            return str(text)

    # ------------------------------------------------------------------
    # ابزارهای رسم تزئینی
    # ------------------------------------------------------------------
    @staticmethod
    def _draw_diamond(c, cx, cy, size, color, filled=True, stroke_w=0.6):
        p = c.beginPath()
        p.moveTo(cx, cy + size)
        p.lineTo(cx + size, cy)
        p.lineTo(cx, cy - size)
        p.lineTo(cx - size, cy)
        p.close()
        if filled:
            c.setFillColor(color)
            c.drawPath(p, stroke=0, fill=1)
        else:
            c.setStrokeColor(color)
            c.setLineWidth(stroke_w)
            c.drawPath(p, stroke=1, fill=0)

    @classmethod
    def _draw_diamond_row(cls, c, cx, cy, count, gap, base_size, color):
        half = count // 2
        for i in range(-half, half + 1):
            size = base_size * (1 - abs(i) / (half + 1.6))
            cls._draw_diamond(c, cx + i * gap, cy, size, color)

    @staticmethod
    def _draw_gradient_rect(c, x, y, w, h, color_top, color_bottom, steps=48):
        r1, g1, b1 = color_top.red, color_top.green, color_top.blue
        r2, g2, b2 = color_bottom.red, color_bottom.green, color_bottom.blue
        step_h = h / steps
        for i in range(steps):
            t = i / (steps - 1)
            r = r1 + (r2 - r1) * t
            g = g1 + (g2 - g1) * t
            b = b1 + (b2 - b1) * t
            c.setFillColorRGB(r, g, b)
            c.rect(x, y + i * step_h, w, step_h + 0.5, stroke=0, fill=1)

    @staticmethod
    def _draw_text_engraved(c, x, y, text, font, size, color, shadow_color, align='right', offset=0.28 * mm):
        c.setFont(font, size)
        c.setFillColor(shadow_color)
        fn = {'right': c.drawRightString, 'center': c.drawCentredString, 'left': c.drawString}[align]
        fn(x, y - offset, text)
        c.setFillColor(color)
        fn(x, y, text)

    @staticmethod
    def _draw_ribbon(c, cx, cy, w, h, point, fill_color):
        x0 = cx - w / 2
        x1 = cx + w / 2
        top = cy + h / 2
        bot = cy - h / 2
        p = c.beginPath()
        p.moveTo(x0, top)
        p.lineTo(x1, top)
        p.lineTo(x1 + point, cy)
        p.lineTo(x1, bot)
        p.lineTo(x0, bot)
        p.lineTo(x0 - point, cy)
        p.close()
        c.setFillColor(fill_color)
        c.drawPath(p, stroke=0, fill=1)

    # ------------------------------------------------------------------
    # تولید PDF
    # ------------------------------------------------------------------
    @classmethod
    def generate_invoice_pdf(cls, invoice_id, request):
        from ..models import Invoice
        from .invoice_service import InvoiceService

        try:
            invoice = Invoice.objects.get(id=invoice_id, transaction__user=request.user)
        except Invoice.DoesNotExist:
            return None

        data = InvoiceService.get_invoice_data(invoice)

        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="invoice_{invoice.invoice_number}.pdf"'

        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4
        font_name, font_bold = cls._register_fonts()
        styles = getSampleStyleSheet()

        CONTENT_LEFT = cls.PAGE_MARGIN + cls.CONTENT_PAD
        CONTENT_RIGHT = width - cls.PAGE_MARGIN - cls.CONTENT_PAD
        CONTENT_WIDTH = CONTENT_RIGHT - CONTENT_LEFT

        # ============================================================
        # واترمارک مرکزی
        # ============================================================
        cls._draw_diamond(c, width / 2, height / 2, 42 * mm, cls.WATERMARK, filled=False, stroke_w=1.2)
        cls._draw_diamond(c, width / 2, height / 2, 30 * mm, cls.WATERMARK, filled=False, stroke_w=1.2)
        cls._draw_diamond(c, width / 2, height / 2, 3 * mm, cls.WATERMARK, filled=True)

        # ============================================================
        # بوردر دوتایی
        # ============================================================
        c.setStrokeColor(cls.GOLD)
        c.setLineWidth(1.1)
        c.roundRect(cls.PAGE_MARGIN, cls.PAGE_MARGIN, width - 2 * cls.PAGE_MARGIN, height - 2 * cls.PAGE_MARGIN, 4 * mm, stroke=1, fill=0)
        c.setStrokeColor(cls.GOLD_LIGHT)
        c.setLineWidth(0.4)
        c.roundRect(
            cls.PAGE_MARGIN + 1.6 * mm, cls.PAGE_MARGIN + 1.6 * mm,
            width - 2 * cls.PAGE_MARGIN - 3.2 * mm, height - 2 * cls.PAGE_MARGIN - 3.2 * mm,
            3.2 * mm, stroke=1, fill=0,
        )

        corner_inset = cls.PAGE_MARGIN + 5 * mm
        for cx_sign, cy_sign in [(1, 1), (-1, 1), (1, -1), (-1, -1)]:
            cx = width / 2 + cx_sign * (width / 2 - corner_inset)
            cy = height / 2 + cy_sign * (height / 2 - corner_inset)
            cls._draw_diamond(c, cx, cy, 2.6 * mm, cls.GOLD)
            cls._draw_diamond(c, cx, cy, 1.1 * mm, cls.GOLD_LIGHT)

        # ============================================================
        # هدر با گرادیانت سرمه‌ای به مشکی
        # ============================================================
        HEADER_H = 38 * mm
        header_top = height - cls.PAGE_MARGIN
        header_bottom = header_top - HEADER_H
        cls._draw_gradient_rect(c, cls.PAGE_MARGIN, header_bottom, width - 2 * cls.PAGE_MARGIN, HEADER_H, cls.NAVY, cls.INK)

        c.setStrokeColor(cls.GOLD)
        c.setLineWidth(1)
        c.line(cls.PAGE_MARGIN, header_bottom, width - cls.PAGE_MARGIN, header_bottom)
        c.setStrokeColor(cls.GOLD_LIGHT)
        c.setLineWidth(0.4)
        c.line(cls.PAGE_MARGIN, header_bottom - 1.3 * mm, width - cls.PAGE_MARGIN, header_bottom - 1.3 * mm)

        cls._draw_diamond(c, CONTENT_LEFT + 2.5 * mm, header_top - 10 * mm, 2.4 * mm, cls.GOLD)

        y = header_top - 14 * mm
        cls._draw_text_engraved(
            c, CONTENT_RIGHT, y, cls.fix_persian_text("فروشگاه دارینه"),
            font_bold, 25, cls.GOLD_LIGHT, cls.INK, align='right',
        )

        # ✅ فقط آدرس فروشگاه
        y -= 8.5 * mm
        c.setFont(font_name, 9.5)
        c.setFillColor(cls.HEADER_SUBTEXT)
        c.drawRightString(CONTENT_RIGHT, y, cls.fix_persian_text(data.get('seller_address', '')))

        # ❌ خطوط تلفن و شناسه حذف شدند

        y = header_bottom - 13 * mm

        # ============================================================
        # ✅ ریبون عنوان فاکتور (فارسی)
        # ============================================================
        RIBBON_W = 82 * mm
        RIBBON_H = 15 * mm
        cls._draw_ribbon(c, width / 2 + 0.7 * mm, y - RIBBON_H / 2 - 0.7 * mm, RIBBON_W, RIBBON_H, 5 * mm, cls.RIBBON_SHADOW)
        cls._draw_ribbon(c, width / 2, y - RIBBON_H / 2, RIBBON_W, RIBBON_H, 5 * mm, cls.GOLD)

        c.setFont(font_bold, 13)
        c.setFillColor(cls.INK)

        # ✅ عنوان فارسی
        invoice_type = data.get('invoice_type', '')
        if 'خرید' in invoice_type or invoice_type == 'BUY':
            title_text = 'فاکتور خرید'
        elif 'فروش' in invoice_type or invoice_type == 'SELL':
            title_text = 'فاکتور فروش'
        else:
            title_text = invoice_type

        c.drawCentredString(width / 2, y - RIBBON_H / 2 - 1.6 * mm, cls.fix_persian_text(title_text))

        y -= RIBBON_H + 8 * mm
        c.setFont(font_name, 8)
        c.setFillColor(cls.GRAY)

        # ✅ ترکیب تاریخ و ساعت
        invoice_date = data.get('invoice_date', '')
        meta_line = f"شماره: {data.get('invoice_number', '')}      تاریخ: {invoice_date}"
        c.drawCentredString(width / 2, y, cls.fix_persian_text(meta_line))

        y -= 6 * mm
        cls._draw_diamond_row(c, width / 2, y, 7, 6 * mm, 1.1 * mm, cls.GOLD_LIGHT)
        y -= 8 * mm

        # ============================================================
        # ✅ جدول اطلاعات خریدار (فروشنده حذف شد)
        # ============================================================
        title_style = ParagraphStyle(
            'TitleStyle', parent=styles['Normal'], fontName=font_bold, fontSize=10,
            alignment=TA_CENTER, textColor=cls.GOLD_LIGHT, leading=14,
        )
        rtl_style = ParagraphStyle(
            'RTLStyle', parent=styles['Normal'], fontName=font_name, fontSize=8.3,
            alignment=TA_RIGHT, leading=13.5, textColor=cls.INK,
        )

        # ✅ فقط اطلاعات خریدار
        buyer_name = data.get('buyer_name', '---')
        buyer_national = data.get('buyer_national_id', '---')
        buyer_phone = data.get('buyer_phone', '---')
        buyer_address = data.get('buyer_address', '---')

        # ✅ اطلاعات فروشنده (فقط نام و آدرس)
        seller_name = data.get('seller_name', '---')
        seller_address = data.get('seller_address', '---')

        info_data = [
            [
                Paragraph(cls.fix_persian_text('خریدار'), title_style),
                Paragraph(cls.fix_persian_text('فروشنده'), title_style),
            ],
            [
                Paragraph(cls.fix_persian_text(f"نام: {buyer_name}"), rtl_style),
                Paragraph(cls.fix_persian_text(f"نام: {seller_name}"), rtl_style),
            ],
            [
                Paragraph(cls.fix_persian_text(f"کد ملی: {buyer_national}"), rtl_style),
                Paragraph(cls.fix_persian_text(""), rtl_style),
            ],
            [
                Paragraph(cls.fix_persian_text(f"تلفن: {buyer_phone}"), rtl_style),
                Paragraph(cls.fix_persian_text(""), rtl_style),
            ],
            [
                Paragraph(cls.fix_persian_text(f"آدرس: {buyer_address}"), rtl_style),
                Paragraph(cls.fix_persian_text(f"آدرس: {seller_address}"), rtl_style),
            ],
        ]

        info_table = Table(info_data, colWidths=[CONTENT_WIDTH / 2, CONTENT_WIDTH / 2])
        info_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), font_name),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BACKGROUND', (0, 0), (-1, 0), cls.NAVY),
            ('BACKGROUND', (0, 1), (-1, -1), cls.CREAM),
            ('BOX', (0, 0), (-1, -1), 0.8, cls.GOLD),
            ('INNERGRID', (0, 0), (-1, -1), 0.4, cls.LINE_GRAY),
            ('TOPPADDING', (0, 0), (-1, -1), 4.5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4.5),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ]))
        iw, ih = info_table.wrap(CONTENT_WIDTH, height)
        y -= ih
        info_table.drawOn(c, CONTENT_LEFT, y)

        y -= 9 * mm
        cls._draw_diamond_row(c, width / 2, y, 7, 6 * mm, 1.1 * mm, cls.GOLD)
        y -= 9 * mm

        # ============================================================
        # جدول جزئیات طلا
        # ============================================================
        gold_header_style = ParagraphStyle(
            'GH', parent=styles['Normal'], fontName=font_bold, fontSize=9.2,
            alignment=TA_CENTER, textColor=cls.WHITE, leading=13,
        )
        gold_value_style = ParagraphStyle(
            'GV', parent=styles['Normal'], fontName=font_bold, fontSize=11,
            alignment=TA_CENTER, textColor=cls.INK, leading=15,
        )
        gold_summary_style = ParagraphStyle(
            'GS', parent=styles['Normal'], fontName=font_name, fontSize=9,
            alignment=TA_CENTER, textColor=cls.INK, leading=13,
        )
        gold_total_label_style = ParagraphStyle(
            'GTL', parent=styles['Normal'], fontName=font_name, fontSize=9.5,
            alignment=TA_CENTER, textColor=cls.GOLD_LIGHT, leading=13,
        )
        gold_total_style = ParagraphStyle(
            'GT', parent=styles['Normal'], fontName=font_bold, fontSize=15,
            alignment=TA_CENTER, textColor=cls.GOLD_LIGHT, leading=19,
        )

        gold_weight = data.get('gold_weight_display', data.get('gold_weight', '0'))
        gold_carat = data.get('gold_carat', 18)
        gold_price = data.get('gold_price_per_gram_display', data.get('gold_price_per_gram', '0'))
        pure_price = data.get('pure_gold_price_display', data.get('pure_gold_price', '0'))
        fee_rate = data.get('fee_rate', '0')
        fee_amount = data.get('fee_amount_display', data.get('fee_amount', '0'))
        total_amount = data.get('total_amount_display', data.get('total_amount', '0'))

        gold_data = [
            [
                Paragraph(cls.fix_persian_text('وزن (گرم)'), gold_header_style),
                Paragraph(cls.fix_persian_text('عیار'), gold_header_style),
                Paragraph(cls.fix_persian_text('قیمت هر گرم'), gold_header_style),
                Paragraph(cls.fix_persian_text('قیمت خالص'), gold_header_style),
            ],
            [
                Paragraph(cls.fix_persian_text(str(gold_weight)), gold_value_style),
                Paragraph(cls.fix_persian_text(str(gold_carat)), gold_value_style),
                Paragraph(cls.fix_persian_text(str(gold_price)), gold_value_style),
                Paragraph(cls.fix_persian_text(str(pure_price)), gold_value_style),
            ],
            [
                Paragraph(
                    cls.fix_persian_text(f"کارمزد ({fee_rate}%): {fee_amount}"),
                    gold_summary_style,
                ),
                '',
                Paragraph(cls.fix_persian_text('مبلغ کل قابل پرداخت'), gold_total_label_style),
                Paragraph(cls.fix_persian_text(str(total_amount)), gold_total_style),
            ],
        ]

        col_w = CONTENT_WIDTH / 4
        gold_table = Table(gold_data, colWidths=[col_w, col_w, col_w * 0.85, col_w * 1.15])
        gold_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), font_name),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('SPAN', (0, 2), (1, 2)),
            ('BACKGROUND', (0, 0), (-1, 0), cls.NAVY),
            ('BACKGROUND', (0, 1), (-1, 1), cls.GOLD_PALE),
            ('BACKGROUND', (0, 2), (1, 2), cls.CREAM),
            ('BACKGROUND', (2, 2), (3, 2), cls.INK),
            ('BOX', (0, 0), (-1, -1), 0.8, cls.GOLD),
            ('INNERGRID', (0, 0), (-1, 1), 0.4, cls.GOLD_LIGHT),
            ('LINEABOVE', (0, 2), (-1, 2), 0.8, cls.GOLD),
            ('TOPPADDING', (0, 0), (-1, -1), 7),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
        ]))
        gw, gh = gold_table.wrap(CONTENT_WIDTH, height)
        y -= gh
        gold_table.drawOn(c, CONTENT_LEFT, y)

        y -= 11 * mm

        # ============================================================
        # کد رهگیری
        # ============================================================
        TRACK_H = 20 * mm
        TRACK_W = 100 * mm
        c.setFillColor(cls.NAVY)
        c.roundRect(width / 2 - TRACK_W / 2, y - TRACK_H, TRACK_W, TRACK_H, 4 * mm, stroke=0, fill=1)
        c.setStrokeColor(cls.GOLD)
        c.setLineWidth(0.8)
        c.roundRect(width / 2 - TRACK_W / 2, y - TRACK_H, TRACK_W, TRACK_H, 4 * mm, stroke=1, fill=0)
        cls._draw_diamond(c, width / 2 - TRACK_W / 2 + 5 * mm, y - TRACK_H / 2, 1.6 * mm, cls.GOLD_LIGHT)
        cls._draw_diamond(c, width / 2 + TRACK_W / 2 - 5 * mm, y - TRACK_H / 2, 1.6 * mm, cls.GOLD_LIGHT)

        c.setFont(font_name, 8)
        c.setFillColor(cls.TRACK_SUBTEXT)
        c.drawCentredString(width / 2, y - 6.5 * mm, cls.fix_persian_text("کد رهگیری"))
        c.setFont(font_bold, 13)
        c.setFillColor(cls.GOLD_LIGHT)
        c.drawCentredString(width / 2, y - 14.5 * mm, cls.fix_persian_text(data.get('tracking_code', '---')))

        y -= TRACK_H + 13 * mm

        # ============================================================
        # امضاها
        # ============================================================
        c.setFont(font_name, 8)
        c.setFillColor(cls.GRAY)
        c.drawRightString(83 * mm, y, cls.fix_persian_text("امضای خریدار"))
        c.setStrokeColor(cls.LINE_GRAY)
        c.setLineWidth(0.6)
        c.line(CONTENT_LEFT, y - 4 * mm, 83 * mm, y - 4 * mm)

        cls._draw_diamond(c, width / 2, y - 3 * mm, 4.2 * mm, cls.GOLD_PALE, filled=False, stroke_w=0.8)
        cls._draw_diamond(c, width / 2, y - 3 * mm, 2.6 * mm, cls.GOLD)

        c.setFont(font_name, 8)
        c.setFillColor(cls.GRAY)
        c.drawRightString(CONTENT_RIGHT, y, cls.fix_persian_text("امضای فروشنده"))
        c.line(width - 83 * mm, y - 4 * mm, CONTENT_RIGHT, y - 4 * mm)

        y -= 17 * mm

        # ============================================================
        # فوتر
        # ============================================================
        c.setStrokeColor(cls.GOLD)
        c.setLineWidth(1.1)
        c.line(CONTENT_LEFT, y, CONTENT_RIGHT, y)
        c.setStrokeColor(cls.GOLD_LIGHT)
        c.setLineWidth(0.4)
        c.line(CONTENT_LEFT, y - 1 * mm, CONTENT_RIGHT, y - 1 * mm)

        y -= 7.5 * mm
        c.setFont(font_bold, 10.5)
        c.setFillColor(cls.GOLD)
        c.drawCentredString(width / 2, y, cls.fix_persian_text("فروشگاه دارینه"))

        y -= 6 * mm
        c.setFont(font_name, 7)
        c.setFillColor(cls.GRAY)
        c.drawCentredString(width / 2, y, cls.fix_persian_text("این فاکتور به عنوان مدرک معتبر خرید/فروش طلا محسوب می‌شود"))

        y -= 5 * mm
        c.setFont(font_name, 6)
        c.setFillColor(cls.LINE_GRAY)
        c.drawCentredString(width / 2, y, cls.fix_persian_text("کلیه حقوق محفوظ است"))

        c.save()

        pdf = buffer.getvalue()
        buffer.close()

        response.write(pdf)
        return response