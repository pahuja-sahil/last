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
import loggingadadadad
import requests
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
            logger.(
                "No Slack token provided or found in environment variable `SLACK_BOT_TOKEN`."
            )
            raise ValueError(
                "Slack token is required. Set `SLACK_BOT_TOKEN` env var or pass token to SlackClient."
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
                raise SlackAPIError(error_msg, response_data=data)

            return data

        except requests.RequestException as exc:
            logger.exception("Network error while calling Slack API")
            raise SlackAPIError(str(exc)) from exc

    # ------------------------------------------------------------------
    # Public API methods
    # ------------------------------------------------------------------

    def post_message(
        self,
        channel: str,
        text: str,
        blocks: Optional[list] = None,
        thread_ts: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Send a message to a channel (or thread).

        Args:
            channel (str): Channel ID (e.g., 'C12345678').
            text (str): Plain‑text fallback message.
            blocks (list, optional): Block Kit layout.
            thread_ts (str, optional): Timestamp of parent message for threaded reply.

        Returns:
            dict: Slack API response.
        """
        payload: Dict[str, Any] = {"channel": channel, "text": text}
        if blocks:
            payload["blocks"] = blocks
        if thread_ts:
            payload["thread_ts"] = thread_ts

        return self._request("POST", "chat.postMessage", payload=payload)

    def list_conversations(
        self,
        types: str = "public_channel,private_channel",
        limit: int = 100,
        cursor: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        List channels (public & private) in the workspace.

        Args:
            types (str): Comma‑separated list of conversation types.
            limit (int): Max number of items to return (max 1000).
            cursor (str, optional): Pagination cursor.

        Returns:
            dict: Slack API response containing `channels` list.
        """
        params = {"types": types, "limit": limit}
        if cursor:
            params["cursor"] = cursor

        return self._request("GET", "conversations.list", params=params)

    def get_history(
        self,
        channel: str,
        limit: int = 200,
        oldest: Optional[float] = None,
        latest: Optional[float] = None,
        cursor: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Retrieve message history for a channel.

        Args:
            channel (str): Channel ID.
            limit (int): Number of messages to fetch (max 1000).
            oldest (float, optional): Unix timestamp to start from.
            latest (float, optional): Unix timestamp to end at.
            cursor (str, optional): Pagination cursor.

        Returns:
            dict: Slack API response containing `messages`.
        """
        params: Dict[str, Any] = {"channel": channel, "limit": limit}
        if oldest:
            params["oldest"] = oldest
        if latest:
            params["latest"] = latest
        if cursor:
            params["cursor"] = cursor

        return self._request("GET", "conversations.history", params=params)

    def add_reaction(
        self,
        channel: str,
        timestamp: str,
        name: str,
    ) -> Dict[str, Any]:
        """
        Add an emoji reaction to a message.

        Args:
            channel (str): Channel ID where the message lives.
            timestamp (str): Message timestamp (`ts` value).
            name (str): Emoji name (e.g., 'thumbsup').

        Returns:
            dict: Slack API response.
        """
        payload = {"channel": channel, "timestamp": timestamp, "name": name}
        return self._request("POST", "reactions.add", payload=payload)

    def get_user_info(self, user_id: str) -> Dict[str, Any]:
        """
        Retrieve metadata for a user.

        Args:
            user_id (str): Slack user ID (e.g., 'U12345678').

        Returns:
            dict: Slack API response containing `user` object.
        """
        params = {"user": user_id}
        return self._request("GET", "users.info", params=params)


# ----------------------------------------------------------------------
# Convenience wrapper functions (optional, for quick use)
# ----------------------------------------------------------------------
def send_simple_message(channel: str, text: str, token: Optional[str] = None) -> Dict[str, Any]:
    """
    Quick helper to send a plain‑text message without instantiating the client manually.

    Args:
        channel (str): Channel ID.
        text (str): Message text.
        token (str, optional): Slack Bot token. If omitted, env var `SLACK_BOT_TOKEN` is used.

    Returns:
        dict: Slack API response.
    """
    client = SlackClient(token=token)
    return client.post_message(channel=channel, text=text)


def list_all_channels(token: Optional[str] = None) -> Dict[str, Any]:
    """
    Quick helper to list all public and private channels.

    Args:
        token (str, optional): Slack Bot token.

    Returns:
        dict: Slack API response.
    """
    client = SlackClient(token=token)
    return client.list_conversations()
