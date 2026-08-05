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


# class RegisterSerializer(serializers.Serializer):
#     mobile = serializers.CharField(
#         max_length=11,
#         min_length=11,
#         error_messages={
#             "required": "شماره موبایل الزامی است",
#             "blank": "شماره موبایل نمی‌تواند خالی باشد",
#             "null": "شماره موبایل نمی‌تواند خالی باشد",
#             "max_length": "شماره موبایل باید 11 رقم باشد",
#             "min_length": "شماره موبایل باید 11 رقم باشد",
#         },
#     )

#     first_name = serializers.CharField(
#         error_messages={
#             "required": "نام الزامی است",
#             "blank": "نام نمی‌تواند خالی باشد",
#             "null": "نام نمی‌تواند خالی باشد",
#         }
#     )

#     last_name = serializers.CharField(
#         error_messages={
#             "required": "نام خانوادگی الزامی است",
#             "blank": "نام خانوادگی نمی‌تواند خالی باشد",
#             "null": "نام خانوادگی نمی‌تواند خالی باشد",
#         }
#     )

#     national_code = serializers.CharField(
#         max_length=10,
#         min_length=10,
#         error_messages={
#             "required": "کد ملی الزامی است",
#             "blank": "کد ملی نمی‌تواند خالی باشد",
#             "null": "کد ملی نمی‌تواند خالی باشد",
#             "max_length": "کد ملی باید دقیقاً 10 رقم باشد",
#             "min_length": "کد ملی باید دقیقاً 10 رقم باشد",
#         },
#     )

#     birth_date = serializers.CharField(
#         error_messages={
#             "required": "تاریخ تولد الزامی است",
#             "blank": "تاریخ تولد نمی‌تواند خالی باشد",
#             "null": "تاریخ تولد نمی‌تواند خالی باشد",
#         }
#     )

#     password = serializers.CharField(
#         min_length=8,
#         error_messages={
#             "required": "رمز عبور الزامی است",
#             "blank": "رمز عبور نمی‌تواند خالی باشد",
#             "null": "رمز عبور نمی‌تواند خالی باشد",
#             "min_length": "رمز عبور باید حداقل 8 کاراکتر باشد",
#         },
#     )

#     confirm_password = serializers.CharField(
#         error_messages={
#             "required": "تکرار رمز عبور الزامی است",
#             "blank": "تکرار رمز عبور نمی‌تواند خالی باشد",
#             "null": "تکرار رمز عبور نمی‌تواند خالی باشد",
#         }
#     )

#     referral_code = serializers.CharField(
#         required=False,
#         allow_blank=True,
#         allow_null=True,
#         error_messages={
#             "invalid": "کد معرف نامعتبر است",
#         }
#     )

#     # =========================
#     # MOBILE VALIDATION
#     # =========================
#     def validate_mobile(self, value):
#         if not value:
#             raise serializers.ValidationError("شماره موبایل نمی‌تواند خالی باشد")
        
#         if not value.isdigit():
#             raise serializers.ValidationError("شماره موبایل فقط باید عدد باشد")

#         if len(value) != 11:
#             raise serializers.ValidationError("شماره موبایل باید دقیقاً 11 رقم باشد")

#         if not value.startswith("09"):
#             raise serializers.ValidationError("شماره موبایل باید با 09 شروع شود")

#         return value

#     # =========================
#     # NATIONAL CODE VALIDATION
#     # =========================
#     def validate_national_code(self, value):
#         if not value:
#             raise serializers.ValidationError("کد ملی نمی‌تواند خالی باشد")
        
#         if not value.isdigit():
#             raise serializers.ValidationError("کد ملی فقط باید عدد باشد")

#         if len(value) != 10:
#             raise serializers.ValidationError("کد ملی باید دقیقاً 10 رقم باشد")

#         return value

#     # =========================
#     # BIRTH DATE VALIDATION
#     # =========================
#     def validate_birth_date(self, value):
#         from datetime import date, datetime
#         import re
        
#         if not value:
#             raise serializers.ValidationError("تاریخ تولد نمی‌تواند خالی باشد")
        
#         value = value.strip()
        
#         formats = [
#             ('%Y-%m-%d', r'^\d{4}-\d{2}-\d{2}$'),
#             ('%Y/%m/%d', r'^\d{4}/\d{2}/\d{2}$'),
#             ('%Y%m%d', r'^\d{8}$'),
#         ]
        
