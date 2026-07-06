from rest_framework_simplejwt.authentication import JWTAuthentication


class CookieJWTAuthentication(JWTAuthentication):

    def authenticate(self, request):

        token = request.COOKIES.get("accessToken")

        if not token:
            return None

        validated = self.get_validated_token(token)

        return (
            self.get_user(validated),
            validated,
        )
