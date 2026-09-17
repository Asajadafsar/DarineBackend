import json
import logging

import redis

from django.conf import settings
from django.core.management.base import BaseCommand
from django.core.cache import cache


logger = logging.getLogger(__name__)


class Command(BaseCommand):

    help = "Listen to Hanzaei Gold Valkey price updates"

    def handle(self, *args, **options):

        config = settings.HANZAEI_VALKEY

        self.stdout.write(
            self.style.SUCCESS(
                "Starting Hanzaei Gold Valkey listener..."
            )
        )

        client = redis.Redis(
            host=config["HOST"],
            port=config["PORT"],
            username=config["USERNAME"],
            password=config["PASSWORD"],

            # rediss
            ssl=True,

            decode_responses=True,

            socket_connect_timeout=10,
            socket_timeout=None,

            health_check_interval=30,

        )

        pubsub = client.pubsub()

        channel = config["CHANNEL"]

        try:

            # تست اتصال
            client.ping()

            self.stdout.write(
                self.style.SUCCESS(
                    "Connected to Hanzaei Valkey."
                )
            )

            pubsub.subscribe(channel)

            self.stdout.write(
                self.style.SUCCESS(
                    f"Subscribed to: {channel}"
                )
            )

            for message in pubsub.listen():

                if message["type"] != "message":
                    continue

                raw_data = message["data"]

                try:

                    data = json.loads(raw_data)

                except json.JSONDecodeError:

                    logger.error(
                        f"Invalid Hanzaei JSON: {raw_data}"
                    )

                    continue

                if data.get("event") != "price_updated":
                    continue

                products = data.get(
                    "products",
                    []
                )

                logger.info(
                    f"Hanzaei price update received: "
                    f"{len(products)} products"
                )

                # ---------------------------------
                # پیدا کردن محصولات
                # ---------------------------------

                gold_18 = None
                mazaneh = None

                for product in products:

                    product_id = product.get(
                        "id"
                    )

                    name = str(
                        product.get(
                            "name",
                            ""
                        )
                    )

                    # ---------------------------------
                    # گرم 18 نقد فردا
                    # ---------------------------------

                    if (
                        "گرم 18 نقد فردا" in name
                        or
                        "گرم ۱۸ نقد فردا" in name
                    ):
                        gold_18 = product

                    # ---------------------------------
                    # مظنه
                    # ---------------------------------

                    elif "مظنه" in name:
                        mazaneh = product

                # ---------------------------------
                # ذخیره آخرین Event
                # ---------------------------------

                result = {
                    "event": data.get(
                        "event"
                    ),

                    "at": data.get(
                        "at"
                    ),

                    "setting": data.get(
                        "setting"
                    ),

                    "gold_18_cash_tomorrow": (
                        gold_18
                    ),

                    "mazaneh": mazaneh,

                    "products": products,
                }

                cache.set(
                    "hanzaei_gold_latest",
                    result,
                    timeout=None,
                )

                # ---------------------------------
                # کش جداگانه قیمت‌ها
                # ---------------------------------

                if gold_18:

                    cache.set(
                        "hanzaei_gold_18",
                        gold_18,
                        timeout=None,
                    )

                if mazaneh:

                    cache.set(
                        "hanzaei_mazaneh",
                        mazaneh,
                        timeout=None,
                    )

                logger.info(
                    "Hanzaei prices cached successfully."
                )

        except Exception as e:

            logger.exception(
                f"Hanzaei Valkey listener error: {e}"
            )

            raise

        finally:

            try:
                pubsub.close()
            except Exception:
                pass

            try:
                client.close()
            except Exception:
                pass