from rest_framework import serializers
from .models import User, BankCard
from .models import CooperationRequest
import jdatetime
from django.core.exceptions import ValidationError


class SendOTPSerializer(serializers.Serializer):
    mobile = serializers.CharField(
        max_length=11,
        error_messages={
            "required": "شماره موبایل الزامی است",
            "blank": "شماره موبایل نمی‌تواند خالی باشد",
            "null": "شماره موبایل نمی‌تواند خالی باشد",
            "max_length": "شماره موبایل باید 11 رقم باشد",
        }
    )


class VerifyOTPSerializer(serializers.Serializer):
    mobile = serializers.CharField(
        max_length=11,
        error_messages={
            "required": "شماره موبایل الزامی است",
            "blank": "شماره موبایل نمی‌تواند خالی باشد",
            "null": "شماره موبایل نمی‌تواند خالی باشد",
        }
    )
    code = serializers.CharField(
        min_length=6,
        max_length=6,
        error_messages={
            "required": "وارد کردن کد تایید الزامی است",
            "blank": "کد تایید نمی‌تواند خالی باشد",
            "null": "کد تایید نمی‌تواند خالی باشد",
            "min_length": "کد تایید باید دقیقا ۶ رقم باشد",
            "max_length": "کد تایید نمی‌تواند بیشتر از ۶ رقم باشد",
        },
    )


class LoginSerializer(serializers.Serializer):
    mobile = serializers.CharField(
        max_length=11,
        error_messages={
            "required": "شماره موبایل الزامی است",
            "blank": "شماره موبایل نمی‌تواند خالی باشد",
            "null": "شماره موبایل نمی‌تواند خالی باشد",
        }
    )
    password = serializers.CharField(
        error_messages={
            "required": "رمز عبور الزامی است",
            "blank": "رمز عبور نمی‌تواند خالی باشد",
            "null": "رمز عبور نمی‌تواند خالی باشد",
        }
    )


class LoginOTPSerializer(serializers.Serializer):
    mobile = serializers.CharField(
        max_length=11,
        error_messages={
            "required": "شماره موبایل الزامی است",
            "blank": "شماره موبایل نمی‌تواند خالی باشد",
            "null": "شماره موبایل نمی‌تواند خالی باشد",
        }
    )
    code = serializers.CharField(
        min_length=6,
        max_length=6,
        error_messages={
            "required": "وارد کردن کد تایید الزامی است",
            "blank": "کد تایید نمی‌تواند خالی باشد",
            "null": "کد تایید نمی‌تواند خالی باشد",
            "min_length": "کد تایید باید دقیقا ۶ رقم باشد",
            "max_length": "کد تایید نمی‌تواند بیشتر از ۶ رقم باشد",
        },
    )


class ResetPasswordRequestSerializer(serializers.Serializer):
    mobile = serializers.CharField(
        max_length=11,
        error_messages={
            "required": "شماره موبایل الزامی است",
            "blank": "شماره موبایل نمی‌تواند خالی باشد",
            "null": "شماره موبایل نمی‌تواند خالی باشد",
        }
    )


class ResetPasswordVerifySerializer(serializers.Serializer):
    mobile = serializers.CharField(
        max_length=11,
        error_messages={
            "required": "شماره موبایل الزامی است",
            "blank": "شماره موبایل نمی‌تواند خالی باشد",
            "null": "شماره موبایل نمی‌تواند خالی باشد",
        }
    )
    code = serializers.CharField(
        min_length=6,
        max_length=6,
        error_messages={
            "required": "وارد کردن کد تایید الزامی است",
            "blank": "کد تایید نمی‌تواند خالی باشد",
            "null": "کد تایید نمی‌تواند خالی باشد",
            "min_length": "کد تایید باید دقیقا ۶ رقم باشد",
            "max_length": "کد تایید نمی‌تواند بیشتر از ۶ رقم باشد",
        },
    )


