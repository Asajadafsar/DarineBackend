# accounts/cookies.py

from django.conf import settings
import os


def is_production():

    return os.environ.get("ENV") == "production"

def set_auth_cookies(
    response,
    access_token,
    refresh_token
):

    prod = is_production()

    cookie_domain = ".darine.shop" if prod else None

    secure = prod

    samesite = "None" if prod else "Lax"

    response.set_cookie(
        key="accessToken",
        value=access_token,
        httponly=True,
        secure=secure,
        samesite=samesite,
        domain=cookie_domain,
        path="/",
        max_age=60 * 60 * 24
    )

    response.set_cookie(
        key="refreshToken",
        value=refresh_token,
        httponly=True,
        secure=secure,
        samesite=samesite,
        domain=cookie_domain,
        path="/",
        max_age=60 * 60 * 24 * 7
    )

    return response
def clear_auth_cookies(response):

    prod = is_production()

    cookie_domain = ".darine.shop" if prod else None

    response.delete_cookie(
        key="accessToken",
        domain=cookie_domain,
        path="/"
    )

    response.delete_cookie(
        key="refreshToken",
        domain=cookie_domain,
        path="/"
    )

    return response
