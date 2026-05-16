from rest_framework import serializers
from .models import User, BankCard


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
            "auth_status",
        ]

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"


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