class ResetPasswordCompleteSerializer(serializers.Serializer):
    mobile = serializers.CharField(
        max_length=11,
        error_messages={
            "required": "شماره موبایل الزامی است",
            "blank": "شماره موبایل نمی‌تواند خالی باشد",
            "null": "شماره موبایل نمی‌تواند خالی باشد",
        }
    )
    code = serializers.CharField(
        min_length=6,
        max_length=6,
        error_messages={
            "required": "وارد کردن کد تایید الزامی است",
            "blank": "کد تایید نمی‌تواند خالی باشد",
            "null": "کد تایید نمی‌تواند خالی باشد",
            "min_length": "کد تایید باید دقیقا ۶ رقم باشد",
            "max_length": "کد تایید نمی‌تواند بیشتر از ۶ رقم باشد",
        },
    )
    password = serializers.CharField(
        min_length=8,
        error_messages={
            "required": "رمز عبور الزامی است",
            "blank": "رمز عبور نمی‌تواند خالی باشد",
            "null": "رمز عبور نمی‌تواند خالی باشد",
            "min_length": "رمز عبور باید حداقل ۸ کاراکتر باشد",
        }
    )
    confirm_password = serializers.CharField(
        min_length=8,
        error_messages={
            "required": "تکرار رمز عبور الزامی است",
            "blank": "تکرار رمز عبور نمی‌تواند خالی باشد",
            "null": "تکرار رمز عبور نمی‌تواند خالی باشد",
            "min_length": "تکرار رمز عبور باید حداقل ۸ کاراکتر باشد",
        }
    )

    def validate(self, attrs):
        if attrs["password"] != attrs["confirm_password"]:
            raise serializers.ValidationError(
                {"confirm_password": "تکرار رمز عبور صحیح نیست"}
            )
        return attrs


class RegisterSerializer(serializers.Serializer):
    mobile = serializers.CharField(
        max_length=11,
        min_length=11,
        error_messages={
            "required": "شماره موبایل الزامی است",
            "blank": "شماره موبایل نمی‌تواند خالی باشد",
            "null": "شماره موبایل نمی‌تواند خالی باشد",
            "max_length": "شماره موبایل باید 11 رقم باشد",
            "min_length": "شماره موبایل باید 11 رقم باشد",
        },
    )

    first_name = serializers.CharField(
        error_messages={
            "required": "نام الزامی است",
            "blank": "نام نمی‌تواند خالی باشد",
            "null": "نام نمی‌تواند خالی باشد",
        }
    )

    last_name = serializers.CharField(
        error_messages={
            "required": "نام خانوادگی الزامی است",
            "blank": "نام خانوادگی نمی‌تواند خالی باشد",
            "null": "نام خانوادگی نمی‌تواند خالی باشد",
        }
    )

    national_code = serializers.CharField(
        max_length=10,
        min_length=10,
        error_messages={
            "required": "کد ملی الزامی است",
            "blank": "کد ملی نمی‌تواند خالی باشد",
            "null": "کد ملی نمی‌تواند خالی باشد",
            "max_length": "کد ملی باید دقیقاً 10 رقم باشد",
            "min_length": "کد ملی باید دقیقاً 10 رقم باشد",
        },
    )

    birth_date = serializers.CharField(
        error_messages={
            "required": "تاریخ تولد الزامی است",
            "blank": "تاریخ تولد نمی‌تواند خالی باشد",
            "null": "تاریخ تولد نمی‌تواند خالی باشد",
        }
    )

    password = serializers.CharField(
        min_length=8,
        error_messages={
            "required": "رمز عبور الزامی است",
            "blank": "رمز عبور نمی‌تواند خالی باشد",
            "null": "رمز عبور نمی‌تواند خالی باشد",
            "min_length": "رمز عبور باید حداقل 8 کاراکتر باشد",
        },
    )

    confirm_password = serializers.CharField(
        error_messages={
            "required": "تکرار رمز عبور الزامی است",
            "blank": "تکرار رمز عبور نمی‌تواند خالی باشد",
            "null": "تکرار رمز عبور نمی‌تواند خالی باشد",
        }
    )

    referral_code = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
        error_messages={
            "invalid": "کد معرف نامعتبر است",
        }
    )

    # =========================
    # MOBILE VALIDATION
    # =========================
    def validate_mobile(self, value):
        if not value:
            raise serializers.ValidationError("شماره موبایل نمی‌تواند خالی باشد")
        
        if not value.isdigit():
            raise serializers.ValidationError("شماره موبایل فقط باید عدد باشد")

        if len(value) != 11:
            raise serializers.ValidationError("شماره موبایل باید دقیقاً 11 رقم باشد")

        if not value.startswith("09"):
            raise serializers.ValidationError("شماره موبایل باید با 09 شروع شود")

        return value

    # =========================
    # NATIONAL CODE VALIDATION
    # =========================
    def validate_national_code(self, value):
        if not value:
            raise serializers.ValidationError("کد ملی نمی‌تواند خالی باشد")
        
        if not value.isdigit():
            raise serializers.ValidationError("کد ملی فقط باید عدد باشد")

        if len(value) != 10:
            raise serializers.ValidationError("کد ملی باید دقیقاً 10 رقم باشد")

        return value

    # =========================
    # BIRTH DATE VALIDATION
    # =========================
    def validate_birth_date(self, value):
        from datetime import date, datetime
        import re
        
        if not value:
            raise serializers.ValidationError("تاریخ تولد نمی‌تواند خالی باشد")
        
        value = value.strip()
        
        formats = [
            ('%Y-%m-%d', r'^\d{4}-\d{2}-\d{2}$'),
            ('%Y/%m/%d', r'^\d{4}/\d{2}/\d{2}$'),
            ('%Y%m%d', r'^\d{8}$'),
        ]
        
        birth_date = None
        for fmt, pattern in formats:
            if re.match(pattern, value):
                try:
                    birth_date = datetime.strptime(value, fmt).date()
                    break
                except ValueError:
                    continue
        
        if birth_date is None:
            raise serializers.ValidationError(
                "فرمت تاریخ تولد نامعتبر است. فرمت‌های مجاز: YYYY-MM-DD یا YYYY/MM/DD یا YYYYMMDD"
            )
        
        today = date.today()
        age = today.year - birth_date.year - (
            (today.month, today.day) < (birth_date.month, birth_date.day)
        )
        
        if age < 18:
            raise serializers.ValidationError(
                f"برای ثبت نام باید حداقل 18 سال داشته باشید. سن شما {age} سال است."
            )
        
        return birth_date.strftime('%Y-%m-%d')

    # =========================
    # GLOBAL VALIDATION
    # =========================
    def validate(self, attrs):
        password = attrs.get("password")
        confirm_password = attrs.get("confirm_password")

        if password != confirm_password:
            raise serializers.ValidationError(
                {"confirm_password": "رمز عبور و تکرار آن یکسان نیست"}
            )

        return attrs


