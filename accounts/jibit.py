# accounts/jibit.py
import requests
from datetime import datetime
import jdatetime

API_KEY = "AY6RMjajiz"
SECRET_KEY = "4CpFJP2KaWHBHIC7lMBxzKZly"
BASE_URL = "https://napi.jibit.ir/ide"


def get_access_token():
    """دریافت توکن جدید از Jibit"""
    url = f"{BASE_URL}/v1/tokens/generate"
    headers = {"Content-Type": "application/json"}
    body = {"apiKey": API_KEY, "secretKey": SECRET_KEY}

    response = requests.post(url, headers=headers, json=body, timeout=15)
    data = response.json()

    if response.status_code != 200:
        raise Exception(f"خطا در دریافت توکن: {data}")

    return data["accessToken"]


def shahkar_match(national_code, mobile_number):
    """
    بررسی تطابق کد ملی با شماره موبایل
    
    Raises:
        Exception: با پیام‌های مختلف بر اساس نوع خطا
    """
    token = get_access_token()
    url = f"{BASE_URL}/v1/services/matching"
    headers = {"Authorization": f"Bearer {token}"}
    params = {
        "nationalCode": national_code,
        "mobileNumber": mobile_number,
    }

    response = requests.get(url, headers=headers, params=params, timeout=15)
    data = response.json()

    # =============================================
    # مدیریت خطاهای مختلف
    # =============================================
    
    if response.status_code == 400:
        error_message = data.get("message", "")
        error_data = str(data).lower()
        
        # ۱. کد ملی در ثبت احوال وجود ندارد
        if "not found" in error_data or "وجود ندارد" in error_message or "nationalcode" in error_data:
            raise Exception("کد ملی وارد شده در ثبت احوال موجود نیست")
        
        # ۲. شماره موبایل نامعتبر
        elif "mobile" in error_data and ("invalid" in error_data or "نامعتبر" in error_message):
            raise Exception("شماره موبایل وارد شده نامعتبر است")
        
        # ۳. عدم تطابق کد ملی و شماره موبایل
        elif "not match" in error_data or "mismatch" in error_data or "تطابق" in error_message:
            raise Exception("مالکیت کد ملی و شماره موبایل وارد شده مطابقت ندارد")
        
        # ۴. سایر خطاها
        else:
            raise Exception(error_message or "اطلاعات وارد شده نامعتبر است")
    
    elif response.status_code != 200:
        error_message = data.get("message", "خطا در ارتباط با سرویس احراز هویت")
        raise Exception(error_message)

    # =============================================
    # بررسی نتیجه تطابق
    # =============================================
    matched = data.get("matched", False)
    
    # اگر matched == False باشد، یعنی تطابق ندارند
    if not matched:
        raise Exception("مالکیت کد ملی و شماره موبایل وارد شده مطابقت ندارد")
    
    return True


def iban_matching(national_code, iban, birth_date_gregorian):
    """
    بررسی تطابق شماره شبا با کد ملی و تاریخ تولد
    """
    token = get_access_token()
    url = f"{BASE_URL}/v1/services/matching"
    headers = {"Authorization": f"Bearer {token}"}
    
    import jdatetime
    
    shamsi_date = jdatetime.date.fromgregorian(date=birth_date_gregorian)
    birth_date_str = shamsi_date.strftime("%Y%m%d")
    
    if not iban.startswith("IR"):
        iban = f"IR{iban}"
    
    params = {
        "nationalCode": national_code,
        "iban": iban,
        "birthDate": birth_date_str
    }

    response = requests.get(url, headers=headers, params=params, timeout=15)
    data = response.json()

    if response.status_code != 200:
        error_msg = data.get("message", "خطا در ارتباط با سرویس احراز هویت")
        error_str = str(data).lower()
        if "iban" in error_str or "شبا" in error_str:
            raise Exception("شبا نامعتبر است")
        elif "nationalcode" in error_str or "کد ملی" in error_str:
            raise Exception("کد ملی وارد شده در ثبت احوال موجود نیست")
        elif "birthdate" in error_str or "تاریخ تولد" in error_str:
            raise Exception("تاریخ تولد نامعتبر است")
        elif "not match" in error_str or "mismatch" in error_str:
            raise Exception("مالکیت کد ملی و شماره شبا مطابقت ندارد")
        else:
            raise Exception(error_msg)

    return {
        "matched": data.get("matched", False),
        "iban_info": data.get("ibanInfo", {})
    }


def get_iban_info(iban):
    """
    دریافت اطلاعات شماره شبا (بدون احراز هویت)
    """
    token = get_access_token()
    url = f"{BASE_URL}/v1/ibans"
    headers = {"Authorization": f"Bearer {token}"}
    
    if not iban.startswith("IR"):
        iban = f"IR{iban}"
    
    params = {"value": iban}

    response = requests.get(url, headers=headers, params=params, timeout=15)
    data = response.json()

    if response.status_code != 200:
        error_msg = data.get("message", "خطا در دریافت اطلاعات شبا")
        raise Exception(error_msg)

    return data.get("ibanInfo", {})


def get_full_iban_info(iban):
    """
    دریافت اطلاعات کامل شبا با فرمت مناسب برای نمایش
    """
    iban_info = get_iban_info(iban)
    
    owners = iban_info.get("owners", [])
    owner_names = []
    for owner in owners:
        first_name = owner.get("firstName", "")
        last_name = owner.get("lastName", "")
        owner_names.append({
            "first_name": first_name,
            "last_name": last_name
        })
    
    owner_full_name = ""
    if owner_names:
        owner_full_name = f"{owner_names[0]['first_name']} {owner_names[0]['last_name']}".strip()
    
    return {
        "iban": iban_info.get("iban", ""),
        "bank": iban_info.get("bank", ""),
        "deposit_number": iban_info.get("depositNumber", ""),
        "status": iban_info.get("status", ""),
        "owners": owner_names,
        "owner_full_name": owner_full_name
    }