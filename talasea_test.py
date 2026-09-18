"""
تست اتصال به طلاسی و وضعیت کاربر
"""
import os
import sys
import django
from pathlib import Path

# =====================================================
# پیدا کردن اسم پوشه settings
# =====================================================
BASE_DIR = Path(__file__).resolve().parent

settings_module = None

# چک کن کدوم پوشه settings.py داره
for item in BASE_DIR.iterdir():
    if item.is_dir() and (item / "settings.py").exists():
        settings_module = f"{item.name}.settings"
        break

if not settings_module:
    print("❌ پوشه settings پیدا نشد!")
    print("پوشه‌های موجود:")
    for item in BASE_DIR.iterdir():
        if item.is_dir():
            print(f"   - {item.name}")
    sys.exit(1)

print(f"✅ settings پیدا شد: {settings_module}")

os.environ.setdefault("DJANGO_SETTINGS_MODULE", settings_module)
django.setup()


# =====================================================
# حالا import کن
# =====================================================
from accounts.models import User
from gold_app.models import Wallet, GoldInventory, Order, Product
from gold_app.services.talasea import TalaseaClient, TalaseaError


def line(title):
    print()
    print("=" * 60)
    print(title)
    print("=" * 60)


# =====================================================
# 1. کاربر
# =====================================================
line("👤 کاربر")

user = User.objects.filter(mobile="09019621710").first()

if not user:
    print("❌ کاربر پیدا نشد")
    sys.exit(1)

print(f"✅ ID: {user.id}")
print(f"   Mobile: {user.mobile}")
print(f"   Active: {user.is_active}")


# =====================================================
# 2. کیف پول
# =====================================================
line("💰 کیف پول")

wallet = Wallet.objects.filter(user=user).first()

if wallet:
    print(f"   قابل برداشت: {wallet.accessible_toman:,} تومان")
    print(f"   بلوکه:       {wallet.blocked_toman:,} تومان")
    print(f"   کل:          {wallet.toman_total:,} تومان")
else:
    print("   ❌ کیف پول نداره")


# =====================================================
# 3. موجودی طلا
# =====================================================
line("🥇 موجودی طلا کاربر")

inv = GoldInventory.objects.filter(user=user).first()

if inv:
    print(f"   قابل برداشت: {inv.accessible_balance} گرم")
    print(f"   بلوکه:       {inv.blocked_balance} گرم")
    print(f"   کل:          {inv.total_balance} گرم")
else:
    print("   ❌ موجودی طلا نداره")


# =====================================================
# 4. سفارش‌ها
# =====================================================
line("📦 سفارش‌ها")

orders = Order.objects.filter(user=user)
print(f"   تعداد: {orders.count()}")

for o in orders.order_by("-created_at")[:5]:
    print(f"   - {o.tracking_code} | {o.status} | {o.total_toman_amount:,} تومان")


# =====================================================
# 5. موجودی طلاسی (حساب دارینه در طلاسی)
# =====================================================
line("🏦 موجودی طلاسی (حساب دارینه)")

try:
    client = TalaseaClient()
    client.login()
    print("✅ Login موفق")

    irt = client.get_irt_balance()
    print()
    print(f"💰 تومان در طلاسی:")
    print(f"   balance: {irt.get('balance', 0):,}")
    print(f"   blocked: {irt.get('blocked', 0):,}")

    gold = client.get_gold_balance()
    print()
    print(f"🥇 طلا در طلاسی:")
    print(f"   balance: {gold.get('balance', 0)}")
    print(f"   blocked: {gold.get('blocked', 0)}")

except TalaseaError as e:
    print(f"❌ خطا: {e}")


# =====================================================
# 6. محصولات سینک‌شده
# =====================================================
line("📦 محصولات سینک‌شده از طلاسی")

products = Product.objects.filter(
    talasea_commodity_id__isnull=False,
    is_active=True,
    inventory_count__gt=0,
).order_by("weight")

print(f"   تعداد: {products.count()}")
print()

for p in products[:5]:
    print(f"📦 {p.name}")
    print(f"   ID: {p.id}")
    print(f"   commodityId: {p.talasea_commodity_id}")
    print(f"   weight: {p.weight}g")
    print(f"   total_weight_with_fees: {p.total_weight_with_fees}g")
    print(f"   sell_price: {p.sell_price:,} تومان")
    print(f"   talasea_irt_price: {p.talasea_irt_price}")
    print(f"   image: {p.talasea_image_url}")
    print()


# =====================================================
# 7. یه محصول تست پیشنهاد بده
# =====================================================
line("🎯 محصول پیشنهادی برای تست")

test_product = Product.objects.filter(
    talasea_commodity_id__isnull=False,
    is_active=True,
    inventory_count__gt=0,
    weight__lt=5,  # کمتر از 5 گرم
).order_by("weight").first()

if test_product:
    print(f"📦 {test_product.name}")
    print(f"   ID: {test_product.id}")
    print(f"   وزن: {test_product.weight} گرم")
    print(f"   قیمت: {test_product.sell_price:,} تومان")
    print()
    print(f"👉 برای تست این body رو استفاده کن:")
    print()
    print("{")
    print(f'    "products": [{{"product_id": {test_product.id}, "quantity": 1}}],')
    print('    "payment_method": "TOMAN",')
    print('    "national_code": "1234567890",')
    print('    "phone_number": "09019621710",')
    print('    "province": "قم",')
    print('    "city": "قم",')
    print('    "address": "پاساژ شهر طلا، پلاک ۲۱",')
    print('    "postal_code": "3719813651",')
    print('    "plaque": "21",')
    print('    "unit": "1",')
    print('    "talasea_delivery_type": "PHYSICAL_DELIVERY",')
    print('    "talasea_city_id": 1,')
    print('    "time_id": "TIME_ID_FROM_API",')
    print('    "first_name": "سجاد",')
    print('    "last_name": "دارینه",')
    print('    "latitude": 34.6399,')
    print('    "longitude": 50.8759')
    print("}")


print()
print("=" * 60)
print("✅ تست کامل شد")
print("=" * 60)