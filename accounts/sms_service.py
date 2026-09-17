from datetime import datetime
import time
import uuid
import threading

import jdatetime
import requests


# ==========================================
# BALE CONFIG
# ==========================================

BALE_API_KEY = "1d74otIKkKuytJDC"
BALE_BOT_ID = 91195008


# ==========================================
# BALE OTP (اجرای غیرهمزمان)
# ==========================================

def send_bale_otp_async(mobile, code):
    """
    ارسال OTP داخل بازوی بله به صورت غیرهمزمان
    """
    def _send():
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
                timeout=10
            )
            print("========== BALE ==========")
            print("STATUS:", response.status_code)
            print("BODY:", response.text)
        except Exception as e:
            print("BALE ERROR:", e)

    # اجرا در یک ترد جداگانه
    thread = threading.Thread(target=_send)
    thread.daemon = True
    thread.start()


# ==========================================
# OTP SMS (با متد SendTokenSingle)
# ==========================================

def send_otp_sms(mobile, code, client_type="gold"):
    """
    ارسال پیامک حاوی کد تایید با استفاده از متد SendTokenSingle
    """
    url = "https://api.sms-webservice.com/api/V3/SendTokenSingle"
    api_key = "276941-6FB7E264C3C440E09148F711F94913C6"

    client_type = (client_type or "gold").lower().strip()

    if client_type == "silver":
        template_key = "darinetem2"
        p3 = ""
    else:
        template_key = "darinetem"
        p3 = "SbBVMIJwADu"

    # ساخت URL با پارامترها
    params = {
        "ApiKey": api_key,
        "TemplateKey": template_key,
        "Destination": mobile,
        "p1": code,
        "p2": code,
        "p3": p3
    }

    try:
        # استفاده از params به جای ساخت URL دستی (سریعتر)
        response = requests.get(
            url, 
            params=params, 
            timeout=10  # کاهش تایم‌اوت برای سرعت بیشتر
        )

        sms_success = False
        
        if response.status_code == 200:
            try:
                data = response.json()
                if data.get("Success") is True or data.get("id"):
                    sms_success = True
            except:
                if '"id"' in response.text or '"Success":true' in response.text.lower():
                    sms_success = True

        # ارسال همزمان در بله (غیرهمزمان)
        send_bale_otp_async(mobile, code)

        return sms_success

    except requests.exceptions.Timeout:
        # در صورت تایم‌اوت، بله رو ارسال کن
        send_bale_otp_async(mobile, code)
        return True  # فرض موفقیت برای پایداری

    except Exception as e:
        print(f"SMS Error: {e}")
        send_bale_otp_async(mobile, code)
        return False


# ==========================================
# LOGIN SUCCESS SMS
# ==========================================

def send_login_sms(mobile):
    """
    ارسال پیامک لاگین موفق با استفاده از متد SendTokenSingle
    """
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
        "p3": ""
    }

    try:
        response = requests.get(url, params=params, timeout=10)

        if response.status_code == 200:
            data = response.json()
            if data.get("Success") is True or data.get("id"):
                return True

        return False

    except requests.exceptions.Timeout:
        return True

    except Exception as e:
        print("LOGIN ERROR:", e)
        return False