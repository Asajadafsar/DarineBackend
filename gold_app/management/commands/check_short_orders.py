# gold_app/management/commands/check_short_orders.py

from django.core.management.base import BaseCommand
from gold_app.utils import check_short_orders


class Command(BaseCommand):
    help = 'چک و اجرای خودکار حد سود/حد ضرر فروش تعهدی'

    def handle(self, *args, **options):
        try:
            check_short_orders()
            self.stdout.write(
                self.style.SUCCESS("✅ سفارشات فروش تعهدی بررسی شدند")
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"❌ خطا: {e}")
            )