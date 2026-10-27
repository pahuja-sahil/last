# --------------------------------------------------------------
#  Meta (Facebook Graph) API Integration – nextapi.py
# --------------------------------------------------------------
#  This module provides a clean, self‑contained wrapper around the
#  Meta Graph API using the `requests` library.
#  Features:
#   • Environment‑based access‑token handling (META_ACCESS_TOKEN)
#   • Simple GET and POST helpers with JSON payloads
#   • Example endpoints:
#        – Get user profile
#        – Publish a post to a Page
#        – Retrieve Page insights
#   • Comprehensive error handling and logging
#   • Type hints and doc‑strings for IDE support
# --------------------------------------------------------------

import os
import json
import logging
from typing import Any, Dic

import requests

# ----------------------------------------------------------------------
# Logging configuration
# ----------------------------------------------------------------------
logger = logging.getLogger(__name__)
if not logger.handlers:                     # avoid duplicate handlers in notebooks
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        fmt="%(asctime)s %(levelname)s %(name)s – %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

# ----------------------------------------------------------------------
# Authentication
# ----------------------------------------------------------------------
# The Meta Graph API uses a short‑lived or long‑lived user/page access token.
# We read it from the environment for security.  The token must have the
# permissions required for the endpoints you intend to call (e.g.
# `pages_manage_posts`, `pages_read_engagement`, `public_profile`, …).

if not _META_TOKEN:
    logger.error(
        "META_ACCESS_TOKEN environment variable not set. "
        "Meta API calls will fail until a valid token is provided."
    )
# Base URL for the Graph API – version can be changed as needed.
_BASE_URL = "https://graph.facebook.com/v17.0"

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def _handle_response(resp: requests.Response) -> Dict[str, Any]:
    """
    Centralised response handling.
    - Raises for HTTP errors.
    - Parses JSON and returns the payload.
    - Logs useful debugging information.
    """
    try:
        resp.raise_for_status()
    except requests.HTTPErr
        # Try to extract the error message returned by Meta
        try:
            error_info = resp.json().get("error", {})
            err_msg = error_info.get("message", str(exc))
            err_code = error_info.get("code", resp.status_code)
        except (ValueError, AttributeError):
            err_msg = str(exc)
            err_code = resp.status_code
        logger.error(
            "Meta API request failed [%s] %s – %s",
            resp.request.method,
            resp.request.url,
            err_msg,
        )
        raise RuntimeError(f"Meta API error {err_code}: {err_msg}") from exc

    try:
        data = resp.json()
        logger.debug("Meta API response data: %s", json.dumps(data, indent=2))
        return data
    except ValueError as exc:
        logger.error("Failed to decode JSON response from Meta API")
        raise RuntimeError("Invalid JSON response from Meta API") from exc


def _get(endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Perform a GET request against the Graph API.
    """
    url = f"{_BASE_URL}/{endpoint}"
    headers = {"Authorization": f"Bearer {_META_TOKEN}"}
    try:
        logger.info("GET %s", url)
        resp = requests.get(url, headers=headers, params=params, timeout=10)
        return _handle_response(resp)
    except requests.RequestException as exc:
        logger.exception("Network error during GET %s", url)
        raise RuntimeError("Network error while contacting Meta API") from exc


def _post(
    endpoint: str,
    data: Optional[Dict[str, Any]] = None,
    json_body: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Perform a POST request against the Graph API.
    """
    url = f"{_BASE_URL}/{endpoint}"
    headers = {"Authorization": f"Bearer {_META_TOKEN}"}
    try:
        logger.info("POST %s", url)
        resp = requests.post(
            url,
            headers=headers,
            data=data,
            json=json_body,
            timeout=10,
        )
        return _handle_response(resp)
    except requests.RequestException as exc:
        logger.exception("Network error during POST %s", url)
        raise RuntimeError("Network error while contacting Meta API") from exc


# ----------------------------------------------------------------------
# Public API – example use‑cases
# ----------------------------------------------------------------------
def get_user_profile(user_id: str = "me", fields: Optional[str] = None) -> Dict[str, Any]:
    """
    Retrieve a Facebook user profile.

    Parameters
    ----------
    user_id: str
        The Graph API user identifier. Use "me" for the token owner.
    fields: str, optional
        Comma‑separated list of fields to return (e.g. "id,name,email").

    Returns
    -------
    dict
        The JSON payload returned by the Graph API.
    """
    params = {"access_token": _META_TOKEN}
    if fields:
        params["fields"] = fields
    return _get(f"{user_id}", params=params)


def publish_page_post(page_id: str, message: str, link: Optional[str] = None) -> Dict[str, Any]:
    """
    Publish a new post to a Facebook Page.

    Parameters
    ----------
    page_id: str
        The ID of the Facebook Page.
    message: str
        The text content of the post.
    link: str, optional
        An optional URL to attach to the post.

    Returns
    -------
    dict
        The Graph API response containing the new post ID.
    """
    endpoint = f"{page_id}/feed"
    payload = {"message": message}
    if link:
        payload["link"] = link
    # The Graph API also accepts the token as a query param, but we send it in the header.
    return _post(endpoint, json_body=payload)


def get_page_insights(page_id: str, metric: str = "page_impressions") -> Dict[str, Any]:
    """
    Retrieve insights for a Facebook Page.

    Parameters
    ----------
    page_id: str
        The ID of the Facebook Page.
    metric: str
        The insight metric to query (default: page_impressions).

    Returns
    -------
    dict
        Insight data returned by the Graph API.
    """
    endpoint = f"{page_id}/insights"
    params = {
        "metric": metric,
        "access_token": _META_TOKEN,
    }
    return _get(endpoint, params=params)


# ----------------------------------------------------------------------
# Example usage (will only run when this file is executed directly)
# ----------------------------------------------------------------------
if __name__ == "__main__":
    # NOTE: These calls require a valid META_ACCESS_TOKEN with the
    # appropriate permissions.  They are provided as quick sanity checks.
    try:
        profile = get_user_profile(fields="id,name,email")
        logger.info("Current user profile: %s", profile)

        # Replace with a real page ID you manage
        # page_id = "123456789012345"
        # post_resp = publish_page_post(page_id, "Hello from the Meta API wrapper!")
        # logger.info("Published post response: %s", post_resp)

        # Replace with a real page ID you manage
        # insights = get_page_insights(page_id, metric="page_impressions")
        # logger.info("Page insights: %s", insights)

    except Exception as e:
        logger.exception("An error occurred while testing Meta API integration")
