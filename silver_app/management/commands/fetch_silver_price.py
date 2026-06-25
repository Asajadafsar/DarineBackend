from django.core.management.base import BaseCommand
from silver_app.utils import save_silver_price_history

class Command(BaseCommand):
    help = 'این دستور قیمت زنده نقره را گرفته و در دیتابیس ذخیره می‌کند'

    def handle(self, *args, **options):
        self.stdout.write("در حال دریافت و ذخیره قیمت نقره...")
        success = save_silver_price_history()
        
        if success:
            self.stdout.write(self.style.SUCCESS("قیمت نقره با موفقیت بروزرسانی شد."))
        else:
            self.stdout.write(self.style.ERROR("خطا در دریافت قیمت نقره."))