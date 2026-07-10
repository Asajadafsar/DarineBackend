from django.urls import path


from .views import (
    AssetValueAPIView,
    BuyGoldCalculateAPIView,
    CoinPriceAPIView,
    GoldAnnouncementAPIView,
    GoldAnnouncementMarkAllReadAPIView,
    GoldAnnouncementMarkReadAPIView,
    GoldBannerListAPIView,
    GoldDashboardAPIView,
    GoldDepositInfoAPIView,
    GoldLimitOrderCancelAPIView,
    GoldLimitOrderCreateAPIView,
    GoldLimitOrderDetailAPIView,
    GoldLimitOrderExecuteAPIView,
    GoldLimitOrderListAPIView,
    GoldLimitOrderPartialUpdateAPIView,
    GoldLimitOrderUpdateAPIView,
    GoldPriceAPIView,
    GoldReferralInfoAPIView,
    GoldShortOrderCloseAPIView,
    GoldShortOrderCreateAPIView,
    GoldShortOrderDetailAPIView,
    GoldShortOrderHistoryAPIView,
    GoldShortOrderLiquidateAPIView,
    GoldShortOrderListAPIView,
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
    SellGoldCalculateAPIView,
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
    
    path("referral-dashboard/", GoldReferralInfoAPIView.as_view()),
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
    path(
    "sell/calculate/",
    SellGoldCalculateAPIView.as_view(),
    name="sell-gold-calculate",
),
    path(
    "buy/calculate/",
    BuyGoldCalculateAPIView.as_view(),
    name="buy-gold-calculate",
),
    path("chart/", GoldChartAPIView.as_view(), name="gold-chart"),
    path("price-alert/", PriceAlertAPIView.as_view()),
    path("price-alert/<int:pk>/", DeletePriceAlertAPIView.as_view()),
    path("price-alert/<int:pk>/toggle/", TogglePriceAlertAPIView.as_view()),
    path("price-alert/report/", PriceAlertReportAPIView.as_view()),
    path("price-alert/logs/", PriceAlertLogAPIView.as_view()),
    # gold_app/urls.py
    path('limit-orders/<int:pk>/update/', GoldLimitOrderUpdateAPIView.as_view(), name='gold-limit-order-update'),
    
    # ویرایش جزئی سفارش (PATCH)
    path('limit-orders/<int:pk>/partial-update/', GoldLimitOrderPartialUpdateAPIView.as_view(), name='gold-limit-order-partial-update'),

    path('short/create/', GoldShortOrderCreateAPIView.as_view(), name='gold-short-create'),
    path('short/', GoldShortOrderListAPIView.as_view(), name='gold-short-list'),
    path('short/<int:pk>/', GoldShortOrderDetailAPIView.as_view(), name='gold-short-detail'),
    path('short/<int:pk>/close/', GoldShortOrderCloseAPIView.as_view(), name='gold-short-close'),
    path('short/<int:pk>/liquidate/', GoldShortOrderLiquidateAPIView.as_view(), name='gold-short-liquidate'),
    path('short/<int:pk>/history/', GoldShortOrderHistoryAPIView.as_view(), name='gold-short-history'),
    path('limit-orders/create/', GoldLimitOrderCreateAPIView.as_view(), name='gold-limit-order-create'),
    path('limit-orders/', GoldLimitOrderListAPIView.as_view(), name='gold-limit-order-list'),
    path('limit-orders/<int:pk>/', GoldLimitOrderDetailAPIView.as_view(), name='gold-limit-order-detail'),
    path('limit-orders/<int:pk>/cancel/', GoldLimitOrderCancelAPIView.as_view(), name='gold-limit-order-cancel'),
    path('limit-orders/<int:pk>/execute/', GoldLimitOrderExecuteAPIView.as_view(), name='gold-limit-order-execute'),
]

