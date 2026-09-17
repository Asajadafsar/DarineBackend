import json
import time
import redis
from datetime import datetime


# ============================================================
# Hanzaei Gold - Valkey Pub/Sub Monitor
# ============================================================

HOST = "vkey.hanzaeigold.com"
PORT = 6379

USERNAME = "api:755"
PASSWORD = "4273e46cf2ad23ea1646ebda3daa70dbacd04ce68f3ff5170fed1324eaa1f61f"

CHANNEL = "prices:pubsub:group:1"

PRODUCT_ID = 60
PRODUCT_NAME = "gold - 18 - farda"

UPDATE_INTERVAL = 60


# ============================================================
# اتصال به Valkey
# ============================================================

client = redis.Redis(
    host=HOST,
    port=PORT,
    username=USERNAME,
    password=PASSWORD,

    # فعلاً برای تست
    ssl=False,

    decode_responses=True,

    socket_timeout=10,
    socket_connect_timeout=10,

    health_check_interval=30,

    retry_on_timeout=True,
)


# ============================================================
# تست اتصال
# ============================================================

print("=" * 60)
print("HANZAEI GOLD PRICE MONITOR")
print("=" * 60)

try:
    print("Connecting to Valkey...")

    response = client.ping()

    if response:
        print("Connection: OK")

except Exception as e:
    print()
    print("Connection ERROR:")
    print(type(e).__name__)
    print(str(e))
    print()

    try:
        client.close()
    except Exception:
        pass

    raise SystemExit(1)


# ============================================================
# Pub/Sub
# ============================================================

print()
print("Creating Pub/Sub connection...")

try:

    pubsub = client.pubsub(
        ignore_subscribe_messages=False
    )

    pubsub.subscribe(CHANNEL)

    print(f"Channel: {CHANNEL}")
    print(f"Product: {PRODUCT_NAME}")
    print(f"Product ID: {PRODUCT_ID}")

    print()
    print("Waiting for price updates...")
    print()

except Exception as e:

    print()
    print("Pub/Sub ERROR:")
    print(type(e).__name__)
    print(str(e))
    print()

    client.close()

    raise SystemExit(1)


# ============================================================
# قیمت‌ها
# ============================================================

price_buy = None
price_sell = None
last_update = None


next_print = time.monotonic() + UPDATE_INTERVAL


# ============================================================
# پردازش پیام‌ها
# ============================================================

try:

    while True:

        message = pubsub.get_message(
            ignore_subscribe_messages=False,
            timeout=1
        )

        if message:

            message_type = message.get("type")

            # ------------------------------------------------
            # Subscribe confirmation
            # ------------------------------------------------

            if message_type == "subscribe":

                print(
                    f"[SUBSCRIBED] "
                    f"{message.get('channel')} "
                    f"=> {message.get('data')}"
                )

            # ------------------------------------------------
            # Message
            # ------------------------------------------------

            elif message_type == "message":

                raw_data = message.get("data")

                print()
                print("[MESSAGE RECEIVED]")
                print("-" * 60)

                try:

                    data = json.loads(raw_data)

                    print(f"Event: {data.get('event')}")
                    print(f"At: {data.get('at')}")

                    # فقط price_updated
                    if data.get("event") != "price_updated":
                        print("Ignoring event.")
                        continue

                    products = data.get("products", [])

                    print(f"Products in message: {len(products)}")

                    found = False

                    for product in products:

                        product_id = product.get("id")

                        print(
                            f"Product ID: {product_id} | "
                            f"Name: {product.get('name')}"
                        )

                        if product_id != PRODUCT_ID:
                            continue

                        found = True

                        price_buy = product.get("price_buy")
                        price_sell = product.get("price_sell")

                        last_update = data.get("at")

                        print()
                        print("🔥 TARGET PRODUCT FOUND")
                        print(
                            f"Name: {product.get('name')}"
                        )
                        print(
                            f"ID: {product_id}"
                        )
                        print(
                            f"Buy: {price_buy:,}"
                            if price_buy is not None
                            else "Buy: None"
                        )
                        print(
                            f"Sell: {price_sell:,}"
                            if price_sell is not None
                            else "Sell: None"
                        )
                        print(
                            f"Updated At: {last_update}"
                        )

                    if not found:
                        print()
                        print(
                            f"Product ID {PRODUCT_ID} "
                            f"not found in this message."
                        )

                except json.JSONDecodeError as e:

                    print("JSON ERROR:")
                    print(e)

                    print()
                    print("Raw message:")
                    print(raw_data)

                except Exception as e:

                    print("MESSAGE ERROR:")
                    print(type(e).__name__)
                    print(str(e))

                print("-" * 60)


        # ====================================================
        # نمایش وضعیت هر 60 ثانیه
        # ====================================================

        now = time.monotonic()

        if now >= next_print:

            current_time = datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )

            print()
            print("=" * 60)
            print("CURRENT STATUS")
            print("=" * 60)

            print(f"Time: {current_time}")
            print(f"Product: {PRODUCT_NAME}")
            print(f"Product ID: {PRODUCT_ID}")

            if price_buy is not None:

                print(
                    f"قیمت خرید: {price_buy:,}"
                )

                print(
                    f"قیمت فروش: {price_sell:,}"
                    if price_sell is not None
                    else "قیمت فروش: None"
                )

                print(
                    f"آخرین آپدیت: {last_update}"
                )

            else:

                print("هنوز قیمت دریافت نشده است.")

            print("=" * 60)
            print()

            next_print += UPDATE_INTERVAL

            if next_print <= now:
                next_print = now + UPDATE_INTERVAL


# ============================================================
# خروج
# ============================================================

except KeyboardInterrupt:

    print()
    print("=" * 60)
    print("Program stopped.")
    print("=" * 60)


except Exception as e:

    print()
    print("=" * 60)
    print("FATAL ERROR")
    print("=" * 60)
    print(type(e).__name__)
    print(str(e))


finally:

    try:
        pubsub.close()
    except Exception:
        pass

    try:
        client.close()
    except Exception:
        pass