from decimal import Decimal
from rest_framework import serializers
import jdatetime
from accounts.models import User, FeeSetting


class UserProfileSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    birth_date = serializers.SerializerMethodField()
    role_display = serializers.SerializerMethodField()
    auth_status_display = serializers.SerializerMethodField()

    gold_buy_fee = serializers.SerializerMethodField()
    gold_sell_fee = serializers.SerializerMethodField()
    silver_buy_fee = serializers.SerializerMethodField()
    silver_sell_fee = serializers.SerializerMethodField()

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
            "gold_buy_fee",
            "gold_sell_fee",
            "silver_buy_fee",
            "silver_sell_fee",
        ]

    def get_full_name(self, obj):
        return f"{obj.first_name or ''} {obj.last_name or ''}".strip()

    def get_birth_date(self, obj):
        if not obj.birth_date:
            return ""
        return jdatetime.date.fromgregorian(
            date=obj.birth_date
        ).strftime("%Y/%m/%d")

    def get_role_display(self, obj):
        return obj.get_role_display()

    def get_auth_status_display(self, obj):
        return obj.get_auth_status_display()

    def get_fee(self, obj, field_name):
        try:
            user_fee = obj.fee
            value = getattr(user_fee, field_name)
        except Exception:
            setting = FeeSetting.objects.last()
            if setting:
                value = getattr(setting, field_name)
            else:
                value = Decimal("0")

        return float(value * Decimal("100"))

    def get_gold_buy_fee(self, obj):
        return self.get_fee(obj, "gold_buy_fee")

    def get_gold_sell_fee(self, obj):
        return self.get_fee(obj, "gold_sell_fee")

    def get_silver_buy_fee(self, obj):
        return self.get_fee(obj, "silver_buy_fee")

    def get_silver_sell_fee(self, obj):
        return self.get_fee(obj, "silver_sell_fee")


