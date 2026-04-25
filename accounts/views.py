import random
from datetime import date
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated # اضافه شد برای باز کردن دسترسی عمومی
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate

from .models import BankCard, User, OTPRequest
from .serializers import (
    BankCardSerializer,
    ChangeMobileConfirmSerializer,
    ChangeMobileRequestSerializer,
    ResetPasswordConfirmSerializer,
    ResetPasswordOTPSerializer,
    SendOTPSerializer, 
    VerifyOTPSerializer, 
    CompleteRegistrationSerializer
)
from .sms_service import send_otp_sms

class RegisterStepOne(APIView):
    """مرحله اول: ارسال کد تایید - دسترسی آزاد"""
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = SendOTPSerializer(data=request.data)
        if serializer.is_valid():
            mobile = serializer.validated_data['mobile']
            
            # تولید کد ۶ رقمی تصادفی
            code = str(random.randint(100000, 999999))
            
            # ارسال پیامک از طریق سرویس
            sms_sent = send_otp_sms(mobile, code)
            
            if sms_sent:
                # ذخیره کد در دیتابیس
                OTPRequest.objects.create(mobile=mobile, code=code)
                return Response({"message": "کد تایید پیامک شد"}, status=status.HTTP_200_OK)
            else:
                return Response({"error": "خطا در سامانه پیامکی. لطفا دوباره تلاش کنید"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RegisterStepTwo(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        mobile = request.data.get('mobile')
        code = request.data.get('code')

        if not mobile or not code:
            return Response({"error": "شماره موبایل و کد الزامی هستند"}, status=400)

        mobile = str(mobile).strip()
        code = str(code).strip()

        # پیدا کردن آخرین کد ساخته شده برای این موبایل
        otp = OTPRequest.objects.filter(
            mobile=mobile, 
            code=code, 
            is_used=False
        ).order_by('-created_at').first()

        if otp:
            if not otp.is_expired():
                otp.is_used = True
                otp.save()
                return Response({
                    "message": "کد تایید شد", 
                    "mobile": mobile
                }, status=200)
            else:
                # برای دیباگ، اینجا چاپ می‌کنیم که چقدر زمان گذشته
                return Response({"error": "کد منقضی شده است. لطفا کد جدید دریافت کنید."}, status=400)
        
        return Response({"error": "کد وارد شده اشتباه است یا قبلاً استفاده شده"}, status=400)


class RegisterStepThree(APIView):
    """مرحله نهایی: دریافت اطلاعات شخصی و ایجاد حساب - دسترسی آزاد"""
    permission_classes = [AllowAny]

    def post(self, request):
        mobile = request.data.get('mobile')
        
        # بررسی تکراری نبودن شماره موبایل
        if User.objects.filter(mobile=mobile).exists():
            return Response({"error": "این شماره موبایل قبلاً ثبت‌نام شده است"}, status=400)

        # بررسی تایید شدن OTP در مرحله قبل
        otp_verified = OTPRequest.objects.filter(mobile=mobile, is_used=True).exists()
        if not otp_verified:
            return Response({"error": "ابتدا باید شماره موبایل خود را تایید کنید"}, status=403)

        serializer = CompleteRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            
            # اعتبارسنجی و تبدیل تاریخ تولد
            try:
                birth_date = date(int(data['birth_year']), int(data['birth_month']), int(data['birth_day']))
            except (ValueError, KeyError):
                return Response({"error": "تاریخ وارد شده معتبر نیست"}, status=400)
            
            # بررسی کد معرف (اختیاری)
            ref_code = data.get('referral_code')
            referred_by = User.objects.filter(referral_code=ref_code).first() if ref_code else None

            # ایجاد کاربر جدید با اطلاعات کامل
            user = User.objects.create(
                mobile=mobile,
                username=mobile,
                first_name=data.get('first_name', ''), 
                last_name=data.get('last_name', ''),   
                national_code=data.get('national_code'),
                card_number=data.get('card_number'),
                birth_date=birth_date,
                referred_by=referred_by,
                auth_status='pending'
            )
            user.set_password(data['password']) # هش کردن رمز عبور
            user.save()
            
            return Response({"message": "حساب کاربری با موفقیت ایجاد شد"}, status=201)
        
        return Response(serializer.errors, status=400)


class LoginWithPassword(APIView):
    """ورود با رمز عبور ثابت - اصلاح شده"""
    permission_classes = [AllowAny]

    def post(self, request):
        mobile = request.data.get('mobile')
        password = request.data.get('password')
        
        if not mobile or not password:
            return Response({"error": "موبایل و رمز عبور را وارد کنید"}, status=400)

        # پیدا کردن یوزر بر اساس موبایل
        user = User.objects.filter(mobile=mobile).first()
        
        # چک کردن وجود یوزر و صحت پسورد (با استفاده از check_password)
        if user and user.check_password(password):
            refresh = RefreshToken.for_user(user)
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'role': user.role,
                'status': user.auth_status,
                'full_name': f"{user.first_name} {user.last_name}"
            })
        
        return Response({"error": "شماره موبایل یا رمز عبور اشتباه است"}, status=status.HTTP_401_UNAUTHORIZED)


class LoginWithOTP(APIView):
    """ورود با شماره موبایل و کد یکبار مصرف (بدون پسورد)"""
    permission_classes = [AllowAny]

    def post(self, request):
        mobile = request.data.get('mobile')
        code = request.data.get('code')
        
        if not mobile or not code:
            return Response({"error": "لطفاً موبایل و کد تایید را وارد کنید"}, status=400)

        # جستجو برای آخرین کد استفاده نشده و معتبر
        otp = OTPRequest.objects.filter(
            mobile=mobile, 
            code=code, 
            is_used=False
        ).order_by('-created_at').first()
        
        if otp and not otp.is_expired():
            # پیدا کردن کاربر متصل به این شماره موبایل
            user = User.objects.filter(mobile=mobile).first()
            
            if user:
                otp.is_used = True
                otp.save()
                
                refresh = RefreshToken.for_user(user)
                return Response({
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                    'role': user.role,
                    'full_name': f"{user.first_name} {user.last_name}"
                })
            else:
                return Response({"error": "کاربری با این شماره یافت نشد. ابتدا ثبت‌نام کنید"}, status=404)
            
        return Response({"error": "کد وارد شده اشتباه یا منقضی شده است"}, status=400)
    


class ResetPasswordRequest(APIView):
    """مرحله اول فراموشی رمز: ارسال کد OTP"""
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ResetPasswordOTPSerializer(data=request.data)
        if serializer.is_valid():
            mobile = serializer.validated_data['mobile']
            
            # بررسی اینکه آیا اصلاً کاربری با این شماره داریم؟
            if not User.objects.filter(mobile=mobile).exists():
                return Response({"error": "کاربری با این شماره یافت نشد"}, status=404)

            code = str(random.randint(100000, 999999))
            
            # استفاده از سرویس پیامک خودت
            sms_sent = send_otp_sms(mobile, code)
            
            if sms_sent:
                OTPRequest.objects.create(mobile=mobile, code=code)
                return Response({"message": "کد بازنشانی رمز عبور ارسال شد"}, status=200)
            return Response({"error": "خطا در ارسال پیامک"}, status=500)
        
        return Response(serializer.errors, status=400)


class ResetPasswordConfirm(APIView):
    """مرحله دوم فراموشی رمز: تایید کد و تغییر پسورد"""
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ResetPasswordConfirmSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            mobile = data['mobile']
            code = data['code']
            new_password = data['new_password']

            # بررسی صحت کد OTP
            otp = OTPRequest.objects.filter(
                mobile=mobile, 
                code=code, 
                is_used=False
            ).order_by('-created_at').first()

            if otp and not otp.is_expired():
                user = User.objects.filter(mobile=mobile).first()
                if user:
                    # تغییر رمز و هش کردن خودکار
                    user.set_password(new_password)
                    user.save()
                    
                    # باطل کردن کد استفاده شده
                    otp.is_used = True
                    otp.save()
                    
                    return Response({"message": "رمز عبور با موفقیت تغییر کرد"}, status=200)
                return Response({"error": "کاربر یافت نشد"}, status=404)
            
            return Response({"error": "کد نامعتبر یا منقضی شده است"}, status=400)
            
        return Response(serializer.errors, status=400)
    

class UserBankCards(APIView):
    permission_classes = [IsAuthenticated] # فقط کاربران لاگین شده

    def get(self, request):
        """لیست کارت‌های بانکی کاربر"""
        cards = BankCard.objects.filter(user=request.user, is_active=True)
        serializer = BankCardSerializer(cards, many=True)
        return Response(serializer.data)

    def post(self, request):
        """ثبت کارت بانکی جدید"""
        serializer = BankCardSerializer(data=request.data)
        if serializer.is_valid():
            # بررسی تعداد کارت‌ها (مثلاً محدودیت ۵ کارت برای هر کاربر)
            if BankCard.objects.filter(user=request.user).count() >= 5:
                return Response({"error": "شما حداکثر می‌توانید ۵ کارت ثبت کنید"}, status=400)
            
            serializer.save(user=request.user)
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)

