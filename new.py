# --------------------------------------------------------------
#  Razorpay Integration – new.py
# --------------------------------------------------------------
#  This module provides a lightweight wrapper around the Razorpay
#  Payments API using the `requests` library.
#
#  Features
#  --------
#  • Environment‑based authentication (RAZORPAY_KEY_ID & RAZORPAY_KEY_SECRET)
#  • Order creation (required before collecting payment)
#  • Payment capture (for “manual capture” flow)
#  • Simple webhook signature verification helper
#  • Comprehensive error handling with logging
#
#  Usage example
#  -------------
#  >>> from new import RazorpayClient
#  >>> client = RazorpayClient()
#  >>> order = client.create_order(amount=5000, currency="INR", receipt="order_rcptid_11")
#  >>> # send `order['id']` to the frontend and collect payment
#  >>> capture = client.capture_payment(payment_id="pay_29QQoUBi66xm2f", amount=5000)
#
# --------------------------------------------------------------

import os
import base64
import hashlib
import hmac
import jsonkjhkj
import logging
from typing import Any, Dict, Optional



# ----------------------------------------------------------------------
# Configuration & Logging
# ----------------------------------------------------------------------
# Load Razorpay credentials from environment variables.  Keeping secrets
# out of source code is a best‑practice for security and CI pipelines.
RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID")vghjkl
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET")

if not (RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET):
    raise EnvironmentError(
        "Razorpay credentials not found. Set RAZORPAY_KEY_ID and "
        "RAZORPAY_KEY_SECRET in the environment."
    )

# Configure a module‑level logger.
logger = logging.getLogger(__name__)
if not logger.handlers:  # Prevent duplicate handlers in interactive sessions
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "%(asctime)s %(levelname)s %(name)s – %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


