from linebot.models import TextSendMessage

from view_show import handle_view_show

import config


def handle_next_show(event, user_id):

    state = config.user_state.get(user_id)

    if not state or "shows" not in state:

        config.line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text="請先查看列表或搜尋。"
            )
        )
        return True

    index = state.get("current_index")

    if index is None:

        config.line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text="請先使用「查看 1」。"
            )
        )
        return True

    if index + 1 >= len(state["shows"]):

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