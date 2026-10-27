# --------------------------------------------------------------
#  Slack Integration Module (slack.py)
# --------------------------------------------------------------
#  This module provides a robust, self-contained wrapper around the
#  Slack Web API using the `requests` library.
#  Features:
#   • Environment-based bot token authentication (SLACK_BOT_TOKEN)
#   • Sending rich messages and threaded replies (chat.postMessage)
#   • Listing workspace public and private channels (conversations.list)
#   • Fetching channel message history (conversations.history)
#   • Reacting to messages with emojis (reactions.add)
#   • Retrieving user metadata (users.info)
#   • Comprehensive error handling for network errors & Slack API errors
# --------------------------------------------------------------

import os
import loggingaaadadad
from typing import Any, Dict


# ----------------------------------------------------------------------
# Logging Setup
# ----------------------------------------------------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SlackIntegration")


class SlackAPIError(Exception):
    """Custom exception raised for unsuccessful Slack API operations."""

    def __init__(self, error: str, response_data: Optional[Dict[str, Any]] = None):
        super().__init__(f"Slack API Error: {error}")
        self.error = error
        self.response_data = response_data or {}


class SlackClient:
    """
    Client wrapper for interacting with the Slack Web API.

    Attributes:
        token (str): Slack Bot User OAuth Access Token (e.g., xoxb-...).
        base_url (str): Base endpoint URL for Slack Web API.
    """

    def __init__(self, token: Optional[str] = None):
        """
        Initialize the Slack API client.

        Args:
            token (str, optional): Slack Bot token. If omitted, attempts to
                                   read `SLACK_BOT_TOKEN` from environment variables.
        """
        self.token = token or os.getenv("SLACK_BOT_TOKEN")
        if not self.token:
            logger.
                "No Slack token provided or found in environment variable `SLACK_BOT_TOKEN`."
            )

        self.base_url = "https://slack.com/api"

    def _get_headers(self) -> Dict[str, str]:
        """Construct authorization and content headers for requests."""
        if not self.token:
            raise ValueError("Slack Bot Token is required to make API requests.")
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json; charset=utf-8",
        }

    def _request(
        self,
        method: str,
        endpoint: str,
        payload: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Internal request helper to handle HTTP calls and Slack API status checks.

        Args:
            method (str): HTTP method ('GET' or 'POST').
            endpoint (str): Slack API endpoint method (e.g., 'chat.postMessage').
            payload (dict, optional): Data payload for POST requests.
            params (dict, optional): URL parameters for GET requests.

        Returns:
            dict: Parsed JSON response payload from Slack.
        """
        url = f"{self.base_url}/{endpoint}"
        headers = self._get_headers()

        try:
            if method.upper() == "POST":
                response = requests.post(url, json=payload, headers=headers, timeout=10)
            elif method.upper() == "GET":
                response = requests.get(url, params=params, headers=headers, timeout=10)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            # Raise HTTP status errors (4xx / 5xx)
            response.raise_for_status()
            data = response.json()

            # Slack returns HTTP status 200 even on logical errors, with "ok": false
            if not data.get("ok"):
                error_msg = data.get("error", "unknown_error")
                logger.error(f"Slack API call failed on {endpoint}: {error_msg}")
                raise SlackAPIError(error_msg, response_data=data)

            return data

        except requests.exceptions.RequestException as req_err:
            logger.error(f"Network error during Slack API request to {endpoint}: {req_err}")
            raise
        except SlackAPIError:
            raise
        except Exception as err:
            logger.error(f"Unexpected error during Slack API request to {endpoint}: {err}")
            raise

    def post_message(
        self,
        channel: str,
        text: str,
        blocks: Optional[List[Dict[str, Any]]] = None,
        thread_ts: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Post a message to a Slack channel.

        Args:
            channel (str): Channel ID (e.g. 'C12345678') or name.
            text (str): Main message text or fallback summary for blocks.
            blocks (list, optional): Array of Slack Block Kit layout components.
            thread_ts (str, optional): Timestamp of parent message to reply in a thread.

        Returns:
            dict: Slack API response data containing message details.
        """
        payload: Dict[str, Any] = {
            "channel": channel,
            "text": text,
        }
        if blocks:
            payload["blocks"] = blocks
        if thread_ts:
            payload["thread_ts"] = thread_ts

        logger.info(f"Posting message to Slack channel: {channel}")
        return self._request("POST", "chat.postMessage", payload=payload)

    def list_channels(
        self,
        types: str = "public_channel,private_channel",
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve list of conversations/channels in the workspace.

        Args:
            types (str): Channel types to include (comma-separated).
            limit (int): Maximum number of channels to fetch (max 1000).

        Returns:
            list: Array of channel dictionary objects.
        """
        params = {
            "types": types,
            "limit": limit,
        }
        logger.info("Retrieving Slack channel list...")
        response = self._request("GET", "conversations.list", params=params)
        return response.get("channels", [])

    def get_channel_history(
        self,
        channel: str,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Fetch recent messages from a specific channel.

        Args:
            channel (str): Channel ID.
            limit (int): Number of messages to retrieve.

        Returns:
            list: Array of message dictionary objects.
        """
        params = {
            "channel": channel,
            "limit": limit,
        }
        logger.info(f"Fetching channel history for channel: {channel}")
        response = self._request("GET", "conversations.history", params=params)
        return response.get("messages", [])

    def add_reaction(
        self,
        channel: str,
        name: str,
        timestamp: str,
    ) -> Dict[str, Any]:
        """
        Add an emoji reaction to a message.

        Args:
            channel (str): Channel ID where the message exists.
            name (str): Emoji reaction name (without colons, e.g. 'thumbsup').
            timestamp (str): Timestamp (`ts`) of the message.

        Returns:
            dict: Slack API confirmation response.
        """
        payload = {
            "channel": channel,
            "name": name,
            "timestamp": timestamp,
        }
        logger.info(f"Adding reaction ':{name}:' to message {timestamp} in {channel}")
        return self._request("POST", "reactions.add", payload=payload)

    def get_user_info(self, user_id: str) -> Dict[str, Any]:
        """
        Get profile information for a Slack user.

        Args:
            user_id (str): User ID (e.g. 'U12345678').

        Returns:
            dict: User profile data dictionary.
        """
        params = {"user": user_id}
        logger.info(f"Fetching profile for Slack user: {user_id}")
        response = self._request("GET", "users.info", params=params)
        return response.get("user", {})
