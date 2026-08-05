# accounts/urls.py

from django.urls import path

from .views import (
    CooperationRequestAPIView,
    MarketPricesAPIView,
    RegisterStepOne,
    RegisterStepTwo,
    RegisterStepThree,
    LoginWithPassword,
    LoginWithOTP,
    RefreshTokenView,
    LogoutView,
    ProfileView,
    TicketCategoriesView,
    TicketDetailView,
    TicketListCreateView,
    TicketMessagesView,
    TicketTrackingView,
    TicketUnreadCountView,
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
    path("send-otp/", RegisterStepOne.as_view()),
    path("verify-otp/", RegisterStepTwo.as_view()),
    path("complete-register/", RegisterStepThree.as_view()),
    # login
    path("login/password/", LoginWithPassword.as_view()),
    path("login/otp/", LoginWithOTP.as_view()),
    # auth
    path("token/refresh/", RefreshTokenView.as_view()),
    path("logout/", LogoutView.as_view()),
    # profile
    path("profile/", ProfileView.as_view()),
    # cards
    path("cards/", UserBankCards.as_view()),
    path("market/prices/", MarketPricesAPIView.as_view(), name="market-prices"),
    path("cards/<int:card_id>/", DeleteBankCard.as_view()),
    # reset password
    path("reset-password/request/", ResetPasswordRequest.as_view()),
    path("reset-password/verify/", ResetPasswordVerify.as_view()),
    path("reset-password/complete/", ResetPasswordComplete.as_view()),
    # change mobile
    path("change-mobile/request/", ChangeMobileRequest.as_view()),
    path("change-mobile/confirm/", ChangeMobileConfirm.as_view()),
    path("cooperation-request/", CooperationRequestAPIView.as_view()),
    path('tickets/categories/', TicketCategoriesView.as_view(), name='ticket-categories'),
    path('tickets/', TicketListCreateView.as_view(), name='ticket-list-create'),
    path('tickets/<int:ticket_id>/', TicketDetailView.as_view(), name='ticket-detail'),
    path('tickets/<int:ticket_id>/messages/', TicketMessagesView.as_view(), name='ticket-messages'),
    path('tickets/unread/count/', TicketUnreadCountView.as_view(), name='ticket-unread-count'),
    path('tickets/tracking/<str:tracking_code>/', TicketTrackingView.as_view(), name='ticket-tracking'),
]
