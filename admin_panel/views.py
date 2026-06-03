from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from accounts.models import User
from .serializers import AdminUserListSerializer
from .permissions import IsAdminRole


# =========================================================
# SUCCESS RESPONSE
# =========================================================

def success_response(
    message="عملیات موفق بود",
    results=None,
    total_results=None,
    status_code=status.HTTP_200_OK
):

    if results is None:
        results = []

    if total_results is None:
        total_results = len(results) if hasattr(results, "__len__") else 0

    return Response(
        {
            "success": True,
            "message": message,
            "data": {
                "total_results": total_results,
                "results": results
            }
        },
        status=status_code
    )


# =========================================================
# ERROR RESPONSE
# =========================================================

def error_response(
    message="خطایی رخ داده است",
    status_code=status.HTTP_400_BAD_REQUEST,
    data=None
):

    return Response(
        {
            "success": False,
            "message": message,
            "data": {
                "total_results": 0,
                "results": data or []
            }
        },
        status=status_code
    )



# =========================================================
# ADMIN USERS LIST
# =========================================================

class AdminUserListAPIView(APIView):

    permission_classes = [IsAdminRole]

    def get(self, request):

        users = User.objects.all().order_by("-id")

        serializer = AdminUserListSerializer(users, many=True)

        return success_response(
            message="لیست کاربران دریافت شد",
            results=serializer.data,
            total_results=users.count()
        )