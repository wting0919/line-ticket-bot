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

from helpers import (
    get_state,
    set_state,
)

import config


def handle_copy_show(event, text, user_id):

    state = get_state(user_id)

    if isinstance(state, dict) and "shows" in state:
        shows = state["shows"]
    else:
        shows = get_all_shows()

    try:
        show_id = int(
            text.replace("複製ID", "").strip()
        )

    except ValueError:

        config.line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text="請輸入格式：\n複製ID 1"
            )
        )
        return True

    source_show = next(
        (
            item
            for item in shows
            if item.get("id") == show_id
        ),
        None,
    )

    if source_show is None:

        config.line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text="❌ 找不到這筆演出"
            )
        )

        return True

    new_show = deepcopy(source_show)

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

    new_show["搶票狀態"] = "待搶票"
    new_show["取票狀態"] = "未取票"

    new_show["搶票時間"] = ""
    new_show["售票階段"] = ""

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
        return True

    set_state(
        user_id,
        {
            "mode": "修改演出",
            "step": "field",
            "show_id": new_show.get("id"),
        }
    )

    message = (
        "✅ 已建立複製演出\n"
        "──────────\n"
        f"🎤 {new_show.get('藝人', '')}\n"
        f"🏷️ {new_show.get('活動', '')}\n"
    )

    if new_show.get("活動名稱"):
        message += f"✨ {new_show['活動名稱']}\n"

    message += (
        "──────────\n"
        "已清除：🕒 搶票時間、🚩 售票階段\n"
        "請選擇要修改的欄位"
    )

    config.line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(
            text=message,
            quick_reply=edit_field_quick_reply()
        )
    )

    return True