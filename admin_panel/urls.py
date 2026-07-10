from django.urls import path
from rest_framework.routers import DefaultRouter

from admin_panel.views import (
    AdminAnalyticsViewSet,
    AdminLogViewSet,
    AnalyticsChartAPIView,
    AnalyticsPurchaseChartAPIView,
    BuySellChartAPIView,
    CategoryAdminViewSet,
    CooperationRequestAdminViewSet,
    DashboardAdminViewSet,
    DepositAdminViewSet,
    GiftCardAdminViewSet,
    GoldAdminViewSet,
    GoldAnnouncementAdminViewSet,
    GoldBalanceAdjustmentViewSet,
    GoldBankAdminViewSet,
    GoldBannerAdminViewSet,
    GoldPriceOffsetAdminViewSet,
    GoldTransactionAdminViewSet,
    OrderAdminViewSet,
    ProductAdminViewSet,
    SilverAdminViewSet,
    SilverAnnouncementAdminViewSet,
    SilverBalanceAdjustmentViewSet,
    SilverBankAdminViewSet,
    SilverBannerAdminViewSet,
    SilverDepositAdminViewSet,
    SilverOrderAdminViewSet,
    SilverPriceOffsetAdminViewSet,
    SilverProductAdminViewSet,
    SilverTransactionAdminViewSet,
    SilverWithdrawAdminViewSet,
    UserAdminViewSet,
    SilverBalanceWithdrawalViewSet,
    WithdrawAdminViewSet,
    GoldBalanceWithdrawalViewSet,
)

router = DefaultRouter()

# =========================================================
# USERS
# =========================================================

router.register(
    r"users",
    UserAdminViewSet,
    basename="users",
)

# =========================================================
# PRODUCTS
# =========================================================

router.register(
    r"products",
    ProductAdminViewSet,
    basename="products",
)

router.register(
    r"categories",
    CategoryAdminViewSet,
    basename="categories",
)

router.register(
    r"silver-products",
    SilverProductAdminViewSet,
    basename="silver-products",
)

# =========================================================
# ORDERS
# =========================================================

router.register(
    r"orders",
    OrderAdminViewSet,
    basename="orders",
)

router.register(
    r"silver-orders",
    SilverOrderAdminViewSet,
    basename="silver-orders",
)

# =========================================================
# GIFT CARD
# =========================================================

router.register(
    r"gift-cards",
    GiftCardAdminViewSet,
    basename="gift-cards",
)

# =========================================================
# DASHBOARD
# =========================================================

router.register(
    r"dashboard",
    DashboardAdminViewSet,
    basename="dashboard",
)

# =========================================================
# BANK
# =========================================================

router.register(
    r"gold-bank",
    GoldBankAdminViewSet,
    basename="gold-bank",
)

router.register(
    r"silver-bank",
    SilverBankAdminViewSet,
    basename="silver-bank",
)

# =========================================================
# COOPERATION
# =========================================================

router.register(
    r"CooperationRequest",
    CooperationRequestAdminViewSet,
    basename="CooperationRequest",
)

# =========================================================
# DEPOSIT / WITHDRAW
# =========================================================

router.register(
    r"OrderDeposit",
    DepositAdminViewSet,
    basename="OrderDeposit",
)

router.register(
    r"silver-OrderDeposit",
    SilverDepositAdminViewSet,
    basename="silver-OrderDeposit",
)

router.register(
    r"OrderWithdraw",
    WithdrawAdminViewSet,
    basename="OrderWithdraw",
)

router.register(
    r"silver-OrderWithdraw",
    SilverWithdrawAdminViewSet,
    basename="silver-OrderWithdraw",
)

# =========================================================
# ANALYTICS
# =========================================================

router.register(
    r"analytics",
    AdminAnalyticsViewSet,
    basename="analytics",
)

# =========================================================
# LOGS
# =========================================================

router.register(
    r"logs",
    AdminLogViewSet,
    basename="logs",
)

# =========================================================
# BANNERS
# =========================================================

router.register(
    r"gold-banners",
    GoldBannerAdminViewSet,
    basename="gold-banners",
)

router.register(
    r"silver-banners",
    SilverBannerAdminViewSet,
    basename="silver-banners",
)

# =========================================================
# MARKET
# =========================================================
# نکته: GoldPriceOffsetAdminViewSet و SilverPriceOffsetAdminViewSet
# دیگر اینجا register نمی‌شوند چون با /offset/ زیرمجموعه‌ی
# market/gold و market/silver تداخل داشتند (router pk pattern
# مثل market/gold/<pk>/ زودتر از market/gold/offset/ match می‌شد).
# این دو مسیر الان به‌صورت صریح در urlpatterns پایین تعریف شده‌اند.
# =========================================================

router.register(
    r"market/gold",
    GoldAdminViewSet,
    basename="admin-gold",
)

router.register(
    r"market/silver",
    SilverAdminViewSet,
    basename="admin-silver",
)

# =========================================================
# ANNOUNCEMENTS
# =========================================================

router.register(
    r"gold-announcements",
    GoldAnnouncementAdminViewSet,
    basename="gold-announcements",
)

router.register(
    r"silver-announcements",
    SilverAnnouncementAdminViewSet,
    basename="silver-announcements",
)

# =========================================================
# BALANCE ADJUSTMENTS
# =========================================================

