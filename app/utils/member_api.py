"""Utilities for member profile API integration."""
from __future__ import annotations

import requests
from flask import current_app

from ..models import SiteSetting, SiteSettingKey


def fetch_member_profile_url(discord_id: str) -> str | None:
    """Fetch member profile URL from the member API.

    Args:
        discord_id: The Discord user ID to look up.

    Returns:
        The profile URL if found, None otherwise.
    """
    base_url = SiteSetting.get(SiteSettingKey.MEMBER_API_BASE_URL, "http://member.dhs.todothere.com")
    api_url = f"{base_url}/api/user-profile-url/{discord_id}"

    try:
        response = requests.get(api_url, timeout=10)
        response.raise_for_status()
        data = response.json()

        if data.get("success"):
            return data.get("profile_url")
        else:
            current_app.logger.info(f"Member API returned error for {discord_id}: {data.get('message')}")
            return None
    except requests.RequestException as e:
        current_app.logger.warning(f"Failed to fetch member profile for {discord_id}: {e}")
        return None
    except ValueError as e:
        current_app.logger.warning(f"Invalid JSON response from member API for {discord_id}: {e}")
        return None


def update_user_profile_url(user) -> None:
    """Update the user's profile URL from the member API.

    Args:
        user: The User model instance to update.
    """
    profile_url = fetch_member_profile_url(user.discord_id)
    if profile_url:
        user.profile_url = profile_url
        current_app.logger.info(f"Updated profile URL for user {user.username}: {profile_url}")
    else:
        user.profile_url = None
        current_app.logger.info(f"No profile URL found for user {user.username}")