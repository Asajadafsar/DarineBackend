# accounts/views.py

import random

from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated

from rest_framework_simplejwt.tokens import RefreshToken

from drf_spectacular.utils import extend_schema

from django.contrib.auth import authenticate
from .sms_service import send_otp_sms, send_login_sms
from admin_panel.utils import create_admin_log
from .models import User, OTPRequest, BankCard

from .serializers import (
    CooperationRequestSerializer,
    RegisterSerializer,
    SendOTPSerializer,
    VerifyOTPSerializer,
    LoginSerializer,
    LoginOTPSerializer,
    ResetPasswordRequestSerializer,
    ResetPasswordVerifySerializer,
    ResetPasswordCompleteSerializer,
    UserProfileSerializer,
    BankCardSerializer,
    ChangeMobileRequestSerializer,
    ChangeMobileConfirmSerializer,
)


from .cookies import set_auth_cookies, clear_auth_cookies

from .utils import success_response, error_response

# # ==========================================
# # REGISTER STEP 1
# # ==========================================

# class RegisterStepOne(APIView):

#     permission_classes = [AllowAny]

#     @extend_schema(request=SendOTPSerializer)
#     def post(self, request):

#         serializer = SendOTPSerializer(data=request.data)

#         if not serializer.is_valid():
#             return error_response("اطلاعات نامعتبر است", serializer.errors)

#         mobile = serializer.validated_data["mobile"]
#         code = str(random.randint(100000, 999999))
#         client_type = request.headers.get("X-Client-Type", "gold")

#         sms_sent = send_otp_sms(mobile, code, client_type)

#         if not sms_sent:
#             return error_response("خطا در ارسال پیامک", status_code=500)

#         # همه OTP های قبلی این موبایل رو غیرفعال کن
#         OTPRequest.objects.filter(mobile=mobile, is_used=False).update(is_used=True)

#         OTPRequest.objects.create(mobile=mobile, code=code)

#         return success_response(message="کد تایید ارسال شد")


# # ==========================================
# # REGISTER STEP 2
# # ==========================================
# # ==========================================
# # REGISTER STEP 2 (اصلاح‌شده و هماهنگ با فرانت)
# # ==========================================

# class RegisterStepTwo(APIView):

#     permission_classes = [AllowAny]

#     def post(self, request):
#         serializer = VerifyOTPSerializer(data=request.data)

#         # مدیریت خطاهای اعتبارسنجی سریالایزر (طول کد، خالی بودن و...)
#         if not serializer.is_valid():
#             error_msg = "اطلاعات نامعتبر است"
#             if "code" in serializer.errors:
#                 error_msg = serializer.errors["code"][0]
#             elif "mobile" in serializer.errors:
#                 error_msg = serializer.errors["mobile"][0]
#             elif "non_field_errors" in serializer.errors:
#                 error_msg = serializer.errors["non_field_errors"][0]

#             return error_response(
#                 message=error_msg,
#                 errors=serializer.errors,
#                 status_code=400
#             )

#         mobile = serializer.validated_data["mobile"]
#         code = serializer.validated_data["code"]

#         # پیدا کردن آخرین کد بدون در نظر گرفتن فیلتر is_used برای فهمیدن اشتباه بودن
#         otp = OTPRequest.objects.filter(
#             mobile=mobile,
#             code=code
#         ).last()

#         if not otp or otp.is_used:
#             return error_response(message="کد تایید وارد شده اشتباه است", status_code=400)

#         if otp.is_expired():
#             return error_response(message="کد تایید منقضی شده است. لطفا مجدداً درخواست کنید", status_code=400)

#         # تایید موفقیت‌آمیز کد
#         otp.is_used = True
#         otp.save()

#         return success_response(message="کد با موفقیت تایید شد")


# # ==========================================
# # REGISTER STEP 3
# # ==========================================

# class RegisterStepThree(APIView):

#     permission_classes = [AllowAny]

#     def post(self, request):

#         serializer = RegisterSerializer(data=request.data)

#         if not serializer.is_valid():
#             return error_response("اطلاعات نامعتبر است", serializer.errors)

#         data = serializer.validated_data
#         mobile = data["mobile"]
#         first_name = data["first_name"]
#         last_name = data["last_name"]
#         national_code = data["national_code"]
#         password = data["password"]
#         birth_date_input = data["birth_date"]
#         referral_code = data.get("referral_code", "")

#         # ۱. بررسی تکراری نبودن شماره موبایل
#         if User.objects.filter(mobile=mobile).exists():
#             return error_response("این شماره قبلا ثبت شده است")

#         # ۲. بررسی تکراری نبودن کد ملی
#         if User.objects.filter(national_code=national_code).exists():
#             return error_response("این کد ملی قبلا ثبت شده است")

#         # ۳. چک کردن وجود تاییدیه OTP (بدون وابستگی به آخرین رکورد یا زمان)
#         # فقط بررسی میکنیم که آیا این موبایل اصلاً مرحله دو را با موفقیت رد کرده است یا خیر
#         has_verified_otp = OTPRequest.objects.filter(
#             mobile=mobile,
#             is_used=True
#         ).exists()

#         if not has_verified_otp:
#             return error_response(
#                 "ابتدا شماره موبایل را تایید کنید",
#                 status_code=403
#             )

#         # ۴. تبدیل تاریخ تولد شمسی/میلادی به گریگوریان
#         birth_date_gregorian = None
#         try:
#             if "/" in birth_date_input:
#                 y, m, d = map(int, birth_date_input.split("/"))
#                 birth_date_gregorian = jdatetime.date(y, m, d).togregorian()
#             else:
#                 birth_date_gregorian = datetime.strptime(birth_date_input, "%Y-%m-%d").date()
#         except Exception:
#             return error_response("فرمت تاریخ نامعتبر است")

#         today = timezone.now().date()
#         age = (
#             today.year
#             - birth_date_gregorian.year
#             - (
#                 (today.month, today.day)
#                 <
#                 (
#                     birth_date_gregorian.month,
#                     birth_date_gregorian.day
#                 )
#             )
#         )
#         if age < 18:
#             return error_response(
#                 message="برای استفاده از خدمات سامانه، باید حداقل ۱۸ سال سن داشته باشید.",
#                 errors={
#                     "birth_date": [
#                         "کاربران زیر ۱۸ سال امکان ثبت‌نام در سامانه را ندارند."
#                     ]
#                 },
#                 status_code=400
#             )

#         # ۵. فرآیند ساخت کاربر و لاگ سیستم
#         try:
#             # بررسی کد معرف
#             referred_by = None
#             if referral_code:
#                 referred_by = User.objects.filter(referral_code=referral_code).first()

#             # ایجاد رکورد کاربر جدید
#             user = User.objects.create(
#                 mobile=mobile,
#                 username=mobile,
#                 first_name=first_name,
#                 last_name=last_name,
#                 national_code=national_code,
#                 birth_date=birth_date_gregorian,
#                 role="customer",
#                 auth_status="pending",
#                 referred_by=referred_by
#             )

#             user.set_password(password)
#             user.save()

#             # مصرف کردن یا پاک کردن تمام OTPهای این موبایل بعد از ثبت نام موفق برای امنیت بیشتر
#             OTPRequest.objects.filter(mobile=mobile).delete()

#             # ثبت لاگ در پنل ادمین
#             create_admin_log(
#                 request=request,
#                 admin=None,
#                 user=user,
#                 action_type="USER_REGISTER",
#                 action="ثبت نام کاربر",
#                 model_name="User",
#                 object_id=user.id,
#                 description=f"کاربر جدید {user.mobile} ثبت نام کرد"
#             )

