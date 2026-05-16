def set_auth_cookies(response, access_token, refresh_token):

    response.set_cookie(
        key="accessToken",
        value=access_token,
        httponly=True,
        secure=False, # production => True
        samesite="Lax",
        path="/",
        max_age=600
    )

    response.set_cookie(
        key="refreshToken",
        value=refresh_token,
        httponly=True,
        secure=False, # production => True
        samesite="Strict",
        path="/",
        max_age=604800
    )

    return response


def clear_auth_cookies(response):

    response.delete_cookie("accessToken")
    response.delete_cookie("refreshToken")

    return response