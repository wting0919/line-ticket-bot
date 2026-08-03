line_bot_api = None

user_state = {}

GROUP_ID = None

CHANNEL_ACCESS_TOKEN = None

import os

DASHBOARD_LOGO_URL = os.getenv(
    "DASHBOARD_LOGO_URL",
    "",
)