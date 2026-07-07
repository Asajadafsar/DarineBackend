from drf_spectacular.extensions import OpenApiAuthenticationExtension

class CookieJWTAuthenticationScheme(OpenApiAuthenticationExtension):
    target_class = "accounts.authentication.CookieJWTAuthentication"
    name = "CookieJWTAuth"

    def get_security_definition(self, auto_schema):
        return {
            "type": "apiKey",
            "in": "cookie",
            "name": "access_token",  # اسم واقعی کوکی‌ای که استفاده می‌کنی
        }