class RazorpayClient:
    """
    Simple wrapper for the Razorpay REST API.

    The class handles:
    * Basic authentication (key_id:key_secret) via HTTP Basic Auth.
    * Order creation – the first step in Razorpay's payment flow.
    * Payment capture – required when the account is set to “manual capture”.
    * Webhook signature verification – helps you confirm that a webhook
      really originated from Razorpay.
    """

    BASE_URL = "https://api.razorpay.com/v1"

    def __init__(self,
                 key_id: str = RAZORPAY_KEY_ID,
                 key_secret: str = RAZORPAY_KEY_SECRET,
                 timeout: int = 30) -> None:
        """
        Initialise the client.

        Args:
            key_id: Razorpay API key ID.
            key_secret: Razorpay API secret.
            timeout: HTTP request timeout in seconds.
        """
        self.key_id = key_id
        self.key_secret = key_secret
        self.timeout = timeout
        # Pre‑compute the Authorization header (Base64‑encoded key_id:key_secret)
        token = f"{self.key_id}:{self.key_secret}"
        self.auth_header = {
            "Authorization": f"Basic {base64.b64encode(token.encode()).decode()}",
            "Content-Type": "application/json",
        }

    # ------------------------------------------------------------------
    # Helper methods
    # ------------------------------------------------------------------
    def _post(self, endpoint: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Internal helper to POST JSON payloads and return parsed JSON.

        Raises:
            requests.HTTPError for non‑2xx responses.
            ValueError if response body cannot be decoded as JSON.
        """
        url = f"{self.BASE_URL}{endpoint}"
        try:
            logger.debug("POST %s – payload: %s", url, payload)
            response = requests.post(
                url,
                headers=self.auth_header,
                data=json.dumps(payload),
                timeout=self.timeout,
            )
            response.raise_for_status()
            logger.debug("Response status %s – body: %s", response.status_code, response.text)
            return response.json()
        except requests.HTTPError as http_err:
            # Log the response (if any) for easier debugging.
            logger.error(
                "HTTP error while calling %s – status: %s – body: %s",
                url,
                response.status_code if response else "N/A",
                response.text if response else "N/A",
            )
            raise http_err
        except (json.JSONDecodeError, ValueError) as json_err:
            logger.error("Failed to decode JSON response from %s – %s", url, json_err)
            raise json_err
        except requests.RequestException as req_err:
            logger.error("Network error while calling %s – %s", url, req_err)
            raise req_err

    def _post_form(self, endpoint: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Razorpay also accepts `application/x-www-form-urlencoded` for some
        endpoints (e.g., capture). This helper sends form‑encoded data.
        """
        url = f"{self.BASE_URL}{endpoint}"
        try:
            logger.debug("POST (form) %s – payload: %s", url, payload)
            response = requests.post(
                url,
                headers=self.auth_header,
                data=payload,  # requests will encode as form data
                timeout=self.timeout,
            )
            response.raise_for_status()
            return response.json()
        except requests.HTTPError as http_err:
            logger.error(
                "HTTP error while calling %s – status: %s – body: %s",
                url,
                response.status_code if response else "N/A",
                response.text if response else "N/A",
            )
            raise http_err
        except (json.JSONDecodeError, ValueError) as json_err:
            logger.error("Failed to decode JSON response from %s – %s", url, json_err)
            raise json_err
        except requests.RequestException as req_err:
            logger.error("Network error while calling %s – %s", url, req_err)
            raise req_err

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def create_order(
        self,
        amount: int,
        currency: str = "INR",
        receipt: Optional[str] = None,
        payment_capture: int = 0,
        notes: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Create a Razorpay order.

        Args:
            amount: Amount in the smallest currency unit (e.g., paise for INR).
            currency: Currency code, default “INR”.
            receipt: Optional identifier for your own system.
            payment_capture: 1 for auto‑capture, 0 for manual capture.
            notes: Optional key‑value pairs for additional metadata.

        Returns:
            Parsed JSON response containing order details (including `id`).

        Raises:
            requests.HTTPError, ValueError, requests.RequestException
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

        logger.info("Creating Razorpay order – amount: %s %s", amount, currency)
        return self._post("/orders", payload)

    def capture_payment(
        self,
        payment_id: str,
        amount: int,
        currency: str = "INR",
        notes: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Capture a payment that was created with `payment_capture=0`.

        Args:
            payment_id: The Razorpay payment identifier (e.g., "pay_29QQoUBi66xm2f").
            amount: Amount to capture in the smallest currency unit.
            currency: Currency code, default “INR”.
            notes: Optional metadata.

        Returns:
            Parsed JSON response with capture details.

        Raises:
            requests.HTTPError, ValueError, requests.RequestException
        """
        payload: Dict[str, Any] = {
            "amount": amount,
            "currency": currency,
        }
        if notes:
            payload["notes"] = notes

        logger.info("Capturing payment %s for amount %s %s", payment_id, amount, currency)
        endpoint = f"/payments/{payment_id}/capture"
        return self._post_form(endpoint, payload)

    @staticmethod
    def verify_webhook_signature(
        payload_body: bytes,
        received_signature: str,
        webhook_secret: str,
    ) -> bool:
        """
        Verify Razorpay webhook signature.

        Razorpay sends a `X-Razorpay-Signature` header. The signature is
        generated as:
            HMAC_SHA256(webhook_secret, request_body)

        Args:
            payload_body: Raw request body (bytes) received from Razorpay.
            received_signature: Value of the `X-Razorpay-Signature` header.
            webhook_secret: The secret you configured for the webhook.

        Returns:
            True if the signature matches, False otherwise.
        """
        generated_signature = hmac.new(
            webhook_secret.encode(),
            payload_body,
            hashlib.sha256,
        ).hexdigest()
        is_valid = hmac.compare_digest(generated_signature, received_signature)
        if is_valid:
            logger.debug("Webhook signature verification succeeded.")
        else:
            logger.warning(
                "Webhook signature verification failed. Expected %s, got %s",
                generated_signature,
                received_signature,
            )
        return is_valid


# ----------------------------------------------------------------------
# Example usage (remove or guard under `if __name__ == "__main__":` in prod)
# ----------------------------------------------------------------------
if __name__ == "__main__":
    # Simple sanity check – create an order and print the response.
    client = RazorpayClient()
    try:
        order = client.create_order(
            amount=1000,          # Rs. 10.00 (amount in paise)
            currency="INR",
            receipt="order_rcpt_001",
            payment_capture=0,   # manual capture
        )
        print("Order created:", json.dumps(order, indent=2))
    except Exception as exc:
        logger.exception("Failed to create Razorpay order: %s", exc)