#             # صدور توکن‌های JWT
#             refresh = RefreshToken.for_user(user)
#             access = refresh.access_token

#             response = success_response(
#                 message="ثبت نام با موفقیت انجام شد",
#                 data={
#                     "user": {
#                         "id": user.id,
#                         "full_name": f"{user.first_name} {user.last_name}",
#                         "role": user.role,
#                         "status": user.auth_status
#                     }
#                 },
#                 status_code=201
#             )

#             # ست کردن کوکی‌های امنیتی احراز هویت
#             set_auth_cookies(response, str(access), str(refresh))

#             return response

#         except Exception as e:
#             return error_response(str(e))


# ==========================================
# REGISTER STEP 1
# ==========================================


class RegisterStepOne(APIView):

    permission_classes = [AllowAny]

    @extend_schema(request=SendOTPSerializer)
    def post(self, request):

        serializer = SendOTPSerializer(data=request.data)

        if not serializer.is_valid():

            response = error_response("اطلاعات نامعتبر است", serializer.errors)

            create_admin_log(
                request=request,
                action_type="REGISTER_ERROR",
                action="خطا در ارسال OTP ثبت نام",
                model_name="OTPRequest",
                success=False,
                response_status=response.status_code,
                error_message=str(serializer.errors),
            )

            return response

        mobile = serializer.validated_data["mobile"]

        code = str(random.randint(100000, 999999))

        client_type = request.headers.get("X-Client-Type", "gold")

        sms_sent = send_otp_sms(mobile, code, client_type)

        if not sms_sent:

            response = error_response("خطا در ارسال پیامک", status_code=500)

            create_admin_log(
                request=request,
                action_type="REGISTER_ERROR",
                action="خطا در ارسال پیامک OTP",
                model_name="OTPRequest",
                success=False,
                response_status=response.status_code,
                description=f"mobile={mobile}",
            )

            return response

        OTPRequest.objects.filter(mobile=mobile, is_used=False).update(is_used=True)

        otp = OTPRequest.objects.create(mobile=mobile, code=code)

        create_admin_log(
            request=request,
            action_type="REGISTER",
            action="درخواست ثبت نام",
            model_name="OTPRequest",
            object_id=otp.id,
            user=None,
            success=True,
            description=f"""
ارسال کد تایید ثبت نام

موبایل:
{mobile}
""",
        )

        return success_response(message="کد تایید ارسال شد")


# ==========================================
# REGISTER STEP 2 (اصلاح‌شده و هماهنگ با فرانت)
# ==========================================


class RegisterStepTwo(APIView):

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)

        # مدیریت خطاهای اعتبارسنجی سریالایزر (طول کد، خالی بودن و...)
        if not serializer.is_valid():
            error_msg = "اطلاعات نامعتبر است"
            if "code" in serializer.errors:
                error_msg = serializer.errors["code"][0]
            elif "mobile" in serializer.errors:
                error_msg = serializer.errors["mobile"][0]
            elif "non_field_errors" in serializer.errors:
                error_msg = serializer.errors["non_field_errors"][0]

            return error_response(
                message=error_msg, errors=serializer.errors, status_code=400
            )

        mobile = serializer.validated_data["mobile"]
        code = serializer.validated_data["code"]

        # پیدا کردن آخرین کد بدون در نظر گرفتن فیلتر is_used برای فهمیدن اشتباه بودن
        otp = OTPRequest.objects.filter(mobile=mobile, code=code).last()

        if not otp or otp.is_used:
            return error_response(
                message="کد تایید وارد شده اشتباه است", status_code=400
            )

        if otp.is_expired():
            return error_response(
                message="کد تایید منقضی شده است. لطفا مجدداً درخواست کنید",
                status_code=400,
            )

        # تایید موفقیت‌آمیز کد
        otp.is_used = True
        otp.save()

        return success_response(message="کد با موفقیت تایید شد")


# ==========================================
# REGISTER STEP 3
# ==========================================

# class RegisterStepThree(APIView):

#     permission_classes = [AllowAny]

#     def post(self, request):

#         serializer = RegisterSerializer(data=request.data)

#         if not serializer.is_valid():

#             response = error_response("اطلاعات نامعتبر است", serializer.errors)

#             create_admin_log(
#                 request=request,
#                 action_type="REGISTER_ERROR",
#                 action="خطا در ثبت نام",
#                 model_name="User",
#                 success=False,
#                 response_status=response.status_code,
#                 error_message=str(serializer.errors),
#             )

#             return response

#         data = serializer.validated_data

#         mobile = data["mobile"]
#         referral_code = data.get("referral_code")  # ✅ دریافت کد معرف

#         user = User.objects.create(
#             mobile=mobile,
#             username=mobile,
#             first_name=data["first_name"],
#             last_name=data["last_name"],
#             national_code=data["national_code"],
#             birth_date=data["birth_date"],
#             role="customer",
#             auth_status="pending",
#         )

#         user.set_password(data["password"])

#         # ✅ تنظیم کاربر معرف (referred_by) اگر کد معرف وجود داشته باشد
#         if referral_code:
#             try:
#                 referrer = User.objects.get(referral_code=referral_code)
#                 user.referred_by = referrer
#                 user.save()
#             except User.DoesNotExist:
#                 # کد معرف نامعتبر - فقط لاگ می‌کنیم و ادامه می‌دیم
#                 create_admin_log(
#                     request=request,
#                     user=user,
#                     action_type="INVALID_REFERRAL",
#                     action="کد معرف نامعتبر",
#                     model_name="User",
#                     object_id=user.id,
#                     success=False,
#                     description=f"""
# کد معرف نامعتبر در ثبت نام

# موبایل کاربر: {mobile}
# کد معرف وارد شده: {referral_code}
# """,
#                 )

#         # ✅ ذخیره نهایی کاربر
#         user.save()

#         create_admin_log(
#             request=request,
#             user=user,
#             action_type="USER_REGISTER",
#             action="ثبت نام کاربر",
#             model_name="User",
#             object_id=user.id,
#             success=True,
#             description=f"""
# کاربر جدید ایجاد شد

# موبایل:
# {user.mobile}

# نام:
# {user.first_name} {user.last_name}

# معرف:
# {user.referred_by.mobile if user.referred_by else 'ندارد'}
# """,
#         )

#         refresh = RefreshToken.for_user(user)

#         access = refresh.access_token

#         response = success_response(
#             message="ثبت نام موفق",
#             status_code=201,
#             data={
#                 "user": {
#                     "id": user.id,
#                     "mobile": user.mobile,
#                     "referred_by": user.referred_by.mobile if user.referred_by else None,
#                 }
#             },
#         )

#         set_auth_cookies(response, str(access), str(refresh))

#         return response


# accounts/views.py
import random
from datetime import datetime
from django.utils import timezone
import jdatetime
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from drf_spectacular.utils import extend_schema
from django.contrib.auth import authenticate

from .serializers import (
    RegisterSerializer,
    SendOTPSerializer,
    VerifyOTPSerializer,
    LoginSerializer,
    LoginOTPSerializer,
    ResetPasswordRequestSerializer,
    ResetPasswordVerifySerializer,
    ResetPasswordCompleteSerializer,
    UserProfileSerializer,
    BankCardSerializer,
    ChangeMobileRequestSerializer,
    ChangeMobileConfirmSerializer,
    CooperationRequestSerializer,
)
from .models import User, OTPRequest, BankCard
from .sms_service import send_otp_sms, send_login_sms
from .cookies import set_auth_cookies, clear_auth_cookies
from .utils import success_response, error_response
from admin_panel.utils import create_admin_log
from .jibit import shahkar_match  # ✅ اضافه کردن ایمپورت

