from .models import AdminLog



def create_admin_log(
        action_type,
        action,
        admin=None,
        user=None,
        model_name=None,
        object_id=None,
        description=None
):

    return AdminLog.objects.create(

        admin=admin,

        user=user,

        action_type=action_type,

        action=action,

        model_name=model_name,

        object_id=object_id,

        description=description
    )