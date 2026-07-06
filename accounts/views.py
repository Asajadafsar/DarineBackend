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


class RegisterStepThree(APIView):

    permission_classes = [AllowAny]

    def post(self, request):

        serializer = RegisterSerializer(data=request.data)

        if not serializer.is_valid():

            response = error_response("اطلاعات نامعتبر است", serializer.errors)

            create_admin_log(
                request=request,
                action_type="REGISTER_ERROR",
                action="خطا در ثبت نام",
                model_name="User",
                success=False,
                response_status=response.status_code,
                error_message=str(serializer.errors),
            )

            return response

        data = serializer.validated_data

        mobile = data["mobile"]

        user = User.objects.create(
            mobile=mobile,
            username=mobile,
            first_name=data["first_name"],
            last_name=data["last_name"],
            national_code=data["national_code"],
            birth_date=data["birth_date"],
            role="customer",
            auth_status="pending",
        )

        user.set_password(data["password"])

        user.save()

        create_admin_log(
            request=request,
            user=user,
            action_type="USER_REGISTER",
            action="ثبت نام کاربر",
            model_name="User",
            object_id=user.id,
            success=True,
            description=f"""
کاربر جدید ایجاد شد

موبایل:
{user.mobile}

نام:
{user.first_name} {user.last_name}
""",
        )

        refresh = RefreshToken.for_user(user)

        access = refresh.access_token

        response = success_response(
            message="ثبت نام موفق",
            status_code=201,
            data={"user": {"id": user.id, "mobile": user.mobile}},
        )

        set_auth_cookies(response, str(access), str(refresh))

        return response


# # ==========================================
# # LOGIN PASSWORD
# # ==========================================

# class LoginWithPassword(APIView):

#     permission_classes = [AllowAny]

#     @extend_schema(
#         request=LoginSerializer
#     )
#     def post(self, request):

#         serializer = LoginSerializer(
#             data=request.data
#         )

#         if not serializer.is_valid():

#             return error_response(
#                 "اطلاعات نامعتبر",
#                 serializer.errors
#             )

#         mobile = serializer.validated_data["mobile"]

#         password = serializer.validated_data["password"]

#         user = authenticate(
#             request,
#             mobile=mobile,
#             password=password
#         )

#         if not user:

#             return error_response(
#                 "شماره موبایل یا رمز عبور اشتباه است",
#                 status_code=401
#             )
#         send_login_sms(user.mobile)
#         refresh = RefreshToken.for_user(user)

#         access = refresh.access_token

#         response = success_response(
#             message="ورود موفق",
#             data={
#                 "user": {
#                     "id": user.id,
#                     "full_name": f"{user.first_name} {user.last_name}",
#                     "role": user.role,
#                     "status": user.auth_status
#                 }
#             }
#         )

#         set_auth_cookies(
#             response,
#             str(access),
#             str(refresh)
#         )

#         return response


# # ==========================================
# # LOGIN OTP
# # ==========================================

# class LoginWithOTP(APIView):

#     permission_classes = [AllowAny]

#     @extend_schema(
#         request=LoginOTPSerializer
#     )
#     def post(self, request):

#         serializer = LoginOTPSerializer(
#             data=request.data
#         )

#         if not serializer.is_valid():

#             return error_response(
#                 "اطلاعات نامعتبر",
#                 serializer.errors
#             )

#         mobile = serializer.validated_data["mobile"]

#         code = serializer.validated_data["code"]

#         otp = OTPRequest.objects.filter(
#             mobile=mobile,
#             code=code,
#             is_used=False
#         ).last()

#         if not otp:
#             return error_response(
#                 "کد اشتباه است"
#             )

#         if otp.is_expired():
#             return error_response(
#                 "کد منقضی شده"
#             )

#         user = User.objects.filter(
#             mobile=mobile
#         ).first()


#         if not user:
#             return error_response(
#                 {
#                     "success": False,
#                      "message": " شماره موبایل ثبت نشده است، لطفا ثبت نام کنید.,",
#                      "need_register": True,
#                      "mobile": mobile
#                 },
#                 status_code=404
#             )

#         otp.is_used = True
#         otp.save()
#         send_login_sms(user.mobile)
#         refresh = RefreshToken.for_user(user)

#         access = refresh.access_token

#         response = success_response(
#             message="ورود موفق",
#             data={
#                 "user": {
#                     "id": user.id,
#                     "full_name": f"{user.first_name} {user.last_name}",
#                     "role": user.role,
#                     "status": user.auth_status
#                 }
#             }
#         )

#         set_auth_cookies(
#             response,
#             str(access),
#             str(refresh)
#         )

#         return response

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


class UserBankCards(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        cards = BankCard.objects.filter(user=request.user, is_active=True)

        serializer = BankCardSerializer(cards, many=True)

        return success_response(message="لیست کارت‌ها", data=serializer.data)

    def post(self, request):

        active_cards_count = BankCard.objects.filter(
            user=request.user, is_active=True
        ).count()

        serializer = BankCardSerializer(data=request.data)

        if not serializer.is_valid():

            return error_response("اطلاعات کارت نامعتبر است", serializer.errors)

        serializer.save(user=request.user)

        return success_response(
            message="کارت ثبت شد", data=serializer.data, status_code=201
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