#         birth_date = None
#         for fmt, pattern in formats:
#             if re.match(pattern, value):
#                 try:
#                     birth_date = datetime.strptime(value, fmt).date()
#                     break
#                 except ValueError:
#                     continue
        
#         if birth_date is None:
#             raise serializers.ValidationError(
#                 "فرمت تاریخ تولد نامعتبر است. فرمت‌های مجاز: YYYY-MM-DD یا YYYY/MM/DD یا YYYYMMDD"
#             )
        
#         today = date.today()
#         age = today.year - birth_date.year - (
#             (today.month, today.day) < (birth_date.month, birth_date.day)
#         )
        
#         if age < 18:
#             raise serializers.ValidationError(
#                 f"برای ثبت نام باید حداقل 18 سال داشته باشید. سن شما {age} سال است."
#             )
        
#         return birth_date.strftime('%Y-%m-%d')

#     # =========================
#     # GLOBAL VALIDATION
#     # =========================
#     def validate(self, attrs):
#         password = attrs.get("password")
#         confirm_password = attrs.get("confirm_password")

#         if password != confirm_password:
#             raise serializers.ValidationError(
#                 {"confirm_password": "رمز عبور و تکرار آن یکسان نیست"}
#             )

#         return attrs



# accounts/serializers.py

from rest_framework import serializers
import jdatetime
import re
from datetime import date, datetime


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
    # VALIDATE MOBILE
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
    # VALIDATE FIRST NAME
    # =========================
    def validate_first_name(self, value):
        if not value:
            raise serializers.ValidationError("نام نمی‌تواند خالی باشد")
        
        value = value.strip()
        
        if len(value) < 2:
            raise serializers.ValidationError("نام باید حداقل ۲ کاراکتر باشد")
        
        if len(value) > 50:
            raise serializers.ValidationError("نام نباید بیشتر از ۵۰ کاراکتر باشد")
        
        # فقط حروف فارسی و فاصله
        if not re.match(r'^[\u0600-\u06FF\s]+$', value):
            raise serializers.ValidationError("نام باید فقط با حروف فارسی وارد شود")
        
        return value

    # =========================
    # VALIDATE LAST NAME
    # =========================
    def validate_last_name(self, value):
        if not value:
            raise serializers.ValidationError("نام خانوادگی نمی‌تواند خالی باشد")
        
        value = value.strip()
        
        if len(value) < 2:
            raise serializers.ValidationError("نام خانوادگی باید حداقل ۲ کاراکتر باشد")
        
        if len(value) > 50:
            raise serializers.ValidationError("نام خانوادگی نباید بیشتر از ۵۰ کاراکتر باشد")
        
        # فقط حروف فارسی و فاصله
        if not re.match(r'^[\u0600-\u06FF\s]+$', value):
            raise serializers.ValidationError("نام خانوادگی باید فقط با حروف فارسی وارد شود")
        
        return value

    # =========================
    # VALIDATE NATIONAL CODE
    # =========================
    def validate_national_code(self, value):
        if not value:
            raise serializers.ValidationError("کد ملی نمی‌تواند خالی باشد")
        
        if not value.isdigit():
            raise serializers.ValidationError("کد ملی فقط باید عدد باشد")

        if len(value) != 10:
            raise serializers.ValidationError("کد ملی باید دقیقاً 10 رقم باشد")

        # اعتبارسنجی الگوریتم کد ملی
        if not self._validate_national_code_algorithm(value):
            raise serializers.ValidationError("کد ملی وارد شده در ثبت احوال موجود نیست")

        return value

    def _validate_national_code_algorithm(self, code):
        """
        الگوریتم اعتبارسنجی کد ملی ایران
        """
        # کدهای ملی نامعتبر
        invalid_codes = [
            '0000000000', '1111111111', '2222222222', '3333333333',
            '4444444444', '5555555555', '6666666666', '7777777777',
            '8888888888', '9999999999'
        ]
        if code in invalid_codes:
            return False
        
        # الگوریتم محاسبه
        s = 0
        for i in range(9):
            s += int(code[i]) * (10 - i)
        
        r = s % 11
        if r < 2:
            return int(code[9]) == r
        else:
            return int(code[9]) == (11 - r)

    # =========================
    # VALIDATE BIRTH DATE
    # =========================
    def validate_birth_date(self, value):
        if not value:
            raise serializers.ValidationError("تاریخ تولد نمی‌تواند خالی باشد")
        
        value = value.strip()
        
        # پشتیبانی از فرمت‌های مختلف
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
        
        # بررسی اینکه تاریخ تولد در آینده نباشد
        today = date.today()
        if birth_date > today:
            raise serializers.ValidationError("تاریخ تولد نمی‌تواند در آینده باشد")
        
        # بررسی حداقل سن (۱۸ سال)
        age = today.year - birth_date.year - (
            (today.month, today.day) < (birth_date.month, birth_date.day)
        )
        
        if age < 18:
            raise serializers.ValidationError(
                f"برای ثبت نام باید حداقل ۱۸ سال داشته باشید. سن شما {age} سال است."
            )
        
        # بررسی حداکثر سن (۱۰۰ سال)
        if age > 100:
            raise serializers.ValidationError(
                f"سن وارد شده ({age} سال) معتبر نیست"
            )
        
        # برگرداندن تاریخ به فرمت استاندارد
        return birth_date.strftime('%Y-%m-%d')

    # =========================
    # VALIDATE PASSWORD
    # =========================
    def validate_password(self, value):
        if not value:
            raise serializers.ValidationError("رمز عبور نمی‌تواند خالی باشد")
        
        if len(value) < 8:
            raise serializers.ValidationError("رمز عبور باید حداقل ۸ کاراکتر باشد")
        
        # بررسی وجود حداقل یک حرف بزرگ
        if not re.search(r'[A-Z]', value):
            raise serializers.ValidationError("رمز عبور باید حداقل یک حرف بزرگ (A-Z) داشته باشد")
        
        # بررسی وجود حداقل یک حرف کوچک
        if not re.search(r'[a-z]', value):
            raise serializers.ValidationError("رمز عبور باید حداقل یک حرف کوچک (a-z) داشته باشد")
        
        # بررسی وجود حداقل یک عدد
        if not re.search(r'\d', value):
            raise serializers.ValidationError("رمز عبور باید حداقل یک عدد داشته باشد")
        
        # بررسی وجود حداقل یک کاراکتر خاص
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', value):
            raise serializers.ValidationError("رمز عبور باید حداقل یک کاراکتر خاص داشته باشد")
        
        return value

    # =========================
    # VALIDATE CONFIRM PASSWORD
    # =========================
    def validate_confirm_password(self, value):
        if not value:
            raise serializers.ValidationError("تکرار رمز عبور نمی‌تواند خالی باشد")
        
        if len(value) < 8:
            raise serializers.ValidationError("تکرار رمز عبور باید حداقل ۸ کاراکتر باشد")
        
        return value

    # =========================
    # VALIDATE REFERRAL CODE (اختیاری)
    # =========================
    def validate_referral_code(self, value):
        if not value:
            return None
        
        value = value.strip()
        
        if len(value) > 20:
            raise serializers.ValidationError("کد معرف نباید بیشتر از ۲۰ کاراکتر باشد")
        
        # بررسی وجود کد معرف در دیتابیس (در مرحله view انجام می‌شود)
        # اینجا فقط اعتبارسنجی فرمت انجام می‌شود
        if not re.match(r'^[A-Za-z0-9]+$', value):
            raise serializers.ValidationError("کد معرف فقط باید شامل حروف و اعداد باشد")
        
        return value

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

    # =========================
    # CREATE METHOD (برای استفاده در view)
    # =========================
    def create(self, validated_data):
        """
        این متد در صورت نیاز برای ایجاد کاربر استفاده می‌شود
        اما در view ما مستقیماً کاربر را ایجاد می‌کنیم
        """
        from .models import User
        
        # حذف confirm_password از دیکشنری
        validated_data.pop('confirm_password', None)
        
        # ایجاد کاربر
        user = User.objects.create_user(
            username=validated_data['mobile'],
            mobile=validated_data['mobile'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            national_code=validated_data['national_code'],
            birth_date=validated_data['birth_date'],
            password=validated_data['password'],
        )
        
        # اگر کد معرف وجود داشت
        referral_code = validated_data.get('referral_code')
        if referral_code:
            try:
                referrer = User.objects.get(referral_code=referral_code)
                user.referred_by = referrer
                user.save()
            except User.DoesNotExist:
                pass
        
        return user

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


# class BankCardSerializer(serializers.ModelSerializer):
#     shaba_number = serializers.CharField(
#         required=False,
#         allow_null=True,
#         allow_blank=True,
#         min_length=24,
#         max_length=24,
#         error_messages={
#             "required": "شماره شبا الزامی است",
#             "blank": "شماره شبا نمی‌تواند خالی باشد",
#             "null": "شماره شبا نمی‌تواند خالی باشد",
#             "min_length": "شماره شبا باید دقیقا ۲۴ رقم باشد",
#             "max_length": "شماره شبا باید دقیقا ۲۴ رقم باشد",
#         },
#     )

#     card_number = serializers.CharField(
#         required=False,
#         allow_null=True,
#         allow_blank=True,
#         min_length=16,
#         max_length=16,
#         error_messages={
#             "required": "شماره کارت الزامی است",
#             "blank": "شماره کارت نمی‌تواند خالی باشد",
#             "null": "شماره کارت نمی‌تواند خالی باشد",
#             "min_length": "شماره کارت باید دقیقا ۱۶ رقم باشد",
#             "max_length": "شماره کارت باید دقیقا ۱۶ رقم باشد",
#         },
#     )

#     bank_name = serializers.CharField(
#         required=False,
#         allow_null=True,
#         allow_blank=True,
#         error_messages={
#             "blank": "نام بانک نمی‌تواند خالی باشد",
#         }
#     )

#     class Meta:
#         model = BankCard
#         fields = [
#             "id",
#             "card_number",
#             "shaba_number",
#             "bank_name",
#             "is_active",
#             "created_at",
#         ]
#         read_only_fields = ["id", "created_at"]

#     def validate_shaba_number(self, value):
#         if not value:
#             return value

#         if not value.isdigit():
#             raise serializers.ValidationError("شماره شبا فقط باید شامل عدد باشد")

#         if len(value) != 24:
#             raise serializers.ValidationError("شماره شبا باید دقیقا ۲۴ رقم باشد")

#         return value

#     def validate_card_number(self, value):
#         if not value:
#             return value

#         if not value.isdigit():
#             raise serializers.ValidationError("شماره کارت فقط باید شامل عدد باشد")

#         if len(value) != 16:
#             raise serializers.ValidationError("شماره کارت باید دقیقا ۱۶ رقم باشد")

#         return value

#     def validate(self, attrs):
#         card_number = attrs.get("card_number", getattr(self.instance, "card_number", None))
#         shaba_number = attrs.get("shaba_number", getattr(self.instance, "shaba_number", None))

#         if not card_number and not shaba_number:
#             raise serializers.ValidationError("حداقل شماره کارت یا شماره شبا الزامی است")

#         if shaba_number:
#             qs = BankCard.objects.filter(shaba_number=shaba_number)
#             if self.instance:
#                 qs = qs.exclude(pk=self.instance.pk)
#             if qs.exists():
#                 raise serializers.ValidationError(
#                     {"shaba_number": "این شماره شبا قبلاً ثبت شده است"}
#                 )

#         if card_number:
#             qs = BankCard.objects.filter(card_number=card_number)
#             if self.instance:
#                 qs = qs.exclude(pk=self.instance.pk)
#             if qs.exists():
#                 raise serializers.ValidationError(
#                     {"card_number": "این شماره کارت قبلاً ثبت شده است"}
#                 )

#         return attrs


# accounts/serializers.py - اضافه کنید

# accounts/serializers.py

# =============================================
# VerifyIBANSerializer - اصلاح شده
# =============================================

class VerifyIBANSerializer(serializers.Serializer):
    shaba_number = serializers.CharField(
        required=True,
        min_length=24,
        max_length=24,
        error_messages={
            "required": "شماره شبا الزامی است",
            "blank": "شماره شبا نمی‌تواند خالی باشد",
            "null": "شماره شبا نمی‌تواند خالی باشد",
            "min_length": "شماره شبا باید دقیقاً ۲۴ رقم باشد",
            "max_length": "شماره شبا باید دقیقاً ۲۴ رقم باشد",
        }
    )
    
    def validate_shaba_number(self, value):  # ✅ تغییر از validate_iban به validate_shaba_number
        if not value:
            raise serializers.ValidationError("شماره شبا نمی‌تواند خالی باشد")
        
        # حذف فاصله‌ها و خط تیره
        value = str(value).replace(" ", "").replace("-", "")
        
        # بررسی اینکه با IR شروع شده یا نه
        has_ir = value.startswith("IR")
        
        # حذف IR اگر وجود داشته باشد
        if has_ir:
            value = value[2:]
        
        # بررسی عددی بودن
        if not value.isdigit():
            raise serializers.ValidationError("شماره شبا فقط باید شامل عدد باشد")
        
        if len(value) != 24:
            raise serializers.ValidationError("شماره شبا باید دقیقاً ۲۴ رقم باشد")
        
        # برگرداندن با IR
        return f"IR{value}"


# accounts/serializers.py - جایگزین کنید

# accounts/serializers.py - بخش BankCardSerializer (همان است)

# accounts/serializers.py - اصلاح BankCardSerializer بدون تغییر مدل

from rest_framework import serializers
from .models import BankCard
from .jibit import get_full_iban_info

# accounts/serializers.py - اصلاح BankCardSerializer با owner_full_name

from rest_framework import serializers
from .models import BankCard
from .jibit import get_full_iban_info


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
    
    # فیلدهای جدید (از Jibit گرفته میشن)
    owner_full_name = serializers.SerializerMethodField()  # تغییر نام به owner_full_name
    deposit_number = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()

    class Meta:
        model = BankCard
        fields = [
            "id",
            "card_number",
            "shaba_number",
            "bank_name",
            "is_active",
            "created_at",
            "owner_full_name",  # تغییر نام
            "deposit_number",
            "status",
        ]
        read_only_fields = ["id", "created_at"]

    def get_iban_info_from_jibit(self, obj):
        """دریافت اطلاعات شبا از Jibit با کش کردن"""
        # اگر اطلاعات قبلاً کش شده، برگردان
        if hasattr(obj, '_cached_iban_info'):
            return obj._cached_iban_info
        
        try:
            if obj.shaba_number:
                # اضافه کردن IR اگر نداره
                iban = obj.shaba_number
                if not iban.startswith('IR'):
                    iban = f"IR{iban}"
                
                iban_info = get_full_iban_info(iban)
                
                # کش کردن برای استفاده‌های بعدی
                obj._cached_iban_info = iban_info
                
                return iban_info
                
        except Exception as e:
            print(f"❌ Error getting IBAN info for {obj.shaba_number}: {e}")
            return None
        
        return None

    def get_owner_full_name(self, obj):  # تغییر نام متد
        """دریافت نام کامل صاحب حساب"""
        iban_info = self.get_iban_info_from_jibit(obj)
        if iban_info:
            return iban_info.get('owner_full_name', '')
        return None

    def get_deposit_number(self, obj):
        """دریافت شماره حساب"""
        iban_info = self.get_iban_info_from_jibit(obj)
        if iban_info:
            return iban_info.get('deposit_number', '')
        return None

    def get_status(self, obj):
        """دریافت وضعیت شبا"""
        iban_info = self.get_iban_info_from_jibit(obj)
        if iban_info:
            return iban_info.get('status', '')
        return None

    def validate_shaba_number(self, value):
        if not value:
            return value

        value = value.replace(" ", "").replace("-", "")
        
        if value.startswith("IR"):
            value = value[2:]

        if not value.isdigit():
            raise serializers.ValidationError("شماره شبا فقط باید شامل عدد باشد")

        if len(value) != 24:
            raise serializers.ValidationError("شماره شبا باید دقیقا ۲۴ رقم باشد")

        return f"IR{value}"

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



class VerifyIBANSerializer(serializers.Serializer):
    shaba_number = serializers.CharField(
        required=True,
        min_length=24,
        max_length=24,
        error_messages={
            "required": "شماره شبا الزامی است",
            "blank": "شماره شبا نمی‌تواند خالی باشد",
            "null": "شماره شبا نمی‌تواند خالی باشد",
            "min_length": "شماره شبا باید دقیقاً ۲۴ رقم باشد",
            "max_length": "شماره شبا باید دقیقاً ۲۴ رقم باشد",
        }
    )
    
    def validate_shaba_number(self, value):
        if not value:
            raise serializers.ValidationError("شماره شبا نمی‌تواند خالی باشد")
        
        # حذف فاصله‌ها و خط تیره
        value = str(value).replace(" ", "").replace("-", "")
        
        # بررسی اینکه با IR شروع شده یا نه
        has_ir = value.startswith("IR")
        
        # حذف IR اگر وجود داشته باشد
        if has_ir:
            value = value[2:]
        
        # بررسی عددی بودن
        if not value.isdigit():
            raise serializers.ValidationError("شماره شبا فقط باید شامل عدد باشد")
        
        if len(value) != 24:
            raise serializers.ValidationError("شماره شبا باید دقیقاً ۲۴ رقم باشد")
        
        # برگرداندن با IR
        return f"IR{value}"

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
    
    
    # accounts/serializers.py - سریالایزرهای تیکت اصلاح شده

from rest_framework import serializers
from django.core.validators import FileExtensionValidator
from .models import Ticket, TicketCategory, TicketMessage


class TicketCategorySerializer(serializers.ModelSerializer):
    """سریالایزر دسته‌بندی تیکت"""
    
    class Meta:
        model = TicketCategory
        fields = ['id', 'name', 'slug', 'description', 'is_active']
        read_only_fields = ['id', 'slug']


class TicketMessageSerializer(serializers.ModelSerializer):
    """سریالایزر پیام تیکت"""
    
    user_name = serializers.SerializerMethodField()
    user_mobile = serializers.SerializerMethodField()
    is_owner = serializers.SerializerMethodField()
    attachment_url = serializers.SerializerMethodField()
    attachment_name = serializers.SerializerMethodField()
    
    created_at_fa = serializers.SerializerMethodField()
    created_at_time = serializers.SerializerMethodField()
    created_at_full = serializers.SerializerMethodField()
    
    class Meta:
        model = TicketMessage
        fields = [
            'id', 'ticket', 'user', 'user_name', 'user_mobile',
            'message', 'attachment', 'attachment_url', 'attachment_name',
            'is_admin', 'is_read', 'read_at', 
            'created_at', 'created_at_fa', 'created_at_time', 'created_at_full',
            'updated_at', 'is_owner'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at', 'is_read', 'read_at']
    
    def get_user_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}".strip() or obj.user.mobile
    
    def get_user_mobile(self, obj):
        return obj.user.mobile
    
    def get_is_owner(self, obj):
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            return obj.user == request.user
        return False
    
    def get_attachment_url(self, obj):
        if obj.attachment:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.attachment.url)
            return obj.attachment.url
        return None
    
    def get_attachment_name(self, obj):
        if obj.attachment:
            return obj.attachment.name.split('/')[-1]
        return None
    
    def get_created_at_fa(self, obj):
        import jdatetime
        if obj.created_at:
            shamsi = jdatetime.datetime.fromgregorian(datetime=obj.created_at)
            return shamsi.strftime("%Y/%m/%d")
        return None
    
    def get_created_at_time(self, obj):
        if obj.created_at:
            return obj.created_at.strftime("%H:%M:%S")
        return None
    
    def get_created_at_full(self, obj):
        import jdatetime
        if obj.created_at:
            shamsi = jdatetime.datetime.fromgregorian(datetime=obj.created_at)
            return shamsi.strftime("%Y/%m/%d %H:%M:%S")
        return None


