from rest_framework_simplejwt.authentication import JWTAuthentication

class CookieJWTAuthentication(JWTAuthentication):

    def authenticate(self, request):

        access_token = request.COOKIES.get("accessToken")

        if not access_token:
            return None

        try:
            validated_token = self.get_validated_token(access_token)

            user = self.get_user(validated_token)

            return user, validated_token

        except Exception:
            return None