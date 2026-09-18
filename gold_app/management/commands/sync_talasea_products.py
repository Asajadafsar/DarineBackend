# gold_app/management/commands/sync_talasea_products.py

from decimal import Decimal, ROUND_DOWN

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from gold_app.models import Product, ProductCategory
from gold_app.services.talasea import TalaseaClient, TalaseaError


# =====================================================
# نقشه‌برداری دسته‌بندی طلاسی به دارینه
# =====================================================
CATEGORY_MAPPING = {
    "GOLD_BAR": {
        "name": "شمش طلا",
        "slug": "gold-bar",
    },
    "GOLD_COIN": {
        "name": "سکه طلا",
        "slug": "gold-coin",
    },
    "GOLD_INGOT": {
        "name": "شمش طلا",
        "slug": "gold-ingot",
    },
    "GOLD_JEWELRY": {
        "name": "جواهرات طلا",
        "slug": "gold-jewelry",
    },
}

# =====================================================
# تبدیل واحدها
# طلاسی: میلی‌گرم → دارینه: گرم
# =====================================================
MG_TO_GR = Decimal("1000")


class Command(BaseCommand):
    help = "سینک خودکار محصولات از طلاسی به دارینه"

    def add_arguments(self, parser):
        parser.add_argument(
            "--update-existing",
            action="store_true",
            help="محصولات موجود رو آپدیت کن (پیش‌فرض: فقط جدیدها)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="فقط نمایش بده، چیزی ذخیره نکن",
        )
        parser.add_argument(
            "--category",
            type=str,
            default=None,
            help="فقط یه دسته خاص (مثلاً GOLD_BAR)",
        )
        parser.add_argument(
            "--deactivate-missing",
            action="store_true",
            help="محصولاتی که دیگه توی طلاسی نیستن رو غیرفعال کن",
        )

    def handle(self, *args, **options):

        update_existing = options["update_existing"]
        dry_run = options["dry_run"]
        target_category = options["category"]
        deactivate_missing = options["deactivate_missing"]

        self.stdout.write(self.style.NOTICE("=" * 60))
        self.stdout.write(self.style.NOTICE("🔄 شروع سینک محصولات از طلاسی"))
        self.stdout.write(self.style.NOTICE("=" * 60))

        # =====================================================
        # 1. اتصال به طلاسی
        # =====================================================
        try:
            client = TalaseaClient()
            data = client.get_commodities()
        except TalaseaError as exc:
            self.stdout.write(self.style.ERROR(f"❌ خطا در طلاسی: {exc}"))
            return

        categories = data.get("categories", [])

        if not categories:
            self.stdout.write(self.style.WARNING("⚠️ هیچ کالایی از طلاسی برنگشت"))
            return

        # =====================================================
        # 2. آمار
        # =====================================================
        stats = {
            "created": 0,
            "updated": 0,
            "skipped": 0,
            "deactivated": 0,
            "categories_created": 0,
            "errors": [],
        }

        received_commodity_ids = set()

        # =====================================================
        # 3. پردازش هر دسته
        # =====================================================
        for cat in categories:
            talasea_category_name = cat.get("category", "")
            items = cat.get("items", [])

            if target_category and talasea_category_name != target_category:
                continue

            self.stdout.write(
                self.style.HTTP_INFO(
                    f"\n📦 دسته: {talasea_category_name} ({len(items)} کالا)"
                )
            )

            darine_category = self._get_or_create_category(
                talasea_category_name, stats, dry_run
            )

            for item in items:
                try:
                    commodity_id = item.get("id")
                    if commodity_id:
                        received_commodity_ids.add(commodity_id)

                    self._process_item(
                        item=item,
                        talasea_category_name=talasea_category_name,
                        darine_category=darine_category,
                        update_existing=update_existing,
                        dry_run=dry_run,
                        stats=stats,
                    )
                except Exception as exc:
                    error_msg = f"کالا {item.get('title', '?')}: {exc}"
                    stats["errors"].append(error_msg)
                    self.stdout.write(self.style.ERROR(f"   ❌ {error_msg}"))

        # =====================================================
        # 4. غیرفعال کردن محصولات حذف‌شده
        # =====================================================
        if deactivate_missing and not dry_run:
            self._deactivate_missing(received_commodity_ids, stats)
        elif deactivate_missing and dry_run:
            missing = Product.objects.filter(
                talasea_commodity_id__isnull=False,
                is_active=True,
            ).exclude(
                talasea_commodity_id__in=received_commodity_ids
            )
            count = missing.count()
            if count > 0:
                self.stdout.write(
                    self.style.WARNING(
                        f"\n⚠️ [DRY] {count} محصول غیرفعال می‌شد"
                    )
                )

        # =====================================================
        # 5. گزارش نهایی
        # =====================================================
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(self.style.SUCCESS("📊 گزارش نهایی:"))
        self.stdout.write(self.style.SUCCESS(f"   ✅ جدید: {stats['created']}"))
        self.stdout.write(self.style.SUCCESS(f"   🔄 آپدیت: {stats['updated']}"))
        self.stdout.write(self.style.WARNING(f"   ⏭️ نادیده: {stats['skipped']}"))
        self.stdout.write(
            self.style.SUCCESS(
                f"   📁 دسته‌های ساخته‌شده: {stats['categories_created']}"
            )
        )

        if deactivate_missing:
            self.stdout.write(
                self.style.WARNING(
                    f"   🚫 غیرفعال‌شده: {stats['deactivated']}"
                )
            )

        if stats["errors"]:
            self.stdout.write(self.style.ERROR(f"\n⚠️ {len(stats['errors'])} خطا:"))
            for err in stats["errors"]:
                self.stdout.write(self.style.ERROR(f"   - {err}"))

        if dry_run:
            self.stdout.write(
                self.style.WARNING("\n⚠️ حالت DRY-RUN: هیچ تغییری ذخیره نشد!")
            )

        self.stdout.write(self.style.SUCCESS("=" * 60))

    # =====================================================
    # HELPER: ساخت/دریافت دسته
    # =====================================================

    def _get_or_create_category(self, talasea_category_name, stats, dry_run):
        """ساخت یا دریافت دسته‌بندی دارینه"""

        mapping = CATEGORY_MAPPING.get(talasea_category_name)

        if mapping:
            name = mapping["name"]
            slug = mapping["slug"]
        else:
            name = talasea_category_name.replace("_", " ").title()
            slug = talasea_category_name.lower().replace("_", "-")

        if dry_run:
            category = ProductCategory.objects.filter(slug=slug).first()
            if not category:
                stats["categories_created"] += 1
                return ProductCategory(id=None, name=name, slug=slug)
            return category

        category, created = ProductCategory.objects.get_or_create(
            slug=slug,
            defaults={"name": name},
        )

        if created:
            stats["categories_created"] += 1
            self.stdout.write(
                self.style.SUCCESS(f"   📁 دسته جدید ساخته شد: {name}")
            )

        return category

    # =====================================================
    # HELPER: پاک‌سازی و انکود URL تصویر
    # =====================================================

    def _clean_url(self, url):
        """
        پاک‌سازی URL تصویر:
        - حذف فاصله‌های ابتدا و انتها
        - جایگزینی فاصله‌های داخل URL با %20
        """
        if not url:
            return None

        url = str(url).strip()

        if not url:
            return None

        # ✅ جایگزینی فاصله‌ها با %20
        url = url.replace(" ", "%20")

        return url

    # =====================================================
    # HELPER: استخراج URL تصویر از description (Fallback)
    # =====================================================

    def _extract_image_from_description(self, description):
        """
        استخراج URL تصویر از description (اگه imgUrl خالی بود)
        """
        if not description:
            return None

        import re
        match = re.search(r'تصویر مرجع:\s*(https?://\S+)', description)
        if match:
            url = match.group(1).strip()
            return self._clean_url(url)

        return None

    # =====================================================
    # HELPER: پردازش یک آیتم
    # =====================================================

    def _process_item(
        self,
        item,
        talasea_category_name,
        darine_category,
        update_existing,
        dry_run,
        stats,
    ):
        """پردازش یه کالا و ذخیره در دارینه"""

        commodity_id = item.get("id")
        title = item.get("title", "").strip()

        if not commodity_id or not title:
            stats["skipped"] += 1
            return

        # ---------------------------------------------------
        # تبدیل وزن
        # ---------------------------------------------------
        net_weight_mg = Decimal(str(item.get("netWeight", 0)))
        net_weight_gr = (net_weight_mg / MG_TO_GR).quantize(
            Decimal("0.001"), rounding=ROUND_DOWN
        )

        total_quantity_mg = Decimal(str(item.get("total_quantity", 0)))
        total_weight_with_fees_gr = (total_quantity_mg / MG_TO_GR).quantize(
            Decimal("0.001"), rounding=ROUND_DOWN
        )

        if total_weight_with_fees_gr <= 0:
            total_weight_with_fees_gr = net_weight_gr

        # ---------------------------------------------------
        # قیمت‌ها
        # ---------------------------------------------------
        irt_price = Decimal(str(item.get("irt_price", 0)))
        fee_irt = Decimal(str(item.get("feeIrt", 0)))
        fee_gold = Decimal(str(item.get("feeGold", 0)))

        if net_weight_gr > 0 and total_weight_with_fees_gr > net_weight_gr:
            profit_percent = (
                (total_weight_with_fees_gr - net_weight_gr)
                / net_weight_gr
                * 100
            ).quantize(Decimal("0.01"))
        else:
            profit_percent = Decimal("0")

        # ---------------------------------------------------
        # ✅ استخراج تصویر
        # ---------------------------------------------------
        # اول از imgUrl
        raw_img_url = item.get("imgUrl", "")
        img_url = self._clean_url(raw_img_url)

        # اگه imgUrl خالی بود، از description استخراج کن
        if not img_url:
            description = item.get("description", "")
            img_url = self._extract_image_from_description(description)

        # ---------------------------------------------------
        # موجودی
        # ---------------------------------------------------
        stock = int(item.get("stock", 0))

        # ---------------------------------------------------
        # carat
        # ---------------------------------------------------
        carat = item.get("carat")

        # ---------------------------------------------------
        # delivery methods
        # ---------------------------------------------------
        delivery_methods = item.get("deliveryMethods", ["PHYSICAL_DELIVERY"])

        if "DIGIEXPRESS_DELIVERY" in delivery_methods:
            delivery_type = "HOME"
        elif "PHYSICAL_DELIVERY" in delivery_methods:
            delivery_type = "IN_PERSON"
        else:
            delivery_type = "HOME"

        # ---------------------------------------------------
        # قیمت طلاسی
        # ---------------------------------------------------
        talasea_irt_price = int(irt_price) if irt_price > 0 else None

        # ---------------------------------------------------
        # بررسی وجود محصول
        # ---------------------------------------------------
        existing = Product.objects.filter(
            talasea_commodity_id=commodity_id
        ).first()

        if existing:
            # ---------------------------------------------
            # آپدیت محصول موجود
            # ---------------------------------------------
            if not update_existing:
                stats["skipped"] += 1
                self.stdout.write(
                    self.style.WARNING(f"   ⏭️ {title[:50]} (موجود)")
                )
                return

            if dry_run:
                stats["updated"] += 1
                self.stdout.write(
                    self.style.HTTP_INFO(f"   🔄 [DRY] {title[:50]}")
                )
                return

            existing.name = title
            existing.category = darine_category
            existing.delivery_type = delivery_type
            existing.weight = net_weight_gr
            existing.total_weight_with_fees = total_weight_with_fees_gr
            existing.sell_price = int(irt_price) if irt_price > 0 else existing.sell_price
            existing.inventory_count = stock
            existing.profit_percent = profit_percent
            existing.description = self._build_description(item, carat)
            existing.talasea_category = talasea_category_name
            existing.talasea_last_sync = timezone.now()
            existing.is_active = stock > 0

            # ✅ فیلدهای جدید
            existing.talasea_image_url = img_url
            existing.talasea_irt_price = talasea_irt_price
            existing.talasea_last_price_update = timezone.now()

            existing.save()

            stats["updated"] += 1
            self.stdout.write(
                self.style.SUCCESS(f"   🔄 {title[:50]}")
            )

        else:
            # ---------------------------------------------
            # محصول جدید
            # ---------------------------------------------
            if dry_run:
                stats["created"] += 1
                self.stdout.write(
                    self.style.HTTP_INFO(f"   ➕ [DRY] {title[:50]}")
                )
                return

            # چک تکراری نبودن اسم
            name_exists = Product.objects.filter(name=title).exists()
            final_name = title
            if name_exists:
                final_name = f"{title} ({commodity_id[-6:]})"

            product = Product.objects.create(
                name=final_name,
                category=darine_category,
                delivery_type=delivery_type,
                weight=net_weight_gr,
                total_weight_with_fees=total_weight_with_fees_gr,
                buy_price=None,
                sell_price=int(irt_price) if irt_price > 0 else None,
                inventory_count=stock,
                description=self._build_description(item, carat),
                profit_percent=profit_percent,
                is_active=stock > 0,
                talasea_commodity_id=commodity_id,
                talasea_category=talasea_category_name,
                talasea_last_sync=timezone.now(),
                # ✅ فیلدهای جدید
                talasea_image_url=img_url,
                talasea_irt_price=talasea_irt_price,
                talasea_last_price_update=timezone.now(),
            )

            stats["created"] += 1
            self.stdout.write(
                self.style.SUCCESS(f"   ➕ {title[:50]}")
            )

    # =====================================================
    # HELPER: ساخت توضیحات
    # =====================================================

    def _build_description(self, item, carat):
        """ساخت متن توضیحات خودکار"""

        parts = []

        if carat:
            parts.append(f"عیار: {carat}")

        net_weight_mg = item.get("netWeight", 0)
        net_weight_gr = Decimal(str(net_weight_mg)) / MG_TO_GR
        parts.append(f"وزن خالص: {net_weight_gr:.3f} گرم")

        total_quantity_mg = item.get("total_quantity", 0)
        total_quantity_gr = Decimal(str(total_quantity_mg)) / MG_TO_GR
        if total_quantity_gr > net_weight_gr:
            parts.append(f"وزن با اجرت: {total_quantity_gr:.3f} گرم")

        delivery_methods = item.get("deliveryMethods", [])
        if delivery_methods:
            methods_text = []
            if "PHYSICAL_DELIVERY" in delivery_methods:
                methods_text.append("ارسال پستی")
            if "DIGIEXPRESS_DELIVERY" in delivery_methods:
                methods_text.append("ارسال دیجی‌اکسپرس")
            if methods_text:
                parts.append(f"روش‌های ارسال: {'، '.join(methods_text)}")

        return "\n".join(parts)

    # =====================================================
    # HELPER: غیرفعال کردن محصولات حذف‌شده
    # =====================================================

    def _deactivate_missing(self, received_commodity_ids, stats):
        """محصولاتی که دیگه توی طلاسی نیستن رو غیرفعال کن"""

        missing = Product.objects.filter(
            talasea_commodity_id__isnull=False,
            is_active=True,
        ).exclude(
            talasea_commodity_id__in=received_commodity_ids
        )

        count = missing.count()

        if count == 0:
            return

        self.stdout.write(
            self.style.WARNING(f"\n🚫 {count} محصول دیگه توی طلاسی نیست:")
        )

        for product in missing:
            self.stdout.write(
                self.style.WARNING(f"   🚫 {product.name[:50]}")
            )

        with transaction.atomic():
            missing.update(is_active=False)

        stats["deactivated"] = count