# accounts/views.py - بخش RegisterStepThree (اصلاح شده)

# ==========================================
# REGISTER STEP 3 (با احراز هویت Jibit)
# ==========================================

# accounts/views.py - RegisterStepThree (نسخه نهایی)

# ==========================================
# REGISTER STEP 3 (با احراز هویت Jibit)
# ==========================================

class RegisterStepThree(APIView):

    permission_classes = [AllowAny]

    def post(self, request):

        serializer = RegisterSerializer(data=request.data)

        # =============================================
        # ۱. اعتبارسنجی سریالایزر
        # =============================================
        if not serializer.is_valid():
            # خطاهای اعتبارسنجی را به صورت دقیق برگردان
            errors = serializer.errors
            
            # استخراج پیام‌های خطا
            error_messages = []
            for field, field_errors in errors.items():
                for error in field_errors:
                    error_messages.append(f"{error}")
            
            return error_response(
                message=" | ".join(error_messages),  # همه خطاها را با | جدا کن
                errors=errors,
                status_code=400
            )

        data = serializer.validated_data

        mobile = data["mobile"]
        national_code = data["national_code"]
        first_name = data["first_name"]
        last_name = data["last_name"]
        password = data["password"]
        birth_date_input = data["birth_date"]
        referral_code = data.get("referral_code")

        # =============================================
        # ۲. بررسی تکراری بودن کد ملی
        # =============================================
        if User.objects.filter(national_code=national_code).exists():
            create_admin_log(
                request=request,
                action_type="REGISTER_ERROR",
                action="کد ملی تکراری",
                model_name="User",
                success=False,
                description=f"""
کد ملی تکراری در ثبت نام

کد ملی: {national_code}
شماره موبایل: {mobile}
"""
            )
            return error_response("مالکیت کد ملی و شماره موبایل وارد شده مطابقت ندارد")

        # =============================================
        # ۳. بررسی تکراری بودن شماره موبایل
        # =============================================
        if User.objects.filter(mobile=mobile).exists():
            return error_response("این شماره قبلاً ثبت شده است")

        # =============================================
        # ۴. چک کردن وجود تاییدیه OTP
        # =============================================
        has_verified_otp = OTPRequest.objects.filter(
            mobile=mobile,
            is_used=True
        ).exists()

        if not has_verified_otp:
            return error_response(
                "ابتدا شماره موبایل را تایید کنید",
                status_code=403
            )

        # =============================================
        # ۵. احراز هویت با Jibit (Shahkar Match)
        # =============================================
        try:
            is_matched = shahkar_match(national_code, mobile)
            
            if not is_matched:
                # این حالت دیگر رخ نمی‌دهد چون تابع خطا raise می‌کند
                pass

        except Exception as e:
            error_message = str(e)
            
            # =============================================
            # تشخیص نوع خطا بر اساس پیام
            # =============================================
            
            # ۱. کد ملی در ثبت احوال وجود ندارد
            if "در ثبت احوال موجود نیست" in error_message:
                create_admin_log(
                    request=request,
                    action_type="REGISTER_ERROR",
                    action="کد ملی در ثبت احوال موجود نیست",
                    model_name="User",
                    success=False,
                    description=f"""
کد ملی در ثبت احوال موجود نیست

کد ملی: {national_code}
شماره موبایل: {mobile}
"""
                )
                return error_response(
                    "کد ملی وارد شده در ثبت احوال موجود نیست",
                    status_code=400
                )
            
            # ۲. عدم تطابق کد ملی و شماره موبایل
            elif "مالکیت" in error_message and "مطابقت ندارد" in error_message:
                create_admin_log(
                    request=request,
                    action_type="REGISTER_ERROR",
                    action="عدم تطابق کد ملی و شماره موبایل",
                    model_name="User",
                    success=False,
                    description=f"""
عدم تطابق کد ملی و شماره موبایل

کد ملی: {national_code}
شماره موبایل: {mobile}
"""
                )
                return error_response(
                    "مالکیت کد ملی و شماره موبایل وارد شده مطابقت ندارد",
                    status_code=400
                )
            
            # ۳. شماره موبایل نامعتبر
            elif "شماره موبایل" in error_message and "نامعتبر" in error_message:
                create_admin_log(
                    request=request,
                    action_type="REGISTER_ERROR",
                    action="شماره موبایل نامعتبر",
                    model_name="User",
                    success=False,
                    description=f"""
شماره موبایل نامعتبر

کد ملی: {national_code}
شماره موبایل: {mobile}
"""
                )
                return error_response(
                    "شماره موبایل وارد شده نامعتبر است",
                    status_code=400
                )
            
            # ۴. سایر خطاها (ارتباط با سرویس و ...)
            else:
                create_admin_log(
                    request=request,
                    action_type="REGISTER_ERROR",
                    action="خطا در سرویس احراز هویت Jibit",
                    model_name="User",
                    success=False,
                    error_message=str(e),
                    description=f"""
خطا در ارتباط با Jibit

کد ملی: {national_code}
شماره موبایل: {mobile}
خطا: {str(e)}
"""
                )
                return error_response(
                    "خطا در سرویس احراز هویت. لطفاً مجدداً تلاش کنید",
                    status_code=503
                )

        # =============================================
        # ۶. تبدیل تاریخ تولد
        # =============================================
        birth_date_gregorian = None
        try:
            if "/" in birth_date_input:
                y, m, d = map(int, birth_date_input.split("/"))
                birth_date_gregorian = jdatetime.date(y, m, d).togregorian()
            else:
                birth_date_gregorian = datetime.strptime(birth_date_input, "%Y-%m-%d").date()
        except Exception:
            return error_response("فرمت تاریخ نامعتبر است")

        # =============================================
        # ۷. بررسی سن (حداقل ۱۸ سال)
        # =============================================
        today = timezone.now().date()
        age = (
            today.year
            - birth_date_gregorian.year
            - (
                (today.month, today.day)
                <
                (
                    birth_date_gregorian.month,
                    birth_date_gregorian.day
                )
            )
        )
        if age < 18:
            return error_response(
                message="برای استفاده از خدمات سامانه، باید حداقل ۱۸ سال سن داشته باشید.",
                errors={
                    "birth_date": [
                        "کاربران زیر ۱۸ سال امکان ثبت‌نام در سامانه را ندارند."
                    ]
                },
                status_code=400
            )

        # =============================================
        # ۸. ساخت کاربر
        # =============================================
        try:
            # بررسی کد معرف
            referred_by = None
            if referral_code:
                try:
                    referred_by = User.objects.get(referral_code=referral_code)
                except User.DoesNotExist:
                    create_admin_log(
                        request=request,
                        action_type="INVALID_REFERRAL",
                        action="کد معرف نامعتبر",
                        model_name="User",
                        success=False,
                        description=f"""
کد معرف نامعتبر در ثبت نام

موبایل کاربر: {mobile}
کد معرف وارد شده: {referral_code}
"""
                    )

            # ایجاد کاربر
            user = User.objects.create(
                mobile=mobile,
                username=mobile,
                first_name=first_name,
                last_name=last_name,
                national_code=national_code,
                birth_date=birth_date_gregorian,
                role="customer",
                auth_status="verified",
                referred_by=referred_by
            )

            user.set_password(password)
            user.save()

            # پاک کردن OTPهای استفاده شده
            OTPRequest.objects.filter(mobile=mobile).delete()

            # ثبت لاگ موفق
            create_admin_log(
                request=request,
                user=user,
                action_type="USER_REGISTER",
                action="ثبت نام کاربر با احراز هویت Jibit",
                model_name="User",
                object_id=user.id,
                success=True,
                description=f"""
کاربر جدید ایجاد شد

موبایل: {user.mobile}
نام: {user.first_name} {user.last_name}
کد ملی: {user.national_code}
وضعیت احراز: تایید شده (Jibit)
معرف: {user.referred_by.mobile if user.referred_by else 'ندارد'}
"""
            )

            # صدور توکن
            refresh = RefreshToken.for_user(user)
            access = refresh.access_token

            response = success_response(
                message="ثبت نام با موفقیت انجام شد",
                status_code=201,
                data={
                    "user": {
                        "id": user.id,
                        "mobile": user.mobile,
                        "full_name": f"{user.first_name} {user.last_name}",
                        "role": user.role,
                        "auth_status": user.auth_status,
                        "referred_by": user.referred_by.mobile if user.referred_by else None,
                    }
                },
            )

            set_auth_cookies(response, str(access), str(refresh))
            return response

        except Exception as e:
            return error_response(str(e))