router.register(
    r"gold-balance-adjustments",
    GoldBalanceAdjustmentViewSet,
    basename="gold-balance-adjustment",
)

router.register(
    r"silver-balance-adjustments",
    SilverBalanceAdjustmentViewSet,
    basename="silver-balance-adjustment",
)
router.register(
    r"gold-balance-withdrawals",
    GoldBalanceWithdrawalViewSet,
    basename="gold-balance-withdrawal",
)

router.register(r"gold-transactions", GoldTransactionAdminViewSet, basename="admin-gold-transactions")
# =========================================================
# BALANCE WITHDRAWALS
# =========================================================

router.register(
    r"silver-balance-withdrawals",
    SilverBalanceWithdrawalViewSet,
    basename="silver-balance-withdrawal",
)
router.register(r'silver-transactions', SilverTransactionAdminViewSet, basename='silver-transaction')

# =========================================================
# URL PATTERNS
# =========================================================

urlpatterns = [

    # -------------------------
    # Market — Gold / Silver Price Offset
    # (صریح و قبل از router.urls تعریف شده تا با
    # market/gold/<pk>/ و market/silver/<pk>/ تداخل نکند)
    # -------------------------

    path(
        "market/gold/offset/",
        GoldPriceOffsetAdminViewSet.as_view(
            {
                "get": "list",
                "post": "create",
            }
        ),
        name="admin-gold-offset-list",
    ),

    path(
        "market/gold/offset/<int:pk>/",
        GoldPriceOffsetAdminViewSet.as_view(
            {
                "get": "retrieve",
                "patch": "partial_update",
                "delete": "destroy",
            }
        ),
        name="admin-gold-offset-detail",
    ),

    path(
        "market/silver/offset/",
        SilverPriceOffsetAdminViewSet.as_view(
            {
                "get": "list",
                "post": "create",
            }
        ),
        name="admin-silver-offset-list",
    ),

    path(
        "market/silver/offset/<int:pk>/",
        SilverPriceOffsetAdminViewSet.as_view(
            {
                "get": "retrieve",
                "patch": "partial_update",
                "delete": "destroy",
            }
        ),
        name="admin-silver-offset-detail",
    ),

    # -------------------------
    # Analytics
    # -------------------------

    path(
        "analytics/chart/",
        AnalyticsChartAPIView.as_view(),
        name="analytics-chart",
    ),

    path(
        "analytics/purchase-chart/",
        AnalyticsPurchaseChartAPIView.as_view(),
        name="analytics-purchase-chart",
    ),

    path(
        "analytics/buy-sell-chart/",
        BuySellChartAPIView.as_view(),
        name="buy-sell-chart",
    ),

    # -------------------------
    # Gold Balance Adjustment
    # -------------------------

    path(
        "gold-balance-adjustments/<int:user_id>/",
        GoldBalanceAdjustmentViewSet.as_view(
            {
                "get": "list",
            }
        ),
        name="gold-balance-adjustment-user-list",
    ),

    path(
        "gold-balance-adjustments/<int:user_id>/<int:pk>/",
        GoldBalanceAdjustmentViewSet.as_view(
            {
                "get": "retrieve",
                "put": "update",
                "patch": "partial_update",
                "delete": "destroy",
            }
        ),
        name="gold-balance-adjustment-detail",
    ),

    # -------------------------
    # Silver Balance Adjustment
    # -------------------------

    path(
        "silver-balance-adjustments/<int:user_id>/<int:pk>/",
        SilverBalanceAdjustmentViewSet.as_view(
            {
                "get": "retrieve",
                "put": "update",
                "patch": "partial_update",
                "delete": "destroy",
            }
        ),
        name="silver-balance-adjustment-detail",
    ),

    path(
        "silver-balance-adjustments/<int:user_id>/",
        SilverBalanceAdjustmentViewSet.as_view(
            {
                "get": "list",
            }
        ),
        name="silver-balance-adjustment-user-list",
    ),

    # -------------------------
    # Gold Balance Withdrawal
    # -------------------------

    path(
        "gold-balance-withdrawals/<int:user_id>/",
        GoldBalanceWithdrawalViewSet.as_view(
            {
                "get": "list",
            }
        ),
        name="gold-balance-withdrawal-user-list",
    ),

    path(
        "gold-balance-withdrawals/<int:user_id>/<int:pk>/",
        GoldBalanceWithdrawalViewSet.as_view(
            {
                "get": "retrieve",
                "put": "update",
                "patch": "partial_update",
                "delete": "destroy",
            }
        ),
        name="gold-balance-withdrawal-detail",
    ),

    # -------------------------
    # Silver Balance Withdrawal
    # -------------------------

    path(
        "silver-balance-withdrawals/<int:user_id>/",
        SilverBalanceWithdrawalViewSet.as_view(
            {
                "get": "list",
            }
        ),
        name="silver-balance-withdrawal-user-list",
    ),

    path(
        "silver-balance-withdrawals/<int:user_id>/<int:pk>/",
        SilverBalanceWithdrawalViewSet.as_view(
            {
                "get": "retrieve",
                "put": "update",
                "patch": "partial_update",
                "delete": "destroy",
            }
        ),
        name="silver-balance-withdrawal-detail",
    ),
]

urlpatterns += router.urls