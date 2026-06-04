from django.urls import path

from .views import (
    AdminCategoryCreateAPIView,
    AdminCategoryDeleteAPIView,
    AdminCategoryListAPIView,
    AdminDashboardAPIView,
    AdminFinancialListAPIView,
    AdminFinancialStatusAPIView,
    AdminGiftCardChangeStatusAPIView,
    AdminGiftCardCreateAPIView,
    AdminGiftCardDeleteAPIView,
    AdminGiftCardDetailAPIView,
    AdminGiftCardListAPIView,
    AdminGiftCardOrderListAPIView,
    AdminGiftCardOrderStatusAPIView,
    AdminGiftCardUpdateAPIView,
    AdminGoldBankCreateAPIView,
    AdminGoldBankDeleteAPIView,
    AdminGoldBankDetailAPIView,
    AdminGoldBankListAPIView,
    AdminGoldBankToggleAPIView,
    AdminGoldBankUpdateAPIView,
    AdminGoldTransactionListAPIView,
    AdminGoldTransactionStatusAPIView,
    AdminOrderListAPIView,
    AdminOrderStatusAPIView,
    AdminProductCreateAPIView,
    AdminProductDeleteAPIView,
    AdminProductDetailAPIView,
    AdminProductListAPIView,
    AdminProductUpdateAPIView,
    AdminSilverBankCreateAPIView,
    AdminSilverBankDeleteAPIView,
    AdminSilverBankDetailAPIView,
    AdminSilverBankListAPIView,
    AdminSilverBankToggleAPIView,
    AdminSilverBankUpdateAPIView,
    AdminSilverCategoryCreateAPIView,
    AdminSilverCategoryDeleteAPIView,
    AdminSilverCategoryListAPIView,
    AdminSilverFinancialListAPIView,
    AdminSilverFinancialStatusAPIView,
    AdminSilverOrderListAPIView,
    AdminSilverOrderStatusAPIView,
    AdminSilverProductCreateAPIView,
    AdminSilverProductDeleteAPIView,
    AdminSilverProductDetailAPIView,
    AdminSilverProductListAPIView,
    AdminSilverProductUpdateAPIView,
    AdminSilverTransactionListAPIView,
    AdminSilverTransactionStatusAPIView,
    AdminUserListAPIView,
    AdminUserDetailAPIView,
    AdminUserUpdateAPIView,
    AdminUserDeleteAPIView,
    AdminUserToggleActiveAPIView
)

