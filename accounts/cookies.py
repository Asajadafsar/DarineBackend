# accounts/cookies.py

from django.conf import settings


def set_auth_cookies(
    response,
    access_token,
    refresh_token
):

    is_production = not settings.DEBUG

    cookie_domain = ".darine.shop" if is_production else None

    secure = is_production

    samesite = "None" if is_production else "Lax"

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

    is_production = not settings.DEBUG

    cookie_domain = ".darine.shop" if is_production else None

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