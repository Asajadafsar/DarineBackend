from rest_framework import serializers
from .models import User, BankCard
from rest_framework import serializers
from .models import CooperationRequest
import jdatetime

class SendOTPSerializer(serializers.Serializer):
    mobile = serializers.CharField(max_length=11)


class VerifyOTPSerializer(serializers.Serializer):
    mobile = serializers.CharField(max_length=11)
    code = serializers.CharField(
        min_length=6,
        max_length=6,
        error_messages={
            "required": "وارد کردن کد تایید الزامی است",
            "blank": "کد تایید نمی‌تواند خالی باشد",
            "min_length": "کد تایید باید دقیقاً ۶ رقم باشد (کوتاه است)",
            "max_length": "کد تایید باید دقیقاً ۶ رقم باشد (بلند است)",
        }
    )


class LoginSerializer(serializers.Serializer):
    mobile = serializers.CharField(max_length=11)
    password = serializers.CharField()


class LoginOTPSerializer(serializers.Serializer):
    mobile = serializers.CharField(max_length=11)
    code = serializers.CharField(max_length=6)


class ResetPasswordRequestSerializer(serializers.Serializer):
    mobile = serializers.CharField(max_length=11)


class ResetPasswordVerifySerializer(serializers.Serializer):
    mobile = serializers.CharField(max_length=11)
    code = serializers.CharField(max_length=6)


class ResetPasswordCompleteSerializer(serializers.Serializer):
    mobile = serializers.CharField(max_length=11)
    code = serializers.CharField(max_length=6)

    password = serializers.CharField(min_length=8)
    confirm_password = serializers.CharField(min_length=8)

    def validate(self, attrs):

        if attrs["password"] != attrs["confirm_password"]:
            raise serializers.ValidationError({
                "confirm_password": "تکرار رمز عبور صحیح نیست"
            })

        return attrs


from rest_framework import serializers


from rest_framework import serializers


from rest_framework import serializers


class RegisterSerializer(serializers.Serializer):

    mobile = serializers.CharField(
        max_length=11,
        min_length=11,
        error_messages={
            "required": "شماره موبایل الزامی است",
            "blank": "شماره موبایل نمی‌تواند خالی باشد",
            "max_length": "شماره موبایل باید 11 رقم باشد",
            "min_length": "شماره موبایل باید 11 رقم باشد",
        }
    )

    first_name = serializers.CharField(
        error_messages={
            "required": "نام الزامی است",
            "blank": "نام نمی‌تواند خالی باشد",
        }
    )

    last_name = serializers.CharField(
        error_messages={
            "required": "نام خانوادگی الزامی است",
            "blank": "نام خانوادگی نمی‌تواند خالی باشد",
        }
    )

    national_code = serializers.CharField(
        max_length=10,
        min_length=10,
        error_messages={
            "required": "کد ملی الزامی است",
            "blank": "کد ملی نمی‌تواند خالی باشد",
            "max_length": "کد ملی باید دقیقاً 10 رقم باشد",
            "min_length": "کد ملی باید دقیقاً 10 رقم باشد",
        }
    )

    birth_date = serializers.CharField(
        error_messages={
            "required": "تاریخ تولد الزامی است",
            "blank": "تاریخ تولد نمی‌تواند خالی باشد",
        }
    )

    password = serializers.CharField(
        min_length=8,
        error_messages={
            "required": "رمز عبور الزامی است",
            "blank": "رمز عبور نمی‌تواند خالی باشد",
            "min_length": "رمز عبور باید حداقل 8 کاراکتر باشد",
        }
    )

    confirm_password = serializers.CharField(
        error_messages={
            "required": "تکرار رمز عبور الزامی است",
            "blank": "تکرار رمز عبور نمی‌تواند خالی باشد",
        }
    )

    referral_code = serializers.CharField(
        required=False,
        allow_blank=True
    )

    # =========================
    # MOBILE VALIDATION
    # =========================
    def validate_mobile(self, value):

        if not value.isdigit():
            raise serializers.ValidationError(
                "شماره موبایل فقط باید عدد باشد"
            )

        if len(value) != 11:
            raise serializers.ValidationError(
                "شماره موبایل باید دقیقاً 11 رقم باشد"
            )

        if not value.startswith("09"):
            raise serializers.ValidationError(
                "شماره موبایل باید با 09 شروع شود"
            )

        return value

    # =========================
    # NATIONAL CODE VALIDATION
    # =========================
    def validate_national_code(self, value):

        if not value.isdigit():
            raise serializers.ValidationError(
                "کد ملی فقط باید عدد باشد"
            )

        if len(value) != 10:
            raise serializers.ValidationError(
                "کد ملی باید دقیقاً 10 رقم باشد"
            )

        return value

    # =========================
    # GLOBAL VALIDATION
    # =========================
    def validate(self, attrs):

        password = attrs.get("password")
        confirm_password = attrs.get("confirm_password")

        # فقط بررسی برابر بودن
        if password != confirm_password:
            raise serializers.ValidationError({
                "confirm_password": [
                    "رمز عبور و تکرار آن یکسان نیست"
                ]
            })

        return attrs

