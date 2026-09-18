from rest_framework.views import exception_handler

from .cookies import clear_auth_cookies


def custom_exception_handler(exc, context):

    response = exception_handler(exc, context)

    if response is None:
        return response

    print("🔥 CUSTOM EXCEPTION HANDLER CALLED")
    print("🔥 EXCEPTION:", repr(exc))
    print("🔥 RESPONSE:", response.data)

    data = response.data

    if isinstance(data, dict):

        if data.get("code") == "token_not_valid":

            print("🔥 TOKEN INVALID → CLEARING COOKIES")

            clear_auth_cookies(response)

    return response