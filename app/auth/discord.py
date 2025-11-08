"""Discord OAuth registration helper."""
from __future__ import annotations

from authlib.integrations.flask_client import OAuth
from flask import Flask


DISCORD_API_BASE_URL = "https://discord.com/api/"


def register_discord_oauth(app: Flask, oauth: OAuth) -> None:
    """Register the Discord OAuth client with the current configuration."""
    oauth.register(
        name="discord",
        client_id=app.config.get("DISCORD_CLIENT_ID"),
        client_secret=app.config.get("DISCORD_CLIENT_SECRET"),
        access_token_url=f"{DISCORD_API_BASE_URL}/oauth2/token",
        authorize_url=f"{DISCORD_API_BASE_URL}/oauth2/authorize",
        api_base_url=DISCORD_API_BASE_URL,
        client_kwargs={
            "scope": "identify email",
            "token_endpoint_auth_method": "client_secret_post",
        },
    )