# ==========================================
# LOGIN PASSWORD
# ==========================================


class LoginWithPassword(APIView):

    permission_classes = [AllowAny]

    @extend_schema(request=LoginSerializer)
    def post(self, request):

        serializer = LoginSerializer(data=request.data)

        if not serializer.is_valid():

            response = error_response("اطلاعات نامعتبر", serializer.errors)

            create_admin_log(
                request=request,
                action_type="LOGIN_FAILED",
                action="خطا در اعتبارسنجی ورود",
                model_name="User",
                response_status=400,
                success=False,
                description=str(serializer.errors),
            )

            return response

        mobile = serializer.validated_data["mobile"]

        password = serializer.validated_data["password"]

        user = authenticate(request, mobile=mobile, password=password)

        if not user:

            response = error_response(
                "شماره موبایل یا رمز عبور اشتباه است", status_code=401
            )

            create_admin_log(
                request=request,
                action_type="LOGIN_FAILED",
                action="ورود ناموفق با رمز عبور",
                model_name="User",
                response_status=401,
                success=False,
                description=f"""
شماره موبایل:
{mobile}
""",
            )

            return response

        send_login_sms(user.mobile)

        refresh = RefreshToken.for_user(user)

        access = refresh.access_token

        response = success_response(
            message="ورود موفق",
            data={
                "user": {
                    "id": user.id,
                    "full_name": f"{user.first_name} {user.last_name}",
                    "role": user.role,
                    "status": user.auth_status,
                }
            },
        )

        create_admin_log(
            request=request,
            user=user,
            action_type="LOGIN_SUCCESS",
            action="ورود موفق با رمز عبور",
            model_name="User",
            object_id=user.id,
            response_status=200,
            success=True,
            description=f"""
کاربر:
{user.mobile}

روش ورود:
Password
""",
        )

        set_auth_cookies(response, str(access), str(refresh))

        return response


# ==========================================
# LOGIN OTP
# ==========================================


class LoginWithOTP(APIView):

    permission_classes = [AllowAny]

    @extend_schema(request=LoginOTPSerializer)
    def post(self, request):

        serializer = LoginOTPSerializer(data=request.data)

        if not serializer.is_valid():

            response = error_response("اطلاعات نامعتبر", serializer.errors)

            create_admin_log(
                request=request,
                action_type="LOGIN_OTP_FAILED",
                action="خطا در اعتبارسنجی OTP",
                model_name="OTPRequest",
                response_status=400,
                success=False,
                description=str(serializer.errors),
            )

            return response

        mobile = serializer.validated_data["mobile"]

        code = serializer.validated_data["code"]

        otp = OTPRequest.objects.filter(mobile=mobile, code=code, is_used=False).last()

        if not otp:

            response = error_response("کد اشتباه است")

            create_admin_log(
                request=request,
                action_type="LOGIN_OTP_FAILED",
                action="OTP اشتباه",
                model_name="OTPRequest",
                response_status=400,
                success=False,
                description=f"mobile={mobile}",
            )

            return response

        if otp.is_expired():

            response = error_response("کد منقضی شده")

            create_admin_log(
                request=request,
                action_type="LOGIN_OTP_FAILED",
                action="OTP منقضی شده",
                model_name="OTPRequest",
                response_status=400,
                success=False,
                description=f"mobile={mobile}",
            )

            return response

        user = User.objects.filter(mobile=mobile).first()

        if not user:

            response = error_response(
                {
                    "success": False,
                    "message": "شماره موبایل ثبت نشده است، لطفا ثبت نام کنید",
                    "need_register": True,
                    "mobile": mobile,
                },
                status_code=404,
            )

            create_admin_log(
                request=request,
                action_type="LOGIN_FAILED",
                action="ورود با OTP بدون کاربر",
                model_name="User",
                response_status=404,
                success=False,
                description=f"mobile={mobile}",
            )

            return response

        otp.is_used = True
        otp.save()

        send_login_sms(user.mobile)

        refresh = RefreshToken.for_user(user)

        access = refresh.access_token

        response = success_response(
            message="ورود موفق",
            data={
                "user": {
                    "id": user.id,
                    "full_name": f"{user.first_name} {user.last_name}",
                    "role": user.role,
                    "status": user.auth_status,
                }
            },
        )

        create_admin_log(
            request=request,
            user=user,
            action_type="LOGIN_SUCCESS",
            action="ورود موفق با OTP",
            model_name="User",
            object_id=user.id,
            response_status=200,
            success=True,
            description=f"""
کاربر:
{user.mobile}

روش ورود:
OTP
""",
        )

        set_auth_cookies(response, str(access), str(refresh))

        return response


# ==========================================
# REFRESH TOKEN
# ==========================================




class RefreshTokenView(APIView):

    permission_classes = [AllowAny]

    def post(self, request):

        refresh_token = request.COOKIES.get("refreshToken")

        if not refresh_token:
            return error_response("رفرش توکن یافت نشد", status_code=401)

        try:

            refresh = RefreshToken(refresh_token)

            access_token = str(refresh.access_token)

            response = success_response(message="توکن بروزرسانی شد")

            set_auth_cookies(
                response=response,
                access_token=access_token,
                refresh_token=refresh_token,
            )

            return response

        except Exception:

            response = error_response("رفرش توکن نامعتبر است", status_code=401)

            clear_auth_cookies(response)

            return response


from django.contrib.auth import logout as django_logout

# ==========================================
# LOGOUT
# ==========================================


class LogoutView(APIView):

    permission_classes = [AllowAny]

    def post(self, request):

        refresh_token = request.COOKIES.get("refreshToken")

        response = success_response(message="خروج موفق")

        if refresh_token:
            try:
                RefreshToken(refresh_token).blacklist()
            except Exception:
                pass

        django_logout(request)

        clear_auth_cookies(response)

        if request.user.is_authenticated:
            try:
                create_admin_log(
                    request=request,
                    user=request.user,
                    action_type="LOGOUT",
                    action="خروج کاربر",
                    model_name="User",
                    object_id=request.user.id,
                    response_status=200,
                    success=True,
                )
            except Exception:
                pass

        return response


