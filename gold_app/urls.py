from django.urls import path

from .views import (
    GoldDashboardAPIView,
    GoldOrderAPIView,
    LatestPriceAPIView,
    PhysicalOrderAPIView,
    UserBalanceAPIView,
    GoldChartAPIView,
    BuyGoldAPIView,
    SellGoldAPIView,
    DepositAPIView,
    WithdrawAPIView,
    ProductListAPIView,
    OrderHistoryAPIView,
    ReportsAPIView,
    RecentTransactionsAPIView,
    RecentDeliveriesAPIView,
    PriceAlertAPIView,
    DeletePriceAlertAPIView,
    ReferralDashboardAPIView,
    GiftCardOrderAPIView,
    GiftCardOrderListAPIView,
    RedeemGiftCardAPIView,
    GiftCardListAPIView,
    AutoSavingPlanAPIView,
    UserAddressesAPIView,
)

urlpatterns = [

    # DASHBOARD
    path(
        'dashboard/',
        GoldDashboardAPIView.as_view()
    ),

    path(
        'balance/',
        UserBalanceAPIView.as_view()
    ),

    path(
        'chart/',
        GoldChartAPIView.as_view()
    ),

    # GOLD
    path(
        'buy/',
        BuyGoldAPIView.as_view()
    ),

    path(
        'sell/',
        SellGoldAPIView.as_view()
    ),

    # WALLET
    path(
        'deposit/',
        DepositAPIView.as_view()
    ),

    path(
        'withdraw/',
        WithdrawAPIView.as_view()
    ),

    # PRODUCTS
    path(
        'products/',
        ProductListAPIView.as_view()
    ),
    path("gold-limit-order/", GoldOrderAPIView.as_view()),
    path("prices/", LatestPriceAPIView.as_view()),



    # ORDERS
    path(
        'orders/',
        OrderHistoryAPIView.as_view()
    ),

    # GIFT CARD
    path(
        'gift-card/order/',
        GiftCardOrderAPIView.as_view()
    ),

    path(
        'gift-card/orders/',
        GiftCardOrderListAPIView.as_view()
    ),

    path(
        'gift-card/redeem/',
        RedeemGiftCardAPIView.as_view()
    ),

    path(
        'gift-card/list/',
        GiftCardListAPIView.as_view()
    ),

    # AUTO SAVING
    path(
        'auto-saving/',
        AutoSavingPlanAPIView.as_view()
    ),

    # USER ADDRESSES
    path(
        'addresses/',
        UserAddressesAPIView.as_view()
    ),

    # REPORTS
    path(
        'reports/',
        ReportsAPIView.as_view()
    ),

    path(
        'recent-transactions/',
        RecentTransactionsAPIView.as_view()
    ),

    path(
        'recent-deliveries/',
        RecentDeliveriesAPIView.as_view()
    ),

    # ALERTS
    path(
        'price-alerts/',
        PriceAlertAPIView.as_view()
    ),

    path(
        'price-alerts/<int:pk>/',
        DeletePriceAlertAPIView.as_view()
    ),

    # REFERRAL
    path(
        'referral-dashboard/',
        ReferralDashboardAPIView.as_view()
    ),
    path(
    'physical-order/',
    PhysicalOrderAPIView.as_view()
),




]