class TicketListSerializer(serializers.ModelSerializer):
    """سریالایزر لیست تیکت‌ها (خلاصه)"""
    
    category_name = serializers.CharField(source='category.name', read_only=True)
    user_mobile = serializers.CharField(source='user.mobile', read_only=True)
    last_message = serializers.SerializerMethodField()
    unread_messages_count = serializers.SerializerMethodField()
    last_message_user_type = serializers.SerializerMethodField()
    status_display = serializers.SerializerMethodField()
    priority_display = serializers.SerializerMethodField()
    
    class Meta:
        model = Ticket
        fields = [
            'id', 'tracking_code', 'title', 'category', 'category_name',
            'status', 'status_display', 'priority', 'priority_display',
            'user', 'user_mobile', 'created_at', 'updated_at',
            'last_activity_at', 'last_message', 'last_message_user_type',
            'unread_messages_count', 'auto_resolved'
        ]
        read_only_fields = ['id', 'tracking_code', 'created_at', 'updated_at']
    
    def get_last_message(self, obj):
        last_msg = obj.messages.last()
        if last_msg:
            return {
                'message': last_msg.message[:100] + ('...' if len(last_msg.message) > 100 else ''),
                'created_at': last_msg.created_at,
                'is_admin': last_msg.is_admin,
                'user_name': f"{last_msg.user.first_name} {last_msg.user.last_name}".strip() or last_msg.user.mobile
            }
        return None
    
    def get_unread_messages_count(self, obj):
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            return obj.messages.filter(is_read=False).exclude(user=request.user).count()
        return obj.messages.filter(is_read=False).count()
    
    def get_last_message_user_type(self, obj):
        return obj.get_last_message_user_type()
    
    def get_status_display(self, obj):
        return obj.get_status_display()
    
    def get_priority_display(self, obj):
        return obj.get_priority_display()


