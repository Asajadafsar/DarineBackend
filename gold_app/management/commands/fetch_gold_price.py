from django.core.management.base import BaseCommand
from gold_app.utils import save_gold_price_history

class Command(BaseCommand):
    help = 'این دستور قیمت زنده طلا را گرفته و در دیتابیس ذخیره می‌کند'

    def handle(self, *args, **options):
        self.stdout.write("در حال دریافت و ذخیره قیمت طلا...")
        success = save_gold_price_history()
        
        if success:
            self.stdout.write(self.style.SUCCESS("قیمت طلا با موفقیت بروزرسانی شد."))
        else:
            self.stdout.write(self.style.ERROR("خطا در دریافت قیمت طلا."))