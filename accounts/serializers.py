from rest_framework import serializers
from .models import BankCard, User, OTPRequest
from django.contrib.auth.hashers import make_password

class SendOTPSerializer(serializers.Serializer):
    mobile = serializers.CharField(max_length=11)

class VerifyOTPSerializer(serializers.Serializer):
    mobile = serializers.CharField(max_length=11)
    code = serializers.CharField(max_length=6)

class CompleteRegistrationSerializer(serializers.Serializer):
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True)
    national_code = serializers.CharField(max_length=10)
    card_number = serializers.CharField(max_length=16, required=False)
    birth_year = serializers.IntegerField()
    birth_month = serializers.IntegerField()
    birth_day = serializers.IntegerField()
    referral_code = serializers.CharField(required=False, allow_blank=True)


    class Meta:
        model = User
        fields = ['national_code', 'card_number', 'password', 'referral_code', 'birth_year', 'birth_month', 'birth_day']

    # def validate_password(self, value):
    #     return make_password(value) # هش کردن پسورد

class ResetPasswordOTPSerializer(serializers.Serializer):
    mobile = serializers.CharField(max_length=11)

class ResetPasswordConfirmSerializer(serializers.Serializer):
    mobile = serializers.CharField(max_length=11)
    code = serializers.CharField(max_length=6)
    new_password = serializers.CharField(write_only=True, min_length=8)

class BankCardSerializer(serializers.ModelSerializer):
    class Meta:
        model = BankCard
        fields = ['id', 'card_number', 'bank_name', 'is_active']
        read_only_fields = ['id']