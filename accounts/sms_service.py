
from datetime import datetime
import uuid

import jdatetime
import requests


# ==========================================
# BALE CONFIG
# ==========================================

BALE_API_KEY = "1d74otIKkKuytJDC"
BALE_BOT_ID = 91195008


# ==========================================
# BALE OTP
# ==========================================

def send_bale_otp(mobile, code):
    """
    ارسال OTP داخل بازوی بله
    """

    phone = str(mobile).strip()

    if phone.startswith("09"):
        phone = "98" + phone[1:]
    elif phone.startswith("+98"):
        phone = phone.replace("+", "")
    elif phone.startswith("98"):
        pass
    else:
        phone = "98" + phone

    url = "https://safir.bale.ai/api/v3/send_message"

    headers = {
        "api-access-key": BALE_API_KEY,
        "Content-Type": "application/json",
    }

    payload = {
        "request_id": str(uuid.uuid4()),
        "bot_id": BALE_BOT_ID,
        "phone_number": phone,
        "message_data": {
            "otp_message": {
                "otp": str(code)
            }
        }
    }

    try:
        response = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=15
        )

        print("========== BALE ==========")
        print("STATUS:", response.status_code)
        print("BODY:", response.text)

        return response.status_code == 200

    except Exception as e:
        print("BALE ERROR:", e)
        return False


# ==========================================
# OTP SMS + BALE
# ==========================================

def send_otp_sms(mobile, code, client_type="gold"):
    url = "https://api.sms-webservice.com/api/V3/SendTokenSingle"
    api_key = "276941-6FB7E264C3C440E09148F711F94913C6"

    client_type = (client_type or "gold").lower().strip()

    if client_type == "silver":
        template_key = "darinetem2"
    else:
        template_key = "darinetem"

    params = {
        "ApiKey": api_key,
        "TemplateKey": template_key,
        "Destination": mobile,
        "p1": code,
        "p2": code,
        "p3": "",
    }

    try:
        response = requests.get(url, params=params, timeout=30)

        sms_success = (
            response.status_code == 200
            and '"id"' in response.text.lower()
        )

        if not sms_success:
            print("SMS FAIL RESPONSE:", response.text)

        # ----------------------------
        # ارسال همزمان در بله
        # ----------------------------
        try:
            send_bale_otp(mobile, code)
        except Exception as e:
            print("BALE SEND ERROR:", e)

        return sms_success

    except requests.exceptions.Timeout:
        print("SMS TIMEOUT - assuming success for stability")

        try:
            send_bale_otp(mobile, code)
        except Exception as e:
            print("BALE SEND ERROR:", e)

        return True

    except Exception as e:
        print(f"SMS Connection Error: {e}")

        try:
            send_bale_otp(mobile, code)
        except Exception as ex:
            print("BALE SEND ERROR:", ex)

        return False


# ==========================================
# LOGIN SUCCESS SMS
# ==========================================

def send_login_sms(mobile):
    url = "https://api.sms-webservice.com/api/V3/SendTokenSingle"
    api_key = "276941-6FB7E264C3C440E09148F711F94913C6"

    now = datetime.now()
    j_now = jdatetime.datetime.fromgregorian(datetime=now)

    params = {
        "ApiKey": api_key,
        "TemplateKey": "login",
        "Destination": mobile,
        "p1": j_now.strftime("%Y/%m/%d"),
        "p2": j_now.strftime("%H:%M"),
        "p3": "",
    }

    try:
        response = requests.get(url, params=params, timeout=30)

        print("LOGIN STATUS:", response.status_code)
        print("LOGIN RESPONSE:", response.text)

        if response.status_code == 200 and '"id"' in response.text.lower():
            return True

        return False

    except requests.exceptions.Timeout:
        print("LOGIN TIMEOUT")
        return True

    except Exception as e:
        print("LOGIN ERROR:", e)
        return False