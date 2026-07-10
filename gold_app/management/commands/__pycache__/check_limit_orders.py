# gold_app/management/commands/check_limit_orders.py

from django.core.management.base import BaseCommand
from gold_app.utils import check_and_execute_limit_orders


class Command(BaseCommand):
    help = 'چک و اجرای خودکار سفارشات با قیمت (Limit Orders)'

    def handle(self, *args, **options):
        try:
            executed = check_and_execute_limit_orders()
            self.stdout.write(
                self.style.SUCCESS(f"✅ {executed} سفارش با موفقیت اجرا شد")
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"❌ خطا در اجرای سفارشات: {e}")
            )