class TicketDetailSerializer(serializers.ModelSerializer):
    """سریالایزر جزئیات تیکت"""
    
    category_name = serializers.CharField(source='category.name', read_only=True)
    user_full_name = serializers.SerializerMethodField()
    user_mobile = serializers.CharField(source='user.mobile', read_only=True)
    messages = TicketMessageSerializer(many=True, read_only=True)
    unread_messages_count = serializers.SerializerMethodField()
    can_edit = serializers.SerializerMethodField()
    can_close = serializers.SerializerMethodField()
    status_display = serializers.SerializerMethodField()
    priority_display = serializers.SerializerMethodField()
    last_message_user_type = serializers.SerializerMethodField()
    attachment_url = serializers.SerializerMethodField()
    attachment_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Ticket
        fields = [
            'id', 'tracking_code', 'user', 'user_full_name', 'user_mobile',
            'category', 'category_name', 'title', 'description',
            'status', 'status_display', 'priority', 'priority_display',
            'attachment', 'attachment_url', 'attachment_name',
            'created_at', 'updated_at', 'resolved_at', 'closed_at',
            'last_activity_at', 'messages', 'unread_messages_count',
            'can_edit', 'can_close', 'auto_resolved',
            'last_message_user_type'
        ]
        read_only_fields = [
            'id', 'tracking_code', 'user', 'created_at', 'updated_at',
            'resolved_at', 'closed_at', 'auto_resolved'
        ]
    
    def get_user_full_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}".strip() or obj.user.mobile
    
    def get_unread_messages_count(self, obj):
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            return obj.messages.filter(is_read=False).exclude(user=request.user).count()
        return obj.messages.filter(is_read=False).count()
    
    def get_can_edit(self, obj):
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            return obj.can_user_edit(request.user)
        return False
    
    def get_can_close(self, obj):
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            return obj.can_user_close(request.user)
        return False
    
    def get_status_display(self, obj):
        return obj.get_status_display()
    
    def get_priority_display(self, obj):
        return obj.get_priority_display()
    
    def get_last_message_user_type(self, obj):
        return obj.get_last_message_user_type()
    
    def get_attachment_url(self, obj):
        if obj.attachment:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.attachment.url)
            return obj.attachment.url
        return None
    
    def get_attachment_name(self, obj):
        if obj.attachment:
            return obj.attachment.name.split('/')[-1]
        return None


