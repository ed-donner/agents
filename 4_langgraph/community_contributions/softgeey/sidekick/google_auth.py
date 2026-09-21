"""Google OAuth2 authentication helper."""

import os
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from config import config


def get_google_credentials() -> Credentials | None:
    """
    Return valid Google credentials.
    Runs local OAuth flow on first use; refreshes token automatically.
    Returns None if credentials.json is not present.
    """
    if not os.path.exists(config.GOOGLE_CREDENTIALS_FILE):
        return None

    creds: Credentials | None = None

    if os.path.exists(config.GOOGLE_TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(
            config.GOOGLE_TOKEN_FILE, config.GOOGLE_SCOPES
        )

    if creds and creds.valid:
        return creds

    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    else:
        flow = InstalledAppFlow.from_client_secrets_file(
            config.GOOGLE_CREDENTIALS_FILE, config.GOOGLE_SCOPES
        )
        creds = flow.run_local_server(port=0)

    with open(config.GOOGLE_TOKEN_FILE, "w") as token_file:
        token_file.write(creds.to_json())

    return creds
