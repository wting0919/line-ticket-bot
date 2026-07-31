from linebot.models import TextSendMessage

from view_show import handle_view_show

line_bot_api = None
user_state = {}


def handle_next_show(event, user_id):

    state = user_state.get(user_id)

    if not state or "shows" not in state:

        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text="請先查看列表或搜尋。"
            )
        )
        return

    index = state.get("current_index")

    if index is None:

        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text="請先使用「查看 1」。"
            )
        )
        return

    if index == 0:

        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text="已經是第一筆。"
            )
        )
        return

    handle_view_show(
        event,
        f"查看 {index}",
        user_id,
    )