class TicketCreateSerializer(serializers.ModelSerializer):
    """سریالایزر ایجاد تیکت جدید"""
    
    class Meta:
        model = Ticket
        fields = ['title', 'description', 'category', 'priority', 'attachment']
    
    def validate_title(self, value):
        value = value.strip()
        min_length = 5
        if len(value) < min_length:
            raise serializers.ValidationError(
                f"عنوان باید حداقل {min_length} کاراکتر باشد (شما {len(value)} کاراکتر وارد کردید)"
            )
        if len(value) > 200:
            raise serializers.ValidationError(
                f"عنوان نباید بیشتر از ۲۰۰ کاراکتر باشد (شما {len(value)} کاراکتر وارد کردید)"
            )
        return value
    
    def validate_description(self, value):
        value = value.strip()
        min_length = 10
        if len(value) < min_length:
            raise serializers.ValidationError(
                f"توضیحات باید حداقل {min_length} کاراکتر باشد (شما {len(value)} کاراکتر وارد کردید)"
            )
        return value
    
    def validate_attachment(self, value):
        if value:
            # بررسی حجم فایل (حداکثر ۱۰ مگابایت)
            if value.size > 10 * 1024 * 1024:
                raise serializers.ValidationError("حجم فایل نباید بیشتر از ۱۰ مگابایت باشد")
            
            # لیست فرمت‌های مجاز
            allowed_extensions = [
                'jpg', 'jpeg', 'png', 'gif', 'bmp', 'svg',
                'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx',
                'zip', 'rar', '7z', 'txt', 'csv', 'json', 'xml'
            ]
            ext = value.name.split('.')[-1].lower()
            if ext not in allowed_extensions:
                raise serializers.ValidationError(
                    f"نوع فایل مجاز نیست. فرمت‌های مجاز: {', '.join(allowed_extensions)}"
                )
        return value


