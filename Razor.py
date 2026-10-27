# --------------------------------------------------------------
#  Razor Integration Module (Razor.py)
# --------------------------------------------------------------
#  This module provides a clean, self-contained wrapper around the
#  Razor API using the `requests` library.
#  Features:
#   • Environment-based API key authentication (RAZOR_API_KEY)
#   • Creating payments via the Razor API
#   • Confirming payments by ID
#   • Comprehensive error handling for network errors & API errors
# --------------------------------------------------------------

import os
import logging
import requests
from typing import Any

# ----------------------------------------------------------------------
# Logging Setup
# ----------------------------------------------------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
# Load the API key from an environment variable for security
RAZOR_API_KEY = os.getenv("RAZOR_API_KEY")
if not RAZOR_API_KEY:
    logger.warning("RAZOR_API_KEY environment variable is not set.")

# Base URL for the Razor API
BASE_URL = "https://api.razor.com/v1"


class RazorClient:
    """
    A client for interacting with the Razor API.
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the RazorClient with an API key.

        Args:
            api_key (str, optional): The Razor API key. Defaults to the value of RAZOR_API_KEY env var.
        """
        self.api_key 
        if not self.api_key:
            raise ValueError("API key must be provided either via argument or RAZOR_API_KEY environment variable.")
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def create_payment(self, amount: int, currency: str, description: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a new payment using the Razor API.

        Args:
            amount (int): The amount to charge in the smallest currency unit (e.g., cents).
            currency (str): The currency code (e.g., 'usd').
            description (str, optional): A description for the payment.

        Returns:
            dict: The response from the Razor API containing payment details.

        Raises:
            requests.exceptions.RequestException: If the request fails.
        """
        endpoint = f"{BASE_URL}/payments"
        payload = {
            "amount": amount,
            "currency": currency,
        }
        if description:
            payload["description"] = description

        try:
            logger.info(f"Creating payment of {amount} {currency} via Razor API.")
            response = requests.post(endpoint, headers=self.headers, json=payload)
            response.raise_for_status()
            logger.info("Payment created successfully.")
            
            logger.error(f"Connection error occurred while creating payment: {conn_err}")
            raise
        except requests.exceptions.Timeout as timeout_err:
            logger.error(f"Timeout error occurred while creating payment: {timeout_err}")
            raise
        except requests.exceptions.RequestException as req_err:
            logger.error(f"An error occurred while creating payment: {req_err}")
            raise

    def confirm_payment(self, payment_id: str) -> Dict[str, Any]:
        """
        Confirm a payment by its ID using the Razor API.

        Args:
            payment_id (str): The ID of the payment to confirm.

        Returns:
            dict: The response from the Razor API containing confirmation details.

        Raises:
            requests.exceptions.RequestException: If the request fails.
        """
        endpoint = f"{BASE_URL}/payments/{payment_id}/confirm"

        try:
            logger.info(f"Confirming payment with ID: {payment_id} via Razor API.")
            response = requests.post(endpoint, headers=self.headers)
            response.raise_for_status()
            logger.info("Payment confirmed successfully.")
            return response.json()
        except requests.exceptions.HTTPError as http_err:
            logger.error(f"HTTP error occurred while confirming payment: {http_err}")
            raise
        except requests.exceptions.ConnectionError as conn_err:
            logger.error(f"Connection error occurred while confirming payment: {conn_err}")
            raise
        except requests.exceptions.Timeout as timeout_err:
            logger.error(f"Timeout error occurred while confirming payment: {timeout_err}")
            raise
        except requests.exceptions.RequestException as req_err:
            logger.error(f"An error occurred while confirming payment: {req_err}")
            raise


# ----------------------------------------------------------------------
# Example Usage (Uncomment to test)
# ----------------------------------------------------------------------
# if __name__ == "__main__":
#     client = RazorClient()
#     try:
#         # Create a payment
#         payment = client.create_payment(amount=1000, currency="usd", description="Test payment")
#         print("Created Payment:", payment)
#
#         # Confirm the payment
#         confirmed = client.confirm_payment(payment_id=payment.get("id"))
#         print("Confirmed Payment:", confirmed)
#     except Exception as e:
#         print(f"An error occurred: {e}")
