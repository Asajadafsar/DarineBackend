from rest_framework import serializers
from .models import User, BankCard
from rest_framework import serializers
from .models import CooperationRequest
import jdatetime

class SendOTPSerializer(serializers.Serializer):
    mobile = serializers.CharField(max_length=11)


class VerifyOTPSerializer(serializers.Serializer):
    mobile = serializers.CharField(max_length=11)
    code = serializers.CharField(max_length=6)


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
    
    


class BankCardSerializer(serializers.ModelSerializer):

    class Meta:
        model = BankCard
        fields = [
            "id",
            "card_number",
            "bank_name",
            "is_active"
        ]


class ChangeMobileRequestSerializer(serializers.Serializer):
    new_mobile = serializers.CharField(max_length=11)


class ChangeMobileConfirmSerializer(serializers.Serializer):
    new_mobile = serializers.CharField(max_length=11)
    code = serializers.CharField(max_length=6)





class CooperationRequestSerializer(serializers.ModelSerializer):

    class Meta:
        model = CooperationRequest
        fields = [
            "id",
            "organization_name",
            "full_name",
            "email",
            "mobile",
            "description",
        ]

    def validate_mobile(self, value):

        if not value.isdigit():
            raise serializers.ValidationError("شماره همراه نامعتبر است")

        if len(value) < 10:
            raise serializers.ValidationError("شماره همراه کوتاه است")

        return value