class UserProfileSerializer(serializers.ModelSerializer):

    full_name = serializers.SerializerMethodField()
    birth_date = serializers.SerializerMethodField()
    role_display = serializers.SerializerMethodField()
    auth_status_display = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "mobile",
            "first_name",
            "last_name",
            "full_name",
            "national_code",
            "birth_date",
            "role",
            "role_display",
            "auth_status",
            "auth_status_display",
        ]

    def get_full_name(self, obj):
        return f"{obj.first_name or ''} {obj.last_name or ''}".strip()

    def get_birth_date(self, obj):
        if not obj.birth_date:
            return ""
        return jdatetime.date.fromgregorian(date=obj.birth_date).strftime("%Y/%m/%d")

    def get_role_display(self, obj):
        return obj.get_role_display()

    def get_auth_status_display(self, obj):
        return obj.get_auth_status_display()
    
    

# serializers.py

from rest_framework import serializers
import re

class BankCardSerializer(serializers.ModelSerializer):

    shaba_number = serializers.CharField(
        required=False,
        allow_null=True,
        allow_blank=True,
        error_messages={
            "max_length": "شماره شبا باید دقیقا ۱۶ رقم باشد."
        }
    )

    card_number = serializers.CharField(
        required=False,
        allow_null=True,
        allow_blank=True,
        error_messages={
            "max_length": "شماره کارت باید دقیقا ۱۶ رقم باشد."
        }
    )


    class Meta:

        model = BankCard

        fields = [
            "id",
            "card_number",
            "shaba_number",
            "bank_name",
            "is_active",
            "created_at"
        ]



    def validate_shaba_number(self, value):

        if value:

            if not value.isdigit():

                raise serializers.ValidationError(
                    "شماره شبا فقط باید شامل عدد باشد."
                )


            if len(value) != 16:

                raise serializers.ValidationError(
                    "شماره شبا باید دقیقا ۱۶ رقم باشد."
                )


        return value



    def validate_card_number(self, value):

        if value:

            if not value.isdigit():

                raise serializers.ValidationError(
                    "شماره کارت فقط باید شامل عدد باشد."
                )


            if len(value) != 16:

                raise serializers.ValidationError(
                    "شماره کارت باید دقیقا ۱۶ رقم باشد."
                )


        return value



    def validate(self, attrs):

        card_number = attrs.get("card_number")
        shaba_number = attrs.get("shaba_number")


        if not card_number and not shaba_number:

            raise serializers.ValidationError(
                "حداقل شماره کارت یا شماره شبا الزامی است."
            )


        return attrs



class ChangeMobileRequestSerializer(serializers.Serializer):
    new_mobile = serializers.CharField(max_length=11)


class ChangeMobileConfirmSerializer(serializers.Serializer):
    new_mobile = serializers.CharField(max_length=11)
    code = serializers.CharField(max_length=6)





class CooperationRequestSerializer(
    serializers.ModelSerializer
):

    full_name = serializers.CharField(
        required=True,
        error_messages={
            "required": "نام و نام خانوادگی الزامی است",
            "blank": "نام و نام خانوادگی نمی‌تواند خالی باشد",
            "max_length": "نام و نام خانوادگی بیش از حد مجاز است",
        }
    )

    mobile = serializers.CharField(
        required=True,
        max_length=11,
        min_length=11,
        error_messages={
            "required": "شماره همراه الزامی است",
            "blank": "شماره همراه نمی‌تواند خالی باشد",
            "max_length": "شماره همراه باید 11 رقم باشد",
            "min_length": "شماره همراه باید 11 رقم باشد",
        }
    )

    description = serializers.CharField(
        required=True,
        error_messages={
            "required": "توضیحات همکاری الزامی است",
            "blank": "توضیحات همکاری نمی‌تواند خالی باشد",
        }
    )

    class Meta:

        model = CooperationRequest

        fields = [
            "id",
            "full_name",
            "mobile",
            "description",
        ]

        read_only_fields = [
            "id"
        ]

    def validate_full_name(
        self,
        value
    ):

        value = value.strip()

        if len(value) < 3:

            raise serializers.ValidationError(
                "نام و نام خانوادگی معتبر نیست"
            )

        return value

    def validate_mobile(
        self,
        value
    ):

        value = value.strip()

        if not value.isdigit():

            raise serializers.ValidationError(
                "شماره همراه نامعتبر است"
            )

        if len(value) != 11:

            raise serializers.ValidationError(
                "شماره همراه باید 11 رقم باشد"
            )

        if not value.startswith("09"):

            raise serializers.ValidationError(
                "شماره همراه باید با 09 شروع شود"
            )

        return value

    def validate_description(
        self,
        value
    ):

        value = value.strip()

        if len(value) < 10:

            raise serializers.ValidationError(
                "توضیحات همکاری حداقل باید 10 کاراکتر باشد"
            )

        return value