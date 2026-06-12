# accounts/urls.py

from django.urls import path

from .views import (

    CooperationRequestAPIView,
    RegisterStepOne,
    RegisterStepTwo,
    RegisterStepThree,

    LoginWithPassword,
    LoginWithOTP,

    RefreshTokenView,
    LogoutView,

    ProfileView,

    UserBankCards,
    DeleteBankCard,

    ResetPasswordRequest,
    ResetPasswordVerify,
    ResetPasswordComplete,

    ChangeMobileRequest,
    ChangeMobileConfirm,
)

urlpatterns = [

    # register
    path(
        'send-otp/',
        RegisterStepOne.as_view()
    ),

    path(
        'verify-otp/',
        RegisterStepTwo.as_view()
    ),

    path(
        'complete-register/',
        RegisterStepThree.as_view()
    ),

    # login
    path(
        'login/password/',
        LoginWithPassword.as_view()
    ),

    path(
        'login/otp/',
        LoginWithOTP.as_view()
    ),

    # auth
    path(
        'token/refresh/',
        RefreshTokenView.as_view()
    ),

    path(
        'logout/',
        LogoutView.as_view()
    ),

    # profile
    path(
        'profile/',
        ProfileView.as_view()
    ),

    # cards
    path(
        'cards/',
        UserBankCards.as_view()
    ),

    path(
        'cards/<int:card_id>/',
        DeleteBankCard.as_view()
    ),

    # reset password
    path(
        'reset-password/request/',
        ResetPasswordRequest.as_view()
    ),

    path(
        'reset-password/verify/',
        ResetPasswordVerify.as_view()
    ),

    path(
        'reset-password/complete/',
        ResetPasswordComplete.as_view()
    ),

    # change mobile
    path(
        'change-mobile/request/',
        ChangeMobileRequest.as_view()
    ),

    path(
        'change-mobile/confirm/',
        ChangeMobileConfirm.as_view()
    ),
    path("cooperation-request/", CooperationRequestAPIView.as_view()),
]

