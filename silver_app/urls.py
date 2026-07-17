# =========================================================
# SILVER URLS
# =========================================================

from django.urls import path

from .views import (
    # =========================
    # DASHBOARD & BALANCE
    # =========================
    BuySilverCalculateAPIView,
    SellSilverCalculateAPIView,
    SilverAnnouncementAPIView,
    SilverAnnouncementMarkAllReadAPIView,
    SilverAnnouncementMarkReadAPIView,
    SilverAssetValueAPIView,
    SilverBannerListAPIView,
    SilverDashboardAPIView,
    SilverDepositInfoAPIView,
    SilverLimitOrderBuyConfirmAPIView,
    SilverLimitOrderCancelAPIView,
    SilverLimitOrderCreateAPIView,
    SilverLimitOrderDetailAPIView,
    SilverLimitOrderExecuteAPIView,
    SilverLimitOrderListAPIView,
    SilverLimitOrderSellConfirmAPIView,
    SilverLimitOrderUpdateAPIView,
    SilverOrderDetailAPIView,
    SilverOrderNoAddressAPIView,
    SilverProductCategoryListAPIView,
    SilverProductDetailAPIView,
    SilverReferralInfoAPIView,
    SilverStatisticsAPIView,
    SilverUserAddressAPIView,
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
    SilverUserAddressCreateAPIView,
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
    # path("order/", SilverPhysicalOrderAPIView.as_view(), name="silver-order"),
    path("order/", SilverOrderNoAddressAPIView.as_view(), name="silver-order"),

    path("product/categories/", SilverProductCategoryListAPIView.as_view()),
    path("deposit/info/", SilverDepositInfoAPIView.as_view()),
    path("addresses/", SilverUserAddressListAPIView.as_view(), name="silver-addresses"),
    path("orders/", SilverOrderHistoryAPIView.as_view(), name="silver-orders"),
    path(
        "address/",
        SilverUserAddressCreateAPIView.as_view(),
        name="silver-address-create",
    ),
    path(
        "address/<int:address_id>/",
        SilverUserAddressAPIView.as_view(),
        name="silver-address",
    ),
    path(
        "orders/<int:order_id>/",
        SilverOrderDetailAPIView.as_view(),
        name="silver-order-detail",
    ),
    # =====================================================
    # REPORTS
    # =====================================================
    path("reports/", SilverReportsAPIView.as_view(), name="silver-reports"),
    # =====================================================
    # RECENT DATA
    # =====================================================
    path(
        "recent/transactions/",
        SilverRecentTransactionsAPIView.as_view(),
        name="silver-recent-transactions",
    ),
    path(
        "recent/deliveries/",
        SilverRecentDeliveriesAPIView.as_view(),
        name="silver-recent-deliveries",
    ),
    path(
    "buy/calculate/",
    BuySilverCalculateAPIView.as_view(),
    name="buy-silver-calculate",
),
# silver_app/urls.py


    
    path('limit-orders/create/', SilverLimitOrderCreateAPIView.as_view(), name='silver-limit-order-create'),
    path('limit-orders/', SilverLimitOrderListAPIView.as_view(), name='silver-limit-order-list'),
    path('limit-orders/<int:pk>/', SilverLimitOrderDetailAPIView.as_view(), name='silver-limit-order-detail'),
    path('limit-orders/<int:pk>/cancel/', SilverLimitOrderCancelAPIView.as_view(), name='silver-limit-order-cancel'),
    path('limit-orders/<int:pk>/execute/', SilverLimitOrderExecuteAPIView.as_view(), name='silver-limit-order-execute'),
    path('limit-orders/<int:pk>/update/', SilverLimitOrderUpdateAPIView.as_view(), name='silver-limit-order-update'),


path(
    "sell/calculate/",
    SellSilverCalculateAPIView.as_view(),
    name="sell-silver-calculate",
),
    path('limit-order/buy/confirm/', SilverLimitOrderBuyConfirmAPIView.as_view(), name='silver-limit-order-buy-confirm'),
    
    # ✅ باکس تایید فروش سفارش با قیمت نقره
    path('limit-order/sell/confirm/', SilverLimitOrderSellConfirmAPIView.as_view(), name='silver-limit-order-sell-confirm'),
    # =====================================================
    # REFERRAL
    # =====================================================
    path("referral/", SilverReferralInfoAPIView.as_view(),),
    path("asset-value/", SilverAssetValueAPIView.as_view(), name="silver-asset-value"),
    path("statistics/", SilverStatisticsAPIView.as_view(), name="silver-statistics"),
    # silver_app/urls.py
    path(
        "products/<int:product_id>/",
        SilverProductDetailAPIView.as_view(),
        name="silver-product-detail",
    ),
    path("banners/", SilverBannerListAPIView.as_view(), name="silver-banners"),
    path("chart/", SilverChartAPIView.as_view(), name="silver-chart"),
    path(
        "announcements/",
        SilverAnnouncementAPIView.as_view(),
        name="silver-announcements",
    ),
    path(
        "announcements/mark-all-read/", SilverAnnouncementMarkAllReadAPIView.as_view(), name="gold-announcements"
    ),
    # path(
    #     "announcements/mark-read/", SilverAnnouncementMarkReadAPIView.as_view(), name="gold-announcements"
    # ),
]
