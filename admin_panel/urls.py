from rest_framework.routers import DefaultRouter

from admin_panel.views import CategoryAdminViewSet, CooperationRequestAdminViewSet, DashboardAdminViewSet, DepositAdminViewSet, GiftCardAdminViewSet, GoldBankAdminViewSet, OrderAdminViewSet, ProductAdminViewSet, SilverBankAdminViewSet, SilverDepositAdminViewSet, SilverOrderAdminViewSet, SilverProductAdminViewSet, SilverWithdrawAdminViewSet, UserAdminViewSet, WithdrawAdminViewSet

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
router.register("Orderithdraw", WithdrawAdminViewSet, basename="Orderithdraw")
router.register("silver-OrderDeposit", SilverDepositAdminViewSet, basename="silver-OrderDeposit")
router.register("silver-Orderithdraw", SilverWithdrawAdminViewSet, basename="silver-Orderithdraw")

urlpatterns = router.urls

