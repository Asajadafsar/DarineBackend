import requests
import logging
import time

logger = logging.getLogger(__name__)

SMS_URL = "https://api.sms-webservice.com/api/V3/SendBulk"

SMS_API_KEY = "276941-6FB7E264C3C440E09148F711F94913C6"

SMS_SENDER = 50004075002699


def send_admin_note_sms(mobile, note):

    text = f"""
کاربر گرامی

وضعیت درخواست شما بروزرسانی شد.

شرح:
{note}

دارینه تیم
darine.shop
""".strip()

    payload = {
        "ApiKey": SMS_API_KEY,
        "Text": text,
        "Sender": SMS_SENDER,
        "Recipients": [{"Destination": mobile, "UserTraceId": int(time.time())}],
    }

    try:

        response = requests.post(
            SMS_URL,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30,
        )

        print("SMS STATUS:", response.status_code)
        print("SMS RESPONSE:", response.text)

        data = response.json()

        if data.get("Success") is True:
            return True

        return False

    except Exception as e:

        print("SMS EXCEPTION:", str(e))
        return False


def get_account_info():

    response = requests.post(
        "https://api.sms-webservice.com/api/V3/AccountInfo",
        json={"ApiKey": SMS_API_KEY},
    )

    print(response.text)
