# accounts/views.py

import random

from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated

from rest_framework_simplejwt.tokens import RefreshToken

from drf_spectacular.utils import extend_schema

from django.contrib.auth import authenticate
from django.utils import timezone
from datetime import date

from .models import User, OTPRequest, BankCard

from .serializers import (
    CooperationRequestSerializer,
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

from .sms_service import send_otp_sms

from .cookies import (
    set_auth_cookies,
    clear_auth_cookies
)

from .utils import (
    success_response,
    error_response
)


# ==========================================
# REGISTER STEP 1
# ==========================================

class RegisterStepOne(APIView):

    permission_classes = [AllowAny]

    @extend_schema(
        request=SendOTPSerializer
    )
    def post(self, request):

        serializer = SendOTPSerializer(data=request.data)

        if not serializer.is_valid():
            return error_response(
                "اطلاعات نامعتبر است",
                serializer.errors
            )

        mobile = serializer.validated_data["mobile"]

        code = str(random.randint(100000, 999999))

        sms_sent = send_otp_sms(
            mobile,
            code
        )

        if not sms_sent:
            return error_response(
                "خطا در ارسال پیامک",
                status_code=500
            )

        OTPRequest.objects.create(
            mobile=mobile,
            code=code
        )

        return success_response(
            message="کد تایید ارسال شد"
        )


# ==========================================
# REGISTER STEP 2
# ==========================================

class RegisterStepTwo(APIView):

    permission_classes = [AllowAny]

    @extend_schema(
        request=VerifyOTPSerializer
    )
    def post(self, request):

        serializer = VerifyOTPSerializer(
            data=request.data
        )

        if not serializer.is_valid():
            return error_response(
                "اطلاعات نامعتبر",
                serializer.errors
            )

        mobile = serializer.validated_data["mobile"]
        code = serializer.validated_data["code"]

        otp = OTPRequest.objects.filter(
            mobile=mobile,
            code=code,
            is_used=False
        ).last()

        if not otp:
            return error_response(
                "کد تایید اشتباه است"
            )

        if otp.is_expired():
            return error_response(
                "کد تایید منقضی شده است"
            )

        otp.is_used = True
        otp.save()

        return success_response(
            message="کد تایید شد"
        )


# ==========================================
# REGISTER STEP 3
# ==========================================

class RegisterStepThree(APIView):

    permission_classes = [AllowAny]

    def post(self, request):

        mobile = request.data.get("mobile")

        if User.objects.filter(mobile=mobile).exists():

            return error_response(
                "این شماره قبلاً ثبت شده"
            )

        otp_verified = OTPRequest.objects.filter(
            mobile=mobile,
            is_used=True
        ).exists()

        if not otp_verified:

            return error_response(
                "ابتدا شماره موبایل را تایید کنید",
                status_code=403
            )

        password = request.data.get("password")
        confirm_password = request.data.get("confirm_password")

        if password != confirm_password:

            return error_response(
                "تکرار رمز عبور صحیح نیست"
            )

        try:

            user = User.objects.create(
                mobile=mobile,
                username=mobile,

                first_name=request.data.get("first_name"),
                last_name=request.data.get("last_name"),

                national_code=request.data.get("national_code"),

                birth_date=request.data.get("birth_date"),

                role="customer",
                auth_status="pending"
            )

            user.set_password(password)

            user.save()

            return success_response(
                message="ثبت نام با موفقیت انجام شد",
                data={
                    "user_id": user.id
                },
                status_code=201
            )

        except Exception as e:

            return error_response(
                str(e)
            )

# ==========================================
# LOGIN PASSWORD
# ==========================================

class LoginWithPassword(APIView):

    permission_classes = [AllowAny]

    @extend_schema(
        request=LoginSerializer
    )
    def post(self, request):

        serializer = LoginSerializer(
            data=request.data
        )

        if not serializer.is_valid():

            return error_response(
                "اطلاعات نامعتبر",
                serializer.errors
            )

        mobile = serializer.validated_data["mobile"]

        password = serializer.validated_data["password"]

        user = authenticate(
            request,
            mobile=mobile,
            password=password
        )

        if not user:

            return error_response(
                "شماره موبایل یا رمز عبور اشتباه است",
                status_code=401
            )

        refresh = RefreshToken.for_user(user)

        access = refresh.access_token

        response = success_response(
            message="ورود موفق",
            data={
                "user": {
                    "id": user.id,
                    "full_name": f"{user.first_name} {user.last_name}",
                    "role": user.role,
                    "status": user.auth_status
                }
            }
        )

        set_auth_cookies(
            response,
            str(access),
            str(refresh)
        )

        return response


# ==========================================
# LOGIN OTP
# ==========================================

class LoginWithOTP(APIView):

    permission_classes = [AllowAny]

    @extend_schema(
        request=LoginOTPSerializer
    )
    def post(self, request):

        serializer = LoginOTPSerializer(
            data=request.data
        )

        if not serializer.is_valid():

            return error_response(
                "اطلاعات نامعتبر",
                serializer.errors
            )

        mobile = serializer.validated_data["mobile"]

        code = serializer.validated_data["code"]

        otp = OTPRequest.objects.filter(
            mobile=mobile,
            code=code,
            is_used=False
        ).last()

        if not otp:
            return error_response(
                "کد اشتباه است"
            )

        if otp.is_expired():
            return error_response(
                "کد منقضی شده"
            )

        user = User.objects.filter(
            mobile=mobile
        ).first()

        if not user:
            return error_response(
                "کاربر یافت نشد",
                status_code=404
            )

        otp.is_used = True
        otp.save()

        refresh = RefreshToken.for_user(user)

        access = refresh.access_token

        response = success_response(
            message="ورود موفق",
            data={
                "user": {
                    "id": user.id,
                    "full_name": f"{user.first_name} {user.last_name}",
                    "role": user.role,
                    "status": user.auth_status
                }
            }
        )

        set_auth_cookies(
            response,
            str(access),
            str(refresh)
        )

        return response


# ==========================================
# REFRESH TOKEN
# ==========================================

class RefreshTokenView(APIView):

    permission_classes = [AllowAny]

    def post(self, request):

        refresh_token = request.COOKIES.get(
            "refreshToken"
        )

        if not refresh_token:
            return error_response(
                "رفرش توکن یافت نشد",
                status_code=401
            )

        try:

            refresh = RefreshToken(
                refresh_token
            )

            access_token = str(
                refresh.access_token
            )

            response = success_response(
                message="توکن بروزرسانی شد"
            )

            response.set_cookie(
                key="accessToken",
                value=access_token,
                httponly=True,
                secure=False,
                samesite="Lax",
                path="/",
                max_age=600
            )

            return response

        except Exception:

            return error_response(
                "رفرش توکن نامعتبر است",
                status_code=401
            )


# ==========================================
# LOGOUT
# ==========================================

class LogoutView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request):

        response = success_response(
            message="خروج موفق"
        )

        clear_auth_cookies(response)

        return response


