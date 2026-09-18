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

    # =====================================================
    # PHYSICAL DELIVERY - 1. دریافت همه کالاها
    # GET /api/partners/commodity
    # =====================================================

    def get_commodities(self):
        """
        دریافت لیست کالاهای قابل تحویل فیزیکی

        Response:
        {
            "categories": [
                {
                    "category": "gold_BAR",
                    "items": [
                        {
                            "title": "string",
                            "feeIrt": 0,
                            "feeGold": 0,
                            "irt_price": 0,
                            "gold_price": 0,
                            "id": "string",
                            "stock": 0,
                            "imgUrl": "string"
                        }
                    ]
                }
            ]
        }
        """

        return self._request(
            "GET",
            "/api/partners/commodity"
        )

    # =====================================================
    # PHYSICAL DELIVERY - 2. دریافت زمان‌های در دسترس
    # GET /api/partners/goldReceive/time
    # =====================================================

    def get_receive_times(self):
        """
        دریافت زمان‌های قابل انتخاب جهت مراجعه حضوری به مغازه

        Response:
        {
            "address": "string",
            "dates.date": "string",
            "dates.day": "string",
            "dates.times.time": "string",
            "dates.times.id": "string"
        }
        """

        return self._request(
            "GET",
            "/api/partners/goldReceive/time"
        )

    # =====================================================
    # PHYSICAL DELIVERY - 3. دریافت لیست شهرها
    # GET /api/partners/locations/getCities/:id
    # =====================================================

    def get_cities(self, province_id=0):
        """
        دریافت لیست استان‌ها و شهرها

        Args:
            province_id: اگر 0 باشد، لیست استان‌ها برمی‌گردد.
                        برای دریافت شهرهای یک استان، ID همان استان ارسال شود.

        Response:
        [
            {
                "city_id": 101,
                "city_name": "تهران",
                "state_id": 1,
                "status": "ACTIVE",
                "province_id": 1,
                "createdAt": "...",
                "updatedAt": "..."
            }
        ]
        """

        try:

            province_id = int(province_id)

        except (ValueError, TypeError):

            province_id = 0

        return self._request(
            "GET",
            f"/api/partners/locations/getCities/{province_id}"
        )

    # =====================================================
    # PHYSICAL DELIVERY - 4. محاسبه هزینه ارسال
    # POST /api/partners/goldReceive/calculateShipmentCost/:type
    # =====================================================

    def calculate_shipment_cost(
        self,
        items,
        delivery_type="PHYSICAL_DELIVERY",
        address_id=None,
    ):
        """
        محاسبه هزینه درخواست تحویل فیزیکی

        Args:
            items: [{"commodityId": "string", "count": 0}, ...]
            delivery_type: "PHYSICAL_DELIVERY" یا "DIGIEXPRESS_DELIVERY"
            address_id: city_id / state_id (برای DIGIEXPRESS اجباری)

        Response:
        {
            "info": {
                "pureGold": 12.5,
                "pureIrt": 15000000,
                "totalGold": 12.65,
                "totalIrt": 15180000,
                "shipmentCostGold": 0.15,
                "shipmentCostIRT": 180000,
                "totalPureQuantity": 12.5,
                "totalItemPriceIRT": 15000000,
                "totalPureAmount": 15000000,
                "feePercent": 2.5,
                "totalFeePercent": 2.5,
                "totalFeeIRT": 375000
            },
            "insurance": {...},
            "delivery": {...},
            "items": [...]
        }
        """

        if not items:

            raise TalaseaError(
                "لیست کالاها نمی‌تواند خالی باشد."
            )

        if delivery_type not in [
            "PHYSICAL_DELIVERY",
            "DIGIEXPRESS_DELIVERY",
        ]:

            raise TalaseaError(
                "نوع تحویل نامعتبر است."
            )

        if (
            delivery_type == "DIGIEXPRESS_DELIVERY"
            and address_id is None
        ):

            raise TalaseaError(
                "برای ارسال با دیجی‌اکسپرس، شناسه آدرس (addressId) اجباری است."
            )

        payload = {
            "items": items,
        }

        if address_id is not None:

            try:

                payload["addressId"] = int(address_id)

            except (ValueError, TypeError):

                raise TalaseaError(
                    "شناسه آدرس (addressId) نامعتبر است."
                )

        return self._request(
            "POST",
            f"/api/partners/goldReceive/calculateShipmentCost/{delivery_type}",
            json=payload
        )

    # =====================================================
    # PHYSICAL DELIVERY - 5. ایجاد درخواست تحویل حضوری
    # POST /api/partners/goldReceive
    # =====================================================

    def create_physical_receive(
        self,
        commodity_id,
        count,
        gold_price,
        user_phone_number,
        user_national_code,
        time_id,
        request_id=None,
    ):
        """
        ایجاد درخواست دریافت طلا از مغازه / تحویل حضوری

        Endpoint:
        POST /api/partners/goldReceive

        Body:
        {
            "commodityId": "string",
            "count": 1,
            "goldPrice": 8000,
            "userPhoneNumber": "",
            "userNationalCode": "",
            "timeId": "",
            "requestId": ""
        }

        Response:
        {
            "message": "string"
        }
        """

        self.ensure_login()

        # =================================================
        # VALIDATE
        # =================================================

        if not commodity_id:

            raise TalaseaError(
                "شناسه کالا (commodityId) الزامی است."
            )

        try:

            count = int(count)

        except (ValueError, TypeError):

            raise TalaseaError(
                "تعداد کالا نامعتبر است."
            )

        if count < 1:

            raise TalaseaError(
                "تعداد کالا باید حداقل ۱ باشد."
            )

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

        if not user_phone_number:

            raise TalaseaError(
                "شماره تلفن کاربر الزامی است."
            )

        if not user_national_code:

            raise TalaseaError(
                "کد ملی کاربر الزامی است."
            )

        if not time_id:

            raise TalaseaError(
                "شناسه زمان دریافت (timeId) الزامی است."
            )

        if not request_id:

            request_id = str(
                uuid.uuid4()
            )

        # =================================================
        # PAYLOAD
        # =================================================

        payload = {

            "commodityId": str(commodity_id),

            "count": count,

            "goldPrice": float(gold_price),

            "userPhoneNumber": str(user_phone_number),

            "userNationalCode": str(user_national_code),

            "timeId": str(time_id),

            "requestId": str(request_id),
        }

        # =================================================
        # SEND
        # =================================================

        try:

            response = self.session.post(
                f"{self.BASE_URL}/api/partners/goldReceive",
                json=payload,
                timeout=20,
            )

        except requests.RequestException as exc:

            raise TalaseaError(
                f"خطا در ارسال درخواست تحویل حضوری به Talasea: {str(exc)}"
            )

        try:

            data = response.json()

        except ValueError:

            raise TalaseaError(
                "پاسخ نامعتبر از Talasea هنگام ثبت درخواست تحویل حضوری دریافت شد."
            )

        # =================================================
        # HTTP ERROR
        # =================================================

        if response.status_code not in [200, 201]:

            message = data.get(
                "message",
                "ثبت درخواست تحویل حضوری در Talasea ناموفق بود."
            )

            code = str(
                data.get("code", "")
            )

            if code == "2010":

                new_price = (
                    data.get("data") or {}
                ).get("price")

                if new_price:

                    raise TalaseaError(
                        "قیمت در لحظه تغییر کرده است. "
                        f"قیمت جدید: {new_price}"
                    )

                raise TalaseaError(
                    "قیمت در لحظه تغییر کرده است."
                )

            if code == "2012":

                raise TalaseaError(
                    "در حال حاضر امکان دریافت این کالا وجود ندارد."
                )

            if code == "2013":

                raise TalaseaError(
                    "حداکثر وزن قابل دریافت در هر مرحله ۱۰۰ گرم می‌باشد."
                )

            if code == "2016":

                raise TalaseaError(
                    "موجودی شما در Talasea کافی نیست."
                )

            if code == "2017":

                raise TalaseaError(
                    "در حال حاضر امکان دریافت این زمان وجود ندارد."
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
                "درخواست تحویل حضوری با موفقیت ثبت شد."
            ),

            "requestId": request_id,

            "raw": data,
        }

    # =====================================================
    # PHYSICAL DELIVERY - 6. ایجاد سبد تحویل (Bulk)
    # POST /api/partners/goldReceive/bulk/:type
    # =====================================================

    def create_bulk_receive(
        self,
        items,
        gold_price,
        user_phone_number,
        user_national_code,
        loca,
        delivery_type="PHYSICAL_DELIVERY",
        time_id=None,
        base_asset="gold",
        request_id=None,
        address_id=None,
    ):
        """
        ایجاد سبد تحویل فیزیکی (ارسال درب منزل / دیجی‌اکسپرس)

        Endpoint:
        POST /api/partners/goldReceive/bulk/:type

        Args:
            items: [{"commodityId": "string", "count": 0}, ...]
            gold_price: قیمت لحظه‌ای طلا (مقیاس Talasea)
            user_phone_number: شماره تلفن
            user_national_code: کد ملی
            loca: {
                "address": "string",
                "postalCode": "string",
                "buildingNumber": "string",
                "apartmentNumber": "string",
                "locationId": 0,  # city_id
                "long": 0,
                "lat": 0,
                "firstName": "string",
                "lastName": "string"
            }
            delivery_type: "PHYSICAL_DELIVERY" یا "DIGIEXPRESS_DELIVERY"
            time_id: فقط برای PHYSICAL_DELIVERY
            base_asset: "IRT" یا "gold" (پیش‌فرض gold)
            request_id: شناسه یکتا
            address_id: city_id (برای DIGIEXPRESS اجباری)

        Response:
        {
            "message": "پردازش سبد انجام شد.",
            "requestIds": "string"
        }
        """

        self.ensure_login()

        # =================================================
        # VALIDATE ITEMS
        # =================================================

        if not items:

            raise TalaseaError(
                "لیست کالاها نمی‌تواند خالی باشد."
            )

        for idx, item in enumerate(items):

            if "commodityId" not in item:

                raise TalaseaError(
                    f"commodityId برای آیتم {idx + 1} الزامی است."
                )

            if "count" not in item:

                raise TalaseaError(
                    f"count برای آیتم {idx + 1} الزامی است."
                )

            try:

                count = int(item["count"])

            except (ValueError, TypeError):

                raise TalaseaError(
                    f"تعداد آیتم {idx + 1} نامعتبر است."
                )

            if count < 1:

                raise TalaseaError(
                    f"تعداد آیتم {idx + 1} باید حداقل ۱ باشد."
                )

        # =================================================
        # VALIDATE DELIVERY TYPE
        # =================================================

        if delivery_type not in [
            "PHYSICAL_DELIVERY",
            "DIGIEXPRESS_DELIVERY",
        ]:

            raise TalaseaError(
                "نوع تحویل نامعتبر است."
            )

        # =================================================
        # VALIDATE TIME (فقط برای PHYSICAL_DELIVERY)
        # =================================================

        if delivery_type == "PHYSICAL_DELIVERY" and not time_id:

            raise TalaseaError(
                "برای تحویل با پست (PHYSICAL_DELIVERY)، شناسه زمان (timeId) الزامی است."
            )

        # =================================================
        # VALIDATE ADDRESS_ID (برای DIGIEXPRESS)
        # =================================================

        if (
            delivery_type == "DIGIEXPRESS_DELIVERY"
            and address_id is None
        ):

            raise TalaseaError(
                "برای ارسال با دیجی‌اکسپرس، شناسه شهر (addressId) اجباری است."
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
        # VALIDATE USER INFO
        # =================================================

        if not user_phone_number:

            raise TalaseaError(
                "شماره تلفن کاربر الزامی است."
            )

        if not user_national_code:

            raise TalaseaError(
                "کد ملی کاربر الزامی است."
            )

        # =================================================
        # VALIDATE LOCA
        # =================================================

        if not isinstance(loca, dict):

            raise TalaseaError(
                "اطلاعات آدرس (loca) نامعتبر است."
            )

        required_loca_fields = [
            "address",
            "postalCode",
            "buildingNumber",
            "apartmentNumber",
            "locationId",
            "long",
            "lat",
            "firstName",
            "lastName",
        ]

        for field in required_loca_fields:

            if field not in loca:

                raise TalaseaError(
                    f"فیلد {field} در اطلاعات آدرس الزامی است."
                )

        # =================================================
        # VALIDATE BASE ASSET
        # =================================================

        if base_asset not in ["IRT", "gold"]:

            raise TalaseaError(
                "baseAsset باید IRT یا gold باشد."
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

            "items": [
                {
                    "commodityId": str(item["commodityId"]),
                    "count": int(item["count"]),
                }
                for item in items
            ],

            "requestId": str(request_id),

            "baseAsset": base_asset,

            "goldPrice": float(gold_price),

            "userPhoneNumber": str(user_phone_number),

            "userNationalCode": str(user_national_code),

            "loca": loca,
        }

        if time_id:

            payload["timeId"] = str(time_id)

        if address_id is not None:

            try:

                payload["addressId"] = int(address_id)

            except (ValueError, TypeError):

                raise TalaseaError(
                    "شناسه آدرس (addressId) نامعتبر است."
                )

        # =================================================
        # SEND
        # =================================================

        try:

            response = self.session.post(
                f"{self.BASE_URL}/api/partners/goldReceive/bulk/{delivery_type}",
                json=payload,
                timeout=30,
            )

        except requests.RequestException as exc:

            raise TalaseaError(
                f"خطا در ارسال سبد تحویل به Talasea: {str(exc)}"
            )

        try:

            data = response.json()

        except ValueError:

            raise TalaseaError(
                "پاسخ نامعتبر از Talasea هنگام ثبت سبد تحویل دریافت شد."
            )

        # =================================================
        # HTTP ERROR
        # =================================================

        if response.status_code not in [200, 201]:

            message = data.get(
                "message",
                "ثبت سبد تحویل در Talasea ناموفق بود."
            )

            code = str(
                data.get("code", "")
            )

            if code == "2010":

                new_price = (
                    data.get("data") or {}
                ).get("price")

                if new_price:

                    raise TalaseaError(
                        "قیمت در لحظه تغییر کرده است. "
                        f"قیمت جدید: {new_price}"
                    )

                raise TalaseaError(
                    "قیمت در لحظه تغییر کرده است."
                )

            if code == "2012":

                raise TalaseaError(
                    "در حال حاضر امکان دریافت این کالا وجود ندارد."
                )

            if code == "2013":

                raise TalaseaError(
                    "حداکثر وزن قابل دریافت در هر مرحله ۱۰۰ گرم می‌باشد."
                )

            if code == "2016":

                raise TalaseaError(
                    "موجودی طلای شما در Talasea کافی نیست."
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
                "سبد تحویل با موفقیت ثبت شد."
            ),

            "requestId": request_id,

            "requestIds": data.get("requestIds"),

            "raw": data,
        }

    # =====================================================
    # PHYSICAL DELIVERY - 7. دریافت همه درخواست‌ها
    # GET /api/partners/goldReceive
    # =====================================================

    def list_receives(
        self,
        user_phone_number=None,
        user_national_code=None,
        from_date=None,
        end_date=None,
        page=None,
        page_size=None,
        request_id=None,
    ):
        """
        دریافت همه درخواست‌های تحویل طلا

        Endpoint:
        GET /api/partners/goldReceive

        Response:
        [
            {
                "createdAt": "string",
                "updatedAt": "string",
                "goldPrice": 0,
                "count": 0,
                "status": 0,
                "totalValue": 0,
                "strReceiveTime": "string",
                "receiveTime": "string",
                "userPhoneNumber": "string",
                "userNationalCode": "string",
                "persianCreatedAt": "string"
            }
        ]
        """

        params = {}

        if user_phone_number:

            params["userPhoneNumber"] = str(
                user_phone_number
            )

        if user_national_code:

            params["userNationalCode"] = str(
                user_national_code
            )

        if from_date:

            params["fromDate"] = str(from_date)

        if end_date:

            params["endDate"] = str(end_date)

        if page:

            params["page"] = str(page)

        if page_size:

            params["pageSize"] = str(page_size)

        if request_id:

            params["requestId"] = str(request_id)

        return self._request(
            "GET",
            "/api/partners/goldReceive",
            params=params
        )

    # =====================================================
    # PHYSICAL DELIVERY - 8. لغو درخواست دریافت طلا
    # POST /api/partners/cancelReceive
    # =====================================================

    def cancel_receive(self, request_id):
        """
        لغو درخواست دریافت طلا

        Endpoint:
        POST /api/partners/cancelReceive

        Body:
        {
            "requestId": "string"
        }

        Response:
        {
            "message": "string"
        }
        """

        self.ensure_login()

        if not request_id:

            raise TalaseaError(
                "شناسه درخواست (requestId) الزامی است."
            )

        payload = {

            "requestId": str(request_id),
        }

        # =================================================
        # SEND
        # =================================================

        try:

            response = self.session.post(
                f"{self.BASE_URL}/api/partners/cancelReceive",
                json=payload,
                timeout=20,
            )

        except requests.RequestException as exc:

            raise TalaseaError(
                f"خطا در لغو درخواست Talasea: {str(exc)}"
            )

        try:

            data = response.json()

        except ValueError:

            raise TalaseaError(
                "پاسخ نامعتبر از Talasea هنگام لغو درخواست دریافت شد."
            )

        # =================================================
        # HTTP ERROR
        # =================================================

        if response.status_code not in [200, 201]:

            message = data.get(
                "message",
                "لغو درخواست در Talasea ناموفق بود."
            )

            code = str(
                data.get("code", "")
            )

            if code == "2020":

                raise TalaseaError(
                    "درخواست یافت نشد."
                )

            if code == "2021":

                raise TalaseaError(
                    "امکان لغو دوباره این مورد وجود ندارد."
                )

            if code == "2022":

                raise TalaseaError(
                    "در حال حاضر امکان لغو این مورد وجود ندارد."
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
                "درخواست با موفقیت لغو شد."
            ),

            "requestId": request_id,

            "raw": data,
        }


