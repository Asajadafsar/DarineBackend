from django.urls import path

from rest_framework.routers import DefaultRouter
from gold_app.utils import get_gold_bubble, get_gold_chart_data
from silver_app.utils import get_silver_bubble, get_silver_chart_data
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
    GoldBankAdminViewSet,
    GoldBannerAdminViewSet,
    GoldPriceOffsetAdminViewSet,
    OrderAdminViewSet,
    ProductAdminViewSet,
    SilverAdminViewSet,
    SilverBankAdminViewSet,
    SilverBannerAdminViewSet,
    SilverDepositAdminViewSet,
    SilverOrderAdminViewSet,
    SilverPriceOffsetAdminViewSet,
    SilverProductAdminViewSet,
    SilverWithdrawAdminViewSet,
    UserAdminViewSet,
    WithdrawAdminViewSet,
)

router = DefaultRouter()

router.register("users", UserAdminViewSet, basename="users")
router.register("products", ProductAdminViewSet, basename="products")
router.register("categories", CategoryAdminViewSet, basename="categories")
router.register("silver-products", SilverProductAdminViewSet, basename="silver-products")
router.register("gift-cards", GiftCardAdminViewSet, basename="gift-cards")
router.register("orders", OrderAdminViewSet, basename="orders")
router.register("silver-orders", SilverOrderAdminViewSet, basename="silver-orders")
router.register("dashboard", DashboardAdminViewSet, basename="dashboard")
router.register("gold-bank", GoldBankAdminViewSet, basename="gold-bank")
router.register("silver-bank", SilverBankAdminViewSet, basename="silver-bank")
router.register("CooperationRequest", CooperationRequestAdminViewSet, basename="CooperationRequest")
router.register("OrderDeposit", DepositAdminViewSet, basename="OrderDeposit")
router.register("silver-OrderDeposit", SilverDepositAdminViewSet, basename="silver-OrderDeposit")
router.register("OrderWithdraw", WithdrawAdminViewSet, basename="OrderWithdraw")
router.register("silver-OrderWithdraw", SilverWithdrawAdminViewSet, basename="silver-OrderWithdraw")
router.register("analytics", AdminAnalyticsViewSet, basename="analytics")
router.register("logs", AdminLogViewSet, basename="logs")
router.register(r"gold-banners", GoldBannerAdminViewSet, basename="gold-banners")
router.register(r"silver-banners", SilverBannerAdminViewSet, basename="silver-banners")
router.register(r"market/gold/offset", GoldPriceOffsetAdminViewSet, basename="admin-gold-offset")
router.register(r"market/silver/offset", SilverPriceOffsetAdminViewSet, basename="admin-silver-offset")
router.register(r"market/gold", GoldAdminViewSet, basename="admin-gold")
router.register(r"market/silver", SilverAdminViewSet, basename="admin-silver")

urlpatterns = [
    path("analytics/chart/", AnalyticsChartAPIView.as_view(), name="analytics-chart"),
    path("analytics/purchase-chart/", AnalyticsPurchaseChartAPIView.as_view(), name="analytics-purchase-chart"),
    path("analytics/buy-sell-chart/", BuySellChartAPIView.as_view(), name="buy-sell-chart"),
]

urlpatterns += router.urls