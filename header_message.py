import random

from datetime import datetime, timedelta

# =========================================================
# TicketCat 每日一句
# =========================================================

CAT_HEADER_MESSAGES = [
    "🐾 今天也加油搶票！",
    "🐾 希望今天是神手的一天！",
    "🐾 搶票模式 ON！",
    "🐾 祝你今天歐氣滿滿 🍀",
    "🐾 今天一定有好消息！",
]


def get_cat_header_message():
    """
    每天固定顯示一句 TicketCat 訊息。

    使用日期作為亂數種子，
    同一天內每次開啟都會顯示同一句。
    """

    taiwan_now = datetime.now() + timedelta(hours=8)

    date_seed = taiwan_now.strftime("%Y%m%d")

    random_generator = random.Random(date_seed)

    return random_generator.choice(
        CAT_HEADER_MESSAGES
    )