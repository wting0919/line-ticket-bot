from copy import deepcopy

from linebot.models import TextSendMessage

from data import (
    insert_show,
)

from show_list import (
    get_all_shows,
)

from ui import (
    edit_field_quick_reply,
)

import config


def handle_copy_show(event, text, user_id):

    state = get_state(user_id)

    if isinstance(state, dict) and "shows" in state:
        shows = state["shows"]
    else:
        shows = get_all_shows()

    try:
        index = int(
            text.replace("複製", "").strip()
        ) - 1

    except Exception:

        config.line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text="請輸入格式：\n複製 1"
            )
        )
        return

    if index < 0 or index >= len(shows):

        config.line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text="❌ 找不到這筆演出"
            )
        )
        return

    new_show = deepcopy(shows[index])

    new_show.pop("id", None)
    new_show.pop("created_at", None)
    new_show.pop("updated_at", None)

    new_show["提醒"] = {
        "前一天": False,
        "30分鐘": False,
        "10分鐘": False,
        "取票": False,
        "演出日": False,
    }

    new_show["搶票狀態"] = "等待搶票"
    new_show["取票狀態"] = "未取票"

    new_show["搶票大師"] = ""
    new_show["取票人"] = ""

    try:
        new_show = insert_show(new_show)

    except Exception as e:

        config.line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text=f"❌ 複製失敗\n{e}"
            )
        )
        return

    user_state[user_id] = {
        "mode": "修改演出",
        "step": "field",
        "show_id": new_show["id"],
    }

    config.line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(
            text=(
                "✅ 已建立複製演出\n\n"
                    f"🎤 {new_show['演出名稱']}\n\n"
                    "原演出已保留，新演出已建立。\n"
                    "請選擇要修改的欄位："
            ),
            quick_reply=edit_field_quick_reply()
        )
    )