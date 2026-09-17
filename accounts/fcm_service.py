# accounts/fcm_service.py

import logging
import os
import requests

import firebase_admin
from firebase_admin import credentials, messaging

from django.conf import settings


logger = logging.getLogger(__name__)


class FCMService:

    TOPICS = {
        "ALL_USERS": "all_users",
    }

    # =========================================================
    # FIREBASE INITIALIZE
    # =========================================================

    @staticmethod
    def initialize_firebase():

        # اگر قبلاً Firebase initialize شده
        if firebase_admin._apps:
            return firebase_admin.get_app()

        credentials_path = getattr(
            settings,
            "FIREBASE_CREDENTIALS",
            None
        )

        if not credentials_path:
            raise RuntimeError(
                "FIREBASE_CREDENTIALS در settings تعریف نشده است."
            )

        if not os.path.exists(credentials_path):
            raise FileNotFoundError(
                f"Firebase credentials پیدا نشد: {credentials_path}"
            )

        cred = credentials.Certificate(
            credentials_path
        )

        app = firebase_admin.initialize_app(
            cred,
            {
                "projectId": getattr(
                    settings,
                    "FIREBASE_PROJECT_ID",
                    None
                )
            }
        )

        logger.info(
            "Firebase Admin initialized successfully"
        )

        return app

    # =========================================================
    # WORKER URL
    # =========================================================

    @staticmethod
    def get_worker_url():

        worker_url = getattr(
            settings,
            "FCM_WORKER_URL",
            None
        )

        if not worker_url:
            raise RuntimeError(
                "FCM_WORKER_URL در settings تعریف نشده است."
            )

        return worker_url.rstrip("/")

    # =========================================================
    # CLEAN DATA
    # =========================================================

    @staticmethod
    def clean_data(data=None):

        if not data:
            return {}

        clean_data = {}

        for key, value in data.items():

            if value is None:
                continue

            clean_data[str(key)] = str(value)

        return clean_data

    # =========================================================
    # SUBSCRIBE TOKEN TO TOPIC
    # =========================================================

    @classmethod
    def subscribe_token_to_topic(
        cls,
        token,
        topic=None
    ):

        topic = topic or cls.TOPICS["ALL_USERS"]

        if not token:

            return {
                "success": False,
                "message": "FCM Token الزامی است.",
                "topic": topic,
            }

        try:

            # ---------------------------------------------
            # Initialize Firebase
            # ---------------------------------------------

            cls.initialize_firebase()

            # ---------------------------------------------
            # Subscribe
            # ---------------------------------------------

            response = messaging.subscribe_to_topic(
                [token],
                topic
            )

            logger.info(
                "FCM SUBSCRIBE | topic=%s | success=%s | failed=%s",
                topic,
                response.success_count,
                response.failure_count,
            )

            # ---------------------------------------------
            # Failed
            # ---------------------------------------------

            if response.failure_count > 0:

                errors = []

                for error in response.errors:

                    errors.append({
                        "index": error.index,
                        "reason": str(error.reason),
                    })

                logger.error(
                    "FCM SUBSCRIBE FAILED | topic=%s | errors=%s",
                    topic,
                    errors,
                )

                return {
                    "success": False,
                    "message": "Token subscribe failed.",
                    "topic": topic,
                    "success_count": response.success_count,
                    "failure_count": response.failure_count,
                    "errors": errors,
                }

            # ---------------------------------------------
            # Success
            # ---------------------------------------------

            logger.info(
                "FCM TOKEN SUBSCRIBED SUCCESSFULLY | topic=%s",
                topic,
            )

            return {
                "success": True,
                "message": "Token subscribed successfully.",
                "topic": topic,
                "success_count": response.success_count,
                "failure_count": response.failure_count,
            }

        except Exception as e:

            logger.exception(
                "FCM subscribe topic error: %s",
                str(e)
            )

            return {
                "success": False,
                "message": str(e),
                "topic": topic,
            }

    # =========================================================
    # UNSUBSCRIBE TOKEN FROM TOPIC
    # =========================================================

    @classmethod
    def unsubscribe_token_from_topic(
        cls,
        token,
        topic=None
    ):

        topic = topic or cls.TOPICS["ALL_USERS"]

        if not token:

            return {
                "success": False,
                "message": "FCM Token الزامی است.",
                "topic": topic,
            }

        try:

            # ---------------------------------------------
            # Initialize Firebase
            # ---------------------------------------------

            cls.initialize_firebase()

            # ---------------------------------------------
            # Unsubscribe
            # ---------------------------------------------

            response = messaging.unsubscribe_from_topic(
                [token],
                topic
            )

            logger.info(
                "FCM UNSUBSCRIBE | topic=%s | success=%s | failed=%s",
                topic,
                response.success_count,
                response.failure_count,
            )

            # ---------------------------------------------
            # Failed
            # ---------------------------------------------

            if response.failure_count > 0:

                errors = []

                for error in response.errors:

                    errors.append({
                        "index": error.index,
                        "reason": str(error.reason),
                    })

                logger.error(
                    "FCM UNSUBSCRIBE FAILED | topic=%s | errors=%s",
                    topic,
                    errors,
                )

                return {
                    "success": False,
                    "message": "Token unsubscribe failed.",
                    "topic": topic,
                    "success_count": response.success_count,
                    "failure_count": response.failure_count,
                    "errors": errors,
                }

            # ---------------------------------------------
            # Success
            # ---------------------------------------------

            logger.info(
                "FCM TOKEN UNSUBSCRIBED SUCCESSFULLY | topic=%s",
                topic,
            )

            return {
                "success": True,
                "message": "Token unsubscribed successfully.",
                "topic": topic,
                "success_count": response.success_count,
                "failure_count": response.failure_count,
            }

        except Exception as e:

            logger.exception(
                "FCM unsubscribe topic error: %s",
                str(e)
            )

            return {
                "success": False,
                "message": str(e),
                "topic": topic,
            }

    # =========================================================
    # REGISTER TOPIC
    # =========================================================

    @classmethod
    def register_topic(
        cls,
        token,
        topic=None
    ):

        return cls.subscribe_token_to_topic(
            token=token,
            topic=topic or cls.TOPICS["ALL_USERS"]
        )

    # =========================================================
    # UNREGISTER TOPIC
    # =========================================================

    @classmethod
    def unregister_topic(
        cls,
        token,
        topic=None
    ):

        return cls.unsubscribe_token_from_topic(
            token=token,
            topic=topic or cls.TOPICS["ALL_USERS"]
        )

    # =========================================================
    # SEND TO CLOUDFLARE WORKER
    # =========================================================

    @classmethod
    def _send_to_worker(
        cls,
        title,
        body,
        topic=None,
        token=None,
        data=None,
        image_url=None,
        priority="high",
    ):

        payload = {
            "title": str(title),
            "body": str(body),
            "data": cls.clean_data(data),
            "priority": str(priority),
        }

        # ---------------------------------------------
        # Topic
        # ---------------------------------------------

        if topic:
            payload["topic"] = str(topic)

        # ---------------------------------------------
        # Token
        # ---------------------------------------------

        if token:
            payload["token"] = str(token)

        # ---------------------------------------------
        # Image
        # ---------------------------------------------

        if image_url:
            payload["image_url"] = str(image_url)

        worker_url = cls.get_worker_url()

        try:

            logger.info(
                "FCM WORKER REQUEST | topic=%s | token=%s",
                topic,
                bool(token),
            )

            response = requests.post(
                worker_url,
                json=payload,
                headers={
                    "Content-Type": "application/json",
                },
                timeout=20,
            )

            # ---------------------------------------------
            # Parse JSON
            # ---------------------------------------------

            try:

                result = response.json()

            except ValueError:

                result = {
                    "success": False,
                    "error": response.text,
                }

            # ---------------------------------------------
            # HTTP Error
            # ---------------------------------------------

            if not response.ok:

                logger.error(
                    "FCM WORKER HTTP ERROR | status=%s | response=%s",
                    response.status_code,
                    result,
                )

                return {
                    "success": False,
                    "message": result.get(
                        "error",
                        "FCM Worker request failed"
                    ),
                    "status_code": response.status_code,
                    "response": result,
                }

            # ---------------------------------------------
            # Worker Error
            # ---------------------------------------------

            if not result.get("success"):

                logger.error(
                    "FCM WORKER ERROR | response=%s",
                    result,
                )

                return {
                    "success": False,
                    "message": result.get(
                        "error",
                        "FCM Worker failed"
                    ),
                    "response": result,
                }

            # ---------------------------------------------
            # Success
            # ---------------------------------------------

            logger.info(
                "FCM NOTIFICATION SENT | message_id=%s",
                result.get("message_id"),
            )

            return {
                "success": True,
                "message": "Notification sent successfully",
                "message_id": result.get(
                    "message_id"
                ),
                "response": result,
            }

        # ---------------------------------------------
        # Timeout
        # ---------------------------------------------

        except requests.Timeout:

            logger.exception(
                "FCM Worker timeout"
            )

            return {
                "success": False,
                "message": "FCM Worker timeout",
            }

        # ---------------------------------------------
        # Connection Error
        # ---------------------------------------------

        except requests.RequestException as e:

            logger.exception(
                "FCM Worker connection error"
            )

            return {
                "success": False,
                "message": str(e),
            }

        # ---------------------------------------------
        # Unexpected Error
        # ---------------------------------------------

        except Exception as e:

            logger.exception(
                "FCM Worker unexpected error"
            )

            return {
                "success": False,
                "message": str(e),
            }

    # =========================================================
    # SEND TO TOPIC
    # =========================================================

    @classmethod
    def send_to_topic(
        cls,
        topic,
        title,
        body,
        data=None,
        image_url=None,
        priority="high",
    ):

        if not topic:

            return {
                "success": False,
                "message": "Topic الزامی است.",
            }

        if not title:

            return {
                "success": False,
                "message": "Title الزامی است.",
            }

        if not body:

            return {
                "success": False,
                "message": "Body الزامی است.",
            }

        return cls._send_to_worker(
            title=title,
            body=body,
            topic=topic,
            data=data,
            image_url=image_url,
            priority=priority,
        )

    # =========================================================
    # SEND TO TOKEN
    # =========================================================

    @classmethod
    def send_to_token(
        cls,
        token,
        title,
        body,
        data=None,
        image_url=None,
        priority="high",
    ):

        if not token:

            return {
                "success": False,
                "message": "FCM Token الزامی است.",
            }

        if not title:

            return {
                "success": False,
                "message": "Title الزامی است.",
            }

        if not body:

            return {
                "success": False,
                "message": "Body الزامی است.",
            }

        return cls._send_to_worker(
            title=title,
            body=body,
            token=token,
            data=data,
            image_url=image_url,
            priority=priority,
        )