# ==========================================
# PROFILE
# ==========================================

class ProfileView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        serializer = UserProfileSerializer(
            request.user
        )

        return success_response(
            message="اطلاعات پروفایل",
            data=serializer.data
        )


# ==========================================
# BANK CARDS
# ==========================================

class UserBankCards(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        cards = BankCard.objects.filter(
            user=request.user,
            is_active=True
        )

        serializer = BankCardSerializer(
            cards,
            many=True
        )

        return success_response(
            message="لیست کارت‌ها",
            data=serializer.data
        )

    def post(self, request):

        active_cards_count = BankCard.objects.filter(
            user=request.user,
            is_active=True
        ).count()

        if active_cards_count >= 5:

            return error_response(
                "حداکثر ۵ کارت مجاز است"
            )

        serializer = BankCardSerializer(
            data=request.data
        )

        if not serializer.is_valid():

            return error_response(
                "اطلاعات کارت نامعتبر است",
                serializer.errors
            )

        serializer.save(
            user=request.user
        )

        return success_response(
            message="کارت ثبت شد",
            data=serializer.data,
            status_code=201
        )


# ==========================================
# DELETE CARD
# ==========================================

class DeleteBankCard(APIView):

    permission_classes = [IsAuthenticated]

    def delete(self, request, card_id):

        card = BankCard.objects.filter(
            id=card_id,
            user=request.user,
            is_active=True
        ).first()

        if not card:

            return error_response(
                "کارت یافت نشد",
                status_code=404
            )

        card.is_active = False
        card.save()

        return success_response(
            message="کارت حذف شد"
        )


# ==========================================
# RESET PASSWORD REQUEST
# ==========================================

class ResetPasswordRequest(APIView):

    permission_classes = [AllowAny]

    @extend_schema(
        request=ResetPasswordRequestSerializer
    )
    def post(self, request):

        serializer = ResetPasswordRequestSerializer(
            data=request.data
        )

        if not serializer.is_valid():

            return error_response(
                "اطلاعات نامعتبر",
                serializer.errors
            )

        mobile = serializer.validated_data["mobile"]

        user = User.objects.filter(
            mobile=mobile
        ).first()

        if not user:

            return error_response(
                "کاربر یافت نشد",
                status_code=404
            )

        code = str(random.randint(100000, 999999))

        sms_sent = send_otp_sms(
            mobile,
            code
        )

        if not sms_sent:

            return error_response(
                "خطا در ارسال پیامک",
                status_code=500
            )

        OTPRequest.objects.create(
            mobile=mobile,
            code=code
        )

        return success_response(
            message="کد بازیابی ارسال شد"
        )


# ==========================================
# RESET PASSWORD VERIFY
# ==========================================

class ResetPasswordVerify(APIView):

    permission_classes = [AllowAny]

    @extend_schema(
        request=ResetPasswordVerifySerializer
    )
    def post(self, request):

        serializer = ResetPasswordVerifySerializer(
            data=request.data
        )

        if not serializer.is_valid():

            return error_response(
                "اطلاعات نامعتبر",
                serializer.errors
            )

        mobile = serializer.validated_data["mobile"]

        code = serializer.validated_data["code"]

        otp = OTPRequest.objects.filter(
            mobile=mobile,
            code=code,
            is_used=False
        ).last()

        if not otp:
            return error_response(
                "کد اشتباه است"
            )

        if otp.is_expired():
            return error_response(
                "کد منقضی شده است"
            )

        return success_response(
            message="کد تایید شد"
        )


# ==========================================
# RESET PASSWORD COMPLETE
# ==========================================

class ResetPasswordComplete(APIView):

    permission_classes = [AllowAny]

    @extend_schema(
        request=ResetPasswordCompleteSerializer
    )
    def post(self, request):

        serializer = ResetPasswordCompleteSerializer(
            data=request.data
        )

        if not serializer.is_valid():

            return error_response(
                "اطلاعات نامعتبر",
                serializer.errors
            )

        mobile = serializer.validated_data["mobile"]

        code = serializer.validated_data["code"]

        password = serializer.validated_data["password"]

        otp = OTPRequest.objects.filter(
            mobile=mobile,
            code=code,
            is_used=False
        ).last()

        if not otp:
            return error_response(
                "کد اشتباه است"
            )

        if otp.is_expired():
            return error_response(
                "کد منقضی شده است"
            )

        user = User.objects.filter(
            mobile=mobile
        ).first()

        if not user:
            return error_response(
                "کاربر یافت نشد",
                status_code=404
            )

        user.set_password(password)
        user.save()

        otp.is_used = True
        otp.save()

        return success_response(
            message="رمز عبور تغییر کرد"
        )


# ==========================================
# CHANGE MOBILE REQUEST
# ==========================================

class ChangeMobileRequest(APIView):

    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=ChangeMobileRequestSerializer
    )
    def post(self, request):

        serializer = ChangeMobileRequestSerializer(
            data=request.data
        )

        if not serializer.is_valid():

            return error_response(
                "اطلاعات نامعتبر",
                serializer.errors
            )

        new_mobile = serializer.validated_data[
            "new_mobile"
        ]

        if User.objects.filter(
            mobile=new_mobile
        ).exists():

            return error_response(
                "این شماره قبلا ثبت شده"
            )

        code = str(random.randint(100000, 999999))

        sms_sent = send_otp_sms(
            new_mobile,
            code
        )

        if not sms_sent:

            return error_response(
                "خطا در ارسال پیامک",
                status_code=500
            )

        OTPRequest.objects.create(
            mobile=new_mobile,
            code=code
        )

        return success_response(
            message="کد تایید ارسال شد"
        )


