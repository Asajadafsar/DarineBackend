import requests


def send_otp_sms(mobile, code, client_type="gold"):
    url = "https://api.sms-webservice.com/api/V3/SendTokenSingle"
    api_key = "276941-6FB7E264C3C440E09148F711F94913C6"

    # =========================
    # TEMPLATE SELECTION FIX
    # =========================
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

        # =========================
        # SAFE CHECK
        # =========================
        if response.status_code == 200 and '"id"' in response.text.lower():
            return True

        print("SMS FAIL RESPONSE:", response.text)
        return False

    except requests.exceptions.Timeout:
        print("SMS TIMEOUT - assuming success for stability")
        return True

    except Exception as e:
        print(f"SMS Connection Error: {e}")
        return False