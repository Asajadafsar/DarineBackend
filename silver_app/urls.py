from django.urls import path
from . import views

urlpatterns = [

    # =========================
    # BALANCE & CHART
    # =========================
    path('balance/', views.SilverBalanceAPIView.as_view()),
    path('chart/', views.SilverChartAPIView.as_view()),

    # =========================
    # TRADE
    # =========================
    path('buy/', views.BuySilverAPIView.as_view()),
    path('sell/', views.SellSilverAPIView.as_view()),

    # =========================
    # WALLET
    # =========================
    path('deposit/', views.DepositSilverAPIView.as_view()),
    path('withdraw/', views.WithdrawSilverAPIView.as_view()),

    # =========================
    # PRODUCT
    # =========================
    path('products/', views.SilverProductListAPIView.as_view()),

    # =========================
    # CART & CHECKOUT
    # =========================
    path('cart/', views.SilverCartAPIView.as_view()),
    path('checkout/', views.SilverCheckoutAPIView.as_view()),

    # =========================
    # ORDERS
    # =========================
    path('orders/', views.SilverOrderHistoryAPIView.as_view()),

    # =========================
    # TRANSACTIONS
    # =========================
    path('recent-transactions/', views.SilverRecentTransactionsAPIView.as_view()),

    # =========================
    # REFERRAL
    # =========================
    path('referral-dashboard/', views.SilverReferralDashboardAPIView.as_view()),
    # =========================
# REPORTS
# =========================
path('reports/', views.SilverReportsAPIView.as_view()),

# =========================
# RECENT DELIVERIES
# =========================
path(
    'recent-deliveries/',
    views.SilverRecentDeliveriesAPIView.as_view()
),
]