# ==========================================
# CHANGE MOBILE CONFIRM
# ==========================================

class ChangeMobileConfirm(APIView):

    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=ChangeMobileConfirmSerializer
    )
    def post(self, request):

        serializer = ChangeMobileConfirmSerializer(
            data=request.data
        )

        if not serializer.is_valid():

            return error_response(
                "اطلاعات نامعتبر",
                serializer.errors
            )

        new_mobile = serializer.validated_data[
            "new_mobile"
        ]

        code = serializer.validated_data[
            "code"
        ]

        otp = OTPRequest.objects.filter(
            mobile=new_mobile,
            code=code,
            is_used=False
        ).last()

        if not otp:
            return error_response(
                "کد اشتباه است"
            )

        if otp.is_expired():
            return error_response(
                "کد منقضی شده"
            )

        request.user.mobile = new_mobile
        request.user.username = new_mobile

        request.user.save()

        otp.is_used = True
        otp.save()

        return success_response(
            message="شماره موبایل تغییر کرد"
        )
    






class CooperationRequestAPIView(APIView):

    permission_classes = [AllowAny]

    def post(self, request):

        serializer = CooperationRequestSerializer(data=request.data)

        if not serializer.is_valid():
            return error_response(data=serializer.errors)

        obj = serializer.save()

        return success_response(
            message="درخواست همکاری با موفقیت ثبت شد",
            status_code=201,
            data={
                "request_id": obj.id
            }
        )