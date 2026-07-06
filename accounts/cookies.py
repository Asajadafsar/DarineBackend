import os

ACCESS_COOKIE = "accessToken"
REFRESH_COOKIE = "refreshToken"


def is_production():
    return os.getenv("ENV") == "production"


def cookie_settings():

    if is_production():
        return {
            "domain": ".darine.shop",
            "secure": True,
            "samesite": "None",
        }

    return {
        "domain": None,
        "secure": False,
        "samesite": "Lax",
    }


def set_auth_cookies(response, access, refresh):

    config = cookie_settings()

    response.set_cookie(
        ACCESS_COOKIE,
        access,
        httponly=True,
        secure=config["secure"],
        samesite=config["samesite"],
        domain=config["domain"],
        path="/",
        max_age=86400,
    )

    response.set_cookie(
        REFRESH_COOKIE,
        refresh,
        httponly=True,
        secure=config["secure"],
        samesite=config["samesite"],
        domain=config["domain"],
        path="/",
        max_age=604800,
    )

    return response


def clear_auth_cookies(response):

    cookies = [
        "accessToken",
        "refreshToken",
    ]

    domains = [
        None,
        "api.darine.shop",
        "gold.darine.shop",
        "silver.darine.shop",
        ".darine.shop",
    ]

    for cookie in cookies:
        for domain in domains:
            response.delete_cookie(
                key=cookie,
                path="/",
                domain=domain,
            )

    return response
