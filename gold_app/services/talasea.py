import uuid
from decimal import Decimal

import requests
from django.conf import settings


class TalaseaError(Exception):
    pass


class TalaseaClient:

    BASE_URL = "https://apistage.talasea.ir"

    def __init__(self):

        self.api_key = getattr(
            settings,
            "TALASEA_API_KEY",
            None
        )

        if not self.api_key:
            raise TalaseaError(
                "TALASEA_API_KEY در تنظیمات Django تعریف نشده است."
            )

        self.session = requests.Session()

        self.session.headers.update({
            "Accept": "application/json",
            "Content-Type": "application/json",
        })

        self.access_token = None

    # =====================================================
    # LOGIN
    # =====================================================

    def login(self):

        try:

            response = self.session.post(
                f"{self.BASE_URL}/api/partners/login",
                json={
                    "api_key": self.api_key
                },
                timeout=15,
            )

        except requests.RequestException as exc:

            raise TalaseaError(
                f"خطا در اتصال به Talasea: {str(exc)}"
            )

        try:

            data = response.json()

        except ValueError:

            raise TalaseaError(
                "پاسخ نامعتبر از Talasea دریافت شد."
            )

        if response.status_code != 200:

            raise TalaseaError(
                data.get(
                    "message",
                    "ورود به Talasea ناموفق بود."
                )
            )

        access_token = data.get(
            "accessToken"
        )

        if not access_token:

            raise TalaseaError(
                "accessToken از Talasea دریافت نشد."
            )

        self.access_token = access_token

        # Talasea:
        # Authorization: ACCESS_TOKEN
        # بدون Bearer

        self.session.headers.update({
            "Authorization": access_token,
        })

        return {
            "access_token": access_token,
            "expire_in": data.get(
                "expireIn"
            ),
        }

    # =====================================================
    # ENSURE LOGIN
    # =====================================================

    def ensure_login(self):

        if not self.access_token:

            self.login()

        return self.access_token

    # =====================================================
    # REQUEST HELPER
    # =====================================================

    def _request(
        self,
        method,
        endpoint,
        **kwargs
    ):

        self.ensure_login()

        url = f"{self.BASE_URL}{endpoint}"

        try:

            response = self.session.request(
                method,
                url,
                timeout=15,
                **kwargs
            )

        except requests.RequestException as exc:

            raise TalaseaError(
                f"خطا در اتصال به Talasea: {str(exc)}"
            )

        try:

            data = response.json()

        except ValueError:

            data = {}

        # =================================================
        # TOKEN EXPIRED
        # =================================================

        if response.status_code == 401:

            self.access_token = None

            self.login()

            try:

                response = self.session.request(
                    method,
                    url,
                    timeout=15,
                    **kwargs
                )

            except requests.RequestException as exc:

                raise TalaseaError(
                    f"خطا در اتصال مجدد به Talasea: {str(exc)}"
                )

            try:

                data = response.json()

            except ValueError:

                data = {}

        # =================================================
        # HTTP ERROR
        # =================================================

        if response.status_code not in [200, 201]:

            message = data.get(
                "message",
                "خطا در ارتباط با Talasea"
            )

            raise TalaseaError(
                str(message)
            )

        return data

    # =====================================================
    # BALANCES
    # =====================================================

    def get_balances(self):

        return self._request(
            "GET",
            "/api/partners/balances"
        )

    # =====================================================
    # IRT BALANCE
    # =====================================================

    def get_irt_balance(self):

        balances = self.get_balances()

        if not isinstance(balances, list):

            return {
                "asset": "IRT",
                "balance": 0,
                "blocked": 0,
            }

        for item in balances:

            if str(
                item.get("asset", "")
            ).upper() == "IRT":

                return item

        return {
            "asset": "IRT",
            "balance": 0,
            "blocked": 0,
        }

    # =====================================================
    # GOLD BALANCE
    # =====================================================

    def get_gold_balance(self):

        balances = self.get_balances()

        if not isinstance(balances, list):

            return {
                "asset": "GOLD",
                "balance": 0,
                "blocked": 0,
            }

        for item in balances:

            if str(
                item.get("asset", "")
            ).upper() == "GOLD":

                return item

        return {
            "asset": "GOLD",
            "balance": 0,
            "blocked": 0,
        }

    # =====================================================
    # GOLD PRICE
    # =====================================================

    def get_gold_price(self):

        data = self._request(
            "GET",
            "/api/partners/price"
        )

        if not isinstance(data, dict):

            raise TalaseaError(
                "پاسخ قیمت Talasea نامعتبر است."
            )

        gold_price = data.get(
            "goldPrice"
        )

        if gold_price is None:

            raise TalaseaError(
                "goldPrice در پاسخ Talasea وجود ندارد."
            )

        try:

            gold_price = Decimal(
                str(gold_price)
            )

        except Exception:

            raise TalaseaError(
                "قیمت طلا دریافت شده از Talasea نامعتبر است."
            )

        if gold_price <= 0:

            raise TalaseaError(
                "قیمت طلا دریافت شده از Talasea نامعتبر است."
            )

        return gold_price

    # =====================================================
    # GOLD PRICE DETAILS
    # =====================================================

    def get_gold_price_details(self):

        data = self._request(
            "GET",
            "/api/partners/price"
        )

        if not isinstance(data, dict):

            raise TalaseaError(
                "پاسخ قیمت Talasea نامعتبر است."
            )

        gold_price = data.get(
            "goldPrice"
        )

        if gold_price is None:

            raise TalaseaError(
                "goldPrice در پاسخ Talasea وجود ندارد."
            )

        try:

            gold_price = Decimal(
                str(gold_price)
            )

        except Exception:

            raise TalaseaError(
                "قیمت طلا دریافت شده از Talasea نامعتبر است."
            )

        if gold_price <= 0:

            raise TalaseaError(
                "قیمت طلا دریافت شده از Talasea نامعتبر است."
            )

        return {
            "goldPrice": gold_price,
            "change24h": data.get(
                "change24h"
            ),
        }

    # =====================================================
    # BUY GOLD
    # =====================================================

    def buy_gold(
        self,
        volume,
        gold_price,
        request_id=None,
    ):
        """
        ثبت سفارش خرید طلا در Talasea

        Endpoint:
        POST /api/partners/order

        Body:

        {
            "type": "buy",
            "volume": 1000,
            "goldPrice": 22074,
            "requestId": "UUID"
        }
        """

        self.ensure_login()

        # =================================================
        # VALIDATE VOLUME
        # =================================================

        try:

            volume = Decimal(
                str(volume)
            )

        except Exception:

            raise TalaseaError(
                "حجم خرید طلا نامعتبر است."
            )

        if volume <= 0:

            raise TalaseaError(
                "حجم خرید طلا باید بیشتر از صفر باشد."
            )

        # =================================================
        # VALIDATE PRICE
        # =================================================

        try:

            gold_price = Decimal(
                str(gold_price)
            )

        except Exception:

            raise TalaseaError(
                "قیمت طلا نامعتبر است."
            )

        if gold_price <= 0:

            raise TalaseaError(
                "قیمت طلا باید بیشتر از صفر باشد."
            )

        # =================================================
        # REQUEST ID
        # =================================================

        if not request_id:

            request_id = str(
                uuid.uuid4()
            )

        # =================================================
        # PAYLOAD
        # =================================================

        payload = {

            "type": "buy",

            "volume": float(
                volume
            ),

            "goldPrice": float(
                gold_price
            ),

            "requestId": str(
                request_id
            ),
        }


        # =================================================
        # SEND ORDER
        # =================================================

        try:

            response = self.session.post(
                f"{self.BASE_URL}/api/partners/order",
                json=payload,
                timeout=20,
            )

        except requests.RequestException as exc:

            raise TalaseaError(
                f"خطا در ارسال سفارش خرید به Talasea: {str(exc)}"
            )

        # =================================================
        # JSON RESPONSE
        # =================================================

        try:

            data = response.json()

        except ValueError:

            raise TalaseaError(
                "پاسخ نامعتبر از Talasea هنگام ثبت سفارش خرید دریافت شد."
            )



        # =================================================
        # HTTP ERROR
        # =================================================

        if response.status_code not in [200, 201]:

            message = data.get(
                "message",
                "ثبت سفارش خرید در Talasea ناموفق بود."
            )

            code = data.get(
                "code"
            )

            # ---------------------------------------------
            # PRICE CHANGED
            # ---------------------------------------------

            if str(code) == "2010":

                new_price = None

                response_data = data.get(
                    "data"
                )

                if isinstance(
                    response_data,
                    dict
                ):

                    new_price = response_data.get(
                        "goldPrice"
                    )

                if new_price:

                    raise TalaseaError(
                        "قیمت در لحظه خرید تغییر کرده است. "
                        f"قیمت جدید: {new_price}"
                    )

                raise TalaseaError(
                    "قیمت در لحظه خرید تغییر کرده است."
                )

            # ---------------------------------------------
            # TALASEA BALANCE
            # ---------------------------------------------

            if str(code) == "2016":

                raise TalaseaError(
                    "موجودی Talasea برای انجام خرید کافی نیست."
                )

            # ---------------------------------------------
            # MINIMUM BUY
            # ---------------------------------------------

            if str(code) == "1014":

                raise TalaseaError(
                    "حداقل مبلغ خرید 50 هزار تومان می باشد."
                )

            # ---------------------------------------------
            # DUPLICATE REQUEST
            # ---------------------------------------------

            if str(code) == "1020":

                raise TalaseaError(
                    "شناسه سفارش در Talasea تکراری است."
                )

            raise TalaseaError(
                str(message)
            )

        # =================================================
        # SUCCESS
        # =================================================

        return {
            "success": True,

            "message": data.get(
                "message",
                "عملیات با موفقیت انجام شد."
            ),

            "goldPrice": data.get(
                "goldPrice",
                gold_price
            ),

            "volume": data.get(
                "volume",
                volume
            ),

            "fee": data.get(
                "fee",
                0
            ),

            "strStatus": data.get(
                "strStatus",
                "PENDING"
            ),

            "totalValue": data.get(
                "totalValue"
            ),

            "requestId": data.get(
                "requestId",
                request_id
            ),
        }

    # =====================================================
    # SELL GOLD
    # =====================================================

    def sell_gold(
        self,
        volume,
        gold_price,
        request_id=None,
    ):
        """
        ثبت سفارش فروش طلا در Talasea

        Endpoint:
        POST /api/partners/order

        Body:

        {
            "type": "sell",
            "volume": 1000,
            "goldPrice": 22074,
            "requestId": "UUID"
        }

        مثال:

        volume = 1000
        gold_price = 22074

        نتیجه:

        {
            "message": "عملیات با موفقیت انجام شد.",
            "goldPrice": 22074,
            "volume": 1000,
            "fee": 0.01,
            "strStatus": "PENDING",
            "totalValue": 21853260
        }
        """

        self.ensure_login()

        # =================================================
        # VALIDATE VOLUME
        # =================================================

        try:

            volume = Decimal(
                str(volume)
            )

        except Exception:

            raise TalaseaError(
                "حجم فروش طلا نامعتبر است."
            )

        if volume <= 0:

            raise TalaseaError(
                "حجم فروش طلا باید بیشتر از صفر باشد."
            )

        # =================================================
        # VALIDATE PRICE
        # =================================================

        try:

            gold_price = Decimal(
                str(gold_price)
            )

        except Exception:

            raise TalaseaError(
                "قیمت طلا نامعتبر است."
            )

        if gold_price <= 0:

            raise TalaseaError(
                "قیمت طلا باید بیشتر از صفر باشد."
            )

        # =================================================
        # REQUEST ID
        # =================================================

        if not request_id:

            request_id = str(
                uuid.uuid4()
            )

        # =================================================
        # PAYLOAD
        # =================================================

        payload = {

            "type": "sell",

            "volume": float(
                volume
            ),

            "goldPrice": float(
                gold_price
            ),

            "requestId": str(
                request_id
            ),
        }

        # =================================================
        # DEBUG LOG
        # =================================================



        # =================================================
        # SEND ORDER
        # =================================================

        try:

            response = self.session.post(
                f"{self.BASE_URL}/api/partners/order",
                json=payload,
                timeout=20,
            )

        except requests.RequestException as exc:

            raise TalaseaError(
                f"خطا در ارسال سفارش فروش به Talasea: {str(exc)}"
            )

        # =================================================
        # JSON RESPONSE
        # =================================================

        try:

            data = response.json()

        except ValueError:

            raise TalaseaError(
                "پاسخ نامعتبر از Talasea هنگام ثبت سفارش فروش دریافت شد."
            )

        # =================================================
        # DEBUG RESPONSE
        # =================================================



        # =================================================
        # HTTP ERROR
        # =================================================

        if response.status_code not in [200, 201]:

            message = data.get(
                "message",
                "ثبت سفارش فروش در Talasea ناموفق بود."
            )

            code = data.get(
                "code"
            )

            # ---------------------------------------------
            # PRICE CHANGED
            # ---------------------------------------------

            if str(code) == "2010":

                new_price = None

                response_data = data.get(
                    "data"
                )

                if isinstance(
                    response_data,
                    dict
                ):

                    new_price = response_data.get(
                        "goldPrice"
                    )

                if new_price:

                    raise TalaseaError(
                        "قیمت در لحظه فروش تغییر کرده است. "
                        f"قیمت جدید: {new_price}"
                    )

                raise TalaseaError(
                    "قیمت در لحظه فروش تغییر کرده است."
                )

            # ---------------------------------------------
            # TALASEA GOLD BALANCE
            # ---------------------------------------------

            if str(code) == "2016":

                raise TalaseaError(
                    "موجودی طلا در Talasea برای انجام فروش کافی نیست."
                )

            # ---------------------------------------------
            # MINIMUM SELL
            # ---------------------------------------------

            if str(code) == "1014":

                raise TalaseaError(
                    "حداقل مبلغ فروش 50 هزار تومان می باشد."
                )

            # ---------------------------------------------
            # DUPLICATE REQUEST
            # ---------------------------------------------

            if str(code) == "1020":

                raise TalaseaError(
                    "شناسه سفارش در Talasea تکراری است."
                )

            # ---------------------------------------------
            # DEFAULT
            # ---------------------------------------------

            raise TalaseaError(
                str(message)
            )

        # =================================================
        # SUCCESS
        # =================================================

        return {

            "success": True,

            "message": data.get(
                "message",
                "عملیات با موفقیت انجام شد."
            ),

            "goldPrice": data.get(
                "goldPrice",
                gold_price
            ),

            "volume": data.get(
                "volume",
                volume
            ),

            "fee": data.get(
                "fee",
                0
            ),

            "strStatus": data.get(
                "strStatus",
                "PENDING"
            ),

            "totalValue": data.get(
                "totalValue"
            ),

            "requestId": data.get(
                "requestId",
                request_id
            ),
        }