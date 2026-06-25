from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status



def custom_exception_handler(exc, context):

    response = exception_handler(
        exc,
        context
    )


    # خطاهای DRF
    if response is not None:

        errors = response.data


        message = "خطایی رخ داده است."

        if isinstance(errors, dict):

            first_key = next(
                iter(errors),
                None
            )

            if first_key:

                value = errors[first_key]

                if isinstance(value, list):

                    message = str(value[0])

                else:

                    message = str(value)


        return Response(
            {
                "success": False,
                "message": message,
                "data": errors
            },
            status=response.status_code
        )


    # ==========================
    # SERVER ERROR 500
    # ==========================

    return Response(
        {
            "success": False,
            "message": "خطای داخلی سرور رخ داده است. لطفا دوباره تلاش کنید.",
            "data": None
        },
        status=status.HTTP_500_INTERNAL_SERVER_ERROR
    )