# accounts/serializers.py - اصلاح کامل TicketMessageCreateSerializer

class TicketMessageCreateSerializer(serializers.ModelSerializer):
    """سریالایزر ایجاد پیام جدید - اصلاح شده"""
    
    message = serializers.CharField(
        required=False,  # ✅ الزامی نیست
        allow_blank=True,  # ✅ خالی مجاز است
        allow_null=True,  # ✅ null مجاز است
        error_messages={
            'blank': 'متن پیام نمی‌تواند خالی باشد',
            'null': 'متن پیام نمی‌تواند خالی باشد',
        }
    )
    
    attachment = serializers.FileField(
        required=False,  # ✅ الزامی نیست
        allow_null=True,
        error_messages={
            'invalid': 'فایل ضمیمه نامعتبر است',
        }
    )
    
    class Meta:
        model = TicketMessage
        fields = ['message', 'attachment']
    
    def validate_message(self, value):
        # اگر مقدار None یا خالی بود، اجازه بده
        if not value or not value.strip():
            return ""
        if len(value.strip()) < 3:
            raise serializers.ValidationError("متن پیام باید حداقل ۳ کاراکتر باشد")
        return value.strip()
    
    def validate_attachment(self, value):
        if value:
            # بررسی حجم فایل (حداکثر ۱۰ مگابایت)
            if value.size > 10 * 1024 * 1024:
                raise serializers.ValidationError("حجم فایل نباید بیشتر از ۱۰ مگابایت باشد")
            
            # لیست فرمت‌های مجاز
            allowed_extensions = [
                'jpg', 'jpeg', 'png', 'gif', 'bmp', 'svg',
                'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx',
                'zip', 'rar', '7z', 'txt', 'csv', 'json', 'xml'
            ]
            ext = value.name.split('.')[-1].lower()
            if ext not in allowed_extensions:
                raise serializers.ValidationError(
                    f"نوع فایل مجاز نیست. فرمت‌های مجاز: {', '.join(allowed_extensions)}"
                )
        return value
    
    def validate(self, attrs):
        """اعتبارسنجی کلی: حداقل یکی از message یا attachment باید وجود داشته باشد"""
        message = attrs.get('message', '')
        attachment = attrs.get('attachment')
        
        if not message and not attachment:
            raise serializers.ValidationError(
                {"non_field_errors": ["حداقل یکی از متن پیام یا فایل ضمیمه باید ارسال شود"]}
            )
        
        return attrs
    

class TicketUpdateSerializer(serializers.ModelSerializer):
    """سریالایزر بروزرسانی تیکت (فقط کاربر)"""
    
    class Meta:
        model = Ticket
        fields = ['title', 'description', 'priority']
    
    def validate_title(self, value):
        value = value.strip()
        min_length = 5
        if len(value) < min_length:
            raise serializers.ValidationError(
                f"عنوان باید حداقل {min_length} کاراکتر باشد (شما {len(value)} کاراکتر وارد کردید)"
            )
        if len(value) > 200:
            raise serializers.ValidationError(
                f"عنوان نباید بیشتر از ۲۰۰ کاراکتر باشد (شما {len(value)} کاراکتر وارد کردید)"
            )
        return value
    
    def validate_description(self, value):
        value = value.strip()
        min_length = 10
        if len(value) < min_length:
            raise serializers.ValidationError(
                f"توضیحات باید حداقل {min_length} کاراکتر باشد (شما {len(value)} کاراکتر وارد کردید)"
            )
        return value