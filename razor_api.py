"""
razor_api.py
------------

A lightweight, self‑contained wrapper around the Razorpay REST API.

Features
~~~~~~~~
* Environment‑based credential handling (`RAZORPAY_KEY_ID` & `RAZORPAY_KEY_SECRET`).
* Simple helper functions for the most common operations:
  - `create_order`
  - `fetch_order`
  - `capture_payment`
  - `verify_signature` (for webhook validation)
* Comprehensive error handling with clear log messages.
* Type hints and doc‑strings for IDE friendliness.

The module can be imported directly:

    from razor_api import RazorpayClient

    client = RazorpayClient()
    order = client.create_order(amount=5000, receipt="order_rcptid_11")
"""

import os
import hmac
import hashlib
import logging

from typing import Any, Dict, Optional

import requests
from requests.auth import HTTPBasicAuth

# ----------------------------------------------------------------------
# Logging configuration (the host application can override this)
# ----------------------------------------------------------------------
logger = logging.getLogger(__name__)
if not logger.handlers:
    # Default to a simple console logger if the host hasn't configured logging.
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


class RazorpayError(Exception):
    """Base exception for all Razorpay‑related errors."""

    def __init__(self, message: str, status_code: Optional[int] = None, payload: Any = None):
        super().__init__(message)
        self.status_code = status_code
        self.payload = payload


class RazorpayClient:
    """
    Razorpay API client.

    The client reads credentials from the environment:

        RAZORPAY_KEY_ID
        RAZORPAY_KEY_SECRET

    If the variables are missing, an exception is raised at instantiation.
    """

    _BASE_URL = "https://api.razorpay.com/v1"

    def __init__(self) -> None:
        self.key_id = os.getenv("RAZORPAY_KEY_ID")
        self.key_secret = os.getenv("RAZORPAY_KEY_SECRET")

        if not self.key_id or not self.key_secret:
            raise RazorpayError(
                "Razorpay credentials not found. Set RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET."
            )

        # `requests` will use HTTP Basic Auth for every request.
        self.auth = HTTPBasicAuth(self.key_id, self.key_secret)

    # ------------------------------------------------------------------
    # Helper: generic request wrapper
    # ------------------------------------------------------------------
    def _request(
        self,
        method: str,
        endpoint: str,
        *,
        json: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        url = f"{self._BASE_URL}{endpoint}"
        try:
            logger.debug("Calling Razorpay %s %s", method, url)
            response = requests.request(
                method,
                url,
                auth=self.auth,
                json=json,
                params=params,
                timeout=15,  # seconds
            )
            response.raise_for_status()
            logger.debug("Razorpay response [%s]: %s", response.status_code, response.text)
            return response.json()
        except requests.HTTPError as http_err:
            # Try to extract Razorpay's error payload for richer context.
            try:
                err_payload = response.json()
            except Exception:
                err_payload = response.text
            logger.error(
                "Razorpay HTTP error %s: %s", response.status_code, err_payload
            )
            raise RazorpayError(
                f"Razorpay HTTP error {response.status_code}",
                status_code=response.status_code,
                payload=err_payload,
            ) from http_err
        except requests.RequestException as req_err:
            logger.error("Network error while contacting Razorpay: %s", req_err)
            raise RazorpayError("Network error while contacting Razorpay") from req_err

    # ------------------------------------------------------------------
    # Public API methods
    # ------------------------------------------------------------------
    def create_order(
        self,
        amount: int,
        currency: str = "INR",
        receipt: Optional[str] = None,
        notes: Optional[Dict[str, str]] = None,
        payment_capture: int = 1,
    ) -> Dict[str, Any]:
        """
        Create a new Razorpay order.

        Parameters
        ----------
        amount: int
            Amount in the smallest currency unit (e.g. paise for INR).
        currency: str, default "INR"
        receipt: str, optional
            Your own identifier for the order.
        notes: dict, optional
            Arbitrary key‑value pairs attached to the order.
        payment_capture: int, default 1
            1 – auto‑capture, 0 – manual capture.

        Returns
        -------
        dict
            The JSON response from Razorpay containing the order details.
        """
        payload: Dict[str, Any] = {
            "amount": amount,
            "currency": currency,
            "payment_capture": payment_capture,
        }
        if receipt:
            payload["receipt"] = receipt
        if notes:
            payload["notes"] = notes

        logger.info("Creating Razorpay order: amount=%s %s", amount, currency)
        return self._request("POST", "/orders", json=payload)

    def fetch_order(self, order_id: str) -> Dict[str, Any]:
        """
        Retrieve details of an existing order.

        Parameters
        ----------
        order_id: str
            The Razorpay order identifier (e.g. `order_9A33XWu170gUtm`).

        Returns
        -------
        dict
            Order information.
        """
        logger.info("Fetching Razorpay order %s", order_id)
        return self._request("GET", f"/orders/{order_id}")

    def capture_payment(
        self,
        payment_id: str,
        amount: int,
        currency: str = "INR",
    ) -> Dict[str, Any]:
        """
        Capture a payment that was created with `payment_capture=0`.

        Parameters
        ----------
        payment_id: str
            The Razorpay payment identifier.
        amount: int
            Amount to capture (must be ≤ the authorized amount) in the smallest currency unit.
        currency: str, default "INR"

        Returns
        -------
        dict
            Capture response.
        """
        payload = {"amount": amount, "currency": currency}
        logger.info("Capturing payment %s for amount %s %s", payment_id, amount, currency)
        return self._request("POST", f"/payments/{payment_id}/capture", json=payload)

    @staticmethod
    def verify_signature(
        payload_body: bytes,
        received_signature: str,
        secret: str,
    ) -> bool:
        """
        Verify Razorpay webhook signature.

        Razorpay signs the request body using HMAC‑SHA256 with the webhook secret.
        This method reproduces the signature and compares it with the header value.

        Parameters
        ----------
        payload_body: bytes
            Raw request body (as received from Flask/Django request.data, etc.).
        received_signature: str
            Value of the `X-Razorpay-Signature` header.
        secret: str
            Webhook secret configured in the Razorpay dashboard.

        Returns
        -------
        bool
            ``True`` if the signature matches, ``False`` otherwise.
        """
        generated_hmac = hmac.new(
            key=secret.encode("utf-8"),
            msg=payload_body,
            digestmod=hashlib.sha256,
        ).hexdigest()
        is_valid = hmac.compare_digest(generated_hmac, received_signature)
        if is_valid:
            logger.debug("Webhook signature verification succeeded.")
        else:
            logger.warning(
                "Webhook signature verification failed. Expected %s, got %s",
                generated_hmac,
                received_signature,
            )
        return is_valid