class BankCardSerializer(serializers.ModelSerializer):
    shaba_number = serializers.CharField(
        required=False,
        allow_null=True,
        allow_blank=True,
        min_length=24,
        max_length=24,
        error_messages={
            "required": "شماره شبا الزامی است",
            "blank": "شماره شبا نمی‌تواند خالی باشد",
            "null": "شماره شبا نمی‌تواند خالی باشد",
            "min_length": "شماره شبا باید دقیقا ۲۴ رقم باشد",
            "max_length": "شماره شبا باید دقیقا ۲۴ رقم باشد",
        },
    )

    card_number = serializers.CharField(
        required=False,
        allow_null=True,
        allow_blank=True,
        min_length=16,
        max_length=16,
        error_messages={
            "required": "شماره کارت الزامی است",
            "blank": "شماره کارت نمی‌تواند خالی باشد",
            "null": "شماره کارت نمی‌تواند خالی باشد",
            "min_length": "شماره کارت باید دقیقا ۱۶ رقم باشد",
            "max_length": "شماره کارت باید دقیقا ۱۶ رقم باشد",
        },
    )

    bank_name = serializers.CharField(
        required=False,
        allow_null=True,
        allow_blank=True,
        error_messages={
            "blank": "نام بانک نمی‌تواند خالی باشد",
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
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def validate_shaba_number(self, value):
        if not value:
            return value

        if not value.isdigit():
            raise serializers.ValidationError("شماره شبا فقط باید شامل عدد باشد")

        if len(value) != 24:
            raise serializers.ValidationError("شماره شبا باید دقیقا ۲۴ رقم باشد")

        return value

    def validate_card_number(self, value):
        if not value:
            return value

        if not value.isdigit():
            raise serializers.ValidationError("شماره کارت فقط باید شامل عدد باشد")

        if len(value) != 16:
            raise serializers.ValidationError("شماره کارت باید دقیقا ۱۶ رقم باشد")

        return value

    def validate(self, attrs):
        card_number = attrs.get("card_number", getattr(self.instance, "card_number", None))
        shaba_number = attrs.get("shaba_number", getattr(self.instance, "shaba_number", None))

        if not card_number and not shaba_number:
            raise serializers.ValidationError("حداقل شماره کارت یا شماره شبا الزامی است")

        if shaba_number:
            qs = BankCard.objects.filter(shaba_number=shaba_number)
            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise serializers.ValidationError(
                    {"shaba_number": "این شماره شبا قبلاً ثبت شده است"}
                )

        if card_number:
            qs = BankCard.objects.filter(card_number=card_number)
            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise serializers.ValidationError(
                    {"card_number": "این شماره کارت قبلاً ثبت شده است"}
                )

        return attrs


class ChangeMobileRequestSerializer(serializers.Serializer):
    new_mobile = serializers.CharField(
        max_length=11,
        error_messages={
            "required": "شماره موبایل جدید الزامی است",
            "blank": "شماره موبایل جدید نمی‌تواند خالی باشد",
            "null": "شماره موبایل جدید نمی‌تواند خالی باشد",
            "max_length": "شماره موبایل باید 11 رقم باشد",
        }
    )


class ChangeMobileConfirmSerializer(serializers.Serializer):
    new_mobile = serializers.CharField(
        max_length=11,
        error_messages={
            "required": "شماره موبایل جدید الزامی است",
            "blank": "شماره موبایل جدید نمی‌تواند خالی باشد",
            "null": "شماره موبایل جدید نمی‌تواند خالی باشد",
        }
    )
    code = serializers.CharField(
        min_length=6,
        max_length=6,
        error_messages={
            "required": "وارد کردن کد تایید الزامی است",
            "blank": "کد تایید نمی‌تواند خالی باشد",
            "null": "کد تایید نمی‌تواند خالی باشد",
            "min_length": "کد تایید باید دقیقا ۶ رقم باشد",
            "max_length": "کد تایید نمی‌تواند بیشتر از ۶ رقم باشد",
        },
    )


class CooperationRequestSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(
        required=True,
        error_messages={
            "required": "نام و نام خانوادگی الزامی است",
            "blank": "نام و نام خانوادگی نمی‌تواند خالی باشد",
            "null": "نام و نام خانوادگی نمی‌تواند خالی باشد",
            "max_length": "نام و نام خانوادگی بیش از حد مجاز است",
        },
    )

    mobile = serializers.CharField(
        required=True,
        max_length=11,
        min_length=11,
        error_messages={
            "required": "شماره همراه الزامی است",
            "blank": "شماره همراه نمی‌تواند خالی باشد",
            "null": "شماره همراه نمی‌تواند خالی باشد",
            "max_length": "شماره همراه باید 11 رقم باشد",
            "min_length": "شماره همراه باید 11 رقم باشد",
        },
    )

    description = serializers.CharField(
        required=True,
        error_messages={
            "required": "توضیحات همکاری الزامی است",
            "blank": "توضیحات همکاری نمی‌تواند خالی باشد",
            "null": "توضیحات همکاری نمی‌تواند خالی باشد",
        },
    )

    class Meta:
        model = CooperationRequest
        fields = ["id", "full_name", "mobile", "description"]
        read_only_fields = ["id"]

    def validate_full_name(self, value):
        value = value.strip()
        if len(value) < 3:
            raise serializers.ValidationError("نام و نام خانوادگی معتبر نیست")
        return value

    def validate_mobile(self, value):
        value = value.strip()
        if not value.isdigit():
            raise serializers.ValidationError("شماره همراه نامعتبر است")
        if len(value) != 11:
            raise serializers.ValidationError("شماره همراه باید 11 رقم باشد")
        if not value.startswith("09"):
            raise serializers.ValidationError("شماره همراه باید با 09 شروع شود")
        return value

    def validate_description(self, value):
        value = value.strip()
        if len(value) < 10:
            raise serializers.ValidationError(
                "توضیحات همکاری حداقل باید 10 کاراکتر باشد"
            )
        return value