# ==========================================
# PROFILE
# ==========================================


class ProfileView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        serializer = UserProfileSerializer(request.user)

        return success_response(message="اطلاعات پروفایل", data=serializer.data)


# ==========================================
# BANK CARDS
# ==========================================


# class UserBankCards(APIView):

#     permission_classes = [IsAuthenticated]

#     def get(self, request):

#         cards = BankCard.objects.filter(user=request.user, is_active=True)

#         serializer = BankCardSerializer(cards, many=True)

#         return success_response(message="لیست کارت‌ها", data=serializer.data)

#     def post(self, request):

#         active_cards_count = BankCard.objects.filter(
#             user=request.user, is_active=True
#         ).count()

#         serializer = BankCardSerializer(data=request.data)

#         if not serializer.is_valid():

#             return error_response("اطلاعات کارت نامعتبر است", serializer.errors)

#         serializer.save(user=request.user)

#         return success_response(
#             message="کارت ثبت شد", data=serializer.data, status_code=201
#         )



# accounts/views.py - جایگزین کنید

from .jibit import iban_matching, get_iban_info
from .serializers import VerifyIBANSerializer


# accounts/views.py


from .jibit import get_full_iban_info
from .serializers import VerifyIBANSerializer

# accounts/views.py - بخش UserBankCards (اصلاح شده)

class UserBankCards(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):
        cards = BankCard.objects.filter(user=request.user, is_active=True)
        serializer = BankCardSerializer(cards, many=True)
        return success_response(message="لیست کارت‌ها", data=serializer.data)

    def post(self, request):
        """
        ثبت شماره شبا با استعلام اطلاعات (بدون احراز هویت)
        """
        user = request.user
        
        print("=" * 60)
        print("🔄 IBAN INQUIRY (Without Verification)")
        print(f"   User ID: {user.id}")
        print(f"   Mobile: {user.mobile}")
        print("=" * 60)
        
        # =============================================
        # ۱. اعتبارسنجی ورودی
        # =============================================
        from .serializers import VerifyIBANSerializer
        
        serializer = VerifyIBANSerializer(data=request.data)
        if not serializer.is_valid():
            print(f"❌ Serializer errors: {serializer.errors}")
            return error_response("اطلاعات نامعتبر است", serializer.errors)
        
        iban = serializer.validated_data["shaba_number"]  # این شامل IR هست
        print(f"✅ IBAN validated: {iban}")
        
        # =============================================
        # ۲. بررسی تکراری بودن شبا برای همین کاربر (نه همه کاربران)
        # =============================================
        shaba_for_db = iban
        if shaba_for_db.startswith("IR"):
            shaba_for_db = shaba_for_db[2:]  # حذف IR برای ذخیره
        
        # ✅ فقط برای کاربر فعلی بررسی می‌شود
        if BankCard.objects.filter(
            user=user,  # فقط کاربر فعلی
            shaba_number=shaba_for_db, 
            is_active=True
        ).exists():
            print(f"❌ IBAN already exists for this user: {shaba_for_db}")
            return error_response("شما قبلاً این شماره شبا را ثبت کرده‌اید")
        
        # =============================================
        # ۳. استعلام اطلاعات شبا از Jibit
        # =============================================
        try:
            from .jibit import get_full_iban_info
            
            print("🔄 Calling get_full_iban_info...")
            iban_info = get_full_iban_info(iban)
            
            print(f"📊 IBAN Info Result:")
            print(f"   Bank: {iban_info['bank']}")
            print(f"   Deposit Number: {iban_info['deposit_number']}")
            print(f"   Status: {iban_info['status']}")
            print(f"   Owner: {iban_info['owner_full_name']}")
            
            # =============================================
            # ۴. ذخیره اطلاعات شبا
            # =============================================
            bank_card = BankCard.objects.create(
                user=user,
                shaba_number=shaba_for_db,  # بدون IR ذخیره می‌شود
                bank_name=iban_info.get("bank", ""),
                card_number="",
                is_active=True,
            )
            
            print(f"✅ BankCard created: {bank_card.id}")
            
            # =============================================
            # ۵. ثبت لاگ موفق
            # =============================================
            from admin_panel.utils import create_admin_log
            
            create_admin_log(
                request=request,
                user=user,
                action_type="IBAN_ADDED",
                action="ثبت شماره شبا جدید",
                model_name="BankCard",
                object_id=bank_card.id,
                success=True,
                description=f"""
ثبت شماره شبا جدید

کاربر: {user.mobile}
شماره شبا: {iban}
بانک: {iban_info.get('bank', '')}
شماره حساب: {iban_info.get('deposit_number', '')}
وضعیت: {iban_info.get('status', '')}
صاحب حساب: {iban_info.get('owner_full_name', '')}
"""
            )
            
            # =============================================
            # ۶. پاسخ موفق
            # =============================================
            print("✅ IBAN added successfully")
            print("=" * 60)
            
            return success_response(
                message="شماره شبا با موفقیت ثبت شد",
                status_code=201,
                data={
                    "id": bank_card.id,
                    "shaba_number": shaba_for_db,
                    "bank": iban_info.get("bank", ""),
                    "deposit_number": iban_info.get("deposit_number", ""),
                    "status": iban_info.get("status", ""),
                    "owner_full_name": iban_info.get("owner_full_name", ""),
                    "owners": iban_info.get("owners", []),
                    "is_active": True,
                }
            )
            
        except Exception as e:
            print(f"❌ Exception: {str(e)}")
            print("=" * 60)
            
            error_message = str(e)
            
            if "شبا نامعتبر" in error_message or "iban" in error_message.lower():
                return error_response(
                    "شماره شبا نامعتبر است. لطفاً شماره شبا را بررسی کنید",
                    status_code=400
                )
            elif "not found" in error_message.lower():
                return error_response(
                    "شماره شبا یافت نشد. لطفاً شماره شبا را بررسی کنید",
                    status_code=404
                )
            else:
                from admin_panel.utils import create_admin_log
                
                create_admin_log(
                    request=request,
                    user=user,
                    action_type="IBAN_ADD_ERROR",
                    action="خطا در ثبت شماره شبا",
                    model_name="User",
                    object_id=user.id,
                    success=False,
                    error_message=str(e),
                    description=f"""
خطا در ثبت شماره شبا

کاربر: {user.mobile}
شماره شبا: {iban}
خطا: {str(e)}
"""
                )
                return error_response(
                    f"خطا در استعلام اطلاعات شبا: {error_message}",
                    status_code=503
                )


# ==========================================
# DELETE CARD
# ==========================================


class DeleteBankCard(APIView):

    permission_classes = [IsAuthenticated]

    def delete(self, request, card_id):

        card = BankCard.objects.filter(
            id=card_id, user=request.user, is_active=True
        ).first()

        if not card:

            return error_response("کارت یافت نشد", status_code=404)

        card.is_active = False
        card.save()

        return success_response(message="کارت حذف شد")


# ==========================================
# RESET PASSWORD REQUEST
# ==========================================


