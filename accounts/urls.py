from django.urls import path
from .views import DeleteBankCard, RegisterStepOne, RegisterStepTwo, RegisterStepThree , LoginWithPassword , LoginWithOTP, ResetPasswordConfirm, ResetPasswordRequest, UserBankCards

urlpatterns = [
    path('send-otp/', RegisterStepOne.as_view(), name='send_otp'),
    path('verify-otp/', RegisterStepTwo.as_view(), name='verify_otp'),
    path('complete-register/', RegisterStepThree.as_view(), name='complete_register'),
    path('login/password/', LoginWithPassword.as_view()),
    path('login/otp/', LoginWithOTP.as_view()),
    path('reset-password/request/', ResetPasswordRequest.as_view(), name='reset_password_request'),
    path('reset-password/confirm/', ResetPasswordConfirm.as_view(), name='reset_password_confirm'),
    path('cards/', UserBankCards.as_view(), name='user_cards'),
    path('cards/<int:card_id>/', DeleteBankCard.as_view(), name='delete_card'),
]
