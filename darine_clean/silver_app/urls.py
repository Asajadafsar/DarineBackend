from django.urls import path
from .views import (
    DepositMoney, ReferralDashboardView, SilverDashboardAPI, SilverProductListView, SilverWalletAPI, BuySilver, 
    SellSilver, SilverDeposit, BankCardAPI, SubmitPhysicalDelivery, UserReportsView, WithdrawMoney
)

urlpatterns = [
    path('dashboard/', SilverDashboardAPI.as_view()),
    path('wallet/', SilverWalletAPI.as_view()),
    path('buy/', BuySilver.as_view()),
    path('sell/', SellSilver.as_view()),
    path('deposit/', SilverDeposit.as_view()),
    path('cards/', BankCardAPI.as_view()),
    path('deposit/', DepositMoney.as_view(), name='silver-deposit'),
    path('withdraw/', WithdrawMoney.as_view(), name='silver-withdraw'),
    path('physical-products/', SilverProductListView.as_view(), name='silver_products'),
    path('physical-delivery/submit/', SubmitPhysicalDelivery.as_view(), name='submit_delivery'),
    path('reports/', UserReportsView.as_view(), name='user_reports'),
    path('referral/dashboard/', ReferralDashboardView.as_view(), name='referral-dashboard'),
    
]