class ResetPasswordRequest(APIView):

    permission_classes = [AllowAny]

    @extend_schema(request=ResetPasswordRequestSerializer)
    def post(self, request):

        serializer = ResetPasswordRequestSerializer(data=request.data)

        if not serializer.is_valid():

            response = error_response("اطلاعات نامعتبر", serializer.errors)

            create_admin_log(
                request=request,
                action_type="PASSWORD_RESET_FAILED",
                action="خطا در درخواست بازیابی رمز",
                model_name="User",
                response_status=400,
                success=False,
                description=str(serializer.errors),
            )

            return response

        mobile = serializer.validated_data["mobile"]

        user = User.objects.filter(mobile=mobile).first()

        if not user:

            response = error_response("کاربر یافت نشد", status_code=404)

            create_admin_log(
                request=request,
                action_type="PASSWORD_RESET_FAILED",
                action="بازیابی رمز برای کاربر ناموجود",
                model_name="User",
                response_status=404,
                success=False,
                description=f"mobile={mobile}",
            )

            return response

        code = str(random.randint(100000, 999999))

        client_type = request.headers.get("X-Client-Type", "gold")

        sms_sent = send_otp_sms(mobile, code, client_type)

        if not sms_sent:

            response = error_response("خطا در ارسال پیامک", status_code=500)

            create_admin_log(
                request=request,
                user=user,
                action_type="PASSWORD_RESET_FAILED",
                action="خطا در ارسال OTP بازیابی",
                model_name="OTPRequest",
                response_status=500,
                success=False,
                description=f"mobile={mobile}",
            )

            return response

        OTPRequest.objects.create(mobile=mobile, code=code)

        create_admin_log(
            request=request,
            user=user,
            action_type="PASSWORD_RESET_REQUEST",
            action="درخواست بازیابی رمز عبور",
            model_name="OTPRequest",
            response_status=200,
            success=True,
            description=f"OTP ارسال شد برای {mobile}",
        )

        return success_response(message="کد بازیابی ارسال شد")


from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from gold_app.utils import get_live_gold_price, get_latest_price, PRICE_URLS

from silver_app.utils import get_live_silver_price

# =========================================================
# MARKET PRICES
# =========================================================


class MarketPricesAPIView(APIView):

    permission_classes = [AllowAny]

    TITLES = {
        "gold": "طلای ۱۸ عیار",
        "silver": "نقره",
        "geram18": "گرم ۱۸",
        "geram24": "گرم ۲۴",
        "gerami": "سکه گرمی",
        "rob": "ربع سکه",
        "nim": "نیم سکه",
        "sekeb": "سکه بهار آزادی",
        "sekee": "سکه امامی",
        "ons": "انس جهانی",
    }

    def get(self, request):

        prices = []

        # =====================================================
        # GOLD
        # =====================================================

        gold_data = get_latest_price("geram18") or {}

        prices.append(
            {
                "type": "gold",
                "title": self.TITLES["gold"],
                "price": int(get_live_gold_price() or 0),
                "change_amount": float(gold_data.get("dayChange") or 0),
                "change_percent": float(gold_data.get("percentChange") or 0),
            }
        )

        # =====================================================
        # SILVER
        # =====================================================

        silver_data = get_latest_price("silver") or {}

        prices.append(
            {
                "type": "silver",
                "title": self.TITLES["silver"],
                "price": int(get_live_silver_price() or 0),
                "change_amount": float(silver_data.get("dayChange") or 0),
                "change_percent": float(silver_data.get("percentChange") or 0),
            }
        )

        # =====================================================
        # OTHER MARKET PRICES
        # =====================================================

        for key in PRICE_URLS.keys():

            data = get_latest_price(key)

            if not data:
                continue

            prices.append(
                {
                    "type": key,
                    "title": self.TITLES.get(key, key),
                    "price": int(data.get("currentRate") or 0),
                    "change_amount": float(data.get("dayChange") or 0),
                    "change_percent": float(data.get("percentChange") or 0),
                }
            )

        return Response({"prices": prices})


# ==========================================
# RESET PASSWORD VERIFY
# ==========================================


class ResetPasswordVerify(APIView):

    permission_classes = [AllowAny]

    @extend_schema(request=ResetPasswordVerifySerializer)
    def post(self, request):

        serializer = ResetPasswordVerifySerializer(data=request.data)

        if not serializer.is_valid():

            return error_response("اطلاعات نامعتبر", serializer.errors)

        mobile = serializer.validated_data["mobile"]

        code = serializer.validated_data["code"]

        otp = OTPRequest.objects.filter(mobile=mobile, code=code, is_used=False).last()

        if not otp:

            create_admin_log(
                request=request,
                action_type="PASSWORD_RESET_FAILED",
                action="OTP بازیابی اشتباه",
                model_name="OTPRequest",
                response_status=400,
                success=False,
                description=f"mobile={mobile}",
            )

            return error_response("کد اشتباه است")

        if otp.is_expired():

            create_admin_log(
                request=request,
                action_type="PASSWORD_RESET_FAILED",
                action="OTP بازیابی منقضی",
                model_name="OTPRequest",
                response_status=400,
                success=False,
                description=f"mobile={mobile}",
            )

            return error_response("کد منقضی شده است")

        create_admin_log(
            request=request,
            action_type="PASSWORD_RESET_VERIFY",
            action="تایید OTP بازیابی",
            model_name="OTPRequest",
            response_status=200,
            success=True,
            description=f"mobile={mobile}",
        )

        return success_response(message="کد تایید شد")


# ==========================================
# RESET PASSWORD COMPLETE
# ==========================================


class ResetPasswordComplete(APIView):

    permission_classes = [AllowAny]

    @extend_schema(request=ResetPasswordCompleteSerializer)
    def post(self, request):

        serializer = ResetPasswordCompleteSerializer(data=request.data)

        if not serializer.is_valid():

            return error_response("اطلاعات نامعتبر", serializer.errors)

        mobile = serializer.validated_data["mobile"]

        code = serializer.validated_data["code"]

        password = serializer.validated_data["password"]

        otp = OTPRequest.objects.filter(mobile=mobile, code=code, is_used=False).last()

        if not otp:

            create_admin_log(
                request=request,
                action_type="PASSWORD_CHANGE_FAILED",
                action="OTP تغییر رمز اشتباه",
                model_name="OTPRequest",
                response_status=400,
                success=False,
                description=f"mobile={mobile}",
            )

            return error_response("کد اشتباه است")

        if otp.is_expired():

            return error_response("کد منقضی شده است")

        user = User.objects.filter(mobile=mobile).first()

        if not user:

            return error_response("کاربر یافت نشد", status_code=404)

        user.set_password(password)

        user.save()

        otp.is_used = True
        otp.save()

        create_admin_log(
            request=request,
            user=user,
            action_type="PASSWORD_CHANGED",
            action="تغییر رمز عبور",
            model_name="User",
            object_id=user.id,
            response_status=200,
            success=True,
        )

        return success_response(message="رمز عبور تغییر کرد")


# ==========================================
# CHANGE MOBILE REQUEST
# ==========================================


class ChangeMobileRequest(APIView):

    permission_classes = [IsAuthenticated]

    @extend_schema(request=ChangeMobileRequestSerializer)
    def post(self, request):

        serializer = ChangeMobileRequestSerializer(data=request.data)

        if not serializer.is_valid():

            return error_response("اطلاعات نامعتبر", serializer.errors)

        new_mobile = serializer.validated_data["new_mobile"]

        if User.objects.filter(mobile=new_mobile).exists():

            return error_response("این شماره قبلا ثبت شده")

        code = str(random.randint(100000, 999999))

        client_type = request.headers.get("X-Client-Type", "gold")

        sms_sent = send_otp_sms(new_mobile, code, client_type)

        if not sms_sent:

            return error_response("خطا در ارسال پیامک", status_code=500)

        OTPRequest.objects.create(mobile=new_mobile, code=code)

        return success_response(message="کد تایید ارسال شد")


