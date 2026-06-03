from accounts.models import User
from rest_framework import serializers


class AdminUserListSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = [
            "id",
            "mobile",
            "first_name",
            "last_name",
            "role",
            "auth_status",
            "is_active",
            "date_joined",
            "updated_at",
        ]