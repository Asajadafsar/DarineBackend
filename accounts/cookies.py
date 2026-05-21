# accounts/cookies.py

def set_auth_cookies(response, access_token, refresh_token):

    response.set_cookie(
        key="accessToken",
        value=access_token,
        httponly=True,
        secure=False,  # وقتی HTTPS شد => True
        samesite="Lax",
        path="/",
        max_age=60 * 60 * 24  # 1 day
    )

    response.set_cookie(
        key="refreshToken",
        value=refresh_token,
        httponly=True,
        secure=False,  # وقتی HTTPS شد => True
        samesite="Lax",
        path="/",
        max_age=60 * 60 * 24 * 7  # 7 days
    )

    return response


def clear_auth_cookies(response):

    response.delete_cookie(
        key="accessToken",
        path="/"
    )

    response.delete_cookie(
        key="refreshToken",
        path="/"
    )

    return response