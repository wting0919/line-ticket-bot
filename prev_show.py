from linebot.models import TextSendMessage

import config

from helpers import (
    has_show_list,
    get_current_index,
)

from view_show import handle_view_show


def handle_prev_show(event, user_id):

    if not has_show_list(user_id):

        config.line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text="請先查看列表或搜尋。"
            )
        )
        return True

    index = get_current_index(user_id)

    if index is None:

        config.line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text="請先使用「查看 1」。"
            )
        )
        return True

    if index == 0:

        config.line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text="已經是第一筆。"
            )
        )
        return True

    handle_view_show(
        event,
        f"查看 {index}",
        user_id,
    )

    return True