urlpatterns = [
    path("users/", AdminUserListAPIView.as_view()),

    path("users/<int:user_id>/", AdminUserDetailAPIView.as_view()),

    path("users/<int:user_id>/update/", AdminUserUpdateAPIView.as_view()),

    path("users/<int:user_id>/delete/", AdminUserDeleteAPIView.as_view()),

    path("users/<int:user_id>/toggle/", AdminUserToggleActiveAPIView.as_view()),
    # PRODUCTS
    path("gold/products/", AdminProductListAPIView.as_view()),
    path("gold/products/create/", AdminProductCreateAPIView.as_view()),
    path("gold/products/<int:pk>/", AdminProductDetailAPIView.as_view()),
    path("gold/products/<int:pk>/update/", AdminProductUpdateAPIView.as_view()),
    path("gold/products/<int:pk>/delete/", AdminProductDeleteAPIView.as_view()),

    # CATEGORIES
    path("gold/categories/", AdminCategoryListAPIView.as_view()),
    path("gold/categories/create/", AdminCategoryCreateAPIView.as_view()),
    path("gold/categories/<int:pk>/delete/", AdminCategoryDeleteAPIView.as_view()),
    path("silver/products/", AdminSilverProductListAPIView.as_view()),
    path("silver/products/create/", AdminSilverProductCreateAPIView.as_view()),
    path("silver/products/<int:pk>/", AdminSilverProductDetailAPIView.as_view()),
    path("silver/products/<int:pk>/update/", AdminSilverProductUpdateAPIView.as_view()),
    path("silver/products/<int:pk>/delete/", AdminSilverProductDeleteAPIView.as_view()),

    path("silver/categories/", AdminSilverCategoryListAPIView.as_view()),
    path("silver/categories/create/", AdminSilverCategoryCreateAPIView.as_view()),
    path("silver/categories/<int:pk>/delete/", AdminSilverCategoryDeleteAPIView.as_view()),

    path("gold/gift-cards/", AdminGiftCardListAPIView.as_view()),
    path("gold/gift-cards/create/", AdminGiftCardCreateAPIView.as_view()),
    path("gold/gift-cards/<int:pk>/", AdminGiftCardDetailAPIView.as_view()),
    path("gold/gift-cards/<int:pk>/update/", AdminGiftCardUpdateAPIView.as_view()),
    path("gold/gift-cards/<int:pk>/delete/", AdminGiftCardDeleteAPIView.as_view()),

# optional action
    path("gold/gift-cards/<int:pk>/status/", AdminGiftCardChangeStatusAPIView.as_view()),
# ORDERS
path("gold/orders/gift-cards/", AdminGiftCardOrderListAPIView.as_view()),
path("gold/orders/gift-cards/<int:pk>/status/", AdminGiftCardOrderStatusAPIView.as_view()),

path("gold/orders/products/", AdminOrderListAPIView.as_view()),
path("gold/orders/products/<int:pk>/status/", AdminOrderStatusAPIView.as_view()),

# FINANCIAL
path("gold/finance/transactions/", AdminFinancialListAPIView.as_view()),
path("gold/finance/transactions/<int:pk>/status/", AdminFinancialStatusAPIView.as_view()),

# GOLD TRADE
path("gold/transactions/", AdminGoldTransactionListAPIView.as_view()),
path("gold/transactions/<int:pk>/status/", AdminGoldTransactionStatusAPIView.as_view()),
# SILVER ORDERS
path("silver/orders/", AdminSilverOrderListAPIView.as_view()),
path("silver/orders/<int:pk>/status/", AdminSilverOrderStatusAPIView.as_view()),

# SILVER FINANCIAL
path("silver/finance/", AdminSilverFinancialListAPIView.as_view()),
path("silver/finance/<int:pk>/status/", AdminSilverFinancialStatusAPIView.as_view()),

# SILVER TRANSACTIONS
path("silver/transactions/", AdminSilverTransactionListAPIView.as_view()),
path("silver/transactions/<int:pk>/status/", AdminSilverTransactionStatusAPIView.as_view()),
path(
    "dashboard/",
    AdminDashboardAPIView.as_view(),
    name="admin-dashboard"
),
# GOLD BANKS

path("gold/banks/", AdminGoldBankListAPIView.as_view()),
path("gold/banks/create/", AdminGoldBankCreateAPIView.as_view()),
path("gold/banks/<int:pk>/", AdminGoldBankDetailAPIView.as_view()),
path("gold/banks/<int:pk>/update/", AdminGoldBankUpdateAPIView.as_view()),
path("gold/banks/<int:pk>/delete/", AdminGoldBankDeleteAPIView.as_view()),
path("gold/banks/<int:pk>/toggle/", AdminGoldBankToggleAPIView.as_view()),


# SILVER BANKS

path("silver/banks/", AdminSilverBankListAPIView.as_view()),
path("silver/banks/create/", AdminSilverBankCreateAPIView.as_view()),
path("silver/banks/<int:pk>/", AdminSilverBankDetailAPIView.as_view()),
path("silver/banks/<int:pk>/update/", AdminSilverBankUpdateAPIView.as_view()),
path("silver/banks/<int:pk>/delete/", AdminSilverBankDeleteAPIView.as_view()),
path("silver/banks/<int:pk>/toggle/", AdminSilverBankToggleAPIView.as_view()),
]