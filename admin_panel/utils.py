from django.db import transaction
from .models import AdminLog



def get_client_ip(request):

    if request is None:
        return None


    x_forwarded_for = request.META.get(
        "HTTP_X_FORWARDED_FOR"
    )


    if x_forwarded_for:

        return x_forwarded_for.split(",")[0].strip()


    return request.META.get(
        "REMOTE_ADDR"
    )



def clean_request_data(data):

    if not data:
        return None


    result = {}


    try:

        for key, value in data.items():

            if hasattr(value, "name"):

                result[key] = {
                    "file": value.name,
                    "size": getattr(
                        value,
                        "size",
                        None
                    )
                }

            elif isinstance(value, (str, int, float, bool)):

                result[key] = value

            else:

                result[key] = str(value)


    except Exception:

        return None


    return result



def create_admin_log(

        action_type,
        action,

        request=None,

        admin=None,
        user=None,

        model_name=None,
        object_id=None,

        description=None,

        tracking_code=None,

        response_status=None,

        success=True,

        error_message=None,

        old_data=None,

        new_data=None,

        extra=None

):


    try:

        # جدا کردن لاگ از تراکنش اصلی
        with transaction.atomic():

            return AdminLog.objects.create(

                admin=admin,

                user=user,


                action_type=action_type,

                action=action,


                model_name=model_name,

                object_id=object_id,


                description=description,


                tracking_code=tracking_code,


                response_status=response_status,


                success=success,


                error_message=error_message,


                method=(
                    request.method
                    if request
                    else None
                ),


                endpoint=(
                    request.path
                    if request
                    else None
                ),


                request_data=(
                    clean_request_data(
                        request.data
                    )
                    if request and hasattr(request, "data")
                    else None
                ),


                response_data=None,


                old_data=old_data,


                new_data=new_data,


                extra=extra,


                ip_address=get_client_ip(request),


                user_agent=(

                    request.META.get(
                        "HTTP_USER_AGENT"
                    )

                    if request

                    else None
                )

            )


    except Exception as e:

        # اگر خود لاگ خراب شد
        # نباید API اصلی بخوابد

        print(
            "ADMIN LOG ERROR:",
            str(e)
        )

        return None