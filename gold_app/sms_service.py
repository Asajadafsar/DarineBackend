import requests


def send_price_alert_sms(mobile, price):

    url = "https://api.sms-webservice.com/api/V3/SendTokenSingle"

    api_key = "276941-6FB7E264C3C440E09148F711F94913C6"

    params = {
        "ApiKey": api_key,
        "TemplateKey": "pricealarm",
        "Destination": mobile,
        "p1": f"{price:,}",
        "p2": "",
        "p3": "",
    }

    try:
        response = requests.get(url, params=params, timeout=30)

        print("PRICE ALERT STATUS:", response.status_code)
        print("PRICE ALERT RESPONSE:", response.text)

        if response.status_code == 200 and '"id"' in response.text.lower():
            return True

        return False

    except requests.exceptions.Timeout:
        print("PRICE ALERT TIMEOUT")
        return True

    except Exception as e:
        print("PRICE ALERT ERROR:", e)
        return False