class DeleteBankCard(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, card_id):
        """غیرفعال کردن (حذف نرم) کارت بانکی"""
        card = BankCard.objects.filter(user=request.user, id=card_id).first()
        if card:
            card.is_active = False # به جای حذف فیزیکی، غیرفعالش می‌کنیم
            card.save()
            return Response({"message": "کارت با موفقیت حذف شد"}, status=200)
        return Response({"error": "کارت یافت نشد"}, status=404)
    

class ChangeMobileRequest(APIView):
    """مرحله اول: ارسال کد تایید به شماره جدید"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangeMobileRequestSerializer(data=request.data)
        if serializer.is_valid():
            new_mobile = serializer.validated_data['new_mobile']

            # بررسی اینکه شماره جدید قبلاً در سیستم نباشد
            if User.objects.filter(mobile=new_mobile).exists():
                return Response({"error": "این شماره موبایل قبلاً توسط کاربر دیگری ثبت شده است"}, status=400)

            code = str(random.randint(100000, 999999))
            
            # ارسال پیامک به شماره جدید
            sms_sent = send_otp_sms(new_mobile, code)
            
            if sms_sent:
                # ذخیره در جدول OTP (می‌توانیم در دیتابیس مشخص کنیم برای چه موبایلی است)
                OTPRequest.objects.create(mobile=new_mobile, code=code)
                return Response({"message": f"کد تایید به شماره {new_mobile} ارسال شد"}, status=200)
            
            return Response({"error": "خطا در ارسال پیامک"}, status=500)
        
        return Response(serializer.errors, status=400)


class ChangeMobileConfirm(APIView):
    """مرحله دوم: تایید کد و جایگزینی شماره موبایل در پروفایل"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangeMobileConfirmSerializer(data=request.data)
        if serializer.is_valid():
            new_mobile = serializer.validated_data['new_mobile']
            code = serializer.validated_data['code']

            # بررسی صحت کد برای شماره جدید
            otp = OTPRequest.objects.filter(
                mobile=new_mobile, 
                code=code, 
                is_used=False
            ).order_by('-created_at').first()

            if otp and not otp.is_expired():
                # تایید شماره جدید و تغییر آن در مدل کاربر
                user = request.user
                user.mobile = new_mobile
                user.username = new_mobile  # چون Username ما همان موبایل است
                user.save()

                # باطل کردن کد
                otp.is_used = True
                otp.save()

                return Response({"message": "شماره موبایل با موفقیت تغییر یافت"}, status=200)
            
            return Response({"error": "کد وارد شده اشتباه یا منقضی شده است"}, status=400)
            
        return Response(serializer.errors, status=400)