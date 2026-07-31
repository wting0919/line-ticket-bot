from linebot.models import TextSendMessage

from view_show import handle_view_show

from helpers import (
    has_show_list,
    get_current_index,
    get_current_shows,
)

import config


def handle_next_show(event, user_id):

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

    shows = get_current_shows(user_id)

    if index + 1 >= len(shows):

        config.line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text="已經是最後一筆。"
            )
        )
        return True

    handle_view_show(
        event,
        f"查看 {index + 2}",
        user_id,
    )

    return True