from django.urls import path


from .views import (
    AssetValueAPIView,
    CoinPriceAPIView,
    GoldAnnouncementAPIView,
    GoldAnnouncementMarkAllReadAPIView,
    GoldAnnouncementMarkReadAPIView,
    GoldBannerListAPIView,
    GoldDashboardAPIView,
    GoldDepositInfoAPIView,
    GoldLimitOrderCreateAPIView,
    GoldLimitOrderListAPIView,
    GoldPriceAPIView,
    GoldStatisticsAPIView,
    LatestPriceAPIView,
    OrderDetailAPIView,
    ParsianPriceAPIView,
    PhysicalOrderAPIView,
    PhysicalOrderNoAddressAPIView,
    PriceAlertLogAPIView,
    PriceAlertReportAPIView,
    ProductCategoryListAPIView,
    ProductDetailAPIView,
    TogglePriceAlertAPIView,
    UserAddressAPIView,
    UserAddressCreateAPIView,
    UserAddressListAPIView,
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
)

urlpatterns = [
    # DASHBOARD
    path("dashboard/", GoldDashboardAPIView.as_view()),
    path("balance/", UserBalanceAPIView.as_view()),
    path("orders/<int:pk>/", OrderDetailAPIView.as_view()),
    # GOLD
    path("buy/", BuyGoldAPIView.as_view()),
    path("sell/", SellGoldAPIView.as_view()),
    # WALLET
    path("deposit/", DepositAPIView.as_view()),
    path("withdraw/", WithdrawAPIView.as_view()),
    # PRODUCTS
    path("products/", ProductListAPIView.as_view()),
    path(
        "products/<int:product_id>/",
        ProductDetailAPIView.as_view(),
        name="product-detail",
    ),
    path("gold-limit-order/", GoldLimitOrderCreateAPIView.as_view()),
    path("prices/", LatestPriceAPIView.as_view()),
    path("gold-limit-orders/", GoldLimitOrderListAPIView.as_view()),
    path("product/categories/", ProductCategoryListAPIView.as_view()),
    path("address/<int:address_id>/", UserAddressAPIView.as_view()),
    # ORDERS
    path("orders/", OrderHistoryAPIView.as_view()),
    # GIFT CARD
    path("gift-card/order/", GiftCardOrderAPIView.as_view()),
    path("gift-card/orders/", GiftCardOrderListAPIView.as_view()),
    path("gift-card/redeem/", RedeemGiftCardAPIView.as_view()),
    path("gift-card/list/", GiftCardListAPIView.as_view()),
    # AUTO SAVING
    path("auto-saving/", AutoSavingPlanAPIView.as_view()),
    # USER ADDRESSES
    path("addresses/", UserAddressListAPIView.as_view()),
    path("address/", UserAddressCreateAPIView.as_view()),
    # REPORTS
    path("reports/", ReportsAPIView.as_view()),
    path("recent-transactions/", RecentTransactionsAPIView.as_view()),
    path("recent-deliveries/", RecentDeliveriesAPIView.as_view()),
    path("price/gold/", GoldPriceAPIView.as_view()),
    path("price/coin/", CoinPriceAPIView.as_view()),
    path("price/parsian/", ParsianPriceAPIView.as_view()),
    path("deposit/info/", GoldDepositInfoAPIView.as_view()),
    path("price-alert/", PriceAlertAPIView.as_view(), name="price-alert"),
    path("price-alerts/<int:pk>/", DeletePriceAlertAPIView.as_view()),
    # REFERRAL
    path("referral-dashboard/", ReferralDashboardAPIView.as_view()),
    path("physical-order/", PhysicalOrderNoAddressAPIView.as_view()),
    path("asset-value/", AssetValueAPIView.as_view(), name="asset-value"),
    path("statistics/", GoldStatisticsAPIView.as_view(), name="gold-statistics"),
    # gold_app/urls.py
    path("banners/", GoldBannerListAPIView.as_view(), name="gold-banners"),
    path(
        "announcements/", GoldAnnouncementAPIView.as_view(), name="gold-announcements"
    ),
    path(
        "announcements/mark-all-read/", GoldAnnouncementMarkAllReadAPIView.as_view(), name="gold-announcements"
    ),
    # path(
    #     "announcements/mark-read/", GoldAnnouncementMarkReadAPIView.as_view(), name="gold-announcements"
    # ),
    path("chart/", GoldChartAPIView.as_view(), name="gold-chart"),
    path("price-alert/", PriceAlertAPIView.as_view()),
    path("price-alert/<int:pk>/", DeletePriceAlertAPIView.as_view()),
    path("price-alert/<int:pk>/toggle/", TogglePriceAlertAPIView.as_view()),
    path("price-alert/report/", PriceAlertReportAPIView.as_view()),
    path("price-alert/logs/", PriceAlertLogAPIView.as_view()),
]
