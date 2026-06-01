# =========================================================
# SILVER URLS
# =========================================================

from django.urls import path

from .views import (

    # =========================
    # DASHBOARD & BALANCE
    # =========================
    SilverDashboardAPIView,
    SilverUserBalanceAPIView,

    # =========================
    # CHART
    # =========================
    SilverChartAPIView,

    # =========================
    # BUY / SELL
    # =========================
    BuySilverAPIView,
    SellSilverAPIView,

    # =========================
    # WALLET
    # =========================
    DepositAPIView,
    WithdrawAPIView,

    # =========================
    # PRODUCTS & ORDERS
    # =========================
    SilverProductListAPIView,
    SilverPhysicalOrderAPIView,
    SilverUserAddressListAPIView,
    SilverOrderHistoryAPIView,

    # =========================
    # REPORTS
    # =========================
    SilverReportsAPIView,

    # =========================
    # RECENT
    # =========================
    SilverRecentTransactionsAPIView,
    SilverRecentDeliveriesAPIView,

    # =========================
    # REFERRAL
    # =========================
    SilverReferralDashboardAPIView,

)

urlpatterns = [

    # =====================================================
    # DASHBOARD & BALANCE
    # =====================================================
    path("dashboard/", SilverDashboardAPIView.as_view(), name="silver-dashboard"),
    path("balance/", SilverUserBalanceAPIView.as_view(), name="silver-balance"),

    # =====================================================
    # CHART
    # =====================================================
    path("chart/", SilverChartAPIView.as_view(), name="silver-chart"),

    # =====================================================
    # BUY / SELL
    # =====================================================
    path("buy/", BuySilverAPIView.as_view(), name="silver-buy"),
    path("sell/", SellSilverAPIView.as_view(), name="silver-sell"),

    # =====================================================
    # WALLET
    # =====================================================
    path("wallet/deposit/", DepositAPIView.as_view(), name="silver-deposit"),
    path("wallet/withdraw/", WithdrawAPIView.as_view(), name="silver-withdraw"),

    # =====================================================
    # PRODUCTS & ORDERS
    # =====================================================
    path("products/", SilverProductListAPIView.as_view(), name="silver-products"),
    path("order/", SilverPhysicalOrderAPIView.as_view(), name="silver-order"),
    path("addresses/", SilverUserAddressListAPIView.as_view(), name="silver-addresses"),
    path("orders/", SilverOrderHistoryAPIView.as_view(), name="silver-orders"),

    # =====================================================
    # REPORTS
    # =====================================================
    path("reports/", SilverReportsAPIView.as_view(), name="silver-reports"),

    # =====================================================
    # RECENT DATA
    # =====================================================
    path("recent/transactions/", SilverRecentTransactionsAPIView.as_view(), name="silver-recent-transactions"),
    path("recent/deliveries/", SilverRecentDeliveriesAPIView.as_view(), name="silver-recent-deliveries"),

    # =====================================================
    # REFERRAL
    # =====================================================
    path("referral/", SilverReferralDashboardAPIView.as_view(), name="silver-referral"),
]