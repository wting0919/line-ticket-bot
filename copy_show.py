from copy import deepcopy

from linebot.models import TextSendMessage

from data import (
    load_data,
    insert_show,
)

from show_list import (
    get_all_shows,
)

from ui import (
    edit_field_quick_reply,
)

line_bot_api = None
user_state = {}


def handle_copy_show(event, text, user_id):

    state = user_state.get(user_id)

    if isinstance(state, dict) and "shows" in state:
        shows = state["shows"]
    else:
        shows = get_all_shows()

    try:
        index = int(
            text.replace("複製", "").strip()
        ) - 1

    except Exception:

        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text="請輸入格式：\n複製 1"
            )
        )
        return

    if index < 0 or index >= len(shows):

        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text="❌ 找不到這筆演出"
            )
        )
        return

    new_show = deepcopy(shows[index])

    new_show.pop("id", None)

    new_show["提醒"] = {
        "前一天": False,
        "30分鐘": False,
        "10分鐘": False,
        "取票": False,
        "演出日": False,
    }

    new_show["搶票狀態"] = "等待搶票"
    new_show["取票狀態"] = "未取票"

    new_show = insert_show(new_show)

    user_state[user_id] = {
        "mode": "修改演出",
        "step": "field",
        "show_id": new_show["id"],
    }

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(
            text=(
                "✅ 已複製演出\n\n"
                f"🎤 {new_show['演出名稱']}\n\n"
                "請選擇要修改的欄位"
            ),
            quick_reply=edit_field_quick_reply()
        )
    )