# ==========================================
# CHANGE MOBILE CONFIRM
# ==========================================


class ChangeMobileConfirm(APIView):

    permission_classes = [IsAuthenticated]

    @extend_schema(request=ChangeMobileConfirmSerializer)
    def post(self, request):

        serializer = ChangeMobileConfirmSerializer(data=request.data)

        if not serializer.is_valid():

            return error_response("اطلاعات نامعتبر", serializer.errors)

        new_mobile = serializer.validated_data["new_mobile"]

        code = serializer.validated_data["code"]

        otp = OTPRequest.objects.filter(
            mobile=new_mobile, code=code, is_used=False
        ).last()

        if not otp:
            return error_response("کد اشتباه است")

        if otp.is_expired():
            return error_response("کد منقضی شده")

        request.user.mobile = new_mobile
        request.user.username = new_mobile

        request.user.save()

        otp.is_used = True
        otp.save()

        return success_response(message="شماره موبایل تغییر کرد")


class CooperationRequestAPIView(APIView):

    permission_classes = [AllowAny]

    def post(self, request):

        serializer = CooperationRequestSerializer(data=request.data)

        if not serializer.is_valid():

            return error_response(errors=serializer.errors)

        cooperation_request = serializer.save()

        return success_response(
            message="درخواست همکاری با موفقیت ثبت شد",
            status_code=201,
            data={
                "request_id": cooperation_request.id,
                "full_name": cooperation_request.full_name,
                "mobile": cooperation_request.mobile,
            },
        )




# accounts/views.py - ویوهای تیکت کامل

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta
from .models import Ticket, TicketMessage, TicketCategory
from .serializers import (
    TicketListSerializer, TicketDetailSerializer, 
    TicketCreateSerializer, TicketUpdateSerializer,
    TicketMessageCreateSerializer, TicketMessageSerializer,
    TicketCategorySerializer
)
from .utils import success_response, error_response
from admin_panel.utils import create_admin_log


# ==========================================
# TICKET CATEGORIES
# ==========================================

class TicketCategoriesView(APIView):
    """دریافت لیست دسته‌بندی‌های تیکت"""
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        categories = TicketCategory.objects.filter(is_active=True)
        serializer = TicketCategorySerializer(categories, many=True)
        return success_response(
            message="لیست دسته‌بندی‌های تیکت",
            data=serializer.data
        )


# ==========================================
# TICKET LIST & CREATE
# ==========================================

class TicketListCreateView(APIView):
    """لیست تیکت‌ها و ایجاد تیکت جدید"""
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """دریافت لیست تیکت‌های کاربر"""
        tickets = Ticket.objects.filter(user=request.user)
        
        # فیلتر بر اساس وضعیت
        status = request.query_params.get('status')
        if status:
            tickets = tickets.filter(status=status)
        
        # فیلتر بر اساس اولویت
        priority = request.query_params.get('priority')
        if priority:
            tickets = tickets.filter(priority=priority)
        
        # جستجو در عنوان یا کد رهگیری
        search = request.query_params.get('search')
        if search:
            tickets = tickets.filter(
                Q(title__icontains=search) | 
                Q(tracking_code__icontains=search)
            )
        
        serializer = TicketListSerializer(
            tickets, 
            many=True, 
            context={'request': request}
        )
        
        return success_response(
            message="لیست تیکت‌ها",
            data=serializer.data
        )
    
    def post(self, request):
        """ایجاد تیکت جدید"""
        serializer = TicketCreateSerializer(data=request.data)
        
        if not serializer.is_valid():
            return error_response("اطلاعات نامعتبر است", serializer.errors)
        
        # ایجاد تیکت
        ticket = Ticket.objects.create(
            user=request.user,
            title=serializer.validated_data['title'],
            description=serializer.validated_data['description'],
            category=serializer.validated_data.get('category'),
            priority=serializer.validated_data.get('priority', 'medium'),
            attachment=serializer.validated_data.get('attachment')
        )
        
        # ثبت لاگ
        create_admin_log(
            request=request,
            user=request.user,
            action_type="TICKET_CREATED",
            action="ایجاد تیکت جدید",
            model_name="Ticket",
            object_id=ticket.id,
            success=True,
            description=f"""
تیکت جدید ایجاد شد

کد رهگیری: {ticket.tracking_code}
عنوان: {ticket.title}
کاربر: {request.user.mobile}
دسته‌بندی: {ticket.category.name if ticket.category else 'بدون دسته‌بندی'}
اولویت: {ticket.get_priority_display()}
"""
        )
        
        # ارسال پیام اولیه (توضیحات تیکت به عنوان اولین پیام)
        TicketMessage.objects.create(
            ticket=ticket,
            user=request.user,
            message=serializer.validated_data['description'],
            is_admin=False
        )
        
        # وضعیت تیکت به pending تغییر می‌کند (چون کاربر پیام داده)
        ticket.status = 'pending'
        ticket.save()
        
        # برگرداندن جزئیات تیکت
        detail_serializer = TicketDetailSerializer(
            ticket, 
            context={'request': request}
        )
        
        return success_response(
            message="تیکت با موفقیت ایجاد شد",
            data=detail_serializer.data,
            status_code=201
        )


# ==========================================
# TICKET DETAIL
# ==========================================

class TicketDetailView(APIView):
    """جزئیات تیکت"""
    
    permission_classes = [IsAuthenticated]
    
    def get_ticket(self, ticket_id, user):
        """دریافت تیکت با بررسی دسترسی"""
        try:
            ticket = Ticket.objects.get(id=ticket_id, user=user)
            return ticket
        except Ticket.DoesNotExist:
            return None
    
    def get(self, request, ticket_id):
        """دریافت جزئیات تیکت"""
        ticket = self.get_ticket(ticket_id, request.user)
        
        if not ticket:
            return error_response("تیکت یافت نشد", status_code=404)
        
        # علامت‌گذاری پیام‌های ادمین به عنوان خوانده شده
        TicketMessage.objects.filter(
            ticket=ticket,
            is_admin=True,
            is_read=False
        ).exclude(user=request.user).update(is_read=True, read_at=timezone.now())
        
        serializer = TicketDetailSerializer(
            ticket, 
            context={'request': request}
        )
        
        return success_response(
            message="جزئیات تیکت",
            data=serializer.data
        )
    
    def put(self, request, ticket_id):
        """بروزرسانی تیکت (فقط کاربر صاحب تیکت)"""
        ticket = self.get_ticket(ticket_id, request.user)
        
        if not ticket:
            return error_response("تیکت یافت نشد", status_code=404)
        
        if not ticket.can_user_edit(request.user):
            return error_response(
                "شما نمی‌توانید این تیکت را ویرایش کنید",
                status_code=403
            )
        
        serializer = TicketUpdateSerializer(ticket, data=request.data, partial=True)
        
        if not serializer.is_valid():
            return error_response("اطلاعات نامعتبر است", serializer.errors)
        
        serializer.save()
        
        create_admin_log(
            request=request,
            user=request.user,
            action_type="TICKET_UPDATED",
            action="بروزرسانی تیکت",
            model_name="Ticket",
            object_id=ticket.id,
            success=True,
            description=f"""
تیکت بروزرسانی شد

کد رهگیری: {ticket.tracking_code}
عنوان: {ticket.title}
کاربر: {request.user.mobile}
"""
        )
        
        detail_serializer = TicketDetailSerializer(
            ticket, 
            context={'request': request}
        )
        
        return success_response(
            message="تیکت با موفقیت بروزرسانی شد",
            data=detail_serializer.data
        )
    
    def delete(self, request, ticket_id):
        """بستن تیکت توسط کاربر"""
        ticket = self.get_ticket(ticket_id, request.user)
        
        if not ticket:
            return error_response("تیکت یافت نشد", status_code=404)
        
        if not ticket.can_user_close(request.user):
            return error_response(
                "شما نمی‌توانید این تیکت را ببندید",
                status_code=403
            )
        
        ticket.status = 'closed'
        ticket.closed_by = request.user
        ticket.closed_at = timezone.now()
        ticket.save()
        
        create_admin_log(
            request=request,
            user=request.user,
            action_type="TICKET_CLOSED",
            action="بستن تیکت توسط کاربر",
            model_name="Ticket",
            object_id=ticket.id,
            success=True,
            description=f"""
تیکت بسته شد

کد رهگیری: {ticket.tracking_code}
عنوان: {ticket.title}
کاربر: {request.user.mobile}
"""
        )
        
        return success_response(
            message="تیکت با موفقیت بسته شد"
        )


