from django.urls import path
from .views import AdminUserListAPIView

urlpatterns = [
    path("users/", AdminUserListAPIView.as_view(), name="admin-users"),
]