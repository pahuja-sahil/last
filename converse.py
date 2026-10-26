# --------------------------------------------------------------
#  Stripe Integration – rebuilt from scratch
# --------------------------------------------------------------
#  This module provides a clean, self‑contained wrapper around the
#  Stripe Payment Intents API using the `requests` library.
#  It replaces the previous implementation with:
#   • Environment‑based secret key handling
#   • Explicit JSON payloads (Stripe now prefers `application/json`)
#   • Detailed error handling and logging
#   • Type hints and doc‑strings for better IDE support
# --------------------------------------------------------------

import os
import json
import logging
from typing import Any, Dict, Optional

import requests

# ----------------------------------------------------------------------
# Configuration & Logging
# ----------------------------------------------------------------------
# Load the secret key from an environment variable.  This is safer than
# hard‑coding the key in source code.
STRIPE_SECRET_KEY: str = os.getenv("STRIPE_SECRET_KEY", "sk_test_your_secret_key")
if not STRIPE_SECRET_KEY or STRIPE_SECRET_KEY.startswith("sk_test_your"):
    logging.warning(
        "Stripe secret key is not set or still contains the placeholder value. "
        "Set the STRIPE_SECRET_KEY environment variable before using the module."
    )

# Base endpoint for the Stripe API (v1 is the current stable version)
STRIPE_API_BASE: str = "https://api.stripe.com/v1"

# Common request headers – Stripe expects JSON payloads for most modern calls
HEADERS: Dict[str, str] = {
    "Authorization": f"Bearer {STRIPE_SECRET_KEY}",
    "Content-Type": "application/json",
}


# ----------------------------------------------------------------------
# Helper – generic request wrapper
# ----------------------------------------------------------------------
def _stripe_request(
    method: str,
    path: str,
    payload: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Perform a request against the Stripe API and return the parsed JSON.

    Args:
        method: HTTP method (e.g. "POST", "GET").
        path: API path relative to STRIPE_API_BASE (e.g. "/payment_intents").
        payload: Dictionary that will be JSON‑encoded as the request body.

    Returns:
        The JSON response from Stripe as a dict.

    Raises:
        RuntimeError: If the request fails or Stripe returns a non‑2xx status.
    """
    url = f"{STRIPE_API_BASE}{path}"
    try:
        response = requests.request(
            method=method,
            url=url,
            headers=HEADERS,
            data=json.dumps(payload) if payload else None,
            timeout=15,
        )
        # Raise an HTTPError for bad status codes (4xx/5xx)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        # Stripe returns useful error info in the response body
        try:
            error_detail = response.json()
        except Exception:
            error_detail = response.text
        logging.error(
            f"Stripe HTTP error [{response.status_code}]: {error_detail}"
        )
        raise RuntimeError(f"Stripe request failed: {error_detail}") from http_err
    except requests.exceptions.RequestException as req_err:
        logging.error(f"Network error while contacting Stripe: {req_err}")
        raise RuntimeError("Network error contacting Stripe") from req_err


# ----------------------------------------------------------------------
# Public API – Payment Intent helpers
# ----------------------------------------------------------------------
def create_payment_intent(
    amount: int,
    currency: str,
    payment_method_types: Optional[list] = None,
    metadata: Optional[Dict[str, str]] = None,
    capture_method: str = "automatic",
) -> Dict[str, Any]:
    """
    Create a new Payment Intent.

    Args:
        amount: Amount in the smallest currency unit (e.g. cents for USD).
        currency: ISO currency code (e.g. "usd").
        payment_method_types: List of allowed payment method types.
                               Defaults to ["card"] if omitted.
        metadata: Optional key‑value pairs you want to attach to the intent.
        capture_method: "automatic" (default) or "manual".

    Returns:
        The full Payment Intent object returned by Stripe.

    Raises:
        RuntimeError on any failure.
    """
    payload: Dict[str, Any] = {
        "amount": amount,
        "currency": currency,
        "capture_method": capture_method,
    }

    if payment_method_types:
        payload["payment_method_types"] = payment_method_types
    else:
        payload["payment_method_types"] = ["card"]

    if metadata:
        payload["metadata"] = metadata

    logging.debug(f"Creating Payment Intent with payload: {payload}")
    return _stripe_request("POST", "/payment_intents", payload)


def confirm_payment_intent(
    payment_intent_id: str,
    payment_method: Optional[str] = None,
    return_url: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Confirm an existing Payment Intent.

    Args:
        payment_intent_id: The ID of the Payment Intent to confirm.
        payment_method: Optional ID of a saved payment method to use.
        return_url: URL to which Stripe should redirect after authentication
                    (required for 3‑DS flows).

    Returns:
        The updated Payment Intent object.

    Raises:
        RuntimeError on any failure.
    """
    payload: Dict[str, Any] = {}
    if payment_method:
        payload["payment_method"] = payment_method
    if return_url:
        payload["return_url"] = return_url

    logging.debug(
        f"Confirming Payment Intent {payment_intent_id} with payload: {payload}"
    )
    return _stripe_request(
        "POST", f"/payment_intents/{payment_intent_id}/confirm", payload
    )


def retrieve_payment_intent(payment_intent_id: str) -> Dict[str, Any]:
    """
    Retrieve a Payment Intent by its ID.

    Args:
        payment_intent_id: The ID of the Payment Intent.

    Returns:
        The Payment Intent object.

    Raises:
        RuntimeError on any failure.
    """
    logging.debug(f"Retrieving Payment Intent {payment_intent_id}")
    return _stripe_request("GET", f"/payment_intents/{payment_intent_id}")


# ----------------------------------------------------------------------
# Example usage (executed only when run as a script)
# ----------------------------------------------------------------------
if __name__ == "__main__":
    # Simple demo: create → confirm → retrieve
    try:
        # 1️⃣ Create a payment intent for $10.00 USD
        intent = create_payment_intent(amount=1000, currency="usd")
        print("Created Payment Intent:", json.dumps(intent, indent=2))

        # 2️⃣ Confirm the intent (no payment method supplied – assumes a
        #    test card will be attached via the dashboard or client SDK)
        confirmed = confirm_payment_intent(intent["id"])
        print("Confirmed Payment Intent:", json.dumps(confirmed, indent=2))

        # 3️⃣ Retrieve the final state
        final_intent = retrieve_payment_intent(intent["id"])
        print("Final Payment Intent state:", json.dumps(final_intent, indent=2))

    except RuntimeError as exc:
        logging.error(f"Stripe workflow failed: {exc}")