# ==========================================
# TICKET MESSAGES
# ==========================================
# accounts/views.py - اصلاح TicketMessagesView

class TicketMessagesView(APIView):
    """مدیریت پیام‌های تیکت"""
    
    permission_classes = [IsAuthenticated]
    
    def get_ticket(self, ticket_id, user):
        try:
            return Ticket.objects.get(id=ticket_id, user=user)
        except Ticket.DoesNotExist:
            return None
    
    def get(self, request, ticket_id):
        """دریافت پیام‌های تیکت"""
        ticket = self.get_ticket(ticket_id, request.user)
        
        if not ticket:
            return error_response("تیکت یافت نشد", status_code=404)
        
        messages = ticket.messages.all()
        serializer = TicketMessageSerializer(
            messages, 
            many=True,
            context={'request': request}
        )
        
        return success_response(
            message="لیست پیام‌ها",
            data=serializer.data
        )
    
    def post(self, request, ticket_id):
        """ارسال پیام جدید در تیکت"""
        ticket = self.get_ticket(ticket_id, request.user)
        
        if not ticket:
            return error_response("تیکت یافت نشد", status_code=404)
        
        if ticket.status == 'closed':
            return error_response(
                "این تیکت بسته شده است و نمی‌توان پیام ارسال کرد",
                status_code=400
            )
        
        serializer = TicketMessageCreateSerializer(data=request.data)
        
        if not serializer.is_valid():
            # گرفتن پیام خطای مناسب به فارسی
            error_messages = []
            for field, errors in serializer.errors.items():
                for error in errors:
                    if field == 'non_field_errors':
                        error_messages.append(error)
                    else:
                        error_messages.append(f"{error}")
            
            return error_response(
                message=" | ".join(error_messages) if error_messages else "اطلاعات نامعتبر است",
                errors=serializer.errors,
                status_code=400
            )
        
        # ایجاد پیام
        message_text = serializer.validated_data.get('message', '').strip()
        attachment = serializer.validated_data.get('attachment')
        
        # اگر پیام خالی بود و فقط عکس داشت، یک پیام پیش‌فرض بگذار
        if not message_text and attachment:
            message_text = "فایل ضمیمه ارسال شد"
        elif not message_text and not attachment:
            # این حالت نباید رخ دهد چون اعتبارسنجی دارد
            return error_response("حداقل یکی از متن پیام یا فایل ضمیمه باید ارسال شود", status_code=400)
        
        message = TicketMessage.objects.create(
            ticket=ticket,
            user=request.user,
            message=message_text,
            attachment=attachment,
            is_admin=False
        )
        
        # وضعیت تیکت به pending تغییر می‌کند (چون کاربر پیام داده)
        if ticket.status not in ['closed', 'resolved']:
            ticket.status = 'pending'
            ticket.save()
        
        create_admin_log(
            request=request,
            user=request.user,
            action_type="TICKET_MESSAGE_SENT",
            action="ارسال پیام در تیکت",
            model_name="TicketMessage",
            object_id=message.id,
            success=True,
            description=f"""
پیام جدید در تیکت

کد رهگیری: {ticket.tracking_code}
تیکت: {ticket.title}
کاربر: {request.user.mobile}
نوع: {'فایل ضمیمه' if attachment and not message_text else 'پیام متنی'}
"""
        )
        
        response_serializer = TicketMessageSerializer(
            message,
            context={'request': request}
        )
        
        return success_response(
            message="پیام با موفقیت ارسال شد",
            data=response_serializer.data,
            status_code=201
        )
# ==========================================
# TICKET UNREAD COUNT
# ==========================================

class TicketUnreadCountView(APIView):
    """تعداد تیکت‌های با پیام خوانده نشده"""
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        tickets = Ticket.objects.filter(user=request.user)
        
        unread_count = 0
        for ticket in tickets:
            unread = ticket.messages.filter(
                is_admin=True,
                is_read=False
            ).exclude(user=request.user).count()
            unread_count += unread
        
        return success_response(
            message="تعداد پیام‌های خوانده نشده",
            data={'unread_count': unread_count}
        )


# ==========================================
# AUTO RESOLVE TICKETS (Cron Job)
# ==========================================

def auto_resolve_tickets():
    """
    تابعی برای حل خودکار تیکت‌ها
    این تابع باید توسط Cron Job یا Celery اجرا شود
    """
    # پیدا کردن تیکت‌هایی که در وضعیت 'answered' هستند
    tickets = Ticket.objects.filter(status='answered')
    
    resolved_count = 0
    for ticket in tickets:
        if ticket.check_and_auto_resolve():
            resolved_count += 1
            
            # ثبت لاگ
            create_admin_log(
                request=None,
                user=None,
                action_type="TICKET_AUTO_RESOLVED",
                action="حل خودکار تیکت",
                model_name="Ticket",
                object_id=ticket.id,
                success=True,
                description=f"""
تیکت به صورت خودکار حل شد

کد رهگیری: {ticket.tracking_code}
عنوان: {ticket.title}
کاربر: {ticket.user.mobile}
دلیل: عدم فعالیت به مدت ۲ روز در وضعیت پاسخ داده شده
"""
            )
    
    return resolved_count


# ==========================================
# TICKET TRACKING (بررسی وضعیت با کد رهگیری)
# ==========================================

class TicketTrackingView(APIView):
    """بررسی وضعیت تیکت با کد رهگیری (بدون نیاز به احراز هویت)"""
    
    permission_classes = [AllowAny]
    
    def get(self, request, tracking_code):
        try:
            ticket = Ticket.objects.get(tracking_code=tracking_code)
        except Ticket.DoesNotExist:
            return error_response("تیکت با این کد رهگیری یافت نشد", status_code=404)
        
        # فقط اطلاعات عمومی را نمایش بده
        data = {
            'tracking_code': ticket.tracking_code,
            'title': ticket.title,
            'status': ticket.get_status_display(),
            'priority': ticket.get_priority_display(),
            'created_at': ticket.created_at,
            'last_activity_at': ticket.last_activity_at,
            'auto_resolved': ticket.auto_resolved,
            'last_message_user_type': ticket.get_last_message_user_type()
        }
        
        return success_response(
            message="وضعیت تیکت",
            data=data
        )