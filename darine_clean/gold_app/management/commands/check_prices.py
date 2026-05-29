# gold_app/management/commands/check_prices.py
from django.core.management.base import BaseCommand
from django.db import connection # اضافه شد
import time
from gold_app.models import PriceAlert
from gold_app.utils import get_live_gold_price

class Command(BaseCommand):
    help = 'Checks gold prices and triggers alerts'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Monitoring prices started..."))
        while True:
            try:
                current_price = get_live_gold_price()
                # پیدا کردن آلارم‌هایی که قیمت هدفشان کمتر یا مساوی قیمت فعلی است
                active_alerts = PriceAlert.objects.filter(is_active=True, target_price__lte=current_price)
                
                for alert in active_alerts:
                    self.stdout.write(self.style.WARNING(f"ALERT: {current_price} reached for {alert.user.mobile}"))
                    
                    if alert.alert_type == 'ONCE':
                        alert.is_active = False
                        alert.save()
                
                # بستن کانکشن دیتابیس برای جلوگیری از خطای Timeout در حلقه‌های طولانی
                connection.close() 
                time.sleep(60) 
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error: {e}"))
                time.sleep(10)