from django.urls import path

from .views import (
    AdminCategoryCreateAPIView,
    AdminCategoryDeleteAPIView,
    AdminCategoryListAPIView,
    AdminProductCreateAPIView,
    AdminProductDeleteAPIView,
    AdminProductDetailAPIView,
    AdminProductListAPIView,
    AdminProductUpdateAPIView,
    AdminSilverCategoryCreateAPIView,
    AdminSilverCategoryDeleteAPIView,
    AdminSilverCategoryListAPIView,
    AdminSilverProductCreateAPIView,
    AdminSilverProductDeleteAPIView,
    AdminSilverProductDetailAPIView,
    AdminSilverProductListAPIView,
    AdminSilverProductUpdateAPIView,
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

]