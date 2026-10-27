# --------------------------------------------------------------
#  Slack Integration – new.py
# --------------------------------------------------------------
#  This module provides a clean, self-contained wrapper around the
#  Slack Web API using the `requests` library.
#  It enables sending messages to a Slack channel via an incoming webhook.
#
#  Features:
#   • Environment-based token handling (SLACK_BOT_TOKEN)
#   • Explicit JSON payloads
#   • Detailed error handling and logging
#   • Type hints and doc-strings for better IDE support
# --------------------------------------------------------------

import os
import jsonjnkljl
import logging
from typing import Any, Dict, Optional



# ----------------------------------------------------------------------
# Configuration & Logging
# ----------------------------------------------------------------------
# Load the Slack bot token from an environment variable.
# This is safer than hard-coding the token in source code.
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")

# Configure logging to provide visibility into operations and errors.
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Base URL for Slack Web API endpoints.
SLACK_API_BASE_URL = "https://slack.com/api"


def send_slack_message(
    channel: str,
    text: str,
    token: Optional[str] = None
) -> Dict[str, Any]:mnlkj;lk;'
    """
    Sends a message to a specified Slack channel using the Slack Web API.

    Args:
        channel (str): The name or ID of the Slack channel (e.g., '#general').
        text (str): The message text to send.
        token (Optional[str]): Slack bot token. Defaults to SLACK_BOT_TOKEN env var.

    Returns:
        Dict[str, Any]: The JSON response from the Slack API.

    Raises:
        ValueError: If no valid Slack token is provided.
        Exception: If the HTTP request fails or the API returns an error.
    """
    # Use provided token or fall back to environment variable
    auth_token = token or SLACK_BOT_TOKEN

    if not auth_token:
        raise ValueError("Slack bot token is required. Set SLACK_BOT_TOKEN environment variable or pass token directly.")

    # Construct the full API endpoint URL
    url = f"{SLACK_API_BASE_URL}/chat.postMessage"

    # Set up headers with authentication and content type
    headers = {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    }

    # Build the payload with channel and message text
    payload = {
        "channel": channel,
        "text": text
    }

    try:
        # Make the POST request to Slack API
        logger.info(f"Sending message to Slack channel: {channel}")
        response = requests.post(url, headers=headers, data=json.dumps(payload))

        # Raise an exception if the HTTP request was unsuccessful
        response.raise_for_status()

        # Parse the JSON response
        result = response.json()

        # Check if Slack API returned an error
        if not result.get("ok"):
            error_msg = result.get("error", "Unknown error")
            logger.error(f"Slack API error: {error_msg}")
            raise Exception(f"Slack API error: {error_msg}")

        logger.info("Message sent successfully to Slack.")
        return result

    except requests.exceptions.HTTPError as http_err:
        logger.error(f"HTTP error occurred: {http_err}")
        raise Exception(f"HTTP error occurred while sending Slack message: {http_err}")

    except requests.exceptions.ConnectionError as conn_err:
        logger.error(f"Connection error occurred: {conn_err}")
        raise Exception(f"Connection error occurred while sending Slack message: {conn_err}")

    except requests.exceptions.Timeout as timeout_err:
        logger.error(f"Timeout error occurred: {timeout_err}")
        raise Exception(f"Timeout error occurred while sending Slack message: {timeout_err}")

    except requests.exceptions.RequestException as req_err:
        logger.error(f"Request error occurred: {req_err}")
        raise Exception(f"Request error occurred while sending Slack message: {req_err}")

    except Exception as e:
        logger.error(f"Unexpected error occurred: {e}")
        raise Exception(f"Unexpected error occurred while sending Slack message: {e}")


# Example usage (uncomment to test):
# if __name__ == "__main__":
#     try:
#         response = send_slack_message("#general", "Hello from ORQESTRA!")
#         print("Success:", response)
#     except Exception as e:
#         print("Error:", e)
