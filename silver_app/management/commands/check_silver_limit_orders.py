# silver_app/management/commands/check_silver_limit_orders.py

from django.core.management.base import BaseCommand
from silver_app.utils import check_and_execute_silver_limit_orders
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'چک و اجرای خودکار سفارشات با قیمت نقره (Silver Limit Orders)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--quiet',
            action='store_true',
            help='خروجی کم‌تر نمایش بده',
        )

    def handle(self, *args, **options):
        quiet = options.get('quiet', False)
        
        try:
            executed = check_and_execute_silver_limit_orders()
            
            if not quiet:
                if executed > 0:
                    self.stdout.write(
                        self.style.SUCCESS(f"✅ {executed} سفارش نقره با موفقیت اجرا شد")
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING("ℹ️ هیچ سفارش نقره‌ای برای اجرا وجود نداشت")
                    )
            
            # لاگ کردن برای رصد
            if executed > 0:
                logger.info(f"✅ {executed} سفارش نقره اجرا شد")
                
        except Exception as e:
            error_msg = f"❌ خطا در اجرای سفارشات نقره: {str(e)}"
            self.stdout.write(
                self.style.ERROR(error_msg)
            )
            logger.error(error_msg)
            raise